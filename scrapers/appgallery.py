"""
华为 AppGallery 游戏榜单
API: web-drcn.hispace.dbankcloud.com/uowap/index
tabCodesStr: GGameRank_2_1_0 (下载榜), GGameRank_2_2_0 (畅销榜)
"""
import logging
from .base import BaseScraper, RankItem

logger = logging.getLogger(__name__)

_API = "https://web-drcn.hispace.dbankcloud.com/uowap/index"

_TAB_MAP = {
    "download": "GGameRank_2_1_0",
    "revenue":  "GGameRank_2_2_0",
}

_HEADERS = {
    "Referer": "https://appgallery.huawei.com/",
    "Accept":  "application/json, text/plain, */*",
}


class AppGalleryScraper(BaseScraper):
    PLATFORM = "appgallery"
    SUPPORTED_RANK_TYPES = ["download", "revenue"]

    def fetch(self, rank_type: str) -> list:
        tab = _TAB_MAP.get(rank_type)
        if not tab:
            return []

        params = {
            "method":      "internal.getTabDetail",
            "serviceType": "0",
            "reqPageNum":  "1",
            "uri":         "owap",
            "tabCodesStr": tab,
        }

        try:
            resp = self._get(_API, params=params, headers=_HEADERS)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning(f"AppGallery 接口请求失败: {e}")
            return []

        # 展开所有 block 中的 dataList
        entries = []
        for block in (data.get("layoutData") or []):
            entries.extend(block.get("dataList") or [])

        items = []
        for i, entry in enumerate(entries[: self.TOP_N]):
            name = (entry.get("name") or entry.get("appName") or "").strip()
            if not name:
                continue
            items.append(RankItem(
                rank=i + 1,
                name=name,
                platform=self.PLATFORM,
                rank_type=rank_type,
                game_id=entry.get("appid") or entry.get("packageName") or "",
                developer=entry.get("developer") or entry.get("developerId") or "",
                icon_url=entry.get("icon") or entry.get("iconUri") or "",
                rating=float(entry.get("averageRating") or entry.get("starRating") or 0),
            ))
        return items
