/* SPDX-License-Identifier: GPL-2.0 */
/*
 * fuxi：内建板级 DTB（CONFIG_FUXI_FORCE_BUILTIN_DTB 时 setup_arch 用它代替 ABL 传入的 DTB）。
 * ABL 只能处理厂商 DTB（它要把 dtbo 分区的 overlay 叠上去，叠到主线 DTB 上会卡死），
 * 所以 boot 镜像里附加厂商 DTB 当"诱饵"，内核这里换成主线 DTB。
 * 构建顺序：先 make qcom/sm8550-xiaomi-fuxi-min.dtb，再 make Image（scripts/fuxi-build-abl.sh）。
 */
	.section .rodata, "a"
	.balign	8
	.globl	fuxi_dtb
fuxi_dtb:
	.incbin	"arch/arm64/boot/dts/qcom/sm8550-xiaomi-fuxi-min.dtb"
	.globl	fuxi_dtb_end
fuxi_dtb_end:
