# 3-Minute Presentation Script

## 0:00–0:20 — Problem

"Hi, this is my solution for the LEC AI Engineering Intern build assessment.

The goal is to crawl a public website, dynamically discover pages, extract structured data, and maintain a deduplicated local catalogue even when the agent is run multiple times."

## 0:20–0:45 — Architecture

"The implementation is intentionally small and reliable.

Requests handles HTTP fetching, BeautifulSoup extracts page content and links, SQLite provides durable state and database-level uniqueness, and a queue acts as the agent's frontier.

The crawler is deterministic, so every decision can be inspected and defended."

## 0:45–1:20 — First run

"I'll run the agent against the public Books to Scrape demo website.

The agent starts with one seed URL. It extracts links from the page and dynamically decides what to visit next. It does not use a fixed URL list or sitemap.

For every page, I store the canonical URL, final URL after redirects, title, summary, timestamps and a SHA-256 content fingerprint."

## 1:20–1:55 — Deduplication

"The important part is idempotency.

Before inserting a page, I canonicalise the URL and check the database. The canonical URL has a UNIQUE constraint, so the database itself prevents duplicate rows.

I also compare content fingerprints. If two different URLs contain the same extracted content, the second one is skipped.

If an existing page is seen again, the existing row is updated and its visit count increases instead of creating another row."

## 1:55–2:25 — Observable reasoning

"The assessment asks for observable reasoning, so I store every important decision.

For example, the trace can say that a URL was queued because it was same-site and unseen, skipped because it was outside the seed hostname, redirected to a canonical URL, or updated because the canonical URL already existed.

This makes the agent's behaviour easy to inspect during review."

## 2:25–2:50 — Repeat-run demonstration

"Now I run the same command again.

The second run can revisit known pages for change detection, but it does not create duplicate catalogue entries. The database row count stays deduplicated while the visit count shows that the page was actually revisited."

## 2:50–3:00 — Close

"The main trade-off I made was prioritising a small working system over a large framework. With more time I would add robots.txt handling, retries and backoff, tests, asynchronous crawling, richer extraction, and optional LLM-based structured extraction with validation."

# Q&A Cheat Sheet

### Why no LLM?

"The core task is crawling, state management and deduplication. An LLM is not required for those guarantees. I kept the critical path deterministic and observable. An LLM can be added later for richer schema extraction without changing the database or deduplication layer."

### Why SQLite?

"It is local, durable, transactional and easy to reproduce for an assessment. The same repository can later move to PostgreSQL with minimal changes to the data-access layer."

### How do you handle changed content?

"The canonical URL remains the same. The content hash is recalculated and the existing catalogue row is updated rather than inserted again."

### How do you handle URL variations?

"Fragments are removed, hosts and paths are normalised, common tracking parameters are removed, and query parameters are sorted."

### What happens if two URLs contain identical content?

"The content hash matches an existing entry, so the second URL is logged as a duplicate-content skip rather than inserted."

### What happens on a redirect?

"The HTTP client follows the redirect, the final URL is canonicalised, and the redirect decision is recorded."

### What would you improve?

"Robots.txt support, stronger retry/backoff, persistent frontier state, better content extraction per website type, tests, concurrency controls, and optional LLM extraction with schema validation."
