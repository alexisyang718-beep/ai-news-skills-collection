#!/usr/bin/env python3
"""
AI 深度专栏 (ai-deep-column) 主流水线

两种运行模式：
1. 发现模式 (discover)：扫描热点 → 推送候选到企微 → 保存候选
2. 生成模式 (generate)：根据选择的话题ID → 生成专栏 → 发布到微信

用法:
  python main.py discover           # 发现候选话题
  python main.py generate 1         # 生成第1个话题的专栏
  python main.py auto               # 自动选最热话题并生成（全自动模式）
"""
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

import pytz

# 确保项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import LOGS_DIR, LOG_FILE
from topic_selector import TopicSelector
from material_collector import MaterialCollector
from article_writer import get_writer
from html_generator import HTMLGenerator
from wechat_publisher import WeChatPublisher
from wecom_notify import WeComNotifier, save_candidates, load_candidates

BJT = pytz.timezone("Asia/Shanghai")
logger = logging.getLogger(__name__)


def setup_logging():
    """配置日志"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )


class DeepColumnPipeline:
    """深度专栏主流水线"""

    def __init__(self):
        self.selector = TopicSelector()
        self.collector = MaterialCollector()
        self.writer = get_writer()
        self.html_gen = HTMLGenerator()
        self.publisher = WeChatPublisher()
        self.notifier = WeComNotifier()

    def discover(self) -> bool:
        """发现模式：扫描热点 → 推送候选"""
        logger.info("="*50)
        logger.info("📡 开始扫描热点话题...")
        logger.info("="*50)

        # 1. 加载新闻
        items = self.selector.load_news()
        if not items:
            logger.warning("无新闻数据")
            return False

        # 2. 聚类
        clusters = self.selector.cluster(items)
        if not clusters:
            logger.warning("未发现热点话题（无达到阈值的聚类）")
            return False

        # 3. 获取候选列表
        candidates = self.selector.get_candidates()
        logger.info(f"发现 {len(candidates)} 个候选话题")

        # 4. 保存候选
        save_candidates(candidates)

        # 5. 推送到企微 / 打印到终端
        self.notifier.send_candidates(candidates)

        return True

    def generate(self, topic_id: int) -> bool:
        """生成模式：根据话题ID生成专栏并发布"""
        logger.info("="*50)
        logger.info(f"✍️ 开始生成专栏（话题 #{topic_id + 1}）...")
        logger.info("="*50)

        # 1. 加载候选（优先用内存中的，否则从文件加载后重新聚类）
        cluster = self.selector.get_cluster_by_id(topic_id)
        if not cluster:
            # 从文件恢复
            candidates = load_candidates()
            if not candidates or topic_id >= len(candidates):
                logger.error(f"话题 #{topic_id + 1} 不存在，请先运行 discover")
                return False
            # 重新加载并聚类以获取完整数据
            items = self.selector.load_news()
            self.selector.cluster(items)
            cluster = self.selector.get_cluster_by_id(topic_id)
            if not cluster:
                logger.error("重新聚类后仍找不到该话题")
                return False

        topic_title = cluster.representative_title
        logger.info(f"话题: {topic_title} ({cluster.count}篇报道)")

        # 2. 收集素材
        logger.info("📦 收集写作素材...")
        materials = self.collector.collect(cluster)
        logger.info(f"素材准备完成 ({len(materials)} 字符)")

        # 3. AI 生成文章
        logger.info("🤖 AI 撰写文章...")
        title, body = self.writer.write_article(topic_title, materials)
        if not title or not body:
            logger.error("文章生成失败")
            return False
        logger.info(f"文章生成完成: {title} ({len(body)} 字符)")

        # 4. 生成 HTML
        logger.info("🎨 生成 HTML...")
        topic_info = {
            "article_count": cluster.count,
            "source_count": cluster.source_count,
        }
        html = self.html_gen.generate(title, body, topic_info)
        logger.info(f"HTML 生成完成 ({len(html)} 字符)")

        # 5. 发布到微信
        logger.info("📤 发布到微信公众号...")
        now = datetime.now(BJT)
        wechat_title = f"AI专栏 | {title}"
        success = self.publisher.publish_column(wechat_title, html)

        if success:
            tokens = self.writer.total_tokens
            logger.info(f"🎉 专栏发布成功！Token 消耗: {tokens}")
        return success

    def auto(self) -> bool:
        """全自动模式：发现热点 → 选最热 → 生成发布"""
        if not self.discover():
            return False
        # 自动选第一个（最热话题）
        return self.generate(0)


def main():
    setup_logging()

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    mode = sys.argv[1].lower()
    pipeline = DeepColumnPipeline()

    if mode == "discover":
        success = pipeline.discover()

    elif mode == "generate":
        if len(sys.argv) < 3:
            print("用法: python main.py generate <话题编号>")
            print("  例如: python main.py generate 1  (选择第1个话题)")
            sys.exit(1)
        topic_num = int(sys.argv[2])
        if topic_num < 1:
            print("跳过本次专栏")
            sys.exit(0)
        success = pipeline.generate(topic_num - 1)  # 用户输入从1开始

    elif mode == "auto":
        success = pipeline.auto()

    else:
        print(f"未知模式: {mode}")
        print("可用模式: discover, generate <N>, auto")
        sys.exit(1)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
