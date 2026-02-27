# -*- coding: utf-8 -*-
"""
关键词筛选器 + 多维评分
评分维度：
  1. 高权重关键词命中（产品发布/重大事件）   +3.0/个
  2. 核心AI关键词命中数量                     +1.0/个
  3. 辅助关键词（大厂名/资本动态）            +0.5/个
  4. 来源优先级（官方源>英文媒体>中文媒体）   +0~2.0
  5. 低价值信号词扣分                          -1.5/个
"""

import logging
from typing import List

from crawler.models import RawNewsItem, ScoredNewsItem
from config.keywords import check_keywords
from config.settings import SOURCE_PRIORITY

logger = logging.getLogger(__name__)


class KeywordFilter:
    """关键词筛选器 + 评分"""

    def __init__(self):
        self.stats = {"total": 0, "passed": 0, "excluded": 0, "no_keywords": 0}

    def filter_news(self, news_list: List[RawNewsItem]) -> List[ScoredNewsItem]:
        self.stats["total"] = len(news_list)
        results = []

        for item in news_list:
            language = item.language or "en"
            text = f"{item.title} {item.summary} {item.content}"
            result = check_keywords(text, language)

            if result["has_exclude"]:
                self.stats["excluded"] += 1
                continue

            if not result["pass"]:
                self.stats["no_keywords"] += 1
                continue

            self.stats["passed"] += 1

            # === 多维评分 ===
            score = 0.0

            # 1) 高权重关键词 — 每命中一个 +3.0
            score += len(result["high_matched"]) * 3.0

            # 2) 核心关键词 — 每命中一个 +1.0（上限5分）
            score += min(len(result["core_matched"]) * 1.0, 5.0)

            # 3) 辅助关键词 — 每命中一个 +0.5（上限2分）
            score += min(len(result["aux_matched"]) * 0.5, 2.0)

            # 4) 来源优先级加分
            source_key = item.source_key or ""
            # 从 site_id 中提取来源名（shared_xxx → xxx）
            clean_key = source_key.replace("shared_", "").lower()
            priority = SOURCE_PRIORITY.get(clean_key, 4)
            # 优先级 1→+2.0, 2→+1.5, 3→+1.0, 4→+0
            source_bonus = max(0, (4 - priority) * 0.5 + 0.5) if priority <= 3 else 0
            score += source_bonus

            # 5) 低价值信号扣分 — 每个 -1.5
            score -= result["low_signal_count"] * 1.5

            # 保底 0.1（通过关键词筛选的至少有个底分）
            score = max(score, 0.1)

            # 游戏相关检测
            gaming_kw = ["游戏", "game", "gaming", "npc", "手游", "电竞"]
            is_gaming = any(kw in text.lower() for kw in gaming_kw)

            results.append(ScoredNewsItem(
                raw_item=item,
                relevance_score=round(score, 2),
                keywords_matched=result["high_matched"] + result["core_matched"] + result["aux_matched"],
                is_gaming_related=is_gaming,
            ))

        # 按评分降序排列
        results.sort(key=lambda x: x.relevance_score, reverse=True)

        logger.info(f"筛选: {self.stats['total']} -> {self.stats['passed']} 条")
        logger.info(f"  排除词过滤: {self.stats['excluded']}, 关键词不匹配: {self.stats['no_keywords']}")
        if results:
            logger.info(f"  评分范围: {results[-1].relevance_score} ~ {results[0].relevance_score}")
        return results
