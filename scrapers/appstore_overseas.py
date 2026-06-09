"""
Apple App Store 海外区域榜单
各子类只覆盖 PLATFORM 和 COUNTRY 两个类变量，其余逻辑复用 AppStoreScraper
"""
from .appstore import AppStoreScraper


class AppStoreUSScraper(AppStoreScraper):
    PLATFORM = "appstore_us"
    COUNTRY  = "us"


class AppStoreJPScraper(AppStoreScraper):
    PLATFORM = "appstore_jp"
    COUNTRY  = "jp"


class AppStoreKRScraper(AppStoreScraper):
    PLATFORM = "appstore_kr"
    COUNTRY  = "kr"


class AppStoreGBScraper(AppStoreScraper):
    PLATFORM = "appstore_gb"
    COUNTRY  = "gb"
