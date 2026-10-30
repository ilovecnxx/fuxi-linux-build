# source/ 说明（范围）

本目录是 **v0.3.0 时期（发布镜像 #191）** 的构建材料快照：`kernel.config`、`kernel.diff`、`kernel.dtb`、
`variants/`、`patches/`、`build-records/`、`initramfs/`。

**v0.4.0 起不再增量同步**：

- 当前内核源码：`build/linux` 分支 `fuxi/20261031`（基线 `5b0764a53`）；
- 全量补丁：`work/patches/full-tree-20261031/full-20261031.diff`（本地，不随仓库发布）；
- 当前基线镜像 `s2idle2`(#207) 的 `.config/.dtb/.build.json` 在本地 `work/kbuild/`；
- 最新构建方式见仓库 README 的「构建与验证」。
