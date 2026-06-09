"""
RuStore 游戏排行榜（Playwright）
下载榜：rustore.ru/catalog/games/all（页面默认排序即下载量排序）
"""
import asyncio
import logging
from .base import BaseScraper, RankItem

logger = logging.getLogger(__name__)

_URL = "https://www.rustore.ru/catalog/games/all"

_JS_EXTRACT = """
() => {
    const links = document.querySelectorAll('a[href*="/catalog/app/"]');
    const results = [];
    for (const a of links) {
        const href = a.getAttribute('href') || '';
        const packageName = href.split('/catalog/app/')[1] || '';
        if (!packageName) continue;
        const img = a.querySelector('img');
        const iconUrl = img ? (img.getAttribute('src') || '') : '';
        const titleEl = a.querySelector('p');
        const name = titleEl ? titleEl.textContent.trim() : '';
        if (!name) continue;
        const ratingEl = a.querySelector('[data-testid="rating"]');
        const ratingTxt = ratingEl ? ratingEl.textContent.trim().replace(',', '.') : '0';
        const rating = parseFloat(ratingTxt) || 0;
        results.push({ name, packageName, iconUrl, rating });
    }
    return results;
}
"""


class RuStoreScraper(BaseScraper):
    PLATFORM = "rustore"
    SUPPORTED_RANK_TYPES = ["download"]

    def fetch(self, rank_type: str) -> list:
        if rank_type != "download":
            return []
        try:
            return asyncio.run(self._async_fetch())
        except Exception as e:
            logger.error(f"RuStore 抓取失败: {e}")
            return []

    async def _async_fetch(self) -> list:
        from playwright.async_api import async_playwright

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
            try:
                ctx = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                    ),
                    locale="ru-RU",
                    viewport={"width": 1920, "height": 1080},
                )
                page = await ctx.new_page()
                await page.goto(_URL, timeout=30000)
                await page.wait_for_timeout(6000)
                raw = await page.evaluate(_JS_EXTRACT)
            finally:
                await browser.close()

        results = []
        for i, item in enumerate(raw[:self.TOP_N]):
            results.append(RankItem(
                rank=i + 1,
                name=item["name"],
                platform=self.PLATFORM,
                rank_type="download",
                game_id=item["packageName"],
                developer="",
                icon_url=item["iconUrl"],
                rating=item["rating"],
            ))
        return results
