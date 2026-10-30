#!/usr/bin/env python3
"""Deal math and expiry. Run: python3 scripts/test_deals.py"""
import datetime, json, os, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deals

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = "2026-10-20"
OFFICIAL_HOSTS = (
    "higgsfield.ai", "x.com", "krea.ai", "magnific.com", "runwayml.com", "fal.ai",
)


def close(a, b, eps=1e-9):
    if abs(a - b) > eps:
        raise SystemExit(f"{a} != {b}")


def main():
    doc = deals.load()
    db = json.load(open(os.path.join(ROOT, "data", "prices.json")))
    rows = {r["id"]: r for r in db["rows"]}
    plans = db["plans"]
    live = [d for d in doc["deals"] if deals.is_current(d, TODAY)]
    ids = [d["id"] for d in live]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate deal ids")
    for deal in live:
        if deal["type"] not in deals.TYPES:
            raise SystemExit(f"bad type {deal['id']}")
        for key in ("vendor", "models", "plans", "conditions", "status", "source_url", "source_quote", "verified_date"):
            if key not in deal:
                raise SystemExit(f"{deal['id']} missing {key}")
        host = deals_host(deal["source_url"])
        if not any(host == h or host.endswith("." + h) for h in OFFICIAL_HOSTS):
            raise SystemExit(f"{deal['id']} source is not a vendor or official account: {host}")
        if deal["status"] != "live":
            raise SystemExit(deal["id"])
    # Stated API rates, not a recomputed anchor percent.
    wan = rows["r002"]
    adj = deals.adjustment(by_id(live, "hf-api-wan-60"), wan, plans)
    close(adj["usd"], 0.056)
    close(adj["list_usd"], 0.14)
    mini = rows["r186"]
    adj = deals.adjustment(by_id(live, "fal-minimax-35"), mini, plans)
    close(adj["usd"], 0.01625)
    close(adj["list_usd"], 0.025)
    # Banner percent is not applied to rows.
    banner = by_id(live, "hf-banner-30")
    for row in db["rows"]:
        if deals.adjustment(banner, row, plans) is not None:
            raise SystemExit("banner percent leaked onto a row")
    kling25 = by_id(live, "mag-kling25-unlimited")
    for row in db["rows"]:
        if deals.adjustment(kling25, row, plans) is not None:
            raise SystemExit(f"Kling 2.5 unlimited matched {row['id']}")
    # Annual checkout price / credits, not 20% off the row.
    plus = next(r for r in db["rows"] if r["id"] == "r080")
    adj = deals.adjustment(by_id(live, "hf-plus-annual"), plus, plans)
    close(adj["usd"], 47 / 1200 * 7.5 / 5)
    close(adj["usd"], 0.05875)
    # Krea yearly 40% uses $21, not a second discount on the yearly row's neighbors.
    krea = next(r for r in db["rows"] if r.get("plan") == "krea-pro-monthly" and r["model"] == "wan-3-0-prime")
    adj = deals.adjustment(by_id(live, "krea-yearly-40"), krea, plans)
    close(adj["usd"], 21 / 20000 * krea["credits_per_clip"] / krea["clip_seconds"])
    # Blended 12-month price for a first-N-months code.
    close(deals.blended_price(50, 100, 3), 87.5)
    synthetic = {
        "id": "code-3mo", "vendor": "Higgsfield", "type": "promo_code", "math": "plan_price",
        "models": [], "plans": ["Plus"], "full_plan_id": "hf-plus-monthly", "deal_plan_id": None,
        "price_before": 59, "price_after": 29.5, "percent": 50, "status": "live", "end": None,
        "conditions": {"first_months": 3, "code": "EXAMPLE", "annual_only": False, "standing": False,
                       "new_users_only": True, "max_resolution": None, "web_only": False},
    }
    adj = deals.adjustment(synthetic, plus, plans)
    close(adj["usd"], 29.5 / 1200 * 7.5 / 5)
    blended = deals.blended_price(29.5, 59, 3)
    close(adj["blended_usd"], blended / 1200 * 7.5 / 5)
    # Bonus credits: price / (credits + bonus) * credits per second.
    bonus = {
        "id": "bonus", "vendor": "Higgsfield", "type": "bonus_credits", "math": "bonus",
        "models": ["wan-3-0-prime"], "plans": ["Plus"], "bonus_credits": 300, "status": "live",
        "show_on_rows": True, "conditions": {},
    }
    # Force a match via models + plan name.
    adj = deals.adjustment(bonus, plus, plans)
    close(adj["usd"], 59 / (1200 + 300) * 7.5 / 5)
    # Unlimited is break-even seconds, never $0. The Wan window is archived after the page check.
    starter = next(r for r in db["rows"] if r["id"] == "r078")
    wan_un = next(d for d in doc["deals"] if d["id"] == "hf-wan3-unlimited-7d")
    if wan_un["status"] != "ended" or deals.is_current(wan_un, "2026-10-21"):
        raise SystemExit("wan unlimited window should be archived")
    adj = deals.adjustment(dict(wan_un, status="live"), starter, plans)
    if adj["usd"] == 0 or adj["usd"] is not None:
        raise SystemExit(f"unlimited leaked a $/s: {adj['usd']}")
    close(adj["breakeven_seconds"], 19 / starter["usd_per_second"])
    # Expiry archives by end date and the next day hides the estimated window.
    window = dict(wan_un, status="live", end="2026-10-20")
    if not deals.is_current(window, "2026-10-20"):
        raise SystemExit("window should still be live on the estimated end date")
    if deals.is_current(window, "2026-10-21"):
        raise SystemExit("window should archive after the end date")
    unlimited = by_id(live, "runway-kling4-unlimited-3d")
    if unlimited.get("math") != "none" or unlimited.get("show_on_rows") is not False or unlimited.get("end") is not None:
        raise SystemExit("runway-kling4-unlimited-3d should not invent a rate or an end date")
    if any(deals.adjustment(unlimited, row, plans) for row in db["rows"]):
        raise SystemExit("runway-kling4-unlimited-3d matched a catalog row")
    runway25 = by_id(live, "runway-kling4-25")
    if runway25.get("math") != "none" or runway25.get("show_on_rows") is not False:
        raise SystemExit("runway-kling4-25 should not invent a rate")
    if runway25.get("end") != "2026-11-30" or runway25.get("end_is_estimate"):
        raise SystemExit("runway-kling4-25 end date should be the pricing-page date 2026-11-30")
    if any(deals.adjustment(runway25, row, plans) for row in db["rows"]):
        raise SystemExit("runway-kling4-25 matched a catalog row")
    sample = json.loads(json.dumps(doc))
    sample["deals"] = [dict(by_id(live, "fal-minimax-35"))]
    log = []
    moved = deals.expire_deals(sample, "2026-10-31", log)
    if moved or sample["deals"][0]["status"] != "live":
        raise SystemExit("deal should stay live on its end date")
    moved = deals.expire_deals(sample, "2026-11-01", log)
    if sample["deals"][0]["status"] != "ended" or not moved:
        raise SystemExit("deal should archive after the end date")
    # Snippet diff flags new sale text and does not publish it.
    with tempfile.TemporaryDirectory() as tmp:
        deals.SNAPSHOT_DIR = os.path.join(tmp, "snaps")
        deals.CANDIDATES_PATH = os.path.join(tmp, "cand.json")
        watch_doc = {"watch": [{"id": "ex", "vendor": "fal", "url": "https://example.test/pricing", "fetch": "static"}]}
        pages = {}

        def fetch(page):
            return pages[page["id"]]

        pages["ex"] = "Welcome. Nothing to see."
        first = deals.scan_pricing_pages(fetch, watch_doc, TODAY)
        if first["candidates"]:
            raise SystemExit("baseline should not publish candidates")
        pages["ex"] = "Welcome. Wan is 40% off this week only."
        second = deals.scan_pricing_pages(fetch, watch_doc, TODAY)
        if not any(c["status"] == "unconfirmed" and "40% off" in c["snippet"] for c in second["candidates"]):
            raise SystemExit(f"missed new sale text: {second['candidates']}")
        pages["ex"] = "Welcome. Nothing to see."
        third = deals.scan_pricing_pages(fetch, watch_doc, "2026-10-21")
        if not any(c["status"] == "possible_end" for c in third["candidates"]):
            raise SystemExit("removed sale text should be flagged, not deleted from deals")
    wan60 = next(d for d in doc["deals"] if d["id"] == "hf-api-wan-60")
    if wan60["end"] != "2026-11-01" or wan60["status"] != "live" or wan60.get("percent") != 60:
        raise SystemExit("hf-api-wan-60 end, status, or percent changed")
    reply = "https://x.com/higgsfield_ai/status/2110074252171116649"
    extra_urls = [s.get("url") for s in wan60.get("sources") or [] if isinstance(s, dict)]
    if reply not in extra_urls or reply == wan60.get("source_url"):
        raise SystemExit("hf-api-wan-60 missing the Oct 31 reply as a second source")
    if "Oct 31" not in wan60.get("notes", "") or "Nov 1" not in wan60.get("notes", ""):
        raise SystemExit("hf-api-wan-60 missing the Oct 31 / Nov 1 note")
    kling4 = next(d for d in doc["deals"] if d["id"] == "hf-kling4-launch")
    if kling4.get("percent") is not None or kling4.get("type") != "percent_off" or kling4.get("status") != "live":
        raise SystemExit("hf-kling4-launch should be a live percent_off deal with no percent")
    if kling4.get("models") != ["kling-4-0"] or kling4.get("start") != "2026-10-21" or kling4.get("end") is not None:
        raise SystemExit("hf-kling4-launch models, start, or end")
    if kling4.get("source_kind") != "changelog":
        raise SystemExit("hf-kling4-launch source_kind")
    if "klingai.com" in json.dumps(doc["deals"]):
        raise SystemExit("do not add an unverified klingai.com promo")
    # History stays out of the live list.
    if any(d.get("season") == "2025" and deals.is_current(d, TODAY) for d in doc["history"]):
        raise SystemExit("2025 history was treated as live")
    print(f"ok {len(live)} live deals")


def by_id(deals_list, deal_id):
    return next(d for d in deals_list if d["id"] == deal_id)


def deals_host(url):
    from urllib.parse import urlsplit
    return (urlsplit(url).hostname or "").lower()


if __name__ == "__main__":
    main()
