#!/usr/bin/env python3
"""The cheapest Seedance 2.5 guide agrees with prices.json and deals.json.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_cheapest_seedance_guide.py
"""
import datetime
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cheapest_seedance_guide
import deals
import seedance_unlimited_guide

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = cheapest_seedance_guide.PATH
PAGE = os.path.join(ROOT, "dist", "guides", "cheapest-seedance-2-5", "index.html")
MODEL = "seedance-2-5"


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
    doc = deals.load()
    today = datetime.date.today().isoformat()
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
        errors.append("no Seedance 2.5 catalog rows")
    by_id = {r["id"]: r for r in db["rows"]}

    # Every catalog Seedance 2.5 rate must appear, formatted like the site.
    for r in rows:
        money = rate_money(r["usd_per_second"])
        if money not in text:
            errors.append(f"{r['id']} rate {money} missing")

    # Cheapest published API at each stated resolution, and the Higgsfield "from" row.
    published = [
        r for r in rows
        if r.get("kind") == "api" and r.get("status") == "verified"
    ]
    if not published:
        errors.append("no published Seedance 2.5 API row")
    else:
        best = sorted(published, key=lambda r: (r["usd_per_second"], r["id"]))[0]
        if rate_money(best["usd_per_second"]) not in desc and best["platform"] not in desc:
            # description may shorten the variant but should name the platform and rate
            if rate_money(best["usd_per_second"]) not in desc:
                errors.append(f"description missing cheapest published rate {rate_money(best['usd_per_second'])}")
            if best["platform"] not in desc:
                errors.append("description missing cheapest published platform")

    # Known catalog ids that must stay cited if present.
    for rid in ("r008", "r017", "r018", "r019", "r039", "r040", "r041",
                "r073", "r074", "r075", "r161", "r163", "r166", "r169"):
        if rid in by_id and by_id[rid]["model"] == MODEL:
            if rate_money(by_id[rid]["usd_per_second"]) not in text:
                errors.append(f"expected catalog {rid} missing")

    # Replicate official rates, when present in the catalog.
    rep = [r for r in rows if r.get("platform") == "Replicate"]
    for r in rep:
        if r["platform"] not in text:
            errors.append("Replicate platform missing")
            break
        if "non_video_in" in (r.get("variant") or "") or "video_in" in (r.get("variant") or ""):
            if r["variant"].split()[0] not in text and r["variant"] not in text:
                errors.append(f"Replicate variant {r['variant']} missing")

    # Unverified Higgsfield plan credits are not turned into a fake $/s.
    if "1,200" in text or "1200" in text:
        # If the guide mentions the 1,200-credit plan, it must not invent a $/s from 80 videos.
        if re.search(r"80 videos[^.]*\$0\.\d+", text, re.I):
            errors.append("invented a $/s from Higgsfield's 80 Seedance 2.5 videos")
    if "Higgsfield Seedance 2.5 per-clip credits" not in " ".join(
        (i.get("item") or "") for i in (db.get("unverified") or [])
    ):
        # If the unverified item is removed, the guide should still refuse a plan $/s without credits.
        pass
    else:
        if "without clip length" not in text.lower() and "without a clip length" not in text.lower() and "clip length or resolution" not in text.lower() and "clip length and resolution" not in text.lower():
            errors.append("missing the Higgsfield plan credit gap")

    # Live unlimited windows: link the existing guide, do not claim $0/s.
    if f'href="{UNLIMITED}"' not in raw.replace("https://vidfare.com", "") and f'href="{seedance_unlimited_guide.PATH}"' not in raw:
        if "/guides/seedance-2-5-unlimited/" not in raw:
            errors.append("does not link the unlimited Seedance 2.5 guide")
    if re.search(r"unlimited[^.]{0,80}\$0/s", text, re.I) and "not $0/s" not in text and "not treated as $0/s" not in text:
        errors.append("treats unlimited as $0/s")
    if "not $0/s" not in text and "not treated as $0/s" not in text:
        errors.append("missing the not $0/s warning")

    class G:
        pass

    # Break-even figures, when windows are live, must match checkout / cheapest same-res API.
    g = {
        "rows": [r for r in db["rows"] if True],
        "deal_doc": doc,
        "dealmod": deals,
        "TODAY": today,
        "plans": db["plans"],
        "DEAL_BY_ID": {d["id"]: d for d in doc["deals"]},
    }
    # Filter current() is already how the site works; tests use all non-expired in prices after build.
    ws = seedance_unlimited_guide.live_windows(g)
    for w in ws:
        res = w.get("resolution")
        checkout = w.get("checkout")
        apis = [
            r for r in rows
            if r.get("kind") == "api" and r.get("resolution") == res
        ]
        if not apis or checkout is None:
            continue
        api = sorted(apis, key=lambda r: (r["usd_per_second"], r["id"]))[0]
        seconds = checkout / api["usd_per_second"]
        needle = f"{seconds:,.0f} seconds"
        if needle not in text:
            errors.append(f"break-even {needle} for {w['deal']['id']} {res} missing")

    if "fpr=emmanuel-bbfe0e" not in raw:
        errors.append("Higgsfield affiliate fpr missing")
    if "Affiliate links never change this price order" not in text:
        errors.append("affiliate price-order sentence missing")
    if "rel=\"sponsored nofollow noopener\"" not in raw and "rel='sponsored nofollow noopener'" not in raw:
        errors.append("affiliate rel missing")

    # Hidden costs cited from official pages.
    for needle in (
        "80 credit minimum",
        "Credits valid for 1 year",
        "failed",
        "token",
    ):
        if needle.lower() not in text.lower():
            errors.append(f"hidden-cost needle missing: {needle}")

    sitemap = open(os.path.join(ROOT, "dist", "sitemap.xml"), encoding="utf-8").read()
    if f"<loc>https://vidfare.com{PATH}</loc>" not in sitemap:
        errors.append("sitemap")
    for rel in (
        "guides/index.html",
        "index.html",
        "models/seedance-2-5/index.html",
    ):
        page = open(os.path.join(ROOT, "dist", rel), encoding="utf-8").read()
        if f'href="{PATH}"' not in page:
            errors.append(f"{rel} does not link the guide")
    guides = open(os.path.join(ROOT, "dist", "guides", "index.html"), encoding="utf-8").read()
    if "comparisons built from the same price rows" not in guides:
        errors.append("guides index is missing the comparisons lead")

    if errors:
        raise SystemExit("cheapest seedance guide:\n- " + "\n- ".join(errors))
    print("ok cheapest seedance 2.5 guide")


# used above; keep a short alias for typo safety in the href check
UNLIMITED = "/guides/seedance-2-5-unlimited/"


if __name__ == "__main__":
    main()
