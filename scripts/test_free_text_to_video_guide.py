#!/usr/bin/env python3
"""The free text-to-video guide agrees with today's catalog and house rules.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_free_text_to_video_guide.py
"""
import html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import free_text_to_video_guide

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = free_text_to_video_guide.PATH
PAGE = os.path.join(ROOT, "dist", "guides", "free-text-to-video-ai", "index.html")


def main():
    if not os.path.isfile(PAGE):
        raise SystemExit(f"{PAGE} is missing; build the site first")
    raw = open(PAGE, encoding="utf-8").read()
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    text = re.sub(r"\s+", " ", text)
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

    haystack = (text + " " + raw).lower()
    for needle in (
        "Krea",
        "Google Flow",
        "Dreamina",
        "Pika",
        "Wan",
        "Hailuo",
        "unknown",
        "100 compute units",
        "50 credits",
        "Affiliate links never change this price order",
        "Confirmed",
        "Unknown",
        "America/Caracas",
        "Key takeaways",
        "What to do next",
        "$0.0167",
        "$0.02",
        "r096",
        "r209",
        "r146",
        "r023",
        "r025",
        "r024",
        "Last checked 2026-",
        free_text_to_video_guide.KREA_VIDEO,
        free_text_to_video_guide.FLOW_CREDITS,
        free_text_to_video_guide.FLOW_MODELS,
        "/guides/free-ai-video-generators/",
        'id="free-t2v-table"',
        'id="paid-t2v-table"',
        'id="takeaways"',
        'id="next-steps"',
        'id="newsletter"',
    ):
        if needle.lower() not in haystack:
            errors.append(f"guide needle missing: {needle}")

    for question in (
        free_text_to_video_guide.QUESTION,
        free_text_to_video_guide.PHRASE,
        "How does free text-to-video AI work, and what does this page cover?",
        "Which free text-to-video option is best for each use?",
        "What does text-to-video cost when the free tier runs out?",
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
    for q in (
        free_text_to_video_guide.QUESTION,
        "What does text-to-video cost when the free tier runs out?",
    ):
        if q.lower() not in faq_raw:
            errors.append(f"FAQ JSON-LD missing {q}")

    if 'id="newsletter"' not in raw:
        errors.append("newsletter signup box missing from end of guide")
    # newsletter is last meaningful block: after how_block
    if raw.rfind('id="newsletter"') < raw.rfind("How do we calculate this?"):
        errors.append("newsletter box is not after the how-we-calculate section")

    sitemap = open(os.path.join(ROOT, "dist", "sitemap.xml"), encoding="utf-8").read()
    if f"<loc>https://vidfare.com{PATH}</loc>" not in sitemap:
        errors.append("sitemap")
    llms = open(os.path.join(ROOT, "dist", "llms.txt"), encoding="utf-8").read()
    if "https://vidfare.com/guides/free-text-to-video-ai/" not in llms:
        errors.append("llms.txt is missing the guide")
    indexnow = open(os.path.join(ROOT, "scripts", "notify_indexnow.py"), encoding="utf-8").read()
    if "https://vidfare.com/guides/free-text-to-video-ai/" not in indexnow:
        errors.append("IndexNow GUIDE_URLS is missing the guide")
    for rel in (
        "guides/index.html",
        "index.html",
        "guides/free-ai-video-generators/index.html",
        "models/veo-3-1/index.html",
        "models/gemini-omni-flash/index.html",
        "models/wan-3-0/index.html",
        "models/grok-imagine/index.html",
    ):
        page = open(os.path.join(ROOT, "dist", rel), encoding="utf-8").read()
        if f'href="{PATH}"' not in page:
            errors.append(f"{rel} does not link the guide")
    guides = open(os.path.join(ROOT, "dist", "guides", "index.html"), encoding="utf-8").read()
    if "comparisons built from the same price rows" not in guides:
        errors.append("guides index is missing the comparisons lead")
    if "Eighteen comparisons" not in guides and "eighteen comparisons" not in guides:
        errors.append("guides index count text was not updated to Eighteen")

    if errors:
        raise SystemExit("free text to video guide:\n- " + "\n- ".join(errors))
    print("ok free text to video guide")


if __name__ == "__main__":
    main()
