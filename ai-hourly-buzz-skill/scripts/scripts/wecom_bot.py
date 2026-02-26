"""企业微信群机器人 Webhook 推送模块"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import requests

WECOM_WEBHOOK_URL = os.environ.get("WECOM_WEBHOOK_URL", "")
SH_TZ = ZoneInfo("Asia/Shanghai")


def format_news_markdown(items: list[dict[str, Any]], generated_at: str | None = None) -> str:
    """将新闻条目格式化为企业微信 Markdown 消息"""
    now_sh = datetime.now(tz=SH_TZ)
    time_str = now_sh.strftime("%m月%d日 %H:%M")

    lines = [f"## AI 热讯 | {time_str}\n"]

    for i, item in enumerate(items, 1):
        title_zh = item.get("title_zh") or ""
        title_en = item.get("title_en") or ""
        title = item.get("title") or ""
        url = item.get("url") or ""
        site_name = item.get("site_name") or ""
        source = item.get("source") or ""

        # 优先中文标题
        display_title = title_zh if title_zh else title
        if not display_title:
            display_title = title_en

        # 截断过长标题
        if len(display_title) > 60:
            display_title = display_title[:57] + "..."

        source_tag = f"`{site_name}`" if site_name else ""
        if source and source != site_name:
            source_tag += f" {source}"

        lines.append(f"**{i}.** [{display_title}]({url})")
        if source_tag:
            lines.append(f"> {source_tag}\n")
        else:
            lines.append("")

    lines.append(f"\n---\n> 数据更新: {time_str} | 共 {len(items)} 条")
    return "\n".join(lines)


def send_to_wecom(items: list[dict[str, Any]], webhook_url: str = "", generated_at: str | None = None) -> bool:
    """推送消息到企业微信群机器人"""
    url = webhook_url or WECOM_WEBHOOK_URL
    if not url:
        print("[WeComBot] No webhook URL configured, skipping push")
        return False

    if not items:
        print("[WeComBot] No items to push, skipping")
        return False

    markdown_content = format_news_markdown(items, generated_at)

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": markdown_content,
        },
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        if result.get("errcode") == 0:
            print(f"[WeComBot] Successfully pushed {len(items)} items")
            return True
        else:
            print(f"[WeComBot] Push failed: {result}")
            return False
    except Exception as exc:
        print(f"[WeComBot] Push error: {exc}")
        return False


def select_top_items(items: list[dict[str, Any]], top_n: int = 20) -> list[dict[str, Any]]:
    """从 AI 过滤后的条目中精选 Top N 条

    优选策略：
    1. 按站点多样性分散选取（避免某一站点占据过多）
    2. 优先选择有中文标题的条目
    3. 优先选择时间最新的
    """
    if len(items) <= top_n:
        return items

    # 按站点分组
    by_site: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        sid = item.get("site_id") or "unknown"
        by_site.setdefault(sid, []).append(item)

    selected: list[dict[str, Any]] = []
    selected_urls: set[str] = set()

    # 轮询式选取：每轮从每个站点取 1 条
    site_queues = {sid: list(sitems) for sid, sitems in by_site.items()}
    round_num = 0

    while len(selected) < top_n and site_queues:
        empty_sites = []
        for sid, queue in site_queues.items():
            if len(selected) >= top_n:
                break
            if not queue:
                empty_sites.append(sid)
                continue
            item = queue.pop(0)
            url = item.get("url") or ""
            if url not in selected_urls:
                selected.append(item)
                selected_urls.add(url)
        for sid in empty_sites:
            del site_queues[sid]
        round_num += 1

    return selected
