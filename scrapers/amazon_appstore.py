"""
Amazon Appstore 游戏畅销榜
注意：Amazon 畅销榜页面为纯客户端渲染（SPA），无 SSR 数据，
      普通 HTTP 请求无法获取游戏列表。需要 Playwright 等无头浏览器支持。
      当前实现保留接口，始终返回空列表并输出警告。
"""
import logging
from .base import BaseScraper, RankItem

logger = logging.getLogger(__name__)


class AmazonAppStoreScraper(BaseScraper):
    PLATFORM = "amazon"
    SUPPORTED_RANK_TYPES = ["download"]

    def fetch(self, rank_type: str) -> list:
        logger.warning(
            "Amazon Appstore 畅销榜为纯 SPA，无法通过 HTTP 请求获取数据，"
            "需要 Playwright 支持。当前返回空列表。"
        )
        return []
