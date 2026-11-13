"""Guide: Higgsfield Black Friday 2026 — what you save per second.

Imported by scripts/build_site.py. Plan prices and sale windows come from
data/deals.json. Per-second rates in the main table come from data/prices.json
Higgsfield plan rows. 6K/9K dollars-per-second are computed from the deal
prices and the same credit rates already on those rows, and are labeled as
computed, not catalog rows. The page states plainly that no Black Friday 2026
offer is on Higgsfield's own site as of the deals' verified dates.
"""
PATH = "/guides/higgsfield-black-friday/"
LABEL = "Higgsfield Black Friday"
PHRASE = "Higgsfield Black Friday 2026: what you save per second"
SOURCE = "https://higgsfield.ai/pricing"
BLOG = "https://higgsfield.ai/blog/higgsfield-11-11-deals"
# Models Higgsfield prices on the plan compare table, in VidFare order.
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


def blurb(g):
    """One plain sentence for the /guides/ index, from the live 11.11 deals."""
    plus = _live(g, "hf-plus-annual")
    ultra = _live(g, "hf-ultra-annual")
    if plus and ultra and plus.get("price_after") is not None and ultra.get("price_after") is not None:
        return (
            f"No Black Friday 2026 sale is listed yet. The 11.11 offer lists Plus annual "
            f"at ${_usd_month(plus['price_after'])[1:]}/mo and Ultra 3K at "
            f"${_usd_month(ultra['price_after'])[1:]}/mo."
        )
    return "No Black Friday 2026 sale is listed on Higgsfield's site yet. The live offer is the 11.11 sale."


def render(g):
    e = g["e"]
    root = g["root"]
    plus_a = _live(g, "hf-plus-annual")
    plus_m = _live(g, "hf-plus-monthly-first")
    ultra_a = _live(g, "hf-ultra-annual")
    ultra_m = _live(g, "hf-ultra-monthly-first")
    ultra_6a = _live(g, "hf-ultra-6k-annual")
    ultra_9a = _live(g, "hf-ultra-9k-annual")
    ultra_6m = _live(g, "hf-ultra-6k-monthly-first")
    ultra_9m = _live(g, "hf-ultra-9k-monthly-first")
    seed = _live(g, "hf-seedance-unlimited-1111")
    biz = _live(g, "hf-seedance-business-30d")
    needed = [plus_a, plus_m, ultra_a, ultra_m]
    if not all(needed):
        raise SystemExit(f"{PATH} missing a live Plus or Ultra 3K 11.11 deal")

    checked = sorted({
        d.get("verified_date") for d in needed + [ultra_6a, ultra_9a, ultra_6m, ultra_9m, seed]
        if d and d.get("verified_date")
    })
    checked_txt = ", ".join(checked) if checked else "not stated"
    # Prefer the newest verified date in running text.
    as_of = checked[-1] if checked else g["TODAY"]
    g["SITEMAP_LASTMOD"][PATH] = as_of

    desc = (
        "No Black Friday 2026 sale is up yet. The 11.11 offer, through Nov 15, "
        f"lists Plus annual at {_usd_month(plus_a['price_after'])}/mo and Ultra 3K "
        f"at {_usd_month(ultra_a['price_after'])}/mo. Here is the per-second math."
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

    # Main $/s table from catalog rows.
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
            label = "estimated from a credit plan" if r.get("status") == "estimate" or est else "from a credit plan"
            cells.append((r, label))
        if missing:
            raise SystemExit(f"{PATH} missing catalog row for {variant} {res}")
        first = cells[0][0]
        name = f"{variant}, {res}"
        if first.get("status") == "estimate" or est:
            name += " (estimate)"
        tds = "".join(f"<td>{e(_rate(g, r['usd_per_second']))}</td>" for r, _ in cells)
        body_rows.append(f"<tr><td>{e(name)}</td>{tds}</tr>")
    rate_table = (
        '<div class="tblwrap"><table><thead>' + head + "</thead><tbody>"
        + "".join(body_rows) + "</tbody></table></div>"
    )

    # Worked example from the Ultra 3K annual Wan 3.0 Prime 480p row.
    if not sample_row:
        raise SystemExit(f"{PATH} missing Wan 3.0 Prime 480p Ultra annual row")
    example = sample_row.get("math") or ""

    # 6K/9K computed rates for the same Wan 3.0 Prime 480p clip, if deals are live.
    extra_bits = []
    clip_cr = sample_row.get("credits_per_clip")
    clip_s = sample_row.get("clip_seconds")
    if clip_cr and clip_s:
        if ultra_9a and ultra_9a.get("price_after") and ultra_9a.get("credits_month"):
            v = _computed(ultra_9a["price_after"], ultra_9a["credits_month"], clip_cr, clip_s)
            extra_bits.append(
                f"On Ultra 9K annual at {_usd_month(ultra_9a['price_after'])}/mo for "
                f"{int(ultra_9a['credits_month']):,} credits, the same 5-second 480p "
                f"Wan 3.0 Prime clip is {_rate(g, v)}. That figure is computed from the "
                f"deal price and the catalog credit rate; it is not a row in the price catalog yet."
            )
        if ultra_6a and ultra_6a.get("price_after") and ultra_6a.get("credits_month"):
            v = _computed(ultra_6a["price_after"], ultra_6a["credits_month"], clip_cr, clip_s)
            extra_bits.append(
                f"Ultra 6K annual at {_usd_month(ultra_6a['price_after'])}/mo for "
                f"{int(ultra_6a['credits_month']):,} credits is {_rate(g, v)} for that clip."
            )
    extra_html = " ".join(e(s) if False else s for s in extra_bits)
    # extra_bits are plain sentences we'll wrap in a <p>
    extra_p = f"<p>{' '.join(extra_bits)}</p>" if extra_bits else ""

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
        best_hf = min(hf_rows, key=lambda r: (r["usd_per_second"], r["id"])) if hf_rows else None
        alt = _cheapest_non_hf(g, model)
        if not best_hf and not alt:
            continue
        if best_hf:
            hf_txt = (
                f"{_rate(g, best_hf['usd_per_second'])} on {e(best_hf.get('plan_name') or best_hf.get('plan') or 'Higgsfield')} "
                f"({e(best_hf.get('resolution') or '')}, {e(best_hf.get('variant') or '')})"
            )
            if best_hf.get("status") == "estimate":
                hf_txt += ", estimate"
        elif model == "seedance-2-5":
            api = [
                r for r in g["rows"]
                if r.get("model") == model and r.get("platform") == "Higgsfield API" and r.get("usd_per_second") is not None
            ]
            if api:
                a = min(api, key=lambda r: r["usd_per_second"])
                hf_txt = (
                    f"No plan rate in the catalog. API list from {_rate(g, a['usd_per_second'])} "
                    f"({e(a.get('resolution') or 'lowest mode')})"
                )
            else:
                hf_txt = "No plan rate in the catalog"
        else:
            hf_txt = "No Higgsfield plan rate in the catalog"
        if alt:
            alt_txt = (
                f"{_rate(g, alt['usd_per_second'])} on {e(alt.get('platform') or '')} "
                f"({e(alt.get('resolution') or '—')}, {e(alt.get('variant') or '')})"
            )
            if alt.get("status") == "estimate":
                alt_txt += ", estimate"
            if alt.get("status") == "promo":
                alt_txt += ", promo"
            alt_txt += f". Checked {e(alt.get('checked') or '')}. {_src(g, alt.get('source_url') or '')}."
        else:
            alt_txt = "None tracked"
        comp_rows.append(f"<tr><td>{e(name)}</td><td>{hf_txt}</td><td>{alt_txt}</td></tr>")
    comp_table = (
        '<div class="tblwrap"><table><thead><tr>'
        "<th>Model</th><th>Cheapest Higgsfield in the catalog</th><th>Cheapest non-Higgsfield</th>"
        "</tr></thead><tbody>" + "".join(comp_rows) + "</tbody></table></div>"
    )

    def plan_line(label, deal, credits=None, renew=False):
        if not deal:
            return ""
        before = deal.get("price_before")
        after = deal.get("price_after")
        pct = deal.get("percent")
        bits = [f"<b>{e(label)}</b>: "]
        if before is not None and after is not None:
            bits.append(f"{_usd_month(before)}/mo list to {_usd_month(after)}")
            if deal.get("conditions", {}).get("annual_only") or "annual" in (label or "").lower():
                bits.append("/mo, billed yearly")
            elif deal.get("conditions", {}).get("first_months"):
                bits.append(" the first month")
                if deal.get("price_before") is not None:
                    bits.append(f", then {_usd_month(deal['price_before'])}/mo")
        if pct is not None:
            bits.append(f", labeled {pct}% off")
        if credits:
            bits.append(f", {credits:,} credits / month")
        bits.append(f". Checked {e(deal.get('verified_date') or '')}. {pricing}.")
        return "<li>" + "".join(bits) + "</li>"

    sale_list = "".join([
        plan_line("Plus annual", plus_a, 1200),
        plan_line("Plus monthly, first month", plus_m, 1200),
        plan_line("Ultra 3K annual", ultra_a, 3000),
        plan_line("Ultra 3K monthly, first month", ultra_m, 3000),
        plan_line("Ultra 6K annual", ultra_6a, (ultra_6a or {}).get("credits_month")),
        plan_line("Ultra 6K monthly, first month", ultra_6m, (ultra_6m or {}).get("credits_month")),
        plan_line("Ultra 9K annual", ultra_9a, (ultra_9a or {}).get("credits_month")),
        plan_line("Ultra 9K monthly, first month", ultra_9m, (ultra_9m or {}).get("credits_month")),
    ])

    window_p = ""
    if seed and seed.get("windows"):
        parts = []
        for w in seed["windows"]:
            plan = w.get("plan") or ""
            billing = w.get("billing") or ""
            days = w.get("days")
            caps = ", ".join(x for x in [
                f"{w['days']} days" if w.get("days") else "",
                f"up to {w['max_clip_seconds']}s" if w.get("max_clip_seconds") else "",
                w.get("resolution") or "",
            ] if x)
            parts.append(f"{plan} {billing}: {caps}")
        window_p = (
            "<p>Unlimited Seedance 2.5 during the 11.11 sale, from the deal record "
            f"(checked {e(seed.get('verified_date') or '')}, {pricing}): "
            + e("; ".join(parts)) +
            ". Those windows are web-only on higgsfield.ai, not on MCP, CLI, Canvas, or Supercomputer, "
            "and speed may change when traffic is high. They are not a dollars-per-second rate. "
            f'See <a href="{root("/guides/seedance-2-5-unlimited/")}">unlimited Seedance 2.5 plans compared</a>.</p>'
        )

    faqs = [
        (
            "Has Higgsfield announced a Black Friday 2026 sale?",
            f"Not as of {as_of}. The pricing page and the official 11.11 deals post list an 11.11 sale, "
            "not a Black Friday, Cyber Monday, or Cyber Week offer. Black Friday 2026 is November 27. "
            "This page will need a recheck then.",
        ),
        (
            "When does the 11.11 sale end?",
            "The pricing page says the 11.11 sale ends on Nov 15. The public sale record the page loads "
            "ends at 2026-11-15T00:00:00Z, which is November 14, 4:00 PM PT. The official blog says "
            "plans must be purchased by November 14 at 23:59 UTC, one minute earlier. Plus and Ultra "
            "monthly first-month prices are labeled as a first payment that then renews at the monthly list. "
            "It is not confirmed whether the listed annual prices stay the same after the sale ends.",
        ),
        (
            "How is dollars per second calculated?",
            "A credit-plan rate is plan price divided by monthly credits, times credits per clip, "
            "divided by seconds in that clip. That math assumes every paid credit is used. "
            "A figure the vendor marks with a tilde, or that VidFare already stores as an estimate, is labeled an estimate. "
            "Seedance 2.5 has no Higgsfield plan credit rate in the catalog, so it has no plan dollars-per-second here.",
        ),
        (
            "Is the 'up to 60% off' badge the saving on every plan?",
            "No. On the annual tab, 60% off is the labeled cut on Ultra 9K annual. "
            f"Ultra 3K annual is labeled {ultra_a.get('percent')}% off, Plus annual {plus_a.get('percent')}% off. "
            "A 60% chip sits next to the 3K/6K/9K selector even when a lower tier is selected. "
            "The card's own percent is the checkout math. Business plans are billed separately as up to 63% off.",
        ),
    ]

    body = f"""<p class="small"><a href="{root("/guides/")}">Guides</a> › Higgsfield Black Friday</p>
<h1>{e(PHRASE)}</h1>
<p class="lead">Higgsfield has not posted a Black Friday 2026 sale on its own site. The offer on the pricing page today is the 11.11 sale, which the page says ends on Nov 15. This page converts those checkout prices into dollars per second of finished video, next to the cheapest alternatives already in the price catalog.</p>
<p class="small">Last checked {e(g["LAST"])}.</p>
<p>Checked {e(as_of)} on the {pricing} and the official {blog}. Prices exclude VAT and local taxes, which are added at checkout. Always confirm the price on Higgsfield's page before you buy.</p>

<h2>What is confirmed, and what is not</h2>
<p>Confirmed: no Black Friday, Cyber Monday, or Cyber Week 2026 label appears on the pricing page or that 11.11 post. A live 11.11 sale is listed, with the plan prices below. The page does not say the sale is for new users only. Unlimited Seedance 2.5 and some image models are included for a limited number of days on Plus and Ultra, only on higgsfield.ai.</p>
<p>Not announced: a Black Friday 2026 discount, its dates, or its fine print. Unknown: whether the listed annual prices revert after Nov 15, the dollar price of the $0 three-day MCP trial's automatic Ultra 3K renewal (the blog only says "a discounted price"), and Higgsfield's Seedance 2.5 credits per clip. Those last two are not turned into dollars per second here.</p>

<h2>11.11 checkout prices</h2>
<p>The banner "up to 60% off" is measured against Higgsfield's own list prices and is the labeled cut on Ultra 9K annual, not on every card. Starter stays {_usd_month(g["plans"]["hf-starter"]["usd_month"])}/mo, monthly or annual, with no 11.11 cut.</p>
<ul>{sale_list}</ul>
<p>Higgsfield's help article {promo_help} says a promo price applies to the first payment or the period stated in the offer, and that the subscription then renews at the standard plan price. Monthly Plus and Ultra first-month cards already state the renewal list price. Annual cards do not say what happens to the listed $35 and $65 prices after Nov 15.</p>
{window_p}

<h2>What you actually save per second</h2>
<p>The formula is the same one the rest of VidFare uses for credit plans: plan dollars per month, divided by credits per month, times credits per clip, divided by seconds in the clip, assuming every paid credit is used. Wan 3.0 and Wan 3.0 Prime credit rates on the pricing-page compare table have no tilde. Kling 3.0, Veo 3.1, and Hailuo 2.3 are marked approximate on that table, so those rows are estimates. VidFare's Kling 3.0 catalog rows use 7.5 credits per 5 seconds at 720p and 8.75 at 1080p, from Higgsfield's yearly clip counts, not the "~7" / "~8" shorthand.</p>
<p>Regular in this table is the monthly list price (Plus {_usd_month(plus_m['price_before'])}, Ultra 3K {_usd_month(ultra_m['price_before'])}). Sale annual is the 11.11 annual checkout. Figures are from the price catalog, last checked {e(sample_row.get("checked") or as_of)}. {pricing}.</p>
{rate_table}
<p>Worked example, Wan 3.0 Prime at 480p on Ultra 3K annual (catalog {e(sample_row["id"])}): {e(example)}</p>
{extra_p}
<p>A first-month monthly price looks cheaper in that first month and much closer to the regular monthly rate over 12 months. For Plus, {_usd_month(plus_m['price_after'])} the first month and {_usd_month(plus_m['price_before'])} for the next 11 months is {_usd_month((plus_m['price_after'] + 11 * plus_m['price_before']) / 12)} a month on average. That blend is illustrative; Higgsfield does not print it.</p>

<h2>Compared with the cheapest alternatives we track</h2>
<p>Rows stay in price order. Affiliate links never change that order. "Cheapest Higgsfield" below is the lowest Higgsfield plan rate already in the catalog (Ultra 3K annual for the models it covers). "Cheapest non-Higgsfield" is the lowest other live row for that model, any resolution.</p>
{comp_table}
<p>On Wan 3.0 and Wan 3.0 Prime, the 11.11 Ultra 3K annual rate is already the cheapest row in the catalog, including other vendors. On Veo 3.1, Krea's Lite estimate is far lower than Higgsfield's Veo 3.1 plan rate. Runway Gen-4, Gemini Omni Flash, and Grok Imagine have no Higgsfield plan rate in the catalog; the pricing-page compare table does not list those three under those names. Seedance 2.5 has no plan credit rate, only the time-limited unlimited windows and an API list price.</p>

<h2>What to recheck</h2>
<p>After Nov 15 (the sale countdown reaches zero at Nov 14, 4:00 PM PT): whether the annual list prices stay at {_usd_month(plus_a['price_after'])} and {_usd_month(ultra_a['price_after'])}, and whether the unlimited windows are gone. On or after Nov 27: whether Higgsfield has posted a Black Friday 2026 offer on its own pricing page or blog. This page does not invent that offer.</p>
{g["faq_html"](faqs)}
<p>Related: <a href="{root("/guides/higgsfield-pricing/")}">Higgsfield pricing explained</a> · <a href="{root("/guides/is-higgsfield-worth-it/")}">Is Higgsfield worth it?</a> · <a href="{root("/guides/seedance-2-5-unlimited/")}">Unlimited Seedance 2.5 plans compared</a> · <a href="{root("/deals/black-friday/")}">Black Friday and holiday deals</a> · <a href="{root("/calculator/")}">credit calculator</a>.</p>
"""
    # news box like other guides? seedance doesn't use news_box in the snippet I saw. skip to avoid layout change issues.

    title = g["page_title"](PHRASE)
    if len(title) > 60:
        raise SystemExit(f"{PATH} title is {len(title)} characters")
    g["guide_page"](PATH, title, desc, body, faqs)
    return {"title": title, "desc": desc, "path": PATH}


if __name__ == "__main__":
    raise SystemExit("imported by scripts/build_site.py")
