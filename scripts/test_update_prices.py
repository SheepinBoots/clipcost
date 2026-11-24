#!/usr/bin/env python3
"""Exit-code rules for the daily price check."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import update_prices as up

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    assert up.exit_code([], False) == 0
    applied = {"status": "changed", "applied": True}
    assert up.exit_code([applied, dict(applied)], False) == 0
    assert up.exit_code([{"status": "missing"}], False) == 1
    assert up.exit_code([applied, {"status": "missing"}], False) == 1
    assert up.exit_code([{"status": "changed"}], False) == 1
    assert up.exit_code([{"status": "deal_candidate"}], False) == 1
    assert up.exit_code([], True) == 2
    assert up.exit_code([{"status": "missing"}], True) == 2
    assert up.retired({"discontinued_on": "2026-10-22"}, "2026-10-23") is True
    assert up.retired({"discontinued_on": "2026-10-23"}, "2026-10-23") is False
    assert up.retired({}, "2026-10-23") is False
    assert up.retired({"status": "discontinued"}, "2026-10-23") is True
    assert up.retired({"status": "verified"}, "2026-10-23") is False
    # Atlas no longer server-renders this card. The price is in the Next.js flight payload.
    db = json.load(open(os.path.join(ROOT, "data", "prices.json")))
    needle = next(c["needle"] for r in db["rows"] if r["id"] == "r077" for c in r["checks"])
    phrase = needle.replace("{N}", "0.099")
    html = "<html><p>MiniMax only</p><script>self.__next_f.push([1," + json.dumps(phrase) + "])</script></html>"
    assert "0.099" not in up.collapse(__import__("bs4").BeautifulSoup(html, "html.parser").get_text(" ", strip=True))
    text = up.next_flight_text(html)
    status, value = up.check(text, {"needle": needle, "expect": 0.099})
    assert status == "ok" and value == 0.099, (status, value)
    assert up.next_flight_text("<html><p>no payload</p></html>") == ""
    assert up.check("visible only", {"needle": needle, "expect": 0.099})[0] == "missing"
    # Replicate hides the billing table in a JSON script BeautifulSoup drops.
    billing = '<script type="application/json">{"billingConfig":{"current_tiers":[{"title":"480p","prices":[{"price":"$0.035","title":"per second of output video"}]},{"title":"720p","prices":[{"price":"$0.07","title":"per second of output video"}]},{"title":"1080p","prices":[{"price":"$0.14","title":"per second of output video"}]}]}}</script>'
    billed = up.billing_tier_text(billing)
    assert up.check(billed, {"needle": "480p: ${N} per second", "expect": 0.035}) == ("ok", 0.035)
    assert up.check(billed, {"needle": "720p: ${N} per second", "expect": 0.07}) == ("ok", 0.07)
    assert up.check(billed, {"needle": "1080p: ${N} per second", "expect": 0.14}) == ("ok", 0.14)
    assert up.billing_tier_text("<html><p>no billing</p></html>") == ""
    # Tiers with a null title (Replicate Seedance 2.5) use criteria as the label.
    untitled = '<script type="application/json">{"billingConfig":{"current_tiers":[{"title":null,"criteria":[{"title":"model variant","description":"non_video_in","value":"non_video_in"},{"title":"target resolution","description":"480p","value":"480p"}],"prices":[{"price":"$0.1028","title":"per second of output video"}]}]}}</script>'
    untitled_text = up.billing_tier_text(untitled)
    assert up.check(untitled_text, {"needle": "model variant is non_video_in, target resolution is 480p: ${N} per second of output video", "expect": 0.1028}) == ("ok", 0.1028)
    assert up.check("if voice control is used you will be charged $0.196 .", {"needle": "you will be charged $0.196", "phrase": True})[0] == "ok"
    assert up.check("no voice price", {"needle": "you will be charged $0.196", "phrase": True})[0] == "missing"
    # A missed phrase has no expect. The report must record it instead of raising.
    missed = {"needle": "you will be charged $0.196", "phrase": True}
    assert missed.get("expect") is None
    # Krea's server HTML now has one monthly price. Yearly card digits are appended as labeled text.
    yearly = "Basic yearly was $9/month Basic yearly card $5/month Pro yearly was $35/month Pro yearly card $21/month"
    assert up.check(yearly, {"needle": "Basic yearly card ${N}/month", "expect": 5}) == ("ok", 5.0)
    assert up.check(yearly, {"needle": "Pro yearly card ${N}/month", "expect": 21}) == ("ok", 21.0)
    assert up.check(yearly, {"needle": "Pro yearly was ${N}/month", "expect": 35}) == ("ok", 35.0)
    assert up.check("Pro yearly card $21 Max", {"needle": "Pro yearly card ${N}", "expect": 21}) == ("changed", 21000000.0)
    # Google Flow plans, credit costs, and notices are checked like rows, against their own sources.
    flow = up.flow_items(db)
    kinds = {kind for kind, _ in flow}
    assert {"flow_plan", "flow_cost", "flow_notice", "flow_daily", "flow_plan_credits_check"} <= kinds, kinds
    for kind, rec in flow:
        assert rec["source"] in db["sources"], (kind, rec["id"])
        assert rec.get("checks"), (kind, rec["id"])
        assert rec.get("source_url", "").startswith("https://"), (kind, rec["id"])
        assert rec.get("checked"), (kind, rec["id"])
    assert up.retired({"retiring_on": "2026-12-05"}, "2026-12-04") is False
    assert up.retired({"retiring_on": "2026-12-05"}, "2026-12-05") is True
    lite = next(rec for kind, rec in flow if rec["id"] == "flow-veo31-lite")
    text = "Veo 3.1 - Lite 4s, 6s, 8s videos Non-Ultra subscribers: 10 Ultra subscribers: 5 Veo 3.1 - Fast"
    assert [up.check(text, c)[0] for c in lite["checks"] if not c.get("phrase")] == ["ok", "ok"]
    # Krea's plan cards come in several A/B layouts. The embedded SvelteKit plan data
    # is read instead, and only amounts marked currency="usd" are emitted.
    krea_html = ('(function(a,b,c,d,e,f,g,h){a.amount=9;a.currency="usd";b.amount=63;b.currency="usd";'
                 'c.amount=9;c.currency="usd";d.amount=84;d.currency="usd";e.amount=35;e.currency="usd";'
                 'f.amount=252;f.currency="usd";g.amount=35;g.currency="usd";h.amount=336;h.currency="usd";'
                 'return {plansAndPrices:{creator_basic:{monthly:a,yearly:b,yearlyDiscountPercent:40,originalMonthly:c,originalYearly:d},'
                 'creator_pro:{monthly:e,yearly:f,yearlyDiscountPercent:50,originalMonthly:g,originalYearly:h}},'
                 'planCards:[{planId:"creator_basic",computeUnits:5000,name:"Basic"},{planId:"creator_pro",computeUnits:20000,name:"Pro"}]}}')
    krea_text = up.krea_plan_text(krea_html)
    for pid in ("krea-basic-yearly", "krea-pro-monthly", "krea-pro-yearly"):
        for c in db["plans"][pid]["checks"]:
            if c["needle"].startswith("Krea USD"):
                assert up.check(krea_text, c)[0] == "ok", (pid, c, krea_text)
    euro_text = up.krea_plan_text(krea_html.replace('currency="usd"', 'currency="eur"'))
    assert "$" not in euro_text and "monthly" not in euro_text, euro_text
    assert up.check(euro_text, {"needle": "Krea USD Pro monthly ${N}/month", "expect": 35})[0] == "missing"
    # A sale-priced plan keeps its sale price until the official end, then switches to the
    # regular price only when the vendor page shows it. Rows are re-derived, never deleted.
    import copy, datetime as dt
    real_append = up.weekly_report.append_event
    up.weekly_report.append_event = lambda event: True
    try:
        base = {"plans": {"kp": {"platform": "Krea", "usd_month": 21, "credits_month": 20000, "source": "krea",
                                 "checks": [{"needle": "Krea USD Pro yearly ${N}/year", "expect": 252}],
                                 "sale": {"deal_id": "d", "ends_at": "2026-11-22T08:00:00Z",
                                          "regular": {"usd_month": 28, "checks": [{"needle": "Krea USD Pro yearly ${N}/year", "expect": 336}]}}}},
                "rows": [{"id": "x1", "model": "m", "platform": "Krea", "variant": "v", "resolution": "480p", "kind": "plan",
                          "plan": "kp", "credits_per_clip": 100.0, "clip_seconds": 2, "status": "estimate",
                          "usd_per_clip": 0.105, "usd_per_second": 0.0525, "source_url": "u", "checked": "2026-11-20",
                          "math": "Krea says ~200 clips on Pro (20,000 units) → ~100 units/clip. $21/mo ÷ 20,000 units = $0.00105/unit; ~100.0 units/clip (2s) → $0.105/clip → $0.0525/s"}],
                "models": {}}
        before = dt.datetime(2026, 11, 22, 7, 59, tzinfo=dt.timezone.utc)
        after = dt.datetime(2026, 11, 22, 16, 0, tzinfo=dt.timezone.utc)
        db1, f1, log1 = copy.deepcopy(base), [], []
        assert up.apply_plan_sales(db1, {"krea": "Krea USD Pro yearly $336/year"}, f1, log1, before, "2026-11-21") == []
        assert db1 == base and not f1 and not log1
        db2, f2, log2 = copy.deepcopy(base), [{"kind": "plan", "id": "kp", "status": "changed"}], []
        assert up.apply_plan_sales(db2, {"krea": "Krea USD Pro yearly $336/year"}, f2, log2, after, "2026-11-22") == ["kp"]
        assert db2["plans"]["kp"]["usd_month"] == 28 and "sale" not in db2["plans"]["kp"]
        assert db2["plans"]["kp"]["checks"][0]["expect"] == 336
        assert len(db2["rows"]) == 1 and db2["rows"][0]["usd_per_second"] == 0.07 and db2["rows"][0]["checked"] == "2026-11-22"
        assert "$28/mo ÷ 20,000 units" in db2["rows"][0]["math"] and db2["rows"][0]["math"].startswith("Krea says ~200 clips")
        assert log2 and log2[0]["new_usd_per_second"] == 0.07 and up.exit_code(f2, False) == 0
        db3, f3, log3 = copy.deepcopy(base), [], []
        assert up.apply_plan_sales(db3, {"krea": "Krea USD Pro yearly $300/year"}, f3, log3, after, "2026-11-22") == []
        assert db3 == base and f3[0]["status"] == "sale_end_unconfirmed" and up.exit_code(f3, False) == 1
    finally:
        up.weekly_report.append_event = real_append
    # The Krea yearly plans in the catalog carry a sale block that ends at Krea's own deadline.
    for pid, month in (("krea-basic-yearly", 7), ("krea-pro-yearly", 28)):
        sale = db["plans"][pid]["sale"]
        assert sale["ends_at"] == "2026-11-26T08:00:00Z" and sale["regular"]["usd_month"] == month
    print("ok")


if __name__ == "__main__":
    main()
