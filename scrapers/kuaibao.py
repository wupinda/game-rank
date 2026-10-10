"""好游快爆榜单：兼容新版异步榜单和仍使用静态 HTML 的下载榜。"""
import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import BaseScraper, RankItem

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.3839.com"
_RANK_API = f"{_BASE_URL}/app/hykb_web/index.php"
_RANK_URLS = {
    "active": f"{_BASE_URL}/top/hot.html",
    "download": f"{_BASE_URL}/top/down.html",
    "reservation": f"{_BASE_URL}/top/expect.html",
}


class KuaibaoScraper(BaseScraper):
    PLATFORM = "kuaibao"
    SUPPORTED_RANK_TYPES = ["active", "download", "reservation"]

    def fetch(self, rank_type: str) -> list:
        url = _RANK_URLS.get(rank_type)
        if not url:
            logger.error("好游快爆不支持榜单: %s", rank_type)
            return []
        try:
            resp = self._get(url, headers={"Referer": f"{_BASE_URL}/"})
            resp.raise_for_status()
            resp.encoding = "utf-8"

            # 新版页面只有菜单，游戏由接口加载。读取实际默认榜单，
            # 避免把 hot（90 天热门）错当成 hot2（本周热门）。
            soup = BeautifulSoup(resp.text, "lxml")
            rank_source = None
            for script in soup.find_all("script", src=False):
                match = re.search(
                    r"RankList\.init\(\s*\{\s*type\s*:\s*['\"]([\w-]+)['\"]",
                    script.get_text(),
                )
                if match:
                    rank_source = match.group(1)
                    break
            if rank_source:
                return self._fetch_dynamic(rank_source, rank_type, url)

            items = self._parse_html(resp.text, rank_type)
            if not items:
                logger.warning("好游快爆 [%s] 未找到有效游戏卡片", rank_type)
            return items
        except Exception as exc:
            logger.error("好游快爆 [%s] 抓取失败: %s", rank_type, exc)
            return []

    def _fetch_dynamic(self, source: str, rank_type: str, referer: str) -> list:
        items, seen = [], set()
        page, offset = 1, 0
        while len(items) < self.TOP_N:
            resp = self._get(
                _RANK_API,
                params={"m": "top", "ac": "rank_list", "type": source,
                        "page": page, "offset": offset},
                headers={"Referer": referer, "X-Requested-With": "XMLHttpRequest"},
            )
            resp.raise_for_status()
            resp.encoding = "utf-8"
            payload = resp.json()
            if not isinstance(payload, dict) or str(payload.get("code")) != "100":
                raise ValueError("榜单接口未返回成功状态")
            html = payload.get("html")
            if not isinstance(html, str) or not html.strip():
                raise ValueError("榜单接口未返回游戏卡片")
            batch = self._parse_html(html, rank_type)
            new_items = [item for item in batch if item.game_id not in seen]
            if not new_items:
                raise ValueError("榜单接口未返回新的有效游戏记录")
            items.extend(new_items)
            seen.update(item.game_id for item in new_items)
            if len(items) >= self.TOP_N or str(payload.get("nextpage", 0)) == "0":
                break
            count = int(payload.get("count", 0))
            if count <= 0:
                raise ValueError("榜单接口分页数量无效")
            offset += count
            page += 1
        return items[:self.TOP_N]

    def _parse_html(self, html: str, rank_type: str) -> list:
        soup = BeautifulSoup(html, "lxml")
        items, seen = [], set()
        # 不能使用 [class*=rank] li，它会匹配菜单和截图。
        for card in soup.select(".game-item, ul.ranking-game > li.rankli"):
            name_el = card.select_one(".game-name .sp-name, .gameInfo .name .sp-name")
            rank_el = card.select_one(".item-num, .rank-num")
            link = card.select_one("a[href*='/a/']")
            if not name_el or not rank_el or not link:
                continue
            name = name_el.get_text(strip=True)
            rank_text = rank_el.get_text(strip=True)
            game_match = re.search(r"/a/(\d+)\.htm(?:[?#]|$)", link.get("href", ""))
            if not name or not re.fullmatch(r"[1-9]\d*", rank_text) or not game_match:
                continue
            game_id = game_match.group(1)
            if game_id in seen:
                continue
            seen.add(game_id)

            developer_el = card.select_one(".auth a")
            score_el = card.select_one(".sp-score, .gameScore .score")
            score_match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*分?",
                                      score_el.get_text(strip=True)) if score_el else None
            rating = float(score_match.group(1)) if score_match else 0.0
            if not 0 <= rating <= 10:
                rating = 0.0
            icon_el = card.select_one(".game-icon img, img.gameLogo")
            icon_src = ""
            if icon_el:
                icon_src = (icon_el.get("data-src") or icon_el.get("lz_src")
                            or icon_el.get("src") or "")

            items.append(RankItem(
                rank=int(rank_text), name=name, platform=self.PLATFORM,
                rank_type=rank_type, game_id=game_id,
                developer=developer_el.get_text(strip=True) if developer_el else "",
                icon_url=urljoin(_BASE_URL, icon_src) if icon_src else "",
                rating=rating,
            ))
            if len(items) >= self.TOP_N:
                break
        return items
