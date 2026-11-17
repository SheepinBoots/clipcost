#!/usr/bin/env python3
"""The AI video generator apps guide agrees with house rules and catalog rows.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_ai_video_generator_apps_guide.py
"""
import html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ai_video_generator_apps_guide

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = ai_video_generator_apps_guide.PATH
PAGE = os.path.join(ROOT, "dist", "guides", "ai-video-generator-apps", "index.html")


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
        "Kling AI",
        "Runway",
        "Pika",
        "official iPhone app",
        "Google Play",
        "1,500 Credits $34.99",
        "$0.0233",
        "60 credits per $1",
        "Affiliate links never change this price order",
        "Confirmed",
        "Unknown",
        "America/Caracas",
        "Key takeaways",
        "What to do next",
        "r146",
        "r111",
        "r209",
        "Last checked 2026-11-16",
        ai_video_generator_apps_guide.LUMA_ANDROID,
        "Infinity AI Solutions",
        "We could not confirm that listing is official",
        ai_video_generator_apps_guide.IOS["pika"],
        ai_video_generator_apps_guide.PLAY["kling"],
        'id="app-listings-table"',
        'id="in-app-prices-table"',
        'id="app-plan-rates-table"',
        'id="takeaways"',
        'id="next-steps"',
        'id="newsletter"',
        "/guides/free-text-to-video-ai/",
    ):
        if needle.lower() not in haystack:
            errors.append(f"guide needle missing: {needle}")

    for question in (
        ai_video_generator_apps_guide.QUESTION,
        ai_video_generator_apps_guide.H1,
        "How did we check, and what counts as official?",
        "What do the apps charge in-app?",
        "What does a second of video cost on each app’s plan?",
        "Which app is best for each use?",
        "How do you tell an official app from a look-alike?",
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
    if raw.rfind('id="newsletter"') < raw.rfind("How do we calculate this?"):
        errors.append("newsletter box is not after the how-we-calculate section")

    sitemap = open(os.path.join(ROOT, "dist", "sitemap.xml"), encoding="utf-8").read()
    if f"<loc>https://vidfare.com{PATH}</loc>" not in sitemap:
        errors.append("sitemap")
    llms = open(os.path.join(ROOT, "dist", "llms.txt"), encoding="utf-8").read()
    if "https://vidfare.com/guides/ai-video-generator-apps/" not in llms:
        errors.append("llms.txt is missing the guide")
    indexnow = open(os.path.join(ROOT, "scripts", "notify_indexnow.py"), encoding="utf-8").read()
    if "https://vidfare.com/guides/ai-video-generator-apps/" not in indexnow:
        errors.append("IndexNow GUIDE_URLS is missing the guide")
    for rel in (
        "guides/index.html",
        "index.html",
        "models/kling-3-0/index.html",
        "models/runway-gen-4/index.html",
        "models/veo-3-1/index.html",
        "models/grok-imagine/index.html",
        "models/seedance-2-5/index.html",
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
        raise SystemExit("AI video generator apps guide:\n- " + "\n- ".join(errors))
    print("ok AI video generator apps guide")


if __name__ == "__main__":
    main()
