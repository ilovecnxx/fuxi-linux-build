# -*- coding: utf-8 -*-
"""横屏 1920x1080 幻灯片"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
BG = (11, 15, 20)
FG = (235, 240, 245)
MUT = (140, 155, 170)
ACC = (94, 200, 255)
WARN = (255, 120, 110)
OK = (120, 220, 150)

def f(sz, bold=False):
    return ImageFont.truetype(FB if bold else FR, sz, index=0)

def card(name, label, title, bullets, accent=ACC, title_color=FG, two_col=None):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    if label:
        d.rectangle([120, 92, 132, 140], fill=accent)
        d.text((154, 94), label, font=f(34, True), fill=MUT)
    y = 190
    if title:
        for line in title.split("\n"):
            d.text((120, y), line, font=f(88, True), fill=title_color)
            y += 118
    y = max(y, 330) if not two_col else 360
    if two_col:
        left, right = two_col
        for col, (head, items, color) in enumerate((left, right)):
            x = 120 + col * 850
            d.text((x, 330), head, font=f(52, True), fill=color)
            yy = 420
            for it in items:
                d.text((x, yy), it, font=f(42), fill=FG)
                yy += 76
    else:
        for text, color, bold, size in bullets:
            d.text((120, y), text, font=f(size, bool(bold)), fill=color)
            y += int(size * 1.55)
    d.rectangle([120, H - 90, W - 120, H - 87], fill=(38, 46, 56))
    im.save("sls_%s.png" % name)

def shot_card(name, label):
    src = "/home/user/文档/deepseek-harness/default-workspace/linux-android/work/shots-20261029/00-test.png"
    im = Image.open(src).convert("RGB")
    # 竖屏截图放到右侧，左侧留文字区
    th = H - 160
    tw = int(im.width * th / im.height)
    shot = im.resize((tw, th), Image.LANCZOS)
    canvas = Image.new("RGB", (W, H), BG)
    canvas.paste(shot, (W - tw - 120, 80))
    d = ImageDraw.Draw(canvas)
    d.rectangle([120, 150, 132, 198], fill=ACC)
    d.text((154, 152), label, font=f(34, True), fill=MUT)
    ty = 300
    for line, sz, col, bold in [("小米 13", 96, FG, True), ("Ubuntu 26.10", 62, ACC, True),
                                ("纯主线内核 7.3.0", 44, FG, False), ("双系统 · 不影响安卓", 40, MUT, False)]:
        d.text((120, ty), line, font=f(sz, bold), fill=col)
        ty += int(sz * 1.35)
    canvas.save("sls_%s.png" % name)

B = lambda t, c=FG, b=False, s=42: (t, c, b, s)

card("01", None, "小米 13 跑纯主线 Linux", [
    B("Linux 7.3.0 + Ubuntu 26.10 · 与安卓双系统共存", ACC, True, 46),
    B("kernel.org 纯主线内核 · 无 Halium · 无 Droidian", MUT, False, 36),
], accent=ACC)
shot_card("02", "成果")
card("03", "01 起因与结论", "Linux 7.3.0", [
    B("kernel.org 纯主线内核，没有任何厂商内核代码", FG),
    B("无 Halium · 无 Droidian · 无 Android HAL", MUT, False, 36),
])
card("04", "01 起因与结论", "已经能用了", [
    B("原生 120Hz 显示 · Adreno 740 GPU 硬解", FG),
    B("双扬声器 · Wi-Fi 7 · 蓝牙", FG),
    B("中文输入法 · 浏览器 · 文件管理", FG),
], title_color=OK)
card("05", "01 起因与结论", "启动 10.6 秒", [
    B("内核 8.76 s  +  用户空间 1.81 s（systemd-analyze）", FG),
    B("重启到 SSH 可登录 ≈ 16 秒", FG),
], title_color=ACC)
card("06", "01 起因与结论", "材料全部开源", [
    B("github.com/ilovecnxx/xiaomi13-fuxi-linux", ACC, True, 44),
    B("镜像 · 内核补丁 · 设备树 · 构建脚本 · 实机验证日志", MUT, False, 34),
])
card("07", "02 方案选择", "两条死路，一条活路", [
    B("① 自制 UEFI（EDK2） → 交接主线内核就黑屏 / 挂起 / 复位", WARN, False, 38),
    B("② kexec 最小 Linux → 正式内核 → 同样不稳定", WARN, False, 38),
    B("③ 让高通 ABL 直接拉起 recovery_b → 稳定", OK, True, 40),
])
card("08", "02 方案选择", "走过的弯路", [
    B("EDK2 能跑、能拿到 GOP 帧缓冲，但交接控制权必挂", FG),
    B("kexec 方案：先起最小 Linux 再跳转，偶发失败", FG),
    B("共同问题：绕不过 ABL 对镜像和 DTB 的处理", MUT, False, 36),
])
card("09", "02 方案选择", "最终方案：借 recovery_b", [
    B("安卓正常开机根本不看这个分区 → 双系统天然成立", FG),
    B("随时回安卓；Linux 刷挂也能长按电源救回来", OK),
    B("代价：要绕开 ABL 的一个坑（下一章）", MUT, False, 36),
], accent=OK)
card("10", "03 启动链", "启动链拆解", [
    B("XBL → 高通 UEFI → ABL → boot.img（内核 + 厂商 DTB）", FG),
    B("→ initramfs（编进内核）→ switch_root → systemd", ACC, True),
    B("ramdisk 为空，命令行从设备树 chosen 读", MUT, False, 36),
])
card("11", "03 启动链", "CONFIG_FUXI_FORCE_BUILTIN_DTB", [
    B("忽略 ABL 传进来的 DTB，强行用编进内核的主线设备树", FG),
    B("initramfs 等 USB 串口就绪，给 8 秒调试窗口", FG),
    B("再 switch_root 到 sda33 上的 Ubuntu 根文件系统", MUT, False, 36),
], title_color=ACC)
card("12", "03 启动链 · 最大的坑", "ABL 会把 dtbo overlay 叠上来", [
    B("叠到主线 DTB 上 → 百分之百卡死黑屏", WARN, True, 44),
    B("叠到厂商 DTB 上 → 一切正常", OK, True, 44),
    B("土办法：镜像里塞厂商 DTB 当诱饵，内核再换成自己的", MUT, False, 34),
], title_color=FG)
card("13", "04 硬件逐个点亮", "触摸 · ST FTM5", [
    B("主线现写驱动，probe 一度全是 -110（控制器没就绪）", FG),
    B("原因：上电时序不对，电源稳之前读 chip id 全是 0", MUT, False, 36),
], title_color=ACC)
card("14", "04 硬件逐个点亮", "显示 · 三星 DSC 面板", [
    B("1080×2400，60 / 90 / 120Hz 三档，三档上电序列只差三条命令", FG),
    B("做完这步，屏幕上第一次出现真正的桌面，而不是点阵字", MUT, False, 36),
], title_color=ACC)
card("15", "04 硬件逐个点亮", "GPU · Adreno 740", [
    B("/vendor/firmware 的 ZAP → TrustZone 返回 -22", WARN, False, 40),
    B("/odm/firmware 小米签名的 ZAP → 一次通过", OK, False, 40),
    B("同一颗芯片、两个目录、两套签名，就这一个差别", MUT, False, 34),
], title_color=ACC)
card("16", "04 硬件逐个点亮", "音频 · CS35L41 ×2 + WCD938x", [
    B("i2c 走 GPIO0 / GPIO1，不是设备树默认的 56 / 57", FG),
    B("GPIO57 是长焦供电 —— 改完引脚才出声", MUT, False, 36),
], title_color=ACC)
card("17", "04 硬件逐个点亮", "Wi-Fi · WCN7850 / ath12k", [
    B("固件从手机自己的 modem 分区只读拉出，打包成 board-2.bin", FG),
    B("不能在 initramfs 阶段 probe，必须等根文件系统就绪再启 ADSP", MUT, False, 34),
], title_color=ACC)
card("18", "04 硬件逐个点亮", "蓝牙 · 没有出厂地址", [
    B("从安卓侧读出本机地址，再用 btmgmt 写一次", FG),
    B("时序要等固件下载完成，否则写不进去", MUT, False, 36),
], title_color=ACC)
card("19", "04 硬件逐个点亮", "传感器 · FastRPC 通路", [
    B("加速度 · 光线 · 距离 · 磁场 全部有读数", FG),
    B("自动亮度就是从这里来的", MUT, False, 36),
], title_color=ACC)
card("20", "05 系统层的坑", "坑 1 · 锁屏密码永远错", [
    B("根文件系统打包时 setuid 位丢了", FG),
    B("unix_chkpwd 读不到 shadow → 密码正确也提示认证失败", WARN, False, 38),
], title_color=WARN)
card("21", "05 系统层的坑", "坑 2 · 关机卡几十秒", [
    B("命令行千万别加 console=ttyGS0", FG),
    B("主机不读 USB 串口时写满阻塞，开关机都被拖住", MUT, False, 36),
], title_color=WARN)
card("22", "05 系统层的坑", "坑 3 · 关机掉进 EDL", [
    B("主线 UFS 驱动没在关机路径释放复位线", FG),
    B("加一个 shutdown 回调释放复位线才正常", OK, False, 38),
], title_color=WARN)
card("23", "05 系统层的坑", "坑 4 · 待机特别费电", [
    B("早期排障参数 cpuidle.off=1 一直留在命令行里", FG),
    B("不进深度空闲、不能挂起 → 耗电偏高，这一版才摘掉", MUT, False, 36),
], title_color=WARN)
card("24", "06 现在能干什么", "能用 / 还不能用", None, two_col=(
    ("能用", ["桌面 · 触摸 · 120Hz", "GPU 硬解 · 双扬声器", "Wi-Fi · 蓝牙", "中文输入 · 浏览器", "调频 · 温控"], OK),
    ("还不能用", ["相机", "蜂窝通话", "指纹（走 TrustZone）", "续航（未开挂起）", "A2DP / USB-C 输出"], WARN),
))
card("25", "06 现在能干什么", "它现在的定位", [
    B("能上网、能打字、能听歌的小 Linux 平板", ACC, True, 48),
    B("不是主力机：相机、蜂窝、续航都还没好", MUT, False, 36),
])
card("26", "07 开源与复现", "xiaomi13-fuxi-linux", [
    B("可刷镜像 · 内核补丁 · 设备树 · 构建脚本", FG),
    B("每一轮实机验证的日志都在仓库里", MUT, False, 36),
], title_color=ACC)
card("27", "07 风险提示", "解锁 BL / 刷 recovery_b 都有风险", [
    B("务必先备份自己的原厂分区", FG),
    B("本文只做记录与分享", MUT, False, 36),
], title_color=WARN)
card("28", None, "下一步", [
    B("日常镜像固化 · 省电 · 相机 · 基带", MUT, False, 40),
    B("github.com/ilovecnxx/xiaomi13-fuxi-linux", ACC, True, 40),
    B("评论区见", FG, True, 44),
], accent=ACC)
print("landscape slides ok")
