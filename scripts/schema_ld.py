"""Shared JSON-LD builders: price offers per shown row, and page dates.

Every offer comes from a row that is shown on the same page, so the price in the
markup is the same string the reader sees (rate_money without the dollar sign).
"""
import json
import os

import page_dates as page_dates_mod


def page_dates(root):
    """First-published dates from data/page_dates.json (written by gen_page_dates.py)."""
    return {path: rec.get("published") for path, rec in page_dates_mod.load(root).items()}


def date_published(g, path):
    return page_dates_mod.published(g["ROOT"], path, g["TODAY"])


def date_modified(g, path):
    """Prefer the stored content-hash lastmod; fall back to a first-pass sitemap date."""
    stored = page_dates_mod.modified(g["ROOT"], path)
    if stored:
        return stored
    return g["SITEMAP_LASTMOD"].get(path) or g["LAST"]


def row_offer(g, r, fmt="rate_money"):
    name = g["models"].get(r["model"], {}).get("name", r["model"])
    res = g["shown_resolution"](r)
    tier = g["shown_tier"](r)
    price = g[fmt](r["usd_per_second"]).lstrip("$")
    desc = (f"Plan or tier: {tier}. Resolution: {res}. Audio: {g['audio_phrase'](r)}. "
            f"Variant: {r.get('variant') or 'not stated'}. Checked {r.get('checked')}.")
    offer = {
        "@type": "Offer",
        "name": f"{name} on {r['platform']}",
        "itemOffered": {"@type": "Service", "name": f"{name} ({res}) video generation"},
        "seller": {"@type": "Organization", "name": r["platform"]},
        "price": price,
        "priceCurrency": "USD",
        "priceSpecification": {
            "@type": "UnitPriceSpecification",
            "price": price,
            "priceCurrency": "USD",
            "unitText": "second of video",
        },
        "description": desc,
    }
    if r.get("source_url"):
        offer["url"] = r["source_url"]
    return offer


def offer_list(g, path, name, rows, fmt="rate_money"):
    """ItemList of Offers, one per shown row, in the page's order. Duplicate rows are dropped."""
    seen, items = set(), []
    for r in rows:
        if not r or r.get("usd_per_second") is None:
            continue
        key = r.get("id") or (r["model"], r["platform"], r.get("variant"), r.get("resolution"), r.get("plan"))
        if key in seen:
            continue
        seen.add(key)
        items.append(row_offer(g, r, fmt))
    if not items:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": name,
        "url": g["SITE_URL"] + path,
        "numberOfItems": len(items),
        "itemListElement": [
            {"@type": "ListItem", "position": i, "item": o} for i, o in enumerate(items, 1)
        ],
    }


def _walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from _walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from _walk(v)


def stamp_dates(g, path, html, title, desc):
    """Add datePublished/dateModified to the page's WebPage node, or add a WebPage node."""
    import re
    pub, mod = date_published(g, path), date_modified(g, path)
    pat = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
    done = False

    def fix(m):
        nonlocal done
        obj = json.loads(m.group(1))
        changed = False
        for o in _walk(obj):
            t = o.get("@type")
            if t == "WebPage" or (isinstance(t, list) and "WebPage" in t):
                o.setdefault("datePublished", pub)
                o.setdefault("dateModified", mod)
                done = changed = True
        if not changed:
            return m.group(0)
        return g["ld_script"](obj)

    html = pat.sub(fix, html)
    if not done:
        node = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": title,
            "description": desc,
            "url": g["SITE_URL"] + path,
            "datePublished": pub,
            "dateModified": mod,
            "author": g["EDITOR_LD"],
            "publisher": {"@type": "Organization", "@id": g["ORG_ID"], "name": g["BRAND"], "url": g["SITE_URL"] + "/"},
        }
        tag = g["ld_script"](node)
        html = html.replace("</head>", tag + "</head>", 1) if "</head>" in html else tag + html
    return html
