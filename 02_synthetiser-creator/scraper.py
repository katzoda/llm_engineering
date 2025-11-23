from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import requests


# Standard headers to fetch a website
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

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

        return (title + "\n\n" + text[:200])

def fetch_website_contents(url):
    """
    Return the title and contents of the website at the given url
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    # retrieve the string from <title> element
    title = soup.title.string if soup.title else "No title found"
    if soup.body:
        # delete not wanted html elements
        for element in soup.body(["script", "style", "img", "input"]):
            element.decompose()
        # extract all visible text from the <body>
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)[:1_000]


def fetch_website_links(url):
    """
    Return the links on the webiste at the given url
    I realize this is inefficient as we're parsing twice! This is to keep the code in the lab simple.
    Feel free to use a class and optimize it!
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link]
