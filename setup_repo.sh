#!/bin/bash
# 一键初始化并推送到 GitHub
# 使用方式：
#   1. 在 GitHub 网页上新建一个空仓库（不要勾选 README），例如名 kids-math-game
#   2. 修改下面两行为你的信息
#   3. 运行：bash setup_repo.sh

# ===== 修改这里 =====
GITHUB_USER="你的GitHub用户名"
REPO_NAME="kids-math-game"
# ====================

set -e

cd "$(dirname "$0")"

# 初始化 git
git init -b main
git config user.name "$GITHUB_USER"
git config user.email "$GITHUB_USER@users.noreply.github.com"

# 添加所有文件并提交
git add .
git commit -m "feat: 数学小天才 Kivy 工程 + GitHub Actions 自动打包"

# 关联远程仓库并推送
git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"
git push -u origin main

echo ""
echo "✅ 推送完成！"
echo "👉 打开 https://github.com/$GITHUB_USER/$REPO_NAME/actions"
echo "👉 点 'Build APK' 工作流 → 'Run workflow'"
echo "👉 等 15-20 分钟后，在 Artifacts 下载 kids-math-game-apk"
