#!/usr/bin/env python3
"""The Runway pricing guide agrees with prices.json and today's official figures.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_runway_pricing_guide.py
"""
import html
import json
import os
import re
import sys
from decimal import Decimal, ROUND_HALF_UP

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import runway_pricing_guide

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = runway_pricing_guide.PATH
PAGE = os.path.join(ROOT, "dist", "guides", "runway-pricing", "index.html")


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

    runway_rows = [r for r in db["rows"] if r.get("platform") == "Runway API"]
    if not runway_rows:
        errors.append("no Runway API rows in prices.json")
    for r in runway_rows:
        money = rate_money(r["usd_per_second"])
        if money + "/s" not in text and money not in text:
            errors.append(f"{r['id']} rate {money} missing")

    turbo = [r for r in runway_rows if r.get("id") == "r047"]
    if not turbo:
        errors.append("catalog is missing official Gen-4 Turbo row r047")
    elif rate_money(turbo[0]["usd_per_second"]) not in desc:
        errors.append("description missing official Gen-4 Turbo API rate")

    haystack = (text + " " + raw).lower()
    for needle in (
        "Free",
        "Standard",
        "Pro",
        "Max",
        "Team",
        "Enterprise",
        "625",
        "2,250",
        "9,500",
        "6,900",
        "$15",
        "$12",
        "$35",
        "$28",
        "$95",
        "$76",
        "$69",
        "$55",
        "$0.05",
        "$0.12",
        "Gen-4.5",
        "Gen-4 Video Turbo",
        "Aleph 2.0",
        "Veo 3.1",
        "Explore Mode",
        "November 30",
        "relaxed",
        "unknown",
        "Affiliate links never change this price order",
        "Confirmed",
        "Unknown",
        runway_pricing_guide.RUNWAY_PLANS,
        runway_pricing_guide.RUNWAY_API,
        runway_pricing_guide.TEAM_PLAN,
        runway_pricing_guide.HELP_UNLIMITED_TO_MAX,
        runway_pricing_guide.HELP_MODE,
    ):
        if needle.lower() not in haystack:
            errors.append(f"guide needle missing: {needle}")

    for question in (
        runway_pricing_guide.QUESTION,
        runway_pricing_guide.PHRASE,
        "What do official Runway plans cost right now?",
        "What do credits buy per second, and what does that cost on each plan?",
        "What does the official Runway API charge?",
        "What does Unlimited's relaxed mode actually mean?",
        "When is a route elsewhere cheaper?",
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

    sitemap = open(os.path.join(ROOT, "dist", "sitemap.xml"), encoding="utf-8").read()
    if f"<loc>https://vidfare.com{PATH}</loc>" not in sitemap:
        errors.append("sitemap")
    llms = open(os.path.join(ROOT, "dist", "llms.txt"), encoding="utf-8").read()
    if "https://vidfare.com/guides/runway-pricing/" not in llms:
        errors.append("llms.txt is missing the guide")
    indexnow = open(os.path.join(ROOT, "scripts", "notify_indexnow.py"), encoding="utf-8").read()
    if "https://vidfare.com/guides/runway-pricing/" not in indexnow:
        errors.append("IndexNow GUIDE_URLS is missing the guide")
    for rel in (
        "guides/index.html",
        "index.html",
        "models/runway-gen-4/index.html",
        "guides/cheapest-ai-video-generator/index.html",
        "guides/kling-ai-pricing/index.html",
    ):
        page = open(os.path.join(ROOT, "dist", rel), encoding="utf-8").read()
        if f'href="{PATH}"' not in page:
            errors.append(f"{rel} does not link the guide")
    guides = open(os.path.join(ROOT, "dist", "guides", "index.html"), encoding="utf-8").read()
    if "comparisons built from the same price rows" not in guides:
        errors.append("guides index is missing the comparisons lead")
    if (
        "Sixteen comparisons" not in guides
        and "sixteen comparisons" not in guides
        and "Fifteen comparisons" not in guides
        and "fifteen comparisons" not in guides
        and "Fourteen comparisons" not in guides
        and "fourteen comparisons" not in guides
        and "Thirteen comparisons" not in guides
        and "thirteen comparisons" not in guides
    ):
        errors.append("guides index count text was not updated")

    if errors:
        raise SystemExit("runway pricing guide:\n- " + "\n- ".join(errors))
    print("ok runway pricing guide")


if __name__ == "__main__":
    main()
