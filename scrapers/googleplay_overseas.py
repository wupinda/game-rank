"""
Google Play 海外各区域子类
仅覆盖 PLATFORM / COUNTRY / LANG，其余逻辑复用 GooglePlayScraper
"""
from .googleplay import GooglePlayScraper


class GooglePlayUSScraper(GooglePlayScraper):
    PLATFORM = "googleplay_us"
    COUNTRY  = "us"
    LANG     = "en"


class GooglePlayJPScraper(GooglePlayScraper):
    PLATFORM = "googleplay_jp"
    COUNTRY  = "jp"
    LANG     = "ja"


class GooglePlayKRScraper(GooglePlayScraper):
    PLATFORM = "googleplay_kr"
    COUNTRY  = "kr"
    LANG     = "ko"


class GooglePlayGBScraper(GooglePlayScraper):
    PLATFORM = "googleplay_gb"
    COUNTRY  = "gb"
    LANG     = "en"
