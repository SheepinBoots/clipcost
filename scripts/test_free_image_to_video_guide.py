#!/usr/bin/env python3
"""The free image-to-video guide agrees with today's official figures.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_free_image_to_video_guide.py
"""
import html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import free_image_to_video_guide

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = free_image_to_video_guide.PATH
PAGE = os.path.join(ROOT, "dist", "guides", "free-image-to-video-ai", "index.html")


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
        "No credit card",
        "100 daily compute units",
        "frames",
        "Affiliate links never change this price order",
        "Confirmed",
        "Unknown",
        "America/Caracas",
        free_image_to_video_guide.KREA_I2V,
        free_image_to_video_guide.FLOW_CREATE,
        free_image_to_video_guide.FLOW_MODELS,
        free_image_to_video_guide.DREAMINA_I2V,
        "/guides/free-ai-video-generators/",
        'id="free-i2v-table"',
    ):
        if needle.lower() not in haystack:
            errors.append(f"guide needle missing: {needle}")

    for question in (
        free_image_to_video_guide.QUESTION,
        free_image_to_video_guide.PHRASE,
        "How does free image-to-video AI work, and what does this page cover?",
        "Which free image-to-video option is best for each use?",
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
    if "https://vidfare.com/guides/free-image-to-video-ai/" not in llms:
        errors.append("llms.txt is missing the guide")
    indexnow = open(os.path.join(ROOT, "scripts", "notify_indexnow.py"), encoding="utf-8").read()
    if "https://vidfare.com/guides/free-image-to-video-ai/" not in indexnow:
        errors.append("IndexNow GUIDE_URLS is missing the guide")
    for rel in (
        "guides/index.html",
        "index.html",
        "guides/free-ai-video-generators/index.html",
        "models/seedance-2-5/index.html",
        "models/veo-3-1/index.html",
        "models/minimax-hailuo/index.html",
    ):
        page = open(os.path.join(ROOT, "dist", rel), encoding="utf-8").read()
        if f'href="{PATH}"' not in page:
            errors.append(f"{rel} does not link the guide")
    guides = open(os.path.join(ROOT, "dist", "guides", "index.html"), encoding="utf-8").read()
    if "comparisons built from the same price rows" not in guides:
        errors.append("guides index is missing the comparisons lead")

    aff = "https://higgsfield.ai/pricing?fpr=emmanuel-bbfe0e"
    if raw.count(aff) != 2:
        errors.append(f"expected 2 Higgsfield affiliate pricing links, found " + str(raw.count(aff)))
    if 'data-vf-affiliate="1"' not in raw or 'data-vf-vendor="higgsfield"' not in raw:
        errors.append("Higgsfield affiliate link is missing data-vf-affiliate / data-vf-vendor tracking")
    if 'rel="sponsored nofollow noopener"' not in raw:
        errors.append("Higgsfield affiliate link is missing rel=sponsored nofollow noopener")
    if 'Higgsfield lists a Free plan with limited use' not in raw:
        errors.append("missing expected affiliate context: Higgsfield lists a Free plan with limited use")
    if errors:
        raise SystemExit("free image to video guide:\n- " + "\n- ".join(errors))
    print("ok free image to video guide")


if __name__ == "__main__":
    main()
