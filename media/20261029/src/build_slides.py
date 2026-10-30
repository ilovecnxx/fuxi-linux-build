# -*- coding: utf-8 -*-
import io, json
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
BG = (11, 15, 20)
FG = (235, 240, 245)
MUT = (140, 155, 170)
ACC = (94, 200, 255)
WARN = (255, 120, 110)
OK = (120, 220, 150)

def f(size, bold=False):
    return ImageFont.truetype(FB if bold else FR, size, index=0)

def card(name, label, blocks, accent=ACC, shot=None):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    # 左上角章节标签
    if label:
        d.rectangle([70, 150, 82, 198], fill=accent)
        d.text((104, 152), label, font=f(36, True), fill=MUT)
    y = 440
    for text, size, color, bold, gap in blocks:
        ft = f(size, bold)
        for line in text.split("\n"):
            w = d.textbbox((0, 0), line, font=ft)[2]
            d.text(((W - w) / 2, y), line, font=ft, fill=color)
            y += int(size * 1.32)
        y += gap
    # 底部细线
    d.rectangle([70, H - 120, W - 70, H - 117], fill=(38, 46, 56))
    im.save("slides_%s.png" % name)

def shot_card(name, label):
    src = "/home/user/文档/deepseek-harness/default-workspace/linux-android/work/shots-20261029/00-test.png"
    im = Image.open(src).convert("RGB")
    im = im.resize((W, int(im.height * W / im.width)), Image.LANCZOS)
    top = max(0, (im.height - H) // 2)
    im = im.crop((0, top, W, top + H))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 128], fill=(0, 0, 0))
    d.rectangle([0, 128, W, 132], fill=ACC)
    d.text((40, 34), label, font=f(42, True), fill=FG)
    im.save("slides_%s.png" % name)

T = lambda *a: a  # noqa

card("01", None, [
    ("小米 13", 122, FG, True, 6),
    ("跑纯主线 Linux", 96, ACC, True, 46),
    ("Linux 7.3.0 + Ubuntu 26.10 · 双系统", 40, MUT, False, 0),
], accent=ACC)

shot_card("02", "小米 13 · Ubuntu 26.10 桌面")

card("03", "01 起因与结论", [
    ("Linux 7.3.0", 104, ACC, True, 18),
    ("kernel.org 纯主线内核", 52, FG, False, 40),
    ("无厂商内核 · 无 Halium · 无 Droidian", 38, MUT, False, 0),
])

card("04", "01 起因与结论", [
    ("已经能用了", 68, OK, True, 46),
    ("原生 120Hz 显示  ·  Adreno 740 GPU", 46, FG, False, 24),
    ("双扬声器  ·  Wi-Fi 7  ·  蓝牙", 46, FG, False, 24),
    ("中文输入法  ·  浏览器  ·  文件管理", 46, FG, False, 0),
])

card("05", "01 起因与结论", [
    ("启动 10.6 秒", 96, ACC, True, 44),
    ("内核 8.76 s  +  用户空间 1.81 s", 44, FG, False, 36),
    ("重启到 SSH 可登录 ≈ 16 秒", 46, FG, False, 0),
])

card("06", "01 起因与结论", [
    ("材料全部开源", 64, FG, True, 40),
    ("github.com/ilovecnxx", 46, ACC, False, 6),
    ("/xiaomi13-fuxi-linux", 46, ACC, False, 34),
    ("镜像 · 内核补丁 · 设备树 · 实机日志", 32, MUT, False, 0),
])

card("07", "02 方案选择", [
    ("两条死路", 92, WARN, True, 34),
    ("一条活路", 92, OK, True, 0),
])

card("08", "02 方案选择", [
    ("① 自制 UEFI（EDK2）", 50, FG, True, 22),
    ("能跑，能拿 GOP 帧缓冲", 40, MUT, False, 16),
    ("交接主线内核 → 黑屏 / 挂起 / 复位", 40, WARN, False, 56),
    ("② kexec 最小 Linux → 正式内核", 50, FG, True, 22),
    ("同样不稳定", 40, WARN, False, 0),
])

card("09", "02 方案选择", [
    ("让 ABL 直接拉起 recovery_b", 56, ACC, True, 52),
    ("正常开机根本不看这个分区", 42, FG, False, 20),
    ("随时能回安卓，刷挂也能救", 42, OK, False, 0),
], accent=OK)

card("10", "03 启动链", [
    ("XBL → 高通 UEFI → ABL", 50, FG, True, 20),
    ("→ boot.img（内核 + 厂商 DTB）", 50, ACC, True, 20),
    ("→ initramfs → switch_root → systemd", 50, FG, True, 44),
    ("ramdisk 为空，initramfs 编进内核", 36, MUT, False, 0),
])

card("11", "03 启动链", [
    ("CONFIG_FUXI_FORCE_BUILTIN_DTB", 40, ACC, True, 34),
    ("忽略 ABL 传进来的 DTB", 46, FG, False, 18),
    ("用设备树里的 chosen / bootargs", 46, FG, False, 0),
])

card("12", "03 启动链 · 最大的坑", [
    ("ABL 会叠 dtbo overlay", 52, FG, True, 44),
    ("叠到主线 DTB  →  必然卡死", 50, WARN, True, 26),
    ("叠到厂商 DTB  →  一切正常", 50, OK, True, 44),
    ("土办法：厂商 DTB 当诱饵，内核再换掉它", 34, MUT, False, 0),
])

card("13", "04 硬件逐个点亮", [
    ("触摸 · ST FTM5", 58, ACC, True, 44),
    ("主线新写驱动，probe 一度全是 -110", 42, FG, False, 18),
    ("原因：上电时序不对，电源稳之前 chip id 全是 0", 38, MUT, False, 0),
])

card("14", "04 硬件逐个点亮", [
    ("显示 · 三星 DSC 面板", 56, ACC, True, 40),
    ("1080×2400，60 / 90 / 120Hz 三档", 46, FG, False, 18),
    ("三档上电序列只差三条命令", 40, MUT, False, 0),
])

card("15", "04 硬件逐个点亮", [
    ("GPU · Adreno 740", 56, ACC, True, 40),
    ("ZAP 签名：/vendor/firmware → TZ 返回 -22", 38, WARN, False, 16),
    ("换 /odm/firmware 的小米签名 → 一次过", 38, OK, False, 0),
])

card("16", "04 硬件逐个点亮", [
    ("音频 · CS35L41 ×2 + WCD938x", 50, ACC, True, 40),
    ("i2c 走 GPIO0 / GPIO1", 46, FG, False, 18),
    ("不是默认的 56 / 57（57 是长焦供电）", 38, MUT, False, 0),
])

card("17", "04 硬件逐个点亮", [
    ("Wi-Fi · WCN7850 / ath12k", 50, ACC, True, 36),
    ("固件从 modem 分区只读拉出 → board-2.bin", 38, FG, False, 16),
    ("不能在 initramfs 阶段 probe，要等根文件系统", 34, MUT, False, 0),
])

card("18", "04 硬件逐个点亮", [
    ("蓝牙 · 没有出厂地址", 52, ACC, True, 40),
    ("从安卓读出本机地址，btmgmt 写一次", 42, FG, False, 16),
    ("时序要等固件下载完成", 36, MUT, False, 0),
])

card("19", "04 硬件逐个点亮", [
    ("传感器 · FastRPC 通路", 52, ACC, True, 40),
    ("加速度 · 光线 · 距离 · 磁场 均有读数", 42, FG, False, 0),
])

card("20", "05 系统层的坑", [
    ("坑 1 · 锁屏密码永远错", 52, WARN, True, 38),
    ("根文件系统打包时 setuid 位丢了", 42, FG, False, 16),
    ("unix_chkpwd 读不到 shadow → 认证失败", 38, MUT, False, 0),
])

card("21", "05 系统层的坑", [
    ("坑 2 · 关机卡几十秒", 52, WARN, True, 38),
    ("命令行别加 console=ttyGS0", 46, FG, False, 16),
    ("主机不读串口时写满阻塞", 38, MUT, False, 0),
])

card("22", "05 系统层的坑", [
    ("坑 3 · 关机掉进 EDL", 52, WARN, True, 38),
    ("UFS 驱动没在关机路径释放复位线", 42, FG, False, 16),
    ("加 shutdown 回调释放复位线", 40, OK, False, 0),
])

card("23", "05 系统层的坑", [
    ("坑 4 · 待机特别费电", 52, WARN, True, 38),
    ("早期排障参数 cpuidle.off=1 一直留着", 40, FG, False, 16),
    ("不进深度空闲、不能挂起", 38, MUT, False, 0),
])

card("24", "06 现在能干什么", [
    ("能用", 64, OK, True, 34),
    ("桌面 · 触摸 · 120Hz · GPU · 双扬声器", 42, FG, False, 18),
    ("Wi-Fi · 蓝牙 · 中文输入 · 浏览器 · 文件管理", 42, FG, False, 0),
])

card("25", "06 现在能干什么", [
    ("还不能用", 60, WARN, True, 32),
    ("相机 · 蜂窝通话 · 指纹", 46, FG, False, 26),
    ("续航比安卓差（未开深度空闲 / 挂起）", 38, MUT, False, 40),
    ("= 能上网、能打字、能听歌的小 Linux 平板", 36, ACC, True, 0),
])

card("26", "07 开源与复现", [
    ("xiaomi13-fuxi-linux", 52, ACC, True, 34),
    ("可刷镜像 · 内核补丁 · 设备树 · 构建脚本", 38, FG, False, 16),
    ("每一轮实机验证日志都在", 38, MUT, False, 0),
])

card("27", "07 风险提示", [
    ("解锁 BL / 刷 recovery_b 有风险", 44, WARN, True, 28),
    ("先备份自己的原厂分区", 42, FG, False, 0),
])

card("28", None, [
    ("下一步", 96, FG, True, 44),
    ("日常镜像固化  ·  省电  ·  相机  ·  基带", 40, MUT, False, 44),
    ("评论区见", 60, ACC, True, 30),
    ("github.com/ilovecnxx/xiaomi13-fuxi-linux", 28, MUT, False, 0),
], accent=ACC)
print("slides ok")
