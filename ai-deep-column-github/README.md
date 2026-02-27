# AI Deep Column

按需生成 AI 行业深度专栏文章，发布到微信公众号。

数据来源于 [ai-hourly-buzz](../ai-hourly-buzz-github) 采集的 `latest-24h.json`，通过热点聚类算法找出被多个来源报道的同一事件，由 AI 撰写深度分析文章。

## 功能

- 从 ai-hourly-buzz 读取 24 小时 AI 新闻
- 热点聚类选题（标题相似度 + 关键实体重叠双重策略）
- 候选话题推送到企业微信，人工选题
- DeepSeek 撰写 800-1500 字深度专栏
- 生成 HTML 并发布到微信公众号

## 部署

目前为手动触发，暂无 GitHub Actions 配置。在本地或服务器上运行：

```bash
pip install -r requirements.txt
cp .env.example .env  # 填入 API 密钥
cd scripts
python main.py
```

需要在 `.env` 中配置（或直接复用 ai-daily-report 的 `.env`）：

| 变量 | 说明 |
|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 |
| `WECHAT_APP_ID` | 微信公众号 AppID |
| `WECHAT_APP_SECRET` | 微信公众号 AppSecret |
| `WECOM_WEBHOOK_URL` | 企业微信群机器人 Webhook URL |
| `SHARED_DATA_DIR` | ai-hourly-buzz 的 data 目录路径（默认 `../ai-hourly-buzz/data`）|
