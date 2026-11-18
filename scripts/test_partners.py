#!/usr/bin/env python3
"""Labelled Partner line: placement, disclosure, tracking, no Sora, unchanged price order.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_partners.py
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
DATA = os.path.join(ROOT, "data", "sponsors.json")
PARTNER_URL = "https://pixeldojo.ai/?a=pdnpo8l5"
REL = "sponsored nofollow noopener"
LABEL = "Partner"
DISCLOSURE = "Affiliate link: VidFare may earn a commission"
BLURB = "PixelDojo is an AI image and video generator."
MODELS = [
    "gemini-omni-flash",
    "grok-imagine",
    "kling-3-0",
    "minimax-hailuo",
    "runway-gen-4",
    "seedance-2-5",
    "veo-3-1",
    "wan-3-0",
    "wan-3-0-prime",
]
OPT_IN_GUIDES = [
    "ai-video-generator-apps",
    "best-ai-video-generator",
    "cheapest-ai-video-generator",
    "cheapest-kling-3-0",
    "cheapest-seedance-2-5",
    "cheapest-wan-3-0",
    "free-ai-video-generators",
    "free-image-to-video-ai",
    "free-text-to-video-ai",
    "grok-imagine-video-cost",
    "higgsfield-alternatives",
    "higgsfield-vs-kling",
    "higgsfield-vs-runway",
    "is-higgsfield-worth-it",
    "seedance-2-5-unlimited",
    "wan-3-0-unlimited",
]
EXCLUDED_GUIDES = [
    "ai-video-project-budget",
    "fal-ai-pricing",
    "google-flow-credits-calculator",
    "higgsfield-black-friday",
    "higgsfield-pricing",
    "higgsfield-promo-code",
    "kling-ai-pricing",
    "runway-pricing",
]
errors = []


def check(cond, msg):
    if not cond:
        errors.append(msg)


def read(rel):
    return open(os.path.join(DIST, rel), encoding="utf-8").read()


class Tables(HTMLParser):
    """Price-table row signatures plus whether a partner line sits inside a table."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.in_tbody = False
        self.table_depth = 0
        self.row = None
        self.rows_by_table = {}
        self.current_table = None
        self.partner_in_table = []
        self.partners = []
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
            key = tid or parent_id or f"table-{len(self.rows_by_table)}"
            self.current_table = key
            self.rows_by_table.setdefault(key, [])
        if tag == "tbody" and self.table_depth:
            self.in_tbody = True
        if tag == "tr" and self.in_tbody and self.table_depth:
            self.row = []
        if tag == "td" and self.row is not None:
            self._cell = []
        if tag == "aside" and "partner-line" in classes:
            self.partners.append(ad.get("data-partner") or "")
            if self.table_depth:
                self.partner_in_table.append(ad.get("data-partner") or "partner")
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


def parse(html):
    p = Tables()
    p.feed(html)
    return p


def price_rows(parsed, preferred_ids):
    for key in preferred_ids:
        if parsed.rows_by_table.get(key):
            return key, parsed.rows_by_table[key]
    if not parsed.rows_by_table:
        return None, []
    key = max(parsed.rows_by_table, key=lambda k: len(parsed.rows_by_table[k]))
    return key, parsed.rows_by_table[key]


def slice_partner(html):
    m = re.search(
        r'<aside\b[^>]*\bclass="[^"]*\bpartner-line\b[^"]*"[^>]*>.*?</aside>',
        html,
        flags=re.S | re.I,
    )
    return m.group(0) if m else ""


def line_ok(html, rel_path):
    check("sora" not in html.lower(), f"{rel_path} names Sora")
    parsed = parse(html)
    check(parsed.partners == ["pixeldojo"], f"{rel_path} partner ids {parsed.partners}")
    check(not parsed.partner_in_table, f"{rel_path} partner line is inside a table")
    check(html.count('class="partner-line"') == 1, f"{rel_path} does not have exactly one partner line")
    check(html.count('data-partner="pixeldojo"') == 1, f"{rel_path} is missing data-partner=pixeldojo")
    chunk = slice_partner(html)
    check(chunk, f"{rel_path} could not slice the partner line")
    if not chunk:
        return parsed
    check(LABEL in chunk and 'class="partner-label"' in chunk, f"{rel_path} is missing the Partner label")
    check("PixelDojo" in chunk and "is an AI image and video generator." in chunk,
          f"{rel_path} is missing the sourced PixelDojo blurb")
    check(DISCLOSURE in chunk and 'class="partner-disclose"' in chunk, f"{rel_path} is missing the affiliate disclosure")
    check(f'href="{PARTNER_URL}"' in chunk, f"{rel_path} partner link is not {PARTNER_URL}")
    check(f'rel="{REL}"' in chunk, f"{rel_path} partner link is missing rel={REL}")
    check('target="_blank"' in chunk, f"{rel_path} partner link is missing target=_blank")
    check('data-vf-partner="pixeldojo"' in chunk, f"{rel_path} is missing data-vf-partner=pixeldojo")
    check('data-vf-sponsor' not in chunk, f"{rel_path} partner line is marked as a sponsor click")
    check('data-sponsor=' not in chunk, f"{rel_path} partner line uses data-sponsor")
    check('class="sponsor' not in chunk, f"{rel_path} partner line uses a sponsor class")
    check(chunk.lower().count("<a ") == 1, f"{rel_path} partner line does not have exactly one link")
    # Clearly not a price row.
    check("<tr" not in chunk.lower() and "<td" not in chunk.lower() and "<table" not in chunk.lower(),
          f"{rel_path} partner line contains table markup")
    # After the house/sponsor box when one is present.
    box = re.search(r'<aside\b[^>]*\bclass="[^"]*\bsponsor\b[^"]*"[^>]*>.*?</aside>', html, flags=re.S | re.I)
    line_at = html.find('class="partner-line"')
    if box:
        check(line_at > box.end(), f"{rel_path} partner line is not after the sponsor box")
        check("pixeldojo" not in box.group(0).lower(), f"{rel_path} sponsor box mentions PixelDojo")
        check("This spot is open" in box.group(0) or "Advertise on VidFare" in box.group(0) or 'data-sponsor="' in box.group(0),
              f"{rel_path} could not confirm the sponsor box stayed the house ad")
    return parsed


def absent(html, rel_path):
    check('class="partner-line"' not in html, f"{rel_path} has a partner line and must not")
    check('data-partner="pixeldojo"' not in html, f"{rel_path} has data-partner=pixeldojo and must not")
    check('data-vf-partner="pixeldojo"' not in html, f"{rel_path} has data-vf-partner=pixeldojo and must not")
    check("sora" not in html.lower(), f"{rel_path} names Sora")


def title_ok(html, rel_path):
    m = re.search(r"<title>(.*?)</title>", html, flags=re.S | re.I)
    check(m is not None, f"{rel_path} is missing a title")
    if m:
        title = re.sub(r"\s+", " ", m.group(1)).strip()
        check(len(title) <= 60, f"{rel_path} title is {len(title)} characters: {title}")


def deactivate(obj):
    if isinstance(obj, dict):
        if "active" in obj:
            obj["active"] = False
        for val in obj.values():
            deactivate(val)
    elif isinstance(obj, list):
        for val in obj:
            deactivate(val)


def main():
    src = json.load(open(DATA, encoding="utf-8"))
    partners = src.get("partners") or []
    check(isinstance(partners, list) and partners, "data/sponsors.json is missing a partners list")
    rec = next((r for r in partners if isinstance(r, dict) and r.get("id") == "pixeldojo"), None)
    check(rec is not None, "data/sponsors.json has no pixeldojo partner record")
    if rec:
        check(rec.get("active") is False, "pixeldojo partner record is still active; it should be switched off")
        check(rec.get("url") == PARTNER_URL, "pixeldojo url does not match the approved affiliate link")
        check(rec.get("label") == LABEL, "pixeldojo label is not Partner")
        check(rec.get("disclosure") == DISCLOSURE, "pixeldojo disclosure text does not match")
        check(rec.get("blurb") == BLURB, "pixeldojo blurb does not match the sourced description")
        check(rec.get("on_models") is True, "pixeldojo on_models is not true")
        check(sorted(rec.get("guides") or []) == OPT_IN_GUIDES, "pixeldojo guides list does not match the opted-in set")
    # The paid Sponsor record stays empty and inactive.
    paid = src.get("partner") or {}
    check(paid.get("active") is not True, "paid partner record is active; the house ad must stay open")
    check(not (paid.get("name") or "").strip() and not (paid.get("url") or "").strip(),
          "paid partner record is filled; PixelDojo must not go in the Sponsor box")

    docs = open(os.path.join(ROOT, "docs", "sponsors.md"), encoding="utf-8").read()
    check("partner-click/" in docs and "partners" in docs, "docs/sponsors.md does not document the partner line")
    check("sora" not in docs.lower(), "docs/sponsors.md names Sora")
    analytics = open(os.path.join(ROOT, "docs", "analytics.md"), encoding="utf-8").read()
    check("partner-click/" in analytics and "pixeldojo" in analytics.lower(), "docs/analytics.md does not document partner-click")
    events = open(os.path.join(ROOT, "src", "vf-events.js"), encoding="utf-8").read()
    check("partner-click/" in events, "src/vf-events.js is missing partner-click")
    # The partner-click handler must return before sponsor-click / outbound-affiliate.
    p_at = events.find("partner-click/")
    s_at = events.find("sponsor-click/")
    # First occurrence in the header comment may precede both; use the send() call.
    send_p = events.find("send('partner-click/'")
    send_s = events.find("send('sponsor-click/'")
    send_aff = events.find("'outbound-affiliate'")
    check(send_p != -1 and send_s != -1 and send_p < send_s, "partner-click is not handled before sponsor-click")
    check(send_p < send_aff, "partner-click is not handled before outbound-affiliate")

    style = open(os.path.join(ROOT, "src", "style.css"), encoding="utf-8").read()
    check(".partner-line{" in style and ".partner-label{" in style, "src/style.css is missing partner-line styles")

    # Pages that must stay clear of the partner line.
    for rel, label in [
        ("index.html", "home"),
        (os.path.join("deals", "index.html"), "/deals/"),
        (os.path.join("guides", "index.html"), "/guides/"),
        (os.path.join("models", "index.html"), "/models/"),
    ]:
        html = read(rel)
        absent(html, label)
        title_ok(html, label)

    model_rows = {}
    for slug in MODELS:
        rel = os.path.join("models", slug, "index.html")
        html = read(rel)
        title_ok(html, rel)
        absent(html, rel)
        parsed = parse(html)
        key, rows = price_rows(parsed, ["prices"])
        model_rows[slug] = (key, rows)
        check(len(rows) >= 1, f"{rel} has no price-table rows to compare")
        check("This spot is open" in html or "Advertise on VidFare" in html,
              f"{rel} lost the house ad when the partner line was switched off")

    guide_rows = {}
    for slug in OPT_IN_GUIDES + EXCLUDED_GUIDES:
        rel = os.path.join("guides", slug, "index.html")
        html = read(rel)
        title_ok(html, rel)
        absent(html, rel)
        parsed = parse(html)
        key, rows = price_rows(parsed, ["prices"])
        guide_rows[slug] = (key, rows)

    # The switch must still work: rebuild with pixeldojo active and confirm the
    # partner line returns without changing price order or the house ad.
    with tempfile.TemporaryDirectory(prefix="vf-partners-on-") as tmp:
        on = json.loads(json.dumps(src))
        for rec in on.get("partners") or []:
            if isinstance(rec, dict) and rec.get("id") == "pixeldojo":
                rec["active"] = True
        on_path = os.path.join(tmp, "sponsors.json")
        json.dump(on, open(on_path, "w", encoding="utf-8"), indent=1)
        on_dist = os.path.join(tmp, "dist")
        env = os.environ.copy()
        env["VIDFARE_DIST"] = on_dist
        env["VIDFARE_SPONSORS"] = on_path
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
            errors.append("rebuild with partners on failed: " + (proc.stderr or proc.stdout)[-500:])
        else:
            def on_html(rel):
                return open(os.path.join(on_dist, rel), encoding="utf-8").read()

            on_home = on_html("index.html")
            check('class="partner-line"' not in on_home, "home gained a partner line when partners were turned on")
            check("This spot is open" in on_home and "Advertise on VidFare" in on_home,
                  "turning partners on removed the house ad from home")

            for slug, (key, rows) in model_rows.items():
                rel = os.path.join("models", slug, "index.html")
                html = on_html(rel)
                line_ok(html, rel)
                check("This spot is open" in html or "Advertise on VidFare" in html,
                      f"{rel} lost the house ad when the partner line was turned on")
                parsed = parse(html)
                _, on_rows = price_rows(parsed, [key or "prices"])
                check(rows == on_rows, f"{rel} price order or ranking changed when the partner line was turned on")

            for slug in OPT_IN_GUIDES:
                key, rows = guide_rows[slug]
                rel = os.path.join("guides", slug, "index.html")
                html = on_html(rel)
                line_ok(html, rel)
                parsed = parse(html)
                _, on_rows = price_rows(parsed, [key or "prices"])
                if rows:
                    check(rows == on_rows, f"{rel} price order or ranking changed when the partner line was turned on")

            for slug in EXCLUDED_GUIDES:
                rel = os.path.join("guides", slug, "index.html")
                html = on_html(rel)
                absent(html, rel)

    if errors:
        print("FAIL")
        for item in errors:
            print("-", item)
        return 1
    print(
        "ok partners: PixelDojo partner record is present and inactive; "
        "no partner line on model pages or guides; house ad untouched; "
        "the active switch still works; price order unchanged"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
