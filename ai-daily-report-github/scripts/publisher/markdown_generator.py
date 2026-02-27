# -*- coding: utf-8 -*-
"""
Markdown生成器
生成格式完整的Markdown日报
"""

import logging
from typing import List
from pathlib import Path
from datetime import datetime

from config.settings import OUTPUT_DIR
from crawler.models import ScoredNewsItem
from processor.time_handler import TimeHandler

logger = logging.getLogger(__name__)


class MarkdownGenerator:
    """Markdown生成器"""

    def __init__(self):
        self.time_handler = TimeHandler()
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.last_generated_file = None

    def generate(
        self,
        categorized_news: dict,
        daily_summary: str = "",
        token_usage: int = 0
    ) -> Path:
        """生成日报Markdown"""
        from ai_service.classifier import CATEGORY_DEFINITIONS

        today = datetime.now()
        date_str = today.strftime('%Y-%m-%d')

        lines = []
        lines.append(f"# AI资讯日报-{date_str}")
        lines.append("")

        lines.append("## AI导语")
        lines.append("")
        if daily_summary:
            lines.append(daily_summary)
        else:
            total_count = sum(len(items) for items in categorized_news.values())
            lines.append(f"今日AI领域共有{total_count}条动态值得关注。")
        lines.append("")
        lines.append("---")
        lines.append("")

        category_config = [
            ("big_tech", "01 大厂动态"),
            ("ai_products", "02 应用与产品"),
            ("ai_tech", "03 模型与技术"),
            ("ai_gaming", "04 AI与游戏"),
            ("industry_news", "05 行业新闻")
        ]

        for cat_key, cat_display_name in category_config:
            lines.append("")
            lines.append(f"## {cat_display_name}")
            lines.append("")

            if cat_key in categorized_news and categorized_news[cat_key]:
                for i, item in enumerate(categorized_news[cat_key], 1):
                    lines.append(self._render_news_item(item, i))
                    lines.append("")
            else:
                lines.append("暂无新闻")
                lines.append("")

        lines.append("*本日报由AI自动生成*")

        md_content = "\n".join(lines)
        self.last_generated_file = self._save_to_file(md_content, date_str)

        return self.last_generated_file

    def _render_news_item(self, item: ScoredNewsItem, index: int) -> str:
        lines = []

        title_cn = item.title_cn or item.raw_item.title
        lines.append(f"### {index}. {title_cn}")
        lines.append("")

        summary = item.summary_cn or item.raw_item.summary
        if summary:
            lines.append(f"{summary}")
            lines.append("")

        source_name = item.raw_item.source_name
        lines.append(f"来源: {source_name}")
        lines.append("")
        lines.append(f"{item.raw_item.url}")

        return "\n".join(lines)

    def _save_to_file(self, md_content: str, date_str: str) -> Path:
        timestamp = datetime.now().strftime('%H%M%S')
        filename = f"report_{date_str}_{timestamp}.md"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)

        logger.info(f"Markdown日报已保存: {filepath}")
        return filepath

    def get_last_generated_file(self) -> Path:
        return self.last_generated_file
