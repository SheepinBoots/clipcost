"""Guide: Higgsfield pricing explained.

Imported by scripts/build_site.py. Plan list prices and 11.11 sale figures were
checked on Higgsfield's own pricing page (and the plans API that page loads) on
2026-11-13. Tracked $/s rows come from data/prices.json.
"""
PATH = "/guides/higgsfield-pricing/"
LABEL = "Higgsfield pricing"
PHRASE = "Higgsfield pricing explained"
QUESTION = "What does every Higgsfield plan cost right now?"
HF_PRICING = "https://higgsfield.ai/pricing"
HF_API = "https://open.higgsfield.ai/pricing"
HELP_PLANS = "https://higgsfield.ai/creator-hub/help-center/plans-and-subscriptions/how-do-higgsfield-plans-work"
HELP_UNLIM = "https://higgsfield.ai/creator-hub/help-center/credits/what-are-unlimited-models-and-which-plans-include-them"
HELP_PROMO = "https://higgsfield.ai/creator-hub/help-center/plans/how-do-promo-prices-work"
CHECKED = "2026-11-13"
# Official sale record the pricing page loads: ends_at 2026-11-15T00:00:00Z.
# That instant is Nov 14, 2026, 4:00 PM PT. The page header says "11.11 sale ends on Nov 15."
SALE_ENDS_UTC = "2026-11-15T00:00:00Z"
SALE_ENDS_PT = "Nov 14, 2026, 4:00 PM PT"

# Official credits per clip from the pricing-page compare table (annual payload
# the page loads), checked 2026-11-13. Tildes are Higgsfield's own.
# model slug, feature name, credits, seconds, tilde, resolution
OFFICIAL_CREDITS = [
    ("wan-3-0", "Wan 3.0 480p", 5, 5, False, "480p"),
    ("wan-3-0", "Wan 3.0 720p", 8.75, 5, False, "720p"),
    ("wan-3-0", "Wan 3.0 1080p", 17.5, 5, False, "1080p"),
    ("wan-3-0-prime", "Wan 3.0 Prime 480p", 7.5, 5, False, "480p"),
    ("wan-3-0-prime", "Wan 3.0 Prime 720p", 15, 5, False, "720p"),
    ("wan-3-0-prime", "Wan 3.0 Prime 1080p", 30, 5, False, "1080p"),
    ("kling-3-0", "Kling 3.0 720p", 7, 5, True, "720p"),
    ("kling-3-0", "Kling 3.0 1080p", 8, 5, True, "1080p"),
    ("kling-3-0", "Kling 3.0 4K", 30, 5, True, "4K"),
    ("seedance-2-5", "Seedance 2.5 720p", 35, 5, False, "720p"),
    ("seedance-2-5", "Seedance 2.5 1080p", 80, 5, False, "1080p"),
    ("veo-3-1", "Google Veo 3.1 Fast 720p", 16, 4, True, "720p"),
    ("veo-3-1", "Google Veo 3.1 Fast 1080p", 16, 4, True, "1080p"),
    ("veo-3-1", "Google Veo 3.1 720p", 40, 4, True, "720p"),
    ("veo-3-1", "Google Veo 3.1 1080p", 40, 4, True, "1080p"),
    ("minimax-hailuo", "Minimax Hailuo 2.3 768p", 6, 6, True, "768p"),
    ("minimax-hailuo", "Minimax Hailuo 2.3 1080p", 10, 6, True, "1080p"),
    ("minimax-hailuo", "Minimax Hailuo 2.3 Fast 768p", 4, 6, True, "768p"),
    ("minimax-hailuo", "Minimax Hailuo 2.3 Fast 1080p", 7, 6, True, "1080p"),
    ("grok-imagine", "Grok Video", 7, 5, True, None),
    ("grok-imagine", "Grok Video Edit", 10, 5, True, None),
]

OUR_MODELS = (
    "wan-3-0-prime",
    "wan-3-0",
    "kling-3-0",
    "seedance-2-5",
    "veo-3-1",
    "gemini-omni-flash",
    "minimax-hailuo",
    "runway-gen-4",
    "grok-imagine",
)


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
    months = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    try:
        return f"{months[int(parts[1]) - 1]} {int(parts[2])}, {parts[0]} PT"
    except (ValueError, IndexError):
        return f"{date} PT"


def blurb(g):
    rows = [r for r in g["rows"] if r.get("platform") == "Higgsfield"]
    if not rows:
        return "Current Higgsfield plans, 11.11 sale prices, credits, and the caveats on Unlimited bonuses."
    best = sorted(rows, key=lambda r: (r["usd_per_second"], r["id"]))[0]
    rate = g["rate_money"](best["usd_per_second"])
    return (
        f"The lowest Higgsfield plan rate we track is {rate}/s "
        f"({best['variant']}, {g['shown_resolution'](best)}). "
        f"The 11.11 sale ends {SALE_ENDS_PT}."
    )


def description(g):
    last = g["LAST"]
    rows = [r for r in g["rows"] if r.get("platform") == "Higgsfield"]
    best = sorted(rows, key=lambda r: (r["usd_per_second"], r["id"]))[0] if rows else None
    rate = g["rate_money"](best["usd_per_second"]) if best else None
    options = []
    if rate:
        options.append(
            f"Every current Higgsfield plan, list vs 11.11 sale prices (ends Nov 14, 4 PM PT), "
            f"credits, and $/s from {rate}/s. Last checked {last}."
        )
    options.append(
        f"Higgsfield plans, 11.11 sale prices (ends Nov 14, 4 PM PT), credits, "
        f"and cost per second for the models we track. Last checked {last}."
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
    models = g["models"]
    plans = g["db"]["plans"] if "db" in g else g.get("plans") or {}
    # build_site may pass plans as a global
    if not plans:
        plans = g.get("plans") or {}
    dates = [CHECKED]
    for r in g["rows"]:
        if r.get("platform") in ("Higgsfield", "Higgsfield API") and r.get("checked"):
            dates.append(r["checked"])
    g["SITEMAP_LASTMOD"][PATH] = max(dates)

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

    hf_plan_rows = [r for r in g["rows"] if r.get("platform") == "Higgsfield"]
    hf_api_rows = [r for r in g["rows"] if r.get("platform") == "Higgsfield API"]
    if not hf_plan_rows:
        raise SystemExit(f"{PATH} needs Higgsfield plan rows in the catalog")

    # Lowest tracked plan rate (used in the lead and description).
    best_plan = sorted(hf_plan_rows, key=lambda r: (r["usd_per_second"], r["id"]))[0]

    # Credit price from catalog plan records (Starter / Plus / Ultra 3K).
    catalog_plans = [p for p in plans.values() if p.get("platform") == "Higgsfield"]
    catalog_plans = sorted(catalog_plans, key=lambda p: (p.get("usd_month") or 0, p.get("plan") or ""))

    q1 = QUESTION
    a1 = (
        f"On the official pricing page, checked {checked_pt(CHECKED)}, individual list prices are "
        "Starter $19/mo (monthly or annual, same price, 270 credits), Plus $59/mo (1,200 credits), "
        "and Ultra 3K $129/mo, Ultra 6K $250/mo, and Ultra 9K $375/mo (3,000 / 6,000 / 9,000 credits). "
        f"The 11.11 sale is still marked active and ends {SALE_ENDS_PT} "
        "(the page header says “11.11 sale ends on Nov 15,” and the sale record the page loads ends at "
        f"{SALE_ENDS_UTC}, which is that PT instant). "
        "Sale checkout prices: Plus annual $35/mo billed yearly (list $59, −41%); Ultra 3K / 6K / 9K annual "
        "$65 / $110 / $150 per month billed yearly (list $129 / $258 / $387). "
        "Monthly first-month prices, then renewal at list: Plus $47 then $59 (20% off once); "
        "Ultra 3K $79 then $129 (40% off once); Ultra 6K $150 then $250 (40% off once); "
        "Ultra 9K $209 then $375 (45% off once). "
        "Business, shown per seat: Team annual $45/seat/mo billed yearly (list $79, −43%, 1,000 credits/seat); "
        "Team monthly $55/seat then listed as 30% off (list $79); "
        "Scale annual $80/seat/mo billed yearly (list $215, −63%, 2,500 credits/seat); "
        "Scale monthly $120/seat/mo (list $215, 45% off). Enterprise is custom. Prices exclude VAT and local taxes."
    )
    q2 = "What do credits buy for the models we track?"
    a2 = (
        "The pricing-page compare table states a credits-per-clip figure for each listed model and resolution. "
        "Wan 3.0 is 5 / 8.75 / 17.5 credits per 5-second clip at 480p / 720p / 1080p; Wan 3.0 Prime is 7.5 / 15 / 30. "
        "Those figures have no tilde. Kling 3.0 is labeled “~7 / ~8 / ~30 credits/5s” at 720p / 1080p / 4K "
        "(the same table’s annual video counts divide to 7.5 and about 8.75 at 720p and 1080p; the catalog keeps those as estimates). "
        "Seedance 2.5 is 35 credits/5s at 720p and 80 credits/5s at 1080p. "
        "Google Veo 3.1 is “~16 credits/4s” (Fast) and “~40 credits/4s” (standard) at 720p and at 1080p. "
        "Minimax Hailuo 2.3 is “~6 / ~10 credits/6s” at 768p / 1080p, or “~4 / ~7” for Fast. "
        "Grok Video is “~7 credits/5s” and Grok Video Edit is “~10 credits/5s,” with no resolution on the label. "
        "Gemini Omni Flash and Runway Gen-4 do not appear on that compare table or on the API pricing index checked today, so this guide does not invent a Higgsfield credit cost for them. "
        "A 10-second clip is shown only where the official unit is 5 seconds and the catalog already prices by the second; Veo’s official unit is 4 seconds and Hailuo’s is 6 seconds, and a 10-second length is not published for those."
    )
    q3 = "When is pay-as-you-go elsewhere cheaper?"
    a3 = (
        "For a short clip billed from plan credits, the cheapest Higgsfield credit rate in today’s sale is Ultra 9K annual at "
        f"$150/mo billed yearly ÷ 9,000 credits = $0.01667/credit, if every paid credit is used. "
        "That still has to beat a published pay-as-you-go rate at the same model and resolution. "
        "Where this catalog already has a Higgsfield plan $/s next to a cheaper verified API elsewhere, the table below names that API. "
        "Higgsfield API list prices are a separate pay-as-you-go route (for example Wan 3.0 Prime at $0.051 / $0.105 / $0.21 per second, and “from” $0.118/s for Seedance 2.5 and “from” $0.071/s for Kling 3.0, with the cheapest mode’s resolution not stated on the list). "
        "Unlimited windows are not treated as $0/s."
    )
    q4 = "How do Unlimited bonuses work, and where do they apply?"
    a4 = (
        "Higgsfield’s help article and the pricing-page footer both say Unlimited models and free generations are accessible only on higgsfield.ai, not on MCP/CLI, Canvas, or Supercomputer. "
        "Generations outside higgsfield.ai deduct credits. The toggle in the generation panel has to be on, or the run uses credits. "
        "Unlimited runs in the standard queue; credit runs are in the priority queue, and Unlimited speed may be adjusted in high traffic. "
        "Access is a one-time period that only works while the paid plan stays active. "
        f"On today’s 11.11 cards, annual Plus includes 14 days of unlimited Seedance 2.5 at 30s and 720p; annual Ultra 3K/6K/9K includes 14 days at 30s and 1080p. "
        "Monthly Plus includes 7 days at 20s and 480p; monthly Ultra 3K includes 14 days at 20s and 720p. Starter lists no Seedance 2.5 unlimited window. "
        "Scale annual, after business verification, includes 30 days of unlimited Seedance 2.5 at 25s and 720p; Scale monthly includes 7 days at the same cap. "
        "Team’s unlimited video window is Seedance 2.0 (15s, 720p), not Seedance 2.5: 14 days on annual, 7 days on monthly, also after business verification. "
        "The page does not say when those day counts start."
    )
    q5 = "How do we calculate this?"
    a5 = g["HOW_PLAIN"]
    faqs = [(q1, a1), (q2, a2), (q3, a3), (q4, a4), (q5, a5)]

    # Catalog plan table
    plan_head = (
        "<thead><tr><th>Plan</th><th>Billing</th><th>Credits / mo</th>"
        "<th>List</th><th>Sale / first payment</th><th>Renews at</th><th>Source</th></tr></thead>"
    )
    # Hand-built official plan rows (visible page + plans API), not invented.
    official_plan_rows = [
        ("Starter", "monthly", "270", "$19", "same as list", "$19", "no 11.11 discount"),
        ("Starter", "annual", "270", "$19/mo billed yearly", "same as list", "$19/mo billed yearly", "no 11.11 discount"),
        ("Plus", "monthly", "1,200", "$59", "$47 first month (20% off once)", "$59", "card + plans API"),
        ("Plus", "annual", "1,200", "$59/mo ($708/yr)", "$35/mo billed yearly, −41%, Save $288", "$35/mo billed yearly on the card and plans API (duration “forever”)", "help article says some promo prices then return to the standard price; the card does not say what happens after the sale"),
        ("Ultra 3K", "monthly", "3,000", "$129", "$79 first month (40% off once)", "$129", "card + plans API"),
        ("Ultra 3K", "annual", "3,000", "$129/mo ($1,548/yr)", "$65/mo billed yearly, −50%, Save $768", "$65/mo billed yearly on the card and plans API (duration “forever”)", "same renewal note as Plus annual"),
        ("Ultra 6K", "monthly", "6,000", "$250", "$150 first month (40% off once)", "$250", "plans API the page loads; 6K card on the Annual toggle also shows the $258 / $110 annual pair"),
        ("Ultra 6K", "annual", "6,000", "$258/mo billed yearly", "$110/mo billed yearly, −57%, Save $1,680", "$110/mo billed yearly on the card and plans API (duration “forever”)", "visible 6K card; Save $1,680 uses the $250 monthly list, not $258"),
        ("Ultra 9K", "monthly", "9,000", "$375", "$209 first month (45% off once)", "$375", "plans API the page loads"),
        ("Ultra 9K", "annual", "9,000", "$387/mo billed yearly", "$150/mo billed yearly, −60%, Save $2,700", "$150/mo billed yearly on the card and plans API (duration “forever”)", "visible 9K card; Save $2,700 uses the $375 monthly list, not $387"),
        ("Team (per seat)", "monthly", "1,000 / seat", "$79", "$55 (30% off)", "$55 on the plans API (duration “forever”)", "business tab; default card shows 5 seats = 5,000 plan credits, plus 1,200 bonus credits that expire in 30 days"),
        ("Team (per seat)", "annual", "1,000 / seat", "$79/seat/mo", "$45/seat/mo billed yearly, −43%, Save $120", "$45/seat/mo billed yearly on the card and plans API (duration “forever”)", "2–9 members; card default 5 seats"),
        ("Scale (per seat)", "monthly", "2,500 / seat", "$215", "$120 / seat/mo (45% off)", "plans API final price is $119.99; the card shows $120", "7-day Seedance 2.5 window, 25s 720p, after business verification"),
        ("Scale (per seat)", "annual", "2,500 / seat", "$215/seat/mo", "$80/seat/mo billed yearly, −63%, Save $480", "$80/seat/mo billed yearly on the card and plans API (duration “forever”)", "30-day Seedance 2.5 window, 25s 720p, after business verification; 5–15 members"),
        ("Enterprise", "custom", "custom", "Contact sales", "custom", "custom", "no public $/seat"),
    ]
    plan_body = "".join(
        "<tr>"
        f"<td>{e(a)}</td><td>{e(b)}</td><td>{e(c)}</td><td>{e(d)}</td><td>{e(ee)}</td><td>{e(f)}</td>"
        f"<td class=\"small\">{e(note)}</td></tr>"
        for a, b, c, d, ee, f, note in official_plan_rows
    )
    plan_table = f'<div class="tblwrap fit"><table>{plan_head}<tbody>{plan_body}</tbody></table></div>'

    # Catalog $/s table: one row per tracked Higgsfield plan rate, cheapest first, grouped lightly.
    # Show plan name from math/variant if present. Use existing row fields.
    def plan_label(r):
        note = (r.get("note") or "") + " " + (r.get("math") or "")
        for label, needle in (
            ("Ultra annual 3K", "$65/mo"),
            ("Ultra monthly 3K", "$129/mo"),
            ("Plus annual", "$35/mo"),
            ("Plus monthly", "$59/mo"),
            ("Starter", "$19/mo"),
        ):
            if needle in (r.get("math") or ""):
                return label
        return r.get("variant") or "Higgsfield plan"

    cat_head = (
        "<thead><tr><th>Model</th><th>Res</th><th>Plan (catalog)</th>"
        "<th>$/s</th><th>Official  clip</th><th>10s (if linear)</th><th>Status</th><th>Source</th></tr></thead>"
    )
    official_by = {}
    for slug, name, credits, secs, tilde, res in OFFICIAL_CREDITS:
        official_by.setdefault((slug, res), []).append((name, credits, secs, tilde))

    def official_clip_text(r):
        hits = official_by.get((r["model"], r.get("resolution"))) or []
        if not hits:
            return "not on today’s compare table"
        name, credits, secs, tilde = hits[0]
        t = f"{'~' if tilde else ''}{credits:g} credits/{secs}s"
        return t

    def ten_s_cell(r):
        hits = official_by.get((r["model"], r.get("resolution"))) or []
        if hits and hits[0][2] != 5:
            return "official unit is not 5s"
        return rate_money(r["usd_per_second"] * 10)

    cat_rows_html = []
    for r in sorted(hf_plan_rows, key=lambda r: (r["usd_per_second"], r["id"])):
        cat_rows_html.append(
            "<tr>"
            f"<td>{e(models.get(r['model'], {}).get('name') or r['model'])}</td>"
            f"<td>{e(shown_resolution(r))}</td>"
            f"<td>{e(plan_label(r))}</td>"
            f'<td class="num">{rate_money(r["usd_per_second"])}{assumption_html(r)}</td>'
            f"<td>{e(official_clip_text(r))}</td>"
            f'<td class="num">{ten_s_cell(r)}</td>'
            f"<td>{status_cell(r)}</td>"
            f"<td>{source_toggle(r)}</td>"
            "</tr>"
        )
    cat_table = f'<div class="tblwrap fit"><table>{cat_head}<tbody>{"".join(cat_rows_html)}</tbody></table></div>'

    # Derived Seedance 2.5 / Grok (not in catalog plan rows) from official credits × catalog plan credit prices.
    def credit_price(usd, credits):
        return usd / credits

    derived_plans = [
        ("Starter", 19, 270),
        ("Plus annual (sale)", 35, 1200),
        ("Plus monthly list", 59, 1200),
        ("Ultra 3K annual (sale)", 65, 3000),
        ("Ultra 3K monthly list", 129, 3000),
        ("Ultra 9K annual (sale)", 150, 9000),
    ]
    derived_models = [x for x in OFFICIAL_CREDITS if x[0] in ("seedance-2-5", "grok-imagine")]
    der_head = (
        "<thead><tr><th>Model</th><th>Official credits</th><th>Plan</th>"
        "<th>$/credit</th><th>Official clip</th><th>$/s (if linear)</th><th>10s (if linear, 5s unit)</th></tr></thead>"
    )
    der_rows = []
    for slug, name, credits, secs, tilde, res in derived_models:
        for plan_name, usd, cr in derived_plans:
            cprice = credit_price(usd, cr)
            clip = cprice * credits
            per_s = clip / secs
            ten = (cprice * credits / secs) * 10 if secs == 5 else "official unit is not 5s"
            label = name + (f" ({res})" if res else " (resolution not stated)")
            credit_label = f"{'~' if tilde else ''}{credits:g} / {secs}s"
            ten_html = ten if isinstance(ten, str) else rate_money(ten)
            der_rows.append(
                "<tr>"
                f"<td>{e(label)}</td><td>{e(credit_label)}</td><td>{e(plan_name)}</td>"
                f'<td class="num">{rate_money(cprice)}</td>'
                f'<td class="num">{rate_money(clip)}</td>'
                f'<td class="num">{rate_money(per_s)}</td>'
                f'<td class="num">{ten_html}</td>'
                "</tr>"
            )
    der_table = f'<div class="tblwrap fit"><table>{der_head}<tbody>{"".join(der_rows)}</tbody></table></div>'

    # PAYG comparison: cheapest catalog HF plan $/s vs cheapest verified non-HF API at same model+res.
    cmp_head = (
        "<thead><tr><th>Model</th><th>Res</th><th>Cheapest HF plan in catalog</th>"
        "<th>Cheapest verified API elsewhere</th><th>Cheaper route</th></tr></thead>"
    )
    cmp_rows = []
    keys = sorted({(r["model"], r.get("resolution")) for r in hf_plan_rows})
    for model, res in keys:
        hf = [r for r in hf_plan_rows if r["model"] == model and r.get("resolution") == res]
        hf_best = sorted(hf, key=lambda r: (r["usd_per_second"], r["id"]))[0]
        others = [
            r for r in g["rows"]
            if r["model"] == model
            and r.get("resolution") == res
            and r.get("kind") == "api"
            and r.get("status") in ("verified", "promo")
            and r.get("platform") not in ("Higgsfield", "Higgsfield API")
        ]
        if not others:
            other_txt = "no verified non-Higgsfield API row at this resolution"
            winner = "Higgsfield plan (no published API comparison at this res)"
        else:
            o = sorted(others, key=lambda r: (r["usd_per_second"], r["id"]))[0]
            other_txt = f"{rate_money(o['usd_per_second'])}/s on {o['platform']} ({o['variant']})"
            if o["usd_per_second"] < hf_best["usd_per_second"]:
                winner = f"PAYG on {o['platform']} is cheaper than this plan rate"
            elif o["usd_per_second"] > hf_best["usd_per_second"]:
                winner = "the Higgsfield plan rate is cheaper, if every paid credit is used"
            else:
                winner = "same published $/s"
        cmp_rows.append(
            "<tr>"
            f"<td>{e(models.get(model, {}).get('name') or model)}</td>"
            f"<td>{e(res or '—')}</td>"
            f'<td class="num">{rate_money(hf_best["usd_per_second"])}/s · {e(plan_label(hf_best))}</td>'
            f"<td>{e(other_txt)}</td>"
            f"<td>{e(winner)}</td>"
            "</tr>"
        )
    cmp_table = f'<div class="tblwrap fit"><table>{cmp_head}<tbody>{"".join(cmp_rows)}</tbody></table></div>'

    api_head = (
        "<thead><tr><th>Model</th><th>Res / note</th><th>Higgsfield API $/s</th><th>Status</th><th>Source</th></tr></thead>"
    )
    api_body = "".join(
        "<tr>"
        f"<td>{e(models.get(r['model'], {}).get('name') or r['model'])}</td>"
        f"<td>{e(shown_resolution(r))}</td>"
        f'<td class="num">{rate_money(r["usd_per_second"])}</td>'
        f"<td>{status_cell(r)}</td>"
        f"<td>{source_toggle(r)}</td>"
        "</tr>"
        for r in sorted(hf_api_rows, key=lambda r: (r["usd_per_second"], r["id"]))
    )
    api_table = (
        f'<div class="tblwrap fit"><table>{api_head}<tbody>{api_body}</tbody></table></div>'
        if hf_api_rows else "<p>No Higgsfield API rows are in the catalog.</p>"
    )

    lead = (
        f"Higgsfield’s current individual and business plan prices, including the 11.11 sale that ends {SALE_ENDS_PT}, "
        "are taken from the official pricing page today. "
        f"The lowest Higgsfield plan rate already in this catalog is {rate_money(best_plan['usd_per_second'])}/s "
        f"({best_plan['variant']}, {shown_resolution(best_plan)}), assuming every paid credit is used. "
        "Unlimited bonuses apply only on higgsfield.ai. Affiliate links never change this price order."
    )

    body = f"""<p class="small"><a href="{root("/guides/")}">Guides</a> › Higgsfield pricing</p>
<h1>{e(PHRASE)}</h1>
<p class="lead">{lead}</p>
{g["checked_line"]()}
<p>Related: <a href="{root("/guides/higgsfield-black-friday/")}">Higgsfield Black Friday 2026: what you save per second</a> · <a href="{root("/guides/is-higgsfield-worth-it/")}">Is Higgsfield worth it?</a> · <a href="{root("/guides/seedance-2-5-unlimited/")}">Unlimited Seedance 2.5 plans compared</a> · <a href="{root("/calculator/")}">credit calculator</a>.</p>

<h2>{e(q1)}</h2>
<p>{e(a1)} Sources: {src(HF_PRICING, "higgsfield.ai/pricing")} (Individual Annual / Monthly and Business tabs, rendered {checked_pt(CHECKED)}), the public plans API and 11.11 sale record that page loads, and {src(HELP_PLANS, "How do Higgsfield plans work?")}.</p>
{plan_table}
<p class="small">Dollar amounts are US list prices as shown, before VAT and local taxes. Team and Scale cards default to 5 seats; Team allows 2–9 members and Scale 5–15. Bonus business credits expire in 30 days and are not included in the credit-price math below. Unused first-month credits roll over on Team and Scale, per the cards.</p>

<h2>{e(q2)}</h2>
<p>{e(a2)} Source: the Video category of the compare table on {src(HF_PRICING, "higgsfield.ai/pricing")}, from the compare API that page loads, checked {checked_pt(CHECKED)}.</p>
<p>The catalog already converts those official (or official-estimate) credit figures into $/s for Starter, Plus, and Ultra 3K, using each plan’s dollars and credits and assuming every paid credit is used. Those tracked rates are below, with a 10-second total only when the official unit is 5 seconds.</p>
{cat_table}
<p>Seedance 2.5 and Grok are on the official compare table but do not have Higgsfield plan rows in the catalog (Seedance 2.5 on plans was left out of earlier guides for the same reason; Grok Video has no stated resolution). The next table applies the same credit-use math to today’s official credits and to the Starter / Plus / Ultra 3K catalog plan prices, plus Ultra 9K annual, which is the cheapest sale credit price. These derived figures are not catalog rows.</p>
{der_table}
<p class="small">Kling 3.0 720p and 1080p stay catalog estimates: the compare table labels them “~7” and “~8” credits/5s, while the same table’s annual video counts divide to 7.5 and about 8.75. No existing catalog dollar amount was changed.</p>

<h2>{e(q3)}</h2>
<p>{e(a3)}</p>
{cmp_table}
<p>Higgsfield API pay-as-you-go, from {src(HF_API, "open.higgsfield.ai/pricing")} and the catalog rows last checked {checked_pt(CHECKED)} (the API “from” figures for Wan 3.0, Kling 3.0, and Seedance 2.5 on that index today still match these rows; the cheapest mode’s resolution is still not stated for the “from” list prices):</p>
{api_table}
<p class="small">Affiliate links never change this price order.</p>

<h2>{e(q4)}</h2>
<p>{e(a4)} Sources: {src(HELP_UNLIM, "What are Unlimited models?")}, the pricing-page footer and plan cards on {src(HF_PRICING, "higgsfield.ai/pricing")}, and the 11.11 sale record the page loads, checked {checked_pt(CHECKED)}.</p>
<p>The same help article describes a longer “365 Unlimited” style of access on mid and top plans: generations on listed models do not deduct credits for a stated period, only while the paid plan stays active, and only on higgsfield.ai. Plus and Ultra cards also say “5 other unlimited models” without naming them on the card. This guide does not invent those five names or treat any Unlimited window as $0/s.</p>
<p>{src(HELP_PROMO, "How promo prices work")} says a promo price applies to the first payment or the period stated in the offer, and that the plan then renews at the standard price. Monthly Plus and Ultra first-month cards already print the renewal list price. Annual cards and the plans API show the sale monthly-equivalent as the renew price (the API marks those annual discounts “forever”). It is not confirmed, from the annual cards alone, whether a new Ultra 9K annual $150/mo price remains after {SALE_ENDS_PT}.</p>

<h2>What is confirmed, and what is not</h2>
<p><b>Confirmed {checked_pt(CHECKED)} on Higgsfield’s own pages and the APIs those pages load:</b> the individual and business list and 11.11 sale prices in the table above; credit allowances; the sale end instant {SALE_ENDS_UTC} ({SALE_ENDS_PT}); Unlimited and free generations only on higgsfield.ai; the Seedance 2.5 / 2.0 window lengths and caps written on the cards; official credits-per-clip in the compare table; catalog Starter / Plus / Ultra 3K dollar amounts, which still match today’s checkout figures; Higgsfield API “from” list prices for Wan 3.0, Wan 3.0 Prime, Kling 3.0, and Seedance 2.5.</p>
<p><b>Unknown:</b> whether annual sale prices stay at $35 / $65 / $110 / $150 after the sale for new buyers, or for renewals, given the tension between the help article and the plans API; when the 7-, 14-, 30-, and 60-day Unlimited clocks start; the five unnamed “other” unlimited models on the Plus/Ultra cards; a published credit cost or Higgsfield plan $/s for Gemini Omni Flash or Runway Gen-4; the resolution of “Grok Video”; credit-pack list prices (the cards say top-ups exist, with a discount on paid plans, but this check did not capture a pack price table); a failed-generation refund rule for plan credits. Invented figures are not shown for those gaps.</p>

<h2>{e(q5)}</h2>
<p>{e(a5)}</p>
{g["how_block"]()}
"""

    title = g["page_title"](PHRASE)
    desc = description(g)
    g["guide_page"](PATH, title, desc, body, faqs)
    return PATH
