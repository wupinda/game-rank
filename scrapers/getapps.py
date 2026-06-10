"""
小米 GetApps 海外商店游戏榜单
API: global.app.mi.com/intl/web/api/category/{categoryId}
categoryId 101 = Action（热门分类）；逐页加载，page 从 1 开始，每页 ~32 条。
使用 lo=IN（印度，数据最全）、la=en。
"""
import logging
from .base import BaseScraper, RankItem

logger = logging.getLogger(__name__)

_BASE = "https://global.app.mi.com/intl/web/api/category"

# 优先抓热门大类（Action/RPG/Strategy）
_CATEGORIES = [101, 112, 115]   # Action, Role Playing, Strategy

_HEADERS = {
    "User-Agent":      ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"),
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer":         "https://global.app.mi.com/",
}

_PARAMS = {"page": 1, "lo": "IN", "la": "en"}


class GetAppsScraper(BaseScraper):
    PLATFORM = "getapps"
    SUPPORTED_RANK_TYPES = ["download"]

    def fetch(self, rank_type: str) -> list:
        seen: set[str] = set()
        items = []

        for cat_id in _CATEGORIES:
            if len(items) >= self.TOP_N:
                break
            try:
                resp = self._get(
                    f"{_BASE}/{cat_id}",
                    params=_PARAMS,
                    headers=_HEADERS,
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.warning(f"GetApps category {cat_id} 请求失败: {e}")
                continue

            for block in data.get("list") or []:
                block_data = block.get("data") or {}
                app_list = block_data.get("listApp") or []
                for app in app_list:
                    name = (app.get("displayName") or app.get("appName") or "").strip()
                    if not name or name in seen:
                        continue
                    seen.add(name)
                    items.append(RankItem(
                        rank=len(items) + 1,
                        name=name,
                        platform=self.PLATFORM,
                        rank_type=rank_type,
                        game_id=app.get("packageName") or str(app.get("id") or ""),
                        developer=app.get("developerName") or app.get("publisherName") or "",
                        icon_url=app.get("icon") or "",
                    ))
                    if len(items) >= self.TOP_N:
                        break

        if not items:
            logger.warning("GetApps 未解析到数据")
        return items
