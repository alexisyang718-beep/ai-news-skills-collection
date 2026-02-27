# -*- coding: utf-8 -*-
"""
分类器
将新闻分为五个类别：
1. 大厂动态：外部公司（OpenAI、Google、Meta、Microsoft等）重大动作
2. AI应用与产品：AI工具、平台、商业化产品发布
3. AI模型与技术：模型、算法、技术进展、基础能力提升
4. AI与游戏：AI在游戏开发、发行、运营中的应用
5. 行业新闻：不属于以上四类，但仍具行业意义
"""

import logging
from typing import List, Dict
import json
import re

from ai_service.deepseek_client import get_client
from crawler.models import ScoredNewsItem

logger = logging.getLogger(__name__)

CATEGORY_DEFINITIONS = {
    "big_tech": {
        "name": "大厂动态",
        "description": "外部公司（OpenAI、Google、Meta、Microsoft等）重大动作"
    },
    "ai_products": {
        "name": "AI应用与产品",
        "description": "AI工具、平台、商业化产品发布"
    },
    "ai_tech": {
        "name": "AI模型与技术",
        "description": "模型、算法、技术进展、基础能力提升"
    },
    "ai_gaming": {
        "name": "AI与游戏",
        "description": "AI在游戏开发、发行、运营中的应用"
    },
    "industry_news": {
        "name": "行业新闻",
        "description": "不属于以上四类，但仍具行业意义"
    }
}


class Classifier:
    """新闻分类器"""

    def __init__(self):
        self.client = get_client()

    def classify_single(self, title: str, summary: str, source_key: str = None) -> str:
        """基于规则的快速分类"""
        if source_key:
            big_tech_sources = [
                "claude_anthropic", "google_blog", "google_workspace",
                "google_deepmind", "google_research"
            ]
            if source_key in big_tech_sources:
                return "big_tech"

            if source_key == "producthunt":
                return "ai_products"

            tech_sources = ["hackernews", "v2ex"]
            if source_key in tech_sources:
                return "ai_tech"

        text = f"{title} {summary}".lower()

        gaming_keywords = [
            "游戏", "game", "gaming", "npc", "手游", "端游",
            "电竞", "esport", "玩家", "player", "买量", "获客",
            "游戏发行", "app store", "google play", "游戏公司",
            "游戏开发", "虚拟人", "数字人", "ugc", "unity", "unreal"
        ]
        if any(kw in text for kw in gaming_keywords):
            return "ai_gaming"

        big_tech_companies = ["openai", "google", "meta", "microsoft", "anthropic", "deepmind", "facebook"]
        big_tech_keywords = ["收购", "并购", "merger", "acquisition", "战略", "策略", "投资", "融资", "funding", "ipo", "上市", "估值", "valuation"]

        has_company = any(company in text for company in big_tech_companies)
        has_action = any(kw in text for kw in big_tech_keywords)

        if has_company and has_action:
            return "big_tech"

        product_keywords = [
            "发布", "launch", "推出", "release", "上线", "工具", "tool",
            "平台", "platform", "产品", "product", "应用", "app", "application",
            "功能", "feature", "服务", "service", "api", "插件", "plugin",
            "更新", "update", "升级", "upgrade"
        ]
        if any(kw in text for kw in product_keywords):
            return "ai_products"

        tech_keywords = [
            "模型", "model", "gpt", "llm", "大模型", "算法", "algorithm",
            "训练", "training", "推理", "inference", "参数", "parameter",
            "transformer", "diffusion", "gan", "技术突破", "breakthrough",
            "benchmark", "性能", "performance", "架构", "architecture"
        ]
        if any(kw in text for kw in tech_keywords):
            return "ai_tech"

        return "industry_news"

    def classify_batch(
        self,
        news_list: List[ScoredNewsItem],
        use_ai: bool = False
    ) -> Dict[str, List[ScoredNewsItem]]:
        """批量分类新闻"""
        if use_ai:
            return self._classify_with_ai(news_list)

        result = {
            "big_tech": [],
            "ai_products": [],
            "ai_tech": [],
            "ai_gaming": [],
            "industry_news": []
        }

        for item in news_list:
            summary = item.summary_cn or item.raw_item.summary
            source_key = item.raw_item.source_key
            category = self.classify_single(item.raw_item.title, summary, source_key)
            item.category = category
            result[category].append(item)

        logger.info("分类完成:")
        for cat_key, cat_items in result.items():
            cat_name = CATEGORY_DEFINITIONS[cat_key]["name"]
            logger.info(f"  {cat_name}: {len(cat_items)} 条")

        return result

    def _classify_with_ai(self, news_list: List[ScoredNewsItem]) -> Dict[str, List[ScoredNewsItem]]:
        """使用AI模型进行更精确的分类"""
        news_to_classify = []
        for i, item in enumerate(news_list):
            title_cn = item.title_cn or item.raw_item.title
            summary = item.summary_cn or item.raw_item.summary
            news_to_classify.append({
                "index": i,
                "title": title_cn,
                "summary": summary[:200]
            })

        batch_size = 10
        results = {}

        for start in range(0, len(news_to_classify), batch_size):
            batch = news_to_classify[start:start + batch_size]

            prompt = f"""请对以下新闻进行分类，从五个类别中选择一个最合适的：

1. big_tech - 大厂动态：OpenAI、Google、Meta、Microsoft等外部公司的重大动作
2. ai_products - AI应用与产品：AI工具、平台、商业化产品发布
3. ai_tech - AI模型与技术：模型、算法、技术进展、基础能力提升
4. ai_gaming - AI与游戏：AI在游戏开发、发行、运营中的应用
5. industry_news - 行业新闻：不属于以上四类，但仍具行业意义

新闻列表：
{json.dumps(batch, ensure_ascii=False, indent=2)}

请按JSON格式输出，如: {{"0": "big_tech", "1": "ai_products", ...}}
只输出JSON，不要其他内容。"""

            messages = [
                {
                    "role": "system",
                    "content": "你是一位专业的科技新闻编辑，擅长对新闻进行准确分类。"
                },
                {"role": "user", "content": prompt}
            ]

            try:
                response = self.client.chat(messages, temperature=0.1, max_tokens=500)

                if response:
                    cleaned = response.strip()
                    if cleaned.startswith("```"):
                        cleaned = re.sub(r'^```\w*\n?', '', cleaned)
                        cleaned = re.sub(r'\n?```$', '', cleaned)

                    batch_results = json.loads(cleaned)
                    for idx, cat in batch_results.items():
                        results[int(idx) + start] = cat
            except Exception as e:
                logger.warning(f"AI分类批次失败: {e}")
                for i, item_data in enumerate(batch):
                    idx = start + i
                    category = self.classify_single(item_data["title"], item_data["summary"])
                    results[idx] = category

        result = {
            "big_tech": [],
            "ai_products": [],
            "ai_tech": [],
            "ai_gaming": [],
            "industry_news": []
        }

        for i, item in enumerate(news_list):
            category = results.get(i, "industry_news")
            item.category = category
            result[category].append(item)

        logger.info("AI分类完成:")
        for cat_key, cat_items in result.items():
            cat_name = CATEGORY_DEFINITIONS[cat_key]["name"]
            logger.info(f"  {cat_name}: {len(cat_items)} 条")

        return result
