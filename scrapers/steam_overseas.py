"""
Steam 海外区域排行榜
继承 SteamScraper，只改 PLATFORM 和 _REGION
"""
from .steam import SteamScraper


class SteamUSScraper(SteamScraper):
    PLATFORM = "steam_us"
    _REGION = "US"


class SteamJPScraper(SteamScraper):
    PLATFORM = "steam_jp"
    _REGION = "JP"


class SteamKRScraper(SteamScraper):
    PLATFORM = "steam_kr"
    _REGION = "KR"


class SteamGBScraper(SteamScraper):
    PLATFORM = "steam_gb"
    _REGION = "GB"
