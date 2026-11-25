import guide_tables
"""Guide: Higgsfield pricing explained.

Imported by scripts/build_site.py. Plan prices come from data/prices.json
(checked against Higgsfield's own pricing page). Black Friday sale status, end
time, and sale prices come from the Higgsfield deal records in data/deals.json
through scripts/deal_copy.py, so the copy flips to "ended" once ends_at passes.
"""
PATH = "/guides/higgsfield-pricing/"
LABEL = "Higgsfield pricing"
PHRASE = "Higgsfield pricing explained"
QUESTION = "What does every Higgsfield plan cost?"
HF_PRICING = "https://higgsfield.ai/pricing"
HF_API = "https://open.higgsfield.ai/pricing"
HELP_PLANS = "https://higgsfield.ai/creator-hub/help-center/plans-and-subscriptions/how-do-higgsfield-plans-work"
HELP_UNLIM = "https://higgsfield.ai/creator-hub/help-center/credits/what-are-unlimited-models-and-which-plans-include-them"
HELP_PROMO = "https://higgsfield.ai/creator-hub/help-center/plans/how-do-promo-prices-work"
HELP_CREDITS = "https://higgsfield.ai/creator-hub/help-center/credits/how-credits-work"
HELP_EXPIRE = "https://higgsfield.ai/creator-hub/help-center/credits/top-up-credits-expire"
HELP_PACKS = "https://higgsfield.ai/creator-hub/help-center/credits/how-credit-packs-work"
HELP_CANCEL = "https://higgsfield.ai/creator-hub/help-center/refunds/how-do-i-cancel-my-subscription"
HELP_REFUND = "https://higgsfield.ai/creator-hub/help-center/refunds/how-do-i-request-a-refund"
HELP_FREE = "https://higgsfield.ai/creator-hub/help-center/plans/what-does-the-free-plan-include"
POLICY_CHECKED = "2026-11-18"
CHECKED = "2026-11-13"
# Official 11.11 sale record, now ended: ends_at 2026-11-15T00:00:00Z.
# That instant is Nov 14, 2026, 7:00 PM ET (4:00 PM PT). The page header said "11.11 sale ends on Nov 15."
# The live sale_11_11 record on 2026-11-17 is the Black Friday window below.
SALE_ENDS_UTC = "2026-11-15T00:00:00Z"
SALE_ENDS_PT = "Nov 14, 2026, 7:00 PM ET (4:00 PM PT)"
BF_CHECKED = "2026-11-24"
BF_CHECKED_WHEN = "Nov 24, 2026, 3:26 PM ET (12:26 PM PT)"
from timefmt import et_pt  # noqa: E402,F401
import deal_copy  # noqa: E402

# Ultra 6K / 9K annual monthly-equivalent prices after the sale. Not in the
# catalog; None means "unknown" until read on Higgsfield's own page.
POST_SALE_6K_ANNUAL = None
POST_SALE_9K_ANNUAL = None

# Official credits per clip from the pricing-page compare table (annual payload
# the page loads), checked 2026-11-13; Wan 3.0 and Wan 3.0 Prime re-read
# 2026-11-24 after Higgsfield's Nov 22 credit cuts. Tildes are Higgsfield's own.
# model slug, feature name, credits, seconds, tilde, resolution
OFFICIAL_CREDITS = [
    ("wan-3-0", "Wan 3.0 480p", 3.75, 5, False, "480p"),
    ("wan-3-0", "Wan 3.0 720p", 7.5, 5, False, "720p"),
    ("wan-3-0", "Wan 3.0 1080p", 15, 5, False, "1080p"),
    ("wan-3-0-prime", "Wan 3.0 Prime 480p", 6.25, 5, False, "480p"),
    ("wan-3-0-prime", "Wan 3.0 Prime 720p", 13.75, 5, False, "720p"),
    ("wan-3-0-prime", "Wan 3.0 Prime 1080p", 27.5, 5, False, "1080p"),
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
    """Date-only check label, e.g. 'Nov 23, 2026'. A date carries no clock, so no zone."""
    from timefmt import day_label
    return day_label(date)


def blurb(g):
    rows = [r for r in g["rows"] if r.get("platform") == "Higgsfield"]
    if not rows:
        return "Current Higgsfield plans, Black Friday card prices, credits, and the caveats on Unlimited bonuses."
    best = sorted(rows, key=lambda r: (r["usd_per_second"], r["id"]))[0]
    rate = g["rate_money"](best["usd_per_second"])
    return (
        f"The lowest Higgsfield plan rate we track is {rate}/s "
        f"({best['variant']}, {g['shown_resolution'](best)}). "
        + deal_copy.hf_sale_sentence(deal_copy.hf_bf(g))
    )


def description(g):
    last = g["LAST"]
    rows = [r for r in g["rows"] if r.get("platform") == "Higgsfield"]
    best = sorted(rows, key=lambda r: (r["usd_per_second"], r["id"]))[0] if rows else None
    rate = g["rate_money"](best["usd_per_second"]) if best else None
    st = deal_copy.hf_bf(g)
    sale = "Black Friday sale prices" if st["live"] else "regular prices after the Black Friday sale"
    options = []
    if rate:
        options.append(
            f"Every current Higgsfield plan: {sale}, "
            f"credits, and $/s from {rate}/s. Last checked {last}."
        )
    options.append(f"Higgsfield plans, credits, and cost per second for the models we track. Last checked {last}.")
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

    st = deal_copy.hf_bf(g)
    money = deal_copy.money
    live = st["live"]
    p_starter = plans.get("hf-starter") or {}
    p_plus_m = plans.get("hf-plus-monthly") or {}
    p_ultra_m = plans.get("hf-ultra-monthly") or {}
    starter_m = p_starter.get("usd_month") or 19
    starter_c = p_starter.get("credits_month") or 270
    plus_m = p_plus_m.get("usd_month") or 59
    plus_c = p_plus_m.get("credits_month") or 1200
    ultra_m = p_ultra_m.get("usd_month") or 129
    ultra_c = p_ultra_m.get("credits_month") or 3000
    pa, ua = deal_copy.plan_month(g, "hf-plus-annual"), deal_copy.plan_month(g, "hf-ultra-annual")
    if live:
        six_a = deal_copy.price_after(st, "hf-ultra-6k-annual")
        nine_a = deal_copy.price_after(st, "hf-ultra-9k-annual")
    else:
        six_a, nine_a = POST_SALE_6K_ANNUAL, POST_SALE_9K_ANNUAL
    first = {i: deal_copy.price_after(st, i) for i in ("hf-plus-monthly-first", "hf-ultra-monthly-first", "hf-ultra-6k-monthly-first", "hf-ultra-9k-monthly-first")}
    q1 = QUESTION
    if live:
        sale_part = (
            deal_copy.hf_sale_sentence(st) + " "
            f"Annual Ultra 6K is {money(six_a)}/mo and Ultra 9K is {money(nine_a)}/mo, billed yearly (lists $258 and $387). "
            f"First month on monthly billing, then renewal at list: Plus {money(first['hf-plus-monthly-first'])} then {money(plus_m)}; "
            f"Ultra 3K {money(first['hf-ultra-monthly-first'])} then {money(ultra_m)}; Ultra 6K {money(first['hf-ultra-6k-monthly-first'])} then $250; "
            f"Ultra 9K {money(first['hf-ultra-9k-monthly-first'])} then $375. "
            "The visible banner is a countdown only, and vendors sometimes extend sales. "
        )
    else:
        sale_part = (
            deal_copy.hf_sale_sentence(st) + " "
            f"Annual billing in data/prices.json: Plus {money(pa)}/mo and Ultra 3K {money(ua)}/mo, billed yearly; "
            f"Ultra 6K {money(six_a)}/mo and Ultra 9K {money(nine_a)}/mo, billed yearly. "
        )
    a1 = (
        f"On the official pricing page, re-read {BF_CHECKED_WHEN}, individual monthly list prices are "
        f"Starter {money(starter_m)}/mo (monthly or annual, same price, {starter_c:,} credits), "
        f"Plus {money(plus_m)}/mo ({plus_c:,} credits), "
        f"and Ultra 3K {money(ultra_m)}/mo, Ultra 6K $250/mo, and Ultra 9K $375/mo ({ultra_c:,} / 6,000 / 9,000 credits). "
        + sale_part +
        f"The 11.11 sale ended at {SALE_ENDS_PT}. "
        "Checkout totals are unknown (VAT and local taxes are calculated at checkout). "
        "Business, shown per seat: Team annual $45/seat/mo billed yearly (list $79, 1,000 credits/seat); "
        "Team monthly $55/seat (list $79); "
        "Scale annual $80/seat/mo billed yearly (list $215, 2,500 credits/seat); "
        "Scale monthly $119.99/seat/mo (list $215). Enterprise is custom. Prices exclude VAT and local taxes."
    )
    q2 = "What do credits buy for the models we track?"
    a2 = (
        "The pricing-page compare table states a credits-per-clip figure for each listed model and resolution. "
        "Wan 3.0 is 3.75 / 7.5 / 15 credits per 5-second clip at 480p / 720p / 1080p; Wan 3.0 Prime is 6.25 / 13.75 / 27.5 (re-read Nov 24, after Higgsfield cut Wan credits on Nov 22). "
        "Those figures have no tilde. Kling 3.0 is labeled “~7 / ~8 / ~30 credits/5s” at 720p / 1080p / 4K "
        "(the same table’s annual video counts divide to 7.5 and about 8.75 at 720p and 1080p; the catalog keeps those as estimates). "
        "Seedance 2.5 is 35 credits/5s at 720p and 80 credits/5s at 1080p. "
        "Google Veo 3.1 is “~16 credits/4s” (Fast) and “~40 credits/4s” (standard) at 720p and at 1080p. "
        "Minimax Hailuo 2.3 is “~6 / ~10 credits/6s” at 768p / 1080p, or “~4 / ~7” for Fast. "
        "Grok Video is “~7 credits/5s” and Grok Video Edit is “~10 credits/5s,” with no resolution on the label. "
        "Gemini Omni Flash and Runway Gen-4 do not appear on that compare table or on the API pricing index checked Nov 13, 2026, so this guide does not invent a Higgsfield credit cost for them. "
        "A 10-second clip is shown only where the official unit is 5 seconds and the catalog already prices by the second; Veo’s official unit is 4 seconds and Hailuo’s is 6 seconds, and a 10-second length is not published for those."
    )
    q3 = "When is pay-as-you-go elsewhere cheaper?"
    a3 = (
        (
            f"For a short clip billed from plan credits, the cheapest Higgsfield credit rate on the current annual prices is Ultra 9K annual at "
            f"{money(nine_a)}/mo billed yearly ÷ 9,000 credits (${nine_a / 9000:.5f}/credit), if every paid credit is used. "
            f"Ultra 6K annual at {money(six_a)}/mo billed yearly ÷ 6,000 credits is ${six_a / 6000:.5f}/credit. "
            if (six_a and nine_a) else
            "The Ultra 6K and 9K annual prices after the sale are not confirmed yet, so their credit rates are not computed. "
        ) +
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
        "On the Nov 16 Individual Annual Plus and Ultra cards, the visible unlimited line is “Unlimited models for 7 days”; when that window starts or ends is unknown. "
        "The earlier 11.11 check on 2026-11-13 had listed annual Plus at 14 days of unlimited Seedance 2.5 at 30s and 720p, and annual Ultra 3K/6K/9K at 14 days at 30s and 1080p; "
        "those 14-day details were not reconfirmed on Nov 16. "
        "The Nov 13 monthly cards listed Plus at 7 days at 20s and 480p and Ultra 3K at 14 days at 20s and 720p. Starter lists no Seedance 2.5 unlimited window. "
        "Scale annual, after business verification, includes 30 days of unlimited Seedance 2.5 at 25s and 720p; Scale monthly includes 7 days at the same cap. "
        "Team’s unlimited video window is Seedance 2.0 (15s, 720p), not Seedance 2.5: 14 days on annual, 7 days on monthly, also after business verification. "
        "The page does not say when those day counts start."
    )
    q_credits_how = "How do Higgsfield credits work?"
    a_credits_how = (
        f"Official help, re-read {checked_pt(POLICY_CHECKED)}, says credits are what Higgsfield charges for image and video generations. "
        "The cost depends on the model, resolution, and duration, and is shown on the Generate button before you confirm. "
        "Plan credits reset and do not roll over: on monthly plans at each paid renewal, and on annual plans every 30 days. "
        "Credit Pack, Auto-Refill, and Boost credits are one-time balances that expire 90 days from purchase. "
        "Promo credits expire on the date shown when they are issued. "
        "Plan credits are spent first; then any remaining credits are spent by the earliest expiry date. "
        "Credits per clip for the models we track are in the compare-table section on this page, not in the help article."
    )
    q_refund = "What is Higgsfield's refund policy?"
    a_refund = (
        f"Official help, re-read {checked_pt(POLICY_CHECKED)}, says refunds are for initial purchases only, "
        "within 7 days or as permitted by the law in your jurisdiction, and only if no credits have been used. "
        "Renewals are not refundable. Credit Packs and Auto-Refill charges can be refunded on the same 7-day, unused-credit conditions. "
        "Offers that unlock access or features rather than credits are not refundable once that access is granted. "
        "Using free generations or Unlimited model generations does not count as credit use. "
        "A service fee of up to 6% is deducted, and if a refund is approved the plan is cancelled immediately, with funds returning to the original payment method in 5–10 business days. "
        "Cancelling a plan does not, by itself, issue a refund. Request a refund through Higgsfield's contact form with your account email, purchase date, amount, and a short reason."
    )
    q_cancel = "How do I cancel a Higgsfield plan?"
    a_cancel = (
        f"Official help, re-read {checked_pt(POLICY_CHECKED)}, says cancelling turns off auto-renewal. "
        "The plan stays active until the end of the current paid period, then the account moves to the free plan. "
        "Cancel from Manage Account, then the plan section, then Plan Settings, then Manage the plan, then Show, then Cancel the plan. "
        "This does not delete your account or your generations, and it does not automatically refund the current period. "
        "Plan credits remain usable until the paid period ends, then they expire. Credit Pack, Auto-Refill, promo, and Boost credits stay available on the free plan until their own expiry dates, and can be spent on the models the free plan includes."
    )
    cheapest_api = sorted(hf_api_rows, key=lambda r: (r["usd_per_second"], r["id"]))[0] if hf_api_rows else None
    q_api_cost = "What does the Higgsfield API cost?"
    if cheapest_api:
        a_api_cost = (
            f"Higgsfield's official API is billed pay-as-you-go, separately from plan credits. "
            f"In our catalog, the cheapest Higgsfield API row is {rate_money(cheapest_api['usd_per_second'])}/s "
            f"for {cheapest_api['model']} ({cheapest_api.get('variant') or 'listed rate'}, {shown_resolution(cheapest_api)}), "
            f"checked {checked_pt(cheapest_api.get('checked'))}. "
            "Other catalog API rows on this page include Wan 3.0 Prime, Wan 3.0, Kling 3.0, and Seedance 2.5 list rates from the official API pricing page. "
            "Those API list prices are not plan-sale prices. Affiliate links never change this price order."
        )
    else:
        a_api_cost = "Higgsfield's official API is billed pay-as-you-go. Catalog API rows were not available when this page was built."
    q_free = "Is Higgsfield free?"
    a_free = (
        f"Yes, there is a free plan. Official help, re-read {checked_pt(POLICY_CHECKED)}, says every new account starts on it at no cost. "
        "It opens a limited set of models, runs one generation at a time, does not include monthly credits or Unlimited models, "
        "and generations can carry a visible Higgsfield watermark. Models on the free plan still deduct credits, so you need credits or free generations already on the account to generate. "
        "Credit Packs cannot be bought on the free plan. Current plan prices and which models sit in the Free column are on Higgsfield's pricing page. "
        "A short dedicated page on whether Higgsfield is free is planned."
    )
    q_unknown = "What is confirmed, and what is not?"
    if live:
        _sale_st = f"live until {st['end']}"
        _unk_sale = "annual prices after the sale ends; whether the sale is extended; "
    else:
        _sale_st = f"ended {st['end']}"
        _unk_sale = "" if (six_a and nine_a) else "Ultra 6K and 9K annual prices after the sale; "
    a_unknown = (
        f"Confirmed {BF_CHECKED_WHEN} on Higgsfield's pricing page and pricing.md: plan prices in the table above, "
        f"business seat prices, Black Friday sale status ({_sale_st}), and Wan 3.0 credits per clip. "
        f"Other compare-table credits per clip were checked {checked_pt(CHECKED)}. The 11.11 sale ended at {SALE_ENDS_PT}. "
        f"Unknown: tax-inclusive checkout totals; {_unk_sale}when the Unlimited models for 7 days window starts; "
        "the five unnamed other unlimited models; published credit cost for Gemini Omni Flash or Runway Gen-4; "
        "Grok Video resolution; credit-pack list prices; and failed-generation refund rules for plan credits."
    )
    q5 = "How do we calculate this?"
    a5 = g["HOW_PLAIN"]
    faqs = [(q1, a1), (q2, a2), (q_credits_how, a_credits_how), (q3, a3), (q_api_cost, a_api_cost), (q4, a4), (q_refund, a_refund), (q_cancel, a_cancel), (q_free, a_free), (q_unknown, a_unknown), (q5, a5)]

    # Catalog plan table
    plan_head = (
        "<thead><tr><th>Plan</th><th>Billing</th><th>Credits / mo</th>"
        "<th>List</th><th>Sale / first payment</th><th>Renews at</th><th>Source</th></tr></thead>"
    )
    # Hand-built official plan rows (visible page + plans API), not invented.
    def sale_cell(deal_id, unit="/mo billed yearly"):
        v = deal_copy.price_after(st, deal_id) if live else None
        return f"{money(v)}{unit} until {st['end']}" if v is not None else "no sale"
    when = f"pricing page, {BF_CHECKED_WHEN}"
    official_plan_rows = [
        ("Starter", "monthly", f"{starter_c:,}", money(starter_m), "no sale", money(starter_m), when),
        ("Starter", "annual", f"{starter_c:,}", f"{money(starter_m)}/mo billed yearly", "no sale", f"{money(starter_m)}/mo billed yearly", when),
        ("Plus", "monthly", f"{plus_c:,}", money(plus_m), sale_cell("hf-plus-monthly-first", " first month"), money(plus_m), when),
        ("Plus", "annual", f"{plus_c:,}", f"{money(plus_m)}/mo (${plus_m*12:,}/yr)", sale_cell("hf-plus-annual"), "unknown after the sale" if live else f"{money(pa)}/mo billed yearly", when),
        ("Ultra 3K", "monthly", f"{ultra_c:,}", money(ultra_m), sale_cell("hf-ultra-monthly-first", " first month"), money(ultra_m), when),
        ("Ultra 3K", "annual", f"{ultra_c:,}", f"{money(ultra_m)}/mo (${ultra_m*12:,}/yr)", sale_cell("hf-ultra-annual"), "unknown after the sale" if live else f"{money(ua)}/mo billed yearly", when),
        ("Ultra 6K", "monthly", "6,000", "$250", sale_cell("hf-ultra-6k-monthly-first", " first month"), "$250", when),
        ("Ultra 6K", "annual", "6,000", "$258/mo billed yearly", sale_cell("hf-ultra-6k-annual"), "unknown after the sale" if live else f"{money(six_a)}/mo billed yearly", when),
        ("Ultra 9K", "monthly", "9,000", "$375", sale_cell("hf-ultra-9k-monthly-first", " first month"), "$375", when),
        ("Ultra 9K", "annual", "9,000", "$387/mo billed yearly", sale_cell("hf-ultra-9k-annual"), "unknown after the sale" if live else f"{money(nine_a)}/mo billed yearly", when),
        ("Team (per seat)", "monthly", "1,000 / seat", "$79", "$55", "$55", "pricing.md, " + BF_CHECKED_WHEN),
        ("Team (per seat)", "annual", "1,000 / seat", "$79/seat/mo", "$45/seat/mo billed yearly", "$45/seat/mo billed yearly", "pricing.md; 2–9 members"),
        ("Scale (per seat)", "monthly", "2,500 / seat", "$215", "$119.99 / seat/mo", "$119.99", "pricing.md; after business verification"),
        ("Scale (per seat)", "annual", "2,500 / seat", "$215/seat/mo", "$80/seat/mo billed yearly", "$80/seat/mo billed yearly", "pricing.md; 5–15 members"),
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
        plan_ids = {"hf-ultra-annual": "Ultra annual 3K", "hf-ultra-monthly": "Ultra monthly 3K",
                    "hf-plus-annual": "Plus annual", "hf-plus-monthly": "Plus monthly", "hf-starter": "Starter"}
        if r.get("plan") in plan_ids:
            return plan_ids[r["plan"]]
        for label, needle in (
            ("Ultra monthly 3K", "$129/mo"),
            ("Plus monthly", "$59/mo"),
            ("Starter", "$19/mo"),
        ):
            if needle in (r.get("math") or ""):
                return label
        return r.get("variant") or "Higgsfield plan"

    cat_head = (
        "<thead><tr><th>Seller</th><th>Model</th><th>Variant</th><th>Plan</th><th>Tier</th><th>Resolution</th><th>Audio</th>"
        "<th>$ / sec</th><th>Official clip</th><th>10s (if linear)</th><th>Status</th><th>Source and date checked</th></tr></thead>"
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
            f'<td>{plat_link(r["platform"], r["source_url"])}</td>'
            f'<td><a href="{root(f"/models/{r["model"]}/")}">{e(models.get(r["model"], {}).get("name") or r["model"])}</a></td>'
            f"<td>{e(r.get('variant') or '')}</td>"
            f"<td>{e(plan_label(r))}</td>"
            f'<td>{e(g["shown_tier"](r))}</td>'
            f"<td>{e(shown_resolution(r))}</td>"
            f"<td>{e(guide_tables.audio_label(g, r))}</td>"
            f'<td class="num"><span class="amt">{rate_money(r["usd_per_second"])}/s</span>{assumption_html(r)}</td>'
            f"<td>{e(official_clip_text(r))}</td>"
            f'<td class="num">{ten_s_cell(r)}</td>'
            f"<td>{status_cell(r)}</td>"
            f'<td>{source_toggle(r)} <span class="small">checked {e(checked_pt(r.get("checked")))}</span></td>'
            "</tr>"
        )
    cat_table = f'<div class="tblwrap fit" id="prices"><table>{cat_head}<tbody>{"".join(cat_rows_html)}</tbody></table></div>'

    # Derived Seedance 2.5 / Grok (not in catalog plan rows) from official credits × catalog plan credit prices.
    def credit_price(usd, credits):
        return usd / credits

    tag_sale = " (sale)" if live else ""
    derived_plans = [("Starter", starter_m, starter_c)]
    if pa:
        derived_plans.append((f"Plus annual{tag_sale}", pa, plus_c))
    derived_plans.append(("Plus monthly list", plus_m, plus_c))
    if ua:
        derived_plans.append((f"Ultra 3K annual{tag_sale}", ua, ultra_c))
    derived_plans.append(("Ultra 3K monthly list", ultra_m, ultra_c))
    if six_a:
        derived_plans.append((f"Ultra 6K annual{tag_sale}", six_a, 6000))
    if nine_a:
        derived_plans.append((f"Ultra 9K annual{tag_sale}", nine_a, 9000))
    derived_models = [x for x in OFFICIAL_CREDITS if x[0] in ("seedance-2-5", "grok-imagine")]
    der_head = (
        "<thead><tr><th>Seller</th><th>Model</th><th>Plan</th><th>Tier</th><th>Resolution</th><th>Audio</th><th>Official credits</th>"
        "<th>$/credit</th><th>Official clip</th><th>$/s (if linear)</th><th>10s (if linear, 5s unit)</th><th>Source and date checked</th></tr></thead>"
    )
    der_rows = []
    hf_plan_src = f'{src(HF_PRICING, "pricing page")}, checked {e(checked_pt(BF_CHECKED))}'
    for slug, name, credits, secs, tilde, res in derived_models:
        for plan_name, usd, cr in derived_plans:
            cprice = credit_price(usd, cr)
            clip = cprice * credits
            per_s = clip / secs
            ten = (cprice * credits / secs) * 10 if secs == 5 else "official unit is not 5s"
            credit_label = f"{'~' if tilde else ''}{credits:g} / {secs}s"
            ten_html = ten if isinstance(ten, str) else rate_money(ten)
            der_rows.append(
                "<tr>"
                "<td>Higgsfield</td>"
                f"<td>{e(name)}</td><td>{e(plan_name)}</td><td>not listed</td><td>{e(res or 'not stated')}</td><td>not stated</td><td>{e(credit_label)}</td>"
                f'<td class="num">{rate_money(cprice)}</td>'
                f'<td class="num">{rate_money(clip)}</td>'
                f'<td class="num">{rate_money(per_s)}</td>'
                f'<td class="num">{ten_html}</td>'
                f'<td class="small">{hf_plan_src}</td>'
                "</tr>"
            )
    der_table = f'<div class="tblwrap fit"><table>{der_head}<tbody>{"".join(der_rows)}</tbody></table></div>'

    # PAYG comparison: cheapest catalog HF plan $/s vs cheapest verified non-HF API at same model+res.
    cmp_head = (
        "<thead><tr><th>Model</th><th>Resolution</th><th>Audio</th><th>Cheapest HF plan in catalog</th>"
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
            other_txt = (
                f"{rate_money(o['usd_per_second'])}/s on {o['platform']} "
                f"({o['variant']}, {guide_tables.plan_label(o)}, tier {g['shown_tier'](o)}, "
                f"{guide_tables.audio_label(g, o)}, checked {checked_pt(o.get('checked'))})"
            )
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
            f"<td>{e(guide_tables.audio_label(g, hf_best))}</td>"
            f'<td class="num">{rate_money(hf_best["usd_per_second"])}/s · {e(plan_label(hf_best))} · tier {e(g["shown_tier"](hf_best))} (checked {e(checked_pt(hf_best.get("checked")))})</td>'
            f"<td>{e(other_txt)}</td>"
            f"<td>{e(winner)}</td>"
            "</tr>"
        )
    cmp_table = f'<div class="tblwrap fit"><table>{cmp_head}<tbody>{"".join(cmp_rows)}</tbody></table></div>'

    api_head = (
        "<thead><tr><th>Seller</th><th>Model</th><th>Plan</th><th>Tier</th><th>Resolution</th><th>Audio</th><th>Higgsfield API $/s</th><th>Status</th><th>Source and date checked</th></tr></thead>"
    )
    api_body = "".join(
        "<tr>"
        f'<td>{plat_link(r["platform"], r["source_url"])}</td>'
        f"<td>{e(models.get(r['model'], {}).get('name') or r['model'])}</td>"
        f'<td>{e(guide_tables.plan_label(r))}</td>'
        f'<td>{e(g["shown_tier"](r))}</td>'
        f"<td>{e(shown_resolution(r))}</td>"
        f"<td>{e(guide_tables.audio_label(g, r))}</td>"
        f'<td class="num">{rate_money(r["usd_per_second"])}</td>'
        f"<td>{status_cell(r)}</td>"
        f'<td>{source_toggle(r)} <span class="small">checked {e(checked_pt(r.get("checked")))}</span></td>'
        "</tr>"
        for r in sorted(hf_api_rows, key=lambda r: (r["usd_per_second"], r["id"]))
    )
    api_table = (
        f'<div class="tblwrap fit"><table>{api_head}<tbody>{api_body}</tbody></table></div>'
        if hf_api_rows else "<p>No Higgsfield API rows are in the catalog.</p>"
    )

    if live:
        promo_tail = (f"The annual sale cards do not print a post-sale price, so what annual billing costs after the sale ends ({st['end']}) is not confirmed. "
                      f"The 11.11 sale already ended at {SALE_ENDS_PT}.")
        sale_status = f"live until {st['end']}"
        unknown_sale = "annual prices after the sale ends; whether the sale is extended; "
    else:
        promo_tail = deal_copy.hf_sale_sentence(st) + f" The 11.11 sale ended at {SALE_ENDS_PT}."
        sale_status = f"ended {st['end']}"
        unknown_sale = "" if (six_a and nine_a) else "Ultra 6K and 9K annual prices after the sale; "
    derived_tail = ("plus Ultra 6K annual and Ultra 9K annual. Ultra 9K annual has the lowest credit price of those plans."
                    if (six_a and nine_a) else "Ultra 6K and 9K annual are left out until their post-sale prices are confirmed.")
    lead = (
        f"Higgsfield’s current individual and business plan prices are taken from the official pricing page, re-read {BF_CHECKED_WHEN}. "
        + deal_copy.hf_sale_sentence(st) + " " +
        f"The lowest Higgsfield plan rate already in this catalog is {rate_money(best_plan['usd_per_second'])}/s "
        f"({best_plan['variant']}, {shown_resolution(best_plan)}), assuming every paid credit is used. "
        "Unlimited bonuses apply only on higgsfield.ai. Affiliate links never change this price order."
    )

    takeaways = f"""<div class="card" id="takeaways">
<h2>Key takeaways</h2>
<ul>
<li><b>Lowest Higgsfield plan rate we track.</b> {e(rate_money(best_plan['usd_per_second']))}/s on {e(plan_label(best_plan))} for {e(models.get(best_plan['model'], {}).get('name') or best_plan['model'])} ({e(shown_resolution(best_plan))}, {e(guide_tables.audio_label(g, best_plan))}), checked {e(checked_pt(best_plan.get('checked')))}.</li>
<li><b>Individual list &amp; current annual plans.</b> Starter {money(starter_m)}/mo ({starter_c:,} credits); Plus {money(plus_m)}/mo monthly ({money(pa)}/mo annual, {plus_c:,} credits); Ultra 3K {money(ultra_m)}/mo monthly ({money(ua)}/mo annual, {ultra_c:,} credits).</li>
<li><b>Black Friday sale status.</b> {e(deal_copy.hf_sale_sentence(st))}</li>
<li><b>Unlimited bonuses.</b> Apply only on higgsfield.ai (never MCP/CLI, Canvas, or Supercomputer) and only while the paid plan stays active.</li>
</ul>
</div>"""

    body = f"""<p class="small"><a href="{root("/guides/")}">Guides</a> › Higgsfield pricing</p>
<h1>{e(PHRASE)}</h1>
<p class="lead">{lead}</p>
{g["checked_line"]()}
<p>Related: <a href="{root("/guides/higgsfield-black-friday/")}">Higgsfield Black Friday 2026: what you save per second</a> · <a href="{root("/guides/is-higgsfield-worth-it/")}">Is Higgsfield worth it?</a> · <a href="{root("/guides/seedance-2-5-unlimited/")}">Unlimited Seedance 2.5 plans compared</a> · <a href="{root("/guides/kling-ai-pricing/")}">Kling AI pricing and credits</a> · <a href="{root("/calculator/")}">credit calculator</a>.</p>
{takeaways}

<h2>Higgsfield catalog per-second prices</h2>
<p>Every Higgsfield plan row in data/prices.json, sorted cheapest first, split by resolution and audio, with plan, tier, usage assumption, and source. Affiliate links never change this price order.</p>
{cat_table}

<h2>{e(q1)}</h2>
<p>{e(a1)} Sources: {src(HF_PRICING, "higgsfield.ai/pricing")} (Individual Annual / Monthly and Business tabs, re-read {checked_pt(BF_CHECKED)}), the public plans API that page loads, and {src(HELP_PLANS, "How do Higgsfield plans work?")}.</p>
{plan_table}
<p class="small">Dollar amounts are US list prices as shown, before VAT and local taxes. Team and Scale cards default to 5 seats; Team allows 2–9 members and Scale 5–15. Bonus business credits expire in 30 days and are not included in the credit-price math below. Unused first-month credits roll over on Team and Scale, per the cards.</p>

<h2>{e(q2)}</h2>
<p>{e(a2)} Source: the Video category of the compare table on {src(HF_PRICING, "higgsfield.ai/pricing")}, from the compare API that page loads, checked {checked_pt(CHECKED)}.</p>
<h2>{e(q_credits_how)}</h2>
<p>{e(a_credits_how)} Sources: {src(HELP_CREDITS, "How do credits work?")}, {src(HELP_EXPIRE, "Do my top-up credits expire, and what happens if I cancel?")}, and {src(HELP_PACKS, "How do Credit Packs work?")}, re-read {e(checked_pt(POLICY_CHECKED))}. Current sale prices for paid plans are in the plan table above and on the <a href="{root("/deals/")}">live deals page</a>; they are not repeated here.</p>
<p>The catalog already converts those official (or official-estimate) credit figures into $/s for Starter, Plus, and Ultra 3K in the <a href="#prices">dated Higgsfield per-second table at the top of this guide</a>, using each plan’s dollars and credits and assuming every paid credit is used.</p>
<p>Seedance 2.5 and Grok are on the official compare table but do not have Higgsfield plan rows in the catalog (Seedance 2.5 on plans was left out of earlier guides for the same reason; Grok Video has no stated resolution). The next table applies the same credit-use math to the official credits and to the Starter / Plus / Ultra 3K catalog plan prices, {e(derived_tail)} These derived figures are not catalog rows.</p>
{der_table}
<p class="small">Kling 3.0 720p and 1080p stay catalog estimates: the compare table labels them “~7” and “~8” credits/5s, while the same table’s annual video counts divide to 7.5 and about 8.75. No existing catalog dollar amount was changed.</p>

<h2>{e(q3)}</h2>
<p>{e(a3)}</p>
{cmp_table}
<p>Higgsfield API pay-as-you-go, from {src(HF_API, "open.higgsfield.ai/pricing")} and the catalog rows last checked {checked_pt(CHECKED)} (the API “from” figures for Wan 3.0, Kling 3.0, and Seedance 2.5 on that index on that date matched these rows; the cheapest mode’s resolution is still not stated for the “from” list prices):</p>
{api_table}
<p class="small">Affiliate links never change this price order.</p>
<h2>{e(q_api_cost)}</h2>
<p>{e(a_api_cost)} Source: {src(HF_API, "open.higgsfield.ai/pricing")} and the catalog API rows in the table above. These are list API rates, not Black Friday plan-sale prices.</p>

<h2>{e(q4)}</h2>
<p>{e(a4)} Sources: {src(HELP_UNLIM, "What are Unlimited models?")}, the pricing-page footer and plan cards on {src(HF_PRICING, "higgsfield.ai/pricing")}, re-read {checked_pt(BF_CHECKED)}, and the ended 11.11 sale record checked {checked_pt(CHECKED)}.</p>
<p>The same help article describes a longer “365 Unlimited” style of access on mid and top plans: generations on listed models do not deduct credits for a stated period, only while the paid plan stays active, and only on higgsfield.ai. Plus and Ultra cards also say “5 other unlimited models” without naming them on the card. This guide does not invent those five names or treat any Unlimited window as $0/s.</p>
<p>{src(HELP_PROMO, "How promo prices work")} says a promo price applies to the first payment or the period stated in the offer, and that the plan then renews at the standard price. Monthly Plus and Ultra first-month cards already print the renewal list price. {e(promo_tail)}</p>

<h2>{e(q_refund)}</h2>
<p>{e(a_refund)} Sources: {src(HELP_REFUND, "How do I request a refund?")} and {src(HELP_CANCEL, "How do I cancel my subscription?")}, re-read {e(checked_pt(POLICY_CHECKED))}. The full terms are also in Section 9.3 of Higgsfield's Terms of Use, linked from that help article. Consumers in the EEA or UK may have a 14-day withdrawal window, per the same refund article.</p>

<h2>{e(q_cancel)}</h2>
<p>{e(a_cancel)} The official menu labels are “Subscription,” “Manage Subscription,” and “Cancel Subscription.” Source: {src(HELP_CANCEL, "How do I cancel my subscription?")}, re-read {e(checked_pt(POLICY_CHECKED))}. Team, Scale, and Enterprise plans are cancelled by the workspace Owner from Organization settings, per that article. Canceling and refunding are separate actions.</p>

<h2>{e(q_free)}</h2>
<p>{e(a_free)} Source: {src(HELP_FREE, "What does the Higgsfield free plan include?")}, re-read {e(checked_pt(POLICY_CHECKED))}.</p>

<h2>{e(q_unknown)}</h2>
<p>{e(a_unknown)}</p>
<p><b>Confirmed {e(BF_CHECKED_WHEN)} on Higgsfield’s own pricing page and pricing.md:</b> the plan prices in the table above, the business seat prices, the Black Friday sale status and the end time in its sale record ({e(sale_status)}), and the Wan 3.0 credits per clip. Other credits per clip in the compare table were checked {checked_pt(CHECKED)}. The 11.11 sale ended at {SALE_ENDS_PT}. Catalog dollar-per-second rows use the plan prices last checked {LAST}. Higgsfield API “from” list prices were last checked {checked_pt(CHECKED)}.</p>
<p><b>Unknown:</b> tax-inclusive checkout totals; {e(unknown_sale)}when the “Unlimited models for 7 days” window starts; the five unnamed “other” unlimited models on the Plus/Ultra cards; a published credit cost or Higgsfield plan $/s for Gemini Omni Flash or Runway Gen-4; the resolution of “Grok Video”; credit-pack list prices; a failed-generation refund rule for plan credits. Invented figures are not shown for those gaps.</p>

{g["how_block"]()}
"""

    title = g["page_title"](PHRASE)
    desc = description(g)
    g["guide_page"](PATH, title, desc, body, faqs)
    return PATH
