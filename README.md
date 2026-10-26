# 小米 13（fuxi / SM8550）Android + 主线 Linux 双系统

在一台 bootloader 已解锁的小米 13 上，让 **Android（LineageOS 24.0）** 与 **自编主线 Linux（Ubuntu 26.10 根文件系统）** 共存，并能在两者之间来回切换。Linux 侧是纯主线内核，**不使用厂商内核、Halium 或 Droidian**。

- 设备：小米 13（代号 `fuxi`，Qualcomm SM8550 / 骁龙 8 Gen 2）
- Android：LineageOS 24.0，位于 A/B 槽位 `b`
- Linux：Linux 7.3.0（基线 commit `5b0764a53235d3c77e1ed674e836e1b3fe1a4b1f`，自编译）+ Ubuntu 26.10，根文件系统在 `linux` 分区 `/dev/sda33`（ext4，100 GB）
- 分区：A/B 动态分区，4K 页；bootloader 已解锁
- 引导：XBL → 高通 UEFI → ABL（槽位 b）；正常开机进 Android，recovery 启动进 `recovery_b` 里的 Linux 镜像
- 仓库：<https://github.com/ilovecnxx/fuxi-linux-build>，发布版本 `v0.1.0-dualboot-20261027`（Release 见仓库页面）

> 本仓库是一份**实验记录 + 可复现的构建/验证材料**，不是一键刷机包。仓库**不包含**根文件系统镜像、厂商固件源码与私钥；发布镜像里内嵌了 801,847 B 的厂商 `fuxi.dtb`，它**只作为 ABL 的引导诱饵，不含可执行代码**（完全自建请从自有设备原厂 ROM 提取）。交付物哈希见根目录 [`SHA256SUMS`](SHA256SUMS)，实机验证记录见 [PROGRESS.md](PROGRESS.md)。首次操作前请先读 [docs/双系统启动说明.md](docs/双系统启动说明.md)。

## 状态一览

| 能力 | 状态 |
|---|---|
| 主线内核启动进入用户空间（M1） | ✅ 已达成 |
| 双系统共存：Android 与 Linux 同一台机器 | ✅ 已达成 |
| 在系统内切换（无需电脑、无需线） | ✅ 已达成 |
| 文本控制台显示（simpledrm + fbcon，tty1） | ✅ 已达成 |
| USB 串口 shell（`/dev/fuxi-acm`，initramfs 8 秒调试窗口） | ✅ 已达成 |
| SSH over USB 网络（手机 `10.42.0.2`） | ✅ 已达成 |
| 触摸 / 实体按键输入 | ❌ 未支持 |
| WiFi / 蓝牙 | ❌ 未支持 |
| GPU 加速 / 图形桌面 | ❌ 未支持 |
| 音频 / 相机 / 通话 | ❌ 未支持 |
| UFS HS-G5 高速链路 | ⚠️ 补丁暂缓（默认 G4，见下） |

## 硬件支持矩阵

| 硬件 | 状态 | 说明 |
|---|---|---|
| SoC / CPU（SM8550，8 核） | ✅ | 主线 7.3.0 启动、SMP 正常 |
| 内存 | ✅ | 正常识别使用 |
| UFS 存储 | ⚠️ | G4 下稳定（根文件系统在 `sda33`）；HS-G5 补丁暂缓 |
| 显示 | ⚠️ | 仅 `simpledrm` + `fbcon` 文本控制台（tty1，16×32 字体）；无面板/DSI 驱动 |
| USB（gadget） | ✅ | CDC ACM 串口 + USB 网络（ECM），供串口 shell、SSH |
| 触摸（ST FTS） | ❌ | 无驱动 |
| 按键 / 电源键输入 | ❌ | 未接入输入子系统 |
| WiFi / 蓝牙 | ❌ | 无驱动 |
| GPU（Adreno） | ❌ | 无驱动 |
| 音频 | ❌ | 无驱动 |
| 相机 | ❌ | 无驱动 |
| 蜂窝网络 / 通话 | ❌ | 不适配，且不建议在主线侧尝试 |

## 快速开始（已验证路径）

前提：小米 13（fuxi）已解锁 bootloader；Android（LineageOS 24.0）在槽位 `b` 可正常启动；Linux 主机上有可用的 `adb` 与 `fastboot`；手机上的 `linux` 分区（`/dev/sda33`）已装好 Ubuntu 根文件系统（**根文件系统需自行准备，本仓库不提供**）。

### 0. 先备份原厂分区（强烈建议）

刷写 `recovery_b` 前，用 `adb` 把它（以及 `boot_b` 等）原样导出到电脑保存。本仓库不附带厂商分区镜像，恢复原厂完全依赖你自己的备份。

```
adb root
adb shell 'ls -l /dev/block/by-name/recovery_b'
adb shell 'dd if=/dev/block/by-name/recovery_b bs=1M 2>/dev/null' > recovery_b-stock.img
adb shell 'sha256sum /dev/block/by-name/recovery_b'
```

（`dd` 的统计信息走 stderr，必须丢弃，否则会混进导出的镜像。）

注意记录 Android 当前槽位（`adb shell getprop ro.boot.slot_suffix`，应为 `_b`）。

### 1. 把 Linux 镜像写进 `recovery_b`

本仓库提供 `images/recovery-linux.img`（7,389,184 B，内核 + 内建 initramfs；sha256 见根目录 [`SHA256SUMS`](SHA256SUMS)）：

```
adb root
adb push images/recovery-linux.img /data/local/tmp/l.img
adb shell 'dd if=/data/local/tmp/l.img of=/dev/block/by-name/recovery_b bs=1M conv=fsync; sync; rm /data/local/tmp/l.img'
```

写入后建议回读校验（`scripts/fuxi-test-recovery.sh` 会自动做 16 位 sha256 比对）。

### 2. 切换到 Linux

- 关机状态：按住 **音量上 + 电源** 开机；
- Android 里：电源菜单 → 重启 → **恢复模式**（LineageOS 需在开发者选项打开"高级重启"）；
- 电脑上：`adb reboot recovery`。

正常开机（电源键）不会碰 `recovery_b`，所以随时可以直接回 Android。万一 Linux 镜像起不来：长按电源 20 秒强制关机/重启，正常开机即回 Android。

### 3. 使用 Linux

- 屏幕：`simpledrm` + `fbcon`，tty1 登录界面（16×32 字体）。触摸、按键暂不可用。
- USB 串口：主线内核的 CDC ACM gadget（`0525:a4a7`）在主机上出现为串口设备，root 自动登录（`fuxi-serial-shell.service`）。仓库 `scripts/udev/` 提供两条主机规则：`51-fuxi-gadget.rules` 把设备软链为 `/dev/fuxi-acm`（普通用户可读写、ModemManager 忽略），`52-fuxi-usb-port-power.rules` 允许脚本"软件拔插"USB 端口。没装规则时设备名是 `/dev/ttyACM*`，`scripts/` 里默认按 `/dev/fuxi-acm` 写，做个符号链接或改脚本变量即可。initramfs 阶段有 **8 秒调试窗口**：在串口上 `touch /tmp/stay` 可让 initramfs 停住不自动启动 Ubuntu。
- USB 网络 / SSH：手机 `10.42.0.2`，主机侧为 NetworkManager 共享连接（`10.42.0.1`，自动 NAT）。`scripts/fuxi-ssh.sh` 封装了 ssh 调用（默认用作者本地 `work/ssh/fuxi_root` 私钥，公开环境下请换成你自己的密钥/密码）。
- 关机/重启：Linux 里 `reboot` 即回 Android。

### 4. 回 Android / 进 fastboot

| 目标 | 操作 |
|---|---|
| 回 Android | Linux 里 `reboot` / `systemctl reboot` |
| 进 Linux | 关机后 音量上+电源；或 Android 重启到 Recovery；或 `adb reboot recovery` |
| 进 fastboot | Linux 里 `systemctl reboot --reboot-argument=bootloader`；或关机后 音量下+电源 |

## 启动链

```
XBL → 高通 UEFI → ABL（槽位 b）
  正常开机 → boot_b … → Android
  recovery → recovery_b 里的 boot.img v1：
              kernel 字段 = Image.gz + 厂商 fuxi.dtb（"诱饵"，只为让 ABL 满意）
              → 主线内核启动，CONFIG_FUXI_FORCE_BUILTIN_DTB=y 忽略 ABL 传入的 DTB，
                改用编进内核的主线 DTB（cmdline 也来自 DTS 的 /chosen/bootargs）
              → 内建 initramfs：USB 串口就绪后等 8 秒，主机没 touch /tmp/stay
                就 switch_root 到 sda33 上的 Ubuntu（systemd）
```

为什么需要"DTB 诱饵"：ABL 会把 `dtbo` 分区的 overlay 叠到镜像附带的 DTB 上，**叠到主线 DTB 会卡死**（用"立即 PSCI 复位"的最小桩内核验证过：附主线 DTB 卡住，附厂商 DTB 19 秒正常回 Android）。所以镜像里放厂商 DTB 当诱饵，内核再用内建主线 DTB 覆盖。

## 构建与验证

完整构建信息（版本、工具链、配置来源、产物哈希、复现步骤）见 [`source/BUILD-INFO.md`](source/BUILD-INFO.md)。要点：

- 内核版本串 `Linux 7.3.0+ #101 SMP PREEMPT Tue Oct 27 06:19:12 CST 2026`，基线 commit `5b0764a53235d3c77e1ed674e836e1b3fe1a4b1f`；
- 受跟踪文件改动 5 处（`source/kernel.diff`），新增文件 4 个（`source/linux-untracked/`）；
- 镜像为 Android boot header v1（page 4096、ramdisk 字段为空、initramfs 已编进内核），结构与 cmdline 见 BUILD-INFO；
- 交付物（`images/` 与 `source/` 制品，共 12 项）的 sha256 见根目录 [`SHA256SUMS`](SHA256SUMS)。

### 源码组成

| 路径 | 内容 |
|---|---|
| `source/kernel.config` | 实际使用的内核配置（`CONFIG_FUXI_FORCE_BUILTIN_DTB=y`、4K 页、内建 initramfs、simpledrm/fbcon、USB gadget 等） |
| `source/kernel.diff` | 对主线内核的 5 处改动：新增 `FUXI_FORCE_BUILTIN_DTB` Kconfig、DTS Makefile、`fuxi_dtb.o`/`fuxi_early.o`、`setup_arch` 覆盖 DTB、`fuxi.nosync` 诊断参数 |
| `source/linux-untracked/` | 主线树里新增的文件：板级 DTS `sm8550-xiaomi-fuxi-min.dts`、`fuxi_dtb.S`（内嵌 DTB）、`fuxi_early.c`（早期屏幕 console）、`fuxi_font.h`（16×32 字体） |
| `source/initramfs/` | `init`（等待 USB 串口 8 秒 → `switch_root` 到 `sda33`，失败时屏幕报告 + 180 秒安全重启）与 `initramfs.list` |
| `source/patches/` | `ufs-qcom-sm8550-g5.patch`（HS-G5，暂缓） |

### 构建镜像

```
# 1) 编内核 + DTB + 内建 initramfs，再打包成 boot.img v1
scripts/fuxi-build-abl.sh <名字>          # → work/kbuild/abl-fuxi-<名字>.img

# 2) 不写分区，fastboot boot 临时启动测试（失败不影响 Android）
scripts/fuxi-run.sh work/kbuild/abl-fuxi-<名字>.img '<手机上要执行的命令>' …

# 3) 写 recovery_b 跑一轮完整回归（写入 → 重启 → SSH → 回 Android，产物进 evidence 式 summary）
scripts/fuxi-test-recovery.sh work/kbuild/abl-fuxi-<名字>.img
```

说明：
- 内嵌 DTB 由内核构建时 `incbin` 进镜像，但 boot.img 头部仍附**厂商 `fuxi.dtb` 诱饵**——该文件需从你自己的原厂 boot/recovery 镜像中提取，本仓库不附带厂商 DTB。
- 改了 initramfs 必须先删 `usr/initramfs_data.cpio*` 再 make，否则不会重新打包（`fuxi-build-abl.sh` 已自动处理）。
- 仓库里的脚本按作者本地工作区布局编写（`tools/platform-tools`、`work/`、`build/` 等），公开环境下请按自己的目录调整变量；`adb`/`fastboot` 直接用系统包也可。

### 验证口径

- `systemd-analyze`：内核 + 用户空间耗时，实测 **8.73–8.89 s + 1.96–2.46 s = 10.715–11.194 s**（三组记录）；
- 从发出重启到 SSH 可用约 16 秒（含 ABL 与重启流程）；
- 镜像写入后回读 sha256 前 16 位比对；
- 原始记录在 `evidence/rtest-*/`（`summary.txt` 时间线 + `ssh.txt` 机器上的实际输出）。

## 已知坑（都踩过）

- **内核 cmdline 不要加 `console=ttyGS0`**：`/dev/console` 会变成 USB 串口，主机没读时写满阻塞——启动卡几分钟、关机永远卡住。
- **ABL 一次失败启动后，同一 fastboot 会话会拒绝后续镜像**：先 `fastboot reboot bootloader` 再继续。
- **USB 线材/接口**：出现 `error -71`、只能 full-speed 枚举时是信号问题，换线换口；主机侧曾记录 399 次过流。`scripts/udev/52-fuxi-usb-port-power.rules` 允许脚本"软件拔插"。
- **不要乱改 GPT 槽位属性**：曾用 `fastboot set_active a` 一次性把 50 多个分区（abl/tz/hyp/aop/modem/uefi…）的 active 位一起切换。`images/sde-gpt-slot-*.bin` 只是备份与对照。
- **UFS HS-G5 暂缓**：G5 下 `reboot -f` 曾进 EDL（约 85 秒后自行退出），G4 下同样流程 10+ 次正常。重新启用前先查 `ufshcd` 关机流程。
- **诊断开关**：`fuxi.nosync=1` 会保留 bootloader 留下的电源/带宽/时钟投票（用于排查 sync_state 相关黑屏），非必要不要开。

## 恢复原厂

1. 用自己的原厂 `recovery_b` 备份写回 `recovery_b`（fastboot 或 Android 内 `dd` 均可）；
2. 确认 `boot_b` 等槽位分区未被改动（本方案只写 `recovery_b`）；
3. 不要尝试改槽位属性；恢复后正常开机即回到 Android。

历史记录：`boot_a` 已写回原厂（sha256 `c02adcce…`）；原厂 `recovery_b` 备份与设备原内容 sha256 一致（备份不随仓库发布，请使用你自己的备份）。更细的步骤见 [docs/双系统启动说明.md](docs/双系统启动说明.md)。

## 免责声明

- 解锁 bootloader 会清空数据、可能失去保修并触发安全机制；刷机、`dd` 写分区等操作**风险自负**，作者不对变砖、数据丢失或设备损坏负责。
- 本仓库不涉及任何破解、绕过安全启动或分发厂商固件/密钥；请使用**你自己拥有的设备与自己的原厂备份**。
- 项目处于早期实验阶段，部分功能（触摸、WiFi、GPU、音频、相机等）**明确不可用**，请勿当作日常可用系统。
- Android 侧使用 LineageOS，请遵守其许可；内核代码遵循上游 GPL-2.0。

## 仓库结构

| 路径 | 内容 |
|---|---|
| `docs/` | [双系统启动说明](docs/双系统启动说明.md)（权威操作文档）、历史交接与可行性调研 |
| `research/` | 上游驱动/启动链调研笔记 |
| `scripts/` | 构建、刷写/启动测试、串口/SSH、槽位表解析、恢复与 udev 规则 |
| `source/` | `kernel.config`、`kernel.diff`、`linux-untracked/`、`initramfs/`、`patches/`；构建信息见 `source/BUILD-INFO.md` |
| `images/` | `recovery-linux.img`（可启动 Linux 镜像）与 sde GPT 槽位表备份 |
| `evidence/` | 实机验证记录（`rtest-*/summary.txt`、`ssh.txt`）与内核构建日志 |
| `SHA256SUMS` | 镜像与源码文件的全量 sha256 |
| `PROGRESS.md` | 时间线与验证证据表 |

> 历史上尝试过的 EDK2/UEFI 诊断引导路线与厂商内核构建流水线**已从当前树移除**（git 历史可查），当前树只保留 ABL 直接引导这一条可行路径。
