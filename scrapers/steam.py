"""
Steam 游戏排行榜（Playwright）
畅销榜：store.steampowered.com/charts/topselling/SG（按收入排名）
活跃榜：store.steampowered.com/charts/mostplayed/SG（当前最高同时在线）
"""
import asyncio
import logging
from .base import BaseScraper, RankItem

logger = logging.getLogger(__name__)

_BASE_URL = "https://store.steampowered.com/charts"

_JS_EXTRACT = """
() => {
    const rows = document.querySelectorAll("tbody tr");
    const results = [];
    for (const row of rows) {
        const tds = row.querySelectorAll("td");
        if (tds.length < 2) continue;
        const rank = parseInt(tds[1].textContent.trim());
        if (!rank || rank > 100) continue;
        const link = row.querySelector("a[href*='/app/']");
        if (!link) continue;
        const href = link.getAttribute("href") || "";
        const m = href.match(/[/]app[/]([0-9]+)[/]([^?]+)/);
        if (!m) continue;
        const appid = m[1];
        const nameSlug = m[2].replace(/_/g, " ");
        const nameLink = tds[2] ? tds[2].querySelector("a") : null;
        const name = (nameLink ? nameLink.textContent.trim() : "") || nameSlug;
        if (!name) continue;
        results.push({ rank, name, appid });
    }
    return results;
}
"""


class SteamScraper(BaseScraper):
    PLATFORM = "steam"
    SUPPORTED_RANK_TYPES = ["revenue", "active"]
    _REGION = "SG"

    def fetch(self, rank_type: str) -> list:
        try:
            return asyncio.run(self._async_fetch(rank_type))
        except Exception as e:
            logger.error(f"Steam [{self._REGION}] {rank_type} 抓取失败: {e}")
            return []

    async def _async_fetch(self, rank_type: str) -> list:
        from playwright.async_api import async_playwright

        slug = "topselling" if rank_type == "revenue" else "mostplayed"
        url = f"{_BASE_URL}/{slug}/{self._REGION}"

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            try:
                page = await browser.new_page(
                    locale="en-US",
                    viewport={"width": 1920, "height": 1080},
                )
                await page.goto(url, timeout=30000)
                await page.wait_for_timeout(5000)
                raw = await page.evaluate(_JS_EXTRACT)
            finally:
                await browser.close()

        results = []
        for item in raw[:self.TOP_N]:
            results.append(RankItem(
                rank=item["rank"],
                name=item["name"],
                platform=self.PLATFORM,
                rank_type=rank_type,
                game_id=item["appid"],
                developer="",
                icon_url=f"https://cdn.cloudflare.steamstatic.com/steam/apps/{item['appid']}/capsule_231x87.jpg",
                rating=0.0,
            ))
        return results
