#!/bin/bash
# 把当前进度（文档/镜像/脚本/研究记录）发布到 GitHub
# 用法: bash scripts/publish-progress.sh "提交说明"
set -e
B="/home/user/文档/deepseek-harness/default-workspace/linux-android"
REPO="${FUXI_GH_REPO:-ilovecnxx/fuxi-linux-build}"
MSG="${1:-progress update $(date +%Y-%m-%d_%H:%M)}"
STAGE="$B/work/gh-publish"
export GIT_TERMINAL_PROMPT=0
if [ ! -d "$STAGE/.git" ]; then
  rm -rf "$STAGE"
  gh repo clone "$REPO" "$STAGE" -- --depth 1 >/dev/null 2>&1 || {
    mkdir -p "$STAGE" && cd "$STAGE" && git init -q && git remote add origin "https://github.com/${REPO}.git"
  }
fi
cd "$STAGE"
mkdir -p docs images scripts research boot-images
cp -f "$B"/docs/*.md docs/ 2>/dev/null || true
cp -f "$B"/research/*.md research/ 2>/dev/null || true
cp -f "$B"/scripts/*.sh scripts/ 2>/dev/null || true
# 只上传较小的关键镜像（<6MB），避免仓库过大
for f in "$B"/work/kbuild/boot-fuxi-*.img; do
  [ -f "$f" ] || continue
  sz=$(stat -c %s "$f")
  [ "$sz" -lt 6291456 ] && cp -f "$f" boot-images/ || true
done
{
  echo "# fuxi 主线移植进度"
  echo
  echo "最近更新：$(date '+%Y-%m-%d %H:%M %Z')"
  echo
  echo "## 当前状态"
  echo '见 docs/交接-给CODEX.md（含 D 系列实验记录）与 docs/参考项目与上游支持调研-fuxi.md。'
  echo
  echo "## 关键结论"
  echo "- EDK2 固件可启动，BDS 正常；异步异常已定位到 FuxiLinuxBoot 驱动并修复"
  echo "- 内核 EFI stub 已执行到 ExitBootServices，但内核本体 head.S 尚未进入"
  echo "- 已实现绕过 stub 的直接跳转（MMU/D-cache off + 内联 cache flush）"
  echo
  echo "## 镜像"
  ls -l boot-images 2>/dev/null | tail -n +2 | awk '{print "- " $9 " (" $5 " bytes)"}'
} > PROGRESS.md
git add -A
git -c user.name="fuxi-agent" -c user.email="fuxi-agent@local" commit -q -m "$MSG" || { echo "无改动"; exit 0; }
git push -q origin HEAD:master 2>&1 | tail -2 || git push -q origin HEAD:main 2>&1 | tail -2
echo "已推送: $MSG"
