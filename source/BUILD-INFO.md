# 构建信息 — 2026-10-27 双系统版本

本目录记录发布镜像 `images/recovery-linux.img` 的完整来源与验证证据，便于复现。

## 产物

| 文件 | 大小 | SHA-256 |
|---|---|---|
| `images/recovery-linux.img` | 7,389,184 B | `b48614f4a71a8364888e4e51d47824e13c775c2369deab40f988a3ffa56ebb6e` |

镜像内包含：

- 内核 `Image.gz`：6,579,778 B（`Linux 7.3.0+`）
- 厂商诱饵 DTB `fuxi.dtb`：801,847 B
- 内建 initramfs（BusyBox，压缩进内核）

> 镜像与 `source/` 产物（共 12 项）的 SHA-256 见仓库根目录 `SHA256SUMS`。

## 源码基线

| 项 | 值 |
|---|---|
| 上游 | `https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git` |
| commit | `5b0764a53235d3c77e1ed674e836e1b3fe1a4b1f`（Merge tag `drm-next-2026-10-21`） |
| 内核版本字符串 | `Linux version 7.3.0+ #101 SMP PREEMPT Tue Oct 27 06:19:12 CST 2026` |
| 受跟踪文件改动 | `source/kernel.diff`：5 个文件，+42/−1 |
| 新增文件 | `source/linux-untracked/`：`sm8550-xiaomi-fuxi-min.dts`、`fuxi_dtb.S`、`fuxi_early.c`、`fuxi_font.h` |
| initramfs | `source/initramfs/init`（可执行）+ `source/initramfs/initramfs.list` |
| 待上游补丁 | `source/patches/ufs-qcom-sm8550-g5.patch`（UFS HS-G5，暂缓） |

`source/kernel.diff` 中值得注意的改动：

- `arch/arm64/Kconfig`：新增 `CONFIG_FUXI_FORCE_BUILTIN_DTB`；
- `arch/arm64/kernel/setup.c`：`setup_arch()` 里把 `__fdt_pointer` 指向内建 DTB（绕过 ABL 的 dtbo overlay）；
- `drivers/base/core.c`：诊断用 `fuxi.nosync=1`，可暂停自动 `sync_state()`；
- `arch/arm64/kernel/Makefile`：编入 `fuxi_dtb.o` 与 `fuxi_early.o`（simpledrm 之前的早期屏幕 console）。

## 构建环境

- Ubuntu 26.10；`aarch64-linux-gnu-gcc` 15.3.0；GNU ld 2.47；GNU Make 4.4.1；dtc 1.7.2；Python 3
- 内核配置：`source/kernel.config`，关键项：
  - `CONFIG_FUXI_FORCE_BUILTIN_DTB=y`（忽略 ABL 传入的 DTB，改用内建主线 DTB）
  - `CONFIG_INITRAMFS_SOURCE="<build>/build/initramfs <build>/build/initramfs.list"`（构建机绝对路径，复现时改成自己的路径）
  - `CONFIG_INITRAMFS_COMPRESSION_GZIP=y`、`CONFIG_CMDLINE_FROM_BOOTLOADER=y`
  - `CONFIG_USB_DWC3_QCOM=y`、`CONFIG_USB_CONFIGFS_ACM=y`（USB 串口 / USB 网络）
  - `CONFIG_DRM_SIMPLEDRM=y` + FB 子系统（fbcon 显示）

## 复现步骤

1. 克隆上游 linux，checkout `5b0764a53235d3c77e1ed674e836e1b3fe1a4b1f`；
2. `cp source/kernel.config .config`；
3. `git apply source/kernel.diff`；
4. 拷贝 `source/linux-untracked/`：`sm8550-xiaomi-fuxi-min.dts` → `arch/arm64/boot/dts/qcom/`，
   其余 3 个 → `arch/arm64/kernel/`；
5. initramfs：把 `source/initramfs/init` 放到 `<build>/build/initramfs/init`（可执行），
   `initramfs.list` 放到 `<build>/build/initramfs.list`；按需修改 `CONFIG_INITRAMFS_SOURCE`；
6. `make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- olddefconfig`；
7. `make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- qcom/sm8550-xiaomi-fuxi-min.dtb Image.gz`；
8. 准备厂商诱饵 DTB：从本机原厂 `boot`/`dtbo` 镜像中提取 `fuxi.dtb`（801,847 B），
   放到 `scripts/fuxi-build-abl.sh` 里 `BAIT_DTB` 指向的位置；
9. `scripts/fuxi-build-abl.sh clean5` → 生成 `work/kbuild/abl-fuxi-clean5.img`
   （脚本调用 Android `mkbootimg` 打包 boot header v1）。

> **厂商固件说明**：发布镜像内嵌的 801,847 B `fuxi.dtb` 是厂商 DTB（作为 ABL 引导诱饵，不含可执行代码）；仓库不以源码形式分发厂商固件，完全自建请从自己设备的原厂 ROM 提取。
> `build/edk2-msm/tools/mkbootimg.py` 未包含在本仓库，可用 AOSP `mkbootimg` 按脚本参数替代。

## 镜像结构

| 字段 | 值 |
|---|---|
| 格式 | Android boot image，header v1（header_size 1648） |
| page_size | 4096 |
| kernel | `Image.gz`（6,579,778 B）+ `fuxi.dtb`（801,847 B）= 7,381,625 B |
| ramdisk | 空（initramfs 已编进内核） |
| 总大小 | 7,389,184 B |

header 中记录的 cmdline（实际生效的 cmdline 来自内建 DTB 的 `/chosen/bootargs`）：

```text
loglevel=7 log_buf_len=2M panic=0 clk_ignore_unused pd_ignore_unused regulator_ignore_unused
arm-smmu.disable_bypass=0 cpuidle.off=1 initramfs_async=0 fbcon=font:TER16x32 console=tty0
fuxi.fb=0xB8000000,1080,2400,1080,32 rdinit=/init
g_cdc.idVendor=0x0525 g_cdc.idProduct=0xa4a7
g_cdc.dev_addr=02:f0:c5:13:00:02 g_cdc.host_addr=02:f0:c5:13:00:01
```

## 实机验证记录（2026-10-27）

| 时间 | 镜像 | 结果 | systemd-analyze（kernel + userspace） |
|---|---|---|---|
| 06:07 | clean1 | Ubuntu SSH 可用，返回 Android | 8.887 + 2.159 = 11.047 s |
| 06:09 | clean2 | Ubuntu SSH 可用，返回 Android | 8.752 + 1.963 = 10.715 s |
| 06:11 | clean3 | Ubuntu SSH 可用（FUXI_KEEP 留在 Ubuntu） | 8.730 + 2.463 = 11.194 s |
| 06:15 | clean4 | Ubuntu SSH 可用（FUXI_KEEP） | — |
| 06:20 | **clean5（本发布镜像）** | Ubuntu SSH 可用（FUXI_KEEP） | — |

- 启动链：ABL → `recovery_b` 中的 boot.img v1 → 内建内核 + 内建 DTB → initramfs → switch_root 到 `sda33` 的 Ubuntu。
- 原始记录：`evidence/rtest-20261027-*/`、`evidence/kbuild-*.log`。
- 说明：clean4/clean5 是发布前最后一次诊断构建（检查 `sync_state`），内核基线同为 7.3.0、启动链与 clean3 相同；
  发布镜像取最后一次实测通过的 clean5。

## 已知限制

- 触摸 / 按键输入、WiFi / 蓝牙、GPU、音频、相机尚未支持；UFS HS-G5 补丁暂缓（`source/patches/`）。
- initramfs 启动后有 8 秒 USB 串口窗口；主机不执行 `touch /tmp/stay` 时会自动 `switch_root` 进 Ubuntu。
- `CONFIG_INITRAMFS_SOURCE` 记录的是构建机绝对路径，复现时必须修改。
