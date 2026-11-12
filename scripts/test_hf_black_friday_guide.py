#!/usr/bin/env python3
"""Check the Higgsfield Black Friday guide against deals.json and prices.json."""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hf_black_friday_guide

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "dist", "guides", "higgsfield-black-friday", "index.html")
PATH = hf_black_friday_guide.PATH


def main():
    errors = []
    if not os.path.isfile(PAGE):
        raise SystemExit(f"missing {PAGE}; build the site first")
    raw = open(PAGE, encoding="utf-8").read()
    text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"\s+", " ", text)

    if f'<link rel="canonical" href="https://vidfare.com{PATH}">' not in raw:
        errors.append("canonical")
    if "Sora" in raw or "sora" in raw:
        errors.append("page names Sora")

    title = re.search(r"<title>(.*?)</title>", raw)
    desc = re.search(r'<meta name="description" content="(.*?)"', raw)
    if not title or len(re.sub(r"&[a-z]+;", "x", title.group(1))) > 60:
        errors.append(f"title missing or over 60: {title.group(1) if title else None}")
    if not desc or len(re.sub(r"&[a-z]+;", "x", desc.group(1))) > 160:
        errors.append(f"description missing or over 160: {desc.group(1) if desc else None}")
    if desc and "No Black Friday 2026 sale is up yet" not in desc.group(1).replace("&amp;", "&"):
        # html escaped apostrophes etc.
        if "No Black Friday 2026 sale is up yet" not in desc.group(1):
            errors.append("description does not say no Black Friday sale is up yet")

    if "has not posted a Black Friday 2026 sale" not in text and "has not posted a Black Friday 2026 sale" not in raw:
        if "not posted a Black Friday 2026 sale" not in text:
            errors.append("guide does not state that no Black Friday 2026 sale is posted")

    doc = json.load(open(os.path.join(ROOT, "data", "deals.json"), encoding="utf-8"))
    by = {d["id"]: d for d in doc["deals"]}
    for did in (
        "hf-plus-annual",
        "hf-ultra-annual",
        "hf-plus-monthly-first",
        "hf-ultra-monthly-first",
        "hf-ultra-6k-annual",
        "hf-ultra-9k-annual",
        "hf-ultra-6k-monthly-first",
        "hf-ultra-9k-monthly-first",
    ):
        d = by.get(did)
        if not d:
            errors.append(f"missing deal {did}")
            continue
        if d.get("status") == "live" and d.get("price_after") is not None:
            needle = f"${d['price_after']:g}"
            if needle not in text and needle not in raw:
                errors.append(f"{did} price {needle} missing from the guide")

    db = json.load(open(os.path.join(ROOT, "data", "prices.json"), encoding="utf-8"))
    # Catalog Ultra 3K annual Wan 3.0 Prime 480p and Wan 3.0 480p must appear.
    def rate(v):
        # Same 4-decimal-under-0.10 rule as rate_money, minus the $ and /s we search loosely.
        from decimal import Decimal, ROUND_HALF_UP
        places = 3 if abs(Decimal(str(v))) >= Decimal("0.1") else 4
        q = Decimal("1").scaleb(-places)
        n = format(Decimal(str(v)).quantize(q, rounding=ROUND_HALF_UP), "f")
        if "." in n:
            n = n.rstrip("0").rstrip(".")
        return n

    for rid in ("r081", "r096", "r111", "r123"):
        row = next(r for r in db["rows"] if r["id"] == rid)
        n = rate(row["usd_per_second"])
        if n not in text and n not in raw:
            errors.append(f"catalog {rid} rate {n} missing")

    # Computed Ultra 9K annual Wan 3.0 Prime 480p from the deal + catalog credits.
    d9 = by.get("hf-ultra-9k-annual")
    sample = next(r for r in db["rows"] if r["id"] == "r081")
    if d9 and d9.get("price_after") and d9.get("credits_month") and sample.get("credits_per_clip"):
        computed = (
            d9["price_after"] / d9["credits_month"]
            * sample["credits_per_clip"]
            / sample["clip_seconds"]
        )
        n = rate(computed)
        if n not in text and n not in raw:
            errors.append(f"computed Ultra 9K annual rate {n} missing")

    if 'href="https://higgsfield.ai/pricing?fpr=emmanuel-bbfe0e"' not in raw:
        errors.append("pricing page affiliate link missing")
    if 'rel="sponsored nofollow noopener"' not in raw:
        errors.append("affiliate rel missing")

    sitemap = open(os.path.join(ROOT, "dist", "sitemap.xml"), encoding="utf-8").read()
    if f"<loc>https://vidfare.com{PATH}</loc>" not in sitemap:
        errors.append("sitemap")
    for rel in ("guides/index.html", "deals/black-friday/index.html", "deals/index.html"):
        page = open(os.path.join(ROOT, "dist", rel), encoding="utf-8").read()
        if f'href="{PATH}"' not in page:
            errors.append(f"{rel} does not link the guide")

    if "Seven" not in open(os.path.join(ROOT, "dist", "guides", "index.html"), encoding="utf-8").read():
        # count word is used in the index heading
        idx = open(os.path.join(ROOT, "dist", "guides", "index.html"), encoding="utf-8").read()
        if "Seven comparisons" not in idx and "7 comparisons" not in idx:
            errors.append("guides index does not say Seven comparisons")

    if errors:
        raise SystemExit("higgsfield black friday guide check failed:\n- " + "\n- ".join(errors))
    print("ok higgsfield black friday guide")


if __name__ == "__main__":
    main()
