#!/usr/bin/env python3
"""/cost/ pages agree with prices.json, footnote clip caps, label sales, and hide when stale.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_cost_pages.py
Rankings are recomputed here from prices.json, not taken from cost_pages.py.
"""
import html
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cost_pages as cost

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
SITE = "https://vidfare.com"
RES = ("480p", "720p", "1080p", "4k")
errors = []


def check(ok, msg):
    if not ok:
        errors.append(msg)


def rate_money(v):
    x = float(v)
    s = f"{x:.4f}" if x < 0.10 else f"{x:.3f}"
    s = s.rstrip("0")
    whole, frac = s.split(".")
    return f"${whole}.{frac.ljust(2, '0')}"


def two(v):
    from decimal import Decimal, ROUND_HALF_UP
    return "$" + str(Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def text(s):
    s = re.sub(r"<(script|style)\b.*?</\1>", " ", s, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)))


db = json.load(open(os.path.join(ROOT, "data", "prices.json")))
today = db["last_full_check"]
_deals = json.load(open(os.path.join(ROOT, "data", "deals.json")))
_deals = _deals["deals"] if isinstance(_deals, dict) else _deals


def live(r):
    if r.get("status") == "discontinued" or (r.get("discontinued_on") and r["discontinued_on"] < today):
        return False
    if r.get("retiring_on") and r["retiring_on"] <= today:
        return False
    return not (r.get("promo_until") and r["promo_until"] < today)


def is_sale(r):
    if r.get("promo_until") or (r.get("list_usd_per_second") or 0) > r["usd_per_second"]:
        return True
    for d in _deals:
        if d.get("status") != "live" or d.get("type") != "plan_sale" or d.get("math") != "plan_price":
            continue
        if (d.get("conditions") or {}).get("standing") or (d.get("end") and d["end"] < today):
            continue
        if d.get("start") and d["start"] > today:
            continue
        for pr in d.get("price_pairs") or [d]:
            if r.get("plan") and r["plan"] == pr.get("deal_plan_id") and (pr.get("price_after") or 0) < (pr.get("price_before") or 0):
                return True
    return False


def stated_cap(r):
    v = ((r.get("variation") or {}).get("duration") or {}).get("max_seconds")
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


cur = [r for r in db["rows"] if live(r)]
models = db["models"]

# ---------- unit tests ----------
check(cost.res_key({"resolution": "480P"}) == "480p", "480P counts as 480p")
check(cost.res_key({"resolution": "720p/1080p"}) is None, "combined resolution is not ranked")
check(cost.res_key({"resolution": "—"}) is None, "dash is not a resolution")
check(cost.combined_note([{"model": "m", "platform": "fal", "resolution": "720p/1080p"}], "m", "1080p")
      == " fal lists it only as one 720p/1080p rate, which is not ranked here.", "combined_note")
check(cost.combined_note([{"model": "m", "platform": "fal", "resolution": "720p/1080p"}], "m", "480p") == "", "combined_note other res")

# ---------- built pages ----------
sitemap = open(os.path.join(DIST, "sitemap.xml"), encoding="utf-8").read()
llms = open(os.path.join(DIST, "llms.txt"), encoding="utf-8").read()
for pg in cost.COST_PAGES:
    path, secs = pg["path"], pg["seconds"]
    check(path.startswith("/cost/"), f"{path}: not under /cost/")
    title = cost.title_of(pg)
    check(len(title) <= 60, f"{path}: title {len(title)} characters")
    page = open(os.path.join(DIST, path.strip("/"), "index.html"), encoding="utf-8").read()
    body = text(page[page.find("<main"):page.find("</main>")])
    check(f"<title>{html.escape(title)}</title>" in page, f"{path}: title")
    check(f'<link rel="canonical" href="{SITE}{path}">' in page, f"{path}: canonical")
    stale = "noindex" in page
    check(stale == ("Stale data:" in body), f"{path}: stale notice and robots disagree")
    check((f"<loc>{SITE}{path}</loc>" in sitemap) == (not stale), f"{path}: sitemap vs stale")
    check((f"{SITE}{path})" in llms) == (not stale), f"{path}: llms.txt vs stale")
    check(not re.search(r"sora", page, re.I), f"{path}: names Sora")
    check("Caracas" not in page, f"{path}: Caracas time")
    check("assumes every credit you pay for is used" in body, f"{path}: usage assumption")
    check(re.search(r"\d{1,2}:\d\d [AP]M ET \(\d{1,2}:\d\d [AP]M PT\)", body) is not None, f"{path}: ET-first check time")
    lds = [json.loads(x) for x in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)]
    flat = [o for x in lds for o in (x if isinstance(x, list) else x.get("@graph", [x]))]
    wp = [o for o in flat if o.get("@type") == "WebPage"]
    check(len(wp) == 1, f"{path}: one WebPage JSON-LD")
    if wp:
        check(wp[0]["name"] in body and wp[0]["description"] in body, f"{path}: JSON-LD name/description not visible")
        check(wp[0]["url"] == SITE + path, f"{path}: JSON-LD url")
    shown = []
    for res in pg["resolutions"]:
        tab = page[page.find(f'<table id="cost-{res.lower()}">'):]
        tab = tab[:tab.find("</table>")]
        check(bool(tab), f"{path}: no table for {res}")
        expect = []
        for slug in models:
            best = None
            for r in cur:
                if r["model"] == slug and str(r.get("resolution")).strip().lower() == res.lower():
                    if best is None or r["usd_per_second"] < best["usd_per_second"]:
                        best = r
            if best:
                expect.append((best["usd_per_second"] * secs, models[slug]["name"], slug, best))
        expect.sort(key=lambda x: (x[0], x[1]))
        trs = re.findall(r"<tr><td data-label=\"Rank\" class=\"num\">(\d+)</td>(.*?)</tr>", tab, re.S)
        check(len(trs) == len(expect), f"{path}: {res} ranks {len(trs)} models, data has {len(expect)}")
        for (rank, tr), (total, mname, slug, best) in zip(trs, expect):
            shown.append(best)
            t = text(tr)
            check(t.strip().startswith(mname), f"{path}: {res} rank {rank} is not {mname}: {t[:60]}")
            cell = text(re.search(rf'data-label="{secs}s clip" class="num">(.*?)</td>', tr, re.S).group(1))
            check(cell.strip().startswith(two(total)), f"{path}: {res} {mname} total")
            check(best["platform"] in cell, f"{path}: {res} {mname} total without its seller")
            cap = stated_cap(best) or cost.CAPS.get(slug)
            n = math.ceil(secs / cap) if cap else 1
            check((f"{n} clips" in cell) == (n > 1), f"{path}: {res} {mname} clip count")
            if cap and cap < secs:
                check("†" in cell, f"{path}: {res} {mname} capped below {secs}s without a footnote mark")
            price = text(re.search(r'data-label="\$/s">(.*?)</td>', tr, re.S).group(1))
            check(f"{rate_money(best['usd_per_second'])}/s on {best['platform']} (" in price, f"{path}: {res} {mname} price without its seller")
            check("Plan or tier: " in t, f"{path}: {res} {mname} without plan or tier")
            for lab in ("Resolution", "Audio", "Checked"):
                m = re.search(rf'data-label="{lab}"[^>]*>(.*?)</td>', tr, re.S)
                check(m is not None and text(m.group(1)).strip() != "", f"{path}: {res} {mname} without {lab}")
            check(re.search(r"(published rate|estimated rate|estimated from credit plan|from credit plan|promo)", price) is not None,
                  f"{path}: {res} {mname} without a rate label")
            sale = is_sale(best)
            has = re.search(r"; (regular \$[\d.]+/s on |cheapest without a sale: \$[\d.]+/s on |no regular price in our data)", price)
            check(bool(has) == sale, f"{path}: {res} {mname} sale price {'without' if sale else 'with'} a regular price")
            has = re.search(r"(regular|cheapest without a sale:) \$[\d.]+ on ", cell)
            check(bool(has) == sale, f"{path}: {res} {mname} {secs}s total sale without a regular price")
        for slug in models:
            if not any(x[2] == slug for x in expect):
                check(re.search(rf'{re.escape(models[slug]["name"])}</a></th><td[^>]*>Not listed: no {res} price in our data\.', tab) is not None,
                      f"{path}: {slug} should be not listed at {res}")
    # Footnotes for every shown model capped below the clip length.
    for slug in {r["model"] for r in shown}:
        cap = next((stated_cap(r) for r in cur if r["model"] == slug and stated_cap(r)), None) or cost.CAPS.get(slug)
        if cap and cap < secs:
            check(f"† {models[slug]['name']} makes clips of up to {cap:g} seconds" in body, f"{path}: no cap footnote for {slug}")
    lead = re.search(r'<p class="lead">(.*?)</p>', page, re.S)
    check(lead is not None, f"{path}: lead missing")
    if lead:
        para = text(lead.group(1))
        for m in re.finditer(r"\$[\d.]*\d(?![\d.])(/s)?", para):
            if para[m.end():].startswith("/mo"):
                continue
            check(para[m.end():].startswith(" on ") or para[m.end():].startswith(" ("), f"{path}: lead price {m.group(0)} without a seller")
        for r in shown:
            if is_sale(r) and f"{rate_money(r['usd_per_second'])}/s on {r['platform']} (" in para:
                m = re.search(rf"{re.escape(rate_money(r['usd_per_second']))}/s on {re.escape(r['platform'])} \(([^()]*)\)", para)
                check(m and "; regular $" in m.group(1) or (m and "cheapest without a sale" in m.group(1)),
                      f"{path}: lead sale price without a regular price")
    for slug in models:
        mp = open(os.path.join(DIST, "models", slug, "index.html"), encoding="utf-8").read()
        check(f'href="{path}"' in mp, f"{path}: no link from /models/{slug}/")
    check(f'href="{path}"' in open(os.path.join(DIST, "calculator", "index.html"), encoding="utf-8").read(),
          f"{path}: no link from /calculator/")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"cost pages ok ({len(cost.COST_PAGES)} page(s))")
