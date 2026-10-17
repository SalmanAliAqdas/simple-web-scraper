"""Collect relevant headline metadata from the public UN OSESGY news listing."""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path
from typing import Callable
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

NEWS_URL = "https://osesgy.unmissions.org/en/news"
ROBOTS_URL = "https://osesgy.unmissions.org/robots.txt"
TERMS_URL = "https://www.un.org/en/about-us/terms-of-use"
SOURCE_NAME = "UN OSESGY"
USER_AGENT = "SimpleNewsScraper/1.0 (educational, non-commercial headline metadata collector)"
REQUEST_TIMEOUT = 15
REQUEST_DELAY = 1.0
KEYWORDS = (
    "yemen", "yemeni", "saudi arabia", "saudi", "houthi", "houthis",
    "ansar allah", "riyadh", "conflict", "ceasefire", "truce",
    "peace process", "red sea", "maritime", "hostilities", "escalation",
    "de-escalation",
)


class AccessNotPermittedError(RuntimeError):
    """Raised when robots.txt blocks access or cannot be checked reliably."""


def _response_html(response: requests.Response) -> str:
    """Decode live UTF-8 pages while remaining friendly to mocked responses."""
    if isinstance(response.content, bytes):
        return response.content.decode("utf-8", errors="replace")
    return response.text


def check_robots_permission(session: requests.Session) -> bool:
    """Check robots.txt, failing closed when its policy cannot be verified."""
    try:
        response = session.get(
            ROBOTS_URL,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise AccessNotPermittedError(
            f"Could not verify robots.txt; no news pages were requested: {error}"
        ) from error

    parser = RobotFileParser()
    parser.set_url(ROBOTS_URL)
    parser.parse(_response_html(response).splitlines())
    return parser.can_fetch(USER_AGENT, NEWS_URL)


def fetch_listing(page_number: int, session: requests.Session) -> str | None:
    """Fetch a single zero-indexed listing page, returning None on an error."""
    try:
        response = session.get(
            NEWS_URL,
            params={"page": page_number},
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return _response_html(response)
    except requests.RequestException as error:
        print(f"Could not fetch listing page {page_number + 1}: {error}")
        return None


def _canonical_url(url: str) -> str:
    """Remove fragments so equivalent article URLs deduplicate reliably."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc.lower(), parts.path, parts.query, ""))


def parse_news_listing(html: str) -> list[dict[str, str]]:
    """Extract headline metadata only; article bodies are never requested."""
    soup = BeautifulSoup(html, "html.parser")
    articles: list[dict[str, str]] = []
    for card in soup.select("article.pattern-vertical-card"):
        link = card.select_one(".pattern-vertical-card__content--title a[href]")
        if link is None:
            continue
        headline = link.get_text(" ", strip=True)
        href = link.get("href", "").strip()
        if not headline or not href:
            continue
        date_element = card.select_one("time")
        publication_date = date_element.get_text(" ", strip=True) if date_element else "Unknown"
        articles.append({
            "headline": headline,
            "publication_date": publication_date,
            "article_url": _canonical_url(urljoin(NEWS_URL, href)),
            "source": SOURCE_NAME,
        })
    return articles


def is_relevant_headline(headline: str) -> bool:
    """Return True when a headline includes a configured conflict-related term."""
    normalized = " ".join(headline.casefold().split())
    return any(keyword in normalized for keyword in KEYWORDS)


def scrape_news(
    pages: int = 1,
    session: requests.Session | None = None,
    sleep_function: Callable[[float], None] = time.sleep,
) -> list[dict[str, str]]:
    """Check permission, then collect filtered metadata from up to three pages."""
    if not 1 <= pages <= 3:
        raise ValueError("pages must be between 1 and 3")
    owns_session = session is None
    active_session = session or requests.Session()
    collected: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    try:
        if not check_robots_permission(active_session):
            raise AccessNotPermittedError(
                f"robots.txt does not permit access to {NEWS_URL}; scraping stopped."
            )
        print("robots.txt permits access to the public news listing.")
        print(f"Usage remains subject to the UN Terms of Use: {TERMS_URL}")
        sleep_function(REQUEST_DELAY)
        for page_index in range(pages):
            print(f"Scraping listing page {page_index + 1} of {pages}...")
            html = fetch_listing(page_index, active_session)
            if html is None:
                print("Stopping because the listing page could not be downloaded.")
                break
            for article in parse_news_listing(html):
                url = article["article_url"]
                if is_relevant_headline(article["headline"]) and url not in seen_urls:
                    seen_urls.add(url)
                    collected.append(article)
            print(f"Collected {len(collected)} matching unique articles so far.")
            if page_index < pages - 1:
                sleep_function(REQUEST_DELAY)
    finally:
        if owns_session:
            active_session.close()
    print(f"Total matching articles collected: {len(collected)}")
    return collected


def save_to_csv(articles: list[dict[str, str]], output_path: str | Path) -> None:
    """Save headline metadata to a UTF-8 CSV file."""
    path = Path(output_path)
    with path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["headline", "publication_date", "article_url", "source"],
        )
        writer.writeheader()
        writer.writerows(articles)
    print(f"Saved {len(articles)} articles to {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect Yemen-conflict headline metadata from UN OSESGY."
    )
    parser.add_argument("--pages", type=int, choices=range(1, 4), default=1,
                        metavar="1-3", help="listing pages to scrape (default: 1)")
    parser.add_argument("--output", default="yemen_saudi_news.csv",
                        help="CSV output path (default: yemen_saudi_news.csv)")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        articles = scrape_news(pages=args.pages)
    except AccessNotPermittedError as error:
        print(f"Access check failed: {error}")
        print("Use an official UN RSS feed or API instead if one becomes available; do not bypass the restriction.")
        raise SystemExit(1) from error
    save_to_csv(articles, args.output)


if __name__ == "__main__":
    main()
