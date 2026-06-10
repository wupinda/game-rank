from .appstore          import AppStoreScraper
from .taptap            import TapTapScraper
from .bilibili          import BilibiliScraper
from .xiaomi            import XiaomiScraper
from .kuaibao           import KuaibaoScraper
from .wegame            import WeGameScraper
from .myapp             import MyAppScraper
from .bilibili_launch   import BilibiliLaunchScraper
from .taptap_calendar   import TapTapCalendarScraper
from .kuaibao_timeline  import KuaibaoTimelineScraper
from .wegame_launch     import WeGameLaunchScraper
from .xiaomi_new        import XiaomiNewScraper
from .rustore            import RuStoreScraper
from .appgallery         import AppGalleryScraper
from .appgallery_cn      import AppGalleryCNScraper
from .galaxystore        import GalaxyStoreScraper
from .getapps            import GetAppsScraper
from .amazon_appstore    import AmazonAppStoreScraper
from .appstore_overseas  import AppStoreUSScraper, AppStoreJPScraper, AppStoreKRScraper, AppStoreGBScraper
from .googleplay         import GooglePlayScraper
from .googleplay_overseas import GooglePlayUSScraper, GooglePlayJPScraper, GooglePlayKRScraper, GooglePlayGBScraper
from .steam              import SteamScraper
from .steam_overseas     import SteamUSScraper, SteamJPScraper, SteamKRScraper, SteamGBScraper
from .epicgames          import EpicGamesScraper
from .msstore            import MsStoreScraper
from .msstore_overseas   import MsStoreUSScraper, MsStoreJPScraper, MsStoreKRScraper, MsStoreGBScraper
from .base              import PLATFORMS, RANK_TYPES, RankItem, LaunchItem, BaseLaunchScraper

ALL_SCRAPERS = {
    "appstore": AppStoreScraper,
    "taptap":   TapTapScraper,
    "bilibili": BilibiliScraper,
    "xiaomi":   XiaomiScraper,
    "kuaibao":  KuaibaoScraper,
    "wegame":   WeGameScraper,
    "myapp":    MyAppScraper,
    # 海外移动平台
    "rustore":     RuStoreScraper,
    "appgallery_cn": AppGalleryCNScraper,
    "appgallery":  AppGalleryScraper,
    "galaxystore": GalaxyStoreScraper,
    "getapps":     GetAppsScraper,
    "amazon":      AmazonAppStoreScraper,
    "appstore_us": AppStoreUSScraper,
    "appstore_jp": AppStoreJPScraper,
    "appstore_kr": AppStoreKRScraper,
    "appstore_gb": AppStoreGBScraper,
    "googleplay":    GooglePlayScraper,
    "googleplay_us": GooglePlayUSScraper,
    "googleplay_jp": GooglePlayJPScraper,
    "googleplay_kr": GooglePlayKRScraper,
    "googleplay_gb": GooglePlayGBScraper,
    # PC 平台
    "steam_us":   SteamUSScraper,
    "steam_jp":   SteamJPScraper,
    "steam_kr":   SteamKRScraper,
    "steam_gb":   SteamGBScraper,
    "epicgames":  EpicGamesScraper,
    "msstore_us": MsStoreUSScraper,
    "msstore_jp": MsStoreJPScraper,
    "msstore_kr": MsStoreKRScraper,
    "msstore_gb": MsStoreGBScraper,
}

ALL_LAUNCH_SCRAPERS = {
    "bilibili": BilibiliLaunchScraper,
    "taptap":   TapTapCalendarScraper,
    "kuaibao":  KuaibaoTimelineScraper,
    "wegame":   WeGameLaunchScraper,
}
