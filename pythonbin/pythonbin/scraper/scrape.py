import argparse
import asyncio
import pathlib
from collections import deque
from urllib.parse import urlparse, urljoin

from boilerpy3 import extractors
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from pydantic import BaseModel


class Extractor:
    def __init__(self, doc: str) -> None:
        self.doc = doc
        self.extractor = extractors.ArticleExtractor()

    def extract(self) -> str:
        soup = BeautifulSoup(self.doc, "html5lib")

        # remove cookies div 'awsccc-sb-ux-c'
        cookie_div = soup.find('div', {'id': 'awsccc-sb-ux-c'})
        if cookie_div:
            cookie_div.decompose()

        # re-create the doc string
        doc_fixed: str = soup.prettify()

        return self.extractor.get_content(doc_fixed)


class PageContent(BaseModel):
    url: str
    title: str
    original_content: str
    extracted_content: str
    links: list[str]
    downward_links: list[str]


async def get_content(url) -> PageContent:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(3000)
            title = await page.title()
            doc = await page.content()
            content = Extractor(doc).extract()

            links = await page.query_selector_all("a")
            hrefs = [await link.get_attribute("href") for link in links]

            # Resolve relative URLs and filter out the ones that don't go downward
            base_url = urlparse(url)
            downward_hrefs = []
            for href in hrefs:
                if not href:
                    continue
                full_url = urljoin(url, href)
                parsed_url = urlparse(full_url)
                if not parsed_url.netloc == base_url.netloc:
                    continue
                if parsed_url == base_url:
                    continue
                if parsed_url.path.startswith(base_url.path):
                    downward_hrefs.append(full_url)

            return PageContent(url=url, title=title, original_content=doc, extracted_content=content, links=hrefs,
                               downward_links=downward_hrefs)
        finally:
            await page.close()
            await browser.close()


async def get_content_with_semaphore(url, semaphore) -> PageContent:
    async with semaphore:
        return await get_content(url)


class Writer:
    output_path: pathlib.Path

    def __init__(self, output_path: pathlib.Path) -> None:
        self.output_path = output_path
        with self.output_path.open("w") as f:
            pass

    def write(self, content: PageContent) -> None:
        with self.output_path.open("a") as f:
            f.write(f"## {content.title}\n\n")
            f.write(content.extracted_content)
            f.write("\n\n")


def convert_url_to_seen_key(url: str) -> str:
    parsed_url = urlparse(url)
    return f"{parsed_url.netloc}{parsed_url.path}"


async def main(url: str):
    writer = Writer(pathlib.Path("/tmp/output.txt"))
    semphore = asyncio.Semaphore(4)
    initial_content = await get_content(url)
    writer.write(initial_content)

    pages = deque(initial_content.downward_links)
    seen_pages = set()
    seen_pages.add(convert_url_to_seen_key(url))
    tasks = []
    while pages or tasks:
        while pages and len(tasks) < semphore._value:
            page_url = pages.popleft()
            if convert_url_to_seen_key(page_url) in seen_pages:
                continue
            print(f"Scraping {page_url}")
            task = asyncio.create_task(get_content_with_semaphore(page_url, semphore))
            tasks.append(task)
            seen_pages.add(convert_url_to_seen_key(page_url))

        if tasks:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                content = await task
                writer.write(content)
                pages.extend(content.downward_links)
            tasks = list(pending)


def run_main(url: str):
    asyncio.run(main(url))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape a URL")
    parser.add_argument("--url", help="URL to scrape", required=True)
    args = parser.parse_args()
    run_main(args.url)
