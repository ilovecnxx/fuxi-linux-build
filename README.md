# 小米 13（fuxi / SM8550）Android + 主线 Linux 双系统

在一台 bootloader 已解锁的小米 13 上，让 **Android（LineageOS 24.0）** 与 **自编主线 Linux（Ubuntu 26.10 根文件系统）** 共存，并能在两者之间来回切换。Linux 侧是纯主线内核，**不使用厂商内核、Halium 或 Droidian**。

- 设备：小米 13（代号 `fuxi`，Qualcomm SM8550 / 骁龙 8 Gen 2）
- Android：LineageOS 24.0，位于 A/B 槽位 `b`
- Linux：Linux 7.3.0（基线 commit `5b0764a53235d3c77e1ed674e836e1b3fe1a4b1f`，自编译）+ Ubuntu 26.10，根文件系统在 `linux` 分区 `/dev/sda33`（ext4，100 GB）
- 分区：A/B 动态分区，4K 页；bootloader 已解锁
- 引导：XBL → 高通 UEFI → ABL（槽位 b）；正常开机进 Android，recovery 启动进 `recovery_b` 里的 Linux 镜像
- 仓库：<https://github.com/ilovecnxx/fuxi-linux-build>；当前版本 **`v0.3.0-dualboot-20261029`**（M6 真机可用：原生显示 / GPU / 120 Hz / 音频 / WiFi 连网）；旧版 `v0.2.0-dualboot-20261027`、`v0.1.0-dualboot-20261027` 的 tag 与 Release 保留

> 本仓库是一份**实验记录 + 可复现的构建/验证材料**，不是一键刷机包。仓库**不包含**根文件系统镜像、厂商固件与私钥；发布镜像里内嵌了 801,847 B 的厂商 `fuxi.dtb`，它**只作为 ABL 的引导诱饵，不含可执行代码**（完全自建请从自有设备原厂 ROM 提取）。交付物哈希见根目录 [`SHA256SUMS`](SHA256SUMS)，实机验证记录见 [PROGRESS.md](PROGRESS.md)。首次操作前请先读 [docs/双系统启动说明.md](docs/双系统启动说明.md)。

## 当前状态（v0.3.0，2026-10-29）

`recovery_b` 里现在是 `screen120-blfix`（`7.3.0+ #191`）。用户在真机上现场确认：

- **原生显示**：MSM DSI + `panel-xiaomi-fuxi` 出画面，触控位置准确（此前只有 `simpledrm` 文本控制台）；
- **GPU**：Adreno 740 改用 `/odm/firmware` 里小米签名的 ZAP 后初始化成功，Phosh 已切到 GPU（FD740）渲染，明显更流畅；
- **120 Hz**：面板 120 Hz + GPU 温控接入，更顺滑、画面正常；
- **显示收尾**：熄屏时写亮度报错的背光修复（面板未 prepared 时只记值、点亮时再应用），3 轮熄屏/唤醒自动测试通过，光线传感器自动亮度生效，GPU 满载 3 分钟约 66 °C 稳定；
- **WiFi**：重启后自动连网，外网/HTTPS 走 WiFi、WiFi SSH 可用、管制域 CN；
- **蓝牙**：出厂地址与对端 L2CAP 链路通过；
- **音频**：两颗 CS35L41 独立测试可听，桌面左右短音用户确认（四声都听见）；
- **基本功能**：HTTPS 根证书、浏览器启动退出、竖屏键盘按键、中文输入与文本保存均已修复并确认。

**仍待验收**（不要当成已通过）：物理亮度观感、物理旋转与桌面联动、90 Hz/动态刷新率；文件选择器（portal）；蓝牙耳机 / A2DP；音频保护标定、完整声道定位与音质、麦克风；实际充电曲线与续航（日常内核仍不启用深度空闲与系统挂起）；相机、蜂窝。

逐项细节见 [docs/目标-M5.md](docs/目标-M5.md) 与下面这批 10-29 记录：

| 记录 | 内容 |
|---|---|
| [PROGRESS.md](PROGRESS.md) | 从设备摸底到今天的完整时间线与逐轮实测证据 |
| [docs/进展-20261029.md](docs/进展-20261029.md) | 10-29 调频/温控与可重复验收 |
| [docs/基本功能修复-20261029.md](docs/基本功能修复-20261029.md) | HTTPS、浏览器、竖屏键盘、中文输入修复 |
| [docs/GPU初始化故障定位-20261029.md](docs/GPU初始化故障定位-20261029.md)、[docs/显示驱动故障定位-20261029.md](docs/显示驱动故障定位-20261029.md) | 原生显示与 Adreno GPU 的故障定位过程 |
| [docs/显示驱动安装-20261029.md](docs/显示驱动安装-20261029.md)、[docs/音频出声修复-20261029.md](docs/音频出声修复-20261029.md) | 显示驱动安装、音频出声修复 |
| [docs/手机日用目标-路线图-20261029.md](docs/手机日用目标-路线图-20261029.md) | 「手机日用」后续路线图 |

## 版本说明：v0.1.0 → v0.3.0

| 版本 | 内容 |
|---|---|
| `v0.1.0`（2026-10-27 凌晨） | 双系统成立：ABL 直接引导 `recovery_b`、主线内核进用户空间、文本控制台、USB 串口与 SSH |
| `v0.2.0`（2026-10-27 白天） | M5/M6：**真机验证**了触摸、按键、电量/充电状态、WiFi/蓝牙硬件；在电脑上**构建**了原生显示/GPU、USB-C/DP、音频、基带、相机、传感器、省电、调频温控、全功能镜像（当版尚未上机） |
| `v0.3.0`（2026-10-29，本版） | 上机落地：原生显示（60/90/120 Hz）、GPU（FD740）渲染、双功放音频、WiFi 连网 + 管制域、蓝牙 L2CAP、CPU 调频/温控进入日常镜像，以及 HTTPS/浏览器/竖屏键盘/中文输入等基本功能修复 |

状态表沿用 ✅（真机验证并留下记录）/ ⚠️（部分验证）/ 🚧（只构建未上机）/ ⏳（未开始）四种标记；本版的实测记录在 `evidence/rtest-20261029-*` 与 `evidence/logs-20261029/`。

## 状态一览

| 能力 | 状态 | 说明 |
|---|---|---|
| 主线内核启动进入用户空间（M1） | ✅ | Linux 7.3.0 进入 systemd，`systemctl is-system-running` = `running` |
| 双系统共存与系统内切换 | ✅ | 只写 `recovery_b`；正常开机不碰它，随时可回 Android |
| 文本控制台（simpledrm + fbcon，tty1） | ✅ | 16×32 字体，登录界面可用 |
| USB 串口 shell（`/dev/fuxi-acm`） | ✅ | initramfs 8 秒调试窗口（`touch /tmp/stay` 可停住） |
| SSH over USB 网络（手机 `10.42.0.2`） | ✅ | 每轮回归都以 SSH 可用为通过标准 |
| 触摸（ST FTM5） | ✅ | 新写主线驱动 `st-ftm5`（SPI4）：chip 3640 / fw 0053、多点、1/10 像素坐标；Phosh 桌面上触控位置经用户现场确认准确 |
| 实体按键（电源 / 音量） | ✅ | `pmic_pwrkey`、`pmic_resin`、`gpio-keys` 均注册；logind 已把电源键设为 ignore |
| 电量 / 充电状态 | ✅ | ADSP remoteproc + pmic_glink + `qcom_battmgr`，电量/电压/电流/温度/健康度可读；10-29 实测插充电器时 `status=Charging`、电流随负载变化（`evidence/logs-20261029/m51-charging-20261029.log`），完整充电曲线仍待观察 |
| WiFi（ath12k / WCN7850） | ✅ | 10-29 整机重启验收：自动连网、外网与 HTTPS 走 WiFi、WiFi SSH 可用、管制域 CN；小米标定的兼容性仍未解决，目前用上游固件 + 参考板标定 |
| 蓝牙 | ✅ | HCI UART/QCA 注册；出厂地址与对端 L2CAP 链路通过（`evidence/logs-20261029/bt-l2ping-20261029.log`）；耳机 / A2DP 未测 |
| 显示（原生面板 + GPU） | ✅ | MSM DSI 原生驱动 + `panel-xiaomi-fuxi`（DSC，60/90/120 Hz），画面与触控经用户现场确认；Adreno 740（FD740）GPU 渲染已切换并明显更流畅；熄屏/唤醒 3 轮与自动亮度已通过，物理亮度观感、90 Hz/动态刷新率待验收 |
| 音频（CS35L41 + WCD938x） | ✅ | 两颗 CS35L41 独立测试可听、桌面左右短音用户确认；保护标定、完整声道定位/音质、麦克风待验收 |
| 基带 / 蜂窝（IPA + MPSS） | 🚧 | v0.2.0 构建（`-modem`），仍未上机，不能视为可用手机功能 |
| 相机（CAMSS） | 🚧 | v0.2.0 构建（`-camera`）+ 调研材料，仍未上机 |
| 传感器（FastRPC / hexagonrpcd） | ⚠️ | 加速度、光线、距离、磁场、指南针已有实测数据，SensorProxy 已接入；物理旋转与桌面联动待验收 |
| 省电 / 挂起（SUSPEND + cpuidle） | 🚧 | 日常镜像仍不启用深度空闲与系统挂起，续航未达目标；`-sleep` 变体待上机 |
| 调频 / 温控 | ✅ | 日常镜像默认带 CPU 调频/温控；daily-pm1 实机运行：3 个 schedutil 策略、43 个热区、3 个 CPU cooling 设备；120 Hz 镜像已接入 GPU 温控 |
| USB-C / DP 桌面 | 🚧 | 已构建（`-disp` / `-desk`），待插显示器/OTG |
| 图形界面（Phosh） | ✅ | Phosh 桌面可用：GPU 渲染、竖屏屏幕键盘（Stevia）、中文输入与文本保存经用户确认；文件选择器待验收 |
| 屏下指纹 | ❌ | Goodix 走 TrustZone，主线短期不可行 |
| UFS HS-G5 高速链路 | ⚠️ | 默认 G4；G5 补丁暂缓（关机路径，见「已知坑」） |

## 硬件支持矩阵

| 硬件 | 状态 | 说明（含实测证据） |
|---|---|---|
| SoC / CPU（SM8550，8 核） | ✅ | 主线 7.3.0 启动、SMP 正常 |
| 内存 | ✅ | 11.1 GB 可用；9 GB tmpfs 写入 + 两次 md5 一致，dmesg 无 Oops/SError（`rtest-20261027-070521`） |
| UFS 存储 | ⚠️ | G4 下稳定（根文件系统在 `sda33`）；关机复位线修复自 `wifi3` 起编入（本轮镜像同一源码树，也含该修复），但多轮关机/重启回归仍未有系统记录；HS-G5 暂缓 |
| 显示 | ✅ | 原生 MSM DSI + `panel-xiaomi-fuxi`：1080×2400、DSC、60/90/120 Hz，画面与触控经用户确认；`simpledrm` + `fbcon` 文本控制台仍可用作兜底 |
| 触摸（ST FTM5） | ✅ | `st-ftm5` probe：chip 3640 / fw 0053 / cfg 0042，panel 2399×1079，坐标 0..10799 × 0..23999，多点 |
| 按键 | ✅ | 电源（`pmic_pwrkey`）、音量下（`pmic_resin`）、音量上（`gpio-keys`）；`/etc/systemd/logind.conf.d/10-fuxi-powerkey.conf` 把电源键设为 ignore |
| 电量 / 充电 | ✅ | `qcom-battmgr-bat`：`STATUS=Charging`、`CAPACITY`、`VOLTAGE_NOW`、`CURRENT_NOW`、`TEMP`、`STATE_OF_HEALTH`、`MODEL_NAME` 可读；10-29 实测插充电器时 99% → 电流随负载 0.1–0.7 A 变化，USB 侧 `online=1`、`DCP` 充电器识别；完整充电曲线与续航未单独验证 |
| WiFi | ✅ | PCIe0 链路 `0000:01:00.0`（17cb:1107）、WCN7850 固件 + `ath12k`；10-29 验收：自动连网、外网/HTTPS 走 WiFi、WiFi SSH、管制域 CN |
| 蓝牙 | ✅ | HCI UART 驱动 + QCA 协议注册；出厂地址与对端 L2CAP 链路 8 包 0% 丢包；耳机 / A2DP 未测 |
| GPU（Adreno 740） | ✅ | `/odm/firmware` 里小米签名的 ZAP 让 PAS 初始化成功（`/vendor/firmware` 的高通测试签名返回 `-22`），GMU 正常，Phosh 用 FD740 渲染 |
| 音频 | ✅ | CS35L41 双功放 + WCD938x（`-audio`/`-audio2` 路径已并入当前变体）；两颗功放独立可听、桌面左右短音确认；麦克风与保护标定待验 |
| 相机 | 🚧 | CAMSS + `fuxi-camera-power`（`-camera`），待读传感器 ID |
| 蜂窝 / 通话 | 🚧 | IPA + MPSS + `tqftpserv`/`rmtfs`（`-modem`），待插 SIM |
| 传感器 | ⚠️ | `CONFIG_QCOM_FASTRPC` + `hexagonrpcd` 已接入，加速度/光线/距离/磁场/指南针有实测数据；旋转联动待验 |
| 省电 / 挂起 | 🚧 | `-sleep`：打开 `SUSPEND`、去掉 `cpuidle.off=1`，待上机；日常镜像仍不进深度空闲 |
| 调频 / 温控 | ✅ | 日常镜像默认 `FUXI_PM=1`：EPSS + schedutil、TSENS、PMIC 过温、LMh、CPU cooling、L3 互连，均已实机运行；GPU 温控已接入 120 Hz 镜像 |
| USB-C / DP | 🚧 | FSA4480 + ucsi/altmode-glink，DP alt mode；`-usbc`/`-desk` 待验 |
| 屏下指纹 | ❌ | TrustZone 内部实现，见 [docs/指纹调研.md](docs/指纹调研.md) |
| 振动马达 | ⏳ | 缺寄存器资料，暂未动 |

## M5 验收标准对照（目标：脱离电脑独立可用）

| # | 验收项 | 状态 |
|---|---|---|
| 1 | 拔掉 USB 线，按住 音量上 + 电源 开机进 Linux | ✅ 已验证 |
| 2 | 能看到电量与充电状态，插充电器会真正充电 | ✅ 状态可读，插充电器时 `Charging` 且电流为正（10-29 实测）；完整充电曲线与续航未单独验证 |
| 3 | WiFi 能连路由器上网，能通过 WiFi SSH 进手机 | ✅ 10-29 整机重启后自动连网：外网/HTTPS 走 WiFi、WiFi SSH、管制域 CN |
| 4 | 触摸可用的图形界面（Phosh）：解锁、开应用、屏幕键盘 | ✅ Phosh + GPU 渲染、竖屏键盘、中文输入与文本保存经用户确认；文件选择器待验收 |
| 5 | 普通重启仍回 Android，Android 侧不受影响 | ✅ 每轮回归验证 |

**结论：v0.3.0 起 M5 的基本可用形态已达成**（能脱离电脑进桌面、联网、输入文字），但仍是**实验机**：相机、蜂窝、指纹、省电/续航、A2DP 与部分细节验收未完成，见上面「当前状态」的待验收清单。

## 镜像（刷写前必读）

| 镜像 | 大小 | 内核构建 | 状态 |
|---|---|---|---|
| `images/recovery-linux.img` | 10,379,264 B | `#191`，2026-10-29 20:29 | ✅ **当前手机 `recovery_b` 上的镜像**（`screen120-blfix`）：原生显示 + GPU + 120 Hz + WiFi 管制域 + 背光（熄屏写亮度）修复；画面、触控、流畅度、熄屏唤醒均经用户/自动测试确认 |
| `images/candidates/abl-fuxi-daily-pm1.img` | 9,732,096 B | `#168`，2026-10-29 00:37 | ✅ 日常基线（CPU 调频/温控），10-29 多轮实机运行；不含原生显示/GPU |
| `images/candidates/abl-fuxi-audio-probe4.img` | 10,047,488 B | `#172`，2026-10-29 01:23 | ⚠️ 音频诊断镜像（两颗功放独立出声已实测），保留作回退 |
| `images/candidates/abl-fuxi-idle1.img` | 10,379,264 B | `#192`，2026-10-29 20:35 | 🚧 省电实验镜像（`-r120idle-audio-disp`，测试 CPU 深度空闲）：写入 `recovery_b` 后正在做 `cpuidle.off=1` 对照，结果未定 |

- `recovery-linux.img` = `abl-fuxi-screen120-blfix`，sha256 `8b59e3ed76c71719b320ae5739ed9cacbaea85d9d1cd535ea1b86a394ff63224`（完整清单见 [`SHA256SUMS`](SHA256SUMS)）；
- 各镜像的大小、内核版本、变体、构建记录与验证状态见 [`source/BUILD-INFO.md`](source/BUILD-INFO.md) 与 `source/build-records/*.build.json`；
- v0.2.0 发布过的候选镜像（`full3` / `wifi7` / `sleep1`）已从当前树移除，需要时从 tag `v0.2.0-dualboot-20261027` 取；
- 镜像起不来时**长按电源 20 秒即回 Android**（正常开机不碰 `recovery_b`，Android 不受影响）；刷写前先在电脑上留一份可用镜像的副本。

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

本仓库提供 `images/recovery-linux.img`（10,379,264 B，内核 + 内建 initramfs；sha256 见根目录 [`SHA256SUMS`](SHA256SUMS)）：

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

- 屏幕 / 桌面：默认进 Phosh 桌面（原生 MSM DSI 面板、GPU 渲染）。tty1 上仍保留 `simpledrm` + `fbcon` 文本控制台（16×32 字体）作兜底；实体按键（logind 已配置）与触摸均可用，屏幕键盘是 Stevia（`mobi.phosh.OSK.service`）。
- USB 串口：主线内核的 CDC ACM gadget（`0525:a4a7`）在主机上出现为串口设备，root 自动登录（`fuxi-serial-shell.service`）。仓库 `scripts/udev/52-fuxi-usb-port-power.rules` 允许脚本"软件拔插"USB 端口；串口默认按 `/dev/fuxi-acm` 命名，没有规则时设备名是 `/dev/ttyACM*`，`scripts/` 里默认按 `/dev/fuxi-acm` 写，做个符号链接或改脚本变量即可。initramfs 阶段有 **8 秒调试窗口**：在串口上 `touch /tmp/stay` 可让 initramfs 停住不自动启动 Ubuntu。
- USB 网络 / SSH：手机 `10.42.0.2`，主机侧为 NetworkManager 共享连接（`10.42.0.1`，自动 NAT）。`scripts/fuxi-ssh.sh` 封装了 ssh 调用（默认用作者本地 `work/ssh/fuxi_root` 私钥，公开环境下请换成你自己的密钥/密码）。
- 电量：`cat /sys/class/power_supply/qcom-battmgr-bat/uevent`（`CAPACITY`、`STATUS`、`VOLTAGE_NOW`、`TEMP` 等）。
- WiFi：10-29 验收时手机已能自动连网（配置存在手机上，仓库不含任何网络凭据）。连自己的网络：`nmcli dev wifi connect <名称> password <密码>`；镜像里无线管制域为 CN。
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

## 历史：v0.2.0 时期的「已构建、待上机」清单

这一节保留 v0.2.0（2026-10-27 白天）当时的待验清单与当时的变体名，作为历史对照；其中**显示/GPU、音频、调频温控、传感器**已在 v0.3.0 完成上机（见上文状态表），**USB-C/DP、基带、相机、省电/挂起、UFS 关机多轮回归**仍是待验项：

| 功能 | 镜像 / 变体 | 上机脚本 | 验证方式 |
|---|---|---|---|
| UFS 关机进 EDL 根因修复 | `wifi3` 起所有镜像（含本轮） | 手工多轮重启 | 关机/重启不再进 EDL；充分验证后再考虑 HS-G5 |
| 原生显示 + GPU | `-disp` / `-desk` / `-full`；当前 `-r120-audio-disp` | `scripts/fuxi-m6-display.sh` | 看屏幕：面板亮、DSC、60/90/120 Hz（`panel_xiaomi_fuxi.refresh=`）、亮度 |
| USB-C / DP 桌面 | `-usbc` / `-desk` | `scripts/fuxi-m6-usbc.sh` | 插拔 OTG/USB3、接 DP 显示器 |
| 音频（双扬声器 + 麦克风） | `-audio2` / 当前镜像 | `scripts/fuxi-m6-audio.sh` | 听声音、说话录音 |
| 基带 / 蜂窝 | `-modem` | `scripts/fuxi-m5-modem.sh` | 插 SIM 看注册、短信；`scripts/fuxi-modem-use.sh status` |
| 相机 | `-camera` | `scripts/fuxi-camera-probe.sh` | CAMSS 探测到传感器、读出 ID |
| 传感器 | 基础配置含 FastRPC | `scripts/fuxi-sensors.sh` | `hexagonrpcd` 起来、SSC 服务可访问 |
| 省电 / 挂起 | `-sleep` | `scripts/fuxi-m6-sleep.sh` | `s2idle` 挂起、CPU 深度空闲生效 |
| 调频 / 温控 | 日常镜像默认 `FUXI_PM=1` | `scripts/fuxi-m6-pm.sh`、`scripts/fuxi-health.sh` | cpufreq 频点可调、TSENS/过温保护生效 |

技术准备（细节见 [docs/目标-M5.md](docs/目标-M5.md) 与各调研文档）：

- **显示**：面板 `xiaomi m3 38 0c 0a`（三星 AMOLED、DSI 命令模式、DSC v1.1、1080×2400 @60/90/120 Hz，复位 GPIO133、TE GPIO86、三路电源 GPIO126/127/42，亮度 DCS 0x51 12 位）；驱动 `panel-xiaomi-fuxi`，上/下电序列由 `scripts/fuxi-panel-cmds.py` 从厂商 DTB 转换，参数存档 `device-info/panel-m3-38-0c-0a.dtsi`；故障定位过程见 [docs/显示驱动故障定位-20261029.md](docs/显示驱动故障定位-20261029.md)。
- **GPU**：Adreno 740，固件 `a740_sqe.fw`、`gmu_gen70200.bin`；签名 zap `a740_zap.mdt` **必须用 `/odm/firmware` 里小米签名的那份**（`/vendor/firmware` 的是高通测试签名，TZ 返回 `-22`，见 [docs/GPU初始化故障定位-20261029.md](docs/GPU初始化故障定位-20261029.md)）。
- **USB-C/DP**：FSA4480（i2c hub 2，`0x42`，方向脚 GPIO11）、ADSP 上 ucsi-glink + altmode-glink、DP alt mode；`-desk` = 原生显示 + GPU + USB-C + DP 输出。
- **音频**：CS35L41 功放 + WCD938x；功放 I2C 在 QUP2 SE0（GPIO0/1，不是 `sm8550.dtsi` 默认的 GPIO56/57），ALSA UCM2 已放进 `rootfs-overlay/`。
- **基带**：IPA + MPSS，固件指向 `qcom/sm8550/xiaomi/fuxi/{modem,modem_dtb,ipa_fws}.mdt`；启动顺序 `fuxi-firmware-devices`（bind IPA）→ `tqftpserv` → `rmtfs`（EFS 副本 `/var/lib/fuxi-rmtfs`，文件模式）→ ModemManager，drop-in 在 `rootfs-overlay/etc/systemd/system/rmtfs.service.d/`。
- **传感器**：`CONFIG_QCOM_FASTRPC` + `hexagonrpcd`。
- **省电**：主镜像遗留启动参数 `cpuidle.off=1`（M2 排障时关的），`-sleep` 变体去掉它并打开 `SUSPEND`/`PM_SLEEP`；PSCI 空闲参数主线与厂商 DTB 一致。
- **调频/温控**：主配置原先 `CPU_FREQ`、`THERMAL` 都没开，`FUXI_PM=1` 叠加 qcom-cpufreq-hw（EPSS）+ schedutil、TSENS、PMIC 过温、LMh、CPU 冷却、L3 互连调频。

## 构建与验证

完整构建信息（各镜像哈希与验证状态、内核配置、工具链、复现步骤）见 [`source/BUILD-INFO.md`](source/BUILD-INFO.md)。要点：

- 内核版本串 `Linux 7.3.0+`，基线 commit `5b0764a53235d3c77e1ed674e836e1b3fe1a4b1f`；发布镜像 `#191`（2026-10-29 20:29 构建并上机），候选镜像 `#168`（daily-pm1）、`#172`（audio-probe4）；
- `source/kernel.diff`：**18 个文件，+217/−8**；`source/linux-untracked/`：**27 个新文件**（按上游相对路径存放）；
- `source/kernel.config` 就是发布镜像 `#191` 实际使用的配置，逐镜像的构建记录在 `source/build-records/*.build.json`（含 boot_image / config / kernel / dtb 四组 sha256）；
- 变体构建由 `scripts/fuxi-build-abl.sh` 按 `FUXI_DTB=sm8550-xiaomi-fuxi-<变体>` / `FUXI_PM=1` 临时打开配置，构建完自动恢复主配置；
- 交付物（`images/`、`source/`、`rootfs-overlay/`、`device-info/`）的 sha256 见根目录 [`SHA256SUMS`](SHA256SUMS)。

### 构建镜像

```
# 1) 编内核 + DTB + 内建 initramfs，再打包成 boot.img v1
scripts/fuxi-build-abl.sh <名字>          # → work/kbuild/abl-fuxi-<名字>.img
#    变体：FUXI_DTB=sm8550-xiaomi-fuxi-disp|r120-audio-disp|usbc|audio|audio2|camera|modem|sleep|full
#    调频温控：FUXI_PM=1（日常镜像默认）

# 2) 不写分区，fastboot boot 临时启动测试（失败不影响 Android）
scripts/fuxi-run.sh work/kbuild/abl-fuxi-<名字>.img '<手机上要执行的命令>' …

# 3) 写 recovery_b 跑一轮完整回归（写入 → 重启 → SSH → 回 Android，产物进 evidence 式 summary）
scripts/fuxi-test-recovery.sh work/kbuild/abl-fuxi-<名字>.img

# 4) 重新上机后按执行链逐项跑（可断点续跑，进度存 work/state/after-reboot.done）
scripts/fuxi-after-reboot.sh --list    # 看待办；--from/--only 指定步骤
```

说明：
- 内嵌 DTB 由内核构建时 `incbin` 进镜像，但 boot.img 头部仍附**厂商 `fuxi.dtb` 诱饵**——该文件需从你自己的原厂 boot/recovery 镜像中提取，本仓库不附带厂商 DTB。
- 改了 initramfs 必须先删 `usr/initramfs_data.cpio*` 再 make，否则不会重新打包（`fuxi-build-abl.sh` 已自动处理）。
- 仓库里的脚本按作者本地工作区布局编写（`tools/platform-tools`、`work/`、`build/` 等），公开环境下请按自己的目录调整变量；`adb`/`fastboot` 直接用系统包也可。
- WiFi/蓝牙部署：`scripts/fuxi-m5-wifi-bt.sh`（固件从本机 Android modem 分区只读拉取，`scripts/fuxi-ath12k-board.py` 打包 `board-2.bin`）。

### 验证口径

- 从发出重启到 SSH 可用 **约 16 秒**（实测：07:25:29 `adb reboot recovery` → 07:25:45 SSH 可用；整个脚本 27 秒，含约 5 秒写分区与回读校验）；
- `systemd-analyze`（touch5 轮）：内核 **8.759 s** + 用户空间 **1.810 s** = **10.569 s**；更早 clean1–clean3 记录为 8.73–8.89 s + 1.96–2.46 s = 10.715–11.194 s；
- 镜像写入后回读 sha256 前 16 位比对；
- 原始记录在 `evidence/rtest-*/`（`summary.txt` 时间线 + `ssh.txt` 机器上的实际输出）；10-29 的记录在 `evidence/rtest-20261029-*`，同日的健康检查、GPU ZAP 修复、显示/120 Hz 交互、充电、蓝牙 L2CAP、温控压测日志在 `evidence/logs-20261029/`，构建日志在 `evidence/build-logs-20261029/`；
- 只读体检脚本 `scripts/fuxi-health.sh`：一条命令检查调频策略、热区、CPU cooling、Phosh、屏幕键盘、触摸设备、DRM 输出、电量、WiFi 与蓝牙（`--require-wifi` 要求已连网）。

### 源码与用户空间组成

| 路径 | 内容 |
|---|---|
| `source/kernel.config` | 主配置（`CONFIG_FUXI_FORCE_BUILTIN_DTB=y`、4K 页、内建 initramfs、simpledrm/fbcon、USB gadget、`ATH12K`、`TOUCHSCREEN_ST_FTM5`、`QCOM_FASTRPC`、`QCOM_IPA`、桌面选项等） |
| `source/kernel.diff` | 对主线内核的 18 处改动（+217/−8）：`FUXI_FORCE_BUILTIN_DTB`、`fuxi_early`、`fuxi.nosync`、面板/触摸/相机电源驱动、`ufs-qcom` 关机释放复位线、`qcom_battmgr` 属性号、`sc8280xp` 音频（含音量与 120 Hz 镜像所需改动）、各变体 DTS |
| `source/linux-untracked/` | 27 个新增文件：主 DTS + 各变体 `.dts`/`.dtsi`（含 120 Hz 音频显示变体 `sm8550-xiaomi-fuxi-r120-audio-disp.dts`）、`fuxi_dtb.S`、`fuxi_early.c`、`fuxi_font.h`、`panel-xiaomi-fuxi.c`、`st-ftm5.c`、`fuxi-camera-power.c`、面板与触摸的 dt-bindings |
| `source/initramfs/` | `init`（等待 USB 串口 8 秒 → `switch_root` 到 `sda33`，失败时屏幕报告 + 180 秒安全重启）与 `initramfs.list` |
| `source/build-records/` | 逐镜像的 `*.build.json`：构建时间、变体 DTB、是否叠加调频温控，以及 boot_image / config / kernel / dtb 的 sha256 |
| `source/dtb/` | 发布镜像实际内建的主线 DTB（`abl-fuxi-screen120-blfix.dtb`，编译产物存档） |
| `source/patches/` | `ufs-qcom-sm8550-g5.patch`（HS-G5，暂缓）与 `history/` 下 M5/M6 增量补丁（音频/相机/面板刷新率/DTS 拆分等） |
| `source/variants/kernel-config-desktop` | 加入桌面内核选项后的完整配置（对照用） |
| `rootfs-overlay/` | 根文件系统覆盖层：`fuxi-firmware-devices`（启动 ADSP、bind ath12k/蓝牙）、`rmtfs` drop-in、ALSA UCM2 |
| `device-info/` | 面板参数 `panel-m3-38-0c-0a.dtsi`、cmd-db 导出 `cmd-db-fuxi.txt` |

## 已知坑（都踩过）

- **内核 cmdline 不要加 `console=ttyGS0`**：`/dev/console` 会变成 USB 串口，主机没读时写满阻塞——启动卡几分钟、关机永远卡住。
- **UFS 关机进 EDL 的根因**：主线 `ufs-qcom` 在关机路径（`ufshcd_wl_shutdown` → `ufs_qcom_suspend`）里把 UFS 复位线拉住不放；启动 ROM 看到 UFS 仍在复位，读不到引导分区 → EDL。修复（加 `.shutdown`，关机时释放复位线）自 `wifi3` 起编入，本轮镜像同一源码树也含该修复，但**多轮关机/重启回归还没有系统记录**；重新启用 HS-G5 前先做这件事。
- **不要 unbind/rebind 半初始化的 ath12k**：会卡死整机。WiFi 固件在根文件系统里，initramfs 阶段 probe 会失败，必须由 `fuxi-firmware-devices.service` 在根文件系统挂好后再启动 ADSP/bind。
- **触摸驱动要注意上电时序**：电源未稳定时复位读 chip id 全是 0，probe 报 `-110: controller did not become ready`（touch1/touch2 两轮失败，touch3 起正常）。
- **电源键必须设 ignore**：`/etc/systemd/logind.conf.d/10-fuxi-powerkey.conf` 写 `HandlePowerKey=ignore`；还没有锁屏/休眠，否则按电源键会把正在跑的 Linux 直接关掉。
- **i2c8（功放）引脚不是默认值**：本机 QUP2 SE0 走 GPIO0/1（"mirb"），不是 `sm8550.dtsi` 默认的 GPIO56/57——GPIO57 是长焦相机 AVDD 开关。音频变体已按 GPIO0/1 改。
- **ABL 一次失败启动后，同一 fastboot 会话会拒绝后续镜像**：先 `fastboot reboot bootloader` 再继续。
- **USB 线材/接口**：出现 `error -71`、只能 full-speed 枚举时是信号问题，换线换口；主机侧曾记录 399 次过流。`scripts/udev/52-fuxi-usb-port-power.rules` 允许脚本"软件拔插"。
- **不要乱改 GPT 槽位属性**：曾用 `fastboot set_active a` 一次性把 50 多个分区（abl/tz/hyp/aop/modem/uefi…）的 active 位一起切换。`images/sde-gpt-slot-*.bin` 只是备份与对照。
- **`cpuidle.off=1` 是 M2 排障遗留**：主镜像因此不进深度空闲、不能挂起，耗电偏高；`-sleep` 变体才去掉。等 `-sleep` 验证通过再并入主配置。
- **诊断开关**：`fuxi.nosync=1` 会保留 bootloader 留下的电源/带宽/时钟投票（排查 sync_state 相关黑屏用），非必要不要开。
- **测试镜像起不来**：长按电源 20 秒回 Android；正常开机不碰 `recovery_b`，Android 不受影响。

## 恢复原厂

1. 用自己的原厂 `recovery_b` 备份写回 `recovery_b`（fastboot 或 Android 内 `dd` 均可）；
2. 确认 `boot_b` 等槽位分区未被改动（本方案只写 `recovery_b`）；
3. 不要尝试改槽位属性；恢复后正常开机即回到 Android。

历史记录：`boot_a` 已写回原厂（sha256 `c02adcce…`）；原厂 `recovery_b` 备份与设备原内容 sha256 一致（备份不随仓库发布，请使用你自己的备份）。更细的步骤见 [docs/双系统启动说明.md](docs/双系统启动说明.md)。

## 免责声明

- 解锁 bootloader 会清空数据、可能失去保修并触发安全机制；刷机、`dd` 写分区等操作**风险自负**，作者不对变砖、数据丢失或设备损坏负责。
- 本仓库不涉及任何破解、绕过安全启动或分发厂商固件/密钥；请使用**你自己拥有的设备与自己的原厂备份**。
- 项目处于实验阶段：v0.3.0 起显示、GPU、触摸、WiFi 连网、蓝牙链路、音频、输入法已上机可用，但**相机、蜂窝、指纹、省电/续航、A2DP 与部分细节仍未验证或明确不可用**，请勿把它当成可以完全替代 Android 的日常手机。
- Android 侧使用 LineageOS，请遵守其许可；内核代码遵循上游 GPL-2.0。

## 仓库结构

| 路径 | 内容 |
|---|---|
| `docs/` | [双系统启动说明](docs/双系统启动说明.md)（权威操作文档）、[目标-M5](docs/目标-M5.md)（M5/M6 进展与待验清单）、[手机日用目标-路线图-20261029](docs/手机日用目标-路线图-20261029.md)、10-29 的进展/基本功能修复/GPU 与显示故障定位/音频/传感器记录、音频/传感器/蜂窝/相机/指纹调研、历史交接与可行性调研 |
| `research/` | 上游驱动/启动链调研笔记 |
| `scripts/` | 构建、变体打包、刷写/启动测试、串口/SSH、WiFi/蓝牙/显示/音频/基带/相机/传感器/省电的上机脚本、槽位表解析、udev 规则 |
| `source/` | `kernel.config`、`kernel.diff`、`linux-untracked/`、`initramfs/`、`patches/`、`variants/`、`build-records/`、`dtb/`；构建信息见 `source/BUILD-INFO.md` |
| `rootfs-overlay/` | Ubuntu 根文件系统覆盖层（固件服务、rmtfs drop-in、ALSA UCM2） |
| `device-info/` | 面板参数、cmd-db 导出等设备常量 |
| `images/` | `recovery-linux.img`（当前 `recovery_b` 上的已验证镜像）、`candidates/`（日常基线与音频回退镜像）、GPT 槽位表备份 |
| `evidence/` | 实机验证记录（`rtest-*/summary.txt`、`ssh.txt`）、`rtest-20261029-*`、`logs-20261029/`（健康检查、GPU、显示/120 Hz、充电、蓝牙、温控压测）、构建日志 |
| `SHA256SUMS` | 镜像、源码、覆盖层与设备信息的全量 sha256 |
| `PROGRESS.md` | 时间线与验证证据表 |

> 历史上尝试过的 EDK2/UEFI 诊断引导路线与厂商内核构建流水线**已从当前树移除**（git 历史可查），当前树只保留 ABL 直接引导这一条可行路径。

## 下一步

1. **把 `screen120-blfix` 提升为日常基线**：补冷启动/长时间运行/多次关机的回归（含 UFS 关机路径），通过后替换 daily 镜像；
2. **显示与音频收尾**：物理亮度观感、90 Hz/动态刷新率、物理旋转联动；音频保护标定、完整声道定位、麦克风录音；
3. **基础桌面收尾**：文件选择器（portal）部署与验收，密码保存/辅助功能相关日志清理；
4. **蓝牙耳机 / A2DP**，以及 WiFi 小米标定兼容性；
5. **省电与续航**：`-sleep`（深度空闲 + 系统挂起）上机；当前在 `#192`（`idle1`）上做 `cpuidle.off=1` 的待机电流对照，结果出来再决定是否并入日常配置；
6. **相机 / 蜂窝**：从「已有实验实现」推进到可上机验证；
7. **USB-C / DP 桌面**、屏下指纹（主线短期不可行，见调研）。
