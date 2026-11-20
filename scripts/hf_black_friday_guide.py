"""Guide: Higgsfield Black Friday 2026 — what you save per second.

Imported by scripts/build_site.py. Current Black Friday plan prices come from
a Nov 19, 2026, 7:20 PM ET (4:20 PM PT) reading of https://higgsfield.ai/pricing. Per-second rates in
the main table come from data/prices.json Higgsfield plan rows. Ultra 6K and
Ultra 9K dollars-per-second are computed from the verified card prices and the
same catalog credit rates, and are labeled computed, not catalog rows.
"""
PATH = "/guides/higgsfield-black-friday/"
LABEL = "Higgsfield Black Friday"
PHRASE = "Higgsfield Black Friday 2026: what you save per second"
SOURCE = "https://higgsfield.ai/pricing"
BLOG = "https://higgsfield.ai/blog/higgsfield-11-11-deals"
# When the pricing page was re-read for this update.
CHECKED = "2026-11-19"
CHECKED_WHEN = "Nov 19, 2026, 7:20 PM ET (4:20 PM PT)"
# Official Black Friday sale record on higgsfield.ai/pricing (sale_11_11).
BF_ENDS_UTC = "2026-11-23T00:00:00Z"
from timefmt import et_pt  # noqa: E402

BF_ENDS_PT = et_pt(BF_ENDS_UTC, long_month=True)  # November 22, 2026, 7:00 PM ET (4:00 PM PT)
# Recorded 11.11 / standing annual prices, last verified Nov 12, now ended.
HIST_11_11_PLUS_MO = 35
HIST_11_11_ULTRA_3K_MO = 65
# Verified on the Individual Annual (or Monthly) cards at CHECKED_WHEN.
PLUS_ANNUAL_MO = 33
ULTRA_3K_ANNUAL_MO = 50
ULTRA_6K_ANNUAL_MO = 97
ULTRA_6K_CREDITS = 6000
ULTRA_9K_ANNUAL_MO = 139
ULTRA_9K_CREDITS = 9000
STARTER_MO = 19
PLUS_LIST_MO = 59
ULTRA_3K_LIST_MO = 129
ULTRA_6K_LIST_MO = 258
ULTRA_9K_LIST_MO = 387
PLUS_MONTHLY_FIRST_MO = 47
ULTRA_3K_MONTHLY_FIRST_MO = 79
ULTRA_6K_MONTHLY_FIRST_MO = 150
ULTRA_9K_MONTHLY_FIRST_MO = 209

MODELS = [
    "wan-3-0-prime",
    "wan-3-0",
    "kling-3-0",
    "veo-3-1",
    "minimax-hailuo",
]
# One representative clip per model for the main table (catalog rows exist).
TABLE_SPECS = [
    ("wan-3-0-prime", "Wan 3.0 Prime", "480p", False),
    ("wan-3-0-prime", "Wan 3.0 Prime", "720p", False),
    ("wan-3-0-prime", "Wan 3.0 Prime", "1080p", False),
    ("wan-3-0", "Wan 3.0", "480p", False),
    ("wan-3-0", "Wan 3.0", "720p", False),
    ("wan-3-0", "Wan 3.0", "1080p", False),
    ("kling-3-0", "Kling 3.0", "720p", True),
    ("kling-3-0", "Kling 3.0", "1080p", True),
    ("veo-3-1", "Veo 3.1", "720p", True),
    ("veo-3-1", "Veo 3.1 Fast", "720p", True),
    ("minimax-hailuo", "Hailuo 2.3", "768p", True),
]
PLAN_COLS = [
    ("hf-plus-monthly", "Plus monthly"),
    ("hf-plus-annual", "Plus annual"),
    ("hf-ultra-monthly", "Ultra 3K monthly"),
    ("hf-ultra-annual", "Ultra 3K annual"),
]


def _deal(g, deal_id):
    return g["DEAL_BY_ID"].get(deal_id)


def _live(g, deal_id):
    d = _deal(g, deal_id)
    if not d:
        return None
    if not g["dealmod"].is_current(d, g["TODAY"]):
        return None
    return d


def _src(g, url, text="source"):
    e = g["e"]
    href, rel = g["outbound"](url)
    return f'<a href="{e(href)}" rel="{rel}" target="_blank">{e(text)}</a>'


def _usd_month(v):
    return f"${v:g}"


def _rate(g, v):
    return g["rate_money"](v) + "/s"


def _row_for(g, model, variant, resolution, plan):
    rows = [
        r for r in g["rows"]
        if r.get("model") == model
        and r.get("platform") == "Higgsfield"
        and r.get("kind") == "plan"
        and r.get("plan") == plan
        and r.get("resolution") == resolution
        and (r.get("variant") or "") == variant
        and r.get("usd_per_second") is not None
    ]
    if not rows:
        # variant stored without Fast suffix sometimes; try startswith
        rows = [
            r for r in g["rows"]
            if r.get("model") == model
            and r.get("platform") == "Higgsfield"
            and r.get("kind") == "plan"
            and r.get("plan") == plan
            and r.get("resolution") == resolution
            and r.get("usd_per_second") is not None
            and variant.lower() in (r.get("variant") or "").lower()
        ]
    if not rows:
        return None
    return sorted(rows, key=lambda r: r["id"])[0]


def _cheapest_non_hf(g, model):
    rows = [
        r for r in g["rows"]
        if r.get("model") == model
        and r.get("usd_per_second") is not None
        and "higgsfield" not in (r.get("platform") or "").lower()
        and r.get("status") != "discontinued"
    ]
    if not rows:
        return None
    return min(rows, key=lambda r: (r["usd_per_second"], r["id"]))


def _computed(usd_month, credits_month, credits_per_clip, clip_seconds):
    return (float(usd_month) / float(credits_month)) * float(credits_per_clip) / float(clip_seconds)


def _audio_label(row):
    audio = row.get("audio")
    if audio in (None, "", "not stated"):
        return "audio not stated"
    return f"audio {audio}"


def blurb(g):
    """One plain sentence for the /guides/ index."""
    return (
        "Higgsfield's pricing page now lists a Black Friday sale: Plus annual at "
        f"${PLUS_ANNUAL_MO:g}/mo and Ultra 3K at ${ULTRA_3K_ANNUAL_MO:g}/mo, billed yearly."
    )


def render(g):
    e = g["e"]
    root = g["root"]
    plus_a_hist = _deal(g, "hf-plus-annual")
    ultra_a_hist = _deal(g, "hf-ultra-annual")
    plus_m_hist = _deal(g, "hf-plus-monthly-first")
    ultra_m_hist = _deal(g, "hf-ultra-monthly-first")

    g["SITEMAP_LASTMOD"][PATH] = CHECKED

    desc = (
        "Higgsfield Black Friday: Plus annual $33/mo and Ultra 3K $50/mo, billed yearly. "
        "Official end Nov 22, 2026, 7:00 PM ET (4:00 PM PT). Checkout totals are unknown."
    )
    if len(desc) > 160:
        raise SystemExit(f"{PATH} description is {len(desc)} characters")

    pricing = _src(g, SOURCE, "Higgsfield pricing page")
    blog = _src(g, BLOG, "11.11 deals post")
    promo_help = _src(
        g,
        "https://higgsfield.ai/creator-hub/help-center/plans/how-do-promo-prices-work",
        "How do promo prices work?",
    )

    # Main $/s table from catalog rows. Each cell is only the rate; tier,
    # resolution, and audio are on the row label plus the notes under the table.
    head = (
        "<tr><th>Model</th><th>Plus monthly</th><th>Plus annual</th>"
        "<th>Ultra 3K monthly</th><th>Ultra 3K annual</th></tr>"
    )
    body_rows = []
    sample_row = None
    for model, variant, res, est in TABLE_SPECS:
        cells = []
        missing = False
        for plan, _label in PLAN_COLS:
            r = _row_for(g, model, variant, res, plan)
            if not r:
                missing = True
                break
            if sample_row is None and plan == "hf-ultra-annual" and model == "wan-3-0-prime" and res == "480p":
                sample_row = r
            cells.append(r)
        if missing:
            raise SystemExit(f"{PATH} missing catalog row for {variant} {res}")
        first = cells[0]
        audio = _audio_label(first)
        name = f"{variant}, {res}, {audio}"
        if first.get("status") == "estimate" or est:
            name += " (estimate)"
        tds = "".join(f"<td>{e(_rate(g, r['usd_per_second']))}</td>" for r in cells)
        body_rows.append(f"<tr><td>{e(name)}</td>{tds}</tr>")
    rate_table = (
        '<div class="tblwrap"><table id="hf-bf-rate-table"><thead>' + head + "</thead><tbody>"
        + "".join(body_rows) + "</tbody></table></div>"
    )

    if not sample_row:
        raise SystemExit(f"{PATH} missing Wan 3.0 Prime 480p Ultra annual row")
    example = sample_row.get("math") or ""

    extra_bits = []
    clip_cr = sample_row.get("credits_per_clip")
    clip_s = sample_row.get("clip_seconds")
    if clip_cr and clip_s:
        v6 = _computed(ULTRA_6K_ANNUAL_MO, ULTRA_6K_CREDITS, clip_cr, clip_s)
        extra_bits.append(
            f"On Ultra 6K annual at {_usd_month(ULTRA_6K_ANNUAL_MO)}/mo for "
            f"{ULTRA_6K_CREDITS:,} credits, the same 5-second 480p Wan 3.0 Prime clip is "
            f"{_rate(g, v6)}. That figure is computed from the card price verified "
            f"{CHECKED_WHEN} and the catalog credit rate; it is not a row in the price catalog."
        )
        v9 = _computed(ULTRA_9K_ANNUAL_MO, ULTRA_9K_CREDITS, clip_cr, clip_s)
        extra_bits.append(
            f"On Ultra 9K annual at {_usd_month(ULTRA_9K_ANNUAL_MO)}/mo for "
            f"{ULTRA_9K_CREDITS:,} credits, that same clip is {_rate(g, v9)}. "
            "That figure is computed from the card price verified "
            f"{CHECKED_WHEN} and the catalog credit rate; it is not a row in the price catalog."
        )
    extra_p = f"<p>{' '.join(e(s) for s in extra_bits)}</p>" if extra_bits else ""

    # Comparison table
    comp_rows = []
    for model in MODELS + ["seedance-2-5", "gemini-omni-flash", "runway-gen-4", "grok-imagine"]:
        name = g["db"]["models"].get(model, {}).get("name") or model
        hf_rows = [
            r for r in g["rows"]
            if r.get("model") == model
            and r.get("platform") == "Higgsfield"
            and r.get("kind") == "plan"
            and r.get("usd_per_second") is not None
        ]
        cheapest_hf = min(hf_rows, key=lambda r: (r["usd_per_second"], r["id"])) if hf_rows else None
        alt = _cheapest_non_hf(g, model)
        if cheapest_hf:
            hf_cell = (
                f"{_rate(g, cheapest_hf['usd_per_second'])} "
                f"({e(cheapest_hf.get('plan') or '')}, {e(cheapest_hf.get('resolution') or '')}, "
                f"{e(_audio_label(cheapest_hf))})"
            )
        else:
            hf_cell = "no Higgsfield plan rate in the catalog"
        if alt:
            alt_cell = (
                f"{_rate(g, alt['usd_per_second'])} "
                f"({e(alt.get('platform') or '')}, {e(alt.get('resolution') or '')}, "
                f"{e(_audio_label(alt))})"
            )
        else:
            alt_cell = "none in the catalog"
        comp_rows.append(f"<tr><td>{e(name)}</td><td>{hf_cell}</td><td>{alt_cell}</td></tr>")
    comp_table = (
        '<div class="tblwrap"><table><thead>'
        "<tr><th>Model</th><th>Cheapest Higgsfield</th><th>Cheapest non-Higgsfield</th></tr>"
        "</thead><tbody>" + "".join(comp_rows) + "</tbody></table></div>"
    )

    hist_plus = _usd_month(HIST_11_11_PLUS_MO)
    hist_ultra = _usd_month(HIST_11_11_ULTRA_3K_MO)
    hist_plus_m = _usd_month((plus_m_hist or {}).get("price_after") or 47)
    hist_ultra_m = _usd_month((ultra_m_hist or {}).get("price_after") or 79)

    q_sale = "Has Higgsfield announced a Black Friday 2026 sale?"
    a_sale = (
        f"Yes. On {CHECKED_WHEN} the official pricing page showed a “BLACK FRIDAY 63% OFF” banner "
        "and “up to 63% OFF” on the Individual Annual cards. Plus annual was "
        f"{_usd_month(PLUS_ANNUAL_MO)}/mo billed yearly, and Ultra 3K annual was "
        f"{_usd_month(ULTRA_3K_ANNUAL_MO)}/mo billed yearly. The official sale record ends at "
        f"{BF_ENDS_UTC}, which is {BF_ENDS_PT}. The 11.11 sale is over. "
        "The same Monthly cards still show first-month Plus and Ultra prices during this extended Black Friday window."
    )
    q_end = "When does the Black Friday sale end?"
    a_end = (
        f"The official sale record on the pricing page (still named sale_11_11, with phase pre_black_friday_63) "
        f"ends at {BF_ENDS_UTC}, which is {BF_ENDS_PT}. The visible banner is only a "
        "countdown (“Offer ends in”); it does not print that calendar date. Vendors sometimes extend sales, "
        "so the banner should be rechecked after that time. Checkout totals remain unknown."
    )
    q_check = "What will I pay at checkout?"
    a_check = (
        "Unknown. The pricing page says prices exclude VAT and local taxes, which are calculated "
        "at checkout. The card prices below are the pre-tax figures shown on the page, not a "
        "completed checkout total."
    )
    q_math = "How is dollars per second calculated?"
    a_math = (
        "A credit-plan rate is plan price divided by monthly credits, times credits per clip, "
        "divided by seconds in that clip. That math assumes every paid credit is used. "
        "A figure the vendor marks with a tilde, or that VidFare already stores as an estimate, is labeled an estimate. "
        "Seedance 2.5 has no Higgsfield plan credit rate in the catalog, so it has no plan dollars-per-second here. "
        "The monthly columns use the catalog list prices (Plus "
        f"{_usd_month(PLUS_LIST_MO)}/mo, Ultra 3K {_usd_month(ULTRA_3K_LIST_MO)}/mo), not the first-month card prices."
    )
    faqs = [(q_sale, a_sale), (q_end, a_end), (q_check, a_check), (q_math, a_math)]

    body = f"""<p class="small"><a href="{root("/guides/")}">Guides</a> › Higgsfield Black Friday</p>
<h1>{e(PHRASE)}</h1>
<p class="lead">Higgsfield has posted a Black Friday 2026 sale on its own pricing page. As of {e(CHECKED_WHEN)}, Plus annual is {_usd_month(PLUS_ANNUAL_MO)}/mo billed yearly and Ultra 3K annual is {_usd_month(ULTRA_3K_ANNUAL_MO)}/mo billed yearly. The official sale record ends at {e(BF_ENDS_UTC)}, which is {e(BF_ENDS_PT)}. The tax-inclusive checkout totals are unknown.</p>
<p class="small">Last checked {e(g["LAST"])}. Official card prices were read {e(CHECKED_WHEN)}. Catalog per-second rows use the date on each row.</p>
<p>Checked {e(CHECKED_WHEN)} on the {pricing}. The page banner says “BLACK FRIDAY 63% OFF” and “Don’t miss your chance to get up to 63% OFF.” Prices exclude VAT and local taxes, calculated at checkout. Always confirm the price on Higgsfield's page before you buy. Affiliate links never change this price order.</p>

<h2>What is on the cards today</h2>
<p>These figures were read on the Individual plan cards at {e(CHECKED_WHEN)}. A percent off is the label on that card, measured against Higgsfield's own list price, and is not 63% on every plan.</p>
<ul>
<li>Starter: {_usd_month(STARTER_MO)}/mo, monthly or billed yearly, 270 credits. No Black Friday cut was shown on the card.</li>
<li>Plus annual: {_usd_month(PLUS_ANNUAL_MO)}/mo billed yearly (list {_usd_month(PLUS_LIST_MO)}, labeled −45%, Save $312), 1,200 credits / month.</li>
<li>Ultra 3K annual: {_usd_month(ULTRA_3K_ANNUAL_MO)}/mo billed yearly (list {_usd_month(ULTRA_3K_LIST_MO)}, labeled −60%, Save $948), 3,000 credits / month.</li>
<li>Ultra 6K annual: {_usd_month(ULTRA_6K_ANNUAL_MO)}/mo billed yearly (list {_usd_month(ULTRA_6K_LIST_MO)}, labeled −62%, Save $1,836), 6,000 credits / month. Save $1,836 uses the $250 monthly list, not {_usd_month(ULTRA_6K_LIST_MO)}.</li>
<li>Ultra 9K annual: {_usd_month(ULTRA_9K_ANNUAL_MO)}/mo billed yearly (list {_usd_month(ULTRA_9K_LIST_MO)}, labeled −63%, Save $2,832), 9,000 credits / month. Save $2,832 uses the $375 monthly list, not {_usd_month(ULTRA_9K_LIST_MO)}.</li>
<li>Plus monthly: {_usd_month(PLUS_MONTHLY_FIRST_MO)} first month, “billed monthly, renews at {_usd_month(PLUS_LIST_MO)},” labeled 20% off, 1,200 credits / month.</li>
<li>Ultra 3K monthly: {_usd_month(ULTRA_3K_MONTHLY_FIRST_MO)} first month, “billed monthly, renews at {_usd_month(ULTRA_3K_LIST_MO)},” labeled 40% off, 3,000 credits / month.</li>
<li>Ultra 6K monthly: {_usd_month(ULTRA_6K_MONTHLY_FIRST_MO)} first month, “billed monthly, renews at $250,” 6,000 credits / month.</li>
<li>Ultra 9K monthly: {_usd_month(ULTRA_9K_MONTHLY_FIRST_MO)} first month, “billed monthly, renews at $375,” labeled 45% off, 9,000 credits / month.</li>
</ul>
<p>Plus and Ultra annual and monthly cards also say “Unlimited models for 7 days,” only on higgsfield.ai. When that 7-day window starts or ends is unknown. The promotion also mentions a roughly $100 gift card for games for the first 10,000 eligible new annual Ultra subscribers, from Nov 20. The Business tab still showed Team annual at $45/seat/mo billed yearly (−43%, Save $120) and Scale annual at $80/seat/mo billed yearly (−63%, Save $480), and Team monthly $55 / Scale monthly $120; those checkout prices match the earlier standing discounts. The Business tab says “up to 63% OFF.” Scale annual still shows 30 days of unlimited Seedance 2.5 at 25s, 720p, after business verification; Team annual shows 14 days of unlimited Seedance 2.0 at 15s, 720p, not Seedance 2.5.</p>
<p>Unknown: the tax-inclusive amount charged at checkout; whether annual sale prices remain after the sale for new buyers or at renewal (the help article {promo_help} says a promo price applies to the first payment or the period stated in the offer, then the plan renews at the standard price; the annual cards do not spell out a post-sale price; the plans API records renew_monthly_price at the sale rate with duration “forever”). A plans API response without the plan-set key the page uses (ps_a3) returned lower Plus and Starter prices ($27/$39 and $15); those figures are not what the visible Individual cards show. The official end is stated above; vendors sometimes extend sales.</p>

<h2>The 11.11 sale, now ended</h2>
<p>The 11.11 sale is over. First-month Plus and Ultra offers in the deal record were marked ended Nov 15, 2026, then appeared again on the Monthly cards during this extended Black Friday window. The official {blog} and the earlier sale countdown pointed at that window (the public sale record ended at 2026-11-15T00:00:00Z, which is November 14, 7:00 PM ET (4:00 PM PT); that older ends_at is no longer the live sale_11_11 record on the pricing page, which now holds the Black Friday window). Recorded 11.11 / standing prices, last verified Nov 12 in the deal record, were Plus annual {e(hist_plus)}/mo and Ultra 3K annual {e(hist_ultra)}/mo, and first-month Plus {e(hist_plus_m)} / Ultra 3K {e(hist_ultra_m)}. Those annual figures are not the cards shown today. The monthly first-month amounts on today’s cards happen to match the old first-month figures, but this page does not treat them as a continuation of 11.11.</p>

<h2>What you actually save per second</h2>
<p>The formula is the same one the rest of VidFare uses for credit plans: plan dollars per month, divided by credits per month, times credits per clip, divided by seconds in the clip, assuming every paid credit is used. Unused credits make the real cost per second higher. Wan 3.0 and Wan 3.0 Prime credit rates on the pricing-page compare table have no tilde. Kling 3.0, Veo 3.1, and Hailuo 2.3 are marked approximate on that table, so those rows are estimates. VidFare's Kling 3.0 catalog rows use 7.5 credits per 5 seconds at 720p and 8.75 at 1080p, from Higgsfield's yearly clip counts, not the "~7" / "~8" shorthand.</p>
<p>Each row names the model, resolution, and audio. Audio is not stated on these Higgsfield plan rows. The four rate columns are catalog plan tiers: Plus monthly at the {_usd_month(PLUS_LIST_MO)}/mo list price for 1,200 credits; Plus annual at the {_usd_month(PLUS_ANNUAL_MO)}/mo billed-yearly sale price for 1,200 credits; Ultra 3K monthly at the {_usd_month(ULTRA_3K_LIST_MO)}/mo list price for 3,000 credits; Ultra 3K annual at the {_usd_month(ULTRA_3K_ANNUAL_MO)}/mo billed-yearly sale price for 3,000 credits. The monthly columns do not use the first-month card prices. Figures are from the price catalog, last checked {e(sample_row.get("checked") or CHECKED)}. {pricing}.</p>
{rate_table}
<p>Worked example, Wan 3.0 Prime at 480p on Ultra 3K annual (catalog {e(sample_row["id"])}): {e(example)}</p>
{extra_p}
<p>A first-month monthly price looks cheaper in that first month and much closer to the regular monthly rate over 12 months. For Plus, {_usd_month(PLUS_MONTHLY_FIRST_MO)} the first month and {_usd_month(PLUS_LIST_MO)} for the next 11 months is {_usd_month((PLUS_MONTHLY_FIRST_MO + 11 * PLUS_LIST_MO) / 12)} a month on average. That blend is illustrative; Higgsfield does not print it.</p>

<h2>Compared with the cheapest alternatives we track</h2>
<p>Rows stay in price order. Affiliate links never change that order. "Cheapest Higgsfield" below is the lowest Higgsfield plan rate already in the catalog (Ultra 3K annual for the models it covers). "Cheapest non-Higgsfield" is the lowest other live row for that model, any resolution.</p>
{comp_table}
<p>On Wan 3.0 and Wan 3.0 Prime, the current Ultra 3K annual catalog rate is already the cheapest row in the catalog, including other vendors. On Veo 3.1, Krea's Lite estimate is far lower than Higgsfield's Veo 3.1 plan rate. Runway Gen-4, Gemini Omni Flash, and Grok Imagine have no Higgsfield plan rate in the catalog; the pricing-page compare table does not list those three under those names. Seedance 2.5 has no plan credit rate, only time-limited unlimited windows and an API list price.</p>

<h2>What to recheck</h2>
<p>Whether the official {e(BF_ENDS_UTC)} end still holds after {e(BF_ENDS_PT)}, in case the sale is extended. The tax-inclusive checkout total. Whether annual sale prices stay at {_usd_month(PLUS_ANNUAL_MO)}, {_usd_month(ULTRA_3K_ANNUAL_MO)}, {_usd_month(ULTRA_6K_ANNUAL_MO)}, and {_usd_month(ULTRA_9K_ANNUAL_MO)} after the sale. Whether the “Unlimited models for 7 days” window is still offered. Whether a plans API call without the plan-set key still returns different Plus and Starter prices than the visible cards.</p>
<h2>{e(q_sale)}</h2>
<p>{e(a_sale)}</p>
<h2>{e(q_end)}</h2>
<p>{e(a_end)}</p>
<h2>{e(q_check)}</h2>
<p>{e(a_check)}</p>
<h2>{e(q_math)}</h2>
<p>{e(a_math)}</p>
{g["faq_html"](faqs)}
<p>Related: <a href="{root("/guides/higgsfield-pricing/")}">Higgsfield pricing explained</a> · <a href="{root("/guides/is-higgsfield-worth-it/")}">Is Higgsfield worth it?</a> · <a href="{root("/guides/seedance-2-5-unlimited/")}">Unlimited Seedance 2.5 plans compared</a> · <a href="{root("/deals/black-friday/")}">Black Friday and holiday deals</a> · <a href="{root("/calculator/")}">credit calculator</a>.</p>
"""

    title = g["page_title"](PHRASE)
    if len(title) > 60:
        raise SystemExit(f"{PATH} title is {len(title)} characters")
    g["guide_page"](PATH, title, desc, body, faqs)
    return {"title": title, "desc": desc, "path": PATH}


if __name__ == "__main__":
    raise SystemExit("imported by scripts/build_site.py")
