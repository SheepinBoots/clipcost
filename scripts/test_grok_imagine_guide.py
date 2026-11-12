#!/usr/bin/env python3
"""The Grok Imagine video cost guide agrees with prices.json.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_grok_imagine_guide.py
"""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grok_imagine_guide

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = grok_imagine_guide.PATH
PAGE = os.path.join(ROOT, "dist", "guides", "grok-imagine-video-cost", "index.html")
MODEL = "grok-imagine"


def rate_money(v):
    x = float(v)
    if x < 0.10:
        s = f"{x:.4f}".rstrip("0").rstrip(".")
    else:
        s = f"{x:.3f}".rstrip("0").rstrip(".")
    return "$" + s


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

    rows = [r for r in db["rows"] if r.get("model") == MODEL]
    if not rows:
        errors.append("no Grok Imagine catalog rows")

    # Every catalog Grok Imagine rate must appear, formatted like the site.
    for r in rows:
        money = rate_money(r["usd_per_second"])
        if money not in text:
            errors.append(f"{r['id']} rate {money} missing")

    published = [
        r for r in rows
        if r.get("kind") == "api" and r.get("status") == "verified"
    ]
    if not published:
        errors.append("no published Grok Imagine API row")
    else:
        best = grok_imagine_guide.cheapest_overall({"rows": rows})
        if rate_money(best["usd_per_second"]) not in desc:
            errors.append(f"description missing cheapest published rate {rate_money(best['usd_per_second'])}")
        if best["platform"] not in desc:
            errors.append("description missing cheapest published platform")

    # Official list prices in the catalog must match the checked official table.
    for (variant, res), usd in grok_imagine_guide.OFFICIAL.items():
        found = [
            r for r in rows
            if r.get("platform") == "xAI API"
            and r.get("resolution") == res
            and variant in (r.get("variant") or "")
            and r.get("usd_per_second") == usd
        ]
        if not found:
            errors.append(f"missing official catalog row {variant} {res} {usd}")
        clip5 = rate_money(usd * 5)
        clip15 = rate_money(usd * 15)
        if clip5 not in text:
            errors.append(f"5s official example {variant} {res} {clip5} missing")
        if clip15 not in text:
            errors.append(f"15s official example {variant} {res} {clip15} missing")

    runway_lite_1080 = [
        r for r in rows
        if r.get("platform") == "Runway API"
        and r.get("resolution") == "1080p"
        and "lite" in (r.get("variant") or "").lower()
        and r.get("usd_per_second") == 0.14
    ]
    if not runway_lite_1080:
        errors.append("missing Runway lite 1080p catalog row at $0.14/s")

    # Confirmed official and plan facts, plus stated unknowns. Avoid the
    # substring "subscribe" in this check list so a later FAQ audit stays clean.
    for needle in (
        "docs.x.ai/developers/pricing",
        "x.ai/pricing",
        "weekly",
        "Extra Usage Credits",
        "720p",
        "480p",
        "Premium",
        "Plus",
        "Super",
        "Ultra",
        "not included on Free or Plus",
        "upscaled from 720p",
        "Affiliate links never change this price order",
        "do not publish",
        "Unknown",
        "Confirmed",
        "Replicate",
        "fal",
        "Runway",
        "Atlas",
        "Krea",
        "Magnific",
        "Higgsfield",
    ):
        if needle.lower() not in text.lower():
            errors.append(f"guide needle missing: {needle}")

    # Visible FAQ answers must appear in the page body (not only JSON-LD).
    for question in (
        grok_imagine_guide.QUESTION,
        "How much is one Grok Imagine video on the official API?",
        "Do X Premium or SuperGrok plans include video, and what are the limits?",
        "Which route is cheapest for a typical video?",
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

    # Catalog price tables (Where / $/s / Status) must be sorted by $/s.
    # Affiliate markup must not change that order. Worked clip-total tables are excluded.
    for table in re.findall(r"<table>(.*?)</table>", raw, re.S):
        header = re.search(r"<thead>(.*?)</thead>", table, re.S)
        if not header or "Status" not in header.group(1) or "$/s" not in header.group(1):
            continue
        # The $/s column is the first numeric cell in each body row.
        values = []
        for tr in re.findall(r"<tr>(.*?)</tr>", re.search(r"<tbody>(.*?)</tbody>", table, re.S).group(1), re.S):
            cell = re.search(r'<td class="num">(\$[0-9.]+)', tr)
            if not cell:
                errors.append("catalog table row missing $/s")
                continue
            values.append(float(cell.group(1)[1:]))
        if values != sorted(values):
            errors.append(f"price table is not sorted by $/s: {values}")

    sitemap = open(os.path.join(ROOT, "dist", "sitemap.xml"), encoding="utf-8").read()
    if f"<loc>https://vidfare.com{PATH}</loc>" not in sitemap:
        errors.append("sitemap")
    llms = open(os.path.join(ROOT, "dist", "llms.txt"), encoding="utf-8").read()
    if "https://vidfare.com/guides/grok-imagine-video-cost/" not in llms:
        errors.append("llms.txt is missing the guide")
    indexnow = open(os.path.join(ROOT, "scripts", "notify_indexnow.py"), encoding="utf-8").read()
    if "https://vidfare.com/guides/grok-imagine-video-cost/" not in indexnow:
        errors.append("IndexNow GUIDE_URLS is missing the guide")
    for rel in (
        "guides/index.html",
        "index.html",
        "models/grok-imagine/index.html",
    ):
        page = open(os.path.join(ROOT, "dist", rel), encoding="utf-8").read()
        if f'href="{PATH}"' not in page:
            errors.append(f"{rel} does not link the guide")
    guides = open(os.path.join(ROOT, "dist", "guides", "index.html"), encoding="utf-8").read()
    if "comparisons built from the same price rows" not in guides:
        errors.append("guides index is missing the comparisons lead")
    if "Ten comparisons" not in guides and "ten comparisons" not in guides:
        errors.append("guides index count text was not updated to Ten")

    if errors:
        raise SystemExit("grok imagine video cost guide:\n- " + "\n- ".join(errors))
    print("ok grok imagine video cost guide")


if __name__ == "__main__":
    main()
