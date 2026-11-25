"""Guide: Runway pricing per second.

Imported by scripts/build_site.py. Official plan prices and consumer credit
rates were read from runway.com/pricing on 2026-11-15. Official API rates
were read from docs.dev.runwayml.com/guides/pricing/ the same day and match
data/prices.json for the cataloged Runway API rows.
"""
from decimal import Decimal, ROUND_HALF_UP
import deal_copy
import guide_tables

PATH = "/guides/runway-pricing/"
LABEL = "Runway pricing"
PHRASE = "Runway pricing per second"
QUESTION = "How much does Runway cost per second?"
RUNWAY_PLANS = "https://runway.com/pricing"
RUNWAY_API = "https://docs.dev.runwayml.com/guides/pricing/"
TEAM_PLAN = "https://runway.com/team-plan"
HELP_UNLIMITED_TO_MAX = "https://help.runwayml.com/hc/en-us/articles/52068047744019-Unlimited-plan-is-switching-to-Max"
HELP_EXPLORE = "https://help.runwayml.com/hc/en-us/articles/32901341877011-Why-does-Explore-Mode-sometimes-move-faster-or-slower"
HELP_UNLIMITED_CREDITS = "https://help.runwayml.com/hc/en-us/articles/37309724921747-Why-does-the-Unlimited-plan-have-credits"
HELP_LEGACY = "https://help.runwayml.com/hc/en-us/articles/18053095835795-Unlimited-plan-details-Legacy"
HELP_MODE = "https://help.runwayml.com/hc/en-us/articles/54428296933011-Generating-in-Unlimited-Mode"
MODEL_PATH = "/models/runway-gen-4/"
CALC_PATH = "/calculator/?model=runway-gen-4&seconds=10"
CHECKED = "2026-11-15"
POLICY_CHECKED = "2026-11-18"

# Individual plans from runway.com/pricing, checked 2026-11-15.
# Yearly prices are the per-month figures shown under Yearly (20% off), billed annually.
# Credits are granted each month (yearly cards also list the yearly credit total).
INDIVIDUAL_PLANS = [
    # name, period, list_monthly, price, credits_per_month, first_note
    ("Free", "one-time", 0, 0, 125, "one-time credits, do not expire"),
    ("Standard", "monthly", 15, 15, 625, "credits reset each cycle"),
    ("Standard", "yearly", 15, 12, 625, "billed annually; credits reset each cycle"),
    ("Pro", "monthly", 35, 35, 2250, "credits reset each cycle"),
    ("Pro", "yearly", 35, 28, 2250, "billed annually; credits reset each cycle"),
    ("Max", "monthly", 95, 95, 9500, "unused credits roll over 1 month"),
    ("Max", "yearly", 95, 76, 9500, "billed annually; unused credits roll over 1 month"),
]
# Team from runway.com/team-plan, checked 2026-11-15. Per seat, 2–9 people.
TEAM_MONTHLY = 69
TEAM_YEARLY = 55
TEAM_CREDITS = 6900

# Consumer compare-table credit rates from runway.com/pricing, checked 2026-11-15.
# credits and seconds are the published clip, not a guessed conversion.
# audio/res are only filled when the table label states them.
CONSUMER_VIDEO = [
    # name, credits, seconds, audio, res, promo_credits or None, promo_note
    ("Gen-4.5", 60, 5, "not stated", "not stated", None, None),
    ("Gen-4 Video", 60, 5, "not stated", "not stated", None, None),
    ("Gen-4 Video Turbo", 25, 5, "not stated", "not stated", None, None),
    ("Gen-4 Aleph", 75, 5, "not stated", "not stated", None, None),
    ("Aleph 2.0", 140, 5, "not stated", "not stated", None, None),
    ("Act-Two", 25, 5, "not stated", "not stated", None, None),
    ("Veo 3.1", 320, 8, "with audio", "not stated", None, None),
    ("Veo 3", 320, 8, "with audio", "not stated", None, None),
    ("Kling 4.0", 118, 5, "not stated", "1080p", 89, "25% off through November 30, 2026"),
    ("Kling 3.0 Pro", 85, 5, "with audio", "not stated (Pro is the quality tier on the label)", None, None),
    ("Kling 3.0 Standard", 65, 5, "with audio", "not stated (Standard is the quality tier on the label)", None, None),
    ("Kling 3.0 Turbo", 80, 5, "not stated", "1080p", None, None),
    ("Kling 3.0 Motion Control", 85, 5, "not stated", "1080p", None, None),
    ("Kling O3 Pro", 85, 5, "not stated", "not stated", None, None),
    ("Kling 2.6 Pro", 125, 5, "not stated", "not stated", None, None),
    ("Kling 2.5 Turbo Pro", 75, 5, "not stated", "1080p", None, None),
    ("Kling 2.5 Turbo", 50, 5, "not stated", "not stated", None, None),
    ("Seedance 2.0 Pro", 160, 4, "not stated", "1080p", None, None),
    ("Seedance 2.0 Fast", 116, 4, "not stated", "not stated", None, None),
    ("Seedance 2.0 Mini", 64, 4, "not stated", "not stated", None, None),
    ("WAN 2.6", 75, 5, "not stated", "1080p", None, None),
    ("WAN 2.6 Flash", 50, 5, "not stated", "1080p", None, None),
    ("HappyHorse 1.0", 150, 5, "not stated", "1080p", None, None),
    ("Grok Imagine", 40, 5, "not stated", "720p", None, None),
    ("Grok Imagine 1.5", 81, 5, "not stated", "720p", None, None),
]

# Paid individual + team plans used for $/s (Free is one-time and is not a monthly rate).
PAID_FOR_RATES = [
    ("Standard", "monthly", Decimal("15"), 625),
    ("Standard", "yearly", Decimal("12"), 625),
    ("Pro", "monthly", Decimal("35"), 2250),
    ("Pro", "yearly", Decimal("28"), 2250),
    ("Max", "monthly", Decimal("95"), 9500),
    ("Max", "yearly", Decimal("76"), 9500),
    ("Team (per seat)", "monthly", Decimal("69"), 6900),
    ("Team (per seat)", "yearly", Decimal("55"), 6900),
]

# Highlighted models for the per-plan $/s table (full credit list is separate).
HIGHLIGHT = {
    "Gen-4.5",
    "Gen-4 Video",
    "Gen-4 Video Turbo",
    "Aleph 2.0",
    "Veo 3.1",
    "Kling 3.0 Pro",
}


def _src(g, url, text="source"):
    e = g["e"]
    href, rel = g["outbound"](url)
    return f'<a href="{e(href)}" rel="{rel}" target="_blank">{e(text)}</a>'


def checked_pt(date):
    """Date-only check label, e.g. 'Nov 23, 2026'. A date carries no clock, so no zone."""
    from timefmt import day_label
    return day_label(date)


def usd(v, places=2):
    q = Decimal("1").scaleb(-places)
    n = Decimal(str(v)).quantize(q, rounding=ROUND_HALF_UP)
    text = f"{abs(n):.{places}f}"
    return f"${text}"


def credit_cost(price, credits):
    return Decimal(str(price)) / Decimal(credits)


def blurb(g):
    official = [
        r
        for r in g["rows"]
        if r.get("platform") == "Runway API" and r.get("id") == "r047"
    ]
    rate = g["rate_money"](official[0]["usd_per_second"]) if official else "$0.05"
    return (
        f"Official Runway Free, Standard, Pro, Max, Team and Enterprise plans, "
        f"official API rates from {rate}/s for Gen-4 Turbo, and cheaper catalog routes we track."
    )


def description(g):
    last = g["LAST"]
    official = [
        r for r in g["rows"] if r.get("platform") == "Runway API" and r.get("id") == "r047"
    ]
    rate = g["rate_money"](official[0]["usd_per_second"]) if official else "$0.05"
    text = (
        "Runway Standard, Pro and Max plans, Gen-4.5 at 12 credits/s, official "
        f"API rates from {rate}/s, and cheaper catalog routes. Last checked {last}."
    )
    if len(text) > 160:
        raise SystemExit(f"{PATH} meta description is over 160 characters: {len(text)}")
    return text


def render(g):
    e, root, LAST = g["e"], g["root"], g["LAST"]
    rate_money = g["rate_money"]
    cost_money = g["cost_money"]
    plat_link = g["plat_link"]
    outbound = g["outbound"]
    shown_resolution = g["shown_resolution"]
    tag = g["tag"]
    deal_badges = g["deal_badges"]
    assumption_html = g["assumption_html"]

    dates = [CHECKED]
    runway_rows = guide_tables.active_rows(g, platform="Runway API")
    gen4_rows = guide_tables.active_rows(g, model="runway-gen-4")
    opening_map = {r["id"]: r for r in runway_rows + gen4_rows}
    opening_rows = sorted(opening_map.values(), key=lambda r: (r["usd_per_second"], r["id"]))
    for r in opening_rows:
        if r.get("checked"):
            dates.append(r["checked"])
    api_checked_dates = sorted({r["checked"] for r in runway_rows if r.get("checked")})
    api_checked_label = (
        checked_pt(api_checked_dates[0])
        if len(api_checked_dates) == 1
        else f"{checked_pt(api_checked_dates[0])} to {checked_pt(api_checked_dates[-1])}"
        if api_checked_dates
        else checked_pt(CHECKED)
    )
    g["SITEMAP_LASTMOD"][PATH] = max(dates)

    def src(url, text="source"):
        return _src(g, url, text)

    def row_source(r):
        href, rel = outbound(r["source_url"])
        link = f'<a href="{e(href)}" rel="{rel}" target="_blank">source</a>'
        return f'{link}, checked {e(checked_pt(r.get("checked")))}'

    plans_src = src(RUNWAY_PLANS, "Runway's pricing page")
    api_src = src(RUNWAY_API, "official API pricing document")
    team_src = src(TEAM_PLAN, "Runway for Teams")
    to_max = src(HELP_UNLIMITED_TO_MAX, "Unlimited plan is switching to Max")
    explore = src(HELP_EXPLORE, "Why does Explore Mode sometimes move faster or slower?")
    unlim_credits = src(HELP_UNLIMITED_CREDITS, "Why does the Unlimited plan have credits?")
    legacy = src(HELP_LEGACY, "Unlimited plan details (Legacy)")
    mode = src(HELP_MODE, "Generating in Unlimited Mode")
    model_href = root(MODEL_PATH)
    calc_href = root(CALC_PATH)
    cheap_href = root("/guides/cheapest-ai-video-generator/")
    kling_href = root("/guides/kling-ai-pricing/")
    grok_href = root("/guides/grok-imagine-video-cost/")
    seedance_href = root("/guides/cheapest-seedance-2-5/")
    wan_href = root("/guides/cheapest-wan-3-0/")
    budget_href = root("/guides/ai-video-project-budget/")

    # --- official plan table ---
    plan_body = []
    for name, period, list_p, price, credits, note in INDIVIDUAL_PLANS:
        if name == "Free":
            rate_txt = "—"
            period_txt = "one-time"
            price_txt = usd(0)
            list_txt = usd(0)
            cred_txt = "125 one-time"
        else:
            rate_txt = usd(credit_cost(price, credits), 4) + "/credit"
            period_txt = period
            price_txt = f"{usd(price)}/mo"
            list_txt = f"{usd(list_p)}/mo"
            cred_txt = f"{credits:,}/mo"
        plan_body.append(
            "<tr>"
            f"<td>{e(name)}</td>"
            f"<td>{e(period_txt)}</td>"
            f'<td class="num">{list_txt}</td>'
            f'<td class="num">{price_txt}</td>'
            f'<td class="num">{cred_txt}</td>'
            f'<td class="num">{rate_txt}</td>'
            f"<td>{e(note)}</td>"
            f'<td class="small">{src(RUNWAY_PLANS, "source")}, checked {e(checked_pt(CHECKED))}</td>'
            "</tr>"
        )
    # Team rows
    for period, price in (("monthly", TEAM_MONTHLY), ("yearly", TEAM_YEARLY)):
        list_p = TEAM_MONTHLY
        rate_txt = usd(credit_cost(price, TEAM_CREDITS), 4) + "/credit"
        plan_body.append(
            "<tr>"
            "<td>Team (per seat)</td>"
            f"<td>{period}</td>"
            f'<td class="num">{usd(list_p)}/mo</td>'
            f'<td class="num">{usd(price)}/mo</td>'
            f'<td class="num">{TEAM_CREDITS:,}/mo</td>'
            f'<td class="num">{rate_txt}</td>'
            "<td>2–9 seats; unused credits roll over 1 month</td>"
            f'<td class="small">{src(TEAM_PLAN, "source")}, checked {e(checked_pt(CHECKED))}</td>'
            "</tr>"
        )
    plan_table = (
        '<div class="tblwrap fit"><table><thead><tr>'
        "<th>Plan</th><th>Billing</th><th>List / month</th><th>Price shown</th>"
        "<th>Credits</th><th>Effective $ / credit</th><th>Notes</th><th>Source and date checked</th>"
        "</tr></thead><tbody>" + "".join(plan_body) + "</tbody></table></div>"
    )

    # --- consumer credits table ---
    kling4_live = deal_copy.is_live(g, "runway-kling4-25")
    cred_body = []
    for name, credits, seconds, audio, res, promo, promo_note in CONSUMER_VIDEO:
        per_s = Decimal(credits) / Decimal(seconds)
        per_s_txt = f"{per_s:.2f}".rstrip("0").rstrip(".")
        promo_txt = "—"
        if promo is not None:
            promo_s = Decimal(promo) / Decimal(seconds)
            if kling4_live:
                promo_txt = (
                    f"{promo} credits / {seconds}s "
                    f"({f'{promo_s:.2f}'.rstrip('0').rstrip('.')} credits/s). {promo_note}"
                )
            else:
                promo_txt = f"Ended ({promo_note})"
        cred_body.append(
            "<tr>"
            f"<td>{e(name)}</td>"
            f"<td>{e(res)}</td>"
            f"<td>{e(audio)}</td>"
            f'<td class="num">{credits} credits / {seconds}s</td>'
            f'<td class="num">{per_s_txt} credits/s</td>'
            f"<td>{e(promo_txt)}</td>"
            f'<td class="small">{src(RUNWAY_PLANS, "source")}, checked {e(checked_pt(CHECKED))}</td>'
            "</tr>"
        )
    cred_table = (
        '<div class="tblwrap fit"><table><thead><tr>'
        "<th>Model (as labeled)</th><th>Res</th><th>Audio</th>"
        "<th>Published clip</th><th>Credits / s</th><th>Promo, if any</th><th>Source and date checked</th>"
        "</tr></thead><tbody>" + "".join(cred_body) + "</tbody></table></div>"
    )

    # --- $/s on each paid plan for highlighted models ---
    def clip10_credits(credits, seconds):
        return (Decimal(credits) / Decimal(seconds)) * Decimal(10)

    rate_head = (
        "<th>Model</th><th>Res</th><th>Audio</th><th>Credits / s</th>"
        + "".join(
            f"<th>{e(name)} {e(period)} $/s</th><th>Per 10s</th>"
            for name, period, _p, _c in PAID_FOR_RATES
            if period == "yearly" and "Team" not in name
        )
    )
    # Keep the $/s table narrower: yearly individual plans only, plus a note that monthly is 25% higher.
    yearly_plans = [p for p in PAID_FOR_RATES if p[1] == "yearly" and "Team" not in p[0]]
    monthly_plans = [p for p in PAID_FOR_RATES if p[1] == "monthly" and "Team" not in p[0]]
    dollar_body = []
    for name, credits, seconds, audio, res, promo, promo_note in CONSUMER_VIDEO:
        if name not in HIGHLIGHT:
            continue
        per_s = Decimal(credits) / Decimal(seconds)
        cells = (
            f"<td>{e(name)}</td>"
            f"<td>{e(res)}</td>"
            f"<td>{e(audio)}</td>"
            f'<td class="num">{f"{per_s:.2f}".rstrip("0").rstrip(".")} credits/s</td>'
        )
        for pname, period, price, plan_credits in yearly_plans + monthly_plans:
            usd_ps = per_s * credit_cost(price, plan_credits)
            ten = clip10_credits(credits, seconds) * credit_cost(price, plan_credits)
            cells += (
                f'<td class="num">{rate_money(usd_ps)}/s</td>'
                f'<td class="num">{cost_money(ten)}</td>'
            )
        dollar_body.append("<tr>" + cells + "</tr>")
    # Build header in yearly-then-monthly order
    dollar_head = (
        "<th>Model</th><th>Res</th><th>Audio</th><th>Credits / s</th>"
        + "".join(
            f"<th>{e(n)} {e(p)}</th><th>10s</th>"
            for n, p, _a, _b in yearly_plans + monthly_plans
        )
    )
    dollar_table = (
        '<div class="tblwrap fit"><table><thead><tr>'
        + dollar_head
        + "</tr></thead><tbody>"
        + "".join(dollar_body)
        + "</tbody></table></div>"
    )

    # Team yearly Gen-4.5 example
    team_year_rate = credit_cost(TEAM_YEARLY, TEAM_CREDITS)
    gen45_s = Decimal(60) / Decimal(5)
    team_gen45 = gen45_s * team_year_rate
    max_year_rate = credit_cost(76, 9500)
    max_turbo = (Decimal(25) / Decimal(5)) * max_year_rate  # $0.04
    max_gen45 = gen45_s * max_year_rate  # $0.096
    std_year_gen45 = gen45_s * credit_cost(12, 625)
    api_turbo = next(r for r in runway_rows if r["id"] == "r047")
    api_gen45 = next(r for r in runway_rows if r["id"] == "r046")

    opening_table = guide_tables.price_table(
        g, opening_rows, table_id="prices", include_model=True, include_10s=True, min_width=1200
    )

    # --- official API catalog table ---
    api_body = []
    for r in sorted(runway_rows, key=lambda r: (r["usd_per_second"], r["id"])):
        audio_txt = guide_tables.audio_label(g, r)
        res = shown_resolution(r)
        api_body.append(
            "<tr>"
            f'<td>{plat_link(r["platform"], r["source_url"])}</td>'
            f'<td>{e(guide_tables.plan_label(r))}</td>'
            f'<td>{e(g["shown_tier"](r))}</td>'
            f"<td>{e(r.get('variant') or r['model'])}</td>"
            f"<td>{e(res)}</td>"
            f"<td>{e(audio_txt)}</td>"
            f'<td class="num"><span class="amt">{rate_money(r["usd_per_second"])}/s</span></td>'
            f'<td class="num">{cost_money(Decimal(str(r["usd_per_second"])) * 10)}</td>'
            f"<td>{tag(r)}{deal_badges(r)}</td>"
            f'<td class="small">{row_source(r)}</td>'
            "</tr>"
        )
    api_table = (
        '<div class="tblwrap fit"><table><thead><tr>'
        "<th>Seller</th><th>Plan</th><th>Tier</th><th>Official API variant</th><th>Resolution</th><th>Audio</th>"
        "<th>$ / sec</th><th>Per 10s</th><th>Status</th><th>Source and date checked</th>"
        "</tr></thead><tbody>" + "".join(api_body) + "</tbody></table></div>"
    )

    # --- cheaper routes: for each catalog model that has a Runway API row ---
    models = g["models"]
    cmp_body = []
    model_slugs = sorted({r["model"] for r in runway_rows}, key=lambda s: models.get(s, {}).get("name") or s)
    for slug in model_slugs:
        all_rows = guide_tables.active_rows(g, model=slug)
        run_rows = [r for r in all_rows if r.get("platform") == "Runway API"]
        cheapest = all_rows[0]
        cheapest_run = run_rows[0]
        beat = cheapest["id"] != cheapest_run["id"] and cheapest["usd_per_second"] < cheapest_run["usd_per_second"]

        def cell(r):
            platform = plat_link(r["platform"], r["source_url"])
            audio_txt = guide_tables.audio_label(g, r)
            plan = guide_tables.plan_label(r)
            tier = g["shown_tier"](r)
            variant = r.get("variant") or ""
            return (
                f'{platform}<br><span class="small">{e(variant)} · plan: {e(plan)} · tier: {e(tier)} · '
                f"{e(shown_resolution(r))} · {e(audio_txt)}</span><br>"
                f'<span class="num"><span class="amt">{rate_money(r["usd_per_second"])}/s</span></span> '
                f"{tag(r)}{deal_badges(r)}<br>"
                f'<span class="small">{row_source(r)}</span>'
            )

        cmp_body.append(
            "<tr>"
            f"<td>{e((models.get(slug) or {}).get('name') or slug)}</td>"
            f"<td>{cell(cheapest_run)}</td>"
            f"<td>{cell(cheapest)}</td>"
            f"<td>{'Yes' if beat else 'No cheaper catalog row'}</td>"
            "</tr>"
        )
    cmp_table = (
        '<div class="tblwrap fit"><table><thead><tr>'
        "<th>Model we track</th><th>Cheapest Runway API row</th>"
        "<th>Cheapest catalog row overall</th><th>Is something cheaper?</th>"
        "</tr></thead><tbody>" + "".join(cmp_body) + "</tbody></table></div>"
    )

    q_plans = "What do official Runway plans cost in " + __import__("timefmt").us_today().strftime("%B %Y") + "?"
    a_plans = (
        f"On {checked_pt(CHECKED)}, the public pricing page listed Free, Standard, Pro, and Max "
        "for individuals, plus a Team plan and an Enterprise tab. There is no plan named Unlimited "
        "for new buyers on that page. Free is $0 with 125 one-time credits that do not expire. "
        "Standard is $15/month, or $12/month billed yearly, with 625 credits a month. "
        "Pro is $35/month, or $28/month billed yearly, with 2,250 credits a month. "
        "Max is $95/month, or $76/month billed yearly, with 9,500 credits a month and a one-month "
        f"rollover for unused credits. Team, from a separate Team page, is $69 per seat per month, "
        "or $55 per seat per month billed yearly, with 6,900 credits per seat per month for groups "
        "of two to nine. Enterprise pricing is custom and is not listed as a public dollar amount. "
        f"Sources: {RUNWAY_PLANS} and {TEAM_PLAN}."
    )
    q_credits = "What do credits buy per second, and what does that cost on each plan?"
    a_credits = (
        f"The pricing-page compare table, read {checked_pt(CHECKED)}, lists credits per clip for "
        "each video model, with resolution or audio only when the label states them. Gen-4.5 and "
        "Gen-4 Video are 60 credits per 5 seconds (12 credits/s). Gen-4 Video Turbo is 25 credits "
        "per 5 seconds (5 credits/s). Aleph 2.0 is 140 credits per 5 seconds (28 credits/s). "
        "Veo 3.1 with audio is 320 credits per 8 seconds (40 credits/s). Dollar costs on a plan "
        "equal those credits times the plan's effective dollars per credit, and they assume every "
        "credit in that month's allotment is used. On Max billed yearly that is "
        f"{rate_money(max_gen45)}/s for Gen-4.5 and {rate_money(max_turbo)}/s for Gen-4 Video Turbo. "
        "Standard and Pro credits reset each cycle, so unused credits raise the real cost."
    )
    q_api = "What does the official Runway API charge?"
    a_api = (
        f"The official API document, checked {checked_pt(CHECKED)}, sells credits at $0.01 each. "
        f"Gen-4 Turbo is 5 credits/s ({rate_money(api_turbo['usd_per_second'])}/s, "
        f"{cost_money(Decimal(str(api_turbo['usd_per_second'])) * 10)} per 10 seconds). "
        f"Gen-4.5 is 12 credits/s ({rate_money(api_gen45['usd_per_second'])}/s, "
        f"{cost_money(Decimal(str(api_gen45['usd_per_second'])) * 10)} per 10 seconds). "
        "Aleph 2.0 is 28 credits/s ($0.28/s) with a 56-credit minimum per generation. "
        "Those Gen-4 figures match the Runway API rows in our catalog. The same document lists "
        "many other models; catalog rows are the ones in the API table below."
    )
    q_unlimited = "What does Unlimited's relaxed mode actually mean?"
    a_unlimited = (
        "Two different things share similar names. The Unlimited plan is a legacy plan that is no "
        "longer offered to new buyers. Official help, updated August 27, 2026 and re-read "
        f"{checked_pt(CHECKED)}, says eligible legacy Unlimited plans stay unchanged through "
        "November 30, 2026, then monthly plans move to Max at $95/month. That legacy plan included "
        "2,250 credits plus Explore Mode (also called Unlimited Mode in the legacy article) for "
        "generations that do not use credits, at a relaxed rate: start times can be slower in busy "
        "periods, and the number of generations at once is limited. Veo 3 and Veo 3.1 were not "
        "available in that mode and required credits. Separately, a help article titled "
        "Generating in Unlimited Mode says Unlimited Mode is a generation mode, not the same as "
        "the legacy plan, and that this mode is currently available on Pro and Max. It may take "
        "longer to start and run fewer jobs at once. Which models it covers on Pro or Max can "
        "change with promotions and plan type; the article says to look for the Unlimited option "
        "in the session. A dollar cost per second cannot be computed for generations in that mode, "
        "because they are not billed in credits."
    )
    cheapest_gen4 = min(gen4_rows, key=lambda r: (r["usd_per_second"], r["id"]))
    q_cheaper = "When is a route elsewhere cheaper?"
    a_cheaper = (
        f"For Runway's own Gen-4, the cheapest catalog row is {rate_money(cheapest_gen4['usd_per_second'])}/s on "
        f"{cheapest_gen4['platform']} ({guide_tables.plan_label(cheapest_gen4)}, tier {g['shown_tier'](cheapest_gen4)}, "
        f"{shown_resolution(cheapest_gen4)}, {guide_tables.audio_label(g, cheapest_gen4)}), "
        f"compared with the official API's {rate_money(api_gen45['usd_per_second'])}/s for Gen-4.5 "
        f"(and {rate_money(api_turbo['usd_per_second'])}/s for Gen-4 Turbo). "
        f"Gen-4 Turbo's cheapest catalog row is the official Runway API at "
        f"{rate_money(api_turbo['usd_per_second'])}/s; we do not track a cheaper Turbo route. "
        "For models Runway also resells, including Kling 3.0, Wan 3.0, Seedance 2.5, Veo 3.1, "
        "Grok Imagine, Gemini Omni Flash, and MiniMax Hailuo, other APIs or credit plans in the "
        "catalog are often cheaper than Runway's API. Those comparisons are in the table below. "
        "A credit-plan rate only holds if you use the credits you pay for. Affiliate links never "
        "change this price order."
    )
    q_unknown = "What is confirmed, and what is not?"
    a_unknown = (
        f"Confirmed {checked_pt(CHECKED)} on official Runway pages: the Free, Standard, Pro, and Max "
        "prices and monthly credits, Team seat prices and credits, the consumer compare-table "
        "credit rates, official API credit rates including Gen-4.5, Gen-4 Turbo, Aleph 2.0, and "
        "Veo 3.1, the $0.01 API credit price, and the help-center description of the legacy "
        "Unlimited plan, Explore Mode, the November 30, 2026 move to Max, and Unlimited Mode on "
        "Pro and Max. Confirmed in the catalog (Runway API rows checked {api_checked_label}): every Runway API $/s row in the API table. Unknown: the public "
        "dollar price of consumer credit packs (the page says the minimum purchase is 1,000 credits "
        "but does not list a price); which models the Free plan includes; a Seedance 2.5 credit "
        "rate on the consumer compare table (the table lists Seedance 2.0 variants; Pro and Max "
        "cards mention Seedance 2.5 without a credit figure); which models Unlimited Mode covers "
        "on Pro and Max at a given moment; Enterprise's custom dollar price; and why the Standard "
        "and Pro plan cards quote 104 and 375 seconds of Gen-4 Turbo, which does not match the "
        "compare table's 25 credits per 5 seconds."
    )

    q_promo = "Is there a Runway promo code?"
    a_promo = (
        f"No public promo or coupon code was listed on Runway's official pricing page when it was opened {checked_pt(POLICY_CHECKED)}. "
        "An Enterprise-tab offer of up to two months of usage free, with a sign-by date, is not a public promo code. "
        "This guide does not invent a code."
    )
    q_free = "Is Runway free?"
    a_free = (
        f"Yes. The official pricing page, opened {checked_pt(POLICY_CHECKED)}, lists a Free plan at $0/month, labelled Free forever, "
        "with 125 one-time credits and 5 GB of storage, plus a selection of generative models. "
        "The page does not publish a complete public list of which models the Free plan includes."
    )
    faqs = [
        (QUESTION, a_plans),
        (q_plans, a_plans),
        (q_credits, a_credits),
        (q_api, a_api),
        (q_unlimited, a_unlimited),
        (q_cheaper, a_cheaper),
        (q_promo, a_promo),
        (q_free, a_free),
        (q_unknown, a_unknown),
    ]
    for q, a in faqs:
        raw = (q + " " + a).lower()
        for bad in ("subscribe", "newsletter", "buttondown"):
            if bad in raw:
                raise SystemExit(f"{PATH} FAQ text contains {bad}")

    lead = (
        f"Official Runway plans, read {e(checked_pt(CHECKED))} from {plans_src}, are Free, "
        f"Standard, Pro, and Max for individuals, plus Team and Enterprise. Standard is "
        f"{usd(15)}/month or {usd(12)}/month billed yearly, with 625 credits a month. Pro is "
        f"{usd(35)}/month or {usd(28)}/month billed yearly, with 2,250 credits. Max is "
        f"{usd(95)}/month or {usd(76)}/month billed yearly, with 9,500 credits. There is no plan "
        f"named Unlimited for new buyers. The official API, from {api_src}, charges $0.01 per "
        f"credit, or {rate_money(api_turbo['usd_per_second'])}/s for Gen-4 Turbo and "
        f"{rate_money(api_gen45['usd_per_second'])}/s for Gen-4.5. On Max billed yearly, Gen-4.5 "
        f"is {rate_money(max_gen45)}/s if you use the month's credits. In our catalog, "
        f"Gen-4 Turbo starts at {rate_money(api_turbo['usd_per_second'])}/s on Runway API and "
        f"Runway Gen-4 rows start at {rate_money(cheapest_gen4['usd_per_second'])}/s on "
        f"{cheapest_gen4['platform']} ({guide_tables.plan_label(cheapest_gen4)})."
    )

    takeaways = f"""<div class="card" id="takeaways">
<h2>Key takeaways</h2>
<ul>
<li><b>Cheapest official Runway API rate.</b> {e(rate_money(api_turbo['usd_per_second']))}/s for Gen-4 Turbo ({e(shown_resolution(api_turbo))}, {e(guide_tables.audio_label(g, api_turbo))}), checked {e(checked_pt(api_turbo.get('checked') or CHECKED))}.</li>
<li><b>Official Gen-4.5 API vs consumer Max yearly.</b> {e(rate_money(api_gen45['usd_per_second']))}/s on Runway API, or {e(rate_money(max_gen45))}/s on Max billed yearly ({usd(76)}/mo, 9,500 credits) if every credit is used.</li>
<li><b>Cheapest Runway Gen-4 catalog row.</b> {e(rate_money(cheapest_gen4['usd_per_second']))}/s on {e(cheapest_gen4['platform'])} ({e(guide_tables.plan_label(cheapest_gen4))}, tier {e(g['shown_tier'](cheapest_gen4))}, {e(shown_resolution(cheapest_gen4))}), checked {e(checked_pt(cheapest_gen4.get('checked') or CHECKED))}.</li>
<li><b>Free plan &amp; Unlimited mode.</b> Free gives 125 one-time credits ({usd(0)}). Legacy Unlimited moved to Max ($95/mo) after Nov 30, 2026; Unlimited Mode is a non-credit mode on Pro and Max.</li>
</ul>
</div>"""

    body = f"""<p class="small"><a href="{root("/guides/")}">Guides</a> › Runway pricing</p>
<h1>{e(PHRASE)}</h1>
<p class="lead">{lead}</p>
<p class="small">Last checked {e(LAST)}. Official plan, compare-table, API, and help-center figures were read {e(checked_pt(CHECKED))}. Catalog rows below use the date on each row. See the <a href="{e(model_href)}">Runway Gen-4 model page</a> and the <a href="{e(calc_href)}">credit calculator for a 10-second Runway Gen-4 clip</a>.</p>
{takeaways}

<h2>Runway Gen-4 and Runway API per-second prices</h2>
<p>Every Runway Gen-4 and Runway API row in data/prices.json, sorted cheapest first, split by resolution and audio, with seller, plan, tier, usage assumption, and source. Affiliate links never change this price order.</p>
{opening_table}

<h2>{e(QUESTION)}</h2>
<p>{e(a_plans)}</p>

<h2>{e(q_plans)}</h2>
<p>The public pricing page, opened {e(checked_pt(CHECKED))} without signing in, has Individual, Team &amp; Enterprise, and API tabs, and a Monthly / Yearly toggle. Yearly is 20% off the monthly price, billed once a year, with the same monthly credit allotment. A free plan sits at {usd(0)} with a one-time 125-credit deposit. {plans_src}. Team prices are from {team_src}.</p>
{plan_table}
<p class="small">Effective $ / credit is plan price ÷ credits in that month, before tax. Yearly rows use the per-month figure shown under Yearly. Team is priced per seat; credits go into one shared pool. Enterprise is listed as custom, with no public dollar amount. The pricing-page FAQ says purchased extra credits never expire and that the minimum pack is 1,000 credits, but it does not list a pack price.</p>

<h2>{e(q_credits)}</h2>
<p>{e(a_credits)} The dollar columns assume a 10-second clip is billed at the same credits-per-second rate as the published clip (5 seconds for most models, 4 seconds for Seedance 2.0, 8 seconds for Veo). If a model does not actually allow a 10-second output, that 10-second total would not apply.</p>
<h3>Published credits per clip</h3>
{cred_table}
<p class="small">Kling 4.0's 25% off promo (through November 30, 2026): {'live' if kling4_live else 'ended'} per data/deals.json. Grok Imagine 1.5 is printed as 81 credits per 5 seconds (16.2 credits/s). The official API lists Grok Imagine 1.5 at 16 credits/s at 720p, plus 1 credit per image or audio reference; this guide does not treat those two figures as the same rate.</p>
<p class="small">The Standard and Pro plan cards say 625 credits equal 104 seconds of Gen-4 Turbo, and 2,250 credits equal 375 seconds. Those second counts only match a 6 credit/s rate. The compare table on the same page lists Gen-4 Video Turbo at 25 credits per 5 seconds (5 credits/s), and the Max card's 1,900 seconds of Gen-4 Turbo with 9,500 credits also matches 5 credits/s. Dollar figures in this guide use the compare table, not those Standard and Pro second counts.</p>
<h3>Dollar cost on each paid individual plan</h3>
{dollar_table}
<p>Team at {usd(TEAM_YEARLY)} per seat per month billed yearly is {usd(credit_cost(TEAM_YEARLY, TEAM_CREDITS), 4)}/credit, or {rate_money(team_gen45)}/s for Gen-4.5 and {rate_money((Decimal(25)/Decimal(5))*team_year_rate)}/s for Gen-4 Video Turbo, with the same usage assumption. Team monthly at {usd(TEAM_MONTHLY)} per seat is {usd(credit_cost(TEAM_MONTHLY, TEAM_CREDITS), 4)}/credit, the same as Max monthly and the official API.</p>

<h2>{e(q_api)}</h2>
<p>{e(a_api)} The API tab on the marketing pricing page says video starts from {rate_money(api_turbo['usd_per_second'])}/sec, which matches Gen-4 Turbo at 5 credits/s. {api_src}.</p>
{api_table}
<p>The official API document also lists models that are not separate rows in this catalog, including Aleph 2.0 at 28 credits/s (56-credit minimum), Act-Two at 5 credits/s, and several Kling 4, Seedance 2.0, and Gemini Omni Flash 1.2 variants. Those dollar figures are $0.01 times the published credits, and they are not ranked in the catalog table above.</p>

<h2>{e(q_unlimited)}</h2>
<p>{e(a_unlimited)}</p>
<p>Official help sources, all opened {e(checked_pt(CHECKED))}: {to_max} (updated August 27, 2026) · {unlim_credits} (updated August 27, 2026) · {explore} (updated August 27, 2026) · {legacy} (updated August 27, 2026) · {mode} (no update date was shown on the article).</p>

<h2>Cheaper routes we track</h2>
<p>These rows are from our catalog, not from Runway's consumer plans. The Runway API column is the cheapest official API row we store for that model. The overall column is the cheapest row we store anywhere, lowest $/s first within each model. A credit-plan figure assumes every credit you pay for is used. Affiliate links never change this price order.</p>
{cmp_table}
<p>Related: <a href="{e(model_href)}">every Runway Gen-4 row on the model page</a> · <a href="{e(cheap_href)}">cheapest rate we track for each model</a> · <a href="{e(kling_href)}">Kling AI pricing and credits</a> · <a href="{e(grok_href)}">Grok Imagine video cost</a> · <a href="{e(seedance_href)}">the cheapest way to use Seedance 2.5</a> · <a href="{e(wan_href)}">cheapest Wan 3.0</a> · <a href="{e(budget_href)}">project budget calculator</a>.</p>

<h2>{e(q_cheaper)}</h2>
<p>{e(a_cheaper)}</p>

<h2>{e(q_promo)}</h2>
<p>{e(a_promo)} Source: {src(RUNWAY_PLANS, "runway.com/pricing")}, opened {e(checked_pt(POLICY_CHECKED))}.</p>

<h2>{e(q_free)}</h2>
<p>{e(a_free)} Source: {src(RUNWAY_PLANS, "runway.com/pricing")}, opened {e(checked_pt(POLICY_CHECKED))}. The Free card is labelled “Free forever.”</p>

<h2>{e(q_unknown)}</h2>
<p>{e(a_unknown)}</p>
<p><b>Confirmed {e(checked_pt(CHECKED))} on official Runway pages:</b> the plan prices, credits, consumer clip rates, official API rates, the $0.01 API credit price, and the help-center account of the legacy Unlimited plan, Explore Mode, the November 30, 2026 move to Max, and Unlimited Mode on Pro and Max.</p>
<p><b>Confirmed in the catalog:</b> every Runway API $/s row in the API table, each with its vendor URL and check date ({e(api_checked_label)}).</p>
<p class="small">Affiliate links never change this price order.</p>
{g["how_block"]()}
"""

    title = g["page_title"](PHRASE)
    desc = description(g)
    g["guide_page"](PATH, title, desc, body, faqs)
    return PATH
