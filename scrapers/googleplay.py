"""
Google Play 游戏榜单（Playwright）
热门免费（下载榜）和创收最高（畅销榜），支持 US/JP/KR/GB 四个区域
通过 gl/hl 参数指定区域，点击 Tab 切换下载榜 / 畅销榜
"""
import asyncio
import logging
from .base import BaseScraper, RankItem

logger = logging.getLogger(__name__)

_BASE_URL = "https://play.google.com/store/games?device=phone"

# 各区域 Tab 标题关键词：(下载榜关键词, 畅销榜关键词)
_REGION_LABELS = {
    "us": (r"top free",      r"top grossing"),
    "gb": (r"top free",      r"top grossing"),
    "jp": (r"無料",           r"売上トップ"),
    "kr": (r"인기 앱/게임",   r"최고 매출"),
}

def _build_js(free_kw: str, gross_kw: str) -> tuple[str, str]:
    extract = r"""(keyword) => {
        const spans = [...document.querySelectorAll("span.ypTNYd")];
        const target = spans.find(s => new RegExp(keyword, "i").test(s.textContent.trim()));
        if (!target) return [];
        let el = target;
        for (let i = 0; i < 6; i++) { el = el.parentElement; if (!el) return []; }
        return [...el.querySelectorAll("a[href*='/store/apps/details']")]
            .filter(a => a.querySelector(".fy9T3c"))
            .map(a => {
                const rankEl = a.querySelector(".fy9T3c div") || a.querySelector(".fy9T3c");
                const rank   = rankEl ? parseInt(rankEl.textContent.trim()) : 0;
                const nameEl = a.querySelector(".DdYX5");
                const devEl  = a.querySelector(".wMUdtb");
                const ratingEl = a.querySelector(".TT9eCd");
                const imgEl  = a.querySelector("img.T75of") || a.querySelector("img");
                const href   = a.getAttribute("href") || "";
                const m      = href.match(/id=([^&]+)/);
                let rating = 0;
                if (ratingEl) {
                    const al = ratingEl.getAttribute("aria-label") || "";
                    const rm = al.match(/[\d.]+/);
                    if (rm) rating = parseFloat(rm[0]);
                }
                return {
                    rank,
                    name:      nameEl  ? nameEl.textContent.trim()  : "",
                    developer: devEl   ? devEl.textContent.trim()   : "",
                    rating,
                    game_id:   m ? m[1] : "",
                    icon:      imgEl   ? (imgEl.src || imgEl.getAttribute("data-src") || "") : "",
                };
            }).filter(r => r.rank > 0);
    }"""

    click = r"""(keyword) => {
        const spans = [...document.querySelectorAll("span.ypTNYd")];
        const target = spans.find(s => new RegExp(keyword, "i").test(s.textContent.trim()));
        if (!target) return false;
        const btn = target.closest(".D3Qfie");
        if (!btn) return false;
        btn.click();
        return true;
    }"""

    return extract, click


class GooglePlayScraper(BaseScraper):
    PLATFORM  = "googleplay"
    COUNTRY   = "us"
    LANG      = "en"
    SUPPORTED_RANK_TYPES = ["download", "revenue"]

    def fetch(self, rank_type: str) -> list:
        try:
            raw = asyncio.run(self._async_fetch_both())
        except Exception as e:
            logger.error(f"Google Play [{self.COUNTRY}] 抓取失败: {e}")
            return []
        items = []
        for r in (raw.get(rank_type) or [])[:self.TOP_N]:
            if not r.get("name"):
                continue
            items.append(RankItem(
                rank=r["rank"],
                name=r["name"],
                platform=self.PLATFORM,
                rank_type=rank_type,
                game_id=r.get("game_id", ""),
                developer=r.get("developer", ""),
                icon_url=r.get("icon", ""),
                rating=float(r.get("rating") or 0),
            ))
        return items

    async def _async_fetch_both(self) -> dict:
        from playwright.async_api import async_playwright

        free_kw, gross_kw = _REGION_LABELS.get(self.COUNTRY, _REGION_LABELS["us"])
        js_extract, js_click = _build_js(free_kw, gross_kw)
        url = f"{_BASE_URL}&gl={self.COUNTRY.upper()}&hl={self.LANG}"

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            try:
                page = await browser.new_page(
                    locale=f"{self.LANG}-{self.COUNTRY.upper()}",
                    viewport={"width": 1920, "height": 1080},
                )
                await page.goto(url, timeout=30000)
                await page.wait_for_timeout(6000)
                await page.evaluate("window.scrollBy(0, 3000)")
                await page.wait_for_timeout(3000)

                free_items = await page.evaluate(js_extract, free_kw)

                await page.evaluate(js_click, gross_kw)
                await page.wait_for_timeout(2000)
                gross_items = await page.evaluate(js_extract, gross_kw)

            finally:
                await browser.close()

        return {"download": free_items, "revenue": gross_items}
