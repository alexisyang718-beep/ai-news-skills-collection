#!/bin/bash
# ai-hourly-buzz 快速部署脚本
set -e

INSTALL_DIR="${1:-.}"
echo "=== AI Hourly Buzz 安装 ==="
echo "安装目录: $INSTALL_DIR"

# 创建项目结构
mkdir -p "$INSTALL_DIR/ai-hourly-buzz"/{data,feeds,scripts,assets,.github/workflows}

# 复制脚本
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp "$SCRIPT_DIR/scripts/"*.py "$INSTALL_DIR/ai-hourly-buzz/scripts/"
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/ai-hourly-buzz/"
cp "$SCRIPT_DIR/.gitignore" "$INSTALL_DIR/ai-hourly-buzz/"
cp "$SCRIPT_DIR/feeds/follow.example.opml" "$INSTALL_DIR/ai-hourly-buzz/feeds/"

# 复制前端资源（如果存在）
if [ -d "$SCRIPT_DIR/../assets" ]; then
  cp "$SCRIPT_DIR/../assets/"*.js "$INSTALL_DIR/ai-hourly-buzz/assets/" 2>/dev/null || true
  cp "$SCRIPT_DIR/../assets/"*.css "$INSTALL_DIR/ai-hourly-buzz/assets/" 2>/dev/null || true
  cp "$SCRIPT_DIR/../assets/"*.html "$INSTALL_DIR/ai-hourly-buzz/" 2>/dev/null || true
fi

# 生成 .env 模板
ENV_FILE="$INSTALL_DIR/ai-hourly-buzz/.env"
if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE" << 'EOF'
# 企业微信群机器人 Webhook（可选，留空则仅输出到终端）
WECOM_WEBHOOK_URL=
EOF
  echo "已生成 .env 模板: $ENV_FILE"
fi

# GitHub Actions workflow
cp "$SCRIPT_DIR/../scripts/.github/workflows/"*.yml "$INSTALL_DIR/ai-hourly-buzz/.github/workflows/" 2>/dev/null || true

# 安装依赖
cd "$INSTALL_DIR/ai-hourly-buzz"
pip install -r requirements.txt

echo ""
echo "=== 安装完成 ==="
echo "1. 编辑 .env 填入你的配置"
echo "2. （可选）将 RSS OPML 文件放到 feeds/follow.opml"
echo "3. 运行: cd ai-hourly-buzz && python scripts/main.py --output-dir data --no-push"
