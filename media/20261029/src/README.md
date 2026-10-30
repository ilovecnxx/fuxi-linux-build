# B 站视频素材包（2026-10-29）

## 成品

| 文件 | 时长 | 说明 |
|---|---|---|
| `小米13跑纯主线Linux-横屏-男声.mp4` | 6:51 | **1920×1080** · 25fps · H.264 + AAC · `zh-CN-YunxiNeural` |
| `小米13跑纯主线Linux-横屏-女声.mp4` | 6:54 | 同上，`zh-CN-XiaoxiaoNeural` |
| `小米13跑纯主线Linux-竖屏-男声.mp4` | 6:51 | 1080×1920（手机端/竖屏流） |
| `小米13跑纯主线Linux-竖屏-女声.mp4` | 6:54 | 同上，女声 |
| `b站视频-字幕.srt` | — | 52 条字幕，与配音逐句对齐，可导入剪映/达芬奇改 |
| `b站视频-脚本-20261029.md` | — | 分镜脚本、解说词、素材清单、B 站包装文案 |

横屏版左侧文字、右侧实机截图；竖屏版全屏卡片。两种都是「章节卡 + 文字卡 + 一张实机桌面截图」的**图文解说版**：内容完整、可直接发布；把录屏按脚本里的素材清单换进去就是成片。


## 60 秒技术版（最新，推荐发布用）

| 文件 | 规格 | 时长 | 大小 |
|---|---|---|---|
| `60秒技术版-横屏-男声.mp4` | 1920×1080 · 25fps · H.264+AAC | 1:05 | 1.6 MB |
| `60秒技术版-横屏-女声.mp4` | 同上（Xiaoxiao） | 1:05 | 1.7 MB |
| `60秒技术版-竖屏-男声.mp4` | 1080×1920 | 1:05 | 1.5 MB |

结构：双系统（借 recovery_b）→ 坑 1 ABL 叠 dtbo overlay + 诱饵 DTB 解法 → 坑 2 GPU ZAP `-22` →
坑 3 功放 i2c GPIO0/1 → 坑 4/5 setuid 丢位 + UFS 掉 EDL → 现状（通了什么 / 没好什么）→ 仓库。

重新出片：

```bash
python3 make_short.py zh-CN-YunxiNeural ls "60秒技术版-横屏-男声.mp4"   # 横屏
python3 make_short.py zh-CN-YunxiNeural pt "60秒技术版-竖屏-男声.mp4"   # 竖屏
```

- 解说词在 `make_short.py` 的 `CUES` 里（8 句），改完直接重跑
- 卡片文案在同一文件的 `base("s60_xx", ...)` 处，`GROUPS` 决定哪几句配哪张卡
- 语速 `rate="+13%"`，句间停顿 `GAP=0.22`

## 长版（6:51）重新生成（改词 / 换音色 / 调语速）

```bash
cd work/b站视频

# 1. 改解说词 → 编辑 cues.json（i 序号顺序即时间顺序）
# 2. 合成配音（音色见下表），输出到 audio/ 或 audio_f/
python3 tts.py zh-CN-YunxiNeural audio

# 3. 重新出片（自动对齐字幕、分镜、音量归一化到 -16 LUFS）
python3 build_video.py audio  "输出名.mp4"              # 竖屏
python3 build_video.py audio  "输出名.mp4" landscape    # 横屏
```

- `tts.py` 里 `rate="+4%"` 是语速，可改 `+0%` / `+8%`
- `build_video.py` 里 `GAP=0.35` 是句间停顿，`LEAD/TAIL` 是首尾留白
- 幻灯片文案在 `build_slides.py` 里，改完 `python3 build_slides.py`（竖屏）/ `python3 build_slides_ls.py`（横屏）重出 28 张卡片
- 桌面截图取自 `../shots-20261029/00-test.png`，换成正式截图后改 `build_slides.py` 里 `shot_card()` 的路径

## 可选音色（`python3 -m edge_tts --list-voices | grep zh-CN`）

| 音色 | 性别 | 适合 |
|---|---|---|
| `zh-CN-YunxiNeural` | 男 | 年轻、活泼，技术区常用（默认） |
| `zh-CN-YunyangNeural` | 男 | 新闻播报，稳重 |
| `zh-CN-XiaoxiaoNeural` | 女 | 亲切自然 |
| `zh-CN-YunjianNeural` | 男 | 解说腔，偏体育/纪录片 |
| `zh-CN-liaoning-XiaobeiNeural` | 女 | 东北话，整活向 |

## 注意

1. **合成靠联网**（微软 Edge 的在线接口），生成完的 mp3 已存本地，可直接复用。
2. 片中的数字（10.6 秒启动、-22、65.9°C）都来自项目文档与实测日志，别口播时改口。
3. 截图/Wi-Fi 名称打码见 `b站视频-脚本-20261029.md` 最后一节。
4. 若之后要「真人出镜 + 录屏」版本，直接把 `narration_*.wav` 当配音轨对齐时间线即可。

## 播放

宿主已装好 **mpv v0.41.0**（AppImage，无需 root）：

```bash
mpv ~/文档/deepseek-harness/default-workspace/linux-android/work/b站视频/小米13跑纯主线Linux-横屏-男声.mp4
# 或直接双击文件管理器里的 mp4（已注册桌面项）；备选：ffplay 同名文件
```
