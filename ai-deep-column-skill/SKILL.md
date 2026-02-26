---
name: ai-deep-column-skill
description: AI hot topic deep analysis column system. Clusters news from ai-hourly-buzz into hot topics using title similarity and entity overlap, generates 800-1500 word in-depth analysis articles via DeepSeek LLM, outputs WeChat-compatible HTML, and publishes to WeChat Official Account. Semi-automatic workflow with candidate topic discovery and manual selection. This skill should be used when the user wants to set up, deploy, customize, or troubleshoot the AI deep column pipeline.
---

# AI Deep Column

Hot topic deep analysis column generator with semi-automatic workflow.

## Overview

This skill provides a deep analysis column pipeline that:
1. Loads pre-filtered AI news from ai-hourly-buzz (`latest-24h.json/items_ai`)
2. Clusters news into hot topics using dual strategy: title similarity + entity overlap
3. Pushes candidate topics to Enterprise WeChat for manual selection
4. Generates 800-1500 word in-depth analysis articles via DeepSeek
5. Outputs WeChat-compatible HTML and publishes to draft box

## Architecture

```
ai-hourly-buzz/data/latest-24h.json (items_ai)
        │
        ▼
  topic_selector.py ──→ wecom_notify.py (候选推送)
  (热点聚类引擎)              │
        │               用户选择话题编号
        ▼                     │
  material_collector.py ◄─────┘
  (素材收集)
        │
        ▼
  article_writer.py (DeepSeek 长文生成)
        │
        ▼
  html_generator.py ──→ wechat_publisher.py
  (微信HTML)              (草稿发布)
```

### Hot Topic Clustering

Dual strategy clustering engine:
- **Strategy 1**: Title similarity (SequenceMatcher ≥ 0.58)
- **Strategy 2**: Normalized entity overlap (≥1 concrete entity + ≥2 total)
- Filters: minimum 4 articles, ≥2 sources, excludes GitHub repos
- Entity normalization: maps company/product names across languages

### Article Structure

Generated articles follow this structure:
- Title (≤25 chars, punchy)
- Lead paragraph (50-80 chars)
- Event Background
- Key Points (2-3 insights)
- Industry Impact
- Future Outlook

## Installation

```bash
bash scripts/setup.sh /path/to/install
```

## Configuration

### Environment Variables (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `DEEPSEEK_API_KEY` | **Yes** | DeepSeek API key |
| `DEEPSEEK_BASE_URL` | No | API base URL (default: `https://api.deepseek.com`) |
| `DEEPSEEK_MODEL` | No | Model name (default: `deepseek-chat`) |
| `WECHAT_APP_ID` | No | WeChat Official Account App ID |
| `WECHAT_APP_SECRET` | No | WeChat Official Account App Secret |
| `WECOM_WEBHOOK_URL` | No | Enterprise WeChat webhook for candidate push |
| `SHARED_DATA_DIR` | No | Path to ai-hourly-buzz data directory |

### Clustering Parameters

Edit `scripts/config/settings.py`:
- `CLUSTER_SIMILARITY_THRESHOLD` — Title similarity threshold (default: 0.58)
- `CLUSTER_MIN_ARTICLES` — Minimum articles per cluster (default: 4)
- `CLUSTER_TIME_WINDOW_HOURS` — Time window in hours (default: 28)
- `MAX_CANDIDATE_TOPICS` — Max candidates to show (default: 8)
- `ARTICLE_WORD_COUNT` — Target word count range (default: "800-1500")

### AI Prompts

Edit `scripts/config/prompts.py` to customize article generation style and structure.

## Usage

Three operating modes:

```bash
cd ai-deep-column

# 1. Discover: Scan hot topics → push candidates to WeChat / terminal
python scripts/main.py discover

# 2. Generate: Select topic by number → generate column → publish
python scripts/main.py generate 1    # Select topic #1

# 3. Auto: Discover → auto-select hottest → generate (fully automatic)
python scripts/main.py auto
```

### Semi-Automatic Workflow

1. Run `discover` (scheduled or manual) — system scans and pushes candidates
2. Review candidates in Enterprise WeChat or terminal
3. Run `generate N` to produce the column for topic N
4. Article is published to WeChat Official Account draft box

### Output

- `output/{title}_{date}.html` — WeChat-compatible HTML article
- `data/candidates.json` — Current candidate topics
- `data/publish_history.json` — Publishing history

## Cost

- Single column generation: ~1600 tokens (~¥0.01 with DeepSeek)
- Materials use meta descriptions, not full article text

## Upstream Dependency

Requires **ai-hourly-buzz** to be running. Set `SHARED_DATA_DIR` to point to its `data/` directory.

Falls back to `archive.json` if `latest-24h.json` is unavailable.

## Dependencies

- Python 3.10+
- requests, openai, python-dateutil, pytz, python-dotenv
