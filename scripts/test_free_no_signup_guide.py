#!/usr/bin/env python3
"""The no-sign-up guide matches the catalog, the live-page check, and house rules.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_free_no_signup_guide.py
"""
import html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import free_no_signup_guide

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = free_no_signup_guide.PATH
PAGE = os.path.join(ROOT, "dist", "guides", "free-ai-video-generator-no-sign-up", "index.html")

UNPUBLISHED = (
    "/guides/is-higgsfield-free/",
    "/guides/is-kling-ai-free/",
    "/guides/is-seedance-free/",
    "/guides/google-flow-pricing/",
)


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
    if " | VidFare" not in title:
        errors.append(f"title is missing the VidFare suffix: {title}")
    if f'<link rel="canonical" href="https://vidfare.com{PATH}">' not in raw:
        errors.append("canonical")
    low = (text + " " + raw).lower()
    if "sora" in low:
        errors.append("names Sora")
    if "america/caracas" in low or re.search(r"\butc\b", low):
        errors.append("page shows Caracas or UTC")
    if "12 major" in low or "twelve major" in low or "12 tools" in low:
        errors.append("still says VidFare tracks 12 tools")
    for slug in UNPUBLISHED:
        if slug in raw:
            errors.append(f"links unpublished {slug}")

    for needle in (
        "Wan 3.0 Prime",
        "Wan 3.0",
        "Kling 3.0",
        "Seedance 2.5",
        "Veo 3.1",
        "Gemini Omni Flash",
        "Omni Flash 1.2",
        "Omni Flash 1.1",
        "MiniMax Hailuo",
        "Runway Gen-4",
        "Grok Imagine",
        "Not in the VidFare catalog",
        "nine",
        "2 minutes",
        "100 units",
        "50 credits",
        "125",
        "SeeDance V1",
        "$0.0125",
        "$0.02",
        "$0.20",
        "$0.30",
        "r096",
        "r055",
        "r209",
        "on Higgsfield",
        "on xAI API",
        "on Runway API",
        "on DeepAI",
        "fpr=emmanuel-bbfe0e",
        "Affiliate links never change this price order",
        "usage assumption",
        " ET (",
        " PT",
        "Key takeaways",
        "What to do next",
        "Last checked 2026-",
        "Not re-confirmed",
        "December 5, 2026",
        free_no_signup_guide.HF_ZERO,
        free_no_signup_guide.DEEPAI_VIDEO,
        free_no_signup_guide.FLOW_CREDITS,
        free_no_signup_guide.KREA_PLANS,
        "/guides/free-ai-video-generators/",
        "/guides/free-text-to-video-ai/",
        "/guides/free-image-to-video-ai/",
        "/guides/google-flow-credits-calculator/",
        'id="no-signup-routes"',
        'id="catalog-account"',
        'id="outside-catalog"',
        'id="paid-no-signup"',
        'id="takeaways"',
        'id="next-steps"',
        'id="newsletter-inline"',
        'id="newsletter"',
        'data-vf-event="newsletter-signup-inline"',
        'data-vf-event="newsletter-signup"',
        'data-sponsor="guide:free-ai-video-generator-no-sign-up"',
        'data-partner="pixeldojo"',
        "Assumes every credit you pay for is used",
    ):
        if needle.lower() not in low and needle not in raw:
            errors.append(f"guide needle missing: {needle}")

    for question in (
        free_no_signup_guide.QUESTION,
        "Do the catalog models need an account to generate video?",
        "Is there a paid option with no account?",
        "What is the least sign-up with a published allowance?",
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
    if "faqpage" not in faq_raw:
        errors.append("FAQ JSON-LD missing")
    if "breadcrumblist" not in faq_raw:
        errors.append("breadcrumb JSON-LD missing")
    for q in (
        free_no_signup_guide.QUESTION,
        "Is there a paid option with no account?",
    ):
        if q.lower() not in faq_raw:
            errors.append(f"FAQ JSON-LD missing {q}")

    main = raw.split("<main", 1)[-1].split("</main>", 1)[0]
    mid_mark = '<section class="news news-inline" id="newsletter-inline">'
    end_mark = '<section class="news" id="newsletter">'
    mid = main.find(mid_mark)
    end = main.find(end_mark)
    if mid < 0 or end < 0 or not mid < end:
        errors.append("mid signup is not above the end signup")
    else:
        frac = mid / max(len(main), 1)
        if not 0.15 <= frac <= 0.45:
            errors.append(f"mid signup is at {frac:.0%} of main, want about 30%")
        before = main[:mid]
        for tag in ("table", "ul", "ol", "details", "figure", "section"):
            opened = len(re.findall(rf"<{tag}\b", before)) - len(re.findall(rf"</{tag}>", before))
            if opened != 0:
                errors.append(f"mid signup is inside a <{tag}>")
        after = main[main.find("</section>", mid) + len("</section>"):].lstrip()
        if not after.startswith("<h2"):
            errors.append("mid signup is not between sections: " + after[:80])
    if raw.rfind('id="newsletter"') < raw.rfind("How do we calculate this?"):
        errors.append("end signup is not after the how-we-calculate section")
    if raw.find('data-sponsor="guide:free-ai-video-generator-no-sign-up"') > raw.find('id="newsletter-inline"'):
        errors.append("sponsor box is not above the mid signup")
    if raw.find('data-partner="pixeldojo"') < raw.find('data-sponsor="guide:free-ai-video-generator-no-sign-up"'):
        errors.append("PixelDojo line is not after the sponsor box")

    paid = raw.split('id="paid-no-signup"', 1)[-1].split("</table>", 1)[0]
    paid_text = html.unescape(re.sub(r"<[^>]+>", " ", paid))
    for earlier, later in (("$0.0125", "$0.02"), ("$0.02", "$0.20"), ("$0.20", "$0.30")):
        if paid_text.find(earlier) < 0 or paid_text.find(earlier) > paid_text.find(later):
            errors.append(f"paid table is not in price order: {earlier} before {later}")

    sitemap = open(os.path.join(ROOT, "dist", "sitemap.xml"), encoding="utf-8").read()
    if f"<loc>https://vidfare.com{PATH}</loc>" not in sitemap:
        errors.append("sitemap")
    llms = open(os.path.join(ROOT, "dist", "llms.txt"), encoding="utf-8").read()
    if "https://vidfare.com/guides/free-ai-video-generator-no-sign-up/" not in llms:
        errors.append("llms.txt is missing the guide")
    indexnow = open(os.path.join(ROOT, "scripts", "notify_indexnow.py"), encoding="utf-8").read()
    if "https://vidfare.com/guides/free-ai-video-generator-no-sign-up/" not in indexnow:
        errors.append("IndexNow GUIDE_URLS is missing the guide")
    for rel in (
        "guides/index.html",
        "index.html",
        "guides/free-ai-video-generators/index.html",
        "guides/free-text-to-video-ai/index.html",
        "guides/free-image-to-video-ai/index.html",
        "models/veo-3-1/index.html",
        "models/gemini-omni-flash/index.html",
        "models/wan-3-0/index.html",
        "models/wan-3-0-prime/index.html",
        "models/kling-3-0/index.html",
        "models/seedance-2-5/index.html",
        "models/minimax-hailuo/index.html",
        "models/runway-gen-4/index.html",
        "models/grok-imagine/index.html",
    ):
        page = open(os.path.join(ROOT, "dist", rel), encoding="utf-8").read()
        if f'href="{PATH}"' not in page and f'href="{PATH}"' not in page:
            errors.append(f"{rel} does not link the guide")
    guides = open(os.path.join(ROOT, "dist", "guides", "index.html"), encoding="utf-8").read()
    if "Which free AI video generators work with no sign-up?" not in guides:
        errors.append("guides hub is missing the question")
    if "Twenty-five comparisons built from the same price rows" not in guides:
        errors.append("guides hub count did not move to twenty-five")

    if errors:
        raise SystemExit("no sign-up guide:\n- " + "\n- ".join(errors))
    print(f"ok no sign-up guide ({len(title)} character title)")


if __name__ == "__main__":
    main()
