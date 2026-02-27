# -*- coding: utf-8 -*-
"""
正文提取器
三级提取：readability → 自定义选择器 → 通用提取
"""

import requests
from bs4 import BeautifulSoup
import logging
import re
import time
from typing import Optional, Tuple, List
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from crawler.models import RawNewsItem

logger = logging.getLogger(__name__)


class ContentExtractor:
    """正文提取器"""

    def __init__(self, headers: dict, timeout: int = 30, max_length: int = 3000):
        self.session = requests.Session()
        self.session.headers.update(headers)
        self.session.verify = False
        self.timeout = timeout
        self.max_length = max_length

    def extract_batch(self, items: List[RawNewsItem], delay: float = 1):
        """批量提取正文"""
        for item in items:
            if item.content and len(item.content) >= 100:
                continue
            content, pub_time = self.extract(item.url, item.source_key)
            item.content = content
            if not item.pub_time and pub_time:
                try:
                    from dateutil import parser
                    item.pub_time = parser.parse(pub_time)
                except Exception:
                    pass
            logger.debug(f"提取: {item.title[:30]}... ({len(content)} 字符)")
            time.sleep(delay)

    def extract(self, url: str, source_key: str = "") -> Tuple[str, Optional[str]]:
        try:
            resp = self.session.get(url, timeout=self.timeout, verify=False)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            html = resp.text

            content, pub_time = self._try_readability(html)
            if not content or len(content) < 100:
                content, pub_time = self._try_custom(html, url)
            if not content or len(content) < 100:
                content, pub_time = self._try_generic(html)

            if content and len(content) > self.max_length:
                content = content[:self.max_length] + "..."

            return content or "", pub_time
        except Exception as e:
            logger.debug(f"提取失败 {url}: {e}")
            return "", None

    def _try_readability(self, html: str) -> Tuple[str, Optional[str]]:
        try:
            from readability import Document
            doc = Document(html)
            content_html = doc.summary()
            soup = BeautifulSoup(content_html, "lxml")
            content = soup.get_text(separator="\n", strip=True)
            pub_time = self._extract_time(html)
            return content, pub_time
        except Exception:
            return "", None

    def _try_custom(self, html: str, url: str) -> Tuple[str, Optional[str]]:
        soup = BeautifulSoup(html, "lxml")
        content_elem = None
        if "techcrunch.com" in url:
            content_elem = soup.select_one(".article-content") or soup.select_one(".entry-content")
        elif "theverge.com" in url:
            content_elem = soup.select_one(".duet--article--article-body-component") or soup.select_one("article")
        elif "36kr.com" in url:
            content_elem = soup.select_one(".article-content") or soup.select_one(".common-width")
        else:
            content_elem = soup.select_one("article") or soup.select_one(".article-content") or soup.select_one("main")

        if content_elem:
            return content_elem.get_text(separator="\n", strip=True), self._extract_time(html)
        return "", None

    def _try_generic(self, html: str) -> Tuple[str, Optional[str]]:
        soup = BeautifulSoup(html, "lxml")
        for tag in soup.select("script, style, nav, header, footer, aside"):
            tag.decompose()
        for sel in ["article", "main", ".content", "#content"]:
            elem = soup.select_one(sel)
            if elem:
                text = elem.get_text(separator="\n", strip=True)
                if len(text) > 200:
                    return text, self._extract_time(str(soup))
        return "", None

    def _extract_time(self, html: str) -> Optional[str]:
        soup = BeautifulSoup(html, "lxml")
        time_elem = soup.select_one("time")
        if time_elem:
            return time_elem.get("datetime") or time_elem.get_text(strip=True)
        meta = soup.select_one('meta[property="article:published_time"]')
        if meta:
            return meta.get("content")
        match = re.search(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', html)
        return match.group() if match else None
