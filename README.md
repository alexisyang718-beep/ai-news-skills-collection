# AI News Skills Collection

A collection of three interconnected CodeBuddy skills for automated AI news aggregation, daily report generation, and deep analysis column writing.

## 🎯 Overview

This repository contains three skills that work together as a complete AI news processing pipeline:

```
┌─────────────────────┐
│  ai-hourly-buzz     │  ← Collects AI news from 10+ sources hourly
│  (Data Collection)  │
└─────────┬───────────┘
          │
          ▼  shared data (archive.json, latest-24h.json)
          │
    ┌─────┴─────┐
    ▼           ▼
┌───────────┐ ┌───────────────┐
│ ai-daily  │ │ ai-deep       │
│ -report   │ │ -column       │
│           │ │               │
│ Daily     │ │ Hot topic     │
│ digest    │ │ deep analysis │
└───────────┘ └───────────────┘
```

## 📦 Skills Included

### 1. ai-hourly-buzz-skill
**Multi-source AI news collection engine**

- Scrapes 10+ web sources (Hacker News, GitHub Trending, Product Hunt, 36Kr, etc.)
- Parses OPML RSS feeds for additional sources
- Filters content by AI/tech relevance
- Translates English titles to Chinese
- Outputs structured JSON data
- Optional Enterprise WeChat push notifications

### 2. ai-daily-report-skill
**Automated AI daily digest generator**

- Reads news from ai-hourly-buzz shared data
- Filters and deduplicates using keyword scoring
- Uses DeepSeek API for classification, summarization, and translation
- Generates WeChat-compatible HTML and Markdown reports
- Publishes to WeChat Official Account draft box

### 3. ai-deep-column-skill
**Hot topic deep analysis column generator**

- Clusters news into hot topics using title similarity and entity overlap
- Semi-automatic workflow with candidate topic discovery
- Generates 800-1500 word in-depth analysis articles via DeepSeek
- Outputs WeChat-compatible HTML for publishing

## 🚀 Quick Start

### Installation

Each skill has its own setup script:

```bash
# Install ai-hourly-buzz (data collection layer)
bash ai-hourly-buzz-skill/scripts/setup.sh /path/to/install

# Install ai-daily-report (depends on ai-hourly-buzz data)
bash ai-daily-report-skill/scripts/setup.sh /path/to/install

# Install ai-deep-column (depends on ai-hourly-buzz data)
bash ai-deep-column-skill/scripts/setup.sh /path/to/install
```

### Configuration

All skills use environment variables for sensitive configuration. Create a `.env` file in each project directory:

```bash
# Common - DeepSeek API (required for ai-daily-report and ai-deep-column)
DEEPSEEK_API_KEY=your-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# WeChat Official Account (optional)
WECHAT_APP_ID=your-app-id
WECHAT_APP_SECRET=your-app-secret

# Enterprise WeChat Bot (optional)
WECOM_WEBHOOK_URL=your-webhook-url

# Shared data directory
SHARED_DATA_DIR=/path/to/ai-hourly-buzz/data
```

### Usage

```bash
# 1. Run hourly news collection
cd ai-hourly-buzz
python scripts/main.py --output-dir data --no-push

# 2. Generate daily report
cd ai-daily-report
python scripts/main.py --no-publish

# 3. Discover hot topics and generate column
cd ai-deep-column
python scripts/main.py discover
python scripts/main.py generate 1  # Select topic #1
```

## 📊 Data Flow

1. **ai-hourly-buzz** collects and stores news in `data/archive.json` and `data/latest-24h.json`
2. **ai-daily-report** reads from shared data, processes with AI, generates daily digest
3. **ai-deep-column** reads from shared data, clusters hot topics, generates deep analysis

## 🔧 GitHub Actions

Each skill includes workflow templates for automated scheduling:

- `ai-hourly-buzz`: Runs hourly
- `ai-daily-report`: Runs daily at 7:00 AM Beijing time
- `ai-deep-column`: Manual trigger or scheduled

### Required Secrets

| Secret | Used By | Description |
|--------|---------|-------------|
| `DEEPSEEK_API_KEY` | daily-report, deep-column | DeepSeek API key |
| `WECHAT_APP_ID` | daily-report, deep-column | WeChat Official Account App ID |
| `WECHAT_APP_SECRET` | daily-report, deep-column | WeChat Official Account App Secret |
| `WECOM_WEBHOOK_URL` | hourly-buzz, deep-column | Enterprise WeChat webhook URL |
| `FOLLOW_OPML_B64` | hourly-buzz | Base64-encoded OPML for RSS feeds |
| `GH_PAT` | daily-report | GitHub PAT for cross-repo checkout |

## 📁 Project Structure

```
ai-news-skills-collection/
├── README.md
├── ai-hourly-buzz-skill/
│   ├── SKILL.md
│   ├── scripts/
│   │   ├── setup.sh
│   │   ├── requirements.txt
│   │   ├── feeds/
│   │   │   └── follow.example.opml
│   │   └── scripts/
│   │       ├── main.py
│   │       ├── collector.py
│   │       └── wecom_bot.py
│   └── assets/
├── ai-daily-report-skill/
│   ├── SKILL.md
│   ├── scripts/
│   │   ├── setup.sh
│   │   ├── requirements.txt
│   │   └── scripts/
│   │       ├── main.py
│   │       ├── config/
│   │       ├── ai_service/
│   │       ├── crawler/
│   │       ├── processor/
│   │       └── publisher/
│   └── assets/
└── ai-deep-column-skill/
    ├── SKILL.md
    ├── scripts/
    │   ├── setup.sh
    │   ├── requirements.txt
    │   └── scripts/
    │       ├── main.py
    │       ├── config/
    │       ├── topic_selector.py
    │       ├── material_collector.py
    │       ├── article_writer.py
    │       ├── html_generator.py
    │       ├── wechat_publisher.py
    │       └── wecom_notify.py
    └── assets/
```

## 📄 License

MIT License

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
