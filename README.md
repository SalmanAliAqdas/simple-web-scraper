# Simple Web Scraper

Simple Web Scraper is a beginner-friendly Python project that collects quote text, author names, and tags from [Quotes to Scrape](https://quotes.toscrape.com/). The website is public and was created specifically for practicing web scraping.

The project demonstrates HTTP requests, HTML parsing, duplicate removal, CSV output, command-line arguments, error handling, and automated testing. It only reads public pages and does not bypass access restrictions or collect private data.

## Features

- Scrapes one to five pages (one page by default)
- Extracts quote text, author names, and tags
- Waits one second between page requests
- Uses a descriptive User-Agent and a 10-second timeout
- Shows page-by-page progress and the final quote count
- Prevents duplicate quotes
- Handles request failures and missing HTML fields gracefully
- Saves results as a UTF-8 CSV file that opens cleanly in Excel
- Includes offline unit tests using local HTML and mocked requests

## Requirements

- Python 3.10 or newer
- Internet access when running the scraper

## Installation

Open the project folder in VS Code, then open a PowerShell terminal with **Terminal > New Terminal**.

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, the environment can still be used directly by replacing `python` in later commands with `.\.venv\Scripts\python.exe`.

Install the dependencies:

```powershell
python -m pip install -r requirements.txt
```

In VS Code, select the environment through **Ctrl+Shift+P > Python: Select Interpreter**, then choose the interpreter inside `.venv`.

## Usage

Scrape the default of one page and save the results to `quotes.csv`:

```powershell
python scraper.py
```

Scrape three pages:

```powershell
python scraper.py --pages 3
```

Choose a different output filename:

```powershell
python scraper.py --pages 5 --output my_quotes.csv
```

The `--pages` value must be from 1 through 5. Existing output at the selected path is replaced.

## Project Structure

```text
simple-web-scraper/
├── scraper.py            # Scraping, parsing, CSV, and command-line logic
├── requirements.txt      # Third-party Python packages
├── sample_output.csv     # Example of the generated CSV format
├── README.md             # Project documentation
├── .gitignore            # Files Git should ignore
└── tests/
    └── test_scraper.py   # Automated unit tests
```

## Testing

Run all tests from the project root:

```powershell
python -m unittest discover -s tests -v
```

The tests do not require internet access. They use local sample HTML and mocked HTTP responses to verify parsing, request settings, error handling, duplicate removal, delays, validation, and CSV output.

## CSV Format

The generated file contains these columns:

| Column | Description |
| --- | --- |
| `quote` | The full quote text |
| `author` | The author's name, or `Unknown` if absent |
| `tags` | Tags joined with commas, or an empty value if absent |

See `sample_output.csv` for an example.

## Limitations

- The scraper supports a maximum of five pages by design.
- It depends on the current HTML structure of Quotes to Scrape; website changes may require selector updates.
- A failed request stops the current run, while any quotes already collected are still saved.
- The program does not retry failed requests or scrape JavaScript-rendered pages.
- The one-second delay is suitable for this practice website but is not a universal scraping policy. Always review a website's terms and access rules before scraping it.
