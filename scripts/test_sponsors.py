#!/usr/bin/env python3
"""PixelDojo partner slot: placement, markup, and unchanged price order.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_sponsors.py
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
DESC = (
    "PixelDojo is an all-in-one AI studio with Kling, Veo, Seedance, Hailuo, WAN, Flux and GPT Image "
    "under one subscription, so you can try and compare models in one place instead of paying for several "
    "separate tools. Plans start at $10 a month, and unused credits roll over while you stay subscribed."
)
DISCLOSE = "Affiliate link: VidFare may earn a commission."
HREF = "https://pixeldojo.ai/?a=pdnpo8l5"
REL = "sponsored nofollow noopener"
errors = []


def check(cond, msg):
    if not cond:
        errors.append(msg)


def read(rel):
    path = os.path.join(DIST, rel)
    return open(path, encoding="utf-8").read()


class TableRows(HTMLParser):
    """Collect tbody row signatures from price tables, and whether a sponsor sits inside one."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.in_tbody = False
        self.table_depth = 0
        self.row = None
        self.rows_by_table = {}
        self.current_table = None
        self.table_ids = []
        self.sponsor_in_table = []
        self.asides = []
        self._cell = None

    def handle_starttag(self, tag, attrs):
        ad = dict(attrs)
        classes = (ad.get("class") or "").split()
        if tag == "table":
            self.table_depth += 1
            tid = ad.get("id") or ""
            parent_id = ""
            for name, pattrs in reversed(self.stack):
                if pattrs.get("id"):
                    parent_id = pattrs["id"]
                    break
            key = tid or parent_id or f"table-{len(self.table_ids)}"
            self.current_table = key
            self.table_ids.append(key)
            self.rows_by_table.setdefault(key, [])
        if tag == "tbody" and self.table_depth:
            self.in_tbody = True
        if tag == "tr" and self.in_tbody and self.table_depth:
            self.row = []
        if tag == "td" and self.row is not None:
            self._cell = []
        if tag == "aside" and "sponsor" in classes:
            self.asides.append(ad.get("data-sponsor") or "")
            if self.table_depth:
                self.sponsor_in_table.append(ad.get("data-sponsor") or "sponsor")
        self.stack.append((tag, ad))

    def handle_endtag(self, tag):
        if tag == "td" and self._cell is not None and self.row is not None:
            self.row.append(re.sub(r"\s+", " ", "".join(self._cell)).strip())
            self._cell = None
        if tag == "tr" and self.row is not None:
            if self.current_table is not None:
                self.rows_by_table[self.current_table].append(tuple(self.row))
            self.row = None
        if tag == "tbody":
            self.in_tbody = False
        if tag == "table" and self.table_depth:
            self.table_depth -= 1
            if self.table_depth == 0:
                self.current_table = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def parse_page(html):
    p = TableRows()
    p.feed(html)
    return p


def slot_ok(html, slot_id, rel_path):
    check(f'data-sponsor="{slot_id}"' in html, f"{rel_path} is missing the {slot_id} sponsor slot")
    check('class="sponsor-label"' in html and ">Sponsor<" in html, f"{rel_path} is missing the Sponsor label")
    check(f'href="{HREF}"' in html, f"{rel_path} is missing the PixelDojo affiliate link")
    check(f'rel="{REL}"' in html and 'target="_blank"' in html, f"{rel_path} PixelDojo link rel/target is wrong")
    check("PixelDojo" in html, f"{rel_path} is missing the PixelDojo name")
    check(DESC in html, f"{rel_path} does not keep the approved PixelDojo description verbatim")
    check(DISCLOSE in html, f"{rel_path} is missing the disclosure line")
    check('src="/pixeldojo.png"' in html, f"{rel_path} is missing the logo")
    check('class="sponsor-logo"' in html, f"{rel_path} is missing the logo class")
    check('class="sponsor-cta"' in html and "Try PixelDojo" in html, f"{rel_path} is missing the Try PixelDojo CTA")
    check('class="sponsor-hit"' in html, f"{rel_path} is missing the whole-box link")
    track = slot_id.replace(":", "-")
    check(f'data-vf-sponsor="{track}"' in html, f"{rel_path} is missing data-vf-sponsor={track}")
    check("sora" not in html.lower(), f"{rel_path} names Sora")
    # The slot must sit outside the price table, and the box is one link with no nested controls.
    parsed = parse_page(html)
    check(slot_id in parsed.asides, f"{rel_path} parser missed slot {slot_id}")
    check(not parsed.sponsor_in_table, f"{rel_path} has a sponsor inside a table: {parsed.sponsor_in_table}")
    start = html.find(f'data-sponsor="{slot_id}"')
    check(start != -1, f"{rel_path} could not slice slot {slot_id}")
    if start != -1:
        end = html.find("</aside>", start)
        chunk = html[start:end]
        check(chunk.lower().count("<a ") == 1, f"{rel_path} sponsor box does not have exactly one link")
        check("<button" not in chunk.lower(), f"{rel_path} sponsor box has a nested button")
    return parsed


def price_table_rows(parsed, preferred_ids):
    for key in preferred_ids:
        if parsed.rows_by_table.get(key):
            return key, parsed.rows_by_table[key]
    # Fallback: the longest tbody (the all-prices table).
    if not parsed.rows_by_table:
        return None, []
    key = max(parsed.rows_by_table, key=lambda k: len(parsed.rows_by_table[k]))
    return key, parsed.rows_by_table[key]


def main():
    home = read("index.html")
    model = read(os.path.join("models", "wan-3-0", "index.html"))
    deals = read(os.path.join("deals", "index.html"))

    home_parsed = slot_ok(home, "home", "index.html")
    model_parsed = slot_ok(model, "model:wan-3-0", "models/wan-3-0/index.html")

    check('data-sponsor="deals"' not in deals, "deals page has a sponsor slot; PixelDojo must not appear there")
    check("PixelDojo" not in deals, "deals page names PixelDojo")
    check(HREF not in deals, "deals page has the PixelDojo link")

    guides_root = os.path.join(DIST, "guides")
    index_guides = read(os.path.join("guides", "index.html"))
    check('data-sponsor="' not in index_guides, "/guides/ index has a sponsor slot; it must not")
    check('data-vf-sponsor="guide-' not in index_guides, "/guides/ index has a guide sponsor tracking attribute")
    guide_pages = []
    for name in sorted(os.listdir(guides_root)):
        page = os.path.join(guides_root, name, "index.html")
        if os.path.isfile(page):
            guide_pages.append(name)
    check(len(guide_pages) >= 10, f"expected many guide pages, found {len(guide_pages)}")
    guide_sample = None
    for slug in guide_pages:
        rel = os.path.join("guides", slug, "index.html")
        html = read(rel)
        parsed = slot_ok(html, f"guide:{slug}", rel)
        boxes = re.findall(r'data-sponsor="([^"]*)"', html)
        check(boxes == [f"guide:{slug}"], f"{rel} sponsor slots {boxes} != [guide:{slug}]")
        tracks = re.findall(r'data-vf-sponsor="([^"]*)"', html)
        check(tracks == [f"guide-{slug}"], f"{rel} data-vf-sponsor values {tracks}")
        h1 = html.find("<h1")
        lead = re.search(r'<p class="lead">.*?</p>', html, re.S)
        slot_at = html.find(f'data-sponsor="guide:{slug}"')
        check(h1 != -1 and slot_at > h1, f"{rel} sponsor box is not after the H1")
        check(lead and slot_at > lead.end(), f"{rel} sponsor box is not after the lead")
        take = re.search(r'id="takeaways"', html)
        if take:
            check(slot_at > take.start(), f"{rel} sponsor box is not after the takeaways")
        if slug == "cheapest-ai-video-generator":
            guide_sample = (slug, parsed, html)
    check(guide_sample is not None, "cheapest-ai-video-generator guide was not built")

    logo = os.path.join(DIST, "pixeldojo.png")
    check(os.path.isfile(logo), "dist/pixeldojo.png was not built")
    if os.path.isfile(logo):
        png = open(logo, "rb").read()
        check(png[:8] == b"\x89PNG\r\n\x1a\n", "dist/pixeldojo.png is not a PNG")

    home_key, home_rows = price_table_rows(home_parsed, ["prices"])
    model_key, model_rows = price_table_rows(model_parsed, ["prices"])
    check(len(home_rows) > 10, f"home price table has too few rows: {len(home_rows)}")
    check(len(model_rows) > 1, f"model price table has too few rows: {len(model_rows)}")

    # Rebuild the site with every sponsor slot turned off, then compare table order.
    with tempfile.TemporaryDirectory(prefix="vf-sponsor-off-") as tmp:
        off_path = os.path.join(tmp, "sponsors.json")
        src = json.load(open(os.path.join(ROOT, "data", "sponsors.json"), encoding="utf-8"))
        for rec in src.values():
            rec["active"] = False
        json.dump(src, open(off_path, "w", encoding="utf-8"), indent=1)
        off_dist = os.path.join(tmp, "dist")
        env = os.environ.copy()
        env["VIDFARE_DIST"] = off_dist
        env["VIDFARE_SPONSORS"] = off_path
        env["VIDFARE_SKIP_VIEWPORT"] = "1"
        proc = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "build_site.py")],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )
        if proc.returncode != 0:
            errors.append("rebuild without sponsors failed: " + (proc.stderr or proc.stdout)[-500:])
        else:
            off_home = parse_page(open(os.path.join(off_dist, "index.html"), encoding="utf-8").read())
            off_model = parse_page(
                open(os.path.join(off_dist, "models", "wan-3-0", "index.html"), encoding="utf-8").read()
            )
            _, off_home_rows = price_table_rows(off_home, [home_key or "prices"])
            _, off_model_rows = price_table_rows(off_model, [model_key or "prices"])
            check(not off_home.asides, "home still has a sponsor slot when every slot is inactive")
            check(not off_model.asides, "model page still has a sponsor slot when every slot is inactive")
            check(home_rows == off_home_rows, "home price order changed when the sponsor was added")
            check(model_rows == off_model_rows, "Wan 3.0 price order changed when the sponsor was added")
            check("PixelDojo" not in open(os.path.join(off_dist, "index.html"), encoding="utf-8").read(), "off build still names PixelDojo")
            if guide_sample:
                slug, guide_parsed, _ = guide_sample
                guide_key, guide_rows = price_table_rows(guide_parsed, ["prices"])
                off_guide = parse_page(
                    open(os.path.join(off_dist, "guides", slug, "index.html"), encoding="utf-8").read()
                )
                _, off_guide_rows = price_table_rows(off_guide, [guide_key or "prices"])
                check(not off_guide.asides, "guide still has a sponsor slot when every slot is inactive")
                if guide_rows:
                    check(guide_rows == off_guide_rows, f"{slug} price order changed when the sponsor was added")

    if errors:
        print("FAIL")
        for item in errors:
            print("-", item)
        return 1
    print("ok sponsors: PixelDojo box on home, models, and every guide, deals empty, price order unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
