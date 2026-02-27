# AI Hourly Buzz

每小时自动采集 AI 行业资讯，推送到企业微信，并输出 JSON 数据供 [ai-daily-report](../ai-daily-report-github) 和 [ai-deep-column](../ai-deep-column-github) 使用。

## 功能

- 每小时从 10+ 数据源采集 AI 相关新闻（TechURLs、Buzzing、TopHub、AIbase 等）
- 支持 OPML 订阅源扩展（可选）
- 英文标题自动翻译为中文（Google Translate 免费接口，失败自动降级 DeepSeek）
- 精选 Top 20 条推送到企业微信群机器人
- 输出 `latest-24h.json` 供下游项目消费，并驱动前端网页展示

## 数据文件

| 文件 | 说明 | 是否提交 Git |
|------|------|------------|
| `data/latest-24h.json` | 过去 24 小时 AI 新闻快照 | ✅ 是 |
| `data/title-zh-cache.json` | 标题翻译缓存 | ✅ 是 |
| `data/archive.json` | 全量归档（运行时缓存，45天滚动）| ❌ 否 |
| `data/source-status.json` | 数据源状态快照 | ❌ 否 |

> `archive.json` 不提交到 Git，每次 Actions 运行冷启动重建，避免仓库历史无限膨胀。
> 下游项目只需要 `latest-24h.json`，功能不受影响。

## 部署（GitHub Actions）

每小时整点自动运行。需要在仓库 Settings → Secrets 中配置：

| Secret | 说明 |
|--------|------|
| `WECOM_WEBHOOK_URL` | 企业微信群机器人 Webhook URL |
| `FOLLOW_OPML_B64` | OPML 订阅文件的 Base64 编码（可选） |

GitHub Pages 已启用，前端页面自动从 `latest-24h.json` 读取数据渲染。

## 本地运行

```bash
pip install -r requirements.txt
python scripts/main.py --output-dir data --top-n 20 --no-push
```
