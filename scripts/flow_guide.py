"""Google Flow credits calculator guide for VidFare.

Imported by scripts/build_site.py after guide_pages. Every plan price, credit
amount, credit cost, and quote is read from the "flow" section of
data/prices.json, which the daily check re-reads on Google's own pages. The API
comparison uses the current API rows for Veo 3.1 and Gemini Omni Flash. This
module does not hard-code a price, a credit amount, or a date.
"""
import json
from decimal import Decimal, ROUND_FLOOR

PATH = "/guides/google-flow-credits-calculator/"
PHRASE = "Google Flow Credits Calculator: Veo 3.1 & Omni Flash"
MODELS = ("veo-3-1", "gemini-omni-flash")
DAYS = 30  # Daily-credit toggle: 50 credits on each of 30 days, only if you generate every day.


def floor_int(n):
    return int(Decimal(str(n)).to_integral_value(rounding=ROUND_FLOOR))


def is_current(rec, today):
    gone = rec.get("retiring_on")
    return not (gone and gone <= today)


def plan_tier_key(plan):
    """Which column of Google's credit table a plan uses: Ultra or everyone else."""
    return "ultra" if (plan or {}).get("tier") == "ultra" else "non_ultra"


def credits_for(cost, plan, seconds):
    """Credits for one generation of `seconds`, for a plan record (None = no plan). None if not offered."""
    per_sec = cost.get("credits_per_second")
    if per_sec:
        lengths = cost["clip_seconds"]
        limit = lengths["subscriber_max"] if plan else lengths["max"]
        if seconds < lengths["min"] or seconds > limit:
            return None
        base = min(seconds, 10) * per_sec["up_to_10s"]
        extra = max(0, seconds - 10) * per_sec["extra_11_15s"]
        return base + extra
    if seconds not in cost["clip_seconds"]:
        return None
    table = cost["credits_per_generation"]
    if "all" in table:
        return table["all"]
    if str(seconds) in table:
        return table[str(seconds)]
    key = plan_tier_key(plan)
    return table.get(key)


def render(g):
    db = g["db"]
    flow = db.get("flow")
    if not flow:
        return
    e = g["e"]
    root = g["root"]
    rate_money = g["rate_money"]
    cost_money = g["cost_money"]
    tag = g["tag"]
    outbound = g["outbound"]
    guide_page = g["guide_page"]
    page_title = g["page_title"]
    models = g["models"]
    rows = g["rows"]
    TODAY = g["TODAY"]
    LAST = g["LAST"]
    SITE_URL = g["SITE_URL"]

    plans = flow["plans"]
    costs = [c for c in flow["credit_costs"] if is_current(c, TODAY)]
    calc_costs = [c for c in costs if "ultra_20x" not in (c.get("credits_per_generation") or {})]
    notices = {n["id"]: n for n in flow["notices"]}
    daily = flow["daily"]["credits_day"]
    help_url = flow["daily"]["source_url"]
    plans_url = next(iter(plans.values()))["source_url"]
    checked_dates = [p["checked"] for p in plans.values()] + [c["checked"] for c in flow["credit_costs"]]
    checked_dates += [n["checked"] for n in flow["notices"]] + [flow["daily"]["checked"], flow["plan_credits_check"]["checked"]]
    updated = max(checked_dates)
    oldest = min(checked_dates)
    g["SITEMAP_LASTMOD"][PATH] = updated

    def link(url, text):
        href, rel = outbound(url)
        return f'<a href="{e(href)}" rel="{rel}" target="_blank">{e(text)}</a>'

    def help_link(text="Google Flow Help"):
        return link(help_url, text)

    def plans_link(text="Google AI plans page"):
        return link(plans_url, text)

    def quote(nid):
        n = notices.get(nid)
        if not n:
            return ""
        return f'“{e(n["quote"])}”'

    def num(n):
        n = float(n)
        return f"{int(n):,}" if n.is_integer() else f"{n:,.2f}".rstrip("0").rstrip(".")

    def per_credit(p):
        return p["usd_month"] / p["credits_month"]

    def best_seconds(c, plan):
        """The longest base length: Veo 8s, Omni Flash 10s. Lower $/s for flat per-clip prices."""
        lengths = c["clip_seconds"]
        if isinstance(lengths, dict):
            return lengths["max"]
        return max(lengths)

    def label(c):
        bits = [c["variant"]]
        if c["resolution"] not in ("not stated", ""):
            bits.append(c["resolution"])
        name = " ".join(bits)
        if c.get("retiring_on"):
            name += f" (retiring {c['retiring_on']})"
        return name

    def usd_per_second(c, p, secs=None):
        secs = secs or best_seconds(c, p)
        cr = credits_for(c, p, secs)
        if cr is None:
            return None, None, secs
        return per_credit(p) * cr / secs, cr, secs

    pro = plans.get("gflow-pro")
    lite = next((c for c in costs if c["id"] == "flow-veo31-lite"), None)
    omni720 = next((c for c in costs if c["id"] == "flow-omni12-720p"), None)
    lowpri = next((c for c in costs if c["id"] == "flow-veo31-lite-lower-priority"), None)

    # ---------- API rows from prices.json ----------
    api_rows = sorted(
        [r for r in rows if r["model"] in MODELS and r.get("kind") == "api"],
        key=lambda r: (r["model"] != "veo-3-1", r["usd_per_second"], r["id"]),
    )

    def cheapest_api(model, resolution=None):
        """Same resolution when our data has one, otherwise the cheapest row for the model."""
        rs = [r for r in api_rows if r["model"] == model]
        same = [r for r in rs if resolution and r["resolution"] == resolution]
        rs = same or rs
        return min(rs, key=lambda r: (r["usd_per_second"], r["id"])) if rs else None

    api_veo = cheapest_api("veo-3-1")
    api_omni = cheapest_api("gemini-omni-flash")
    gemini_omni12 = next((r for r in api_rows if r["platform"] == "Google Gemini API" and r["variant"] == "gemini-omni-1.2-flash"), None)
    gemini_omni11 = next((r for r in api_rows if r["platform"] == "Google Gemini API" and r["variant"] == "gemini-omni-1.1-flash"), None)

    def api_clause(r):
        return (
            f"{rate_money(r['usd_per_second'])}/s for {r['variant']} on {r['platform']} "
            f"({r['resolution'] if r['resolution'] not in ('—', '') else 'resolution not listed'}, "
            f"{g['rate_label'](r)}, checked {r['checked']})"
        )

    # ---------- Key sentences, all from data ----------
    key_lines = []
    if pro and lite:
        rate, cr, secs = usd_per_second(lite, pro)
        clips = floor_int(pro["credits_month"] / cr)
        key_lines.append(
            f"On {pro['plan']} ({cost_money(pro['usd_month'])} a month, {num(pro['credits_month'])} Flow credits), "
            f"an {secs}-second Veo 3.1 Lite clip costs {num(cr)} credits. That is {num(clips)} clips a month, "
            f"or about {rate_money(rate)} per second of video."
        )
    if pro and omni720:
        rate, cr, secs = usd_per_second(omni720, pro)
        clips = floor_int(pro["credits_month"] / cr)
        key_lines.append(
            f"A {secs}-second Omni Flash 1.2 clip at 720p costs {num(cr)} credits on any plan, "
            f"so {pro['plan']} buys {num(clips)} of them, about {rate_money(rate)} per second."
        )
    intro = (
        "Google Flow charges credits per generated video, and the cost depends on the model, the resolution, "
        "the clip length, and whether you are on Google AI Ultra. Pick a plan and a model below to see credits per clip, "
        "clips per month, and the effective dollars per second. "
    )
    assumptions = (
        f"Assumptions: the $/s figure is the plan's monthly price divided by its monthly Flow credits, times the credits a clip uses, "
        f"divided by the clip length. It assumes you use every credit and puts the whole plan price on video, "
        f"although Google AI plans include other benefits. The {daily} free daily credits are left out unless you tick the box. "
        f"Prices are US prices from Google's plans page. Taxes and student or trial offers are not included."
    )

    # ---------- Retirement banner ----------
    ret = notices.get("retirement")
    banner = ""
    if ret:
        if TODAY < ret["date"]:
            head = f"Changing {ret['date']}."
            lead_in = "Google Flow Help says:"
        else:
            head = f"Retired {ret['date']}."
            lead_in = "Before that date, Google Flow Help said:"
        banner = (
            f'<div class="callout" role="note"><b>{e(head)}</b> {e(lead_in)} {quote("retirement")} '
            f'<span class="small">({help_link("source")}, checked {e(ret["checked"])})</span></div>'
        )
    api_route = ""
    if gemini_omni11 and "December 3, 2026" in (gemini_omni11.get("note") or ""):
        note = gemini_omni11["note"]
        start = note.find("Effective December 3, 2026")
        sentence = note[start:].strip() if start >= 0 else note
        api_route = (
            f'<p class="small">Separate from Flow, on the Gemini API: {e(sentence)} '
            f'(from our <a href="{root("/models/gemini-omni-flash/")}">Gemini Omni Flash price rows</a>, '
            f'{link(gemini_omni11["source_url"], "source")}, checked {e(gemini_omni11["checked"])}).</p>'
        )

    # ---------- Calculator ----------
    plan_opts = ['<option value="none">No plan (free daily credits only)</option>']
    for pid, p in plans.items():
        sel = " selected" if pid == "gflow-pro" else ""
        price = f"{cost_money(p['usd_year'])}/yr" if p.get("usd_year") else f"{cost_money(p['usd_month'])}/mo"
        plan_opts.append(f'<option value="{e(pid)}"{sel}>{e(p["plan"])}: {price}</option>')
    model_opts = []
    for c in calc_costs:
        sel = " selected" if lite is not None and c["id"] == lite["id"] else ""
        model_opts.append(f'<option value="{e(c["id"])}"{sel}>{e(label(c))}</option>')

    seed_rate, seed_cr, seed_secs = (None, None, 8)
    if pro and lite:
        seed_rate, seed_cr, seed_secs = usd_per_second(lite, pro)
    seed_clips = floor_int(pro["credits_month"] / seed_cr) if pro and seed_cr else 0
    seed_clip_cost = per_credit(pro) * seed_cr if pro and seed_cr else 0

    calc_payload = {
        "plans": {pid: {k: p.get(k) for k in ("plan", "usd_month", "usd_year", "credits_month", "tier", "billing")} for pid, p in plans.items()},
        "costs": calc_costs,
        "daily": daily,
        "days": DAYS,
        "default": {"plan": "gflow-pro", "cost": lite["id"] if lite else (calc_costs[0]["id"] if calc_costs else ""), "seconds": seed_secs},
    }
    payload = json.dumps(calc_payload, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")

    calc_html = f"""<div class="calc"><div class="card">
<div class="field"><label class="small" for="fPlan">Plan</label><select id="fPlan">{"".join(plan_opts)}</select></div>
<div class="field"><label class="small" for="fModel">Model and resolution</label><select id="fModel">{"".join(model_opts)}</select></div>
<div class="field"><label class="small" for="fSecs">Clip length</label><select id="fSecs"></select></div>
<div class="field"><label class="small" for="fPer">Videos per request</label><select id="fPer"><option value="1">1</option><option value="2">2</option></select></div>
<label class="chk" for="fDaily"><input type="checkbox" id="fDaily"> add {daily} daily credits × {DAYS} days</label>
<p class="small" id="fMsg" role="status"></p>
</div>
<div class="card">
<div class="small">Credits per video</div><div class="kpi" id="kCredits">{num(seed_cr) if seed_cr is not None else "—"}</div>
<div class="small" style="margin-top:8px">Videos per month</div><div class="kpi" id="kClips">{num(seed_clips)}</div>
<div class="small" style="margin-top:8px">Cost per video</div><div class="kpi" id="kClip">{cost_money(seed_clip_cost) if seed_cr else "—"}</div>
<div class="small" style="margin-top:8px">Cost per second</div><div class="kpi" id="kSec">{rate_money(seed_rate) if seed_rate is not None else "—"}</div>
<p class="small" id="kNote">{e(pro["plan"]) if pro else ""}: {cost_money(pro["usd_month"]) if pro else ""} a month for {num(pro["credits_month"]) if pro else ""} Flow credits. Estimated from Google's credit table, not a list price.</p>
</div></div>
<noscript><p class="small">Turn on JavaScript to change the plan, model, or length. The figures above are {e(pro["plan"]) if pro else ""} with an {seed_secs}-second Veo 3.1 Lite clip.</p></noscript>"""

    # ---------- Credit cost table (Google's table, current models) ----------
    cost_rows = []
    for c in costs:
        if c.get("credits_per_second"):
            ps = c["credits_per_second"]
            lengths = c["clip_seconds"]
            credit_txt = (
                f"{num(ps['up_to_10s'])} per second up to {lengths['max']}s; "
                f"{num(ps['extra_11_15s'])} per extra second from 11 to {lengths['subscriber_max']}s (paid plans)"
            )
            length_txt = f"{lengths['min']}–{lengths['max']}s ({lengths['subscriber_max']}s on paid plans)"
        else:
            t = c["credits_per_generation"]
            if "all" in t:
                credit_txt = f"{num(t['all'])}"
            elif "ultra_20x" in t:
                credit_txt = f"{num(t['ultra_20x'])} (Lower Priority mode)"
            elif "ultra" in t:
                credit_txt = f"{num(t['non_ultra'])}; Ultra: {num(t['ultra'])}"
            else:
                credit_txt = ", ".join(f"{k}s: {num(v)}" for k, v in t.items())
            length_txt = ", ".join(f"{s}s" for s in c["clip_seconds"])
        who = c.get("eligible") or ""
        status = f'<span class="tag estimate">retiring {e(c["retiring_on"])}</span>' if c.get("retiring_on") else ""
        cost_rows.append(
            "<tr>"
            f'<td><a href="{root(f"/models/{c["model"]}/")}">{e(c["variant"])}</a>{(" " + status) if status else ""}</td>'
            f"<td>{e(c['resolution'])}</td>"
            f"<td>{e(length_txt)}</td>"
            f"<td>{e(credit_txt)}</td>"
            f"<td>{e(who)}</td>"
            f'<td>{help_link("source")} · {e(c["checked"])}</td>'
            "</tr>"
        )
    cost_table = (
        '<div class="tblwrap fit"><table><thead><tr><th>Model</th><th>Res</th><th>Lengths</th>'
        "<th>Credits per video</th><th>Who</th><th>Source</th></tr></thead><tbody>"
        + "".join(cost_rows) + "</tbody></table></div>"
    )

    # ---------- Plan table ----------
    plan_rows = []
    for pid, p in plans.items():
        price = f"{cost_money(p['usd_year'])}/yr ({cost_money(p['usd_month'])}/mo)" if p.get("usd_year") else f"{cost_money(p['usd_month'])}/mo"
        plan_rows.append(
            "<tr>"
            f"<td>{e(p['plan'])}</td>"
            f'<td class="num">{price}</td>'
            f'<td class="num">{num(p["credits_month"])}</td>'
            f'<td class="num">{rate_money(per_credit(p))}</td>'
            f'<td>{plans_link("source")} · {e(p["checked"])}</td>'
            "</tr>"
        )
    plan_table = (
        '<div class="tblwrap fit"><table><thead><tr><th>Plan</th><th>Price</th><th>Flow credits / month</th>'
        "<th>$ / credit</th><th>Source</th></tr></thead><tbody>" + "".join(plan_rows) + "</tbody></table></div>"
    )

    # ---------- Flow vs API ----------
    plan_ids = list(plans.keys())
    vs_head = "<thead><tr><th>Flow model</th><th>Clip</th>" + "".join(f"<th>{e(plans[pid]['plan'])}</th>" for pid in plan_ids) + "<th>Cheapest API row</th></tr></thead>"
    vs_rows = []
    for c in calc_costs:
        cells = []
        secs = best_seconds(c, None)
        for pid in plan_ids:
            rate, cr, _ = usd_per_second(c, plans[pid], secs)
            cells.append(f'<td class="num">{rate_money(rate) if rate is not None else "—"}<div class="assume">{num(cr) if cr is not None else "—"} cr</div></td>')
        api = cheapest_api(c["model"], c["resolution"])
        api_cell = (
            f'{rate_money(api["usd_per_second"])}/s<div class="small">{e(api["platform"])} · {e(api["variant"])} · '
            f'{e(api["resolution"] if api["resolution"] not in ("—", "") else "res not listed")}</div>'
            if api else "not in our data"
        )
        vs_rows.append(f"<tr><td>{e(label(c))}</td><td class=\"num\">{secs}s</td>{''.join(cells)}<td>{api_cell}</td></tr>")
    vs_table = f'<div class="tblwrap fit"><table>{vs_head}<tbody>{"".join(vs_rows)}</tbody></table></div>'

    api_html_rows = []
    for r in api_rows:
        href, rel = outbound(r["source_url"])
        api_html_rows.append(
            f'<tr data-price-id="{e(r["id"])}">'
            f'<td><a href="{root(f"/models/{r["model"]}/")}">{e(models[r["model"]]["name"])}</a></td>'
            f"<td>{e(r['platform'])}</td>"
            f"<td>{e(r['variant'])}</td>"
            f"<td>{e(r['resolution'])}</td>"
            f'<td class="num">{rate_money(r["usd_per_second"])}</td>'
            f"<td>{tag(r)}</td>"
            f'<td><a href="{e(href)}" rel="{rel}" target="_blank">source</a> · {e(r["checked"])}</td>'
            "</tr>"
        )
    api_table = (
        '<div class="tblwrap fit"><table><thead><tr><th>Model</th><th>Where</th><th>Variant</th><th>Res</th>'
        "<th>$/s</th><th>Status</th><th>Source</th></tr></thead><tbody>" + "".join(api_html_rows) + "</tbody></table></div>"
    )

    compare_bits = []
    if pro and omni720 and gemini_omni12:
        rate, _cr, secs = usd_per_second(omni720, pro)
        compare_bits.append(
            f"Omni Flash 1.2 at 720p on {pro['plan']} works out to about {rate_money(rate)}/s for a {secs}-second clip, "
            f"next to {api_clause(gemini_omni12)}."
        )
    if pro and lite and api_veo:
        rate, _cr, secs = usd_per_second(lite, pro)
        compare_bits.append(
            f"Veo 3.1 Lite on {pro['plan']} is about {rate_money(rate)}/s for an {secs}-second clip. "
            f"The cheapest current Veo 3.1 API row we track is {api_clause(api_veo)}. "
            "That is a different Veo 3.1 mode, so treat it as a price reference, not a like-for-like match."
        )
    compare_text = " ".join(compare_bits)
    veo_gemini_note = ""
    if any(r for r in g["retired_rows"] if r["model"] == "veo-3-1" and r["platform"] == "Google Gemini API"):
        veo_gemini_note = (
            f' Our Gemini API Veo 3.1 rows are marked discontinued, so they are not in this table. '
            f'They stay on the <a href="{root("/models/veo-3-1/")}">Veo 3.1 page</a> under retired prices.'
        )

    # ---------- Gotchas (Google's words) ----------
    gotchas = []
    for nid, lead in (
        ("per_generation", "Credits are per video, not per prompt."),
        ("monthly_rollover", "Monthly credits do not roll over."),
        ("daily_refresh", f"The {daily} daily credits refresh from your first generation."),
        ("peak_hours", "No plan, no video at peak times."),
        ("extend", "Veo Extend is gone."),
        ("subject_to_change", "Costs can change."),
    ):
        if nid in notices:
            gotchas.append(f"<li><b>{e(lead)}</b> {quote(nid)}</li>")
    if lowpri:
        gotchas.append(
            f"<li><b>Veo 3.1 Lite can cost 0 credits on Ultra 20x.</b> Google's table lists "
            f"{num(lowpri['credits_per_generation']['ultra_20x'])} credits for 4s, 6s, or 8s Veo 3.1 Lite videos in Lower Priority mode, "
            f"for {e(lowpri['eligible'])}. The calculator does not price that mode, because a zero-credit video has no per-credit cost.</li>"
        )
    gotcha_html = (
        "<ul>" + "".join(gotchas) + "</ul>"
        f'<p class="small">Quotes from {help_link("Manage your Google Flow credits")} (Google Flow Help), checked {e(oldest if oldest == updated else updated)}. '
        "Peak hours of 2 PM to 5 PM UTC are 6 AM to 9 AM Pacific while the US is on standard time.</p>"
    )

    # ---------- FAQ (plain text; also FAQPage JSON-LD) ----------
    faqs = []
    if pro and lite:
        rate, cr, secs = usd_per_second(lite, pro)
        n_lite = floor_int(pro["credits_month"] / cr)
        a = (
            f"{pro['plan']} adds {num(pro['credits_month'])} Flow credits a month. Veo 3.1 Lite costs {num(cr)} credits per video "
            f"at 4, 6, or 8 seconds, so that is {num(n_lite)} Veo 3.1 Lite videos a month."
        )
        fast = next((c for c in costs if c["id"] == "flow-veo31-fast"), None)
        if fast:
            fcr = credits_for(fast, pro, 8)
            a += f" Veo 3.1 Fast costs {num(fcr)} credits, so {num(floor_int(pro['credits_month'] / fcr))} videos, until it retires on {fast['retiring_on']}."
        a += f" Everyone also gets {daily} credits a day, and a request that makes 2 videos uses credits for both."
        faqs.append((f"How many Veo 3.1 videos does {pro['plan'].split(' (')[0]} get in Flow?", a))
    faqs.append((
        "Do Google Flow credits roll over?",
        "No. Google says unused monthly Flow credits do not roll over to the next month, and unused daily credits do not roll over either. "
        "Monthly plan credits refresh at the start of your billing cycle.",
    ))
    faqs.append((
        "When do the daily Flow credits refresh?",
        f"Google says the {daily}-credit daily refresh is triggered by your first generation, so the next {daily} arrive the day after you first use them.",
    ))
    faqs.append((
        "Why did one prompt use double the credits?",
        "Google's credit costs are per generation, not per request. Google says a single Flow request may generate 2 videos, and each one is charged.",
    ))
    if compare_text:
        faqs.append(("Is Google Flow cheaper than the API?", compare_text + " The Flow figure assumes you use every credit and counts the whole plan price as video spend."))
    if ret:
        faqs.append((
            f"What changes in Flow on {ret['date']}?",
            f"Google says Veo 3.1 Fast, Veo 3.1 Quality, and Omni Flash 1.1 will be retired on {ret['date']}, and points users to Omni Flash 1.2 or Veo 3.1 Lite. "
            "The calculator drops those models after that date.",
        ))
    faqs.append((
        "Can I buy more Flow credits?",
        "Google says Plus, Pro, and Ultra plan members can buy AI credits in supported regions, except Japan. "
        "Google's help page does not list AI credit prices, so they are not in this calculator.",
    ))
    faqs.append((
        "How is this different from the VidFare credit calculator?",
        f"This page only covers Google Flow credits on Google AI plans. The credit calculator ({SITE_URL}/calculator/) covers Higgsfield, Krea, and Magnific plans, "
        f"and the project budget calculator ({SITE_URL}/guides/ai-video-project-budget/) prices a finished video from dollars per second.",
    ))
    how = (
        "Plan prices and monthly Flow credits come from Google's plans page. Credits per video come from Google Flow Help. "
        "Dollars per second is plan price ÷ monthly Flow credits × credits per video ÷ clip seconds. "
        "It assumes every credit is used and the whole plan price is spent on video, so it is an estimate, not a list price. "
        "API rates are the current API rows in VidFare's price data, each with its own source and checked date. "
        "The daily price check re-reads every Flow number on Google's pages."
    )
    faqs.append(("How do we calculate this?", how))

    faq_html = "".join(f"<h2>{e(q)}</h2><p>{e(a)}</p>" for q, a in faqs)
    faq_html = faq_html.replace(e(f"{SITE_URL}/calculator/"), f'<a href="{root("/calculator/")}">{e(SITE_URL + "/calculator/")}</a>', 1)
    faq_html = faq_html.replace(
        e(f"{SITE_URL}/guides/ai-video-project-budget/"),
        f'<a href="{root("/guides/ai-video-project-budget/")}">{e(SITE_URL + "/guides/ai-video-project-budget/")}</a>', 1,
    )

    key_html = "".join(f"<li>{e(x)}</li>" for x in key_lines)
    script = (
        "<script>\nconst FLOW=" + payload + ";\n" + FLOW_JS + "\n</script>"
    )
    body = f"""<p class="small"><a href="{root("/guides/")}">Guides</a> › Google Flow credits</p>
<h1>{e(PHRASE)}</h1>
<p class="lead">{e(intro)}{"".join(e(x) + " " for x in key_lines[:1])}</p>
<p class="small">Last updated {e(updated)}. Flow numbers checked {e(updated)} on {help_link()} and the {plans_link()}. API prices last checked {e(LAST)}.</p>
{banner}
<p class="small">{e(assumptions)}</p>
<h2>Flow credits calculator</h2>
{calc_html}
<p class="small">Using a Higgsfield, Krea, or Magnific plan instead? Use the <a href="{root("/calculator/")}">credit calculator</a>. Pricing a whole project from dollars per second? Use the <a href="{root("/guides/ai-video-project-budget/")}">project budget calculator</a>.</p>
<h2>Key numbers</h2>
<ul>{key_html}</ul>
<h2>Flow credits per video</h2>
<p>Google's own table, for the models Flow sells today. Costs are per generated video.</p>
{cost_table}
<h2>Google AI plans and Flow credits</h2>
<p>Every account gets {daily} Flow credits a day. Paid plans add monthly credits. {e("Google's help page names the Ultra plans Google AI Ultra $100 and Google AI Ultra $200.")}</p>
{plan_table}
<h2>Flow vs API: dollars per second</h2>
<p>Effective $/s for each Flow model on each plan, at the longest standard clip, next to the cheapest current API row for the same model in VidFare's data (same resolution when we have one). "cr" is credits per video.</p>
{vs_table}
<p>{e(compare_text)}{veo_gemini_note}</p>
{api_route}
<h3>Veo 3.1 and Gemini Omni Flash API rows</h3>
{api_table}
<h2>Gotchas Google states</h2>
{gotcha_html}
{faq_html}
{script}"""
    desc = "Flow credits per video for Veo 3.1 and Omni Flash on Google AI Plus, Pro and Ultra: clips per month and cost per second vs the API."
    desc = f"{desc} Checked {updated}."
    guide_page(PATH, page_title(PHRASE), desc, body, faqs)


FLOW_JS = r"""
(function(){
const $=id=>document.getElementById(id);
function rateMoney(v){const n=Number(v),neg=n<0,abs=Math.abs(n),places=abs>=0.1?3:4,q=Math.pow(10,places),rounded=Math.round(abs*q),whole=Math.floor(rounded/q);let frac=String(rounded%q).padStart(places,'0').replace(/0+$/,'');if(frac.length<2)frac=frac.padEnd(2,'0');return (neg?'-$':'$')+whole+'.'+frac;}
function costMoney(v){const neg=Number(v)<0,n=Math.round(Math.abs(Number(v))*100),whole=Math.floor(n/100),frac=String(n%100).padStart(2,'0');return (neg?'-$':'$')+whole+'.'+frac;}
function num(n){return Number(n).toLocaleString('en-US',{maximumFractionDigits:2});}
const costs={};FLOW.costs.forEach(c=>{costs[c.id]=c;});
function lengths(c,plan){
  if(c.credits_per_second){const L=c.clip_seconds,max=plan?L.subscriber_max:L.max,out=[];for(let s=L.min;s<=max;s++)out.push(s);return out;}
  return c.clip_seconds.slice();
}
function credits(c,plan,s){
  if(c.credits_per_second){const L=c.clip_seconds,max=plan?L.subscriber_max:L.max;if(s<L.min||s>max)return null;
    return Math.min(s,10)*c.credits_per_second.up_to_10s+Math.max(0,s-10)*c.credits_per_second.extra_11_15s;}
  if(c.clip_seconds.indexOf(s)<0)return null;
  const t=c.credits_per_generation;
  if('all' in t)return t.all;
  if(String(s) in t)return t[String(s)];
  const key=plan&&plan.tier==='ultra'?'ultra':'non_ultra';
  return key in t?t[key]:null;
}
function fillLengths(keep){
  const c=costs[$('fModel').value],plan=FLOW.plans[$('fPlan').value]||null;
  const list=lengths(c,plan),prev=Number($('fSecs').value);
  $('fSecs').innerHTML=list.map(s=>'<option value="'+s+'">'+s+' seconds</option>').join('');
  let want=keep&&list.indexOf(prev)>=0?prev:(list.indexOf(FLOW.default.seconds)>=0&&!c.credits_per_second?FLOW.default.seconds:list[list.length-1]);
  if(c.credits_per_second&&!(keep&&list.indexOf(prev)>=0))want=Math.min(10,list[list.length-1]);
  $('fSecs').value=String(want);
}
function render(){
  const pid=$('fPlan').value,plan=FLOW.plans[pid]||null,c=costs[$('fModel').value];
  const s=Number($('fSecs').value),per=Number($('fPer').value),daily=$('fDaily').checked;
  const cr=credits(c,plan,s);
  const msg=[];
  if(cr==null){$('kCredits').textContent='\u2014';$('kClips').textContent='\u2014';$('kClip').textContent='\u2014';$('kSec').textContent='\u2014';$('fMsg').textContent='That length is not offered for this model on this plan.';return;}
  const pool=(plan?plan.credits_month:0)+((daily||!plan)?FLOW.daily*FLOW.days:0);
  $('kCredits').textContent=num(cr)+(per>1?' ('+num(cr*per)+' per request)':'');
  if(cr===0){$('kClips').textContent='not limited by credits';}
  else{const vids=Math.floor(pool/cr);$('kClips').textContent=num(vids)+(per>1?' ('+num(Math.floor(pool/(cr*per)))+' requests)':'');}
  if(!plan){
    $('kClip').textContent='$0.00';$('kSec').textContent='$0.00';
    $('kNote').textContent='No plan: '+FLOW.daily+' credits a day, counted here as '+FLOW.daily+' \u00d7 '+FLOW.days+' days if you generate every day. Google says non-plan users may not be able to generate videos at peak hours. Lengths over 10s need a paid plan.';
  }else{
    const usd=plan.usd_month,perCredit=usd/pool,clip=perCredit*cr,sec=clip/s;
    $('kClip').textContent=costMoney(clip);
    $('kSec').textContent=rateMoney(sec)+(per>1?' ('+rateMoney(sec*per)+' if you keep 1 of '+per+')':'');
    const price=plan.usd_year?costMoney(plan.usd_year)+' a year ('+costMoney(usd)+' a month)':costMoney(usd)+' a month';
    $('kNote').textContent=plan.plan+': '+price+' for '+num(plan.credits_month)+' Flow credits'+(daily?' plus '+num(FLOW.daily*FLOW.days)+' daily credits':'')+'. Estimated from Google\u2019s credit table, not a list price.';
  }
  if(c.retiring_on)msg.push(c.variant+' retires on '+c.retiring_on+' in Flow.');
  if(c.credits_per_second&&s>10)msg.push('Seconds 11 to 15 cost '+c.credits_per_second.extra_11_15s+' credits each.');
  $('fMsg').textContent=msg.join(' ');
}
$('fPlan').addEventListener('input',()=>{fillLengths(true);render();});
$('fModel').addEventListener('input',()=>{fillLengths(false);render();});
['fSecs','fPer','fDaily'].forEach(id=>$(id).addEventListener('input',render));
fillLengths(false);
render();
})();
"""

QUESTION = "How many Google Flow credits does a Veo 3.1 or Omni Flash video cost?"


def blurb(g):
    """One plain sentence for the /guides/ index, from the same Flow records."""
    flow = g["db"].get("flow") or {}
    plans = flow.get("plans") or {}
    pro = plans.get("gflow-pro")
    lite = next((c for c in flow.get("credit_costs") or [] if c["id"] == "flow-veo31-lite"), None)
    if not pro or not lite:
        return "Credits per video, videos per month, and cost per second for Google Flow plans."
    cr = credits_for(lite, pro, max(lite["clip_seconds"]))
    rate = pro["usd_month"] / pro["credits_month"] * cr / max(lite["clip_seconds"])
    return (
        f"On {pro['plan']}, an {max(lite['clip_seconds'])}-second Veo 3.1 Lite video costs {cr:g} Flow credits, "
        f"about {g['rate_money'](rate)} per second if you use every credit."
    )
