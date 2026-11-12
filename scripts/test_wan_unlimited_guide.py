#!/usr/bin/env python3
"""The Wan 3.0 unlimited guide agrees with data/deals.json and prices.json.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_wan_unlimited_guide.py
"""
import datetime, html, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deals

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "dist", "guides", "wan-3-0-unlimited", "index.html")
ENDED = "hf-wan3-unlimited-7d"


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
    text = html.unescape(raw)
    doc = deals.load()
    db = json.load(open(os.path.join(ROOT, "data", "prices.json"), encoding="utf-8"))
    today = datetime.date.today().isoformat()
    errors = []
    title = html.unescape(re.search(r"<title>(.*?)</title>", raw).group(1))
    desc = html.unescape(re.search(r'<meta name="description" content="(.*?)"', raw).group(1))
    if len(title) > 60:
        errors.append(f"title is {len(title)} characters: {title}")
    if len(desc) > 160:
        errors.append(f"description is {len(desc)} characters")
    if '<link rel="canonical" href="https://vidfare.com/guides/wan-3-0-unlimited/">' not in raw:
        errors.append("canonical")
    if "sora" in text.lower():
        errors.append("names Sora")
    if "No vendor we track sells Wan 3.0 as unlimited today" not in text:
        errors.append("missing the no-live-unlimited lead")
    live = [
        d for d in doc["deals"]
        if d.get("type") == "unlimited_window"
        and ("wan-3-0" in (d.get("models") or []) or "wan-3-0-prime" in (d.get("models") or []))
        and deals.is_current(d, today)
    ]
    if live:
        errors.append(f"guide says none are live but deals.json has {[d['id'] for d in live]}")
    ended = next((d for d in doc["deals"] if d["id"] == ENDED), None)
    if not ended:
        errors.append(f"missing {ENDED}")
    else:
        if ended.get("status") != "ended":
            errors.append(f"{ENDED} is not marked ended")
        if "30 seconds" not in text or "1080p" not in text:
            errors.append("changelog caps 30 seconds / 1080p missing")
        if "Pro and above" not in text:
            errors.append("changelog availability missing")
        if ENDED.replace("-", " ") and "7-day" not in text.lower() and "7 days" not in text.lower() and "7-day window" not in text:
            errors.append("ended 7-day window not described")
        if "creator-hub/changelog" not in raw:
            errors.append("changelog source link missing")
        title_on_page = ended.get("title") or ""
        # The official changelog title, or the deal title, should appear in some form.
        if "Unlimited Wan 3.0 for 7 days" not in text and title_on_page not in text:
            errors.append("ended offer title missing")

    rows = {r["id"]: r for r in db["rows"]}
    for rid, needle_model in (("r025", "Replicate"), ("r026", "Replicate"), ("r027", "Replicate"),
                              ("r001", "Higgsfield API"), ("r081", "Ultra"), ("r096", "Ultra")):
        r = rows[rid]
        money = rate_money(r["usd_per_second"])
        if money not in text and money + "/s" not in text:
            # rate_money may already be used with /s in the page
            if money not in text:
                errors.append(f"{rid} rate {money} missing")
        if rid in ("r025", "r001") and needle_model not in text:
            errors.append(f"{rid} platform {needle_model} missing")

    if "fpr=emmanuel-bbfe0e" not in raw:
        errors.append("Higgsfield affiliate fpr missing")
    if "Affiliate links never change this price order" not in text:
        errors.append("affiliate price-order sentence missing")
    sitemap = open(os.path.join(ROOT, "dist", "sitemap.xml"), encoding="utf-8").read()
    if "<loc>https://vidfare.com/guides/wan-3-0-unlimited/</loc>" not in sitemap:
        errors.append("sitemap")
    for rel in (
        "guides/index.html",
        "index.html",
        "models/wan-3-0/index.html",
        "models/wan-3-0-prime/index.html",
    ):
        page = open(os.path.join(ROOT, "dist", rel), encoding="utf-8").read()
        if 'href="/guides/wan-3-0-unlimited/"' not in page:
            errors.append(f"{rel} does not link the guide")
    guides = open(os.path.join(ROOT, "dist", "guides", "index.html"), encoding="utf-8").read()
    if "comparisons built from the same price rows" not in guides:
        errors.append("guides index is missing the comparisons lead")
    if errors:
        raise SystemExit("wan unlimited guide:\n- " + "\n- ".join(errors))
    print("ok wan 3.0 unlimited guide")


if __name__ == "__main__":
    main()
