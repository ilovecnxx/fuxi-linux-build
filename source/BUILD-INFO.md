# 构建信息 — 2026-10-29 v0.3.0（M6 上机：原生显示 / GPU / 120 Hz / 音频 / WiFi）

本文件记录 v0.3.0 发布镜像与源码的来源、构建方法、验证状态。哈希清单见根目录 `SHA256SUMS`。

## 镜像一览

| 镜像 | 大小 | SHA-256 | 内核版本 | 变体 / 状态 |
|---|---|---|---|---|
| `images/recovery-linux.img` | 10,379,264 B | `8b59e3ed76c71719b320ae5739ed9cacbaea85d9d1cd535ea1b86a394ff63224` | `7.3.0+ #191`（2026-10-29 20:29 CST） | `-r120-audio-disp` + `FUXI_PM=1`。**当前手机 `recovery_b` 上的镜像**（`screen120-blfix`）：原生显示 + GPU（FD740）+ 120 Hz + 音频变体 + WiFi 管制域 CN + 熄屏亮度写入修复；画面、触控、流畅度、熄屏唤醒经确认 |
| `images/candidates/abl-fuxi-daily-pm1.img` | 9,732,096 B | `3b02fd600d16c41af37503495962046f8733eb014f297a3ac7e0de88c0bbced8` | `7.3.0+ #168`（2026-10-29 00:37 CST） | `-min` + `FUXI_PM=1`，日常基线：CPU 调频/温控、传感器与蓝牙部署；**不含原生显示/GPU**。10-29 白天多轮实机运行 |
| `images/candidates/abl-fuxi-audio-probe4.img` | 10,047,488 B | `d16eaab0ee4e5d4aaf0c06f65d000752e624cac2cee1def8103e525ae1efff16` | `7.3.0+ #172`（2026-10-29 01:23 CST） | `-audio`，音频诊断镜像：两颗 CS35L41 功放独立出声已实测，保留作回退 |
| `images/candidates/abl-fuxi-idle1.img` | 10,379,264 B | `4b614770e59455f7c0d2fbba471b1c55b092089495bd6ac5f92f86fc290a9c51` | `7.3.0+ #192`（2026-10-29 20:35 CST） | `-r120idle-audio-disp` + `FUXI_PM=1`，省电实验：测试 CPU 深度空闲（`cpuidle`），正在做 `cpuidle.off=1` 对照，结果未定 |

> 逐镜像的构建记录在 `source/build-records/abl-fuxi-*.build.json`（构建时间、变体 DTB、是否叠加调频温控，以及 boot_image / config / kernel / dtb 四组 sha256）。
> 发布镜像实际内建的主线 DTB 存档在 `source/dtb/abl-fuxi-screen120-blfix.dtb`。
> v0.2.0 发布过的候选镜像（`full3` / `wifi7` / `sleep1`）已从当前树移除，需要时从 tag `v0.2.0-dualboot-20261027` 取。

## 源码基线

| 项 | 值 |
|---|---|
| 上游 | `https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git` |
| commit | `5b0764a53235d3c77e1ed674e836e1b3fe1a4b1f` |
| 受跟踪文件改动 | `source/kernel.diff`：18 个文件，+218/−8 |
| 新增文件 | `source/linux-untracked/`：28 个（按上游相对路径存放） |
| 当前树对应的构建 | `#191`（`abl-fuxi-screen120-blfix`，2026-10-29 20:29） |

`source/kernel.diff` 要点：

- `arch/arm64/Kconfig` + `setup.c` + `kernel/Makefile`：`CONFIG_FUXI_FORCE_BUILTIN_DTB`（用内建 DTB 绕过 ABL 的 dtbo overlay）、`fuxi_dtb.o` / `fuxi_early.o`；
- `drivers/base/core.c`：`fuxi.nosync=1` 诊断参数；
- `drivers/gpu/drm/panel/*`：面板驱动 `panel-xiaomi-fuxi`（DSC、60/90/120 Hz、`panel_xiaomi_fuxi.refresh=` 参数）；
- `drivers/input/touchscreen/*`：触摸驱动 `st-ftm5`（上电时序修正）；
- `drivers/misc/*`：相机电源 `fuxi-camera-power`；
- `drivers/ufs/host/ufs-qcom.c`：关机时释放 UFS 复位线（修复重启进 EDL）；
- `drivers/power/supply/qcom_battmgr.c`：电量/充电属性号；
- `sound/soc/qcom/sc8280xp.c`、`sound/soc/soc-ops.c`：音频（WCD938x + CS35L41）及音量路径修正；
- 其余：各变体 DTS（`-min/-disp/-r120-audio-disp/-usbc/-audio/-audio2/-camera/-modem/-sleep/-desk/-full`）。

新增文件（`source/linux-untracked/`）包括：主/变体 DTS 与 dtsi、`fuxi_dtb.S`、`fuxi_early.c`、`fuxi_font.h`、`panel-xiaomi-fuxi.c`、`st-ftm5.c`、`fuxi-camera-power.c`，以及面板与触摸的 dt-bindings（`Documentation/devicetree/bindings/...`）。

## 内核配置

`source/kernel.config` 就是 `#191` 发布镜像实际使用的配置（`-r120-audio-disp` + `FUXI_PM=1`），已包含：`DRM_MSM`/DSI/面板、`ATH12K`、`TOUCHSCREEN_ST_FTM5`、`QCOM_FASTRPC`、`QCOM_IPA`、CPU 调频与温控（EPSS/schedutil、TSENS、PMIC 过温、LMh、CPU cooling）、桌面选项（squashfs/loop/FUSE/overlayfs/zram/exFAT/NTFS3/uinput/dm-crypt/TUN/veth/nftables 等）。

变体配置由构建脚本临时打开、构建完自动恢复主配置（`scripts/fuxi-build-abl.sh`）：

| 构建变量 | 说明 |
|---|---|
| `FUXI_DTB=sm8550-xiaomi-fuxi-disp` | 原生显示（DRM_MSM/DSI/面板/GPU） |
| `FUXI_DTB=sm8550-xiaomi-fuxi-r120-audio-disp` | 显示 + 120 Hz + 音频（**发布镜像用的变体**） |
| `FUXI_DTB=sm8550-xiaomi-fuxi-usbc` | USB-C（UCSI/FSA4480/dual-role/xHCI） |
| `FUXI_DTB=sm8550-xiaomi-fuxi-audio` / `-audio2` | 音频（ALSA/ASoC/AudioReach/CS35L41/WCD938x） |
| `FUXI_DTB=sm8550-xiaomi-fuxi-camera` | 相机（CCI/CAMSS/fuxi-camera-power） |
| `FUXI_DTB=sm8550-xiaomi-fuxi-modem` | 基带（IPA + MPSS） |
| `FUXI_DTB=sm8550-xiaomi-fuxi-sleep` | `SUSPEND` + `PM_SLEEP`，并自动 `FUXI_PM=1` |
| `FUXI_DTB=sm8550-xiaomi-fuxi-full` | 显示 + USB-C + 音频 + DP 全开 |
| `FUXI_PM=1` | 叠加调频/温控（EPSS/schedutil/TSENS/PMIC 过温/LMh/L3），日常镜像默认开启；`FUXI_PM=0` 用于对照 |

`source/variants/kernel-config-desktop` 是加入桌面内核选项后的完整配置，供对照。

## 复现步骤

1. 克隆上游 linux，checkout `5b0764a53235d3c77e1ed674e836e1b3fe1a4b1f`；
2. `cp source/kernel.config .config`，`git apply source/kernel.diff`；
3. 把 `source/linux-untracked/` 按同名路径拷回内核树；
4. initramfs：`source/initramfs/init` → `<build>/build/initramfs/init`（可执行），`initramfs.list` → `<build>/build/initramfs.list`，按需改 `CONFIG_INITRAMFS_SOURCE`；
5. `make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- olddefconfig`；
6. 准备厂商诱饵 DTB `fuxi.dtb`（从自有设备原厂 ROM 提取，801,847 B），放到 `scripts/fuxi-build-abl.sh` 的 `BAIT_DTB` 路径；
7. 构建：`scripts/fuxi-build-abl.sh <名字>`（可加 `FUXI_DTB=...` / `FUXI_PM=1`），产物在 `work/kbuild/abl-fuxi-<名字>.img`，并自动写出同名 `.config`、`.dtb`、`.build.json`。

> 厂商固件与 DTB 不随仓库分发。发布镜像内嵌的 801,847 B 厂商 DTB 只作为 ABL 引导诱饵（不含可执行代码）。
> GPU 的签名 ZAP 必须取自手机 `/odm/firmware`（小米签名）；`/vendor/firmware` 里的是高通测试签名，TrustZone 会返回 `-22`。

## 用户空间覆盖层

`rootfs-overlay/`（对应 Ubuntu 根文件系统 `sda33`）：

- `usr/local/sbin/fuxi-firmware-devices`：根文件系统就绪后启动 ADSP、bind ath12k、必要时 bind 蓝牙 serdev；
- `etc/systemd/system/fuxi-firmware-devices.service`、`etc/systemd/system/rmtfs.service.d/10-fuxi.conf`（带 MPSS 条件，无基带镜像跳过）；
- `usr/share/alsa/ucm2/Qualcomm/sm8550/Xiaomi-13/`：ALSA UCM2 配置；
- 文件选择器（`xdg-desktop-portal-gtk` 优先）候选配置与部署脚本。

## 验证状态

### 2026-10-27（v0.2.0，M5 硬件）

| 时间 | 镜像 | 结果 |
|---|---|---|
| 06:52 | touch3 | 触摸驱动 `st-ftm5` probe：chip 3640 / fw 0053，注册 input 设备 |
| 06:56 | touch5 | 完整回归：4 个输入设备齐全、`systemd-analyze` 10.569 s、SSH 可用 |
| 07:05 | mem1 | 9 GB tmpfs 写入 + 两次 md5 一致，dmesg 无异常 |
| 07:08 / 07:13 | adsp1 / adsp2 | ADSP remoteproc 启动、battmgr 电量属性可读 |
| 07:25 | wifi1 | PCIe0 枚举出 01:00.0、蓝牙 HCI 注册；SSH 可用 |

### 2026-10-28 ~ 10-29（v0.3.0，M6 上机）

| 时间 | 镜像 | 结果 |
|---|---|---|
| 10-29 00:37 | daily-pm1（`#168`） | 日常基线：CPU 调频/温控实机运行，`scripts/fuxi-health.sh` 体检通过 |
| 10-29 14:09 | screen-audio8（`#184`） | 原生 DSI 首次出数字画面（1080×2400），但 Adreno ZAP `-22`、桌面仍软件渲染 |
| 10-29 17:49 | screen-audio9-host-bindingfix（`#187`） | 换 `/odm/firmware` 签名 ZAP 后 GPU 初始化成功，Phosh 切 FD740；用户确认画面正常、触控准确、明显流畅 |
| 10-29 20:04 | screen120-gputherm（`#189`） | 120 Hz + GPU 温控；用户确认更顺滑、画面正常 |
| 10-29 20:12 | screen120-regcn（`#190`） | 补 WiFi 管制域 CN；整机重启后自动连网、外网/HTTPS 走 WiFi、WiFi SSH 通过；音频、蓝牙 L2CAP、充电读数、温控压测均有当日记录 |
| 10-29 20:29 | **screen120-blfix（`#191`）** | 面板背光修复（熄屏时写亮度不再报错）；3 轮熄屏/唤醒、自动亮度、GPU 满载 3 分钟约 65.9 °C 通过；`fuxi-health.sh --require-wifi --require-sensors` 失败 0 |

原始记录：`evidence/rtest-20261027-*/`、`evidence/rtest-20261029-*/`、`evidence/logs-20261029/`、`evidence/build-logs-20261027pm/`、`evidence/build-logs-20261029/`。

## 已知限制

- 相机（CAMSS）、蜂窝（IPA + MPSS）、USB-C/DP 桌面、省电/挂起（`-sleep`）仍只做到构建，未上机验收。
- 音频保护标定、完整声道定位/音质、麦克风录音未验证。
- 物理亮度观感、90 Hz/动态刷新率、物理旋转与桌面联动未验证；文件选择器（portal）未部署验收；蓝牙耳机 / A2DP 未测。
- 日常镜像仍不启用深度空闲与系统挂起，续航不达目标。
- WiFi 使用上游固件 + 参考板标定，小米标定的兼容性仍待解决。
- 屏下指纹走 TrustZone，主线短期不可行（见 `docs/指纹调研.md`）。
- UFS HS-G5 补丁暂缓（`source/patches/ufs-qcom-sm8550-g5.patch`），默认 G4；关机复位线修复已含但多轮回归未整理。
- `CONFIG_INITRAMFS_SOURCE` 记录的是构建机绝对路径，复现时必须修改。
