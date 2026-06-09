"""
TapTap 近期焦点（app-calendar）
GET https://www.taptap.cn/webapiv2/calendar/v1/event-list?X-UA=...&day=<unix_ts_cst_midnight>
data.list_a/list_b/list_c — event_type 1=首发/上线, 3=预约测试
"""
import logging
import time
from datetime import datetime, timezone, timedelta
from .base import BaseLaunchScraper, LaunchItem

logger = logging.getLogger(__name__)

_URL   = "https://www.taptap.cn/webapiv2/calendar/v1/event-list"
_X_UA  = (
    "V=1&PN=WebApp&LANG=zh_CN&VN_CODE=102&LOC=CN&PLT=PC"
    "&DS=Android&UID=4bac27cb-afa3-4c48-8cb3-60f6027cebc5"
    "&OS=Windows&OSV=10&DT=PC"
)
_CST = timezone(timedelta(hours=8))
_HEADERS = {
    "Referer":         "https://www.taptap.cn/app-calendar",
    "Accept":          "application/json",
    "Accept-Language": "zh-CN,zh;q=0.9",
}
class TapTapCalendarScraper(BaseLaunchScraper):
    PLATFORM   = "taptap"
    DAYS_AHEAD = 60   # 覆盖约两个月的近期焦点

    def fetch_launches(self) -> list:
        results = []
        seen    = set()
        today   = datetime.now(_CST).replace(hour=0, minute=0, second=0, microsecond=0)

        for offset in range(self.DAYS_AHEAD):
            day = today + timedelta(days=offset)
            ts  = int(day.timestamp())
            try:
                resp = self._get(_URL, headers=_HEADERS, params={"X-UA": _X_UA, "day": ts})
                resp.raise_for_status()
                dd = resp.json().get("data") or {}
                for lk in ("list_a", "list_b", "list_c"):
                    for item in (dd.get(lk) or []):
                        # 只取焦点大卡（近期焦点），event_level=1
                        if item.get("event_level") != 1:
                            continue
                        aci       = item.get("app_card_info") or {}
                        game_name = aci.get("title") or ""
                        event_type = item.get("sub_event_type_title") or ""
                        # 同一游戏可能同时有"预下载"和"首发"两个独立事件，按(名称+类型)去重
                        dedup_key = (game_name, event_type)
                        if not game_name or dedup_key in seen:
                            continue
                        seen.add(dedup_key)
                        st = item.get("start_time") or 0
                        if st:
                            launch_time = datetime.fromtimestamp(st, tz=_CST).strftime("%Y-%m-%d %H:%M")
                        else:
                            launch_time = day.strftime("%Y-%m-%d")
                        devs      = aci.get("developers") or []
                        developer = next(
                            (d.get("name") for d in devs if d.get("type") == "publisher"),
                            devs[0].get("name") if devs else "",
                        )
                        icon_info = aci.get("icon") or {}
                        icon_url  = (
                            icon_info.get("original_url")
                            or icon_info.get("url")
                            or ""
                        ) if isinstance(icon_info, dict) else (icon_info or "")
                        results.append(LaunchItem(
                            platform=self.PLATFORM,
                            game_name=game_name,
                            launch_time=launch_time,
                            launch_type=item.get("sub_event_type_title") or "",
                            developer=developer or "",
                            game_id=str(aci.get("id") or ""),
                            icon_url=icon_url,
                        ))
                time.sleep(0.3)
            except Exception as e:
                logger.warning(f"taptap calendar day {day.date()}: {e}")
        return results
