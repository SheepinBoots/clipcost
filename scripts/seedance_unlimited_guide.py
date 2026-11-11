"""Guide: Unlimited Seedance 2.5 plans compared.

Imported by scripts/build_site.py. Every offer, price, window, and cap is read
from data/deals.json (the `windows` list on each unlimited_window deal) and
data/prices.json (plan prices and per-second API rows). Nothing here hard-codes
a price. Break-even seconds are plan price / API dollars per second.
"""
import math

PATH = "/guides/seedance-2-5-unlimited/"
LABEL = "Unlimited Seedance 2.5"
MODEL = "seedance-2-5"
PHRASE = "Unlimited Seedance 2.5 Plans Compared"
RES_ORDER = {"480p": 480, "720p": 720, "1080p": 1080}

# Pages checked for this guide that hold no Seedance 2.5 unlimited offer.
# Text only, no prices: each line says what the page shows and links it.
NOT_COUNTED_CHECKED = "2026-11-11"
NOT_COUNTED = [
    ("Runway", "https://runway.com/pricing",
     "Pro and Max list Seedance 2.5 as a model with no Unlimited label. The Unlimited badge on that row belongs to Topaz AI Upscale."),
    ("Magnific", "https://www.magnific.com/pricing",
     "Seedance 2.5 (480p Draft, 720p, 1080p) is charged in credits per 4-second clip. The UNLIMITED tags there are on Kling 2.5 and image models."),
    ("Krea", "https://www.krea.ai/pricing",
     "Max and Business list \u201cUnlimited relaxed generations\u201d, but the page does not say that covers Seedance 2.5. Seedance 2.5 is counted against compute units."),
    ("Higgsfield Team", "https://higgsfield.ai/pricing",
     "The Team business plan lists unlimited Seedance 2.0 (15s, 720p), not Seedance 2.5."),
]


def _ceil(x):
    return int(math.ceil(x - 1e-9))


def usd(v):
    """Whole dollars without cents, else two places. $4,800 and $47, not $4800.00."""
    return f"${v:,.0f}" if float(v).is_integer() else f"${v:,.2f}"


def per_sec(v):
    """API rate as stored, up to 4 places, so the break-even math can be redone by hand."""
    txt = f"{v:.4f}".rstrip("0")
    if len(txt.split(".")[1]) < 2:
        txt = f"{v:.2f}"
    return "$" + txt


def _int(n):
    return f"{int(n):,}" if float(n).is_integer() else f"{n:,.2f}"


def _deals(g):
    doc = g["deal_doc"]
    return [d for d in doc["deals"] if d.get("type") == "unlimited_window" and MODEL in (d.get("models") or [])]


def live_windows(g):
    """One record per plan window on every live Seedance 2.5 unlimited deal."""
    dealmod, today = g["dealmod"], g["TODAY"]
    plans, by_id = g["plans"], g["DEAL_BY_ID"]
    out = []
    for deal in _deals(g):
        if not dealmod.is_current(deal, today):
            continue
        for w in deal.get("windows") or []:
            rec = dict(w, deal=deal)
            billing = w.get("billing") or ""
            if w.get("usd_seat_month") is not None:
                seats = w.get("seats") or 1
                month = w["usd_seat_month"] * seats
                rec["month"] = month
                rec["checkout"] = month * 12 if billing == "annual" else month
                yearly = f", billed yearly ({usd(month * 12)} a year)" if billing == "annual" else ""
                rec["price_text"] = (
                    f"${w['usd_seat_month']:g}/seat/mo{yearly}; the card shows {seats} seats "
                    f"({usd(month)}/mo)"
                )
            else:
                plan = plans.get(w.get("plan_id") or "")
                if not plan or plan.get("usd_month") is None:
                    continue
                sale = by_id.get(w.get("price_deal") or "")
                if sale and dealmod.is_current(sale, today) and sale.get("price_after") is not None:
                    first, renew = sale["price_after"], sale.get("price_before") or plan["usd_month"]
                    rec["month"] = first
                    rec["checkout"] = first
                    rec["price_text"] = f"${first:g} first month, then ${renew:g}/mo"
                elif billing == "annual":
                    rec["month"] = plan["usd_month"]
                    rec["checkout"] = plan["usd_month"] * 12
                    rec["price_text"] = (
                        f"${plan['usd_month']:g}/mo billed yearly ({usd(plan['usd_month'] * 12)} a year)"
                    )
                else:
                    rec["month"] = plan["usd_month"]
                    rec["checkout"] = plan["usd_month"]
                    rec["price_text"] = f"${plan['usd_month']:g}/mo"
            out.append(rec)
    out.sort(key=lambda r: (r["checkout"], r["deal"]["id"], r.get("plan") or ""))
    return out


def ended_deals(g):
    dealmod, today = g["dealmod"], g["TODAY"]
    rs = [d for d in _deals(g) if not dealmod.is_current(d, today) and not dealmod.is_upcoming(d, today)]
    return sorted(rs, key=lambda d: d.get("end") or "", reverse=True)


def api_rows(g, res, published_only=False):
    rs = [
        r for r in g["rows"]
        if r["model"] == MODEL and r.get("kind") == "api" and r.get("resolution") == res
        and (not published_only or g["rate_label"](r) == "published rate")
    ]
    return sorted(rs, key=lambda r: (r["usd_per_second"], r["id"]))


def blurb(g):
    ws = live_windows(g)
    if not ws:
        return "No live unlimited Seedance 2.5 offer is in the deal data. Expired offers and the per-second rates are compared."
    lo = min(w["days"] for w in ws)
    hi = max(w["days"] for w in ws)
    cheapest = ws[0]
    span = f"{lo} days" if lo == hi else f"{lo} to {hi} days"
    return (
        f"No plan is truly unlimited. The live windows run {span}, with clip and resolution caps, "
        f"from {usd(cheapest['checkout'])} at checkout."
    )


def render(g):
    e, root, outbound = g["e"], g["root"], g["outbound"]
    rate_money, cost_money, rate_label = per_sec, usd, g["rate_label"]
    models, LAST = g["models"], g["LAST"]
    name = models[MODEL]["name"]
    ws = live_windows(g)
    gone = ended_deals(g)
    if not ws and not gone:
        raise SystemExit("seedance unlimited guide needs at least one Seedance 2.5 unlimited_window deal")

    def src(url, text="source"):
        href, rel = outbound(url)
        return f'<a href="{e(href)}" rel="{rel}" target="_blank">{e(text)}</a>'

    checked_dates = [d.get("verified_date") or "" for d in _deals(g)]
    used_res = sorted({w["resolution"] for w in ws}, key=lambda s: RES_ORDER.get(s, 9999))
    picks = {}
    for res in used_res:
        any_rs = api_rows(g, res)
        pub_rs = api_rows(g, res, True)
        picks[res] = (any_rs[0] if any_rs else None, pub_rs[0] if pub_rs else None)
        for r in (picks[res][0], picks[res][1]):
            if r is not None:
                checked_dates.append(r.get("checked") or "")
    offers_checked = max(d for d in checked_dates if d) if any(checked_dates) else LAST
    g["SITEMAP_LASTMOD"][PATH] = offers_checked

    days = [w["days"] for w in ws]
    clips = [w["max_clip_seconds"] for w in ws if w.get("max_clip_seconds")]
    resl = [w["resolution"] for w in ws]
    vendors = sorted({w["deal"]["vendor"] for w in ws})
    web_only = all(g["dealmod"].conditions(w["deal"]).get("web_only") for w in ws) if ws else False
    speed_note = any("speed" in (w["deal"].get("notes") or "").lower() for w in ws)
    new_users = [w for w in ws if g["dealmod"].conditions(w["deal"]).get("new_users_only")]
    ends = sorted({w["deal"]["end"] for w in ws if w["deal"].get("end")})
    runway_gone = next((d for d in gone if d.get("vendor") == "Runway"), None)

    # ---------- short answer ----------
    if ws:
        span = f"{min(days)} days" if min(days) == max(days) else f"{min(days)} to {max(days)} days"
        lims = [
            f"a time window of {span}",
            f"a clip cap of {min(clips)} to {max(clips)} seconds" if clips and min(clips) != max(clips) else (f"a {clips[0]}-second clip cap" if clips else ""),
            f"a resolution cap ({', '.join(sorted(set(resl), key=lambda s: RES_ORDER.get(s, 9999)))} depending on plan)",
        ]
        if web_only:
            lims.append("web app only (no API, MCP or CLI)")
        if speed_note:
            lims.append("speed that may be slowed in busy periods")
        short = (
            f"No. Every live unlimited {name} offer we found ({', '.join(vendors)}) comes with "
            + ", ".join(x for x in lims[:-1] if x) + (", and " if len(lims) > 1 else "") + lims[-1] + "."
        )
        if ends:
            short += f" The sale that carries the individual-plan windows ends {ends[0]}."
    else:
        short = f"No live unlimited {name} offer is in our deal data right now."
    if runway_gone:
        short += f" Runway's unlimited {name} ended {runway_gone['end']}{' (the date we saw it gone)' if runway_gone.get('end_is_estimate') else ''}."
    limits_html = "<ul>" + "".join(f"<li>{e(x)}</li>" for x in lims if x) + "</ul>" if ws else ""

    # ---------- offer table ----------
    common = []
    if ws and all(g["dealmod"].conditions(w["deal"]).get("web_only") for w in ws):
        common.append("web app only")
    if ws and all("speed" in (w["deal"].get("notes") or "").lower() for w in ws):
        common.append("speed may be adjusted in high traffic")
    if ws and not new_users:
        common.append("none of the pages says new users only")
    one_vendor = len(vendors) == 1

    def plan_name(w):
        return w["plan"] if one_vendor else f"{w['deal']['vendor']} {w['plan']}"

    offer_head = "<thead><tr><th>Plan</th><th>Price</th><th>Window</th><th>Source</th></tr></thead>"
    offer_rows = []
    for w in ws:
        d = w["deal"]
        cond = g["dealmod"].conditions(d)
        extra = []
        if "business verification" in (w.get("quote") or "").lower():
            extra.append("business verification")
        if cond.get("new_users_only"):
            extra.append("new users only")
        if d.get("end"):
            extra.append(f"sale ends {d['end']}")
        extra_html = f'<div class="small">{e("; ".join(extra))}</div>' if extra else ""
        offer_rows.append(
            "<tr>"
            f"<td>{e(plan_name(w))}<div class=\"small\">{e(w.get('billing') or '')}</div></td>"
            f"<td>{e(w['price_text'])}</td>"
            f"<td><b>{w['days']} days</b> \u00b7 {e(w['resolution'])} \u00b7 {w['max_clip_seconds']}s clips{extra_html}</td>"
            f"<td><details class=\"src\"><summary>source</summary><div class=\"math\">\u201c{e(w.get('quote') or d.get('source_quote') or '')}\u201d "
            f"{src(d['source_url'], 'pricing page')} \u00b7 checked {e(d.get('verified_date') or '')}</div></details></td>"
            "</tr>"
        )
    offer_table = (
        f'<div class="tblwrap fit"><table>{offer_head}<tbody>{"".join(offer_rows)}</tbody></table></div>'
        if offer_rows else "<p>No live offer.</p>"
    )
    common_html = f'<p class="small">Every window below: {e("; ".join(common))}.</p>' if common else ""

    # ---------- break-even ----------
    be_head = "<thead><tr><th>Plan</th><th>You pay</th><th>Break-even</th><th>Per day</th></tr></thead>"
    be_rows, be_facts = [], []
    for w in ws:
        best, pub = picks.get(w["resolution"], (None, None))
        plan_cell = f"<td>{e(plan_name(w))}<div class=\"small\">{e(w.get('billing') or '')}, {e(w['resolution'])}</div></td>"
        if best is None:
            be_rows.append(
                f"<tr>{plan_cell}<td class=\"num\">{cost_money(w['checkout'])}</td>"
                "<td>no API row at this resolution</td><td>\u2014</td></tr>"
            )
            continue
        secs = _ceil(w["checkout"] / best["usd_per_second"])
        per_day = w["checkout"] / best["usd_per_second"] / w["days"]
        clip_n = per_day / w["max_clip_seconds"] if w.get("max_clip_seconds") else None
        vs = (
            f'<div class="small">vs {rate_money(best["usd_per_second"])}/s, {e(best["platform"])}, '
            f'{e(rate_label(best))} ({src(best["source_url"])})</div>'
        )
        alt = ""
        if pub is not None and pub is not best:
            alt = (
                f'<div class="small">Cheapest published rate, {rate_money(pub["usd_per_second"])}/s {e(pub["platform"])}: '
                f'{_int(_ceil(w["checkout"] / pub["usd_per_second"]))} s</div>'
            )
        month_line = ""
        if w["checkout"] != w["month"]:
            month_line = (
                f'<div class="small">One month\u2019s share ({cost_money(w["month"])}): '
                f'{_int(_ceil(w["month"] / best["usd_per_second"]))} s</div>'
            )
        per_day_txt = f"<b>{_int(_ceil(per_day))} s</b>"
        if clip_n is not None:
            per_day_txt += f'<div class="small">\u2248 {clip_n:.1f} max-length {w["max_clip_seconds"]}s clips</div>'
        be_rows.append(
            f"<tr>{plan_cell}"
            f"<td class=\"num\">{cost_money(w['checkout'])}</td>"
            f"<td><b>{_int(secs)} s</b>{vs}{month_line}{alt}</td>"
            f"<td>{per_day_txt}</td>"
            "</tr>"
        )
        be_facts.append((w, best, secs, per_day))
    be_table = (
        f'<div class="tblwrap fit"><table>{be_head}<tbody>{"".join(be_rows)}</tbody></table></div>'
        if be_rows else ""
    )
    formula = (
        "Break-even seconds = what you pay at checkout \u00f7 the cheapest current pay-per-second "
        f"{name} API rate at the same resolution, rounded up. Per day = break-even seconds \u00f7 days in the window."
    )
    assumptions = [
        "The whole checkout price is counted against Seedance 2.5. The plans also include monthly credits and other unlimited models, so this overstates the break-even if you use those too.",
        "Annual plans are billed yearly, so \u201cyou pay\u201d is 12 months at the per-month price. One month\u2019s share is shown under it.",
        "Every second you generate in the window is one you would otherwise have paid the API for. Retries count, because the API bills them too.",
        "API rows are matched on resolution only. Audio, input type and clip-length differences between an API row and the plan are not adjusted.",
        "Taxes are excluded, as on the vendor pages.",
    ]

    # ---------- when it wins ----------
    wins = []
    if be_facts:
        lo = min(be_facts, key=lambda f: (f[3], f[0]["checkout"]))
        hi = max(be_facts, key=lambda f: (f[3], f[0]["checkout"]))
        wins.append(
            f"Lowest daily bar: {lo[0]['deal']['vendor']} {lo[0]['plan']} ({lo[0].get('billing')}) needs about "
            f"{_int(_ceil(lo[3]))} seconds of {lo[0]['resolution']} video a day for {lo[0]['days']} days to beat "
            f"{rate_money(lo[1]['usd_per_second'])}/s on {lo[1]['platform']}."
        )
        if hi is not lo:
            wins.append(
                f"Highest daily bar: {hi[0]['deal']['vendor']} {hi[0]['plan']} ({hi[0].get('billing')}) needs about "
                f"{_int(_ceil(hi[3]))} seconds a day over {hi[0]['days']} days if you count the full checkout price against the window."
            )
    wins += [
        "Unlimited wins when you will generate a lot in a short, known stretch: batch work, many re-rolls of the same shot, or testing prompts before a paid render.",
        "Per-second wins when you need fewer seconds than the break-even, need the API or automation (the windows are web app only), need a deadline you can count on (speed can be slowed in busy periods), or need a clip length or resolution above the plan's cap.",
    ]
    hi_res = [w for w in ws if w["resolution"] == "1080p"]
    if hi_res:
        wins.append(
            "Only " + ", ".join(f"{w['deal']['vendor']} {w['plan']} ({w.get('billing')})" for w in hi_res)
            + " includes 1080p in the window. Every other live window stops at 720p or lower."
        )

    # ---------- expired ----------
    gone_head = "<thead><tr><th>Offer</th><th>Ended</th><th>Source</th></tr></thead>"
    gone_rows = []
    for d in gone:
        when = (d.get("end") or "date not stated") + (" (seen gone)" if d.get("end_is_estimate") else "")
        note = (d.get("notes") or "")
        last = note.rsplit("Checked ", 1)
        why = ("Checked " + last[1]) if len(last) == 2 and last[1][:10] == d.get("verified_date") else note
        gone_rows.append(
            "<tr>"
            f"<td>{e(d['vendor'])}: {e(d.get('title') or d['id'])}"
            f"<details class=\"src\"><summary>what changed</summary><div class=\"math\">{e(why)}</div></details></td>"
            f"<td>{e(when)}</td>"
            f"<td>{src(d['source_url'])} \u00b7 {e(d.get('verified_date') or '')}</td>"
            "</tr>"
        )
    gone_table = (
        f'<div class="tblwrap fit"><table>{gone_head}<tbody>{"".join(gone_rows)}</tbody></table></div>'
        if gone_rows else "<p>No expired offer is in the deal data.</p>"
    )

    not_counted = "<ul>" + "".join(
        f"<li><b>{e(v)}</b>: {e(t)} {src(u, 'Pricing page')} \u00b7 checked {NOT_COUNTED_CHECKED}.</li>"
        for v, u, t in NOT_COUNTED
    ) + "</ul>"

    checklist = [
        "Check the exact model. Seedance 2.5 and Seedance 2.0 windows are listed separately, and some plans unlock only 2.0.",
        "Match the billing toggle. The same plan name has a different window, clip cap and resolution on monthly and annual billing.",
        "Read the resolution and clip cap for your plan, and compare them with the length you actually need.",
        "Note the renewal price. A first-month sale price renews at the full monthly price.",
        "Plan for the web app only. Unlimited generations do not run through the API, MCP or CLI.",
        "Leave slack in your deadline. The vendor says unlimited speed can be adjusted during high traffic.",
        "Look for an Unlimited switch in the model menu. Higgsfield's August guide said generations drew from credits unless it was on.",
        "Count your break-even seconds with the table above before you pay.",
    ]

    # ---------- FAQ ----------
    faqs = [("Is there a truly unlimited Seedance 2.5 plan?", short)]
    if be_facts:
        lo = min(be_facts, key=lambda f: (f[2], f[0]["checkout"]))
        faqs.append((
            "How many seconds before an unlimited Seedance 2.5 plan pays off?",
            f"The smallest break-even in the table is {lo[0]['deal']['vendor']} {lo[0]['plan']} ({lo[0].get('billing')}): "
            f"{cost_money(lo[0]['checkout'])} \u00f7 {rate_money(lo[1]['usd_per_second'])}/s ({lo[1]['platform']}, {lo[0]['resolution']}) "
            f"= {_int(lo[2])} seconds. {formula}",
        ))
    faqs.append((
        "Does unlimited Seedance 2.5 work on the API?",
        ("No. Higgsfield says unlimited models are accessible only on higgsfield.ai, not on MCP/CLI, Canvas or Supercomputer. "
         "API calls are billed per second; the cheapest rates are on the Seedance 2.5 model page.")
        if web_only else "The live offers do not all say. Check the vendor page before you rely on it.",
    ))
    if runway_gone:
        faqs.append((
            "Is Runway's Seedance 2.5 unlimited?",
            f"Not any more. We saw it gone on {runway_gone['end']}: {runway_gone.get('source_quote') or ''}".strip(),
        ))
    starter_bit = ("Starter lists no Seedance 2.5 unlimited window on the pricing page. "
                   if any(w["deal"]["vendor"] == "Higgsfield" for w in ws) else "")
    faqs.append((
        "Is there free unlimited Seedance 2.5?",
        starter_bit + "We found no free unlimited Seedance 2.5 offer on the vendor pages we track. Every live window is part of a paid plan.",
    ))
    wan_gone = [d for d in g["deal_doc"]["deals"]
                if d.get("type") == "unlimited_window" and "wan-3-0" in (d.get("models") or [])
                and g["dealmod"].is_current(d, g["TODAY"])]
    faqs.append((
        "Is there an unlimited Wan 3.0 plan?",
        ("Yes, see the deals page." if wan_gone else
         "Not in our deal data right now. The last Wan 3.0 unlimited window we tracked has ended, and Higgsfield's pricing page lists Wan 3.0 at credit rates."),
    ))
    how = (
        formula + " Offers come from the vendor's own pricing page, with the date we checked it and the words it used. "
        "API rates are current rows from the price data, labelled published or estimated. "
        f"The full method is on the about page ({g['SITE_URL']}/about/)."
    )
    faqs.append(("How do we calculate this?", how))

    lead = short
    month = g["MONTH"]
    body = f"""<p class="small"><a href="{root("/guides/")}">Guides</a> \u203a {e(LABEL)}</p>
<h1>Unlimited {e(name)} plans compared ({e(month)})</h1>
<p class="lead">{e(lead)}</p>
<p class="small">Offers checked {e(offers_checked)}. Last checked {e(LAST)}.</p>
<h2>Is there a truly unlimited Seedance 2.5 plan?</h2>
<p>No. \u201cUnlimited\u201d here means unlimited generations inside these limits:</p>
{limits_html}
<h2>Live unlimited {e(name)} offers</h2>
<p>{len(ws)} plan windows{(" on " + e(vendors[0])) if len(vendors) == 1 else ""}, from the deal data, cheapest checkout first. Open a source to see the vendor's words and the date we checked.</p>
{common_html}
{offer_table}
<h2>Break-even: when does unlimited beat paying per second?</h2>
<p>{e(formula)}</p>
{be_table}
<p class="small">Assumptions:</p>
<ul class="small">{"".join(f"<li>{e(a)}</li>" for a in assumptions)}</ul>
<h2>When unlimited beats per-second, and when it doesn't</h2>
<ul>{"".join(f"<li>{e(x)}</li>" for x in wins)}</ul>
<h2>Expired or pulled offers</h2>
<p>Old screenshots still circulate. These offers are in our deal archive and are not live.</p>
{gone_table}
<h2>Checked, but not counted as unlimited {e(name)}</h2>
{not_counted}
<h2>Checklist before you pay</h2>
<ol>{"".join(f"<li>{e(x)}</li>" for x in checklist)}</ol>
<p>Related: <a href="{root(f"/models/{MODEL}/")}">{e(name)} price per second</a> \u00b7 <a href="{root("/deals/")}">all live deals</a> \u00b7 <a href="{root("/guides/is-higgsfield-worth-it/")}">is Higgsfield worth it?</a> \u00b7 <a href="{root(f"/calculator/?model={MODEL}")}">credit calculator</a></p>
{"".join(f"<h2>{e(q)}</h2><p>{e(a)}</p>" for q, a in faqs[1:-1])}
{g["how_block"](how)}"""

    title = g["page_title"](PHRASE)
    if ws:
        span = f"{min(days)}" if min(days) == max(days) else f"{min(days)}\u2013{max(days)}"
        desc = (
            f"No {name} plan is truly unlimited. {len(ws)} live windows of {span} days with clip and resolution caps, "
            f"from {cost_money(ws[0]['checkout'])}. Break-even seconds vs API $/s."
        )
    else:
        desc = f"No live unlimited {name} offer right now. Expired offers and break-even seconds vs the API $/s."
    if len(desc) > 160:
        raise SystemExit(f"{PATH} description is {len(desc)} characters")
    g["guide_page"](PATH, title, desc, body, faqs)
    return {"title": title, "desc": desc, "windows": ws, "breakeven": be_facts, "ended": gone}
