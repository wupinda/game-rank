"""
好游快爆 即将上线 — https://www.3839.com/timeline.html
SSR HTML，无 JSON API，用 BeautifulSoup 解析。
只取 panelList[rel=1]（即将上线 tab），跳过 rel="last7"（已上线）。
"""
import re
import logging
from datetime import date
from bs4 import BeautifulSoup
from .base import BaseLaunchScraper, LaunchItem

logger = logging.getLogger(__name__)

_URL = "https://www.3839.com/timeline.html"
_HEADERS = {
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer":         "https://www.3839.com/",
}
_SKIP_REL   = {"last7"}
_SKIP_TYPES = {"上线试玩", "海外首发"}

# 关键词优先级从高到低，先匹配先返回
_TYPE_RULES = [
    ("海外上线",    "海外首发"),
    ("上线试玩",    "上线试玩"),
    ("预下载",      "预下载"),
    ("不删档测试",  "不删档测试"),
    ("删档测试",    "删档测试"),
    ("删档",        "删档测试"),
    ("内测",        "内测"),
    ("测试",        "测试"),
    ("正式上线",    "首发"),
    ("上线",        "首发"),
]

def _extract_type(text: str) -> str:
    for keyword, label in _TYPE_RULES:
        if keyword in text:
            return label
    return ""


class KuaibaoTimelineScraper(BaseLaunchScraper):
    PLATFORM = "kuaibao"

    def fetch_launches(self) -> list:
        resp = self._get(_URL, headers=_HEADERS)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        panels = soup.select(".panelList")
        # rel=1 = 即将上线 tab
        panel = next((p for p in panels if str(p.get("rel", "")) == "1"), None)
        if not panel:
            logger.warning("kuaibao: 即将上线 panel (rel=1) not found")
            return []

        results    = []
        today_year = date.today().year

        for card in panel.select(".foreCard"):
            rel = card.get("rel", "")
            if rel in _SKIP_REL:
                continue
            date_hd    = card.select_one(".foreCard-hd")
            date_label = date_hd.get_text(strip=True) if date_hd else ""
            launch_time = _parse_date(date_label, today_year)

            for li in card.select("ul.foreList li"):
                em = li.select_one(".name em")
                if not em:
                    continue
                game_name = em.get_text(strip=True)
                if not game_name:
                    continue

                # 红框说明文字：.info 内评分之外的那个 span
                info_spans  = li.select(".info span")
                launch_type = ""
                for sp in info_spans:
                    if "score" not in sp.get("class", []):
                        raw = sp.get_text(strip=True)
                        if raw:
                            launch_type = _extract_type(raw)
                            break

                if not launch_type or launch_type in _SKIP_TYPES:
                    continue

                img      = li.select_one(".img img")
                icon_url = ""
                if img:
                    src = img.get("src") or img.get("lz_src") or ""
                    icon_url = ("https:" + src) if src.startswith("//") else src

                results.append(LaunchItem(
                    platform=self.PLATFORM,
                    game_name=game_name,
                    launch_time=launch_time,
                    launch_type=launch_type,
                    developer="",
                    icon_url=icon_url,
                ))
        return results


def _parse_date(label: str, year: int) -> str:
    m = re.search(r'(\d+)月(\d+)日', label)
    if m:
        return f"{year}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return label
