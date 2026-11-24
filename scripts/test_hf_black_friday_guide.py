#!/usr/bin/env python3
"""Check the Higgsfield Black Friday guide against prices.json and the deal records in deals.json."""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hf_black_friday_guide

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "dist", "guides", "higgsfield-black-friday", "index.html")
PATH = hf_black_friday_guide.PATH


def main():
    errors = []
    if not os.path.isfile(PAGE):
        raise SystemExit(f"missing {PAGE}; build the site first")
    raw = open(PAGE, encoding="utf-8").read()
    text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"\s+", " ", text)

    if f'<link rel="canonical" href="https://vidfare.com{PATH}">' not in raw:
        errors.append("canonical")
    if "Sora" in raw or "sora" in raw:
        errors.append("page names Sora")

    title = re.search(r"<title>(.*?)</title>", raw)
    desc = re.search(r'<meta name="description" content="(.*?)"', raw)
    if not title or len(re.sub(r"&[a-z]+;", "x", title.group(1))) > 60:
        errors.append(f"title missing or over 60: {title.group(1) if title else None}")
    if not desc or len(re.sub(r"&[a-z]+;", "x", desc.group(1))) > 160:
        errors.append(f"description missing or over 160: {desc.group(1) if desc else None}")
    desc_txt = (desc.group(1) if desc else "").replace("&amp;", "&")
    # Sale wording follows the deal records in deals.json, never hardcoded prices.
    import deal_copy
    g = {}
    st = deal_copy.hf_bf(g)
    pa = deal_copy.price_after(st, "hf-plus-annual")
    ua = deal_copy.price_after(st, "hf-ultra-annual")
    if st["live"]:
        for v in (pa, ua):
            if v is not None and f"${v:g}" not in desc_txt:
                errors.append(f"description does not name the ${v:g} annual sale price")
        if st["end"] and st["end"] not in text:
            errors.append(f"live sale end {st['end']} missing")
        if "sale has ended" in text.lower():
            errors.append("guide says the sale has ended while its deal is live")
        live_needles = [f"${deal_copy.price_after(st, i):g}" for i in st["live_ids"] if deal_copy.price_after(st, i)]
    else:
        if "ended" not in desc_txt.lower():
            errors.append("description does not say the sale ended")
        if st["end"] and st["end"] not in text:
            errors.append(f"sale end {st['end']} missing")
        for bad in ("is live", "live until", "ends in", "sale is on"):
            if bad in text:
                errors.append(f"ended sale still described as live: {bad!r}")
        live_needles = []
    if "No Black Friday 2026 sale is up yet" in desc_txt or "has not posted a Black Friday 2026 sale" in text:
        errors.append("guide still says no Black Friday 2026 sale is posted")
    if "Caracas" in raw:
        errors.append("page names Caracas")

    for needle in [
        "$19",
        "billed yearly",
        "11.11",
        "calculated at checkout",
        "audio not stated",
        "assuming every paid credit is used",
        "id=\"newsletter\"",
    ] + live_needles:
        if needle not in text and needle not in raw:
            errors.append(f"missing needle: {needle}")

    db = json.load(open(os.path.join(ROOT, "data", "prices.json"), encoding="utf-8"))

    def rate(v):
        from decimal import Decimal, ROUND_HALF_UP
        places = 3 if abs(Decimal(str(v))) >= Decimal("0.1") else 4
        q = Decimal("1").scaleb(-places)
        n = format(Decimal(str(v)).quantize(q, rounding=ROUND_HALF_UP), "f")
        if "." in n:
            n = n.rstrip("0").rstrip(".")
        return n

    for rid in ("r081", "r096", "r111", "r123"):
        row = next(r for r in db["rows"] if r["id"] == rid)
        n = rate(row["usd_per_second"])
        if n not in text and n not in raw:
            errors.append(f"catalog {rid} rate {n} missing")

    sample = next(r for r in db["rows"] if r["id"] == "r081")
    six = deal_copy.price_after(st, "hf-ultra-6k-annual") if st["live"] else None
    nine = deal_copy.price_after(st, "hf-ultra-9k-annual") if st["live"] else None
    if sample.get("credits_per_clip") and sample.get("clip_seconds"):
        for label, mo, credits in (("6K", six, hf_black_friday_guide.ULTRA_6K_CREDITS), ("9K", nine, hf_black_friday_guide.ULTRA_9K_CREDITS)):
            if mo is None:
                continue
            n = rate(mo / credits * sample["credits_per_clip"] / sample["clip_seconds"])
            if n not in text and n not in raw:
                errors.append(f"computed Ultra {label} annual rate {n} missing")

    if 'href="https://higgsfield.ai/pricing?fpr=emmanuel-bbfe0e"' not in raw:
        errors.append("pricing page affiliate link missing")
    if 'rel="sponsored nofollow noopener"' not in raw:
        errors.append("affiliate rel missing")

    sitemap = open(os.path.join(ROOT, "dist", "sitemap.xml"), encoding="utf-8").read()
    if f"<loc>https://vidfare.com{PATH}</loc>" not in sitemap:
        errors.append("sitemap")
    for rel in ("guides/index.html", "deals/black-friday/index.html", "deals/index.html"):
        page = open(os.path.join(ROOT, "dist", rel), encoding="utf-8").read()
        if f'href="{PATH}"' not in page:
            errors.append(f"{rel} does not link the guide")

    idx = open(os.path.join(ROOT, "dist", "guides", "index.html"), encoding="utf-8").read()
    if "comparisons built from the same price rows" not in idx:
        errors.append("guides index is missing the comparisons lead")
    cur_pa = deal_copy.plan_month({"plans": db["plans"]}, "hf-plus-annual")
    if st["live"] and cur_pa is not None and f"${cur_pa:g}/mo" not in idx:
        errors.append(f"guides index blurb does not mention ${cur_pa:g}/mo")

    if errors:
        raise SystemExit("higgsfield black friday guide check failed:\n- " + "\n- ".join(errors))
    print("ok higgsfield black friday guide")


if __name__ == "__main__":
    main()
