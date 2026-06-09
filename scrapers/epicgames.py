"""
Epic Games Store 排行榜
畅销榜：store.epicgames.com/collection/top-sellers
下载榜：store.epicgames.com/collection/top-free-to-play
活跃榜：store.epicgames.com/collection/most-played
数据来源：store.epicgames.com/graphql (collectionLayoutQuery, country=SG)
"""
import logging
from .base import BaseScraper, RankItem

logger = logging.getLogger(__name__)

_GQL_URL = "https://store.epicgames.com/graphql"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Referer": "https://store.epicgames.com/",
}

_SLUG_MAP = {
    "revenue":  "top-sellers",
    "download": "top-free-to-play",
    "active":   "most-played",
}

_QUERY = """
query collectionLayoutQuery($locale: String, $slug: String) {
  Storefront {
    collectionLayout(locale: $locale, slug: $slug) {
      collectionOffers {
        title
        id
        namespace
        developerDisplayName
        publisherDisplayName
        keyImages { type url }
        seller { name }
      }
    }
  }
}
"""


def _pick_image(key_images: list) -> str:
    for t in ("OfferImageTall", "Thumbnail", "OfferImageWide"):
        for img in key_images:
            if img.get("type") == t:
                return img.get("url", "")
    return key_images[0].get("url", "") if key_images else ""


class EpicGamesScraper(BaseScraper):
    PLATFORM = "epicgames"
    SUPPORTED_RANK_TYPES = ["download", "revenue", "active"]

    def fetch(self, rank_type: str) -> list:
        slug = _SLUG_MAP.get(rank_type)
        if not slug:
            return []
        try:
            resp = self._post(
                _GQL_URL,
                json={
                    "query": _QUERY,
                    "variables": {"locale": "en-US", "slug": slug},
                },
                headers=_HEADERS,
            )
            resp.raise_for_status()
            offers = (
                resp.json()
                .get("data", {})
                .get("Storefront", {})
                .get("collectionLayout", {})
                .get("collectionOffers", [])
            )
        except Exception as e:
            logger.error(f"Epic Games {rank_type} 失败: {e}")
            return []

        results = []
        for i, o in enumerate(offers[:self.TOP_N]):
            title = o.get("title", "")
            if not title:
                continue
            developer = o.get("developerDisplayName") or (o.get("seller") or {}).get("name", "")
            results.append(RankItem(
                rank=i + 1,
                name=title,
                platform=self.PLATFORM,
                rank_type=rank_type,
                game_id=o.get("id", ""),
                developer=developer,
                icon_url=_pick_image(o.get("keyImages") or []),
                rating=0.0,
            ))
        return results
