# 硬件资料

本目录归档**本台设备实测得到的硬件配置**，以及小米 13（fuxi）**不同批次/供应商**的差异与适配方法。

| 文档 | 内容 |
|---|---|
| [本机硬件配置](本机硬件配置.md) | 本机（`2211133C`）逐项硬件清单、总线地址、驱动状态与实测证据 |
| [配件供应商差异](配件供应商差异.md) | 面板/触摸/相机模组/电池等供应商变体，以及如何判断自己手上是哪一版 |
| `../device-info/` | 原始导出：厂商面板参数 `panel-m3-38-0c-0a.dtsi`、cmd-db 导出 `cmd-db-fuxi.txt` |

> 说明：硬件配置是**本机实测**结果（Linux 侧 sysfs/dmesg + Android 侧只读探测 + 厂商 DTB），
> 不同批次的小米 13 可能在触摸 IC、相机模组厂、存储容量、电池型号上不同。刷任何镜像前，
> 先按[配件供应商差异](配件供应商差异.md)里的命令确认自己的硬件版本。

数据来源：

- Linux 侧：`uname -a`、`/proc/cpuinfo`、`/proc/meminfo`、`/sys/class/drm/`、`/sys/class/power_supply/`、
  `/sys/class/remoteproc/`、`/sys/bus/spmi/devices/`、`/sys/bus/soundwire/devices/`、`dmesg`
- Android 侧：`getprop`、`/proc/cmdline`、厂商 DTB（`strings` 解析）、
  `/vendor/lib64/camera/*sensormodule*.bin` 模块名
- 采集时间：2026-10-30，Linux `7.3.0+ #207`
