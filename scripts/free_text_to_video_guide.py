"""Guide: Free text to video AI.

Imported by scripts/build_site.py. Official text-to-video pages were read
on 2026-11-17. This page never names Sora.
"""

PATH = "/guides/free-text-to-video-ai/"
LABEL = "Free text to video"
PHRASE = "Free text to video AI"
QUESTION = "Which free AI tools turn text into video?"
CHECKED = "2026-11-17"
CHECKED_WHEN = "Nov 17, 2026, 9:49–9:57 AM ET (6:49–6:57 AM PT)"

FLOW_CREATE = "https://support.google.com/flow/answer/16353334?hl=en"
FLOW_MODELS = "https://support.google.com/flow/answer/16352836?hl=en"
FLOW_CREDITS = "https://support.google.com/flow/answer/16526234?hl=en"
GOOGLE_AI_PLANS = "https://one.google.com/about/google-ai-plans/"
KREA_VIDEO = "https://www.krea.ai/features/ai-video-generator"
KREA_PLANS = "https://www.krea.ai/pricing"
KREA_I2V = "https://www.krea.ai/apps/image-to-video"
DREAMINA_T2V = "https://dreamina.capcut.com/ai-video/make-text-to-video-with-free-credits"
DREAMINA_PLANS = "https://dreamina.capcut.com/plans"
PIKA_PLANS = "https://pika.art/pricing"
WAN_PLANS = "https://create.wan.video/pricing?whereToMemberShip=membership_plans"
HAILUO_TERMS = "https://hailuoai.video/doc/payment-policy.html"
RUNWAY_PLANS = "https://runway.com/pricing"
KLING_PLANS = "https://kling.ai/app/membership/membership-plan"
HF_PLANS = "https://higgsfield.ai/pricing"
LUMA_PLANS = "https://lumalabs.ai/pricing"
XAI_GROK = "https://x.ai/grok"
XAI_PRICING = "https://x.ai/pricing"
GROK_APP = "https://apps.apple.com/us/app/id6670324846"
META_AI = "https://ai.meta.com/meta-ai/"
AA_T2V = "https://artificialanalysis.ai/video/leaderboard/text-to-video"

CATALOG_PAID = ("r096", "r209", "r146", "r023", "r025", "r024")


def _src(g, url, text="source"):
    e = g["e"]
    href, rel = g["outbound"](url)
    return f'<a href="{e(href)}" rel="{rel}" target="_blank">{e(text)}</a>'


def _row_by_id(g, rid):
    for r in g["rows"]:
        if r["id"] == rid:
            return r
    raise SystemExit(f"{PATH} missing catalog row {rid}")


def blurb(g):
    return (
        "Which official free tiers actually turn a text prompt into video, with "
        "the limits, watermark, resolution, and audio the vendor published."
    )


def description(g):
    text = (
        "Free text to video AI: which free tiers turn a prompt into video, "
        "with daily limits, resolution, audio, and watermarks. Last checked Nov 17, 2026."
    )
    if len(text) > 160:
        raise SystemExit(f"{PATH} meta description is over 160 characters: {len(text)}")
    return text


def render(g):
    e, root, LAST = g["e"], g["root"], g["LAST"]
    rate_money, rate_label = g["rate_money"], g["rate_label"]
    shown_resolution, shown_audio = g["shown_resolution"], g["shown_audio"]
    dates = [CHECKED, LAST]
    g["SITEMAP_LASTMOD"][PATH] = max(dates)

    def src(url, text="source"):
        return _src(g, url, text)

    flow_create = src(FLOW_CREATE, "Create videos in Google Flow")
    flow_models = src(FLOW_MODELS, "Google Flow models and supported features")
    flow_credits = src(FLOW_CREDITS, "Google Flow credit help")
    google_plans = src(GOOGLE_AI_PLANS, "Google AI plans")
    krea_video = src(KREA_VIDEO, "Krea’s AI video generator page")
    krea_plans = src(KREA_PLANS, "Krea’s pricing page")
    krea_i2v = src(KREA_I2V, "Krea’s image-to-video page")
    dreamina_t2v = src(DREAMINA_T2V, "Dreamina’s text-to-video guide")
    dreamina_plans = src(DREAMINA_PLANS, "Dreamina plans")
    pika_src = src(PIKA_PLANS, "Pika’s pricing page")
    wan_plans = src(WAN_PLANS, "Wan membership plans")
    hailuo_terms = src(HAILUO_TERMS, "Hailuo subscription service terms")
    runway_src = src(RUNWAY_PLANS, "Runway’s pricing page")
    kling_src = src(KLING_PLANS, "Kling membership plans")
    hf_src = src(HF_PLANS, "Higgsfield’s pricing page")
    luma_src = src(LUMA_PLANS, "Luma’s pricing page")
    xai_grok = src(XAI_GROK, "x.ai/grok")
    grok_app = src(GROK_APP, "Grok on the App Store")
    xai_pricing = src(XAI_PRICING, "x.ai/pricing")
    meta_src = src(META_AI, "Meta AI assistant page")
    aa_t2v = src(AA_T2V, "Artificial Analysis AA-Video-T2V v2.1 leaderboard")

    free_href = root("/guides/free-ai-video-generators/")
    i2v_href = root("/guides/free-image-to-video-ai/")
    flow_calc = root("/guides/google-flow-credits-calculator/")
    seedance_href = root("/models/seedance-2-5/")
    veo_href = root("/models/veo-3-1/")
    hailuo_href = root("/models/minimax-hailuo/")
    wan_href = root("/models/wan-3-0/")
    grok_model = root("/models/grok-imagine/")
    omni_href = root("/models/gemini-omni-flash/")
    cheapest_href = root("/guides/cheapest-ai-video-generator/")
    best_href = root("/guides/best-ai-video-generator/")
    grok_guide = root("/guides/grok-imagine-video-cost/")
    wan_cheap = root("/guides/cheapest-wan-3-0/")
    budget_href = root("/guides/ai-video-project-budget/")
    runway_guide = root("/guides/runway-pricing/")
    calc_veo = root("/calculator/?model=veo-3-1&seconds=8")

    def trow(*cells):
        return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"

    free_table = f"""<div class="tblwrap" id="free-t2v-table">
<table style="min-width:1200px;width:1200px">
<thead><tr>
<th>Tool</th>
<th>Text-to-video on the free tier?</th>
<th>Published free-tier limits</th>
<th>Resolution</th>
<th>Audio</th>
<th>Watermark</th>
<th>Source</th>
</tr></thead>
<tbody>
{trow(
    "Google Flow (Omni Flash 1.2, Veo 3.1 Lite)",
    "Yes. The models help page lists Text to Video “without a Google AI subscription” on Omni Flash 1.2, and Text to Video on Veo 3.1 Lite, which all users can use.",
    "50 Flow credits a day with or without a paid Google AI plan. Unused daily credits do not roll over, and the refresh is triggered by your first generation. Veo 3.1 Lite: 10 credits per 4, 6, or 8 second clip for non-Ultra users, so about 5 clips a day if every credit goes to Lite. Omni Flash 1.2: 3 to 10 seconds per clip without a paid plan, at 1 credit per second in 360p (about 50 seconds a day) or 3 credits per second in 720p (about 16 seconds a day, 48 credits). During peak hours, roughly 2 PM to 5 PM UTC, people without a paid plan may not be able to generate video. Credits are tied to your Google account.",
    "Veo 3.1 Lite: 720p. Omni Flash 1.2: 360p or 720p. Upscaling to 1080p needs a Plus, Pro, or Ultra plan.",
    "Not stated for free clips. The models page lists custom voices as an Omni Flash feature, with regional limits. Neither help page says whether a free clip includes a soundtrack.",
    "Unknown on the help pages read today.",
    f"{flow_models} · {flow_credits} · {flow_create}, read {e(CHECKED_WHEN)}.",
)}
{trow(
    "Krea",
    "Yes, with a free account. Krea’s AI video generator page says to create a free account, open the Video Tool, type your prompt, pick one of the free video models, and generate.",
    "100 compute units a day on the $0 plan, with no credit card required. Which free video models accept a text-only prompt, and how many units a text-to-video clip costs, are not published on that page. Krea’s image-to-video page names the models marked Free plan in its video tool (MiniMax H3, only during the current MiniMax promotion; Hailuo 2.3 Fast; LTX-2 19B) and says 100 daily units cover about two 5-second LTX-2 19B clips at 512p. That example is stated for image-to-video. Seedance 2.5 and Veo 3.1 need Pro or higher. Videos made on the free plan are for personal use.",
    "Unknown for a free text-to-video clip. LTX-2 19B, which Krea calls the most affordable model on the free plan, renders at 512p or 768p.",
    "Unknown on Free. Krea says supported models generate sound, and names Veo 3.1, which needs Pro or higher.",
    "No. Krea says it does not add a watermark to the videos you generate, on the free plan or on paid plans.",
    f"{krea_video} · {krea_plans} · {krea_i2v}, read {e(CHECKED_WHEN)}.",
)}
{trow(
    "Dreamina",
    "Yes, according to Dreamina’s own text-to-video guide (dated Nov 13, 2026): you can make a video from text without buying a paid plan, using the daily free credits and the text-to-video route in the video creator.",
    "Free daily credits with no upfront payment, on the plans page. The guide says 120 credits a day in the US, with different allowances in other regions, and calls that a starting budget, not a fixed number of videos. It also says a daily allowance does not mean every premium model or long duration is free. Credits per clip: unknown.",
    "Unknown on the free tier.",
    "Unknown as a rule. In the guide’s own free-account example, with a model it calls 1.0 Mini, clips of about five seconds had no audio track.",
    "Yes in that same example: the guide says the clips had a watermark. Watermark removal was listed as a paid Basic benefit in the Nov 15, 2026 check.",
    f"{dreamina_t2v} · {dreamina_plans}, read {e(CHECKED_WHEN)}.",
)}
{trow(
    "Grok Imagine",
    "Unknown. The product page says Grok is “free to try on the web and in the apps” and lists text-to-video up to 15 seconds at 720p. The plan grid read Nov 12, 2026 PT listed video generation as not included on Free.",
    "No free clip or credit allowance is published.",
    "720p for text-to-video on the product page. A separate Imagine blurb says up to 2K. Which applies to a free trial is not stated.",
    "Not stated for a free trial. The App Store listing says Grok can create short videos with sound.",
    "Unknown.",
    f"{xai_grok} · {grok_app}, read {e(CHECKED_WHEN)}. {xai_pricing}, read Nov 12, 2026 PT, in <a href=\"{e(grok_guide)}\">how much a Grok Imagine video costs</a>.",
)}
{trow(
    "Pika",
    "Not from the plan itself. Free is $0 with all models and 0 monthly credits (credit packs only).",
    "0 monthly credits. Packs are 60 credits per $1 on every plan. 2 video jobs in parallel.",
    "Depends on the model. The pricing table lists Pika H3 Flex at 768p and Pika 2.5 at 720p for 5-second clips.",
    "Not stated per video model in the pricing table.",
    "No watermark on Free. A commercial license is not included on Free.",
    f"{pika_src}, read {e(CHECKED_WHEN)}.",
)}
{trow(
    "Runway",
    "Unknown. Free includes “a selection of generative creative models to test concepts,” without naming text-to-video.",
    "125 one-time credits. They are not a monthly refill.",
    "Unknown on Free.",
    "Unknown on Free.",
    "Unknown on Free. “No watermarks” is listed on Standard, not on Free.",
    f"{runway_src}, read {e(CHECKED_WHEN)}.",
)}
{trow(
    "Hailuo (MiniMax)",
    "Unknown as a labeled free text-to-video allowance. The terms say free users who log in get basic features that include video generation.",
    "A one-time welcome package of free credits for new accounts, which expires three days after it is granted. The amount is not stated.",
    "Unknown on Free.",
    "Unknown on Free.",
    "Yes. Free-user downloads include a watermark, from the terms (last updated July 14, 2025).",
    f"{hailuo_terms}, read {e(CHECKED_WHEN)}.",
)}
{trow(
    "Wan, Kling AI, Higgsfield",
    "Unknown. These three plan pages are filled in by script and did not load in the Nov 17, 2026 check, so nothing in this row was re-read that day.",
    "From the Nov 15, 2026 check: Wan’s $0 plan gives daily check-in credits of an unpublished amount; Kling Basic is $0 with no monthly credits; Higgsfield Free lists 0 monthly credits.",
    "Unknown.",
    "Unknown.",
    "Unknown on Nov 17, 2026. In the Nov 15, 2026 check, watermark removal was a paid benefit on Wan and on Kling.",
    f"{wan_plans} · {kling_src} · {hf_src}, last read Nov 15, 2026 in <a href=\"{e(free_href)}\">free AI video generators: what you get</a>; not loaded Nov 17, 2026.",
)}
{trow(
    "Luma, Meta AI",
    "Luma: no. No public free plan is listed; individual plans start at Plus, $30 a month, with 10,000 credits. Meta AI: unknown; the Meta AI page returned an error on Nov 17, 2026.",
    "None published.",
    "Not applicable for Luma. Unknown for Meta AI.",
    "Not applicable for Luma. Unknown for Meta AI.",
    "Not applicable for Luma. Unknown for Meta AI.",
    f"{luma_src}, read {e(CHECKED_WHEN)}. {meta_src} returned an error on Nov 17, 2026.",
)}
</tbody></table></div>"""

    def catalog_cells(rid, route, model_input, assumption):
        r = _row_by_id(g, rid)
        audio = shown_audio(r)
        audio_txt = "with audio" if audio == "with" else ("without audio" if audio == "without" else "not stated")
        label = rate_label(r)
        href, rel = g["outbound"](r["source_url"])
        source = (
            f'<a href="{e(href)}" rel="{rel}" target="_blank">source</a>, '
            f"catalog row {e(rid)}, checked {e(r['checked'])} PT."
        )
        return (
            float(r["usd_per_second"]),
            trow(
                route,
                model_input,
                e(shown_resolution(r)),
                e(audio_txt),
                f"{e(rate_money(r['usd_per_second']))}/s {e(label)}",
                assumption,
                source,
            ),
        )

    paid_bits = []
    paid_bits.append(catalog_cells(
        "r096",
        "Higgsfield plan · Ultra (annual), $50 a month for 3,000 credits",
        "Wan 3.0, 5-second clip. Input type not stated.",
        "Assumes every credit you pay for is used. 5 credits per clip.",
    ))
    paid_bits.append(catalog_cells(
        "r209",
        "xAI API · pay as you go",
        "Grok Imagine Video 1.5 Lite. Text or image input.",
        "Billed per second of output, for 1 to 15 seconds, so no credits go unused. Retries are billed too.",
    ))
    paid_bits.append(catalog_cells(
        "r146",
        "Krea plan · Basic (yearly), $5 a month for 5,000 units",
        "Veo 3.1 Lite, 4-second clip. Input type not stated.",
        "Assumes every unit you pay for is used. Krea publishes approximate clip counts, so units per clip are derived.",
    ))

    flow = (g.get("db") or {}).get("flow") or {}
    plans = flow.get("plans") or {}
    plus = plans.get("gflow-plus") or {}
    pro = plans.get("gflow-pro") or {}
    # Veo 3.1 Lite, 8s, 10 credits (non-Ultra), monthly credits only.
    def flow_rate(plan):
        usd = float(plan["usd_month"])
        credits = float(plan["credits_month"])
        return usd / credits * 10.0 / 8.0

    pro_rate = flow_rate(pro)
    plus_rate = flow_rate(plus)
    paid_bits.append((
        pro_rate,
        trow(
            f"Google Flow · {e(pro['plan'])}, {e(g['cost_money'](pro['usd_month']))} a month for {e(str(int(pro['credits_month'])))} credits",
            "Veo 3.1 Lite, 8-second clip. Text-to-video is supported.",
            "720p",
            "not stated",
            f"{e(rate_money(pro_rate))}/s from credit plan",
            f"{e(g['cost_money'](pro['usd_month']))} ÷ {e(str(int(pro['credits_month'])))} credits × 10 credits ÷ 8 seconds. Assumes every monthly credit goes to 8-second Lite clips. The 50 daily credits are not counted.",
            f"{google_plans}, checked {e(pro['checked'])} PT · {flow_credits}, read 2026-11-17. Not a catalog row; figured from the Flow plan data in prices.json.",
        ),
    ))
    paid_bits.append(catalog_cells(
        "r023",
        "fal API · pay as you go",
        "MiniMax H3 Max Turbo. Text-to-video.",
        "Billed per second of output. Retries are billed too.",
    ))
    paid_bits.append((
        plus_rate,
        trow(
            f"Google Flow · {e(plus['plan'])}, {e(g['cost_money'](plus['usd_month']))} a month for {e(str(int(plus['credits_month'])))} credits",
            "Veo 3.1 Lite, 8-second clip. Text-to-video is supported.",
            "720p",
            "not stated",
            f"{e(rate_money(plus_rate))}/s from credit plan",
            f"{e(g['cost_money'](plus['usd_month']))} ÷ {e(str(int(plus['credits_month'])))} credits × 10 credits ÷ 8 seconds. Assumes every monthly credit goes to 8-second Lite clips. The 50 daily credits are not counted.",
            f"{google_plans}, checked {e(plus['checked'])} PT · {flow_credits}, read 2026-11-17. Not a catalog row; figured from the Flow plan data in prices.json.",
        ),
    ))
    pika_pack_rate = 10.0 / 60.0 / 5.0
    paid_bits.append((
        pika_pack_rate,
        trow(
            "Pika · credit pack bought on the Free plan, 60 credits per $1",
            "Pika H3 Flex, 5-second clip. Input type not stated.",
            "768p",
            "not stated",
            f"{e(rate_money(pika_pack_rate))}/s from credit pack",
            "10 credits per clip ÷ 60 credits per $1 = $0.167 per clip. Assumes you use the pack credits you buy.",
            f"{pika_src}, read 2026-11-17. Not a catalog row; figured from Pika’s pricing page.",
        ),
    ))
    paid_bits.append(catalog_cells(
        "r025",
        "Replicate API · pay as you go",
        "Wan 3.0. Text or image input.",
        "Billed per second of output, for clips of 2 to 30 seconds. Retries are billed too.",
    ))
    paid_bits.append(catalog_cells(
        "r024",
        "fal API · pay as you go",
        "Grok Imagine Video 1.5. Text-to-video.",
        "Billed per second of output. Retries are billed too.",
    ))
    paid_bits.sort(key=lambda item: item[0])
    paid_table = f"""<div class="tblwrap" id="paid-t2v-table">
<table style="min-width:1200px;width:1200px">
<thead><tr>
<th>Route and tier</th>
<th>Model and input</th>
<th>Resolution</th>
<th>Audio</th>
<th>Rate</th>
<th>Usage assumption</th>
<th>Source and date checked</th>
</tr></thead>
<tbody>
{''.join(html for _usd, html in paid_bits)}
</tbody></table></div>"""

    a_q = (
        "Google Flow and Krea are the two free tiers that clearly publish "
        "text-to-video today. Google Flow’s help pages list Text to Video for "
        "people without a paid Google AI plan on both Omni Flash 1.2 (3 to 10 "
        "seconds) and Veo 3.1 Lite (4, 6, or 8 seconds at 720p), paid for from "
        "50 credits a day. Krea says a free account can open its Video Tool, "
        "type a prompt, pick one of the free video models, and generate, using "
        "100 compute units a day with no credit card and no watermark. "
        "Dreamina’s own guide says you can make a video from text with its "
        "free daily credits, 120 a day in the US, but it does not publish what "
        "a clip costs. Grok says it is free to try, with no published free "
        "video allowance. Pika Free has 0 monthly credits, Runway’s 125 "
        "credits are one-time, and Luma has no public free plan. Everything "
        "else is unknown."
    )
    a_how = (
        "Text-to-video AI generates a short clip from a written description "
        "alone, so the model decides how everything looks. This guide lists a "
        "tool as a yes only when an official page says, or clearly shows, that "
        "a text prompt can make a video on the free tier. Free tiers are paid "
        "for in daily credits, one-time credits, or compute units, and a clip "
        "count is given only when the vendor publishes both the allowance and "
        "what a clip costs. Quality scores come from Artificial Analysis’s "
        "text-to-video board and are quoted only for models a free tier or a "
        "priced row actually offers. Scores on this page are copied from that "
        "board, as opened Nov 17, 2026, with their 95% interval and rank "
        "range. This page does not invent scores, and it does not rank free "
        "tiers by Elo."
    )
    a_best = (
        "For a daily allowance you can count, and the highest published quality "
        "score we could confirm on a free allowance: Google Flow. For no "
        "credit card and no watermark: Krea Free, for personal use. For the "
        "Seedance family in a consumer app: Dreamina, with a clip count that "
        "is not published. For a watermark-free export on a $0 plan: Pika, but "
        "only after you buy a credit pack. For a one-time trial: Runway’s 125 "
        "credits. A best-for or not-for line is given only where a vendor page "
        "or a cited score supports it."
    )
    a_cost = (
        "Less than most first paid plans suggest, if you can use an API or a "
        "multi-model plan. The cheapest catalog row in the table is $0.0167 "
        "per second for Wan 3.0 on Higgsfield Ultra (annual) at 480p, audio "
        "not stated, but that row does not state input type. The lowest rate "
        "in our catalog whose vendor page states text-to-video input is $0.02 "
        "per second for Grok Imagine Video 1.5 Lite on the xAI API at 480p, "
        "audio not stated, billed per second of output. MiniMax H3 Max Turbo "
        "is $0.025 per second on fal at 480p, and Wan 3.0 is $0.035 per "
        "second on Replicate at 480p. On Google Flow, an 8-second Veo 3.1 "
        "Lite clip at 720p works out to $0.025 per second on Google AI Pro, "
        "if you use every monthly credit. Each row in the table states its "
        "tier, resolution, audio, and usage assumption."
    )
    a_unknown = (
        "Unknown, and not guessed: whether any free clip includes sound, as a "
        "rule stated by the vendor; Google Flow’s watermark on the help pages "
        "read Nov 17, 2026; which of Krea’s free video models accept a "
        "text-only prompt, and how many units a text-to-video clip costs; "
        "Dreamina’s credits per clip and free resolution; whether Grok’s free "
        "trial includes video; which models Runway’s 125 one-time credits can "
        "buy; Hailuo’s welcome-credit amount; and the Wan, Kling, and "
        "Higgsfield free tiers, whose plan pages did not load in the Nov 17, "
        "2026 check. Meta AI was not verified that day."
    )

    faqs = [
        (QUESTION, a_q),
        ("How does free text-to-video AI work, and what does this page cover?", a_how),
        ("Which free text-to-video option is best for each use?", a_best),
        ("What does text-to-video cost when the free tier runs out?", a_cost),
        ("What is confirmed, and what is not?", a_unknown),
    ]
    for q, a in faqs:
        raw = (q + " " + a).lower()
        for bad in ("subscribe", "newsletter", "buttondown"):
            if bad in raw:
                raise SystemExit(f"{PATH} FAQ text contains {bad}")

    lead = (
        f"Google Flow and Krea are the two free tiers that clearly publish "
        f"text-to-video today. Flow gives 50 credits a day, about five Veo 3.1 "
        f"Lite clips at 720p if every credit goes to Lite, from {flow_credits}. "
        f"Krea gives 100 compute units a day with no credit card and no "
        f"watermark, for personal use, from {krea_video}. Official pages were "
        f"read {e(CHECKED_WHEN)}. Anything a vendor did not publish is marked "
        f"unknown. This page does not repeat the full free-tier table; for "
        f"sign-up rules and every plan see "
        f"<a href=\"{e(free_href)}\">free AI video generators: what you get</a>, "
        f"and to start from a photo see "
        f"<a href=\"{e(i2v_href)}\">free image to video AI</a>."
    )

    takeaways = f"""<div class="card" id="takeaways">
<h2>Key takeaways</h2>
<ul>
<li><b>A daily allowance you can count.</b> Google Flow: 50 credits a day, about five Veo 3.1 Lite clips (4, 6, or 8 seconds, 720p), or about 16 seconds of Omni Flash 1.2 at 720p, if you spend every credit on one model.</li>
<li><b>No card, no watermark.</b> Krea Free: 100 compute units a day. Krea says free-plan videos are for personal use. What a text-to-video clip costs in units is not published.</li>
<li><b>Daily credits, clip count unknown.</b> Dreamina. A Dreamina guide says 120 credits a day in the US; the cost of a clip is not published.</li>
<li><b>Not a source of free clips.</b> Pika Free has 0 monthly credits, Runway’s 125 credits are one-time, and Luma lists no public free plan.</li>
<li><b>Audio.</b> No vendor we read states, as a rule, whether a free clip includes sound, so audio is marked not stated or unknown on every free row.</li>
<li><b>After the free tier.</b> The cheapest catalog row in the paid table is $0.0167/s for Wan 3.0 on Higgsfield Ultra (annual) at 480p, audio not stated, input type not stated. The lowest catalog rate whose vendor page states text-to-video input is $0.02/s (Grok Imagine Video 1.5 Lite, xAI API, 480p, audio not stated, billed per second of output).</li>
</ul>
</div>"""

    next_steps = f"""<div class="card" id="next-steps">
<h2>What to do next</h2>
<ul>
<li><b>Check the vendor page.</b> Free allowances change without notice. Confirm today’s numbers on {flow_credits} or {krea_plans} before you plan around them.</li>
<li><b>Try the calculator.</b> Put your clip length into the <a href="{e(calc_veo)}">credit calculator for Veo 3.1 at 8 seconds</a>, or the <a href="{e(flow_calc)}">Google Flow credits calculator</a>, to see what the paid step costs you.</li>
<li><b>Open the model page.</b> Every current rate, with its source and date: <a href="{e(veo_href)}">Veo 3.1</a> · <a href="{e(omni_href)}">Gemini Omni Flash</a> · <a href="{e(wan_href)}">Wan 3.0</a> · <a href="{e(grok_model)}">Grok Imagine</a>.</li>
</ul>
</div>"""

    body = f"""<p class="small"><a href="{root("/guides/")}">Guides</a> › Free text to video</p>
<h1>{e(PHRASE)}</h1>
<p class="lead">{lead}</p>
<p class="small">Last checked {e(LAST)}. Official pages were read {e(CHECKED_WHEN)}. Catalog paid-step rows use the date on each row. Affiliate links never change this price order. Every dollar-per-second figure below states its usage assumption, tier, resolution, and audio.</p>
{takeaways}

<h2>{e(QUESTION)}</h2>
<p>{e(a_q)}</p>

<h2>How does free text-to-video AI work, and what does this page cover?</h2>
<p>{e(a_how)} {aa_t2v} ranks models on generating video with audio from a text prompt, using Elo from pairwise human preference votes.</p>

<h2>Free text-to-video tools: limits, resolution, audio, and watermark</h2>
<p>One row per tool. A “yes” means an official page published a free way to make a video from a text prompt. Anything those pages do not state is marked unknown.</p>
{free_table}
<p class="small">Sources and check time {e(CHECKED_WHEN)}, except where a cell gives an earlier date.</p>

<h2>Which free text-to-video option is best for each use?</h2>
<p>{e(a_best)}</p>
<ul>
<li><b>Google Flow.</b> Best for: a daily allowance you can count (50 credits, about five Veo 3.1 Lite clips), and the highest published text-to-video score we could confirm on a free allowance: Gemini Omni Flash 1.2 at Elo 1151 ±14 (rank range 3–9, 5,634 samples) on {aa_t2v}. Not for: a top score from Lite, since Veo 3.1 Lite is Elo 949 ±14 (rank range 26–30) on the same board; generating between roughly 2 PM and 5 PM UTC without a paid plan; or clips longer than 10 seconds. {flow_models} · {flow_credits}. Related: <a href="{e(flow_calc)}">Google Flow credits calculator</a> · <a href="{e(veo_href)}">Veo 3.1</a> · <a href="{e(omni_href)}">Gemini Omni Flash</a>.</li>
<li><b>Krea Free.</b> Best for: no credit card and no watermark, both stated by Krea. Not for: commercial work, since Krea says videos made on the free plan are for personal use, or for Seedance 2.5 and Veo 3.1, which need Pro or higher. {krea_video} · {krea_plans}. MiniMax H3 (768p) is Elo 1159 ±13 (rank range 2–7) on the same board, and Krea’s image-to-video page marks MiniMax H3 as Free plan during the current MiniMax promotion; whether it accepts a text-only prompt on Free is unknown. Related: <a href="{e(hailuo_href)}">MiniMax Hailuo model page</a>.</li>
<li><b>Dreamina.</b> Best for: the Seedance family in a consumer app with daily credits, as Dreamina states. Not for: planning a clip count ahead of time, since credits per clip are not published, or a clean file from the free example, which Dreamina’s own guide says had a watermark and no audio track. {dreamina_t2v} · {dreamina_plans}. Related: <a href="{e(seedance_href)}">Seedance 2.5 model page</a>.</li>
<li><b>Pika.</b> Best for: a watermark-free export on a $0 plan once you buy a pack; Pika H3 Flex is Elo 1124 ±14 (rank range 11–15) on the same board. Not for: free clips, since Free has 0 monthly credits and no commercial license. {pika_src}.</li>
<li><b>Runway.</b> Best for: a single trial session on 125 one-time credits. Not for: recurring free use. Runway’s own models were not on the board read Nov 17, 2026, so their quality is unknown here. {runway_src}. Related: <a href="{e(runway_guide)}">Runway pricing per second</a>.</li>
</ul>
<p>No line given. Grok Imagine, Hailuo, Wan, Kling, and Higgsfield do not publish a free text-to-video allowance on the pages we could read, so this page gives them no best-for or not-for line.</p>

<h2>What does text-to-video cost when the free tier runs out?</h2>
<p>{e(a_cost)}</p>
{paid_table}
<p>Rows are in price order. A plan rate assumes you use what you pay for; an API rate is billed per second of output. The with-audio row is listed because it is the cheapest text-to-video row in the catalog whose vendor page states audio. Affiliate links never change this price order.</p>
<p>Related: <a href="{e(cheapest_href)}">cheapest rate we track for each model</a> · <a href="{e(best_href)}">best AI video generator by value</a> · <a href="{e(grok_guide)}">Grok Imagine video cost</a> · <a href="{e(wan_cheap)}">cheapest Wan 3.0</a> · <a href="{e(budget_href)}">project budget calculator</a>.</p>

<h2>What is confirmed, and what is not?</h2>
<p>{e(a_unknown)}</p>
<p><b>Confirmed {e(CHECKED_WHEN)} on official pages:</b> Flow’s Text to Video support without a paid Google AI plan, its 50 daily credits, and the Lite and Omni Flash 1.2 credit costs; Krea’s free text-to-video path, 100 units a day, no card, no watermark, and personal-use rule; Dreamina’s free daily credits and the 120-a-day US figure on a Dreamina guide; Pika Free’s 0 monthly credits, no watermark, and 60-credits-per-$1 packs; Runway’s 125 one-time credits; Hailuo’s watermarked free downloads and three-day welcome credits; Luma’s lack of a public free plan. <b>Confirmed {e(CHECKED_WHEN)} on Artificial Analysis:</b> the Elo figures, intervals, and rank ranges quoted above. <b>Carried from earlier checks, with their dates:</b> the Wan, Kling, and Higgsfield rows (Nov 15, 2026), the Grok plan grid (Nov 12, 2026 PT), and the catalog rows (2026-11-16).</p>
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
