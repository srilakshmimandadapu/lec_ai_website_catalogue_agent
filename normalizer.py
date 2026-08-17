from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term",
    "utm_content", "gclid", "fbclid", "ref", "source"
}

def canonicalize(base_url: str, href: str):
    if not href:
        return None
    absolute = urljoin(base_url, href)
    parsed = urlparse(absolute)
    if parsed.scheme not in {"http", "https"}:
        return None
    host = (parsed.hostname or "").lower()
    if not host:
        return None
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    query_items = [
        (k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in TRACKING_PARAMS
    ]
    query = urlencode(sorted(query_items))
    return urlunparse((
        parsed.scheme.lower(), host, path, "", query, ""
    ))
