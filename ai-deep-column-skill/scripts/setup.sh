#!/bin/bash
# ai-deep-column 快速部署脚本
set -e

INSTALL_DIR="${1:-.}"
echo "=== AI Deep Column 安装 ==="
echo "安装目录: $INSTALL_DIR"

# 创建项目结构
mkdir -p "$INSTALL_DIR/ai-deep-column"/{data,output,logs,scripts/config}

# 复制脚本
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp "$SCRIPT_DIR/scripts/"*.py "$INSTALL_DIR/ai-deep-column/scripts/"
cp "$SCRIPT_DIR/scripts/config/"*.py "$INSTALL_DIR/ai-deep-column/scripts/config/"
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/ai-deep-column/"
cp "$SCRIPT_DIR/.gitignore" "$INSTALL_DIR/ai-deep-column/"

# 复制封面图
if [ -f "$SCRIPT_DIR/../assets/default_cover.jpg" ]; then
  cp "$SCRIPT_DIR/../assets/default_cover.jpg" "$INSTALL_DIR/ai-deep-column/data/"
fi

# 生成 .env 模板
ENV_FILE="$INSTALL_DIR/ai-deep-column/.env"
if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE" << 'EOF'
# DeepSeek API（必填）
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 微信公众号（发布到草稿箱，留空则仅输出本地文件）
WECHAT_APP_ID=
WECHAT_APP_SECRET=

# 企业微信群机器人（可选，用于推送候选话题）
WECOM_WEBHOOK_URL=

# 共享数据目录（ai-hourly-buzz 的 data 目录路径）
# SHARED_DATA_DIR=/path/to/ai-hourly-buzz/data
EOF
  echo "已生成 .env 模板: $ENV_FILE"
fi

# 安装依赖
cd "$INSTALL_DIR/ai-deep-column"
pip install -r requirements.txt

echo ""
echo "=== 安装完成 ==="
echo "1. 编辑 .env 填入你的 API Key 和公众号凭证"
echo "2. 确保 SHARED_DATA_DIR 指向 ai-hourly-buzz/data"
echo "3. 发现候选: cd ai-deep-column && python scripts/main.py discover"
echo "4. 生成专栏: python scripts/main.py generate 1"
