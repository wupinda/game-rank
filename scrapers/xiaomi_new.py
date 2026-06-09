"""
小米游戏 预约榜 — game.xiaomi.com/api/getRankList?type=10
预约榜收录尚未上线的游戏，gameOpeningTime 通常为 0（未公布具体时间）。
"""
import logging
from datetime import datetime
from .base import BaseLaunchScraper, LaunchItem

logger = logging.getLogger(__name__)

_URL = "https://game.xiaomi.com/api/getRankList"
_HEADERS = {
    "Referer": "https://game.xiaomi.com/rank",
    "Accept":  "application/json",
}


class XiaomiNewScraper(BaseLaunchScraper):
    PLATFORM = "xiaomi"

    def fetch_launches(self) -> list:
        params = {"type": 10, "tagId": "", "page": 1}
        resp   = self._get(_URL, headers=_HEADERS, params=params)
        resp.raise_for_status()
        items  = resp.json().get("list") or []
        results = []
        for it in items[:self.TOP_N]:
            gi = it.get("gameInfo") or {}
            d  = it.get("detail") or {}
            ts = d.get("gameOpeningTime") or 0
            launch_time = (
                datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M")
                if ts else ""
            )
            results.append(LaunchItem(
                platform=self.PLATFORM,
                game_name=gi.get("displayName") or it.get("displayName") or "",
                launch_time=launch_time,
                launch_type="预约",
                developer=d.get("developerCompanyName") or d.get("developer_name") or "",
                game_id=str(gi.get("appId") or ""),
                icon_url=gi.get("gameIcon") or "",
            ))
        return results
