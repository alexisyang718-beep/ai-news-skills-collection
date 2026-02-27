# AI Daily Report

每天北京时间 7:00 自动生成 AI 资讯日报，发布到微信公众号。

数据来源于 [ai-hourly-buzz](../ai-hourly-buzz-github) 采集的 `latest-24h.json`（或 `archive.json`），无数据时回退到独立 RSS 采集。

## 功能

- 从 ai-hourly-buzz 读取过去 24 小时 AI 新闻
- AI 摘要生成（DeepSeek，中英文均支持）
- 按类别分组：大厂动态 / AI 产品 / AI 技术 / AI 游戏 / 行业新闻
- 生成 HTML 日报并发布到微信公众号
- 输出存档 HTML 提交到仓库（`output/` 目录）

## 部署（GitHub Actions）

每天 UTC 23:00（北京时间次日 7:00）自动运行。需要在仓库 Settings → Secrets 中配置：

| Secret | 说明 |
|--------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址（可选，默认 `https://api.deepseek.com`）|
| `WECHAT_APP_ID` | 微信公众号 AppID |
| `WECHAT_APP_SECRET` | 微信公众号 AppSecret |
| `GH_PAT` | 用于 checkout ai-hourly-buzz 仓库的 Personal Access Token |

## 本地运行

```bash
pip install -r requirements.txt
cp .env.example .env  # 填入 API 密钥
cd scripts
python main.py --no-publish
```
