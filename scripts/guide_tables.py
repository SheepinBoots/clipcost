"""Shared dated per-second price table builder for upgraded guides.

Every figure, seller, plan, tier, resolution, audio flag, status, checked date,
and source URL comes straight from data/prices.json (g["rows"]). Reuses existing
.tblwrap / .fit / .amt / .small / .badges markup and CSS classes.
"""
from timefmt import day_label


def active_rows(g, model=None, platform=None):
    """Non-discontinued catalog rows with a numeric usd_per_second."""
    out = []
    for r in g["rows"]:
        if r.get("status") == "discontinued":
            continue
        if r.get("usd_per_second") is None:
            continue
        if model and r.get("model") != model:
            continue
        if platform and r.get("platform") != platform:
            continue
        out.append(r)
    return sorted(out, key=lambda r: (float(r["usd_per_second"]), r["id"]))


def cheapest_by_model(g, slugs=None):
    """Cheapest active catalog row for each covered model, sorted by $/s."""
    order = list(slugs or g["models"].keys())
    picks = []
    for slug in order:
        rs = active_rows(g, model=slug)
        if rs:
            picks.append(rs[0])
    return sorted(picks, key=lambda r: (float(r["usd_per_second"]), r["id"]))


def plat_link(g, platform, source_url=""):
    return g["plat_link"](platform, source_url)


def audio_label(g, r):
    return {"with": "with audio", "without": "without audio"}.get(g["shown_audio"](r), "not stated")


def plan_label(r):
    if r.get("plan_name"):
        return r["plan_name"]
    return "pay-as-you-go API" if r.get("kind") == "api" else "not listed"


def usage_note(g, r):
    base = (g["assumption_text"](r) or "").strip()
    math = (r.get("math") or "").strip()
    note = (r.get("note") or "").strip()
    if r.get("kind") == "plan":
        parts = [p for p in (base, math) if p]
        if not parts:
            parts = ["From credit plan. Assumes every credit you pay for is used."]
        return " ".join(parts)
    parts = [p for p in (base, math, note) if p]
    if not parts:
        return "Published rate, billed per second of output."
    return " ".join(parts)


def price_table(g, rows, *, table_id="prices", include_model=True, include_10s=False, min_width=1160):
    """Render a dated per-second price table with Seller, Plan, Tier, Resolution, Audio, Rate, Status, Usage, Source."""
    e = g["e"]
    rate_money = g["rate_money"]
    rate_label = g["rate_label"]
    cost_money = g["cost_money"]
    shown_resolution = g["shown_resolution"]
    shown_tier = g["shown_tier"]
    plat_link = g["plat_link"]
    outbound = g["outbound"]
    models = g["models"]

    cols = []
    if include_model:
        cols.append("<th>Model</th>")
    cols += [
        "<th>Seller</th>",
        "<th>Variant</th>",
        "<th>Plan</th>",
        "<th>Tier</th>",
        "<th>Resolution</th>",
        "<th>Audio</th>",
        "<th>$ / sec</th>",
    ]
    if include_10s:
        cols.append("<th>Per 10s</th>")
    cols += [
        "<th>Usage assumption</th>",
        "<th>Source and date checked</th>",
    ]
    head = "<thead><tr>" + "".join(cols) + "</tr></thead>"

    body = []
    for r in rows:
        mname = (models.get(r["model"]) or {}).get("name") or r["model"]
        mpath = g["root"](f"/models/{r['model']}/")
        seller = plat_link(r["platform"], r["source_url"])
        variant = r.get("variant") or mname
        plan = plan_label(r)
        tier = shown_tier(r)
        res = shown_resolution(r)
        aud = audio_label(g, r)
        rate = rate_money(r["usd_per_second"])
        status = rate_label(r)
        promo_until = ""
        if r.get("status") == "promo" and r.get("promo_until"):
            promo_until = f" until {e(r['promo_until'])}"
        href, rel = outbound(r["source_url"])
        src_html = (
            f'Checked {e(day_label(r.get("checked")))}. '
            f'<a href="{e(href)}" rel="{rel}" target="_blank">source</a>, '
            f'catalog row {e(r["id"])}'
        )
        cells = []
        if include_model:
            cells.append(f'<td><a href="{e(mpath)}">{e(mname)}</a></td>')
        cells += [
            f"<td>{seller}</td>",
            f"<td>{e(variant)}</td>",
            f"<td>{e(plan)}</td>",
            f"<td>{e(tier)}</td>",
            f"<td>{e(res)}</td>",
            f"<td>{e(aud)}</td>",
            f'<td class="num"><span class="amt">{e(rate)}/s</span> <span class="small">{e(status)}{promo_until}</span></td>',
        ]
        if include_10s:
            ten = cost_money(float(r["usd_per_second"]) * 10)
            cells.append(f'<td class="num">{e(ten)}</td>')
        cells += [
            f'<td class="small">{e(usage_note(g, r))}</td>',
            f'<td class="small">{src_html}</td>',
        ]
        body.append(f'<tr data-price-id="{e(r["id"])}">' + "".join(cells) + "</tr>")

    style = f' style="min-width:{int(min_width)}px;width:{int(min_width)}px"' if min_width else ""
    id_attr = f' id="{e(table_id)}"' if table_id else ""
    return f'<div class="tblwrap"{id_attr}><table{style}>{head}<tbody>{"".join(body)}</tbody></table></div>'
