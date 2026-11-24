"""Write data/page_dates.json: the first-published date of each page.

The date is the day (US Eastern) of the first commit that added dist/<path>/index.html.
Run it locally on a full clone; CI uses a shallow checkout, so the build reads the
committed file instead of git. Existing entries are never moved; new pages get their
first-commit date, or today when they are not committed yet.
"""
import datetime, json, os, subprocess, sys
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "page_dates.json")
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
    data = json.load(open(OUT)) if os.path.exists(OUT) else {}
    found = first_added()
    for path, day in found.items():
        data.setdefault(path, day)
    data = dict(sorted(data.items()))
    with open(OUT, "w") as f:
        json.dump(data, f, indent=1)
        f.write("\n")
    print(f"{len(data)} page dates in {OUT}")

if __name__ == "__main__":
    main()
