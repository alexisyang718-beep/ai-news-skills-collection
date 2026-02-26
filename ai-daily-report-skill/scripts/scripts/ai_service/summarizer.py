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
                "content": "你是一位专业的科技新闻编辑，擅长提取新闻核心要点并生成简洁的中文摘要。"
            },
            {"role": "user", "content": prompt}
        ]

        response = self.client.chat(messages, temperature=0.3, max_tokens=500)

        if response:
            summary = response.strip().strip('"\'')
            return summary

        return None

    def _build_summary_prompt(self, title: str, content: str, language: str) -> str:
        if language == "zh":
            return f"""请为以下中文新闻生成一段简洁的摘要（100-150字）：

标题：{title}

正文：
{content}

要求：
1. 提取核心事件和关键信息
2. 保持客观中立
3. 必须保持标题中出现的公司/机构名称正确，不要改写（如OpenAI、Google、微软、腾讯等）
4. 输出纯文本，不需要任何格式标记
5. 直接输出摘要内容，不要加任何前缀或"摘要："等字样"""
        else:
            return f"""请将以下英文新闻翻译并总结成一段中文摘要（100-150字）：

Title: {title}

Content:
{content}

要求：
1. 翻译并提取核心事件和关键信息
2. 输出为流畅的中文
3. 保持客观中立
4. 必须保持标题中出现的公司名称准确翻译（如Google保持Google或谷歌，OpenAI保持OpenAI），不要随意改成其他公司
5. 输出纯文本，不需要任何格式标记
6. 直接输出摘要内容，不要加任何前缀或【新闻X】等标记"""

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
                            item.summary_cn = summaries[j]
                            logger.debug(f"批量摘要完成: {item.raw_item.title[:30]}...")
                    continue

            for item in batch:
                content = item.raw_item.content or item.raw_item.summary
                if content:
                    summary = self.summarize_single(
                        item.raw_item.title,
                        content,
                        item.raw_item.language
                    )
                    if summary:
                        item.summary_cn = summary
                        logger.debug(f"单条摘要完成: {item.raw_item.title[:30]}...")

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

        prompt = f"""请为以下{len(batch)}条新闻分别生成中文摘要，每条50-80字。

{chr(10).join(news_texts)}

要求：
1. 如果原文是英文，先翻译再总结
2. 提取核心事件和关键信息
3. 按照JSON数组格式输出，如: ["摘要1", "摘要2"]
4. 只输出JSON数组，不要其他内容"""

        messages = [
            {
                "role": "system",
                "content": "你是一位专业的科技新闻编辑。请严格按照JSON数组格式输出摘要。"
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

                summaries = json.loads(cleaned)
                if isinstance(summaries, list) and len(summaries) == len(batch):
                    return summaries
            except Exception as e:
                logger.warning(f"批量摘要解析失败: {e}")

        return None
