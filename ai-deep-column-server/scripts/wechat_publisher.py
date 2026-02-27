"""微信公众号发布器

精简版——只负责上传封面、创建草稿，复用日报的 token 管理逻辑。
"""
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
import pytz

from config.settings import (
    WECHAT_APP_ID, WECHAT_APP_SECRET, WECHAT_API_BASE,
    DATA_DIR, DEFAULT_COVER,
)

logger = logging.getLogger(__name__)
BJT = pytz.timezone("Asia/Shanghai")


class WeChatPublisher:
    """微信公众号草稿发布"""

    def __init__(self):
        self._access_token: Optional[str] = None
        self._token_expires: float = 0
        self._token_file = DATA_DIR / "wechat_token.json"

    def publish_column(self, title: str, html_content: str) -> bool:
        """发布专栏文章到草稿箱"""
        token = self._get_access_token()
        if not token:
            logger.error("获取 access_token 失败")
            return False

        # 上传封面
        thumb_media_id = self._upload_cover(token)
        if not thumb_media_id:
            logger.error("上传封面失败")
            return False

        # 创建草稿
        media_id = self._add_draft(token, title, html_content, thumb_media_id)
        if not media_id:
            logger.error("创建草稿失败")
            return False

        # 记录发布历史
        self._save_history(title, media_id)
        logger.info(f"✅ 专栏已发布到草稿箱: {title} (media_id={media_id})")
        return True

    def _get_access_token(self) -> Optional[str]:
        """三级缓存获取 access_token"""
        now = time.time()

        # 内存缓存
        if self._access_token and now < self._token_expires - 60:
            return self._access_token

        # 文件缓存
        if self._token_file.exists():
            try:
                data = json.loads(self._token_file.read_text())
                if data.get("expires_at", 0) > now + 60:
                    self._access_token = data["access_token"]
                    self._token_expires = data["expires_at"]
                    return self._access_token
            except Exception:
                pass

        # API 请求
        try:
            url = f"{WECHAT_API_BASE}/token"
            params = {
                "grant_type": "client_credential",
                "appid": WECHAT_APP_ID,
                "secret": WECHAT_APP_SECRET,
            }
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()

            if "access_token" in data:
                self._access_token = data["access_token"]
                self._token_expires = now + data.get("expires_in", 7200)
                # 写入文件缓存
                self._token_file.write_text(json.dumps({
                    "access_token": self._access_token,
                    "expires_at": self._token_expires,
                }))
                return self._access_token
            else:
                logger.error(f"获取 token 失败: {data}")
        except Exception as e:
            logger.error(f"请求 token 异常: {e}")
        return None

    def _upload_cover(self, token: str) -> Optional[str]:
        """上传封面图"""
        cover_path = DEFAULT_COVER
        if not cover_path.exists():
            logger.error(f"封面文件不存在: {cover_path}")
            return None

        url = f"{WECHAT_API_BASE}/material/add_material?access_token={token}&type=image"
        try:
            with open(cover_path, "rb") as f:
                files = {"media": (cover_path.name, f, "image/jpeg")}
                resp = requests.post(url, files=files, timeout=30)
            data = resp.json()
            if "media_id" in data:
                logger.info(f"封面上传成功: {data['media_id']}")
                return data["media_id"]
            else:
                logger.error(f"封面上传失败: {data}")
        except Exception as e:
            logger.error(f"封面上传异常: {e}")
        return None

    def _add_draft(self, token: str, title: str, content: str,
                   thumb_media_id: str) -> Optional[str]:
        """创建草稿"""
        url = f"{WECHAT_API_BASE}/draft/add?access_token={token}"
        body = {
            "articles": [{
                "title": title,
                "author": "AI深度专栏",
                "content": content,
                "thumb_media_id": thumb_media_id,
                "need_open_comment": 1,
                "only_fans_can_comment": 0,
            }]
        }
        try:
            resp = requests.post(
                url,
                data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json; charset=utf-8"},
                timeout=30,
            )
            data = resp.json()
            if "media_id" in data:
                return data["media_id"]
            else:
                logger.error(f"创建草稿失败: {data}")
        except Exception as e:
            logger.error(f"创建草稿异常: {e}")
        return None

    def _save_history(self, title: str, media_id: str):
        """追加发布历史"""
        history_file = DATA_DIR / "publish_history.json"
        history = []
        if history_file.exists():
            try:
                history = json.loads(history_file.read_text())
            except Exception:
                pass

        now = datetime.now(BJT)
        history.append({
            "title": title,
            "media_id": media_id,
            "published_at": now.isoformat(),
            "type": "column",
        })
        history_file.write_text(json.dumps(history, ensure_ascii=False, indent=2))
