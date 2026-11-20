#!/usr/bin/env python3
"""The AI Video Price Index page, CSV and JSON agree with prices.json and its git history.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_price_index.py
The numbers here are recomputed without price_index.py, so a bug there cannot hide.
"""
import csv
import datetime
import html
import io
import json
import os
import re
import statistics
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import price_index

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
PAGE = os.path.join(DIST, "price-index", "index.html")
CSV = os.path.join(DIST, "data", "price-index.csv")
JSON = os.path.join(DIST, "data", "price-index.json")
NINE = ["Wan 3.0 Prime", "Wan 3.0", "Kling 3.0", "Seedance 2.5", "Veo 3.1", "Gemini Omni Flash",
        "MiniMax Hailuo", "Runway Gen-4", "Grok Imagine"]
TIER_RES = {"480p": "480p", "720p": "720p", "1080p": "1080p", "4k": "4k"}


def rate_money(v):
    x = float(v)
    s = f"{x:.4f}" if x < 0.10 else f"{x:.3f}"
    s = s.rstrip("0")
    whole, frac = s.split(".")
    return f"${whole}.{frac.ljust(2, '0')}"


def live(r, day):
    if r.get("status") == "discontinued":
        return False
    if r.get("discontinued_on") and r["discontinued_on"] < day:
        return False
    if r.get("promo_until") and r["promo_until"] < day:
        return False
    return True


def per_model(db, day, tier):
    best = {}
    for r in db["rows"]:
        if r["model"] not in db["models"] or not live(r, day):
            continue
        if tier != "any" and str(r.get("resolution") or "").strip().lower() != TIER_RES[tier]:
            continue
        if r["model"] not in best or r["usd_per_second"] < best[r["model"]]:
            best[r["model"]] = r["usd_per_second"]
    return best


def visible(raw):
    raw = re.sub(r"<script\b.*?</script>", " ", raw, flags=re.S)
    raw = re.sub(r"<style\b.*?</style>", " ", raw, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw)))


def unit_errors():
    errors = []
    if price_index.tier_of("480P") != "480p" or price_index.tier_of("4K") != "4k":
        errors.append("tier_of does not normalise case")
    for res in ("768p", "2K", "lowest mode", "720p/1080p", "—", None):
        if price_index.tier_of(res) is not None:
            errors.append(f"tier_of({res!r}) should have no tier")
    rows = [
        {"model": "a", "resolution": "720p", "usd_per_second": 0.10, "status": "verified", "promo_until": None},
        {"model": "a", "resolution": "720p", "usd_per_second": 0.02, "status": "promo", "promo_until": "2026-11-10"},
        {"model": "b", "resolution": "720p", "usd_per_second": 0.30, "status": "verified", "promo_until": None},
        {"model": "c", "resolution": "720p", "usd_per_second": 0.01, "status": "discontinued", "promo_until": None},
        {"model": "d", "resolution": "1080p", "usd_per_second": 0.20, "status": "verified", "promo_until": None},
        {"model": "zz", "resolution": "720p", "usd_per_second": 0.001, "status": "verified", "promo_until": None},
    ]
    slugs = ["a", "b", "c", "d"]
    p = price_index.index_point(rows, slugs, "2026-11-10", "720p")
    if (p["models_priced"], p["cheapest"]) != (2, 0.02) or abs(p["median"] - 0.16) > 1e-12:
        errors.append(f"promo on its last day should count: {p}")
    p = price_index.index_point(rows, slugs, "2026-11-11", "720p")
    if (p["models_priced"], p["cheapest"]) != (2, 0.10) or abs(p["median"] - 0.20) > 1e-12:
        errors.append(f"expired promo should drop out: {p}")
    p = price_index.index_point(rows, slugs, "2026-11-11", "any")
    if p["models_priced"] != 3 or p["row"]["model"] != "a":
        errors.append(f"unknown model or discontinued row counted: {p}")
    if price_index.pct_text(price_index.pct_change(0.04, 0.03)) != "-25.0%":
        errors.append("pct_text")
    if price_index.pct_text(price_index.pct_change(None, 0.03)) != "n/a":
        errors.append("pct_text n/a")

    # History: a day uses the last saved catalog on or before it. Nothing in between is invented.
    def cat(v):
        return {"rows": [{"model": "a", "resolution": "720p", "usd_per_second": v, "status": "verified", "promo_until": None}]}
    snaps = [("2026-11-01", "aaaaaaaa", "2026-11-01T12:00:00-05:00"), ("2026-11-04", "bbbbbbbb", "2026-11-04T12:00:00-05:00")]
    store = {"aaaaaaaa": cat(0.10), "bbbbbbbb": cat(0.04)}
    db = {"models": {"a": {"name": "A"}}, "rows": cat(0.03)["rows"]}
    s = price_index.build_series(ROOT, db, "2026-11-06", snapshots=snaps, loader=store.get)
    got = [(d["date"], d["tiers"]["720p"]["cheapest"], d["catalog"]) for d in s["days"]]
    want = [("2026-11-01", 0.10, "aaaaaaa"), ("2026-11-02", 0.10, "aaaaaaa"), ("2026-11-03", 0.10, "aaaaaaa"),
            ("2026-11-04", 0.04, "bbbbbbb"), ("2026-11-05", 0.04, "bbbbbbb"), ("2026-11-06", 0.03, "current")]
    if got != want:
        errors.append(f"series carry-forward is wrong: {got}")
    s = price_index.build_series(ROOT, db, "2026-11-06", snapshots=[], loader=store.get)
    if len(s["days"]) != 1 or s["days"][0]["date"] != "2026-11-06":
        errors.append("without history the series should be today only")
    return errors


def page_errors():
    errors = []
    for path in (PAGE, CSV, JSON):
        if not os.path.isfile(path):
            return [f"{path} is missing; build the site first"]
    raw = open(PAGE, encoding="utf-8").read()
    text = visible(raw)
    db = json.load(open(os.path.join(ROOT, "data", "prices.json"), encoding="utf-8"))
    changes = json.load(open(os.path.join(ROOT, "data", "changes.json"), encoding="utf-8"))
    today = json.load(open(JSON, encoding="utf-8"))["series"][-1]["date"]

    title = html.unescape(re.search(r"<title>(.*?)</title>", raw).group(1))
    if title != price_index.TITLE or len(title) > 60:
        errors.append(f"title {len(title)} chars: {title}")
    if '<link rel="canonical" href="https://vidfare.com/price-index/">' not in raw:
        errors.append("canonical")
    if '<meta name="robots" content="index,follow">' not in raw:
        errors.append("page is not indexable")
    if "sora" in raw.lower():
        errors.append("names Sora")
    if "caracas" in raw.lower() or " UTC" in text:
        errors.append("time not in ET/PT format")
    for n in NINE:
        if n not in text:
            errors.append(f"model {n} missing")
    if text.count("<h1") > 1 or raw.count("<h1>") != 1:
        errors.append("one h1")

    # Today's headline numbers, recomputed.
    for tier, label in price_index.TIERS:
        vals = list(per_model(db, today, tier).values())
        shown = len(vals) >= price_index.MIN_MODELS
        row = re.search(rf'<th scope="row">{re.escape(label)}</th>(.*?)</tr>', raw, re.S)
        if shown and not row:
            errors.append(f"tier {label} has {len(vals)} models but is not shown")
            continue
        if not shown:
            if row:
                errors.append(f"tier {label} has only {len(vals)} models but is shown")
            elif vals and f"{label} ({len(vals)} of {len(db['models'])})" not in text:
                errors.append(f"tier {label} is not footnoted")
            continue
        cells = visible(row.group(1))
        med, low = rate_money(statistics.median(vals)), rate_money(min(vals))
        if f"{len(vals)} of {len(db['models'])}" not in cells or med not in cells or low not in cells:
            errors.append(f"tier {label}: expected {len(vals)} models, median {med}, cheapest {low}; got {cells}")
    anyv = list(per_model(db, today, "any").values())
    lead = visible(re.search(r'<p class="lead">(.*?)</p>', raw, re.S).group(1))
    if rate_money(statistics.median(anyv)) not in lead or rate_money(min(anyv)) not in lead:
        errors.append(f"lead numbers: {lead}")

    # Per-model table: now, and the change columns use the catalog saved for that day.
    rows = dict(re.findall(r'<tr><th scope="row"><a href="/models/([a-z0-9-]+)/">.*?</th>(.*?)</tr>', raw, re.S))
    series = list(csv.DictReader(io.StringIO(open(CSV, encoding="utf-8").read())))
    by_day = {}
    for r in series:
        by_day.setdefault(r["date"], r["catalog"])
    week = (datetime.date.fromisoformat(today) - datetime.timedelta(days=7)).isoformat()
    start = series[0]["date"]
    old = {}
    for day in (week, start):
        sha = by_day.get(day)
        if sha and sha != "current":
            out = subprocess.run(["git", "-C", ROOT, "show", f"{sha}:data/prices.json"], capture_output=True, text=True)
            old[day] = per_model(json.loads(out.stdout), day, "any") if out.returncode == 0 else None
    now = per_model(db, today, "any")
    for slug, m in db["models"].items():
        cells = rows.get(slug)
        if cells is None:
            errors.append(f"model row {slug} missing")
            continue
        parts = re.findall(r"<td[^>]*>(.*?)</td>", cells, re.S)
        if rate_money(now[slug]) not in visible(parts[0]):
            errors.append(f"{slug} now should be {rate_money(now[slug])}")
        for day, part in ((week, parts[1]), (start, parts[2])):
            ref = (old.get(day) or {}).get(slug)
            if ref is None:
                if "n/a" not in part:
                    errors.append(f"{slug} {day} should be n/a")
                continue
            pct = (now[slug] - ref) / ref * 100
            want = "0.0%" if abs(pct) < 0.05 else f"{'+' if pct > 0 else '-'}{abs(pct):.1f}%"
            if want not in part or rate_money(ref) not in part:
                errors.append(f"{slug} vs {day}: want {want} from {rate_money(ref)}, got {visible(part)}")
        lw = sum(1 for c in changes if c.get("type") == "price" and c.get("model") == slug and c["date"] > week)
        la = sum(1 for c in changes if c.get("type") == "price" and c.get("model") == slug and c["date"] > start)
        if f"{lw} / {la}" not in parts[3]:
            errors.append(f"{slug} logged change count should be {lw} / {la}")
    if not old.get(week) and "n/a" not in text:
        errors.append("missing history is not shown as n/a")

    # Every CSV row matches a recomputation from that day's catalog.
    cache = {}
    for r in series:
        sha = r["catalog"]
        if sha == "current":
            src = db
        else:
            if sha not in cache:
                out = subprocess.run(["git", "-C", ROOT, "show", f"{sha}:data/prices.json"], capture_output=True, text=True)
                cache[sha] = json.loads(out.stdout)
            src = cache[sha]
        vals = list(per_model(src, r["date"], r["tier"]).values())
        if int(r["models_priced"]) != len(vals):
            errors.append(f"csv {r['date']} {r['tier']} models_priced")
        elif vals and (abs(float(r["median_usd_per_second"]) - statistics.median(vals)) > 1e-6
                       or abs(float(r["cheapest_usd_per_second"]) - min(vals)) > 1e-6):
            errors.append(f"csv {r['date']} {r['tier']} numbers")
    days = sorted({r["date"] for r in series})
    for a, b in zip(days, days[1:]):
        if (datetime.date.fromisoformat(b) - datetime.date.fromisoformat(a)).days != 1:
            errors.append(f"csv skips from {a} to {b}")
    if days[-1] != today:
        errors.append("csv does not end today")

    # Chart: inline SVG with a text alternative, no script.
    svg = re.search(r"<svg\b.*?</svg>", raw, re.S)
    if not svg or 'role="img"' not in svg.group(0) or "<title" not in svg.group(0) or "<desc" not in svg.group(0):
        errors.append("chart needs an inline svg with role=img, title and desc")
    if 'id="pi-daily"' not in raw:
        errors.append("chart needs the daily table as a text alternative")

    # Dataset JSON-LD matches the page.
    lds = [json.loads(x) for x in re.findall(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)]
    ds = next((x for x in lds if x.get("@type") == "Dataset"), None)
    if not ds:
        errors.append("Dataset JSON-LD missing")
    else:
        if ds["name"] not in text or ds["description"] not in text:
            errors.append("Dataset name/description not visible on the page")
        urls = sorted(d["contentUrl"] for d in ds.get("distribution", []))
        if urls != ["https://vidfare.com/data/price-index.csv", "https://vidfare.com/data/price-index.json"]:
            errors.append(f"Dataset distribution {urls}")
        for u in urls:
            if u.replace("https://vidfare.com", "") not in raw:
                errors.append(f"{u} not linked on the page")
        if ds.get("temporalCoverage") != f"{start}/{today}":
            errors.append("temporalCoverage")
    if "Cite this" not in text or "https://vidfare.com/price-index/" not in text:
        errors.append("cite line")

    # Site wiring.
    sitemap = open(os.path.join(DIST, "sitemap.xml"), encoding="utf-8").read()
    if "<loc>https://vidfare.com/price-index/</loc>" not in sitemap:
        errors.append("sitemap")
    llms = open(os.path.join(DIST, "llms.txt"), encoding="utf-8").read()
    line = next((l for l in llms.splitlines() if "/price-index/" in l), "")
    if not line or rate_money(statistics.median(anyv)) not in line or rate_money(min(anyv)) not in line:
        errors.append("llms.txt line missing or numbers differ")
    for rel in ("index.html", "changes/index.html", "reports/index.html", "deals/index.html", "models/wan-3-0/index.html"):
        body = open(os.path.join(DIST, rel), encoding="utf-8").read()
        foot = body[body.find("<footer"):]
        if 'href="/price-index/">Price index</a>' not in foot:
            errors.append(f"{rel} footer link")
    for rel in ("changes/index.html", "reports/index.html"):
        main = open(os.path.join(DIST, rel), encoding="utf-8").read()
        main = main[main.find("<main"):main.find("</main>")]
        if 'href="/price-index/"' not in main:
            errors.append(f"{rel} does not link the index")
    return errors


def main():
    errors = unit_errors() + page_errors()
    if errors:
        raise SystemExit("price index check failed:\n- " + "\n- ".join(errors))
    print("ok price index page, CSV, JSON and links agree with prices.json and its git history")
    return 0


if __name__ == "__main__":
    sys.exit(main())
