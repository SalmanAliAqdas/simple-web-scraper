# Simple Web Scraper

A beginner-friendly Python project containing two respectful command-line web scrapers:

- **Quotes Scraper** collects quotes, authors, and tags from [Quotes to Scrape](https://quotes.toscrape.com/), a public scraping-practice website.
- **OSESGY News Scraper** collects headline metadata related to Yemen, Saudi Arabia, the Houthis, and associated conflict topics from the public [UN OSESGY news listing](https://osesgy.unmissions.org/en/news).

Both tools use `requests`, Beautiful Soup, and Python's built-in CSV support. They include timeouts, descriptive User-Agent headers, polite delays, duplicate prevention, progress output, and offline automated tests.

## Responsible Use

The news scraper checks OSESGY's `robots.txt` before requesting any listing page and stops if access is disallowed or the policy cannot be verified. As checked on 17 October 2026, `/en/news` was not disallowed for general crawlers. The [United Nations Terms of Use](https://www.un.org/en/about-us/terms-of-use) permit personal, non-commercial use subject to their conditions and any material-specific restrictions.

The news scraper requests listing pages only. It stores headlines, publication dates, article URLs, and the source name; it does not download article bodies. It does not bypass paywalls, authentication, CAPTCHAs, anti-bot controls, or access restrictions. Website policies can change, so the runtime robots check remains authoritative.

## Features

### Quotes Scraper

- Scrapes one to five pages, with one page as the default
- Extracts quote text, authors, and tags
- Waits one second between page requests
- Removes duplicate quotes and handles missing fields
- Writes UTF-8 CSV output

### OSESGY News Scraper

- Scrapes one to three listing pages, with one page as the default
- Checks `robots.txt` before every run and fails closed when access is unclear
- Extracts headline, publication date, article URL, and source name only
- Filters headlines using Yemen-conflict terms such as Yemen, Saudi Arabia, Houthi, Ansar Allah, Riyadh, ceasefire, truce, Red Sea, and escalation
- Removes duplicate article URLs
- Uses a 15-second timeout and waits one second between requests
- Stops cleanly on access-policy or network failures

## Requirements

- Python 3.10 or newer
- Internet access when running either scraper

## Installation

Open this folder in VS Code and select **Terminal > New Terminal**. In PowerShell, create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, use `.\.venv\Scripts\python.exe` instead of `python` in the commands below. In VS Code, the environment can be selected with **Ctrl+Shift+P > Python: Select Interpreter**.

## Usage

### Quotes Scraper

Scrape one page to the default `quotes.csv` file:

```powershell
python scraper.py
```

Scrape three pages to a chosen output file:

```powershell
python scraper.py --pages 3 --output my_quotes.csv
```

### OSESGY News Scraper

Scrape one listing page to the default `yemen_saudi_news.csv` file:

```powershell
python news_scraper.py
```

Scrape the maximum of three listing pages:

```powershell
python news_scraper.py --pages 3
```

Choose another output path:

```powershell
python news_scraper.py --pages 2 --output filtered_news.csv
```

If the robots policy blocks the listing or cannot be checked, the program exits without requesting news pages and recommends using an official UN RSS feed or API instead.

## Output Formats

The quotes CSV contains `quote`, `author`, and `tags` columns. The news CSV contains `headline`, `publication_date`, `article_url`, and `source` columns. Generated CSV files are ignored by Git, while the curated `sample_output.csv` remains included as a quotes example.

## Project Structure

```text
simple-web-scraper/
|-- scraper.py                 # Existing quotes scraper
|-- news_scraper.py            # OSESGY headline metadata scraper
|-- requirements.txt           # Third-party dependencies
|-- sample_output.csv          # Curated quotes CSV example
|-- README.md                  # Project documentation
|-- .gitignore                 # Generated and local files excluded from Git
`-- tests/
    |-- test_scraper.py        # Quotes scraper tests
    `-- test_news_scraper.py   # News scraper tests
```

## Testing

Run the complete offline test suite from the project root:

```powershell
python -m unittest discover -s tests -v
```

The tests use local HTML and mocked HTTP responses. They cover parsing, request settings, robots-policy enforcement, filtering, duplicate removal, delays, network errors, validation, and CSV output without contacting either website.

## Limitations

- The quotes scraper supports at most five pages; the news scraper supports at most three listing pages.
- HTML selector changes on either source may require parser updates.
- Headline filtering is keyword-based and can omit relevant items or include false positives.
- The news scraper does not download article text, follow article links, retry failed requests, or execute JavaScript.
- OSESGY and UN policies and access controls may change. The scraper must not be modified to evade them.
- Collected UN metadata is intended for personal, non-commercial use under the applicable UN terms.
