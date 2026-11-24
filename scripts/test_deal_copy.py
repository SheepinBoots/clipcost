#!/usr/bin/env python3
"""Guides must never show an ended deal as live.

1. Unit checks on deals.ends_at_passed and the deal_copy wording.
2. The built dist/: for every deal that is not current, no guide says it is
   live or that it "ends"/"is live until" its end time.
3. A throwaway build with the clock moved just past the Higgsfield Black
   Friday ends_at (VIDFARE_NOW): every Higgsfield guide, the free guide and
   /deals/black-friday/ must switch to "ended" copy.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_deal_copy.py
"""
import datetime
import glob
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deal_copy
import deals as dealmod
from timefmt import us_today

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HF_GUIDES = (
    "guides/higgsfield-black-friday",
    "guides/higgsfield-pricing",
    "guides/higgsfield-promo-code",
    "guides/free-ai-video-generators",
)


def visible(path):
    raw = open(path, encoding="utf-8").read()
    body = re.sub(r"<script.*?</script>", " ", raw, flags=re.S)
    text = html.unescape(re.sub(r"<[^>]+>", " ", body))
    meta = " ".join(html.unescape(m) for m in re.findall(r'<meta [^>]*content="([^"]*)"', raw))
    ld = " ".join(html.unescape(m) for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S))
    return re.sub(r"\s+", " ", text + " " + meta + " " + ld)


def load_deals():
    doc = json.load(open(os.path.join(ROOT, "data", "deals.json"), encoding="utf-8"))
    return doc["deals"] if isinstance(doc, dict) else doc


def live_phrases(d):
    """Wording that would present deal d as still running."""
    out = []
    for long_month in (False, True):
        label = deal_copy.end_label(d, long_month=long_month)
        if label and d.get("ends_at"):
            out += [f"live until {label}", f"ends {label}", f"Ends {label}", f"is on until {label}"]
    return out


def check_dist(dist, records, today, errors, now=None):
    ended = [d for d in records if not dealmod.is_current(d, today) and d.get("ends_at")]
    if now is not None:
        ended = [d for d in records if d.get("ends_at") and dealmod.ends_at_passed(d, now=now)]
    pages = sorted(glob.glob(os.path.join(dist, "guides", "*", "index.html")))
    if not pages:
        errors.append(f"no guide pages under {dist}")
    for page in pages:
        text = visible(page)
        rel = os.path.relpath(page, dist)
        for d in ended:
            for phrase in live_phrases(d):
                if phrase in text:
                    errors.append(f"{rel}: ended deal {d['id']} shown as live ({phrase!r})")


def check_hf_ended(dist, errors, label):
    for rel in HF_GUIDES:
        page = os.path.join(dist, rel, "index.html")
        if not os.path.isfile(page):
            errors.append(f"{label}: {rel} missing")
            continue
        text = visible(page)
        for bad in ("sale is live", "is live on its pricing page until", "Black Friday prices are on the plan cards",
                    "A Black Friday sale is on", "Black Friday sale prices, credits"):
            if bad in text:
                errors.append(f"{label}: {rel} shows the ended Higgsfield sale as live ({bad!r})")
        if "higgsfield" in rel and "has ended" not in text:
            errors.append(f"{label}: {rel} does not say the Higgsfield sale has ended")
    promo = open(os.path.join(dist, "guides", "higgsfield-promo-code", "index.html"), encoding="utf-8").read()
    cur = re.search(r'id="prices".*?</table>', promo, re.S)
    if cur and "Black Friday" in cur.group(0):
        errors.append(f"{label}: promo code page lists the ended Black Friday sale as a current deal")
    bf = visible(os.path.join(dist, "deals", "black-friday", "index.html"))
    if "Higgsfield Black Friday sale ends" in bf:
        errors.append(f"{label}: /deals/black-friday/ still says the Higgsfield sale ends")


def main():
    errors = []
    # 1. ends_at is exact.
    probe = {"id": "p", "status": "live", "end": "2026-11-24", "ends_at": "2026-11-25T00:00:00Z"}
    utc = datetime.timezone.utc
    if dealmod.ends_at_passed(probe, now=datetime.datetime(2026, 11, 24, 23, 59, 59, tzinfo=utc)):
        errors.append("ends_at_passed is true before ends_at")
    if not dealmod.ends_at_passed(probe, now=datetime.datetime(2026, 11, 25, 0, 0, 0, tzinfo=utc)):
        errors.append("ends_at_passed is false at ends_at")
    live_state = {"live": True, "deals": {"hf-plus-annual": {"price_after": 30}, "hf-ultra-annual": {"price_after": 45}},
                  "end": "Nov 24, 2026, 7:00 PM ET (4:00 PM PT)", "verified": "2026-11-24"}
    ended_state = dict(live_state, live=False)
    if "live" not in deal_copy.hf_sale_sentence(live_state) or "ended" in deal_copy.hf_sale_sentence(live_state):
        errors.append("live sale sentence wording")
    s = deal_copy.hf_sale_sentence(ended_state)
    if "has ended" not in s or "live" in s or "$30" in s:
        errors.append(f"ended sale sentence wording: {s}")

    records = load_deals()
    today = us_today().isoformat()
    # 2. The real build.
    dist = os.path.join(ROOT, "dist")
    if not os.path.isdir(os.path.join(dist, "guides")):
        raise SystemExit("build the site before running this test")
    check_dist(dist, records, today, errors)
    if not deal_copy.hf_bf({})["live"]:
        check_hf_ended(dist, errors, "dist")

    # 3. A build with the clock just past the Higgsfield Black Friday end.
    ends = [d["ends_at"] for d in records if d["id"] in deal_copy.HF_BF_IDS and d.get("ends_at")]
    if ends:
        end = max(datetime.datetime.fromisoformat(e.replace("Z", "+00:00")) for e in ends)
        now = max(end, datetime.datetime.now(utc)) + datetime.timedelta(seconds=1)
        tmp = tempfile.mkdtemp(prefix="vidfare-ended-")
        try:
            env = dict(os.environ, VIDFARE_DIST=tmp, VIDFARE_SKIP_VIEWPORT="1",
                       VIDFARE_NOW=now.strftime("%Y-%m-%dT%H:%M:%SZ"))
            res = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "build_site.py")],
                                 env=env, cwd=ROOT, capture_output=True, text=True)
            if res.returncode != 0:
                errors.append("ended-clock build failed: " + (res.stderr or res.stdout)[-400:])
            else:
                check_dist(tmp, records, today, errors, now=now)
                check_hf_ended(tmp, errors, "ended-clock build")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    if errors:
        raise SystemExit("deal copy check failed:\n- " + "\n- ".join(errors))
    print("ok deal copy: no guide shows an ended deal as live")


if __name__ == "__main__":
    main()
