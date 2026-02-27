"""热点聚类选题引擎

优先从 latest-24h.json 的 items_ai 加载已过滤的AI新闻（数据量小、无需重复过滤），
回退到 archive.json 全量过滤。
按「标题相似度 + 关键实体重叠」双重策略聚类，
找出被多个源报道的同一事件作为热点候选。
"""
import json
import hashlib
import logging
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Dict, Optional, Any, Set

from dateutil import parser as dateparser
import pytz

from config.settings import (
    SHARED_ARCHIVE_FILE,
    SHARED_LATEST_FILE,
    CLUSTER_SIMILARITY_THRESHOLD,
    CLUSTER_MIN_ARTICLES,
    CLUSTER_TIME_WINDOW_HOURS,
    MAX_CANDIDATE_TOPICS,
)

logger = logging.getLogger(__name__)
BJT = pytz.timezone("Asia/Shanghai")

# ============== AI 相关性过滤 ==============

AI_KEYWORDS = [
    "aigc", "llm", "gpt", "claude", "gemini", "deepseek", "openai",
    "anthropic", "hugging face", "huggingface", "transformer", "diffusion",
    "agent", "多模态", "大模型", "大语言模型", "人工智能", "机器学习",
    "深度学习", "智能体", "算力", "微调", "chatgpt", "copilot",
    "midjourney", "stable diffusion", "sora", "mistral", "llama",
    "qwen", "通义", "文心", "kimi", "moonshot", "百川", "智谱",
    "coze", "dify", "langchain", "rag",
]

TECH_KEYWORDS = [
    "robot", "robotics", "embodied", "autonomous", "chip", "semiconductor",
    "cuda", "npu", "gpu", "开源", "芯片", "机器人", "具身", "自动驾驶",
]

NOISE_KEYWORDS = [
    "娱乐", "明星", "八卦", "足球", "篮球", "彩票", "情感", "旅游", "美食",
]

COMMERCE_KEYWORDS = [
    "淘宝", "天猫", "京东", "拼多多", "券后", "热销", "促销", "优惠",
    "补贴", "下单", "首发价", "原价", "到手", "任选",
]

EN_SIGNAL_RE = re.compile(
    r"(?i)(?<![a-z0-9])"
    r"(ai|aigc|llm|gpt|openai|anthropic|deepseek|gemini|claude|"
    r"robot|robotics|machine learning|artificial intelligence|"
    r"transformer|diffusion|neural|copilot|chatgpt|midjourney|sora|"
    r"llama|mistral|stable diffusion|langchain|rag)"
    r"(?![a-z0-9])"
)

AI_SITE_IDS = {"aibase", "aihot", "aihubtoday"}
TOPHUB_ALLOW = [
    "readhub", "hacker news", "github", "product hunt", "v2ex",
    "少数派", "infoq", "36氪", "机器之心", "量子位", "科技", "人工智能",
]
TOPHUB_BLOCK = [
    "热销总榜", "淘宝", "天猫", "京东", "拼多多", "抖音", "快手", "微博", "小红书",
]


def _contains_any(text: str, keywords: list) -> bool:
    t = text.lower()
    return any(k in t for k in keywords)


def is_ai_related(record: dict) -> bool:
    """判断一条新闻是否与AI/科技相关"""
    site_id = str(record.get("site_id", "")).lower()
    title = str(record.get("title", ""))
    source = str(record.get("source", record.get("site_name", "")))
    url = str(record.get("url", ""))
    text = f"{title} {source} {url}".lower()

    if _contains_any(text, COMMERCE_KEYWORDS):
        return False
    if site_id == "zeli":
        return "24h" in source.lower()
    if site_id == "tophub":
        src = source.lower()
        if _contains_any(src, TOPHUB_BLOCK):
            return False
        if not _contains_any(src, TOPHUB_ALLOW):
            return False
    if site_id in AI_SITE_IDS:
        return True
    has_ai = _contains_any(text, AI_KEYWORDS) or EN_SIGNAL_RE.search(text) is not None
    has_tech = _contains_any(text, TECH_KEYWORDS)
    if not (has_ai or has_tech):
        return False
    if _contains_any(text, NOISE_KEYWORDS) and not has_ai:
        return False
    return True


# ============== 实体提取（轻量级） ==============

# 要跟踪的关键实体（公司/产品/人名）
ENTITY_PATTERNS = [
    # 公司（归一化为统一名）
    (r"(?i)\b(openai)\b", "openai"),
    (r"(?i)\b(anthropic)\b", "anthropic"),
    (r"(?i)\b(google|alphabet)\b|谷歌", "google"),
    (r"(?i)\b(nvidia)\b|英伟达", "nvidia"),
    (r"(?i)\b(samsung)\b|三星", "samsung"),
    (r"(?i)\b(microsoft)\b|微软", "microsoft"),
    (r"(?i)\b(apple)\b|苹果", "apple"),
    (r"(?i)\b(meta)\b", "meta"),
    (r"(?i)\b(amazon)\b|亚马逊", "amazon"),
    (r"(?i)\b(tesla)\b|特斯拉", "tesla"),
    (r"(?i)\b(deepseek)\b", "deepseek"),
    (r"(?i)\b(mistral)\b", "mistral"),
    (r"(?i)\b(xai)\b", "xai"),
    (r"(?i)\b(hugging\s*face)\b", "huggingface"),
    (r"百度", "baidu"),
    (r"腾讯", "tencent"),
    (r"华为", "huawei"),
    (r"字节", "bytedance"),
    (r"阿里", "alibaba"),
    # 产品（归一化）
    (r"(?i)\b(gemini)\b", "gemini"),
    (r"(?i)\b(claude)\b", "claude"),
    (r"(?i)\b(gpt[-\s]?\d?|chatgpt)\b", "gpt"),
    (r"(?i)\b(copilot)\b", "copilot"),
    (r"(?i)\b(sora)\b", "sora"),
    (r"(?i)\b(galaxy\s*s2\d)\b", "galaxy_s26"),
    (r"(?i)\b(llama)\b", "llama"),
    (r"(?i)\b(qwen)\b|通义", "qwen"),
    # 事件/概念
    (r"(?i)\b(safety|safe)\b|安全", "safety"),
    (r"(?i)\b(pledge|promise|承诺)\b", "pledge"),
    (r"(?i)\b(policy|policies|政策)\b", "policy"),
    (r"(?i)\b(fundrais|funding|融资|raised?\s+\$)\b", "fundraise"),
    (r"(?i)\b(acqui[rs]|收购)\b", "acquisition"),
    (r"(?i)\b(agentic|agent)\b|智能体", "agent"),
    (r"(?i)\b(robotaxi|自动驾驶|autonomous\s*driv)\b", "autonomous"),
    (r"(?i)\b(waymo)\b", "waymo"),
    (r"(?i)\b(wayve)\b", "wayve"),
    (r"(?i)\b(uber)\b", "uber"),
]
_entity_regexes = [(re.compile(p), norm) for p, norm in ENTITY_PATTERNS]
def extract_entities(text: str) -> Set[str]:
    """从文本中提取归一化实体"""
    entities = set()
    for regex, norm in _entity_regexes:
        if regex.search(text):
            entities.add(norm)
    return entities


# ============== 数据模型 ==============

class NewsItem:
    """轻量新闻条目"""
    __slots__ = ("id", "title", "url", "source", "site_id", "published_at",
                 "title_zh", "title_en", "entities")

    def __init__(self, **kwargs):
        for k in self.__slots__:
            setattr(self, k, kwargs.get(k, ""))
        if not self.entities:
            self.entities = set()


class TopicCluster:
    """一个热点话题聚类"""

    MIN_TITLE_LEN = 8

    def __init__(self, seed: NewsItem):
        self.articles: List[NewsItem] = [seed]
        self.sources: set = {seed.site_id}
        self.entities: Set[str] = set(seed.entities)
        self.representative_title: str = self._pick_title(seed)

    @property
    def count(self) -> int:
        return len(self.articles)

    @property
    def source_count(self) -> int:
        return len(self.sources)

    def try_add(self, item: NewsItem, threshold: float) -> bool:
        """双重策略聚类：标题相似度 OR 实体重叠度"""
        item_title = self._normalize(item.title_zh or item.title)
        if len(item_title) < self.MIN_TITLE_LEN:
            return False

        # 策略1: 标题相似度
        for existing in self.articles[:10]:
            existing_title = self._normalize(existing.title_zh or existing.title)
            if len(existing_title) < self.MIN_TITLE_LEN:
                continue
            ratio = SequenceMatcher(None, item_title, existing_title).ratio()
            if ratio >= threshold:
                self._add(item)
                return True

        # 策略2: 实体重叠 — 至少有2个共同的「具体实体」（公司或产品）
        # 排除纯概念词（safety, agent 等）的误聚
        if item.entities and self.entities:
            overlap = item.entities & self.entities
            # 具体实体 = 公司名 + 产品名（非通用概念）
            GENERIC_ENTITIES = {"safety", "pledge", "policy", "fundraise", "acquisition",
                                "agent", "autonomous", "gpt"}
            concrete_overlap = overlap - GENERIC_ENTITIES
            # 需要至少1个具体实体重叠 + 总重叠≥2
            if len(concrete_overlap) >= 1 and len(overlap) >= 2:
                self._add(item)
                return True

        return False

    def _add(self, item: NewsItem):
        self.articles.append(item)
        self.sources.add(item.site_id)
        self.entities |= item.entities
        # 更新代表标题
        new_title = self._pick_title(item)
        if self._is_better_title(new_title, self.representative_title):
            self.representative_title = new_title

    @staticmethod
    def _pick_title(item: 'NewsItem') -> str:
        zh = item.title_zh
        en = item.title
        # 排除 GitHub 仓库名格式
        if zh and len(zh) > 8 and not re.match(r'^[\w.-]+\s*/\s*[\w.-]+$', zh.strip()):
            return zh
        if en and not re.match(r'^[\w.-]+\s*/\s*[\w.-]+$', en.strip()):
            return en
        return zh or en

    @staticmethod
    def _is_better_title(new: str, old: str) -> bool:
        """判断新标题是否比旧的更适合做代表"""
        # 偏好中文、长度适中(15-50)的标题
        def score(t):
            s = 0
            if any('\u4e00' <= c <= '\u9fff' for c in t):
                s += 10  # 中文优先
            length = len(t)
            if 15 <= length <= 50:
                s += 5
            elif 10 <= length <= 60:
                s += 2
            return s
        return score(new) > score(old)

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)
        for prefix in ["ai ", "人工智能 ", "突发 ", "快讯 ", "重磅 ", "独家 "]:
            if text.startswith(prefix):
                text = text[len(prefix):]
        return text.strip()

    def summary_titles(self, max_n: int = 8) -> List[str]:
        """返回聚类中的代表性标题列表（去重，排除GitHub仓库名）"""
        seen = set()
        titles = []
        for a in self.articles:
            t = a.title_zh if a.title_zh and len(a.title_zh) > 8 else a.title
            normalized = self._normalize(t)
            if len(normalized) < self.MIN_TITLE_LEN:
                continue
            # 跳过 GitHub 仓库格式（xxx / yyy）
            if re.match(r'^[\w.-]+\s*/\s*[\w.-]+$', t.strip()):
                continue
            if normalized not in seen:
                seen.add(normalized)
                titles.append(t)
            if len(titles) >= max_n:
                break
        return titles


# ============== 主选择器 ==============

class TopicSelector:
    """热点聚类选题引擎"""

    def __init__(self):
        self.clusters: List[TopicCluster] = []

    def load_news(self) -> List[NewsItem]:
        """优先从 latest-24h.json 的 items_ai 加载（已预过滤AI新闻），
        回退到 archive.json 全量过滤。"""

        items_raw = []
        source_name = ""

        # 优先: latest-24h.json → items_ai（已过滤，数据量小）
        if SHARED_LATEST_FILE.exists():
            with open(SHARED_LATEST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            items_raw = data.get("items_ai", [])
            source_name = f"latest-24h.json/items_ai ({len(items_raw)} 条)"
            logger.info(f"从 {source_name} 加载数据")
        # 回退: archive.json（需要自行过滤）
        elif SHARED_ARCHIVE_FILE.exists():
            with open(SHARED_ARCHIVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            all_items = data.get("items", data) if isinstance(data, dict) else data
            items_raw = [r for r in all_items if is_ai_related(r)]
            source_name = f"archive.json (过滤后 {len(items_raw)} 条)"
            logger.info(f"latest-24h.json 不存在，回退到 {source_name}")
        else:
            logger.error(f"数据文件不存在: {SHARED_LATEST_FILE} / {SHARED_ARCHIVE_FILE}")
            return []

        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=CLUSTER_TIME_WINDOW_HOURS)
        items = []

        for raw in items_raw:
            pub_time = self._parse_time(raw)
            if pub_time and pub_time < cutoff:
                continue

            title = raw.get("title", "")
            if len(title) < 5:
                continue

            title_zh = raw.get("title_zh", "")
            full_text = f"{title} {title_zh}"
            entities = extract_entities(full_text)

            item = NewsItem(
                id=raw.get("id", hashlib.md5(raw.get("url", "").encode()).hexdigest()),
                title=title,
                url=raw.get("url", ""),
                source=raw.get("source", raw.get("site_name", "")),
                site_id=raw.get("site_id", ""),
                published_at=pub_time,
                title_zh=title_zh,
                title_en=raw.get("title_en", ""),
                entities=entities,
            )
            items.append(item)

        logger.info(f"数据源: {source_name}，时间窗口内有效 {len(items)} 条")
        return items

    def cluster(self, items: List[NewsItem]) -> List[TopicCluster]:
        """对新闻进行聚类"""
        clusters: List[TopicCluster] = []

        for item in items:
            title = TopicCluster._normalize(item.title_zh or item.title)
            if len(title) < TopicCluster.MIN_TITLE_LEN:
                continue

            added = False
            for c in clusters:
                if c.try_add(item, CLUSTER_SIMILARITY_THRESHOLD):
                    added = True
                    break
            if not added:
                clusters.append(TopicCluster(seed=item))

        # 过滤：至少 N 条报道，且来源数≥2
        hot_clusters = [c for c in clusters
                        if c.count >= CLUSTER_MIN_ARTICLES and c.source_count >= 2]

        # 排除纯 GitHub 仓库聚类（所有文章标题都是 xxx/yyy 格式）
        GITHUB_REPO_RE = re.compile(r'^[\w.-]+\s*/\s*[\w.-]+$')
        filtered = []
        for c in hot_clusters:
            real_titles = [a for a in c.articles
                           if not GITHUB_REPO_RE.match((a.title_zh or a.title).strip())]
            if len(real_titles) >= 2:  # 至少2条非仓库名标题
                filtered.append(c)
        hot_clusters = filtered
        # 按 报道数 × 来源数 排序
        hot_clusters.sort(key=lambda c: c.count * c.source_count, reverse=True)

        self.clusters = hot_clusters[:MAX_CANDIDATE_TOPICS]
        logger.info(f"聚类完成：{len(clusters)} 个簇，"
                     f"{len(hot_clusters)} 个热点（≥{CLUSTER_MIN_ARTICLES}篇），"
                     f"取 Top {len(self.clusters)}")

        for i, c in enumerate(self.clusters):
            logger.info(f"  话题{i+1}: {c.representative_title[:40]} "
                         f"({c.count}篇/{c.source_count}源) "
                         f"实体: {', '.join(list(c.entities)[:5])}")
        return self.clusters

    def get_candidates(self) -> List[Dict[str, Any]]:
        """返回候选话题列表"""
        candidates = []
        for i, c in enumerate(self.clusters):
            candidates.append({
                "topic_id": i,
                "title": c.representative_title,
                "article_count": c.count,
                "source_count": c.source_count,
                "sample_titles": c.summary_titles(5),
                "sources": list(c.sources),
                "entities": list(c.entities)[:10],
            })
        return candidates

    def get_cluster_by_id(self, topic_id: int) -> Optional[TopicCluster]:
        if 0 <= topic_id < len(self.clusters):
            return self.clusters[topic_id]
        return None

    @staticmethod
    def _parse_time(raw: dict) -> Optional[datetime]:
        for key in ("published_at", "first_seen_at", "last_seen_at", "timestamp"):
            val = raw.get(key)
            if not val:
                continue
            try:
                if isinstance(val, (int, float)):
                    return datetime.fromtimestamp(val, tz=timezone.utc)
                dt = dateparser.parse(str(val))
                if dt and dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                continue
        return None
