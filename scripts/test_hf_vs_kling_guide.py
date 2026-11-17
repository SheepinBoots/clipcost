#!/usr/bin/env python3
"""The higgsfield vs kling guide agrees with today's catalog and house rules.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_hf_vs_kling_guide.py
"""
import html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hf_vs_kling_guide

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = hf_vs_kling_guide.PATH
PAGE = os.path.join(ROOT, "dist", "guides", "higgsfield-vs-kling", "index.html")


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
    for needle in NEEDLES:
        if needle.lower() not in haystack:
            errors.append(f"guide needle missing: {needle}")

    for question in QUESTIONS:
        if question not in text:
            errors.append(f"visible text missing: {question}")

    faq_raw = ""
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S):
        faq_raw += m.group(1).lower()
    for bad in ("subscribe", "newsletter", "buttondown"):
        if bad in faq_raw:
            errors.append(f"FAQ JSON-LD contains {bad}")
    for q in QUESTIONS[:1]:
        if q.lower() not in faq_raw:
            errors.append(f"FAQ JSON-LD missing {q}")

    if 'id="newsletter"' not in raw:
        errors.append("newsletter signup box missing from end of guide")
    if raw.rfind('id="newsletter"') < raw.rfind("How do we calculate this?"):
        errors.append("newsletter box is not after the how-we-calculate section")
    if 'id="takeaways"' in raw:
        # house ad should come after takeaways when present
        pass

    sitemap = open(os.path.join(ROOT, "dist", "sitemap.xml"), encoding="utf-8").read()
    if f"<loc>https://vidfare.com{PATH}</loc>" not in sitemap:
        errors.append("sitemap")
    llms = open(os.path.join(ROOT, "dist", "llms.txt"), encoding="utf-8").read()
    if f"https://vidfare.com{PATH}" not in llms:
        errors.append("llms.txt is missing the guide")
    indexnow = open(os.path.join(ROOT, "scripts", "notify_indexnow.py"), encoding="utf-8").read()
    if f"https://vidfare.com{PATH}" not in indexnow:
        errors.append("IndexNow GUIDE_URLS is missing the guide")
    for rel in RELS:
        page = open(os.path.join(ROOT, "dist", rel), encoding="utf-8").read()
        if f'href="{PATH}"' not in page:
            errors.append(f"{rel} does not link the guide")
    guides = open(os.path.join(ROOT, "dist", "guides", "index.html"), encoding="utf-8").read()
    if "comparisons built from the same price rows" not in guides:
        errors.append("guides index is missing the comparisons lead")
    if not re.search(r"\b[A-Z][a-z]+(?:-[a-z]+)? comparisons built from the same price rows", guides):
        errors.append("guides index count text is missing")

    if errors:
        raise SystemExit("higgsfield vs kling guide:\n- " + "\n- ".join(errors))
    print("ok higgsfield vs kling guide")


NEEDLES = ['Key takeaways', 'What to do next', 'unknown', 'Affiliate links never change this price order', 'America/Caracas', 'r111', 'r059', 'r007', '$0.0250', '$0.084', '/guides/kling-ai-pricing/', '/guides/higgsfield-pricing/', '/guides/higgsfield-alternatives/', '/guides/higgsfield-vs-runway/', 'id="takeaways"', 'id="next-steps"', 'id="newsletter"', 'id="kling-720p-table"', 'https://kling.ai/document-api/pricing/base/video.md']
QUESTIONS = ['Is Kling cheaper on Higgsfield or on the official site?', 'How does this comparison work?', 'What do official Kling plans and Higgsfield plans cost?', 'Which option is best for each use?', 'What is confirmed, and what is not?']
RELS = ['guides/index.html', 'index.html', 'guides/kling-ai-pricing/index.html', 'models/kling-3-0/index.html']

if __name__ == "__main__":
    main()
