# AI Daily Report（服务器部署版）

每天北京时间 7:00 自动生成 AI 资讯日报，发布到微信公众号。

本版本适用于**自有服务器**部署，数据直接从本地 `ai-hourly-buzz-server/data/` 读取，无需 checkout GitHub 仓库。

## 部署

由 `ai-hourly-buzz-server/deploy/setup_cron.sh` 统一配置，无需单独操作。

手动运行：

```bash
pip install -r requirements.txt
SHARED_DATA_DIR=../ai-hourly-buzz-server/data
cd scripts && python main.py --no-publish
```

## 配置

复用 `ai-hourly-buzz-server/.env` 中的密钥，额外需要：

| 变量 | 说明 |
|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥（摘要生成）|
| `WECHAT_APP_ID` | 微信公众号 AppID |
| `WECHAT_APP_SECRET` | 微信公众号 AppSecret |
| `SHARED_DATA_DIR` | buzz 的 data 目录路径（cron 脚本自动设置）|

## 日志

```bash
tail -f ~/ai-news-skills-collection/logs/daily-report.log
```
