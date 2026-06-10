"""
三星 Galaxy Store 游戏榜单
API: samsungapps.com/appquery/getPopularApps.as
categoryId G000005679 = Games
"""
import logging
from .base import BaseScraper, RankItem

logger = logging.getLogger(__name__)

_API = "https://samsungapps.com/appquery/getPopularApps.as"

_HEADERS = {
    "Referer":         "https://galaxystore.samsung.com/",
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}


class GalaxyStoreScraper(BaseScraper):
    PLATFORM = "galaxystore"
    SUPPORTED_RANK_TYPES = ["download"]

    def fetch(self, rank_type: str) -> list:
        if rank_type != "download":
            return []

        params = {
            "pageIndex":   0,
            "pageSize":    self.TOP_N,
            "categoryId":  "G000005679",
            "serviceType": "PHONE",
        }

        try:
            resp = self._get(_API, params=params, headers=_HEADERS)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning(f"Galaxy Store 接口请求失败: {e}")
            return []

        app_list = data.get("appList") or data.get("list") or []
        items = []
        for i, entry in enumerate(app_list[: self.TOP_N]):
            name = (entry.get("contentName") or entry.get("appName") or "").strip()
            if not name:
                continue
            items.append(RankItem(
                rank=i + 1,
                name=name,
                platform=self.PLATFORM,
                rank_type=rank_type,
                game_id=entry.get("contentId") or entry.get("appId") or "",
                developer=entry.get("sellerName") or entry.get("developerName") or "",
                icon_url=entry.get("thumbnailUrl") or entry.get("iconUrl") or "",
                rating=float(entry.get("averageRating") or 0),
            ))
        return items
