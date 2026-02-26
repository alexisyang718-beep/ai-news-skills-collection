"""素材收集器

从热点聚类中提取相关新闻素材，
组装成 AI 写作所需的上下文。
"""
import logging
import re
import requests
from typing import List, Dict, Optional

from topic_selector import TopicCluster, NewsItem

logger = logging.getLogger(__name__)

# 简单的 headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class MaterialCollector:
    """从聚类中收集写作素材"""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    def collect(self, cluster: TopicCluster, max_articles: int = 8) -> str:
        """
        从聚类中收集素材，返回格式化的素材文本。
        优先用标题+摘要，只对 Top 几条尝试提取正文。
        """
        articles = cluster.articles[:max_articles]
        materials = []

        for i, article in enumerate(articles):
            title = article.title_zh or article.title
            source = article.source or article.site_id

            # 对前3条尝试抓取摘要（控制成本和时间）
            excerpt = ""
            if i < 3:
                excerpt = self._fetch_excerpt(article.url)

            entry = f"### 报道 {i+1}（来源: {source}）\n标题: {title}"
            if excerpt:
                entry += f"\n摘要: {excerpt}"
            materials.append(entry)

        header = (
            f"话题: {cluster.representative_title}\n"
            f"报道数量: {cluster.count} 篇，涉及 {cluster.source_count} 个来源\n"
        )
        return header + "\n\n" + "\n\n".join(materials)

    def _fetch_excerpt(self, url: str, max_chars: int = 500) -> str:
        """尝试从 URL 抓取摘要文本"""
        if not url:
            return ""
        try:
            resp = requests.get(url, headers=HEADERS, timeout=self.timeout, allow_redirects=True)
            resp.raise_for_status()
            text = resp.text

            # 尝试提取 meta description
            desc = self._extract_meta_description(text)
            if desc and len(desc) > 30:
                return desc[:max_chars]

            # 尝试提取 og:description
            og_desc = self._extract_og_description(text)
            if og_desc and len(og_desc) > 30:
                return og_desc[:max_chars]

            # 提取正文前 N 字符
            body_text = self._extract_body_text(text)
            if body_text:
                return body_text[:max_chars]

        except Exception as e:
            logger.debug(f"获取摘要失败 {url}: {e}")
        return ""

    @staticmethod
    def _extract_meta_description(html: str) -> str:
        match = re.search(
            r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']',
            html, re.IGNORECASE
        )
        if not match:
            match = re.search(
                r'<meta\s+content=["\']([^"\']+)["\']\s+name=["\']description["\']',
                html, re.IGNORECASE
            )
        return match.group(1).strip() if match else ""

    @staticmethod
    def _extract_og_description(html: str) -> str:
        match = re.search(
            r'<meta\s+property=["\']og:description["\']\s+content=["\']([^"\']+)["\']',
            html, re.IGNORECASE
        )
        if not match:
            match = re.search(
                r'<meta\s+content=["\']([^"\']+)["\']\s+property=["\']og:description["\']',
                html, re.IGNORECASE
            )
        return match.group(1).strip() if match else ""

    @staticmethod
    def _extract_body_text(html: str) -> str:
        """简易正文提取"""
        # 移除 script/style
        text = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # 移除 HTML 标签
        text = re.sub(r'<[^>]+>', ' ', text)
        # 合并空白
        text = re.sub(r'\s+', ' ', text).strip()
        # 取前面有意义的部分
        if len(text) > 100:
            return text[:500]
        return ""
