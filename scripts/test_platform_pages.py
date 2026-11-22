#!/usr/bin/env python3
"""/platforms/ pages agree with prices.json, label every row as an estimate, show regular prices next to sale
plans, explain the unit math, link from the model pages and the calculator, and hide when stale.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_platform_pages.py
Rows and numbers are recomputed here from prices.json and deals.json, not taken from platform_pages.py.
"""
import datetime
import html
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import platform_pages as pp
import timefmt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
SITE = "https://vidfare.com"
errors = []


def check(ok, msg):
    if not ok:
        errors.append(msg)


def rate_money(v):
    from decimal import Decimal, ROUND_HALF_UP
    x = float(Decimal(str(v)).quantize(Decimal("0.0001") if float(v) < 0.10 else Decimal("0.001"), rounding=ROUND_HALF_UP))
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


def read(rel):
    return open(os.path.join(DIST, rel), encoding="utf-8").read()


db = json.load(open(os.path.join(ROOT, "data", "prices.json")))
today = db["last_full_check"]
deals = json.load(open(os.path.join(ROOT, "data", "deals.json")))
deals = deals["deals"] if isinstance(deals, dict) else deals
# Sale badges follow the site build date (US Pacific), which can be later than the catalog check.
deal_today = timefmt.us_today().isoformat()
live_deals = {d["id"] for d in deals if d.get("status") == "live" and not (d.get("end") and d["end"] < deal_today)}


def live(r):
    if r.get("status") == "discontinued" or (r.get("discontinued_on") and r["discontinued_on"] < today):
        return False
    if r.get("retiring_on") and r["retiring_on"] <= today:
        return False
    return not (r.get("promo_until") and r["promo_until"] < today)


# Unit: a plan with no card, or a card older than 7 days, is not priced.
_g = {"plans": {"a": {"checked": "2026-11-19"}, "b": {"checked": "2026-11-10"}}}
check(set(pp.plan_gaps(_g, [{"plan": "a"}, {"plan": "b"}, {"plan": "c"}], "2026-11-20")) == {"b", "c"}, "plan_gaps")
check(pp.mo(5) == "5" and pp.mo(14.5) == "14.50", "mo()")

sitemap = read("sitemap.xml")
llms = read("llms.txt")
calc = read("calculator/index.html")
check(len(pp.PLATFORM_PAGES) >= 1, "no platform pages")
for page in pp.PLATFORM_PAGES:
    path, plat, secs = page["path"], page["platform"], page["seconds"]
    raw = read(path.strip("/") + "/index.html")
    main = raw[raw.find("<main"):raw.find("</main>")]
    body = text(main)
    title = html.unescape(re.search(r"<title>(.*?)</title>", raw).group(1))
    check(title == page["title"] + " | VidFare" and len(title) <= 60, f"{path}: title {title!r} ({len(title)})")
    check(f'<link rel="canonical" href="{SITE}{path}">' in raw, f"{path}: canonical")
    check("sora" not in raw.lower(), f"{path}: names Sora")
    check("caracas" not in raw.lower(), f"{path}: Caracas time")
    every = [r for r in db["rows"] if r["platform"] == plat and r["model"] in db["models"] and live(r)]
    # Plans with no card, or a card older than 7 days, are shown as not priced and their rows are left out.
    gaps = {r["plan"] for r in every if r["plan"] not in db["plans"] or
            (datetime.date.fromisoformat(today) - datetime.date.fromisoformat(db["plans"][r["plan"]].get("checked") or "2000-01-01")).days > 7}
    rows = [r for r in every if r["plan"] not in gaps]
    check(rows, f"{path}: no rows in prices.json")
    est = all(r.get("status") == "estimate" for r in rows)
    approx = "~" if est else ""
    mt = text(main[main.find('id="plat-method"'):main.find("</table>", main.find('id="plat-method"'))])
    for pid in gaps:
        check("Not priced: " in mt and (db["plans"].get(pid, {}).get("plan") or pid) in mt, f"{path}: {pid} should show as not priced")
    if page.get("former_name"):
        check(body.count(page["former_name"]) == 1, f"{path}: former name should appear once")
    # Stale guard.
    old = min(r["checked"] for r in rows)
    stale = (datetime.date.fromisoformat(today) - datetime.date.fromisoformat(old)).days > 7
    robots = re.search(r'<meta name="robots" content="([^"]+)"', raw).group(1)
    check(robots == ("noindex,follow" if stale else "index,follow"), f"{path}: robots {robots} with oldest {old}")
    check((f"<loc>{SITE}{path}</loc>" in sitemap) != stale, f"{path}: sitemap entry vs stale={stale}")
    check((f"]({SITE}{path})" in llms) != stale, f"{path}: llms.txt entry vs stale={stale}")
    # Every row once in the by-plan table, with its numbers, labels, resolution and audio.
    tb = main[main.find('id="plat-plans"'):]
    tb = tb[:tb.find("</table>")]
    trs = re.findall(r"<tr><th scope=\"row\">(.*?)</tr>", tb, re.S)
    check(len(trs) == len(rows), f"{path}: {len(trs)} rows in the plan table, data has {len(rows)}")
    check(f"{len(rows)} rows" in body, f"{path}: row count in heading")
    for r in rows:
        plan = db["plans"][r["plan"]]
        multi = len({str(x.get("resolution")) for x in rows if (x["model"], x["variant"]) == (r["model"], r["variant"])}) > 1
        lab = r["variant"] + (f", {r['resolution']}" if multi else "")
        hit = [t for t in trs if f">{html.escape(lab, quote=True)}</a>" in t and f"Plan: {html.escape(plan['plan'])}<" in t]
        check(len(hit) == 1, f"{path}: {r['id']} {r['variant']} {plan['plan']} found {len(hit)} times")
        if len(hit) != 1:
            continue
        t = text(hit[0])
        check(f"{rate_money(r['usd_per_second'])}/s on {plat} (" in t, f"{path}: {r['id']} $/s")
        check(two(r["usd_per_second"] * secs) in t, f"{path}: {r['id']} {secs}s total")
        want = ("estimated from credit plan", "Estimated from credit plan.") if r.get("status") == "estimate" else ("from credit plan", "From credit plan.")
        check(want[0] in t and f"{want[1]} Assumes every credit you pay for is used." in t, f"{path}: {r['id']} rate/usage label")
        res = str(r.get("resolution") or "").strip()
        check((res if res.lower() in ("480p", "720p", "768p", "1080p", "4k") else "not listed") in t, f"{path}: {r['id']} resolution")
        check(any(a in t for a in ("with", "without", "not stated")), f"{path}: {r['id']} audio")
        check(f"{approx}{r['credits_per_clip']:,.0f} {page['unit']} per {r['clip_seconds']:g}s clip" in t, f"{path}: {r['id']} units per clip")
        on_sale = bool(plan.get("sale")) and plan["sale"].get("deal_id") in live_deals
        if on_sale:
            reg = plan["sale"]["regular"]["usd_month"] / plan["credits_month"] * r["credits_per_clip"] / r["clip_seconds"]
            check(f"regular {rate_money(reg)}/s on {plat}" in t, f"{path}: {r['id']} sale without regular $/s {rate_money(reg)}")
            check(f"regular {two(reg * secs)} on {plat}" in t, f"{path}: {r['id']} sale {secs}s total without regular price")
            check("DEAL" in t, f"{path}: {r['id']} sale badge")
        else:
            check("regular" not in t and "Black Friday" not in t, f"{path}: {r['id']} regular price on a row not on sale")
        if r["model"] == "veo-3-1":
            n = math.ceil(secs / 8)
            check(f"{n} clips (max 8s each)" in t, f"{path}: {r['id']} Veo clip count")
    # Cheapest per variant, ranked.
    best = {}
    labs = {}
    for r in rows:
        multi = len({str(x.get("resolution")) for x in rows if (x["model"], x["variant"]) == (r["model"], r["variant"])}) > 1
        k = (r["variant"], str(r.get("resolution")))
        labs[k] = r["variant"] + (f", {r['resolution']}" if multi else "")
        if k not in best or r["usd_per_second"] < best[k]["usd_per_second"]:
            best[k] = r
    ranked = sorted(best.values(), key=lambda r: (r["usd_per_second"], r["variant"]))
    tb = main[main.find('id="plat-cheapest"'):]
    tb = tb[:tb.find("</table>")]
    got = re.findall(r'<th scope="row"><a [^>]*>([^<]*)</a>', tb)
    check(got == [html.escape(labs[(r["variant"], str(r.get("resolution")))], quote=True) for r in ranked], f"{path}: cheapest order {got}")
    lead = text(re.search(r'<p class="lead">(.*?)</p>', main, re.S).group(1))
    r0 = ranked[0]
    check(f"The cheapest is {r0['variant']} at {rate_money(r0['usd_per_second'])}/s on {plat} (" in lead, f"{path}: lead cheapest: {lead[:200]}")
    check("assumes every credit you pay for is used" in lead, f"{path}: lead usage assumption")
    check(re.search(r"\d+:\d\d [AP]M ET \(\d+:\d\d [AP]M PT\)", lead), f"{path}: lead time not ET-first with PT")
    # Method: each plan's price, units and $/unit; units per clip and clips per plan.
    tb = main[main.find('id="plat-method"'):]
    tb = text(tb[:tb.find("</table>")])
    for pid in dict.fromkeys(r["plan"] for r in rows):
        p = db["plans"][pid]
        check(f"{p['plan']} ${pp.mo(p['usd_month'])}/mo" in tb, f"{path}: method price for {pid}")
        check(f"{p['credits_month']:,} ${p['usd_month'] / p['credits_month']:.5f}" in tb, f"{path}: method units for {pid}")
        if p.get("sale") and p["sale"].get("deal_id") in live_deals:
            check(f"regular ${pp.mo(p['sale']['regular']['usd_month'])}/mo" in tb, f"{path}: {pid} sale plan without regular price")
            check("3:00 AM ET (12:00 AM PT)" in tb, f"{path}: {pid} sale end not ET-first with PT")
    tb = main[main.find('id="plat-units"'):]
    tb = tb[:tb.find("</table>")]
    for r in rows:
        p = db["plans"][r["plan"]]
        n = math.floor(p["credits_month"] / r["credits_per_clip"] + 1e-6)
        check(f"{approx}{n:,}" in tb, f"{path}: clips a month for {r['id']}")
    check(page.get("gap_note", "") in body, f"{path}: plan gap note")
    # Links from each model Krea sells, and the calculator.
    link = f'<a href="{path}">{page["title"]}</a>'
    for slug in db["models"]:
        mp = read(f"models/{slug}/index.html")
        sells = any(r["model"] == slug for r in rows)
        line = re.search(r'<p class="small">Platform prices: (.*?)</p>', mp)
        check(bool(line and link in line.group(1)) == sells, f"{path}: model page {slug} link (sells={sells})")
    line = re.search(r'<p class="small">Platform prices: (.*?)</p>', calc)
    check(bool(line and link in line.group(1)), f"{path}: calculator link")
    # JSON-LD matches the visible h1 and description.
    lds = [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)]
    wp = [d for d in lds if d.get("@type") == "WebPage"]
    check(wp and wp[0]["name"] == page["h1"] and wp[0]["description"] == page["description"], f"{path}: JSON-LD WebPage")
    check(html.escape(page["description"], quote=True) in main and f"<h1>{html.escape(page['h1'])}</h1>" in main, f"{path}: visible h1/description")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"platform pages ok ({len(pp.PLATFORM_PAGES)} page(s))")
