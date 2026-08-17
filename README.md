# LEC AI — Website Catalogue Agent

A small, working web-crawling agent that dynamically discovers same-site URLs, extracts structured data, stores it in SQLite, and prevents duplicate catalogue entries across repeated runs.

## Stack

- Python
- Requests + BeautifulSoup
- SQLite
- FastAPI
- Deterministic queue-based crawl agent

No external LLM/API key is required.

## Features

1. Dynamically chooses URLs from links discovered on fetched pages.
2. Crawls only the seed hostname.
3. Canonicalises URLs by removing fragments, normalising paths, sorting query parameters and removing common tracking parameters.
4. Follows redirects and records the final canonical URL.
5. Extracts title, URL, timestamp, summary and SHA-256 content fingerprint.
6. Uses a SQLite UNIQUE constraint on canonical URL.
7. Uses content hashes to avoid duplicate content under different URLs.
8. Repeated runs update existing rows instead of inserting duplicates.
9. Records observable decisions: visit, queue, redirect, add, update, skip and error.

## Project structure

```text
lec_ai_website_catalogue_agent/
├── app/
│   ├── __init__.py
│   ├── agent.py
│   ├── api.py
│   ├── config.py
│   ├── db.py
│   ├── extractor.py
│   ├── main.py
│   └── normalizer.py
├── data/
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Windows setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.main init-db
```

If PowerShell blocks activation, you can run the Python executable directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## macOS/Linux setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main init-db
```

## Run the crawler

Use the included public practice site:

```bash
python -m app.main crawl --url https://books.toscrape.com/ --max-pages 10
```

Then inspect the catalogue:

```bash
python -m app.main pages
```

Inspect decisions:

```bash
python -m app.main decisions
```

Inspect run statistics:

```bash
python -m app.main runs
```

## Idempotency demonstration

Run the exact same crawl twice:

```bash
python -m app.main crawl --url https://books.toscrape.com/ --max-pages 10
python -m app.main crawl --url https://books.toscrape.com/ --max-pages 10
python -m app.main pages
```

The second run may revisit pages, but the canonical URL UNIQUE constraint and content hash logic prevent duplicate catalogue rows.

The `visits` value increases when an existing canonical URL is revisited.

## API

Start the API:

```bash
uvicorn app.api:app --reload
```

Open:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/pages
http://127.0.0.1:8000/decisions
http://127.0.0.1:8000/runs
```

Trigger a crawl:

```bash
curl -X POST http://127.0.0.1:8000/crawl
```

## Engineering decisions

### Dynamic scheduling
There is no fixed URL list or sitemap. Each page can add new URLs to the frontier. URLs not yet in the database are prioritised.

### Idempotency
The database has `canonical_url UNIQUE`. Existing URLs are updated rather than inserted.

### Content deduplication
Extracted meaningful text is hashed with SHA-256. A different URL with the same fingerprint is logged as duplicate content and skipped.

### URL variations
Fragments are removed, host/path are normalised, tracking parameters are removed, and query parameters are sorted.

### Redirects
Requests follows redirects. The final URL is canonicalised and the redirect is recorded in the decision log.

### Observable reasoning
Every major action is stored with a reason in the `decisions` table. This is what you should show in the 3-minute video.

## Responsible crawling

Only crawl public pages you are permitted to access. Keep the request rate low and follow applicable site terms and robots policies.

## Future improvements

- robots.txt and crawl-delay support
- retry/backoff
- persistent URL frontier
- stronger near-duplicate detection
- unit/integration tests
- asynchronous crawling with concurrency limits
- richer extractors for news/products/docs
- optional LLM-assisted structured extraction with schema validation
- PostgreSQL deployment and a dashboard
