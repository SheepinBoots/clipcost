#!/usr/bin/env python3
"""House open-spot ad: placement, markup, no paid partner, unchanged price order.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_sponsors.py
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
LABEL = "This spot is open"
HEADING = "Advertise on VidFare"
PITCH = "Reach people who are comparing AI video prices."
CTA = "Advertise here"
HREF = "/advertise/"
DISCLOSE_NOTE = "Some links on this page are affiliate links."
# Example of the paid partner record (not rendered). Filling this in and
# setting active to true is the one edit that replaces the house ad.
EXAMPLE_PARTNER = {
    "name": "Example Tool",
    "url": "https://example.com/?ref=vidfare",
    "tagline": "A short description the partner approved, kept verbatim.",
    "logo": "/example.png",
    "disclosure": "Affiliate link: VidFare may earn a commission.",
    "cta": "Try Example Tool",
    "active": True,
}
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
    check('class="sponsor-label"' in html and LABEL in html, f"{rel_path} is missing the open-spot label")
    check(HEADING in html, f"{rel_path} is missing the Advertise on VidFare heading")
    check(PITCH in html, f"{rel_path} is missing the house-ad pitch")
    check(f'href="{HREF}"' in html, f"{rel_path} is missing the /advertise/ link")
    check('class="sponsor-cta"' in html and CTA in html, f"{rel_path} is missing the Advertise here CTA")
    check('class="sponsor-hit"' in html, f"{rel_path} is missing the whole-box link")
    track = "house-" + slot_id.replace(":", "-")
    check(f'data-vf-sponsor="{track}"' in html, f"{rel_path} is missing data-vf-sponsor={track}")
    check("sora" not in html.lower(), f"{rel_path} names Sora")
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
        check("sponsored" not in chunk, f"{rel_path} house ad uses rel=sponsored")
        check('target="_blank"' not in chunk, f"{rel_path} house ad uses target=_blank")
        check("Affiliate link" not in chunk, f"{rel_path} house ad includes an affiliate disclosure")
        check("commission" not in chunk.lower(), f"{rel_path} house ad mentions a commission")
    return parsed


def price_table_rows(parsed, preferred_ids):
    for key in preferred_ids:
        if parsed.rows_by_table.get(key):
            return key, parsed.rows_by_table[key]
    if not parsed.rows_by_table:
        return None, []
    key = max(parsed.rows_by_table, key=lambda k: len(parsed.rows_by_table[k]))
    return key, parsed.rows_by_table[key]


def without_sponsor(html):
    return re.sub(r"<aside\b[^>]*\bclass=\"[^\"]*\bsponsor\b[\s\S]*?</aside>", "", html, flags=re.I)


def main():
    # The example partner shape is documented for a later one-file edit.
    check(all(k in EXAMPLE_PARTNER for k in ("name", "url", "tagline", "cta", "active")), "example partner record is missing fields")

    home = read("index.html")
    model = read(os.path.join("models", "wan-3-0", "index.html"))
    deals = read(os.path.join("deals", "index.html"))

    home_parsed = slot_ok(home, "home", "index.html")
    model_parsed = slot_ok(model, "model:wan-3-0", "models/wan-3-0/index.html")

    check('data-sponsor="deals"' not in deals, "deals page has a sponsor slot; the house ad must not appear there")
    check(LABEL not in deals and HEADING not in deals, "deals page shows the house ad")

    guides_root = os.path.join(DIST, "guides")
    index_guides = read(os.path.join("guides", "index.html"))
    check('data-sponsor="' not in index_guides, "/guides/ index has a sponsor slot; it must not")
    check('data-vf-sponsor="house-guide-' not in index_guides, "/guides/ index has a guide sponsor tracking attribute")
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
        check(tracks == [f"house-guide-{slug}"], f"{rel} data-vf-sponsor values {tracks}")
        h1 = html.find("<h1")
        lead = re.search(r'<p class="lead">.*?</p>', html, re.S)
        slot_at = html.find(f'data-sponsor="guide:{slug}"')
        check(h1 != -1 and slot_at > h1, f"{rel} sponsor box is not after the H1")
        check(lead and slot_at > lead.end(), f"{rel} sponsor box is not after the lead")
        take = re.search(r'id="takeaways"', html)
        if take:
            check(slot_at > take.start(), f"{rel} sponsor box is not after the takeaways")
        # The affiliate note stays only when the page has a real affiliate link
        # outside the house ad (for example a Higgsfield fpr= link).
        rest = without_sponsor(html)
        has_aff = bool(re.search(r'<a\b[^>]*(rel="sponsored|fpr=)', rest))
        if not has_aff:
            check(DISCLOSE_NOTE not in html, f"{rel} has the affiliate disclosure note with only the house ad")
        if slug == "cheapest-ai-video-generator":
            guide_sample = (slug, parsed, html)

    check(guide_sample is not None, "cheapest-ai-video-generator guide was not built")
    flow = read(os.path.join("guides", "google-flow-credits-calculator", "index.html"))
    check(DISCLOSE_NOTE not in flow, "Flow credits guide has the affiliate note with only the house ad")
    check(DISCLOSE_NOTE in home, "home is missing the affiliate disclosure note next to real affiliate links")

    # PixelDojo may only appear in the labelled Partner line, never as a logo
    # and never inside the paid/house Sponsor box.
    forbidden = "pixeldojo"
    for dirpath, _, filenames in os.walk(DIST):
        for name in filenames:
            if forbidden in name.lower():
                errors.append(f"built file name contains {forbidden}: {os.path.relpath(os.path.join(dirpath, name), DIST)}")
                continue
            path = os.path.join(dirpath, name)
            ext = os.path.splitext(name)[1].lower()
            if ext in {".png", ".jpg", ".jpeg", ".ico", ".webp", ".woff", ".woff2"}:
                continue
            try:
                text = open(path, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            remainder = re.sub(
                r'<aside\b[^>]*\bclass="[^"]*\bpartner-line\b[^"]*"[^>]*>.*?</aside>',
                "",
                text,
                flags=re.S | re.I,
            )
            if forbidden in remainder.lower():
                errors.append(f"built file contains {forbidden} outside a partner line: {os.path.relpath(path, DIST)}")
            for chunk in re.findall(r'<aside\b[^>]*\bclass="[^"]*\bsponsor\b[^"]*"[^>]*>.*?</aside>', text, flags=re.S | re.I):
                if forbidden in chunk.lower():
                    errors.append(f"sponsor box contains {forbidden}: {os.path.relpath(path, DIST)}")
    src_logo = os.path.join(ROOT, "src", "pixeldojo.png")
    dist_logo = os.path.join(DIST, "pixeldojo.png")
    check(not os.path.isfile(src_logo), "src/pixeldojo.png is still in the repo")
    check(not os.path.isfile(dist_logo), "dist/pixeldojo.png was still built")

    home_key, home_rows = price_table_rows(home_parsed, ["prices"])
    model_key, model_rows = price_table_rows(model_parsed, ["prices"])
    check(len(home_rows) > 10, f"home price table has too few rows: {len(home_rows)}")
    check(len(model_rows) > 1, f"model price table has too few rows: {len(model_rows)}")

    # Rebuild with every sponsor slot turned off, then compare table order.
    with tempfile.TemporaryDirectory(prefix="vf-sponsor-off-") as tmp:
        off_path = os.path.join(tmp, "sponsors.json")
        src = json.load(open(os.path.join(ROOT, "data", "sponsors.json"), encoding="utf-8"))
        def deactivate(obj):
            if isinstance(obj, dict):
                if "active" in obj:
                    obj["active"] = False
                for val in obj.values():
                    deactivate(val)
            elif isinstance(obj, list):
                for val in obj:
                    deactivate(val)
        deactivate(src)
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
            off_home_html = open(os.path.join(off_dist, "index.html"), encoding="utf-8").read()
            check(HEADING not in off_home_html and LABEL not in off_home_html, "off build still shows the house ad")
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
    print("ok sponsors: house open-spot ad on home, models, and every guide, deals empty, price order unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
