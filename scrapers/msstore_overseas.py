"""
Microsoft Store 海外区域排行榜
继承 MsStoreScraper，只改 PLATFORM 和 _GL
"""
from .msstore import MsStoreScraper


class MsStoreUSScraper(MsStoreScraper):
    PLATFORM = "msstore_us"
    _GL = "US"


class MsStoreJPScraper(MsStoreScraper):
    PLATFORM = "msstore_jp"
    _GL = "JP"


class MsStoreKRScraper(MsStoreScraper):
    PLATFORM = "msstore_kr"
    _GL = "KR"


class MsStoreGBScraper(MsStoreScraper):
    PLATFORM = "msstore_gb"
    _GL = "GB"
