# -*- coding: utf-8 -*-
"""
全局配置文件
支持环境变量覆盖，适合 GitHub Actions 部署
"""

import os
from pathlib import Path

# ============== 项目路径 ==============
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"

# ============== 共享数据路径（从 ai-hourly-buzz 读取） ==============
# GitHub Actions 中通过环境变量指定
SHARED_DATA_DIR = Path(os.environ.get(
    "SHARED_DATA_DIR",
    str(PROJECT_ROOT.parent / "ai-hourly-buzz" / "data")
))
SHARED_ARCHIVE_FILE = SHARED_DATA_DIR / "archive.json"

# ============== DeepSeek API 配置 ==============
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

# API调用参数
API_MAX_RETRIES = 3
API_RETRY_DELAY = 2
API_TIMEOUT = 60
API_BATCH_SIZE = 5

# ============== 微信公众号配置 ==============
WECHAT_APP_ID = os.environ.get("WECHAT_APP_ID", "")
WECHAT_APP_SECRET = os.environ.get("WECHAT_APP_SECRET", "")
WECHAT_API_BASE = "https://api.weixin.qq.com/cgi-bin"

# ============== 内容处理配置 ==============
MAX_CONTENT_LENGTH = 3000
TITLE_SIMILARITY_THRESHOLD = 0.8
MIN_NEWS_PER_CATEGORY = 3
MAX_NEWS_PER_CATEGORY = 10

# ============== 时间配置 ==============
TIMEZONE = "Asia/Shanghai"
SCHEDULE_TIME = "07:00"

# ============== 来源优先级 ==============
SOURCE_PRIORITY = {
    "openai": 1, "google_blog": 1, "google_research": 1,
    "google_workspace": 1, "anthropic": 1, "github": 1,
    "techcrunch": 2, "theverge": 2, "techspective": 2,
    "36kr": 3, "qbitai": 3, "jiqizhixin": 3,
}

# ============== 爬虫配置 ==============
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 1

# ============== 日志配置 ==============
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = LOGS_DIR / "daily_report.log"

# ============== 缓存配置 ==============
NEWS_CACHE_FILE = DATA_DIR / "news_cache.json"
CACHE_RETENTION_DAYS = 7
