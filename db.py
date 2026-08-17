import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_url TEXT NOT NULL UNIQUE,
    source_url TEXT NOT NULL,
    final_url TEXT NOT NULL,
    title TEXT,
    summary TEXT,
    content_hash TEXT NOT NULL,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    visits INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS crawl_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    seed_url TEXT NOT NULL,
    pages_fetched INTEGER NOT NULL DEFAULT 0,
    pages_added INTEGER NOT NULL DEFAULT 0,
    pages_updated INTEGER NOT NULL DEFAULT 0,
    pages_skipped INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    action TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES crawl_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_pages_hash ON pages(content_hash);
CREATE INDEX IF NOT EXISTS idx_decisions_run ON decisions(run_id);
"""

@contextmanager
def connect():
    Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with connect() as conn:
        conn.executescript(SCHEMA)

def create_run(seed_url: str, started_at: str) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO crawl_runs(started_at, seed_url) VALUES (?, ?)",
            (started_at, seed_url),
        )
        return int(cur.lastrowid)

def finish_run(run_id: int, finished_at: str, stats: dict):
    with connect() as conn:
        conn.execute(
            """UPDATE crawl_runs
               SET finished_at=?, pages_fetched=?, pages_added=?,
                   pages_updated=?, pages_skipped=?
               WHERE id=?""",
            (
                finished_at, stats["fetched"], stats["added"],
                stats["updated"], stats["skipped"], run_id
            ),
        )

def get_page(canonical_url: str):
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM pages WHERE canonical_url=?",
            (canonical_url,),
        ).fetchone()

def find_by_hash(content_hash: str):
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM pages WHERE content_hash=? LIMIT 1",
            (content_hash,),
        ).fetchone()

def upsert_page(canonical_url, source_url, final_url, title,
                summary, content_hash, now):
    existing = get_page(canonical_url)
    if existing:
        with connect() as conn:
            conn.execute(
                """UPDATE pages
                   SET source_url=?, final_url=?, title=?, summary=?,
                       content_hash=?, last_seen_at=?, visits=visits+1
                   WHERE canonical_url=?""",
                (source_url, final_url, title, summary,
                 content_hash, now, canonical_url),
            )
        return "updated"

    with connect() as conn:
        conn.execute(
            """INSERT INTO pages
               (canonical_url, source_url, final_url, title, summary,
                content_hash, first_seen_at, last_seen_at, visits)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)""",
            (canonical_url, source_url, final_url, title, summary,
             content_hash, now, now),
        )
    return "added"

def add_decision(run_id, url, action, reason, now):
    with connect() as conn:
        conn.execute(
            """INSERT INTO decisions(run_id, url, action, reason, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (run_id, url, action, reason, now),
        )

def list_pages(limit=100):
    with connect() as conn:
        return conn.execute(
            """SELECT id, canonical_url, title, summary, first_seen_at,
                      last_seen_at, visits
               FROM pages ORDER BY id DESC LIMIT ?""",
            (limit,),
        ).fetchall()

def list_decisions(run_id=None, limit=100):
    with connect() as conn:
        if run_id is None:
            return conn.execute(
                "SELECT * FROM decisions ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return conn.execute(
            """SELECT * FROM decisions
               WHERE run_id=? ORDER BY id DESC LIMIT ?""",
            (run_id, limit),
        ).fetchall()

def list_runs(limit=20):
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM crawl_runs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
