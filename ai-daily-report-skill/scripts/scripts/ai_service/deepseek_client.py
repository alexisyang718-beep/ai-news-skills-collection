# -*- coding: utf-8 -*-
"""DeepSeek API客户端"""

import logging
import time
from typing import Optional
from openai import OpenAI

from config.settings import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    API_MAX_RETRIES, API_RETRY_DELAY, API_TIMEOUT
)

logger = logging.getLogger(__name__)


class DeepSeekClient:
    """DeepSeek API客户端"""

    def __init__(self):
        self.client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
        self.model = DEEPSEEK_MODEL
        self.total_tokens = 0

    def chat(self, messages: list, temperature: float = 0.3, max_tokens: int = 2000) -> Optional[str]:
        for attempt in range(API_MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=API_TIMEOUT,
                )
                if response.usage:
                    self.total_tokens += response.usage.total_tokens
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"API调用失败 ({attempt+1}/{API_MAX_RETRIES}): {e}")
                if attempt < API_MAX_RETRIES - 1:
                    time.sleep(API_RETRY_DELAY * (attempt + 1))
        return None

    def get_total_tokens(self) -> int:
        return self.total_tokens


_client = None

def get_client() -> DeepSeekClient:
    global _client
    if _client is None:
        _client = DeepSeekClient()
    return _client
