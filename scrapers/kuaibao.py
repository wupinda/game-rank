"""
好游快爆 (www.3839.com) 榜单
SSR 页面，直接用 requests + BeautifulSoup 解析，无需 Playwright。

支持：活跃榜（热门）、下载榜、预约榜
"""
import logging
import re
from bs4 import BeautifulSoup
from .base import BaseScraper, RankItem

logger = logging.getLogger(__name__)

_RANK_URLS = {
    "active":      "https://www.3839.com/top/hot.html",
    "download":    "https://www.3839.com/top/down.html",
    "reservation": "https://www.3839.com/top/expect.html",
}


class KuaibaoScraper(BaseScraper):
    PLATFORM = "kuaibao"
    SUPPORTED_RANK_TYPES = ["active", "download", "reservation"]

    def fetch(self, rank_type: str) -> list:
        url = _RANK_URLS.get(rank_type, _RANK_URLS["active"])
        try:
            resp = self._get(url, headers={
                "Referer":         "https://www.3839.com/",
                "Accept":          "text/html,application/xhtml+xml,*/*",
                "Accept-Encoding": "gzip, deflate",
            })
            resp.raise_for_status()
            resp.encoding = "utf-8"
        except Exception as e:
            logger.error(f"好游快爆 [{rank_type}] 请求失败: {e}")
            return []

        return self._parse_html(resp.text, rank_type)

    def _parse_html(self, html: str, rank_type: str) -> list:
        soup  = BeautifulSoup(html, "lxml")
        items = []
        seen  = set()

        # 游戏卡片：[class*=rank] 下的 li，跳过空行
        for li in soup.select("[class*=rank] li"):
            texts = [t.strip() for t in li.stripped_strings if t.strip()]
            if not texts:
                continue

            # 第一个文本通常是排名数字，跳过纯数字找游戏名
            name = ""
            for t in texts:
                if t and len(t) >= 2 and not re.match(r'^[\d\s\.]+$', t) and "厂商" not in t:
                    name = t
                    break
            if not name or name in seen:
                continue
            seen.add(name)

            # 开发商（紧跟"厂商："标签后面的文本，排除预约数/下载数）
            developer = ""
            for i, t in enumerate(texts):
                if "厂商" in t and i + 1 < len(texts):
                    candidate = texts[i + 1]
                    if not re.search(r'[万预约下载]', candidate):
                        developer = candidate
                    break

            # 评分（含"分"的文本）
            rating = 0.0
            for t in texts:
                m = re.search(r'([\d.]+)\s*分', t)
                if m:
                    try:
                        rating = float(m.group(1))
                    except ValueError:
                        pass
                    break

            # 图标 URL
            icon_el  = li.select_one("img")
            icon_url = icon_el.get("src", "") or icon_el.get("data-src", "") if icon_el else ""

            # 游戏 ID（来自 a 标签 href，如 /a/123456.htm）
            a_el    = li.select_one("a[href*='/a/']")
            game_id = ""
            if a_el:
                m = re.search(r'/a/(\d+)', a_el.get("href", ""))
                if m:
                    game_id = m.group(1)

            items.append(RankItem(
                rank=len(items) + 1,
                name=name,
                platform=self.PLATFORM,
                rank_type=rank_type,
                game_id=game_id,
                developer=developer,
                icon_url=icon_url,
                rating=rating,
            ))

            if len(items) >= self.TOP_N:
                break

        return items
