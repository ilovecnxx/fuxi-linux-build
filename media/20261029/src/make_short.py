# -*- coding: utf-8 -*-
"""60 秒技术版：python3 make_short.py <voice> <aspect: ls|pt> <out.mp4>"""
import asyncio, io, json, os, sys, wave, array, subprocess
import edge_tts
from PIL import Image, ImageDraw, ImageFont

VOICE, ASPECT, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
LS = ASPECT == "ls"
W, H = (1920, 1080) if LS else (1080, 1920)
SC = 1.0 if LS else 0.62
STEM = os.path.basename(OUT).split('.')[0]
ADIR = "audio_short_%s" % VOICE.split("-")[2][:4].lower()

FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
BG, FG, MUT = (11, 15, 20), (235, 240, 245), (140, 155, 170)
ACC, WARN, OK = (94, 200, 255), (255, 120, 110), (120, 220, 150)

CUES = [
 "小米 13 跑 kernel.org 的纯主线 Linux 7.3，只借 recovery_b 做入口，和安卓双系统并存。",
 "坑一：高通的 ABL 会把 dtbo overlay 叠到主线 DTB 上，必然黑屏卡死。",
 "解法：镜像里塞一个厂商 DTB 当诱饵，内核再用 FORCE_BUILTIN_DTB 换成自己的设备树。",
 "坑二：Adreno 740 的 ZAP，vendor 分区的签名被 TrustZone 拒成 -22，换 odm 分区小米签名的一次过。",
 "坑三：音频功放 i2c 走 GPIO0 和 GPIO1，不是设备树默认的 56/57。",
 "坑四：打包丢了 setuid 位，锁屏密码永远提示错误；UFS 关机没放复位线，会掉进 EDL。",
 "现在 120Hz 显示、GPU 硬解、双扬声器、Wi-Fi 7、中文输入都通了。",
 "相机、蜂窝、指纹、续航还没好，代码和日志都在 GitHub。",
]
# slide 名 -> 覆盖的 cue 序号（从 0 开始）
GROUPS = [("01", [0]), ("02", [1]), ("03", [2]), ("04", [3]), ("05", [4]),
          ("06", [5]), ("07_u", [6]), ("07", [7])]

def f(sz, bold=False):
    return ImageFont.truetype(FB if bold else FR, max(12, int(sz * SC)), index=0)

def base(name, label, title, bullets, accent=ACC, title_color=FG):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    x0 = int(120 * SC) if LS else int(90 * SC)
    if label:
        d.rectangle([x0, int(92 * SC), x0 + int(12 * SC), int(140 * SC)], fill=accent)
        d.text((x0 + int(34 * SC), int(94 * SC)), label, font=f(34, True), fill=MUT)
    y = int(190 * SC)
    for line in title.split("\n"):
        d.text((x0, y), line, font=f(88, True), fill=title_color)
        y += int(118 * SC)
    y = max(y, int(330 * SC))
    for text, color, bold, size in bullets:
        d.text((x0, y), text, font=f(size, bool(bold)), fill=color)
        y += int(size * 1.55 * SC)
    d.rectangle([x0, H - int(90 * SC), W - x0, H - int(87 * SC)], fill=(38, 46, 56))
    im.save("%s.png" % name)

B = lambda t, c=FG, b=False, s=42: (t, c, b, s)

base("s60_01", None, "小米 13 跑纯主线 Linux", [
    B("60 秒：方案 + 四个坑", ACC, True, 48),
    B("kernel.org Linux 7.3 · 借 recovery_b 做入口 · 与安卓双系统并存", MUT, False, 34),
])
base("s60_02", "坑 1", "ABL 会把 dtbo overlay 叠上来", [
    B("叠到主线 DTB 上 → 必然黑屏卡死", WARN, True, 46),
], title_color=WARN)
base("s60_03", "坑 1 · 解法", "厂商 DTB 当诱饵", [
    B("镜像里塞厂商 DTB 满足 ABL", FG),
    B("内核 FORCE_BUILTIN_DTB 换成自己的设备树", ACC, True),
], accent=OK)
base("s60_04", "坑 2", "Adreno 740 的 ZAP 认证", [
    B("/vendor/firmware → TrustZone 返回 -22", WARN, False, 40),
    B("/odm/firmware 小米签名 → 一次通过", OK, False, 40),
], title_color=ACC)
base("s60_05", "坑 3", "功放 i2c 走 GPIO0 / GPIO1", [
    B("不是设备树默认的 56 / 57", FG),
    B("GPIO57 是长焦供电 → 改引脚才出声", MUT, False, 36),
], title_color=ACC)
base("s60_06", "坑 4 / 5", "两个系统层的坑", [
    B("打包丢 setuid → 锁屏密码永远提示错误", WARN, False, 38),
    B("UFS 关机没放复位线 → 掉进 EDL", WARN, False, 38),
])
base("s60_07_u", "现状", "已经通了", [
    B("120Hz 显示 · GPU 硬解 · 双扬声器 · Wi-Fi 7 · 中文输入", OK, False, 38),
])
base("s60_07", "现状", "还没好", [
    B("相机 · 蜂窝 · 指纹 · 续航", WARN, False, 38),
    B("github.com/ilovecnxx/xiaomi13-fuxi-linux", ACC, True, 34),
])
print("slides ok")

# ---- TTS ----
os.makedirs(ADIR, exist_ok=True)
async def speak():
    sem = asyncio.Semaphore(3)
    async def one(i, text):
        async with sem:
            await edge_tts.Communicate(text, VOICE, rate="+13%").save(os.path.join(ADIR, "c%02d.mp3" % i))
    await asyncio.gather(*(one(i, t) for i, t in enumerate(CUES, 1)))
asyncio.run(speak())
print("tts ok")

SR, GAP, LEAD, TAIL = 24000, 0.22, 0.45, 0.7
for i in range(1, len(CUES) + 1):
    p = os.path.join(ADIR, "c%02d.mp3" % i)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", p,
                    "-ar", str(SR), "-ac", "1", p[:-4] + ".wav"], check=True)

sil = lambda s: array.array('h', bytes(2 * int(round(s * SR))))
master, tl, t = array.array('h'), [], LEAD
master.extend(sil(LEAD))
for i in range(1, len(CUES) + 1):
    with wave.open(os.path.join(ADIR, "c%02d.wav" % i), "rb") as w:
        data = array.array('h', w.readframes(w.getnframes()))
    dur = len(data) / SR
    tl.append({"i": i - 1, "start": round(t, 3), "end": round(t + dur, 3), "text": CUES[i - 1]})
    master.extend(data); master.extend(sil(GAP)); t += dur + GAP
master.extend(sil(TAIL)); total = t + TAIL
narr = "narr_%s.wav" % STEM
with wave.open(narr, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(master.tobytes())

lst = "list_%s.txt" % STEM
bounds, prev = [], 0.0
for idx, (name, idxs) in enumerate(GROUPS):
    end = total if idx + 1 == len(GROUPS) else (tl[idxs[-1]]["end"] + tl[GROUPS[idx + 1][1][0]]["start"]) / 2
    bounds.append((name, prev, end)); prev = end
with io.open(lst, "w", encoding="utf-8") as fh:
    for name, a, b in bounds:
        fh.write("file 's60_%s.png'\nduration %.3f\n" % (name, max(0.4, b - a)))
    fh.write("file 's60_%s.png'\n" % bounds[-1][0])

ts = lambda x: "%02d:%02d:%05.2f" % (int(x // 3600), int(x % 3600 // 60), x % 60)
fsize, mv, mlr = (36, 55, 260) if LS else (42, 200, 80)
ass = "subs_%s.ass" % STEM
with io.open(ass, "w", encoding="utf-8") as fh:
    fh.write("[Script Info]\nScriptType: v4.00+\nPlayResX: %d\nPlayResY: %d\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n"
             "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour,"
             " Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow,"
             " Alignment, MarginL, MarginR, MarginV, Encoding\n"
             "Style: Default,Noto Sans CJK SC,%d,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,1,0,1,3,1,2,%d,%d,%d,1\n\n"
             "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
             % (W, H, fsize, mlr, mlr, mv))
    for c in tl:
        fh.write("Dialogue: 0,%s,%s,Default,,0,0,0,,%s\n" % (ts(c["start"]), ts(c["end"]), c["text"]))

subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                "-i", narr, "-vf", "fps=25,format=yuv420p,ass=%s,fade=t=in:st=0:d=0.4,fade=t=out:st=%.2f:d=0.7" % (ass, total - 0.7),
                "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-t", "%.2f" % total, "-shortest",
                "-movflags", "+faststart", OUT], check=True)
print("done %s  %.1f 秒" % (OUT, total))
