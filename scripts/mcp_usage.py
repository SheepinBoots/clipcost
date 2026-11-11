#!/usr/bin/env python3
"""Read VidFare MCP usage counts from Workers Analytics Engine.

Points are anonymous: method, tool name, coarse client bucket, and a probe
flag. The token needs Account Analytics Read on the VidFare account.
It is not the Worker deploy token. Do not commit the token.

  CLOUDFLARE_ACCOUNT_ID=... CLOUDFLARE_API_TOKEN=... python3 scripts/mcp_usage.py
  python3 scripts/mcp_usage.py --days 7
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
    "requests (not unique people, visits, or sponsor impressions; "
    "retries can inflate them). v2 points only"
)
PACIFIC = ZoneInfo("America/Los_Angeles")


def query(days):
    return (
        "SELECT toDate(timestamp) AS day_utc, blob1 AS method, blob2 AS tool, "
        "blob3 AS client, SUM(_sample_interval) AS requests, "
        "SUM(_sample_interval * double1) AS probes, "
        "SUM(_sample_interval) - SUM(_sample_interval * double1) AS non_probes "
        f"FROM {DATASET} "
        "WHERE blob8 = 'v2' "
        f"AND timestamp > NOW() - INTERVAL '{int(days)}' DAY "
        "GROUP BY day_utc, method, tool, client "
        "ORDER BY day_utc, method, tool, client "
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
        lines.append("No requests in this window.")
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
        probes = row["probes"]
        non_probes = row["non_probes"]
        if isinstance(probes, float) and probes.is_integer():
            probes = int(probes)
        if isinstance(non_probes, float) and non_probes.is_integer():
            non_probes = int(non_probes)
        lines.append(
            f"  {row['method']}  {row['tool']}  {row['client']}  "
            f"{count}  probes {probes}  non-probes {non_probes}"
        )
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
