# AI News Skills Collection

三个相互关联的 AI 资讯自动化项目：每小时采集、每日日报、深度专栏，共同构成一套完整的 AI 资讯处理流水线。

## 项目关系

```
ai-hourly-buzz（每小时采集）
       │
       │  latest-24h.json
       ▼
 ┌─────┴──────┐
 ▼            ▼
ai-daily-report    ai-deep-column
（每日日报）        （深度专栏）
```

## 目录结构

本仓库包含三套部署方案：

| 文件夹后缀 | 说明 |
|-----------|------|
| `-skill`  | CodeBuddy Skill 格式，原始版本 |
| `-github` | GitHub Actions 部署方案 |
| `-server` | 自有服务器部署方案（cron + 飞书多维表格）|

```
ai-news-skills-collection/
├── ai-hourly-buzz-github/    # GitHub Actions + Pages
├── ai-daily-report-github/   # GitHub Actions
├── ai-deep-column-github/    # 手动触发
├── ai-hourly-buzz-server/    # cron + 飞书多维表格
├── ai-daily-report-server/   # cron
├── ai-deep-column-server/    # 手动触发
├── ai-hourly-buzz-skill/     # 原始 Skill 版本
├── ai-daily-report-skill/    # 原始 Skill 版本
└── ai-deep-column-skill/     # 原始 Skill 版本
```

## 两套方案对比

| | `-github` 方案 | `-server` 方案 |
|--|--------------|--------------|
| 调度 | GitHub Actions | 服务器 cron |
| 数据展示 | GitHub Pages 网页 | 飞书多维表格 |
| archive.json | 每次冷启动重建 | 本地磁盘持久 |
| 数据共享 | checkout 仓库 | 读本地文件 |
| Actions 额度 | 消耗（约 1200 分钟/月）| 不消耗 |
| 适用场景 | 无服务器、轻量部署 | 有服务器、稳定运行 |

## 快速开始（GitHub 方案）

### 1. 配置 Secrets

在仓库 Settings → Secrets and variables → Actions 中添加：

| Secret | 用途 |
|--------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥（日报、专栏使用）|
| `WECHAT_APP_ID` | 微信公众号 AppID |
| `WECHAT_APP_SECRET` | 微信公众号 AppSecret |
| `WECOM_WEBHOOK_URL` | 企业微信群机器人 Webhook |
| `FOLLOW_OPML_B64` | OPML 订阅文件 Base64（可选）|
| `GH_PAT` | 用于日报跨仓库读取数据的 Personal Access Token |

### 2. 启用 GitHub Actions

三个项目的 workflow 文件位于各自 `-github` 文件夹的 `.github/workflows/` 下：

- `ai-hourly-buzz-github`：每小时整点自动运行，结果写入 `data/latest-24h.json`
- `ai-daily-report-github`：每天北京时间 7:00 自动运行
- `ai-deep-column-github`：手动触发

### 3. 本地运行

```bash
# 采集（不推送企微）
cd ai-hourly-buzz-github
pip install -r requirements.txt
python scripts/main.py --output-dir data --no-push

# 生成日报（不发布微信）
cd ai-daily-report-github
pip install -r requirements.txt
cd scripts && python main.py --no-publish

# 生成专栏
cd ai-deep-column-github
pip install -r requirements.txt
cd scripts && python main.py
```

## 关键设计说明

### Token 优化
- `ai-hourly-buzz` 标题翻译使用 Google Translate 免费接口，零 AI 消耗
- `ai-daily-report` 标题翻译同样优先免费接口，DeepSeek 仅作降级备用
- 所有 AI prompt 已精简，减少约 30% input token

### 仓库大小控制
- `archive.json`（全量归档，每小时变动）**不提交到 Git**，避免历史无限膨胀
- 下游项目只依赖 `latest-24h.json`，功能不受影响
- `title-zh-cache.json`（翻译缓存）正常提交，避免重复翻译

### GitHub Actions 额度（免费账号 2000 分钟/月）
- `ai-hourly-buzz`：约 720 次/月 × 1-2 分钟 ≈ 1000 分钟
- `ai-daily-report`：约 30 次/月 × 3-5 分钟 ≈ 120 分钟
- 合计约 1200 分钟，在免费额度内

## License

MIT
