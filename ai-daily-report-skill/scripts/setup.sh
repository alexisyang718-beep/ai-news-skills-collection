#!/bin/bash
# ai-daily-report 快速部署脚本
set -e

INSTALL_DIR="${1:-.}"
echo "=== AI Daily Report 安装 ==="
echo "安装目录: $INSTALL_DIR"

# 创建项目结构
mkdir -p "$INSTALL_DIR/ai-daily-report"/{data,output,logs,scripts/{config,ai_service,crawler,processor,publisher},.github/workflows}

# 复制脚本
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp "$SCRIPT_DIR/scripts/"*.py "$INSTALL_DIR/ai-daily-report/scripts/" 2>/dev/null || true
cp "$SCRIPT_DIR/scripts/config/"*.py "$INSTALL_DIR/ai-daily-report/scripts/config/"
cp "$SCRIPT_DIR/scripts/ai_service/"*.py "$INSTALL_DIR/ai-daily-report/scripts/ai_service/"
cp "$SCRIPT_DIR/scripts/crawler/"*.py "$INSTALL_DIR/ai-daily-report/scripts/crawler/"
cp "$SCRIPT_DIR/scripts/processor/"*.py "$INSTALL_DIR/ai-daily-report/scripts/processor/"
cp "$SCRIPT_DIR/scripts/publisher/"*.py "$INSTALL_DIR/ai-daily-report/scripts/publisher/"
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/ai-daily-report/"
cp "$SCRIPT_DIR/.gitignore" "$INSTALL_DIR/ai-daily-report/"

# 复制封面图
if [ -f "$SCRIPT_DIR/../assets/default_cover.jpg" ]; then
  cp "$SCRIPT_DIR/../assets/default_cover.jpg" "$INSTALL_DIR/ai-daily-report/data/"
fi

# 生成 .env 模板
ENV_FILE="$INSTALL_DIR/ai-daily-report/.env"
if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE" << 'EOF'
# DeepSeek API（必填）
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 微信公众号（发布到草稿箱，留空则仅输出本地文件）
WECHAT_APP_ID=
WECHAT_APP_SECRET=

# 共享数据目录（ai-hourly-buzz 的 data 目录路径）
# SHARED_DATA_DIR=/path/to/ai-hourly-buzz/data
EOF
  echo "已生成 .env 模板: $ENV_FILE"
fi

# 安装依赖
cd "$INSTALL_DIR/ai-daily-report"
pip install -r requirements.txt

echo ""
echo "=== 安装完成 ==="
echo "1. 编辑 .env 填入你的 API Key 和公众号凭证"
echo "2. 确保 SHARED_DATA_DIR 指向 ai-hourly-buzz/data"
echo "3. 运行: cd ai-daily-report && python scripts/main.py"
