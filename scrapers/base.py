from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import date
from typing import List
import requests
import time
import logging

logger = logging.getLogger(__name__)

RANK_TYPES = {
    "active":        "活跃榜",
    "revenue":       "畅销榜",
    "download":      "下载榜",
    "reservation":   "预约榜",
}

PLATFORMS = {
    "appstore": "App Store",
    "taptap":   "TapTap",
    "bilibili": "B站",
    "xiaomi":   "小米",
    "kuaibao":  "快爆",
    "wegame":   "WeGame",
    "myapp":    "应用宝",
    # 海外移动平台
    "rustore":     "RuStore",
    "appstore_us": "App Store (US)",
    "appstore_jp": "App Store (JP)",
    "appstore_kr": "App Store (KR)",
    "appstore_gb": "App Store (GB)",
    "googleplay":    "Google Play",
    "googleplay_us": "Google Play (US)",
    "googleplay_jp": "Google Play (JP)",
    "googleplay_kr": "Google Play (KR)",
    "googleplay_gb": "Google Play (GB)",
    # 海外其他移动平台
    "appgallery":  "AppGallery",
    "galaxystore": "Galaxy Store",
    "getapps":     "GetApps",
    "amazon":      "Amazon Appstore",
    # PC 平台
    "steam_us":   "Steam (US)",
    "steam_jp":   "Steam (JP)",
    "steam_kr":   "Steam (KR)",
    "steam_gb":   "Steam (GB)",
    "epicgames":  "Epic Games Store",
    "msstore_us": "Microsoft Store (US)",
    "msstore_jp": "Microsoft Store (JP)",
    "msstore_kr": "Microsoft Store (KR)",
    "msstore_gb": "Microsoft Store (GB)",
}


@dataclass
class RankItem:
    rank: int
    name: str
    platform: str
    rank_type: str
    game_id: str = ""
    developer: str = ""
    icon_url: str = ""
    rating: float = 0.0
    test_time: str = ""   # 开测时间，仅开测榜填写
    test_info: str = ""   # 测试类型/状态，仅开测榜填写
    fetch_date: str = field(default_factory=lambda: date.today().isoformat())

    def to_dict(self) -> dict:
        d = {
            "排名":     self.rank,
            "游戏名称": self.name,
            "平台":     PLATFORMS.get(self.platform, self.platform),
            "榜单类型": RANK_TYPES.get(self.rank_type, self.rank_type),
            "开发商":   self.developer,
            "评分":     self.rating if self.rating else "",
            "游戏ID":   self.game_id,
            "图标URL":  self.icon_url,
            "抓取日期": self.fetch_date,
        }
        if self.test_time:
            d["开测时间"] = self.test_time
        if self.test_info:
            d["测试类型"] = self.test_info
        return d


@dataclass
class LaunchItem:
    platform: str
    game_name: str
    launch_time: str    # "YYYY-MM-DD" or "YYYY-MM-DD HH:MM"
    launch_type: str    # "公测" / "首发" / "删档测试" etc.
    developer: str = ""
    game_id: str = ""
    icon_url: str = ""
    fetch_date: str = field(default_factory=lambda: date.today().isoformat())


class BaseScraper(ABC):
    PLATFORM = ""
    SUPPORTED_RANK_TYPES: List[str] = []
    TOP_N = 20

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Connection":      "keep-alive",
    }

    def __init__(self, timeout: int = 30, proxies: dict = None):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        if proxies:
            self.session.proxies.update(proxies)

    @abstractmethod
    def fetch(self, rank_type: str) -> List[RankItem]:
        """拉取指定榜单的 Top N 数据"""

    def fetch_all(self) -> List[RankItem]:
        results = []
        for rank_type in self.SUPPORTED_RANK_TYPES:
            try:
                label = f"{PLATFORMS.get(self.PLATFORM, self.PLATFORM)} {RANK_TYPES.get(rank_type, rank_type)}"
                logger.info(f"正在抓取: {label}")
                items = self.fetch(rank_type)
                results.extend(items[: self.TOP_N])
                logger.info(f"  完成，获取 {len(items)} 条")
                time.sleep(1.5)
            except Exception as exc:
                logger.error(f"抓取失败 [{self.PLATFORM}/{rank_type}]: {exc}")
        return results

    def _get(self, url: str, **kwargs) -> requests.Response:
        return self.session.get(url, timeout=self.timeout, **kwargs)

    def _post(self, url: str, **kwargs) -> requests.Response:
        return self.session.post(url, timeout=self.timeout, **kwargs)


class BaseLaunchScraper(BaseScraper):
    """Base class for launch/testing schedule scrapers (no rank feed)."""
    SUPPORTED_RANK_TYPES: List[str] = []

    def fetch(self, rank_type: str) -> List[RankItem]:
        return []

    def fetch_launches(self) -> List[LaunchItem]:
        raise NotImplementedError
