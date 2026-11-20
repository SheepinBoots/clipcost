"""Clip-cost ranking pages under /cost/.

Imported by scripts/build_site.py. One entry in COST_PAGES is one page. Every number
comes from data/prices.json at build time, so each page rebuilds with the daily price
run and needs no hand edits. Built to serve /cost/10-second/ now and later
/cost/1080p/ and /cost/30-second/ (different `seconds` or `resolutions`).

Rules
- For each model and resolution, the row ranked is that model's lowest usd_per_second
  among rows whose stated resolution is exactly that tier (case-insensitive, so
  "480P" counts as 480p). Tier names, dashes and combined values such as "720p/1080p"
  are not a resolution and are not ranked.
- A clip total is usd_per_second x seconds. Past a model's longest single clip (the
  cap), the total is the same rate and the row says how many clips it needs.
  Caps come from the rows' stated max_seconds, else CAPS below (vendor docs). A model
  with neither says so in a footnote.
- Rows are ordered by the total only. Affiliate status plays no part.
- A model with no row at a resolution is listed as "not listed". Nothing is invented.
- Stale guard: same as /compare/ (compare_pages.STALE_DAYS).
"""
import math
import re

import compare_pages as cp

# Longest single clip per model when the rows do not state one (vendor docs).
# Models absent here have no cap in our data or docs; their footnote says so.
CAPS = {"wan-3-0-prime": 30, "wan-3-0": 30, "kling-3-0": 15, "seedance-2-5": 30,
        "veo-3-1": 8, "gemini-omni-flash": 15, "grok-imagine": 15}

COST_PAGES = [
    {
        "path": "/cost/10-second/",
        "title": "How Much a 10-Second AI Video Costs",
        "h1": "How much a 10-second AI video costs",
        "description": ("What one 10-second AI video clip costs on the cheapest platform for each of 9 models, "
                        "ranked at 480p, 720p and 1080p. Rebuilt daily from our price data."),
        "seconds": 10,
        "resolutions": ("480p", "720p", "1080p"),
    },
    {
        "path": "/cost/1080p/",
        "title": "1080p AI Video Cost by Model and Platform",
        "h1": "1080p AI video cost by model and platform",
        "description": ("The cheapest 1080p price per second and per 10-second clip for 9 AI video models, "
                        "plus each model's 1080p price on every platform. Rebuilt daily."),
        "seconds": 10,
        "resolutions": ("1080p",),
        # Ranking heading; {res}, {n} and {total} are filled in.
        "rank_h2": "Cheapest {res} price for each model: {n} of {total} models listed",
        # Name a cheaper variant (Lite, Turbo, ...) next to the model in ranking rows and the lead.
        "variant_in_name": True,
        # One table per model with its cheapest row at the resolution on each platform.
        "by_platform": True,
    },
]

# Words in a row's variant that name a cheaper or different tier of the model.
VARIANT_WORDS = ("lite", "fast", "turbo", "max", "pro", "plus", "mini", "flash")


def title_of(page):
    return page["title"] + cp.BRAND_SUFFIX


def res_key(r):
    s = cp.res_of(r)
    return s.lower() if s else None


def cheapest_at(rows, slug, res):
    best = None
    for r in rows:
        if r["model"] == slug and res_key(r) == res.lower():
            if best is None or r["usd_per_second"] < best["usd_per_second"]:
                best = r
    return best


def model_cap(rows, slug):
    """(cap or None, source) with source 'data', 'config' or 'none'."""
    cap, src, _mismatch = cp.cap_info(rows, slug, CAPS.get(slug))
    if cap is None:
        return None, "none"
    return cap, src


def ranking(rows, models, res, secs):
    """[(model slug, row, total, clips, cap)] sorted by total, then model name; and the not-listed slugs."""
    ranked, missing = [], []
    for slug in models:
        r = cheapest_at(rows, slug, res)
        if r is None:
            missing.append(slug)
            continue
        cap = cp.stated_max(r) or model_cap(rows, slug)[0]
        ranked.append((slug, r, r["usd_per_second"] * secs, cp.clips_needed(secs, cap), cap))
    ranked.sort(key=lambda x: (x[2], models[x[0]]["name"]))
    return ranked, missing


def variant_suffix(r, model_name):
    """'Lite' for grok_imagine_1_5_lite, 'Max Turbo' for MiniMax H3 Max Turbo; '' when the variant
    names no tier word beyond the model's own name."""
    have = set(re.split(r"[^a-z0-9.]+", model_name.lower()))
    words = []
    for w in re.split(r"[^a-z0-9.]+", str(r.get("variant") or "").lower()):
        if w in VARIANT_WORDS and w not in have and w.title() not in words:
            words.append(w.title())
    return " ".join(words)


def display_name(r, model_name, on=True):
    v = variant_suffix(r, model_name) if on else ""
    return f"{model_name} {v}" if v else model_name


def per_platform(rows, slug, res):
    """[(platform, cheapest row there, number of rows there)] at exactly `res`, cheapest first."""
    best, count = {}, {}
    for r in rows:
        if r["model"] == slug and res_key(r) == res.lower():
            p = r["platform"]
            count[p] = count.get(p, 0) + 1
            if p not in best or r["usd_per_second"] < best[p]["usd_per_second"]:
                best[p] = r
    return sorted(((p, best[p], count[p]) for p in best), key=lambda x: (x[1]["usd_per_second"], x[0]))


def combined_note(rows, slug, res):
    """' fal lists it only as one 720p/1080p rate.' when a combined resolution includes `res`."""
    hits = []
    for r in rows:
        v = str(r.get("resolution") or "")
        if r["model"] == slug and "/" in v and res.lower() in [x.strip().lower() for x in v.split("/")]:
            if (r["platform"], v) not in hits:
                hits.append((r["platform"], v))
    if not hits:
        return ""
    return " " + "; ".join(f"{p} lists it only as one {v} rate" for p, v in hits) + ", which is not ranked here."


def links_html(slug, root, nl=False):
    """Small link line for a model page or the calculator ('*' = every cost page)."""
    hits = [p for p in COST_PAGES if slug == "*" or slug in p.get("models", ()) or not p.get("models")]
    if not hits:
        return ""
    links = " · ".join(f'<a href="{root(p["path"])}">{p["title"]}</a>' for p in hits)
    return f'<p class="small">Clip cost: {links}.</p>' + ("\n" if nl else "")


def render_page(g, page):
    e, root, rate_money = g["e"], g["root"], g["rate_money"]
    models, rows, TODAY, LAST = g["models"], g["rows"], g["TODAY"], g["LAST"]
    two = g["_money_places"]
    secs = page["seconds"]
    lab = cp.Labels(g, rows, TODAY)
    name = {s: models[s]["name"] for s in models}

    ranks = {res: ranking(rows, models, res, secs) for res in page["resolutions"]}
    shown = [x[1] for res in page["resolutions"] for x in ranks[res][0]]
    plat = {}
    if page.get("by_platform"):
        plat = {(res, s): per_platform(rows, s, res) for res in page["resolutions"] for s in models}
        shown += [x[1] for v in plat.values() for x in v if x[1] not in shown]
    vname = lambda r, slug: display_name(r, name[slug], page.get("variant_in_name", False))
    stale = cp.is_stale(shown, TODAY, cp.STALE_DAYS)
    old = cp.oldest_checked(shown)
    run = cp.run_text(g.get("CHECK_RUN"), LAST)

    # Cap footnotes: models capped below the clip length, and models with no known cap.
    caps = {s: model_cap(rows, s) for s in models}
    on_page = {r["model"] for r in shown}
    short = [s for s in models if caps[s][0] is not None and caps[s][0] < secs and s in on_page]
    unknown = [s for s in models if caps[s][0] is None and any(cheapest_at(rows, s, res) for res in page["resolutions"])]
    marks = {s: "†" for s in short}
    marks.update({s: "‡" for s in unknown})
    notes = []
    for s in short:
        n = math.ceil(secs / caps[s][0])
        notes.append(f"† {name[s]} makes clips of up to {caps[s][0]:g} seconds, so a {secs}-second video is {n} clips "
                     f"at the same price per second. The total is for {'both' if n == 2 else 'all ' + str(n)} clips.")
    for s in unknown:
        notes.append(f"‡ Our price data does not state the longest single clip for {name[s]}. The total is the price per "
                     f"second × {secs}; check the vendor page for whether {secs} seconds is one clip.")

    def row_html(i, slug, r, total, n, cap):
        reg = lab.regular_text(r, secs)
        reg_html = f'<br><span class="small regular">{e(reg)}</span>' if reg else ""
        more = f'<br><span class="small">{n} clips (max {cap:g}s each){marks.get(slug, "")}</span>' if n > 1 else (
            f'<span class="small">{marks[slug]}</span>' if slug in marks else "")
        return (f'<tr><td data-label="Rank" class="num">{i}</td>'
                f'<th scope="row"><a href="{root("/models/" + slug + "/")}">{e(vname(r, slug))}</a><br>'
                f'<span class="small">Plan or tier: {e(lab.plan_text(r))} · {e(r["variant"])}</span></th>'
                f'<td data-label="{secs}s clip" class="num"><b>{two(total, 2)}</b>{more}'
                f'<br><span class="small">{e(lab.seller_short(r))}</span>{reg_html}</td>'
                f'<td data-label="$/s"><b>{rate_money(r["usd_per_second"])}/s</b> {lab.seller_html(r, regular=True)}'
                f'{g["deal_badges"](r)}{g["assumption_html"](r)}</td>'
                f'<td data-label="Resolution">{e(cp.res_of(r))}</td>'
                f'<td data-label="Audio">{e(g["shown_audio"](r))}</td>'
                f'<td data-label="Checked" class="small">{e(r["checked"])}<br>{g["source_link"](r)}</td></tr>')

    sections, tids = [], []
    for res in page["resolutions"]:
        ranked, missing = ranks[res]
        tid = f"cost-{res.lower()}"
        tids.append("#" + tid)
        body_rows = "".join(row_html(i + 1, *x) for i, x in enumerate(ranked))
        body_rows += "".join(
            f'<tr><td data-label="Rank" class="num">–</td><th scope="row"><a href="{root("/models/" + s + "/")}">{e(name[s])}</a></th>'
            f'<td data-label="{secs}s clip" colspan="5">Not listed: no {e(res)} price in our data.{e(combined_note(rows, s, res))}</td></tr>'
            for s in missing)
        table = cp._table(
            f'<thead><tr><th scope="col">Rank</th><th scope="col">Model, plan or tier</th><th scope="col">{secs}s clip</th>'
            f'<th scope="col">$/s, seller, plan and label</th><th scope="col">Resolution</th><th scope="col">Audio</th>'
            f'<th scope="col">Checked</th></tr></thead><tbody>{body_rows}</tbody>', tid)
        h2 = page.get("rank_h2", "{secs}-second clip at {res}: {n} of {total} models listed").format(
            secs=secs, res=res, n=len(ranked), total=len(models))
        sections.append(f'<h2 id="r{res.lower()}">{e(h2)}</h2>\n{table}')

    def lead_bit(res):
        ranked, _ = ranks[res]
        if not ranked:
            return f"At {res}, no model has a price in our data. "
        slug, r, total, n, _cap = ranked[0]
        reg = lab.regular_text(r, secs)
        clip = f", {n} clips" if n > 1 else ""
        return (f"At {res}, the cheapest {secs}-second clip is {vname(r, slug)} at {two(total, 2)} on {r['platform']}"
                + (f" ({reg})" if reg else "") + f"{clip}: {rate_money(r['usd_per_second'])}/s {lab.seller(r)}. ")
    lead = "".join(lead_bit(res) for res in reversed(page["resolutions"])) + f"Prices last checked {run}."

    stale_html = ""
    if stale:
        stale_html = (f'<p class="disclose"><b>Stale data:</b> at least one price on this page was last checked '
                      f'{e(cp.day_text(old)) if old else "never"}, more than {cp.STALE_DAYS} days ago. Check the vendor pages before you buy. '
                      f'This page is hidden from search until the prices are re-checked.</p>')
    if page.get("by_platform"):
        for res in page["resolutions"]:
            sections.append(f'<h2 id="p{res.lower()}">Every {e(res)} price by model and platform</h2>\n'
                            f'<p class="small">Each model\'s cheapest {e(res)} row on each platform we track, cheapest first.</p>')
            for slug in models:
                got = plat[(res, slug)]
                h3 = f'<h3 id="p{res.lower()}-{slug}"><a href="{root("/models/" + slug + "/")}">{e(name[slug])}</a> at {e(res)}</h3>'
                if not got:
                    sections.append(h3 + f'\n<p>Not listed: no {e(res)} price in our data.{e(combined_note(rows, slug, res))}</p>')
                    continue
                trs = ""
                for p_, r, k in got:
                    cap = cp.stated_max(r) or caps[slug][0]
                    n = cp.clips_needed(secs, cap)
                    reg = lab.regular_text(r, secs)
                    reg_html = f'<br><span class="small regular">{e(reg)}</span>' if reg else ""
                    more = f'<br><span class="small">{n} clips (max {cap:g}s each){marks.get(slug, "")}</span>' if n > 1 else (
                        f'<span class="small">{marks[slug]}</span>' if slug in marks else "")
                    many = f'<br><span class="small">cheapest of {k} {e(res)} rows here</span>' if k > 1 else ""
                    trs += (f'<tr><th scope="row">{e(p_)}<br><span class="small">Plan or tier: {e(lab.plan_text(r))} · {e(r["variant"])}</span>{many}</th>'
                            f'<td data-label="$/s"><b>{rate_money(r["usd_per_second"])}/s</b> {lab.seller_html(r, regular=True)}'
                            f'{g["deal_badges"](r)}{g["assumption_html"](r)}</td>'
                            f'<td data-label="{secs}s clip" class="num"><b>{two(r["usd_per_second"] * secs, 2)}</b>{more}{reg_html}</td>'
                            f'<td data-label="Resolution">{e(cp.res_of(r))}</td>'
                            f'<td data-label="Audio">{e(g["shown_audio"](r))}</td>'
                            f'<td data-label="Checked" class="small">{e(r["checked"])}<br>{g["source_link"](r)}</td></tr>')
                tid = f"cost-p{res.lower()}-{slug}"
                tids.append("#" + tid)
                note = combined_note(rows, slug, res)
                sections.append(h3 + "\n" + cp._table(
                    f'<thead><tr><th scope="col">Platform, plan or tier</th><th scope="col">$/s, seller, plan and label</th>'
                    f'<th scope="col">{secs}s clip</th><th scope="col">Resolution</th><th scope="col">Audio</th>'
                    f'<th scope="col">Checked</th></tr></thead><tbody>{trs}</tbody>', tid)
                    + (f'\n<p class="small">{e(note.strip())}</p>' if note else ""))
    foot = ("<ul class=\"small\">" + "".join(f"<li>{e(n)}</li>" for n in notes) + "</ul>") if notes else ""
    method = f"""<h2 id="method">How these numbers work</h2>
<ul>
<li>Each price is one row of our <a href="{root("/data/")}">price data</a>, copied from the vendor page linked in its row, with the date we checked it.</li>
<li>For each model and resolution we take its lowest price per second on any platform we track, and multiply by {secs} seconds. A model whose longest clip is shorter than {secs} seconds needs more than one clip, and the row says how many.</li>
<li>Credit-plan rows {e(g["CREDIT_USE"])}. Unused credits make the real cost per second higher. Rows labelled estimated are not list prices. A sale price shows its regular price next to it.</li>
<li>Plan or tier, resolution and audio are shown as the vendor states them. Rows that name a tier but no resolution, or a combined value such as 720p/1080p, are not ranked. "Not listed" means our data has no price at that resolution.</li>
<li>Rows are ordered by the clip total only. Affiliate links never change the order.</li>
<li>This page rebuilds with every daily price check. If any row on it goes more than {cp.STALE_DAYS} days without a check, the page shows a notice and is hidden from search until it is re-checked. Oldest check on this page: {e(cp.day_text(old)) if old else "none"}.</li>
</ul>"""
    body = f"""<p class="small"><a href="{root("/")}">Prices</a> › Cost › {e(page["h1"])}</p>
<h1>{e(page["h1"])}</h1>
{g["byline_html"]()}
{stale_html}
<p class="lead">{e(lead)}</p>
<p class="small">{e(page["description"])}</p>
{g["partner_lines_html"](page["path"])}
{chr(10).join(sections)}
{foot}
<p class="small">See every price on the model pages, or check a credit plan in the <a href="{root("/calculator/")}">credit calculator</a>.</p>
{method}
{g["news_box"]()}"""
    ld = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": page["h1"],
        "description": page["description"],
        "url": g["SITE_URL"] + page["path"],
        "dateModified": LAST,
        "about": [{"@type": "Thing", "name": name[s]} for s in models],
        "publisher": {"@type": "Organization", "@id": g["ORG_ID"], "name": g["BRAND"], "url": g["SITE_URL"] + "/"},
    }
    # Row headers carry long variant names (e.g. "gemini-omni-1.2-flash (1080p with upsampling)"); let them wrap
    # so the 1080p table fits the desktop column instead of scrolling sideways. The clip column gets room only on
    # wide screens; at 1024px the minimum width pushed the table 29px past its column.
    head = cp._css(tuple(tids)) + "<style>" + ",".join(f"{t} tbody th" for t in tids) + "{white-space:normal;min-width:180px}@media(min-width:1100px){" + ",".join(f"{t} td:nth-child(3)" for t in tids if not t.startswith("#cost-p")) + "{min-width:150px}}</style>" + g["ld_join"](ld, g["breadcrumb_ld"]([("Prices", "/"), (page["h1"], page["path"])]))
    g["page"](page["path"], title_of(page), page["description"], body, "", head,
              robots="noindex,follow" if stale else "index,follow")
    if not stale:
        g["SITEMAP_LASTMOD"][page["path"]] = LAST
    tops = {res: [(x[0], x[1], x[2], x[3], lab.regular_text(x[1], secs)) for x in ranks[res][0][:3]] for res in page["resolutions"]}
    return {"path": page["path"], "stale": stale, "oldest": old, "short": short, "unknown": unknown,
            "missing": {res: ranks[res][1] for res in page["resolutions"]}, "tops": tops}


def render(g):
    out = [render_page(g, p) for p in COST_PAGES]
    g["COST_PAGES"] = out
    return out


def sitemap_paths(g):
    return [p["path"] for p in g.get("COST_PAGES", []) if not p["stale"]]


def llms_lines(g):
    lines = []
    for page, built in zip(COST_PAGES, g.get("COST_PAGES", [])):
        if built["stale"]:
            continue
        bits = []
        for res in page["resolutions"]:
            top = built["tops"][res]
            if top:
                slug, r, total, n, reg = top[0]
                bits.append(f"{res} from {g['_money_places'](total, 2)} ({g['models'][slug]['name']} on {r['platform']}"
                            + (f"; {reg}" if reg else "") + ")")
        tail = f"Ranked for all {len(g['models'])} models" + (", with every platform's price" if page.get("by_platform") else "")
        lines.append(f"- [{page['title']}]({g['SITE_URL']}{page['path']}): cheapest {page['seconds']}-second clip: "
                     f"{'; '.join(bits)}. {tail}.")
    return lines
