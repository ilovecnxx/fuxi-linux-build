# Adreno 740 ZAP diagnosis

The screen-audio8 kernel log reports `a740_sqe.fw` and `gmu_gen70200.bin` loaded from the new firmware path (GMU v4.1.9). The signed Fuxi-specific `a740_zap.mdt` then fails PAS initialization with `-22`; the subsequent GMU `GPU_SET` OOB call times out. The kernel code reports that error from the `qcom_pas_init_image()` path after firmware lookup/MDT handling, so this is not a missing SQE/GMU file.

The available evidence cannot distinguish a secure-world signature/metadata rejection from PAS state or platform prerequisites. No bypass, blob replacement, or GPU acceleration claim is justified. Keep Pixman software rendering until a separately scoped GPU validation. Runtime log: `work/claude-logs/rtest-20261029-140912/ssh.txt`. Firmware provenance and hashes: `work/backup/display-install-20261029-104150/gpu-firmware/manifest.json`.
