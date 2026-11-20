#!/usr/bin/env python3
"""/compare/ pages agree with prices.json, respect clip caps, and hide when stale.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_compare_pages.py
Numbers are recomputed here from prices.json, not taken from compare_pages.py.
"""
import html
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare_pages as cp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
SITE = "https://vidfare.com"
errors = []


def check(ok, msg):
    if not ok:
        errors.append(msg)


def rate_money(v):
    x = float(v)
    s = f"{x:.4f}" if x < 0.10 else f"{x:.3f}"
    s = s.rstrip("0")
    whole, frac = s.split(".")
    return f"${whole}.{frac.ljust(2, '0')}"


def two(v):
    from decimal import Decimal, ROUND_HALF_UP
    return "$" + str(Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def live(r, day):
    if r.get("status") == "discontinued" or (r.get("discontinued_on") and r["discontinued_on"] < day):
        return False
    return not (r.get("promo_until") and r["promo_until"] < day)


def text(s):
    s = re.sub(r"<(script|style)\b.*?</\1>", " ", s, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)))


# ---------- unit tests (no build needed) ----------
check(cp.clips_needed(30, 15) == 2 and cp.clips_needed(15, 15) == 1 and cp.clips_needed(16, 15) == 2, "clips_needed")
check(cp.clip_total(0.1, 30, 15) == (0.1 * 30, 2), "clip_total past the cap")
check(cp.clip_total(0.1, 10, 30) == (0.1 * 10, 1), "clip_total under the cap")
mk = lambda m, mx: {"model": m, "variation": {"duration": {"max_seconds": mx}}}
check(cp.cap_info([mk("x", 15), mk("x", "not stated")], "x", 15) == (15, "data", ""), "cap from data")
check(cp.cap_info([mk("x", "not stated")], "x", 15) == (15, "config", ""), "cap falls back to config")
check(cp.cap_info([mk("x", 10)], "x", 15)[2] != "", "cap mismatch is reported")
check(cp.cap_info([mk("x", 10), mk("x", 15)], "x", 15)[1:] == ("config", "rows disagree: 10s, 15s"), "rows disagree")
# Stale guard
check(not cp.is_stale([{"checked": "2026-11-13"}], "2026-11-20"), "7 days old is not stale")
check(cp.is_stale([{"checked": "2026-11-12"}], "2026-11-20"), "8 days old is stale")
check(cp.is_stale([{"checked": "2026-11-20"}, {"checked": "2026-11-01"}], "2026-11-20"), "one old row makes the page stale")
check(cp.is_stale([], "2026-11-20"), "no rows is stale")
fake = {"COMPARE_PAGES": [{"path": "/compare/a/", "stale": True}, {"path": "/compare/b/", "stale": False}]}
check(cp.sitemap_paths(fake) == ["/compare/b/"], "stale page left out of the sitemap")
# Order ignores affiliates: only $/s and platform.
rows = [{"platform": "Higgsfield", "model": "a", "resolution": "720p", "usd_per_second": 0.2, "checked": "2026-11-20"},
        {"platform": "Higgsfield", "model": "b", "resolution": "720p", "usd_per_second": 0.3, "checked": "2026-11-20"},
        {"platform": "fal", "model": "a", "resolution": "720p", "usd_per_second": 0.1, "checked": "2026-11-20"},
        {"platform": "fal", "model": "b", "resolution": "720p", "usd_per_second": 0.4, "checked": "2026-11-20"}]
plats, got = cp.page_rows(rows, {"a": "a", "b": "b", "resolutions": ("720p",)})
check(plats == ["Higgsfield", "fal"], "shared platforms")
check([r["usd_per_second"] for r in got] == [0.1, 0.2, 0.3, 0.4], "rows sorted by $/s only")
check(cp.run_text("2026-11-20T08:00:44", "2026-11-20") == "Nov 20, 2026, 11:00 AM ET (8:00 AM PT)", "run time ET first")
check(cp.run_text("2026-11-19T08:00:44", "2026-11-20") == "Nov 20, 2026", "old run falls back to the date")

# ---------- built pages ----------
db = json.load(open(os.path.join(ROOT, "data", "prices.json")))
today = db["last_full_check"]
cur = [r for r in db["rows"] if live(r, today)]
sitemap = open(os.path.join(DIST, "sitemap.xml"), encoding="utf-8").read()
llms = open(os.path.join(DIST, "llms.txt"), encoding="utf-8").read()
for pair in cp.PAIRS:
    path = pair["path"]
    check(path.startswith("/compare/"), f"{path}: not under /compare/")
    title = cp.title_of(pair)
    check(len(title) <= 60, f"{path}: title {len(title)} characters")
    page = open(os.path.join(DIST, path.strip("/"), "index.html"), encoding="utf-8").read()
    body = text(page[page.find("<main"):page.find("</main>")])
    check(f"<title>{html.escape(title)}</title>" in page, f"{path}: title")
    check(f'<link rel="canonical" href="{SITE}{path}">' in page, f"{path}: canonical")
    stale = "noindex" in page
    check(stale == ("Stale data:" in body), f"{path}: stale notice and robots disagree")
    check((f"<loc>{SITE}{path}</loc>" in sitemap) == (not stale), f"{path}: sitemap vs stale")
    check((f"{SITE}{path})" in llms) == (not stale), f"{path}: llms.txt vs stale")
    check(not re.search(r"sora", page, re.I), f"{path}: names Sora")
    check("Caracas" not in page, f"{path}: Caracas time")
    check("assumes every credit you pay for is used" in body, f"{path}: usage assumption")
    check(re.search(r"\d{1,2}:\d\d [AP]M ET \(\d{1,2}:\d\d [AP]M PT\)", body) is not None, f"{path}: ET-first check time")
    lds = [json.loads(x) for x in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)]
    flat = [o for x in lds for o in (x if isinstance(x, list) else x.get("@graph", [x]))]
    wp = [o for o in flat if o.get("@type") == "WebPage"]
    check(len(wp) == 1, f"{path}: one WebPage JSON-LD")
    if wp:
        check(wp[0]["name"] in body and wp[0]["description"] in body, f"{path}: JSON-LD name/description not visible")
        check(wp[0]["url"] == SITE + path, f"{path}: JSON-LD url")
    A, B = pair["a"], pair["b"]
    caps = pair["caps"]
    # Stated caps in the data must match the config.
    for s in (A, B):
        stated = {((r.get("variation") or {}).get("duration") or {}).get("max_seconds") for r in cur if r["model"] == s}
        stated = {x for x in stated if isinstance(x, (int, float))}
        check(not stated or stated == {caps[s]}, f"{path}: {s} cap {caps[s]} vs data {stated}")
    # Headline numbers recomputed.
    head = page[page.find('id="cmp-headline"'):]
    head = head[:head.find("</table>")]
    for res in pair["resolutions"]:
        for s in (A, B):
            best = None
            for r in cur:
                if r["model"] == s and str(r.get("resolution")).strip() == res:
                    if best is None or r["usd_per_second"] < best["usd_per_second"]:
                        best = r
            name = db["models"][s]["name"]
            row = re.search(rf'<tr><th scope="row">{re.escape(name)}, {res}</th>(.*?)</tr>', head, re.S)
            check(row is not None, f"{path}: headline row {name} {res}")
            if not row or best is None:
                continue
            cells = row.group(1)
            check(f"<b>{rate_money(best['usd_per_second'])}</b>" in cells, f"{path}: {name} {res} $/s")
            check(best["platform"] in text(cells), f"{path}: {name} {res} platform")
            for secs in pair["seconds"]:
                cell = re.search(rf'data-label="{secs}s clip" class="num">(.*?)</td>', cells, re.S).group(1)
                check(cell.startswith(two(best["usd_per_second"] * secs)), f"{path}: {name} {res} {secs}s total")
                n = math.ceil(secs / caps[s])
                check((f"{n} clips" in cell) == (n > 1), f"{path}: {name} {res} {secs}s clip count")
    # Platform table: every row shows plan/tier, resolution, audio and a label.
    plats = {r["platform"] for r in cur if r["model"] == A} & {r["platform"] for r in cur if r["model"] == B}
    check(f"Platforms that sell both: {len(plats)}" in body, f"{path}: platform count {len(plats)}")
    ptab = page[page.find('id="cmp-platforms"'):]
    ptab = ptab[:ptab.find("</table>")]
    trs = re.findall(r"<tr><th scope=\"row\">.*?</tr>", ptab, re.S)
    check(len(trs) > 0, f"{path}: platform table empty")
    for tr in trs:
        for lab in ("Plan or tier", "Resolution", "Audio", "Label", "Checked"):
            m = re.search(rf'data-label="{lab}"[^>]*>(.*?)</td>', tr, re.S)
            check(m is not None and text(m.group(1)).strip() != "", f"{path}: row without {lab}")
        check(re.search(r'class="tag (verified|estimate|promo)"', tr) is not None, f"{path}: row without a rate label")
        if "credit plan" in text(tr):
            check("Assumes every credit you pay for is used." in tr, f"{path}: plan row without the usage assumption")
    for s in (A, B):
        mp = open(os.path.join(DIST, "models", s, "index.html"), encoding="utf-8").read()
        check(f'href="{path}"' in mp, f"{path}: no link from /models/{s}/")
    check(f'href="{path}"' in open(os.path.join(DIST, "calculator", "index.html"), encoding="utf-8").read(),
          f"{path}: no link from /calculator/")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"compare pages ok ({len(cp.PAIRS)} page(s))")
