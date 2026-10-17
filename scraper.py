"""Scrape quotes from https://quotes.toscrape.com/ and save them as CSV."""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path
from typing import Callable

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://quotes.toscrape.com/page/{page}/"
USER_AGENT = "SimpleWebScraper/1.0 (educational project; respectful scraping)"
REQUEST_TIMEOUT = 10


def fetch_page(page_number: int, session: requests.Session) -> str | None:
    """Fetch one page and return its HTML, or None if the request fails."""
    url = BASE_URL.format(page=page_number)
    try:
        response = session.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.text
    except requests.RequestException as error:
        print(f"Could not fetch page {page_number}: {error}")
        return None


def parse_quotes(html: str) -> list[dict[str, str]]:
    """Extract quote text, author, and tags from a page of HTML."""
    soup = BeautifulSoup(html, "html.parser")
    quotes: list[dict[str, str]] = []

    for quote_box in soup.select("div.quote"):
        text_element = quote_box.select_one("span.text")
        author_element = quote_box.select_one("small.author")
        tag_elements = quote_box.select("a.tag")

        text = text_element.get_text(strip=True) if text_element else "Unknown"
        author = author_element.get_text(strip=True) if author_element else "Unknown"
        tags = ", ".join(tag.get_text(strip=True) for tag in tag_elements)

        quotes.append({"quote": text, "author": author, "tags": tags})

    return quotes


def scrape_quotes(
    pages: int = 1,
    session: requests.Session | None = None,
    sleep_function: Callable[[float], None] = time.sleep,
) -> list[dict[str, str]]:
    """Scrape between one and five pages while removing duplicate quotes."""
    if not 1 <= pages <= 5:
        raise ValueError("pages must be between 1 and 5")

    owns_session = session is None
    active_session = session or requests.Session()
    collected: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    try:
        for page_number in range(1, pages + 1):
            print(f"Scraping page {page_number} of {pages}...")
            html = fetch_page(page_number, active_session)
            if html is None:
                print("Stopping because the page could not be downloaded.")
                break

            for quote in parse_quotes(html):
                identity = (quote["quote"], quote["author"])
                if identity not in seen:
                    seen.add(identity)
                    collected.append(quote)

            print(f"Collected {len(collected)} unique quotes so far.")
            if page_number < pages:
                sleep_function(1)
    finally:
        if owns_session:
            active_session.close()

    print(f"Total quotes collected: {len(collected)}")
    return collected


def save_to_csv(quotes: list[dict[str, str]], output_path: str | Path) -> None:
    """Write quote dictionaries to a UTF-8 CSV file."""
    path = Path(output_path)
    with path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["quote", "author", "tags"])
        writer.writeheader()
        writer.writerows(quotes)
    print(f"Saved {len(quotes)} quotes to {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scrape quotes, authors, and tags from quotes.toscrape.com."
    )
    parser.add_argument(
        "--pages",
        type=int,
        choices=range(1, 6),
        default=1,
        metavar="1-5",
        help="number of pages to scrape (default: 1)",
    )
    parser.add_argument(
        "--output",
        default="quotes.csv",
        help="CSV output path (default: quotes.csv)",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    quotes = scrape_quotes(pages=args.pages)
    save_to_csv(quotes, args.output)


if __name__ == "__main__":
    main()
