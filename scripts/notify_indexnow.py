#!/usr/bin/env python3
"""Submit every sitemap URL to IndexNow after a successful Pages deploy.

Reads dist/sitemap.xml, POSTs one JSON batch to api.indexnow.org, and prints
the HTTP status. A non-2xx response, or any request error, is a warning.
This script always exits 0 so a search-engine ping cannot fail the deploy.
"""
import json
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

SITEMAP = Path("dist/sitemap.xml")
ENDPOINT = "https://api.indexnow.org/indexnow"
HOST = "sheepinboots.github.io"
KEY = "52237a276970019be653b2921724b15c"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"


def warn(message):
    print(f"::warning::{message}")


def sitemap_urls(path):
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    urls = []
    seen = set()
    for el in root.iter():
        if el.tag != "loc" and not el.tag.endswith("}loc"):
            continue
        url = (el.text or "").strip()
        if url and url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def main():
    if not SITEMAP.is_file():
        warn(f"IndexNow skipped: {SITEMAP} not found")
        return 0
    try:
        urls = sitemap_urls(SITEMAP)
    except ET.ParseError as exc:
        warn(f"IndexNow skipped: could not parse {SITEMAP} ({exc})")
        return 0
    if not urls:
        warn("IndexNow skipped: sitemap contained no URLs")
        return 0

    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            status = resp.status
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        status = exc.code
        body = exc.read().decode("utf-8", errors="replace")
    except Exception as exc:
        warn(f"IndexNow request failed: {exc}")
        return 0

    print(f"IndexNow HTTP {status}")
    print(f"Submitted {len(urls)} URL(s)")
    for url in urls:
        print(f"  {url}")
    if body.strip():
        print(body[:1000])
    if status < 200 or status >= 300:
        warn(f"IndexNow returned HTTP {status}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        warn(f"IndexNow failed: {exc}")
        sys.exit(0)
