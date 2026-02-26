---
name: ai-hourly-buzz-skill
description: AI news hourly collection and aggregation system. Collects AI-related news from 10+ web sources and OPML RSS feeds, deduplicates, translates EN→ZH, filters by AI relevance, and outputs structured JSON data. Supports enterprise WeChat push notifications. This skill should be used when the user wants to set up, deploy, customize, or troubleshoot the AI hourly news collection system.
---

# AI Hourly Buzz

Multi-source AI news collection engine with hourly scheduling.

## Overview

This skill provides a complete AI news collection system that:
1. Scrapes 10+ web sources (Hacker News, GitHub Trending, Product Hunt, 36Kr, etc.)
2. Parses OPML RSS feeds for additional sources
3. Filters content by AI/tech relevance using keyword rules
4. Translates English titles to Chinese (via free Google Translate)
5. Deduplicates by title similarity and URL normalization
6. Outputs structured JSON data (`archive.json`, `latest-24h.json`)
7. Optionally pushes top items to Enterprise WeChat group bot

## Architecture

```
Web Sources (10+) ──┐
                     ├──→ collector.py ──→ main.py ──→ JSON output
OPML RSS Feeds ──────┘         │                          │
                               └─ wecom_bot.py ──→ WeChat push
```

### Output Data

- `data/archive.json` — Full archive (rolling 45 days)
- `data/latest-24h.json` — 24-hour window with `items_ai` (filtered) and `items_all` (raw)
- `data/source-status.json` — Source health monitoring
- `data/title-zh-cache.json` — Translation cache

### Item Schema

```json
{
  "id": "hash_id",
  "site_id": "hackernews",
  "site_name": "Hacker News",
  "source": "Hacker News",
  "title": "Original English Title",
  "url": "https://...",
  "published_at": "2026-01-01T00:00:00Z",
  "first_seen_at": "2026-01-01T00:00:00Z",
  "last_seen_at": "2026-01-01T01:00:00Z",
  "title_zh": "中文标题",
  "title_en": "English Title",
  "title_bilingual": "中文标题 | English Title"
}
```

## Installation

```bash
bash scripts/setup.sh /path/to/install
```

The setup script:
1. Creates project directory structure
2. Copies all source code
3. Generates `.env` template
4. Installs Python dependencies

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `WECOM_WEBHOOK_URL` | No | Enterprise WeChat bot webhook URL |

### OPML RSS Feeds

Place your OPML file at `feeds/follow.opml`. See `feeds/follow.example.opml` for format.

For GitHub Actions deployment, base64-encode the OPML and store as `FOLLOW_OPML_B64` secret.

## Usage

```bash
# Local run (no push)
python scripts/main.py --output-dir data --no-push

# With RSS feeds
python scripts/main.py --output-dir data --rss-opml feeds/follow.opml --no-push

# Full run with WeChat push
python scripts/main.py --output-dir data --top-n 20

# CLI options
python scripts/main.py --help
```

### GitHub Actions

The included workflow (`.github/workflows/update-news.yml`) runs hourly.

Required secrets:
- `WECOM_WEBHOOK_URL` — Enterprise WeChat webhook (optional)
- `FOLLOW_OPML_B64` — Base64-encoded OPML file (optional)

## Downstream Projects

This project's output data is consumed by:
- **ai-daily-report** — Reads `archive.json` for daily AI digest
- **ai-deep-column** — Reads `latest-24h.json/items_ai` for hot topic clustering

## Dependencies

- Python 3.10+
- requests, beautifulsoup4, feedparser, python-dateutil
