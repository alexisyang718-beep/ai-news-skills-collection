# -*- coding: utf-8 -*-
"""
摘要生成器
使用DeepSeek API生成新闻摘要
"""

import logging
from typing import List, Optional
import json
import re

from ai_service.deepseek_client import get_client
from crawler.models import ScoredNewsItem

logger = logging.getLogger(__name__)


class Summarizer:
    """摘要生成器"""

    def __init__(self):
        self.client = get_client()

    def summarize_single(self, title: str, content: str, language: str = "en") -> Optional[str]:
        """为单条新闻生成中文摘要"""
        if len(content) > 1200:
            content = content[:1200] + "..."

        prompt = self._build_summary_prompt(title, content, language)

        messages = [
            {
                "role": "system",
                "content": "你是科技新闻编辑，生成简洁中文摘要。"
            },
            {"role": "user", "content": prompt}
        ]

        response = self.client.chat(messages, temperature=0.3, max_tokens=500)

        if response:
            summary = response.strip().strip('"\'')
            return summary

        return None

    # 无效摘要的关键词列表
    INVALID_SUMMARY_KEYWORDS = [
        "正文内容为空", "正文内容缺失", "正文缺失", "内容为空", "内容缺失",
        "无法生成有效摘要", "无法生成摘要", "未能获取", "无法获取",
        "没有提供正文", "缺少正文", "正文为空", "无正文", "无法提取",
        "content is empty", "no content", "content missing",
    ]

    @classmethod
    def is_invalid_summary(cls, summary: str) -> bool:
        """检测摘要是否为无效内容（模型声称内容为空等）"""
        if not summary:
            return True
        summary_lower = summary.lower()
        return any(kw in summary_lower for kw in cls.INVALID_SUMMARY_KEYWORDS)

    def _build_summary_prompt(self, title: str, content: str, language: str) -> str:
        if language == "zh":
            return f"""为以下新闻生成100-150字中文摘要，提取核心事件，保持客观，保留公司名原名，正文不足时根据标题推断，直接输出摘要：

标题：{title}
正文：{content}"""
        else:
            return f"""将以下英文新闻翻译并总结成100-150字中文摘要，提取核心事件，保持客观，保留公司名原名，正文不足时根据标题推断，直接输出摘要：

Title: {title}
Content: {content}"""

    def summarize_batch(
        self,
        news_list: List[ScoredNewsItem],
        batch_size: int = 2
    ) -> List[ScoredNewsItem]:
        """批量生成摘要"""
        logger.info(f"开始批量生成摘要: {len(news_list)} 条新闻")

        for i in range(0, len(news_list), batch_size):
            batch = news_list[i:i + batch_size]

            if len(batch) > 1:
                summaries = self._batch_summarize(batch)
                if summaries:
                    for j, item in enumerate(batch):
                        if j < len(summaries):
                            s = summaries[j]
                            # 容错：模型可能返回 dict 而非 str
                            if isinstance(s, dict):
                                s = s.get("content", s.get("summary", str(s)))
                            item.summary_cn = str(s).strip() if s else ""
                            logger.debug(f"批量摘要完成: {item.raw_item.title[:30]}...")
                    continue

            # 批量失败或单条 → 逐条处理
            for item in batch:
                if item.summary_cn:
                    continue
                content = item.raw_item.content or item.raw_item.summary or ""
                # 即使正文为空，也用标题生成摘要
                if not content:
                    content = item.raw_item.title
                summary = self.summarize_single(
                    item.raw_item.title,
                    content,
                    item.raw_item.language
                )
                if summary:
                    item.summary_cn = summary
                    logger.debug(f"单条摘要完成: {item.raw_item.title[:30]}...")

        # 最后兜底：仍无摘要的用 raw_item.summary 填充
        no_summary_count = 0
        for item in news_list:
            if not item.summary_cn:
                item.summary_cn = item.raw_item.summary or ""
                no_summary_count += 1
        if no_summary_count:
            logger.warning(f"仍有 {no_summary_count} 条新闻无摘要")

        logger.info(f"摘要生成完成，消耗tokens: {self.client.get_total_tokens()}")
        return news_list

    def _batch_summarize(self, batch: List[ScoredNewsItem]) -> Optional[List[str]]:
        """批量处理多条新闻（单次API调用）"""
        MAX_CONTENT_PER_ITEM = 600
        MAX_TOTAL_CHARS = 2500

        news_texts = []
        total_chars = 0
        for i, item in enumerate(batch):
            content = item.raw_item.content or item.raw_item.summary
            if len(content) > MAX_CONTENT_PER_ITEM:
                content = content[:MAX_CONTENT_PER_ITEM] + "..."

            entry = f"【新闻{i + 1}】({item.raw_item.language == 'en' and '英文' or '中文'})\n标题: {item.raw_item.title}\n正文: {content}"
            news_texts.append(entry)

            total_chars += len(entry)
            if total_chars > MAX_TOTAL_CHARS:
                logger.warning(f"批量输入过长 ({total_chars} chars)，改为逐条处理")
                return None

        prompt = f"""为以下{len(batch)}条新闻各生成50-80字中文摘要，英文新闻先翻译再总结，正文不足时根据标题推断，按JSON数组输出["摘要1","摘要2"]，只输出数组：

{chr(10).join(news_texts)}"""

        messages = [
            {
                "role": "system",
                "content": "你是科技新闻编辑，按JSON数组格式输出摘要。"
            },
            {"role": "user", "content": prompt}
        ]

        response = self.client.chat(messages, temperature=0.3, max_tokens=1500)

        if response:
            try:
                cleaned = response.strip()
                if cleaned.startswith("```"):
                    cleaned = re.sub(r'^```\w*\n?', '', cleaned)
                    cleaned = re.sub(r'\n?```$', '', cleaned)

                # 尝试提取 JSON 数组（容错：模型可能输出额外文本）
                json_match = re.search(r'\[[\s\S]*\]', cleaned)
                if json_match:
                    cleaned = json_match.group(0)

                summaries = json.loads(cleaned)
                if isinstance(summaries, list) and len(summaries) == len(batch):
                    return summaries
                elif isinstance(summaries, list) and len(summaries) > 0:
                    logger.warning(f"批量摘要数量不匹配: 期望{len(batch)}，得到{len(summaries)}")
            except Exception as e:
                logger.warning(f"批量摘要解析失败: {e}")

        return None
