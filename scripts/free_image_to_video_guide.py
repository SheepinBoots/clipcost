"""Guide: Free image to video AI.

Imported by scripts/build_site.py. Official image-to-video pages were read
on 2026-11-16. This page never names Sora. It links to the free-generators
guide for general free-tier caps and does not copy that table in full.
"""

PATH = "/guides/free-image-to-video-ai/"
LABEL = "Free image to video"
PHRASE = "Free image to video AI"
QUESTION = "Which tools let you animate a photo for free?"
CHECKED = "2026-11-16"
CHECKED_WHEN = "Nov 16, 2026, 8:34 AM ET (5:34 AM PT)"

KREA_I2V = "https://www.krea.ai/apps/image-to-video"
KREA_PLANS = "https://www.krea.ai/pricing"
FLOW_CREATE = "https://support.google.com/flow/answer/16353334?hl=en"
FLOW_MODELS = "https://support.google.com/flow/answer/16352836?hl=en"
FLOW_CREDITS = "https://support.google.com/flow/answer/16526234?hl=en"
DREAMINA_I2V = "https://dreamina.capcut.com/ai-video/image-to-video"
DREAMINA_PLANS = "https://dreamina.capcut.com/plans"
PIKA_PLANS = "https://pika.art/pricing"
WAN_HOME = "https://create.wan.video/"
WAN_PLANS = "https://create.wan.video/pricing?whereToMemberShip=membership_plans"
HAILUO_HOME = "https://hailuoai.video/"
HAILUO_TERMS = "https://hailuoai.video/doc/payment-policy.html"
RUNWAY_PLANS = "https://runway.com/pricing"
KLING_PLANS = "https://kling.ai/app/membership/membership-plan"
HF_PLANS = "https://higgsfield.ai/pricing"
LUMA_PLANS = "https://lumalabs.ai/pricing"
GROK_COM = "https://grok.com/imagine"
XAI_GROK = "https://x.ai/grok"
AA_I2V = "https://artificialanalysis.ai/video/leaderboard/image-to-video"


def _src(g, url, text="source"):
    e = g["e"]
    href, rel = g["outbound"](url)
    return f'<a href="{e(href)}" rel="{rel}" target="_blank">{e(text)}</a>'


def blurb(g):
    return (
        "Which official free tiers actually let you animate a photo, with the "
        "limits, watermark, and resolution the vendor published."
    )


def description(g):
    text = (
        "Free image to video AI: which tools animate a photo on a free tier, "
        "with limits, watermarks, and resolution. Last checked Nov 16, 2026."
    )
    if len(text) > 160:
        raise SystemExit(f"{PATH} meta description is over 160 characters: {len(text)}")
    return text


def render(g):
    e, root, LAST = g["e"], g["root"], g["LAST"]
    dates = [CHECKED, LAST]
    g["SITEMAP_LASTMOD"][PATH] = max(dates)

    def src(url, text="source"):
        return _src(g, url, text)

    krea_i2v = src(KREA_I2V, "Krea’s image-to-video page")
    krea_plans = src(KREA_PLANS, "Krea’s pricing page")
    flow_create = src(FLOW_CREATE, "Create videos in Google Flow")
    flow_models = src(FLOW_MODELS, "Google Flow models and supported features")
    flow_credits = src(FLOW_CREDITS, "Google Flow credit help")
    dreamina_i2v = src(DREAMINA_I2V, "Dreamina’s image-to-video page")
    dreamina_plans = src(DREAMINA_PLANS, "Dreamina plans")
    pika_src = src(PIKA_PLANS, "Pika’s pricing page")
    wan_home = src(WAN_HOME, "create.wan.video")
    wan_plans = src(WAN_PLANS, "Wan membership plans")
    hailuo_home = src(HAILUO_HOME, "hailuoai.video")
    hailuo_terms = src(HAILUO_TERMS, "Hailuo payment terms")
    runway_src = src(RUNWAY_PLANS, "Runway’s pricing page")
    kling_src = src(KLING_PLANS, "Kling membership plans")
    hf_src = src(HF_PLANS, "Higgsfield’s pricing page")
    luma_src = src(LUMA_PLANS, "Luma’s pricing page")
    grok_src = src(GROK_COM, "grok.com/imagine")
    xai_src = src(XAI_GROK, "x.ai/grok")
    aa_i2v = src(AA_I2V, "Artificial Analysis AA-Video-I2V v2.1")

    free_href = root("/guides/free-ai-video-generators/")
    seedance_href = root("/models/seedance-2-5/")
    veo_href = root("/models/veo-3-1/")
    hailuo_href = root("/models/minimax-hailuo/")
    wan_href = root("/models/wan-3-0/")
    kling_href = root("/models/kling-3-0/")
    grok_model = root("/models/grok-imagine/")
    omni_href = root("/models/gemini-omni-flash/")
    flow_calc = root("/guides/google-flow-credits-calculator/")

    def row(tool, i2v, limits, res, mark, source_html):
        return (
            "<tr>"
            f"<td>{tool}</td>"
            f"<td>{i2v}</td>"
            f"<td>{limits}</td>"
            f"<td>{res}</td>"
            f"<td>{mark}</td>"
            f"<td>{source_html}</td>"
            "</tr>"
        )

    table = f"""<div class="tblwrap" id="free-i2v-table">
<table style="min-width:1080px;width:1080px">
<thead><tr>
<th>Tool</th>
<th>Image-to-video on the free tier?</th>
<th>Published free-tier limits</th>
<th>Resolution</th>
<th>Watermark</th>
<th>Source</th>
</tr></thead>
<tbody>
{row(
    "Krea",
    "Yes, with a free account. The image-to-video page says generating needs a free Krea account.",
    "Free-plan models today: MiniMax H3 (up to 15s, start and end frame), Hailuo 2.3 Fast (up to 10s, start frame), and LTX-2 19B (up to 10s, start frame). A free account’s 100 daily compute units cover about two 5-second LTX-2 19B clips at 512p; one Hailuo 2.3 Fast or MiniMax H3 clip costs more than that. MiniMax H3 is on the free plan only during the current MiniMax promotion, with no end date published on that page. Seedance 2.5, Veo 3.1, Wan 3.0, and Kling 3.0 / 4.0 are marked paid-plan in Krea.",
    "Hailuo 2.3 Fast: up to 1080p. LTX-2 19B: up to 768p, with the worked free example at 512p. MiniMax H3: not stated on that row.",
    "Unknown. A watermark FAQ is on the page, but the answer was not expanded in this check.",
    f"{krea_i2v}, opened {e(CHECKED_WHEN)}. No credit card is required on the $0 plan, from {krea_plans}.",
)}
{row(
    "Google Flow (Veo 3.1 Lite, Omni Flash 1.2)",
    "Yes. Official help says you can animate images and add start and end frames or ingredients to a video prompt.",
    "50 Flow credits a day with or without a paid Google AI plan, shared across the account. Veo 3.1 Lite: frames-to-video (first, or first and last) at 4, 6, or 8 seconds; ingredients/references-to-video at 8 seconds only. All users can access Omni Flash models; Omni can generate or edit from text, frames, or ingredients, including a 360p option at one-third the credit cost of 720p. A Google account is required. Peak-hour video limits for people without a paid plan still apply.",
    "Veo 3.1 Lite is described as a 720p baseline. Omni Flash offers 360p and 720p. Higher paid lengths or upscales are not assumed here.",
    "Unknown on the help pages opened today.",
    f"{flow_create} · {flow_models} · {flow_credits}, opened {e(CHECKED_WHEN)}.",
)}
{row(
    "Dreamina",
    "The product page is an image-to-video generator, and the plans FAQ says Dreamina provides free daily credits for images and videos. The same image-to-video FAQ says trial or free credits may vary by account, region, and model, so the free I2V allotment is not a single published number.",
    "Unknown as a free-tier clip cap. Seedance 2.5 is described as supporting single clips up to 30 seconds and an ultra-long range of 5 to 180 seconds; that is a model capability, not a confirmed free-tier allowance. Sign-in is offered.",
    "Unknown on the free tier. The product page lets you pick duration, resolution, and aspect ratio in the live selector, without printing a free-tier cap.",
    "Unknown on the image-to-video page. Watermark removal was listed as a paid Basic benefit on the plans page in the Nov 15, 2026 free-tier check.",
    f"{dreamina_i2v} · {dreamina_plans}, opened {e(CHECKED_WHEN)}.",
)}
{row(
    "Pika",
    "Unknown as a clearly labeled free image-to-video allotment. The Free plan includes all models, no watermark, and 0 monthly credits, with credit packs available.",
    "0 monthly credits on Free, so you need a pack or some other credit grant to generate. Whether image input is included on Free without a pack is not stated.",
    "Unknown on Free.",
    "No watermark on Free, from the pricing page.",
    f"{pika_src}, opened {e(CHECKED_WHEN)}.",
)}
{row(
    "Wan",
    "The product UI lists First &amp; Last Frame and multimodal inputs, and the $0 plan includes daily check-in credits. That is not a complete published free I2V spec.",
    "Unknown. The page says “Log in to grab daily bonus” and “Free Credits inside,” with no published credit amount or I2V clip cap.",
    "The homepage control showed 720p in this check; whether that is a free-tier cap is unknown.",
    "Unknown on this check. Watermark-free export was a paid benefit on the Nov 15, 2026 membership-page check.",
    f"{wan_home} · {wan_plans}, opened {e(CHECKED_WHEN)}.",
)}
{row(
    "Hailuo (MiniMax)",
    "Unknown. The homepage has a Create Video box with reference slots and a sign-up offer of welcome credits. It does not clearly label a free image-to-video allotment.",
    "Unknown amount. Terms still say new accounts can get a one-time welcome package that expires after three days. There are no recurring monthly credits on Free.",
    "The homepage control showed 2K and 5s in this check; whether that is a free-tier cap is unknown.",
    "Yes for free downloads, from the terms (last updated July 14, 2025, and not re-dated today).",
    f"{hailuo_home} · {hailuo_terms}, opened {e(CHECKED_WHEN)}.",
)}
{row(
    "Runway, Kling, Higgsfield, Grok Imagine, Luma, Meta AI",
    f"Unknown for a published free image-to-video path, except Luma, which still lists no public free plan. Runway Free is 125 one-time credits for “a selection of generative creative models,” without naming image-to-video. Kling Basic is $0 with no monthly credits. Higgsfield lists a Free plan with limited use ({hf_src}). grok.com/imagine loaded a chat box with Sign in and Sign up; x.ai/grok returned 403.",
    "Unknown, or no public free plan (Luma).",
    "Unknown.",
    "Unknown.",
    f"{runway_src} · {kling_src} · {hf_src} · {grok_src} · {xai_src} · {luma_src}, opened {e(CHECKED_WHEN)}.",
)}
</tbody>
</table>
</div>"""

    a_q = (
        "The clearest published free image-to-video path today is Krea’s free "
        "account: you upload a photo, sign in, and generate with the models "
        "marked Free plan, using 100 compute units a day and no credit card. "
        "Google Flow also officially lets you animate images with frames or "
        "ingredients, on the 50 daily credits that come with a Google account. "
        "Dreamina has an image-to-video product and says it provides free daily "
        "credits, but the I2V FAQ warns that trial or free credits can vary, so "
        "this page does not invent a clip count. Everything else is unknown or "
        "has no public free plan. For the wider free-tier caps, watermarks, and "
        "paid steps, use the free AI video generators guide rather than this page."
    )
    a_how = (
        "Image-to-video AI takes a still photo as the starting picture and "
        "generates the frames that follow, usually with a short motion prompt. "
        "This guide only lists a tool when an official page says, or clearly "
        "shows, that you can start from an image on a free tier. Quality "
        "leaderboards such as Artificial Analysis’s image-to-video board are "
        "useful for paid-model comparisons; they are not a free-tier allotment."
    )
    a_best = (
        "If you want a documented free photo-to-video path with no card: Krea "
        "Free, using the models marked Free plan, with the unit math above. If "
        "you already have a Google account and want official frames-to-video "
        "help: Google Flow, at 50 credits a day, with Veo 3.1 Lite at 4, 6, or "
        "8 seconds in 720p, or Omni Flash including a 360p option. If you want "
        "Seedance image-to-video in a consumer app: Dreamina may give free or "
        "trial credits, but the amount is not a single published figure. If you "
        "only care about a watermark-free $0 plan, Pika Free has no watermark "
        "and 0 monthly credits, so it is not by itself a source of free I2V clips."
    )
    a_unknown = (
        "Unknown, and not guessed: a no-account image-to-video path; Krea’s "
        "watermark and commercial-use answers, which did not expand in this "
        "check; whether MiniMax H3 stays on Krea’s free plan after the current "
        "promotion; Dreamina’s free I2V credit amount, resolution cap, and "
        "whether the 30-second and 180-second figures apply on the free tier; "
        "Pika, Wan, Hailuo, Runway, Kling, Higgsfield, and Grok Imagine free "
        "image-to-video clip caps; Meta AI (not verified for video I2V today); "
        "and Luma, which has image-to-video on paid plans only."
    )

    faqs = [
        (QUESTION, a_q),
        ("How does free image-to-video AI work, and what does this page cover?", a_how),
        ("Which free image-to-video option is best for each use?", a_best),
        ("What is confirmed, and what is not?", a_unknown),
    ]
    for q, a in faqs:
        raw = (q + " " + a).lower()
        for bad in ("subscribe", "newsletter", "buttondown"):
            if bad in raw:
                raise SystemExit(f"{PATH} FAQ text contains {bad}")

    lead = (
        f"Animating a photo is different from a text-only free tier. This guide "
        f"covers which official tools offer image-to-video on a free tier, and "
        f"the limits, watermark, and resolution those pages actually publish. "
        f"Official pages were read {e(CHECKED_WHEN)}. It does not repeat the "
        f"full free-tier table; for credits, catch-alls, and paid steps see "
        f"<a href=\"{e(free_href)}\">free AI video generators: what you get</a>."
    )

    body = f"""<p class="small"><a href="{root("/guides/")}">Guides</a> › Free image to video</p>
<h1>{e(PHRASE)}</h1>
<p class="lead">{lead}</p>
<p class="small">Last checked {e(LAST)}. Official image-to-video pages were read {e(CHECKED_WHEN)}. Affiliate links never change this price order.</p>

<h2>{e(QUESTION)}</h2>
<p>{e(a_q)}</p>

<h2>How does free image-to-video AI work, and what does this page cover?</h2>
<p>{e(a_how)} {aa_i2v} is a public quality source if you want paid-model Elo; this page does not invent scores and does not rank free tiers by Elo.</p>

<h2>Free image-to-video tools, limits, watermark, and resolution</h2>
<p>One row per tool. A “yes” means an official page published a free way to start from an image. Anything those pages do not state is marked unknown.</p>
{table}
<p class="small">Sources and check time {e(CHECKED_WHEN)}: {flow_create} · {flow_models} · {flow_credits}.</p>

<h2>Which free image-to-video option is best for each use?</h2>
<p>{e(a_best)}</p>
<ul>
<li><b>A documented free photo-to-video path, no card.</b> Krea Free. {krea_i2v} · {krea_plans}. Related: <a href="{e(hailuo_href)}">MiniMax Hailuo model page</a>.</li>
<li><b>Official frames-to-video on a daily credit grant.</b> Google Flow, with a Google account and 50 daily credits. Related: <a href="{e(flow_calc)}">Google Flow credits calculator</a> · <a href="{e(veo_href)}">Veo 3.1</a> · <a href="{e(omni_href)}">Gemini Omni Flash</a>.</li>
<li><b>Seedance in a consumer app.</b> Dreamina’s image-to-video page, with free or trial credits that can vary. {dreamina_i2v} · {dreamina_plans}. <a href="{e(seedance_href)}">Seedance 2.5 model page</a>.</li>
<li><b>If you only wanted a watermark-free $0 plan.</b> Pika Free has no watermark and 0 monthly credits, so it is not a published free I2V allotment. {pika_src}.</li>
</ul>
<p>Related: <a href="{e(free_href)}">free AI video generators: what you get</a> · <a href="{e(wan_href)}">Wan 3.0 model page</a> · <a href="{e(kling_href)}">Kling 3.0 model page</a> · <a href="{e(grok_model)}">Grok Imagine model page</a>.</p>

<h2>What is confirmed, and what is not?</h2>
<p>{e(a_unknown)}</p>
<p><b>Confirmed {e(CHECKED_WHEN)} on official pages:</b> Krea’s free-plan image-to-video models and unit example; Flow’s frames and ingredients help, Veo 3.1 Lite lengths, and Omni 360p option; Dreamina’s I2V product page and variable free/trial credit language; Pika Free’s all-models / no-watermark / 0-credit plan; Luma’s lack of a public free plan. <b>Not confirmed:</b> the unknowns listed above.</p>
<p class="small">Affiliate links never change this price order.</p>
{g["how_block"]()}
"""

    if "sora" in body.lower() or "sora" in description(g).lower() or "sora" in PHRASE.lower():
        raise SystemExit(f"{PATH} source would name Sora")

    title = g["page_title"](PHRASE)
    desc = description(g)
    g["guide_page"](PATH, title, desc, body, faqs)
    return PATH
