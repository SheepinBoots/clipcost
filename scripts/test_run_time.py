#!/usr/bin/env python3
"""The price-check run time shows in US time (ET first, PT in brackets), never in the future.

A CI runner stores UTC and a manual run on the box stores Pacific time. Both must show the same instant.
Run: python3 scripts/test_run_time.py
"""
import datetime as dt
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare_pages as cp
import timefmt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UTC = dt.timezone.utc
errors = []


def check(ok, msg):
    if not ok:
        errors.append(msg)


WANT = "Nov 20, 2026, 4:26 PM ET (1:26 PM PT)"
now = dt.datetime(2026, 11, 20, 22, 30, tzinfo=UTC)  # 2:30 PM PT, after the 1:26 PM PT run
cases = {
    "runner UTC with Z": "2026-11-20T21:26:29Z",
    "runner UTC with +00:00": "2026-11-20T21:26:29+00:00",
    "manual PT with offset": "2026-11-20T13:26:29-08:00",
    "manual PT, old stamp without offset": "2026-11-20T13:26:29",
    "runner UTC, old stamp without offset": "2026-11-20T21:26:29",
}
for name, stamp in cases.items():
    got = cp.run_text(stamp, "2026-11-20", now=now)
    check(got == WANT, f"{name}: {got!r}, want {WANT!r}")
    t = timefmt.run_instant(stamp, now)
    check(t is not None and t <= now, f"{name}: instant {t} is in the future")

# Never a future time: a stamp after `now` shows the date only.
check(cp.run_text("2026-11-21T03:00:00Z", "2026-11-20", now=now) == "Nov 20, 2026", "future UTC stamp shown as a time")
check(cp.run_text("2026-11-20T23:59:00", "2026-11-20", now=now) == "Nov 20, 2026", "future stamp without offset shown as a time")
# A run on another US date than the catalog date shows the catalog date only.
check(cp.run_text("2026-11-21T01:00:00Z", "2026-11-21", now=dt.datetime(2026, 11, 21, 2, tzinfo=UTC)) == "Nov 21, 2026",
      "a 5 PM PT run (next day in UTC) is not on the Nov 21 catalog date")
check(cp.run_text("2026-11-21T01:00:00Z", "2026-11-20", now=dt.datetime(2026, 11, 21, 2, tzinfo=UTC))
      == "Nov 20, 2026, 8:00 PM ET (5:00 PM PT)", "evening PT run after midnight UTC")
# Writer: UTC with Z, and a US date whatever the machine's zone.
w = timefmt.now_utc_iso()
check(re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", w) is not None, f"writer stamp {w!r} has no Z")
check(timefmt.us_today() == dt.datetime.now(timefmt.PT).date(), "us_today is not the Pacific date")
src = open(os.path.join(ROOT, "scripts", "update_prices.py"), encoding="utf-8").read()
check('"run": timefmt.now_utc_iso()' in src, "update_prices does not store the run with an offset")
check("datetime.date.today()" not in src and "datetime.datetime.now()" not in src, "update_prices uses the machine's local zone")
# The stored stamp has an offset and is not in the future.
run = json.load(open(os.path.join(ROOT, "data", "check_report.json"))).get("run")
check(run is None or re.search(r"(Z|[+-]\d\d:\d\d)$", run), f"check_report.json run {run!r} has no offset")
check(run is None or timefmt.run_instant(run) is not None, f"check_report.json run {run!r} is in the future")
# Built pages never show Caracas or UTC for the check time.
dist = os.path.join(ROOT, "dist")
for rel in ("compare/kling-3-0-vs-veo-3-1/index.html", "cost/10-second/index.html"):
    path = os.path.join(dist, rel)
    if os.path.exists(path):
        html = open(path, encoding="utf-8").read()
        m = re.search(r"Prices last checked ([^<]*?)\.(?:<| )", html)
        check(m is not None, f"{rel}: no 'Prices last checked'")
        if m:
            check("UTC" not in m.group(1) and "Caracas" not in m.group(1), f"{rel}: {m.group(1)}")
            check(re.fullmatch(r"\w{3} \d{1,2}, \d{4}(, \d{1,2}:\d\d [AP]M ET \(.*PT\))?", m.group(1)) is not None,
                  f"{rel}: not ET first with PT: {m.group(1)}")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"run time ok ({len(cases)} stamp forms show {WANT})")
