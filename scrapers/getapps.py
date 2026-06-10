"""
小米 GetApps 海外商店游戏榜单
API: global.intl.miui.com/channel/categorylist.do
categoryId 2 = Games；type 5 = 热门下载，type 7 = 热玩
接口结构与国内小米相似，复用同类字段解析逻辑。
"""
import logging
from .base import BaseScraper, RankItem

logger = logging.getLogger(__name__)

_API = "https://global.intl.miui.com/channel/categorylist.do"

_TYPE_MAP = {
    "download": 5,
    "active":   7,
}

_HEADERS = {
    "Referer":         "https://global.intl.miui.com/",
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}


class GetAppsScraper(BaseScraper):
    PLATFORM = "getapps"
    SUPPORTED_RANK_TYPES = ["download", "active"]

    def fetch(self, rank_type: str) -> list:
        type_id = _TYPE_MAP.get(rank_type, _TYPE_MAP["download"])

        params = {
            "categoryId": 2,
            "pageIndex":  1,
            "pageSize":   self.TOP_N,
            "type":       type_id,
        }

        try:
            resp = self._get(_API, params=params, headers=_HEADERS)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning(f"GetApps 接口请求失败: {e}")
            return []

        raw_list = data.get("list") or []
        items = []
        for item in raw_list[: self.TOP_N]:
            gi   = item.get("gameInfo") or item
            name = (gi.get("displayName") or gi.get("appName") or gi.get("name") or "").strip()
            if not name:
                continue
            items.append(RankItem(
                rank=len(items) + 1,
                name=name,
                platform=self.PLATFORM,
                rank_type=rank_type,
                game_id=str(gi.get("appId") or gi.get("gameId") or ""),
                developer=gi.get("developerName") or gi.get("developer") or "",
                icon_url=gi.get("icon") or gi.get("iconUrl") or "",
                rating=float(gi.get("userScore") or gi.get("rating") or 0),
            ))
        return items
