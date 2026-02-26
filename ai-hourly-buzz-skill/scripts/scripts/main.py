#!/usr/bin/env python3
"""AI Hourly Buzz - 主入口

每小时运行：
1. 调用 collector 引擎采集全量数据（10 网页源 + OPML RSS）
2. 精选 Top 15-20 条 AI 相关新闻
3. 推送到企业微信群机器人
4. 输出 JSON 数据供前端展示和日报消费
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# 将 scripts 目录加入 path
sys.path.insert(0, str(Path(__file__).parent))

from collector import (
    UTC,
    collect_all,
    create_session,
    utc_now,
    iso,
    load_archive,
    make_item_id,
    normalize_url,
    normalize_source_for_display,
    maybe_fix_mojibake,
    is_ai_related_record,
    is_hubtoday_placeholder_title,
    normalize_aihubtoday_records,
    event_time,
    parse_iso,
    load_title_zh_cache,
    add_bilingual_fields,
    dedupe_items_by_title_url,
    fetch_opml_rss,
)
from wecom_bot import select_top_items, send_to_wecom


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Hourly Buzz - Collect & Push")
    parser.add_argument("--output-dir", default="data", help="Directory for output JSON files")
    parser.add_argument("--window-hours", type=int, default=24, help="24h window size")
    parser.add_argument("--archive-days", type=int, default=45, help="Keep archive for N days")
    parser.add_argument("--translate-max-new", type=int, default=80, help="Max new EN->ZH title translations")
    parser.add_argument("--rss-opml", default="", help="OPML file path for RSS sources")
    parser.add_argument("--rss-max-feeds", type=int, default=0, help="Max OPML feeds (0=all)")
    parser.add_argument("--top-n", type=int, default=20, help="Top N items to push to WeChat Work")
    parser.add_argument("--wecom-webhook", default="", help="WeChat Work bot webhook URL")
    parser.add_argument("--no-push", action="store_true", help="Skip WeChat Work push")
    args = parser.parse_args()

    now = utc_now()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    archive_path = output_dir / "archive.json"
    latest_path = output_dir / "latest-24h.json"
    status_path = output_dir / "source-status.json"
    title_cache_path = output_dir / "title-zh-cache.json"

    # --- 1. 加载历史归档 ---
    archive = load_archive(archive_path)
    print(f"[Main] Loaded archive: {len(archive)} items")

    # --- 2. 采集 ---
    session = create_session()
    raw_items, statuses = collect_all(session, now)
    print(f"[Main] Collected {len(raw_items)} items from web sources")

    rss_feed_statuses: list[dict] = []
    if args.rss_opml:
        opml_path = Path(args.rss_opml).expanduser()
        if opml_path.exists():
            rss_items, rss_summary_status, rss_feed_statuses = fetch_opml_rss(
                now, opml_path, max_feeds=max(0, int(args.rss_max_feeds))
            )
            raw_items.extend(rss_items)
            statuses.append(rss_summary_status)
            print(f"[Main] Collected {len(rss_items)} items from OPML RSS")

    # --- 3. 更新归档 ---
    from datetime import timedelta

    for raw in raw_items:
        title = raw.title.strip()
        url = normalize_url(raw.url)
        if not title or not url or not url.startswith("http"):
            continue

        item_id = make_item_id(raw.site_id, raw.source, title, url)
        existing = archive.get(item_id)
        if existing is None:
            archive[item_id] = {
                "id": item_id,
                "site_id": raw.site_id,
                "site_name": raw.site_name,
                "source": raw.source,
                "title": title,
                "url": url,
                "published_at": iso(raw.published_at),
                "first_seen_at": iso(now),
                "last_seen_at": iso(now),
            }
        else:
            existing["site_id"] = raw.site_id
            existing["site_name"] = raw.site_name
            existing["source"] = raw.source
            existing["title"] = title
            existing["url"] = url
            if raw.published_at:
                if raw.site_id == "opmlrss" or not existing.get("published_at"):
                    existing["published_at"] = iso(raw.published_at)
            existing["last_seen_at"] = iso(now)

    # 裁剪过期数据
    keep_after = now - timedelta(days=args.archive_days)
    pruned = {}
    for item_id, record in archive.items():
        ts = (
            parse_iso(record.get("last_seen_at"))
            or parse_iso(record.get("published_at"))
            or parse_iso(record.get("first_seen_at"))
            or now
        )
        if ts >= keep_after:
            pruned[item_id] = record
    archive = pruned
    print(f"[Main] Archive after prune: {len(archive)} items")

    # --- 4. 24h 窗口过滤 ---
    window_start = now - timedelta(hours=args.window_hours)
    latest_items_all = []
    for record in archive.values():
        ts = event_time(record)
        if not ts or ts < window_start:
            continue
        normalized = dict(record)
        normalized["title"] = maybe_fix_mojibake(str(normalized.get("title") or ""))
        normalized["source"] = maybe_fix_mojibake(normalize_source_for_display(
            str(normalized.get("site_id") or ""),
            str(normalized.get("source") or ""),
            str(normalized.get("url") or ""),
        ))
        if str(normalized.get("site_id") or "") == "aihubtoday" and is_hubtoday_placeholder_title(
            str(normalized.get("title") or "")
        ):
            continue
        latest_items_all.append(normalized)

    latest_items_all = normalize_aihubtoday_records(latest_items_all)
    latest_items_all.sort(key=lambda x: event_time(x) or datetime.min.replace(tzinfo=UTC), reverse=True)

    # AI 过滤
    latest_items = [r for r in latest_items_all if is_ai_related_record(r)]
    print(f"[Main] 24h window: {len(latest_items_all)} total, {len(latest_items)} AI-related")

    # --- 5. 翻译 + 去重 ---
    title_cache = load_title_zh_cache(title_cache_path)
    latest_items, latest_items_all, title_cache = add_bilingual_fields(
        latest_items, latest_items_all, session, title_cache,
        max_new_translations=max(0, args.translate_max_new),
    )
    latest_items_ai_dedup = dedupe_items_by_title_url(latest_items, random_pick=False)
    latest_items_all_dedup = dedupe_items_by_title_url(latest_items_all, random_pick=True)
    print(f"[Main] After dedup: {len(latest_items_ai_dedup)} AI, {len(latest_items_all_dedup)} all")

    # --- 6. 站点统计 ---
    site_stat = {}
    raw_count_by_site = {}
    for record in latest_items_all:
        sid = record["site_id"]
        raw_count_by_site[sid] = raw_count_by_site.get(sid, 0) + 1

    site_name_by_id = {}
    for record in latest_items_all:
        site_name_by_id[record["site_id"]] = record["site_name"]
    for s in statuses:
        sid = s["site_id"]
        if sid not in site_name_by_id:
            site_name_by_id[sid] = s.get("site_name") or sid

    for record in latest_items_ai_dedup:
        sid = record["site_id"]
        if sid not in site_stat:
            site_stat[sid] = {
                "site_id": sid,
                "site_name": record["site_name"],
                "count": 0,
                "raw_count": raw_count_by_site.get(sid, 0),
            }
        site_stat[sid]["count"] += 1

    for sid, site_name in site_name_by_id.items():
        if sid not in site_stat:
            site_stat[sid] = {
                "site_id": sid,
                "site_name": site_name,
                "count": 0,
                "raw_count": raw_count_by_site.get(sid, 0),
            }

    # --- 7. 写入 JSON ---
    latest_payload = {
        "generated_at": iso(now),
        "window_hours": args.window_hours,
        "total_items": len(latest_items_ai_dedup),
        "total_items_ai_raw": len(latest_items),
        "total_items_raw": len(latest_items_all),
        "total_items_all_mode": len(latest_items_all_dedup),
        "topic_filter": "ai_tech_robotics",
        "archive_total": len(archive),
        "site_count": len(site_stat),
        "source_count": len({f"{i['site_id']}::{i['source']}" for i in latest_items_ai_dedup}),
        "site_stats": sorted(site_stat.values(), key=lambda x: x["count"], reverse=True),
        "items": latest_items_ai_dedup,
        "items_ai": latest_items_ai_dedup,
        "items_all_raw": latest_items_all,
        "items_all": latest_items_all_dedup,
    }

    archive_payload = {
        "generated_at": iso(now),
        "total_items": len(archive),
        "items": sorted(
            archive.values(),
            key=lambda x: parse_iso(x.get("last_seen_at")) or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        ),
    }

    status_payload = {
        "generated_at": iso(now),
        "sites": statuses,
        "successful_sites": sum(1 for s in statuses if s["ok"]),
        "failed_sites": [s["site_id"] for s in statuses if not s["ok"]],
        "zero_item_sites": [s["site_id"] for s in statuses if s.get("ok") and int(s.get("item_count") or 0) == 0],
        "fetched_raw_items": len(raw_items),
        "items_before_topic_filter": len(latest_items_all),
        "items_in_24h": len(latest_items_ai_dedup),
    }

    latest_path.write_text(json.dumps(latest_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    archive_path.write_text(json.dumps(archive_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    status_path.write_text(json.dumps(status_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    title_cache_path.write_text(json.dumps(title_cache, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[Main] Wrote: {latest_path} ({len(latest_items_ai_dedup)} AI items)")
    print(f"[Main] Wrote: {archive_path} ({len(archive)} items)")

    # --- 8. 企业微信推送 ---
    if not args.no_push:
        top_items = select_top_items(latest_items_ai_dedup, top_n=args.top_n)
        webhook_url = args.wecom_webhook or os.environ.get("WECOM_WEBHOOK_URL", "")
        if webhook_url:
            send_to_wecom(top_items, webhook_url=webhook_url, generated_at=iso(now))
        else:
            print("[Main] No WECOM_WEBHOOK_URL set, skipping push")
    else:
        print("[Main] --no-push flag set, skipping WeChat Work push")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
