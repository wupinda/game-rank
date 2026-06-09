"""
小米游戏中心 (game.xiaomi.com) 榜单
API: game.xiaomi.com/api/getRankList
  type=5 → 下载榜
  type=6 → 新品榜
  type=7 → 热玩榜
数据位于 list[].gameInfo.displayName 等嵌套字段。
"""
import logging
from .base import BaseScraper, RankItem

logger = logging.getLogger(__name__)

_API = "https://game.xiaomi.com/api/getRankList"

_TYPE_MAP = {
    "download":    5,
    "active":      6,
    "reservation": 10,
}

_HEADERS = {
    "Referer":         "https://game.xiaomi.com/rank",
    "Accept":          "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate",
}


class XiaomiScraper(BaseScraper):
    PLATFORM = "xiaomi"
    SUPPORTED_RANK_TYPES = ["download", "active", "reservation"]

    def fetch(self, rank_type: str) -> list:
        type_id = _TYPE_MAP.get(rank_type, _TYPE_MAP["active"])
        params = {"type": type_id, "tagId": "", "page": 1}
        try:
            resp = self._get(_API, params=params, headers=_HEADERS)
            resp.raise_for_status()
            if not resp.text or not resp.text.strip():
                return []
            data     = resp.json()
            raw_list = data.get("list") or []
        except Exception as e:
            logger.warning(f"小米接口请求失败: {e}")
            return []

        items = []
        for item in raw_list[: self.TOP_N]:
            gi   = item.get("gameInfo") or {}
            det  = item.get("detail") or {}
            rank = (item.get("rank") or {}).get("current") or (len(items) + 1)
            items.append(RankItem(
                rank=rank,
                name=gi.get("displayName") or gi.get("mainName") or "",
                platform=self.PLATFORM,
                rank_type=rank_type,
                game_id=str(gi.get("gameId") or gi.get("appId") or ""),
                developer=det.get("developer_name") or det.get("developerCompanyName") or "",
                icon_url=gi.get("icon") or "",
                rating=float(item.get("userScoreV2") or 0),
            ))
        return items
