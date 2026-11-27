"""Per-page lastmod from content hashes, not from the catalog check date.

data/page_dates.json stores each page's first-published date, lastmod, and a hash
of the rendered HTML with volatile date fields stripped out. A page's dateModified,
sitemap lastmod, and visible "Last updated YYYY-MM-DD." line advance only when that
hash changes. The sitewide footer "Data last checked" and per-row checked dates stay
as source-check records and do not move lastmod.

On a first run (no hash yet), the stored lastmod is kept and only the hash is added,
so existing pages are not reset to today.
"""
import hashlib
import json
import os
import re

ISO = r"\d{4}-\d{2}-\d{2}"
MONTH = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
    r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|"
    r"Nov(?:ember)?|Dec(?:ember)?)"
)
DAY = rf"(?:{ISO}|{MONTH} \d{{1,2}}, \d{{4}})"
# Optional "7:20 PM ET (4:20 PM PT)" after a day label.
TIME = r"(?:, \d{1,2}:\d{2} [AP]M ET \(\d{1,2}:\d{2} [AP]M PT\))?"

# Page-chrome "Last updated 2026-11-27." — not vendor quotes, which use a comma
# ("Last updated 2026-11-27, US dollars") or a month name ("Last updated Apr 17, 2026").
PAGE_UPDATED = re.compile(rf"(Last updated )({ISO})(\.)")

_PAGE_TYPES = {"WebPage", "Article", "BlogPosting", "NewsArticle", "ItemPage"}
_CACHE = None


def dates_path(root):
    return os.path.join(root, "data", "page_dates.json")


def _entry(value):
    if isinstance(value, str):
        return {"published": value, "modified": None, "hash": None}
    if not isinstance(value, dict):
        return {"published": None, "modified": None, "hash": None}
    return {
        "published": value.get("published"),
        "modified": value.get("modified"),
        "hash": value.get("hash"),
    }


def load(root):
    global _CACHE
    if _CACHE is not None and _CACHE[0] == root:
        return _CACHE[1]
    path = dates_path(root)
    raw = json.load(open(path, encoding="utf-8")) if os.path.isfile(path) else {}
    data = {k: _entry(v) for k, v in raw.items()}
    _CACHE = (root, data)
    return data


def invalidate():
    global _CACHE
    _CACHE = None


def save(root, data):
    out = {}
    for path in sorted(data):
        rec = _entry(data[path])
        item = {}
        if rec["published"]:
            item["published"] = rec["published"]
        if rec["modified"]:
            item["modified"] = rec["modified"]
        if rec["hash"]:
            item["hash"] = rec["hash"]
        out[path] = item
    with open(dates_path(root), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
        f.write("\n")
    invalidate()
    load(root)


def published(root, path, fallback=None):
    rec = load(root).get(path) or {}
    return rec.get("published") or fallback


def modified(root, path, fallback=None):
    rec = load(root).get(path) or {}
    return rec.get("modified") or fallback


def _canonicalize_ld(html):
    """Parse JSON-LD blocks and dump them in a stable form so formatting is not a content change."""
    pat = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)

    def canon(m):
        try:
            obj = json.loads(m.group(1))
        except json.JSONDecodeError:
            return m.group(0)
        body = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return f'<script type="application/ld+json">{body}</script>'

    return pat.sub(canon, html)


def strip_volatile(html):
    """Remove check/update/lastmod stamps so a re-check alone does not change the hash."""
    html = _canonicalize_ld(html)
    html = re.sub(rf'"(dateModified|datePublished|temporalCoverage)":\s*"{ISO}"', r'"\1":""', html)
    html = re.sub(rf"Data last checked {ISO}", "Data last checked", html)
    html = re.sub(rf"Last full check {ISO}", "Last full check", html)
    html = re.sub(rf"(?i)Last checked {DAY}{TIME}\.?", "Last checked", html)
    html = re.sub(rf"(?i)(?<![A-Za-z])Checked {DAY}{TIME}", "Checked", html)
    html = re.sub(rf"(?i)API prices last checked {DAY}{TIME}", "API prices last checked", html)
    html = re.sub(rf"<br>{ISO}(?=</td>)", "<br>", html)
    html = re.sub(rf"[Pp]ublished on {DAY}", "published on", html)
    html = re.sub(rf"(?i)as of {DAY}", "as of", html)
    html = re.sub(rf"Deals ending by {DAY}", "Deals ending by", html)
    html = re.sub(rf"oldest row check on this page is {DAY}", "oldest row check on this page is", html)
    html = PAGE_UPDATED.sub(r"\1\3", html)
    return html


def content_hash(html):
    return hashlib.sha256(strip_volatile(html).encode("utf-8")).hexdigest()


def _ld_script(obj):
    raw = json.dumps(obj, ensure_ascii=False).replace("<", "\\u003c")
    return f'<script type="application/ld+json">{raw}</script>'


def _types(value):
    if isinstance(value, list):
        return set(value)
    if isinstance(value, str):
        return {value}
    return set()


def _walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v)


def set_page_modified(html, day, ld_script=None):
    """Write dateModified on page-level JSON-LD nodes and the visible Last updated line."""
    write_ld = ld_script or _ld_script
    pat = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)

    def fix(m):
        try:
            obj = json.loads(m.group(1))
        except json.JSONDecodeError:
            return m.group(0)
        changed = False
        for node in _walk(obj):
            if _types(node.get("@type")) & _PAGE_TYPES and "dateModified" in node:
                if node.get("dateModified") != day:
                    node["dateModified"] = day
                    changed = True
        if not changed:
            return m.group(0)
        return write_ld(obj)

    html = pat.sub(fix, html)
    html = PAGE_UPDATED.sub(rf"\g<1>{day}\3", html)
    return html


def set_sitemap_lastmod(xml, site_url, path, day):
    loc = f"<loc>{site_url}{path}</loc>"
    return re.sub(
        re.escape(loc) + rf"<lastmod>{ISO}</lastmod>",
        f"{loc}<lastmod>{day}</lastmod>",
        xml,
        count=1,
    )


def html_path(dist, path):
    return os.path.join(dist, path.lstrip("/"), "index.html")


def apply_to_dist(root, dist, urls, today, site_url="https://vidfare.com", ld_script=None, sitemap_lastmod=None):
    """Hash each built page, advance lastmod only when the hash is new, and write the dates back."""
    data = load(root)
    sitemap_fp = os.path.join(dist, "sitemap.xml")
    sitemap = open(sitemap_fp, encoding="utf-8").read() if os.path.isfile(sitemap_fp) else ""
    changed = False
    for path in urls:
        fp = html_path(dist, path)
        if not os.path.isfile(fp):
            continue
        src = open(fp, encoding="utf-8").read()
        digest = content_hash(src)
        rec = data.get(path) or {"published": None, "modified": None, "hash": None}
        prev_hash = rec.get("hash")
        prev_mod = rec.get("modified")
        if not rec.get("published"):
            rec["published"] = today
            changed = True
        if prev_hash is None:
            # First time we see this page: keep the seeded lastmod, or today's date for a new page.
            rec["modified"] = prev_mod or today
            rec["hash"] = digest
            changed = True
        elif prev_hash != digest:
            rec["modified"] = today
            rec["hash"] = digest
            changed = True
        day = rec["modified"]
        new = set_page_modified(src, day, ld_script=ld_script)
        if new != src:
            open(fp, "w", encoding="utf-8").write(new)
            src = new
        # Store the hash of the written file so a JSON-LD reformat cannot
        # look like a content change on the next build.
        final_hash = content_hash(src)
        if rec.get("hash") != final_hash:
            rec["hash"] = final_hash
            changed = True
        data[path] = rec
        if sitemap_lastmod is not None:
            sitemap_lastmod[path] = day
        if sitemap:
            updated = set_sitemap_lastmod(sitemap, site_url, path, day)
            if updated != sitemap:
                sitemap = updated
    if sitemap:
        open(sitemap_fp, "w", encoding="utf-8").write(sitemap)
    if changed:
        save(root, data)
    else:
        # Still refresh the module cache so later readers see in-memory lastmod.
        invalidate()
        global _CACHE
        _CACHE = (root, data)
    return data


def apply(g, urls):
    """Hook for build_site.py: stamp dist, sitemap, and SITEMAP_LASTMOD from content hashes."""
    return apply_to_dist(
        g["ROOT"],
        g["DIST"],
        urls,
        g["TODAY"],
        site_url=g["SITE_URL"],
        ld_script=g["ld_script"],
        sitemap_lastmod=g["SITEMAP_LASTMOD"],
    )
