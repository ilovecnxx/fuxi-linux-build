# screen-audio8 设备记录（2026-10-29）

- 内核：`7.3.0+ #184`；boot ID `73e26334-82e6-491c-98ee-4597ee565503`。
- `recovery_b` 镜像：`work/kbuild/abl-fuxi-screen-audio8.img`；SHA256 `0e00d418ef9e66a916502288ad8e03e32c2b64f8e17bf085975dc4bc86a53090`；镜像长度回读校验通过。
- MSM DRM/DSI：connector connected，模式 `1080x2400`；启动快照中 Phoc framebuffer 绑定到活动 CRTC/plane；无 simpledrm 设备。背光 `ae94000.dsi.0`，最大值 4095。
- Phosh active、NRestarts=0；采样日志未见 DSI transfer failure 或 DPU underrun。Adreno ZAP 初始化返回 `-22`，单独跟踪。
- **未完成**：实物画质、亮度、刷新稳定、触控及熄屏/唤醒验收。数字状态不构成物理显示通过。
- 回退镜像 `audio-probe4` 与完整原分区备份保留。
