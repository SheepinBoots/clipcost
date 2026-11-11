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
    print("ok")


if __name__ == "__main__":
    main()
