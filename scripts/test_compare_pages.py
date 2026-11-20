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
check(cp.plan_short("Ultra (annual)") == "Ultra annual" and cp.plan_short("not listed") == "", "plan_short")
check(cp.deal_name("Black Friday: Ultra annual billing") == "Black Friday price" and cp.deal_name("50% off") == "deal price", "deal_name")
check(cp.seller_text({"platform": "Higgsfield"}, "Ultra (annual)", ["Black Friday price"], "estimated from credit plan")
      == "on Higgsfield (Ultra annual, Black Friday price, estimated from credit plan)", "seller_text")
check(cp.seller_text({"platform": "Higgsfield"}, "Ultra (annual)", ["Black Friday price"], "from credit plan",
                     "regular $0.151/s on Higgsfield, Ultra monthly at $129/mo")
      == "on Higgsfield (Ultra annual, Black Friday price, from credit plan; regular $0.151/s on Higgsfield, Ultra monthly at $129/mo)",
      "seller_text with a regular price")
# Sale rows get a regular price from the data, or the cheapest non-sale row, never an invented one.
_sale = {"type": "plan_sale", "standing": False, "usd": 0.05, "list_usd": 0.15}
_r1 = {"platform": "H", "model": "m", "resolution": "720p", "usd_per_second": 0.05}
check(cp.regular_for(_r1, [_sale], [_r1], lambda x: [])["usd"] == 0.15, "regular from the deal's prior price")
check(cp.regular_for(_r1, [dict(_sale, standing=True)], [_r1], lambda x: []) is None, "standing discount is not a sale")
check(cp.regular_for(_r1, [dict(_sale, usd=0.04)], [_r1], lambda x: []) is None, "deal that is not the row's price")
check(cp.regular_for(_r1, [dict(_sale, type="unlimited_window")], [_r1], lambda x: []) is None, "unlimited window is not a sale price")
_p = {"platform": "P", "model": "m", "resolution": "720p", "usd_per_second": 0.02, "promo_until": "2026-12-01"}
_n1 = {"platform": "Q", "model": "m", "resolution": "720p", "usd_per_second": 0.09}
_n2 = {"platform": "R", "model": "m", "resolution": "720p", "usd_per_second": 0.07}
_n3 = {"platform": "S", "model": "m", "resolution": "1080p", "usd_per_second": 0.01}
check(cp.regular_for(_p, [], [_p, _n1, _n2, _n3], lambda x: [])["row"] is _n2, "cheapest without a sale, same model and resolution")
check(cp.regular_for(_p, [], [_p, _n3], lambda x: []) == {"kind": "none"}, "no regular price is not invented")
check(cp.regular_for(dict(_p, list_usd_per_second=0.08), [], [_p], lambda x: [])["usd"] == 0.08, "row's own list rate")
check(cp.and_list(["720p", "1080p"]) == "720p and 1080p" and cp.and_list(["480p", "720p", "1080p"]) == "480p, 720p and 1080p", "and_list")
_like = cp.same_seller(rows, {"a": "a", "b": "b", "resolutions": ("720p",)})
check([(x[0], x[1]) for x in _like] == [("720p", "Higgsfield"), ("720p", "fal")], "same_seller")
check(cp.same_seller(rows[:1] + rows[3:], {"a": "a", "b": "b", "resolutions": ("720p",)}) == [], "same_seller none")
check(cp.run_text("2026-11-20T08:00:44", "2026-11-20") == "Nov 20, 2026, 11:00 AM ET (8:00 AM PT)", "run time ET first")
check(cp.run_text("2026-11-19T08:00:44", "2026-11-20") == "Nov 20, 2026", "old run falls back to the date")

# ---------- built pages ----------
db = json.load(open(os.path.join(ROOT, "data", "prices.json")))
today = db["last_full_check"]
_deals = json.load(open(os.path.join(ROOT, "data", "deals.json")))
_deals = _deals["deals"] if isinstance(_deals, dict) else _deals


def is_sale(r):
    """Recomputed from the data: a promo row, a row with a higher list rate, or the sale plan of a
    live, non-standing plan sale whose price went down."""
    if r.get("promo_until") or (r.get("list_usd_per_second") or 0) > r["usd_per_second"]:
        return True
    for d in _deals:
        if d.get("status") != "live" or d.get("type") != "plan_sale" or d.get("math") != "plan_price":
            continue
        if (d.get("conditions") or {}).get("standing") or (d.get("end") and d["end"] < today):
            continue
        if d.get("start") and d["start"] > today:
            continue
        for pr in d.get("price_pairs") or [d]:
            if r.get("plan") and r["plan"] == pr.get("deal_plan_id") and (pr.get("price_after") or 0) < (pr.get("price_before") or 0):
                return True
    return False

cur = [r for r in db["rows"] if live(r, today)]

# res_gap_note: built from the data, and the approved wording for today's Veo 3.1 1080p rows.
_m = {"v": {"name": "Veo 3.1"}, "k": {"name": "Kling 3.0"}}
_spec = {"gap": "v", "res": "1080p", "other": "k", "platform_short": {"Google Gemini API": "Gemini API"}}
_gone = [{"model": "v", "platform": "Google Gemini API", "resolution": "1080p", "discontinued_on": "2026-10-22"},
         {"model": "v", "platform": "Google Gemini API", "resolution": "1080p", "discontinued_on": "2026-10-22"}]
_comb = [{"model": "v", "platform": "fal", "resolution": "720p/1080p"}]
check(cp.res_gap_note(_gone + _comb, _comb, _spec, _m) == "Our data has no current 1080p-only Veo 3.1 price; the Gemini API "
      "1080p rows were discontinued Oct 22, 2026, and fal lists one rate for 720p/1080p.", "res_gap_note: gone + combined")
check(cp.res_gap_note(_comb, _comb, _spec, _m) == "Our data has no current 1080p-only Veo 3.1 price; fal lists one rate for 720p/1080p.",
      "res_gap_note: combined only")
check(cp.res_gap_note([], [], _spec, _m) == "Our data has no current 1080p-only Veo 3.1 price.", "res_gap_note: nothing")
_new = [{"model": "v", "platform": "fal", "resolution": "1080p"}]
check(cp.res_gap_note(_new, _new, _spec, _m) == "Our data has current 1080p-only Veo 3.1 prices on fal, which does not sell Kling 3.0.",
      "res_gap_note: a current row")
_kv = next(p for p in cp.PAIRS if p["path"] == "/compare/kling-3-0-vs-veo-3-1/")
check("Our data has no current 1080p-only Veo 3.1 price; the Gemini API 1080p rows were discontinued Oct 22, 2026, "
      "and fal lists one rate for 720p/1080p." in cp.note_text(_kv, db["rows"], cur, db["models"]),
      "kling-veo note: approved 1080p wording not rendered from today's data")
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
            check(f"<b>{rate_money(best['usd_per_second'])}/s</b>" in cells, f"{path}: {name} {res} $/s")
            price_cell = re.search(r'data-label="Cheapest \$/s">(.*?)</td>', cells, re.S).group(1)
            check(f"{rate_money(best['usd_per_second'])}/s on {best['platform']} (" in text(price_cell),
                  f"{path}: {name} {res} price does not name its seller next to it")
            for secs in pair["seconds"]:
                cell = re.search(rf'data-label="{secs}s clip" class="num">(.*?)</td>', cells, re.S).group(1)
                check(cell.startswith(two(best["usd_per_second"] * secs)), f"{path}: {name} {res} {secs}s total")
                check(best["platform"] in text(cell), f"{path}: {name} {res} {secs}s total without its seller")
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
        check("Plan or tier: " in text(tr.split("</th>")[0]), f"{path}: row without plan or tier")
        for lab in ("Resolution", "Audio", "Checked"):
            m = re.search(rf'data-label="{lab}"[^>]*>(.*?)</td>', tr, re.S)
            check(m is not None and text(m.group(1)).strip() != "", f"{path}: row without {lab}")
        check(re.search(r"\((?:[^()]*, )?(published rate|estimated rate|estimated from credit plan|from credit plan|promo)\)", text(tr)) is not None,
              f"{path}: row without a rate label next to the price")
        if "credit plan" in text(tr):
            check("Assumes every credit you pay for is used." in tr, f"{path}: plan row without the usage assumption")
    # Seller next to every price.
    platforms = {r["platform"] for r in db["rows"]}
    for tid in ("cmp-headline",):
        tab = page[page.find(f'id="{tid}"'):]
        tab = tab[:tab.find("</table>")]
        for td in re.findall(r"<td\b[^>]*>(.*?)</td>", tab, re.S):
            t = text(td)
            if re.search(r"\$\d", t):
                check(any(p in t for p in platforms), f"{path}: {tid} price without a seller: {t.strip()[:80]}")
    for tr in trs:
        plat = text(re.search(r'<th scope="row">(.*?)<br>', tr, re.S).group(1)).strip()
        # Totals in a platform row sit in the row headed by that seller and plan.
        check(plat in platforms, f"{path}: row header is not a seller: {plat}")
        cell = text(re.search(r'data-label="\$/s"[^>]*>(.*?)</td>', tr, re.S).group(1))
        check(re.search(rf"\$[\d.]+/s on {re.escape(plat)} \(", cell) is not None, f"{path}: row $/s without its seller {plat}")
    lead = re.search(r'<p class="lead">(.*?)</p>', page, re.S)
    same = re.search(r'<p id="same-seller">(.*?)</p>', page, re.S)
    check(lead is not None and same is not None, f"{path}: lead or same-seller line missing")
    if lead and same:
        for para in (text(lead.group(1)), text(same.group(1))):
            for m in re.finditer(r"\$[\d.]*\d(?![\d.])(/s)?", para):
                if para[m.end():].startswith("/mo"):
                    continue  # a plan's monthly price inside a regular-price note, e.g. "at $129/mo"
                check(para[m.end():].startswith(" on "), f"{path}: price {m.group(0)} in the lead has no seller next to it")
        like = [(res, p) for res in pair["resolutions"] for p in sorted(plats)
                if all(any(r["platform"] == p and r["model"] == m and str(r.get("resolution")).strip() == res for r in cur) for m in (A, B))]
        st = text(same.group(1))
        if like:
            for res, p in like:
                check(f"At {res}," in st and f"/s on {p} (" in st, f"{path}: same-seller line misses {p} {res}")
        else:
            check("no like-for-like price" in st, f"{path}: same-seller line should say there is none")
    # Every sale or promo price in a headline or summary has a regular or non-sale price next to it,
    # and a price that is not on sale gets none.
    for res in pair["resolutions"]:
        for s in (A, B):
            best = None
            for r in cur:
                if r["model"] == s and str(r.get("resolution")).strip() == res:
                    if best is None or r["usd_per_second"] < best["usd_per_second"]:
                        best = r
            if best is None:
                continue
            name = db["models"][s]["name"]
            on_sale = is_sale(best)
            row = re.search(rf'<tr><th scope="row">{re.escape(name)}, {res}</th>(.*?)</tr>', head, re.S)
            if not row:
                continue
            price_cell = text(re.search(r'data-label="Cheapest \$/s">(.*?)</td>', row.group(1), re.S).group(1))
            has = re.search(r"; (regular \$[\d.]+/s on |cheapest without a sale: \$[\d.]+/s on |no regular price in our data)", price_cell)
            check(bool(has) == on_sale, f"{path}: {name} {res} sale price {'without' if on_sale else 'with'} a regular price: {price_cell[:160]}")
            for secs in pair["seconds"]:
                cell = text(re.search(rf'data-label="{secs}s clip" class="num">(.*?)</td>', row.group(1), re.S).group(1))
                has = re.search(r"(regular|cheapest without a sale:) \$[\d.]+ on ", cell)
                check(bool(has) == on_sale, f"{path}: {name} {res} {secs}s total sale price without a regular price")
            if on_sale and lead and same:
                rate = rate_money(best["usd_per_second"])
                for label, para in (("lead", text(lead.group(1))), ("same-seller", text(same.group(1)))):
                    for m in re.finditer(rf"{re.escape(rate)}/s on {re.escape(best['platform'])} \(([^()]*)\)", para):
                        check(re.search(r"; (regular \$|cheapest without a sale: \$|no regular price)", m.group(1)) is not None,
                              f"{path}: {label} sale price {rate}/s without a regular price")
                    tot = two(best["usd_per_second"] * 10)
                    for m in re.finditer(rf"{re.escape(tot)} on {re.escape(best['platform'])}( \(([^()]*)\))?", para):
                        check(m.group(2) is not None and re.match(r"(regular|cheapest without a sale:) \$", m.group(2)) is not None,
                              f"{path}: {label} 10s total {tot} on a sale price without a regular price")
    if pair.get("note"):
        check(cp.note_text(pair, db["rows"], cur, db["models"]) in body, f"{path}: note not shown")
    # No invented rows: a model with no price at a resolution says so.
    for res in pair["resolutions"]:
        for s in (A, B):
            if not any(r["model"] == s and str(r.get("resolution")).strip() == res for r in cur):
                check(f"No {res} price in our data." in head, f"{path}: {s} {res} should say no price")
    for s in (A, B):
        mp = open(os.path.join(DIST, "models", s, "index.html"), encoding="utf-8").read()
        check(f'href="{path}"' in mp, f"{path}: no link from /models/{s}/")
    check(f'href="{path}"' in open(os.path.join(DIST, "calculator", "index.html"), encoding="utf-8").read(),
          f"{path}: no link from /calculator/")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"compare pages ok ({len(cp.PAIRS)} page(s))")
