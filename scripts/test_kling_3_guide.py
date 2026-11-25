#!/usr/bin/env python3
"""The Kling 3.0 cost guide agrees with prices.json and the house rules.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_kling_3_guide.py
"""
import html
import json
import os
import re
import sys
from decimal import Decimal, ROUND_HALF_UP

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kling_3_guide

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = kling_3_guide.PATH
PAGE = os.path.join(ROOT, "dist", "guides", "cheapest-kling-3-0", "index.html")


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
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw)))
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
    # House rule: never name the banned model.
    if "sora" in raw.lower() or "sora" in text.lower():
        errors.append("names Sora")

    rows = [
        r for r in db["rows"]
        if r["model"] == "kling-3-0" and r.get("status") != "discontinued" and r.get("usd_per_second") is not None
    ]
    rows.sort(key=lambda r: (float(r["usd_per_second"]), r["id"]))
    # Every catalog row appears in the full table, in price order.
    table = re.search(r'id="all-kling-rows".*?</table>', raw, re.S)
    if not table:
        errors.append("full Kling 3.0 table missing")
    else:
        ids = re.findall(r"catalog row (r\d+)", table.group(0))
        if ids != [r["id"] for r in rows]:
            errors.append(f"full table is not every Kling 3.0 row in price order: {ids}")
        trs = re.findall(r"<tr>(.*?)</tr>", table.group(0), re.S)[1:]
        for tr in trs:
            cells = re.findall(r"<td>(.*?)</td>", tr, re.S)
            if len(cells) != 9:
                errors.append("a full-table row is missing a column")
                continue
            if not cells[4].strip() or not cells[5].strip():
                errors.append("a row has no resolution or audio cell")
            if "Assumes" not in cells[7] and "Billed per second" not in cells[7]:
                errors.append(f"a row has no usage assumption: {cells[7][:80]}")
            if "checked" not in cells[8]:
                errors.append("a row has no checked date")
    # Per-platform table is in price order.
    first = re.search(r'id="prices".*?</table>', raw, re.S)
    if first:
        amts = [float(a) for a in re.findall(r'<span class="amt">\$([0-9.]+)/s</span>', first.group(0))]
        if amts != sorted(amts):
            errors.append(f"per-platform table is not in price order: {amts}")
        for platform in ("Higgsfield", "Magnific", "Higgsfield API", "Kling API", "Runway API", "fal"):
            if platform not in first.group(0):
                errors.append(f"per-platform table is missing {platform}")
    else:
        errors.append("per-platform table missing")

    cheapest = rows[0]
    for needle in (
        rate_money(cheapest["usd_per_second"]),
        "$0.084",
        "$0.126",
        "$0.0714",
        "$0.0962",
        "$0.112",
        "$0.168",
        "Kling AI video",
        "image to video",
        "Affiliate links never change this price order",
        "Key takeaways",
        "What to do next",
        "What is confirmed, and what is not?",
        "Unknown",
        "Last checked 2026-",
        " ET (",
        "/guides/kling-ai-pricing/",
        "/models/kling-3-0/",
        "/guides/higgsfield-pricing/",
        'id="takeaways"',
        'id="next-steps"',
        'id="newsletter"',
        'data-vf-sponsor="house-guide-cheapest-kling-3-0"',
        kling_3_guide.KLING_API,
    ):
        if needle.lower() not in (text + " " + raw).lower():
            errors.append(f"guide needle missing: {needle}")

    # Order: takeaways, then the house ad, then the first table; newsletter last.
    t = raw.find('id="takeaways"')
    ad = raw.find('data-vf-sponsor="house-guide-cheapest-kling-3-0"')
    tb = raw.find('id="prices"')
    if not (0 <= t < ad < tb):
        errors.append("house ad is not between the takeaways and the first table")
    if raw.rfind('id="newsletter"') < raw.rfind("How do we calculate this?"):
        errors.append("newsletter box is not after the how-we-calculate section")
    if raw.rfind('id="next-steps"') > raw.rfind('id="newsletter"'):
        errors.append("What to do next is after the newsletter")

    # Affiliate links keep rel=sponsored and the approved ref.
    for m in re.finditer(r'<a href="([^"]*higgsfield\.ai[^"]*)" rel="([^"]+)"', raw):
        if "fpr=emmanuel-bbfe0e" not in m.group(1) or "sponsored" not in m.group(2):
            errors.append(f"Higgsfield link without affiliate tag or rel=sponsored: {m.group(1)}")

    ld = ""
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S):
        ld += m.group(1)
    faq = None
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S):
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
    for rel in ("guides/index.html", "index.html", "models/kling-3-0/index.html"):
        page = open(os.path.join(ROOT, "dist", rel), encoding="utf-8").read()
        if f'href="{PATH}"' not in page:
            errors.append(f"{rel} does not link the guide")

    if errors:
        raise SystemExit("Kling 3.0 guide:\n- " + "\n- ".join(errors))
    print("ok Kling 3.0 guide")


if __name__ == "__main__":
    main()
