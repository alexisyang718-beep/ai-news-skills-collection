# AI Deep Column（服务器部署版）

按需生成 AI 行业深度专栏文章，发布到微信公众号。

本版本适用于**自有服务器**部署，数据直接从本地 `ai-hourly-buzz-server/data/` 读取。

## 运行

手动触发（选题后生成文章）：

```bash
pip install -r requirements.txt
# 设置数据目录
export SHARED_DATA_DIR=../ai-hourly-buzz-server/data
cd scripts

# 发现热点话题（推送候选到企微）
python main.py discover

# 生成指定话题的文章（选择企微推送的编号）
python main.py generate 1
```

## 配置

在 `ai-hourly-buzz-server/.env` 中追加：

| 变量 | 说明 |
|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥（文章生成）|
| `WECHAT_APP_ID` | 微信公众号 AppID |
| `WECHAT_APP_SECRET` | 微信公众号 AppSecret |
| `WECOM_WEBHOOK_URL` | 企业微信 Webhook（候选话题通知）|
| `SHARED_DATA_DIR` | buzz 的 data 目录路径 |
