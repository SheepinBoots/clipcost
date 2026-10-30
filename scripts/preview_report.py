#!/usr/bin/env python3
"""Render weekly report pages into a local preview directory.

The deployed site stays unchanged: REPORTS_ENABLED in scripts/build_site.py
still controls dist/. This command writes the reports index and, when one
qualifies, the latest eligible week.

  python3 scripts/preview_report.py
  python3 scripts/preview_report.py --as-of 2026-10-30
  python3 scripts/preview_report.py --out /tmp/vidfare-preview
"""
import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(description="Preview the latest eligible weekly price report.")
    parser.add_argument("--as-of", help="ISO date. Default is today. The week closes on Friday.")
    parser.add_argument("--out", default=os.path.join(ROOT, "preview"), help="Directory to write.")
    args = parser.parse_args()
    out = os.path.abspath(args.out)
    env = os.environ.copy()
    env["VIDFARE_REPORT_PREVIEW"] = "1"
    env["VIDFARE_PREVIEW_DIR"] = out
    if args.as_of:
        env["VIDFARE_AS_OF"] = args.as_of
    subprocess.check_call([sys.executable, os.path.join(ROOT, "scripts", "build_site.py")], cwd=ROOT, env=env)
    status = os.path.join(out, "STATUS.txt")
    if os.path.isfile(status):
        print(open(status, encoding="utf-8").read(), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
