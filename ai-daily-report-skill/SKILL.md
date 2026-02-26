---
name: ai-daily-report-skill
description: AI daily news report generation system. Reads news data from ai-hourly-buzz, uses DeepSeek LLM for classification, summarization, and translation, generates formatted HTML/Markdown reports, and publishes to WeChat Official Account drafts. This skill should be used when the user wants to set up, deploy, customize, or troubleshoot the AI daily report pipeline.
---

# AI Daily Report

Automated AI industry daily digest with LLM-powered analysis and WeChat publishing.

## Overview

This skill provides a full daily report pipeline that:
1. Loads news from ai-hourly-buzz shared data (`archive.json`)
2. Filters and deduplicates using keyword scoring and title similarity
3. Uses DeepSeek API for AI-powered classification (5 categories), summarization, and translation
4. Generates formatted HTML (WeChat-compatible inline styles) and Markdown reports
5. Publishes to WeChat Official Account draft box

## Architecture

```
ai-hourly-buzz/data/archive.json
        │
        ▼
  shared_loader.py ──→ filter.py ──→ deduplicator.py
                                          │
                                          ▼
                              deepseek_client.py
                              ├── classifier.py (5类分类)
                              ├── summarizer.py (摘要生成)
                              └── translator.py (翻译)
                                          │
                                          ▼
                              html_generator.py ──→ wechat_publisher.py
                              markdown_generator.py
```

### Five Categories

1. Large Model Updates (大模型动态)
2. AI Applications (AI应用)
3. Industry News (行业动态)
4. Research Frontier (研究前沿)
5. Developer Tools (开发者工具)

## Installation

```bash
bash scripts/setup.sh /path/to/install
```

The setup script creates project structure, copies code, generates `.env` template, and installs dependencies.

## Configuration

### Environment Variables (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `DEEPSEEK_API_KEY` | **Yes** | DeepSeek API key for LLM calls |
| `DEEPSEEK_BASE_URL` | No | API base URL (default: `https://api.deepseek.com`) |
| `DEEPSEEK_MODEL` | No | Model name (default: `deepseek-chat`) |
| `WECHAT_APP_ID` | No | WeChat Official Account App ID |
| `WECHAT_APP_SECRET` | No | WeChat Official Account App Secret |
| `SHARED_DATA_DIR` | No | Path to ai-hourly-buzz data directory |

### Keyword Scoring

Edit `scripts/config/keywords.py` to customize the multi-layer keyword scoring system:
- Layer 1: Core AI keywords (highest weight)
- Layer 2: Tech company names
- Layer 3: Industry terms
- Layer 4: General tech terms

### RSS Sources

Edit `scripts/config/rss_sources.py` for additional independent RSS crawling (optional, mainly uses shared data).

## Usage

```bash
# Generate report (local output only)
cd ai-daily-report
python scripts/main.py --no-publish

# Generate and publish to WeChat
python scripts/main.py

# CLI options
python scripts/main.py --help
```

### GitHub Actions

The included workflow (`.github/workflows/daily_report.yml`) runs daily at 7:00 AM Beijing time.

Required secrets:
- `DEEPSEEK_API_KEY` — DeepSeek API key
- `WECHAT_APP_ID` / `WECHAT_APP_SECRET` — WeChat credentials
- `GH_PAT` — GitHub PAT for cross-repo checkout of ai-hourly-buzz

**Important**: Update `YOUR_GITHUB_USERNAME` in the workflow file to your actual GitHub username.

### Output

- `output/AI资讯日报_M月D日.html` — WeChat-compatible HTML
- `output/report_YYYY-MM-DD_HHMMSS.md` — Markdown archive
- `data/publish_history.json` — Publishing history

## Upstream Dependency

Requires **ai-hourly-buzz** to be running and producing `archive.json` data. Set `SHARED_DATA_DIR` to point to its `data/` directory.

## Dependencies

- Python 3.10+
- requests, openai, feedparser, beautifulsoup4, lxml, readability-lxml
- python-dateutil, pytz, python-dotenv
