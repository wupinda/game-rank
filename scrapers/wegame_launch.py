"""
WeGame 新游发布
通过 Playwright 渲染 https://www.wegame.com.cn/store 并提取新游发布区域数据
用 getBoundingClientRect() 精确匹配日期与游戏卡片的对应关系
"""
import asyncio
import logging
from datetime import date, datetime, timedelta

from .base import BaseLaunchScraper, LaunchItem

logger = logging.getLogger(__name__)

_URL = "https://www.wegame.com.cn/store"

_STATUS_MAP = {
    "现已上线": "首发",
    "即将上线": "首发",
    "正式上线": "首发",
    "公测":     "公测",
    "不删档":   "不删档测试",
    "删档":     "删档测试",
    "重大测试": "测试",
    "内测":     "内测",
    "预约活动": "预约",
    "预约":     "预约",
    "限时活动": "活动",
}

_SKIP_STATUS = {"新游前瞻"}

_JS = """() => {
    const dates = [];
    for (const di of document.querySelectorAll(".gscroll-title-list-item")) {
        const el = di.querySelector(".date-num");
        if (!el) continue;
        const r = el.getBoundingClientRect();
        dates.push({date: el.textContent.trim(), cx: r.left + r.width / 2});
    }
    const results = [];
    for (const card of document.querySelectorAll(".gscroll-cont-list .game-card-v3")) {
        const r = card.getBoundingClientRect();
        const nameEl  = card.querySelector(".widget-gcard-tit span:first-child");
        const statEl  = card.querySelector(".widget-futureyg-act-desc");
        const linkEl  = card.querySelector(".widget-gcard-cover a");
        const imgEl   = card.querySelector(".widget-gcard-cover img");
        const cx = r.left + r.width / 2;
        let bestDate = "", bestDist = Infinity;
        for (const d of dates) {
            const dist = Math.abs(d.cx - cx);
            if (dist < bestDist) { bestDist = dist; bestDate = d.date; }
        }
        results.push({
            date:    bestDate,
            name:    nameEl ? nameEl.textContent.trim() : "",
            status:  statEl ? statEl.textContent.trim() : "",
            game_id: linkEl ? linkEl.getAttribute("href").replace("/store/", "") : "",
            icon:    imgEl  ? imgEl.src : "",
        });
    }
    return results;
}"""


def _normalize_status(status: str) -> str:
    for k, v in _STATUS_MAP.items():
        if k in status:
            return v
    return status


def _parse_date(date_str: str) -> str:
    """Convert MM-DD to YYYY-MM-DD using current or next year."""
    today = date.today()
    try:
        mm, dd = map(int, date_str.split("-"))
        candidate = date(today.year, mm, dd)
        # If the date is more than 90 days in the past, it's either this year's
        # old event or next year's upcoming event — keep as-is (it will be
        # filtered out by DAYS_LOOKBACK anyway)
        return candidate.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return ""


class WeGameLaunchScraper(BaseLaunchScraper):
    PLATFORM = "wegame"
    DAYS_LOOKBACK = 60   # 保留今天往前 N 天的已上线游戏

    def fetch_launches(self) -> list:
        try:
            return asyncio.run(self._async_fetch())
        except Exception as e:
            logger.error(f"wegame launch scraper error: {e}")
            return []

    async def _async_fetch(self) -> list:
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            try:
                page = await browser.new_page(
                    locale="zh-CN",
                    viewport={"width": 1920, "height": 1080},
                )
                await page.goto(_URL, timeout=30000)
                await page.wait_for_timeout(8000)
                raw = await page.evaluate(_JS)
            finally:
                await browser.close()

        today = date.today()
        cutoff = today - timedelta(days=self.DAYS_LOOKBACK)

        results = []
        seen = set()
        for item in raw:
            name   = (item.get("name")   or "").strip()
            status = (item.get("status") or "").strip()

            if not name or status in _SKIP_STATUS:
                continue

            date_str = _parse_date(item.get("date", ""))
            if not date_str:
                continue

            game_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if game_date < cutoff:
                continue

            key = (name, date_str)
            if key in seen:
                continue
            seen.add(key)

            results.append(LaunchItem(
                platform=self.PLATFORM,
                game_name=name,
                launch_time=date_str + " 00:00",
                launch_type=_normalize_status(status),
                developer="",
                game_id=item.get("game_id", ""),
                icon_url=item.get("icon", ""),
            ))

        return results
