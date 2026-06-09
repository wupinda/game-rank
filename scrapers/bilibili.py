"""
B站游戏 (game.bilibili.com) 榜单
常规榜单 API: le3-api.game.bilibili.com/pc/game/ranking/page_ranking_list
  ranking_type=1 → hot_list (活跃/热门)
  ranking_type=2 → good_commend_list (好评/畅销)
  ranking_type=5 → order_list (预约榜)
"""
from .base import BaseScraper, RankItem

_API_RANKING = "https://le3-api.game.bilibili.com/pc/game/ranking/page_ranking_list"

_TYPE_CONFIG = {
    "active":      (1, "hot_list"),
    "revenue":     (2, "good_commend_list"),
    "reservation": (5, "order_list"),
}

_HEADERS = {
    "Referer": "https://game.bilibili.com/",
    "Origin":  "https://game.bilibili.com",
}


class BilibiliScraper(BaseScraper):
    PLATFORM = "bilibili"
    SUPPORTED_RANK_TYPES = ["active", "reservation"]

    def fetch(self, rank_type: str) -> list:
        rtype, data_key = _TYPE_CONFIG.get(rank_type, (1, "hot_list"))
        params   = {"ranking_type": rtype, "page_num": 1, "page_size": self.TOP_N}
        resp     = self._get(_API_RANKING, params=params, headers=_HEADERS)
        resp.raise_for_status()
        raw_list = resp.json().get("data", {}).get(data_key) or []
        return [self._parse(i + 1, g, rank_type) for i, g in enumerate(raw_list)]

    @staticmethod
    def _parse(rank: int, g: dict, rank_type: str) -> RankItem:
        return RankItem(
            rank=rank,
            name=g.get("title") or g.get("game_name") or "",
            platform="bilibili",
            rank_type=rank_type,
            game_id=str(g.get("game_id") or g.get("id") or ""),
            developer=g.get("developer") or "",
            icon_url=g.get("game_icon") or g.get("icon") or "",
        )
