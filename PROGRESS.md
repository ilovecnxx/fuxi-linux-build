# 进展与验证记录

本文件记录从设备摸底到"Android + 主线 Linux 双系统可用"的时间线，以及可复核的实机验证证据。上手操作请看 [README.md](README.md)，权威操作步骤见 [docs/双系统启动说明.md](docs/双系统启动说明.md)。

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

### 2026-10-27 — 改为 ABL 直接引导 `recovery_b`，双系统成功

- **03:xx–04:50**：用"立即 PSCI 复位"的最小桩内核验证 ABL 的 DTB 行为——镜像附**主线 DTB** 时卡死；附**厂商 `fuxi.dtb`** 时正常跳转（19 秒回 Android）。据此确定方案：镜像里放厂商 DTB 当"诱饵"，内核用 `CONFIG_FUXI_FORCE_BUILTIN_DTB=y` 忽略 ABL 的 DTB、改用内建主线 DTB。
- **04:30–05:31**：`abl-fuxi-v1` … `v5` 迭代，跑通 `recovery_b` → 主线内核 → 内建 initramfs → `switch_root` 到 `sda33` 上的 Ubuntu（systemd）。
- **06:03–06:11**：clean1 / clean2 / clean3 连续三组完整回归（写 `recovery_b` → 回读校验 → 重启进 Linux → SSH → 回 Android），全部通过，启动耗时稳定。
- **06:15 / 06:19**：clean4 / clean5 用于 `sync_state` 诊断（`fuxi.nosync` 调试参数），系统仍正常进入用户空间；06:19 构建的 clean5 定为发布镜像 `images/recovery-linux.img`。
- **06:21**：发布树整理并冻结为 `v0.1.0-dualboot-20261027`。

## 验证证据

### 双系统启动：clean1 – clean5（2026-10-27）

| # | 时间 | 镜像 | sha256（前 16 位） | 结果 | systemd-analyze（kernel + userspace = total） |
|---|---|---|---|---|---|
| 1 | 06:07:23 | clean1 | `b724f94712dbd60c` | 写入并校验；+24 s SSH 可用；+41 s 回 Android | 8.887 + 2.159 = **11.047 s** |
| 2 | 06:09:39 | clean2 | `11bb7076fa544ab2` | 写入并校验；+25 s SSH 可用；+43 s 回 Android | 8.752 + 1.963 = **10.715 s** |
| 3 | 06:11:26 | clean3 | `2583e5fa198105c9` | 写入并校验；+25 s SSH 可用；留在 Ubuntu（`FUXI_KEEP=1`） | 8.730 + 2.463 = **11.194 s** |
| 4 | 06:15:55 | clean4 | `bdae068f2f26c169` | 写入并校验；+60 s SSH 可用；留在 Ubuntu（诊断构建） | 未采集 |
| 5 | 06:19:31 | **clean5（发布镜像）** | `b48614f4a71a8364` | 写入并校验；+53 s SSH 可用；`systemctl is-system-running` = `running`；留在 Ubuntu | 未采集 |

说明：

- "写入并校验"指镜像 `dd` 进 `recovery_b` 后回读 16 位 sha256 与源文件一致；每轮都是真实设备回归。
- "+N s" 是测试脚本从开始到"Ubuntu SSH 可用"的墙钟秒数（含重启、ABL、内核与用户空间启动），**不是**内核启动耗时；内核/用户空间耗时以目标机 `systemd-analyze` 为准。
- clean1–clean3 为连续稳定回归，合计到用户空间 **10.715–11.194 s（内核 8.7–8.9 s + 用户空间 2.0–2.5 s）**。
- clean4 / clean5 是发布前的 `sync_state` 诊断构建，未跑 `systemd-analyze`，因此表中留空，不补数字。
- 原始记录：`evidence/rtest-20261027-060723/`、`-060939/`、`-061126/`、`-061555/`、`-061931/`（各含 `summary.txt` 时间线与 `ssh.txt` 的机器实际输出）；构建日志：`evidence/kbuild-20261027-0610.log`。

### 发布镜像

| 项 | 值 |
|---|---|
| 文件 | `images/recovery-linux.img` |
| 大小 | 7,389,184 B |
| sha256 | 见仓库根 [SHA256SUMS](SHA256SUMS) |
| 内核 | `Linux 7.3.0+ #101 SMP PREEMPT Tue Oct 27 06:19:12 CST 2026` |
| 内核基线 | commit `5b0764a53235d3c77e1ed674e836e1b3fe1a4b1f` |
| 构建时间 | 2026-10-27 06:19 |
| 实测 | 06:19:31 一轮完整回归通过（写入校验 → SSH 可用 → 留在 Ubuntu，systemd running） |
| 来源 | clean5 构建；与 clean1–clean3 同一启动链，仅多 `sync_state` 诊断改动 |

镜像内部结构、源码改造、构建环境与复现步骤见 [`source/BUILD-INFO.md`](source/BUILD-INFO.md)；交付物哈希（12 项）见根目录 [`SHA256SUMS`](SHA256SUMS)。

### 里程碑摘要

- **M1（主线内核进入用户空间）**：2026-10-27 00:20，`/init` 正常运行、串口 shell 可用；当时走的是 EDK2 UEFI 诊断路线，相关代码已从当前树移除（历史见 [docs/交接-给CODEX.md](docs/交接-给CODEX.md)）。
- **M3（UFS 根文件系统 + 用户空间）**：`sda33` 上的 Ubuntu 26.10 正常启动，`systemd` 进入 `running`，SSH over USB 可用。
- **双系统（Android ↔ Linux）**：自 clean1 起，每轮测试都能在 Android → Linux → Android 之间完整闭环；日常开机不碰 `recovery_b`，因此 Android 始终可用。

## 已知未完成（截至 2026-10-27）

- 触摸 / 实体按键输入、WiFi / 蓝牙、GPU、音频、相机、通话：**均未支持**。
- 显示仅 `simpledrm` + `fbcon` 文本控制台（tty1，16×32 字体）；无面板 / DSI 驱动，无图形桌面。
- UFS HS-G5：补丁暂缓（`source/patches/ufs-qcom-sm8550-g5.patch`）。实测 G5 下 `reboot -f` 曾进 EDL，G4 下同样流程 10+ 次正常；重新启用前需先查 `ufshcd` 关机流程。
- EDK2/UEFI 诊断引导与厂商内核构建流水线：已放弃并从当前树移除，保留在 git 历史中。

## 如何复现一轮验证

```
# 写 recovery_b 跑一轮完整回归（写入 → 回读校验 → 重启进 Linux → SSH → 回 Android）
scripts/fuxi-test-recovery.sh <镜像路径>

# 不写分区，fastboot boot 临时测试
scripts/fuxi-run.sh <镜像路径> '<手机上要执行的命令>'
```

产物与 `evidence/rtest-*/` 同结构；内核/镜像的构建方法见 [`source/BUILD-INFO.md`](source/BUILD-INFO.md)。
