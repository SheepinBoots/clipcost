#!/usr/bin/env python3
"""#94 rule: keep the end signup; keep the mid signup only when a full section sits between the two boxes.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_double_signup_rule.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
SRC = os.path.join(ROOT, "scripts", "build_site.py")
MID = '<section class="news news-inline" id="newsletter-inline">'
END = '<section class="news" id="newsletter">'
# The 9 model pages are the ones that lose the mid box after #90 moved it
# below the price table, leaving only short data-page link lines before the end box.
MODEL_LOSE_MID = [
    "/models/gemini-omni-flash/",
    "/models/grok-imagine/",
    "/models/kling-3-0/",
    "/models/minimax-hailuo/",
    "/models/runway-gen-4/",
    "/models/seedance-2-5/",
    "/models/veo-3-1/",
    "/models/wan-3-0-prime/",
    "/models/wan-3-0/",
]
errors = []


def check(ok, msg):
    if not ok:
        errors.append(msg)


def load_prune():
    text = open(SRC, encoding="utf-8").read()
    start = text.find("INLINE_NEWS_MARK = ")
    end = text.find("\ndef news_box_inline(", start)
    if start < 0 or end < 0:
        raise SystemExit("could not find prune helpers in build_site.py")
    ns = {"re": re}
    exec(text[start:end], ns)
    return ns["prune_close_mid_signup"]


prune = load_prune()

MID_BOX = f'{MID}<h2 style="margin-top:0">Mid</h2><form></form></section>'
END_BOX = f'{END}<h2 style="margin-top:0">End</h2><form></form></section>'


def trial(between):
    return prune("INTRO\n" + MID_BOX + "\n" + between + "\n" + END_BOX)


# Link lines only, as on model pages after #90: drop mid.
out = trial('<p class="small">Compare: <a href="/compare/x/">X</a>.</p>\n<p class="small">Clip cost: <a href="/cost/10-second/">10s</a>.</p>')
check(MID not in out and END in out, "link-only between should drop the mid signup")

# Heading plus table: keep mid.
out = trial("<h2>Rates</h2><div class=\"tblwrap\"><table><tr><td>1</td></tr></table></div>")
check(MID in out and END in out, "h2 plus table should keep the mid signup")

# Heading plus FAQ: keep mid.
out = trial("<h2>FAQ</h2><div class=\"faq\"><h3>Q</h3><p>A</p></div>")
check(MID in out and END in out, "h2 plus FAQ should keep the mid signup")

# Heading plus prose: keep mid (budget guide and similar).
out = trial("<h2>How much does a 1-minute clip cost?</h2><p>A finished minute at 3x retries is 180 billed seconds.</p>")
check(MID in out and END in out, "h2 plus prose should keep the mid signup")

# Heading plus list: keep mid.
out = trial("<h2>Takeaways</h2><ul><li>One</li><li>Two</li></ul>")
check(MID in out and END in out, "h2 plus list should keep the mid signup")

# No heading: drop mid.
out = trial("<p>A lone paragraph with no heading.</p>")
check(MID not in out and END in out, "no heading should drop the mid signup")

# Only one of the two boxes: leave body alone.
check(prune("hello " + MID_BOX) == "hello " + MID_BOX, "mid-only body should be unchanged")
check(prune("hello " + END_BOX) == "hello " + END_BOX, "end-only body should be unchanged")


def walk_pages():
    rows = []
    for dirpath, _, files in os.walk(DIST):
        if "index.html" not in files:
            continue
        rel = os.path.relpath(dirpath, DIST)
        path = "/" if rel == "." else "/" + rel.replace(os.sep, "/") + "/"
        html = open(os.path.join(dirpath, "index.html"), encoding="utf-8").read()
        rows.append((path, MID in html, END in html))
    return rows


pages = walk_pages()
lost = sorted(p for p, mid, end in pages if end and not mid and p.startswith("/models/"))
# Every model page in the catalog should be in lost, and nothing else should newly lose mid
# relative to the pre-rule set of 45. Hubs that already had end-only are excluded.
check(lost == MODEL_LOSE_MID, f"model pages that lose mid: {lost}")
for path, mid, end in pages:
    if path in MODEL_LOSE_MID:
        check(end and not mid, f"{path}: expected end signup only")
    elif path.startswith("/guides/") and path != "/guides/":
        check(mid and end, f"{path}: guides keep mid when a full section sits between the boxes")
    elif path.startswith(("/compare/", "/cost/", "/platforms/")) or path == "/price-index/":
        check(mid and end, f"{path}: data pages should keep mid and end")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"double-signup rule ok (mid dropped on {len(MODEL_LOSE_MID)} model pages; guides and data pages keep both)")
