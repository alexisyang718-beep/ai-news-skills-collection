"""ai-deep-column 全局配置"""
import os
from pathlib import Path
from dotenv import load_dotenv

# ============== 项目路径 ==============
PROJECT_ROOT = Path(__file__).parent.parent.parent  # ai-deep-column/
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"

for d in [DATA_DIR, OUTPUT_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ============== 加载 .env ==============
# 优先加载自己的 .env，再加载日报的 .env（复用密钥）
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT.parent / "ai-daily-report" / ".env")

# ============== DeepSeek API ==============
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
API_MAX_RETRIES = 3
API_RETRY_DELAY = 2
API_TIMEOUT = 120  # 长文生成需要更长超时

# ============== 微信公众号 ==============
WECHAT_APP_ID = os.environ.get("WECHAT_APP_ID", "")
WECHAT_APP_SECRET = os.environ.get("WECHAT_APP_SECRET", "")
WECHAT_API_BASE = "https://api.weixin.qq.com/cgi-bin"

# ============== 企业微信 ==============
WECOM_WEBHOOK_URL = os.environ.get("WECOM_WEBHOOK_URL", "")

# ============== 共享数据（来自 ai-hourly-buzz） ==============
SHARED_DATA_DIR = Path(os.environ.get(
    "SHARED_DATA_DIR",
    str(PROJECT_ROOT.parent / "ai-hourly-buzz" / "data")
))
SHARED_ARCHIVE_FILE = SHARED_DATA_DIR / "archive.json"
SHARED_LATEST_FILE = SHARED_DATA_DIR / "latest-24h.json"  # 已过滤的AI新闻

# ============== 热点聚类参数 ==============
CLUSTER_SIMILARITY_THRESHOLD = 0.58  # 标题相似度阈值
CLUSTER_MIN_ARTICLES = 4             # 最少报道数才算热点
CLUSTER_TIME_WINDOW_HOURS = 28       # 时间窗口（含缓冲）
MAX_CANDIDATE_TOPICS = 8             # 最多推送候选话题数
ARTICLE_WORD_COUNT = "800-1500"      # 专栏文章字数范围

# ============== 封面 ==============
DEFAULT_COVER = DATA_DIR / "default_cover.jpg"

# ============== 日志 ==============
LOG_FILE = LOGS_DIR / "deep_column.log"
