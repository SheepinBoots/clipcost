#!/usr/bin/env python3
"""The best-AI-video-generator guide agrees with prices.json and today's AA figures.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_best_ai_video_guide.py
"""
import html
import json
import os
import re
import sys
from decimal import Decimal, ROUND_HALF_UP

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import best_ai_video_guide

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = best_ai_video_guide.PATH
PAGE = os.path.join(ROOT, "dist", "guides", "best-ai-video-generator", "index.html")


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

    for rid in (
        best_ai_video_guide.ROW_WAN,
        best_ai_video_guide.ROW_PRIME,
        best_ai_video_guide.ROW_KLING,
        best_ai_video_guide.ROW_SEEDANCE,
        best_ai_video_guide.ROW_VEO,
        best_ai_video_guide.ROW_OMNI,
        best_ai_video_guide.ROW_HAILUO,
        best_ai_video_guide.ROW_GROK,
        best_ai_video_guide.ROW_RUNWAY,
    ):
        match = [r for r in db["rows"] if r.get("id") == rid]
        if not match:
            errors.append(f"catalog is missing {rid}")
            continue
        money = rate_money(match[0]["usd_per_second"])
        if money + "/s" not in text and money not in text:
            errors.append(f"{rid} rate {money} missing")

    haystack = (text + " " + raw).lower()
    for needle in (
        "1174",
        "1159",
        "1156",
        "1151",
        "1051",
        "1000",
        "963",
        "unknown",
        "Wan 3.0 Prime",
        "Runway Gen-4",
        "Artificial Analysis",
        "AA-Video-T2V v2.1",
        "AA-Video-I2V v2.1",
        "Affiliate links never change this price order",
        "Confirmed",
        "Unknown",
        " ET (",
        best_ai_video_guide.AA_T2V,
        best_ai_video_guide.AA_I2V,
        "/guides/cheapest-ai-video-generator/",
        "id=\"best-value-table\"",
        "November 16",
    ):
        if needle.lower() not in haystack:
            errors.append(f"guide needle missing: {needle}")

    # expired promo rate should not be presented as the current Hailuo step
    if "$0.0175" in text or "$0.0175/s" in text:
        errors.append("expired Hailuo promo rate $0.0175 still appears")

    for question in (
        best_ai_video_guide.QUESTION,
        best_ai_video_guide.PHRASE,
        "How do you measure quality?",
        "How do you measure cost?",
        "Which model is best for each use?",
        "What is confirmed, and what is not?",
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
    if "https://vidfare.com/guides/best-ai-video-generator/" not in llms:
        errors.append("llms.txt is missing the guide")
    indexnow = open(os.path.join(ROOT, "scripts", "notify_indexnow.py"), encoding="utf-8").read()
    if "https://vidfare.com/guides/best-ai-video-generator/" not in indexnow:
        errors.append("IndexNow GUIDE_URLS is missing the guide")
    for rel in (
        "guides/index.html",
        "index.html",
        "guides/cheapest-ai-video-generator/index.html",
        "models/wan-3-0/index.html",
        "models/runway-gen-4/index.html",
        "models/seedance-2-5/index.html",
    ):
        page = open(os.path.join(ROOT, "dist", rel), encoding="utf-8").read()
        if f'href="{PATH}"' not in page:
            errors.append(f"{rel} does not link the guide")
    guides = open(os.path.join(ROOT, "dist", "guides", "index.html"), encoding="utf-8").read()
    if "comparisons built from the same price rows" not in guides:
        errors.append("guides index is missing the comparisons lead")

    if errors:
        raise SystemExit("best AI video guide:\n- " + "\n- ".join(errors))
    print("ok best AI video guide")


if __name__ == "__main__":
    main()
