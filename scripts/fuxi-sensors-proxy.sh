#!/bin/bash
# 传感器第二步：在手机上重编 Ubuntu 的 iio-sensor-proxy 3.9，打开 Qualcomm SSC 支持（libssc），
# 给桌面（Phosh/GNOME）提供自动旋转、距离（通话贴脸熄屏）、光线（自动亮度）、指南针。
# Ubuntu 的 debian/rules 把 "ARCHES_QCOM_SSC = arm64" 注释掉了（Debian 原本是开的）→ 去掉注释 + 装 libssc-dev 重编。
# 源码是 Ubuntu 镜像上的同版本源码包（work/src/iio-sensor-proxy/，orig + debian），不改上游代码。
# 前提：手机在 Ubuntu、能上网，hexagonrpcd 已跑通（scripts/fuxi-sensors.sh）。
# 用法: scripts/fuxi-sensors-proxy.sh
set -u
B="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$B/work/claude-logs/sensors-proxy-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$LOG") 2>&1
say() { echo "$(date +%T) $*"; }
ssh_() { timeout "${T:-120}" "$B/scripts/fuxi-ssh.sh" "$@"; }

say "== 1. 推源码"
tar -C "$B/work/src/iio-sensor-proxy" -cf - . | ssh_ 'rm -rf /root/build/iio-sensor-proxy && mkdir -p /root/build/iio-sensor-proxy && tar -C /root/build/iio-sensor-proxy -xf - && echo src-ok'

say "== 2. 装依赖并编译（几分钟）"
T=3600 ssh_ 'set -e
export DEBIAN_FRONTEND=noninteractive
apt-get install -y --no-install-recommends build-essential debhelper fakeroot dpkg-dev meson pkgconf libgudev-1.0-dev \
  systemd-dev libpolkit-gobject-1-dev libssc-dev locales-all gtk-doc-tools libgtk-3-dev 2>&1 | tail -n 2
cd /root/build/iio-sensor-proxy
tar xf iio-sensor-proxy_3.9.orig.tar.bz2
cd iio-sensor-proxy-3.9 && tar xf ../iio-sensor-proxy_3.9-1ubuntu1.debian.tar.xz
sed -i "s/^# ARCHES_QCOM_SSC = arm64/ARCHES_QCOM_SSC = arm64/" debian/rules
grep -n "^ARCHES_QCOM_SSC" debian/rules
DEB_BUILD_OPTIONS=nocheck dpkg-buildpackage -b -uc -us -d 2>&1 | tail -n 5
ls -1 ../*.deb'

say "== 3. 安装并锁定版本（避免 apt 升级换回没有 SSC 的版本）"
T=300 ssh_ 'cd /root/build/iio-sensor-proxy && dpkg -i iio-sensor-proxy_*_arm64.deb 2>&1 | tail -n 2 && apt-mark hold iio-sensor-proxy
grep -q "iio-sensor-proxy（SSC）" /root/fuxi-mainline-backup/CHANGES.txt || echo "fuxi-mainline（传感器）: iio-sensor-proxy 3.9 重编（ssc-support=enabled），apt-mark hold；apt: libssc-dev 及编译依赖" >> /root/fuxi-mainline-backup/CHANGES.txt
systemctl restart iio-sensor-proxy; sleep 5
systemctl --no-pager status iio-sensor-proxy | tail -n 8
timeout 15 monitor-sensor 2>&1 | head -n 20'
say "完成，日志 $LOG"
