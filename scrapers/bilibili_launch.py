"""
B站开测榜 — le3-api.game.bilibili.com
GET /pc/game/ranking/page_start_test_list?page_num=1&page_size=50&x-fix-page-num=1
-> data[] with game_name_v2, start_test_time(ms), start_test_type, developer_name
"""
import logging
from datetime import datetime
from .base import BaseLaunchScraper, LaunchItem

logger = logging.getLogger(__name__)

_URL = "https://le3-api.game.bilibili.com/pc/game/ranking/page_start_test_list"
_HEADERS = {
    "Referer": "https://game.bilibili.com/platform/ranks/testing",
    "Origin":  "https://game.bilibili.com",
}


class BilibiliLaunchScraper(BaseLaunchScraper):
    PLATFORM = "bilibili"

    def fetch_launches(self) -> list:
        params = {"page_num": 1, "page_size": 50, "x-fix-page-num": 1}
        resp = self._get(_URL, headers=_HEADERS, params=params)
        resp.raise_for_status()
        items = resp.json().get("data") or []
        results = []
        for it in items:
            ts = int(it.get("start_test_time") or 0)
            if ts:
                launch_time = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M")
            else:
                launch_time = ""
            icon = it.get("icon") or ""
            if icon.startswith("//"):
                icon = "https:" + icon
            results.append(LaunchItem(
                platform=self.PLATFORM,
                game_name=it.get("game_name_v2") or it.get("game_name") or "",
                launch_time=launch_time,
                launch_type=it.get("start_test_type") or "",
                developer=it.get("developer_name") or it.get("establisher_name") or "",
                game_id=str(it.get("game_base_id") or ""),
                icon_url=icon,
            ))
        return results
