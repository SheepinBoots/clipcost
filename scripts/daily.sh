#!/usr/bin/env bash
# Daily routine: re-check every source, apply API price changes to the log, rebuild the static site.
# Exit 0 includes API price changes this run applied. Exit 1 means a number is missing or a change was not applied.
set -u
cd "$(dirname "$0")/.."
python3 scripts/update_prices.py --apply; status=$?
python3 scripts/build_site.py
exit $status
