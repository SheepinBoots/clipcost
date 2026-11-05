#!/usr/bin/env python3
"""Read VidFare MCP tool-request counts from Workers Analytics Engine.

The token needs Account Analytics Read on the VidFare account.
It is not the Worker deploy token.

  CLOUDFLARE_ACCOUNT_ID=... CLOUDFLARE_API_TOKEN=... python3 scripts/mcp_usage.py
  python3 scripts/mcp_usage.py --days 14
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

DATASET = "vidfare_mcp_usage"
LABEL = (
    "tool requests (not unique people, visits, or sponsor impressions; "
    "retries and tests can inflate them)"
)
PACIFIC = ZoneInfo("America/Los_Angeles")


def query(days):
    return (
        "SELECT toDate(timestamp) AS day_utc, blob1 AS tool, blob2 AS outcome, "
        "SUM(_sample_interval * double1) AS requests "
        f"FROM {DATASET} "
        f"WHERE timestamp > NOW() - INTERVAL '{int(days)}' DAY "
        "GROUP BY day_utc, tool, outcome "
        "ORDER BY day_utc, tool, outcome "
        "FORMAT JSON"
    )


def pacific_start(day):
    """UTC midnight of this date, shown on the Pacific clock."""
    start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    return start.astimezone(PACIFIC).strftime("%Y-%m-%d %H:%M %Z")


def rows_from_api(payload):
    data = payload.get("data")
    if isinstance(data, list):
        return data
    return []


def render(rows):
    lines = [
        LABEL,
        "Days are UTC. The time in parentheses is when that UTC day starts in Pacific Time.",
        "",
    ]
    if not rows:
        lines.append("No tool requests in this window.")
        return "\n".join(lines) + "\n"
    current = None
    for row in rows:
        day = datetime.fromisoformat(str(row["day_utc"])).date()
        if day != current:
            current = day
            lines.append(f"{day.isoformat()} UTC (starts {pacific_start(day)})")
        count = row["requests"]
        if isinstance(count, float) and count.is_integer():
            count = int(count)
        lines.append(f"  {row['tool']}  {row['outcome']}  {count}")
    return "\n".join(lines) + "\n"


def fetch(account_id, token, days):
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/analytics_engine/sql"
    request = urllib.request.Request(
        url,
        data=query(days).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise SystemExit(f"Analytics query failed: HTTP {exc.code} {detail}") from exc
    return rows_from_api(payload)


def main(argv=None):
    parser = argparse.ArgumentParser(description=LABEL)
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args(argv)
    if args.days < 1:
        raise SystemExit("--days must be at least 1")
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not account or not token:
        raise SystemExit("Set CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN (Account Analytics Read).")
    print(render(fetch(account, token, args.days)), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
