from bs4 import BeautifulSoup
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth


async def scrape_site(url):
    # initialize Stealth with Playwright
    async with Stealth().use_async(async_playwright()) as p:

        # launch headless browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")

        title = await page.title()

        # Extract data from the page
        text = await page.content()

        await browser.close()

        soup = BeautifulSoup(text, 'html.parser')
        for irrelevant in soup(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.get_text(separator="\n", strip=True)

        return (title + "\n\n" + text[:2000])

# This function scrapes one page, creates a scrape job for playwright function by scrape_multiple_sites(urls):
async def fetch_site(page, url):
    await page.goto(url, wait_until="networkidle")
    title = await page.title()
    text = await page.content()
    return url, title, text


async def scrape_multiple_sites(urls):
    # initialize Stealth with Playwright
    async with Stealth().use_async(async_playwright()) as p:

        # launch headless browser
        browser = await p.chromium.launch(headless=True)

        tasks = []

        for url in urls:
            page = await browser.new_page()
            # schedule an async scraping job for each page
            tasks.append(fetch_site(page, url))

        # Run all scraping tasks concurrently
        results = await asyncio.gather(*tasks)

        await browser.close()
     
        return results
