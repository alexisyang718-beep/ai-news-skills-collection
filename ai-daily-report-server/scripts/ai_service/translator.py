# -*- coding: utf-8 -*-
"""
翻译器
英译中翻译
"""

import logging
from typing import Optional
import requests

from ai_service.deepseek_client import get_client

logger = logging.getLogger(__name__)


def _translate_free(text: str) -> Optional[str]:
    """Google Translate 免费接口，失败返回 None"""
    try:
        r = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client": "gtx", "sl": "auto", "tl": "zh-CN", "dt": "t", "q": text},
            timeout=8,
        )
        r.raise_for_status()
        payload = r.json()
        if not isinstance(payload, list) or not payload:
            return None
        segs = payload[0]
        if not isinstance(segs, list):
            return None
        result = "".join(str(s[0]) for s in segs if isinstance(s, list) and s and s[0]).strip()
        return result if result and result != text else None
    except Exception:
        return None


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

        prompt = f"将以下英文翻译成中文，AI/API等缩写和公司名保留英文，直接输出译文：\n\n{text}"

        messages = [
            {
                "role": "system",
                "content": "你是科技新闻翻译，英译中，准确流畅。"
            },
            {"role": "user", "content": prompt}
        ]

        response = self.client.chat(messages, temperature=0.2, max_tokens=500)

        if response:
            return response.strip().strip('"\'')

        return None

    def translate_batch_titles(self, titles: list[str]) -> Optional[list[str]]:
        """批量翻译英文标题，优先用免费接口，失败时降级到 DeepSeek"""
        if not titles:
            return []

        results = {}
        need_ai = []  # (original_index, title) 免费接口失败的条目

        for i, title in enumerate(titles):
            if not title:
                continue
            t = title[:150] if len(title) > 150 else title
            chinese_ratio = sum(1 for c in t if '\u4e00' <= c <= '\u9fff') / len(t)
            if chinese_ratio > 0.3:
                continue  # 已是中文，不需翻译

            zh = _translate_free(t)
            if zh:
                results[i] = zh[:80]
            else:
                need_ai.append((i, t))

        # 免费接口失败的批量交给 DeepSeek
        if need_ai:
            MAX_PER_BATCH = 5
            for start in range(0, len(need_ai), MAX_PER_BATCH):
                batch = need_ai[start:start + MAX_PER_BATCH]
                news_texts = [f"{j+1}. {t}" for j, (_, t) in enumerate(batch)]
                prompt = f"将以下{len(batch)}条英文新闻标题译成中文，每行一条，只输出译文：\n\n" + "\n".join(news_texts)
                messages = [{"role": "user", "content": prompt}]
                response = self.client.chat(messages, temperature=0.2, max_tokens=400)
                if response:
                    lines = [l.strip() for l in response.strip().split('\n') if l.strip()]
                    for j, (orig_idx, orig_title) in enumerate(batch):
                        if j < len(lines):
                            results[orig_idx] = lines[j][:80]

        return [results.get(i, title) for i, title in enumerate(titles)]

    def translate_title(self, title: str) -> Optional[str]:
        """翻译单条新闻标题，优先用免费接口，失败时降级到 DeepSeek"""
        if not title:
            return title
        t = title[:150] if len(title) > 150 else title
        chinese_ratio = sum(1 for c in t if '\u4e00' <= c <= '\u9fff') / len(t)
        if chinese_ratio > 0.3:
            return title

        zh = _translate_free(t)
        if zh:
            return zh[:80]

        # 降级到 DeepSeek
        prompt = f"将以下英文新闻标题译成中文，只输出译文：\n\n{t}"
        messages = [{"role": "user", "content": prompt}]
        response = self.client.chat(messages, temperature=0.2, max_tokens=80)
        if response:
            return response.strip().strip('"\'')[:80]
        return title
