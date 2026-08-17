import argparse
import json

from .agent import crawl
from .config import settings
from .db import init_db, list_decisions, list_pages, list_runs

def print_rows(rows):
    for row in rows:
        print(dict(row))

def main():
    parser = argparse.ArgumentParser(
        description="LEC AI website catalogue agent"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db", help="Create SQLite tables")

    crawl_cmd = sub.add_parser("crawl", help="Run the crawler")
    crawl_cmd.add_argument("--url", default=settings.seed_url)
    crawl_cmd.add_argument("--max-pages", type=int, default=settings.max_pages)

    sub.add_parser("pages", help="Show catalogue entries")

    decisions_cmd = sub.add_parser(
        "decisions", help="Show observable agent decisions"
    )
    decisions_cmd.add_argument("--run-id", type=int, default=None)

    sub.add_parser("runs", help="Show crawl runs")

    args = parser.parse_args()

    if args.command == "init-db":
        init_db()
        print("Database initialized.")
    elif args.command == "crawl":
        print(json.dumps(
            crawl(args.url, args.max_pages), indent=2
        ))
    elif args.command == "pages":
        print_rows(list_pages())
    elif args.command == "decisions":
        print_rows(list_decisions(args.run_id))
    elif args.command == "runs":
        print_rows(list_runs())

if __name__ == "__main__":
    main()
