"""AI Video Price Index: /price-index/.

Imported by scripts/build_site.py. Every number comes from data/prices.json:
today's file for the latest point, and the copy of that file saved in git for
each earlier day. Nothing is typed in by hand, so the page, the CSV and the
JSON update on every build. A day without a saved catalog is not invented:
the series only starts on the first day the catalog was saved.

Index rules
- The 9 tracked models are the keys of prices.json "models". Nothing else counts.
- A model's price for a tier is its cheapest current row at that resolution:
  the same pick as cheapest() on the site. Discontinued rows and promos past
  promo_until are left out. Temporary promos still on are included and labelled.
- Median: the median of those per-model prices (mean of the middle two when the
  count is even). Cheapest: the lowest of them.
- A tier is shown only when at least MIN_MODELS models have a price there.
- Affiliate links play no part. Rows are compared on usd_per_second only.
"""
import csv
import datetime
import io
import json
import os
import statistics
import subprocess
from zoneinfo import ZoneInfo

import timefmt

PATH = "/price-index/"
H1 = "AI Video Price Index"
TITLE = "AI Video Price Index: cost per second over time | VidFare"
DESCRIPTION = (
    "Median and cheapest price per second across 9 AI video models, by resolution, "
    "rebuilt daily from VidFare's checked prices. CSV and JSON downloads."
)
CSV_PATH = "/data/price-index.csv"
JSON_PATH = "/data/price-index.json"
MIN_MODELS = 5
TIERS = [
    ("any", "Any resolution"),
    ("480p", "480p"),
    ("720p", "720p"),
    ("1080p", "1080p"),
    ("4k", "4K"),
]
TIER_LABEL = dict(TIERS)
ET = ZoneInfo("America/New_York")
CSV_FIELDS = [
    "date", "tier", "models_priced", "median_usd_per_second", "cheapest_usd_per_second",
    "cheapest_model", "cheapest_platform", "cheapest_resolution", "cheapest_row_id",
    "cheapest_status", "catalog",
]


# ---------- pure helpers (tested directly) ----------

def tier_of(resolution):
    """480p, 720p, 1080p or 4k. Anything else (768p, 2K, 'lowest mode', '720p/1080p') has no tier."""
    s = str(resolution or "").strip().lower()
    return s if s in ("480p", "720p", "1080p", "4k") else None


def is_current(r, day):
    """Same rule as current() in build_site.py, evaluated on `day`."""
    if r.get("status") == "discontinued":
        return False
    end = r.get("discontinued_on")
    if end and end < day:
        return False
    if r.get("promo_until") and r["promo_until"] < day:
        return False
    return isinstance(r.get("usd_per_second"), (int, float)) and not isinstance(r.get("usd_per_second"), bool)


def model_picks(rows, model_slugs, day, tier="any"):
    """{slug: cheapest current row} for one tier. Ties keep the first row in file order."""
    out = {}
    for r in rows:
        if r.get("model") not in model_slugs or not is_current(r, day):
            continue
        if tier != "any" and tier_of(r.get("resolution")) != tier:
            continue
        best = out.get(r["model"])
        if best is None or r["usd_per_second"] < best["usd_per_second"]:
            out[r["model"]] = r
    return out


def index_point(rows, model_slugs, day, tier):
    picks = model_picks(rows, model_slugs, day, tier)
    if not picks:
        return {"models_priced": 0, "median": None, "cheapest": None, "row": None}
    vals = [r["usd_per_second"] for r in picks.values()]
    low = min(picks.values(), key=lambda r: (r["usd_per_second"], model_slugs.index(r["model"])))
    return {
        "models_priced": len(picks),
        "median": statistics.median(vals),
        "cheapest": low["usd_per_second"],
        "row": low,
    }


def pct_change(old, new):
    if old in (None, 0) or new is None:
        return None
    return (new - old) / old * 100


def pct_text(p):
    if p is None:
        return "n/a"
    if abs(p) < 0.05:
        return "0.0%"
    return f"{'+' if p > 0 else '-'}{abs(p):.1f}%"


def day_text(day):
    d = datetime.date.fromisoformat(day)
    return f"{d.strftime('%b')} {d.day}, {d.year}"


def short_day(day):
    d = datetime.date.fromisoformat(day)
    return f"{d.strftime('%b')} {d.day}"


# ---------- history from git ----------

def git_snapshots(root):
    """[(et_day, commit, iso_time)] oldest first, last commit of each ET day. ([], reason) when unavailable."""
    try:
        shallow = subprocess.run(["git", "-C", root, "rev-parse", "--is-shallow-repository"],
                                 capture_output=True, text=True, timeout=30)
        if shallow.returncode != 0:
            return [], "git history is not available in this build"
        if shallow.stdout.strip() == "true" and os.environ.get("GITHUB_ACTIONS") == "true":
            # actions/checkout clones one commit. Fetch the rest so each day's prices.json is readable.
            # Done here, not in the workflow files, so no workflow change is needed.
            subprocess.run(["git", "-C", root, "fetch", "--quiet", "--unshallow", "origin"],
                           capture_output=True, text=True, timeout=300)
            shallow = subprocess.run(["git", "-C", root, "rev-parse", "--is-shallow-repository"],
                                     capture_output=True, text=True, timeout=30)
        if shallow.stdout.strip() == "true":
            return [], "this build has a shallow git checkout, so earlier days are not available"
        log = subprocess.run(["git", "-C", root, "log", "--format=%H %cI", "--", "data/prices.json"],
                             capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return [], "git history is not available in this build"
    if log.returncode != 0:
        return [], "git history is not available in this build"
    by_day = {}
    for line in log.stdout.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        sha, when = parts
        day = datetime.datetime.fromisoformat(when).astimezone(ET).date().isoformat()
        by_day.setdefault(day, (sha, when))  # log is newest first: keep the day's last commit
    snaps = sorted((day, sha, when) for day, (sha, when) in by_day.items())
    return snaps, None if snaps else "no saved copy of prices.json was found in git"


def load_commit(root, sha):
    out = subprocess.run(["git", "-C", root, "show", f"{sha}:data/prices.json"],
                         capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        return None
    try:
        return json.loads(out.stdout)
    except ValueError:
        return None


def build_series(root, db, today, snapshots=None, loader=None):
    """Daily points from the first saved catalog to today. Today uses the working prices.json.

    Returns {"days": [{"date", "catalog", "tiers": {tier: point}, "models": {slug: row}}], "gap": reason or None}.
    """
    model_slugs = list(db["models"].keys())
    gap = None
    if snapshots is None:
        snapshots, gap = git_snapshots(root)
    loader = loader or (lambda sha: load_commit(root, sha))
    cache = {}
    days = []
    if snapshots:
        start = datetime.date.fromisoformat(snapshots[0][0])
        end = datetime.date.fromisoformat(today)
        i = 0
        d = start
        while d < end:
            ds = d.isoformat()
            while i + 1 < len(snapshots) and snapshots[i + 1][0] <= ds:
                i += 1
            sha = snapshots[i][1]
            if sha not in cache:
                cache[sha] = loader(sha)
            snap = cache[sha]
            if snap and snap.get("rows"):
                days.append(_day(ds, sha[:7], snap["rows"], model_slugs))
            d += datetime.timedelta(days=1)
    days.append(_day(today, "current", db["rows"], model_slugs))
    return {"days": days, "gap": gap, "snapshots": snapshots}


def _day(day, catalog, rows, model_slugs):
    return {
        "date": day,
        "catalog": catalog,
        "tiers": {t: index_point(rows, model_slugs, day, t) for t, _ in TIERS},
        "models": model_picks(rows, model_slugs, day, "any"),
    }


def day_on(series, day):
    for d in series["days"]:
        if d["date"] == day:
            return d
    return None


def shown_tiers(latest):
    return [t for t, _ in TIERS if latest["tiers"][t]["models_priced"] >= MIN_MODELS]


def thin_tiers(latest):
    return [t for t, _ in TIERS if 0 < latest["tiers"][t]["models_priced"] < MIN_MODELS]


# ---------- downloads ----------

def csv_text(series, models):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(CSV_FIELDS)
    for d in series["days"]:
        for t, _ in TIERS:
            p = d["tiers"][t]
            r = p["row"]
            w.writerow([
                d["date"], t, p["models_priced"],
                "" if p["median"] is None else _num(p["median"]),
                "" if p["cheapest"] is None else _num(p["cheapest"]),
                models[r["model"]]["name"] if r else "", r["platform"] if r else "",
                r.get("resolution") or "" if r else "", r.get("id") or "" if r else "",
                r.get("status") or "" if r else "", d["catalog"],
            ])
    return buf.getvalue()


def _num(v):
    return float(f"{v:.6g}")


def json_doc(series, models, site_url, last, method):
    latest = series["days"][-1]
    out = {
        "name": H1,
        "url": site_url + PATH,
        "description": DESCRIPTION,
        "currency": "USD",
        "unit": "US dollars per second of finished video",
        "last_full_check": last,
        "min_models_per_tier": MIN_MODELS,
        "tiers": {t: label for t, label in TIERS},
        "tiers_shown": shown_tiers(latest),
        "method": method,
        "history_gap": series["gap"],
        "series": [],
        "model_cheapest": [],
    }
    for d in series["days"]:
        row = {"date": d["date"], "catalog": d["catalog"], "tiers": {}}
        for t, _ in TIERS:
            p = d["tiers"][t]
            r = p["row"]
            row["tiers"][t] = {
                "models_priced": p["models_priced"],
                "median_usd_per_second": None if p["median"] is None else _num(p["median"]),
                "cheapest_usd_per_second": None if p["cheapest"] is None else _num(p["cheapest"]),
                "cheapest_model": r["model"] if r else None,
                "cheapest_platform": r["platform"] if r else None,
                "cheapest_resolution": r.get("resolution") if r else None,
                "cheapest_row_id": r.get("id") if r else None,
            }
        out["series"].append(row)
    for d in series["days"]:
        for slug, r in d["models"].items():
            out["model_cheapest"].append({
                "date": d["date"], "model": slug, "model_name": models[slug]["name"],
                "usd_per_second": _num(r["usd_per_second"]), "platform": r["platform"],
                "resolution": r.get("resolution"), "row_id": r.get("id"), "status": r.get("status"),
            })
    return out


# ---------- chart ----------

def chart_svg(series, rate_money, tier="any"):
    """Step lines (a price holds until the day it changes), so no value between two days is implied."""
    pts = [(d["date"], d["tiers"][tier]["median"], d["tiers"][tier]["cheapest"]) for d in series["days"]
           if d["tiers"][tier]["median"] is not None]
    W, H = 420, 250
    left, right, top, bottom = 52, 14, 14, 36
    pw, ph = W - left - right, H - top - bottom
    hi = max(max(m, c) for _, m, c in pts)
    step = 0.01 if hi <= 0.06 else (0.02 if hi <= 0.12 else 0.05)
    ymax = step * (int(hi * 1.15 / step) + 1)
    n = len(pts)

    def x(i):
        return left + (pw * i / (n - 1) if n > 1 else pw / 2)

    def y(v):
        return top + ph - ph * v / ymax

    def path(idx):
        cmd = []
        for i, p in enumerate(pts):
            v = p[idx]
            if i == 0:
                cmd.append(f"M{x(i):.1f},{y(v):.1f}")
            else:
                cmd.append(f"H{x(i):.1f}V{y(v):.1f}")
        if n == 1:
            cmd.append(f"H{x(0) + 4:.1f}")
        return "".join(cmd)

    grid = []
    k = 0
    while step * k <= ymax + 1e-9:
        v = step * k
        grid.append(
            f'<line x1="{left}" x2="{W - right}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="#252b3a" stroke-width="1"/>'
            f'<text x="{left - 6}" y="{y(v) + 4:.1f}" text-anchor="end" font-size="12" fill="#9aa3b5">{rate_money(v) if v else "$0"}</text>'
        )
        k += 1
    ticks = sorted({0, n // 2, n - 1}) if n > 2 else list(range(n))
    xl = []
    for i in ticks:
        anchor = "start" if i == 0 else ("end" if i == n - 1 else "middle")
        xl.append(f'<text x="{x(i):.1f}" y="{H - 12}" text-anchor="{anchor}" font-size="12" fill="#9aa3b5">{short_day(pts[i][0])}</text>')
    first, last = pts[0], pts[-1]
    title = f"{H1}: median and cheapest $/s, {TIER_LABEL[tier].lower()}, {day_text(first[0])} to {day_text(last[0])}"
    desc = (
        f"Median went from {rate_money(first[1])} to {rate_money(last[1])} per second. "
        f"Cheapest went from {rate_money(first[2])} to {rate_money(last[2])} per second."
    )
    return (
        f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-labelledby="pi-chart-t pi-chart-d" '
        f'style="display:block;max-width:640px;height:auto" xmlns="http://www.w3.org/2000/svg">'
        f'<title id="pi-chart-t">{title}</title><desc id="pi-chart-d">{desc}</desc>'
        + "".join(grid) + "".join(xl)
        + f'<path d="{path(1)}" fill="none" stroke="#7aa7ff" stroke-width="2.5"/>'
        + f'<path d="{path(2)}" fill="none" stroke="#5ce1a8" stroke-width="2.5" stroke-dasharray="6 4"/>'
        + "</svg>"
    ), title, desc


# ---------- page ----------

# Page-only CSS: at phone width the two summary tables stack into one block per row,
# with each value under its column name, instead of scrolling sideways.
_T = ("#pi-headline", "#pi-models")
def _sel(suffix):
    return ",".join(f"{t}{suffix}" for t in _T)
MOBILE_CSS = (
    "<style>@media(max-width:600px){"
    + _sel(" thead") + "{display:none}"
    + ",".join(f"{t},{t} tbody,{t} tr,{t} th,{t} td" for t in _T) + "{display:block;width:auto}"
    + _sel(" tr") + "{border-bottom:1px solid var(--line);padding:8px 0}"
    + _sel(" tbody tr:last-child") + "{border-bottom:0}"
    + _sel(" th") + "{position:static;background:none;border:0;padding:4px 12px;color:var(--txt);white-space:normal;cursor:auto}"
    + _sel(" td") + "{border:0;padding:3px 12px}"
    + _sel(" td::before") + "{content:attr(data-label) \": \";color:var(--mut);font-size:13px}"
    + "}</style>"
)

def render(g):
    e, root, rate_money = g["e"], g["root"], g["rate_money"]
    models, db, TODAY, LAST = g["models"], g["db"], g["TODAY"], g["LAST"]
    SITE_URL, BRAND, ORG_ID = g["SITE_URL"], g["BRAND"], g["ORG_ID"]
    ROOT, DIST = g["ROOT"], g["DIST"]

    series = build_series(ROOT, db, TODAY)
    g["PRICE_INDEX"] = series
    latest = series["days"][-1]
    start = series["days"][0]
    week_day = (datetime.date.fromisoformat(TODAY) - datetime.timedelta(days=7)).isoformat()
    week = day_on(series, week_day)
    shown = shown_tiers(latest)
    thin = thin_tiers(latest)
    if "any" not in shown:
        raise SystemExit(f"{PATH}: fewer than {MIN_MODELS} models have a current price")
    g["SITEMAP_LASTMOD"][PATH] = LAST

    def money_or_na(v):
        return "n/a" if v is None else rate_money(v)

    def who(r, platform=True):
        bits = [models[r["model"]]["name"]]
        if platform:
            plan = (r.get("plan_name") or "").strip() if r.get("kind") == "plan" else ""
            bits.append(f"on {r['platform']}" + (f" {plan} plan" if plan else ""))
        res = str(r.get("resolution") or "").strip()
        tail = []
        if res and res not in ("—", "-", "–"):
            tail.append(res)
        if r.get("status") == "promo":
            tail.append("promo" + (f" until {r['promo_until']}" if r.get("promo_until") else ""))
        elif r.get("status") == "estimate":
            tail.append("estimate")
        return " ".join(bits) + (f" ({', '.join(tail)})" if tail else "")

    def tie_text(day, point):
        tied = [r for r in day["models"].values()
                if r["usd_per_second"] == point["cheapest"] and r is not point["row"]]
        return "".join(f", tied with {who(r)}" for r in tied)

    a = latest["tiers"]["any"]
    lead = (
        f"The median of the 9 tracked models' cheapest prices is {rate_money(a['median'])} per second of video. "
        f"The cheapest is {rate_money(a['cheapest'])} per second, {e(who(a['row']))}{e(tie_text(latest, a))}. "
        f"Prices last checked {day_text(LAST)}."
    )
    week_note = (f"7 days ago is {day_text(week_day)}." if week
                 else f"7 days ago ({day_text(week_day)}) is not available: {series['gap'] or 'the series starts later'}.")

    # Headline table
    hrows = []
    for t in shown:
        p = latest["tiers"][t]
        wp = week["tiers"][t] if week else None
        wm = wp["median"] if wp and wp["models_priced"] >= MIN_MODELS else None
        change = pct_text(pct_change(wm, p["median"])) if wm is not None else "n/a"
        hrows.append(
            f"<tr><th scope=\"row\">{e(TIER_LABEL[t])}</th><td data-label=\"Models priced\">{p['models_priced']} of {len(models)}</td>"
            f'<td data-label="Median $/s"><b>{rate_money(p["median"])}</b></td>'
            f'<td data-label="Cheapest $/s"><b>{rate_money(p["cheapest"])}</b><br><span class="small">{e(who(p["row"]))}</span></td>'
            f'<td data-label="Median 7 days ago"><b>{money_or_na(wm)}</b><br><span class="small">{e(change)}</span></td></tr>'
        )
    thin_note = ""
    if thin:
        parts = [f"{TIER_LABEL[t]} ({latest['tiers'][t]['models_priced']} of {len(models)})" for t in thin]
        thin_note = (f"<p class=\"small\">Not shown: {e(', '.join(parts))}. A tier needs a current price for at least "
                     f"{MIN_MODELS} of the {len(models)} models before a median means anything. The rows are still in the CSV and JSON.</p>")
    headline = (
        '<div class="tblwrap"><table id="pi-headline"><thead><tr><th>Resolution</th><th>Models priced</th>'
        '<th>Median $/s</th><th>Cheapest $/s</th><th>Median 7 days ago</th></tr></thead><tbody>'
        + "".join(hrows) + "</tbody></table></div>"
    )

    # Per-model change table
    price_changes = [c for c in g["changes"] if c.get("type") == "price"]
    mrows = []
    na_reasons = set()
    for slug, m in models.items():
        now = latest["models"].get(slug)
        if now is None:
            mrows.append(f"<tr><th scope=\"row\">{e(m['name'])}</th><td colspan=\"4\">n/a: no current price</td></tr>")
            continue

        def cell(ref_day, ref, label):
            if ref is None:
                reason = series["gap"] or "the series starts later"
                na_reasons.add(f"{label}: {reason}.")
                return f'<td data-label="vs {e(label)}">n/a<br><span class="small">no data for that day</span></td>'
            r = ref["models"].get(slug)
            if r is None:
                na_reasons.add(f"{m['name']} had no current price on {day_text(ref['date'])}.")
                return f'<td data-label="vs {e(label)}">n/a<br><span class="small">no price that day</span></td>'
            pc = pct_change(r["usd_per_second"], now["usd_per_second"])
            return (f'<td data-label="vs {e(label)}"><b>{pct_text(pc)}</b><br><span class="small">from {rate_money(r["usd_per_second"])}, '
                    f'{e(r["platform"])}</span></td>')

        logged_week = sum(1 for c in price_changes if c.get("model") == slug and c["date"] > week_day)
        logged_all = sum(1 for c in price_changes if c.get("model") == slug and c["date"] > start["date"])
        mrows.append(
            f"<tr><th scope=\"row\"><a href=\"{root(f'/models/{slug}/')}\">{e(m['name'])}</a></th>"
            f'<td data-label="Cheapest now"><b>{rate_money(now["usd_per_second"])}</b><br><span class="small">{e(who(now, platform=True)[len(m["name"]) + 1:])}</span></td>'
            + cell(week_day, week, f"{short_day(week_day)} (7 days ago)")
            + cell(start["date"], start, f"{short_day(start['date'])} (start)")
            + f'<td data-label="Logged price changes, 7 days / all">{logged_week} / {logged_all}</td></tr>'
        )
    model_table = (
        '<div class="tblwrap"><table id="pi-models"><thead><tr><th>Model</th><th>Cheapest now</th>'
        f'<th>vs {e(short_day(week_day))}</th><th>vs {e(short_day(start["date"]))}</th>'
        '<th>Logged changes, 7d / all</th></tr></thead><tbody>'
        + "".join(mrows) + "</tbody></table></div>"
    )
    na_html = ("<p class=\"small\">n/a: " + e(" ".join(sorted(na_reasons))) + "</p>") if na_reasons else ""

    # Chart
    svg, chart_title, chart_desc = chart_svg(series, rate_money)
    drows = "".join(
        f'<tr><td>{e(day_text(d["date"]))}</td><td class="num">{money_or_na(d["tiers"]["any"]["median"])}</td>'
        f'<td class="num">{money_or_na(d["tiers"]["any"]["cheapest"])}</td></tr>'
        for d in reversed(series["days"])
    )
    chart = (
        f'<figure style="margin:0">{svg}'
        f'<figcaption class="small"><span style="color:#7aa7ff">━ Median</span> · '
        f'<span style="color:#5ce1a8">╍ Cheapest</span> · any resolution, US dollars per second. '
        f'{e(chart_desc)}</figcaption></figure>'
        f'<details><summary>Daily values as a table</summary><div class="tblwrap"><table id="pi-daily"><thead><tr>'
        f'<th>Date</th><th>Median $/s</th><th>Cheapest $/s</th></tr></thead><tbody>{drows}</tbody></table></div></details>'
    )

    # Methodology
    snaps = series["snapshots"]
    latest_saved = ""
    if snaps:
        latest_saved = f" The last saved catalog before this build is from {e(timefmt.et_pt(snaps[-1][2]))}."
    checked = sorted(r.get("checked") for r in latest["models"].values() if r.get("checked"))
    check_range = (f"{day_text(checked[0])}" if checked and checked[0] == checked[-1]
                   else f"{day_text(checked[0])} to {day_text(checked[-1])}") if checked else "not stated"
    method = {
        "price": "Each model's price is its cheapest current row in prices.json: the same pick as the model pages.",
        "usage": f"API rows are the vendor's stated rate. Credit-plan rows {g['CREDIT_USE']}.",
        "median": "Median of the per-model prices in a tier (mean of the middle two when the count is even).",
        "cheapest": "Lowest of the per-model prices in a tier.",
        "tiers": f"480p, 720p, 1080p and 4K are exact resolution labels. Shown when at least {MIN_MODELS} of the models have a price.",
        "history": "Each earlier day uses the last prices.json saved in git on or before that day (Eastern time). Today uses the current file.",
    }
    method_html = f"""<h2 id="method">How the index is calculated</h2>
<ul>
<li><b>Models.</b> {e(", ".join(m["name"] for m in models.values()))}. Nothing else is counted.</li>
<li><b>Price per model.</b> The cheapest current row for that model across every API and credit plan we list, the same pick as the model pages. Rows marked discontinued and promos past their end date are left out. A temporary promo that is still on counts, and it is labelled.</li>
<li><b>Usage assumption.</b> API rows are the vendor's stated $/s. Credit-plan rows are plan price ÷ credits × credits per clip ÷ clip length, which {e(g["CREDIT_USE"])}. Deal-adjusted prices from <a href="{root("/deals/")}">Deals</a> are not used.</li>
<li><b>Median and cheapest.</b> The median is the middle of the per-model prices in a tier (the mean of the two middle ones when the count is even). The cheapest is the lowest of them.</li>
<li><b>Resolution tiers.</b> 480p, 720p, 1080p and 4K use the exact resolution on the row. MiniMax Hailuo's 768p, 2K, and rows priced per mode count only under any resolution. A tier is shown when at least {MIN_MODELS} models have a price.</li>
<li><b>Order.</b> Only $/s sets the order. Affiliate and partner links never change it.</li>
<li><b>History.</b> Each earlier day uses the last copy of prices.json saved on or before that day, Eastern time, so it shows what {BRAND} published then. Nothing is filled in between saved copies. A move can come from a vendor price change, a newly added row, or a correction. Vendor price changes are listed on <a href="{root("/changes/")}">Price changes</a> and counted in the last column of the model table (the 7 days before {day_text(TODAY)}, and since the start).{latest_saved}</li>
<li><b>Check dates.</b> Last full check {day_text(LAST)}. The per-model prices for {day_text(TODAY)} were checked {check_range}.</li>
</ul>"""

    cite_text = f'{BRAND}. "{H1}." {SITE_URL}{PATH} (prices checked {day_text(LAST)}).'
    body = f"""<h1>{e(H1)}</h1>
<p class="lead">{lead}</p>
<p class="small">{e(DESCRIPTION)} Series since {day_text(start["date"])}. {e(week_note)}</p>
{g["page_sponsor_html"](PATH)}
{g["partner_lines_html"](PATH)}
<h2 id="headline">Median and cheapest $/s by resolution</h2>
{headline}
{thin_note}
<h2 id="chart">Median and cheapest over time</h2>
{chart}
{g["news_box_inline"]()}
<h2 id="models">Cheapest price per model: now, a week ago, at the start</h2>
<p class="small">Each model's cheapest $/s at any resolution and where it is. The change columns compare with the cheapest price on that day, which may have been on another platform.</p>
{model_table}
{na_html}
{method_html}
<h2 id="cite">Cite this</h2>
<p><code>{e(cite_text)}</code></p>
<p>Downloads, rebuilt with the page: {g["json_link"](CSV_PATH, "price-index.csv")} · {g["json_link"](JSON_PATH, "price-index.json")}. The full catalog is on <a href="{root("/data/")}">Price data</a>.</p>
{g["data_links_html"]()}
{g["news_box"]()}"""

    ld = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": H1,
        "description": DESCRIPTION,
        "url": SITE_URL + PATH,
        "creator": {"@type": "Organization", "@id": ORG_ID, "name": BRAND, "url": SITE_URL + "/"},
        "isAccessibleForFree": True,
        "dateModified": LAST,
        "temporalCoverage": f"{start['date']}/{latest['date']}",
        "variableMeasured": [
            {"@type": "PropertyValue", "name": "Median $/s", "unitText": "USD per second of video"},
            {"@type": "PropertyValue", "name": "Cheapest $/s", "unitText": "USD per second of video"},
        ],
        "measurementTechnique": "Median and minimum of each model's cheapest current price per second in prices.json.",
        "distribution": [
            {"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": SITE_URL + CSV_PATH},
            {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": SITE_URL + JSON_PATH},
        ],
    }
    g["page"](PATH, TITLE, DESCRIPTION, body, PATH, MOBILE_CSS + g["ld_join"](
        ld, g["breadcrumb_ld"]([("Prices", "/"), (H1, PATH)])))

    os.makedirs(os.path.join(DIST, "data"), exist_ok=True)
    open(os.path.join(DIST, "data", "price-index.csv"), "w", encoding="utf-8").write(csv_text(series, models))
    with open(os.path.join(DIST, "data", "price-index.json"), "w", encoding="utf-8") as fh:
        json.dump(json_doc(series, models, SITE_URL, LAST, method), fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    return series


def llms_line(g):
    series = g.get("PRICE_INDEX")
    if not series:
        return None
    a = series["days"][-1]["tiers"]["any"]
    rm = g["rate_money"]
    return (
        f"- [{H1}]({g['SITE_URL']}{PATH}): median and cheapest $/s across the {len(g['models'])} models by resolution, "
        f"daily since {series['days'][0]['date']}. Now: median {rm(a['median'])}/s, cheapest {rm(a['cheapest'])}/s. "
        f"Downloads: {g['SITE_URL']}{CSV_PATH} and {g['SITE_URL']}{JSON_PATH}."
    )
