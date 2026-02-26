"""企业微信通知器

将候选话题推送到企微群，等待选择。
"""
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

import requests
import pytz

from config.settings import WECOM_WEBHOOK_URL, DATA_DIR
from config.prompts import WECOM_CANDIDATE_TEMPLATE

logger = logging.getLogger(__name__)
BJT = pytz.timezone("Asia/Shanghai")


class WeComNotifier:
    """企微候选话题推送"""

    def send_candidates(self, candidates: List[Dict]) -> bool:
        """推送候选话题列表到企微"""
        if not WECOM_WEBHOOK_URL:
            logger.warning("未配置 WECOM_WEBHOOK_URL，跳过企微推送")
            # 改为打印到控制台
            self._print_candidates(candidates)
            return True

        now = datetime.now(BJT)
        date_str = f"{now.month}月{now.day}日"

        topics_text = self._format_topics(candidates)
        content = WECOM_CANDIDATE_TEMPLATE.format(
            date=date_str,
            topics_text=topics_text,
        )

        return self._send_markdown(content)

    def _format_topics(self, candidates: List[Dict]) -> str:
        """格式化候选话题列表"""
        lines = []
        for c in candidates:
            tid = c["topic_id"] + 1  # 从1开始展示
            title = c["title"][:50]
            count = c["article_count"]
            sources = c["source_count"]
            sample = c["sample_titles"][0] if c["sample_titles"] else ""
            if len(sample) > 40:
                sample = sample[:40] + "..."

            lines.append(
                f"**{tid}. {title}**\n"
                f"   > {count}篇报道 · {sources}个来源\n"
                f"   > 样例: {sample}"
            )
        return "\n\n".join(lines)

    def _send_markdown(self, content: str) -> bool:
        """发送 markdown 消息到企微"""
        try:
            resp = requests.post(
                WECOM_WEBHOOK_URL,
                json={"msgtype": "markdown", "markdown": {"content": content}},
                timeout=10,
            )
            data = resp.json()
            if data.get("errcode") == 0:
                logger.info("候选话题已推送到企微")
                return True
            else:
                logger.error(f"企微推送失败: {data}")
                return False
        except Exception as e:
            logger.error(f"企微推送异常: {e}")
            return False

    def _print_candidates(self, candidates: List[Dict]):
        """终端打印候选话题（无企微时使用）"""
        now = datetime.now(BJT)
        print(f"\n{'='*60}")
        print(f"📊 AI专栏候选话题 ({now.month}月{now.day}日)")
        print(f"{'='*60}")
        for c in candidates:
            tid = c["topic_id"] + 1
            title = c["title"]
            count = c["article_count"]
            sources = c["source_count"]
            print(f"\n  {tid}. 【{title}】")
            print(f"     📰 {count}篇报道 · {sources}个来源")
            if c["sample_titles"]:
                for st in c["sample_titles"][:3]:
                    print(f"     - {st[:60]}")
        print(f"\n{'='*60}")
        print("输入话题编号选择（如 1），输入 0 跳过")


def save_candidates(candidates: List[Dict]):
    """保存候选话题到文件，供后续选择使用"""
    filepath = DATA_DIR / "candidates.json"
    filepath.write_text(json.dumps(candidates, ensure_ascii=False, indent=2))
    logger.info(f"候选话题已保存: {filepath}")


def load_candidates() -> List[Dict]:
    """加载候选话题"""
    filepath = DATA_DIR / "candidates.json"
    if filepath.exists():
        return json.loads(filepath.read_text())
    return []
