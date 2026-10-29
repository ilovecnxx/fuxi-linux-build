// SPDX-License-Identifier: GPL-2.0
/*
 * fuxi（Xiaomi 13）早期屏幕 console：在 simpledrm/fbcon 接管前显示内核日志。
 * 手机没有可用 UART；内核若在 simpledrm probe 前出错，只能通过屏幕看日志。
 *
 * 只在命令行带 fuxi.fb=0x<phys>,<stride_px>,<height>,<width>,<bpp> 时启用。
 * early_initcall 注册（CON_PRINTBUFFER 会回放此前的全部日志）；DT 里有可用的
 * simple-framebuffer 时，late_initcall_sync 注销，把屏幕交给 fbcon。
 */
#include <linux/console.h>
#include <linux/init.h>
#include <linux/io.h>
#include <linux/kernel.h>
#include <linux/of.h>
#include <asm/cacheflush.h>

#include "fuxi_font.h"

#define FUXI_TEXT_X	16
#define FUXI_TEXT_Y	64
#define FUXI_TEXT_SCALE	3
#define FUXI_TEXT_LH	50
#define FUXI_TEXT_MAX	48

static phys_addr_t fuxi_fb_base;
static unsigned int fuxi_fb_stride, fuxi_fb_width, fuxi_fb_height;
static bool fuxi_fb_valid, fuxi_cons_registered;
static void *fuxi_fb_lin;
static unsigned int fuxi_text_line;
static char fuxi_cons_buf[FUXI_TEXT_MAX];
static unsigned int fuxi_cons_len;

static int __init fuxi_fb_param(char *str)
{
	unsigned long long base;
	unsigned int stride, height, width, bpp;

	if (str && sscanf(str, "0x%llx,%u,%u,%u,%u",
			  &base, &stride, &height, &width, &bpp) == 5 &&
	    stride && height && width && bpp == 32) {
		fuxi_fb_base = base;
		fuxi_fb_stride = stride;
		fuxi_fb_width = width;
		fuxi_fb_height = height;
		fuxi_fb_valid = true;
	}
	return 0;
}
early_param("fuxi.fb", fuxi_fb_param);

/* 画一行放大的 8x16 字符；白字黑底，写到底后从头覆盖。 */
static void fuxi_draw_line(const char *s, unsigned int len)
{
	unsigned int maxc = (fuxi_fb_width - FUXI_TEXT_X) / (8 * FUXI_TEXT_SCALE);
	unsigned int row, sy, ch, col, sc, x, y;

	len = min3(len, maxc, (unsigned int)FUXI_TEXT_MAX);
	y = FUXI_TEXT_Y + fuxi_text_line * FUXI_TEXT_LH;
	if (y + FUXI_TEXT_LH > fuxi_fb_height) {
		fuxi_text_line = 0;
		y = FUXI_TEXT_Y;
	}
	for (row = 0; row < 16; row++) {
		for (sy = 0; sy < FUXI_TEXT_SCALE; sy++) {
			u32 *p = (u32 *)fuxi_fb_lin +
				 (phys_addr_t)(y + row * FUXI_TEXT_SCALE + sy) *
				 fuxi_fb_stride + FUXI_TEXT_X;

			/* 先清整行，消除上一轮残留 */
			for (x = 0; x < fuxi_fb_width - FUXI_TEXT_X; x++)
				p[x] = 0;
			for (ch = 0; ch < len; ch++) {
				unsigned char c = s[ch];
				unsigned char bits;

				if (c < 32 || c > 126)
					c = ' ';
				bits = fuxi_font8x16[c - 32][row];
				for (col = 0; col < 8; col++) {
					u32 color = (bits & (0x80u >> col)) ? 0x00ffffffu : 0;

					for (sc = 0; sc < FUXI_TEXT_SCALE; sc++)
						p[(ch * 8 + col) * FUXI_TEXT_SCALE + sc] = color;
				}
			}
			dcache_clean_poc((unsigned long)p,
					 (unsigned long)(p + fuxi_fb_width - FUXI_TEXT_X));
		}
	}
	fuxi_text_line++;
}

static void fuxi_console_write(struct console *co, const char *s,
			       unsigned int count)
{
	unsigned int i;

	for (i = 0; i < count; i++) {
		if (s[i] == '\r')
			continue;
		if (s[i] == '\n' || fuxi_cons_len >= FUXI_TEXT_MAX) {
			fuxi_draw_line(fuxi_cons_buf, fuxi_cons_len);
			fuxi_cons_len = 0;
			if (s[i] == '\n')
				continue;
		}
		fuxi_cons_buf[fuxi_cons_len++] = s[i];
	}
}

static struct console fuxi_console = {
	.name	= "fuxifb",
	.write	= fuxi_console_write,
	.flags	= CON_PRINTBUFFER | CON_ENABLED,
	.index	= -1,
};

static int __init fuxi_console_init(void)
{
	size_t size = (size_t)fuxi_fb_stride * fuxi_fb_height * 4;
	unsigned int y;

	if (!fuxi_fb_valid)
		return 0;
	/*
	 * arm64 ioremap() 会拒绝 linear-map 帧缓冲，须用 linear map 并清理缓存。
	 * DTS 以 no-map（cont_splash）保留帧缓冲时，改用 ioremap_wc。
	 */
	if (pfn_is_map_memory(PHYS_PFN(fuxi_fb_base)))
		fuxi_fb_lin = phys_to_virt(fuxi_fb_base);
	else
		fuxi_fb_lin = (void __force *)ioremap_wc(fuxi_fb_base, size);
	if (!fuxi_fb_lin)
		return -ENOMEM;
	for (y = 0; y < fuxi_fb_height; y++) {
		u32 *p = (u32 *)fuxi_fb_lin + (phys_addr_t)y * fuxi_fb_stride;

		memset(p, 0, fuxi_fb_width * 4);
		dcache_clean_poc((unsigned long)p, (unsigned long)(p + fuxi_fb_width));
	}
	fuxi_cons_registered = true;
	register_console(&fuxi_console);
	return 0;
}
early_initcall(fuxi_console_init);

/* simpledrm + fbcon 接管帧缓冲后让位，避免两者同时往屏幕上画 */
static int __init fuxi_console_handover(void)
{
	struct device_node *np = of_find_compatible_node(NULL, NULL, "simple-framebuffer");
	bool fb = np && of_device_is_available(np);

	of_node_put(np);
	if (fuxi_cons_registered && fb) {
		pr_info("fuxi: handing screen over to simpledrm/fbcon\n");
		unregister_console(&fuxi_console);
		fuxi_cons_registered = false;
	}
	return 0;
}
late_initcall_sync(fuxi_console_handover);
