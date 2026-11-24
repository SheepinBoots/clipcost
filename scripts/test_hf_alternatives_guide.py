#!/usr/bin/env python3
"""The higgsfield alternatives guide agrees with today's catalog and house rules.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_hf_alternatives_guide.py
"""
import html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hf_alternatives_guide

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = hf_alternatives_guide.PATH
PAGE = os.path.join(ROOT, "dist", "guides", "higgsfield-alternatives", "index.html")


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
        raise SystemExit("higgsfield alternatives guide:\n- " + "\n- ".join(errors))
    print("ok higgsfield alternatives guide")


NEEDLES = ['Key takeaways', 'What to do next', 'unknown', 'Affiliate links never change this price order', ' ET (', 'OpenArt', 'Krea', 'Replicate', 'r096', 'r127', 'r202', '$0.015', '$0.06', '$0.1028', '/guides/higgsfield-pricing/', '/guides/is-higgsfield-worth-it/', '/guides/higgsfield-vs-kling/', '/guides/higgsfield-vs-runway/', '/guides/fal-ai-pricing/', '/guides/best-ai-video-generator/', '/guides/free-ai-video-generators/', 'id="takeaways"', 'id="next-steps"', 'id="newsletter"', 'id="platform-cheap-table"', 'https://openart.ai/pricing']
QUESTIONS = ['Which Higgsfield alternatives are cheaper per second?', 'How does this page rank Higgsfield alternatives?', 'Which option is best for each use?', 'What free Higgsfield alternatives are there?', 'How does Higgsfield compare with OpenArt on price?', 'What is confirmed, and what is not?']
RELS = ['guides/index.html', 'index.html', 'guides/higgsfield-pricing/index.html', 'guides/is-higgsfield-worth-it/index.html', 'models/wan-3-0/index.html', 'models/kling-3-0/index.html', 'models/veo-3-1/index.html', 'models/minimax-hailuo/index.html', 'models/seedance-2-5/index.html']

if __name__ == "__main__":
    main()
