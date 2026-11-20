#!/usr/bin/env python3
"""Mid-page signup and sponsor box on model pages, /compare/, /cost/, /platforms/ and /price-index/ (home has only the end signup).

Run after the build: python3 scripts/build_site.py && python3 scripts/test_mid_signup.py
- one mid signup (newsletter-signup-inline) and one end signup (newsletter-signup) per page,
  both the Kit form 10170819, unique input ids, the end box loads the reCAPTCHA helper and ck.5.js
- the mid box sits at the chosen section boundary, never inside a table, list or section
- the new data pages carry the model-page sponsor box (house fallback) and the PixelDojo line after it
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare_pages as cp
import cost_pages as cost
import platform_pages as plat

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
MID = '<section class="news news-inline" id="newsletter-inline">'
END = '<section class="news" id="newsletter">'
errors = []


def check(ok, msg):
    if not ok:
        errors.append(msg)


def read(path):
    return open(os.path.join(DIST, path.strip("/"), "index.html") if path != "/" else os.path.join(DIST, "index.html"),
                encoding="utf-8").read()


def main_of(html):
    return html[html.find("<main"):html.find("</main>")]


def common(path, html):
    m = main_of(html)
    check(m.count(MID) == 1, f"{path}: {m.count(MID)} mid signups, want 1")
    check(m.count(END) == 1, f"{path}: {m.count(END)} end signups, want 1")
    mid, end = m.find(MID), m.find(END)
    check(0 <= mid < end, f"{path}: mid signup must sit above the end signup")
    forms = re.findall(r"<form\b[^>]*>", m)
    check(len(forms) == 2, f"{path}: {len(forms)} forms, want 2")
    check(all('data-sv-form="10170819"' in f and 'action="https://app.kit.com/forms/10170819/subscriptions"' in f for f in forms),
          f"{path}: a form is not Kit form 10170819")
    check(sum('data-vf-event="newsletter-signup-inline"' in f for f in forms) == 1, f"{path}: mid form not marked newsletter-signup-inline")
    check(sum('data-vf-event="newsletter-signup-inline"' not in f for f in forms) == 1, f"{path}: end form marking")
    ids = re.findall(r'\bid="([^"]+)"', html)
    dup = sorted({i for i in ids if ids.count(i) > 1})
    check(not dup, f"{path}: duplicate ids {dup}")
    check(html.count("ck.5.js") == 1 and html.count("api.js?render=") == 1, f"{path}: ck.5.js / reCAPTCHA helper should load once")
    check(html.find("api.js?render=") < html.find("ck.5.js"), f"{path}: reCAPTCHA helper must run before ck.5.js")
    check(m.count("protected by reCAPTCHA") == 2, f"{path}: each form needs the reCAPTCHA notice")
    check("You&#x27;re in!" in html or "You're in!" in html or "You&#39;re in!" in html, f"{path}: success copy missing")
    before, after = m[:mid], m[mid + len(MID):]
    # Not inside a table, list, details, figure or another section.
    for tag in ("table", "ul", "ol", "details", "figure", "section", "dl"):
        opened = len(re.findall(rf"<{tag}\b", before)) - len(re.findall(rf"</{tag}>", before))
        check(opened == 0, f"{path}: mid signup is inside a <{tag}>")
    return before, after


def next_tag(after):
    rest = after[after.find("</section>") + len("</section>"):].lstrip()
    return rest[:160]


# Model pages: after the live deals section (or the sponsor/partner block), before guide links and "All <model> prices".
import json
db = json.load(open(os.path.join(ROOT, "data", "prices.json")))
for slug, m in db["models"].items():
    path = f"/models/{slug}/"
    html = read(path)
    before, after = common(path, html)
    rest = next_tag(after)
    check(rest.startswith('<p class="small">') or rest.startswith("<h2>"), f"{path}: mid signup should be followed by the guide links or a heading: {rest[:80]}")
    check(f"<h2>All {m['name']} prices</h2>" in after, f"{path}: mid signup must sit above the price table")
    check('data-sponsor="model:' + slug + '"' in before, f"{path}: sponsor box should stay above the mid signup")
    if "<h2>Live deals for this model</h2>" in html:
        check(before.rstrip().endswith("</div>") and "Live deals for this model" in before, f"{path}: mid signup should follow the live deals section")

# Home: no mid signup (Emmanuel 2026-11-20); one end signup under the price table, sponsor box unchanged.
html = read("/")
m = main_of(html)
check(MID not in html and 'data-vf-event="newsletter-signup-inline"' not in html, "/: home should not have a mid signup")
check(m.count(END) == 1 and len(re.findall(r"<form\b", m)) == 1, "/: home should have exactly the end signup")
check(m.find('id="prices"') < m.find(END), "/: end signup must stay under the price table")
check('data-sponsor="home"' in m, "/: home sponsor box missing")

# New data pages: sponsor box like the model pages, partner line right after it, then the mid signup at a section boundary.
pages = [(p["path"], '<h2 id="platforms">') for p in cp.PAIRS]
for p in cost.COST_PAGES:
    ids = re.findall(r'<h2 id="([^"]+)"', main_of(read(p["path"])))
    pages.append((p["path"], f'<h2 id="{ids[1]}">'))
pages.append(("/price-index/", '<h2 id="models">'))
for p in plat.PLATFORM_PAGES:
    pages.append((p["path"], '<h2 id="plans">'))
for path, nxt in pages:
    html = read(path)
    before, after = common(path, html)
    check(next_tag(after).startswith(nxt), f"{path}: mid signup should be followed by {nxt}: {next_tag(after)[:60]}")
    sid = "page:" + re.sub(r"[^a-z0-9]+", "-", path.strip("/")).strip("-")
    check(f'data-sponsor="{sid}"' in before, f"{path}: missing sponsor box {sid}")
    box = re.search(rf'<aside class="([^"]+)" data-sponsor="{re.escape(sid)}">.*?</aside>\s*<aside class="partner-line" data-partner="pixeldojo">', html, re.S)
    check(box is not None, f"{path}: PixelDojo partner line should follow the sponsor box")
    if box:
        check("sponsor-box" in box.group(1), f"{path}: sponsor box class {box.group(1)}")
    check(html.find(f'data-sponsor="{sid}"') < html.find("<h2"), f"{path}: sponsor box should sit above the first section, as on model pages")
    check("Some links on this page are affiliate links." in html, f"{path}: affiliate note missing")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"mid signup ok ({len(db['models'])} model pages, {len(pages)} data pages; home has none)")
