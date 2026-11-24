"""Guide: Higgsfield vs Kling.

Imported by scripts/build_site.py. Catalog rows were last fully checked
on 2026-11-17. Official Kling plan prices are carried from the Nov 14,
2026 membership-page check in the Kling pricing guide. This page never
names Sora.
"""

PATH = "/guides/higgsfield-vs-kling/"
LABEL = "Higgsfield vs Kling"
PHRASE = "Higgsfield vs Kling"
QUESTION = "Is Kling cheaper on Higgsfield or on the official site?"
CHECKED = "2026-11-17"
CHECKED_WHEN = "Nov 17, 2026, 3:50–3:53 PM ET (12:50–12:53 PM PT)"
KLING_PLANS_CHECKED = "2026-11-14"

HF_PLANS = "https://higgsfield.ai/pricing"
HF_API = "https://open.higgsfield.ai/pricing"
KLING_PLANS = "https://kling.ai/app/membership/membership-plan"
KLING_API = "https://kling.ai/document-api/pricing/base/video.md"
KLING_GUIDE = "/guides/kling-ai-pricing/"
HF_PRICING = "/guides/higgsfield-pricing/"
HF_WORTH = "/guides/is-higgsfield-worth-it/"
ALTS = "/guides/higgsfield-alternatives/"
VS_RUNWAY = "/guides/higgsfield-vs-runway/"
FAL_GUIDE = "/guides/fal-ai-pricing/"

# Like-for-like 720p no-audio where we have it, then a wider catalog set.
ROWS_720P = ("r111", "r007", "r059", "r034", "r015")
ROWS_API = ("r059", "r060", "r064", "r062", "r065", "r063", "r061")
ROWS_HF = ("r111", "r115", "r109", "r113")


def _src(g, url, text="source"):
    e = g["e"]
    href, rel = g["outbound"](url)
    return f'<a href="{e(href)}" rel="{rel}" target="_blank">{e(text)}</a>'


def _row_by_id(g, rid):
    for r in g["rows"]:
        if r["id"] == rid:
            return r
    raise SystemExit(f"{PATH} missing catalog row {rid}")


def checked_pt(date):
    """Date-only check label, e.g. 'Nov 23, 2026'. A date carries no clock, so no zone."""
    from timefmt import day_label
    return day_label(date)


def blurb(g):
    return (
        "Kling 3.0 on Higgsfield versus the official API and plans: cost per "
        "second, credits, and the limits we could verify."
    )


def description(g):
    text = (
        "Higgsfield vs Kling: Kling 3.0 on Higgsfield versus the official API "
        "and plans, with cost per second. Last checked Nov 17, 2026."
    )
    if len(text) > 160:
        raise SystemExit(f"{PATH} meta description is over 160 characters: {len(text)}")
    return text


import deal_copy  # noqa: E402


def render(g):
    _pa = deal_copy.money(deal_copy.plan_month(g, "hf-plus-annual"))
    _ua = deal_copy.money(deal_copy.plan_month(g, "hf-ultra-annual"))
    _P = g["plans"]
    _sm, _sc = deal_copy.money(_P["hf-starter"]["usd_month"]), f'{_P["hf-starter"]["credits_month"]:,}'
    _pm, _pc = deal_copy.money(_P["hf-plus-monthly"]["usd_month"]), f'{_P["hf-plus-annual"]["credits_month"]:,}'
    _um, _uc = deal_copy.money(_P["hf-ultra-monthly"]["usd_month"]), f'{_P["hf-ultra-annual"]["credits_month"]:,}'
    _hf_checked = max(_P[k]["checked"] for k in ("hf-starter", "hf-plus-monthly", "hf-plus-annual", "hf-ultra-monthly", "hf-ultra-annual"))
    _sale = " (Black Friday sale price until " + deal_copy.hf_bf(g)["end"] + ")" if deal_copy.hf_bf(g)["live"] else ""
    e, root, LAST = g["e"], g["root"], g["LAST"]
    rate_money = g["rate_money"]
    shown_tier = g["shown_tier"]
    shown_resolution = g["shown_resolution"]
    audio_phrase = g["audio_phrase"]
    assumption_html = g["assumption_html"]
    plat_link = g["plat_link"]
    tag = g["tag"]
    dates = [CHECKED, LAST, KLING_PLANS_CHECKED]
    g["SITEMAP_LASTMOD"][PATH] = max(dates)

    def src(url, text="source"):
        return _src(g, url, text)

    def row_by(rid):
        return _row_by_id(g, rid)

    hf_src = src(HF_PLANS, "Higgsfield’s pricing page")
    hf_api_src = src(HF_API, "Higgsfield API pricing")
    kling_plans = src(KLING_PLANS, "Kling membership plans")
    kling_api = src(KLING_API, "official Kling API pricing")
    kling_guide = root(KLING_GUIDE)
    hf_price = root(HF_PRICING)
    hf_worth = root(HF_WORTH)
    alts = root(ALTS)
    vs_runway = root(VS_RUNWAY)
    fal_href = root(FAL_GUIDE)
    kling_model = root("/models/kling-3-0/")
    calc = root("/calculator/?model=kling-3-0&seconds=5")

    r111 = row_by("r111")
    r059 = row_by("r059")
    r007 = row_by("r007")
    r062 = row_by("r062")

    def catalog_table(row_ids, table_id):
        head = (
            "<thead><tr><th>Where</th><th>Variant</th><th>Tier</th>"
            "<th>Res</th><th>Audio</th><th>$/s</th><th>Status</th><th>Source</th></tr></thead>"
        )
        body_rows = []
        for rid in row_ids:
            r = row_by(rid)
            href, rel = g["outbound"](r["source_url"])
            source = (
                f'<a href="{e(href)}" rel="{rel}" target="_blank">pricing page</a>'
                f' · {e(r.get("checked") or "")}'
                f'{assumption_html(r)}'
            )
            if (r.get("math") or "").strip() or (r.get("note") or "").strip():
                bits = []
                if (r.get("math") or "").strip():
                    bits.append(e(r["math"].strip()))
                if (r.get("note") or "").strip():
                    bits.append(e(r["note"].strip()))
                source = (
                    f'<details class="src"><summary>source</summary>'
                    f'<div class="math">{" ".join(bits)} {source}</div></details>'
                )
            body_rows.append(
                "<tr>"
                f'<td>{plat_link(r["platform"], r["source_url"])}</td>'
                f'<td>{e(r["variant"])}</td>'
                f'<td>{e(shown_tier(r))}</td>'
                f'<td>{e(shown_resolution(r))}</td>'
                f'<td>{e(audio_phrase(r))}</td>'
                f'<td class="num">{rate_money(r["usd_per_second"])}</td>'
                f'<td>{tag(r)} <span class="small">{e(rid)}</span></td>'
                f"<td>{source}</td>"
                "</tr>"
            )
        return (
            f'<div class="tblwrap" id="{e(table_id)}"><table>{head}'
            f'<tbody>{"".join(body_rows)}</tbody></table></div>'
        )

    a_q = (
        f"For Kling 3.0, Higgsfield’s cheapest catalog estimate is "
        f"{rate_money(r111['usd_per_second'])}/s at 720p on Ultra (annual), using about "
        f"7.5 credits per 5-second clip and assuming every paid credit is used. Audio is "
        f"not stated on that row. The official Kling API is {rate_money(r059['usd_per_second'])}/s "
        f"at 720p without audio, or {rate_money(r062['usd_per_second'])}/s at 720p with audio. "
        f"Official app-plan cost per second is unknown, because Kling does not publish how "
        f"many credits a clip uses. Higgsfield’s API “from” list price is "
        f"{rate_money(r007['usd_per_second'])}/s; the cheapest mode’s resolution is not "
        f"stated on that list. Affiliate links never change this price order."
    )
    a_how = (
        "This page compares Kling 3.0 bought on Higgsfield with Kling bought direct. "
        "A Higgsfield credit-plan figure uses the official (or official-estimate) credits "
        "per clip and the plan’s dollars and credits, and it holds only if you use the "
        "credits you pay for. Official API rows are published dollar rates per second of "
        "output. Official app plans are shown as dollars and credits per month, not as "
        "$/s, when credits per clip are unpublished."
    )
    a_plans = (
        f"On {checked_pt(KLING_PLANS_CHECKED)}, the official membership page listed a $0 "
        f"Basic plan with no monthly credits, then Standard, Pro, Premier, and Ultra+. "
        f"Standard was $6.99 for the first month, then $8.80 a month (list $10), with 660 "
        f"credits a month. Yearly Standard was $79.20 (list $120) and grants 660 credits "
        f"each month for 12 months. Premier lets you pick 8,000, 18,000, 28,000, or 38,000 "
        f"credits a month. Those membership figures were not re-opened on Nov 17, 2026; see "
        f"Kling AI pricing and credits for the full tables. Higgsfield’s catalog plans, "
        f"checked {checked_pt(_hf_checked)}, are Starter {_sm} a month for {_sc} credits, Plus "
        f"{_pm} monthly or {_pa} a month billed annually for {_pc} credits, and Ultra {_um} "
        f"monthly or {_ua} a month billed annually for {_uc} credits{_sale}."
    )
    a_best = (
        "Higgsfield Ultra (annual) is best for the lowest Kling 3.0 catalog rate we can "
        "show at 720p, if you use every paid credit. It is not for a published official "
        "app-plan $/s, because that conversion is unknown, or for buyers who only want "
        "the official Kling site and API. The official Kling API is best for a published "
        "pay-as-you-go rate with a stated resolution and audio flag. It is not the "
        "cheapest catalog route for Kling 3.0 at 720p. No line is given for official "
        "Standard or Premier cost per second."
    )
    a_unknown = (
        f"Confirmed {checked_pt(CHECKED)} in the catalog: Higgsfield Ultra (annual) and "
        f"other plan estimates for Kling 3.0, the Higgsfield API “from” list price, "
        f"official Kling API dollar rates, and the fal and Runway API rows in the tables. "
        f"Confirmed {checked_pt(KLING_PLANS_CHECKED)} on the official membership page: "
        f"Basic, Standard, Pro, Premier, and Ultra+ prices and monthly credits, including "
        f"the first-month Standard offer. The catalog note on the cheapest Higgsfield "
        f"Kling 3.0 row also records a 7-day unlimited Kling 3.0 window on Plus and Ultra; "
        f"this page does not treat that window as $0/s, and when the window starts is "
        f"unknown. Unknown: how many official app credits a Kling 3.0 clip uses, at any "
        f"resolution, with or without audio; a Replicate Kling 3.0 rate; and the resolution "
        f"of Higgsfield API’s cheapest “from” mode."
    )

    faqs = [
        (QUESTION, a_q),
        ("How does this comparison work?", a_how),
        ("What do official Kling plans and Higgsfield plans cost?", a_plans),
        ("Which option is best for each use?", a_best),
        ("What is confirmed, and what is not?", a_unknown),
    ]
    for q, a in faqs:
        raw = (q + " " + a).lower()
        for bad in ("subscribe", "newsletter", "buttondown"):
            if bad in raw:
                raise SystemExit(f"{PATH} FAQ text contains {bad}")

    lead = (
        f"{e(a_q)} Official Kling membership prices below are from "
        f"{e(checked_pt(KLING_PLANS_CHECKED))}. Catalog rows were checked {e(checked_pt(CHECKED))}. "
        f"Related: <a href=\"{e(kling_guide)}\">Kling AI pricing and credits</a> · "
        f"<a href=\"{e(hf_price)}\">Higgsfield pricing explained</a> · "
        f"<a href=\"{e(hf_worth)}\">Is Higgsfield worth it?</a> · "
        f"<a href=\"{e(alts)}\">Higgsfield alternatives</a> · "
        f"<a href=\"{e(vs_runway)}\">Higgsfield vs Runway</a> · "
        f"<a href=\"{e(fal_href)}\">fal pricing vs Replicate, WaveSpeed, and Runware</a>."
    )

    takeaways = f"""<div class="card" id="takeaways">
<h2>Key takeaways</h2>
<ul>
<li><b>Higgsfield’s 720p estimate is lower than the official API.</b> Ultra (annual) is {rate_money(r111['usd_per_second'])}/s at 720p, audio not stated, if you use every paid credit. The official API is {rate_money(r059['usd_per_second'])}/s at 720p without audio.</li>
<li><b>Official app $/s is unknown.</b> The membership page lists credits per month, but not credits per Kling 3.0 clip.</li>
<li><b>Higgsfield API is a separate route.</b> The published “from” list price is {rate_money(r007['usd_per_second'])}/s; the cheapest mode’s resolution is not stated.</li>
<li><b>A 7-day unlimited Kling 3.0 window</b> is noted on Plus and Ultra in the catalog. This page does not treat that window as $0/s.</li>
<li><b>Affiliate links never change this price order.</b></li>
</ul>
</div>"""

    next_steps = f"""<div class="card" id="next-steps">
<h2>What to do next</h2>
<ul>
<li><b>Check the vendor page.</b> Confirm the current rates on {hf_src}, {kling_plans}, or {kling_api} before you buy.</li>
<li><b>Try the calculator.</b> Put your clip length into the <a href="{e(calc)}">credit calculator for Kling 3.0 at 5 seconds</a>.</li>
<li><b>Open the model page.</b> Every current Kling 3.0 rate, with its source and date: <a href="{e(kling_model)}">Kling 3.0</a>.</li>
</ul>
</div>"""

    body = f"""<p class="small"><a href="{root("/guides/")}">Guides</a> › Higgsfield vs Kling</p>
<h1>{e(PHRASE)}</h1>
<p class="lead">{lead}</p>
<p class="small">Last checked {e(LAST)}. Catalog rows use the date on each row. Official Kling plan prices are from {e(checked_pt(KLING_PLANS_CHECKED))}. Non-catalog notes on this page were prepared {e(CHECKED_WHEN)}. Affiliate links never change this price order. Every dollar-per-second figure below states its usage assumption, tier, resolution, and audio.</p>
{takeaways}

<h2>{e(QUESTION)}</h2>
<p>{e(a_q)}</p>

<h2>How does this comparison work?</h2>
<p>{e(a_how)}</p>

<h2>Kling 3.0 at 720p, or the closest published row</h2>
<p>Lowest catalog $/s first. The official API row is 720p without audio. Higgsfield’s cheapest plan row is 720p, audio not stated. Higgsfield API’s “from” row does not state the cheapest mode’s resolution. Runway API and fal rows are included so you can see other catalog routes for the same model.</p>
{catalog_table(ROWS_720P, "kling-720p-table")}

<h2>Official Kling API rates</h2>
<p>Published dollar rates from {kling_api}, checked {e(checked_pt(CHECKED))} in the catalog.</p>
{catalog_table(ROWS_API, "kling-api-table")}

<h2>Higgsfield plan estimates for Kling 3.0</h2>
<p>These credit-plan figures assume you use every paid credit. The cheapest 720p and 1080p Ultra (annual) estimates, plus two higher-cost Ultra rows, are shown so the spread is visible. Higgsfield labels some credit figures with a tilde; those rows are estimates.</p>
{catalog_table(ROWS_HF, "kling-hf-table")}
<p>{hf_api_src} is a pay-as-you-go list, not the same as a monthly plan.</p>

<h2>What do official Kling plans and Higgsfield plans cost?</h2>
<p>{e(a_plans)} Full official tables: <a href="{e(kling_guide)}">Kling AI pricing and credits</a>. Higgsfield plan math: <a href="{e(hf_price)}">Higgsfield pricing explained</a>.</p>

<h2>Which option is best for each use?</h2>
<p>{e(a_best)}</p>
<ul>
<li><b>Higgsfield Ultra (annual).</b> Best for: the lowest Kling 3.0 catalog rate we can show at 720p, if you use every paid credit. Not for: a published official app-plan $/s, or for staying only on kling.ai. {hf_src}.</li>
<li><b>Official Kling API.</b> Best for: a published pay-as-you-go rate with a stated resolution and audio flag. Not for: the lowest catalog $/s at 720p. {kling_api}.</li>
</ul>
<p>No line given for official Standard, Pro, Premier, or Ultra+ cost per second, because credits per clip are not published.</p>

<h2>What is confirmed, and what is not?</h2>
<p>{e(a_unknown)}</p>
<p class="small">Affiliate links never change this price order.</p>
{next_steps}
{g["how_block"]()}
"""

    if "sora" in body.lower() or "sora" in description(g).lower() or "sora" in PHRASE.lower():
        raise SystemExit(f"{PATH} source would name Sora")

    title = g["page_title"](PHRASE)
    desc = description(g)
    g["guide_page"](PATH, title, desc, body, faqs)
    return PATH
