"""
Scraper Service — fetches and extracts readable content from a URL.

Kept deliberately simple: we extract title + body text for AI analysis.
Does not follow redirects through login walls.
"""

import logging
from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; LinkVault/1.0; +https://github.com/linkvault)"
    )
}
TIMEOUT_SECONDS = 8


@dataclass
class ScrapedPage:
    title: str
    text: str
    ok: bool  # False if scraping failed — AI still runs on partial data


def scrape_url(url: str) -> ScrapedPage:
    """
    Fetch a URL and extract its title and body text.
    Never raises — returns ScrapedPage(ok=False) on any error.

    Args:
        url: A valid HTTP/HTTPS URL

    Returns:
        ScrapedPage with title, text, and ok flag
    """
    hostname = urlparse(url).hostname or url

    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT_SECONDS, allow_redirects=True)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning("Scrape failed for %s: %s", hostname, e)
        return ScrapedPage(title=hostname, text="", ok=False)

    try:
        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract title: prefer og:title > <title> > hostname
        og_title = soup.find("meta", property="og:title")
        title_tag = soup.find("title")
        title = (
            (og_title.get("content") if og_title else None)
            or (title_tag.get_text(strip=True) if title_tag else None)
            or hostname
        )

        # Remove script/style noise before extracting text
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        return ScrapedPage(title=str(title)[:512], text=text, ok=True)

    except Exception as e:
        logger.warning("Parse failed for %s: %s", hostname, e)
        return ScrapedPage(title=hostname, text="", ok=False)
