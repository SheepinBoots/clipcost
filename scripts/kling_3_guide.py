"""Guide: Kling 3.0 cost per second, and where it is cheapest.

Imported by scripts/build_site.py. Every catalog figure is rendered from
data/prices.json. Official pages for fal, the Kling API document, Runway's API
pricing, the Higgsfield API model pages, and Higgsfield's plan page were
re-read on 2026-11-17 (CHECKED_WHEN). Figures that are not catalog rows are
labelled that way. This page never names the banned model.
"""

PATH = "/guides/cheapest-kling-3-0/"
LABEL = "Kling 3.0 cost"
PHRASE = "Kling 3.0 cost per second: where it’s cheapest"
QUESTION = "Where is Kling 3.0 cheapest right now?"
CHECKED = "2026-11-17"
CHECKED_WHEN = "Nov 17, 2026, 5:04–5:15 PM America/Caracas (1:04–1:15 PM PT)"
MODEL = "kling-3-0"
MODEL_PATH = "/models/kling-3-0/"

KLING_API = "https://kling.ai/document-api/pricing/base/video.md"
KLING_PLANS = "https://kling.ai/app/membership/membership-plan"
FAL_PRO_T2V = "https://fal.ai/models/fal-ai/kling-video/v3/pro/text-to-video"
FAL_STD_I2V = "https://fal.ai/models/fal-ai/kling-video/v3/standard/image-to-video"
HF_PLANS = "https://higgsfield.ai/pricing"
HF_API_PRICING = "https://open.higgsfield.ai/pricing"
HF_API_STD_T2V = "https://open.higgsfield.ai/models/kling-video/v3.0/std/text-to-video"
HF_API_STD_I2V = "https://open.higgsfield.ai/models/kling-video/v3.0/std/image-to-video"
HF_API_PRO_T2V = "https://open.higgsfield.ai/models/kling-video/v3.0/pro/text-to-video"
HF_API_PRO_I2V = "https://open.higgsfield.ai/models/kling-video/v3.0/pro/image-to-video"
RUNWAY_API = "https://docs.dev.runwayml.com/guides/pricing/"

# Read on the Higgsfield API model pages at CHECKED_WHEN. Not catalog rows.
HF_API_STD_720 = 0.0714
HF_API_PRO_1080 = 0.0962

PLATFORM_ORDER_NOTE = "Affiliate links never change this price order."


def _src(g, url, text="source"):
    e = g["e"]
    href, rel = g["outbound"](url)
    return f'<a href="{e(href)}" rel="{rel}" target="_blank">{e(text)}</a>'


def checked_pt(date):
    if not date:
        return "date not stated"
    parts = str(date).split("-")
    months = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    try:
        return f"{months[int(parts[1]) - 1]} {int(parts[2])}, {parts[0]} PT"
    except (ValueError, IndexError):
        return f"{date} PT"


def kling_rows(g):
    rows = [
        r for r in g["rows"]
        if r.get("model") == MODEL
        and r.get("usd_per_second") is not None
        and r.get("status") != "discontinued"
    ]
    return sorted(rows, key=lambda r: (float(r["usd_per_second"]), r["id"]))


def _row(g, rid):
    for r in g["rows"]:
        if r["id"] == rid:
            return r
    raise SystemExit(f"{PATH} missing catalog row {rid}")


def _audio_word(g, r):
    a = g["shown_audio"](r)
    return {"with": "with audio", "without": "without audio"}.get(a, "not stated")


def _route(r):
    plan = r.get("plan_name") or ""
    kind = "credit plan" if r.get("kind") == "plan" else "pay as you go API"
    if plan:
        return f"{r['platform']} · {plan} ({kind})"
    return f"{r['platform']} ({kind})"


def _assumption(r):
    math = (r.get("math") or "").strip()
    if r.get("kind") == "plan":
        lead = "Estimated from credit plan. " if r.get("status") == "estimate" else "From credit plan. "
        text = lead + (math + ". " if math else "") + "Assumes every credit you pay for is used."
        if r.get("platform") == "Higgsfield":
            text += " Higgsfield’s own label is ~7 credits per 5 s at 720p, ~8 at 1080p, ~30 at 4K."
        return text
    if math:
        return f"{math}. Billed per second of output, so no credits go unused."
    return "Billed per second of output, so no credits go unused."


def cheapest_by_platform(rows):
    best = {}
    for r in rows:
        p = r["platform"]
        if p not in best:
            best[p] = r
    return sorted(best.values(), key=lambda r: (float(r["usd_per_second"]), r["id"]))


def blurb(g):
    rows = kling_rows(g)
    if not rows:
        return "Every Kling 3.0 price we track, cheapest first."
    c = rows[0]
    return (
        f"Every Kling 3.0 route we track, cheapest first: from "
        f"{g['rate_money'](c['usd_per_second'])}/s on {c['platform']}, "
        f"against {g['rate_money'](0.084)}/s on the official Kling API at 720p."
    )


def description(g):
    text = (
        "Kling 3.0 cost per second on Kling, Higgsfield, fal, Runway, Krea and "
        f"Magnific, cheapest first, with audio and resolution. Last checked {g['LAST']}."
    )
    if len(text) > 160:
        raise SystemExit(f"{PATH} meta description is over 160 characters: {len(text)}")
    return text


def render(g):
    e, root, LAST = g["e"], g["root"], g["LAST"]
    rate_money, cost_money = g["rate_money"], g["cost_money"]
    shown_resolution, rate_label = g["shown_resolution"], g["rate_label"]
    rows = kling_rows(g)
    if not rows:
        raise SystemExit(f"{PATH} needs Kling 3.0 rows")
    dates = [CHECKED, LAST] + [r["checked"] for r in rows if r.get("checked")]
    g["SITEMAP_LASTMOD"][PATH] = max(dates)

    def src(url, text="source"):
        return _src(g, url, text)

    def trow(*cells):
        return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"

    def row_source(r):
        href, rel = g["outbound"](r["source_url"])
        return (
            f'<a href="{e(href)}" rel="{rel}" target="_blank">source</a>, '
            f"catalog row {e(r['id'])}, checked {e(checked_pt(r.get('checked')))}"
        )

    def cat_row(r, extra_note=""):
        res = shown_resolution(r)
        if r["id"] == "r007":
            res = "lowest mode (720p on the model page)"
        variant = r.get("variant") or ""
        return trow(
            e(_route(r)),
            e(variant),
            e(res),
            e(_audio_word(g, r)),
            f'<span class="amt">{e(rate_money(r["usd_per_second"]))}/s</span> <span class="small">{e(rate_label(r))}</span>',
            e(_assumption(r)) + (f" {extra_note}" if extra_note else ""),
            row_source(r),
        )

    head = """<thead><tr>
<th>Where and tier</th>
<th>Variant</th>
<th>Resolution</th>
<th>Audio</th>
<th>Rate</th>
<th>Usage assumption</th>
<th>Source and date checked</th>
</tr></thead>"""

    # --- Table 1: cheapest row per platform, plus two read-today API modes ---
    per_platform = cheapest_by_platform(rows)
    bits = []
    for r in per_platform:
        note = ""
        if r["id"] == "r007":
            note = (
                f"The Kling 3.0 Standard text-to-video model page says “720p: $0.0714” per video second, "
                f"read {e(CHECKED_WHEN)} ({src(HF_API_STD_T2V, 'Higgsfield API model page')})."
            )
        bits.append((float(r["usd_per_second"]), cat_row(r, note)))
    bits.append((
        HF_API_PRO_1080,
        trow(
            "Higgsfield API · Kling 3.0 Pro (pay as you go API)",
            "Kling 3.0 Pro, text or image to video",
            "1080p",
            "not stated",
            f'<span class="amt">{e(rate_money(HF_API_PRO_1080))}/s</span> <span class="small">published rate</span>',
            "Total price = selected rate × output duration in seconds, per the model page. Not a catalog row.",
            f"{src(HF_API_PRO_T2V, 'text-to-video page')} · {src(HF_API_PRO_I2V, 'image-to-video page')}, read {e(CHECKED_WHEN)}. Not a catalog row.",
        ),
    ))
    bits.sort(key=lambda b: b[0])
    platform_table = (
        f'<div class="tblwrap" id="prices"><table style="min-width:1200px;width:1200px">{head}<tbody>'
        + "".join(h for _v, h in bits)
        + "</tbody></table></div>"
    )

    # --- Table 2: every catalog row ---
    all_table = (
        f'<div class="tblwrap" id="all-kling-rows"><table style="min-width:1200px;width:1200px">{head}<tbody>'
        + "".join(cat_row(r) for r in rows)
        + "</tbody></table></div>"
    )

    cheapest = rows[0]
    api_rows = [r for r in rows if r.get("kind") == "api"]
    cheapest_api = api_rows[0]
    with_audio = [r for r in rows if g["shown_audio"](r) == "with"]
    cheapest_audio = with_audio[0]
    verified_plan = [r for r in rows if r.get("kind") == "plan" and r.get("status") == "verified"]
    mag = verified_plan[0] if verified_plan else None
    r059 = _row(g, "r059")
    r062 = _row(g, "r062")
    r064 = _row(g, "r064")
    r015 = _row(g, "r015")
    r016 = _row(g, "r016")
    r034 = _row(g, "r034")
    r112 = _row(g, "r112")
    r111 = _row(g, "r111")
    if cheapest["id"] != "r111":
        raise SystemExit(f"{PATH} copy assumes r111 is the cheapest Kling 3.0 row; it is {cheapest['id']}")
    if cheapest_api["id"] != "r007":
        raise SystemExit(f"{PATH} copy assumes r007 is the cheapest Kling 3.0 API row; it is {cheapest_api['id']}")
    if cheapest_audio["id"] != "r064":
        raise SystemExit(f"{PATH} copy assumes r064 is the cheapest with-audio row; it is {cheapest_audio['id']}")
    if mag is None or mag["id"] != "r160":
        raise SystemExit(f"{PATH} copy assumes r160 is the cheapest non-estimate plan row")

    ten = lambda v: cost_money(float(v) * 10)

    model_href = root(MODEL_PATH)
    kling_guide = root("/guides/kling-ai-pricing/")
    hf_pricing = root("/guides/higgsfield-pricing/")
    hf_worth = root("/guides/is-higgsfield-worth-it/")
    hf_bf = root("/guides/higgsfield-black-friday/")
    runway_guide = root("/guides/runway-pricing/")
    best_href = root("/guides/best-ai-video-generator/")
    cheap_href = root("/guides/cheapest-ai-video-generator/")
    i2v_free = root("/guides/free-image-to-video-ai/")
    apps_href = root("/guides/ai-video-generator-apps/")
    calc_href = root("/calculator/?model=kling-3-0&seconds=10")

    kling_api_src = src(KLING_API, "Kling’s official API pricing document")
    fal_pro = src(FAL_PRO_T2V, "fal’s Kling 3.0 Pro page")
    fal_std = src(FAL_STD_I2V, "fal’s Kling 3.0 Standard image-to-video page")
    hf_plans = src(HF_PLANS, "Higgsfield’s pricing page")
    hf_api_list = src(HF_API_PRICING, "Higgsfield API pricing list")
    hf_std_i2v = src(HF_API_STD_I2V, "Higgsfield API Standard image-to-video page")
    hf_std_t2v = src(HF_API_STD_T2V, "Higgsfield API Standard text-to-video page")
    runway_src = src(RUNWAY_API, "Runway API pricing")
    kling_plans = src(KLING_PLANS, "Kling membership plans")

    a_q = (
        f"The cheapest Kling 3.0 rate we track is {rate_money(r111['usd_per_second'])} per second "
        f"on Higgsfield Ultra (annual) at 720p, audio not stated. That is an estimate from the "
        f"credit plan: $50 a month for 3,000 credits, about 7.5 credits per 5-second clip, and it "
        f"assumes you use every credit you pay for. With no credits to use up, the cheapest "
        f"pay-as-you-go rate is {rate_money(HF_API_STD_720)} per second for Kling 3.0 Standard at "
        f"720p on the Higgsfield API, audio not stated. The official Kling API charges "
        f"{rate_money(r059['usd_per_second'])} per second at 720p without native audio and "
        f"{rate_money(r062['usd_per_second'])} with it. The cheapest rate whose vendor page says the "
        f"clip includes audio is {rate_money(r064['usd_per_second'])} per second for Kling 3.0 Turbo with native "
        f"audio at 720p on the official API. Higgsfield links on this page are affiliate links, and "
        f"they never change this price order."
    )
    a_rate = (
        f"It depends on the route. Credit plans run from {rate_money(r111['usd_per_second'])} per "
        f"second (Higgsfield Ultra annual, 720p, estimate) to more than $0.25 per second at 4K, and "
        f"each assumes every credit is used. Pay-as-you-go APIs run from {rate_money(HF_API_STD_720)} "
        f"per second (Higgsfield API, Standard, 720p) through {rate_money(r059['usd_per_second'])} "
        f"(official Kling API, 720p, no audio), {rate_money(r034['usd_per_second'])} (Runway API, "
        f"Standard, no audio) and {rate_money(r015['usd_per_second'])} (fal Pro, audio off), up to "
        f"$0.42 or more per second at 4K. A 10-second 720p clip without audio is {ten(r059['usd_per_second'])} "
        f"on the official API and {ten(HF_API_STD_720)} on the Higgsfield API."
    )
    a_audio = (
        f"At 720p and 1080p, native audio raises the per-second price on every route that prices it "
        "separately. At 4K, the official API and fal charge $0.42 a second either way. On the "
        f"official Kling API, 720p is {rate_money(r059['usd_per_second'])} per second without audio "
        f"and {rate_money(r062['usd_per_second'])} with it, and Kling 3.0 Turbo with audio is "
        f"{rate_money(r064['usd_per_second'])} at 720p. On fal Pro it is "
        f"{rate_money(r015['usd_per_second'])} with audio off and {rate_money(r016['usd_per_second'])} "
        f"with audio on, or $0.196 with voice control. On the Runway API, Standard is $0.09 without audio "
        f"and $0.13 with it. Higgsfield’s plan page and the Higgsfield API model pages do not say "
        f"whether their Kling 3.0 rates include audio, so those rows say not stated."
    )
    a_i2v = (
        "On the pages that state input type, yes. fal’s Kling 3.0 Pro image-to-video mode lists the "
        "same $0.112 per second with audio off and $0.168 with audio on as its text-to-video mode, and "
        "fal’s Standard image-to-video page lists $0.084 and $0.126. The Higgsfield API model pages "
        f"list {rate_money(HF_API_STD_720)} per second at 720p for Standard image-to-video and for "
        f"Standard text-to-video, and {rate_money(HF_API_PRO_1080)} at 1080p for Pro in both modes. "
        "The official Kling API table bills Kling 3.0 per second of output and does not list a "
        "separate image-to-video price. Higgsfield’s plan page and Runway’s API page give one Kling "
        "3.0 price without naming the input type."
    )
    a_direct = (
        f"Not on price. The official Kling API ({rate_money(r059['usd_per_second'])} per second at "
        f"720p without audio) is undercut by the Higgsfield API at {rate_money(HF_API_STD_720)}, and "
        f"by credit plans on Higgsfield, Magnific and Krea if you use every credit. It is cheaper than "
        f"fal Pro ({rate_money(r015['usd_per_second'])}) and Runway’s Pro variants. The official Kling "
        "app sells monthly credits, but Kling does not publish how many credits a Kling 3.0 clip uses, "
        "so this page cannot turn an app plan into a cost per second. Higgsfield’s annual plan rows "
        "use its current sale prices. Higgsfield’s pricing page gives the sale an end of "
        "2026-11-18T00:00:00Z (Nov 17, 2026, 4:00 PM PT), unless it is extended."
    )
    a_unknown = (
        "Unknown, and not guessed: how many credits a Kling 3.0 clip uses in the official Kling app, "
        "so no app-plan cost per second is shown; whether Higgsfield’s plan rates and Higgsfield API "
        "rates include native audio; which settings give the top of the Higgsfield API price range "
        "($0.1071 for Standard image-to-video, $0.1443 for Pro); Krea’s Kling 3.0 resolution; "
        "Higgsfield’s annual price after its Black Friday sale ends; and a Replicate Kling 3.0 rate, "
        "since none is in our catalog."
    )

    faqs = [
        (QUESTION, a_q),
        ("What does Kling 3.0 cost per second?", a_rate),
        ("What does Kling AI video cost with audio?", a_audio),
        ("Does Kling AI image to video cost the same as text to video?", a_i2v),
        ("Is Kling direct cheaper than Higgsfield or fal?", a_direct),
        ("What is confirmed, and what is not?", a_unknown),
    ]
    for q, a in faqs:
        raw = (q + " " + a).lower()
        for bad in ("subscribe", "newsletter", "buttondown"):
            if bad in raw:
                raise SystemExit(f"{PATH} FAQ text contains {bad}")

    lead = (
        f"The cheapest Kling 3.0 rate we track is {e(rate_money(r111['usd_per_second']))}/s on "
        f"Higgsfield Ultra (annual) at 720p, audio not stated, an estimate that assumes you use every "
        f"credit. The cheapest pay-as-you-go rate is {e(rate_money(HF_API_STD_720))}/s for Kling 3.0 "
        f"Standard at 720p on the Higgsfield API. The official Kling API is "
        f"{e(rate_money(r059['usd_per_second']))}/s at 720p without native audio and "
        f"{e(rate_money(r062['usd_per_second']))}/s with it, from {kling_api_src}. Every row below "
        f"states its tier, resolution, audio, usage assumption, source, and the date it was checked. "
        f"For Kling’s own plans and credit packs, see "
        f"<a href=\"{e(kling_guide)}\">Kling AI pricing and credits</a>."
    )

    takeaways = f"""<div class="card" id="takeaways">
<h2>Key takeaways</h2>
<ul>
<li><b>Cheapest if you use every credit.</b> {e(rate_money(r111['usd_per_second']))}/s on Higgsfield Ultra (annual), 720p, audio not stated. Estimated from a $50-a-month plan at Higgsfield’s current sale price.</li>
<li><b>Cheapest pay as you go.</b> {e(rate_money(HF_API_STD_720))}/s on the Higgsfield API, Kling 3.0 Standard, 720p, audio not stated. At 1080p, Higgsfield API Pro is {e(rate_money(HF_API_PRO_1080))}/s.</li>
<li><b>Kling direct.</b> The official API is {e(rate_money(r059['usd_per_second']))}/s at 720p without audio and {e(rate_money(r062['usd_per_second']))}/s with audio. App credits per clip are not published.</li>
<li><b>Cheapest with audio included.</b> {e(rate_money(r064['usd_per_second']))}/s for Kling 3.0 Turbo with native audio at 720p on the official API.</li>
<li><b>Image to video.</b> fal and the Higgsfield API list the same per-second rate for image-to-video as for text-to-video.</li>
</ul>
</div>"""

    next_steps = f"""<div class="card" id="next-steps">
<h2>What to do next</h2>
<ul>
<li><b>Check the vendor page.</b> Prices and sale prices change without notice. Confirm today’s figure on {kling_api_src}, {hf_plans}, or {fal_pro} before you buy.</li>
<li><b>Try the calculator.</b> Put your clip length into the <a href="{e(calc_href)}">credit calculator for a 10-second Kling 3.0 clip</a> to see what your plan really costs when you do not use every credit.</li>
<li><b>Open the model page.</b> Every current Kling 3.0 rate, with its source and date, is on the <a href="{e(model_href)}">Kling 3.0 model page</a>.</li>
</ul>
</div>"""

    body = f"""<p class="small"><a href="{root("/guides/")}">Guides</a> › Kling 3.0 cost</p>
<h1>{e(PHRASE)}</h1>
<p class="lead">{lead}</p>
<p class="small">Last checked {e(LAST)}. Official pages were re-read {e(CHECKED_WHEN)}. Catalog rows use the date on each row. {PLATFORM_ORDER_NOTE} Every dollar-per-second figure below states its usage assumption, tier, resolution, and audio.</p>
{takeaways}

<h2>{e(QUESTION)}</h2>
<p>{e(a_q)}</p>

<h2>Kling 3.0 cost per second, cheapest route on each platform</h2>
<p>One row per platform: the lowest Kling 3.0 rate we track there, cheapest first. One Higgsfield API mode read today (Pro at 1080p) is included and labelled as not a catalog row. A credit-plan rate is plan price ÷ credits × credits per clip ÷ seconds, and it assumes every credit you pay for is used. Unused credits make the real cost higher.</p>
{platform_table}
<p class="small">{PLATFORM_ORDER_NOTE} Higgsfield links can be affiliate links. Higgsfield’s annual plan rows use the sale prices on {hf_plans} ($33 a month for Plus, $50 for Ultra 3K, billed yearly), read {e(CHECKED_WHEN)}. The sale record on that page ends 2026-11-18T00:00:00Z (Nov 17, 2026, 4:00 PM PT; 8:00 PM America/Caracas) unless Higgsfield extends it; see <a href="{e(hf_bf)}">Higgsfield Black Friday</a>.</p>

<h2>What does Kling 3.0 cost per second?</h2>
<p>{e(a_rate)}</p>

<h2>What does Kling AI video cost with audio?</h2>
<p>{e(a_audio)} Sources: {kling_api_src} · {fal_pro} · {runway_src}, read {e(CHECKED_WHEN)}.</p>

<h2>Does Kling AI image to video cost the same as text to video?</h2>
<p>{e(a_i2v)}</p>
<p>Sources read {e(CHECKED_WHEN)}: {fal_pro} (its Image to Video (pro) mode) · {fal_std} · {hf_std_i2v} · {hf_std_t2v} · {hf_api_list}, which shows Standard image-to-video as $0.0714–$0.1071 per second and Pro as $0.0962–$0.1443 per second without saying which settings give each end of the range. For free ways to animate a photo, see <a href="{e(i2v_free)}">free image to video AI</a>.</p>

<h2>Is Kling direct cheaper than Higgsfield or fal?</h2>
<p>{e(a_direct)}</p>
<p>Kling AI video comes from Kuaishou. Kling sells Kling 3.0 two ways: monthly credits in the Kling app ({kling_plans}) and per-second resource packages on the API ({kling_api_src}), which lists 720p, 1080p, and 4K with or without native audio, plus Kling 3.0 Turbo with native audio. Higgsfield, fal, Runway, Krea, and Magnific resell the same model. Kling’s app plans, first-month prices, and credit packs are in <a href="{e(kling_guide)}">Kling AI pricing and credits</a>, and Higgsfield’s credit math is in <a href="{e(hf_pricing)}">Higgsfield pricing explained</a> and <a href="{e(hf_worth)}">is Higgsfield worth it?</a>. Official iPhone and Android apps are compared in <a href="{e(apps_href)}">AI video generator apps</a>.</p>
<p>If Higgsfield’s annual sale price ends and Ultra bills at its $129 monthly list price, the same 720p Kling 3.0 math is {e(rate_money(r112['usd_per_second']))}/s (catalog row r112, Ultra monthly), still below the official API’s {e(rate_money(r059['usd_per_second']))}/s if you use every credit.</p>

<h2>Every Kling 3.0 price we track</h2>
<p>All {len(rows)} current Kling 3.0 rows in our catalog, cheapest first. Resolution says “not listed” where the vendor gives a tier name instead of a resolution.</p>
{all_table}
<p class="small">{PLATFORM_ORDER_NOTE} Related: <a href="{e(cheap_href)}">cheapest rate we track for each model</a> · <a href="{e(best_href)}">best AI video generator by value</a> · <a href="{e(runway_guide)}">Runway pricing per second</a> · <a href="{e(root("/guides/higgsfield-vs-kling/"))}">Higgsfield vs Kling</a> · <a href="{e(root("/guides/fal-ai-pricing/"))}">fal pricing vs Replicate and others</a>.</p>

<h2>What is confirmed, and what is not?</h2>
<p>{e(a_unknown)}</p>
<p><b>Confirmed {e(CHECKED_WHEN)} on official pages:</b> the official Kling API rates for Kling 3.0 and Kling 3.0 Turbo; fal’s Pro and Standard rates, including the image-to-video modes; Runway’s Kling 3.0 credits per second; the Higgsfield API Standard 720p and Pro 1080p rates; and Higgsfield’s sale prices and its approximate Kling 3.0 credits per 5-second clip. <b>From the catalog:</b> every row in the tables above, each with its own checked date.</p>
{next_steps}
{g["how_block"]()}
"""

    if "sora" in body.lower() or "sora" in description(g).lower() or "sora" in PHRASE.lower():
        raise SystemExit(f"{PATH} source would name the banned model")
    title = g["page_title"](PHRASE)
    desc = description(g)
    g["guide_page"](PATH, title, desc, body, faqs)
    return PATH
