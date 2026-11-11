#!/usr/bin/env python3
"""The unlimited Seedance 2.5 guide agrees with data/deals.json and prices.json.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_seedance_guide.py
"""
import datetime, html, json, math, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deals

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "dist", "guides", "seedance-2-5-unlimited", "index.html")
MODEL = "seedance-2-5"


def main():
    if not os.path.isfile(PAGE):
        raise SystemExit(f"{PAGE} is missing; build the site first")
    raw = open(PAGE, encoding="utf-8").read()
    text = html.unescape(raw)
    doc = deals.load()
    db = json.load(open(os.path.join(ROOT, "data", "prices.json")))
    today = datetime.date.today().isoformat()
    errors = []
    title = html.unescape(re.search(r"<title>(.*?)</title>", raw).group(1))
    desc = html.unescape(re.search(r'<meta name="description" content="(.*?)"', raw).group(1))
    if len(title) > 60 or len(desc) > 160:
        errors.append(f"title {len(title)} or description {len(desc)} too long")
    if '<link rel="canonical" href="https://vidfare.com/guides/seedance-2-5-unlimited/">' not in raw:
        errors.append("canonical")
    if "sora" in text.lower():
        errors.append("names Sora")
    sd = [d for d in doc["deals"] if d.get("type") == "unlimited_window" and MODEL in (d.get("models") or [])]
    live = [d for d in sd if deals.is_current(d, today)]
    for d in live:
        if not d.get("windows"):
            errors.append(f"{d['id']} is live with no windows list")
        if not d.get("source_url") or not d.get("verified_date"):
            errors.append(f"{d['id']} needs source_url and verified_date")
        for w in d.get("windows") or []:
            if w.get("quote") and w["quote"] not in text:
                errors.append(f"{d['id']} {w.get('plan')} {w.get('billing')} quote is not on the page")
            if f"{w['days']} days" not in text or f"{w['max_clip_seconds']}s" not in text:
                errors.append(f"{d['id']} {w.get('plan')} window or clip cap missing")
    for d in sd:
        if not deals.is_current(d, today) and not deals.is_upcoming(d, today):
            if (d.get("title") or d["id"]) not in text:
                errors.append(f"ended deal {d['id']} missing from the expired table")
    rows = [r for r in db["rows"] if r["model"] == MODEL and r.get("kind") == "api"]
    for d in live:
        for w in d.get("windows") or []:
            same = sorted((r for r in rows if r.get("resolution") == w["resolution"]), key=lambda r: (r["usd_per_second"], r["id"]))
            if not same:
                continue
            plan = db["plans"].get(w.get("plan_id") or "")
            if w.get("usd_seat_month") is not None:
                month = w["usd_seat_month"] * (w.get("seats") or 1)
                pay = month * 12 if w.get("billing") == "annual" else month
            elif w.get("price_deal"):
                pay = next(x for x in doc["deals"] if x["id"] == w["price_deal"])["price_after"]
            else:
                pay = plan["usd_month"] * (12 if w.get("billing") == "annual" else 1)
            secs = int(math.ceil(pay / same[0]["usd_per_second"] - 1e-9))
            if f"{secs:,} s" not in text:
                errors.append(f"break-even {secs:,} s for {w.get('plan')} {w.get('billing')} missing")
    sitemap = open(os.path.join(ROOT, "dist", "sitemap.xml"), encoding="utf-8").read()
    if "<loc>https://vidfare.com/guides/seedance-2-5-unlimited/</loc>" not in sitemap:
        errors.append("sitemap")
    for rel in ("guides/index.html", "deals/index.html", "models/seedance-2-5/index.html"):
        if 'href="/guides/seedance-2-5-unlimited/"' not in open(os.path.join(ROOT, "dist", rel), encoding="utf-8").read():
            errors.append(f"{rel} does not link the guide")
    if errors:
        raise SystemExit("seedance guide check failed:\n- " + "\n- ".join(errors))
    print(f"ok seedance guide: {len(live)} live deals, {sum(len(d.get('windows') or []) for d in live)} windows")


if __name__ == "__main__":
    main()
