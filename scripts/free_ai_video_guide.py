"""Guide: Free AI video generators: what you get.

Imported by scripts/build_site.py. Official free-tier facts were read from
vendor pages on 2026-11-15. Catalog paid-step rates come from data/prices.json
and were last fully checked 2026-11-14. This page never names Sora.
"""
from decimal import Decimal, ROUND_HALF_UP

PATH = "/guides/free-ai-video-generators/"
LABEL = "Free AI video generators"
PHRASE = "Free AI video generators: what you get"
QUESTION = "What do you actually get from a free AI video generator?"
CHECKED = "2026-11-15"
CHECKED_WHEN = (
    "Nov 15, 2026, 10:24–10:32 AM America/Caracas (6:24–6:32 AM PT)"
)

# Official pages opened on CHECKED.
FLOW_CREDITS = "https://support.google.com/flow/answer/16526234?hl=en"
GOOGLE_AI_PLANS = "https://one.google.com/about/google-ai-plans/"
KREA_PLANS = "https://www.krea.ai/pricing"
RUNWAY_PLANS = "https://runway.com/pricing"
DREAMINA_PLANS = "https://dreamina.capcut.com/plans"
DREAMINA_FREE = "https://dreamina.capcut.com/ai-video/make-text-to-video-with-free-credits"
DREAMINA_PRICE = "https://dreamina.capcut.com/pricing/dreamina-price"
KLING_PLANS = "https://kling.ai/app/membership/membership-plan"
HF_PLANS = "https://higgsfield.ai/pricing"
PIKA_PLANS = "https://pika.art/pricing"
HAILUO_TERMS = "https://hailuoai.video/doc/payment-policy.html"
HAILUO_PLANS = "https://hailuoai.video/pricing"
XAI_GROK = "https://x.ai/grok"
GROK_COM = "https://grok.com/"
WAN_PLANS = "https://create.wan.video/pricing?whereToMemberShip=membership_plans"
LUMA_PLANS = "https://lumalabs.ai/pricing"
META_AI = "https://www.meta.ai/"
META_ABOUT = "https://ai.meta.com/meta-ai/"

# Catalog row ids for the cheapest paid step we track (prices.json, last full check 2026-11-14).
ROW_VEO = "r146"          # Krea Veo 3.1 Lite Basic yearly 720p estimate $0.02222/s
ROW_KLING = "r111"        # Higgsfield Ultra annual Kling 3.0 720p estimate $0.0325/s
ROW_WAN = "r096"          # Higgsfield Ultra annual Wan 3.0 480p verified $0.02167/s
ROW_HAILUO = "r194"       # fal MiniMax H3 Max Turbo 480p promo $0.0175/s through Nov 15
ROW_GROK = "r055"         # Runway API grok_imagine_1_5_lite 480p verified $0.02/s
ROW_RUNWAY = "r047"       # Runway API gen4_turbo verified $0.05/s
ROW_SEEDANCE = "r202"     # Replicate seedance-2.5 non_video_in 480p verified $0.1028/s
ROW_OMNI = "r199"         # Google Gemini API gemini-omni-1.2-flash 720p estimate $0.07/s


def _src(g, url, text="source"):
    e = g["e"]
    href, rel = g["outbound"](url)
    return f'<a href="{e(href)}" rel="{rel}" target="_blank">{e(text)}</a>'


def usd(v, places=2):
    q = Decimal("1").scaleb(-places)
    n = Decimal(str(v)).quantize(q, rounding=ROUND_HALF_UP)
    text = f"{abs(n):.{places}f}"
    return f"${text}"


def row_by_id(rows, rid):
    for r in rows:
        if r.get("id") == rid:
            return r
    return None


def paid_phrase(g, r):
    """Short paid-step cell: rate, status, platform, variant, res, audio."""
    rate_money = g["rate_money"]
    rate = rate_money(r["usd_per_second"]) + "/s"
    status = g["rate_label"](r)
    plat = r.get("platform") or "not stated"
    variant = r.get("variant") or r.get("model") or "model not stated"
    res = g["shown_resolution"](r)
    audio = g["audio_phrase"](r)
    kind = "plan" if r.get("kind") == "plan" else "API"
    return (
        f"{rate} {status} · {plat} {kind} · {variant} · {res} · {audio}"
    )


def blurb(g):
    return (
        "What each major tool's free tier actually includes: credits or daily "
        "allowance, watermarks, commercial use, and the cheapest paid step we track."
    )


def description(g):
    text = (
        "What you get on free AI video tiers: credits, watermarks, commercial "
        "use, and the cheapest paid step we track. Last checked Nov 15, 2026."
    )
    if len(text) > 160:
        raise SystemExit(f"{PATH} meta description is over 160 characters: {len(text)}")
    return text


def render(g):
    e, root, LAST = g["e"], g["root"], g["LAST"]
    rate_money = g["rate_money"]
    cost_money = g["cost_money"]
    outbound = g["outbound"]
    rows = g["rows"]

    dates = [CHECKED, LAST]
    for rid in (
        ROW_VEO, ROW_KLING, ROW_WAN, ROW_HAILUO, ROW_GROK, ROW_RUNWAY, ROW_SEEDANCE, ROW_OMNI
    ):
        r = row_by_id(rows, rid)
        if r and r.get("checked"):
            dates.append(r["checked"])
    g["SITEMAP_LASTMOD"][PATH] = max(dates)

    def src(url, text="source"):
        return _src(g, url, text)

    def row_src(r):
        href, rel = outbound(r["source_url"])
        link = f'<a href="{e(href)}" rel="{rel}" target="_blank">source</a>'
        return f'{link}, catalog row {e(r["id"])}, checked {e(r.get("checked") or "date not stated")} PT'

    veo = row_by_id(rows, ROW_VEO)
    kling = row_by_id(rows, ROW_KLING)
    wan = row_by_id(rows, ROW_WAN)
    hailuo = row_by_id(rows, ROW_HAILUO)
    grok = row_by_id(rows, ROW_GROK)
    runway = row_by_id(rows, ROW_RUNWAY)
    seedance = row_by_id(rows, ROW_SEEDANCE)
    omni = row_by_id(rows, ROW_OMNI)
    missing = [
        name
        for name, r in (
            ("r146", veo),
            ("r111", kling),
            ("r096", wan),
            ("r194", hailuo),
            ("r055", grok),
            ("r047", runway),
            ("r202", seedance),
            ("r199", omni),
        )
        if r is None
    ]
    if missing:
        raise SystemExit(f"{PATH} missing catalog rows: {', '.join(missing)}")

    flow_src = src(FLOW_CREDITS, "Google Flow credit help")
    plans_src = src(GOOGLE_AI_PLANS, "Google AI plans")
    krea_src = src(KREA_PLANS, "Krea's pricing page")
    runway_src = src(RUNWAY_PLANS, "Runway's pricing page")
    dreamina_plans_src = src(DREAMINA_PLANS, "Dreamina plans")
    dreamina_free_src = src(DREAMINA_FREE, "Dreamina's text-to-video guide")
    dreamina_price_src = src(DREAMINA_PRICE, "Dreamina pricing FAQ")
    kling_src = src(KLING_PLANS, "Kling membership plans")
    hf_src = src(HF_PLANS, "Higgsfield's pricing page")
    pika_src = src(PIKA_PLANS, "Pika's pricing page")
    hailuo_terms_src = src(HAILUO_TERMS, "Hailuo subscription service terms")
    hailuo_plans_src = src(HAILUO_PLANS, "Hailuo's pricing page")
    xai_src = src(XAI_GROK, "x.ai/grok")
    grok_src = src(GROK_COM, "grok.com")
    wan_src = src(WAN_PLANS, "create.wan.video membership plans")
    luma_src = src(LUMA_PLANS, "Luma's pricing page")
    meta_src = src(META_AI, "meta.ai")
    meta_about_src = src(META_ABOUT, "Meta AI assistant page")

    flow_href = root("/guides/google-flow-credits-calculator/")
    veo_href = root("/models/veo-3-1/")
    omni_href = root("/models/gemini-omni-flash/")
    kling_guide = root("/guides/kling-ai-pricing/")
    kling_model = root("/models/kling-3-0/")
    runway_guide = root("/guides/runway-pricing/")
    runway_model = root("/models/runway-gen-4/")
    hf_guide = root("/guides/higgsfield-pricing/")
    grok_guide = root("/guides/grok-imagine-video-cost/")
    grok_model = root("/models/grok-imagine/")
    wan_guide = root("/guides/cheapest-wan-3-0/")
    wan_model = root("/models/wan-3-0/")
    seedance_guide = root("/guides/cheapest-seedance-2-5/")
    seedance_model = root("/models/seedance-2-5/")
    hailuo_model = root("/models/minimax-hailuo/")
    cheap_href = root("/guides/cheapest-ai-video-generator/")
    budget_href = root("/guides/ai-video-project-budget/")
    calc_href = root("/calculator/")

    # --- comparison table ---
    def tr(cells):
        tds = "".join(f"<td>{c}</td>" for c in cells)
        return f"<tr>{tds}</tr>"

    table_rows = [
        tr([
            f'Google Flow (Veo 3.1 Lite, Omni Flash 1.2)',
            f'50 Flow credits each day, with or without a paid Google AI plan. Unused daily credits do not roll over. Refresh is triggered by the first generation of the day. {flow_src}.',
            f'About 5 Veo 3.1 Lite clips a day, if every credit goes to Lite: Lite is 10 credits per 4s, 6s, or 8s clip at 720p for non-Ultra users. Or about 50s of Omni Flash 1.2 at 360p (1 credit/s), or about 16s at 720p (3 credits/s, 48 credits). During about 2–5 PM UTC, people without a paid plan may be unable to generate video. {flow_src}.',
            f'Veo 3.1 Lite: 4s, 6s, or 8s. Omni Flash 1.2: up to 10s for all users. {flow_src}.',
            f'Veo 3.1 Lite: 720p. Omni Flash 1.2: 360p or 720p. {flow_src}.',
            "Unknown. The help article does not say.",
            "Unknown. The help article does not say.",
            "Lite and Omni Flash 1.2 are billed as video generations; the help article does not say whether those outputs include a soundtrack.",
            "A Google account is required. Whether a card is required on the free allowance is not stated.",
            e(paid_phrase(g, veo)) + f'. {row_src(veo)}. Official first paid Google AI Plus plan is $4.99/month plus 200 extra Flow credits a month, from {plans_src}.',
        ]),
        tr([
            "Krea",
            f'$0/month, 100 compute units a day, no credit card required. The daily allowance refills each day; after it is used up you wait or move to a paid plan. {krea_src}.',
            "Unknown. The public page does not publish how many units a video clip costs on the Free plan, so this site does not convert 100 units into a clip count.",
            "Unknown on Free.",
            "Unknown on Free.",
            "Unknown on Free.",
            f'Not included. The plan comparison says commercial license is a feature of Basic, Pro, and Max, not Free. {krea_src}.',
            "Unknown on Free.",
            f'Sign-up, no credit card required. {krea_src}.',
            e(paid_phrase(g, veo)) + f'. {row_src(veo)}.',
        ]),
        tr([
            "Dreamina (Seedance)",
            f'Free daily credits, with no upfront payment, on {dreamina_plans_src}. A Dreamina guide on the same domain says that includes 120 credits a day in the US, and that other regions can differ, and that this is not a fixed number of videos. {dreamina_free_src}. The plans page itself does not print the daily amount.',
            "Unknown. Official pages do not publish how many credits a Seedance clip costs on the Free plan.",
            "Unknown on Free.",
            "Unknown on Free.",
            f'Likely yes. Paid Basic lists “Remove the Dreamina watermark” as a plan benefit. {dreamina_plans_src}.',
            f'Unknown. The pricing FAQ says commercial-use eligibility depends on Dreamina’s terms, the content, and the models or assets involved. {dreamina_price_src}.',
            "Unknown on Free.",
            "Sign-up. No upfront payment on Free; a card is not described as required for the free daily credits.",
            e(paid_phrase(g, seedance)) + f'. {row_src(seedance)}. Official first paid Dreamina Basic lists at $15/month for 1,575 credits/month (a first-month promo was also on the page). {dreamina_plans_src}.',
        ]),
        tr([
            "Runway",
            f'$0, 125 one-time credits “to explore Runway’s AI tools,” plus 5 GB storage. The credits are a one-time grant, not a monthly refill. {runway_src}.',
            "Unknown. Free includes “a selection of generative creative models.” The page does not say which video models those 125 credits can buy, so this site does not convert them into a clip count.",
            "Unknown on Free.",
            "Unknown on Free.",
            "Unknown on Free. “No watermarks” is listed on Standard, not on Free.",
            "Unknown on Free.",
            "Unknown on Free.",
            f'Sign-up (“Start Free”). Whether a card is required is not stated. {runway_src}.',
            e(paid_phrase(g, runway)) + f'. {row_src(runway)}. Official first paid plan is Standard at $15/month or $12/month billed yearly, with 625 credits a month. {runway_src}. See also {f"<a href=\"{e(runway_guide)}\">Runway pricing per second</a>"}.',
        ]),
        tr([
            "Pika",
            f'$0. Monthly credits: 0 (credit packs only). All models included. 2 video and 2 image+audio jobs in parallel. You can buy top-up packs on Free without starting a paid plan, at 60 credits per $1; pack credits expire 365 days after purchase. {pika_src}.',
            "Zero included clips from plan credits. The page does not publish a signup bonus. “Free generations” in the FAQ are a limited-time Pika H3 Flex daily perk on Creator and Fancy, not on Free.",
            "Depends on the model; Free includes all models. A single Free max length is not published.",
            "Depends on the model. The compare table lists example clips such as Seedance 2.5 at 480p, 720p, or 1080p.",
            f'No. The FAQ says Free plan exports have no watermark. {pika_src}.',
            f'No. Commercial license is not included on Free. {pika_src}.',
            "Image+audio jobs are listed on Free. Whether a given video model writes a soundtrack depends on that model; the Free plan card does not add a single audio rule.",
            "Sign-up. A card is not required to be on Free; a card is required only if you buy a pack.",
            f'Pika is not a row in our catalog. Official first paid plan is Starter at $10/month or $8/month billed yearly, with 600 credits a month. On Starter, a 5-second Seedance 2.5 clip at 720p is listed at 122 credits, about $2.03, or about $0.407/s, if you use the month’s credits on that clip size. {pika_src}. The cheapest Seedance 2.5 row we track is {e(paid_phrase(g, seedance))}. {row_src(seedance)}.',
        ]),
        tr([
            "Wan (create.wan.video)",
            f'$0/month. Daily check-in to earn free credits. 1 video and 1 image at a time. Access to 6 image styles. The page does not say how many credits a check-in gives. {wan_src}.',
            "Unknown. The page does not say how many credits a Wan 3.0 clip costs, or how many credits a check-in gives.",
            "Unknown on Free. “Create longer videos (10–30s)” is listed on Pro and Premium, not on Free.",
            "Unknown on Free. “Create High-Res Videos (1080p)” is listed on Pro and Premium, not on Free.",
            "Likely yes. “Download watermark-free images & videos” is listed on Pro and Premium, not on Free.",
            "Unknown. The membership page does not say.",
            "Unknown. The membership page does not say.",
            f'Sign-in. The page prompts you to log in to claim a daily bonus. A card is not described as required for the $0 plan. {wan_src}.',
            e(paid_phrase(g, wan)) + f'. {row_src(wan)}. Official first paid plan is Pro at $5/month billed yearly ($10 billed monthly), with 300 credits a month. {wan_src}.',
        ]),
        tr([
            "Kling AI",
            f'A $0 Basic plan is listed, with no monthly credits. “Daily Free Credits for Subscribers” is marked as not included on Basic. {kling_src}.',
            "Unknown. The membership page does not publish how many credits, if any, a Basic account can spend, or how many credits a Kling 3.0 clip costs in the app. A “Sign In to Claim Gift” / limited-time free credits prompt is on the page, with no amount.",
            "Unknown on Basic.",
            "Not 1080p or 4K. Those outputs are listed as paid benefits. The exact Basic max resolution is not published.",
            "Likely yes. “Brand watermark removal” is a paid-plan benefit, marked as not included on Basic.",
            "Not included. “Generated content is for commercial use” is a paid-plan benefit, marked as not included on Basic.",
            "Unknown on Basic.",
            f'Sign-in. Whether a card is required for Basic is not stated. {kling_src}.',
            e(paid_phrase(g, kling)) + f'. {row_src(kling)}. Official first paid plan is Standard at $8.80/month after a $6.99 first month, with 660 credits a month. See {f"<a href=\"{e(kling_guide)}\">Kling AI pricing and credits</a>"}. {kling_src}.',
        ]),
        tr([
            "Higgsfield",
            f'A Free plan is listed: limited access to selected AI models, no monthly credits (the compare table prints 0), and one generation at a time. {hf_src}.',
            "Unknown. With 0 monthly credits, the page does not publish how many, if any, complimentary generations the Free plan actually allows, or which models are in the “selected” set.",
            "Unknown on Free.",
            "Unknown on Free.",
            "Unknown. The pricing page does not mention a watermark on Free.",
            f'Not included. Commercial use is listed as not included on Free and included on paid plans. {hf_src}.',
            "Unknown on Free.",
            "Sign-in is offered from the pricing page. Whether a card is required for Free is not stated.",
            e(paid_phrase(g, wan)) + f' is the cheapest Higgsfield catalog row we track. {row_src(wan)}. Official first paid Starter is listed at $19/month for 270 credits a month. A Black Friday sale (up to 60% off) was on the same page today; this guide does not treat the animated sale digits as a verified price. {hf_src}.',
        ]),
        tr([
            "Hailuo (MiniMax)",
            f'Free users who sign in can generate video. Downloads include a watermark. There are no recurring monthly credits. New accounts registered on or after June 18, 2025 get a one-time welcome package of free credits that expire three days after they are granted, one package per user. The terms do not state the amount. {hailuo_terms_src}. The public pricing table did not load today; the homepage CTA says new users receive free credits, from {hailuo_plans_src}.',
            "Unknown. The official terms do not publish the welcome-credit amount or the credits a Hailuo clip costs on Free, so this site does not invent a clip count.",
            "Unknown on Free. The pricing table did not load today.",
            "Unknown on Free.",
            f'Yes. Free-user downloads include a watermark. {hailuo_terms_src}.',
            "Not stated for free users. The terms grant commercial-use language for content generated and downloaded on a paid plan, and do not say the same for Free.",
            "Unknown on Free.",
            "Sign-in. Whether a card is required for Free is not stated.",
            e(paid_phrase(g, hailuo)) + f'. {row_src(hailuo)}. That fal promo is listed through November 15, 2026, with standard rates resuming November 16. Official first paid Hailuo Standard is $14.99/month for 1,000 credits, with watermark-free downloads and queue priority, from {hailuo_terms_src} (terms last updated July 14, 2025). The homepage also showed a “from $9.99/mo” banner today; that figure is not in the terms and is not used as a plan price here.',
        ]),
        tr([
            "Grok Imagine",
            f'“Free to try on the web and in the apps. Upgrade to SuperGrok for higher limits.” {xai_src}. No public free credit or daily clip allotment is printed on {xai_src} or {grok_src}.',
            "Unknown. Official pages do not publish a free clip or credit limit.",
            f'Up to 15 seconds, from the product page. {xai_src}.',
            f'The feature list says text-to-video up to 15 seconds at 720p. A separate Imagine blurb on the same page says “up to 2K resolution and 15-second videos.” Which of those applies to the free trial is not stated. {xai_src}.',
            "Unknown.",
            "Unknown.",
            "Unknown.",
            f'Sign-in with an X or email account. {xai_src}. Whether a card is required to try it is not stated.',
            e(paid_phrase(g, grok)) + f'. {row_src(grok)}. See {f"<a href=\"{e(grok_guide)}\">How much a Grok Imagine video costs</a>"}.',
        ]),
        tr([
            "Luma",
            f'No public free plan with a credit allotment is listed. Public individual plans start at Plus, $30/month, with 10,000 credits. {luma_src}.',
            "None published.",
            "Not applicable; no public free plan.",
            "Not applicable.",
            "Not applicable.",
            "Commercial use is listed on Plus, not on a free plan.",
            "Paid model cards on the same page list audio where the model includes it. That does not create a free allowance.",
            "Sign-in is offered. There is no published free allotment to start without paying.",
            "Luma video models are not separate rows in this catalog, so there is no Luma $/s figure here. Plus at $30/month for 10,000 credits is the official first paid step, from {luma_src}.",
        ]),
        tr([
            "Meta AI",
            f'Public pages describe a free assistant and image generation. They do not publish a free video-generation credit allotment, daily cap, or plan card. {meta_src} returned a 403 challenge in one check and a marketing page in another; {meta_about_src} was readable. Video limits are unknown.',
            "Unknown. No video free-tier allotment was published on the pages that loaded.",
            "Unknown.",
            "Unknown.",
            "Unknown.",
            "Unknown.",
            "Unknown.",
            "Sign-in / log in is offered. Whether a card is required is not stated.",
            "Meta AI video is not a row in our catalog, so there is no catalog paid step to quote.",
        ]),
    ]

    table = f"""<div class="tblwrap" id="free-tier-table">
<table style="min-width:1080px;width:1080px">
<thead><tr>
<th>Tool</th>
<th>Free credits or seconds</th>
<th>Clips that equals</th>
<th>Max length</th>
<th>Resolution</th>
<th>Watermark</th>
<th>Commercial use</th>
<th>Audio</th>
<th>Sign-up / card</th>
<th>Cheapest paid step we track</th>
</tr></thead>
<tbody>
{"".join(table_rows)}
</tbody>
</table>
</div>"""

    q_table = "What does each major free tier actually include?"
    a_table = (
        "It varies widely, and several tools publish a $0 plan without publishing "
        "how many clips that plan can actually make. Google Flow gives 50 credits "
        "a day, which is about five Veo 3.1 Lite clips at 720p if you spend every "
        "credit on Lite. Krea gives 100 compute units a day with no card required, "
        "but does not publish a clip conversion on Free. Dreamina gives free daily "
        "credits (a Dreamina guide says 120 a day in the US). Runway gives 125 "
        "one-time credits. Pika’s Free plan includes all models and no watermark, "
        "but 0 monthly credits. Wan’s Free plan uses daily check-in credits whose "
        "amount is not published. Kling Basic, Higgsfield Free, and Hailuo Free "
        "also omit a usable clip count on the public pages we could read today."
    )

    q_best = "Which free option is best for each use?"
    a_best = (
        "For a repeating daily allowance you can count: Google Flow, at about five "
        "Veo 3.1 Lite clips a day if you use every credit on Lite, is the only row "
        "in this table with a published credits-per-clip figure. For a daily "
        "allowance without a card: Krea’s Free plan. For a watermark-free export "
        "on a $0 plan: Pika, which also includes all of its models, but only if "
        "you buy a credit pack or already have credits — Free itself includes 0 "
        "monthly credits and no commercial license. For a one-session trial of "
        "Runway’s tools: Runway’s 125 one-time credits. For Seedance in a consumer "
        "app with daily credits: Dreamina, with the US daily amount taken from a "
        "Dreamina guide, not from the plans table."
    )

    q_catches = "What are the usual catches on a “free” plan?"
    a_catches = (
        "Watermarks are the most common: Hailuo Free downloads include one; Kling "
        "Basic, Wan Free, and Dreamina Free look likely to include one because "
        "watermark removal is listed as a paid benefit. Commercial use is often "
        "a paid-plan right — Pika Free, Kling Basic, and Higgsfield Free do not "
        "include it. Queues and caps: Higgsfield Free and Wan Free allow one "
        "generation at a time; Flow may block video for people without a paid "
        "plan around 2–5 PM UTC. Allotments can be one-time, not daily: Runway’s "
        "125 credits do not refill, and Hailuo’s welcome credits expire after "
        "three days. Daily credits often do not roll over, as Flow’s help page "
        "states. A $0 plan with 0 monthly credits, such as Pika Free or "
        "Higgsfield Free, is not a source of recurring clips unless another grant "
        "is published."
    )

    q_pay = "When does paying become cheaper per second?"
    a_pay = (
        "As soon as you need more clips than the free cap, a commercial license, "
        "or (on most tools except Pika) a watermark-free export, the free tier "
        "stops being a complete substitute. After that, the cheapest paid step "
        "is often not the vendor’s first consumer plan. In our catalog, a Krea "
        "yearly estimate for Veo 3.1 Lite at 720p is "
        f"{g['rate_money'](veo['usd_per_second'])}/s, "
        "a Higgsfield yearly plan estimate for Kling 3.0 at 720p is "
        f"{g['rate_money'](kling['usd_per_second'])}/s, "
        "and a fal promo for MiniMax H3 Max Turbo at 480p is "
        f"{g['rate_money'](hailuo['usd_per_second'])}/s "
        "through November 15, 2026. Those figures assume you use the credits you "
        "pay for, and each row states its tier, resolution, and audio. A credit "
        "pack on a $0 plan can also cost more per clip than the first paid plan "
        "if the pack rate is worse; on Pika, packs and Starter are both listed "
        "at 60 credits per $1."
    )

    q_unknown = "What is confirmed, and what is not?"
    a_unknown = (
        "Confirmed today on official pages: Flow’s 50 daily credits and Lite and "
        "Omni Flash 1.2 credit costs; Krea Free at 100 units a day with no card; "
        "Runway Free at 125 one-time credits; Dreamina’s free daily credits and "
        "the US 120-credit figure on a Dreamina guide; Kling’s $0 Basic plan with "
        "no monthly credits; Higgsfield’s Free plan with 0 monthly credits; "
        "Pika Free with 0 monthly credits, no watermark, and no commercial "
        "license; Hailuo’s watermarked free downloads and three-day welcome "
        "credits; Wan’s $0 plan with daily check-in credits; Grok being free to "
        "try, with 15-second video mentioned on the product page; and Luma "
        "listing no public free plan. Unknown, and not guessed: clip counts "
        "where credits-per-clip are unpublished; watermark, commercial use, "
        "max length, resolution, or audio where the official page is silent; "
        "Hailuo’s welcome-credit amount; Wan’s check-in credit amount; which "
        "models Runway Free actually includes; Meta AI’s video free tier, which "
        "was not published on the pages that loaded; and any login-gated or "
        "region-gated figure we could not read."
    )

    faqs = [
        (QUESTION, a_table),
        (q_table, a_table),
        (q_best, a_best),
        (q_catches, a_catches),
        (q_pay, a_pay),
        (q_unknown, a_unknown),
    ]
    for q, a in faqs:
        raw = (q + " " + a).lower()
        for bad in ("subscribe", "newsletter", "buttondown"):
            if bad in raw:
                raise SystemExit(f"{PATH} FAQ text contains {bad}")

    lead = (
        f"Most “free” AI video tools give you a tight cap, a watermark, or both, "
        f"and several $0 plans publish no clip count at all. Official pages were "
        f"read {e(CHECKED_WHEN)}. Google Flow still gives 50 credits a day, about "
        f"five Veo 3.1 Lite clips at 720p if you spend every credit on Lite, from "
        f"{flow_src}. Krea’s Free plan is 100 units a day with no credit card, from "
        f"{krea_src}. Pika’s Free plan has no watermark and 0 monthly credits, from "
        f"{pika_src}. Anything a vendor did not publish is marked unknown."
    )

    body = f"""<p class="small"><a href="{root("/guides/")}">Guides</a> › Free AI video generators</p>
<h1>{e(PHRASE)}</h1>
<p class="lead">{lead}</p>
<p class="small">Last checked {e(LAST)}. Official free-tier figures were read {e(CHECKED_WHEN)}. Catalog paid-step rows use the date on each row. Affiliate links never change this price order. Every dollar-per-second figure below states its usage assumption, tier, resolution, and audio.</p>

<h2>{e(QUESTION)}</h2>
<p>{e(a_table)}</p>

<h2>{e(q_table)}</h2>
<p>One row per tool. “Clips that equals” is filled only when the official page publishes both the free allotment and the credits (or seconds) a named clip costs. Paid-step rates are the cheapest matching row in our catalog, except where we have no catalog row and quote the official first paid plan instead.</p>
{table}
<p class="small">Sources and check time {e(CHECKED_WHEN)}: {flow_src} · {plans_src} · {krea_src} · {runway_src} · {dreamina_plans_src} · {dreamina_free_src} · {dreamina_price_src} · {kling_src} · {hf_src} · {pika_src} · {hailuo_terms_src} · {hailuo_plans_src} · {xai_src} · {grok_src} · {wan_src} · {luma_src} · {meta_src} · {meta_about_src}. Catalog rows are dated on each paid-step cell.</p>

<h2>{e(q_best)}</h2>
<p>{e(a_best)}</p>
<ul>
<li><b>A daily cap you can count.</b> Google Flow is the only row with a published credits-per-clip figure: 50 daily credits ÷ 10 credits per Veo 3.1 Lite generation ≈ 5 clips a day at 720p, in 4s, 6s, or 8s, if you use every credit on Lite and you can generate (see the peak-hour note). {flow_src}. Details: <a href="{e(flow_href)}">Google Flow credits calculator</a> · <a href="{e(veo_href)}">Veo 3.1 model page</a> · <a href="{e(omni_href)}">Gemini Omni Flash model page</a>.</li>
<li><b>No credit card, daily refill.</b> Krea Free: 100 units a day, no card. Clip count unknown. {krea_src}.</li>
<li><b>No watermark on a $0 plan.</b> Pika Free exports have no watermark and include all models, but 0 monthly credits and no commercial license. {pika_src}.</li>
<li><b>Seedance in a consumer app.</b> Dreamina publishes free daily credits. A Dreamina guide says 120 a day in the US, with other regions differing. Clip count unknown. {dreamina_plans_src} · {dreamina_free_src}. <a href="{e(seedance_model)}">Seedance 2.5 model page</a>.</li>
<li><b>A one-time trial, not a daily allowance.</b> Runway Free: 125 credits once. {runway_src}. <a href="{e(runway_guide)}">Runway pricing per second</a>.</li>
</ul>

<h2>{e(q_catches)}</h2>
<p>{e(a_catches)}</p>

<h2>{e(q_pay)}</h2>
<p>{e(a_pay)}</p>
<p>Related model and pricing pages: <a href="{e(cheap_href)}">cheapest rate we track for each model</a> · <a href="{e(kling_guide)}">Kling AI pricing and credits</a> · <a href="{e(runway_guide)}">Runway pricing per second</a> · <a href="{e(hf_guide)}">Higgsfield pricing explained</a> · <a href="{e(grok_guide)}">Grok Imagine video cost</a> · <a href="{e(wan_guide)}">cheapest Wan 3.0</a> · <a href="{e(seedance_guide)}">cheapest Seedance 2.5</a> · <a href="{e(budget_href)}">project budget calculator</a> · <a href="{e(calc_href)}">credit calculator</a> · <a href="{e(hailuo_model)}">MiniMax Hailuo model page</a> · <a href="{e(kling_model)}">Kling 3.0 model page</a> · <a href="{e(runway_model)}">Runway Gen-4 model page</a> · <a href="{e(wan_model)}">Wan 3.0 model page</a> · <a href="{e(grok_model)}">Grok Imagine model page</a>.</p>

<h2>{e(q_unknown)}</h2>
<p>{e(a_unknown)}</p>
<p><b>Confirmed {e(CHECKED_WHEN)} on official pages:</b> the free-tier facts in the table, each with its source link. <b>Confirmed in the catalog (rows last stored as checked 2026-11-14):</b> the paid-step $/s figures, each with its vendor URL, usage assumption, tier, resolution, and audio.</p>
<p class="small">Affiliate links never change this price order.</p>
{g["how_block"]()}
"""

    # Hard rule: this page must never name Sora, including in comments rendered to HTML.
    if "sora" in body.lower() or "sora" in description(g).lower() or "sora" in PHRASE.lower():
        raise SystemExit(f"{PATH} source would name Sora")

    title = g["page_title"](PHRASE)
    desc = description(g)
    g["guide_page"](PATH, title, desc, body, faqs)
    return PATH
