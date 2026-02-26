# -*- coding: utf-8 -*-
"""
微信公众号发布器
调用公众号API发布到草稿箱
"""

import logging
import requests
import json
import time
from typing import Optional
from pathlib import Path

from config.settings import (
    WECHAT_APP_ID, WECHAT_APP_SECRET, WECHAT_API_BASE,
    DATA_DIR
)
from processor.time_handler import TimeHandler

logger = logging.getLogger(__name__)


class WeChatPublisher:
    """微信公众号发布器"""

    def __init__(self):
        self.app_id = WECHAT_APP_ID
        self.app_secret = WECHAT_APP_SECRET
        self.api_base = WECHAT_API_BASE
        self.access_token = None
        self.token_expires_at = 0
        self.time_handler = TimeHandler()
        self.token_cache_file = DATA_DIR / "wechat_token.json"

    def _get_access_token(self) -> Optional[str]:
        if self.access_token and time.time() < self.token_expires_at - 60:
            return self.access_token

        if self._load_token_from_cache():
            return self.access_token

        url = f"{self.api_base}/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.app_secret
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if "access_token" in data:
                self.access_token = data["access_token"]
                expires_in = data.get("expires_in", 7200)
                self.token_expires_at = time.time() + expires_in
                self._save_token_to_cache()
                logger.info("获取access_token成功")
                return self.access_token
            else:
                logger.error(f"获取access_token失败: {data}")
                return None

        except Exception as e:
            logger.error(f"请求access_token失败: {e}")
            return None

    def _load_token_from_cache(self) -> bool:
        try:
            if self.token_cache_file.exists():
                with open(self.token_cache_file, "r") as f:
                    data = json.load(f)

                if data.get("expires_at", 0) > time.time() + 60:
                    self.access_token = data["access_token"]
                    self.token_expires_at = data["expires_at"]
                    return True
        except Exception:
            pass
        return False

    def _save_token_to_cache(self):
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(self.token_cache_file, "w") as f:
                json.dump({
                    "access_token": self.access_token,
                    "expires_at": self.token_expires_at
                }, f)
        except Exception as e:
            logger.warning(f"保存token缓存失败: {e}")

    def add_draft(self, title: str, content: str, thumb_media_id: str = None) -> Optional[str]:
        access_token = self._get_access_token()
        if not access_token:
            logger.error("无法获取access_token，发布失败")
            return None

        if not thumb_media_id:
            default_cover = DATA_DIR / "default_cover.jpg"
            if default_cover.exists():
                logger.info("正在上传默认封面图片...")
                thumb_media_id = self.upload_image(str(default_cover))
                if not thumb_media_id:
                    logger.error("上传默认封面失败")
                    return None
            else:
                logger.error("未找到默认封面图片，请先创建 data/default_cover.jpg")
                return None

        url = f"{self.api_base}/draft/add"
        params = {"access_token": access_token}

        article = {
            "title": title,
            "author": "AI日报",
            "thumb_media_id": thumb_media_id,
            "digest": "",
            "content": content,
            "content_source_url": "",
            "need_open_comment": 0,
            "only_fans_can_comment": 0
        }

        data = {"articles": [article]}

        try:
            json_data = json.dumps(data, ensure_ascii=False)
            response = requests.post(
                url,
                params=params,
                data=json_data.encode('utf-8'),
                headers={"Content-Type": "application/json; charset=utf-8"},
                timeout=60
            )
            response.raise_for_status()
            result = response.json()

            if "media_id" in result:
                logger.info(f"草稿发布成功，media_id: {result['media_id']}")
                return result["media_id"]
            else:
                logger.error(f"草稿发布失败: {result}")
                return None

        except Exception as e:
            logger.error(f"发布草稿请求失败: {e}")
            return None

    def upload_image(self, image_path: str) -> Optional[str]:
        access_token = self._get_access_token()
        if not access_token:
            return None

        url = f"{self.api_base}/material/add_material"
        params = {"access_token": access_token, "type": "image"}

        try:
            with open(image_path, "rb") as f:
                files = {"media": f}
                response = requests.post(url, params=params, files=files, timeout=60)
                response.raise_for_status()
                result = response.json()

                if "media_id" in result:
                    logger.info(f"图片上传成功，media_id: {result['media_id']}")
                    return result["media_id"]
                else:
                    logger.error(f"图片上传失败: {result}")
                    return None

        except Exception as e:
            logger.error(f"上传图片失败: {e}")
            return None

    def publish_daily_report(self, html_content: str) -> bool:
        now = self.time_handler.get_now()
        title = f"AI资讯日报 {now.year}年{now.month}月{now.day}日"

        media_id = self.add_draft(title, html_content)

        if media_id:
            logger.info(f"日报已发布到草稿箱: {title}")
            self._save_publish_history(title, media_id)
            return True
        else:
            logger.error("日报发布失败")
            return False

    def _save_publish_history(self, date_str: str, media_id: str):
        history_file = DATA_DIR / "publish_history.json"

        try:
            if history_file.exists():
                with open(history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            else:
                history = {"history": []}

            history["history"].append({
                "date": date_str,
                "media_id": media_id,
                "publish_time": self.time_handler.get_now().isoformat()
            })
            history["last_publish"] = self.time_handler.get_now().isoformat()

            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.warning(f"保存发布历史失败: {e}")
