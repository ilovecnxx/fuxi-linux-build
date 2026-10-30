# -*- coding: utf-8 -*-
"""用法: python3 build_video.py <音频目录> <输出mp4> [landscape]"""
import io, json, os, sys, wave, array, subprocess

adir, out = sys.argv[1], sys.argv[2]
LS = len(sys.argv) > 3 and sys.argv[3] == "landscape"
PREFIX = "sls_" if LS else "slides_"
SR = 24000
GAP, LEAD, TAIL = 0.35, 0.6, 1.0
STEM = os.path.basename(out).split('.')[0]

cues = json.load(io.open("cues.json", encoding="utf-8"))
os.makedirs(adir, exist_ok=True)
for c in cues:
    mp3 = os.path.join(adir, "c%02d.mp3" % c["i"])
    wav = mp3[:-4] + ".wav"
    if not os.path.exists(wav):
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", mp3,
                        "-ar", str(SR), "-ac", "1", wav], check=True)

def silence(sec):
    return array.array('h', bytes(2 * int(round(sec * SR))))

master, timeline, t = array.array('h'), [], LEAD
master.extend(silence(LEAD))
for c in cues:
    with wave.open(os.path.join(adir, "c%02d.wav" % c["i"]), "rb") as w:
        data = array.array('h', w.readframes(w.getnframes()))
    dur = len(data) / SR
    timeline.append({"i": c["i"], "start": round(t, 3), "end": round(t + dur, 3), "text": c["text"]})
    master.extend(data); master.extend(silence(GAP)); t += dur + GAP
master.extend(silence(TAIL))
total = t + TAIL
narr = "narration_%s.wav" % STEM
with wave.open(narr, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(master.tobytes())

groups = [
    ("01", range(1, 4)), ("02", range(4, 6)), ("03", range(6, 7)), ("04", range(7, 8)),
    ("05", range(8, 10)), ("06", range(10, 11)), ("07", range(11, 12)), ("08", range(12, 14)),
    ("09", range(14, 17)), ("10", range(17, 19)), ("11", range(19, 21)), ("12", range(21, 24)),
    ("13", range(24, 26)), ("14", range(26, 28)), ("15", range(28, 30)), ("16", range(30, 32)),
    ("17", range(32, 34)), ("18", range(34, 35)), ("19", range(35, 36)), ("20", range(36, 38)),
    ("21", range(38, 40)), ("22", range(40, 42)), ("23", range(42, 44)), ("24", range(44, 45)),
    ("25", range(45, 48)), ("26", range(48, 50)), ("27", range(50, 51)), ("28", range(51, 53)),
]
cu = {c["i"]: c for c in timeline}
bounds, prev = [], 0.0
for idx, (name, rng) in enumerate(groups):
    end = total if idx + 1 == len(groups) else (cu[rng[-1]]["end"] + cu[groups[idx + 1][1][0]]["start"]) / 2
    bounds.append((name, prev, end)); prev = end

lst = "list_%s.txt" % STEM
with io.open(lst, "w", encoding="utf-8") as fh:
    for name, a, b in bounds:
        fh.write("file '%s%s.png'\nduration %.3f\n" % (PREFIX, name, max(0.5, b - a)))
    fh.write("file '%s%s.png'\n" % (PREFIX, bounds[-1][0]))

def ts(x):
    return "%02d:%02d:%05.2f" % (int(x // 3600), int(x % 3600 // 60), x % 60)

if LS:
    resx, resy, fsize, mv, mlr = 1920, 1080, 36, 55, 260
else:
    resx, resy, fsize, mv, mlr = 1080, 1920, 42, 200, 80

ass = "subs_%s.ass" % STEM
with io.open(ass, "w", encoding="utf-8") as fh:
    fh.write("[Script Info]\nScriptType: v4.00+\nPlayResX: %d\nPlayResY: %d\n"
             "WrapStyle: 0\nScaledBorderAndShadow: yes\n\n"
             "[V4+ Styles]\n"
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour,"
             " Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline,"
             " Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
             "Style: Default,Noto Sans CJK SC,%d,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,"
             "100,100,1,0,1,3,1,2,%d,%d,%d,1\n\n"
             "[Events]\n"
             "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
             % (resx, resy, fsize, mlr, mlr, mv))
    for c in timeline:
        fh.write("Dialogue: 0,%s,%s,Default,,0,0,0,,%s\n"
                 % (ts(c["start"]), ts(c["end"]), c["text"].replace("\n", r"\N")))

subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "concat", "-safe", "0", "-i", lst, "-i", narr,
                "-vf", "fps=25,format=yuv420p,ass=%s,fade=t=in:st=0:d=0.6,fade=t=out:st=%.2f:d=0.9" % (ass, total - 0.9),
                "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
                "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
                "-t", "%.2f" % total, "-shortest", "-movflags", "+faststart", out], check=True)
print("done", out, "%.1fs" % total)
