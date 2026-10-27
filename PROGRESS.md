# 进展与验证记录

本文件记录从设备摸底到「Android + 主线 Linux 双系统 + M5/M6」的时间线，以及可复核的实机验证证据。上手操作请看 [README.md](README.md)，权威操作步骤见 [docs/双系统启动说明.md](docs/双系统启动说明.md)，M5/M6 详细进展见 [docs/目标-M5.md](docs/目标-M5.md)。

**当前版本 `v0.2.0-dualboot-20261027`。** 本版必须区分两类状态：✅ 在真实设备上跑过并留下记录；🚧 只在电脑上构建成功、没有上机验收（设备 2026-10-27 13:16 后离线）。

## 时间线

### 2026-10-24 — 设备摸底与完整备份

- 确认设备状态：小米 13（fuxi / SM8550），bootloader 已解锁，A/B 动态分区，4K 页；LineageOS 24.0 位于槽位 `b`。
- 备份原厂分区（`recovery_b`、`boot_b` 等），并导出 sde（LUN4）GPT 槽位表：
  `images/sde-gpt-slot-a.bin`、`images/sde-gpt-slot-b-android.bin`（可用 `scripts/fuxi-gpt-slots.py` 解析、对照槽位属性）。
- 方案结论：**不改动 Android 的 `boot_b`，只借 `recovery_b` 作为 Linux 入口**，是风险最低的双系统路径；失败时正常开机仍回 Android。

### 2026-10-25 ~ 10-26 — EDK2 / UEFI 诊断引导路线（已放弃）

- 自制 EDK2 UEFI 能启动并拿到 GOP 帧缓冲，但在把控制权交给主线内核时反复失败（黑屏、挂起）；kexec 路线也不可靠。
- 期间解决了一批内核早期问题（帧缓冲在 linear map 内、initramfs 缺目录、早期屏幕 console 等）。**2026-10-27 00:20，主线内核首次进入用户空间（M1）**。
- 该路线相关的 UEFI 固件、内嵌内核方案已从当前树移除（git 历史可查）；当前树只保留 ABL 直接引导。

### 2026-10-27 凌晨 — 改为 ABL 直接引导 `recovery_b`，双系统成功（v0.1.0）

- **03:xx–04:50**：用「立即 PSCI 复位」的最小桩内核验证 ABL 的 DTB 行为——镜像附**主线 DTB** 时卡死；附**厂商 `fuxi.dtb`** 时正常跳转（19 秒回 Android）。据此确定方案：镜像里放厂商 DTB 当「诱饵」，内核用 `CONFIG_FUXI_FORCE_BUILTIN_DTB=y` 忽略 ABL 的 DTB、改用内建主线 DTB。
- **04:30–05:31**：`abl-fuxi-v1` … `v5` 迭代，跑通 `recovery_b` → 主线内核 → 内建 initramfs → `switch_root` 到 `sda33` 上的 Ubuntu（systemd）。
- **06:03–06:11**：clean1 / clean2 / clean3 连续三组完整回归（写 `recovery_b` → 回读校验 → 重启进 Linux → SSH → 回 Android），全部通过，启动耗时稳定。
- **06:15 / 06:19**：clean4 / clean5 用于 `sync_state` 诊断（`fuxi.nosync` 调试参数），系统仍正常进入用户空间；06:19 构建的 clean5 定为 v0.1.0 发布镜像。
- **06:21**：发布树整理并冻结为 `v0.1.0-dualboot-20261027`。

### 2026-10-27 上午 — M5：触摸 / 按键 / 电量 / WiFi 蓝牙硬件（真机验证）

每一轮都是真实设备回归：写 `recovery_b` → 回读 sha256 校验 → `adb reboot recovery` → SSH → 执行命令 → 回 Android（或留在 Ubuntu）。

- **06:30 按键**（keys2）：`pmic_pwrkey`、`pmic_resin`、`gpio-keys` 三个输入设备全部注册；写入 `/etc/systemd/logind.conf.d/10-fuxi-powerkey.conf` 把电源键设为 `HandlePowerKey=ignore`（还没有锁屏/休眠，避免误关机），`systemctl restart systemd-logind` 生效。
- **06:47–06:56 触摸**（touch1–touch5）：第一版驱动 probe 报 `-110: controller did not become ready`（上电时序问题），touch2 读回 chip id 全 0；修正上电/复位顺序后 **touch3 probe 成功**：`st-ftm5 spi0.0: chip 3640 fw 0053 cfg 0042 panel 2399x1079`，注册 `ST FTM5 Touchscreen`；touch5 确认 4 个输入设备齐全、`systemd-analyze` = 8.759 s + 1.810 s = 10.569 s、`systemctl is-system-running` = `running`。
- **07:05 内存压测**（mem1）：`Memory: 11156704K/12249724K available`；tmpfs 写 9 GB 后两次 md5 一致（`3ced23ea87d1`），dmesg 中 Oops/SError/异常计数 0。
- **07:08 / 07:13 电量**（adsp1 / adsp2）：adsp1 时 ADSP 固件尚未加载（initramfs 阶段 probe 太早，`Direct firmware load ... adsp.mdt failed with error -2`）；adsp2 加 `fuxi-remoteproc.service`（根文件系统就绪后启动 ADSP）后 `remoteproc0` = `running`，`qcom-battmgr-bat` 属性可读（`STATUS=Charging`、`CAPACITY`、`VOLTAGE_NOW=4352000`、`TEMP=302`、`STATE_OF_HEALTH=78`、`MODEL_NAME=M3_4500mah_67w` 等）。
- **07:24–07:25 WiFi / 蓝牙硬件**（wifi1）：无线固件全部取自本机 Android modem 分区（`amss.bin`/`m3.bin`/`regdb.bin`，用 `scripts/fuxi-ath12k-board.py` 打包 `board-2.bin`）；PCIe0 设备枚举出 `0000:01:00.0`、蓝牙 HCI UART/QCA 注册；WCN7850 固件与 `ath12k` 启动的记录见 `docs/目标-M5.md`（随树 `ssh.txt` 的 dmesg 被 `head` 截断，未保留该段输出）。**没有连网**（需要用户提供 WiFi 名称/密码），蓝牙配对未测。此轮镜像 `wifi1` 是 v0.2.0 的发布镜像。

### 2026-10-27 下午 — M6：显示 / 音频 / 基带 / 相机 / 传感器 / 省电（仅构建，未上机）

设备在 07:25 最后一轮实测后没有回到 Android，07:40 起自动脚本反复等 Android 回归（07:40/07:45/07:56/08:21 均超时），09:16 的后台任务一直等到 **13:16 超时，判定设备离线**。此后所有工作只做到「构建成功」，`evidence/build-logs-20261027pm/` 有对应日志：

- **07:40–08:30**：定位并修复 **UFS 关机进 EDL** 的根因（主线 `ufs-qcom` 关机路径拉住 UFS 复位线；给平台驱动加 `.shutdown` 释放），`wifi3` 起镜像包含该修复——**该修复本身还没在设备上验证过**（发布镜像 `wifi1` 更早，不含此修复）。
- **08:09–08:57**：原生显示准备（面板 `xiaomi m3 38 0c 0a` 参数、`panel-xiaomi-fuxi` 驱动、上/下电序列转换、`-disp` 变体）、GPU 固件；基带准备（`-modem`：IPA + MPSS、`tqftpserv`/`rmtfs`）；USB-C/DP（`-usbc`/`-desk`）；蓝牙修正（`uart14` 在 `qupv3_id_1` 下，之前的主 DTS 没开这个 QUP）。
- **08:56**：DTS 拆成 dtsi 片段（`-disp/-modem/-audio/-audio2/-usbc` 等），变体 `.dts` 只做 include 组合（拆分前后 dtb 逐字节一致）；新增 `-full` 全功能变体。
- **09:10–09:22**：发现主配置 `CPU_FREQ`、`THERMAL` 都没开（CPU 停在引导程序留下的频率），加 `FUXI_PM=1` 调频温控构建（`-pm`）；桌面/日常内核选项补进主配置（squashfs/loop/FUSE/overlayfs/zram/exFAT/NTFS3/uinput/dm-crypt/TUN/veth/nftables 等）。
- **10:10**：修正 i2c8 引脚错误——本机 QUP2 SE0（功放 I2C）走 GPIO0/1，不是 `sm8550.dtsi` 默认的 GPIO56/57（GPIO57 是长焦 AVDD）；audio1/audio2/full2 重编。
- **10:12–10:13 音频**（audio1/audio2）：CS35L41 功放 + WCD938x 编解码，ALSA UCM2 放进 `rootfs-overlay/`。
- **11:36–11:46 相机与面板刷新率**：`-camera`（CAMSS + `fuxi-camera-power` 测试驱动）、面板 `panel_xiaomi_fuxi.refresh=60|90|120`（厂商三个 timing 的上电序列只差 3 条命令）；`disp4`/`desk2`/`full3`。
- **11:54–11:59 省电与最新基础镜像**（sleep1 / wifi7）：`-sleep` 去掉 `cpuidle.off=1` 并打开 `SUSPEND`/`PM_SLEEP`（PSCI 空闲参数与厂商 DTB 一致）；`wifi7`（`#148`）是与当前 `source/` 树对应的最新构建。
- **13:16**：自动执行链等待 Android 超时，确认设备离线；此后未再上机。

### 2026-10-27 17:xx — 发布 `v0.2.0-dualboot-20261027`

- 发布树：`docs/`（新增 目标-M5 与音频/传感器/蜂窝/相机/指纹调研，更新双系统启动说明）、`scripts/`（新增 20+ 个 M5/M6 脚本）、`rootfs-overlay/`、`source/`（kernel.diff 13 文件 +165/−7、23 个新文件、增量补丁、变体配置）、`device-info/`、`evidence/`（新增六轮实测 + 下午构建日志）。
- 镜像：`images/recovery-linux.img` = 最后真机验证的 `wifi1`；`images/candidates/` = `full3`/`wifi7`/`sleep1`（已构建、待上机验证）。
- 旧 `v0.1.0-dualboot-20261027` 的 Release 保留。

## 验证证据

### 双系统启动：clean1 – clean5（2026-10-27 凌晨，v0.1.0）

| # | 时间 | 镜像 | sha256（前 16 位） | 结果 | systemd-analyze（kernel + userspace = total） |
|---|---|---|---|---|---|
| 1 | 06:07:23 | clean1 | `b724f94712dbd60c` | 写入并校验；+24 s SSH 可用；+41 s 回 Android | 8.887 + 2.159 = **11.047 s** |
| 2 | 06:09:39 | clean2 | `11bb7076fa544ab2` | 写入并校验；+25 s SSH 可用；+43 s 回 Android | 8.752 + 1.963 = **10.715 s** |
| 3 | 06:11:26 | clean3 | `2583e5fa198105c9` | 写入并校验；+25 s SSH 可用；留在 Ubuntu（`FUXI_KEEP=1`） | 8.730 + 2.463 = **11.194 s** |
| 4 | 06:15:55 | clean4 | `bdae068f2f26c169` | 写入并校验；+60 s SSH 可用；留在 Ubuntu（诊断构建） | 未采集 |
| 5 | 06:19:31 | clean5（v0.1.0 发布镜像） | `b48614f4a71a8364` | 写入并校验；+53 s SSH 可用；`systemctl is-system-running` = `running`；留在 Ubuntu | 未采集 |

### M5 真机验证：touch1 – wifi1（2026-10-27 上午，v0.2.0）

| # | 时间 | 镜像 | sha256（前 16 位） | 结果 |
|---|---|---|---|---|
| 1 | 06:52:32 | touch3 | `41f106f8eefa0cfa` | 写入并校验；+28 s SSH 可用；**触摸驱动 probe 成功**：`chip 3640 fw 0053 cfg 0042 panel 2399x1079`，注册 `ST FTM5 Touchscreen`；留在 Ubuntu |
| 2 | 06:56:50 | touch5 | `728f841ff2a8156a` | 写入并校验；+28 s SSH 可用；4 个输入设备（`pmic_pwrkey`/`pmic_resin`/`ST FTM5 Touchscreen`/`gpio-keys`）；`systemd-analyze` = 8.759 + 1.810 = **10.569 s**；`is-system-running` = `running`；+45 s 回 Android |
| 3 | 07:05:21 | mem1 | `1023003ca4bba9a3` | 写入并校验；+24 s SSH 可用；9 GB tmpfs 写入 + 两次 md5 一致（`3ced23ea87d1`）；内存异常计数 0；+94 s 回 Android |
| 4 | 07:08:38 | adsp1 | `c9b812fe346ee6db` | 写入并校验；+24 s SSH 可用；ADSP 固件未加载（`adsp.mdt` -2，initramfs 阶段 probe 太早）→ 定位为「根文件系统就绪后再启动 ADSP」；留在 Ubuntu |
| 5 | 07:13:32 | adsp2 | `cb6468a884002101` | 写入并校验；+29 s SSH 可用；`fuxi-remoteproc.service` 启动 ADSP 后 `remoteproc0` = `running`；`qcom-battmgr-bat` 属性可读（`STATUS=Charging`、`CAPACITY`、`VOLTAGE_NOW`、`TEMP` 等）；留在 Ubuntu |
| 6 | 07:25:18 | **wifi1（v0.2.0 发布镜像）** | `05f088e0210a7f8f` | 写入并校验；+27 s SSH 可用（+5 s 写入、+11 s reboot、**reboot→SSH 约 16 s**）；PCIe0 枚举出 `0000:01:00.0`、蓝牙 HCI UART/QCA 注册（随树 `ssh.txt` 只截取到这两段；WCN7850 固件与 `ath12k` 启动的记录见 `docs/目标-M5.md`）；留在 Ubuntu |

说明：

- 「写入并校验」指镜像 `dd` 进 `recovery_b` 后回读 16 位 sha256 与源文件一致；每一轮都是真实设备回归。
- 「+N s」是测试脚本从开始到「Ubuntu SSH 可用」的墙钟秒数（含写分区与重启），**不是**内核启动耗时；内核/用户空间耗时以目标机 `systemd-analyze` 为准。
- touch1/touch2 未列入（probe 失败：`-110 controller did not become ready` / chip id 全 0，失败记录在本地日志、未随仓库发布），正是 touch3 修好上电时序的依据。
- **没有连网/配对**：WiFi 需要用户提供 SSID/密码，蓝牙配对未做；电量只验证了「状态可读」，插充电器的完整充电流程未单独验证。
- 原始记录：`evidence/rtest-20261027-065232/`、`-065650/`、`-070521/`、`-070838/`、`-071332/`、`-072518/`（各含 `summary.txt` 时间线与 `ssh.txt` 的机器实际输出）；v0.1.0 的 clean1–clean5 在 `evidence/rtest-20261027-06*/`。

### 发布镜像（v0.2.0）

| 项 | 值 |
|---|---|
| 文件 | `images/recovery-linux.img` |
| 大小 | 8,691,712 B |
| sha256 | `05f088e0210a7f8f451a3c43b760893bdd2b12624303eff46da8bc3cd395d80a`（根 [SHA256SUMS](SHA256SUMS)） |
| 内核 | `Linux 7.3.0+` `#113 SMP PREEMPT Tue Oct 27 07:23:58 CST 2026` |
| 内核基线 | commit `5b0764a53235d3c77e1ed674e836e1b3fe1a4b1f` |
| 构建时间 | 2026-10-27 07:23 |
| 实测 | 07:25:18 一轮完整回归通过（写入校验 → reboot → SSH 可用约 16 s，留在 Ubuntu） |
| 来源 | `abl-fuxi-wifi1`（基础 `-min` 配置）；**不含**下午构建的显示/音频/基带/相机/传感器/省电改动与 UFS 关机修复 |
| 内部结构 / 源码 / 复现 | 见 [`source/BUILD-INFO.md`](source/BUILD-INFO.md) |

### 候选镜像（已构建、待上机验证）

| 文件 | 大小 | 内核构建 | 变体 | 状态 |
|---|---|---|---|---|
| `images/candidates/abl-fuxi-full3.img` | 10,485,760 B | `#146`，11:44 | `-full`（显示 + GPU + USB-C/DP + 音频） | 🚧 未上机 |
| `images/candidates/abl-fuxi-wifi7.img` | 9,748,480 B | `#148`，11:59 | 基础配置，与当前 `source/` 树对应 | 🚧 未上机 |
| `images/candidates/abl-fuxi-sleep1.img` | 9,748,480 B | `#147`，11:54 | `-sleep`（SUSPEND + 调频温控，去 `cpuidle.off=1`） | 🚧 未上机 |

> 三个候选镜像只验证到「构建成功、boot header 正常、内核段可解压」；**没有任何一轮实机启动**。上机前请先看 [README.md](README.md) 的「已验证镜像与候选镜像」一节，起不来时长按电源 20 秒回 Android。

### 里程碑摘要

- **M1（主线内核进入用户空间）**：2026-10-27 00:20，`/init` 正常运行、串口 shell 可用；当时走的是 EDK2 UEFI 诊断路线，相关代码已从当前树移除（历史见 git 记录）。
- **M3（UFS 根文件系统 + 用户空间）**：`sda33` 上的 Ubuntu 26.10 正常启动，`systemd` 进入 `running`，SSH over USB 可用。
- **M4（双系统闭环）**：自 clean1 起，每轮测试都能在 Android → Linux → Android 之间完整闭环；日常开机不碰 `recovery_b`，因此 Android 始终可用。
- **M5（脱离电脑独立可用）**：部分达成——独立开机 ✅、按键/触摸/电量状态 ✅、普通重启回 Android ✅；**WiFi 连网与 Phosh 图形界面未完成**。
- **M6（整机功能）**：显示/GPU、USB-C/DP、音频、基带、相机、传感器、省电、调频温控**已完成构建**，等设备回归后逐项验收。

## 已知未完成（截至 2026-10-27 发布）

- **未在设备上验证**（构建成功）：原生显示 + GPU、USB-C/DP 桌面、音频、基带/蜂窝、相机、传感器、省电/挂起、调频温控、`full3` 日常镜像、`wifi7` 最新基础镜像。
- **UFS 关机进 EDL 修复**：根因已定位、修复已编进 `wifi3` 起的镜像，但**没有设备验证记录**；发布镜像 `wifi1` 不含。HS-G5 仍暂缓（`source/patches/ufs-qcom-sm8550-g5.patch`）。
- **WiFi/蓝牙**：硬件就绪但未连网（需用户 SSID/密码），蓝牙固件与配对未验证。
- **图形界面**：Phosh 未开始；触摸驱动可用但当前只有 tty。
- **显示**：仍以 simpledrm + fbcon 为主，原生面板/GPU 驱动只是构建好了。
- **屏下指纹**：TrustZone 内部实现，主线短期不可行，见 [docs/指纹调研.md](docs/指纹调研.md)。
- **UFS HS-G5**：补丁暂缓；重新启用前先确认关机路径修复有效。

## 待上机验证的动作清单（设备回来后按顺序）

1. `scripts/fuxi-m5-wifi-bt.sh`（部署 / 复核 WiFi + 蓝牙硬件）；
2. WiFi 连网：`nmcli dev wifi connect <名称> password <密码>`（需用户提供），验证 WiFi 下 SSH；
3. `scripts/fuxi-m5-phosh.sh`（M5.3 图形界面，CPU 软件渲染）；
4. `scripts/fuxi-m6-display.sh`（原生显示 + GPU，需要看屏幕）；
5. `scripts/fuxi-m5-modem.sh`（基带首次启动，需插 SIM）；
6. `scripts/fuxi-m6-audio.sh`（扬声器，需要听；通过后再测 audio2 麦克风）；
7. `scripts/fuxi-m6-usbc.sh`（OTG/USB3，之后测 desk 接显示器）；
8. `scripts/fuxi-sensors.sh`（传感器：`hexagonrpcd`）；
9. `scripts/fuxi-camera-probe.sh`（相机传感器 ID）；
10. `scripts/fuxi-m6-pm.sh`（调频温控）、`scripts/fuxi-m6-sleep.sh`（省电/挂起）；
11. 多轮重启验证 UFS 关机修复，再考虑 HS-G5。

以上已串进 `scripts/fuxi-after-reboot.sh`（可断点续跑，进度存 `work/state/after-reboot.done`；WiFi 账号用 `FUXI_WIFI_SSID`/`FUXI_WIFI_PSK` 传入）。

## 如何复现一轮验证

```
# 写 recovery_b 跑一轮完整回归（写入 → 回读校验 → 重启进 Linux → SSH → 回 Android）
scripts/fuxi-test-recovery.sh <镜像路径>

# 不写分区，fastboot boot 临时测试
scripts/fuxi-run.sh <镜像路径> '<手机上要执行的命令>'
```

产物与 `evidence/rtest-*/` 同结构；内核/镜像的构建方法见 [`source/BUILD-INFO.md`](source/BUILD-INFO.md)。
