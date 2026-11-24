"""Guide: Higgsfield vs Runway.

Imported by scripts/build_site.py. Catalog rows were last fully checked
on 2026-11-17. Runway plan cards were re-read the same day. The legacy
Unlimited-to-Max facts are from Runway’s help center as last fully read
on 2026-11-15. This page never names Sora.
"""

PATH = "/guides/higgsfield-vs-runway/"
LABEL = "Higgsfield vs Runway"
PHRASE = "Higgsfield vs Runway"
QUESTION = "Is Runway cheaper than Higgsfield per second?"
CHECKED = "2026-11-17"
CHECKED_WHEN = "Nov 17, 2026, 3:50–3:53 PM ET (12:50–12:53 PM PT)"
UNLIMITED_CHECKED = "2026-11-15"

HF_PLANS = "https://higgsfield.ai/pricing"
RUNWAY_PLANS = "https://runway.com/pricing"
RUNWAY_API = "https://docs.dev.runwayml.com/guides/pricing/"
HELP_UNLIMITED_TO_MAX = "https://help.runwayml.com/hc/en-us/articles/52068047744019-Unlimited-plan-is-switching-to-Max"
KREA_PLANS = "https://www.krea.ai/pricing"
RUNWAY_GUIDE = "/guides/runway-pricing/"
HF_PRICING = "/guides/higgsfield-pricing/"
HF_WORTH = "/guides/is-higgsfield-worth-it/"
ALTS = "/guides/higgsfield-alternatives/"
VS_KLING = "/guides/higgsfield-vs-kling/"
FAL_GUIDE = "/guides/fal-ai-pricing/"
BEST = "/guides/best-ai-video-generator/"

ROWS_OVERALL = ("r096", "r055", "r146", "r047", "r045")
ROWS_RUNWAY = ("r047", "r046", "r055", "r034", "r045", "r050", "r039")
ROWS_KREA_RW = ("r155", "r157", "r156", "r046")
ROWS_VEO = ("r146", "r127", "r045")


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


def blurb(g):
    return (
        "Higgsfield vs Runway on plan and API rates, with a short Krea vs "
        "Runway note. Unlimited is not sold to new buyers."
    )


def description(g):
    text = (
        "Higgsfield vs Runway: plan and API rates, plus a short Krea vs Runway "
        "note. Unlimited is not sold to new buyers. Last checked Nov 17, 2026."
    )
    if len(text) > 160:
        raise SystemExit(f"{PATH} meta description is over 160 characters: {len(text)}")
    return text


import deal_copy  # noqa: E402


def render(g):
    _pa = deal_copy.money(deal_copy.plan_month(g, "hf-plus-annual"))
    _ua = deal_copy.money(deal_copy.plan_month(g, "hf-ultra-annual"))
    _sale = " (Black Friday sale price until " + deal_copy.hf_bf(g)["end"] + ")" if deal_copy.hf_bf(g)["live"] else ""
    e, root, LAST = g["e"], g["root"], g["LAST"]
    rate_money = g["rate_money"]
    shown_tier = g["shown_tier"]
    shown_resolution = g["shown_resolution"]
    audio_phrase = g["audio_phrase"]
    assumption_html = g["assumption_html"]
    plat_link = g["plat_link"]
    tag = g["tag"]
    dates = [CHECKED, LAST, UNLIMITED_CHECKED]
    g["SITEMAP_LASTMOD"][PATH] = max(dates)

    def src(url, text="source"):
        return _src(g, url, text)

    def row_by(rid):
        return _row_by_id(g, rid)

    hf_src = src(HF_PLANS, "Higgsfield’s pricing page")
    rw_src = src(RUNWAY_PLANS, "Runway’s pricing page")
    rw_api = src(RUNWAY_API, "Runway API pricing")
    to_max = src(HELP_UNLIMITED_TO_MAX, "Unlimited plan is switching to Max")
    krea_src = src(KREA_PLANS, "Krea’s pricing page")
    rw_guide = root(RUNWAY_GUIDE)
    hf_price = root(HF_PRICING)
    hf_worth = root(HF_WORTH)
    alts = root(ALTS)
    vs_kling = root(VS_KLING)
    fal_href = root(FAL_GUIDE)
    best_href = root(BEST)
    rw_model = root("/models/runway-gen-4/")
    wan_model = root("/models/wan-3-0/")
    veo_model = root("/models/veo-3-1/")
    calc = root("/calculator/?model=runway-gen-4&seconds=5")

    r096 = row_by("r096")
    r055 = row_by("r055")
    r047 = row_by("r047")
    r046 = row_by("r046")
    r146 = row_by("r146")
    r155 = row_by("r155")
    r045 = row_by("r045")
    r127 = row_by("r127")

    def catalog_table(row_ids, table_id):
        head = (
            "<thead><tr><th>Where</th><th>Model</th><th>Variant</th><th>Tier</th>"
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
                f'<td><a href="{root(f"/models/{r["model"]}/")}">{e(g["models"][r["model"]]["name"])}</a></td>'
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
        f"It depends on the model. Higgsfield has no Runway Gen-4 row in our catalog, "
        f"so there is no like-for-like Higgsfield price for Gen-4 or Gen-4.5. "
        f"Higgsfield’s cheapest catalog rate overall is {rate_money(r096['usd_per_second'])}/s "
        f"for Wan 3.0 at 480p on Ultra (annual), if you use every paid credit. Runway’s "
        f"cheapest catalog API row is {rate_money(r055['usd_per_second'])}/s for Grok Imagine "
        f"1.5 Lite at 480p. Runway Gen-4 Turbo on the official API is "
        f"{rate_money(r047['usd_per_second'])}/s, and Gen-4.5 is {rate_money(r046['usd_per_second'])}/s, "
        f"both billed at $0.01 per official API credit. Runway does not sell a plan named "
        f"Unlimited to new buyers. Affiliate links never change this price order."
    )
    a_plans = (
        f"On {checked_pt(CHECKED)}, Runway’s public pricing page still listed Free, "
        f"Standard, Pro, and Max for individuals. Free is $0 with 125 one-time credits. "
        f"Standard is $15 a month, or $12 a month billed yearly, with 625 credits a month. "
        f"Pro is $35 a month, or $28 a month billed yearly, with 2,250 credits. Max is "
        f"$95 a month, or $76 a month billed yearly, with 9,500 credits and a one-month "
        f"credit rollover. There is no plan named Unlimited for new buyers on that page. "
        f"{to_max}, last fully read {checked_pt(UNLIMITED_CHECKED)}, says eligible legacy "
        f"Unlimited plans stay unchanged through November 30, 2026, then monthly plans "
        f"move to Max at $95 a month. Higgsfield’s catalog plans, checked the same day "
        f"as the Runway cards, are Starter $19 a month for 270 credits, Plus $59 monthly "
        f"or {_pa} a month billed annually for 1,200 credits, and Ultra $129 monthly or "
        f"{_ua} a month billed annually for 3,000 credits{_sale}."
    )
    a_krea = (
        f"Krea’s cheapest catalog estimate for Runway Gen-4.5 is "
        f"{rate_money(r155['usd_per_second'])}/s on Basic (yearly), using Krea’s published "
        f"approximate clip count and a 2-second unit. The official Runway API for Gen-4.5 "
        f"is {rate_money(r046['usd_per_second'])}/s. Those are the same model family, but "
        f"Krea’s figure is an estimate and does not state resolution or audio. Runway "
        f"Gen-4 Turbo on the official API, at {rate_money(r047['usd_per_second'])}/s, is a "
        f"different variant and is cheaper than that Krea Gen-4.5 estimate. For Veo 3.1, "
        f"Krea Lite at {rate_money(r146['usd_per_second'])}/s is below Runway API’s cheapest "
        f"Veo 3.1 row at {rate_money(r045['usd_per_second'])}/s and below Higgsfield’s "
        f"cheapest Veo 3.1 Fast row at {rate_money(r127['usd_per_second'])}/s."
    )
    a_best = (
        "Higgsfield Ultra (annual) is best for the lowest catalog rate we track on Wan 3.0 "
        "and several other non-Runway models, if you use every paid credit. It is not for "
        "a Gen-4 or Gen-4.5 price we can show, because those Higgsfield rows do not exist "
        "in the catalog. Runway API is best for official Gen-4 Turbo or Gen-4.5 rates, and "
        "for Grok Imagine 1.5 Lite at 480p. It is not the cheapest catalog route for Veo 3.1 "
        "Lite, where Krea is lower. Krea Basic (yearly) is best for the lowest Gen-4.5 "
        "estimate we track, and for Veo 3.1 Lite. It is not a substitute for official "
        "Runway Gen-4 Turbo. No line is given for a Higgsfield Gen-4 rate."
    )
    a_unknown = (
        f"Confirmed {checked_pt(CHECKED)} on Runway’s public pricing page: Free, Standard, "
        f"Pro, and Max prices and monthly credits, and the 125 one-time Free credits. "
        f"Confirmed the same day in the catalog: Runway API rates, Krea Gen-4.5 and Veo 3.1 "
        f"Lite estimates, and Higgsfield’s cheapest Wan 3.0 and Veo 3.1 Fast rows. "
        f"Confirmed {checked_pt(UNLIMITED_CHECKED)} in Runway’s help center: Unlimited is "
        f"a legacy plan not sold to new buyers, and eligible monthly Unlimited plans move "
        f"to Max after November 30, 2026. Unknown: a Higgsfield plan or API rate for "
        f"Runway Gen-4 or Gen-4.5; resolution and audio on the Krea Gen-4.5 rows; and "
        f"which models Unlimited Mode covers on Pro or Max at a given moment."
    )

    faqs = [
        (QUESTION, a_q),
        ("What do Runway and Higgsfield plans cost, and what happened to Unlimited?", a_plans),
        ("How does Krea compare with Runway, and what other alternatives are there?", a_krea),
        ("Which option is best for each use?", a_best),
        ("What is confirmed, and what is not?", a_unknown),
    ]
    for q, a in faqs:
        raw = (q + " " + a).lower()
        for bad in ("subscribe", "newsletter", "buttondown"):
            if bad in raw:
                raise SystemExit(f"{PATH} FAQ text contains {bad}")

    lead = (
        f"{e(a_q)} Runway plan cards were read {e(CHECKED_WHEN)}. "
        f"Related: <a href=\"{e(rw_guide)}\">Runway pricing per second</a> · "
        f"<a href=\"{e(hf_price)}\">Higgsfield pricing explained</a> · "
        f"<a href=\"{e(hf_worth)}\">Is Higgsfield worth it?</a> · "
        f"<a href=\"{e(alts)}\">Higgsfield alternatives</a> · "
        f"<a href=\"{e(vs_kling)}\">Higgsfield vs Kling</a> · "
        f"<a href=\"{e(fal_href)}\">fal pricing vs Replicate, WaveSpeed, and Runware</a>."
    )

    takeaways = f"""<div class="card" id="takeaways">
<h2>Key takeaways</h2>
<ul>
<li><b>No like-for-like Gen-4 price on Higgsfield.</b> That model is not in the Higgsfield catalog. Compare official Runway API rates with other platforms that publish a Gen-4 or Gen-4.5 row.</li>
<li><b>Cheapest catalog rates are not the same model.</b> Higgsfield Wan 3.0 is {rate_money(r096['usd_per_second'])}/s on Ultra (annual). Runway API Grok Imagine 1.5 Lite is {rate_money(r055['usd_per_second'])}/s at 480p. Gen-4 Turbo is {rate_money(r047['usd_per_second'])}/s.</li>
<li><b>Unlimited is not sold to new buyers.</b> Legacy monthly Unlimited plans move to Max after November 30, 2026, per Runway’s help center.</li>
<li><b>Krea can undercut official Runway Gen-4.5 and Veo 3.1</b> in the catalog, as estimates. Gen-4 Turbo on the official API is a cheaper, different variant.</li>
<li><b>Affiliate links never change this price order.</b></li>
</ul>
</div>"""

    next_steps = f"""<div class="card" id="next-steps">
<h2>What to do next</h2>
<ul>
<li><b>Check the vendor page.</b> Confirm today’s plan or API rate on {rw_src}, {rw_api}, or {hf_src} before you buy.</li>
<li><b>Try the calculator.</b> Put your clip length into the <a href="{e(calc)}">credit calculator for Runway Gen-4 at 5 seconds</a>.</li>
<li><b>Open the model page.</b> Every current rate, with its source and date: <a href="{e(rw_model)}">Runway Gen-4</a> · <a href="{e(wan_model)}">Wan 3.0</a> · <a href="{e(veo_model)}">Veo 3.1</a>.</li>
</ul>
</div>"""

    body = f"""<p class="small"><a href="{root("/guides/")}">Guides</a> › Higgsfield vs Runway</p>
<h1>{e(PHRASE)}</h1>
<p class="lead">{lead}</p>
<p class="small">Last checked {e(LAST)}. Official Runway plan cards were read {e(CHECKED_WHEN)}. Catalog rows use the date on each row. Affiliate links never change this price order. Every dollar-per-second figure below states its usage assumption, tier, resolution, and audio.</p>
{takeaways}

<h2>{e(QUESTION)}</h2>
<p>{e(a_q)}</p>

<h2>What do Runway and Higgsfield plans cost, and what happened to Unlimited?</h2>
<p>{e(a_plans)} The longer official-plan walkthrough is in <a href="{e(rw_guide)}">Runway pricing per second</a>.</p>

<h2>Catalog rates that come up in this comparison</h2>
<p>These rows are not all the same model. They are the cheapest Higgsfield, Runway API, and Krea figures this page cites, plus official Gen-4 Turbo and Veo 3.1 on Runway, so the lead numbers have a source.</p>
{catalog_table(ROWS_OVERALL, "overall-table")}

<h2>Official Runway API rows we track</h2>
<p>Billed at $0.01 per official API credit, from {rw_api}, checked {e(checked_pt(CHECKED))} in the catalog. Resolution is shown when the vendor stated it.</p>
{catalog_table(ROWS_RUNWAY, "runway-api-table")}

<h2>How does Krea compare with Runway, and what other alternatives are there?</h2>
<p>{e(a_krea)} {krea_src}. Other catalog routes for models Runway also sells, including Wan 3.0 and Kling 3.0, are ranked in <a href="{e(alts)}">Higgsfield alternatives</a> and <a href="{e(best_href)}">best AI video generator by value</a>.</p>
{catalog_table(ROWS_KREA_RW, "krea-runway-table")}
<h3>Veo 3.1 on Krea, Higgsfield, and Runway</h3>
{catalog_table(ROWS_VEO, "veo-table")}

<h2>Which option is best for each use?</h2>
<p>{e(a_best)}</p>
<ul>
<li><b>Higgsfield Ultra (annual).</b> Best for: the lowest catalog rate we track on Wan 3.0 and several other non-Runway models, if you use every paid credit. Not for: a Gen-4 or Gen-4.5 price we can show. {hf_src}.</li>
<li><b>Runway API.</b> Best for: official Gen-4 Turbo or Gen-4.5 rates, and Grok Imagine 1.5 Lite at 480p. Not for: the lowest Veo 3.1 Lite catalog rate. {rw_api}.</li>
<li><b>Krea Basic (yearly).</b> Best for: the lowest Gen-4.5 estimate we track, and Veo 3.1 Lite. Not for: replacing official Runway Gen-4 Turbo, which is a cheaper, different variant. {krea_src}.</li>
</ul>
<p>No line given for a Higgsfield Gen-4 rate, because that row is not in the catalog.</p>

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
