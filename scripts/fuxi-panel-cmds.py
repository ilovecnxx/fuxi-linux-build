#!/usr/bin/env python3
"""从厂商 DTB 的 qcom,mdss_dsi_* 面板节点生成主线 DRM 面板驱动的上电/下电命令序列（C 代码片段）。

厂商命令格式（downstream dsi_panel.c）：每条 7 字节头 + 数据
  [type][last][channel][flags][wait_ms][len_hi][len_lo][payload...]
  type 0x05 DCS 短写无参（payload = cmd, 0 填充）、0x15 DCS 短写 1 参、0x39 DCS 长写、
       0x29 generic 长写、0x13/0x23 generic 短写
用法: fuxi-panel-cmds.py <面板 dtsi> <timing 序号> <qcom,mdss-dsi-on-command|...>
输出: 缩进一级的 mipi_dsi_*_multi 调用，可直接贴进驱动函数体
"""
import re
import sys


def parse(blk, prop):
    m = re.search(re.escape(prop) + r" = \[([0-9a-f ]+)\]", blk)
    if not m:
        sys.exit(f"{prop} not found")
    b = [int(x, 16) for x in m.group(1).split()]
    cmds, k = [], 0
    while k < len(b):
        dtype, wait, dlen = b[k], b[k + 4], (b[k + 5] << 8) | b[k + 6]
        cmds.append((dtype, wait, b[k + 7:k + 7 + dlen]))
        k += 7 + dlen
    if k != len(b):
        sys.exit("trailing bytes")
    return cmds


def emit(dtype, payload):
    if dtype == 0x05:
        payload = payload[:1]
    if dtype in (0x05, 0x15, 0x39):
        fn = "mipi_dsi_dcs_write_seq_multi"
    elif dtype in (0x03, 0x13, 0x23, 0x29):
        fn = "mipi_dsi_generic_write_seq_multi"
    else:
        sys.exit(f"unsupported dsi type {dtype:#x}")
    args = [f"0x{x:02x}" for x in payload]
    lines, cur = [], f"\t{fn}(&dsi_ctx, "
    indent = " " * len(f"\t{fn}(") + "\t" * 0
    for i, a in enumerate(args):
        piece = a + (", " if i < len(args) - 1 else ");")
        if len(cur.expandtabs(8)) + len(piece) > 80:
            lines.append(cur.rstrip())
            cur = "\t\t\t\t     " + piece
        else:
            cur += piece
    lines.append(cur)
    return "\n".join(lines)


def main():
    path, idx, prop = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    t = open(path, encoding="utf-8").read()
    i = t.index(f"timing@{idx} {{")
    j = t.find("timing@", i + 1)
    blk = t[i:j if j > 0 else len(t)]
    for dtype, wait, payload in parse(blk, prop):
        print(emit(dtype, payload))
        if wait:
            print(f"\tmipi_dsi_msleep(&dsi_ctx, {wait});")


if __name__ == "__main__":
    main()
