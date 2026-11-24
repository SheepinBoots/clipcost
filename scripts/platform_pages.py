"""One-platform price pages under /platforms/.

Imported by scripts/build_site.py. One entry in PLATFORM_PAGES is one page: every covered
model the platform sells, priced on each of its plans in data/prices.json. Built for
/platforms/krea/ and reusable for /platforms/magnific/ with one more entry.

Rules
- Rows are the platform's current rows in prices.json; nothing is invented. A plan the
  platform sells but our data has no rows for is named in the entry's `gap_note`.
- Credit- or unit-plan rows are estimates: plan price / units a month x units per clip /
  clip length. The method table shows those numbers from the same plan and row data.
- A clip total is usd_per_second x seconds. Past a model's longest single clip (the cap,
  from the rows or cost_pages.CAPS) the row says how many clips it needs.
- A sale plan shows its regular price next to it through compare_pages.Labels (the live
  deal), so the labels drop when the deal ends and the daily check re-derives the rows.
- Stale guard: same as /compare/ (compare_pages.STALE_DAYS).
"""
import datetime
import math

import compare_pages as cp
import cost_pages as cost

PLATFORM_PAGES = [
    {
        "path": "/platforms/krea/",
        "platform": "Krea",
        "title": "Krea AI Video Prices by Model and Plan",
        "h1": "Krea AI video prices by model and plan",
        "description": ("Every Krea video model we track, priced per second and per 10-second clip on each "
                        "Krea plan, estimated from Krea's compute units. Rebuilt daily."),
        "seconds": 10,
        # Krea's own word for its plan currency.
        "unit": "compute units",
        "gap_note": ("Krea also sells Basic on monthly billing and a Max plan. Our price data has no rows for "
                     "them yet, so they are not priced here."),
    },
    {
        "path": "/platforms/magnific/",
        "platform": "Magnific",
        "title": "Magnific AI Video Prices by Model and Plan",
        "h1": "Magnific AI video prices by model and plan",
        "description": ("Every Magnific video model we track, priced per second and per 10-second clip on each "
                        "Magnific plan, from Magnific's credit prices. Rebuilt daily."),
        "seconds": 10,
        "unit": "credits",
        "former_name": "Magnific was formerly called Freepik.",
        # Magnific states credits per clip, so its rows are worked out from stated numbers, not estimates.
        "units_note": ("Magnific's pricing page states the credits each model uses per clip, so these rows use stated "
                       "numbers. Annual plans grant the year's credits up front, valid for one year; the monthly figure "
                       "is the yearly total ÷ 12."),
        "gap_note": ("Magnific also bills these plans monthly. Our price data has only the annual plan cards, so "
                     "monthly billing is not priced here."),
    },
]


def title_of(page):
    return page["title"] + cp.BRAND_SUFFIX


def page_rows(g, page):
    """The platform's current rows for covered models, in model, variant and plan order."""
    models, plans = g["models"], g["plans"]
    order = {pid: i for i, pid in enumerate(plans)}
    mo = {s: i for i, s in enumerate(models)}
    rs = [r for r in g["rows"] if r["platform"] == page["platform"] and r["model"] in models]
    first = {}
    for r in rs:
        first.setdefault((r["model"], r["variant"]), len(first))
    rs.sort(key=lambda r: (mo[r["model"]], first[(r["model"], r["variant"])], order.get(r.get("plan"), 99), r["usd_per_second"]))
    return rs


def page_plans(g, rs):
    """[(plan id, plan)] used by the rows, in prices.json order."""
    used = {r.get("plan") for r in rs}
    return [(pid, p) for pid, p in g["plans"].items() if pid in used]


def plan_gaps(g, rows, today):
    """{plan id: reason} for plans whose rows we leave unpriced: no plan card, or a card older than STALE_DAYS."""
    out = {}
    for r in rows:
        pid = r.get("plan")
        p = g["plans"].get(pid)
        if p is None:
            out[pid] = "not priced: no plan card in our data"
        elif not p.get("checked") or (datetime.date.fromisoformat(today) - datetime.date.fromisoformat(p["checked"])).days > cp.STALE_DAYS:
            out[pid] = (f"not priced: plan card last checked {cp.day_text(p['checked']) if p.get('checked') else 'never'}, "
                        f"more than {cp.STALE_DAYS} days ago")
    return out


def sale_state(g, plan):
    """(deal, live) for a plan with a sale block; (None, False) otherwise."""
    sale = plan.get("sale")
    if not sale:
        return None, False
    deal = g["DEAL_BY_ID"].get(sale.get("deal_id"))
    live = any(d["id"] == sale.get("deal_id") for d in g["LIVE_DEALS"])
    return deal, live


def mo(v):
    """5 -> '5', 14.5 -> '14.50' (plan prices per month)."""
    return f"{v:g}" if float(v).is_integer() else f"{v:.2f}"


def clips_in_plan(plan, r):
    upc = r.get("credits_per_clip")
    if not upc:
        return None
    return math.floor(plan["credits_month"] / upc + 1e-6)


def links_html(slug, root, rows=None, nl=False):
    """Small link line for a model page ('*' = every platform page, e.g. the calculator)."""
    hits = [p for p in PLATFORM_PAGES
            if slug == "*" or any(r["platform"] == p["platform"] and r["model"] == slug for r in (rows or []))]
    if not hits:
        return ""
    links = " · ".join(f'<a href="{root(p["path"])}">{p["title"]}</a>' for p in hits)
    return f'<p class="small">Platform prices: {links}.</p>' + ("\n" if nl else "")


def vendor_link(vendor, root):
    """' · <a>Krea AI Video Prices by Model and Plan</a>' for a live deal card of a vendor with a page."""
    hits = [p for p in PLATFORM_PAGES if p["platform"] == vendor]
    return "".join(f' · <a class="small" href="{root(p["path"])}">{p["title"]}</a>' for p in hits)


def render_page(g, page):
    e, root, rate_money = g["e"], g["root"], g["rate_money"]
    models, TODAY, LAST = g["models"], g["TODAY"], g["LAST"]
    two = g["_money_places"]
    secs, unit, plat = page["seconds"], page["unit"], page["platform"]
    lab = cp.Labels(g, g["rows"], TODAY)
    every = page_rows(g, page)
    gaps = plan_gaps(g, every, TODAY)
    rs = [r for r in every if r.get("plan") not in gaps]
    plist = page_plans(g, rs)
    # A row is an estimate when the platform's clip counts are approximate (Krea); else it uses stated credits.
    est = bool(rs) and all(r.get("status") == "estimate" for r in rs)
    approx = "~" if est else ""
    stale = cp.is_stale(rs, TODAY, cp.STALE_DAYS)
    old = cp.oldest_checked(rs)
    run = cp.run_text(g.get("CHECK_RUN"), LAST)
    slugs = list(dict.fromkeys(r["model"] for r in rs))
    variants = list(dict.fromkeys((r["model"], r["variant"]) for r in rs))
    # One option per model, variant and resolution (Magnific sells Seedance 2.5 at 720p and 1080p).
    key = lambda r: (r["model"], r["variant"], str(r.get("resolution") or ""))
    options = list(dict.fromkeys(key(r) for r in rs))
    multi_res = {(m, v) for m, v, _ in options if sum(1 for o in options if o[:2] == (m, v)) > 1}

    def label(r):
        return r["variant"] + (f', {g["shown_resolution"](r)}' if (r["model"], r["variant"]) in multi_res else "")
    caps = {s: cost.model_cap(g["rows"], s)[0] for s in slugs}

    def cap_of(r):
        return cp.stated_max(r) or caps[r["model"]]

    unknown = [s for s in slugs if caps[s] is None and not any(cp.stated_max(r) for r in rs if r["model"] == s)]
    notes = []
    for s in unknown:
        notes.append(f"‡ Our price data does not state the longest single clip for {models[s]['name']}. The {secs}-second "
                     f"total is the price per second × {secs}; check {plat} for whether {secs} seconds is one clip.")

    def model_link(r):
        return f'<a href="{root("/models/" + r["model"] + "/")}">{e(label(r))}</a>'

    def clip_cell(r):
        n = cp.clips_needed(secs, cap_of(r))
        mark = '<span class="small">‡</span>' if r["model"] in unknown else ""
        more = f'<br><span class="small">{n} clips (max {cap_of(r):g}s each)</span>' if n > 1 else ""
        reg = lab.regular_text(r, secs)
        reg_html = f'<br><span class="small regular">{e(reg)}</span>' if reg else ""
        return (f'<td data-label="{secs}s clip" class="num"><b>{two(r["usd_per_second"] * secs, 2)}</b>{mark}{more}'
                f'<br><span class="small">{e(lab.seller_short(r))}</span>{reg_html}</td>')

    def price_cell(r):
        return (f'<td data-label="$/s"><b>{rate_money(r["usd_per_second"])}/s</b> {lab.seller_html(r, regular=True)}'
                f'{g["deal_badges"](r)}{g["assumption_html"](r)}</td>')

    def facts(r):
        return (f'<td data-label="Resolution">{e(g["shown_resolution"](r))}</td>'
                f'<td data-label="Audio">{e(g["shown_audio"](r))}</td>')

    # 1. Cheapest plan for each model and variant.
    best = {}
    for r in rs:
        k = key(r)
        if k not in best or r["usd_per_second"] < best[k]["usd_per_second"]:
            best[k] = r
    ranked = sorted(best.values(), key=lambda r: (r["usd_per_second"], r["variant"]))
    trs = "".join(
        f'<tr><td data-label="Rank" class="num">{i + 1}</td>'
        f'<th scope="row">{model_link(r)}<br><span class="small">Plan: {e(lab.plan_text(r))} · {e(models[r["model"]]["name"])}</span></th>'
        + clip_cell(r) + price_cell(r) + facts(r)
        + f'<td data-label="Checked" class="small">{e(r["checked"])}<br>{g["source_link"](r)}</td></tr>'
        for i, r in enumerate(ranked))
    tids = ["#plat-cheapest", "#plat-plans", "#plat-method", "#plat-units"]
    sections = [
        f'<h2 id="cheapest">Cheapest {e(plat)} plan for each model: {len(ranked)} {"options" if multi_res else "variants"} {"from" if multi_res else "of"} {len(slugs)} models</h2>\n'
        f'<p class="small">Each model variant {e(plat)} sells, on its cheapest {e(plat)} plan, ordered by price per second. '
        + (f'Every row is an estimate from {e(plat)}\'s plans.' if est else f'Every row is worked out from {e(plat)}\'s plan prices and credits.') + '</p>\n'
        + cp._table(
            f'<thead><tr><th scope="col">Rank</th><th scope="col">Model, plan</th><th scope="col">{secs}s clip</th>'
            f'<th scope="col">$/s, plan and label</th><th scope="col">Resolution</th><th scope="col">Audio</th>'
            f'<th scope="col">Checked</th></tr></thead><tbody>{trs}</tbody>', "plat-cheapest")]

    # 2. Every row, by model and plan.
    trs = ""
    for r in rs:
        plan = g["plans"].get(r.get("plan")) or {}
        upc = r.get("credits_per_clip")
        units = (f'{approx}{upc:,.0f} {e(unit)} per {r["clip_seconds"]:g}s clip' if upc and r.get("clip_seconds") else "not stated")
        trs += (f'<tr><th scope="row">{model_link(r)}<br><span class="small">Plan: {e(lab.plan_text(r))}</span></th>'
                + price_cell(r) + clip_cell(r) + facts(r)
                + f'<td data-label="Units">{units}</td>'
                + f'<td data-label="Checked" class="small">{e(r["checked"])}<br>{g["source_link"](r)}</td></tr>')
    sections.append(
        f'<h2 id="plans">Every {e(plat)} video price by plan: {len(rs)} rows</h2>\n'
        f'<p class="small">Each model variant on each {e(plat)} plan in our data. Plan, resolution and audio are shown as {e(plat)} states them.</p>\n'
        + cp._table(
            f'<thead><tr><th scope="col">Model, plan</th><th scope="col">$/s, plan and label</th><th scope="col">{secs}s clip</th>'
            f'<th scope="col">Resolution</th><th scope="col">Audio</th><th scope="col">{e(unit.capitalize())}</th>'
            f'<th scope="col">Checked</th></tr></thead><tbody>{trs}</tbody>', "plat-plans"))

    # 3. Method: the plans, then units per clip and clips per plan.
    ptrs, sale_notes = "", []
    for pid, p in plist:
        deal, live = sale_state(g, p)
        price = f'${mo(p["usd_month"])}/mo'
        if p.get("sale") and live:
            reg = p["sale"]["regular"]["usd_month"]
            price = (f'<b>${mo(p["usd_month"])}/mo</b> <span class="small">{e(cp.deal_name((deal or {}).get("title")))}, '
                     f'{e(g["when_label"](deal))}; <span class="regular">regular ${mo(reg)}/mo</span></span>')
            sale_notes.append(p["sale"].get("note") or "")
        elif p.get("sale"):
            price = (f'${mo(p["usd_month"])}/mo <span class="small">sale price; the sale was due to end '
                     f'{e(g["when_label"](deal) if deal else p["sale"]["ends_at"])}. These rows keep it until our daily '
                     f'check confirms the regular price on {e(plat)}.</span>')
        per = p["usd_month"] / p["credits_month"]
        ptrs += (f'<tr><th scope="row">{e(p["plan"])}</th><td data-label="Price">{price}</td>'
                 f'<td data-label="{e(unit.capitalize())} a month" class="num">{p["credits_month"]:,}</td>'
                 f'<td data-label="$ per unit" class="num">${per:.5f}</td>'
                 f'<td data-label="Checked" class="small">{e(p.get("checked") or "")}<br>{g["source_link"](p)}</td></tr>')
    for pid, why in gaps.items():
        p = g["plans"].get(pid) or {}
        ptrs += (f'<tr><th scope="row">{e(p.get("plan") or pid)}</th><td data-label="Price" colspan="3">{e(why[0].upper() + why[1:])}.</td>'
                 f'<td data-label="Checked" class="small">{e(p.get("checked") or "")}</td></tr>')
    plan_table = cp._table(
        f'<thead><tr><th scope="col">Plan</th><th scope="col">Price</th><th scope="col">{e(unit.capitalize())} a month</th>'
        f'<th scope="col">$ per unit</th><th scope="col">Checked</th></tr></thead><tbody>{ptrs}</tbody>', "plat-method")
    utrs = ""
    for opt in options:
        r = next(x for x in rs if key(x) == opt)
        upc = r.get("credits_per_clip")
        cells = "".join(
            f'<td data-label="Clips on {e(p["plan"])}" class="num">'
            + (f'{approx}{clips_in_plan(p, r):,}' if any(x.get("plan") == pid and key(x) == opt for x in rs) and upc else "–")
            + "</td>" for pid, p in plist)
        utrs += (f'<tr><th scope="row">{model_link(r)}</th>'
                 f'<td data-label="Clip length" class="num">{r["clip_seconds"]:g}s</td>'
                 f'<td data-label="{e(unit.capitalize())} per clip" class="num">' + (f'{approx}{upc:,.0f}' if upc else "not stated") + "</td>"
                 + cells + "</tr>")
    units_table = cp._table(
        f'<thead><tr><th scope="col">Model</th><th scope="col">Clip length</th><th scope="col">{e(unit.capitalize())} per clip</th>'
        + "".join(f'<th scope="col">Clips a month on {e(p["plan"])}</th>' for _pid, p in plist)
        + f'</tr></thead><tbody>{utrs}</tbody>', "plat-units")
    ex = ranked[0] if ranked else None
    ex_plan = (g["plans"].get(ex.get("plan")) or {}) if ex else {}
    example = ""
    if ex and ex_plan and ex.get("credits_per_clip"):
        per = ex_plan["usd_month"] / ex_plan["credits_month"]
        example = (f"<li>Example: {e(ex['variant'])} on {e(ex_plan['plan'])} is ${mo(ex_plan['usd_month'])}/mo ÷ "
                   f"{ex_plan['credits_month']:,} {e(unit)} = ${per:.5f} per unit; × {approx}{ex['credits_per_clip']:,.1f} {e(unit)} per "
                   f"{ex['clip_seconds']:g}s clip = ${ex['usd_per_clip']:.3f} a clip; ÷ {ex['clip_seconds']:g} seconds = "
                   f"{rate_money(ex['usd_per_second'])}/s. That plan's {ex_plan['credits_month']:,} {e(unit)} make about "
                   f"{clips_in_plan(ex_plan, ex):,} such clips a month.</li>")
    sections.append(f"""<h2 id="method">How these numbers work</h2>
<p>{e(plat)} sells video through monthly allowances of {e(unit)}, not a price per second. Every price on this page is {"our estimate" if est else "worked out"} from {e(plat)}'s own USD plan data: the plan price, the {e(unit)} it includes, and the {e(unit)} each clip uses.</p>
{plan_table}
<h3 id="units">{e(unit.capitalize())} per clip and clips each plan includes</h3>
{units_table}
<ul>
<li>Price per second = plan price per month ÷ {e(unit)} a month × {e(unit)} per clip ÷ clip length in seconds. The {secs}-second cost is that rate × {secs}. A model whose longest clip is shorter than {secs} seconds needs more than one clip, and the row says how many.</li>
<li>{e(page["units_note"]) if page.get("units_note") else f'{e(plat)} publishes approximate clip counts ("~") for its plans. We divide the plan\'s {e(unit)} by that count to get the {e(unit)} per clip, so every row is labelled estimated from credit plan.'}</li>
{example}
<li>Every row on this page {e(g["CREDIT_USE"])}. Unused {e(unit)} make the real cost per second higher.</li>
<li>A sale plan shows its regular price next to it. When the sale ends, the sale labels go away and the next daily check moves the rows to the regular plan price once {e(plat)}'s page shows it.</li>
<li>{e(page.get("gap_note") or "")} Only models VidFare covers are listed.</li>
<li>This page rebuilds with every daily price check. If any row on it goes more than {cp.STALE_DAYS} days without a check, the page shows a notice and is hidden from search until it is re-checked. Oldest check on this page: {e(cp.day_text(old)) if old else "none"}.</li>
</ul>""" + ("".join(f'\n<p class="small">{e(n)}</p>' for n in sale_notes if n)))

    stale_html = ""
    if stale:
        stale_html = (f'<p class="disclose"><b>Stale data:</b> at least one price on this page was last checked '
                      f'{e(cp.day_text(old)) if old else "never"}, more than {cp.STALE_DAYS} days ago. Check {e(plat)} before you buy. '
                      f'This page is hidden from search until the prices are re-checked.</p>')
    if ex:
        n = cp.clips_needed(secs, cap_of(ex))
        reg = lab.regular_text(ex, secs)
        lead = (f"{plat} sells {len(slugs)} of the {len(models)} video models we track, as {len(variants)} model variants on "
                f"{len(plist)} plans in our data. The cheapest is {ex['variant']} at {rate_money(ex['usd_per_second'])}/s "
                f"{lab.seller(ex)}, so a {secs}-second video costs {two(ex['usd_per_second'] * secs, 2)}"
                + (f", {n} clips" if n > 1 else "") + (f" ({reg})" if reg else "")
                + f". Every price here is {'estimated' if est else 'worked out'} from {plat}'s {'plans' if est else 'credit plans'} and {g['CREDIT_USE']}. Prices last checked {run}.")
    else:
        lead = f"Our price data has no current {plat} video rows. Prices last checked {run}."
    foot = ("<ul class=\"small\">" + "".join(f"<li>{e(n)}</li>" for n in notes) + "</ul>") if notes else ""
    faqs = cp.data_faqs(g, f"How much does AI video cost on {plat}?", lead, run, old)
    body = f"""<p class="small"><a href="{root("/")}">Prices</a> › Platforms › {e(page["h1"])}</p>
<h1>{e(page["h1"])}</h1>
{g["byline_html"]()}
{stale_html}
<p class="lead">{e(lead)}</p>
<p class="small">{e(page["description"])}</p>{f'{chr(10)}<p class="small">{e(page["former_name"])}</p>' if page.get("former_name") else ""}
{g["page_sponsor_html"](page["path"])}
{g["partner_lines_html"](page["path"])}
{chr(10).join(sections[:1] + [g["news_box_inline"]()] + sections[1:2])}
{foot}
{sections[2]}
<p class="small">See every platform on the model pages, or check a {e(plat)} plan in the <a href="{root("/calculator/")}">credit calculator</a>.</p>
{g["data_links_html"](page["path"])}
{g["faq_html"](faqs)}
{g["news_box"]()}"""
    ld = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": page["h1"],
        "description": page["description"],
        "url": g["SITE_URL"] + page["path"],
        "dateModified": LAST,
        "about": [{"@type": "Organization", "name": plat}] + [{"@type": "Thing", "name": models[s]["name"]} for s in slugs],
        "publisher": {"@type": "Organization", "@id": g["ORG_ID"], "name": g["BRAND"], "url": g["SITE_URL"] + "/"},
    }
    import schema_ld
    ld_blocks = [ld, g["guide_faq_ld"](page["path"], faqs)] + [x for x in [schema_ld.offer_list(g, page["path"], page["h1"] + " – prices per second", rs)] if x]
    head = (cp._css(tuple(tids)) + "<style>" + ",".join(f"{t} tbody th" for t in tids) + "{white-space:normal;min-width:160px}"
            # Column headings wrap too, so the units table (one column per plan) fits at 1024px and up.
            + ",".join(f"{t} thead th" for t in tids) + "{white-space:normal}"
            # The clip column gets room only on wide screens, as on /cost/ pages.
            "@media(min-width:1100px){#plat-cheapest td:nth-child(3),#plat-plans td:nth-child(3){min-width:150px}}</style>"
            + g["ld_join"](*ld_blocks, g["breadcrumb_ld"]([("Prices", "/"), (page["h1"], page["path"])])))
    g["page"](page["path"], title_of(page), page["description"], body, "", head,
              robots="noindex,follow" if stale else "index,follow")
    if not stale:
        g["SITEMAP_LASTMOD"][page["path"]] = LAST
    return {"est": est, "gaps": gaps, "path": page["path"], "stale": stale, "oldest": old, "rows": rs, "ranked": ranked,
            "models": slugs, "plans": [pid for pid, _ in plist],
            "cheapest": [(r, lab.regular_text(r), lab.regular_text(r, secs)) for r in ranked]}


def render(g):
    out = [render_page(g, p) for p in PLATFORM_PAGES]
    g["PLATFORM_PAGES"] = out
    return out


def sitemap_paths(g):
    return [p["path"] for p in g.get("PLATFORM_PAGES", []) if not p["stale"]]


def llms_lines(g):
    lines = []
    rm = g["rate_money"]
    for page, built in zip(PLATFORM_PAGES, g.get("PLATFORM_PAGES", [])):
        if built["stale"] or not built["ranked"]:
            continue
        r, reg, _ = built["cheapest"][0]
        plan = cp.plan_short(g["shown_tier"](r))
        lines.append(f"- [{page['title']}]({g['SITE_URL']}{page['path']}): {len(built['models'])} models, "
                     f"{len(built['rows'])} plan rows, all {'estimated' if built['est'] else 'worked out'} from {page['platform']}'s plans. Cheapest: "
                     f"{r['variant']} {rm(r['usd_per_second'])}/s ({plan}" + (f"; {reg}" if reg else "") + ").")
    return lines
