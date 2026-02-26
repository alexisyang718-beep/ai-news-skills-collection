# -*- coding: utf-8 -*-
"""
关键词库配置
多层评分机制：高权重核心词 > 核心词 > 辅助词
排除低价值内容（观点文、泛应用、社会新闻中的AI点缀）
"""

import re

# ============== 高权重关键词（产品发布/重大事件） ==============
# 匹配到这些词的新闻直接获得高分
HIGH_VALUE_ZH = [
    "发布", "推出", "上线", "开源", "开放",
    "融资", "收购", "投资", "估值", "IPO",
    "突破", "首次", "全球首", "最新",
    "GPT-5", "GPT-4", "o1", "o3", "o4",
    "Gemini", "Claude", "Llama", "Qwen", "DeepSeek",
    "Sora", "文生视频", "Runway",
]

HIGH_VALUE_EN = [
    r"\blaunch", r"\breleas", r"\bannounce", r"open.?source",
    r"\bfunding\b", r"\bacquisition\b", r"\bIPO\b", r"\bvaluation\b",
    r"breakthrough", r"\bfirst\b.*\bever\b",
    r"GPT-5", r"GPT-4o", r"\bo[134]-", r"o1\b", r"o3\b",
    r"Gemini", r"Claude\s*\d", r"Llama\s*\d", r"Qwen",
    r"Sora\b", r"Runway\b",
]

# ============== 核心AI关键词 ==============
CORE_KEYWORDS_ZH = [
    "ai", "人工智能", "aigc", "llm", "大模型", "多模态",
    "智能体", "推理", "训练", "微调", "深度学习", "机器学习",
    "transformer", "gpt", "claude", "gemini", "deepseek",
    "语音识别", "计算机视觉", "生成式", "文生图",
    "gpu", "算力", "openai", "anthropic", "copilot", "chatgpt",
    "midjourney", "stable diffusion",
]

CORE_KEYWORDS_EN = [
    r"\bai\b", r"artificial intelligence", r"\baigc\b", r"\bllm\b",
    r"large language model", r"foundation model", r"multimodal",
    r"\bagent\b", r"reasoning", r"inference", r"training", r"fine-tuning",
    r"deep learning", r"machine learning", r"neural network",
    r"transformer", r"\bgpt\b", r"claude", r"gemini", r"deepseek",
    r"speech recognition", r"computer vision", r"generative",
    r"\bgpu\b", r"compute", r"openai", r"anthropic", r"copilot",
    r"chatgpt", r"midjourney", r"stable diffusion",
]

# ============== 辅助关键词 ==============
AUX_KEYWORDS_ZH = [
    "google", "deepmind", "microsoft", "meta", "amazon", "nvidia",
    "腾讯", "字节", "阿里", "百度", "华为", "小米",
    "智谱", "minimax", "moonshot", "月之暗面", "kimi",
    "融资", "投资", "收购", "估值",
]

AUX_KEYWORDS_EN = [
    r"google", r"deepmind", r"microsoft", r"\bmeta\b",
    r"amazon", r"\baws\b", r"nvidia", r"apple",
    r"funding", r"investment", r"acquisition", r"valuation",
]

# ============== 排除关键词（低价值内容） ==============
EXCLUDE_KEYWORDS_ZH = [
    "招聘", "诉讼", "课程", "培训",
    # 边缘社会新闻
    "贩毒", "毒品", "犯罪集团", "黑帮",
    "战争", "军事打击", "导弹",
    # 纯观点文/水文标志
    "如何应对", "该如何看待", "你怎么看",
]

EXCLUDE_KEYWORDS_EN = [
    r"\bhiring\b", r"\btutorial\b", r"how to",
    r"\blawsuit\b", r"\bcourse\b", r"training program",
    # 边缘社会新闻
    r"\bcartel\b", r"\bdrug\b.*\btraffick", r"\bmilitary strike",
    # 纯观点文
    r"opinion:", r"editorial:",
]

# ============== 低价值信号词（降分但不排除） ==============
# 这些词出现时说明新闻可能是泛AI讨论而非具体事件
LOW_VALUE_SIGNALS_ZH = [
    "如何", "为什么", "能否", "是否", "争议",
    "窃取", "盗取", "黑客利用", "被用于",
    "强制", "禁止使用", "监管担忧",
    "另一回事", "尚未", "还需",
    "观点", "评论", "专栏", "分析师认为",
    # 教程/指南类
    "教程", "指南", "安装指南", "保姆级", "手把手",
    "方案", "实战指南", "入门", "入行",
    "零代码", "零基础", "0经验",
    "心得", "经历", "亲身",
    "附代码", "附项目地址", "附教程",
    # 自媒体感叹类
    "炸了", "震撼", "疯了", "太强了", "吊打",
    "居然", "竟然", "万字",
]

LOW_VALUE_SIGNALS_EN = [
    r"\bhow\b.*\bwill\b", r"\bwhy\b", r"\bcan\b.*\breally\b",
    r"\bsteal\b", r"\bhack\b", r"\btheft\b", r"\bused\s+by\b.*\bcriminal",
    r"\bforce\b.*\bemploy", r"\bmandate\b",
    r"\banother\s+matter\b", r"\bnot\s+yet\b",
    r"\bopinion\b", r"\bcommentary\b", r"\bcolumn\b",
    r"\bcontrovers", r"\bconcern",
    # tutorial/guide
    r"\btutorial\b", r"\bguide\b", r"\bstep.by.step\b",
    r"\bhow\s+to\b", r"\bgetting\s+started\b",
]

# ============== 编译正则 ==============
COMPILED_HIGH_ZH = [re.compile(kw, re.IGNORECASE) for kw in HIGH_VALUE_ZH]
COMPILED_HIGH_EN = [re.compile(kw, re.IGNORECASE) for kw in HIGH_VALUE_EN]
COMPILED_CORE_EN = [re.compile(kw, re.IGNORECASE) for kw in CORE_KEYWORDS_EN]
COMPILED_AUX_EN = [re.compile(kw, re.IGNORECASE) for kw in AUX_KEYWORDS_EN]
COMPILED_EXCLUDE_EN = [re.compile(kw, re.IGNORECASE) for kw in EXCLUDE_KEYWORDS_EN]
COMPILED_CORE_ZH = [re.compile(kw, re.IGNORECASE) for kw in CORE_KEYWORDS_ZH]
COMPILED_AUX_ZH = [re.compile(kw, re.IGNORECASE) for kw in AUX_KEYWORDS_ZH]
COMPILED_EXCLUDE_ZH = [re.compile(kw) for kw in EXCLUDE_KEYWORDS_ZH]
COMPILED_LOW_ZH = [re.compile(kw, re.IGNORECASE) for kw in LOW_VALUE_SIGNALS_ZH]
COMPILED_LOW_EN = [re.compile(kw, re.IGNORECASE) for kw in LOW_VALUE_SIGNALS_EN]


def check_keywords(text: str, language: str) -> dict:
    """检查关键词匹配，返回分层结果"""
    if language == "zh":
        high = [kw for kw, p in zip(HIGH_VALUE_ZH, COMPILED_HIGH_ZH) if p.search(text)]
        core = [kw for kw, p in zip(CORE_KEYWORDS_ZH, COMPILED_CORE_ZH) if p.search(text)]
        aux = [kw for kw, p in zip(AUX_KEYWORDS_ZH, COMPILED_AUX_ZH) if p.search(text)]
        exclude = any(p.search(text) for p in COMPILED_EXCLUDE_ZH)
        low_signals = sum(1 for p in COMPILED_LOW_ZH if p.search(text))
    else:
        t = text.lower()
        high = [kw for kw, p in zip(HIGH_VALUE_EN, COMPILED_HIGH_EN) if p.search(t)]
        core = [kw for kw, p in zip(CORE_KEYWORDS_EN, COMPILED_CORE_EN) if p.search(t)]
        aux = [kw for kw, p in zip(AUX_KEYWORDS_EN, COMPILED_AUX_EN) if p.search(t)]
        exclude = any(p.search(t) for p in COMPILED_EXCLUDE_EN)
        low_signals = sum(1 for p in COMPILED_LOW_EN if p.search(t))

    return {
        "pass": len(core) >= 1 and not exclude,
        "high_matched": high,
        "core_matched": core,
        "aux_matched": aux,
        "has_exclude": exclude,
        "low_signal_count": low_signals,
    }
