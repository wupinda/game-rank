"""
Apple App Store 榜单
使用 iTunes RSS v1 接口（稳定，支持按游戏分类过滤）
Genre 6014 = Games
支持：下载榜（top-free）、畅销榜（top-grossing）
子类可覆盖 COUNTRY / PLATFORM 以抓取其他区域
"""
from .base import BaseScraper, RankItem

_BASE = "https://itunes.apple.com/{country}/rss/{feed}/limit={n}/genre=6014/json"

_FEED_MAP = {
    "download": "topfreeapplications",
    "revenue":  "topgrossingapplications",
}


class AppStoreScraper(BaseScraper):
    PLATFORM = "appstore"
    COUNTRY  = "cn"
    SUPPORTED_RANK_TYPES = ["download", "revenue"]  # App Store 无预约榜

    def fetch(self, rank_type: str) -> list:
        feed = _FEED_MAP.get(rank_type)
        if not feed:
            return []

        url  = _BASE.format(country=self.COUNTRY, feed=feed, n=self.TOP_N)
        resp = self._get(url, headers={"Referer": "https://apps.apple.com/"})
        resp.raise_for_status()

        entries = resp.json().get("feed", {}).get("entry", [])
        results = []
        for i, entry in enumerate(entries):
            name      = entry.get("im:name",   {}).get("label", "")
            developer = entry.get("im:artist", {}).get("label", "")
            app_id    = entry.get("id", {}).get("attributes", {}).get("im:id", "")
            # 取最大分辨率图标（最后一项）
            images    = entry.get("im:image", [])
            icon_url  = images[-1].get("label", "") if images else ""
            rating_raw = entry.get("im:averageUserRating", {})
            rating    = float(rating_raw.get("label", 0) or 0) if isinstance(rating_raw, dict) else 0.0

            results.append(RankItem(
                rank=i + 1,
                name=name,
                platform=self.PLATFORM,
                rank_type=rank_type,
                game_id=app_id,
                developer=developer,
                icon_url=icon_url,
                rating=rating,
            ))
        return results
