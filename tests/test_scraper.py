"""Automated tests for the Simple Web Scraper."""

import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from scraper import fetch_page, parse_quotes, save_to_csv, scrape_quotes


SAMPLE_HTML = """
<html><body>
  <div class="quote">
    <span class="text">“A useful quote.”</span>
    <small class="author">Ada Example</small>
    <div class="tags"><a class="tag">learning</a><a class="tag">python</a></div>
  </div>
  <div class="quote">
    <span class="text">“A useful quote.”</span>
    <small class="author">Ada Example</small>
    <a class="tag">duplicate</a>
  </div>
  <div class="quote"><span class="text">“Text without details.”</span></div>
</body></html>
"""


class ScraperTests(unittest.TestCase):
    def test_parse_quotes_extracts_fields_and_handles_missing_data(self):
        quotes = parse_quotes(SAMPLE_HTML)

        self.assertEqual(len(quotes), 3)
        self.assertEqual(quotes[0]["quote"], "“A useful quote.”")
        self.assertEqual(quotes[0]["author"], "Ada Example")
        self.assertEqual(quotes[0]["tags"], "learning, python")
        self.assertEqual(quotes[2]["author"], "Unknown")
        self.assertEqual(quotes[2]["tags"], "")

    def test_fetch_page_uses_timeout_and_user_agent(self):
        response = Mock(text=SAMPLE_HTML)
        response.raise_for_status.return_value = None
        session = Mock()
        session.get.return_value = response

        result = fetch_page(2, session)

        self.assertEqual(result, SAMPLE_HTML)
        session.get.assert_called_once()
        _, kwargs = session.get.call_args
        self.assertEqual(kwargs["timeout"], 10)
        self.assertIn("SimpleWebScraper", kwargs["headers"]["User-Agent"])

    def test_fetch_page_handles_network_errors(self):
        session = Mock()
        session.get.side_effect = requests.RequestException("offline")

        with patch("builtins.print"):
            self.assertIsNone(fetch_page(1, session))

    def test_scrape_removes_duplicates_and_waits_between_pages(self):
        session = Mock()
        response = Mock(text=SAMPLE_HTML)
        response.raise_for_status.return_value = None
        session.get.return_value = response
        sleeper = Mock()

        with patch("builtins.print"):
            quotes = scrape_quotes(2, session=session, sleep_function=sleeper)

        self.assertEqual(len(quotes), 2)
        self.assertEqual(session.get.call_count, 2)
        sleeper.assert_called_once_with(1)

    def test_scrape_rejects_invalid_page_count(self):
        with self.assertRaises(ValueError):
            scrape_quotes(6)

    def test_save_to_csv_writes_headers_and_rows(self):
        quotes = [{"quote": "Hello", "author": "Author", "tags": "tag"}]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output.csv"
            with patch("builtins.print"):
                save_to_csv(quotes, output)
            with output.open(encoding="utf-8-sig", newline="") as csv_file:
                rows = list(csv.DictReader(csv_file))

        self.assertEqual(rows, quotes)


if __name__ == "__main__":
    unittest.main()
