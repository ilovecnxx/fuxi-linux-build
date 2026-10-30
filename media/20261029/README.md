# 宣传素材 · 2026-10-29

小米 13（fuxi / SM8550）跑纯主线 Linux 7.3 + Ubuntu 26.10 的 B 站 / 酷安素材包。

## short/ 60 秒技术版（推荐发布）

| 文件 | 规格 | 时长 | 大小 |
|---|---|---|---|
| `60秒技术版-横屏-男声.mp4` | 1920×1080 · 25fps · H.264+AAC | 1:05 | 1.6 MB |
| `60秒技术版-横屏-女声.mp4` | 同上（Xiaoxiao） | 1:05 | 1.7 MB |
| `60秒技术版-竖屏-男声.mp4` | 1080×1920 | 1:05 | 1.5 MB |

内容：借 `recovery_b` 做双系统 → 坑 1 ABL 叠 dtbo overlay（厂商 DTB 当诱饵 + `CONFIG_FUXI_FORCE_BUILTIN_DTB`）→
坑 2 Adreno ZAP `/vendor` 签名 `-22`、换 `/odm` 小米签名 → 坑 3 功放 i2c 走 GPIO0/GPIO1 →
坑 4/5 打包丢 `setuid`（锁屏密码永远错）、UFS 关机没放复位线（掉 EDL）→ 现状。

## long/ 6 分钟完整解说版

| 文件 | 规格 | 时长 | 大小 |
|---|---|---|---|
| `小米13跑纯主线Linux-横屏-男声.mp4` | 1920×1080 | 6:51 | 10 MB |
| `小米13跑纯主线Linux-横屏-女声.mp4` | 1920×1080 | 6:54 | 11 MB |
| `小米13跑纯主线Linux-竖屏-男声.mp4` | 1080×1920 | 6:51 | 10 MB |
| `小米13跑纯主线Linux-竖屏-女声.mp4` | 1080×1920 | 6:54 | 10 MB |

28 张章节卡，讲全移植过程：方案取舍（EDK2 / kexec / ABL）、启动链拆解、硬件逐个点亮
（触摸 / 显示 / GPU / 音频 / Wi-Fi / 蓝牙 / 传感器）、四个系统层的坑、现状与不足。

## covers/

`封面-A.png`（居中大字）、`封面-B.png`（左对齐技术风），均为 B 站标准 1146×717。

## src/ 可复现

- `b站视频-脚本-20261029.md` —— 分镜脚本、解说词、素材清单、B 站包装文案（标题 / 简介 / 标签）
- `酷安投稿-小米13主线Linux-20261029.md` —— 酷安图文稿
- `tts.py` / `make_short.py` / `build_video.py` / `build_slides*.py` / `cues.json` —— 生成管线
  （配音用 edge-tts，`zh-CN-YunxiNeural` / `zh-CN-XiaoxiaoNeural`）
- `b站视频-字幕.srt`（52 条）、`timeline.json`（句级时间轴）

生成管线需要：`python3`、`Pillow`、`edge-tts`、`ffmpeg`、Noto Sans CJK 字体。
音频中间件（wav/mp3 分句）未入库，可按下述命令重新合成：

```bash
python3 tts.py zh-CN-YunxiNeural audio
python3 build_video.py audio "out.mp4" landscape      # 长版
python3 make_short.py zh-CN-YunxiNeural ls "out.mp4"  # 60 秒版
```

## 校验

`SHA256SUMS` 覆盖本目录全部文件（不含自身）。

## 内容口径

所有技术数据（启动 10.6 s、ZAP `-22`、GPU 满载 ~66 °C、120 Hz 等）均出自仓库 `docs/` 与 `evidence/` 的实机日志。
未验收项（相机、蜂窝、指纹、续航、A2DP、USB-C 输出）在视频与文稿中均按「尚未通过」表述，不宣称完成。
