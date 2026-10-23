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
                login = await page.goto('https://accounts.google.com/ServiceLogin?service=youtube', wait_until='domcontentloaded', timeout=25000)
                state = await page.context.storage_state()
                logger.warning('Google sign-in page probe: HTTP=%s, title=%r, host=%s, cookie_count=%d', login.status if login else None, (await page.title())[:120], __import__('urllib.parse', fromlist=['urlparse']).urlparse(page.url).hostname, len(state['cookies']))
            finally:
                await browser.close()
    except Exception as exc:
        logger.error('YouTube Chromium probe failed: %s: %s', type(exc).__name__, str(exc)[:300])
