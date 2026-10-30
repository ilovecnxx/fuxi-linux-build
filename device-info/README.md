# 设备常量导出（device-info）

从本机 Android/厂商 DTB 只读导出的硬件常量，供主线 DTS/驱动对照。

| 文件 | 内容 | 用途 |
|---|---|---|
| `cmd-db-fuxi.txt` | Qualcomm cmd-db（RPMh 命令数据库）导出 | 核对各 LDO/regulator 支持的命令与电压档 |
| `panel-m3-38-0c-0a.dtsi` | 厂商面板节点（`qcom,mdss_dsi_m3_38_0c_0a_dsc_cmd`） | 上/下电序列、亮度、DSC 参数的唯一来源 |

本机完整硬件清单与供应商差异见 [`../hardware/`](../hardware/)。

> 注：`work/device-info/` 下还有本机运行中 DTB、相机模块库文件名等中间产物，仅在本机保留，不随仓库发布。
