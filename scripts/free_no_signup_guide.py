"""Guide: Free AI video generators with no sign-up.

Imported by scripts/build_site.py. Official pages were read on Nov 20, 2026,
7:05 PM ET (4:05 PM PT). Catalog rates come from data/prices.json. This page
never names Sora. VidFare tracks nine models, not a list of twelve tools.
"""

PATH = "/guides/free-ai-video-generator-no-sign-up/"
LABEL = "No sign-up"
PHRASE = "Free AI video generators, no sign-up"
QUESTION = "Which free AI video generators work with no sign-up?"
CHECKED = "2026-11-20"
CHECKED_WHEN = "Nov 20, 2026, 7:05 PM ET (4:05 PM PT)"

# Pages opened at CHECKED_WHEN. A 403 or an empty app shell is recorded as
# not readable. Nothing below is a generation we ran.
HF_ZERO = "https://huggingface.co/docs/hub/spaces-zerogpu"
HF_PRICING = "https://huggingface.co/pricing"
HF_LTX = "https://huggingface.co/spaces/Lightricks/LTX-2-3"
VHEER_HOME = "https://vheer.com/"
VHEER_PRICING = "https://vheer.com/pricing"
VHEER_T2V = "https://vheer.com/app/text-to-video"
DEEPAI_VIDEO = "https://deepai.org/video"
FLOW_CREDITS = "https://support.google.com/flow/answer/16526234?hl=en"
FLOW_START = "https://support.google.com/flow/answer/16353333?hl=en"
KREA_VIDEO = "https://www.krea.ai/features/ai-video-generator"
KREA_PLANS = "https://www.krea.ai/pricing"
DREAMINA_PRICE = "https://dreamina.capcut.com/pricing/dreamina-price"
DREAMINA_T2V = "https://dreamina.capcut.com/ai-video/make-text-to-video-with-free-credits"
PIKA_PLANS = "https://pika.art/pricing"
WAN_PLANS = "https://create.wan.video/pricing?whereToMemberShip=membership_plans"
HAILUO_TERMS = "https://hailuoai.video/doc/payment-policy.html"
RUNWAY_PLANS = "https://runway.com/pricing"
KLING_PLANS = "https://kling.ai/app/membership/membership-plan"
HF_FREE = "https://higgsfield.ai/creator-hub/help-center/plans/what-does-the-free-plan-include"
LUMA_PLANS = "https://lumalabs.ai/pricing"
XAI_GROK = "https://x.ai/grok"
GROK_IMAGINE = "https://grok.com/imagine"
META_AI = "https://www.meta.ai/"
PERCHANCE = "https://perchance.org/ai-video-generator"

# DeepAI's video page, read CHECKED_WHEN. Not catalog rows.
DEEPAI_HD = 0.20
DEEPAI_HOLLYWOOD = 0.30
DEEPAI_PRO = 9.99

UNPUBLISHED = (
    "/guides/is-higgsfield-free/",
    "/guides/is-kling-ai-free/",
    "/guides/is-seedance-free/",
    "/guides/google-flow-pricing/",
)


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
        "Which sellers publish a way to generate a video with no account, "
        "and what the nine catalog models require instead."
    )


def description(g):
    text = (
        "AI video with no sign-up: what the 9 VidFare models require, "
        "Hugging Face’s no-account GPU quota, and a paid DeepAI route. "
        "Checked Nov 20, 2026."
    )
    if len(text) > 160:
        raise SystemExit(f"{PATH} meta description is over 160 characters: {len(text)}")
    return text


def render(g):
    e, root, LAST = g["e"], g["root"], g["LAST"]
    rate_money = g["rate_money"]
    cost_money = g["cost_money"]
    rate_label = g["rate_label"]
    shown_resolution = g["shown_resolution"]
    shown_tier = g["shown_tier"]
    shown_audio = g["shown_audio"]
    input_phrase = g["input_phrase"]
    assumption_text = g["assumption_text"]
    rows = g["rows"]

    dates = [CHECKED, LAST]
    g["SITEMAP_LASTMOD"][PATH] = max(dates)

    def src(url, text="source"):
        return _src(g, url, text)

    hf_zero = src(HF_ZERO, "Hugging Face ZeroGPU documentation")
    hf_price = src(HF_PRICING, "Hugging Face pricing")
    hf_ltx = src(HF_LTX, "LTX 2.3 Distilled Space")
    vheer_home = src(VHEER_HOME, "Vheer’s home page")
    vheer_price = src(VHEER_PRICING, "Vheer’s pricing page")
    vheer_t2v = src(VHEER_T2V, "Vheer’s text-to-video page")
    deepai = src(DEEPAI_VIDEO, "DeepAI’s video page")
    flow_credits = src(FLOW_CREDITS, "Google Flow credit help")
    flow_start = src(FLOW_START, "Get started with Google Flow")
    krea_video = src(KREA_VIDEO, "Krea’s AI video generator page")
    krea_plans = src(KREA_PLANS, "Krea’s pricing page")
    dreamina_price = src(DREAMINA_PRICE, "Dreamina’s pricing page")
    dreamina_t2v = src(DREAMINA_T2V, "Dreamina’s text-to-video guide")
    pika_src = src(PIKA_PLANS, "Pika’s pricing page")
    wan_plans = src(WAN_PLANS, "Wan membership plans")
    hailuo_terms = src(HAILUO_TERMS, "Hailuo subscription service terms")
    runway_src = src(RUNWAY_PLANS, "Runway’s pricing page")
    kling_src = src(KLING_PLANS, "Kling membership plans")
    hf_free = src(HF_FREE, "Higgsfield help: what the free plan includes")
    luma_src = src(LUMA_PLANS, "Luma’s pricing page")
    xai_grok = src(XAI_GROK, "x.ai/grok")
    grok_imagine = src(GROK_IMAGINE, "grok.com/imagine")
    meta_src = src(META_AI, "meta.ai")
    perchance = src(PERCHANCE, "perchance.org")

    free_href = root("/guides/free-ai-video-generators/")
    t2v_href = root("/guides/free-text-to-video-ai/")
    i2v_href = root("/guides/free-image-to-video-ai/")
    flow_calc = root("/guides/google-flow-credits-calculator/")
    calc_href = root("/calculator/")
    model_href = {
        "wan-3-0": root("/models/wan-3-0/"),
        "wan-3-0-prime": root("/models/wan-3-0-prime/"),
        "kling-3-0": root("/models/kling-3-0/"),
        "seedance-2-5": root("/models/seedance-2-5/"),
        "veo-3-1": root("/models/veo-3-1/"),
        "gemini-omni-flash": root("/models/gemini-omni-flash/"),
        "minimax-hailuo": root("/models/minimax-hailuo/"),
        "runway-gen-4": root("/models/runway-gen-4/"),
        "grok-imagine": root("/models/grok-imagine/"),
    }
    wan_guide = root("/guides/cheapest-wan-3-0/")
    seedance_guide = root("/guides/cheapest-seedance-2-5/")
    kling_guide = root("/guides/kling-ai-pricing/")
    runway_guide = root("/guides/runway-pricing/")
    hf_guide = root("/guides/higgsfield-pricing/")
    grok_guide = root("/guides/grok-imagine-video-cost/")

    def trow(*cells):
        return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"

    def model_link(slug):
        name = g["models"][slug]["name"]
        return f'<a href="{e(model_href[slug])}">{e(name)}</a>'

    when = e(CHECKED_WHEN)
    not_catalog = "Not in the VidFare catalog."

    routes_table = f"""<div class="tblwrap" id="no-signup-routes">
<table style="min-width:1180px;width:1180px">
<thead><tr>
<th>Service</th>
<th>In the VidFare catalog?</th>
<th>Works with no account?</th>
<th>Published limits</th>
<th>Models and resolution</th>
<th>Audio</th>
<th>Watermark</th>
<th>Source</th>
</tr></thead>
<tbody>
{trow(
    "Hugging Face Spaces (hosted demos)",
    not_catalog,
    "Yes, documented. The usage table lists Unauthenticated as its own tier.",
    "2 minutes of GPU time a day, at low queue priority. A free account gets 5 minutes. PRO is listed at $9 a month on the pricing page, with an 8× ZeroGPU quota. The docs list a PRO account at 40 minutes a day. The quota resets 24 hours after the first GPU use. Clips per day are not published.",
    "Depends on the demo. The LTX 2.3 Distilled Space page loaded and showed the demo running on ZeroGPU. We did not run a generation.",
    "Not stated.",
    "Not stated.",
    f"{hf_zero} · {hf_price} · {hf_ltx}, read {when}.",
)}
{trow(
    "Vheer (third-party site)",
    not_catalog,
    "Claimed on the home page, which says unlimited generations with no signup. Not tested. The pricing page describes a Free plan, so the no-account video terms are not clear from the pages alone.",
    "Home page: unlimited generations. Pricing page: Free is $0 with 50 credits a month, basic image generation, and personal use. Premium starts at $9.99 a month. Which of these applies to video without an account is not stated.",
    "The text-to-video page showed 720p and 4 seconds selected, on a model labelled SeeDance V1 Pro Fast. That is not Seedance 2.5, and it is not a catalog model.",
    "Not stated.",
    "The home page and the Free plan card both say no watermark.",
    f"{vheer_home} · {vheer_t2v} · {vheer_price}, read {when}.",
)}
{trow(
    "DeepAI",
    not_catalog,
    "Yes, but paid. The video page says agents and developers with no account can buy video pay-per-call, with no API key.",
    f"HD is {e(rate_money(DEEPAI_HD))} per second at 720p. Hollywood mode is {e(rate_money(DEEPAI_HOLLYWOOD))} per second at 2K. DeepAI Pro is {e(cost_money(DEEPAI_PRO))} a month and includes the first 25 seconds of standard video and the first 8 seconds of 2K Hollywood mode. This page does not turn that bundle into a per-second rate.",
    "HD at 720p, and Hollywood mode at 2K, as the page names them.",
    "Not stated.",
    "Not stated.",
    f"{deepai}, read {when}.",
)}
{trow(
    "Perchance",
    not_catalog,
    "Unknown. The page returned 403 and could not be read.",
    "Unknown.",
    "Unknown.",
    "Unknown.",
    "Unknown.",
    f"{perchance}, not readable on {when}.",
)}
</tbody></table></div>"""

    catalog_table = f"""<div class="tblwrap" id="catalog-account">
<table style="min-width:1100px;width:1100px">
<thead><tr>
<th>Catalog model</th>
<th>Account needed to generate?</th>
<th>What the seller page said</th>
<th>Source</th>
</tr></thead>
<tbody>
{trow(
    model_link("wan-3-0"),
    "Not re-confirmed. The membership page we fetched did not include plan text, so this check does not say whether a clip generates before login.",
    "The Nov 15, 2026 check on the free-generators guide said the $0 plan asks you to log in for a daily bonus of an unpublished amount. That figure was not on the page we could read today.",
    f"{wan_plans}, read {when}; plan text was not in the response. Earlier record: <a href=\"{e(free_href)}\">free AI video generators: what you get</a> · <a href=\"{e(wan_guide)}\">cheapest Wan 3.0</a>.",
)}
{trow(
    model_link("wan-3-0-prime"),
    "Not re-confirmed. Same seller page as Wan 3.0. Wan 3.0 Prime is a separate catalog model, not a tier of Wan 3.0.",
    "No separate no-account path was in the HTML we received. The page did not include plan text.",
    f"{wan_plans}, read {when}; plan text was not in the response. <a href=\"{e(model_href['wan-3-0-prime'])}\">Wan 3.0 Prime prices</a>.",
)}
{trow(
    model_link("kling-3-0"),
    "Not re-confirmed. The membership page we fetched was an app shell and did not include plan names, prices, or a sign-in prompt.",
    "The Nov 15, 2026 check on the free-generators guide said Basic is $0, sign-in is offered, and a limited-time gift does not state an amount. That text was not in today’s response.",
    f"{kling_src}, read {when}; plan text was not in the response. <a href=\"{e(kling_guide)}\">Kling AI pricing and credits</a>.",
)}
{trow(
    model_link("seedance-2-5"),
    "Yes, on the consumer page we could read. Dreamina’s pricing page says the free option uses the credits available in your account, and the page shows Sign in. Dreamina is the consumer seller, not a separate catalog model.",
    "A Dreamina guide says 120 credits a day in the US, with other regions differing. Krea’s video page says Pro or higher unlocks Seedance 2.5, so Krea Free is not a Seedance 2.5 allowance. Catalog API rows for this model are accounts too.",
    f"{dreamina_price} · {dreamina_t2v} · {krea_video}, read {when}. <a href=\"{e(seedance_guide)}\">cheapest Seedance 2.5</a>.",
)}
{trow(
    model_link("veo-3-1"),
    "Yes. Google Flow’s get-started page requires age 18 or older and a supported region. The credit help page says 50 credits a day are shared across your account, with or without a paid plan. Neither page describes generating with no account.",
    "Veo 3.1 Lite is 10 credits per 4, 6, or 8 second clip at 720p for people who are not on Google AI Ultra, so about five clips a day if every credit goes to Lite. During the peak hours named on the credit help page, people without a paid plan may not be able to generate video. Krea says Veo 3.1 needs Pro or higher.",
    f"{flow_start} · {flow_credits} · {krea_video}, read {when}. <a href=\"{e(flow_calc)}\">Google Flow credits calculator</a>.",
)}
{trow(
    model_link("gemini-omni-flash"),
    "Yes, on the same Google Flow account as Veo 3.1. The catalog name is Gemini Omni Flash 1.1. The Flow help page read today prices Omni Flash 1.2 and says Omni Flash 1.1 will be retired on December 5, 2026. Those are not the same version.",
    "Omni Flash 1.2 is 1 credit per second at 360p and 3 credits per second at 720p, for clips up to 10 seconds, for all users. Fifty daily credits are about 50 seconds at 360p, or 16 seconds at 720p (48 credits), if every credit goes to that one model.",
    f"{flow_credits} · {flow_start}, read {when}.",
)}
{trow(
    model_link("minimax-hailuo"),
    "Yes. The terms say free users get video generation upon logging in.",
    "Downloads include a watermark. New accounts get a one-time welcome package of free credits that expires three days after it is granted. The amount is not stated.",
    f"{hailuo_terms}, read {when}.",
)}
{trow(
    model_link("runway-gen-4"),
    "Yes. The pricing page describes a Free plan and offers Login. It does not describe generating with no account.",
    "The page’s own FAQ says the Free plan includes a one-time deposit of 125 credits that does not expire. That sentence does not say which Gen-4 variants those credits buy.",
    f"{runway_src}, read {when}. <a href=\"{e(runway_guide)}\">Runway pricing per second</a>.",
)}
{trow(
    model_link("grok-imagine"),
    "Unknown on the consumer site. grok.com/imagine loaded, and the text we could read did not state a no-account video path. x.ai/grok returned 403. The API rate in the paid table needs an API account.",
    "No free video allowance was published on the pages we could read today.",
    f"{grok_imagine}, read {when}. {xai_grok} returned 403. <a href=\"{e(grok_guide)}\">how much a Grok Imagine video costs</a>.",
)}
</tbody></table></div>"""

    outside_table = f"""<div class="tblwrap" id="outside-catalog">
<table style="min-width:1080px;width:1080px">
<thead><tr>
<th>Tool</th>
<th>In the VidFare catalog?</th>
<th>Account needed?</th>
<th>Published allowance</th>
<th>Source</th>
</tr></thead>
<tbody>
{trow(
    "Krea",
    not_catalog,
    "Yes. A free account. The video page and the pricing page both say no credit card is required.",
    "100 units a day on the $0 plan. Krea does not add a watermark on the free plan or on paid plans. Videos made on the free plan are for personal use. Seedance 2.5 and Veo 3.1 need Pro or higher. How many units a clip costs on Free is not published on the video page.",
    f"{krea_video} · {krea_plans}, read {when}.",
)}
{trow(
    "Pika",
    not_catalog,
    "Yes. The pricing page offers Login and Start free. The Free plan is an account plan, not a no-account path.",
    "Free is $0 with 0 monthly credits, credit packs only, no watermark, and no commercial license. It is not a published pile of free clips.",
    f"{pika_src}, read {when}.",
)}
{trow(
    "Luma",
    not_catalog,
    "No public free plan was listed. Individual plans start at a paid plan.",
    f"Plus is {e(cost_money(30))} a month with 10,000 credits. No $0 allowance was on the pricing page.",
    f"{luma_src}, read {when}.",
)}
{trow(
    "Meta AI",
    not_catalog,
    "Unknown. meta.ai returned 403, so this check does not say whether video generates with no account.",
    "No video allowance was readable.",
    f"{meta_src}, not readable on {when}.",
)}
</tbody></table></div>"""

    def seller_rate(r):
        label = rate_label(r)
        tier = shown_tier(r)
        if tier and tier != "not listed":
            return f"{e(rate_money(r['usd_per_second']))}/s on {e(r['platform'])} ({e(tier)}, {e(label)})"
        return f"{e(rate_money(r['usd_per_second']))}/s on {e(r['platform'])} ({e(label)})"

    def audio_txt(r):
        audio = shown_audio(r)
        if audio == "with":
            return "with audio"
        if audio == "without":
            return "without audio"
        return "not stated"

    def catalog_paid(r):
        href, rel = g["outbound"](r["source_url"])
        source = (
            f'<a href="{e(href)}" rel="{rel}" target="_blank">source</a>, '
            f"catalog row {e(r['id'])}, checked {e(r['checked'])} PT."
        )
        extra = assumption_text(r)
        if r.get("math"):
            extra = (extra + " " if extra else "") + r["math"]
        if r.get("note"):
            extra = (extra + " " if extra else "") + r["note"]
        if not extra:
            extra = "Billed per second of output. Retries are billed too."
        elif r.get("kind") == "api":
            extra = extra.rstrip(".") + ". Billed per second of output. Retries are billed too."
        model = (
            f'{e(g["models"][r["model"]]["name"])}, {e(r["variant"])}. '
            f'Input: {e(input_phrase(r))}.'
        )
        needs = "Needs an account."
        route = f'{e(r["platform"])} · {e(r.get("plan_name") or r.get("kind") or "route")}. {needs}'
        return (
            float(r["usd_per_second"]),
            r["id"],
            trow(
                route,
                model,
                e(shown_resolution(r)),
                e(audio_txt(r)),
                seller_rate(r),
                e(extra),
                source,
            ),
        )

    def published(r):
        return rate_label(r) == "published rate"

    pubs = sorted((r for r in rows if published(r)), key=lambda r: (r["usd_per_second"], r["id"]))
    if not pubs:
        raise SystemExit(f"{PATH} has no published-rate row")
    floor = pubs[0]["usd_per_second"]
    tied = [r for r in pubs if r["usd_per_second"] == floor]
    overall = min(rows, key=lambda r: (r["usd_per_second"], r["id"]))
    paid_bits = []
    seen = set()
    if overall["id"] not in {r["id"] for r in tied}:
        paid_bits.append(catalog_paid(overall))
        seen.add(overall["id"])
    for r in tied:
        if r["id"] not in seen:
            paid_bits.append(catalog_paid(r))
            seen.add(r["id"])

    def deepai_row(name, usd, res, assumption):
        return (
            usd,
            name,
            trow(
                f"DeepAI · pay-per-call, no account. {not_catalog}",
                e(name),
                e(res),
                "not stated",
                f"{e(rate_money(usd))}/s on DeepAI (published rate)",
                e(assumption),
                f"{deepai}, read {when}.",
            ),
        )

    paid_bits.append(deepai_row(
        "DeepAI video, HD",
        DEEPAI_HD,
        "720p",
        "Billed per second of output, as the page states. Audio is not stated. Not a catalog row.",
    ))
    paid_bits.append(deepai_row(
        "DeepAI video, Hollywood mode",
        DEEPAI_HOLLYWOOD,
        "2K",
        "Billed per second of output, as the page states. Audio is not stated. Not a catalog row.",
    ))
    paid_bits.sort(key=lambda item: (item[0], item[1]))
    prices = [item[0] for item in paid_bits]
    if prices != sorted(prices):
        raise SystemExit(f"{PATH} paid table is not in price order")
    paid_table = f"""<div class="tblwrap" id="paid-no-signup">
<table style="min-width:1180px;width:1180px">
<thead><tr>
<th>Route and seller</th>
<th>Model</th>
<th>Resolution</th>
<th>Audio</th>
<th>Rate</th>
<th>Usage assumption</th>
<th>Source and date checked</th>
</tr></thead>
<tbody>
{''.join(html for _usd, _key, html in paid_bits)}
</tbody></table></div>"""

    lowest_pub = ", ".join(
        f"{rate_money(r['usd_per_second'])} per second for {r['variant']} on {r['platform']} "
        f"at {shown_resolution(r)}, audio {audio_txt(r)} (catalog row {r['id']}, checked {r['checked']})"
        for r in tied
    )
    overall_clause = (
        f"{rate_money(overall['usd_per_second'])} per second for {overall['variant']} on {overall['platform']}"
        f" ({shown_tier(overall)}, {shown_resolution(overall)}, audio {audio_txt(overall)}, "
        f"{rate_label(overall)}, catalog row {overall['id']}, checked {overall['checked']})"
    )

    a_which = (
        "Hugging Face documents one no-account route: an unauthenticated visitor gets "
        "2 minutes of GPU time a day on hosted demo Spaces, at low queue priority. "
        f"DeepAI documents a no-account route that is paid, at {rate_money(DEEPAI_HD)} per second "
        f"for HD at 720p and {rate_money(DEEPAI_HOLLYWOOD)} per second for Hollywood mode at 2K. "
        "Vheer’s home page says generations are unlimited with no signup, while its pricing page "
        "lists a Free plan of 50 credits a month, so what applies to video without an account is not clear. "
        "None of the nine catalog models has a no-account path on a seller page that loaded today. "
        "Wan’s and Kling’s plan pages did not include plan text, so those three model rows "
        "(Wan 3.0, Wan 3.0 Prime, and Kling 3.0) are not re-confirmed. We did not run a generation."
    )
    a_catalog = (
        "Where the seller page loaded, yes. Google Flow, which serves Veo 3.1 and the Omni Flash "
        "line, requires age 18 or older and a supported region, and its 50 daily credits are shared "
        "across your account. The catalog model is Gemini Omni Flash 1.1; the Flow page read today "
        "prices Omni Flash 1.2 and says Omni Flash 1.1 retires on December 5, 2026. Dreamina, the "
        "consumer seller for Seedance 2.5, ties free credits to the credits in your account and shows "
        "Sign in. Hailuo’s terms give free users video generation upon logging in. Runway’s pricing "
        "page describes a Free plan with a one-time deposit of 125 credits. Higgsfield says every new "
        "account starts on the free plan, which has no monthly credits. Grok Imagine’s consumer page "
        "did not state a no-account video path, and x.ai/grok returned 403. Wan 3.0, Wan 3.0 Prime, "
        "and Kling 3.0 are separate catalog models whose plan pages did not include plan text today."
    )
    a_paid = (
        f"Yes. DeepAI’s video page says people with no account can buy video pay-per-call at "
        f"{rate_money(DEEPAI_HD)} per second for HD at 720p and {rate_money(DEEPAI_HOLLYWOOD)} per second "
        f"for Hollywood mode at 2K. Audio is not stated. DeepAI Pro is {cost_money(DEEPAI_PRO)} a month "
        "and includes the first 25 seconds of standard video and the first 8 seconds of 2K Hollywood mode. "
        "This page does not turn that bundle into a per-second rate. "
        f"The lowest rate in the VidFare catalog is {overall_clause}. "
        f"The lowest published rates are {lowest_pub}. "
        "Those catalog routes need an account. The table is in price order."
    )
    a_least = (
        "If an account with no card is acceptable, Krea is the seller that states it: a free account, "
        "no credit card, 100 units a day, and no watermark. Krea is not in the VidFare catalog, and "
        "free-plan videos are for personal use. Google Flow publishes 50 credits a day, about five "
        "Veo 3.1 Lite clips at 720p if every credit goes to Lite, for an account that meets the age "
        "and region rules. Hugging Face publishes a no-account allowance in minutes of GPU time, not "
        "in clips. A best-for line is given only where the provider’s page supports it."
    )
    a_unknown = (
        "Unknown, and not guessed: whether Wan 3.0, Wan 3.0 Prime, or Kling 3.0 can be generated "
        "before login, because those plan pages did not include plan text; whether Grok Imagine or "
        "Meta AI will generate a video with no account; whether Vheer’s no-signup line covers video, "
        "and which model and limits apply; how many clips Hugging Face’s 2 minutes of GPU time produce; "
        "the resolution, length, audio, and watermark of those no-account clips; and Perchance, whose "
        "page returned 403. We read pages and did not run generations."
    )

    faqs = [
        (QUESTION, a_which),
        ("Do the catalog models need an account to generate video?", a_catalog),
        ("Is there a paid option with no account?", a_paid),
        ("What is the least sign-up with a published allowance?", a_least),
        ("What is confirmed, and what is not?", a_unknown),
    ]
    for q, a in faqs:
        raw = (q + " " + a).lower()
        for bad in ("subscribe", "newsletter", "buttondown"):
            if bad in raw:
                raise SystemExit(f"{PATH} FAQ text contains {bad}")

    lead = (
        "VidFare tracks nine models. On the seller pages that included plan text "
        f"{e(CHECKED_WHEN)}, none of them publishes a way to generate a video with no account. "
        "Wan 3.0, Wan 3.0 Prime, and Kling 3.0 are separate models, and their plan pages did not "
        "include plan text on this check. Outside the catalog, Hugging Face documents "
        f"2 minutes of GPU time a day with no account, from {hf_zero}. DeepAI sells pay-per-call "
        f"video with no account. Vheer’s home page says no signup; its pricing page lists a monthly "
        f"credit cap, so the video terms are not clear. We did not run a generation. For free tiers "
        f"that do use an account, see <a href=\"{e(free_href)}\">free AI video generators: what you get</a>."
    )

    takeaways = f"""<div class="card" id="takeaways">
<h2>Key takeaways</h2>
<ul>
<li><b>Nine catalog models.</b> Wan 3.0 Prime, Wan 3.0, Kling 3.0, Seedance 2.5, Veo 3.1, Gemini Omni Flash, MiniMax Hailuo, Runway Gen-4, and Grok Imagine. Krea, Pika, Luma, Meta AI, Vheer, DeepAI, and Hugging Face are outside the catalog and are labelled that way.</li>
<li><b>No catalog model published a no-account path</b> on a seller page that loaded. Wan, Wan 3.0 Prime, and Kling could not be re-read.</li>
<li><b>Documented no-account route.</b> Hugging Face Spaces: 2 minutes of GPU time a day, low queue priority. Clips per day: not published.</li>
<li><b>Paid, no account.</b> DeepAI, {e(rate_money(DEEPAI_HD))}/s on DeepAI for HD at 720p. Audio is not stated.</li>
<li><b>Claimed, and contradicted on the same site.</b> Vheer’s home page says unlimited and no signup. Its pricing page lists 50 credits a month. Not tested. SeeDance V1 on that site is not Seedance 2.5.</li>
<li><b>Least account with a published allowance.</b> Krea: free account, no card, 100 units a day, no watermark, personal use. Not in the catalog.</li>
</ul>
</div>"""

    next_steps = f"""<div class="card" id="next-steps">
<h2>What to do next</h2>
<ul>
<li><b>Check the vendor page.</b> No-account access can change without notice. Open {hf_zero} or {deepai} and confirm the terms before you rely on them.</li>
<li><b>Try the calculator.</b> If you end up paying, put your clip length into the <a href="{e(calc_href)}">credit calculator</a>.</li>
<li><b>Open the model page.</b> Every current catalog rate, with its source and date: <a href="{e(model_href['veo-3-1'])}">Veo 3.1</a> · <a href="{e(model_href['gemini-omni-flash'])}">Gemini Omni Flash</a> · <a href="{e(model_href['wan-3-0'])}">Wan 3.0</a> · <a href="{e(model_href['wan-3-0-prime'])}">Wan 3.0 Prime</a> · <a href="{e(model_href['grok-imagine'])}">Grok Imagine</a>.</li>
</ul>
</div>"""

    body = f"""<p class="small"><a href="{root("/guides/")}">Guides</a> › No sign-up</p>
<h1>{e(PHRASE)}</h1>
<p class="lead">{lead}</p>
<p class="small">Last checked {e(LAST)}. Official pages were read {e(CHECKED_WHEN)}. Catalog rows use the date on each row. Affiliate links never change this price order. Every dollar-per-second figure below names its seller and states its usage assumption, tier, resolution, and audio.</p>
{takeaways}

<h2>{e(QUESTION)}</h2>
<p>{e(a_which)}</p>
{routes_table}
<p class="small">These services are outside the VidFare catalog. Sources and check time {e(CHECKED_WHEN)}. We did not run a generation.</p>

<h2>Do the catalog models need an account to generate video?</h2>
<p>{e(a_catalog)} Higgsfield sells several of these models. {hf_free}, read {e(CHECKED_WHEN)}, says every new account starts on the free plan, the plan has no monthly credits, models on it still deduct credits, and a watermark can appear. That is an account. Which of the nine models are in the free set is not stated. <a href="{e(hf_guide)}">Higgsfield pricing explained</a>.</p>
{catalog_table}
<p class="small">Sources and check time {e(CHECKED_WHEN)}, except where a cell cites the Nov 15, 2026 record. “Not re-confirmed” means this fetch did not include the plan text.</p>

<h2>Which tools outside the catalog still ask for an account?</h2>
<p>These products are not VidFare catalog models. They are here because people search for them next to the nine models. Each cell is the page we read, not a test generation.</p>
{outside_table}
<p class="small">Sources and check time {e(CHECKED_WHEN)}. Google Flow is the seller for Veo 3.1 and the Omni Flash line, so it is in the catalog table above rather than listed here as an extra model.</p>

<h2>Is there a paid option with no account?</h2>
<p>{e(a_paid)}</p>
{paid_table}
<p>Rows are in price order. A catalog plan rate assumes you use what you pay for. An API rate is billed per second of output. DeepAI’s no-account rates are published on its own page and are not catalog rows. Affiliate links never change this price order.</p>

<h2>What is the least sign-up with a published allowance?</h2>
<p>{e(a_least)}</p>
<ul>
<li><b>Hugging Face Spaces.</b> Best for: the no-account allowance a provider states as a number, 2 minutes of GPU time a day. Not for: a known clip count, which is not published, or a fast queue, because unauthenticated use is low priority. {hf_zero}.</li>
<li><b>Krea, with a free account.</b> Best for: no credit card, 100 units a day, and no watermark, all stated by Krea. Not for: commercial work, because Krea says free-plan videos are for personal use, or for Seedance 2.5 and Veo 3.1, which need Pro or higher. Not in the VidFare catalog. {krea_video} · {krea_plans}.</li>
<li><b>Google Flow, with an account.</b> Best for: a daily amount you can count, 50 credits, about five Veo 3.1 Lite clips at 720p if every credit goes to Lite. Not for: skipping the age and region rules, or generating during the peak hours the credit help page names, without a paid plan. Related: <a href="{e(flow_calc)}">Google Flow credits calculator</a> · <a href="{e(model_href['veo-3-1'])}">Veo 3.1</a> · <a href="{e(model_href['gemini-omni-flash'])}">Gemini Omni Flash</a>.</li>
</ul>
<p>No line given. Vheer, Perchance, Meta AI, the Grok consumer site, Wan, and Kling do not have a best-for line: the pages we could read do not support one, or they did not load.</p>
<p>Related: <a href="{e(free_href)}">free AI video generators: what you get</a> · <a href="{e(t2v_href)}">free text to video AI</a> · <a href="{e(i2v_href)}">free image to video AI</a> · <a href="{e(kling_guide)}">Kling AI pricing</a> · <a href="{e(runway_guide)}">Runway pricing</a> · <a href="{e(grok_guide)}">Grok Imagine cost</a> · <a href="{e(wan_guide)}">cheapest Wan 3.0</a> · <a href="{e(seedance_guide)}">cheapest Seedance 2.5</a>.</p>

<h2>What is confirmed, and what is not?</h2>
<p>{e(a_unknown)}</p>
<p><b>Confirmed {e(CHECKED_WHEN)} on official pages:</b> Hugging Face’s unauthenticated, free, and PRO GPU tiers, the $9 PRO price, and the 8× quota line; the LTX 2.3 Distilled Space loading on ZeroGPU; Vheer’s home-page claim, its Free plan card, and the SeeDance V1 Pro Fast selector; DeepAI’s pay-per-call rates, resolutions, and Pro terms; Google Flow’s age and region rules, 50 daily credits, Veo 3.1 Lite credit cost, and Omni Flash 1.2 credit cost, plus the December 5, 2026 retirement note for Omni Flash 1.1; Krea’s free account, 100 units a day, no card, no watermark, personal-use rule, and the Pro requirement for Seedance 2.5 and Veo 3.1; Dreamina’s account-tied free credits and the 120-a-day US figure on a Dreamina guide; Hailuo’s login rule, watermark, and three-day welcome credits; Runway’s 125 one-time Free credits; Pika Free’s 0 monthly credits; Luma’s Plus plan at {e(cost_money(30))} a month; Higgsfield’s free-plan rules. <b>Not readable {e(CHECKED_WHEN)}:</b> Wan’s plan text, Kling’s plan text, x.ai/grok, meta.ai, and Perchance. <b>Catalog rows</b> use the checked date on each paid-table row.</p>
<p class="small">Affiliate links never change this price order.</p>
{next_steps}
{g["how_block"]()}
"""

    blob = (body + description(g) + PHRASE).lower()
    if "sora" in blob:
        raise SystemExit(f"{PATH} source would name Sora")
    for banned in ("america/caracas", "utc"):
        if banned in blob:
            raise SystemExit(f"{PATH} source contains {banned}")
    for slug in UNPUBLISHED:
        if slug in body:
            raise SystemExit(f"{PATH} links unpublished {slug}")

    title = g["page_title"](PHRASE)
    if len(title) > 60:
        raise SystemExit(f"{PATH} title is {len(title)} characters: {title}")
    g["guide_page"](PATH, title, description(g), body, faqs)
    return PATH
