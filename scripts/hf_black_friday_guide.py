"""Guide: Higgsfield Black Friday 2026 — what you save per second.

Imported by scripts/build_site.py. Sale status, sale prices and end times come
from data/deals.json (Higgsfield Black Friday deal records) through
scripts/deal_copy.py, so the copy flips to "ended" as soon as the deal ends.
Current plan prices and per-second rates come from data/prices.json.
"""
PATH = "/guides/higgsfield-black-friday/"
LABEL = "Higgsfield Black Friday"
PHRASE = "Higgsfield Black Friday 2026: what you save per second"
SOURCE = "https://higgsfield.ai/pricing"
BLOG = "https://higgsfield.ai/blog/higgsfield-11-11-deals"
# Fallback content date; the deal records' verified date is used when newer.
CHECKED = "2026-11-19"
from timefmt import et_pt  # noqa: E402,F401
import deal_copy  # noqa: E402

# Recorded 11.11 / standing annual prices, last verified Nov 12, now ended (history).
HIST_11_11_PLUS_MO = 35
HIST_11_11_ULTRA_3K_MO = 65
ULTRA_6K_CREDITS = 6000
ULTRA_9K_CREDITS = 9000

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
    """One plain sentence for the /guides/ index, from deals.json."""
    st = deal_copy.hf_bf(g)
    if st["live"]:
        return (f"Higgsfield's Black Friday sale is live until {st['end']}: Plus annual "
                f"{deal_copy.money(deal_copy.price_after(st, 'hf-plus-annual'))}/mo and Ultra 3K "
                f"{deal_copy.money(deal_copy.price_after(st, 'hf-ultra-annual'))}/mo, billed yearly.")
    return f"Higgsfield's Black Friday sale has ended (last phase ended {st['end']}). What the sale saved per second, and current prices."


def render(g):
    e = g["e"]
    root = g["root"]
    plus_a_hist = _deal(g, "hf-plus-annual")
    ultra_a_hist = _deal(g, "hf-ultra-annual")
    plus_m_hist = _deal(g, "hf-plus-monthly-first")
    ultra_m_hist = _deal(g, "hf-ultra-monthly-first")

    g["SITEMAP_LASTMOD"][PATH] = max(CHECKED, deal_copy.hf_bf(g)["verified"] or CHECKED)

    st = deal_copy.hf_bf(g)
    pa = deal_copy.price_after(st, "hf-plus-annual")
    ua = deal_copy.price_after(st, "hf-ultra-annual")
    if st["live"]:
        desc = (f"Higgsfield Black Friday: Plus annual {deal_copy.money(pa)}/mo and Ultra 3K {deal_copy.money(ua)}/mo, billed yearly. "
                f"Ends {st['end']}. Checkout totals are unknown.")
    else:
        desc = (f"Higgsfield's Black Friday sale ended {st['end']}. What it saved per second, "
                "current plan prices, and what is unknown.")
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
    for did, credits, label in (("hf-ultra-6k-annual", ULTRA_6K_CREDITS, "Ultra 6K"), ("hf-ultra-9k-annual", ULTRA_9K_CREDITS, "Ultra 9K")):
        price = deal_copy.price_after(st, did)
        if st["live"] and price and clip_cr and clip_s:
            v = _computed(price, credits, clip_cr, clip_s)
            extra_bits.append(
                f"On {label} annual at {_usd_month(price)}/mo for {credits:,} credits under the sale, the same "
                f"5-second 480p Wan 3.0 Prime clip is {_rate(g, v)}. That figure is computed from the deal record "
                f"(verified {st['verified']}) and the catalog credit rate; it is not a row in the price catalog."
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

    pricing_md = _src(g, "https://higgsfield.ai/pricing.md", "Higgsfield pricing.md")
    sale_sentence = deal_copy.hf_sale_sentence(st)
    prices_sentence = deal_copy.hf_prices_sentence(g)
    plus_list = deal_copy.plan_month(g, "hf-plus-monthly")
    ultra_list = deal_copy.plan_month(g, "hf-ultra-monthly")
    plus_ann = deal_copy.plan_month(g, "hf-plus-annual")
    ultra_ann = deal_copy.plan_month(g, "hf-ultra-annual")
    if st["live"]:
        cards = []
        for did in deal_copy.HF_BF_IDS:
            d = st["deals"].get(did)
            if d and did in st["live_ids"]:
                cards.append(f"<li>{e(d.get('title') or did)}. {e(d.get('source_quote') or '')}</li>")
        cards_html = (
            f"<h2>What is on the cards now</h2>\n<p>From the deal records, verified {e(st['verified'])} on the {pricing} and {pricing_md}. "
            f"The sale ends {e(st['end_long'])}. Prices exclude VAT and local taxes.</p>\n<ul>{''.join(cards)}</ul>"
        )
        ann_word = "billed-yearly sale price"
    else:
        cards_html = (
            f"<h2>The sale has ended</h2>\n<p>{e(sale_sentence)} {e(prices_sentence)} Source: {pricing}. "
            "A price Higgsfield’s page does not show is marked unknown. Prices exclude VAT and local taxes.</p>"
        )
        ann_word = "current billed-yearly price"

    q_sale = "Is the Higgsfield Black Friday 2026 sale still on?"
    a_sale = sale_sentence
    q_end = "When does the Black Friday sale end?"
    if st["live"]:
        a_end = (f"The sale record on Higgsfield's pricing page ends at {st['ends_at']}, which is {st['end_long']}. "
                 "The visible banner is only a countdown. Vendors sometimes extend sales, so VidFare rechecks after that time.")
    else:
        a_end = (f"It has ended. The last phase ended {st['end_long']} ({st['ends_at']}), from the sale record on "
                 f"Higgsfield's pricing page, rechecked {st['verified']}. " + " ".join(p + "." for p in deal_copy.hf_phases_text(st)))
    q_check = "What will I pay at checkout?"
    a_check = (
        "Unknown. The pricing page says prices exclude VAT and local taxes, which are calculated "
        "at checkout. The card prices are the pre-tax figures shown on the page, not a "
        "completed checkout total."
    )
    q_math = "How is dollars per second calculated?"
    a_math = (
        "A credit-plan rate is plan price divided by monthly credits, times credits per clip, "
        "divided by seconds in that clip. That math assumes every paid credit is used. "
        "A figure the vendor marks with a tilde, or that VidFare already stores as an estimate, is labeled an estimate. "
        "Seedance 2.5 has no Higgsfield plan credit rate in the catalog, so it has no plan dollars-per-second here. "
        f"The monthly columns use the catalog monthly prices (Plus {deal_copy.money(plus_list)}/mo, "
        f"Ultra 3K {deal_copy.money(ultra_list)}/mo), not first-month offers."
    )
    faqs = [(q_sale, a_sale), (q_end, a_end), (q_check, a_check), (q_math, a_math)]

    body = f"""<p class="small"><a href="{root("/guides/")}">Guides</a> › Higgsfield Black Friday</p>
<h1>{e(PHRASE)}</h1>
<p class="lead">{e(sale_sentence)} The tax-inclusive checkout totals are unknown.</p>
<p class="small">Last checked {e(g["LAST"])}. Sale status is read from the deal records (verified {e(st["verified"] or "unknown")}). Catalog per-second rows use the date on each row. Always confirm the price on Higgsfield's page before you buy. Affiliate links never change this price order.</p>

{cards_html}

<h2>The 11.11 sale, now ended</h2>
<p>The 11.11 sale is over. Its public sale record ended at 2026-11-15T00:00:00Z, which is November 14, 7:00 PM ET (4:00 PM PT), per the official {blog}. Recorded 11.11 / standing prices, last verified Nov 12 in the deal record, were Plus annual {_usd_month(HIST_11_11_PLUS_MO)}/mo and Ultra 3K annual {_usd_month(HIST_11_11_ULTRA_3K_MO)}/mo. How promo prices renew: {promo_help}.</p>

<h2>What you actually save per second</h2>
<p>The formula is the same one the rest of VidFare uses for credit plans: plan dollars per month, divided by credits per month, times credits per clip, divided by seconds in the clip, assuming every paid credit is used. Unused credits make the real cost per second higher. Wan 3.0 and Wan 3.0 Prime credit rates on the pricing-page compare table have no tilde. Kling 3.0, Veo 3.1, and Hailuo 2.3 are marked approximate on that table, so those rows are estimates.</p>
<p>Each row names the model, resolution, and audio. Audio is not stated on these Higgsfield plan rows. The four rate columns are catalog plan tiers: Plus monthly at {deal_copy.money(plus_list)}/mo for 1,200 credits; Plus annual at the {ann_word} of {deal_copy.money(plus_ann)}/mo for 1,200 credits; Ultra 3K monthly at {deal_copy.money(ultra_list)}/mo for 3,000 credits; Ultra 3K annual at the {ann_word} of {deal_copy.money(ultra_ann)}/mo for 3,000 credits. Figures are from the price catalog, last checked {e(sample_row.get("checked") or CHECKED)}. {pricing}.</p>
{rate_table}
<p>Worked example, Wan 3.0 Prime at 480p on Ultra 3K annual (catalog {e(sample_row["id"])}): {e(example)}</p>
{extra_p}

<h2>Compared with the cheapest alternatives we track</h2>
<p>Rows stay in price order. Affiliate links never change that order. "Cheapest Higgsfield" below is the lowest Higgsfield plan rate already in the catalog (Ultra 3K annual for the models it covers). "Cheapest non-Higgsfield" is the lowest other live row for that model, any resolution.</p>
{comp_table}
<p>On Wan 3.0 and Wan 3.0 Prime, the current Ultra 3K annual catalog rate is already the cheapest row in the catalog, including other vendors. On Veo 3.1, Krea's Lite estimate is far lower than Higgsfield's Veo 3.1 plan rate. Runway Gen-4, Gemini Omni Flash, and Grok Imagine have no Higgsfield plan rate in the catalog; the pricing-page compare table does not list those three under those names. Seedance 2.5 has no plan credit rate, only time-limited unlimited windows and an API list price.</p>

<h2>What to recheck</h2>
<p>Whether Higgsfield starts another sale phase; VidFare's daily check re-reads the pricing page and its sale record. The tax-inclusive checkout total. Whether the annual card price changes again. Whether a plans API call without the plan-set key still returns different Plus and Starter prices than the visible cards.</p>
<h2>{e(q_sale)}</h2>
<p>{e(a_sale)}</p>
<h2>{e(q_end)}</h2>
<p>{e(a_end)}</p>
<h2>{e(q_check)}</h2>
<p>{e(a_check)}</p>
<h2>{e(q_math)}</h2>
<p>{e(a_math)}</p>
<p>Related: <a href="{root("/guides/higgsfield-pricing/")}">Higgsfield pricing explained</a> · <a href="{root("/guides/is-higgsfield-worth-it/")}">Is Higgsfield worth it?</a> · <a href="{root("/guides/seedance-2-5-unlimited/")}">Unlimited Seedance 2.5 plans compared</a> · <a href="{root("/deals/black-friday/")}">Black Friday and holiday deals</a> · <a href="{root("/calculator/")}">credit calculator</a>.</p>
"""

    title = g["page_title"](PHRASE)
    if len(title) > 60:
        raise SystemExit(f"{PATH} title is {len(title)} characters")
    g["guide_page"](PATH, title, desc, body, faqs)
    return {"title": title, "desc": desc, "path": PATH}


if __name__ == "__main__":
    raise SystemExit("imported by scripts/build_site.py")
