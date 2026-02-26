# -*- coding: utf-8 -*-
"""
RSS解析器
从RSS源获取新闻列表
"""

import feedparser
import requests
import logging
import hashlib
import time
import ssl
from datetime import datetime
from typing import List, Dict, Optional

from crawler.models import RawNewsItem

logger = logging.getLogger(__name__)
ssl._create_default_https_context = ssl._create_unverified_context


class RSSParser:
    """RSS源解析器"""

    def __init__(self, sources: list, headers: dict, timeout: int = 30, delay: float = 1):
        self.sources = [s for s in sources if s.get("extraction_method") != "web_scrape"]
        self.headers = headers
        self.timeout = timeout
        self.delay = delay

    def parse_all(self) -> List[RawNewsItem]:
        all_news = []
        for source in self.sources:
            try:
                logger.info(f"解析RSS: {source['name']}")
                news = self._parse_single(source)
                all_news.extend(news)
                logger.info(f"  -> {len(news)} 条")
                time.sleep(self.delay)
            except Exception as e:
                logger.error(f"解析 {source['name']} 失败: {e}")
        return all_news

    def _parse_single(self, source: Dict) -> List[RawNewsItem]:
        news_list = []
        try:
            resp = requests.get(source["url"], headers=self.headers, timeout=self.timeout)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)

            for entry in feed.entries:
                item = self._parse_entry(entry, source)
                if item:
                    news_list.append(item)
        except Exception as e:
            logger.error(f"RSS {source['name']}: {e}")
        return news_list

    def _parse_entry(self, entry, source: Dict) -> Optional[RawNewsItem]:
        title = entry.get("title", "").strip()
        url = entry.get("link", "").strip()
        if not title or not url:
            return None

        pub_time = self._parse_time(entry)
        summary = ""
        if "summary" in entry:
            summary = entry.summary
        elif "description" in entry:
            summary = entry.description

        from bs4 import BeautifulSoup
        summary = BeautifulSoup(summary, "html.parser").get_text(separator=" ", strip=True)

        return RawNewsItem(
            id=hashlib.md5(url.encode()).hexdigest(),
            title=title,
            url=url,
            source_key=source["key"],
            source_name=source["name"],
            source_type=source["source_type"],
            language=source["language"],
            pub_time=pub_time,
            summary=summary[:500],
            content="",
        )

    def _parse_time(self, entry) -> Optional[datetime]:
        for field in ["published_parsed", "updated_parsed", "created_parsed"]:
            if field in entry and entry[field]:
                try:
                    return datetime(*entry[field][:6])
                except Exception:
                    continue
        for field in ["published", "updated", "created"]:
            if field in entry and entry[field]:
                try:
                    from dateutil import parser
                    return parser.parse(entry[field])
                except Exception:
                    continue
        return None
