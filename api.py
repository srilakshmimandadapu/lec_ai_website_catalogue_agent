from fastapi import FastAPI

from .agent import crawl
from .config import settings
from .db import init_db, list_decisions, list_pages, list_runs

app = FastAPI(
    title="LEC AI Website Catalogue Agent",
    version="1.0.0"
)

init_db()

@app.get("/")
def root():
    return {
        "name": "LEC AI Website Catalogue Agent",
        "seed_url": settings.seed_url,
        "endpoints": ["/health", "/pages", "/decisions", "/runs"]
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/crawl")
def run_crawl():
    return crawl()

@app.get("/pages")
def pages(limit: int = 100):
    return [dict(row) for row in list_pages(limit)]

@app.get("/decisions")
def decisions(run_id: int | None = None, limit: int = 100):
    return [dict(row) for row in list_decisions(run_id, limit)]

@app.get("/runs")
def runs(limit: int = 20):
    return [dict(row) for row in list_runs(limit)]
