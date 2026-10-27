// SPDX-License-Identifier: GPL-2.0-only
/*
 * Panel driver for the Xiaomi 13 (fuxi) "m3 38 0c 0a" Samsung AMOLED
 * command mode DSI panel with DSC (1080x2400).
 *
 * Init/exit sequences are taken from the vendor device tree node
 * qcom,mdss_dsi_m3_38_0c_0a_dsc_cmd (timing@0, 60 Hz; the 90/120 Hz timings only
 * differ in three commands, selected with the "refresh" parameter); scripts/fuxi-panel-cmds.py
 * converts them.
 */

#include <linux/backlight.h>
#include <linux/delay.h>
#include <linux/gpio/consumer.h>
#include <linux/module.h>
#include <linux/of.h>
#include <linux/regulator/consumer.h>

#include <drm/display/drm_dsc.h>
#include <drm/drm_mipi_dsi.h>
#include <drm/drm_modes.h>
#include <drm/drm_panel.h>
#include <drm/drm_probe_helper.h>

/*
 * The panel's refresh rate is selected by three commands in the init
 * sequence (vendor timing@0/1/2 = 60/120/90 Hz, identical porches).
 */
static unsigned int refresh = 60;
module_param(refresh, uint, 0444);
MODULE_PARM_DESC(refresh, "Refresh rate in Hz: 60 (default), 90 or 120");

struct xiaomi_fuxi_rate {
	unsigned int hz;
	u8 reg60;	/* 0x60: 0x00 = 120 Hz, 0x08 = 60/90 Hz */
	u8 regbd;	/* 0xbd at offset 0x30 */
	u8 regf2;	/* 0xf2 at offset 0x16, second byte */
};

static const struct xiaomi_fuxi_rate xiaomi_fuxi_rates[] = {
	{ .hz = 60, .reg60 = 0x08, .regbd = 0x04, .regf2 = 0x70 },
	{ .hz = 90, .reg60 = 0x08, .regbd = 0x01, .regf2 = 0x88 },
	{ .hz = 120, .reg60 = 0x00, .regbd = 0x04, .regf2 = 0x70 },
};

static const struct xiaomi_fuxi_rate *xiaomi_fuxi_rate(void)
{
	int i;

	for (i = 0; i < ARRAY_SIZE(xiaomi_fuxi_rates); i++)
		if (xiaomi_fuxi_rates[i].hz == refresh)
			return &xiaomi_fuxi_rates[i];
	return &xiaomi_fuxi_rates[0];
}

struct xiaomi_fuxi_panel {
	struct drm_panel panel;
	struct mipi_dsi_device *dsi;
	struct drm_dsc_config dsc;
	struct gpio_desc *reset_gpio;
	struct regulator_bulk_data supplies[3];
};

/* power-up order and the settle time after each supply (vendor dsi_panel_pwr_supply_M3) */
static const struct {
	const char *name;
	unsigned int post_on_ms;
} xiaomi_fuxi_supplies[] = {
	{ "vddio", 2 },
	{ "vddd", 0 },
	{ "vci", 10 },
};

static inline struct xiaomi_fuxi_panel *to_xiaomi_fuxi_panel(struct drm_panel *panel)
{
	return container_of(panel, struct xiaomi_fuxi_panel, panel);
}

static int xiaomi_fuxi_on(struct xiaomi_fuxi_panel *ctx)
{
	const struct xiaomi_fuxi_rate *rate = xiaomi_fuxi_rate();
	struct mipi_dsi_multi_context dsi_ctx = { .dsi = ctx->dsi };

	ctx->dsi->mode_flags |= MIPI_DSI_MODE_LPM;

	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x9e, 0x11, 0x00, 0x00, 0x89,
				     0x30, 0x80, 0x09, 0xd8, 0x04, 0x38, 0x00,
				     0x28, 0x02, 0x1c, 0x02, 0x1c, 0x02, 0x00,
				     0x02, 0x3b, 0x00, 0x20, 0x03, 0x92, 0x00,
				     0x07, 0x00, 0x0e, 0x02, 0xe0, 0x02, 0x8b,
				     0x18, 0x00, 0x10, 0xf0, 0x03, 0x0c, 0x20,
				     0x00, 0x06, 0x0b, 0x0b, 0x33, 0x0e, 0x1c,
				     0x2a, 0x38, 0x46, 0x54, 0x62, 0x69, 0x70,
				     0x77, 0x79, 0x7b, 0x7d, 0x7e, 0x01, 0x02,
				     0x01, 0x00, 0x09, 0x40, 0x09, 0xbe, 0x19,
				     0xfc, 0x19, 0xfa, 0x19, 0xf8, 0x1a, 0x38,
				     0x1a, 0x78, 0x1a, 0xb6, 0x2a, 0xb6, 0x2a,
				     0xf4, 0x2a, 0xf4, 0x4b, 0x34, 0x63, 0x74,
				     0x00);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x9d, 0x01);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x11);
	mipi_dsi_msleep(&dsi_ctx, 120);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x35, 0x00);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x2a, 0x00, 0x00, 0x04, 0x37);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x2b, 0x00, 0x00, 0x09, 0x5f);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0x5a, 0x5a);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x60, rate->reg60);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xb0, 0x00, 0x30, 0xbd);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xbd, rate->regbd);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xb0, 0x00, 0x16, 0xf2);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf2, 0x01, rate->regf2);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf7, 0x0f);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0xa5, 0xa5);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0x5a, 0x5a);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xb0, 0x00, 0x36, 0xc5);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xc5, 0x11);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xb0, 0x00, 0x3a, 0xc5);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xc5, 0x3f, 0x21);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xb0, 0x00, 0x52, 0xc5);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xc5, 0x3f, 0x21);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0xa5, 0xa5);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0x5a, 0x5a);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xb0, 0x00, 0x0d, 0x94);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x94, 0x20);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x53, 0x28);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x51, 0x00, 0x00);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf7, 0x0f);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0xa5, 0xa5);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0x5a, 0x5a);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xe5, 0x15);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xb0, 0x00, 0x3d, 0xf4);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf4, 0xf0);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xed, 0x43, 0x49, 0x42, 0x03);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0xa5, 0xa5);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0x5a, 0x5a);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xb0, 0x00, 0x0a, 0xb1);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xb1, 0x18, 0x48, 0x20);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0xa5, 0xa5);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0x5a, 0x5a);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xb0, 0x01, 0x64, 0x92);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x92, 0x70);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0xa5, 0xa5);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0x5a, 0x5a);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xb0, 0x02, 0x7e, 0x92);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x92, 0x0f);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0xa5, 0xa5);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0x5a, 0x5a);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xbb, 0x30);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf7, 0x0f);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0xa5, 0xa5);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0x5a, 0x5a);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xb0, 0x00, 0x20, 0xf6);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf6, 0xf0);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0xa5, 0xa5);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0x5a, 0x5a);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xb0, 0x00, 0x4e, 0x98);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x98, 0x00, 0x09, 0x80);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xb0, 0x00, 0x0f, 0xf6);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf6, 0x10);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf7, 0x0f);
	mipi_dsi_msleep(&dsi_ctx, 20);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x29);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0xa5, 0xa5);

	return dsi_ctx.accum_err;
}

static int xiaomi_fuxi_off(struct xiaomi_fuxi_panel *ctx)
{
	struct mipi_dsi_multi_context dsi_ctx = { .dsi = ctx->dsi };

	ctx->dsi->mode_flags |= MIPI_DSI_MODE_LPM;

	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0x5a, 0x5a);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x28);
	mipi_dsi_msleep(&dsi_ctx, 20);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xb0, 0x00, 0x4e, 0x98);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x98, 0x01, 0x09, 0x80);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xb0, 0x00, 0x0f, 0xf6);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf6, 0x02);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf7, 0x0f);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0xa5, 0xa5);
	mipi_dsi_msleep(&dsi_ctx, 100);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x10);
	mipi_dsi_msleep(&dsi_ctx, 120);

	return dsi_ctx.accum_err;
}

static void xiaomi_fuxi_power_off(struct xiaomi_fuxi_panel *ctx)
{
	gpiod_set_value_cansleep(ctx->reset_gpio, 1);
	regulator_bulk_disable(ARRAY_SIZE(ctx->supplies), ctx->supplies);
}

static int xiaomi_fuxi_prepare(struct drm_panel *panel)
{
	struct xiaomi_fuxi_panel *ctx = to_xiaomi_fuxi_panel(panel);
	struct device *dev = &ctx->dsi->dev;
	int i, ret;

	for (i = 0; i < ARRAY_SIZE(ctx->supplies); i++) {
		ret = regulator_enable(ctx->supplies[i].consumer);
		if (ret) {
			dev_err(dev, "failed to enable %s: %d\n",
				ctx->supplies[i].supply, ret);
			while (--i >= 0)
				regulator_disable(ctx->supplies[i].consumer);
			return ret;
		}
		if (xiaomi_fuxi_supplies[i].post_on_ms)
			msleep(xiaomi_fuxi_supplies[i].post_on_ms);
	}

	/* vendor qcom,mdss-dsi-reset-sequence = <0 1>, <1 10> */
	gpiod_set_value_cansleep(ctx->reset_gpio, 1);
	usleep_range(1000, 2000);
	gpiod_set_value_cansleep(ctx->reset_gpio, 0);
	usleep_range(10000, 11000);

	ret = xiaomi_fuxi_on(ctx);
	if (ret < 0) {
		dev_err(dev, "failed to initialize panel: %d\n", ret);
		xiaomi_fuxi_power_off(ctx);
		return ret;
	}

	return 0;
}

static int xiaomi_fuxi_unprepare(struct drm_panel *panel)
{
	struct xiaomi_fuxi_panel *ctx = to_xiaomi_fuxi_panel(panel);
	int ret;

	ret = xiaomi_fuxi_off(ctx);
	if (ret < 0)
		dev_err(&ctx->dsi->dev, "failed to un-initialize panel: %d\n", ret);

	xiaomi_fuxi_power_off(ctx);
	return 0;
}

/* vendor timing@0: h 124/32/124, v 128/24/132; .clock is set for the selected rate */
static const struct drm_display_mode xiaomi_fuxi_mode = {
	.clock = (1080 + 124 + 32 + 124) * (2400 + 128 + 24 + 132) * 60 / 1000,
	.hdisplay = 1080,
	.hsync_start = 1080 + 124,
	.hsync_end = 1080 + 124 + 32,
	.htotal = 1080 + 124 + 32 + 124,
	.vdisplay = 2400,
	.vsync_start = 2400 + 128,
	.vsync_end = 2400 + 128 + 24,
	.vtotal = 2400 + 128 + 24 + 132,
	.width_mm = 69,
	.height_mm = 153,
	.type = DRM_MODE_TYPE_DRIVER,
};

static int xiaomi_fuxi_get_modes(struct drm_panel *panel,
				 struct drm_connector *connector)
{
	struct drm_display_mode mode = xiaomi_fuxi_mode;

	mode.clock = mode.htotal * mode.vtotal * xiaomi_fuxi_rate()->hz / 1000;

	return drm_connector_helper_get_modes_fixed(connector, &mode);
}

static const struct drm_panel_funcs xiaomi_fuxi_panel_funcs = {
	.prepare = xiaomi_fuxi_prepare,
	.unprepare = xiaomi_fuxi_unprepare,
	.get_modes = xiaomi_fuxi_get_modes,
};

static int xiaomi_fuxi_bl_update_status(struct backlight_device *bl)
{
	struct mipi_dsi_device *dsi = bl_get_data(bl);
	u16 brightness = backlight_get_brightness(bl);
	int ret;

	dsi->mode_flags &= ~MIPI_DSI_MODE_LPM;
	ret = mipi_dsi_dcs_set_display_brightness_large(dsi, brightness);
	dsi->mode_flags |= MIPI_DSI_MODE_LPM;

	return ret;
}

static const struct backlight_ops xiaomi_fuxi_bl_ops = {
	.update_status = xiaomi_fuxi_bl_update_status,
};

static struct backlight_device *
xiaomi_fuxi_create_backlight(struct mipi_dsi_device *dsi)
{
	struct device *dev = &dsi->dev;
	const struct backlight_properties props = {
		.type = BACKLIGHT_RAW,
		.brightness = 2047,
		.max_brightness = 4095,
	};

	return devm_backlight_device_register(dev, dev_name(dev), dev, dsi,
					      &xiaomi_fuxi_bl_ops, &props);
}

static int xiaomi_fuxi_probe(struct mipi_dsi_device *dsi)
{
	struct device *dev = &dsi->dev;
	struct xiaomi_fuxi_panel *ctx;
	int i, ret;

	ctx = devm_drm_panel_alloc(dev, struct xiaomi_fuxi_panel, panel,
				   &xiaomi_fuxi_panel_funcs,
				   DRM_MODE_CONNECTOR_DSI);
	if (IS_ERR(ctx))
		return PTR_ERR(ctx);

	for (i = 0; i < ARRAY_SIZE(ctx->supplies); i++)
		ctx->supplies[i].supply = xiaomi_fuxi_supplies[i].name;
	ret = devm_regulator_bulk_get(dev, ARRAY_SIZE(ctx->supplies), ctx->supplies);
	if (ret < 0)
		return dev_err_probe(dev, ret, "failed to get regulators\n");

	/* the bootloader left the panel on: keep it that way until prepare */
	ctx->reset_gpio = devm_gpiod_get(dev, "reset", GPIOD_ASIS);
	if (IS_ERR(ctx->reset_gpio))
		return dev_err_probe(dev, PTR_ERR(ctx->reset_gpio),
				     "failed to get reset-gpios\n");

	ctx->dsi = dsi;
	mipi_dsi_set_drvdata(dsi, ctx);

	dsi->lanes = 4;
	dsi->format = MIPI_DSI_FMT_RGB888;
	dsi->mode_flags = MIPI_DSI_CLOCK_NON_CONTINUOUS;

	/* matches the PPS sent in xiaomi_fuxi_on() (DSC 1.1, 8 bpc, 8 bpp) */
	ctx->dsc.dsc_version_major = 1;
	ctx->dsc.dsc_version_minor = 1;
	ctx->dsc.slice_height = 40;
	ctx->dsc.slice_width = 540;
	ctx->dsc.slice_count = 2;
	ctx->dsc.bits_per_component = 8;
	ctx->dsc.bits_per_pixel = 8 << 4;
	ctx->dsc.block_pred_enable = true;
	dsi->dsc = &ctx->dsc;

	ctx->panel.prepare_prev_first = true;

	ctx->panel.backlight = xiaomi_fuxi_create_backlight(dsi);
	if (IS_ERR(ctx->panel.backlight))
		return dev_err_probe(dev, PTR_ERR(ctx->panel.backlight),
				     "failed to create backlight\n");

	ret = devm_drm_panel_add(dev, &ctx->panel);
	if (ret)
		return ret;

	return devm_mipi_dsi_attach(dev, dsi);
}

static const struct of_device_id xiaomi_fuxi_of_match[] = {
	{ .compatible = "xiaomi,fuxi-m3-38-0c-0a" },
	{ /* sentinel */ }
};
MODULE_DEVICE_TABLE(of, xiaomi_fuxi_of_match);

static struct mipi_dsi_driver xiaomi_fuxi_driver = {
	.probe = xiaomi_fuxi_probe,
	.driver = {
		.name = "panel-xiaomi-fuxi",
		.of_match_table = xiaomi_fuxi_of_match,
	},
};
module_mipi_dsi_driver(xiaomi_fuxi_driver);

MODULE_DESCRIPTION("Panel driver for the Xiaomi 13 (fuxi) AMOLED DSC command mode panel");
MODULE_LICENSE("GPL");
