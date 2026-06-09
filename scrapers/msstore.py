"""
Microsoft Store 游戏排行榜
下载榜：apps.microsoft.com/collections/computed/games/TopFree
畅销榜：apps.microsoft.com/collections/computed/games/TopGrossing
数据来源：apps.microsoft.com Reco API（gl=SG, hl=zh-CN）
"""
import logging
from .base import BaseScraper, RankItem

logger = logging.getLogger(__name__)

_RECO_URL = "https://apps.microsoft.com/api/Reco/GetComputedProductsList"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://apps.microsoft.com/",
}

_LIST_MAP = {
    "download": "topFree",
    "revenue":  "topGrossing",
}


class MsStoreScraper(BaseScraper):
    PLATFORM = "msstore"
    SUPPORTED_RANK_TYPES = ["download", "revenue"]
    _GL = "SG"

    def fetch(self, rank_type: str) -> list:
        list_name = _LIST_MAP.get(rank_type)
        if not list_name:
            return []
        try:
            resp = self._get(_RECO_URL, headers=_HEADERS, params={
                "listName":           list_name,
                "pgNo":               1,
                "noItems":            self.TOP_N + 5,
                "filteredCategories": "all",
                "mediaType":          "games",
                "gl":                 self._GL,
                "hl":                 "zh-CN",
                "exp":                0,
            })
            resp.raise_for_status()
            products = resp.json().get("productsList", [])
        except Exception as e:
            logger.error(f"Microsoft Store [{self._GL}] {rank_type} 失败: {e}")
            return []

        results = []
        for i, p in enumerate(products[:self.TOP_N]):
            results.append(RankItem(
                rank=i + 1,
                name=p.get("title", ""),
                platform=self.PLATFORM,
                rank_type=rank_type,
                game_id=p.get("productId", ""),
                developer=p.get("publisherName", ""),
                icon_url=p.get("iconUrl", "") or p.get("posterArtUrl", ""),
                rating=float(p.get("averageRating") or 0),
            ))
        return results
