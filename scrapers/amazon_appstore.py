"""
Amazon Appstore 游戏畅销榜
通过抓取 Best Sellers 页面解析排名。
注意：Amazon 有反爬机制，如持续返回空结果建议配合代理使用。
"""
import re
import logging
from .base import BaseScraper, RankItem

logger = logging.getLogger(__name__)

_URL = "https://www.amazon.com/best-sellers-apps-games/zgbs/mobile-apps/2350149011"

_HEADERS = {
    "User-Agent":      ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# 多个候选正则，依次尝试
_PATTERNS = [
    # 结构化的 zg-item-immersion 区块
    re.compile(r'class="p13n-sc-truncate[^"]*"\s*[^>]*>\s*([^<]{2,80}?)\s*<', re.S),
    # 备用：data-p13n-asin-metadata JSON 中的 title
    re.compile(r'"title"\s*:\s*"([^"]{2,80})"'),
]


class AmazonAppStoreScraper(BaseScraper):
    PLATFORM = "amazon"
    SUPPORTED_RANK_TYPES = ["download"]

    def fetch(self, rank_type: str) -> list:
        if rank_type != "download":
            return []

        try:
            resp = self._get(_URL, headers=_HEADERS)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            logger.warning(f"Amazon Appstore 请求失败: {e}")
            return []

        names: list[str] = []
        for pat in _PATTERNS:
            found = pat.findall(html)
            cleaned = [n.strip() for n in found if len(n.strip()) > 1]
            if len(cleaned) >= 5:
                names = cleaned
                break

        if not names:
            logger.warning("Amazon Appstore 未解析到数据，页面结构可能已变更")
            return []

        seen: set[str] = set()
        items = []
        for name in names:
            if name in seen:
                continue
            seen.add(name)
            items.append(RankItem(
                rank=len(items) + 1,
                name=name,
                platform=self.PLATFORM,
                rank_type=rank_type,
            ))
            if len(items) >= self.TOP_N:
                break
        return items
