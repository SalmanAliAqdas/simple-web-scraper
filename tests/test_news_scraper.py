"""Offline tests for the UN OSESGY headline metadata scraper."""

import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from news_scraper import (
    AccessNotPermittedError,
    check_robots_permission,
    fetch_listing,
    is_relevant_headline,
    parse_news_listing,
    save_to_csv,
    scrape_news,
)

ROBOTS_ALLOWED = "User-agent: *\nDisallow: /admin/\n"
ROBOTS_BLOCKED = "User-agent: *\nDisallow: /en/news\n"
SAMPLE_HTML = """
<html><body>
  <article class="pattern-vertical-card">
    <div class="pattern-vertical-card__content--title">
      <h5><a href="/en/news/yemen-peace-update">Yemen peace process update</a></h5>
    </div>
    <time datetime="2026-10-10">10 October 2026</time>
  </article>
  <article class="pattern-vertical-card">
    <div class="pattern-vertical-card__content--title">
      <a href="/en/news/unrelated">Office staffing announcement</a>
    </div>
  </article>
  <article class="pattern-vertical-card">
    <div class="pattern-vertical-card__content--title">
      <a href="/en/news/yemen-peace-update#main">Yemen peace process update</a>
    </div>
    <time>10 October 2026</time>
  </article>
</body></html>
"""


def make_response(text: str) -> Mock:
    response = Mock()
    response.content = text.encode("utf-8")
    response.text = text
    response.raise_for_status.return_value = None
    return response


class NewsScraperTests(unittest.TestCase):
    def test_robots_allows_public_news_listing(self):
        session = Mock()
        session.get.return_value = make_response(ROBOTS_ALLOWED)
        self.assertTrue(check_robots_permission(session))
        _, kwargs = session.get.call_args
        self.assertEqual(kwargs["timeout"], 15)
        self.assertIn("SimpleNewsScraper", kwargs["headers"]["User-Agent"])

    def test_robots_blocks_disallowed_listing(self):
        session = Mock()
        session.get.return_value = make_response(ROBOTS_BLOCKED)
        self.assertFalse(check_robots_permission(session))

    def test_robots_network_failure_fails_closed(self):
        session = Mock()
        session.get.side_effect = requests.RequestException("offline")
        with self.assertRaises(AccessNotPermittedError):
            check_robots_permission(session)

    def test_parse_listing_extracts_metadata(self):
        articles = parse_news_listing(SAMPLE_HTML)
        self.assertEqual(len(articles), 3)
        self.assertEqual(articles[0]["headline"], "Yemen peace process update")
        self.assertEqual(articles[0]["publication_date"], "10 October 2026")
        self.assertEqual(articles[0]["article_url"], "https://osesgy.unmissions.org/en/news/yemen-peace-update")
        self.assertEqual(articles[0]["source"], "UN OSESGY")
        self.assertEqual(articles[1]["publication_date"], "Unknown")

    def test_keyword_filter_is_case_insensitive(self):
        self.assertTrue(is_relevant_headline("Talks with ANSAR ALLAH resume"))
        self.assertTrue(is_relevant_headline("Envoy concludes visit to Riyadh"))
        self.assertFalse(is_relevant_headline("Office staffing announcement"))

    def test_fetch_listing_handles_network_error(self):
        session = Mock()
        session.get.side_effect = requests.RequestException("offline")
        with patch("builtins.print"):
            self.assertIsNone(fetch_listing(0, session))

    def test_scrape_filters_deduplicates_and_delays(self):
        session = Mock()
        session.get.side_effect = [
            make_response(ROBOTS_ALLOWED), make_response(SAMPLE_HTML),
            make_response(SAMPLE_HTML),
        ]
        sleeper = Mock()
        with patch("builtins.print"):
            articles = scrape_news(2, session=session, sleep_function=sleeper)
        self.assertEqual(len(articles), 1)
        self.assertEqual(session.get.call_count, 3)
        self.assertEqual(sleeper.call_count, 2)
        sleeper.assert_any_call(1.0)

    def test_scrape_stops_when_robots_disallows_access(self):
        session = Mock()
        session.get.return_value = make_response(ROBOTS_BLOCKED)
        with self.assertRaises(AccessNotPermittedError):
            scrape_news(1, session=session, sleep_function=Mock())
        session.get.assert_called_once()

    def test_scrape_rejects_more_than_three_pages(self):
        with self.assertRaises(ValueError):
            scrape_news(4)

    def test_save_to_csv_writes_expected_fields(self):
        articles = [{
            "headline": "Yemen update", "publication_date": "10 October 2026",
            "article_url": "https://example.test/article", "source": "UN OSESGY",
        }]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "news.csv"
            with patch("builtins.print"):
                save_to_csv(articles, output)
            with output.open(encoding="utf-8-sig", newline="") as csv_file:
                rows = list(csv.DictReader(csv_file))
        self.assertEqual(rows, articles)


if __name__ == "__main__":
    unittest.main()
