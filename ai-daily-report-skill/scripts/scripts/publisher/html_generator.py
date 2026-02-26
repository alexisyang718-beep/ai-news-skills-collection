# -*- coding: utf-8 -*-
"""
HTML生成器
根据分类结果生成日报HTML（适配微信公众号样式）
"""

import logging
from typing import List
from pathlib import Path
from datetime import datetime

from config.settings import OUTPUT_DIR
from crawler.models import ScoredNewsItem
from processor.time_handler import TimeHandler

logger = logging.getLogger(__name__)


class HTMLGenerator:
    """HTML生成器"""

    def __init__(self):
        self.time_handler = TimeHandler()
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.last_generated_file = None

    def generate(
        self,
        categorized_news: dict,
        daily_summary: str = ""
    ) -> str:
        """
        生成日报HTML

        Args:
            categorized_news: 分类后的新闻字典
            daily_summary: 每日导语

        Returns:
            生成的HTML内容
        """
        from ai_service.classifier import CATEGORY_DEFINITIONS

        date_str = self.time_handler.get_report_date()

        if not daily_summary:
            daily_summary = self._generate_daily_summary(categorized_news)

        html_parts = []
        html_parts.append(self._get_html_header())
        html_parts.append(self._render_summary(daily_summary))

        category_order = ["big_tech", "ai_products", "ai_tech", "ai_gaming", "industry_news"]
        category_titles = {
            "big_tech": "01 大厂动态",
            "ai_products": "02 应用与产品",
            "ai_tech": "03 模型与技术",
            "ai_gaming": "04 AI与游戏",
            "industry_news": "05 行业新闻"
        }

        for cat_key in category_order:
            if cat_key in categorized_news and categorized_news[cat_key]:
                cat_name = category_titles[cat_key]
                html_parts.append(self._render_section(
                    cat_name,
                    categorized_news[cat_key]
                ))

        html_parts.append(self._get_html_footer())

        html_content = "\n".join(html_parts)
        self.last_generated_file = self._save_to_file(html_content, date_str)

        return html_content

    def _get_html_header(self) -> str:
        return '<div style="max-width:100%;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,\'Helvetica Neue\',Arial,sans-serif;">'

    def _get_html_footer(self) -> str:
        return '</div>'

    def _render_summary(self, summary: str) -> str:
        return f'''
<div style="padding:12px 0;margin:16px 0;color:#7a4fd6;font-size:16px;font-weight:bold;line-height:1.6;">
{summary}
</div>
'''

    def _render_section(self, title: str, news_list: List[ScoredNewsItem]) -> str:
        parts = []
        parts.append('<p style="margin:0;">&nbsp;</p>')
        parts.append(f'''
<p style="color:#000000;font-weight:bold;font-size:24px;font-style:italic;margin:0 0 16px 0;">{title}</p>
''')

        for i, item in enumerate(news_list, 1):
            news_title = item.title_cn or item.raw_item.title
            news_summary = item.summary_cn or item.raw_item.summary
            news_url = item.raw_item.url
            source_name = item.raw_item.source_name

            parts.append(f'''
<div style="margin-bottom:20px;">
<p style="color:#7a4fd6;font-weight:bold;font-size:18px;margin:0 0 12px 0;line-height:1.5;">{i}. {news_title}</p>
<p style="color:#000000;font-size:16px;line-height:1.7;margin:0 0 10px 0;text-align:justify;">{news_summary}</p>
<p style="color:#d6d6d6;font-size:14px;font-weight:bold;margin:0 0 6px 0;">来源: {source_name}</p>
<p style="font-size:14px;font-weight:bold;margin:0;word-break:break-all;"><a href="{news_url}" style="color:#d6d6d6;text-decoration:none;">{news_url}</a></p>
</div>''')

            if i < len(news_list):
                parts.append('<p style="margin:0;">&nbsp;</p>')

        return "\n".join(parts)

    def _generate_daily_summary(self, categorized_news: dict) -> str:
        total_count = sum(len(items) for items in categorized_news.values())
        if total_count == 0:
            return "今日AI行业暂无重大动态更新。"

        from ai_service.classifier import CATEGORY_DEFINITIONS
        summary_parts = []
        for cat_key, cat_items in categorized_news.items():
            if cat_items:
                cat_name = CATEGORY_DEFINITIONS[cat_key]["name"]
                summary_parts.append(f"{cat_name}{len(cat_items)}条")

        if summary_parts:
            return f"今日AI领域共有{total_count}条动态：" + "、".join(summary_parts) + "。"

        return "今日AI行业暂无重大动态更新。"

    def _save_to_file(self, html_content: str, date_str: str) -> Path:
        filename = f"AI资讯日报_{date_str}.html"
        filepath = self.output_dir / filename

        full_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI资讯日报_{date_str}</title>
</head>
<body>
{html_content}
</body>
</html>'''

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(full_html)

        logger.info(f"日报已保存: {filepath}")
        return filepath

    def get_last_generated_file(self) -> Path:
        return self.last_generated_file

    def get_wechat_content(self, html_content: str) -> str:
        return html_content
