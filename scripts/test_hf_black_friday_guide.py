#!/usr/bin/env python3
"""Check the Higgsfield Black Friday guide against prices.json and today's verified card prices."""
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
    desc_txt = (desc.group(1) if desc else "").replace("&amp;", "&")
    if "$33" not in desc_txt or "$50" not in desc_txt:
        errors.append("description does not name the $33 and $50 annual sale prices")
    if "unknown" not in desc_txt.lower():
        errors.append("description does not mark unknown facts as unknown")
    if "No Black Friday 2026 sale is up yet" in desc_txt or "has not posted a Black Friday 2026 sale" in text:
        errors.append("guide still says no Black Friday 2026 sale is posted")

    for needle in (
        "Black Friday 65% off",
        "$33",
        "$50",
        "$90",
        "$19",
        "$47",
        "$79",
        "billed yearly",
        "ended Nov 15",
        "11.11",
        "sale end date",
        "calculated at checkout",
        "audio not stated",
        "assuming every paid credit is used",
        "Ultra 9K annual card price was not verified",
        hf_black_friday_guide.CHECKED_WHEN,
        "id=\"newsletter\"",
    ):
        if needle not in text and needle not in raw:
            errors.append(f"missing needle: {needle}")

    db = json.load(open(os.path.join(ROOT, "data", "prices.json"), encoding="utf-8"))

    def rate(v):
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

    sample = next(r for r in db["rows"] if r["id"] == "r081")
    if sample.get("credits_per_clip") and sample.get("clip_seconds"):
        computed = (
            hf_black_friday_guide.ULTRA_6K_ANNUAL_MO
            / hf_black_friday_guide.ULTRA_6K_CREDITS
            * sample["credits_per_clip"]
            / sample["clip_seconds"]
        )
        n = rate(computed)
        if n not in text and n not in raw:
            errors.append(f"computed Ultra 6K annual rate {n} missing")

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

    idx = open(os.path.join(ROOT, "dist", "guides", "index.html"), encoding="utf-8").read()
    if "comparisons built from the same price rows" not in idx:
        errors.append("guides index is missing the comparisons lead")
    if "Plus annual at $33/mo" not in idx and "$33/mo" not in idx:
        errors.append("guides index blurb does not mention $33/mo")

    if errors:
        raise SystemExit("higgsfield black friday guide check failed:\n- " + "\n- ".join(errors))
    print("ok higgsfield black friday guide")


if __name__ == "__main__":
    main()
