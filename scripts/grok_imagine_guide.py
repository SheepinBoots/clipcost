"""Guide: How much does a Grok Imagine video cost?

Imported by scripts/build_site.py. Official xAI API rates and catalog vendor
rows come from data/prices.json. Plan prices and usage rules are cited from
the official pages checked for this guide, not invented.
"""
PATH = "/guides/grok-imagine-video-cost/"
LABEL = "Grok Imagine video cost"
PHRASE = "How much does a Grok Imagine video cost?"
QUESTION = "How much does a Grok Imagine video cost?"
MODEL = "grok-imagine"

XAI_PRICING = "https://docs.x.ai/developers/pricing"
XAI_VIDEO = "https://docs.x.ai/developers/model-capabilities/video/overview"
XAI_15 = "https://docs.x.ai/developers/models/grok-imagine-video-1.5"
XAI_LITE = "https://docs.x.ai/developers/models/grok-imagine-video-1.5-lite"
XAI_V1 = "https://docs.x.ai/developers/models/grok-imagine-video"
XAI_API = "https://x.ai/api"
XAI_PLANS = "https://x.ai/pricing"
GROK_FAQ = "https://docs.x.ai/grok/faq"
XSUB_PRICING = "https://docs.x.ai/x-subscription/pricing"
XSUB_LIMITS = "https://docs.x.ai/x-subscription/usage-limits"
XSUB_EXTRA = "https://docs.x.ai/x-subscription/extra-usage"
FAL = "https://fal.ai/models/xai/grok-imagine-video/v1.5/text-to-video"
RUNWAY = "https://docs.dev.runwayml.com/guides/pricing/"
REP = "https://replicate.com/xai/grok-imagine-video-1.5"
ATLAS = "https://www.atlascloud.ai/pricing"
KREA = "https://www.krea.ai/pricing"
MAG = "https://www.magnific.com/pricing"
HF_API = "https://open.higgsfield.ai/pricing"
HF_PLANS = "https://higgsfield.ai/pricing"

# Official list prices from docs.x.ai/developers/pricing, checked 2026-11-12 PT.
# Also stored as catalog rows once those rows exist.
OFFICIAL = {
    ("grok-imagine-video-1.5", "480p"): 0.08,
    ("grok-imagine-video-1.5", "720p"): 0.14,
    ("grok-imagine-video-1.5", "1080p"): 0.25,
    ("grok-imagine-video-1.5-lite", "480p"): 0.02,
    ("grok-imagine-video-1.5-lite", "720p"): 0.03,
    ("grok-imagine-video-1.5-lite", "1080p"): 0.14,
}

# Clip lengths shown in the worked examples. Official duration range is 1-15s.
EXAMPLE_SECONDS = (5, 15)


def _src(g, url, text="source"):
    e = g["e"]
    href, rel = g["outbound"](url)
    return f'<a href="{e(href)}" rel="{rel}" target="_blank">{e(text)}</a>'


def checked_pt(date):
    if not date:
        return "date not stated"
    parts = str(date).split("-")
    if len(parts) != 3:
        return f"{date} PT"
    year, month, day = parts
    months = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    try:
        return f"{months[int(month) - 1]} {int(day)}, {year} PT"
    except (ValueError, IndexError):
        return f"{date} PT"


def _model_rows(g):
    return [r for r in g["rows"] if r.get("model") == MODEL]


def official_row(g, variant, res):
    rows = [
        r for r in _model_rows(g)
        if r.get("platform") == "xAI API"
        and r.get("resolution") == res
        and (r.get("variant") or "") == variant
    ]
    return sorted(rows, key=lambda r: (r["usd_per_second"], 0 if r.get("platform") == "xAI API" else 1, r["id"]))[0] if rows else None


def cheapest_at(g, res, variant_substr=None):
    rows = [r for r in _model_rows(g) if r.get("resolution") == res]
    if variant_substr:
        rows = [r for r in rows if variant_substr in ((r.get("variant") or "") + " " + (r.get("platform") or ""))]
    if not rows:
        return None
    return sorted(rows, key=lambda r: (r["usd_per_second"], 0 if r.get("platform") == "xAI API" else 1, r["id"]))[0]


def cheapest_overall(g):
    rows = _model_rows(g)
    if not rows:
        return None
    return sorted(rows, key=lambda r: (r["usd_per_second"], 0 if r.get("platform") == "xAI API" else 1, r["id"]))[0]


def official_rate(variant, res, g=None):
    if g is not None:
        row = official_row(g, variant, res)
        if row:
            return row["usd_per_second"]
    return OFFICIAL.get((variant, res))


def blurb(g):
    best = cheapest_overall(g)
    if not best:
        return "Official Grok Imagine API rates, paid-plan limits, and catalog vendor prices compared."
    rate = g["rate_money"](best["usd_per_second"])
    return (
        f"The lowest Grok Imagine rate in the catalog is {rate}/s on {best['platform']} "
        f"({g['shown_resolution'](best)}, {best['variant']}). "
        "Paid-plan video limits are a weekly usage pool, not a published credits-per-clip figure."
    )


def description(g, best):
    last = g["LAST"]
    rate = g["rate_money"](best["usd_per_second"]) if best else None
    options = []
    if rate:
        options.append(
            f"Grok Imagine Video 1.5 costs from {rate}/s on {best['platform']} "
            f"({g['shown_resolution'](best)}, {best['variant']}). "
            f"Plan limits, credits, and vendor rates compared. Last checked {last}."
        )
        options.append(
            f"Grok Imagine Video 1.5 costs from {rate}/s on {best['platform']} "
            f"({g['shown_resolution'](best)}). Plan limits and vendor rates compared. Last checked {last}."
        )
    options.append(
        f"Grok Imagine video cost: official API rates, paid-plan limits, and vendor APIs. Last checked {last}."
    )
    for text in options:
        if len(text) <= 160:
            return text
    raise SystemExit(f"{PATH} meta description is over 160 characters")


def render(g):
    e, root, LAST = g["e"], g["root"], g["LAST"]
    rate_money = g["rate_money"]
    plat_link, outbound = g["plat_link"], g["outbound"]
    shown_resolution = g["shown_resolution"]
    assumption_html = g["assumption_html"]
    tag, deal_badges = g["tag"], g["deal_badges"]
    name = g["models"][MODEL]["name"]

    rows = _model_rows(g)
    if not rows:
        raise SystemExit(f"{PATH} needs at least one {MODEL} price row")
    best = cheapest_overall(g)
    dates = [r.get("checked") or "" for r in rows] + ["2026-11-12"]
    g["SITEMAP_LASTMOD"][PATH] = max(d for d in dates if d)

    def src(url, text="source"):
        return _src(g, url, text)

    def source_toggle(r):
        parts = []
        if (r.get("math") or "").strip():
            parts.append(e(r["math"].strip()))
        if (r.get("note") or "").strip():
            parts.append(e(r["note"].strip()))
        href, rel = outbound(r["source_url"])
        link = f'<a href="{e(href)}" rel="{rel}" target="_blank">pricing page</a>'
        checked = e(r.get("checked") or "")
        body = " ".join(parts + [link, "· " + checked]).strip()
        return f'<details class="src"><summary>source</summary><div class="math">{body}</div></details>'

    def status_cell(r):
        promo = ""
        if r.get("status") == "promo" and r.get("promo_until"):
            promo = f' <span class="small">until {e(r["promo_until"])}</span>'
        return f'<span class="badges">{tag(r)}{promo}{deal_badges(r)}</span>'

    def kind_label(r):
        if r.get("kind") == "plan":
            return "credit plan"
        if r.get("status") == "estimate" or g["rate_label"](r).startswith("estimated"):
            return "API estimate"
        return "pay-as-you-go API"

    def row_html(r):
        return (
            "<tr>"
            f"<td>{plat_link(r['platform'], r['source_url'])}</td>"
            f"<td>{e(r['variant'])}</td>"
            f"<td>{e(kind_label(r))}</td>"
            f"<td>{e(shown_resolution(r))}</td>"
            f'<td class="num">{rate_money(r["usd_per_second"])}{assumption_html(r)}</td>'
            f"<td>{status_cell(r)}</td>"
            f"<td>{source_toggle(r)}</td>"
            "</tr>"
        )

    head = (
        "<thead><tr><th>Where</th><th>Variant</th><th>Type</th>"
        "<th>Res</th><th>$/s</th><th>Status</th><th>Source</th></tr></thead>"
    )

    def table_for(rs, empty="No catalog row in this group."):
        if not rs:
            return f"<p>{e(empty)}</p>"
        body = "".join(row_html(r) for r in sorted(rs, key=lambda r: (r["usd_per_second"], r["id"])))
        return f'<div class="tblwrap fit"><table>{head}<tbody>{body}</tbody></table></div>'

    def clip_cost(usd, seconds):
        return usd * seconds

    # Official worked examples (1.5 and lite) at 5s and 15s.
    example_rows = []
    for variant, label in (
        ("grok-imagine-video-1.5-lite", "1.5 lite"),
        ("grok-imagine-video-1.5", "1.5"),
    ):
        for res in ("480p", "720p", "1080p"):
            usd = official_rate(variant, res, g)
            if usd is None:
                continue
            cells = "".join(
                f'<td class="num">{rate_money(clip_cost(usd, sec))}</td>'
                for sec in EXAMPLE_SECONDS
            )
            example_rows.append(
                f"<tr><td>{e(label)}</td><td>{e(res)}</td>"
                f'<td class="num">{rate_money(usd)}/s</td>{cells}</tr>'
            )
    example_table = (
        '<div class="tblwrap fit"><table><thead><tr>'
        "<th>Official model</th><th>Res</th><th>$/s</th>"
        + "".join(f"<th>{s}s clip</th>" for s in EXAMPLE_SECONDS)
        + "</tr></thead><tbody>"
        + "".join(example_rows)
        + "</tbody></table></div>"
    )

    lite480 = official_rate("grok-imagine-video-1.5-lite", "480p", g)
    best_rate = rate_money(best["usd_per_second"])
    lead = (
        f"On the official API, {name} starts at {rate_money(lite480)}/s for grok-imagine-video-1.5-lite at 480p "
        f"({src(XAI_PRICING, 'xAI API pricing')}, checked {checked_pt('2026-11-12')}). "
        "A clip is billed per second of output, for 1 to 15 seconds, so a 5-second lite 480p video is "
        f"{rate_money(clip_cost(lite480, 5))} and a 15-second clip is {rate_money(clip_cost(lite480, 15))}, before any input-image charge. "
        "Paid Grok plans that include video generation draw from a shared weekly usage pool; those pages do not publish a credits-per-video figure, so this guide does not invent one. "
        "Affiliate links never change this price order."
    )

    # Vendor groups
    xai_rows = [r for r in rows if r.get("platform") == "xAI API"]
    fal_rows = [r for r in rows if r.get("platform") == "fal"]
    runway_rows = [r for r in rows if r.get("platform") == "Runway API"]
    other_rows = [r for r in rows if r.get("platform") not in ("xAI API", "fal", "Runway API")]

    q1 = QUESTION
    a1 = (
        f"The cheapest published rate in the catalog is {best_rate}/s on {best['platform']} "
        f"({shown_resolution(best)}, {best['variant']}), checked {checked_pt(best.get('checked'))}. "
        "That is a pay-as-you-go API rate: one video costs that figure times the output length, plus any stated input charge. "
        "On paid Grok plans that include video generation, usage comes from a weekly pool shown as a percentage; "
        "the official pages do not say how many credits one video uses, so no plan dollars-per-second figure is shown."
    )
    q2 = "How much is one Grok Imagine video on the official API?"
    a2 = (
        "Official output rates, checked "
        f"{checked_pt('2026-11-12')} on the API pricing page: grok-imagine-video-1.5 is "
        f"{rate_money(0.08)}/s at 480p, {rate_money(0.14)}/s at 720p, and {rate_money(0.25)}/s at 1080p; "
        f"grok-imagine-video-1.5-lite is {rate_money(0.02)}/s at 480p, {rate_money(0.03)}/s at 720p, and {rate_money(0.14)}/s at 1080p. "
        "Clips are 1 to 15 seconds, and cost scales with duration. Image input is $0.01 per image on both models. "
        "On grok-imagine-video-1.5, preset-voice audio input is free. Lite 1080p is upscaled from 720p; 1.5 is native 1080p."
    )
    q3 = "Do X Premium or SuperGrok plans include video, and what are the limits?"
    a3 = (
        "On the official plan page, video generation is not included on Free or Plus, and is included on Premium, Super, Ultra, Teams, and Enterprise. "
        "Plus does include image generation (Imagine). Super's card also says you can create 1080p, 15-second videos. "
        "Paid usage is a single weekly pool shared across Grok products, not a daily cap per product. "
        "The pool is shown as a percentage; the official pages do not publish the absolute size of the pool or a credits-per-video figure. "
        "There is a 720p cap per tier: 720p videos automatically fall back to 480p once that cap is hit, but the numeric cap is not stated. "
        "Extra usage credits can be bought on the web from $5, expire one year after purchase unless otherwise stated, and are priced at standard rates, which the FAQ says is higher than included weekly usage."
    )
    q4 = "Which route is cheapest for a typical video?"
    a4 = (
        f"For a short text-to-video clip with no input image, the cheapest published 480p and 720p rates are lite at {rate_money(0.02)}/s and {rate_money(0.03)}/s on the official API, matching Runway's lite credits at those resolutions. "
        f"The cheapest published 1080p rate is lite at {rate_money(0.14)}/s; the official video overview says that 1080p lite output is upscaled from 720p. "
        f"If you need native 1080p, references, or voice references, grok-imagine-video-1.5 is {rate_money(0.08)}/{rate_money(0.14)}/{rate_money(0.25)} per second at 480p/720p/1080p on the official API and on fal. "
        "A paid Premium-or-higher plan can be cheaper per clip only if you stay inside the included weekly pool, but this guide cannot convert that pool into dollars per second because the official pages do not give the numbers."
    )
    q5 = "How do we calculate this?"
    a5 = g["HOW_PLAIN"]
    faqs = [(q1, a1), (q2, a2), (q3, a3), (q4, a4), (q5, a5)]

    body = f"""<p class="small"><a href="{root("/guides/")}">Guides</a> › Grok Imagine video cost</p>
<h1>{e(PHRASE)}</h1>
<p class="lead">{lead}</p>
{g["checked_line"]()}
<p>Related: <a href="{root("/models/grok-imagine/")}">{e(name)} model page</a> · <a href="{root("/guides/cheapest-ai-video-generator/")}">cheapest AI video generator by model</a> · <a href="{root("/calculator/")}">credit calculator</a>.</p>

<h2>{e(q1)}</h2>
<p>{e(a1)}</p>

<h2>{e(q2)}</h2>
<p>{e(a2)} Sources: {src(XAI_PRICING, "API pricing")}, {src(XAI_VIDEO, "video overview")}, {src(XAI_15, "1.5 model page")}, and {src(XAI_LITE, "1.5 lite model page")}, checked {checked_pt("2026-11-12")}.</p>
{example_table}
<p class="small">Worked clip totals are official output $/s × length. They do not include the $0.01 per input image, and they do not apply a US-regional token premium: that 1.1× line on the pricing page is about token usage, and the page does not say it applies to Imagine video.</p>

<h2>Official API rates</h2>
<p>These catalog rows are the official list prices from {src(XAI_PRICING, "docs.x.ai/developers/pricing")}, checked {checked_pt("2026-11-12")}. Duration is 1 to 15 seconds. Image input is $0.01 per image. On 1.5, preset-voice audio input is free ({src(XAI_15, "1.5 model page")}). Lite 1080p is upscaled from 720p ({src(XAI_VIDEO, "video overview")}). Batch API accepts image and video but bills them at standard rates, with no batch discount. Image and video generation are not in the text-model batch discount table.</p>
{table_for(xai_rows, "Official xAI API rows are missing from the catalog.")}

<h2>{e(q3)}</h2>
<p>{e(a3)} Sources: {src(XAI_PLANS, "x.ai/pricing")} feature grid and plan cards; {src(XSUB_PRICING, "X plan list prices")} (Plus $8/mo or $80/yr, Premium $30/mo or $300/yr, Super $100/mo or $1,000/yr, Ultra $200/mo or $2,000/yr; prices exclude tax); {src(GROK_FAQ, "Grok FAQ")} on the weekly pool, Extra Usage Credits, and the 720p fallback; {src(XSUB_LIMITS, "usage limits")} and {src(XSUB_EXTRA, "extra usage credits")}, checked {checked_pt("2026-11-12")}.</p>
<p>Existing Cursor, SuperGrok, and X Premium plans continue unless you change or cancel them. New self-serve customers choose the current plan names on {src(XAI_PLANS, "x.ai/pricing")}. Paid plans include API access, but API usage is billed separately at standard model rates and does not draw from the plan's usage pool (same pricing-page FAQ, checked {checked_pt("2026-11-12")}).</p>

<h2>Catalog and other vendors</h2>
<p>fal's Grok Imagine Video 1.5 text-to-video page matches the official 1.5 output rates: {rate_money(0.08)} / {rate_money(0.14)} / {rate_money(0.25)} per second at 480p / 720p / 1080p, with worked 5-second examples of $0.40 / $0.70 / $1.25. Cost scales linearly with duration. That endpoint has no input images or references, so no per-image charges apply ({src(FAL, "fal Grok Imagine Video 1.5")}, checked {checked_pt("2026-11-12")}).</p>
{table_for(fal_rows)}
<p>Runway bills grok_imagine_1_5 at 10 / 16 / 29 credits per second at 480p / 720p / 1080p, plus 1 credit per image or audio reference (including an image-to-video start frame). Lite is 2 / 3 / 14 credits per second at 480p / 720p / 1080p, plus 1 credit for an image-to-video start frame. Credits are $0.01 each, so those output rates are {rate_money(0.10)} / {rate_money(0.16)} / {rate_money(0.29)} for 1.5 and {rate_money(0.02)} / {rate_money(0.03)} / {rate_money(0.14)} for lite ({src(RUNWAY, "Runway API pricing")}, checked {checked_pt("2026-11-12")}). Runway 1.5 is higher than the official 1.5 list. Lite output rates match the official lite list; the extra start-frame credit is on top.</p>
{table_for(runway_rows)}
<p>Atlas Cloud's pricing payload lists the same official output rates for Grok Imagine Video v1.5 text-to-video ({rate_money(0.08)} / {rate_money(0.14)} / {rate_money(0.25)} per second) and for V1.5 Lite text-to-video ({rate_money(0.02)} / {rate_money(0.03)} / {rate_money(0.14)} per second), marked as not estimates, with a “minimum duration and fixed-duration tiers remain part of the model formula” note. Those Atlas rows are not in the catalog. Developer SKUs are also listed. Source: {src(ATLAS, "Atlas Cloud pricing")}, checked {checked_pt("2026-11-12")}.</p>
<p>Replicate's official model page bills {rate_money(0.08)} per second of output video, with no resolution breakdown in the billing table. The page is an image-to-video preview and says every prediction needs an input image; for text-to-video it points to a different model slug. That {rate_money(0.08)}/s figure is not ranked as a 480p, 720p, or 1080p catalog row ({src(REP, "Replicate Grok Imagine Video 1.5")}, checked {checked_pt("2026-11-12")}).</p>
{table_for(other_rows, "No other catalog rows.")}
<p>Krea's pricing page lists approximate counts only, including “Grok Imagine 1.5 1s, 480p” at about 84 / 337 / 675 videos across plan columns. Those counts are tildes, so this catalog does not turn them into dollars per second ({src(KREA, "Krea pricing")}, checked {checked_pt("2026-11-12")}).</p>
<p>Magnific lists “Grok Unlimited” at 70 credits per image, and names Grok Imagine in a footer list of tools. That published credit figure is per image, not per second of video, so it is not ranked here ({src(MAG, "Magnific pricing")}, checked {checked_pt("2026-11-12")}).</p>
<p>Higgsfield's API pricing page and plan page, as fetched today, did not publish a Grok Imagine Video 1.5 dollars-per-second or credits-per-clip figure ({src(HF_API, "Higgsfield API pricing")} and {src(HF_PLANS, "Higgsfield pricing")}, checked {checked_pt("2026-11-12")}).</p>

<h2>{e(q4)}</h2>
<p>{e(a4)}</p>
<ul>
<li>Casual short clips, no references: official lite or Runway lite at the same output $/s, watching input-image add-ons on Runway and the official $0.01/image fee.</li>
<li>Native 1080p, references, or voices: official 1.5 or fal at the official 1.5 rates; Runway 1.5 costs more per second.</li>
<li>Included plan usage: only Premium and higher include video generation. This can be the cheapest route if you stay inside the weekly pool, but the official pages do not say how many videos that pool buys.</li>
<li>After the weekly pool is used up: Extra usage credits are at standard rates, which the FAQ says are higher than included usage. The official API at list price is the rate those “standard rates” can be compared with, but the FAQ does not print a credits-per-video table.</li>
</ul>
<p class="small">Affiliate links never change this price order.</p>

<h2>Hidden costs</h2>
<p><b>Input media.</b> Official 1.5 and lite charge $0.01 per input image. 1.5 also charges for video input; preset-voice audio input is free. Runway adds 1 credit ($0.01) per image or audio reference on 1.5, and 1 credit for an image-to-video start frame on lite. fal's text-to-video page says no per-image charges apply on that endpoint.</p>
<p><b>Failed generations.</b> The official pricing, FAQ, and vendor pages checked today do not state a single refund rule for a failed Grok Imagine video. Treat that cost as unknown.</p>
<p><b>Plan pool and 720p fallback.</b> A high-quality video uses more of the weekly pool than a chat message, but the amount is not published. After the 720p cap for your tier, 720p output falls back to 480p. Extra credits expire after one year unless otherwise stated, and can only be bought on the web today.</p>
<p><b>Older official model.</b> grok-imagine-video (without 1.5) is a separate official model at {rate_money(0.05)}/s at 480p and {rate_money(0.07)}/s at 720p, with $0.01 per second of video input and $0.002 per input image, and no 1080p rate on the pricing table ({src(XAI_V1, "grok-imagine-video model page")} and {src(XAI_PRICING, "API pricing")}, checked {checked_pt("2026-11-12")}). It is not this catalog model and is not mixed into the 1.5 tables.</p>

<h2>What is confirmed, and what is not</h2>
<p><b>Confirmed {checked_pt("2026-11-12")} on official xAI pages:</b> the 1.5 and 1.5-lite output rates and image-input fee; 1–15 second duration; lite 1080p upscaled from 720p; preset-voice audio input free on 1.5; batch video at standard rates; plan prices and the feature grid for video generation (not on Free or Plus; included from Premium up); weekly shared usage pool replacing per-product daily limits; Extra Usage Credits from $5, one-year expiry unless otherwise stated, priced at standard rates; 720p fallback after an unstated per-tier cap; API usage on paid plans billed separately; existing SuperGrok and X Premium plans continue unless changed.</p>
<p><b>Confirmed on vendor pages today, matching or adding to the catalog:</b> fal 1.5 output rates and 5-second examples; Runway 1.5 and lite credit rates, including lite 1080p at 14 credits/s; Atlas standard T2V rates matching the official list; Replicate's $0.08/s I2V billing with no resolution breakdown; Krea's approximate 1.5 counts; Magnific's per-image Grok credit line.</p>
<p><b>Unknown:</b> how many credits or dollars one Imagine video uses on a paid plan; the size of each plan's weekly pool and of the 720p cap; whether a US-regional 1.1× token premium applies to Imagine video; a failed-generation refund rule; a Higgsfield 1.5 video rate; a Replicate resolution breakdown; Krea or Magnific video dollars-per-second. Invented figures are not shown for those gaps.</p>
<h2>{e(q5)}</h2>
<p>{e(a5)}</p>
{g["how_block"]()}
"""

    title = g["page_title"](PHRASE)
    desc = description(g, best)
    g["guide_page"](PATH, title, desc, body, faqs)
    return PATH
