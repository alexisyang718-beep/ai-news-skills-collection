# AI Hourly Buzz（服务器部署版）

每小时自动采集 AI 行业资讯，推送到企业微信，并写入飞书多维表格。

本版本适用于**自有服务器**部署，用 cron 替代 GitHub Actions，用飞书多维表格替代 GitHub Pages 网页。

## 与 GitHub 版本的差异

| | `-github` 版本 | `-server` 版本（本版本）|
|--|--------------|----------------------|
| 调度方式 | GitHub Actions | 服务器 cron |
| 数据展示 | GitHub Pages 静态网页 | 飞书多维表格 |
| archive.json | 每次冷启动重建 | 本地磁盘持久保存 |
| 跨项目数据共享 | checkout 仓库 | 直接读本地文件 |

## 部署步骤

### 1. 上传代码到服务器

```bash
git clone https://github.com/alexisyang718-beep/ai-news-skills-collection.git
cd ai-news-skills-collection
```

### 2. 配置环境变量

```bash
cd ai-hourly-buzz-server
cp .env.example .env
# 编辑 .env，填入各项密钥
```

| 变量 | 必填 | 说明 |
|------|------|------|
| `WECOM_WEBHOOK_URL` | 是 | 企业微信群机器人 Webhook |
| `FEISHU_APP_ID` | 是 | 飞书自建应用 App ID |
| `FEISHU_APP_SECRET` | 是 | 飞书自建应用 App Secret |
| `FEISHU_BITABLE_TOKEN` | 是 | 多维表格 URL 中的 appToken |
| `FEISHU_TABLE_ID` | 是 | 多维表格中的 table ID |
| `DEEPSEEK_API_KEY` | 否 | 标题翻译降级备用 |

### 3. 飞书多维表格准备

在飞书创建多维表格，添加以下字段（均为文本类型）：
`标题` / `英文标题` / `链接` / `来源` / `发布时间` / `采集时间`

将飞书自建应用添加为多维表格的协作者（需有编辑权限）。

### 4. 一键配置 cron

```bash
bash deploy/setup_cron.sh ~/ai-news-skills-collection
```

配置后的定时任务：
- `ai-hourly-buzz`：每小时整点
- `ai-daily-report`：每天北京时间 7:00

### 5. 手动测试

```bash
pip install -r requirements.txt
python scripts/main.py --output-dir data --no-push
```

## 日志

```bash
tail -f ~/ai-news-skills-collection/logs/buzz.log
```
