#!/usr/bin/env python3
"""The Kling AI pricing guide agrees with prices.json and today's official figures.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_kling_pricing_guide.py
"""
import html
import json
import os
import re
import sys
from decimal import Decimal, ROUND_HALF_UP

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kling_pricing_guide

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = kling_pricing_guide.PATH
PAGE = os.path.join(ROOT, "dist", "guides", "kling-ai-pricing", "index.html")


def rate_money(v):
    places = 3 if abs(Decimal(str(v))) >= Decimal("0.1") else 4
    q = Decimal("1").scaleb(-places)
    n = Decimal(str(v)).quantize(q, rounding=ROUND_HALF_UP)
    text = f"{abs(n):.{places}f}"
    whole, frac = text.split(".")
    frac = frac.rstrip("0")
    if len(frac) < 2:
        frac = frac.ljust(2, "0")
    return f"${whole}.{frac}"


def main():
    if not os.path.isfile(PAGE):
        raise SystemExit(f"{PAGE} is missing; build the site first")
    raw = open(PAGE, encoding="utf-8").read()
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    text = re.sub(r"\s+", " ", text)
    db = json.load(open(os.path.join(ROOT, "data", "prices.json"), encoding="utf-8"))
    errors = []

    title = html.unescape(re.search(r"<title>(.*?)</title>", raw).group(1))
    desc = html.unescape(re.search(r'<meta name="description" content="(.*?)"', raw).group(1))
    if len(title) > 60:
        errors.append(f"title is {len(title)} characters: {title}")
    if len(desc) > 160:
        errors.append(f"description is {len(desc)} characters: {desc}")
    if f'<link rel="canonical" href="https://vidfare.com{PATH}">' not in raw:
        errors.append("canonical")
    if "sora" in text.lower() or "sora" in raw.lower():
        errors.append("names Sora")

    kling_rows = [r for r in db["rows"] if r.get("model") == "kling-3-0"]
    if not kling_rows:
        errors.append("no Kling 3.0 rows in prices.json")
    for r in kling_rows:
        money = rate_money(r["usd_per_second"])
        if money + "/s" not in text and money not in text:
            errors.append(f"{r['id']} rate {money} missing")

    official = [r for r in kling_rows if r.get("platform") == "Kling API" and r.get("id") == "r059"]
    if not official:
        errors.append("catalog is missing official Kling API 720p no-audio row r059")
    else:
        if rate_money(official[0]["usd_per_second"]) not in desc:
            errors.append("description missing official 720p no-audio API rate")

    haystack = (text + " " + raw).lower()
    for needle in (
        "Standard",
        "Pro",
        "Premier",
        "Ultra+",
        "Business",
        "660",
        "3,000",
        "8,000",
        "18,000",
        "57,000",
        "$6.99",
        "$8.80",
        "$10",
        "$25.99",
        "$32.56",
        "$79.20",
        "$293.04",
        "$0.084",
        "$0.126",
        "$0.84",
        "$1.26",
        "without audio",
        "with audio",
        "unknown",
        "Affiliate links never change this price order",
        "Confirmed",
        "Unknown",
        "Kling 3.0",
        "fal",
        "Runway",
        "Higgsfield",
        "Magnific",
        "Krea",
        "Replicate",
        "2 years",
        kling_pricing_guide.KLING_PLANS,
        kling_pricing_guide.KLING_API,
    ):
        if needle.lower() not in haystack:
            errors.append(f"guide needle missing: {needle}")

    for question in (
        kling_pricing_guide.QUESTION,
        kling_pricing_guide.PHRASE,
        "What do official Kling plans cost right now?",
        "What do official Kling credits buy per second or per clip?",
        "What does the official Kling API charge for Kling 3.0?",
        "When is pay-as-you-go or a plan elsewhere cheaper?",
        "What is confirmed, and what is not?",
        "How do we calculate this?",
    ):
        if question not in text:
            errors.append(f"visible text missing: {question}")

    faq_raw = ""
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S):
        faq_raw += m.group(1).lower()
    for bad in ("subscribe", "newsletter", "buttondown"):
        if bad in faq_raw:
            errors.append(f"FAQ JSON-LD contains {bad}")

    if 'id="newsletter"' not in raw:
        errors.append("newsletter signup box missing from end of guide")
    if "fpr=emmanuel-bbfe0e" not in raw:
        errors.append("Higgsfield affiliate fpr missing")

    sitemap = open(os.path.join(ROOT, "dist", "sitemap.xml"), encoding="utf-8").read()
    if f"<loc>https://vidfare.com{PATH}</loc>" not in sitemap:
        errors.append("sitemap")
    llms = open(os.path.join(ROOT, "dist", "llms.txt"), encoding="utf-8").read()
    if "https://vidfare.com/guides/kling-ai-pricing/" not in llms:
        errors.append("llms.txt is missing the guide")
    indexnow = open(os.path.join(ROOT, "scripts", "notify_indexnow.py"), encoding="utf-8").read()
    if "https://vidfare.com/guides/kling-ai-pricing/" not in indexnow:
        errors.append("IndexNow GUIDE_URLS is missing the guide")
    for rel in (
        "guides/index.html",
        "index.html",
        "models/kling-3-0/index.html",
        "guides/cheapest-ai-video-generator/index.html",
        "guides/is-higgsfield-worth-it/index.html",
        "guides/higgsfield-pricing/index.html",
    ):
        page = open(os.path.join(ROOT, "dist", rel), encoding="utf-8").read()
        if f'href="{PATH}"' not in page:
            errors.append(f"{rel} does not link the guide")
    guides = open(os.path.join(ROOT, "dist", "guides", "index.html"), encoding="utf-8").read()
    if "comparisons built from the same price rows" not in guides:
        errors.append("guides index is missing the comparisons lead")
    if "Twelve comparisons" not in guides and "twelve comparisons" not in guides:
        errors.append("guides index count text was not updated to Twelve")

    if errors:
        raise SystemExit("kling pricing guide:\n- " + "\n- ".join(errors))
    print("ok kling pricing guide")


if __name__ == "__main__":
    main()
