"""Guide: AI video generator apps.

Imported by scripts/build_site.py. US store listings and official pages
were read on 2026-11-17. This page never names Sora.
"""

PATH = "/guides/ai-video-generator-apps/"
LABEL = "AI video generator apps"
PHRASE = "AI video generator apps"
H1 = "AI video generator apps: official listings and prices"
QUESTION = "Which AI video generators have an official app?"
CHECKED = "2026-11-17"
CHECKED_WHEN = "Nov 17, 2026, 9:49–9:57 AM ET (6:49–6:57 AM PT)"

# Official iPhone listings (US App Store IDs), confirmed via Apple’s public lookup.
IOS = {
    "kling": "https://apps.apple.com/us/app/id6738049229",
    "runway": "https://apps.apple.com/us/app/id1665024375",
    "pika": "https://apps.apple.com/us/app/id6680155400",
    "dreamina": "https://apps.apple.com/us/app/id6749606485",
    "luma": "https://apps.apple.com/us/app/id6478852867",
    "grok": "https://apps.apple.com/us/app/id6670324846",
    "krea": "https://apps.apple.com/us/app/id6742134132",
    "flow": "https://apps.apple.com/us/app/id6751294549",
    "gemini": "https://apps.apple.com/us/app/id6477489729",
    "meta": "https://apps.apple.com/us/app/id1558240027",
}
PLAY = {
    "kling": "https://play.google.com/store/apps/details?id=kling.ai.video.chat",
    "runway": "https://play.google.com/store/apps/details?id=com.runwayml.prod",
    "dreamina": "https://play.google.com/store/apps/details?id=com.lemon.dreamina",
    "hailuo": "https://play.google.com/store/apps/details?id=ai.hailuo.video",
    "grok": "https://play.google.com/store/apps/details?id=ai.x.grok",
    "flow": "https://play.google.com/store/apps/details?id=com.google.android.apps.labs.whisk",
    "gemini": "https://play.google.com/store/apps/details?id=com.google.android.apps.bard",
    "meta": "https://play.google.com/store/apps/details?id=com.facebook.stella",
}
HAILUO_HOME = "https://hailuoai.video/"
XAI_GROK = "https://x.ai/grok"
FLOW_WHERE = "https://support.google.com/flow/answer/16353544?hl=en"
FLOW_MODELS = "https://support.google.com/flow/answer/16352836?hl=en"
FLOW_CREDITS = "https://support.google.com/flow/answer/16526234?hl=en"
GOOGLE_AI_PLANS = "https://one.google.com/about/google-ai-plans/"
KREA_VIDEO = "https://www.krea.ai/features/ai-video-generator"
KREA_PLANS = "https://www.krea.ai/pricing"
PIKA_PLANS = "https://pika.art/pricing"
RUNWAY_PLANS = "https://runway.com/pricing"
KLING_PLANS = "https://kling.ai/app/membership/membership-plan"
KLING_API = "https://kling.ai/document-api/pricing/base/video.md"
LUMA_PLANS = "https://lumalabs.ai/pricing"
HF_PLANS = "https://higgsfield.ai/pricing"
HAILUO_TERMS = "https://hailuoai.video/doc/payment-policy.html"
DREAMINA_PLANS = "https://dreamina.capcut.com/plans"
AA_T2V = "https://artificialanalysis.ai/video/leaderboard/text-to-video"

# Neutral wording for the unconfirmed Google Play listing. Listed in the PR.
LUMA_ANDROID = (
    "Unconfirmed. A Google Play listing with the same title is published by a "
    "different developer (the listing names Infinity AI Solutions) and is "
    "marked “Contains ads.” We could not confirm that listing is official."
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
        "Which AI video tools have an official iPhone or Android app, what "
        "the US listings charge in-app, and how that compares with the web price."
    )


def description(g):
    text = (
        "AI video generator apps: which tools have official iPhone and Android "
        "apps, what they charge in-app, and the web price. Last checked Nov 17, 2026."
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

    def app_src(url, label="App Store"):
        return src(url, label)

    ios_kling = app_src(IOS["kling"], "App Store")
    ios_runway = app_src(IOS["runway"], "App Store")
    ios_pika = app_src(IOS["pika"], "App Store")
    ios_dreamina = app_src(IOS["dreamina"], "App Store")
    ios_luma = app_src(IOS["luma"], "App Store")
    ios_grok = app_src(IOS["grok"], "App Store")
    ios_krea = app_src(IOS["krea"], "App Store")
    ios_flow = app_src(IOS["flow"], "App Store")
    ios_gemini = app_src(IOS["gemini"], "App Store")
    ios_meta = app_src(IOS["meta"], "App Store")
    play_kling = app_src(PLAY["kling"], "Google Play")
    play_runway = app_src(PLAY["runway"], "Google Play")
    play_dreamina = app_src(PLAY["dreamina"], "Google Play")
    play_hailuo = app_src(PLAY["hailuo"], "Google Play")
    play_grok = app_src(PLAY["grok"], "Google Play")
    play_flow = app_src(PLAY["flow"], "Google Play")
    play_gemini = app_src(PLAY["gemini"], "Google Play")
    play_meta = app_src(PLAY["meta"], "Google Play")
    hailuo_home = src(HAILUO_HOME, "hailuoai.video")
    xai_grok = src(XAI_GROK, "x.ai/grok")
    flow_where = src(FLOW_WHERE, "Where you can use Google Flow")
    flow_models = src(FLOW_MODELS, "Google Flow models and supported features")
    flow_credits = src(FLOW_CREDITS, "Google Flow credit help")
    google_plans = src(GOOGLE_AI_PLANS, "Google AI plans")
    krea_video = src(KREA_VIDEO, "Krea’s AI video generator page")
    krea_plans = src(KREA_PLANS, "Krea’s pricing page")
    pika_src = src(PIKA_PLANS, "Pika’s pricing page")
    runway_src = src(RUNWAY_PLANS, "Runway’s pricing page")
    kling_plans = src(KLING_PLANS, "Kling membership plans")
    kling_api = src(KLING_API, "official Kling API pricing")
    luma_src = src(LUMA_PLANS, "Luma’s pricing page")
    hf_ultra = src(HF_PLANS, "Higgsfield Ultra (annual)")
    hailuo_terms = src(HAILUO_TERMS, "Hailuo subscription service terms")
    dreamina_plans = src(DREAMINA_PLANS, "Dreamina plans")
    aa_t2v = src(AA_T2V, "Artificial Analysis AA-Video-T2V v2.1 leaderboard")

    free_t2v = root("/guides/free-text-to-video-ai/")
    flow_calc = root("/guides/google-flow-credits-calculator/")
    runway_guide = root("/guides/runway-pricing/")
    kling_guide = root("/guides/kling-ai-pricing/")
    grok_guide = root("/guides/grok-imagine-video-cost/")
    free_href = root("/guides/free-ai-video-generators/")
    cheapest_href = root("/guides/cheapest-ai-video-generator/")
    kling_model = root("/models/kling-3-0/")
    runway_model = root("/models/runway-gen-4/")
    veo_href = root("/models/veo-3-1/")
    grok_model = root("/models/grok-imagine/")
    seedance_href = root("/models/seedance-2-5/")
    calc_kling = root("/calculator/?model=kling-3-0&seconds=10")
    calc_home = root("/calculator/")

    def trow(*cells):
        return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"

    # App Store ratings: Apple public lookup on Nov 17, 2026, after Claude’s
    # morning read. Dreamina moved to 3.0 from 53 ratings (was 2.9 from 51).
    # Gemini’s rating count moved to 2,436,492 (was 2,435,388).
    listings = f"""<div class="tblwrap" id="app-listings-table">
<table style="min-width:1200px;width:1200px">
<thead><tr>
<th>Tool</th>
<th>iPhone (US App Store)</th>
<th>Android (Google Play)</th>
<th>What the listing says about video</th>
<th>In-app purchases</th>
<th>Source</th>
</tr></thead>
<tbody>
{trow(
    "Kling AI",
    "Yes. “Kling AI: AI Image&amp;Video Maker,” seller KLING AI PTE. LTD. Rated 4.7 from 34,667 ratings. Requires iOS 15.0.",
    "Yes. Same title, developer KLING AI. Rated 4.5.",
    "The listing says it turns text and images into videos, up to 15 seconds in native 1080p or 4K, with Video Extension up to 3 minutes.",
    "Yes on both stores.",
    f"{ios_kling} · {play_kling}, read {e(CHECKED_WHEN)}. iPhone rating also confirmed in Apple’s public lookup on Nov 17, 2026.",
)}
{trow(
    "Runway",
    "Yes. “Runway: AI Image &amp; Video,” seller Runway AI, Inc. Rated 4.5 from 20,575 ratings. Requires iOS 16.4. Linked from runway.com.",
    "Yes. Same title, developer Runway AI Inc. Rated 4.0. Linked from runway.com.",
    "Text to video, image to video, and video to video. The listing names Seedance 2.5, Kling 3 Pro, and Gen-4.5.",
    "Yes on both stores.",
    f"{ios_runway} · {play_runway}, read {e(CHECKED_WHEN)}. iPhone rating also confirmed in Apple’s public lookup on Nov 17, 2026.",
)}
{trow(
    "Pika",
    "Yes. “Pika - AI Video,” seller Mellis, Inc. Rated 4.7 from 4,324 ratings. Requires iOS 18.0.",
    "None found from Mellis, Inc. Google Play search returned apps under the Pika name from other developers.",
    "The listing describes building a video from your photos and a text prompt, and image-to-video.",
    "Yes on the App Store.",
    f"{ios_pika}, read {e(CHECKED_WHEN)}. iPhone rating also confirmed in Apple’s public lookup on Nov 17, 2026.",
)}
{trow(
    "Dreamina",
    "Yes. “Dreamina AI: Image&amp;Video Maker,” seller BYTEDANCE PTE. LTD. Rated 3.0 from 53 ratings. Requires iOS 15.0.",
    "Yes. Same title, developer Bytedance Pte. Ltd. Rated 2.9.",
    "The listing says you can generate video clips from a text prompt or animate your images.",
    "Yes on both stores.",
    f"{ios_dreamina} · {play_dreamina}, read {e(CHECKED_WHEN)}. iPhone rating from Apple’s public lookup on Nov 17, 2026 (it had moved from 2.9 from 51 ratings earlier that day).",
)}
{trow(
    "Hailuo (MiniMax)",
    "Unknown. Hailuo’s own site points to an App Store listing, but that address returned not found in the US store on Nov 17, 2026, and Apple’s directory search returned no app from MiniMax.",
    "Yes. “Hailuo AI: Image&amp;Video Maker,” developer MiniMax AI. Rated 4.3. Linked from hailuoai.video.",
    "An image and video maker, from the listing title.",
    "Yes on Google Play.",
    f"{play_hailuo} · {hailuo_home}, read {e(CHECKED_WHEN)}.",
)}
{trow(
    "Luma Dream Machine",
    "Yes. “Luma Dream Machine,” seller Luma AI, Inc. Rated 4.5 from 1,800 ratings. Requires iOS 17.0. Last updated Apr 17, 2026.",
    e(LUMA_ANDROID),
    "The listing says you can create images and videos with Luma’s models, “available now on iOS.”",
    "Yes on the App Store.",
    f"{ios_luma}, read {e(CHECKED_WHEN)}. iPhone rating and Apr 17, 2026 update also confirmed in Apple’s public lookup on Nov 17, 2026. No official Google Play link is given, because we could not confirm one.",
)}
{trow(
    "Grok",
    "Yes. “Grok,” seller X Corp. Rated 4.9 from 1,615,809 ratings. Requires iOS 17.4.",
    "Yes. “Grok,” developer shown as SpaceX Super Intelligence. Rated 4.9. The product page says Grok is available on web, iOS and Android.",
    "The listing says Grok Imagine can create short videos with sound, or turn your photos into videos.",
    "Yes on both stores.",
    f"{ios_grok} · {play_grok} · {xai_grok}, read {e(CHECKED_WHEN)}. iPhone rating also confirmed in Apple’s public lookup on Nov 17, 2026.",
)}
{trow(
    "Krea",
    "Yes. “Krea: AI Images and Videos,” seller KREA.AI, INC. Rated 4.5 from 756 ratings. Requires iOS 18.0.",
    "None found from Krea in Google Play search on Nov 17, 2026.",
    "The listing says you can create videos with generators such as Kling, Hailuo, Hunyuan, Luma Ray 2, or Runway. That is the listing’s own list.",
    "Yes on the App Store.",
    f"{ios_krea}, read {e(CHECKED_WHEN)}. iPhone rating also confirmed in Apple’s public lookup on Nov 17, 2026.",
)}
{trow(
    "Google Flow",
    "Yes. “Google Flow,” seller Google LLC. Rated 3.7 from 161 ratings. Requires iOS 16.0.",
    "Yes. “Google Flow,” developer Google Labs. Rated 4.2.",
    "The listing says you can create and refine images and videos from your phone. Flow help says the mobile app can be downloaded in its supported countries.",
    "None listed on the App Store. The Google Play listing is not marked with in-app purchases.",
    f"{ios_flow} · {play_flow} · {flow_where}, read {e(CHECKED_WHEN)}. iPhone rating also confirmed in Apple’s public lookup on Nov 17, 2026.",
)}
{trow(
    "Google Gemini",
    "Yes. “Google Gemini,” seller Google LLC. Rated 4.7 from 2,436,492 ratings. Requires iOS 18.2.",
    "Yes. “Google Gemini,” developer Google LLC. Rated 4.5.",
    "The listing says video with Gemini Omni is for Google AI Plus, Pro, Ultra, and Workspace users.",
    "Yes on the App Store (Google AI plans). The Google Play listing is not marked with in-app purchases.",
    f"{ios_gemini} · {play_gemini}, read {e(CHECKED_WHEN)}. iPhone rating count from Apple’s public lookup on Nov 17, 2026 (it had moved from 2,435,388 earlier that day).",
)}
{trow(
    "Meta AI",
    "Yes. “Meta AI,” seller Meta Platforms, Inc. Rated 4.7 from 300,598 ratings. Requires iOS 18.4.",
    "Yes. “Meta AI,” developer Meta Platforms, Inc. Rated 4.6.",
    "Unknown. The listing describes image generation and does not mention video generation.",
    "None listed on the App Store. The Google Play listing is marked with in-app purchases.",
    f"{ios_meta} · {play_meta}, read {e(CHECKED_WHEN)}. iPhone rating also confirmed in Apple’s public lookup on Nov 17, 2026.",
)}
{trow(
    "Higgsfield, Wan",
    "None found from the vendor. Apple’s directory search returned only apps from other developers that use these names.",
    "None found from the vendor. Google Play search returned only apps from other developers that use these names.",
    "Not applicable.",
    "Not applicable.",
    f"Apple’s app directory search and Google Play search, run {e(CHECKED_WHEN)}.",
)}
</tbody></table></div>"""

    iap_table = f"""<div class="tblwrap" id="in-app-prices-table">
<table style="min-width:1200px;width:1200px">
<thead><tr>
<th>App</th>
<th>Items and listed US price (tier)</th>
<th>Resolution</th>
<th>Audio</th>
<th>Same tier on the vendor’s web page</th>
<th>Source and date checked</th>
</tr></thead>
<tbody>
{trow(
    "Kling AI",
    "Standard plan (monthly) $10.00 · Pro plan (monthly) $37.00 · Premier plan (monthly) $92.00 · 660 Credits $10.00",
    "not stated on the listing",
    "not stated on the listing",
    "Standard: list $10.00 a month, $6.99 for the first month, then $8.80 a month, with 660 credits a month. Read Nov 14, 2026 PT in <a href=\"" + e(kling_guide) + "\">Kling AI pricing and credits</a>; the page did not load on Nov 17, 2026.",
    f"{ios_kling}, read 2026-11-17. {kling_plans}, read Nov 14, 2026 PT.",
)}
{trow(
    "Runway",
    "Standard - Monthly $14.99 · Standard - Yearly $143.99 · Pro - Monthly $35.00 · Max - Monthly $95.00 · 1000 Generation Credits $10.00",
    "not stated on the listing",
    "not stated on the listing",
    "Standard: $15 a month, or $12 a month billed yearly, with 625 credits a month.",
    f"{ios_runway} · {runway_src}, both read 2026-11-17.",
)}
{trow(
    "Pika",
    "Starter $14.99 · Creator $49.99 · 1,500 Credits $34.99 · 3,000 Credits $69.99. The billing period of Starter and Creator is not stated on the listing.",
    "not stated on the listing",
    "not stated on the listing",
    "Starter: $10 a month, or $8 a month billed yearly, with 600 credits a month. Creator: $35 a month. Packs: 60 credits per $1.",
    f"{ios_pika} · {pika_src}, both read 2026-11-17. The $34.99 / 1,500-credit pack was also on the US App Store page later on Nov 17, 2026.",
)}
{trow(
    "Dreamina",
    "Basic Monthly Subscription $15.00 · Standard Monthly Subscription $36.00 · Credits Pack $10.00",
    "not stated on the listing",
    "not stated on the listing",
    "Basic: $15 a month for 1,575 credits a month. Read Nov 15, 2026 in <a href=\"" + e(free_href) + "\">free AI video generators: what you get</a>.",
    f"{ios_dreamina}, read 2026-11-17. {dreamina_plans}, read Nov 15, 2026.",
)}
{trow(
    "Luma Dream Machine",
    "Lite $9.99 · Plus $29.99 · Unlimited $94.99. The billing period is not stated on the listing.",
    "not stated on the listing",
    "not stated on the listing",
    "Plus: $30 a month with 10,000 credits. The web page on Nov 17, 2026 lists Plus, Pro ($90), and Ultra ($300); it lists no Lite or Unlimited plan.",
    f"{ios_luma} · {luma_src}, both read 2026-11-17.",
)}
{trow(
    "Grok",
    "SuperGrok Lite $10.00 · SuperGrok $30.00 · SuperGrok Plus $100.00 · SuperGrok Heavy $300.00 · Extra Usage Credits 5 USD $5.00. The billing period is not stated on the listing.",
    "not stated on the listing",
    "not stated on the listing",
    "Not re-read on Nov 17, 2026. The plan grid read Nov 12, 2026 PT is in <a href=\"" + e(grok_guide) + "\">how much a Grok Imagine video costs</a>.",
    f"{ios_grok}, read 2026-11-17.",
)}
{trow(
    "Krea",
    "Individual Basic Monthly $9.00 · Individual Pro Monthly $35.00 · Individual Max Monthly $70.00 · 10k Compute Units $20.00",
    "not stated on the listing",
    "not stated on the listing",
    "Basic: $9 a month on monthly billing, with 5,000 units a month. Free: $0, 100 units a day.",
    f"{ios_krea} · {krea_video}, both read 2026-11-17.",
)}
{trow(
    "Google Gemini (Google AI plans)",
    "Google AI Plus (400 GB) $4.99 · Google AI Pro (5 TB) $19.99 · Google AI Ultra (30 TB) $199.99",
    "not stated on the listing",
    "not stated on the listing",
    "Google AI Plus: $4.99 a month with 200 extra Flow credits a month. Google AI Pro: $19.99 a month with 1,000.",
    f"{ios_gemini}, read 2026-11-17. {google_plans}, checked 2026-11-16 PT · {flow_credits}, read 2026-11-17.",
)}
{trow(
    "Google Flow",
    "No in-app purchases are listed.",
    "Not applicable",
    "Not applicable",
    "50 Flow credits a day with or without a paid Google AI plan, shared across your account on any device.",
    f"{ios_flow} · {flow_credits}, both read 2026-11-17.",
)}
</tbody></table></div>"""

    r146 = _row_by_id(g, "r146")
    r111 = _row_by_id(g, "r111")
    r209 = _row_by_id(g, "r209")
    r059 = _row_by_id(g, "r059")
    r062 = _row_by_id(g, "r062")
    flow = (g.get("db") or {}).get("flow") or {}
    pro = (flow.get("plans") or {}).get("gflow-pro") or {}
    pro_rate = float(pro["usd_month"]) / float(pro["credits_month"]) * 10.0 / 8.0
    pika_starter = 10.0 / 600.0 * 10.0 / 5.0
    luma_plus = 30.0 / 10000.0 * 100.0 / 5.0
    runway_turbo = 15.0 / 104.0
    runway_gen45 = 15.0 / 52.0

    def cat_source(r):
        href, rel = g["outbound"](r["source_url"])
        return (
            f'<a href="{e(href)}" rel="{rel}" target="_blank">source</a>, '
            f"catalog row {e(r['id'])}, checked {e(r['checked'])} PT."
        )

    krea_audio = shown_audio(r146)
    krea_audio_txt = "with audio" if krea_audio == "with" else ("without audio" if krea_audio == "without" else "not stated")

    paid_bits = [
        (
            float(r146["usd_per_second"]),
            trow(
                "Krea · Basic (yearly), $5 a month for 5,000 units",
                "Veo 3.1 Lite, 4-second clip",
                e(shown_resolution(r146)),
                e(krea_audio_txt),
                f"{e(rate_money(r146['usd_per_second']))}/s {e(rate_label(r146))}",
                "Assumes every unit you pay for is used. Krea publishes approximate clip counts, so units per clip are derived.",
                cat_source(r146),
            ),
        ),
        (
            pro_rate,
            trow(
                f"Google Flow · {e(pro['plan'])}, {e(g['cost_money'](pro['usd_month']))} a month for {e(str(int(pro['credits_month'])))} credits",
                "Veo 3.1 Lite, 8-second clip",
                "720p",
                "not stated",
                f"{e(rate_money(pro_rate))}/s from credit plan",
                f"{e(g['cost_money'](pro['usd_month']))} ÷ {e(str(int(pro['credits_month'])))} credits × 10 credits ÷ 8 seconds. Assumes every monthly credit goes to 8-second Lite clips. The 50 daily credits are not counted.",
                f"{google_plans}, checked {e(pro['checked'])} PT · {flow_credits}, read 2026-11-17. Not a catalog row; figured from the Flow plan data in prices.json.",
            ),
        ),
        (
            pika_starter,
            trow(
                "Pika · Starter (web, monthly), $10 a month for 600 credits",
                "Pika H3 Flex, 5-second clip",
                "768p",
                "not stated",
                f"{e(rate_money(pika_starter))}/s from credit plan",
                "$10 ÷ 600 credits × 10 credits ÷ 5 seconds. Assumes all 600 credits go to this model.",
                f"{pika_src}, read 2026-11-17. Not a catalog row; figured from Pika’s pricing page.",
            ),
        ),
        (
            luma_plus,
            trow(
                "Luma · Plus (web, monthly), $30 a month for 10,000 credits",
                "Ray3.2, text-to-video, SDR, 5-second clip",
                "720p",
                "not stated on the vendor’s pricing table",
                f"{e(rate_money(luma_plus))}/s from credit plan",
                "$30 ÷ 10,000 credits × 100 credits ÷ 5 seconds. Assumes every credit is used. The page also prints “No keyframes: plus 30 credits”; if that applies to a text-only clip, the clip is 130 credits, or $0.078/s.",
                f"{luma_src}, read 2026-11-17. Not a catalog row; figured from Luma’s pricing page.",
            ),
        ),
        (
            runway_turbo,
            trow(
                "Runway · Standard (web, monthly), $15 a month for 625 credits",
                "Gen-4 Turbo",
                "not stated in that line",
                "not stated",
                f"{e(rate_money(runway_turbo))}/s from credit plan",
                "$15 ÷ 104 seconds. Runway states that 625 credits equal 104 seconds of Gen-4 Turbo. Assumes all 625 credits go to this model.",
                f"{runway_src}, read 2026-11-17. Not a catalog row; figured from Runway’s pricing page.",
            ),
        ),
        (
            runway_gen45,
            trow(
                "Runway · Standard (web, monthly), $15 a month for 625 credits",
                "Gen-4.5",
                "not stated in that line",
                "not stated",
                f"{e(rate_money(runway_gen45))}/s from credit plan",
                "$15 ÷ 52 seconds. Runway states that 625 credits equal 52 seconds of Gen-4.5. Assumes all 625 credits go to this model.",
                f"{runway_src}, read 2026-11-17. Not a catalog row; figured from Runway’s pricing page.",
            ),
        ),
    ]
    paid_bits.sort(key=lambda item: item[0])
    unknown_rows = (
        trow(
            "Kling AI · any in-app plan",
            "Kling models in the app",
            "unknown",
            "unknown",
            "Unknown",
            f"Credits per clip in the app are not published on a page we could read, so no plan figure is given. Cheapest catalog route for Kling 3.0: {e(rate_money(r111['usd_per_second']))}/s {e(rate_label(r111))} · {hf_ultra} · {e(shown_resolution(r111))} · audio {e(shown_audio(r111))}, if every credit is used. The official API is {e(rate_money(r059['usd_per_second']))}/s at {e(shown_resolution(r059))} without audio and {e(rate_money(r062['usd_per_second']))}/s with audio.",
            f"{cat_source(r111)} · {kling_api}, checked {e(r059['checked'])} PT.",
        )
        + trow(
            "Grok · any in-app plan",
            "Grok Imagine Video 1.5",
            "unknown",
            "unknown",
            "Unknown",
            f"Paid plans draw on a shared weekly usage pool, and the pages read Nov 12, 2026 PT do not say how much one video uses. Cheapest catalog route: {e(rate_money(r209['usd_per_second']))}/s {e(rate_label(r209))} · xAI API · Grok Imagine Video 1.5 Lite · {e(shown_resolution(r209))} · audio {e(shown_audio(r209))}, billed per second of output.",
            cat_source(r209),
        )
        + trow(
            "Dreamina, Hailuo · any in-app plan",
            "Seedance and Hailuo models in the app",
            "unknown",
            "unknown",
            "Unknown",
            "Credits per clip are not published on the pages we read. Hailuo Standard is $14.99 a month for 1,000 credits; Dreamina Basic is $15 a month for 1,575 credits.",
            f"{hailuo_terms}, read 2026-11-17 · {dreamina_plans}, read Nov 15, 2026.",
        )
    )
    paid_table = f"""<div class="tblwrap" id="app-plan-rates-table">
<table style="min-width:1200px;width:1200px">
<thead><tr>
<th>Plan and tier</th>
<th>Model and clip</th>
<th>Resolution</th>
<th>Audio</th>
<th>Cost per second</th>
<th>Usage assumption</th>
<th>Source and date checked</th>
</tr></thead>
<tbody>
{''.join(html for _usd, html in paid_bits)}
{unknown_rows}
</tbody></table></div>"""

    a_q = (
        "Of the 13 tools this guide covers, ten have an official iPhone app in "
        "the US App Store today and eight have an official Android listing on "
        "Google Play. Kling AI, Runway, Dreamina, Grok, Google Flow, Google "
        "Gemini, and Meta AI are on both stores. Pika and Krea are on iPhone "
        "only, and Luma is confirmed on iPhone only. Hailuo is confirmed on "
        "Android; the iPhone listing its own site points to returned not found "
        "in the US store on Nov 17, 2026. We found no app published by "
        "Higgsfield or Wan on either store. Searches on both stores also "
        "return apps from other developers under these names, so check the "
        "developer name before you install or pay."
    )
    a_how = (
        "An app counts as official here when the seller or developer name on "
        "the store listing is the vendor’s own, or when the vendor’s own site "
        "links to that listing. Each iPhone listing was read from the US App "
        "Store, including its seller, rating, and in-app purchase list. Each "
        "Android listing was read from Google Play in the US, including its "
        "developer name, rating, and whether it is marked with in-app "
        "purchases. Store listings do not state the resolution or audio of "
        "what a purchase buys, so those are marked not stated. Per-second "
        "costs come from the vendor’s web pricing page or from our catalog, "
        "never from a store listing."
    )
    a_iap = (
        "The App Store lists up to ten in-app items per app, with a name and a "
        "US price, and it does not state the billing period unless the period "
        "is in the item name. Runway’s Standard is $14.99 a month in the app "
        "and $15 on the web. Kling’s Standard plan (monthly) is $10.00 in the "
        "app, which matches the web list price; the web page read Nov 14, 2026 "
        "PT showed $8.80 a month after a $6.99 first month. Pika’s 1,500-credit "
        "pack is $34.99 in the App Store, about $0.0233 per credit; on the "
        "web, packs are 60 credits per $1, about $0.0167 per credit."
    )
    a_cost = (
        "It depends on the plan and the model, and four of these apps do not "
        "publish enough to work it out. Where the vendor publishes credits per "
        "clip, the plan figures are: $0.025 per second for Veo 3.1 Lite at "
        "720p on Google AI Pro in Google Flow; $0.0333 per second for Pika H3 "
        "Flex at 768p on Pika Starter; $0.06 per second for Luma Ray3.2 at "
        "720p on Luma Plus; and $0.144 per second for Gen-4 Turbo on Runway "
        "Standard. Each assumes you use every credit you pay for, and audio is "
        "not stated on any of those rows. Kling, Grok, Dreamina, and Hailuo "
        "do not publish credits per clip for their plans on the pages we read, "
        "so their in-app cost per second is unknown."
    )
    a_best = (
        "For a free daily allowance on a phone: Google Flow, with 50 credits a "
        "day and no in-app purchases listed. For several model families in one "
        "official app on both stores: Runway. For Kling itself on both stores: "
        "Kling AI. For the most-rated app in this guide: Grok. For iPhone "
        "users who want Pika’s own model: Pika. For a free plan with no card "
        "and no watermark on iPhone: Krea. A best-for or not-for line is given "
        "only where a store listing, a vendor page, or a cited score supports it."
    )
    a_unknown = (
        "Unknown, and not guessed: whether Hailuo’s iPhone app is available in "
        "the US App Store; whether the Google Play listing titled “Luma Dream "
        "Machine,” published by a different developer, is official; whether "
        "Higgsfield or Wan publish an app under another name; the billing "
        "period of App Store items whose name does not state it; the credits, "
        "resolution, and audio attached to any in-app purchase, which store "
        "listings do not state; credits per clip on Kling, Grok, Dreamina, and "
        "Hailuo plans; and Meta AI’s video generation limits. Store ratings "
        "and prices are for the US stores and change over time."
    )

    faqs = [
        (QUESTION, a_q),
        ("How did we check, and what counts as official?", a_how),
        ("What do the apps charge in-app?", a_iap),
        ("What does a second of video cost on each app’s plan?", a_cost),
        ("Which app is best for each use?", a_best),
        ("What is confirmed, and what is not?", a_unknown),
    ]
    for q, a in faqs:
        raw = (q + " " + a).lower()
        for bad in ("subscribe", "newsletter", "buttondown"):
            if bad in raw:
                raise SystemExit(f"{PATH} FAQ text contains {bad}")

    lead = (
        f"Ten of the 13 tools this guide covers have an official iPhone app in "
        f"the US App Store today, and eight have an official Android listing on "
        f"Google Play. Kling AI, Runway, Dreamina, Grok, Google Flow, Google "
        f"Gemini, and Meta AI are on both stores; Pika and Krea are iPhone only; "
        f"and we found no app published by Higgsfield or Wan. Store listings and "
        f"vendor pages were read {e(CHECKED_WHEN)}. In-app prices are copied from "
        f"the App Store’s own list, and anything a listing does not state is "
        f"marked unknown. If you only want the lowest price per second, see "
        f"<a href=\"{e(cheapest_href)}\">the cheapest AI video generator by model</a>."
    )

    takeaways = f"""<div class="card" id="takeaways">
<h2>Key takeaways</h2>
<ul>
<li><b>On both stores.</b> Kling AI, Runway, Dreamina, Grok, Google Flow, Google Gemini, and Meta AI.</li>
<li><b>iPhone only.</b> Pika and Krea. Luma Dream Machine is confirmed on iPhone only. Hailuo is confirmed on Android; its iPhone link returned not found in the US store on Nov 17, 2026.</li>
<li><b>No vendor app found.</b> Higgsfield and Wan. Both stores return apps from other developers under those names, so check the developer name.</li>
<li><b>The app is not always the cheapest place to buy.</b> Pika’s 1,500-credit pack is $34.99 in the App Store, about $0.0233 per credit; on the web, packs are 60 credits per $1, about $0.0167 per credit.</li>
<li><b>Free on a phone.</b> Google Flow gives 50 credits a day, shared across your account on any device, and its listings show no in-app purchases.</li>
<li><b>What listings leave out.</b> No store listing states the resolution or audio of what a purchase buys, so both are marked not stated on every in-app row.</li>
</ul>
</div>"""

    next_steps = f"""<div class="card" id="next-steps">
<h2>What to do next</h2>
<ul>
<li><b>Check the vendor page.</b> Open the app from the link on the vendor’s own site, confirm the developer name, and compare the in-app price with the web price before you buy: {runway_src} · {pika_src} · {kling_plans}.</li>
<li><b>Try the calculator.</b> Put your clip length into the <a href="{e(calc_kling)}">credit calculator for Kling 3.0 at 10 seconds</a>, or pick any model in the <a href="{e(calc_home)}">credit calculator</a>, to see what a plan really costs per second.</li>
<li><b>Open the model page.</b> Every current rate, with its source and date: <a href="{e(kling_model)}">Kling 3.0</a> · <a href="{e(runway_model)}">Runway Gen-4</a> · <a href="{e(veo_href)}">Veo 3.1</a> · <a href="{e(grok_model)}">Grok Imagine</a> · <a href="{e(seedance_href)}">Seedance 2.5</a>.</li>
</ul>
</div>"""

    lookalikes = (
        "Check the seller or developer name on the listing, and prefer the link "
        "on the vendor’s own website. On Nov 17, 2026, Google Play search for "
        "Pika and for Higgsfield returned listings from other developers under "
        "those names. A Google Play listing with the title “Luma Dream Machine” "
        "is published by a different developer from Luma’s iPhone app (the "
        "listing names Infinity AI Solutions). A matching name and logo are not "
        "proof that a listing is official. If a listing is marked “Contains ads,” "
        "or the developer name is not the vendor’s, we treat it as unconfirmed."
    )

    body = f"""<p class="small"><a href="{root("/guides/")}">Guides</a> › AI video generator apps</p>
<h1>{e(H1)}</h1>
<p class="lead">{lead}</p>
<p class="small">Last checked {e(LAST)}. Store listings and official pages were read {e(CHECKED_WHEN)}. Catalog rows use the date on each row. Affiliate links never change this price order. Every dollar-per-second figure below states its usage assumption, tier, resolution, and audio.</p>
{takeaways}

<h2>{e(QUESTION)}</h2>
<p>{e(a_q)}</p>

<h2>How did we check, and what counts as official?</h2>
<p>{e(a_how)}</p>

<h2>Official app listings by store</h2>
<p>One row per tool. Ratings are the US App Store rating and count, and the Google Play rating, as shown when the listing was read. A rating is not a quality score for the video model.</p>
{listings}

<h2>What do the apps charge in-app?</h2>
<p>{e(a_iap)}</p>
{iap_table}
<p>Item names are copied as the App Store prints them. The listing shows a selection of items, not every plan. Google Play marks a listing with in-app purchases but does not print an item list in the page we read, so Android in-app prices are unknown here.</p>

<h2>What does a second of video cost on each app’s plan?</h2>
<p>{e(a_cost)}</p>
{paid_table}
<p>Rows with a figure are in price order. Plan figures use the vendor’s web price; an App Store price for the same tier can differ, as the table above shows. Affiliate links never change this price order.</p>

<h2>Which app is best for each use?</h2>
<p>{e(a_best)}</p>
<ul>
<li><b>Google Flow.</b> Best for: a free daily allowance on a phone: 50 credits a day, shared across your account on any device, with no in-app purchases listed. Gemini Omni Flash 1.2, one of its models, is Elo 1151 ±14 (rank range 3–9) on {aa_t2v}. Not for: Frames to Video with Omni Flash 1.2, which Google says is currently only available at Google Flow on the web, or generating between roughly 2 PM and 5 PM UTC without a paid plan. {flow_models} · {flow_credits}. Related: <a href="{e(flow_calc)}">Google Flow credits calculator</a> · <a href="{e(free_t2v)}">free text to video AI</a>.</li>
<li><b>Runway.</b> Best for: several model families in one official app on both stores; the listing names Seedance 2.5, Kling 3 Pro, and Gen-4.5. Not for: the lowest cost per second: on Standard, Gen-4.5 works out to $0.288/s if you use every credit, resolution and audio not stated. {runway_src}. Related: <a href="{e(runway_guide)}">Runway pricing per second</a>.</li>
<li><b>Kling AI.</b> Best for: Kling itself on both stores; the listing states clips up to 15 seconds in native 1080p or 4K. Not for: the top of the text-to-video board: Kling 3.0 1080p (Pro) is the fixed Elo 1000 reference point at rank 23, and Wan 3.0 leads at Elo 1174 ±13 (rank range 1–2). {aa_t2v}. Related: <a href="{e(kling_guide)}">Kling AI pricing and credits</a> · <a href="{e(kling_model)}">Kling 3.0 model page</a>.</li>
<li><b>Grok.</b> Best for: the most-rated app in this guide, at 4.9 from 1,615,809 US App Store ratings, with text-to-video up to 15 seconds at 720p on the product page. Not for: a free video allowance you can count, since none is published, or the top of the quality board: Grok Imagine Video 1.5 is Elo 1051 ±13 (rank range 16–18). {xai_grok}. Related: <a href="{e(grok_guide)}">how much a Grok Imagine video costs</a>.</li>
<li><b>Pika.</b> Best for: iPhone users who want Pika’s own model; Pika H3 Flex is Elo 1124 ±14 (rank range 11–15). Not for: Android, where we found no listing from Pika’s publisher, or buying credit packs in the app: $34.99 for 1,500 credits is about $0.0233 per credit, against about $0.0167 per credit for web packs. {pika_src}.</li>
<li><b>Krea.</b> Best for: a free plan with no credit card and no watermark, as Krea’s web pages state, on iPhone. Not for: Android, where we found no listing from Krea, or commercial work on the free plan, which Krea says is for personal use. {krea_video}.</li>
<li><b>Luma Dream Machine.</b> Not for: current plan names in the app. The iPhone app was last updated Apr 17, 2026 and lists Lite, Plus, and Unlimited, while the web page on Nov 17, 2026 lists Plus, Pro, and Ultra. No best-for line is given. {luma_src}.</li>
</ul>
<p>No line given. Dreamina, Hailuo, Google Gemini, and Meta AI: the listings and pages we read do not support a best-for or not-for line. Dreamina’s 3.0 App Store rating comes from 53 ratings, a small sample.</p>

<h2>How do you tell an official app from a look-alike?</h2>
<p>{e(lookalikes)}</p>

<h2>What is confirmed, and what is not?</h2>
<p>{e(a_unknown)}</p>
<p><b>Confirmed {e(CHECKED_WHEN)} on store listings:</b> each seller or developer name, rating, minimum iOS version, and App Store in-app item list in the tables above; the in-app purchases mark on each Google Play listing; Flow’s lack of listed in-app purchases. iPhone ratings and seller names were also checked against Apple’s public lookup later on Nov 17, 2026. <b>Confirmed {e(CHECKED_WHEN)} on official pages:</b> Runway, Pika, Luma, and Krea web prices; Flow’s daily credits and credit costs; Hailuo’s plan terms. <b>Confirmed {e(CHECKED_WHEN)} on Artificial Analysis:</b> the Elo figures and rank ranges quoted above. <b>Carried from earlier checks, with their dates:</b> Kling web prices (Nov 14, 2026 PT), Dreamina Basic (Nov 15, 2026), the Grok plan grid (Nov 12, 2026 PT), and the catalog rows (2026-11-16).</p>
<p class="small">Affiliate links never change this price order.</p>
{next_steps}
{g["how_block"]()}
"""

    hay = (body + description(g) + PHRASE + H1).lower()
    if "sora" in hay:
        raise SystemExit(f"{PATH} source would name Sora")

    title = g["page_title"](PHRASE)
    desc = description(g)
    g["guide_page"](PATH, title, desc, body, faqs)
    return PATH
