"""
WeGame 商店 (www.wegame.com.cn) 榜单

无需 Playwright，直接调用 WeGame Web API（无需登录/Cookie）。

  预约之星: POST /api/rail/web/data_filter/game_rank/query_follow_rank
            {"rank_name": "week_most_follower", ...}
  最高热度: POST /api/rail/web/data_filter/game_info/filter
            {"rank_name": "popular_this_week", ...}
"""
import logging
from .base import BaseScraper, RankItem

logger = logging.getLogger(__name__)

_BASE      = "https://www.wegame.com.cn"
_FILTER_EP = f"{_BASE}/api/rail/web/data_filter/game_info/filter"
_FOLLOW_EP = f"{_BASE}/api/rail/web/data_filter/game_rank/query_follow_rank"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer":         "https://www.wegame.com.cn/store/",
    "Origin":          "https://www.wegame.com.cn",
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

_FOLLOW_FILTERS = [
    "game_id", "game_name", "name", "logo_url", "banner_icon_url",
    "week_follow_num", "comments", "poster_url_h",
]


class WeGameScraper(BaseScraper):
    PLATFORM = "wegame"
    SUPPORTED_RANK_TYPES = ["reservation", "download"]

    def fetch(self, rank_type: str) -> list:
        if rank_type == "reservation":
            return self._fetch_follow_rank(rank_type, "week_most_follower")
        if rank_type == "download":
            return self._fetch_popular(rank_type)
        logger.warning(f"WeGame: unknown rank_type {rank_type!r}")
        return []

    def _fetch_popular(self, rank_type: str) -> list:
        body = {
            "property": [],
            "rank_name": "popular_this_week",
            "sort_by_asc": False,
            "filters": [],
            "keyword": "",
            "search_field": [],
            "tags": [],
            "stamp": {},
            "response_format": 0,
            "start_page": 0,
            "items_per_pager": self.TOP_N,
            "search_type": 0,
            "price_range": [0, 1000000],
            "not_owned_games": False,
        }
        resp = self._post(_FILTER_EP, body)
        items = resp.get("items") or []
        result = []
        for rank, item in enumerate(items[: self.TOP_N], 1):
            result.append(RankItem(
                rank=rank,
                name=item.get("game_name") or item.get("name") or "",
                platform=self.PLATFORM,
                rank_type=rank_type,
                game_id=str(item.get("game_id") or ""),
                developer=item.get("developer_name") or item.get("developer") or "",
                icon_url=item.get("logo_url") or item.get("banner_icon_url") or "",
                rating=0.0,
            ))
        return result

    def _fetch_follow_rank(self, rank_type: str, rank_name: str) -> list:
        body = {
            "rank_name": rank_name,
            "filters": _FOLLOW_FILTERS,
            "num": self.TOP_N,
            "pos": 0,
            "list_type": 4,
            "only_unpublished": 1,
            "stamp": {"agent_client_language": ""},
        }
        resp = self._post(_FOLLOW_EP, body)
        err = (resp.get("result") or {}).get("error_code", 0)
        if err:
            raise RuntimeError(f"WeGame API error {err}")
        items = resp.get("items") or []
        result = []
        for rank, item in enumerate(items[: self.TOP_N], 1):
            result.append(RankItem(
                rank=rank,
                name=item.get("game_name") or item.get("name") or "",
                platform=self.PLATFORM,
                rank_type=rank_type,
                game_id=str(item.get("game_id") or ""),
                developer="",
                icon_url=item.get("logo_url") or item.get("banner_icon_url") or "",
                rating=0.0,
            ))
        return result

    def _post(self, url: str, body: dict) -> dict:
        resp = self.session.post(
            url, json=body, headers=_HEADERS, timeout=self.timeout
        )
        resp.raise_for_status()
        return resp.json()
