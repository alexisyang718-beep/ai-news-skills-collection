# -*- coding: utf-8 -*-
"""
网页爬虫
爬取36氪AI频道和Techmeme
"""

import requests
from bs4 import BeautifulSoup
import logging
import hashlib
import time
import re
from typing import List, Dict

from crawler.models import RawNewsItem

logger = logging.getLogger(__name__)


class WebScraper:
    """网页爬虫"""

    def __init__(self, sources: list, headers: dict, timeout: int = 30, delay: float = 1):
        self.sources = [s for s in sources if s.get("extraction_method") == "web_scrape"]
        self.headers = headers
        self.timeout = timeout
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(headers)

    def scrape_all(self) -> List[RawNewsItem]:
        all_news = []
        for source in self.sources:
            try:
                logger.info(f"爬取网页: {source['name']}")
                news = self._scrape(source)
                all_news.extend(news)
                logger.info(f"  -> {len(news)} 条")
                time.sleep(self.delay)
            except Exception as e:
                logger.error(f"爬取 {source['name']} 失败: {e}")
        return all_news

    def _scrape(self, source: Dict) -> List[RawNewsItem]:
        try:
            resp = self.session.get(source["url"], timeout=self.timeout)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            soup = BeautifulSoup(resp.text, "lxml")

            if source["key"] == "36kr_ai":
                return self._parse_36kr(soup, source)
            elif source["key"] == "techmeme":
                return self._parse_techmeme(soup, source)
            return []
        except Exception as e:
            logger.error(f"爬取 {source['name']}: {e}")
            return []

    def _parse_36kr(self, soup: BeautifulSoup, source: Dict) -> List[RawNewsItem]:
        results = []
        articles = soup.select("div.article-item") or soup.select(".kr-flow-article-item") or soup.select("article")
        for article in articles[:20]:
            try:
                title_elem = (
                    article.select_one("a.article-item-title") or
                    article.select_one("h2 a") or
                    article.select_one("a[href*='/p/']")
                )
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)
                url = title_elem.get("href", "")
                if not url.startswith("http"):
                    url = "https://36kr.com" + url

                summary_elem = article.select_one(".article-item-description") or article.select_one("p")
                summary = summary_elem.get_text(strip=True) if summary_elem else ""

                results.append(RawNewsItem(
                    id=hashlib.md5(url.encode()).hexdigest(),
                    title=title, url=url,
                    source_key=source["key"], source_name=source["name"],
                    source_type=source["source_type"], language=source["language"],
                    pub_time=None, summary=summary[:500], content="",
                ))
            except Exception:
                continue
        return results

    def _parse_techmeme(self, soup: BeautifulSoup, source: Dict) -> List[RawNewsItem]:
        results = []
        items = soup.select(".clus .ii") or soup.select("div.ii")
        for item in items[:30]:
            try:
                link = item.select_one("a.ourh") or item.select_one("a")
                if not link:
                    continue
                title = link.get_text(strip=True)
                url = link.get("href", "")
                if not url.startswith("http"):
                    url = "https://techmeme.com/" + url

                src_elem = item.select_one(".cite2") or item.select_one("cite")
                src_name = src_elem.get_text(strip=True) if src_elem else "Techmeme"

                results.append(RawNewsItem(
                    id=hashlib.md5(url.encode()).hexdigest(),
                    title=title, url=url,
                    source_key=source["key"], source_name=src_name,
                    source_type=source["source_type"], language=source["language"],
                    pub_time=None, summary="", content="",
                ))
            except Exception:
                continue
        return results
