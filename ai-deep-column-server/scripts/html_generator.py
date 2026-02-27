"""微信公众号适配 HTML 生成器

将 Markdown 格式的专栏文章转换为微信公众号兼容的内联样式 HTML。
"""
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import pytz

from config.settings import OUTPUT_DIR

logger = logging.getLogger(__name__)
BJT = pytz.timezone("Asia/Shanghai")


class HTMLGenerator:
    """专栏文章 HTML 生成器"""

    def generate(self, title: str, body_markdown: str, topic_info: dict = None) -> str:
        """
        将标题+Markdown正文转为微信公众号HTML。
        topic_info: {"article_count": N, "source_count": M}
        """
        body_html = self._markdown_to_html(body_markdown)
        now = datetime.now(BJT)
        date_str = now.strftime("%Y年%m月%d日")

        # 报道统计
        stats = ""
        if topic_info:
            stats = f'<p style="font-size:12px;color:#999;margin:0 0 15px 0;">📊 综合 {topic_info.get("source_count", 0)} 个来源 {topic_info.get("article_count", 0)} 篇报道</p>'

        html = f'''<div style="max-width:100%;margin:0 auto;padding:15px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;color:#333;line-height:1.8;font-size:15px;">

  <!-- 头部 -->
  <div style="text-align:center;margin-bottom:25px;">
    <h1 style="font-size:22px;font-weight:bold;color:#1a1a1a;margin:0 0 10px 0;line-height:1.4;">{title}</h1>
    <p style="font-size:12px;color:#999;margin:0;">AI深度专栏 | {date_str}</p>
    {stats}
  </div>

  <!-- 分隔线 -->
  <div style="border-top:2px solid #7a4fd6;margin:0 0 20px 0;"></div>

  <!-- 正文 -->
  <div style="font-size:15px;color:#333;line-height:1.9;">
    {body_html}
  </div>

  <!-- 尾部 -->
  <div style="border-top:1px solid #eee;margin-top:30px;padding-top:15px;text-align:center;">
    <p style="font-size:12px;color:#999;margin:0;">本文由 AI 基于多源新闻素材自动生成，仅供参考</p>
    <p style="font-size:12px;color:#999;margin:5px 0 0 0;">AI深度专栏 · 每日热点深度解读</p>
  </div>

</div>'''

        # 保存到文件
        self._save(title, html, now)
        return html

    def _markdown_to_html(self, md: str) -> str:
        """将 Markdown 转为内联样式 HTML"""
        lines = md.split("\n")
        html_parts = []
        in_list = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if in_list:
                    html_parts.append("</ul>")
                    in_list = False
                html_parts.append("")
                continue

            # ## 二级标题
            if stripped.startswith("## "):
                if in_list:
                    html_parts.append("</ul>")
                    in_list = False
                text = stripped[3:].strip()
                html_parts.append(
                    f'<h2 style="font-size:18px;font-weight:bold;color:#7a4fd6;'
                    f'margin:25px 0 12px 0;padding-left:10px;'
                    f'border-left:3px solid #7a4fd6;">{text}</h2>'
                )
                continue

            # ### 三级标题
            if stripped.startswith("### "):
                if in_list:
                    html_parts.append("</ul>")
                    in_list = False
                text = stripped[4:].strip()
                html_parts.append(
                    f'<h3 style="font-size:16px;font-weight:bold;color:#444;'
                    f'margin:20px 0 8px 0;">{text}</h3>'
                )
                continue

            # 列表项
            if stripped.startswith("- ") or stripped.startswith("* "):
                if not in_list:
                    html_parts.append('<ul style="padding-left:20px;margin:8px 0;">')
                    in_list = True
                text = self._inline_format(stripped[2:])
                html_parts.append(
                    f'<li style="margin:5px 0;color:#333;">{text}</li>'
                )
                continue

            # 有序列表
            m = re.match(r'^(\d+)\.\s+(.+)', stripped)
            if m:
                if not in_list:
                    html_parts.append('<ul style="padding-left:20px;margin:8px 0;list-style-type:decimal;">')
                    in_list = True
                text = self._inline_format(m.group(2))
                html_parts.append(
                    f'<li style="margin:5px 0;color:#333;">{text}</li>'
                )
                continue

            # 引用
            if stripped.startswith("> "):
                if in_list:
                    html_parts.append("</ul>")
                    in_list = False
                text = self._inline_format(stripped[2:])
                html_parts.append(
                    f'<blockquote style="border-left:3px solid #ddd;padding:8px 15px;'
                    f'margin:10px 0;color:#666;background:#f9f9f9;font-size:14px;">'
                    f'{text}</blockquote>'
                )
                continue

            # 普通段落
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            text = self._inline_format(stripped)
            html_parts.append(f'<p style="margin:10px 0;text-indent:0;">{text}</p>')

        if in_list:
            html_parts.append("</ul>")

        return "\n".join(html_parts)

    @staticmethod
    def _inline_format(text: str) -> str:
        """处理行内格式：粗体、斜体、行内代码"""
        # **粗体**
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color:#1a1a1a;">\1</strong>', text)
        # *斜体*
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        # `代码`
        text = re.sub(
            r'`(.+?)`',
            r'<code style="background:#f5f5f5;padding:2px 5px;border-radius:3px;font-size:13px;color:#c7254e;">\1</code>',
            text
        )
        return text

    def _save(self, title: str, html: str, now: datetime):
        """保存 HTML 到 output 目录"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        safe_title = re.sub(r'[^\w\u4e00-\u9fff]', '_', title)[:30]
        filename = f"{safe_title}_{now.strftime('%Y%m%d')}.html"
        filepath = OUTPUT_DIR / filename
        filepath.write_text(html, encoding="utf-8")
        logger.info(f"HTML 已保存: {filepath}")
