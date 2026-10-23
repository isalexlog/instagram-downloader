import logging
from playwright.async_api import async_playwright

logger = logging.getLogger('youtube_browser_probe')

async def run_probe():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
            try:
                page = await browser.new_page()
                response = await page.goto('https://www.youtube.com/', wait_until='domcontentloaded', timeout=25000)
                logger.warning('YouTube Chromium probe: HTTP=%s, title=%r, url=%s', response.status if response else None, (await page.title())[:120], page.url)
            finally:
                await browser.close()
    except Exception as exc:
        logger.error('YouTube Chromium probe failed: %s: %s', type(exc).__name__, str(exc)[:300])
