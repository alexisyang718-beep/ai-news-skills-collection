# -*- coding: utf-8 -*-
"""
翻译器
英译中翻译
"""

import logging
from typing import Optional

from ai_service.deepseek_client import get_client

logger = logging.getLogger(__name__)


class Translator:
    """翻译器"""

    def __init__(self):
        self.client = get_client()

    def translate_to_chinese(self, text: str, context: str = "") -> Optional[str]:
        """将英文翻译成中文"""
        if not text or not text.strip():
            return text

        chinese_ratio = sum(1 for c in text if '\u4e00' <= c <= '\u9fff') / len(text)
        if chinese_ratio > 0.5:
            return text

        MAX_TEXT_LENGTH = 800
        if len(text) > MAX_TEXT_LENGTH:
            text = text[:MAX_TEXT_LENGTH] + "..."

        prompt = f"""请将以下英文文本翻译成中文，保持专业术语的准确性：

{text}

要求：
1. 翻译要准确、流畅
2. AI、API等专业缩写可以保留英文
3. 公司名、产品名保留英文或使用约定俗成的中文译名
4. 直接输出翻译结果，不要加任何前缀或说明"""

        messages = [
            {
                "role": "system",
                "content": "你是一位专业的科技新闻翻译，擅长将英文科技新闻翻译成准确流畅的中文。"
            },
            {"role": "user", "content": prompt}
        ]

        response = self.client.chat(messages, temperature=0.2, max_tokens=500)

        if response:
            return response.strip().strip('"\'')

        return None

    def translate_batch_titles(self, titles: list[str]) -> Optional[list[str]]:
        """批量翻译英文标题"""
        if not titles:
            return []

        to_translate = []
        indices = []
        for i, title in enumerate(titles):
            chinese_ratio = sum(1 for c in title if '\u4e00' <= c <= '\u9fff') / len(title) if title else 0
            if chinese_ratio > 0.3:
                to_translate.append("")
                indices.append(i)
            elif title and len(title) > 150:
                to_translate.append(title[:150] + "...")
                indices.append(i)
            elif title:
                to_translate.append(title)
                indices.append(i)
            else:
                to_translate.append("")
                indices.append(i)

        if not any(to_translate):
            return titles.copy()

        MAX_TITLES_PER_BATCH = 5
        results = {}

        for start in range(0, len(to_translate), MAX_TITLES_PER_BATCH):
            batch = to_translate[start:start + MAX_TITLES_PER_BATCH]
            batch_indices = indices[start:start + MAX_TITLES_PER_BATCH]

            news_texts = []
            for i, title in enumerate(batch):
                if not title:
                    continue
                news_texts.append(f"{i+1}. {title}")

            if not news_texts:
                continue

            prompt = f"""请将以下{len(news_texts)}条英文新闻标题翻译成中文：

{chr(10).join(news_texts)}

要求：
1. 每行翻译一行，保持顺序
2. 只输出翻译后的标题，不要序号
3. 每行一个标题"""

            messages = [
                {
                    "role": "system",
                    "content": "你是一位专业的新闻编辑，擅长翻译新闻标题。只输出翻译结果，不要序号，每行一个标题。"
                },
                {"role": "user", "content": prompt}
            ]

            response = self.client.chat(messages, temperature=0.2, max_tokens=400)

            if response:
                translated_lines = [line.strip() for line in response.strip().split('\n') if line.strip()]
                trans_idx = 0
                for i, title in enumerate(batch):
                    if title:
                        if trans_idx < len(translated_lines):
                            results[batch_indices[i]] = translated_lines[trans_idx][:80]
                        else:
                            results[batch_indices[i]] = title[:80]
                        trans_idx += 1

        final_results = []
        for i, title in enumerate(titles):
            if i in results:
                final_results.append(results[i])
            else:
                final_results.append(title)

        return final_results

    def translate_title(self, title: str) -> Optional[str]:
        """翻译单条新闻标题"""
        if not title:
            return title

        if len(title) > 150:
            title = title[:150] + "..."

        chinese_ratio = sum(1 for c in title if '\u4e00' <= c <= '\u9fff') / len(title)
        if chinese_ratio > 0.3:
            return title

        prompt = f"""请将以下英文新闻标题翻译成中文：

{title}

要求：
1. 标题要简洁有力
2. 保持新闻标题的风格
3. 只输出翻译后的标题，不要其他内容"""

        messages = [
            {
                "role": "system",
                "content": "你是一位专业的新闻编辑，擅长翻译新闻标题。"
            },
            {"role": "user", "content": prompt}
        ]

        response = self.client.chat(messages, temperature=0.2, max_tokens=80)

        if response:
            return response.strip().strip('"\'')[:80]

        return title
