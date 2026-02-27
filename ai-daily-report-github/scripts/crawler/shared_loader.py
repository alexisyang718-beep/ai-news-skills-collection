# -*- coding: utf-8 -*-
"""
共享数据加载器
从 ai-hourly-buzz 的 archive.json 读取已采集数据
"""

import json
import logging
import hashlib
from datetime import datetime, timedelta, timezone
from typing import List
from pathlib import Path

from crawler.models import RawNewsItem

logger = logging.getLogger(__name__)

_CST = timezone(timedelta(hours=8))


class SharedDataLoader:
    """从 ai-hourly-buzz 共享数据加载新闻"""

    def __init__(self, archive_path: Path = None):
        from config.settings import SHARED_ARCHIVE_FILE
        self.archive_path = archive_path or SHARED_ARCHIVE_FILE

    def load(self, hours: int = 28) -> List[RawNewsItem]:
        """
        加载最近N小时的共享数据

        Args:
            hours: 加载多少小时内的数据

        Returns:
            RawNewsItem 列表
        """
        if not self.archive_path.exists():
            logger.warning(f"共享数据文件不存在: {self.archive_path}")
            return []

        try:
            with open(self.archive_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"读取共享数据失败: {e}")
            return []

        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            logger.warning("共享数据为空")
            return []

        now = datetime.now(_CST)
        cutoff = now - timedelta(hours=hours)

        results = []
        for item in items:
            try:
                # 解析时间 — 兼容多种字段名
                pub_time = None
                ts = (item.get("published_at")
                      or item.get("first_seen_at")
                      or item.get("timestamp")
                      or item.get("pubDate")
                      or item.get("pub_time"))
                if ts:
                    try:
                        if isinstance(ts, (int, float)):
                            pub_time = datetime.fromtimestamp(ts, tz=_CST)
                        else:
                            from dateutil import parser
                            pub_time = parser.parse(str(ts))
                            if pub_time.tzinfo is None:
                                pub_time = pub_time.replace(tzinfo=_CST)
                    except Exception:
                        pass

                # 时间过滤
                if pub_time and pub_time < cutoff:
                    continue

                url = item.get("url", "") or item.get("link", "")
                title = item.get("title", "")
                if not url or not title:
                    continue

                item_id = item.get("id") or hashlib.md5(url.encode()).hexdigest()

                # 检测语言
                cn_chars = sum(1 for c in title if '\u4e00' <= c <= '\u9fff')
                language = "zh" if cn_chars / max(len(title), 1) > 0.3 else "en"

                # 来源信息 — 兼容 site_name/source 字段
                source = item.get("source", "") or item.get("site_name", "")
                source_key = item.get("site_id", "") or f"shared_{source}" if source else "shared"
                raw = RawNewsItem(
                    id=item_id,
                    title=title,
                    url=url,
                    source_key=source_key,
                    source_name=source or "AI热讯",
                    source_type="shared",
                    language=language,
                    pub_time=pub_time,
                    summary=item.get("summary", "") or item.get("description", ""),
                    content="",
                )
                results.append(raw)

            except Exception as e:
                logger.debug(f"解析共享数据条目失败: {e}")
                continue

        logger.info(f"从共享数据加载: {len(results)} 条（{hours}小时内）")
        return results
