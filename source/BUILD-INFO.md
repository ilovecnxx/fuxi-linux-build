# 构建信息 — 2026-10-27 v0.2.0（M5/M6 更新）

本文件记录 v0.2.0 发布镜像与源码的来源、构建方法、验证状态。哈希清单见根目录 `SHA256SUMS`。

## 镜像一览

| 镜像 | 大小 | SHA-256 | 内核版本 | 变体 / 状态 |
|---|---|---|---|---|
| `images/recovery-linux.img` | 8,691,712 B | `05f088e0210a7f8f451a3c43b760893bdd2b12624303eff46da8bc3cd395d80a` | `#113 SMP PREEMPT Tue Oct 27 07:23:58 CST 2026` | 基础配置（`-min` DTB）。**最后在真机完整验证**（2026-10-27 07:25：SSH 可用） |
| `images/candidates/abl-fuxi-full3.img` | 10,485,760 B | `7a130e771448adaff9a32e13f933336dc2de94a2df4ca64c2b564723f7e5ac4e` | `#146 SMP PREEMPT Tue Oct 27 11:44:38 CST 2026` | `-full`（原生显示 + GPU + USB-C/DP + 音频）。**已构建、待上机验证** |
| `images/candidates/abl-fuxi-wifi7.img` | 9,748,480 B | `9fff5cfca6039f7171fd6a3bf7b69729197079314c0296f1ed8eaf29dbadf61b` | `#148 SMP PREEMPT Tue Oct 27 11:59:12 CST 2026` | 基础配置，**与 `source/` 当前树对应的最新构建**。待上机验证 |
| `images/candidates/abl-fuxi-sleep1.img` | 9,748,480 B | `abbaec17bffa881ff70b1c06a0da95a7b5c052d78ae28d12911d9915d6abd9a5` | `#147 SMP PREEMPT Tue Oct 27 11:54:19 CST 2026` | `-sleep`（SUSPEND + 调频温控，去掉 `cpuidle.off=1`）。待上机验证 |

> 设备在 2026-10-27 13:16 后离线；`full3` / `wifi7` / `sleep1` 与下午的显示/音频/基带/相机/传感器/省电功能只做到「构建成功」，**没有实机验收**。
> `recovery-linux.img`（wifi1）是最后一个完成完整回归的镜像。

## 源码基线

| 项 | 值 |
|---|---|
| 上游 | `https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git` |
| commit | `5b0764a53235d3c77e1ed674e836e1b3fe1a4b1f` |
| 受跟踪文件改动 | `source/kernel.diff`：13 个文件，+165/−7 |
| 新增文件 | `source/linux-untracked/`：23 个（按上游相对路径存放） |
| 当前树对应的构建 | `#148`（`abl-fuxi-wifi7`，2026-10-27 11:59） |

`source/kernel.diff` 要点：

- `arch/arm64/Kconfig` + `setup.c` + `kernel/Makefile`：`CONFIG_FUXI_FORCE_BUILTIN_DTB`（用内建 DTB 绕过 ABL 的 dtbo overlay）、`fuxi_dtb.o` / `fuxi_early.o`；
- `drivers/base/core.c`：`fuxi.nosync=1` 诊断参数；
- `drivers/gpu/drm/panel/*`：面板驱动 `panel-xiaomi-fuxi`（DSC、60/90/120 Hz）；
- `drivers/input/touchscreen/*`：触摸驱动 `st-ftm5`；
- `drivers/misc/*`：相机电源 `fuxi-camera-power`；
- `drivers/ufs/host/ufs-qcom.c`：关机时释放 UFS 复位线（修复重启进 EDL）；
- `drivers/power/supply/qcom_battmgr.c`：电量/充电属性号；
- `sound/soc/qcom/sc8280xp.c`：音频（WCD938x + CS35L41）；
- 其余：各变体 DTS（`-disp/-usbc/-audio/-audio2/-camera/-modem/-sleep/-desk/-full`）。

新增文件（`source/linux-untracked/`）包括：主/变体 DTS 与 dtsi（12 个）、`fuxi_dtb.S`、`fuxi_early.c`、`fuxi_font.h`、`panel-xiaomi-fuxi.c`、`st-ftm5.c`、`fuxi-camera-power.c`。

## 内核配置

`source/kernel.config` 是主配置（`-min` 基础镜像），已包含：`QCOM_FASTRPC`、`QCOM_IPA`、`ATH12K`、`TOUCHSCREEN_ST_FTM5`、桌面选项（squashfs/loop/FUSE/overlayfs/zram/exFAT/NTFS3/uinput/dm-crypt/TUN/veth/nftables 等）。

变体配置由构建脚本临时打开、构建完自动恢复主配置（`scripts/fuxi-build-abl.sh`）：

| 构建变量 | 说明 |
|---|---|
| `FUXI_DTB=sm8550-xiaomi-fuxi-disp` | 原生显示（DRM_MSM/DSI/面板/GPU） |
| `FUXI_DTB=sm8550-xiaomi-fuxi-usbc` | USB-C（UCSI/FSA4480/dual-role/xHCI） |
| `FUXI_DTB=sm8550-xiaomi-fuxi-audio` / `-audio2` | 音频（ALSA/ASoC/AudioReach/CS35L41/WCD938x） |
| `FUXI_DTB=sm8550-xiaomi-fuxi-camera` | 相机（CCI/CAMSS/fuxi-camera-power） |
| `FUXI_DTB=sm8550-xiaomi-fuxi-modem` | 基带（IPA + MPSS） |
| `FUXI_DTB=sm8550-xiaomi-fuxi-sleep` | `SUSPEND` + `PM_SLEEP`，并自动 `FUXI_PM=1` |
| `FUXI_DTB=sm8550-xiaomi-fuxi-full` | 显示 + USB-C + 音频 + DP 全开 |
| `FUXI_PM=1` | 叠加调频/温控（EPSS/schedutil/TSENS/PMIC 过温/LMh/L3） |

`source/variants/kernel-config-desktop` 是 09:15 加入桌面内核选项后的完整配置，供对照。

## 复现步骤

1. 克隆上游 linux，checkout `5b0764a53235d3c77e1ed674e836e1b3fe1a4b1f`；
2. `cp source/kernel.config .config`，`git apply source/kernel.diff`；
3. 把 `source/linux-untracked/` 按同名路径拷回内核树；
4. initramfs：`source/initramfs/init` → `<build>/build/initramfs/init`（可执行），`initramfs.list` → `<build>/build/initramfs.list`，按需改 `CONFIG_INITRAMFS_SOURCE`；
5. `make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- olddefconfig`；
6. 准备厂商诱饵 DTB `fuxi.dtb`（从自有设备原厂 ROM 提取，801,847 B），放到 `scripts/fuxi-build-abl.sh` 的 `BAIT_DTB` 路径；
7. 构建：`scripts/fuxi-build-abl.sh <名字>`（可加 `FUXI_DTB=...` / `FUXI_PM=1`），产物在 `work/kbuild/abl-fuxi-<名字>.img`。

> 厂商固件与 DTB 不随仓库分发。发布镜像内嵌的 801,847 B 厂商 DTB 只作为 ABL 引导诱饵（不含可执行代码）。

## 用户空间覆盖层

`rootfs-overlay/`（对应 Ubuntu 根文件系统 `sda33`）：

- `usr/local/sbin/fuxi-firmware-devices`：根文件系统就绪后启动 ADSP、bind ath12k、必要时 bind 蓝牙 serdev；
- `etc/systemd/system/fuxi-firmware-devices.service`、`etc/systemd/system/rmtfs.service.d/10-fuxi.conf`；
- `usr/share/alsa/ucm2/Qualcomm/sm8550/Xiaomi-13/`：ALSA UCM2 配置。

## 验证状态（2026-10-27）

| 时间 | 镜像 | 结果 |
|---|---|---|
| 06:52 | touch3 | 触摸驱动 `st-ftm5` probe：chip 3640 / fw 0053，注册 input 设备 |
| 06:56 | — | 完整回归：SSH 可用，返回 Android |
| 07:05 | — | 完整回归：SSH 可用，返回 Android |
| 07:08 / 07:13 | adsp1 / adsp2 | ADSP remoteproc 启动、battmgr 电量属性可读 |
| 07:25 | **wifi1** | PCIe0 枚举出 01:00.0、蓝牙 HCI 注册（WCN7850 固件/ath12k 启动记录见 docs/目标-M5.md）；SSH 可用 |
| 13:16 | — | 设备离线（等待 Android 回归），之后只构建未验证 |

原始记录：`evidence/rtest-20261027-*/`、`evidence/build-logs-20261027pm/`。

## 已知限制

- 触摸/按键/电量已可用，但**没有图形界面**（Phosh 尚未安装验证）；显示仍是 simpledrm + fbcon。
- WiFi/蓝牙硬件已就绪，**尚未连网/配对**（需要用户提供 WiFi 账号；蓝牙固件与配对未验证）。
- 原生显示/GPU、USB-C/DP、音频、基带/通话、相机、传感器、省电：已构建，等设备回归后逐个验收。
- 屏下指纹走 TrustZone，主线短期不可行（见 `docs/指纹调研.md`）。
- UFS HS-G5 补丁暂缓（`source/patches/ufs-qcom-sm8550-g5.patch`），默认 G4。
- `CONFIG_INITRAMFS_SOURCE` 记录的是构建机绝对路径，复现时必须修改。
