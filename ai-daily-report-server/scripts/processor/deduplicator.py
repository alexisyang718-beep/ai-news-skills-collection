# -*- coding: utf-8 -*-
"""
去重器
基于标题相似度和URL去重
"""

import logging
import json
from typing import List, Dict, Set
from difflib import SequenceMatcher
from pathlib import Path
from datetime import datetime

from crawler.models import ScoredNewsItem

logger = logging.getLogger(__name__)


class Deduplicator:
    """去重器"""

    def __init__(self, threshold: float = 0.8, cache_file: Path = None):
        self.threshold = threshold
        self.cache_file = cache_file
        self.processed_urls: Set[str] = set()
        if cache_file:
            self._load_cache()

    def _load_cache(self):
        try:
            if self.cache_file and self.cache_file.exists():
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.processed_urls = set(data.get("processed_urls", []))
                    logger.info(f"缓存加载: {len(self.processed_urls)} 个URL")
        except Exception as e:
            logger.warning(f"加载缓存失败: {e}")

    def _save_cache(self):
        if not self.cache_file:
            return
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump({
                    "processed_urls": list(self.processed_urls),
                    "last_update": datetime.now().isoformat()
                }, f, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")

    def deduplicate(self, news_list: List[ScoredNewsItem]) -> List[ScoredNewsItem]:
        if not news_list:
            return []

        sorted_news = sorted(news_list, key=lambda x: x.relevance_score, reverse=True)
        unique = []
        seen_titles: Dict[str, ScoredNewsItem] = {}

        for item in sorted_news:
            url = item.raw_item.url
            title = item.raw_item.title.lower().strip()

            if url in self.processed_urls:
                continue

            is_dup = False
            for seen_title, seen_item in seen_titles.items():
                if SequenceMatcher(None, title, seen_title).ratio() >= self.threshold:
                    is_dup = True
                    # 官方源替换非官方源
                    if item.raw_item.source_type == "official" and seen_item.raw_item.source_type != "official":
                        unique.remove(seen_item)
                        del seen_titles[seen_title]
                        unique.append(item)
                        seen_titles[title] = item
                    break

            if not is_dup:
                unique.append(item)
                seen_titles[title] = item

        # 更新缓存
        for item in unique:
            self.processed_urls.add(item.raw_item.url)
        self._save_cache()

        logger.info(f"去重: {len(news_list)} -> {len(unique)} 条")
        return unique
