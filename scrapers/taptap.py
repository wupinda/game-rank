"""
TapTap China (www.taptap.cn) 榜单
通过 Web API 直接获取，无需 Playwright。

端点：GET /webapiv2/app-top/v2/hits?from=N&limit=10&type_name=TYPE&X-UA=...
  type_name=pop     → 活跃榜 (/top/played)
  type_name=hot     → 下载榜 (/top/download)
  type_name=reserve → 预约榜 (/top/reserve)

每次最多 limit=10，分两次请求 (from=0, from=10) 合计 TOP20。
"""
from .base import BaseScraper, RankItem

_API = "https://www.taptap.cn/webapiv2/app-top/v2/hits"

_TYPE_NAMES = {
    "active":      "pop",
    "download":    "hot",
    "reservation": "reserve",
}

_XUA = (
    "V=1&PN=WebApp&LANG=zh_CN&VN_CODE=102&LOC=CN"
    "&PLT=PC&DS=Android&OS=Windows&OSV=10&DT=PC"
)

_HEADERS = {
    "Referer":         "https://www.taptap.cn/",
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


class TapTapScraper(BaseScraper):
    PLATFORM = "taptap"
    SUPPORTED_RANK_TYPES = ["active", "download", "reservation"]

    def fetch(self, rank_type: str) -> list:
        type_name = _TYPE_NAMES.get(rank_type, "pop")
        items = []
        seen_ids: set = set()

        # Two pages: from=0 and from=10 (limit max = 10)
        for start in range(0, max(self.TOP_N, 10), 10):
            if len(items) >= self.TOP_N:
                break
            params = {"from": start, "limit": 10, "type_name": type_name, "X-UA": _XUA}
            resp = self._get(_API, params=params, headers=_HEADERS)
            resp.raise_for_status()
            raw = resp.json().get("data", {}).get("list") or []
            if not raw:
                break
            for entry in raw:
                if len(items) >= self.TOP_N:
                    break
                app = entry.get("app") or {}
                gid = str(app.get("id") or "")
                if gid in seen_ids:
                    continue
                seen_ids.add(gid)
                items.append(RankItem(
                    rank=len(items) + 1,
                    name=app.get("title") or app.get("name") or "",
                    platform=self.PLATFORM,
                    rank_type=rank_type,
                    game_id=gid,
                    developer=(
                        (app.get("developer") or {}).get("name", "")
                        if isinstance(app.get("developer"), dict)
                        else ""
                    ),
                    icon_url=(
                        (app.get("icon") or {}).get("url", "")
                        if isinstance(app.get("icon"), dict)
                        else ""
                    ),
                    rating=float(
                        (app.get("rating") or {}).get("score", 0) or 0
                        if isinstance(app.get("rating"), dict)
                        else 0
                    ),
                ))

        return items
