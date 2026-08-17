import hashlib
import re
from bs4 import BeautifulSoup

def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()

def extract_page(html: str, final_url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    title = clean_text(
        soup.title.get_text(" ", strip=True)
    ) if soup.title else ""

    headings = [
        clean_text(h.get_text(" ", strip=True))
        for h in soup.find_all(["h1", "h2", "h3"])
    ]
    paragraphs = [
        clean_text(p.get_text(" ", strip=True))
        for p in soup.find_all("p")
    ]
    meaningful = [x for x in headings + paragraphs if x]
    body_text = clean_text(" ".join(meaningful))
    if not body_text:
        body_text = clean_text(soup.get_text(" ", strip=True))

    summary = body_text[:500]
    content_hash = hashlib.sha256(
        body_text.encode("utf-8", errors="ignore")
    ).hexdigest()

    return {
        "title": title[:500],
        "summary": summary,
        "content_hash": content_hash,
        "links": [a["href"] for a in soup.find_all("a", href=True)],
        "final_url": final_url,
    }
