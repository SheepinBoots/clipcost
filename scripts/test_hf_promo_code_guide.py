#!/usr/bin/env python3
"""The Higgsfield promo code page lists only sourced deals, with end dates as stated.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_hf_promo_code_guide.py
"""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hf_promo_code_guide as guide

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = guide.PATH
PAGE = os.path.join(ROOT, "dist", "guides", "higgsfield-promo-code", "index.html")
OFFICIAL = ("https://higgsfield.ai/", "https://x.com/higgsfield_ai/", "https://x.com/higgsfield/")


def main():
    if not os.path.isfile(PAGE):
        raise SystemExit(f"{PAGE} is missing; build the site first")
    raw = open(PAGE, encoding="utf-8").read()
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw)))
    errors = []

    title = html.unescape(re.search(r"<title>(.*?)</title>", raw).group(1))
    desc = html.unescape(re.search(r'<meta name="description" content="(.*?)"', raw).group(1))
    if len(title) > 60:
        errors.append(f"title is {len(title)} characters: {title}")
    if len(desc) > 160:
        errors.append(f"description is {len(desc)} characters: {desc}")
    if f'<link rel="canonical" href="https://vidfare.com{PATH}">' not in raw:
        errors.append("canonical")
    # House rule: never name the banned model.
    if "sora" in raw.lower() or "sora" in text.lower():
        errors.append("names Sora")

    # Every entry has an official source, a stated end (or "not stated"), and a check time.
    for d in guide.CURRENT + guide.EXPIRED:
        url = d["source"][0]
        if not url.startswith(OFFICIAL):
            errors.append(f"{d['title']}: source is not an official Higgsfield page or account: {url}")
        if not d.get("ends"):
            errors.append(f"{d['title']}: no end date text")
        if not d.get("checked"):
            errors.append(f"{d['title']}: no last-checked time")
    for d in guide.CURRENT:
        if not d.get("code"):
            errors.append(f"{d['title']}: no code cell")
        if "No code" not in d["code"]:
            # A real code must name its official source in the same entry.
            if "higgsfield" not in d["source"][0]:
                errors.append(f"{d['title']}: a code without an official source")
    if 'id="prices"' not in raw or 'id="expired-deals"' not in raw:
        errors.append("current or ended deals table missing")
    cur = re.search(r'id="prices".*?</table>', raw, re.S).group(0)
    if cur.count("<tr>") - 1 != len(guide.CURRENT):
        errors.append("current table row count does not match CURRENT")
    if "11.11" in cur:
        errors.append("the ended 11.11 sale is listed as current")
    old = re.search(r'id="expired-deals".*?</table>', raw, re.S).group(0)
    if "11.11" not in old or "Expired" not in old:
        errors.append("the 11.11 sale is not marked expired")

    for needle in (
        "No public code",
        "no public Higgsfield promo code",
        "$33",
        "$50",
        "$90",
        "End date not stated",
        "0 days, 2 hours, 55 minutes",
        "PT",
        "Last checked",
        "Affiliate disclosure",
        "fpr=emmanuel-bbfe0e",
        "Manage Account",
        "/guides/higgsfield-black-friday/",
        "/guides/higgsfield-pricing/",
        "Key takeaways",
        "What to do next",
        'id="takeaways"',
        'id="next-steps"',
        'id="newsletter"',
        'data-vf-sponsor="house-guide-higgsfield-promo-code"',
        guide.PRICING,
        guide.HELP_CODES,
    ):
        if needle.lower() not in (text + " " + raw).lower():
            errors.append(f"guide needle missing: {needle}")

    t = raw.find('id="takeaways"')
    ad = raw.find('data-vf-sponsor="house-guide-higgsfield-promo-code"')
    tb = raw.find('id="prices"')
    if not (0 <= t < ad < tb):
        errors.append("house ad is not between the takeaways and the first table")
    if raw.rfind('id="newsletter"') < raw.rfind("How do we calculate this?"):
        errors.append("newsletter box is not after the how-we-calculate section")

    for m in re.finditer(r'<a href="([^"]*higgsfield\.ai[^"]*)" rel="([^"]+)"', raw):
        if "fpr=emmanuel-bbfe0e" not in m.group(1) or "sponsored" not in m.group(2):
            errors.append(f"Higgsfield link without affiliate tag or rel=sponsored: {m.group(1)}")

    faq = None
    ld = ""
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S):
        ld += m.group(1)
        obj = json.loads(m.group(1))
        if obj.get("@type") == "FAQPage":
            faq = obj
    if not faq:
        errors.append("FAQPage JSON-LD missing")
    else:
        for q in faq["mainEntity"]:
            if q["name"] not in text:
                errors.append(f"FAQ question not visible: {q['name']}")
            if html.unescape(q["acceptedAnswer"]["text"]) not in text:
                errors.append(f"FAQ answer not visible for: {q['name']}")
    for bad in ("subscribe", "newsletter", "buttondown"):
        if bad in ld.lower():
            errors.append(f"JSON-LD contains {bad}")

    sitemap = open(os.path.join(ROOT, "dist", "sitemap.xml"), encoding="utf-8").read()
    if not re.search(rf"<loc>https://vidfare.com{re.escape(PATH)}</loc><lastmod>\d{{4}}-\d\d-\d\d</lastmod>", sitemap):
        errors.append("sitemap entry with lastmod missing")
    llms = open(os.path.join(ROOT, "dist", "llms.txt"), encoding="utf-8").read()
    if f"https://vidfare.com{PATH}" not in llms:
        errors.append("llms.txt is missing the guide")
    indexnow = open(os.path.join(ROOT, "scripts", "notify_indexnow.py"), encoding="utf-8").read()
    if f"https://vidfare.com{PATH}" not in indexnow:
        errors.append("IndexNow GUIDE_URLS is missing the guide")
    for rel in ("guides/index.html", "index.html"):
        page = open(os.path.join(ROOT, "dist", rel), encoding="utf-8").read()
        if f'href="{PATH}"' not in page:
            errors.append(f"{rel} does not link the guide")

    if errors:
        raise SystemExit("Higgsfield promo code guide:\n- " + "\n- ".join(errors))
    print("ok Higgsfield promo code guide")


if __name__ == "__main__":
    main()
