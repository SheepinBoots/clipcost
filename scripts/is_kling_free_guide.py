import guide_tables
import deal_copy
"""Guide: Is Kling AI free?

Imported by scripts/build_site.py. Catalog $/s figures are rendered from a
price-sorted query of data/prices.json. Official plan and credit-planning
figures come only from static official documents re-read on CHECKED_WHEN
(kling.ai/llms.txt, the API markdown pricing page, and the Jul 28, 2026 blog).
The membership and policy pages are JS-only and produced no saved payload, so
this page does not mark their on-screen wording confirmed.
"""

PATH = "/guides/is-kling-ai-free/"
LABEL = "Is Kling AI free?"
PHRASE = "Is Kling AI free?"
QUESTION = "Is Kling AI free?"
MODEL = "kling-3-0"
MODEL_PATH = "/models/kling-3-0/"
CHECKED = "2026-11-24"
CHECKED_WHEN = "Nov 24, 2026, 7:48–7:50 PM ET (4:48–4:50 PM PT)"
BLOG_DATE = "Jul 28, 2026"

KLING_LLMS = "https://kling.ai/llms.txt"
KLING_API = "https://kling.ai/document-api/pricing/base/video.md"
KLING_PLANS = "https://kling.ai/app/membership/membership-plan"
KLING_BLOG = "https://kling.ai/blog/kling-video-3-0-credit-cost-guide"
HF_PLANS = "https://higgsfield.ai/pricing"
MAG_PLANS = "https://www.magnific.com/pricing"

# Official llms.txt figures, fetched CHECKED_WHEN. Not catalog $/s rows.
OFFICIAL = {
    "basic": 0,
    "standard_first": 6.99,
    "standard_then": 8.80,
    "standard_list": 10.00,
    "standard_year": 79.20,
    "standard_year_list": 120.00,
    "standard_credits": 660,
}

# Official blog (BLOG_DATE), re-read CHECKED_WHEN. Planning figures only.
BLOG_STD_720P_CLIPS = 33
BLOG_4K_CREDITS_PER_S = 30
BLOG_ELEMENT_BASIC = 30
BLOG_ELEMENT_STANDARD = 50

PLATFORM_ORDER_NOTE = "Affiliate links never change this price order."


def _src(g, url, text="source"):
    e = g["e"]
    href, rel = g["outbound"](url)
    return f'<a href="{e(href)}" rel="{rel}" target="_blank">{e(text)}</a>'


def checked_pt(date):
    from timefmt import day_label
    return day_label(date)


def kling_rows(g):
    rows = [
        r for r in g["rows"]
        if r.get("model") == MODEL
        and r.get("usd_per_second") is not None
        and r.get("status") != "discontinued"
    ]
    return sorted(rows, key=lambda r: (float(r["usd_per_second"]), r["id"]))


def _row(rows, rid):
    for r in rows:
        if r["id"] == rid:
            return r
    raise SystemExit(f"{PATH} missing catalog row {rid}")


def _audio_word(g, r):
    a = g["shown_audio"](r)
    return {"with": "with audio", "without": "without audio"}.get(a, "not stated")


def _assumption(r):
    math = (r.get("math") or "").strip()
    if r.get("kind") == "plan":
        lead = "Estimated from credit plan. " if r.get("status") == "estimate" else "From credit plan. "
        text = lead + (math + ". " if math else "") + "Assumes every credit you pay for is used."
        return text
    if math:
        return f"{math}. Billed per second of output, so no credits go unused."
    return "Published rate, billed per second of output."


def _status_label(r):
    if r.get("kind") == "plan" and r.get("status") == "estimate":
        return "estimated from credit plan"
    if r.get("status") == "estimate":
        return "estimated"
    return r.get("status") or "verified"


def _clip5(g, r):
    clip_money = g["clip_money"]
    if r.get("usd_per_clip") is not None:
        return clip_money(r["usd_per_clip"])
    return clip_money(float(r["usd_per_second"]) * 5)


def shown_subset(rows):
    """Cheapest four catalog rows, the cheapest non-Higgsfield row if not already included, and official 720p API rows, in price order."""
    top = list(rows[:4])
    ids = {r["id"] for r in top}
    non_hf = next((r for r in rows if r.get("platform") not in ("Higgsfield", "Higgsfield API") and r["id"] not in ids), None)
    extra = []
    if non_hf:
        extra.append(non_hf)
        ids.add(non_hf["id"])
    for rid in ("r059", "r062"):
        r = _row(rows, rid)
        if r["id"] not in ids:
            extra.append(r)
    return sorted(top + extra, key=lambda r: (float(r["usd_per_second"]), r["id"]))


def blurb(g):
    rows = kling_rows(g)
    cheapest = rows[0]
    rate = g["rate_money"](cheapest["usd_per_second"])
    return (
        "Kling’s official documents list a $0 Basic plan with no monthly credits, "
        "for personal non-commercial use. The cheapest Kling 3.0 rate we track is "
        f"{rate}/s, and the official API rate is also on the page."
    )


def description(g):
    rows = kling_rows(g)
    cheapest = rows[0]
    rate = g["rate_money"](cheapest["usd_per_second"])
    last = g["LAST"]
    text = (
        "Kling AI’s Basic plan is $0 with no monthly credits in official docs, "
        f"and is not for commercial use. Cheapest Kling 3.0 we track: {rate}/s. "
        f"Checked {last}."
    )
    if len(text) > 160:
        raise SystemExit(f"{PATH} meta description is over 160 characters: {len(text)}")
    return text


def render(g):
    e, root, LAST = g["e"], g["root"], g["LAST"]
    rate_money = g["rate_money"]
    cost_money = g["cost_money"]
    shown_resolution = g["shown_resolution"]
    outbound = g["outbound"]

    rows = kling_rows(g)
    if not rows:
        raise SystemExit(f"{PATH} has no Kling 3.0 catalog rows")
    cheapest, nxt = rows[0], rows[1]
    r059, r062 = _row(rows, "r059"), _row(rows, "r062")
    subset = shown_subset(rows)
    non_hf = next(r for r in rows if r.get("platform") not in ("Higgsfield", "Higgsfield API"))

    llms = _src(g, KLING_LLMS, "Kling’s official llms.txt")
    api_src = _src(g, KLING_API, "Kling’s API pricing document")
    blog_src = _src(g, KLING_BLOG, "Kling’s official credit-planning blog")

    bf = deal_copy.hf_bf(g)
    sale_clause = ""
    table_sale = ""
    if bf["live"] and cheapest.get("platform") == "Higgsfield":
        month = deal_copy.plan_month(g, cheapest.get("plan")) or deal_copy.price_after(bf, cheapest.get("plan") or "")
        end = bf.get("end_long") or bf.get("end")
        if month is not None and end:
            sale_clause = (
                f", using a Higgsfield Black Friday plan price of {deal_copy.money(month)} a month "
                f"billed yearly that Higgsfield says ends {end}"
            )
            table_sale = f" Black Friday plan price, ends {end}."

    def row_src(r):
        href, rel = outbound(r["source_url"])
        return (
            f"Checked {e(checked_pt(r.get('checked')))}. "
            f'<a href="{e(href)}" rel="{rel}" target="_blank">source</a>.'
        )

    def trow(r):
        href, rel = outbound(r["source_url"])
        where = f'<a href="{e(href)}" rel="{rel}" target="_blank">{e(r["platform"])}</a>'
        how = _assumption(r)
        if table_sale and r["id"] == cheapest["id"] and "Black Friday" not in how:
            how += table_sale
        return (
            "<tr>"
            "<td>Kling 3.0</td>"
            f"<td>{where}</td>"
            f"<td>{e(r.get('variant') or 'Kling 3.0')}</td>"
            f"<td>{e(g['shown_tier'](r))}</td>"
            f"<td>{e(shown_resolution(r))}</td>"
            f"<td>{e(_audio_word(g, r))}</td>"
            f"<td>{e(rate_money(r['usd_per_second']))}</td>"
            f"<td>{e(_clip5(g, r))}</td>"
            f"<td>{e(_status_label(r))}</td>"
            f"<td>{e(how)}</td>"
            f"<td>{row_src(r)}</td>"
            "</tr>"
        )

    table_rows = "\n".join(trow(r) for r in subset)
    price_table = (
        '<div class="tblwrap" id="prices">\n<table>\n<thead>\n<tr>\n'
        "  <th>Model</th><th>Where</th><th>Variant / plan</th><th>Plan tier</th>\n"
        "  <th>Resolution</th><th>Audio</th><th>$ / sec</th><th>Per 5s clip</th><th>Status</th>\n"
        "  <th>How we got it</th><th>Source</th>\n"
        "</tr>\n</thead>\n<tbody>\n"
        f"{table_rows}\n"
        "</tbody>\n</table>\n</div>"
    )

    o = OFFICIAL
    a_free = (
        f"Partly. {e(checked_pt(CHECKED))}, Kling’s official llms.txt, which cites the membership page as its source, "
        f"lists a Basic plan at $0 with no monthly credits, for personal non-commercial use. "
        f"The same reading of that file lists paid Standard, Pro, Premier, and Ultra plans. "
        f"The official credit-planning blog dated {BLOG_DATE}, re-read {e(checked_pt(CHECKED))}, also lists Basic at $0 "
        f"with no monthly credits and says generated content on Basic is not for commercial use. "
        f"The membership page itself is a JavaScript app and produced no saved payload on this check, so this page does not treat its on-screen wording as confirmed. "
        f"Sources: Kling’s official llms.txt, fetched {CHECKED_WHEN}, and Kling’s official credit-planning blog, dated {BLOG_DATE}."
    )
    a_include = (
        f"Official llms.txt, fetched {CHECKED_WHEN}, lists Basic at {cost_money(o['basic'])} with no monthly credits. "
        f"Standard, the cheapest official paid plan in that file, is {cost_money(o['standard_first'])} for the first month, "
        f"then {cost_money(o['standard_then'])} a month (list {cost_money(o['standard_list'])}), "
        f"or {cost_money(o['standard_year'])} a year (list {cost_money(o['standard_year_list'])}), with {o['standard_credits']} credits a month. "
        f"The official blog dated {BLOG_DATE} lists the same $0 Basic plan, no monthly credits, and element creation quantity "
        f"{BLOG_ELEMENT_BASIC} on Basic versus {BLOG_ELEMENT_STANDARD} on Standard. It lists 1080p video generation, "
        f"brand watermark removal, image upscaling, video extension, fast-track generation, and commercial use as Standard benefits. "
        f"Those blog figures are dated {BLOG_DATE}; confirm the live membership page before you buy. "
        f"Sources: Kling’s official llms.txt · Kling’s official credit-planning blog."
    )
    a_how_many = (
        f"Official llms.txt lists no monthly credits on Basic, so this page does not turn a recurring free allowance into a clip count. "
        f"Kling does publish dated planning figures on its official blog ({BLOG_DATE}): Standard’s {o['standard_credits']} monthly credits are described as "
        f"“{o['standard_credits']} images / {BLOG_STD_720P_CLIPS} 720p videos,” and native 4K output for the Kling VIDEO 3.0 series is described as "
        f"{BLOG_4K_CREDITS_PER_S} credits per second, as a planning reference to confirm on the live generation panel. "
        f"This page does not convert those blog figures into a VidFare cost per second, and it does not invent a free-clip count. "
        f"The same llms.txt file says credit use varies by model, resolution, duration, audio, and generation mode, and that failed generations do not consume credits. "
        f"Sources: Kling’s official llms.txt, fetched {CHECKED_WHEN}; Kling’s official credit-planning blog, dated {BLOG_DATE}."
    )
    a_commercial = (
        f"Official llms.txt describes Basic as being for personal non-commercial use, and lists commercial use on Standard. "
        f"The official blog dated {BLOG_DATE} says generated content on Basic is not for commercial use, and lists commercial use and brand watermark removal as Standard benefits. "
        f"The Terms of Paid Service and Credits Policy pages are JavaScript apps and produced no saved payload on this check, so this page does not quote them. "
        f"Sources: Kling’s official llms.txt · Kling’s official credit-planning blog."
    )
    a_api = (
        f"No free tier is listed. Kling’s official API pricing document, checked {e(checked_pt(CHECKED))}, does not mention free trial units. "
        f"It bills Kling 3.0 per second of output: {rate_money(r059['usd_per_second'])} per second at 720p without native audio and "
        f"{rate_money(r062['usd_per_second'])} per second with native audio. A 5-second 720p clip is {_clip5(g, r059)} without audio and {_clip5(g, r062)} with audio. "
        f"These are published rates, not plan estimates. Source: Kling’s official API pricing document."
    )
    a_cheap = (
        f"As of {e(checked_pt(cheapest.get('checked') or CHECKED))}, the cheapest Kling 3.0 rate we track is "
        f"{rate_money(cheapest['usd_per_second'])} per second on {cheapest['platform']}, "
        f"plan tier {guide_tables.plan_label(cheapest)}, {shown_resolution(cheapest)}, {_audio_word(g, cheapest)}, "
        f"{_status_label(cheapest)}, priced at 5 seconds: about {_clip5(g, cheapest)} for a 5s clip. "
        f"It assumes every credit you pay for is used{sale_clause}. "
        f"The next-cheapest catalog row is {rate_money(nxt['usd_per_second'])} per second on {nxt['platform']}, "
        f"plan tier {guide_tables.plan_label(nxt)}, {shown_resolution(nxt)}, {_audio_word(g, nxt)}, "
        f"{_status_label(nxt)}, about {_clip5(g, nxt)} for a 5s clip, checked {checked_pt(nxt.get('checked'))}. "
        f"The cheapest non-Higgsfield row we track is {rate_money(non_hf['usd_per_second'])} per second on {non_hf['platform']}, "
        f"plan tier {guide_tables.plan_label(non_hf)}, {shown_resolution(non_hf)}, checked {checked_pt(non_hf.get('checked'))}. "
        f"Both of those catalog rows are cheaper per second than Kling’s own API at {rate_money(r059['usd_per_second'])} per second for 720p without audio, but only if you use the credits. "
        f"Kling’s own app plans are not converted to dollars per second here, because this page treats the blog’s clip estimates as planning figures, not as a published list price."
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
        (QUESTION, a_free),
        ("What does the free Basic plan include?", a_include),
        ("How many free Kling videos can you make?", a_how_many),
        ("Can you use free Kling videos commercially?", a_commercial),
        ("Is the Kling API free?", a_api),
        ("What is the cheapest paid way to use Kling 3.0?", a_cheap),
        ("How do we calculate this?", a_how),
    ]
    for _name, _text in faqs:
        low = _text.lower()
        if "subscribe" in low or "newsletter" in low:
            raise SystemExit(f"{PATH} FAQ text contains newsletter wording")

    takeaways = (
        '<div class="card" id="takeaways">\n'
        "<h2>Key takeaways</h2>\n<ul>\n"
        f"<li><b>There is a $0 plan in official documents.</b> Basic is {e(cost_money(o['basic']))} on Kling’s official llms.txt, with no monthly credits, fetched {e(checked_pt(CHECKED))}.</li>\n"
        f"<li><b>Free output is not for commercial use.</b> Official llms.txt describes Basic as personal non-commercial use. The official blog dated {BLOG_DATE} says the same, and lists commercial use and brand watermark removal on Standard.</li>\n"
        f"<li><b>Cheapest official paid plan in those documents.</b> Standard is {e(cost_money(o['standard_first']))} for the first month, then {e(cost_money(o['standard_then']))}/month (list {e(cost_money(o['standard_list']))}), or {e(cost_money(o['standard_year']))}/year (list {e(cost_money(o['standard_year_list']))}), with {o['standard_credits']} credits a month, fetched {e(checked_pt(CHECKED))}.</li>\n"
        f"<li><b>Cheapest Kling 3.0 per second we track.</b> {e(rate_money(cheapest['usd_per_second']))}/s on {e(cheapest['platform'])}, {e(guide_tables.plan_label(cheapest))}, {e(shown_resolution(cheapest))}, {e(_audio_word(g, cheapest))}, {e(_status_label(cheapest))}, checked {e(checked_pt(cheapest.get('checked')))}. It assumes every credit you pay for is used{e(sale_clause)}.</li>\n"
        f"<li><b>No free API tier is listed.</b> The official API is {e(rate_money(r059['usd_per_second']))}/s at 720p without audio and {e(rate_money(r062['usd_per_second']))}/s with audio, checked {e(checked_pt(CHECKED))}.</li>\n"
        "</ul>\n</div>"
    )

    compare = (
        '<div class="tblwrap" id="basic-vs-standard">\n<table>\n<thead>\n'
        "<tr><th>Benefit</th><th>Basic</th><th>Standard</th><th>Source</th></tr>\n"
        "</thead>\n<tbody>\n"
        f"<tr><td>Price</td><td>{e(cost_money(o['basic']))}</td><td>{e(cost_money(o['standard_first']))} first month, then {e(cost_money(o['standard_then']))}/month (list {e(cost_money(o['standard_list']))}), or {e(cost_money(o['standard_year']))}/year (list {e(cost_money(o['standard_year_list']))})</td><td>Fetched {e(checked_pt(CHECKED))}. {llms}.</td></tr>\n"
        f"<tr><td>Monthly plan credits</td><td>None</td><td>{o['standard_credits']} credits/month</td><td>Fetched {e(checked_pt(CHECKED))}. {llms}.</td></tr>\n"
        f"<tr><td>Commercial use</td><td>Not for commercial use (personal non-commercial)</td><td>Listed as yes</td><td>Fetched {e(checked_pt(CHECKED))}. {llms}. The official blog dated {BLOG_DATE} agrees ({blog_src}).</td></tr>\n"
        f"<tr><td>Element creation quantity</td><td>{BLOG_ELEMENT_BASIC}</td><td>{BLOG_ELEMENT_STANDARD}</td><td>Official blog dated {BLOG_DATE}, re-read {e(checked_pt(CHECKED))}. {blog_src}.</td></tr>\n"
        f"<tr><td>1080p video, watermark removal, image upscaling, video extension, fast-track</td><td>Not listed as included in the {BLOG_DATE} blog</td><td>Listed as included</td><td>Official blog dated {BLOG_DATE}, re-read {e(checked_pt(CHECKED))}. {blog_src}.</td></tr>\n"
        "</tbody>\n</table>\n</div>\n"
        '<p class="small">These official-plan facts come from static documents, not from a saved membership-page payload. The membership page is a JavaScript app and was not marked confirmed. Which models Basic can use, and a maximum resolution below 1080p, are not stated in llms.txt.</p>'
    )

    model_href = root(MODEL_PATH)
    cheap_href = root("/guides/cheapest-kling-3-0/")
    kling_guide = root("/guides/kling-ai-pricing/")
    free_href = root("/guides/free-ai-video-generators/")
    nosign_href = root("/guides/free-ai-video-generator-no-sign-up/")
    vs_href = root("/guides/higgsfield-vs-kling/")
    deals_href = root("/deals/")

    lead = (
        f"Partly. Official Kling documents fetched {CHECKED_WHEN} list a Basic plan at {cost_money(o['basic'])} "
        f"with no monthly credits, for personal non-commercial use, so this page does not turn a recurring free allowance into a clip count. "
        f"Kling’s official blog dated {BLOG_DATE} publishes planning figures for paid Standard and 4K credits (see below), which this page does not convert into a VidFare cost per second. "
        f"If you pay, the cheapest Kling 3.0 rate we track is {rate_money(cheapest['usd_per_second'])} per second on {cheapest['platform']}’s "
        f"{guide_tables.plan_label(cheapest)} plan at {shown_resolution(cheapest)}, {_audio_word(g, cheapest)}, "
        f"{_status_label(cheapest)}: about {_clip5(g, cheapest)} for a 5s clip, assuming every credit you pay for is used "
        f"(checked {checked_pt(cheapest.get('checked'))}{sale_clause}). "
        f"The next-cheapest catalog row is {rate_money(nxt['usd_per_second'])} per second on {nxt['platform']}, "
        f"{guide_tables.plan_label(nxt)}, {shown_resolution(nxt)} (checked {checked_pt(nxt.get('checked'))}). "
        f"Kling’s own API charges {rate_money(r059['usd_per_second'])} per second at 720p without audio, or {_clip5(g, r059)} for a 5s clip (checked {checked_pt(CHECKED)})."
    )

    confirmed = (
        "<h2>What is confirmed, and what is not?</h2>\n<ul>\n"
        f"  <li><b>Confirmed {CHECKED_WHEN} in {llms}:</b> Basic at {cost_money(o['basic'])} with no monthly credits, for personal non-commercial use; Standard’s first-month, ongoing, list, and yearly prices and {o['standard_credits']} credits a month; credits deducted on generation and refunded if a generation fails; standard credit packs at $10 for 660 credits ($1 for 66 credits).</li>\n"
        f"  <li><b>Confirmed from {blog_src}, dated {BLOG_DATE}, re-read {e(checked_pt(CHECKED))}:</b> Basic at $0 with no monthly credits and no commercial use; element creation {BLOG_ELEMENT_BASIC} vs {BLOG_ELEMENT_STANDARD}; Standard planning figures of “{o['standard_credits']} images / {BLOG_STD_720P_CLIPS} 720p videos”; 4K planning reference of {BLOG_4K_CREDITS_PER_S} credits per second for the Kling VIDEO 3.0 series, to confirm on the live generation panel; Standard benefits including 1080p video, brand watermark removal, and commercial use.</li>\n"
        f"  <li><b>Confirmed {e(checked_pt(CHECKED))} in {api_src}:</b> the Kling 3.0 720p rates above, and no mention of free trial units.</li>\n"
        "  <li><b>Catalog rows:</b> every dollar-per-second figure in the table is a current <code>data/prices.json</code> row, sorted cheapest first, each with its own checked date and source.</li>\n"
        "  <li><b>Not confirmed on this check (no saved membership or policy payload):</b> wording on the JavaScript membership page, including any limited-time sale or a monthly free-credit claim for accounts without a paid plan; the Terms of Paid Service; and the Credits Policy. Those claims are omitted rather than guessed.</li>\n"
        "</ul>"
    )

    body = (
        f'<p class="small"><a href="{root("/guides/")}">Guides</a> › Is Kling AI free?</p>\n'
        f"<h1>{e(PHRASE)}</h1>\n"
        f'<p class="lead">{lead}</p>\n'
        f'<p class="small">Last checked {e(LAST)}. Official static pages were read {CHECKED_WHEN}, without signing in. Catalog rows use the date on each row.</p>\n'
        f"{takeaways}\n\n"
        f"<h2>{e(QUESTION)}</h2>\n"
        f"<p>{e(a_free)}</p>\n"
        f'<p class="small">Looking for tools you can try without an account? See <a href="{e(nosign_href)}">free AI video generators with no sign-up</a>.</p>\n\n'
        "<h2>What does the free Basic plan include?</h2>\n"
        f"<p>{e(a_include)}</p>\n"
        f"{compare}\n\n"
        "<h2>How many free Kling videos can you make?</h2>\n"
        f"<p>{e(a_how_many)}</p>\n\n"
        "<h2>Can you use free Kling videos commercially?</h2>\n"
        f"<p>{e(a_commercial)}</p>\n\n"
        "<h2>Is the Kling API free?</h2>\n"
        f"<p>{e(a_api)}</p>\n\n"
        "<h2>What is the cheapest paid way to use Kling 3.0?</h2>\n"
        f"<p>{e(a_cheap)}</p>\n"
        f"{price_table}\n"
        f'<p class="small">This table shows the four cheapest Kling 3.0 catalog rows, the cheapest non-Higgsfield catalog row, and Kling’s own 720p API rows, in price order from a sort of current <code>data/prices.json</code> rows. Every other seller, resolution, and audio option is on the <a href="{e(model_href)}">Kling 3.0 model page</a> and in <a href="{e(cheap_href)}">Kling 3.0 cost per second</a>. Higgsfield links on this page are affiliate links; they never change the order of the rows. {PLATFORM_ORDER_NOTE}</p>\n'
        f'<p class="small">Related: <a href="{e(kling_guide)}">Kling AI pricing and credits</a> · <a href="{e(free_href)}">free AI video generators compared</a> · <a href="{e(vs_href)}">Higgsfield vs Kling</a> · <a href="{e(deals_href)}">current AI video deals</a>.</p>\n\n'
        f"{confirmed}\n"
        f'{g["how_block"]()}\n'
    )

    if "sora" in body.lower() or "sora" in description(g).lower() or "sora" in PHRASE.lower():
        raise SystemExit(f"{PATH} source would name the banned model")
    title = g["page_title"](PHRASE)
    if len(title) > 60:
        raise SystemExit(f"{PATH} title is {len(title)} characters: {title}")
    desc = description(g)
    g["guide_page"](PATH, title, desc, body, faqs)
    return PATH
