# -*- coding: utf-8 -*-
"""
RSS源配置
16个经过验证的信息源
"""

RSSHUB_MIRRORS = [
    "https://rsshub.rssforever.com",
    "https://rsshub.ddsrem.com",
]
RSSHUB_BASE = RSSHUB_MIRRORS[0]

def rsshub(path: str) -> str:
    return f"{RSSHUB_BASE}{path}"

RSS_SOURCES = [
    # === 可获取完整正文（5个）===
    {
        "name": "Google Research Blog", "key": "google_research",
        "url": "https://research.google/blog/rss/",
        "source_type": "official", "language": "en",
        "extraction_method": "readability",
    },
    {
        "name": "TechCrunch AI", "key": "techcrunch_ai",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "source_type": "en_media", "language": "en",
        "extraction_method": "readability",
    },
    {
        "name": "The Verge", "key": "theverge",
        "url": "https://www.theverge.com/rss/index.xml",
        "source_type": "en_media", "language": "en",
        "extraction_method": "readability",
    },
    {
        "name": "Techspective AI", "key": "techspective_ai",
        "url": "https://techspective.net/category/technology/artificial-intelligence/feed/",
        "source_type": "en_media", "language": "en",
        "extraction_method": "readability",
    },
    {
        "name": "GitHub Blog", "key": "github_blog",
        "url": "https://github.blog/feed/",
        "source_type": "official", "language": "en",
        "extraction_method": "readability",
    },

    # === RSS本身已完整（4个）===
    {
        "name": "Google Workspace Updates", "key": "google_workspace",
        "url": "https://feeds.feedburner.com/GoogleAppsUpdates",
        "source_type": "official", "language": "en",
        "extraction_method": "rss_content",
    },
    {
        "name": "硅基观察Pro", "key": "guiji_pro",
        "url": "https://wechat2rss.bestblogs.dev/feed/f21c3e34df9b5fecfda57e2e53512864255ed4cd.xml",
        "source_type": "zh_media", "language": "zh",
        "extraction_method": "rss_html",
    },
    {
        "name": "赛博禅心", "key": "saibo_chanxin",
        "url": "https://wechat2rss.bestblogs.dev/feed/752c31ca0446b837339463fc5440539e20267d2f.xml",
        "source_type": "zh_media", "language": "zh",
        "extraction_method": "rss_html",
    },
    {
        "name": "Founder Park", "key": "founder_park",
        "url": "https://wechat2rss.bestblogs.dev/feed/f940695505f2be1399d23cc98182297cadf6f90d.xml",
        "source_type": "zh_media", "language": "zh",
        "extraction_method": "rss_html",
    },

    # === 仅摘要（5个）===
    {
        "name": "新智元", "key": "xin_zhiyuan",
        "url": "https://raw.githubusercontent.com/osnsyc/Wechat-Scholar/main/channels/gh_108f2a2a27f4.xml",
        "source_type": "zh_media", "language": "zh",
        "extraction_method": "summary_only",
    },
    {
        "name": "Claude (Anthropic)", "key": "claude_anthropic",
        "url": "https://api.xgo.ing/rss/user/01f60d63a61b44d692cc35c7feb0b4a4",
        "source_type": "official", "language": "en",
        "extraction_method": "summary_only",
    },
    {
        "name": "The Rundown AI", "key": "rundown_ai",
        "url": "https://api.xgo.ing/rss/user/83b1ea38940b4a1d81ea57d1ffb12ad7",
        "source_type": "en_media", "language": "en",
        "extraction_method": "summary_only",
    },
    {
        "name": "Google DeepMind Blog", "key": "google_deepmind",
        "url": "https://deepmind.google/blog/rss.xml",
        "source_type": "official", "language": "en",
        "extraction_method": "summary_only",
    },
    {
        "name": "Google Blog", "key": "google_blog",
        "url": "https://blog.google/rss/",
        "source_type": "official", "language": "en",
        "extraction_method": "summary_only",
    },

    # === 网页爬取（2个）===
    {
        "name": "36氪AI频道", "key": "36kr_ai",
        "url": "https://36kr.com/information/AI",
        "source_type": "zh_media", "language": "zh",
        "extraction_method": "web_scrape",
    },
    {
        "name": "Techmeme", "key": "techmeme",
        "url": "https://techmeme.com",
        "source_type": "en_media", "language": "en",
        "extraction_method": "web_scrape",
    },
]

ALL_SOURCES = {s["key"]: s for s in RSS_SOURCES}
