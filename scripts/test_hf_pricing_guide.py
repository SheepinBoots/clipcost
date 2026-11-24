#!/usr/bin/env python3
"""The Higgsfield pricing guide agrees with prices.json and today's official figures.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_hf_pricing_guide.py
"""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hf_pricing_guide

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = hf_pricing_guide.PATH
PAGE = os.path.join(ROOT, "dist", "guides", "higgsfield-pricing", "index.html")


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

    rows = [r for r in db["rows"] if r.get("platform") == "Higgsfield"]
    if not rows:
        errors.append("no Higgsfield plan rows")
    for r in rows:
        money = rate_money(r["usd_per_second"])
        if money not in text:
            errors.append(f"{r['id']} rate {money} missing")

    best = hf_pricing_guide.blurb({"rows": rows, "rate_money": rate_money, "shown_resolution": lambda r: r.get("resolution") or "—"})
    # blurb uses shown_resolution and rate_money; if cheapest rate missing from desc:
    cheapest = sorted(rows, key=lambda r: (r["usd_per_second"], r["id"]))[0]
    if rate_money(cheapest["usd_per_second"]) not in desc:
        errors.append(f"description missing cheapest tracked plan rate {rate_money(cheapest['usd_per_second'])}")

    # Official sale and plan figures that must appear.
    for needle in (
        "$19",
        "$59",
        "$129",
        "$79",
        "Black Friday",
        "$250",
        "$258",
        "$375",
        "$387",
        "270",
        "1,200",
        "3,000",
        "6,000",
        "9,000",
        "11.11",
        "Nov 14, 2026, 7:00 PM ET (4:00 PM PT)",
        "only on higgsfield.ai",
        "Affiliate links never change this price order",
        "Confirmed",
        "Unknown",
        "Seedance 2.5",
        "Wan 3.0 Prime",
        "Kling 3.0",
        "Grok Video",
        "Gemini Omni Flash",
        "Runway Gen-4",
        "Enterprise",
        "Team",
        "Scale",
        "35 credits/5s",
        "80 credits/5s",
    ):
        if needle.lower() not in text.lower():
            errors.append(f"guide needle missing: {needle}")

    # Sale figures come from the deal records in deals.json.
    import deal_copy
    st = deal_copy.hf_bf({})
    if st["live"]:
        for i in st["live_ids"]:
            v = deal_copy.price_after(st, i)
            if v is not None and f"${v:g}" not in text:
                errors.append(f"live deal {i} price ${v:g} missing")
        if st["end"] not in text:
            errors.append(f"live sale end {st['end']} missing")
        if "sale has ended" in text.lower():
            errors.append("says the Black Friday sale has ended while its deal is live")
    else:
        if "Black Friday sale has ended" not in text:
            errors.append("ended Black Friday sale is not described as ended")
        if "live until" in text or "is live on its pricing page" in text:
            errors.append("ended Black Friday sale still described as live")
    if "right now" in text.lower() and "Nov 19" in text:
        errors.append("stale Nov 19 prices presented as current")

    for question in (
        hf_pricing_guide.QUESTION,
        "What do credits buy for the models we track?",
        "When is pay-as-you-go elsewhere cheaper?",
        "How do Unlimited bonuses work, and where do they apply?",
        "How do we calculate this?",
    ):
        if question not in text:
            errors.append(f"FAQ question missing from visible text: {question}")

    faq_raw = ""
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S):
        faq_raw += m.group(1).lower()
    for bad in ("subscribe", "newsletter", "buttondown"):
        if bad in faq_raw:
            errors.append(f"FAQ JSON-LD contains {bad}")

    if "fpr=emmanuel-bbfe0e" not in raw:
        errors.append("Higgsfield affiliate fpr missing")
    if 'rel="sponsored nofollow noopener"' not in raw and "rel='sponsored nofollow noopener'" not in raw:
        errors.append("affiliate rel missing")

    sitemap = open(os.path.join(ROOT, "dist", "sitemap.xml"), encoding="utf-8").read()
    if f"<loc>https://vidfare.com{PATH}</loc>" not in sitemap:
        errors.append("sitemap")
    llms = open(os.path.join(ROOT, "dist", "llms.txt"), encoding="utf-8").read()
    if "https://vidfare.com/guides/higgsfield-pricing/" not in llms:
        errors.append("llms.txt is missing the guide")
    indexnow = open(os.path.join(ROOT, "scripts", "notify_indexnow.py"), encoding="utf-8").read()
    if "https://vidfare.com/guides/higgsfield-pricing/" not in indexnow:
        errors.append("IndexNow GUIDE_URLS is missing the guide")
    for rel in (
        "guides/index.html",
        "index.html",
        "guides/is-higgsfield-worth-it/index.html",
        "guides/higgsfield-black-friday/index.html",
        "deals/black-friday/index.html",
    ):
        page = open(os.path.join(ROOT, "dist", rel), encoding="utf-8").read()
        if f'href="{PATH}"' not in page:
            errors.append(f"{rel} does not link the guide")
    guides = open(os.path.join(ROOT, "dist", "guides", "index.html"), encoding="utf-8").read()
    if "comparisons built from the same price rows" not in guides:
        errors.append("guides index is missing the comparisons lead")

    if errors:
        raise SystemExit("higgsfield pricing guide:\n- " + "\n- ".join(errors))
    print("ok higgsfield pricing guide")


if __name__ == "__main__":
    main()
