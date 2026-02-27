"""飞书多维表格写入模块

将 latest-24h.json 中的新条目追加写入飞书多维表格（Bitable）。
通过对比上次写入的记录 ID，只写入本次新增的条目，避免重复。

环境变量：
    FEISHU_APP_ID        飞书自建应用 App ID
    FEISHU_APP_SECRET    飞书自建应用 App Secret
    FEISHU_BITABLE_TOKEN 多维表格的 app_token（URL 中的那串 ID）
    FEISHU_TABLE_ID      表格 ID（sheet 的 table_id）
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests

SH_TZ = ZoneInfo("Asia/Shanghai")

FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
FEISHU_BITABLE_TOKEN = os.environ.get("FEISHU_BITABLE_TOKEN", "")
FEISHU_TABLE_ID = os.environ.get("FEISHU_TABLE_ID", "")

_token_cache: dict[str, Any] = {"token": "", "expires_at": 0}


def _get_tenant_access_token() -> str:
    """获取飞书 tenant_access_token，有效期内复用缓存"""
    now = time.time()
    if _token_cache["token"] and _token_cache["expires_at"] > now + 60:
        return _token_cache["token"]

    resp = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"飞书鉴权失败: {data}")

    _token_cache["token"] = data["tenant_access_token"]
    _token_cache["expires_at"] = now + int(data.get("expire", 7200))
    return _token_cache["token"]


def _bitable_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_get_tenant_access_token()}",
        "Content-Type": "application/json",
    }


def _append_records(records: list[dict[str, Any]]) -> int:
    """批量写入记录，每批最多 500 条，返回实际写入条数"""
    if not records:
        return 0

    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_BITABLE_TOKEN}/tables/{FEISHU_TABLE_ID}/records/batch_create"
    written = 0
    batch_size = 500

    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        payload = {"records": [{"fields": r} for r in batch]}
        resp = requests.post(url, headers=_bitable_headers(), json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"写入飞书多维表格失败: {data}")
        written += len(batch)

    return written


def _load_written_ids(cache_path: Path) -> set[str]:
    """加载已写入飞书的条目 ID 集合"""
    if not cache_path.exists():
        return set()
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        return set(data) if isinstance(data, list) else set()
    except Exception:
        return set()


def _save_written_ids(cache_path: Path, ids: set[str]) -> None:
    cache_path.write_text(json.dumps(sorted(ids), ensure_ascii=False), encoding="utf-8")


def sync_to_feishu(latest_path: Path, cache_path: Path) -> int:
    """
    将 latest-24h.json 中的新条目写入飞书多维表格。
    返回本次写入的条数，0 表示无新增或配置缺失。
    """
    if not all([FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_BITABLE_TOKEN, FEISHU_TABLE_ID]):
        print("[Feishu] 环境变量未配置，跳过飞书写入")
        return 0

    if not latest_path.exists():
        print("[Feishu] latest-24h.json 不存在，跳过")
        return 0

    payload = json.loads(latest_path.read_text(encoding="utf-8"))
    items = payload.get("items_ai") or payload.get("items") or []

    written_ids = _load_written_ids(cache_path)
    new_items = [it for it in items if it.get("id") and it["id"] not in written_ids]

    if not new_items:
        print("[Feishu] 无新增条目，跳过写入")
        return 0

    records = []
    for it in new_items:
        title_zh = it.get("title_zh") or ""
        title_en = it.get("title_en") or ""
        title = it.get("title") or ""
        display_title = title_zh or title

        # 发布时间转北京时间字符串
        published_raw = it.get("published_at") or it.get("first_seen_at") or ""
        published_str = published_raw
        if published_raw:
            try:
                from collector import parse_iso
                dt = parse_iso(published_raw)
                if dt:
                    published_str = dt.astimezone(SH_TZ).strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass

        records.append({
            "标题": display_title,
            "英文标题": title_en or title,
            "链接": it.get("url") or "",
            "来源": it.get("source") or it.get("site_name") or "",
            "发布时间": published_str,
            "采集时间": datetime.now(SH_TZ).strftime("%Y-%m-%d %H:%M"),
        })

    count = _append_records(records)
    new_ids = {it["id"] for it in new_items}
    # 只保留最近 5000 条 ID，防止缓存无限增长
    all_ids = written_ids | new_ids
    if len(all_ids) > 5000:
        all_ids = set(sorted(all_ids)[-5000:])
    _save_written_ids(cache_path, all_ids)

    print(f"[Feishu] 写入 {count} 条新记录")
    return count
