// SPDX-License-Identifier: GPL-2.0-only
/*
 * Camera module power switch for bring-up of the Xiaomi 13 (fuxi) cameras.
 *
 * Powers a camera module (supplies in DT order, MCLK, reset) on and off from
 * sysfs so that the sensor can be identified over CCI with i2c-dev before a
 * real sensor driver exists:
 *
 *   echo 1 > /sys/bus/platform/devices/<node>/power
 *   i2ctransfer -y <cci bus> w2@0x1a 0x00 0x16 r2
 *   echo 0 > /sys/bus/platform/devices/<node>/power
 *
 * DT: compatible "xiaomi,fuxi-camera-power"; "supply-names" lists the
 * "<name>-supply" properties in power-up order; "clocks" = MCLK
 * ("clock-frequency", default 19.2 MHz); "reset-gpios" (asserted = in reset).
 */

#include <linux/clk.h>
#include <linux/delay.h>
#include <linux/gpio/consumer.h>
#include <linux/module.h>
#include <linux/mod_devicetable.h>
#include <linux/mutex.h>
#include <linux/of.h>
#include <linux/platform_device.h>
#include <linux/regulator/consumer.h>

#define FUXI_CAM_MAX_SUPPLIES	8

struct fuxi_cam_power {
	struct device *dev;
	struct regulator_bulk_data supplies[FUXI_CAM_MAX_SUPPLIES];
	int num_supplies;
	struct clk *mclk;
	u32 mclk_rate;
	struct gpio_desc *reset;
	struct mutex lock;
	bool on;
};

static int fuxi_cam_power_on(struct fuxi_cam_power *cp)
{
	int i, ret;

	gpiod_set_value_cansleep(cp->reset, 1);

	for (i = 0; i < cp->num_supplies; i++) {
		ret = regulator_enable(cp->supplies[i].consumer);
		if (ret) {
			dev_err(cp->dev, "failed to enable %s: %d\n",
				cp->supplies[i].supply, ret);
			goto err_supplies;
		}
		usleep_range(1000, 1500);
	}

	ret = clk_set_rate(cp->mclk, cp->mclk_rate);
	if (ret)
		dev_warn(cp->dev, "failed to set MCLK to %u: %d\n", cp->mclk_rate, ret);
	ret = clk_prepare_enable(cp->mclk);
	if (ret) {
		dev_err(cp->dev, "failed to enable MCLK: %d\n", ret);
		goto err_supplies;
	}
	usleep_range(1000, 1500);

	gpiod_set_value_cansleep(cp->reset, 0);
	usleep_range(10000, 11000);

	dev_info(cp->dev, "powered on (MCLK %lu Hz)\n", clk_get_rate(cp->mclk));
	return 0;

err_supplies:
	while (--i >= 0)
		regulator_disable(cp->supplies[i].consumer);
	return ret;
}

static void fuxi_cam_power_off(struct fuxi_cam_power *cp)
{
	int i;

	gpiod_set_value_cansleep(cp->reset, 1);
	usleep_range(1000, 1500);
	clk_disable_unprepare(cp->mclk);
	for (i = cp->num_supplies - 1; i >= 0; i--)
		regulator_disable(cp->supplies[i].consumer);
	dev_info(cp->dev, "powered off\n");
}

static ssize_t power_show(struct device *dev, struct device_attribute *attr,
			  char *buf)
{
	struct fuxi_cam_power *cp = dev_get_drvdata(dev);

	return sysfs_emit(buf, "%d\n", cp->on);
}

static ssize_t power_store(struct device *dev, struct device_attribute *attr,
			   const char *buf, size_t count)
{
	struct fuxi_cam_power *cp = dev_get_drvdata(dev);
	bool on;
	int ret = 0;

	ret = kstrtobool(buf, &on);
	if (ret)
		return ret;

	mutex_lock(&cp->lock);
	if (on && !cp->on) {
		ret = fuxi_cam_power_on(cp);
		if (!ret)
			cp->on = true;
	} else if (!on && cp->on) {
		fuxi_cam_power_off(cp);
		cp->on = false;
	}
	mutex_unlock(&cp->lock);

	return ret ? ret : count;
}
static DEVICE_ATTR_RW(power);

static struct attribute *fuxi_cam_power_attrs[] = {
	&dev_attr_power.attr,
	NULL
};
ATTRIBUTE_GROUPS(fuxi_cam_power);

static int fuxi_cam_power_probe(struct platform_device *pdev)
{
	struct device *dev = &pdev->dev;
	struct fuxi_cam_power *cp;
	const char *names[FUXI_CAM_MAX_SUPPLIES];
	int i, ret;

	cp = devm_kzalloc(dev, sizeof(*cp), GFP_KERNEL);
	if (!cp)
		return -ENOMEM;
	cp->dev = dev;
	mutex_init(&cp->lock);

	ret = of_property_read_string_array(dev->of_node, "supply-names", names,
					    FUXI_CAM_MAX_SUPPLIES);
	if (ret < 0)
		return dev_err_probe(dev, ret, "no supply-names\n");
	cp->num_supplies = ret;
	for (i = 0; i < cp->num_supplies; i++)
		cp->supplies[i].supply = names[i];
	ret = devm_regulator_bulk_get(dev, cp->num_supplies, cp->supplies);
	if (ret)
		return dev_err_probe(dev, ret, "failed to get supplies\n");

	cp->mclk = devm_clk_get(dev, NULL);
	if (IS_ERR(cp->mclk))
		return dev_err_probe(dev, PTR_ERR(cp->mclk), "failed to get MCLK\n");
	cp->mclk_rate = 19200000;
	of_property_read_u32(dev->of_node, "clock-frequency", &cp->mclk_rate);

	cp->reset = devm_gpiod_get(dev, "reset", GPIOD_OUT_HIGH);
	if (IS_ERR(cp->reset))
		return dev_err_probe(dev, PTR_ERR(cp->reset), "failed to get reset\n");

	platform_set_drvdata(pdev, cp);
	return 0;
}

static void fuxi_cam_power_remove(struct platform_device *pdev)
{
	struct fuxi_cam_power *cp = platform_get_drvdata(pdev);

	mutex_lock(&cp->lock);
	if (cp->on)
		fuxi_cam_power_off(cp);
	cp->on = false;
	mutex_unlock(&cp->lock);
}

static const struct of_device_id fuxi_cam_power_of_match[] = {
	{ .compatible = "xiaomi,fuxi-camera-power" },
	{ }
};
MODULE_DEVICE_TABLE(of, fuxi_cam_power_of_match);

static struct platform_driver fuxi_cam_power_driver = {
	.probe = fuxi_cam_power_probe,
	.remove = fuxi_cam_power_remove,
	.driver = {
		.name = "fuxi-camera-power",
		.of_match_table = fuxi_cam_power_of_match,
		.dev_groups = fuxi_cam_power_groups,
	},
};
module_platform_driver(fuxi_cam_power_driver);

MODULE_DESCRIPTION("Xiaomi 13 camera module power switch for bring-up");
MODULE_LICENSE("GPL");
