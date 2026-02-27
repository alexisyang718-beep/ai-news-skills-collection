# -*- coding: utf-8 -*-
"""时间处理器"""

import logging
from datetime import datetime, timedelta
from typing import Optional
import pytz
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


class TimeHandler:
    """时间处理器"""

    def __init__(self, timezone: str = "Asia/Shanghai"):
        self.tz = pytz.timezone(timezone)
        self.utc = pytz.UTC

    def get_now(self) -> datetime:
        return datetime.now(self.tz)

    def get_24h_range(self) -> tuple:
        """过去28小时到现在（多留4小时缓冲）"""
        now = self.get_now()
        return now - timedelta(hours=28), now

    def convert_to_beijing(self, dt: datetime) -> datetime:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = self.utc.localize(dt)
        return dt.astimezone(self.tz)

    def parse_time(self, time_str: str) -> Optional[datetime]:
        if not time_str:
            return None
        try:
            dt = date_parser.parse(time_str)
            return self.convert_to_beijing(dt)
        except Exception:
            return None

    def get_report_date(self) -> str:
        now = self.get_now()
        return f"{now.month}月{now.day}日"

    def format_time(self, dt: datetime, fmt: str = "%Y-%m-%d %H:%M") -> str:
        if dt is None:
            return ""
        return self.convert_to_beijing(dt).strftime(fmt)
