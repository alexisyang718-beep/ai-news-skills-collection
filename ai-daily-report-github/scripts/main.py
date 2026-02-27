#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI资讯日报自动化系统 - 主程序
协调各模块执行完整工作流

设计要点：
- 优先从 ai-hourly-buzz 的共享数据读取已采集新闻
- 回退到独立 RSS 采集
- 深度处理：关键词筛选 → 去重 → 正文提取 → AI摘要翻译 → 5类分类
- 双输出：HTML存档 + 微信公众号草稿
"""

import logging
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import (
    LOG_LEVEL, LOG_FORMAT, LOG_FILE, LOGS_DIR,
    MAX_NEWS_PER_CATEGORY
)
from crawler.models import RawNewsItem, ScoredNewsItem
from crawler.shared_loader import SharedDataLoader
from crawler.rss_parser import RSSParser
from crawler.web_scraper import WebScraper
from crawler.content_extractor import ContentExtractor
from processor.filter import KeywordFilter
from processor.deduplicator import Deduplicator
from processor.time_handler import TimeHandler
from ai_service.summarizer import Summarizer
from ai_service.translator import Translator
from ai_service.classifier import Classifier
from ai_service.deepseek_client import get_client
from publisher.html_generator import HTMLGenerator
from publisher.markdown_generator import MarkdownGenerator
from publisher.wechat_publisher import WeChatPublisher


def setup_logging():
    """配置日志"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding='utf-8')
    ]

    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
        handlers=handlers
    )

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("feedparser").setLevel(logging.WARNING)


class DailyReportPipeline:
    """日报生成流水线"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 数据采集
        from config.rss_sources import RSS_SOURCES
        from config.settings import REQUEST_HEADERS, REQUEST_TIMEOUT, REQUEST_DELAY
        self.shared_loader = SharedDataLoader()
        self.rss_parser = RSSParser(sources=RSS_SOURCES, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT, delay=REQUEST_DELAY)
        self.web_scraper = WebScraper(sources=RSS_SOURCES, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT, delay=REQUEST_DELAY)
        self.content_extractor = ContentExtractor(headers=REQUEST_HEADERS)

        # 数据处理
        self.keyword_filter = KeywordFilter()
        self.deduplicator = Deduplicator()
        self.time_handler = TimeHandler()

        # AI服务
        self.summarizer = Summarizer()
        self.translator = Translator()
        self.classifier = Classifier()

        # 发布
        self.html_generator = HTMLGenerator()
        self.markdown_generator = MarkdownGenerator()
        self.wechat_publisher = WeChatPublisher()

    def run(self, publish_to_wechat: bool = True) -> bool:
        """执行完整的日报生成流程"""
        start_time = datetime.now()
        self.logger.info("=" * 50)
        self.logger.info("开始生成AI资讯日报")
        self.logger.info("=" * 50)

        try:
            # 1. 采集新闻（优先共享数据）
            self.logger.info("\n📥 步骤1: 采集新闻...")
            raw_news = self._collect_news()
            if not raw_news:
                self.logger.warning("未获取到任何新闻，流程终止")
                return False

            # 2. 时间过滤
            self.logger.info("\n📅 步骤2: 筛选过去24小时新闻...")
            recent_news = self._filter_by_time(raw_news)
            if not recent_news:
                self.logger.warning("未找到过去24小时的新闻，使用所有新闻")
                recent_news = raw_news[:50]

            # 3. 关键词筛选
            self.logger.info("\n🔍 步骤3: 筛选相关新闻...")
            filtered_news = self._filter_news(recent_news)
            if not filtered_news:
                self.logger.warning("筛选后无相关新闻，流程终止")
                return False

            # 4. 去重
            self.logger.info("\n🔄 步骤4: 去重处理...")
            unique_news = self._deduplicate(filtered_news)
            if not unique_news:
                self.logger.warning("去重后无新闻，流程终止")
                return False

            # 4.5 按评分排序，取Top N
            unique_news.sort(key=lambda x: x.relevance_score, reverse=True)
            MAX_TOTAL = 50  # 最多处理50条高质量新闻
            if len(unique_news) > MAX_TOTAL:
                self.logger.info(f"按评分取前 {MAX_TOTAL} 条 (共 {len(unique_news)} 条)")
                unique_news = unique_news[:MAX_TOTAL]

            # 打印Top10标题和评分供调试
            self.logger.info("Top-10 新闻:")
            for i, item in enumerate(unique_news[:10]):
                title = item.raw_item.title[:60]
                self.logger.info(f"  {i+1}. [{item.relevance_score:.1f}分] {title}")

            # 5. 提取正文
            self.logger.info("\n📄 步骤5: 提取新闻正文...")
            self._extract_content(unique_news)

            # 6. AI处理（摘要+翻译）
            self.logger.info("\n🤖 步骤6: AI生成摘要和翻译...")
            processed_news = self._ai_process(unique_news)

            # 7. 分类（五个类别）
            self.logger.info("\n📊 步骤7: 新闻分类...")
            categorized_news = self._classify_news(processed_news)

            # 8. 限制每个类别的数量
            for category in categorized_news:
                categorized_news[category] = categorized_news[category][:MAX_NEWS_PER_CATEGORY]

            total_count = sum(len(items) for items in categorized_news.values())

            # 9. 生成HTML和Markdown
            self.logger.info("\n📝 步骤8: 生成日报...")
            daily_summary = self._generate_daily_summary(categorized_news)
            html_content = self.html_generator.generate(categorized_news, daily_summary)

            token_usage = get_client().get_total_tokens()
            self.markdown_generator.generate(categorized_news, daily_summary, token_usage)

            # 10. 发布到微信
            if publish_to_wechat:
                self.logger.info("\n📤 步骤9: 发布到微信公众号...")
                self._publish_to_wechat(html_content)

            # 统计
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self.logger.info("\n" + "=" * 50)
            self.logger.info("✅ 日报生成完成!")
            from ai_service.classifier import CATEGORY_DEFINITIONS
            for cat_key, cat_items in categorized_news.items():
                cat_name = CATEGORY_DEFINITIONS[cat_key]["name"]
                self.logger.info(f"   - {cat_name}: {len(cat_items)} 条")
            self.logger.info(f"   - 总计: {total_count} 条")
            self.logger.info(f"   - 耗时: {duration:.1f} 秒")
            self.logger.info(f"   - Token消耗: {get_client().get_total_tokens()}")
            self.logger.info("=" * 50)

            return True

        except Exception as e:
            self.logger.error(f"日报生成失败: {e}", exc_info=True)
            return False

    def _collect_news(self) -> List[RawNewsItem]:
        """采集新闻 — 优先从 ai-hourly-buzz 共享数据读取"""
        all_news = []

        # 尝试加载共享数据
        self.logger.info("尝试从 ai-hourly-buzz 共享数据加载...")
        shared_news = self.shared_loader.load()
        if shared_news:
            all_news.extend(shared_news)
            self.logger.info(f"共享数据获取: {len(shared_news)} 条")

        # 如果共享数据不足，独立采集
        if len(all_news) < 10:
            self.logger.info("共享数据不足，启动独立采集...")

            self.logger.info("从RSS源采集...")
            rss_news = self.rss_parser.parse_all()
            all_news.extend(rss_news)
            self.logger.info(f"RSS源获取: {len(rss_news)} 条")

            self.logger.info("从网页采集...")
            web_news = self.web_scraper.scrape_all()
            all_news.extend(web_news)
            self.logger.info(f"网页爬取: {len(web_news)} 条")

        self.logger.info(f"共采集: {len(all_news)} 条新闻")
        return all_news

    def _filter_by_time(self, news_list: List[RawNewsItem]) -> List[RawNewsItem]:
        """按时间筛选（过去24小时）"""
        start, end = self.time_handler.get_24h_range()
        self.logger.info(f"筛选时间范围: {start.strftime('%Y-%m-%d %H:%M')} ~ {end.strftime('%Y-%m-%d %H:%M')}")

        filtered = []
        no_time_count = 0

        for item in news_list:
            if item.pub_time is None:
                filtered.append(item)
                no_time_count += 1
                continue

            beijing_time = self.time_handler.convert_to_beijing(item.pub_time)
            item.pub_time = beijing_time

            if start <= beijing_time <= end:
                filtered.append(item)

        self.logger.info(f"时间过滤: {len(news_list)} -> {len(filtered)} 条 (无时间戳: {no_time_count})")
        return filtered

    def _filter_news(self, news_list: List[RawNewsItem]) -> List[ScoredNewsItem]:
        """关键词筛选"""
        return self.keyword_filter.filter_news(news_list)

    def _deduplicate(self, news_list: List[ScoredNewsItem]) -> List[ScoredNewsItem]:
        return self.deduplicator.deduplicate(news_list)

    def _extract_content(self, news_list: List[ScoredNewsItem]):
        """提取正文"""
        items_to_extract = []
        for item in news_list:
            if not item.raw_item.content or len(item.raw_item.content) < 100:
                items_to_extract.append(item.raw_item)

        if items_to_extract:
            self.logger.info(f"需要提取正文: {len(items_to_extract)} 条")
            self.content_extractor.extract_batch(items_to_extract)

    def _ai_process(self, news_list: List[ScoredNewsItem]) -> List[ScoredNewsItem]:
        """AI处理：生成摘要和翻译标题"""
        from ai_service.summarizer import Summarizer
        news_list = self.summarizer.summarize_batch(news_list)

        # 过滤掉无效摘要的新闻（模型声称"内容为空/缺失"等）
        before_count = len(news_list)
        news_list = [item for item in news_list if not Summarizer.is_invalid_summary(item.summary_cn)]
        filtered = before_count - len(news_list)
        if filtered:
            self.logger.info(f"过滤掉 {filtered} 条无效摘要的新闻，剩余 {len(news_list)} 条")

        # 收集所有需要翻译的英文标题（基于实际内容检测，而非 language 字段）
        en_indices = []
        en_titles = []
        for i, item in enumerate(news_list):
            title = item.raw_item.title
            cn_ratio = sum(1 for c in title if '\u4e00' <= c <= '\u9fff') / max(len(title), 1)
            if cn_ratio < 0.3:  # 中文字符不足30%，视为英文标题需翻译
                en_indices.append(i)
                en_titles.append(title)
            else:
                # 中文标题直接设置
                item.title_cn = title

        if en_titles:
            self.logger.info(f"批量翻译 {len(en_titles)} 个英文标题...")
            cn_titles = self.translator.translate_batch_titles(en_titles)
            if cn_titles and len(cn_titles) == len(en_titles):
                for i, idx in enumerate(en_indices):
                    if cn_titles[i]:
                        news_list[idx].title_cn = cn_titles[i]

        # 兜底：对仍无中文标题的英文新闻逐条翻译
        untranslated = 0
        for item in news_list:
            if not item.title_cn:
                title = item.raw_item.title
                cn_ratio = sum(1 for c in title if '\u4e00' <= c <= '\u9fff') / max(len(title), 1)
                if cn_ratio < 0.3:
                    translated = self.translator.translate_title(title)
                    if translated:
                        item.title_cn = translated
                        untranslated += 1
                    else:
                        item.title_cn = title
                else:
                    item.title_cn = title
        if untranslated:
            self.logger.info(f"逐条翻译兜底: {untranslated} 个标题")

        return news_list

    def _classify_news(self, news_list: List[ScoredNewsItem]) -> dict:
        return self.classifier.classify_batch(news_list, use_ai=False)

    def _generate_daily_summary(self, categorized_news: dict) -> str:
        """使用AI生成每日导语"""
        titles = []
        for category, items in categorized_news.items():
            for item in items[:2]:
                title = item.title_cn or item.raw_item.title
                titles.append(title[:50])

        if not titles:
            return "今日AI行业暂无重大动态更新。"

        titles = titles[:8]

        prompt = f"""请根据以下今日AI资讯标题，生成一段50-80字的每日导语摘要，概括今日AI领域的主要动态：

{chr(10).join(['- ' + t for t in titles])}

要求：
1. 简洁概括今日主要动态
2. 突出重点公司和技术
3. 语言流畅，适合作为日报开头
4. 直接输出导语内容，不要加任何前缀"""

        try:
            client = get_client()
            response = client.chat([
                {"role": "system", "content": "你是一位专业的科技新闻编辑。"},
                {"role": "user", "content": prompt}
            ], temperature=0.5, max_tokens=200)

            if response:
                return response.strip().strip('"\'')
        except Exception as e:
            self.logger.warning(f"生成导语失败: {e}")

        total_count = sum(len(items) for items in categorized_news.values())
        return f"今日AI领域共有{total_count}条动态值得关注。"

    def _publish_to_wechat(self, html_content: str) -> bool:
        return self.wechat_publisher.publish_daily_report(html_content)


def main():
    """主函数"""
    setup_logging()

    publish_to_wechat = True
    if "--no-publish" in sys.argv or "--local-only" in sys.argv:
        publish_to_wechat = False
        logging.info("仅生成本地文件，不发布到微信")

    pipeline = DailyReportPipeline()
    success = pipeline.run(publish_to_wechat=publish_to_wechat)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
