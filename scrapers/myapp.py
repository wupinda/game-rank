"""
应用宝 (sj.qq.com) 预约榜
页面使用 Next.js SSR，游戏数据内嵌在 __NEXT_DATA__ 中，无需 Playwright。

端点：GET https://sj.qq.com/reserve-game-list
数据路径：props.pageProps.dynamicCardResponse.data.components[0].data.itemData
"""
import re
import json
import logging
from .base import BaseScraper, RankItem

logger = logging.getLogger(__name__)

_URL = "https://sj.qq.com/reserve-game-list?sort_type=hot"

_HEADERS = {
    "Referer":         "https://sj.qq.com/",
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

_NEXT_DATA_RE = re.compile(
    r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL
)


class MyAppScraper(BaseScraper):
    PLATFORM = "myapp"
    SUPPORTED_RANK_TYPES = ["reservation"]

    def fetch(self, rank_type: str) -> list:
        resp = self._get(_URL, headers=_HEADERS)
        resp.raise_for_status()

        m = _NEXT_DATA_RE.search(resp.text)
        if not m:
            logger.warning("myapp: __NEXT_DATA__ not found")
            return []

        nd = json.loads(m.group(1))
        try:
            components = (
                nd["props"]["pageProps"]
                ["dynamicCardResponse"]["data"]["components"]
            )
            raw = components[0]["data"]["itemData"]
        except (KeyError, IndexError) as e:
            logger.warning(f"myapp: unexpected data structure: {e}")
            return []

        items = []
        for rank, it in enumerate(raw[: self.TOP_N], 1):
            items.append(RankItem(
                rank=rank,
                name=it.get("name") or "",
                platform=self.PLATFORM,
                rank_type=rank_type,
                game_id=str(it.get("app_id") or it.get("pkg_name") or ""),
                developer=it.get("developer") or it.get("operator") or "",
                icon_url=it.get("icon") or "",
                rating=float(it.get("average_rating") or 0),
            ))
        return items
