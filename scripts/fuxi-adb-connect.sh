#!/usr/bin/env bash
# 连接手机的无线 ADB（重启后也能自动连上）。
#
# 手机侧一次性配置（已做，见 docs/无线ADB方案-20261031.md）：
#   setprop persist.adb.tcp.port 5555   # persist.* 跨重启保留，开机 adbd 直接监听 5555
#   并把主机公钥写进 /data/misc/adb/adb_keys（免授权弹窗）
#
# 本脚本按以下顺序尝试，任一成功即返回 0：
#   1) adb mdns services 发现 _adb._tcp 后按 mDNS 名字连接（不受 IP 变化影响）
#   2) 直接连已知地址（FUXI_ADB_ADDR，默认 10.10.10.43:5555）
#   3) 在当前网段扫 5555 端口
#
# 用法：
#   scripts/fuxi-adb-connect.sh            # 连一次
#   scripts/fuxi-adb-connect.sh --wait     # 循环等到连上（用于开机后）
#   scripts/fuxi-adb-connect.sh --watch    # 常驻：掉线就重连
set -uo pipefail

B="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="$B/tools/platform-tools:$PATH"
export LD_LIBRARY_PATH="$B/tools/platform-tools/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

KNOWN_ADDR="${FUXI_ADB_ADDR:-10.10.10.43:5555}"
SUBNET_PREFIX="${FUXI_ADB_SUBNET:-10.10.10}"

say() { printf '%s %s\n' "$(date +%T)" "$*"; }

adb_ready() {
    adb devices 2>/dev/null | awk 'NR>1 && $2=="device"{found=1} END{exit !found}'
}

try_mdns() {
    local name
    timeout 12 adb start-server >/dev/null 2>&1
    name="$(timeout 8 adb mdns services 2>/dev/null | awk '$2=="_adb._tcp"{print $1; exit}')"
    [ -n "$name" ] || return 1
    say "mDNS 发现 $name，按名字连接"
    timeout 12 adb connect "$name" >/dev/null 2>&1
    adb_ready
}

try_known() {
    say "直连 $KNOWN_ADDR"
    timeout 10 adb connect "$KNOWN_ADDR" >/dev/null 2>&1
    adb_ready
}

try_scan() {
    local ip port
    say "扫描 ${SUBNET_PREFIX}.0/24 的 5555 端口"
    for ip in $(seq 1 254); do
        ( timeout 1 bash -c "echo > /dev/tcp/${SUBNET_PREFIX}.$ip/5555" 2>/dev/null \
            && echo "${SUBNET_PREFIX}.$ip" ) &
    done > /tmp/fuxi-adb-scan.$$ 2>/dev/null
    wait
    for ip in $(sort -u /tmp/fuxi-adb-scan.$$ 2>/dev/null); do
        rm -f /tmp/fuxi-adb-scan.$$
        say "扫描命中 $ip:5555"
        timeout 10 adb connect "$ip:5555" >/dev/null 2>&1
        adb_ready && return 0
    done
    rm -f /tmp/fuxi-adb-scan.$$
    return 1
}

connect_once() {
    adb_ready && { say "ADB 已连接："; adb devices | awk 'NR>1 && $2=="device"'; return 0; }
    try_mdns && { say "已连接（mDNS）"; return 0; }
    try_known && { say "已连接（已知地址）"; return 0; }
    try_scan && { say "已连接（扫描）"; return 0; }
    return 1
}

case "${1:-}" in
    --wait)
        for i in $(seq 1 120); do
            connect_once && exit 0
            say "等待手机（${i}/120）…"; sleep 5
        done
        say "超时：手机未连上"; exit 1
        ;;
    --watch)
        while true; do
            if ! adb_ready; then
                say "ADB 掉线，重连中…"
                connect_once || sleep 10
            fi
            sleep 15
        done
        ;;
    *)
        connect_once && exit 0
        say "连不上手机。检查：手机与电脑同一 WiFi；手机 开发者选项→无线调试 打开。"
        exit 1
        ;;
esac
