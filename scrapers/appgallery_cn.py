"""
华为 AppGallery 游戏榜单（国内 CN 区）
两步鉴权：先 POST getInterfaceCode 获取 JWT，再带 Interface-Code header 查排行。
base: web-drcn.hispace.dbankcloud.com/edge  (中国北区)
tabUri: 游戏排行固定 ID，可通过 internal.getTemplate 动态发现。
"""
import time
import logging
from .base import BaseScraper, RankItem

logger = logging.getLogger(__name__)

_UA        = ("Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36")
_EDGE_BASE = "https://web-drcn.hispace.dbankcloud.com/edge"
_TOKEN_URL = f"{_EDGE_BASE}/webedge/getInterfaceCode"
_DATA_URL  = f"{_EDGE_BASE}/uowap/index"

# 游戏排行 tabId（通过 internal.getTemplate 发现的固定值）
_GAME_RANK_URI = "fb4b62896f47464fb0053045368b2ac4"  # 畅销榜

_TOKEN_HEADERS = {
    "User-Agent":    _UA,
    "Content-Type":  "application/json",
    "Accept":        "application/json, text/plain, */*",
    "Referer":       "https://appgallery.huawei.com/",
    "Origin":        "https://appgallery.huawei.com",
}


class AppGalleryCNScraper(BaseScraper):
    PLATFORM = "appgallery_cn"
    SUPPORTED_RANK_TYPES = ["revenue"]

    def _get_token(self) -> str:
        try:
            resp = self.session.post(
                _TOKEN_URL,
                json={},
                headers=_TOKEN_HEADERS,
                timeout=10,
            )
            resp.raise_for_status()
            # Response is a quoted JWT string, e.g. '"eyJ..."'
            token = resp.text.strip().strip('"')
            return token
        except Exception as e:
            logger.warning(f"AppGallery CN 获取 token 失败: {e}")
            return ""

    def fetch(self, rank_type: str) -> list:
        token = self._get_token()
        if not token:
            return []

        ts_ms = int(time.time() * 1000)
        interface_code = f"{token}_{ts_ms}"

        headers_data = {
            "User-Agent":     _UA,
            "Accept":         "application/json, text/plain, */*",
            "Referer":        "https://appgallery.huawei.com/",
            "Interface-Code": interface_code,
        }

        all_items: list[RankItem] = []
        page = 1
        max_pages = (self.TOP_N // 25) + 2

        while len(all_items) < self.TOP_N and page <= max_pages:
            params = {
                "method":      "internal.getTabDetail",
                "serviceType": "20",
                "reqPageNum":  str(page),
                "uri":         _GAME_RANK_URI,
                "maxResults":  "25",
            }
            try:
                resp = self._get(_DATA_URL, params=params, headers=headers_data)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.warning(f"AppGallery CN 数据请求失败 (page {page}): {e}")
                break

            if data.get("rtnCode") != 0:
                logger.warning(f"AppGallery CN rtnCode={data.get('rtnCode')}: {data.get('rtnDesc', '')}")
                break

            entries = []
            for layout in data.get("layoutData") or []:
                entries.extend(layout.get("dataList") or [])

            if not entries:
                break

            for entry in entries:
                name = (entry.get("name") or "").strip()
                if not name:
                    continue
                all_items.append(RankItem(
                    rank=len(all_items) + 1,
                    name=name,
                    platform=self.PLATFORM,
                    rank_type=rank_type,
                    game_id=entry.get("appid") or entry.get("package") or "",
                    developer=entry.get("developer") or "",
                    icon_url=entry.get("icon") or "",
                    rating=float(entry.get("stars") or entry.get("score") or 0),
                ))
                if len(all_items) >= self.TOP_N:
                    break

            if not data.get("hasNextPage"):
                break
            page += 1

        if not all_items:
            logger.warning("AppGallery CN 未解析到数据")
        return all_items
