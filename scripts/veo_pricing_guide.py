"""Guide: Veo 3.1 pricing.

Imported by scripts/build_site.py. Catalog $/s figures, rankings, and table
order are rendered from a price-sorted query of data/prices.json. Higgsfield
Black Friday end wording comes from data/deals.json and is omitted when the
deal is not live. Google Flow plan prices and credit costs come from the
prices.json "flow" section. Google Cloud "/ 1 count" list lines are vendor
list prices, not catalog rows, and are not ranked.
"""
import deal_copy
from timefmt import day_label, utc_span

PATH = "/guides/veo-3-1-pricing/"
LABEL = "Veo 3.1 pricing"
PHRASE = "Veo 3.1 pricing"
H1 = "Veo 3.1 pricing: what it costs per second, and where"
MODEL = "veo-3-1"
GOOGLE_CHECKED = "2026-11-24"
GOOGLE_WHEN = "Nov 24, 2026, 8:19–8:21 PM ET (5:19–5:21 PM PT)"
DEPRECATIONS = "https://ai.google.dev/gemini-api/docs/deprecations"
GEMINI_PRICING = "https://ai.google.dev/gemini-api/docs/pricing"
VEO_MODELS = "https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/veo/3-1-generate"
GCP_PRICING = "https://cloud.google.com/vertex-ai/generative-ai/pricing"
FLOW_HELP = "https://support.google.com/flow/answer/16526234?hl=en"
AI_PLANS = "https://one.google.com/about/google-ai-plans/"

# Official Google Cloud list lines, printed "/ 1 count". Not catalog $/s rows.
GCP_LIST = (
    ("Veo 3.1", "Video + Audio", "720p, 1080p", "$0.40 / 1 count"),
    ("Veo 3.1", "Video + Audio", "4K", "$0.60 / 1 count"),
    ("Veo 3.1", "Video", "720p, 1080p", "$0.20 / 1 count"),
    ("Veo 3.1", "Video", "4K", "$0.40 / 1 count"),
    ("Veo 3.1 Fast", "Video + Audio", "720p", "$0.10 / 1 count"),
    ("Veo 3.1 Fast", "Video + Audio", "1080p", "$0.12 / 1 count"),
    ("Veo 3.1 Fast", "Video + Audio", "4K", "$0.30 / 1 count"),
    ("Veo 3.1 Fast", "Video", "720p", "$0.08 / 1 count"),
    ("Veo 3.1 Fast", "Video", "1080p", "$0.10 / 1 count"),
    ("Veo 3.1 Fast", "Video", "4K", "$0.25 / 1 count"),
    ("Veo 3.1 Lite", "Video + Audio", "720p", "$0.05 / 1 count"),
    ("Veo 3.1 Lite", "Video + Audio", "1080p", "$0.08 / 1 count"),
    ("Veo 3.1 Lite", "Video", "720p", "$0.03 / 1 count"),
    ("Veo 3.1 Lite", "Video", "1080p", "$0.05 / 1 count"),
)


def _src(g, url, text="source"):
    e = g["e"]
    href, rel = g["outbound"](url)
    return f'<a href="{e(href)}" rel="{rel}" target="_blank">{e(text)}</a>'


def veo_rows(g):
    rows = [
        r
        for r in g["rows"]
        if r.get("model") == MODEL
        and r.get("usd_per_second") is not None
        and r.get("status") != "discontinued"
    ]
    return sorted(rows, key=lambda r: (float(r["usd_per_second"]), r["id"]))


def _is_fast(r):
    return "fast" in (r.get("variant") or "").lower()


def first_api(rows):
    return next(r for r in rows if r.get("kind") == "api")


def first_audio(rows):
    return next(r for r in rows if r.get("audio") is True)


def first_full(rows):
    return next(r for r in rows if not _is_fast(r))


def first_full_api(rows):
    return next(r for r in rows if r.get("kind") == "api" and not _is_fast(r))


def first_4k(rows):
    return next(r for r in rows if "4k" in str(r.get("resolution") or "").lower())


def _audio_word(g, r):
    a = g["shown_audio"](r)
    return {"with": "with audio", "without": "without audio"}.get(a, "not stated")


def _plan_dollars(v):
    return "unknown" if v is None else f"${v:g}"


def _clip(g, r, seconds):
    return g["money"](float(r["usd_per_second"]) * seconds)


def _deal_for_plan(plan):
    if plan in ("hf-ultra-annual", "hf-plus-annual"):
        return plan
    return None


def _sale_note(g, r):
    """Black Friday end wording from deals.json, only while that plan deal is live."""
    deal_id = _deal_for_plan(r.get("plan"))
    if not deal_id or not deal_copy.is_live(g, deal_id):
        return ""
    end = deal_copy.end_label(deal_copy.deal(g, deal_id))
    if not end:
        return ""
    return f" Black Friday plan price; ends {end}."


def _sale_end(g):
    """Shared end clock for Ultra/Plus annual, if either deal is live."""
    for deal_id in ("hf-ultra-annual", "hf-plus-annual"):
        if deal_copy.is_live(g, deal_id):
            return deal_copy.end_label(deal_copy.deal(g, deal_id))
    return None


def _how(g, r):
    label = g["rate_label"](r)
    math = (r.get("math") or "").strip()
    note = (r.get("note") or "").strip()
    bits = []
    if r.get("kind") == "plan":
        lead = "Estimated from credit plan." if r.get("status") == "estimate" else "From credit plan."
        bits.append(lead)
        if math:
            bits.append(math)
        bits.append("Assumes every credit you pay for is used.")
        bits.append(_sale_note(g, r).strip())
    else:
        bits.append("Published rate" + ("" if math else ", billed per second of output") + ".")
        if math:
            extra = math
            if note:
                extra = extra + "; " + note.rstrip(".") + "."
            else:
                extra = extra if extra.endswith(".") else extra + "."
            bits.append(extra)
    return " ".join(b for b in bits if b)


def _notice_date(flow, notice_id):
    for n in flow.get("notices") or []:
        if n.get("id") == notice_id:
            return n.get("retiring_on") or n.get("date")
    return None


def _long_day(date):
    import datetime as dt
    d = dt.date.fromisoformat(str(date)[:10])
    return d.strftime("%B ") + str(d.day) + d.strftime(", %Y")


def _lite_credits(flow):
    for c in flow.get("credit_costs") or []:
        if c.get("id") == "flow-veo31-lite":
            return c.get("credits_per_generation") or {}
    return {}


def _flow_about_rate(g, usd_month, credits_month, credits_per_video, seconds=8):
    raw = float(usd_month) / float(credits_month) * float(credits_per_video) / float(seconds)
    return g["rate_money"](raw)


def blurb(g):
    rows = veo_rows(g)
    rate = g["money"](rows[0]["usd_per_second"]) if rows else ""
    return (
        f"Every current Veo 3.1 price per second, cheapest first ({rate}/s as of this build), "
        "plus why Google no longer sells Veo 3.1 pay as you go and what Veo 3.1 Lite costs in Google Flow."
    )


def description(g):
    rows = veo_rows(g)
    cheapest = rows[0]
    api = first_api(rows)
    money = g["money"]
    last = day_label(cheapest.get("checked") or g["LAST"])
    text = (
        f"Cheapest Veo 3.1 is {money(cheapest['usd_per_second'])}/s "
        f"({cheapest.get('variant')}, {g['shown_resolution'](cheapest)}, "
        f"Higgsfield credit-plan estimate). "
        f"Pay as you go from {money(api['usd_per_second'])}/s on {api['platform']}. "
        f"Checked {last}."
    )
    # Keep the published shape if the current cheapest is still Higgsfield Fast 720p.
    if cheapest.get("platform") == "Higgsfield" and cheapest.get("variant") == "Veo 3.1 Fast":
        text = (
            f"Cheapest Veo 3.1 is {money(cheapest['usd_per_second'])}/s "
            f"(Veo 3.1 Fast, 720p, Higgsfield credit-plan estimate). "
            f"Pay as you go from {money(api['usd_per_second'])}/s on Runway API. "
            f"Checked {last}."
        )
    if len(text) > 160:
        raise SystemExit(f"{PATH} meta description is {len(text)} characters: {text}")
    return text


def render(g):
    e, root, LAST = g["e"], g["root"], g["LAST"]
    money = g["money"]
    rows = veo_rows(g)
    if len(rows) < 3:
        raise SystemExit(f"{PATH} expected current Veo 3.1 catalog rows, got {len(rows)}")
    cheapest, nxt, nxt2 = rows[0], rows[1], rows[2]
    api = first_api(rows)
    audio_row = first_audio(rows)
    full = first_full(rows)
    full_api = first_full_api(rows)
    # The next full API row, if tied.
    full_api_tie = next(
        (
            r
            for r in rows
            if r is not full_api
            and r.get("kind") == "api"
            and not _is_fast(r)
            and float(r["usd_per_second"]) == float(full_api["usd_per_second"])
        ),
        None,
    )
    fourk = first_4k(rows)
    sale_end = _sale_end(g)
    ultra_month = deal_copy.plan_month(g, "hf-ultra-annual")
    bf_live_ultra = deal_copy.is_live(g, "hf-ultra-annual") and cheapest.get("plan") == "hf-ultra-annual"

    flow = (g.get("db") or {}).get("flow") or {}
    lite = _lite_credits(flow)
    lite_non = lite.get("non_ultra")
    lite_ultra = lite.get("ultra")
    daily = (flow.get("daily") or {}).get("credits_day")
    daily_lite = (int(daily) // int(lite_non)) if daily and lite_non else None
    retire_on = _notice_date(flow, "retirement")
    extend_on = _notice_date(flow, "extend")
    retired = bool(retire_on and str(g["TODAY"]) >= str(retire_on))
    peak = utc_span(14, 17)
    disc = [
        r
        for r in (g.get("db") or {}).get("rows", [])
        if r.get("model") == MODEL and r.get("status") == "discontinued"
    ]
    gemini_checked = max((r.get("checked") for r in disc if r.get("checked")), default=None)

    def src_cell(r):
        return (
            f"Checked {e(day_label(r.get('checked')))}. "
            f"{_src(g, r.get('source_url') or '', 'source')}."
        )

    body_rows = []
    for r in rows:
        body_rows.append(
            "<tr>"
            f"<td>Veo 3.1</td>"
            f"<td>{g['plat_link'](r['platform'], r.get('source_url') or '')}</td>"
            f"<td>{e(r.get('variant') or 'Veo 3.1')}</td>"
            f"<td>{e(g['shown_tier'](r))}</td>"
            f"<td>{e(g['shown_resolution'](r))}</td>"
            f"<td>{e(_audio_word(g, r))}</td>"
            f"<td>{e(money(r['usd_per_second']))}</td>"
            f"<td>{e(g['rate_label'](r))}</td>"
            f"<td>{e(_how(g, r))}</td>"
            f"<td>{src_cell(r)}</td>"
            "</tr>"
        )
    price_table = (
        '<div class="tblwrap" id="prices">\n<table>\n<thead>\n<tr>\n'
        "  <th>Model</th><th>Where</th><th>Variant / plan</th><th>Plan tier</th>\n"
        "  <th>Resolution</th><th>Audio</th><th>$ / sec</th><th>Status</th>\n"
        "  <th>How we got it</th><th>Source</th>\n"
        "</tr>\n</thead>\n<tbody>\n"
        + "\n".join(body_rows)
        + "\n</tbody>\n</table>\n</div>"
    )

    gcp_src = (
        f"Checked {e(day_label(GOOGLE_CHECKED))}. "
        f"{_src(g, GCP_PRICING, 'source')}."
    )
    gcp_body = []
    first = True
    for model, output, res, price in GCP_LIST:
        src = f'<td rowspan="{len(GCP_LIST)}">{gcp_src}</td>' if first else ""
        first = False
        gcp_body.append(
            f"<tr><td>{e(model)}</td><td>{e(output)}</td><td>{e(res)}</td><td>{e(price)}</td>{src}</tr>"
        )
    gcp_table = (
        '<div class="tblwrap" id="google-cloud-list">\n<table>\n<thead>\n'
        "<tr><th>Google Cloud model</th><th>Output</th><th>Resolution</th>"
        "<th>Price as printed</th><th>Source</th></tr>\n"
        "</thead>\n<tbody>\n"
        + "\n".join(gcp_body)
        + "\n</tbody>\n</table>\n</div>"
    )

    flow_plans = flow.get("plans") or {}
    plan_order = (
        "gflow-plus",
        "gflow-pro",
        "gflow-pro-annual",
        "gflow-ultra-5x",
        "gflow-ultra-20x",
    )
    flow_help_src = _src(g, FLOW_HELP, "Flow help")
    flow_body = []
    for pid in plan_order:
        p = flow_plans.get(pid) or {}
        if not p:
            continue
        credits = p.get("credits_month")
        tier = p.get("tier")
        per = lite_ultra if tier == "ultra" else lite_non
        videos = (int(credits) // int(per)) if credits and per else None
        if p.get("billing", "").startswith("annual") and p.get("usd_year") is not None:
            price_cell = f"{_plan_dollars(p['usd_year'])}/year"
            usd_for_rate = p.get("usd_month")
        else:
            price_cell = f"{_plan_dollars(p.get('usd_month'))}/month"
            usd_for_rate = p.get("usd_month")
        about = _flow_about_rate(g, usd_for_rate, credits, per) if usd_for_rate and credits and per else "—"
        name = p.get("plan") or pid
        help_name = p.get("help_name")
        if help_name:
            name = f"{name} (Flow’s “{help_name.replace('Google AI ', '')}”)"
        src = (
            f"Plan price: catalog, checked {e(day_label(p.get('checked') or GOOGLE_CHECKED))}. "
            f"Credits: {flow_help_src}, checked {e(day_label((flow.get('daily') or {}).get('checked') or GOOGLE_CHECKED))}."
        )
        flow_body.append(
            "<tr>"
            f"<td>{e(name)}</td>"
            f"<td>{e(price_cell)}</td>"
            f"<td>{e(f'{credits:,}' if isinstance(credits, int) else str(credits))}</td>"
            f"<td>{e(str(per) if per is not None else '—')}</td>"
            f"<td>{e(f'{videos:,}' if isinstance(videos, int) else '—')}</td>"
            f"<td>{e(about)}</td>"
            f"<td>{src}</td>"
            "</tr>"
        )
    flow_table = (
        '<div class="tblwrap" id="flow-plans">\n<table>\n<thead>\n'
        "<tr><th>Google AI plan</th><th>Price</th><th>Flow credits a month</th>"
        "<th>Veo 3.1 Lite credits per video</th><th>Lite videos a month</th>"
        "<th>About $/s for an 8s video, if every credit is used</th><th>Source</th></tr>\n"
        "</thead>\n<tbody>\n"
        + "\n".join(flow_body)
        + "\n</tbody>\n</table>\n</div>"
    )

    cheap_s = money(cheapest["usd_per_second"])
    api_s = money(api["usd_per_second"])
    audio_s = money(audio_row["usd_per_second"])
    full_s = money(full["usd_per_second"])
    full_api_s = money(full_api["usd_per_second"])
    fourk_s = money(fourk["usd_per_second"])
    nxt_s = money(nxt["usd_per_second"])
    clip4 = money(cheapest["usd_per_clip"]) if cheapest.get("usd_per_clip") is not None else _clip(g, cheapest, cheapest.get("clip_seconds") or 4)
    sale_lead = ""
    sale_take = ""
    sale_section = ""
    sale_foot = ""
    if bf_live_ultra and sale_end:
        sale_lead = (
            f" That rate uses a Higgsfield Black Friday plan price that ends {sale_end}."
        )
        sale_take = (
            f" It uses a Black Friday plan price that ends {sale_end}."
        )
        if ultra_month is not None:
            sale_section = (
                f" It also uses Higgsfield’s Black Friday price of {_plan_dollars(ultra_month)} a month billed yearly, "
                f"which Higgsfield says ends {sale_end}."
            )
        sale_foot = (
            f" Higgsfield’s annual-plan rows use Black Friday plan prices that end {sale_end}."
        )

    last = day_label(LAST)
    lead = (
        f"As of {e(day_label(cheapest.get('checked') or LAST))}, the cheapest Veo 3.1 rate we track is "
        f"{cheap_s} per second for {e(cheapest.get('variant') or 'Veo 3.1')} at {e(g['shown_resolution'](cheapest))} "
        f"on {e(cheapest['platform'])}’s {e(g['shown_tier'](cheapest))} plan, {_audio_word(g, cheapest)}, "
        f"{e(g['rate_label'](cheapest))} and priced on a {e(str(cheapest.get('clip_seconds') or 4))}-second clip "
        f"({clip4} a clip), assuming every credit you pay for is used.{sale_lead} "
        f"The cheapest pay-as-you-go rate is {api_s} per second for {e(api.get('variant') or 'Veo 3.1')} "
        f"{_audio_word(g, api)} on the {e(api['platform'])}, a published rate "
        f"({_clip(g, api, 8)} for an 8-second clip). "
        f"Google no longer sells Veo 3.1 pay as you go: its Gemini API preview models were shut down Oct 22, 2026, "
        f"and Google Cloud lists its current Veo 3.1 models as Provisioned Throughput or fixed quota only. "
        f"In Google Flow, every account gets {daily} free credits a day, enough for "
        f"{daily_lite} 720p Veo 3.1 Lite videos."
    )

    takeaways = (
        '<div class="card" id="takeaways">\n'
        "<h2>Key takeaways</h2>\n<ul>\n"
        f"<li><b>Cheapest if you use every credit.</b> {e(cheap_s)}/s for {e(cheapest.get('variant'))} on "
        f"{e(cheapest['platform'])}, {e(g['shown_tier'](cheapest))}, {e(g['shown_resolution'](cheapest))}, "
        f"{_audio_word(g, cheapest)}, {e(g['rate_label'](cheapest))}, checked {e(day_label(cheapest.get('checked')))}."
        f"{sale_take}</li>\n"
        f"<li><b>Cheapest pay as you go.</b> {e(api_s)}/s for {e(api.get('variant') or 'Veo 3.1 Fast')} "
        f"{_audio_word(g, api)} on the {e(api['platform'])}, or {e(audio_s)}/s with audio, published rates checked "
        f"{e(day_label(api.get('checked')))}.</li>\n"
        f"<li><b>Full Veo 3.1, not Fast.</b> From {e(full_s)}/s on {e(full['platform'])}, {e(g['shown_tier'](full))}, "
        f"{e(g['shown_resolution'](full))}, {e(g['rate_label'](full))}. By API, from {e(full_api_s)}/s without audio "
        f"on {e(full_api['platform'])}"
        + (f" or the {e(full_api_tie['platform'])}" if full_api_tie else "")
        + f", checked {e(day_label(full_api.get('checked')))}.</li>\n"
        f"<li><b>Google direct.</b> No pay-as-you-go Veo 3.1 is listed. The Gemini API preview models were shut down "
        f"Oct 22, 2026, and Google Cloud’s Veo 3.1 models are Provisioned Throughput or fixed quota only, "
        f"checked {e(day_label(GOOGLE_CHECKED))}.</li>\n"
        f"<li><b>Free in Google Flow.</b> {daily} free credits a day buy {daily_lite} 720p Veo 3.1 Lite videos "
        f"at {lite_non} credits each."
        + (
            f" Flow {'retired' if retired else 'retires'} Veo 3.1 Fast and Quality on {e(_long_day(retire_on))}."
            if retire_on
            else ""
        )
        + "</li>\n"
        "</ul>\n</div>"
    )

    # Next-in-sort prose: if rows[1] and rows[2] tie, say so.
    if float(nxt["usd_per_second"]) == float(nxt2["usd_per_second"]):
        next_sentence = (
            f"Next in the sort is a tie at {nxt_s} per second: "
            f"{e(nxt.get('variant') or 'Veo 3.1')} {_audio_word(g, nxt)} on the {e(nxt['platform'])}, "
            f"a published rate with resolution {e(g['shown_resolution'](nxt))}, and "
            f"{e(nxt2.get('variant') or 'Veo 3.1')} on {e(nxt2['platform'])} {e(g['shown_tier'](nxt2))} at "
            f"{e(g['shown_resolution'](nxt2))}, {e(g['rate_label'](nxt2))}."
        )
    else:
        next_sentence = (
            f"Next in the sort is {nxt_s} per second for {e(nxt.get('variant') or 'Veo 3.1')} on "
            f"{e(nxt['platform'])}, {e(g['shown_tier'](nxt))}."
        )

    a_cheap = (
        f"Sorting every current Veo 3.1 row in our catalog by price per second on {day_label(cheapest.get('checked') or LAST)}, "
        f"the cheapest is {cheap_s} per second for {cheapest.get('variant') or 'Veo 3.1'} on {cheapest['platform']}, "
        f"plan tier {g['shown_tier'](cheapest)}, {g['shown_resolution'](cheapest)}, {_audio_word(g, cheapest)}, "
        f"{g['rate_label'](cheapest)}. {cheapest['platform']} prices it per {cheapest.get('clip_seconds') or 4}-second clip, "
        f"{clip4} a clip, and the rate assumes every credit you pay for is used.{sale_section} "
        f"{next_sentence} At {nxt_s} per second, a 5-second clip is {_clip(g, nxt, 5)} and an 8-second clip is {_clip(g, nxt, 8)}."
    )

    # Full Veo 3.1 with audio on APIs: first full API with audio, plus any same-price tie.
    full_audio_api = next(
        (r for r in rows if r.get("kind") == "api" and not _is_fast(r) and r.get("audio") is True),
        None,
    )
    fa_s = money(full_audio_api["usd_per_second"]) if full_audio_api else None
    a_audio = (
        f"Among rows whose seller states that the clip includes audio, the cheapest on {day_label(audio_row.get('checked') or LAST)} is "
        f"{audio_s} per second for {audio_row.get('variant') or 'Veo 3.1'} with audio on the {audio_row['platform']}, "
        f"a published rate with resolution {g['shown_resolution'](audio_row)}: "
        f"{_clip(g, audio_row, 5)} for a 5-second clip or {_clip(g, audio_row, 8)} for an 8-second clip. "
        + (
            f"On pay-as-you-go APIs, full Veo 3.1 with audio is {fa_s} per second on {full_audio_api['platform']} at "
            f"{g['shown_resolution'](full_audio_api)} and on the Runway API, so an 8-second clip is "
            f"{_clip(g, full_audio_api, 8)}. "
            if full_audio_api
            else ""
        )
        + f"At 4K, the cheapest row is {fourk_s} per second for {fourk.get('variant') or 'Veo 3.1'} on {fourk['platform']}, "
        f"plan tier {g['shown_tier'](fourk)}, {g['rate_label'](fourk)}, checked {day_label(fourk.get('checked'))}, "
        f"assuming every credit you pay for is used. Higgsfield’s Veo 3.1 rows do not state audio, so they are left out of this comparison."
    )

    a_google = (
        f"Not pay as you go. Google’s Gemini API deprecations page, read {day_label(GOOGLE_CHECKED)}, lists "
        f"veo-3.1-generate-preview, veo-3.1-fast-generate-preview, and veo-3.1-lite-generate-preview as shut down on "
        f"October 22, 2026, with gemini-omni-1.2-flash as the replacement, and the Gemini API pricing page no longer lists Veo. "
        f"On Google Cloud’s Gemini Enterprise Agent Platform, the model cards for Veo 3.1, Veo 3.1 Fast, and Veo 3.1 Lite list "
        f"pay-as-you-go as not supported; they are offered through Provisioned Throughput or fixed quota, in the us-central1 region. "
        f"Our last Gemini API Veo 3.1 rows, last checked {day_label(gemini_checked) if gemini_checked else 'an earlier date'}, "
        f"are kept as discontinued and are not used in any ranking on this page."
    )

    plus = flow_plans.get("gflow-plus") or {}
    pro = flow_plans.get("gflow-pro") or {}
    ultra5 = flow_plans.get("gflow-ultra-5x") or {}
    ultra20 = flow_plans.get("gflow-ultra-20x") or {}
    a_flow = (
        f"Google’s Flow help page, read {day_label(GOOGLE_CHECKED)}, says every account gets {daily} Google Flow credits a day "
        f"with or without a paid plan, and unused daily credits do not roll over. Veo 3.1 Lite makes 4-, 6-, or 8-second videos "
        f"at 720p for {lite_non} credits each, or {lite_ultra} credits on Google AI Ultra plans, so the free daily credits cover "
        f"{daily_lite} Lite videos. Google AI Plus adds {plus.get('credits_month'):,} credits a month, "
        f"Pro {pro.get('credits_month'):,}, "
        f"Ultra $100 {ultra5.get('credits_month'):,}, and "
        f"Ultra $200 {ultra20.get('credits_month'):,}. "
        f"Google says accounts without a paid plan may not be able to generate videos during peak hours, roughly {peak}. "
        f"Credit costs are per generation, not per request, and one request can make two videos."
    )

    retire_clause = (
        f"Google’s Flow help page, read {day_label(GOOGLE_CHECKED)}, says Veo 3.1 Fast and Veo 3.1 Quality "
        + (
            f"were retired on {_long_day(retire_on)}"
            if retired
            else f"will be retired on {_long_day(retire_on)}"
        )
        + ", and points users to Omni Flash 1.2 or Veo 3.1 Lite."
        if retire_on
        else f"Google’s Flow help page, read {day_label(GOOGLE_CHECKED)}, describes the Flow models currently listed there."
    )
    extend_clause = (
        f" It also says Veo Extend was retired on {_long_day(extend_on)}."
        if extend_on
        else ""
    )
    a_retire = (
        f"In Google Flow, yes. {retire_clause}{extend_clause} "
        f"On Google Cloud, the Veo 3.1 and Veo 3.1 Fast model cards list a retirement date of May 4, 2027 or later, "
        f"and Veo 3.1 Lite is listed as Preview. The third-party rows above come from each seller’s own pricing page, "
        f"and none of those rows has a retirement date, so each stays in the table until its seller’s page changes."
    )

    a_how = (
        "Each dollar figure is a current price row, with the vendor page and the date that page was checked. "
        "A published rate is a dollars-per-second figure on that page, or an API credit count times the credit price the page states. "
        "A credit-plan figure is plan price ÷ credits × credits per clip ÷ seconds, and it assumes every credit you pay for is used. "
        'When the vendor marks that count with "~", "roughly", or "estimated", the row is labelled estimated from credit plan and is not a list price. '
        "A promo shows its end date when the vendor gave one. "
        "The full method is on the about page."
    )

    faqs = [
        ("What is the cheapest Veo 3.1 price per second?", a_cheap),
        ("What does Veo 3.1 with audio cost?", a_audio),
        ("Can you pay Google directly for Veo 3.1?", a_google),
        ("How much does Veo 3.1 cost in Google Flow?", a_flow),
        ("Is Veo 3.1 Fast being retired?", a_retire),
        ("How do we calculate this?", a_how),
    ]
    for _name, _text in faqs:
        low = _text.lower()
        if "subscribe" in low or "newsletter" in low:
            raise SystemExit(f"{PATH} FAQ text contains newsletter wording")

    dep = _src(g, DEPRECATIONS, "Google’s Gemini API deprecations page")
    gem = _src(g, GEMINI_PRICING, "Gemini API pricing page")
    models_src = _src(g, VEO_MODELS, "Google Cloud’s Veo 3.1 model page")
    gcp = _src(g, GCP_PRICING, "Google Cloud’s pricing page")
    flow_src = _src(g, FLOW_HELP, "Google’s Flow credits help page")
    confirmed = (
        "<h2>What is confirmed, and what is not?</h2>\n<ul>\n"
        f"  <li>Catalog rows: every row in the price table, each checked against its seller’s own pricing page on the date in its Source cell "
        f"({e(day_label(cheapest.get('checked')))}, or {e(day_label(fourk.get('checked')))} for Magnific).</li>\n"
        f"  <li>Confirmed {e(day_label(GOOGLE_CHECKED))} on {dep}: the three Veo 3.1 preview models shut down on October 22, 2026. "
        f"The {gem} had no Veo section the same evening.</li>\n"
        f"  <li>Confirmed {e(day_label(GOOGLE_CHECKED))} on {models_src} (last updated 2026-11-24): pay-as-you-go not supported for Veo 3.1, "
        f"Veo 3.1 Fast, or Veo 3.1 Lite; Provisioned Throughput and fixed quota supported; us-central1; release and retirement dates.</li>\n"
        f"  <li>Confirmed {e(day_label(GOOGLE_CHECKED))} on {gcp}: the Veo list lines above, printed per count.</li>\n"
        f"  <li>Confirmed {e(day_label(GOOGLE_CHECKED))} on {flow_src}: {daily} daily credits, plan credit amounts, Veo 3.1 Lite credit costs, "
        f"the peak-hours limit, and the {e(_long_day(retire_on)) if retire_on else 'Flow'} retirement notice.</li>\n"
        f"  <li>From our catalog, not re-read for this guide: the Google AI plan prices in the Flow table, checked {e(day_label((flow_plans.get('gflow-plus') or {}).get('checked') or LAST))}.</li>\n"
        "  <li>Not stated, so not guessed here: what one “count” is on Google Cloud’s Veo price list; Provisioned Throughput prices for Veo; "
        "whether third-party sellers will keep Veo 3.1 Fast after Flow retires it; audio on Higgsfield’s Veo 3.1 rows; and the resolution of the Runway API rows.</li>\n"
        "</ul>"
    )

    model_href = root("/models/veo-3-1/")
    vs_kling = root("/compare/kling-3-0-vs-veo-3-1/")
    vs_seed = root("/compare/seedance-2-5-vs-veo-3-1/")
    cheapest_all = root("/guides/cheapest-ai-video-generator/")
    deals_href = root("/deals/")
    flow_calc = root("/guides/google-flow-credits-calculator/")
    about = root("/about/")

    body = (
        f'<p class="small"><a href="{root("/guides/")}">Guides</a> › Veo 3.1 pricing</p>\n'
        f"<h1>{e(H1)}</h1>\n"
        f'<p class="disclose">Some links on this page are affiliate links. '
        f'<a href="{e(root("/about/#disclosure"))}">Affiliate disclosure</a>.</p>\n'
        f'<p class="lead">{lead}</p>\n'
        f'<p class="small">Last checked {e(LAST)}. Google’s pages were read {e(GOOGLE_WHEN)}. Catalog rows use the date on each row.</p>\n'
        f"{takeaways}\n\n"
        f"<h2>What is the cheapest Veo 3.1 price per second?</h2>\n"
        f"<p>{e(a_cheap)}</p>\n"
        f"{price_table}\n"
        f'<p class="small">All {len(rows)} current Veo 3.1 rows in our catalog, sorted by price per second only (ties by catalog row id). '
        f"Credit-plan rows assume every credit you pay for is used; unused credits make the real cost per second higher. "
        f"Estimated-from-plan rows are not list prices.{sale_foot} "
        f"Higgsfield links on this page are affiliate links; they never change the order of the rows.</p>\n\n"
        f"<h2>What does Veo 3.1 with audio cost?</h2>\n"
        f"<p>{e(a_audio)}</p>\n\n"
        f"<h2>Can you pay Google directly for Veo 3.1?</h2>\n"
        f"<p>{e(a_google)}</p>\n"
        f"{gcp_table}\n"
        f'<p class="small">Google Cloud’s pricing page prints each Veo price as “/ 1 count” and does not say what a count is on that page, '
        f"and the model cards say these models are not sold pay as you go. So these are list lines, not price-per-second rows: "
        f"they are not converted to $/s, not added to the catalog, and not ranked.</p>\n\n"
        f"<h2>How much does Veo 3.1 cost in Google Flow?</h2>\n"
        f"<p>{e(a_flow)}</p>\n"
        f"{flow_table}\n"
        f'<p class="small">Plan lines, not catalog rows, and not in the ranking above. Plan prices are from our catalog’s check of Google’s AI plans page '
        f"on {e(day_label((flow_plans.get('gflow-plus') or {}).get('checked') or LAST))}; credit amounts and Lite costs are from Google’s Flow help page the same day. "
        f"The per-second figure is plan price ÷ monthly credits × credits per video ÷ 8 seconds. It assumes you use every credit and counts the whole plan price as video spend, although Google AI plans include other features. Flow Lite is 720p only. "
        f'For other lengths and models, use the <a href="{e(flow_calc)}">Google Flow credits calculator</a>.</p>\n\n'
        f"<h2>Is Veo 3.1 Fast being retired?</h2>\n"
        f"<p>{e(a_retire)}</p>\n"
        f'<p class="small">Related: <a href="{e(model_href)}">every Veo 3.1 price on the model page</a> · '
        f'<a href="{e(vs_kling)}">Kling 3.0 vs Veo 3.1</a> · '
        f'<a href="{e(vs_seed)}">Seedance 2.5 vs Veo 3.1</a> · '
        f'<a href="{e(cheapest_all)}">cheapest rate for each model</a> · '
        f'<a href="{e(deals_href)}">current AI video deals</a>.</p>\n\n'
        f"{confirmed}\n"
        f'{g["how_block"]()}\n'
    )

    if "sora" in body.lower() or "sora" in description(g).lower() or "sora" in PHRASE.lower():
        raise SystemExit(f"{PATH} source would name the banned model")
    # Visible copy must stay on ET/PT clocks.
    visible = __import__("re").sub(r"<script[^>]*>.*?</script>", " ", body, flags=__import__("re").I | __import__("re").S)
    visible = __import__("re").sub(r"<[^>]+>", " ", visible)
    if __import__("re").search(r"\bUTC\b", visible):
        raise SystemExit(f"{PATH} visible copy contains UTC")
    title = g["page_title"](PHRASE)
    if len(title) > 60:
        raise SystemExit(f"{PATH} title is {len(title)} characters: {title}")
    desc = description(g)
    g["guide_page"](PATH, title, desc, body, faqs)
    return PATH
