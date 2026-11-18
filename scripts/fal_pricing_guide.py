"""Guide: fal pricing vs Replicate, WaveSpeed, and Runware.

Imported by scripts/build_site.py. Catalog rows were last fully checked
on 2026-11-17. WaveSpeed, Runware, and Replicate model pages were read
the same day for non-catalog or confirmation figures. This page never
names Sora.
"""

PATH = "/guides/fal-ai-pricing/"
LABEL = "fal AI pricing"
PHRASE = "fal pricing vs Replicate and others"
QUESTION = "How does fal pricing compare with Replicate, WaveSpeed, and Runware?"
CHECKED = "2026-11-17"
POLICY_CHECKED = "2026-11-18"
HF_API = "https://open.higgsfield.ai/pricing"
CHECKED_WHEN = "Nov 17, 2026, 4:50–4:53 PM America/Caracas (12:50–12:53 PM PT)"

FAL_PRICING = "https://fal.ai/pricing"
FAL_WAN = "https://fal.ai/models/alibaba/wan-3.0/text-to-video"
FAL_WANP = "https://fal.ai/models/alibaba/wan-3.0-prime/text-to-video"
FAL_SEED = "https://fal.ai/models/bytedance/seedance-2.5/text-to-video"
FAL_H3T = "https://fal.ai/models/minimax/h3-max-turbo/text-to-video"
FAL_KLING = "https://fal.ai/models/fal-ai/kling-video/v3/pro/text-to-video"
FAL_VEO = "https://fal.ai/models/fal-ai/veo3.1"
REP_WAN = "https://replicate.com/alibaba/wan-3"
REP_SEED = "https://replicate.com/bytedance/seedance-2.5"
WS_PRICING = "https://wavespeed.ai/pricing"
WS_WAN = "https://wavespeed.ai/models/alibaba/wan-3.0/text-to-video"
WS_WANP = "https://wavespeed.ai/models/alibaba/wan-3.0-prime/text-to-video"
WS_SEED = "https://wavespeed.ai/models/bytedance/seedance-2.5/text-to-video"
WS_H3 = "https://wavespeed.ai/models/wavespeed-ai/minimax-h3/text-to-video"
RW_PRICING = "https://runware.ai/pricing"
RW_WAN = "https://runware.ai/wan-3-0"
RW_H3 = "https://runware.ai/minimax-h3"
ALTS = "/guides/higgsfield-alternatives/"
VS_KLING = "/guides/higgsfield-vs-kling/"
VS_RUNWAY = "/guides/higgsfield-vs-runway/"
BEST = "/guides/best-ai-video-generator/"

WAN_ROWS = ("r025", "r009")
PRIME_ROWS = ("r012",)
SEED_ROWS = ("r202", "r017")
H3_ROWS = ("r023", "r022")
KLING_ROWS = ("r015", "r016", "r059")
VEO_ROWS = ("r020",)
GROK_ROWS = ("r209", "r055", "r024")


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
        "fal AI pricing versus Replicate, WaveSpeed, and Runware, compared "
        "per second for the same models, with list and sale rates labelled."
    )


def description(g):
    text = (
        "fal AI pricing versus Replicate, WaveSpeed, and Runware for the same "
        "models, in dollars per second. Last checked Nov 17, 2026."
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

    fal_src = src(FAL_PRICING, "fal’s pricing page")
    fal_wan = src(FAL_WAN, "fal’s Wan 3.0 page")
    rep_wan = src(REP_WAN, "Replicate’s Wan 3.0 page")
    rep_seed = src(REP_SEED, "Replicate’s Seedance 2.5 page")
    ws_src = src(WS_PRICING, "WaveSpeed’s pricing page")
    ws_wan = src(WS_WAN, "WaveSpeed’s Wan 3.0 text-to-video page")
    ws_wanp = src(WS_WANP, "WaveSpeed’s Wan 3.0 Prime text-to-video page")
    ws_seed = src(WS_SEED, "WaveSpeed’s Seedance 2.5 text-to-video page")
    ws_h3 = src(WS_H3, "WaveSpeed’s MiniMax H3 text-to-video page")
    rw_src = src(RW_PRICING, "Runware’s pricing page")
    rw_wan = src(RW_WAN, "Runware’s Wan 3.0 page")
    rw_h3 = src(RW_H3, "Runware’s MiniMax H3 page")
    alts = root(ALTS)
    vs_kling = root(VS_KLING)
    vs_runway = root(VS_RUNWAY)
    best_href = root(BEST)
    wan_model = root("/models/wan-3-0/")
    prime_model = root("/models/wan-3-0-prime/")
    seed_model = root("/models/seedance-2-5/")
    hailuo_model = root("/models/minimax-hailuo/")
    kling_model = root("/models/kling-3-0/")
    veo_model = root("/models/veo-3-1/")
    grok_model = root("/models/grok-imagine/")
    calc = root("/calculator/?model=wan-3-0&seconds=5")

    r009 = row_by("r009")
    r025 = row_by("r025")
    r012 = row_by("r012")
    r017 = row_by("r017")
    r202 = row_by("r202")
    r023 = row_by("r023")
    r015 = row_by("r015")
    r020 = row_by("r020")
    r024 = row_by("r024")
    r209 = row_by("r209")

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

    def manual_table(table_id, rows):
        head = (
            "<thead><tr><th>Where</th><th>Model</th><th>Tier</th>"
            "<th>Res</th><th>Audio</th><th>$/s</th><th>Status</th><th>Source</th></tr></thead>"
        )
        body_rows = []
        for where, model, tier, res, audio, rate, status, source_html in rows:
            body_rows.append(
                "<tr>"
                f"<td>{where}</td>"
                f"<td>{model}</td>"
                f"<td>{tier}</td>"
                f"<td>{res}</td>"
                f"<td>{audio}</td>"
                f'<td class="num">{rate}</td>'
                f"<td>{status}</td>"
                f"<td>{source_html}</td>"
                "</tr>"
            )
        return (
            f'<div class="tblwrap" id="{e(table_id)}"><table>{head}'
            f'<tbody>{"".join(body_rows)}</tbody></table></div>'
        )

    live_note = f"Read {e(CHECKED_WHEN)}. Not a catalog row."
    wan_live = manual_table("wan-live-table", [
        ("WaveSpeed", "Wan 3.0", "API list", "480p", "optional (default on in the form; the published table does not change the rate)", "$0.05", "published list rate", f"{ws_wan}. 720p is $0.10/s and 1080p is $0.20/s on the same table. {live_note}"),
        ("WaveSpeed", "Wan 3.0 Prime", "API list", "480p", "not stated as a price change on the table", "$0.075", "published list rate", f"{ws_wanp}. 720p is $0.15/s and 1080p is $0.30/s. {live_note}"),
        ("Runware", "Wan 3.0", "API sale, through November 23, 2026", "480p", "same rate for every stated input type", "$0.015", "promo; list $0.05/s", f"{rw_wan}. Sale is 70% off. List rates are $0.05, $0.10, and $0.20/s at 480p, 720p, and 1080p. Sale 720p is $0.03/s and 1080p is $0.06/s. {live_note}"),
        ("Runware", "Wan 3.0 Prime", "API sale, through November 23, 2026", "480p", "same rate for every stated input type", "$0.034", "promo; list $0.068/s", f"{rw_wan}. Sale is 50% off. List rates are $0.068, $0.14, and $0.28/s. Sale 720p is $0.07/s and 1080p is $0.14/s. {live_note}"),
    ])
    seed_live = manual_table("seed-live-table", [
        ("WaveSpeed", "Seedance 2.5", "API list, no reference video", "480p", "not stated as a separate audio price on the table", "$0.18", "published list rate", f"{ws_seed}. 720p is $0.36/s, 1080p is $0.90/s, and 4K is $1.80/s, billed linearly from 4 to 30 seconds. A reference-video path uses a lower per-second rate ($0.11/s at 480p) on both the normalized input and the output. {live_note}"),
        ("WaveSpeed", "Seedance 2.5 Flash", "API list, no reference video", "480p", "not stated as a separate audio price on the table", "$0.12", "published list rate", f"{src(WS_SEED.replace('seedance-2.5/', 'seedance-2.5-flash/'), 'WaveSpeed’s Seedance 2.5 Flash page')}. 720p is $0.24/s, 1080p is $0.60/s, and 4K is $1.20/s. {live_note}"),
        ("Runware", "Seedance 2.5", "API", "unknown", "unknown", "unknown", "not verified today", f"The Runware Seedance 2.5 model page loaded, but it did not publish a dollars-per-second rate at a stated resolution in the HTML we could read. {live_note}"),
    ])
    h3_live = manual_table("h3-live-table", [
        ("WaveSpeed", "MiniMax H3", "API list", "480p", "native stereo audio is described on the page; the table is by resolution", "$0.04", "published list rate", f"{ws_h3}. 540p is $0.06/s, 768p is $0.08/s, and 1080p is $0.16/s. This is labelled MiniMax H3, not H3 Max Turbo. {live_note}"),
        ("Runware", "MiniMax H3", "API list", "768p", "reference audio is free; output audio is not priced separately on the page", "$0.08", "published list rate", f"{rw_h3}. 1440p (2K) is $0.13/s. A 5-second clip, the shortest supported length, is $0.40 at 768p or $0.65 at 2K. Reference video is $0.13 per second uploaded. {live_note}"),
    ])

    a_q = (
        f"For the same models at the same resolution, Replicate is cheaper than fal "
        f"for Wan 3.0 at 480p ({rate_money(r025['usd_per_second'])}/s versus "
        f"{rate_money(r009['usd_per_second'])}/s) and for Seedance 2.5 at 480p with no "
        f"video input ({rate_money(r202['usd_per_second'])}/s versus fal’s token-billed "
        f"estimate of {rate_money(r017['usd_per_second'])}/s, which includes audio). "
        f"WaveSpeed’s published list for Wan 3.0 at 480p is $0.05/s, the same as fal. "
        f"Runware is running a sale through November 23, 2026: Wan 3.0 at 480p is $0.015/s "
        f"(list $0.05/s), which is below fal’s {rate_money(r009['usd_per_second'])}/s while "
        f"the sale lasts. After the sale, Runware’s published list matches fal at 480p, "
        f"720p, and 1080p. A price we could not verify at a stated resolution is marked "
        f"unknown."
    )
    a_how = (
        "This page compares pay-as-you-go API rates for the same model, at the same "
        "resolution when the vendor stated it. Catalog rows are used where they exist. "
        "WaveSpeed and Runware are not in the catalog, so their figures were read from "
        "official pages today and are labelled as such. A sale rate is shown next to its "
        "list rate and end date. Token-billed or estimated rows stay labelled as estimates. "
        "Variants with different names, such as MiniMax H3 and MiniMax H3 Max Turbo, are "
        "not treated as one price."
    )
    a_best = (
        "Replicate is best for Wan 3.0 at 480p and for Seedance 2.5 at 480p with no video "
        "input, among the catalog rows we can compare, and those Replicate rates were also "
        "on the vendor pages today. Runware’s Wan 3.0 sale is best for the lowest verified "
        "480p Wan 3.0 API rate we could read today, through November 23, 2026. It is not "
        "for a post-sale rate below fal, because the published list then matches fal. "
        "fal remains a useful default when you already use its endpoint, but it is not the "
        "cheapest verified option for those two models. No line is given for Runware "
        "Seedance 2.5, or for WaveSpeed or Runware Kling 3.0, because those $/s figures "
        "at a stated resolution were not verified today."
    )
    a_unknown = (
        f"Confirmed {checked_pt(CHECKED)} in the catalog, and re-checked on the Replicate "
        f"model pages today: Wan 3.0 at $0.035, $0.07, and $0.14 per second at 480p, 720p, "
        f"and 1080p, and Seedance 2.5 at $0.1028/s (480p, no video input) and $0.2312/s "
        f"(720p, no video input). Confirmed today on WaveSpeed model pages: the Wan 3.0, "
        f"Wan 3.0 Prime, Seedance 2.5, Seedance 2.5 Flash, and MiniMax H3 list tables "
        f"quoted above. Confirmed today on Runware: the Wan 3.0 and Wan 3.0 Prime sale and "
        f"list rates through November 23, 2026, and MiniMax H3 at $0.08/s (768p) and "
        f"$0.13/s (1440p). WaveSpeed also states that eligible new accounts get $1 in "
        f"free credits, with no credit card required to start, on {ws_src}. Unknown: a "
        f"Runware Seedance 2.5 or Kling 3.0 rate at a stated resolution; a WaveSpeed "
        f"Kling 3.0 rate (the pricing starting table lists Kling 4.0, not 3.0); a "
        f"WaveSpeed or Runware Veo 3.1 rate we could verify today; and whether MiniMax H3 "
        f"on WaveSpeed or Runware is billed as the same product as fal’s H3 Max Turbo."
    )

    q_video_api = "How do video generation API prices compare?"
    a_video_api = (
        "This page already compares catalog API rows for Seedance 2.5, MiniMax, Kling 3.0, Veo 3.1, and Grok Imagine, next to Replicate, WaveSpeed, and Runware where we have a verified rate. "
        "Higgsfield API list rates for the same models are also in our catalog. "
        "Seedance 2.0 is not in this catalog, so no Seedance 2.0 API rate is shown. "
        "Affiliate links never change this price order."
    )
    q_coupon = "Is there a fal coupon code?"
    a_coupon = (
        f"No public coupon or promo code was listed on fal's official pricing page when it was opened {checked_pt(POLICY_CHECKED)}. "
        "This guide does not invent a code."
    )
    faqs = [
        (QUESTION, a_q),
        ("How does this API comparison work?", a_how),
        (q_video_api, a_video_api),
        ("Which API is best for each use?", a_best),
        (q_coupon, a_coupon),
        ("What is confirmed, and what is not?", a_unknown),
    ]
    for q, a in faqs:
        raw = (q + " " + a).lower()
        for bad in ("subscribe", "newsletter", "buttondown"):
            if bad in raw:
                raise SystemExit(f"{PATH} FAQ text contains {bad}")

    lead = (
        f"{e(a_q)} Official WaveSpeed, Runware, and Replicate pages were read "
        f"{e(CHECKED_WHEN)}. Related: <a href=\"{e(alts)}\">Higgsfield alternatives</a> · "
        f"<a href=\"{e(vs_kling)}\">Higgsfield vs Kling</a> · "
        f"<a href=\"{e(vs_runway)}\">Higgsfield vs Runway</a> · "
        f"<a href=\"{e(best_href)}\">best AI video generator by value</a>."
    )

    takeaways = f"""<div class="card" id="takeaways">
<h2>Key takeaways</h2>
<ul>
<li><b>Replicate undercuts fal on two catalog models we can compare like for like.</b> Wan 3.0 at 480p is {rate_money(r025['usd_per_second'])}/s versus fal’s {rate_money(r009['usd_per_second'])}/s. Seedance 2.5 at 480p with no video input is {rate_money(r202['usd_per_second'])}/s versus fal’s token-billed estimate of {rate_money(r017['usd_per_second'])}/s.</li>
<li><b>WaveSpeed’s Wan 3.0 list at 480p matches fal</b> at $0.05/s. Seedance 2.5 list at 480p, with no reference video, is $0.18/s, between Replicate and fal.</li>
<li><b>Runware’s Wan 3.0 sale is $0.015/s at 480p through November 23, 2026</b> (list $0.05/s). After the sale, the published list matches fal at 480p, 720p, and 1080p.</li>
<li><b>Unverified rates stay unknown.</b> Runware Seedance 2.5, and Kling 3.0 on WaveSpeed or Runware, have no verified $/s at a stated resolution on this page.</li>
</ul>
</div>"""

    next_steps = f"""<div class="card" id="next-steps">
<h2>What to do next</h2>
<ul>
<li><b>Check the vendor page.</b> Confirm today’s API rate on {fal_src}, {rep_wan}, {ws_src}, or {rw_wan} before you send traffic.</li>
<li><b>Try the calculator.</b> Put your clip length into the <a href="{e(calc)}">credit calculator for Wan 3.0 at 5 seconds</a>.</li>
<li><b>Open the model page.</b> Every current catalog rate, with its source and date: <a href="{e(wan_model)}">Wan 3.0</a> · <a href="{e(prime_model)}">Wan 3.0 Prime</a> · <a href="{e(seed_model)}">Seedance 2.5</a> · <a href="{e(hailuo_model)}">MiniMax Hailuo</a> · <a href="{e(kling_model)}">Kling 3.0</a> · <a href="{e(veo_model)}">Veo 3.1</a> · <a href="{e(grok_model)}">Grok Imagine</a>.</li>
</ul>
</div>"""

    body = f"""<p class="small"><a href="{root("/guides/")}">Guides</a> › fal AI pricing</p>
<h1>{e(PHRASE)}</h1>
<p class="lead">{lead}</p>
<p class="small">Last checked {e(LAST)}. Official WaveSpeed, Runware, and Replicate pages were read {e(CHECKED_WHEN)}. Catalog rows use the date on each row. Every dollar-per-second figure below states its usage assumption, tier, resolution, and audio. A non-catalog figure is labelled and dated.</p>
{takeaways}

<h2>{e(QUESTION)}</h2>
<p>{e(a_q)}</p>

<h2>How does this API comparison work?</h2>
<p>{e(a_how)}</p>

<h2>Wan 3.0 at 480p</h2>
<p>Catalog rows first, lowest $/s first, then today’s official WaveSpeed and Runware figures, which are not catalog rows.</p>
{catalog_table(WAN_ROWS, "wan-catalog-table")}
{wan_live}
<p>Replicate also publishes $0.07/s at 720p and $0.14/s at 1080p on {rep_wan}, matching a doubling and quadrupling of the 480p rate. Those 720p and 1080p figures are not separate catalog rows today.</p>

<h2>Wan 3.0 Prime</h2>
{catalog_table(PRIME_ROWS, "prime-catalog-table")}
<p>WaveSpeed’s list and Runware’s sale for Prime are in the live table above. fal’s catalog row is {rate_money(r012['usd_per_second'])}/s at 480p, from {src(FAL_WANP, "fal’s Wan 3.0 Prime page")}.</p>

<h2>Seedance 2.5</h2>
<p>The Replicate catalog row is the no-video-input rate at 480p. fal’s catalog row is a token-billed estimate at 480p with audio. They are the closest same-model comparison we can show, and the billing methods differ.</p>
{catalog_table(SEED_ROWS, "seed-catalog-table")}
{seed_live}

<h2>MiniMax H3-family rows</h2>
<p>These names are not treated as one product. fal’s cheapest catalog row is MiniMax H3 Max Turbo. WaveSpeed and Runware pages are labelled MiniMax H3.</p>
{catalog_table(H3_ROWS, "h3-catalog-table")}
{h3_live}

<h2>Kling 3.0 and Veo 3.1</h2>
<p>fal’s Kling 3.0 catalog rows are the Pro tier. The official Kling API 720p row is included so you can see a published direct rate. WaveSpeed’s starting table lists Kling 4.0, not Kling 3.0, and Runware’s Kling 3.0 Standard page did not publish a $/s at a stated resolution in the HTML we could read, so those two are unknown here.</p>
{catalog_table(KLING_ROWS, "kling-catalog-table")}
{catalog_table(VEO_ROWS, "veo-catalog-table")}
<p>fal’s Veo 3.1 Standard catalog row is {rate_money(r020['usd_per_second'])}/s without audio, from {src(FAL_VEO, "fal’s Veo 3.1 page")}. A WaveSpeed or Runware Veo 3.1 rate was not verified today.</p>

<h2>Grok Imagine Video 1.5</h2>
<p>fal’s catalog row is the 1.5 model at 480p with audio. The cheaper official xAI and Runway API rows are Grok Imagine 1.5 Lite, a different variant, at 480p with audio not stated.</p>
{catalog_table(GROK_ROWS, "grok-catalog-table")}

<h2>{e(q_video_api)}</h2>
<p>{e(a_video_api)} The Seedance 2.5, MiniMax, Kling 3.0, Veo 3.1, and Grok tables above are the fal and other-API rows we already track. Higgsfield API list rates, from {src(HF_API, "open.higgsfield.ai/pricing")} and our catalog, sit on the <a href="{root("/guides/higgsfield-pricing/")}">Higgsfield pricing</a> page and on each model page. A general “video generation API” price does not exist as one number: it depends on the model, resolution, audio, and vendor.</p>

<h2>Which API is best for each use?</h2>
<p>{e(a_best)}</p>
<ul>
<li><b>Replicate.</b> Best for: Wan 3.0 at 480p, and Seedance 2.5 at 480p with no video input, among the verified like-for-like rows. Not for: a post-sale Wan 3.0 rate as low as Runware’s current 70% off sale. {rep_wan} · {rep_seed}.</li>
<li><b>Runware, through November 23, 2026.</b> Best for: the lowest verified Wan 3.0 API rate we could read today ($0.015/s at 480p). Not for: assuming that sale rate lasts after November 23, or for a verified Seedance 2.5 $/s. {rw_wan}.</li>
<li><b>WaveSpeed.</b> Best for: a published Wan 3.0 list that matches fal at 480p, 720p, and 1080p, and a published Seedance 2.5 list at 480p ($0.18/s) between Replicate and fal. Not for: a verified Kling 3.0 rate. {ws_wan} · {ws_seed}.</li>
<li><b>fal.</b> Best for: staying on one endpoint you already use, with catalog coverage across Wan, Seedance, Kling, Veo, MiniMax, and Grok. Not for: the lowest verified Wan 3.0 or Seedance 2.5 rate in this comparison. {fal_wan}.</li>
</ul>
<p>No line given for Runware Seedance 2.5, or for Kling 3.0 on WaveSpeed or Runware, because those rates were not verified at a stated resolution.</p>

<h2>{e(q_coupon)}</h2>
<p>{e(a_coupon)} Source: {src(FAL_PRICING, "fal.ai/pricing")}, opened {e(checked_pt(POLICY_CHECKED))}.</p>

<h2>What is confirmed, and what is not?</h2>
<p>{e(a_unknown)}</p>
{next_steps}
{g["how_block"]()}
"""

    if "sora" in body.lower() or "sora" in description(g).lower() or "sora" in PHRASE.lower():
        raise SystemExit(f"{PATH} source would name Sora")

    title = g["page_title"](PHRASE)
    desc = description(g)
    g["guide_page"](PATH, title, desc, body, faqs)
    return PATH
