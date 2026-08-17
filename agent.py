from collections import deque
from datetime import datetime, timezone
import time
from urllib.parse import urlparse

import requests

from .config import settings
from .db import (
    add_decision, create_run, finish_run, find_by_hash,
    get_page, init_db, upsert_page
)
from .extractor import extract_page
from .normalizer import canonicalize

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def same_site(url, seed_url):
    return (urlparse(url).hostname or "").lower() == (
        urlparse(seed_url).hostname or ""
    ).lower()

def crawl(seed_url=None, max_pages=None):
    init_db()
    seed_url = seed_url or settings.seed_url
    max_pages = max_pages or settings.max_pages

    seed = canonicalize(seed_url, seed_url)
    if not seed:
        raise ValueError("Invalid seed URL")

    run_id = create_run(seed, now_iso())
    queue = deque([seed])
    queued = {seed}
    visited_this_run = set()
    stats = {"fetched": 0, "added": 0, "updated": 0, "skipped": 0}

    session = requests.Session()
    session.headers.update({"User-Agent": settings.user_agent})

    while queue and stats["fetched"] < max_pages:
        current = queue.popleft()
        if current in visited_this_run:
            continue

        if not same_site(current, seed):
            add_decision(
                run_id, current, "skip",
                "Different hostname from the seed; crawl is same-site only.",
                now_iso()
            )
            stats["skipped"] += 1
            continue

        visited_this_run.add(current)
        add_decision(
            run_id, current, "visit",
            f"Selected dynamically from the frontier; "
            f"{len(queue)} URLs were waiting before fetch.",
            now_iso()
        )

        try:
            response = session.get(
                current, timeout=settings.request_timeout,
                allow_redirects=True
            )
            stats["fetched"] += 1
        except requests.RequestException as exc:
            add_decision(
                run_id, current, "error",
                f"Request failed: {type(exc).__name__}: {exc}",
                now_iso()
            )
            continue

        if response.status_code >= 400:
            add_decision(
                run_id, current, "skip",
                f"HTTP status {response.status_code}; not catalogued.",
                now_iso()
            )
            continue

        final_url = canonicalize(current, response.url) or current
        data = extract_page(response.text, final_url)

        if final_url != current:
            add_decision(
                run_id, current, "redirect",
                f"Server redirected to canonical URL {final_url}.",
                now_iso()
            )

        duplicate_content = find_by_hash(data["content_hash"])
        if duplicate_content and duplicate_content["canonical_url"] != final_url:
            add_decision(
                run_id, final_url, "skip",
                f"Content hash matches existing entry "
                f"{duplicate_content['canonical_url']}; duplicate avoided.",
                now_iso()
            )
            stats["skipped"] += 1
        else:
            action = upsert_page(
                canonical_url=final_url,
                source_url=current,
                final_url=final_url,
                title=data["title"],
                summary=data["summary"],
                content_hash=data["content_hash"],
                now=now_iso(),
            )
            stats[action] += 1
            reason = (
                "New canonical URL and content fingerprint."
                if action == "added"
                else
                "Existing canonical URL matched; row updated without a duplicate."
            )
            add_decision(run_id, final_url, action, reason, now_iso())

        for href in data["links"]:
            next_url = canonicalize(final_url, href)
            if not next_url or not same_site(next_url, seed):
                continue
            if next_url in visited_this_run or next_url in queued:
                continue

            if get_page(next_url) is None:
                queue.appendleft(next_url)
                reason = "Same-site and not yet in the catalogue; prioritised."
            else:
                queue.append(next_url)
                reason = "Known URL queued for change detection after unseen URLs."

            add_decision(run_id, next_url, "queue", reason, now_iso())
            queued.add(next_url)

        time.sleep(0.15)

    finish_run(run_id, now_iso(), stats)
    stats["run_id"] = run_id
    return stats
