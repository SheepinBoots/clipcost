#!/usr/bin/env python3
"""The free AI video generators guide agrees with prices.json and today's official figures.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_free_ai_video_guide.py
"""
import html
import json
import os
import re
import sys
from decimal import Decimal, ROUND_HALF_UP

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import free_ai_video_guide

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = free_ai_video_guide.PATH
PAGE = os.path.join(ROOT, "dist", "guides", "free-ai-video-generators", "index.html")


def rate_money(v):
    # Same half-up rounding as build_site.rate_money (4 places under $0.10, else 3).
    from decimal import Decimal, ROUND_HALF_UP
    d = Decimal(str(v))
    places = 3 if abs(d) >= Decimal("0.1") else 4
    text = f"{abs(d.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)):.{places}f}"
    whole, frac = text.split(".")
    frac = frac.rstrip("0").ljust(2, "0")
    return f"{'-' if d < 0 else ''}${whole}.{frac}"



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

    # Catalog paid-step rates must appear.
    for rid in (
        free_ai_video_guide.ROW_VEO,
        free_ai_video_guide.ROW_KLING,
        free_ai_video_guide.ROW_WAN,
        free_ai_video_guide.ROW_HAILUO,
        free_ai_video_guide.ROW_GROK,
        free_ai_video_guide.ROW_RUNWAY,
        free_ai_video_guide.ROW_SEEDANCE,
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
        "Google Flow",
        "50",
        "Veo 3.1 Lite",
        "Krea",
        "100",
        "Runway",
        "125",
        "Dreamina",
        "Kling",
        "Basic",
        "Higgsfield",
        "Pika",
        "no watermark",
        "Hailuo",
        "Grok Imagine",
        "Wan",
        "check-in",
        "Luma",
        "Meta AI",
        "unknown",
        "Affiliate links never change this price order",
        "Confirmed",
        "Unknown",
        " ET (",
        free_ai_video_guide.FLOW_CREDITS,
        free_ai_video_guide.KREA_PLANS,
        free_ai_video_guide.RUNWAY_PLANS,
        free_ai_video_guide.DREAMINA_PLANS,
        free_ai_video_guide.KLING_PLANS,
        free_ai_video_guide.HF_PLANS,
        free_ai_video_guide.PIKA_PLANS,
        free_ai_video_guide.HAILUO_TERMS,
        free_ai_video_guide.WAN_PLANS,
        free_ai_video_guide.XAI_GROK,
        free_ai_video_guide.LUMA_PLANS,
        "id=\"free-tier-table\"",
        "id=\"no-signup\"",
        "Which free AI video generator works with no sign-up?",
        "No credit card required",
        "None of the official free video tiers",
        free_ai_video_guide.SIGNUP_CHECKED_WHEN,
    ):
        if needle.lower() not in haystack:
            errors.append(f"guide needle missing: {needle}")

    for question in (
        free_ai_video_guide.QUESTION,
        free_ai_video_guide.PHRASE,
        "What does each major free tier actually include?",
        "Which free AI video generator works with no sign-up?",
        "Which free option is best for each use?",
        "What are the usual catches on a “free” plan?",
        "When does paying become cheaper per second?",
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
    # visible FAQ answers must appear
    for q, a in (
        (free_ai_video_guide.QUESTION, None),
    ):
        if q not in text:
            errors.append(f"visible question missing: {q}")

    if 'id="newsletter"' not in raw:
        errors.append("newsletter signup box missing from end of guide")

    sitemap = open(os.path.join(ROOT, "dist", "sitemap.xml"), encoding="utf-8").read()
    if f"<loc>https://vidfare.com{PATH}</loc>" not in sitemap:
        errors.append("sitemap")
    llms = open(os.path.join(ROOT, "dist", "llms.txt"), encoding="utf-8").read()
    if "https://vidfare.com/guides/free-ai-video-generators/" not in llms:
        errors.append("llms.txt is missing the guide")
    indexnow = open(os.path.join(ROOT, "scripts", "notify_indexnow.py"), encoding="utf-8").read()
    if "https://vidfare.com/guides/free-ai-video-generators/" not in indexnow:
        errors.append("IndexNow GUIDE_URLS is missing the guide")
    for rel in (
        "guides/index.html",
        "index.html",
        "models/runway-gen-4/index.html",
        "models/kling-3-0/index.html",
        "models/veo-3-1/index.html",
        "models/gemini-omni-flash/index.html",
        "models/grok-imagine/index.html",
        "models/wan-3-0/index.html",
        "models/seedance-2-5/index.html",
        "models/minimax-hailuo/index.html",
        "guides/cheapest-ai-video-generator/index.html",
    ):
        page = open(os.path.join(ROOT, "dist", rel), encoding="utf-8").read()
        if f'href="{PATH}"' not in page:
            errors.append(f"{rel} does not link the guide")
    guides = open(os.path.join(ROOT, "dist", "guides", "index.html"), encoding="utf-8").read()
    if "comparisons built from the same price rows" not in guides:
        errors.append("guides index is missing the comparisons lead")
    if not re.search(r"\b[A-Z][a-z]+(?:-[a-z]+)? comparisons built from the same price rows", guides):
        errors.append("guides index count text is missing")

    # footer Guides line
    footer_sample = open(os.path.join(ROOT, "dist", "index.html"), encoding="utf-8").read()
    if "/guides/free-ai-video-generators/" not in footer_sample:
        errors.append("home page is missing the footer or guides list link")

    if errors:
        raise SystemExit("free AI video guide:\n- " + "\n- ".join(errors))
    print("ok free AI video guide")


if __name__ == "__main__":
    main()
