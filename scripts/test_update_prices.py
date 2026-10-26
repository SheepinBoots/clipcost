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
    print("ok")


if __name__ == "__main__":
    main()
