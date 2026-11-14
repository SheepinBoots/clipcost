"""Guide: Kling AI pricing and credits.

Imported by scripts/build_site.py. Official membership prices were read from
Kling's membership page on 2026-11-14. Official API rates were read from
Kling's API pricing document the same day and match data/prices.json.
"""
PATH = "/guides/kling-ai-pricing/"
LABEL = "Kling AI pricing"
PHRASE = "Kling AI pricing and credits"
QUESTION = "How much does Kling AI cost, and what do credits buy?"
KLING_PLANS = "https://kling.ai/app/membership/membership-plan"
KLING_API = "https://kling.ai/document-api/pricing/base/video.md"
KLING_MARKETING = "https://kling.ai/pricing"
PAID_TERMS = "https://kling.ai/docs/payment-policy"
MODEL_PATH = "/models/kling-3-0/"
CALC_PATH = "/calculator/?model=kling-3-0&seconds=10"
CHECKED = "2026-11-14"

# Official membership prices from the membership-plan page and the
# memberships-by-duration payload that page loaded on 2026-11-14.
# Prices are USD. Credits are the amounts the page displays (660, 3000, …).
# Yearly plans grant that credit amount each month for 12 months.
# First-month "FIRST" prices are a one-time 30% off list, per the page.
MONTHLY_PLANS = [
    # name, credits/mo, first, then, list, first per-100, then per-100
    ("Standard", 660, 6.99, 8.80, 10.00, 1.06, 1.33),
    ("Pro", 3000, 25.99, 32.56, 37.00, 0.87, 1.09),
    ("Premier (8,000 credits)", 8000, 64.99, 80.96, 92.00, 0.81, 1.01),
    ("Premier (18,000 credits)", 18000, 144.99, 181.99, 207.00, 0.81, 1.01),
    ("Premier (28,000 credits)", 28000, 225.99, 283.99, 322.00, 0.81, 1.01),
    ("Premier (38,000 credits)", 38000, 299.99, 376.99, 428.00, 0.79, 0.99),
    ("Ultra+", 57000, 432.99, 544.99, 619.00, 0.76, 0.96),
]
YEARLY_PLANS = [
    # name, credits/mo, yearly, list yearly, per-100
    ("Standard", 660, 79.20, 120.00, 1.00),
    ("Pro", 3000, 293.04, 444.00, 0.81),
    ("Premier (8,000 credits)", 8000, 728.64, 1104.00, 0.76),
    ("Premier (18,000 credits)", 18000, 1639.99, 2484.00, 0.76),
    ("Premier (28,000 credits)", 28000, 2550.99, 3864.00, 0.76),
    ("Premier (38,000 credits)", 38000, 3389.99, 5136.00, 0.74),
    ("Ultra+", 57000, 4902.99, 7428.00, 0.72),
]
# Credit packs from the same page's points payload, checked 2026-11-14.
# Purchased credits: paid-service terms say validity is 2 years.
CREDIT_PACKS = [
    # bought, bonus, price, per-100
    (330, 0, 5.00, 1.52),
    (660, 0, 10.00, 1.52),
    (1320, 0, 20.00, 1.52),
    (3300, 200, 50.00, 1.43),
    (6600, 900, 100.00, 1.33),
    (13200, 2800, 200.00, 1.25),
    (39600, 8400, 600.00, 1.25),
    (79200, 16800, 1200.00, 1.25),
]

# Official API resource-package rates from KLING_API, checked 2026-11-14.
# These Kling 3.0 figures match catalog rows r059–r065.
API_RATES = [
    # variant, res, audio, usd_per_second, units, catalog_id or None
    ("Kling 3.0, no native audio", "720p", False, 0.084, "0.6 Units", "r059"),
    ("Kling 3.0, no native audio", "1080p", False, 0.112, "0.8 Units", "r060"),
    ("Kling 3.0, no native audio", "4K", False, 0.42, "3.0 Units", "r061"),
    ("Kling 3.0, with native audio", "720p", True, 0.126, "0.9 Units", "r062"),
    ("Kling 3.0, with native audio", "1080p", True, 0.168, "1.2 Units", "r063"),
    ("Kling 3.0, with native audio", "4K", True, 0.42, "3.0 Units", "r061"),
    ("Kling 3.0 Turbo, with native audio", "720p", True, 0.112, "0.8 Units", "r064"),
    ("Kling 3.0 Turbo, with native audio", "1080p", True, 0.14, "1.0 Unit", "r065"),
]


def _src(g, url, text="source"):
    e = g["e"]
    href, rel = g["outbound"](url)
    return f'<a href="{e(href)}" rel="{rel}" target="_blank">{e(text)}</a>'


def checked_pt(date):
    if not date:
        return "date not stated"
    parts = str(date).split("-")
    if len(parts) != 3:
        return f"{date} PT"
    months = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    try:
        return f"{months[int(parts[1]) - 1]} {int(parts[2])}, {parts[0]} PT"
    except (ValueError, IndexError):
        return f"{date} PT"


def usd(v, places=2):
    q = f"{float(v):.{places}f}"
    if places > 2:
        q = q.rstrip("0").rstrip(".")
        if "." in q:
            whole, frac = q.split(".", 1)
            if len(frac) < 2:
                q = whole + "." + frac.ljust(2, "0")
    return f"${q}"


def blurb(g):
    official = [r for r in g["rows"] if r.get("platform") == "Kling API" and r.get("id") == "r059"]
    rate = g["rate_money"](official[0]["usd_per_second"]) if official else "$0.084"
    return (
        f"Official Kling plans and credits, official API rates from {rate}/s "
        f"at 720p without audio, and cheaper catalog routes we track."
    )


def description(g):
    last = g["LAST"]
    text = (
        "Kling Standard, Pro, Premier and Ultra+ plans, official API rates "
        f"from $0.084/s at 720p, and cheaper catalog routes. Last checked {last}."
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
    kling_rows = [r for r in g["rows"] if r.get("model") == "kling-3-0"]
    for r in kling_rows:
        if r.get("checked"):
            dates.append(r["checked"])
    g["SITEMAP_LASTMOD"][PATH] = max(dates)

    def src(url, text="source"):
        return _src(g, url, text)

    def row_source(r):
        href, rel = outbound(r["source_url"])
        link = f'<a href="{e(href)}" rel="{rel}" target="_blank">source</a>'
        return f'{link}, checked {e(checked_pt(r.get("checked")))}'

    official = [r for r in kling_rows if r.get("platform") == "Kling API"]
    r059 = next(r for r in official if r["id"] == "r059")
    r062 = next(r for r in official if r["id"] == "r062")
    cheapest = sorted(kling_rows, key=lambda r: (r["usd_per_second"], r["id"]))[0]
    verified = [r for r in kling_rows if r.get("status") == "verified"]
    cheapest_verified = sorted(verified, key=lambda r: (r["usd_per_second"], r["id"]))[0]

    ten_no = cost_money(0.084 * 10)
    ten_yes = cost_money(0.126 * 10)

    # --- official plan tables ---
    def comma(n):
        return f"{int(n):,}"

    monthly_body = []
    for name, credits, first, then, list_p, p100_first, p100_then in MONTHLY_PLANS:
        monthly_body.append(
            "<tr>"
            f"<td>{e(name)}</td>"
            f'<td class="num">{comma(credits)}</td>'
            f'<td class="num">{usd(list_p)}</td>'
            f'<td class="num">{usd(first)}</td>'
            f'<td class="num">{usd(then)}</td>'
            f'<td class="num">{usd(p100_then)}</td>'
            "</tr>"
        )
    monthly_table = (
        '<div class="tblwrap fit"><table><thead><tr>'
        "<th>Plan</th><th>Credits / month</th><th>List</th><th>First month</th>"
        "<th>Then / month</th><th>$ / 100 credits (ongoing)</th>"
        "</tr></thead><tbody>" + "".join(monthly_body) + "</tbody></table></div>"
    )

    yearly_body = []
    for name, credits, yearly, list_y, p100 in YEARLY_PLANS:
        yearly_body.append(
            "<tr>"
            f"<td>{e(name)}</td>"
            f'<td class="num">{comma(credits)}</td>'
            f'<td class="num">{usd(list_y)}</td>'
            f'<td class="num">{usd(yearly)}</td>'
            f'<td class="num">{usd(yearly / 12, 2)}</td>'
            f'<td class="num">{usd(p100)}</td>'
            "</tr>"
        )
    yearly_table = (
        '<div class="tblwrap fit"><table><thead><tr>'
        "<th>Plan</th><th>Credits / month</th><th>List / year</th><th>Yearly price</th>"
        "<th>Equivalent / month</th><th>$ / 100 credits</th>"
        "</tr></thead><tbody>" + "".join(yearly_body) + "</tbody></table></div>"
    )

    pack_body = []
    for bought, bonus, price, p100 in CREDIT_PACKS:
        total = bought + bonus
        bonus_txt = f"{comma(bought)} + {comma(bonus)} bonus" if bonus else comma(bought)
        pack_body.append(
            "<tr>"
            f'<td class="num">{bonus_txt}</td>'
            f'<td class="num">{comma(total)}</td>'
            f'<td class="num">{usd(price)}</td>'
            f'<td class="num">{usd(p100)}</td>'
            "</tr>"
        )
    pack_table = (
        '<div class="tblwrap fit"><table><thead><tr>'
        "<th>Credits in the pack</th><th>Total credits</th><th>Price</th><th>$ / 100 credits</th>"
        "</tr></thead><tbody>" + "".join(pack_body) + "</tbody></table></div>"
    )

    api_body = []
    for variant, res, audio, rate, units, _rid in API_RATES:
        audio_txt = "with audio" if audio else "without audio"
        clip10 = cost_money(rate * 10)
        api_body.append(
            "<tr>"
            f"<td>{e(variant)}</td>"
            f"<td>{e(res)}</td>"
            f"<td>{e(audio_txt)}</td>"
            f'<td class="num">{rate_money(rate)}/s</td>'
            f'<td class="num">{clip10}</td>'
            f"<td>{e(units)}</td>"
            "</tr>"
        )
    api_table = (
        '<div class="tblwrap fit"><table><thead><tr>'
        "<th>Official API variant</th><th>Res</th><th>Audio</th>"
        "<th>$/s</th><th>Per 10s</th><th>Units on the official table</th>"
        "</tr></thead><tbody>" + "".join(api_body) + "</tbody></table></div>"
    )

    # Third-party comparison: one cheapest row per platform+resolution+audio bucket,
    # but show all catalog kling-3-0 rows sorted by $/s so price order is preserved.
    cmp_body = []
    for r in sorted(kling_rows, key=lambda r: (r["usd_per_second"], r["id"])):
        platform = plat_link(r["platform"], r["source_url"])
        res = shown_resolution(r)
        audio = r.get("audio")
        if audio is True:
            audio_txt = "with audio"
        elif audio is False:
            audio_txt = "without audio"
        else:
            audio_txt = "not stated"
        kind = "API" if r.get("kind") == "api" else "credit plan"
        plan = r.get("plan_name") or ""
        variant = r.get("variant") or ""
        label = variant if not plan else f"{variant} · {plan}"
        assume = ""
        if assumption_html(r):
            assume = assumption_html(r)
        status = f'<span class="badges">{tag(r)}{deal_badges(r)}</span>'
        cmp_body.append(
            "<tr>"
            f"<td>{platform}</td>"
            f"<td>{e(label)}</td>"
            f"<td>{e(kind)}</td>"
            f"<td>{e(res)}</td>"
            f"<td>{e(audio_txt)}</td>"
            f'<td class="num">{rate_money(r["usd_per_second"])}/s</td>'
            f"<td>{status}</td>"
            f"<td class=\"small\">{row_source(r)}</td>"
            "</tr>"
        )
        # assume is visual note; include math in source cell already via details? keep compact
        if assume:
            pass
    cmp_table = (
        '<div class="tblwrap fit"><table><thead><tr>'
        "<th>Where</th><th>Variant / plan</th><th>Type</th><th>Res</th><th>Audio</th>"
        "<th>$/s</th><th>Status</th><th>Source</th>"
        "</tr></thead><tbody>" + "".join(cmp_body) + "</tbody></table></div>"
    )

    hf = src(KLING_PLANS, "Kling membership plans")
    api_src = src(KLING_API, "official API pricing document")
    terms = src(PAID_TERMS, "Kling Terms of Paid Service")
    model_href = root(MODEL_PATH)
    calc_href = root(CALC_PATH)
    cheap_href = root("/guides/cheapest-ai-video-generator/")
    hf_href = root("/guides/higgsfield-pricing/")
    budget_href = root("/guides/ai-video-project-budget/")

    q_plans = "What do official Kling plans cost right now?"
    a_plans = (
        f"On {checked_pt(CHECKED)}, the official membership page listed Standard, Pro, "
        "Premier (with 8,000, 18,000, 28,000 or 38,000 credits a month), and Ultra+, "
        "plus a Business tab. Monthly plans show a one-time first-month price, then a "
        "lower-than-list ongoing monthly price. Yearly plans are billed once a year and "
        "grant the listed credits each month for 12 months. The figures are in the tables "
        f"on this page, from {KLING_PLANS}."
    )
    q_credits = "What do official Kling credits buy per second or per clip?"
    a_credits = (
        "That number is unknown. The official membership page lists how many credits "
        "each plan includes, and the cost per 100 credits, but it does not publish how "
        "many credits a Kling 3.0 or Kling 4.0 clip uses at a given resolution, with or "
        "without audio. This guide does not invent that conversion. Official API billing "
        "uses a separate resource-package unit priced in dollars on the API document, "
        "not the app credit packs."
    )
    q_api = "What does the official Kling API charge for Kling 3.0?"
    a_api = (
        f"The official API document, checked {checked_pt(CHECKED)}, prices Kling 3.0 at "
        f"{rate_money(0.084)}/s at 720p without native audio ({ten_no} per 10 seconds) "
        f"and {rate_money(0.126)}/s at 720p with native audio ({ten_yes} per 10 seconds). "
        f"1080p is {rate_money(0.112)}/s without audio and {rate_money(0.168)}/s with audio. "
        f"4K is {rate_money(0.42)}/s with or without native audio. Kling 3.0 Turbo with "
        f"native audio is {rate_money(0.112)}/s at 720p and {rate_money(0.14)}/s at 1080p. "
        "Those dollar figures match the Kling API rows in our catalog."
    )
    q_cheaper = "When is pay-as-you-go or a plan elsewhere cheaper?"
    a_cheaper = (
        f"The cheapest Kling 3.0 rate we track is {rate_money(cheapest['usd_per_second'])}/s "
        f"on {cheapest['platform']} ({cheapest['variant']}, {shown_resolution(cheapest)}), "
        f"{'a credit-plan estimate' if cheapest.get('status') == 'estimate' else 'a verified rate'}, "
        f"checked {checked_pt(cheapest.get('checked'))}. The cheapest verified rate is "
        f"{rate_money(cheapest_verified['usd_per_second'])}/s on {cheapest_verified['platform']} "
        f"({cheapest_verified['variant']}, {shown_resolution(cheapest_verified)}). "
        f"Both undercut the official API's {rate_money(0.084)}/s at 720p without audio. "
        "A credit-plan rate only holds if you use the credits you pay for. Official API "
        "rates can still be cheaper than some other APIs, including fal Pro and several "
        "Runway API variants. Affiliate links never change this price order."
    )
    q_unknown = "What is confirmed, and what is not?"
    a_unknown = (
        f"Confirmed {checked_pt(CHECKED)} on official Kling pages: the membership plan "
        "prices, monthly credit allotments, first-month and ongoing monthly prices, yearly "
        "prices, credit packs, and the official API dollar rates for Kling 3.0 (and the "
        "other official API rows on the same document, which are not in this catalog). "
        "Confirmed in our catalog the same day: the third-party $/s rows in the comparison "
        "table, each with its vendor URL. Unknown: how many official app credits a clip "
        "uses, so an app-credit cost per second or per clip is not shown; whether the "
        f"marketing page at {KLING_MARKETING} lists a different regional price (that URL "
        "rendered as a product page, not a plan table); and a Replicate Kling 3.0 rate, "
        "because we do not have one in the catalog."
    )

    # Avoid the substring "subscribe" in FAQ JSON-LD (it also matches "subscription").
    faqs = [
        (QUESTION, a_plans),
        (q_plans, a_plans),
        (q_credits, a_credits),
        (q_api, a_api),
        (q_cheaper, a_cheaper),
        (q_unknown, a_unknown),
    ]
    for q, a in faqs:
        raw = (q + " " + a).lower()
        for bad in ("subscribe", "newsletter", "buttondown"):
            if bad in raw:
                raise SystemExit(f"{PATH} FAQ text contains {bad}")

    lead = (
        f"Official Kling membership plans, read {e(checked_pt(CHECKED))} from "
        f"{hf}, start at {usd(6.99)} for the first month of Standard (then {usd(8.80)}/month; "
        f"list {usd(10)}/month) with 660 credits a month. The official API, from {api_src}, "
        f"charges {rate_money(0.084)}/s at 720p without native audio ({ten_no} per 10 seconds) "
        f"and {rate_money(0.126)}/s with native audio ({ten_yes} per 10 seconds). "
        f"Those API figures match our catalog. The cheapest Kling 3.0 rate we track is "
        f"{rate_money(cheapest['usd_per_second'])}/s on {e(cheapest['platform'])}. "
        "How many official app credits a clip uses is not published, so that conversion is not shown."
    )

    body = f"""<p class="small"><a href="{root("/guides/")}">Guides</a> › Kling AI pricing</p>
<h1>{e(PHRASE)}</h1>
<p class="lead">{lead}</p>
<p class="small">Last checked {e(LAST)}. Official membership and API figures were read {e(checked_pt(CHECKED))}. Catalog rows below use the date on each row. See the <a href="{e(model_href)}">Kling 3.0 model page</a> and the <a href="{e(calc_href)}">credit calculator for a 10-second Kling 3.0 clip</a>.</p>

<h2>{e(QUESTION)}</h2>
<p>{e(a_plans)}</p>
<h2>{e(q_plans)}</h2>
<p>The official membership page, opened {e(checked_pt(CHECKED))} without signing in, lists Standard, Pro, Premier, and Ultra+, with Yearly (34% off the listed yearly price), Monthly (12% off list after the first month), and Business tabs. Monthly plans show a one-time first-month offer (the page says it is available once) and then a lower ongoing monthly price. Premier lets you pick 8,000, 18,000, 28,000, or 38,000 credits a month; the page's default Premier tile was 18,000. Yearly plans are billed once a year and grant the listed credits each month for 12 months. A free Basic tier appears in the comparison grid at {usd(0)}. {hf}.</p>
{monthly_table}
<p class="small">Monthly first-month prices are 30% off list, except Premier 8,000 credits, which the payload lists at 29% off ({usd(64.99)} vs {usd(92)} list). Ongoing monthly prices are 12% off list. $ / 100 credits in this table is the ongoing monthly rate, not the first-month rate.</p>
<h3>Yearly official plans</h3>
{yearly_table}
<p class="small">Yearly prices are 34% off the listed yearly total (12× the monthly list). Equivalent / month is the yearly price divided by 12, rounded to the cent. Credits / month are granted each month of the year, not once a year.</p>
<p>The Business tab, from the same page load, listed a Pro-level team plan at {usd(98)} per seat per month (ongoing), or {usd(876)} per seat per year, with 10,000 credits a month per seat and a default of 3 seats. Seat totals were listed from 3 to 15 seats. {hf}.</p>

<h2>Official credit packs</h2>
<p>The same membership page also sells credit packs. Larger packs include bonus credits. Kling's {terms} (effective Oct 10, 2026) say purchased credits are valid for 2 years. These packs are not the official API resource packages.</p>
{pack_table}

<h2>{e(q_credits)}</h2>
<p>{e(a_credits)} Benefits the page does list for paid plans include a generation queue, 1080p/4K video generation, watermark removal, and commercial use of generated content. It also mentions daily free credits for members and, during promotional periods, discounts that use fewer credits on eligible models, without a credits-per-clip table.</p>

<h2>{e(q_api)}</h2>
<p>{e(a_api)}</p>
<p>The official API document bills Kling 3.0 per second of output. A 10-second 720p clip is {ten_no} without native audio and {ten_yes} with native audio. The document also lists other official models, including Kling 4.0, Kling 4.0 Flash, Kling 3.0 Omni, Kling O1, and Kling 2.6. Those models are not in this catalog, so they are not turned into ranked $/s rows here. The dollar figures below are the ones printed on the official table, checked {e(checked_pt(CHECKED))}. {api_src}.</p>
{api_table}

<h2>Cheaper routes we track</h2>
<p>These are the Kling 3.0 rows in our catalog, lowest $/s first. A credit-plan figure is plan price ÷ credits × credits per clip, and it assumes every credit you pay for is used. Unused credits make the real cost higher. Higgsfield links can be affiliate links; they never change this price order. Official API rows are included so you can see which third-party rates beat them.</p>
{cmp_table}
<p>fal also publishes Standard rates of {rate_money(0.084)}/s without audio and {rate_money(0.126)}/s with audio, matching the official 720p API, plus {rate_money(0.154)}/s with voice control, on {src("https://fal.ai/models/fal-ai/kling-video/v3/standard/text-to-video", "fal's Kling 3.0 Standard text-to-video page")}, checked {e(checked_pt(CHECKED))}. Our catalog currently stores fal's Pro rates ({rate_money(0.112)}/s off, {rate_money(0.168)}/s on, and a {rate_money(0.196)}/s voice-control modifier on the Pro row). Replicate is not in our Kling 3.0 catalog, so no Replicate rate is shown.</p>
<p>Related: <a href="{e(cheap_href)}">cheapest rate we track for each model</a> · <a href="{e(hf_href)}">Higgsfield pricing explained</a> · <a href="{e(budget_href)}">project budget calculator</a> · <a href="{e(model_href)}">every Kling 3.0 row on the model page</a>.</p>

<h2>{e(q_cheaper)}</h2>
<p>{e(a_cheaper)}</p>

<h2>{e(q_unknown)}</h2>
<p>{e(a_unknown)}</p>
<p><b>Confirmed {e(checked_pt(CHECKED))} on official Kling pages:</b> Standard, Pro, Premier (four credit tiers), and Ultra+ monthly and yearly prices, first-month and ongoing monthly prices, credits per month, credit packs, the Business seat prices above, and the official API dollar rates for Kling 3.0. The membership page loaded without a login. Purchased-credit validity of 2 years is in the paid-service terms dated Oct 10, 2026.</p>
<p><b>Confirmed in the catalog the same day:</b> every third-party and official API $/s row in the comparison table, each with its vendor URL and checked date.</p>
<p><b>Unknown:</b> how many official app credits a Kling 3.0 or 4.0 clip uses, at any resolution, with or without audio, so an app-plan cost per second is not shown; a regional price, if any, that appears only after sign-in; a Replicate Kling 3.0 rate; and whether official API resource-package units can be mixed with app credits (the two price lists are presented as separate products).</p>
<p class="small">Affiliate links never change this price order.</p>
{g["how_block"]()}
"""

    title = g["page_title"](PHRASE)
    desc = description(g)
    g["guide_page"](PATH, title, desc, body, faqs)
    return PATH
