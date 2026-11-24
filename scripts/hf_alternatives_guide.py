"""Guide: Higgsfield alternatives by cost.

Imported by scripts/build_site.py. Catalog rows were last fully checked
on 2026-11-17. OpenArt plan prices were read the same day. This page
never names Sora.
"""

PATH = "/guides/higgsfield-alternatives/"
LABEL = "Higgsfield alternatives"
PHRASE = "Higgsfield alternatives by cost"
QUESTION = "Which Higgsfield alternatives are cheaper per second?"
CHECKED = "2026-11-17"
CHECKED_WHEN = "Nov 17, 2026, 3:50–3:53 PM ET (12:50–12:53 PM PT)"

HF_PLANS = "https://higgsfield.ai/pricing"
KREA_PLANS = "https://www.krea.ai/pricing"
OPENART_PLANS = "https://openart.ai/pricing"
FREE_GUIDE = "/guides/free-ai-video-generators/"
FREE_T2V = "/guides/free-text-to-video-ai/"
HF_PRICING = "/guides/higgsfield-pricing/"
HF_WORTH = "/guides/is-higgsfield-worth-it/"
BEST = "/guides/best-ai-video-generator/"
VS_KLING = "/guides/higgsfield-vs-kling/"
VS_RUNWAY = "/guides/higgsfield-vs-runway/"
FAL_GUIDE = "/guides/fal-ai-pricing/"
WAN_GUIDE = "/guides/cheapest-wan-3-0/"

# Cheapest catalog row per platform, plus same-model comparisons.
PLAT_CHEAP = ("r096", "r055", "r209", "r127", "r023", "r178", "r025", "r005", "r076", "r199", "r059")
WAN_ROWS = ("r096", "r025", "r005", "r009", "r028")
PRIME_ROWS = ("r081", "r001", "r012", "r031")
VEO_ROWS = ("r127", "r045", "r020")
KLING_ROWS = ("r111", "r007", "r059", "r034", "r015")
HAILUO_ROWS = ("r132", "r023", "r178", "r076", "r050")
SEED_ROWS = ("r202", "r008", "r169", "r073", "r039", "r017")


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
        "Higgsfield alternatives ranked by cost per second, with the models "
        "where another catalog route is cheaper, and a short OpenArt comparison."
    )


def description(g):
    text = (
        "Higgsfield alternatives ranked by cost per second, including where "
        "Krea and Replicate are cheaper. Last checked Nov 17, 2026."
    )
    if len(text) > 160:
        raise SystemExit(f"{PATH} meta description is over 160 characters: {len(text)}")
    return text


def render(g):
    e, root, LAST = g["e"], g["root"], g["LAST"]
    rate_money = g["rate_money"]
    shown_tier = g["shown_tier"]
    shown_resolution = g["shown_resolution"]
    audio_phrase = g["audio_phrase"]
    assumption_html = g["assumption_html"]
    plat_link = g["plat_link"]
    tag = g["tag"]
    dates = [CHECKED, LAST]
    g["SITEMAP_LASTMOD"][PATH] = max(dates)

    def src(url, text="source"):
        return _src(g, url, text)

    def row_by(rid):
        return _row_by_id(g, rid)

    hf_src = src(HF_PLANS, "Higgsfield’s pricing page")
    krea_src = src(KREA_PLANS, "Krea’s pricing page")
    oa_src = src(OPENART_PLANS, "OpenArt’s pricing page")
    free_href = root(FREE_GUIDE)
    t2v_href = root(FREE_T2V)
    hf_price = root(HF_PRICING)
    hf_worth = root(HF_WORTH)
    best_href = root(BEST)
    vs_kling = root(VS_KLING)
    vs_runway = root(VS_RUNWAY)
    fal_href = root(FAL_GUIDE)
    krea_plat = root("/platforms/krea/")
    wan_href = root(WAN_GUIDE)
    wan_model = root("/models/wan-3-0/")
    veo_model = root("/models/veo-3-1/")
    kling_model = root("/models/kling-3-0/")
    hailuo_model = root("/models/minimax-hailuo/")
    seed_model = root("/models/seedance-2-5/")
    calc_wan = root("/calculator/?model=wan-3-0&seconds=5")

    r096 = row_by("r096")
    r202 = row_by("r202")
    r127 = row_by("r127")
    r008 = row_by("r008")

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
        f"Higgsfield still has the lowest catalog rate we track: "
        f"{rate_money(r096['usd_per_second'])}/s for Wan 3.0 at 480p on Ultra (annual), "
        f"audio not stated, from a credit plan, if you use every credit you pay for. "
        f"The cheapest catalog Veo 3.1 rate is Higgsfield’s Veo 3.1 Fast row at "
        f"{rate_money(r127['usd_per_second'])}/s at 720p on Ultra (annual). "
        f"Krea does not publish a per-second or per-model video price, so it is not in this ranking. Replicate’s Seedance 2.5 "
        f"rate is {rate_money(r202['usd_per_second'])}/s at 480p with no video input, under "
        f"Higgsfield API’s “from” {rate_money(r008['usd_per_second'])}/s, whose cheapest-mode "
        f"resolution is not stated. Affiliate links never change this price order."
    )
    a_how = (
        "This page ranks sites like Higgsfield by the dollars-per-second rows in our "
        "catalog, then compares the same model side by side so a cheap row for a "
        "different model is not treated as a like-for-like saving. A credit-plan figure "
        "assumes you use the credits you pay for; unused credits make the real cost higher. "
        "An API figure is billed per second of output, at the resolution and audio the "
        "vendor published. Higgsfield is an affiliate; those links never change this "
        "price order."
    )
    a_best = (
        "Best-for lines are given only where a catalog row or a vendor page supports them. "
        "Higgsfield Ultra (annual) is best for the lowest catalog rate we track on Wan 3.0, "
        "Wan 3.0 Prime, Kling 3.0, and Hailuo 2.3, if you use every paid credit. It is not "
        "for a Krea per-second price, which Krea does not publish, or for Seedance 2.5 on a Higgsfield plan, "
        "because that plan rate is not in the catalog. Higgsfield Ultra (annual) is also best for Veo 3.1 Fast, "
        "Lite cost in the catalog. Replicate is best for Seedance 2.5 at 480p with no video "
        "input among the rows we can compare. No line is given for OpenArt cost per second, "
        "because credits per clip were not published on the public pricing page we read."
    )
    a_free = (
        "Higgsfield lists a Free plan with 0 monthly credits and limited access to selected "
        "models; how many complimentary generations it actually allows, and which models are "
        "in that set, is unknown. Official pages that do publish a countable free text-to-video "
        "allowance are covered in our free-tier guides: Google Flow (50 credits a day) and "
        "Krea Free (100 compute units a day, no card). Kling lists a $0 Basic plan but does "
        "not publish credits per clip. OpenArt’s public pricing page, read Nov 17, 2026, did not "
        "publish a free-plan credit allotment, so that figure is unknown."
    )
    a_openart = (
        "OpenArt’s public pricing page, read Nov 17, 2026, lists four individual plans per seat: "
        "Starter $14 a month for 4,000 credits, Plus $34 for 12,000, Pro $56 for 24,000, "
        "and Wonder $240 for 106,000. The same page’s structured data lists annual billed "
        "rates of $13, $27, $44, and $175 a month. The visible cards also show a first-year "
        "annual promotional price ($11, $24, $36, and $144 a month). OpenArt says promotional "
        "discounts apply only to the first billing period and that the plan then renews at "
        "the then-current list price. Credits per clip for Wan, Kling, Veo, or Hailuo are "
        "not on that public page, so an OpenArt dollars-per-second figure is unknown and is "
        "not shown. Starter has no commercial-use right in the structured data; Plus and "
        f"higher do. Higgsfield’s catalog Starter is ${g['plans']['hf-starter']['usd_month']:,} a month for "
        f"{g['plans']['hf-starter']['credits_month']:,} credits, checked {checked_pt(g['plans']['hf-starter']['checked'])}."
    )
    a_unknown = (
        f"Confirmed from the catalog (last full check {g['LAST']}): the platform and "
        "same-model rows in the tables, including Higgsfield Ultra (annual) plan math at "
        f"${g['plans']['hf-ultra-annual']['usd_month']:,}/month for {g['plans']['hf-ultra-annual']['credits_month']:,} credits "
        f"(checked {checked_pt(g['plans']['hf-ultra-annual']['checked'])}). Confirmed Nov 17, 2026 on OpenArt’s pricing page: the monthly "
        "and annual list prices, first-year promotional annual card prices, credit allotments, "
        "and the first-period promo rule. Unknown: OpenArt credits per clip, so no OpenArt "
        "$/s; Higgsfield Free complimentary generations and the “selected” free models; "
        "how many official Kling app credits a clip uses; a Higgsfield plan rate for "
        "Seedance 2.5, Gemini Omni Flash, or Runway Gen-4; and a current official Google "
        "Gemini API rate for Veo 3.1, because those catalog rows are marked discontinued "
        "(discontinued on 2026-10-22)."
    )

    faqs = [
        (QUESTION, a_q),
        ("How does this page rank Higgsfield alternatives?", a_how),
        ("Which option is best for each use?", a_best),
        ("What free Higgsfield alternatives are there?", a_free),
        ("How does Higgsfield compare with OpenArt on price?", a_openart),
        ("What is confirmed, and what is not?", a_unknown),
    ]
    for q, a in faqs:
        raw = (q + " " + a).lower()
        for bad in ("subscribe", "newsletter", "buttondown"):
            if bad in raw:
                raise SystemExit(f"{PATH} FAQ text contains {bad}")

    lead = (
        f"{e(a_q)} Official pages used for non-catalog facts were read {e(CHECKED_WHEN)}. "
        f"Plan rates and API lists: <a href=\"{e(hf_price)}\">Higgsfield pricing explained</a> · "
        f"<a href=\"{e(hf_worth)}\">Is Higgsfield worth it?</a> · "
        f"<a href=\"{e(vs_kling)}\">Higgsfield vs Kling</a> · "
        f"<a href=\"{e(vs_runway)}\">Higgsfield vs Runway</a> · "
        f"<a href=\"{e(fal_href)}\">fal pricing vs Replicate, WaveSpeed, and Runware</a>."
    )

    takeaways = f"""<div class="card" id="takeaways">
<h2>Key takeaways</h2>
<ul>
<li><b>Lowest catalog rate is still Higgsfield.</b> Wan 3.0 at 480p on Ultra (annual) is {rate_money(r096['usd_per_second'])}/s, from a credit plan, if you use every paid credit. Audio is not stated. {e(r096['id'])}.</li>
<li><b>Higgsfield is the cheapest catalog Veo 3.1 rate.</b> Ultra (annual) estimates {rate_money(r127['usd_per_second'])}/s for Veo 3.1 Fast at 720p, from Higgsfield’s published credit figure. Krea does not publish a per-second or per-model video price, so VidFare does not compute one. See <a href="{e(krea_plat)}">Krea AI video plan prices</a>.</li>
<li><b>Replicate is cheaper for Seedance 2.5 at 480p.</b> {rate_money(r202['usd_per_second'])}/s with no video input, against Higgsfield API’s “from” {rate_money(r008['usd_per_second'])}/s, whose cheapest-mode resolution is not stated.</li>
<li><b>OpenArt $/s is unknown.</b> Plan prices were verified Nov 17, 2026. Credits per clip are not on the public pricing page, so no per-second figure is shown.</li>
<li><b>Affiliate links never change this price order.</b></li>
</ul>
</div>"""

    next_steps = f"""<div class="card" id="next-steps">
<h2>What to do next</h2>
<ul>
<li><b>Check the vendor page.</b> Confirm the current plan or API rate on {hf_src}, {krea_src}, or the source link in each row before you buy.</li>
<li><b>Try the calculator.</b> Put your clip length into the <a href="{e(calc_wan)}">credit calculator for Wan 3.0 at 5 seconds</a>.</li>
<li><b>Open the model page.</b> Every current rate, with its source and date: <a href="{e(wan_model)}">Wan 3.0</a> · <a href="{e(veo_model)}">Veo 3.1</a> · <a href="{e(kling_model)}">Kling 3.0</a> · <a href="{e(hailuo_model)}">MiniMax Hailuo</a> · <a href="{e(seed_model)}">Seedance 2.5</a>.</li>
</ul>
</div>"""

    body = f"""<p class="small"><a href="{root("/guides/")}">Guides</a> › Higgsfield alternatives</p>
<h1>{e(PHRASE)}</h1>
<p class="lead">{lead}</p>
<p class="small">Last checked {e(LAST)}. Official non-catalog pages were read {e(CHECKED_WHEN)}. Catalog rows use the date on each row. Affiliate links never change this price order. Every dollar-per-second figure below states its usage assumption, tier, resolution, and audio.</p>
{takeaways}

<h2>{e(QUESTION)}</h2>
<p>{e(a_q)}</p>

<h2>How does this page rank Higgsfield alternatives?</h2>
<p>{e(a_how)} Related: <a href="{e(wan_href)}">cheapest Wan 3.0</a> · <a href="{e(best_href)}">best AI video generator by value</a>.</p>

<h2>Cheapest catalog rate on each platform</h2>
<p>One row per platform we track, using that platform’s lowest current catalog rate, lowest $/s first. These rows are not the same model, so a cheaper platform here may not be cheaper for the model you want. The same-model tables below are the like-for-like comparisons.</p>
{catalog_table(PLAT_CHEAP, "platform-cheap-table")}
<p class="small">Official Google Gemini API Veo 3.1 catalog rows, including the old Lite rate, are marked discontinued (discontinued on 2026-10-22). They are not in this ranking. The Google Gemini API row above is the cheapest current catalog rate on that API, which is Gemini Omni Flash, not Veo 3.1.</p>

<h2>Same model, side by side</h2>
<p>Each table is one model, lowest catalog $/s first. A “from” Higgsfield API list price is included where it exists; its cheapest-mode resolution may be unstated.</p>
<h3>Wan 3.0</h3>
{catalog_table(WAN_ROWS, "wan-table")}
<h3>Wan 3.0 Prime</h3>
{catalog_table(PRIME_ROWS, "prime-table")}
<h3>Veo 3.1</h3>
{catalog_table(VEO_ROWS, "veo-table")}
<h3>Kling 3.0</h3>
{catalog_table(KLING_ROWS, "kling-table")}
<p>A longer official-vs-Higgsfield walkthrough is in <a href="{e(vs_kling)}">Higgsfield vs Kling</a>.</p>
<h3>MiniMax Hailuo and H3-family rows</h3>
<p>These variants are not identical. Hailuo 2.3, H3 Max Turbo, H3 Max, and H3 Fast are listed under the same model page in our catalog, but the vendor names differ, so a cheaper H3 Max Turbo row is not a substitute price for Hailuo 2.3.</p>
{catalog_table(HAILUO_ROWS, "hailuo-table")}
<h3>Seedance 2.5</h3>
<p>There is no Higgsfield plan row for Seedance 2.5 in the catalog. The Higgsfield figure below is the API “from” list price.</p>
{catalog_table(SEED_ROWS, "seedance-table")}

<h2>Which option is best for each use?</h2>
<p>{e(a_best)}</p>
<ul>
<li><b>Higgsfield Ultra (annual).</b> Best for: the lowest catalog rate we track on Wan 3.0, Wan 3.0 Prime, Kling 3.0, Hailuo 2.3, and Veo 3.1 Fast, if you use every paid credit. Not for: Seedance 2.5 on a plan rate we can show, or pay-as-you-go without a monthly plan. {hf_src}. Related: <a href="{e(hf_price)}">Higgsfield pricing</a>.</li>
<li><b>Krea plans.</b> Best for: Krea’s own plan prices and unit allowances, including a Free plan with 100 units a day. Not for: a per-second catalog rate — Krea does not publish one, so VidFare does not compute one. {krea_src}. Related: <a href="{e(krea_plat)}">Krea AI video plan prices</a>.</li>
<li><b>Replicate.</b> Best for: Seedance 2.5 at 480p with no video input, among the rows we can compare. Not for: Wan 3.0, where Higgsfield’s plan rate is lower.</li>
</ul>
<p>No line given for OpenArt cost per second, or for a Higgsfield plan rate on Seedance 2.5, Gemini Omni Flash, or Runway Gen-4, because those per-second figures are not in the catalog or were not published on the pages we could verify.</p>

<h2>What free Higgsfield alternatives are there?</h2>
<p>{e(a_free)} See <a href="{e(free_href)}">free AI video generators: what you get</a> and <a href="{e(t2v_href)}">free text to video AI</a>.</p>

<h2>How does Higgsfield compare with OpenArt on price?</h2>
<p>{e(a_openart)} {oa_src}, read {e(CHECKED_WHEN)}.</p>

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
