# -*- coding: utf-8 -*-
"""数据模型定义"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class RawNewsItem:
    """原始新闻条目"""
    id: str
    title: str
    url: str
    source_key: str
    source_name: str
    source_type: str  # official / en_media / zh_media / shared
    language: str
    pub_time: Optional[datetime]
    summary: str
    content: str


@dataclass
class ScoredNewsItem:
    """带评分的新闻条目"""
    raw_item: RawNewsItem
    relevance_score: float = 0.0
    keywords_matched: List[str] = field(default_factory=list)
    is_gaming_related: bool = False
    has_exclude_words: bool = False
    # AI 处理后添加
    summary_cn: str = ""      # 中文摘要
    title_cn: str = ""        # 中文标题
    category: str = ""        # 分类结果
