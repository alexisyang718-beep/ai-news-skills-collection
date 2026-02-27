"""AI 深度专栏文章撰写

使用 DeepSeek 基于素材生成结构化长文。
"""
import logging
import time
from typing import Optional, Tuple
from openai import OpenAI

from config.settings import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    API_MAX_RETRIES, API_RETRY_DELAY, API_TIMEOUT,
    ARTICLE_WORD_COUNT,
)
from config.prompts import ARTICLE_SYSTEM, ARTICLE_USER

logger = logging.getLogger(__name__)

# 模块级单例
_client: Optional["ArticleWriter"] = None


def get_writer() -> "ArticleWriter":
    global _client
    if _client is None:
        _client = ArticleWriter()
    return _client


class ArticleWriter:
    """AI 文章撰写器"""

    def __init__(self):
        self.client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
            timeout=API_TIMEOUT,
        )
        self.total_tokens = 0

    def write_article(self, topic_title: str, materials: str) -> Tuple[Optional[str], Optional[str]]:
        """
        生成专栏文章。
        返回 (title, body_markdown) 或 (None, None)。
        """
        user_prompt = ARTICLE_USER.format(
            topic_title=topic_title,
            materials=materials,
            word_count=ARTICLE_WORD_COUNT,
        )

        response = self._chat(
            system=ARTICLE_SYSTEM,
            user=user_prompt,
            temperature=0.6,
            max_tokens=4000,
        )

        if not response:
            return None, None

        return self._parse_article(response)

    def _chat(self, system: str, user: str,
              temperature: float = 0.3, max_tokens: int = 2000) -> Optional[str]:
        """调用 DeepSeek API，带重试"""
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

        for attempt in range(API_MAX_RETRIES):
            try:
                resp = self.client.chat.completions.create(
                    model=DEEPSEEK_MODEL,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                if resp.usage:
                    self.total_tokens += resp.usage.total_tokens
                    logger.info(f"Token 消耗: +{resp.usage.total_tokens} (累计 {self.total_tokens})")

                content = resp.choices[0].message.content
                return content.strip() if content else None

            except Exception as e:
                delay = API_RETRY_DELAY * (attempt + 1)
                logger.warning(f"API 调用失败 (尝试 {attempt+1}/{API_MAX_RETRIES}): {e}")
                if attempt < API_MAX_RETRIES - 1:
                    time.sleep(delay)

        logger.error("API 调用全部失败")
        return None

    @staticmethod
    def _parse_article(raw: str) -> Tuple[Optional[str], Optional[str]]:
        """从 AI 输出中解析标题和正文"""
        lines = raw.strip().split("\n")

        title = None
        body_start = 0

        for i, line in enumerate(lines):
            stripped = line.strip()
            # 匹配 TITLE: xxx 格式
            if stripped.upper().startswith("TITLE:"):
                title = stripped[6:].strip().strip("《》「」【】")
                continue
            # 跳过分隔线
            if stripped == "---" or stripped == "":
                continue
            # 找到正文起始
            body_start = i
            break

        body = "\n".join(lines[body_start:]).strip()

        if not title:
            # 尝试从正文第一个 # 标题提取
            for line in lines:
                if line.strip().startswith("# "):
                    title = line.strip().lstrip("# ").strip()
                    body = body.replace(line, "", 1).strip()
                    break

        if not title:
            title = "AI深度专栏"

        return title, body
