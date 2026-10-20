#!/usr/bin/env bash
# Daily routine: re-check every source, apply API price changes to the log, rebuild the static site.
# Exit 1 from update_prices.py means "something changed or a number went missing - review data/check_report.json".
set -u
cd "$(dirname "$0")/.."
python3 scripts/update_prices.py --apply; status=$?
python3 scripts/build_site.py
exit $status
