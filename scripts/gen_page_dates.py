"""Write data/page_dates.json: the first-published date of each page.

The date is the day (US Eastern) of the first commit that added dist/<path>/index.html.
Run it locally on a full clone; CI uses a shallow checkout, so the build reads the
committed file instead of git. Existing published dates, lastmod, and content hashes
are never moved; new pages get their first-commit date, or today when they are not
committed yet. lastmod and hashes are filled in by page_dates.apply during the build.
"""
import datetime, os, subprocess
from zoneinfo import ZoneInfo

import page_dates

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = page_dates.dates_path(ROOT)
ET = ZoneInfo("America/New_York")

def first_added():
    log = subprocess.run(
        ["git", "log", "--reverse", "--diff-filter=A", "--format=@%at", "--name-only", "--", "dist"],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout
    seen, stamp = {}, None
    for line in log.splitlines():
        line = line.strip()
        if line.startswith("@"):
            stamp = datetime.datetime.fromtimestamp(int(line[1:]), ET).date().isoformat()
        elif line.endswith("index.html") and stamp:
            path = "/" + line[len("dist/"):-len("index.html")]
            seen.setdefault(path, stamp)
    return seen

def main():
    data = page_dates.load(ROOT)
    found = first_added()
    today = datetime.datetime.now(ET).date().isoformat()
    for path, day in found.items():
        rec = data.get(path) or {"published": None, "modified": None, "hash": None}
        if not rec.get("published"):
            rec["published"] = day or today
            data[path] = rec
    page_dates.save(ROOT, data)
    print(f"{len(data)} page dates in {OUT}")

if __name__ == "__main__":
    main()
