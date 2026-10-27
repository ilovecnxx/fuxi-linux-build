#!/bin/bash
# 从 Android 固件生成主线需要的 WCN7850 固件目录（只读复制，不改手机任何分区）：
#   WiFi（ath12k）：work/firmware-src/kiwi/（modem 分区 image/kiwi 的拷贝）→
#     amss20.bin → amss.bin；phy_ucode20.elf → m3.bin（Android cnss 对 Kiwi 就是把它当 M3 加载）；
#     regdb.bin；board-2.bin = bd_m3.elf（芯片 board_id=0xff，小米按机型代号 M3 选标定数据）
#   蓝牙（btqca）：work/firmware-src/bt/（Android /vendor/bt_firmware/image 的拷贝）里的 hmt* →
#     qca/hmtbtfw20.tlv、qca/hmtnv20.bin（以及 hmtnv20.bXX 变体）
# 产物：work/firmware/{ath12k/WCN7850/hw2.0,qca}/ → 部署到手机 /lib/firmware/
set -euo pipefail
B="$(cd "$(dirname "$0")/.." && pwd)"
K="$B/work/firmware-src/kiwi"
BT="$B/work/firmware-src/bt"
W="$B/work/firmware/ath12k/WCN7850/hw2.0"
Q="$B/work/firmware/qca"

if [ -f "$K/amss20.bin" ]; then
  mkdir -p "$W"
  cp "$K/amss20.bin" "$W/amss.bin"
  cp "$K/phy_ucode20.elf" "$W/m3.bin"
  cp "$K/regdb.bin" "$W/regdb.bin"
  python3 -I "$B/scripts/fuxi-ath12k-board.py" "$W/board-2.bin" \
    "bus=pci,vendor=17cb,device=1107,subsystem-vendor=17cb,subsystem-device=1107,qmi-chip-id=2,qmi-board-id=255=$K/bd_m3.elf" \
    "bus=pci,qmi-chip-id=2,qmi-board-id=255=$K/bd_m3.elf"
  echo "[wifi] $(ls "$W" | tr '\n' ' ')"
else
  echo "[wifi] 缺 $K/amss20.bin（先从 modem 分区 image/kiwi 复制）"
fi

if ls "$BT"/hmt* >/dev/null 2>&1; then
  mkdir -p "$Q"
  cp "$BT"/hmt* "$Q/"
  echo "[bt] $(ls "$Q" | tr '\n' ' ')"
else
  echo "[bt] 缺 $BT/hmt*（先从 Android /vendor/bt_firmware/image 复制）"
fi
