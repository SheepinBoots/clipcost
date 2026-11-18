"""Guide: Higgsfield promo codes and current deals (a living page).

Imported by scripts/build_site.py. Only codes and deals from Higgsfield's own
pages or official accounts are listed. Every entry carries its source link,
the end date exactly as the source states it (or "end date not stated"), and
the time it was last checked. No code is ever invented. When a deal ends,
move it to EXPIRED with the date it ended. This page never names the banned
model.
"""

PATH = "/guides/higgsfield-promo-code/"
LABEL = "Higgsfield promo codes"
PHRASE = "Higgsfield promo code and current deals"
QUESTION = "Is there a Higgsfield promo code right now?"
CHECKED = "2026-11-17"
CHECKED_WHEN = "Nov 17, 2026, 8:16 PM America/Caracas (4:16 PM PT)"
RECHECK_WHEN = "Nov 17, 2026, 8:16 PM America/Caracas (4:16 PM PT)"
COUNTDOWN_READ = (
    "47 hours, 43 minutes at 4:16 PM PT (8:16 PM America/Caracas) on Nov 17, 2026"
)
# As the pricing page's embedded sale record (source "sale_11_11", phase "pre_black_friday_64") states it.
BF_ENDS_UTC = "2026-11-20T00:00:00Z"
BF_ENDS_LOCAL = "Nov 19, 2026, 4:00 PM PT; 8:00 PM America/Caracas"
KLING4_ENDS_UTC = "2026-10-29T00:00:00Z"
KLING4_ENDS_LOCAL = "Oct 28, 2026, 5:00 PM PT; 8:00 PM America/Caracas"

PRICING = "https://higgsfield.ai/pricing"
HELP_CODES = "https://higgsfield.ai/creator-hub/help-center/credits/how-promo-codes-work"
HELP_PROMO_PRICES = "https://higgsfield.ai/creator-hub/help-center/plans/how-do-promo-prices-work"
CHANGELOG = "https://higgsfield.ai/creator-hub/changelog"
BLOG_1111 = "https://higgsfield.ai/blog/higgsfield-11-11-deals"
MCP_PAGE = "https://higgsfield.ai/mcp"
X_HF_AI = "https://x.com/higgsfield_ai"
X_HF = "https://x.com/higgsfield"
X_MCP_TRIAL = "https://x.com/higgsfield/status/2120536193612087536"
X_GENJUTSU = "https://x.com/higgsfield_ai/status/2109681164806177267"

# Current entries. Each one: title, what you get, code, end as stated, source, last checked.
CURRENT = [
    {
        "id": "bf-annual",
        "title": "Black Friday sale: annual plans",
        "offer": "Plus $33/mo billed yearly (was $59, card says −45%, “Save $312”). Ultra 3K $50/mo billed yearly (was $129, −60%, “Save $948”). Ultra 6K $95/mo billed yearly (card shows $258 crossed out, −63%, “Save $1,860”). Ultra 9K $136/mo billed yearly (was $387, −64%, “Save $2,868”). Starter stays $19/mo.",
        "code": "No code. The price is on the plan card.",
        "ends": "Ends " + BF_ENDS_UTC + " (" + BF_ENDS_LOCAL + "), the end time in the sale record embedded in the pricing page. The page itself shows only a countdown, which read " + COUNTDOWN_READ + ", matching that time. Vendors sometimes extend sales.",
        "source": (PRICING, "Higgsfield pricing page"),
        "checked": RECHECK_WHEN,
    },
    {
        "id": "monthly-first",
        "title": "First month off on monthly plans",
        "offer": "Plus $47 for the first month, “renews at $59” (20% off). Ultra 3K $79, “renews at $129” (40% off). Ultra 6K $150, “renews at $250” (40% off). Ultra 9K $209, “renews at $375” (45% off).",
        "code": "No code. The price is on the plan card.",
        "ends": "The official sale record ends at " + BF_ENDS_UTC + " (" + BF_ENDS_LOCAL + "). The monthly cards print the renewal list price but do not print a separate calendar end.",
        "source": (PRICING, "Higgsfield pricing page, Monthly tab"),
        "checked": RECHECK_WHEN,
    },
    {
        "id": "business-monthly",
        "title": "Business plans, monthly",
        "offer": "Team $55 per seat a month (was $79, 30% off, 5 seats shown). Scale $120 per seat a month (was $215, 45% off). The Business tab banner says “Up to 63% OFF.” Billed yearly, the plan data the pricing page loads lists Team at $45 per seat a month (43% off) and Scale at $80 a month (63% off).",
        "code": "No code. The price is on the plan card.",
        "ends": "End date not stated.",
        "source": (PRICING, "Higgsfield pricing page, Business plans tab"),
        "checked": RECHECK_WHEN,
    },
    {
        "id": "referral",
        "title": "Discount through a referral link",
        "offer": "Higgsfield’s affiliate program terms say “anyone who signs up through your link gets up to 50% off for three hours.” Whether that combines with the Black Friday prices is not stated. VidFare’s Higgsfield links are referral links of this kind.",
        "code": "No code. It applies through the link.",
        "ends": "End date not stated. The changelog entry gives the “Terms as of August 24, 2026.”",
        "source": (CHANGELOG, "Higgsfield changelog, Aug 24, 2026 (Affiliate Program)"),
        "checked": CHECKED_WHEN,
    },
]

# Ended, or not confirmed as current. Kept so a reader can see why it is not above.
EXPIRED = [
    {
        "title": "11.11 sale (up to 60% off, first-month offers)",
        "status": "Expired",
        "ends": "Ended. The first-month offers ended Nov 15, 2026 in our deal record; the public sale record ended at 2026-11-15T00:00:00Z (Nov 14, 2026, 4:00 PM PT).",
        "source": (BLOG_1111, "Higgsfield 11.11 deals blog post"),
        "checked": CHECKED_WHEN,
    },
    {
        "title": "Wan 3.0 on the API, 60% off",
        "status": "Expired",
        "ends": "“until October 31, 2026,” as the Oct 13, 2026 changelog entry states.",
        "source": (CHANGELOG, "Higgsfield changelog, Oct 13, 2026"),
        "checked": CHECKED_WHEN,
    },
    {
        "title": "Genjutsu API, 50% off",
        "status": "Expired",
        "ends": "“through Oct 31 2026,” as the official post states.",
        "source": (X_GENJUTSU, "@higgsfield_ai post"),
        "checked": CHECKED_WHEN,
    },
    {
        "title": "Free 72-hour Higgsfield MCP trial",
        "status": "Not confirmed current",
        "ends": "End date not stated. Posted Nov 10–11, 2026; after 72 hours the post says it renews to Ultra with 40% off the first month unless you cancel. The MCP page did not show the trial on Nov 17, 2026.",
        "source": (X_MCP_TRIAL, "@higgsfield post, Nov 11, 2026"),
        "checked": CHECKED_WHEN,
    },
    {
        "title": "Kling 4.0 launch discount",
        "status": "Expired",
        "ends": "Ended " + KLING4_ENDS_UTC + " (" + KLING4_ENDS_LOCAL + "), the end time in the launch record (“kling_4_release”) embedded in Higgsfield’s pricing page. The Oct 21, 2026 changelog only says “a launch discount is applied for a limited time.”",
        "source": (PRICING, "Higgsfield pricing page (embedded launch record)"),
        "checked": RECHECK_WHEN,
    },
]


def _src(g, url, text="source"):
    e = g["e"]
    href, rel = g["outbound"](url)
    return f'<a href="{e(href)}" rel="{rel}" target="_blank">{e(text)}</a>'


def _row(g, rid):
    for r in g["rows"]:
        if r["id"] == rid:
            return r
    raise SystemExit(f"{PATH} missing catalog row {rid}")


def _pretty(date):
    months = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    y, m, d = (int(x) for x in date.split("-"))
    return f"{months[m - 1]} {d}, {y}"


def blurb(g):
    return (
        "No public Higgsfield promo code on its official pages or accounts. The current "
        "deals, each with its source, stated end date, and last check."
    )


def description(g):
    text = (
        f"Higgsfield promo code: no public code found. Current deals from Higgsfield’s own "
        f"pages, each with its source and stated end date. Last checked {_pretty(CHECKED)}."
    )
    if len(text) > 160:
        raise SystemExit(f"{PATH} meta description is over 160 characters: {len(text)}")
    return text


def render(g):
    e, root, LAST = g["e"], g["root"], g["LAST"]
    rate_money = g["rate_money"]
    g["SITEMAP_LASTMOD"][PATH] = max(CHECKED, LAST)

    def src(url, text="source"):
        return _src(g, url, text)

    pricing = src(PRICING, "Higgsfield’s pricing page")
    help_codes = src(HELP_CODES, "How do promocodes work?")
    help_prices = src(HELP_PROMO_PRICES, "How do promo prices work?")
    changelog = src(CHANGELOG, "Higgsfield changelog")
    x_ai = src(X_HF_AI, "@higgsfield_ai")
    x_hf = src(X_HF, "@higgsfield")
    bf_href = root("/guides/higgsfield-black-friday/")
    pricing_href = root("/guides/higgsfield-pricing/")
    worth_href = root("/guides/is-higgsfield-worth-it/")
    kling_href = root("/guides/cheapest-kling-3-0/")
    deals_href = root("/deals/")
    calc_href = root("/calculator/?model=kling-3-0&seconds=10")

    # Kling 3.0 at 720p, audio not stated, as a per-second example of each plan price.
    r109 = _row(g, "r109")  # Plus annual
    r111 = _row(g, "r111")  # Ultra annual
    r110 = _row(g, "r110")  # Plus monthly, list
    r112 = _row(g, "r112")  # Ultra monthly, list
    for r, usd in ((r109, 33), (r111, 50), (r110, 59), (r112, 129)):
        plan = (g["db"].get("plans") or {}).get(r.get("plan")) or {}
        if plan and float(plan.get("usd_month") or 0) != float(usd):
            raise SystemExit(f"{PATH} copy assumes {r['plan']} is ${usd}/mo; catalog says {plan.get('usd_month')}")
    credits_clip = 7.5
    six_k = 95.0 / 6000 * credits_clip / 5
    nine_k = 136.0 / 9000 * credits_clip / 5
    plus_first = 47.0 / 1200 * credits_clip / 5
    ultra_first = 79.0 / 3000 * credits_clip / 5

    def example(entry_id):
        if entry_id == "bf-annual":
            return (
                f"Plus annual {e(rate_money(r109['usd_per_second']))}/s (catalog row r109); "
                f"Ultra 3K annual {e(rate_money(r111['usd_per_second']))}/s (row r111); "
                f"Ultra 6K annual {e(rate_money(six_k))}/s, computed from the $95 card and 6,000 credits; Ultra 9K annual {e(rate_money(nine_k))}/s, computed from the $136 card and 9,000 credits. Neither is a catalog row."
            )
        if entry_id == "monthly-first":
            return (
                f"First month only: Plus {e(rate_money(plus_first))}/s, Ultra 3K {e(rate_money(ultra_first))}/s, computed, not catalog rows. "
                f"After it renews: Plus {e(rate_money(r110['usd_per_second']))}/s (row r110), Ultra 3K {e(rate_money(r112['usd_per_second']))}/s (row r112)."
            )
        if entry_id == "referral":
            return "Not computed. The terms say “up to 50%” without a per-plan price."
        return "Not computed. The seat price and per-seat credits do not map to one clip rate."

    def trow(*cells):
        return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"

    cur_rows = []
    for d in CURRENT:
        url, label = d["source"]
        cur_rows.append(trow(
            f"<b>{e(d['title'])}</b>",
            e(d["offer"]),
            e(d["code"]),
            e(d["ends"]),
            example(d["id"]),
            src(url, label),
            e(d["checked"]),
        ))
    current_table = f"""<div class="tblwrap" id="prices"><table style="min-width:1250px;width:1250px">
<thead><tr>
<th>Deal and tier</th>
<th>What you get</th>
<th>Code</th>
<th>Ends, as the source states it</th>
<th>Example: Kling 3.0 at 720p, audio not stated</th>
<th>Source</th>
<th>Last checked</th>
</tr></thead>
<tbody>{''.join(cur_rows)}</tbody></table></div>"""

    old_rows = []
    for d in EXPIRED:
        url, label = d["source"]
        old_rows.append(trow(
            f"<b>{e(d['title'])}</b>",
            e(d["status"]),
            e(d["ends"]),
            src(url, label),
            e(d["checked"]),
        ))
    expired_table = f"""<div class="tblwrap" id="expired-deals"><table style="min-width:1000px;width:1000px">
<thead><tr>
<th>Deal</th>
<th>Status</th>
<th>End, as the source states it</th>
<th>Source</th>
<th>Last checked</th>
</tr></thead>
<tbody>{''.join(old_rows)}</tbody></table></div>"""

    a_q = (
        "No. We found no public Higgsfield promo code on Higgsfield’s pricing page, help center, "
        "changelog, or its official X accounts @higgsfield_ai and @higgsfield, checked Nov 17, 2026, "
        "4:16 PM PT. The current discount needs no code: Higgsfield’s Black Friday prices are on "
        "the plan cards, with Plus at $33 a month and Ultra 3K at $50 a month, billed yearly, Ultra "
        "6K at $95, and Ultra 9K at $136. Higgsfield’s help center says promo codes are announced on its official social "
        "channels first, handed out at Discord community events, or issued case by case by Support. "
        "This page lists no code until one appears on an official channel."
    )
    a_discount = (
        "Not a code. The Black Friday sale is applied on the pricing page itself: up to 64% off, with "
        "Plus annual at $33 a month (was $59), Ultra 3K annual at $50 (was $129), Ultra 6K annual "
        "at $95, and Ultra 9K annual at $136 (was $387). Monthly plans show a first-month price instead: Plus $47, then $59; Ultra 3K $79, then "
        "$129. Prices exclude VAT and local taxes, which are added at checkout."
    )
    a_end = (
        "The sale record embedded in Higgsfield’s pricing page ends at 2026-11-20T00:00:00Z, which is "
        "Nov 19, 2026, 4:00 PM PT (8:00 PM America/Caracas). The page itself prints no date, only a "
        "countdown, which read 47 hours, 43 minutes at 4:16 PM PT on Nov 17, 2026, matching that time. "
        "The record is labelled as a pre-Black Friday phase (pre_black_friday_64), and vendors sometimes extend sales, so "
        "check the pricing page before you buy."
    )
    a_how = (
        "Sign in, click your avatar, choose Manage Account, open Promocode in the left sidebar, select "
        "Enter code, and type the code exactly, with no extra spaces. Higgsfield says the benefit is "
        "applied instantly and the page then shows the discount and any credits added. One code means "
        "one activation unless its terms say otherwise. Promo credits expire on the date shown when they "
        "are added, and Support codes expire if they are not activated within 7 days."
    )
    a_where = (
        "From Higgsfield itself. Its help center names three sources: marketing promos announced on its "
        "official social media channels first, codes for active participants in Higgsfield Discord "
        "community events, and Support promos issued case by case, which cannot be requested. A code "
        "on a coupon site that does not appear on one of those channels is not listed here."
    )
    a_renew = (
        "No. Higgsfield’s help center says a promo price applies to the first payment or the period "
        "stated in the offer, and the plan then renews at the standard price. Its Nov 11, 2026 "
        "changelog says a sale discount covers the first year of an annual plan or the first month of "
        "a monthly one. The monthly cards say so directly, for example Plus at $47 “renews at $59.” "
        "For annual plans the sources disagree: the plan data the pricing page loads lists the annual "
        "discount as lasting “forever,” with a renewal price equal to the sale price. What an annual "
        "plan renews at after its first year is not confirmed."
    )
    a_old = (
        "The 11.11 sale ended, with its first-month offers ending Nov 15, 2026. The Kling 4.0 launch "
        "discount ended at 2026-10-29T00:00:00Z (Oct 28, 2026, 5:00 PM PT). The Wan 3.0 API 60% off "
        "ended October 31, 2026, and the Genjutsu API 50% off ended Oct 31, 2026. A free 72-hour MCP "
        "trial posted Nov 10–11 is not confirmed as current, so it is not listed as a live deal."
    )

    faqs = [
        (QUESTION, a_q),
        ("Is there a Higgsfield AI discount code for Black Friday?", a_discount),
        ("When does the Higgsfield Black Friday sale end?", a_end),
        ("How do I use a Higgsfield promo code?", a_how),
        ("Where do real Higgsfield promo codes come from?", a_where),
        ("Does the discount last after the first payment?", a_renew),
        ("Which Higgsfield deals have ended?", a_old),
    ]
    for q, a in faqs:
        raw = (q + " " + a).lower()
        for bad in ("subscribe", "newsletter", "buttondown"):
            if bad in raw:
                raise SystemExit(f"{PATH} FAQ text contains {bad}")

    lead = (
        f"There is no public Higgsfield promo code on Higgsfield’s own pages or official accounts right "
        f"now. The current discount needs no code: Black Friday prices are on the plan cards on "
        f"{pricing}, with Plus at $33 a month and Ultra 3K at $50 a month, billed yearly. The sale "
        f"record on that page ends Nov 19, 2026, 4:00 PM PT (2026-11-20T00:00:00Z), unless Higgsfield "
        f"extends it. Every deal below has its source, its end date exactly as "
        f"the source states it, and when we last checked it, {e(CHECKED_WHEN)}."
    )

    takeaways = f"""<div class="card" id="takeaways">
<h2>Key takeaways</h2>
<ul>
<li><b>No public code.</b> None on Higgsfield’s pricing page, help center, changelog, {x_ai}, or {x_hf}, checked {e(CHECKED_WHEN)}.</li>
<li><b>No code needed for the sale.</b> Plus $33/mo, Ultra 3K $50/mo, Ultra 6K $95/mo, Ultra 9K $136/mo, billed yearly, before tax.</li>
<li><b>Ends Nov 19, 4:00 PM PT.</b> That is 2026-11-20T00:00:00Z (8:00 PM America/Caracas), from the sale record in the pricing page; the visible countdown matches. Vendors sometimes extend sales.</li>
<li><b>Renewals.</b> Monthly sale prices cover the first month, then renew at the standard price. For annual plans, the help center says standard price after the first year, but the plan data lists the discount as “forever,” so that is not confirmed.</li>
<li><b>Per second.</b> At the sale price, Kling 3.0 at 720p works out to {e(rate_money(r111['usd_per_second']))}/s on Ultra 3K annual if you use every credit.</li>
</ul>
</div>"""

    next_steps = f"""<div class="card" id="next-steps">
<h2>What to do next</h2>
<ul>
<li><b>Check the vendor page.</b> Sale prices and countdowns change without notice. Confirm the price on {pricing} before you buy.</li>
<li><b>Try the calculator.</b> See what a plan costs per clip when you do not use every credit: <a href="{e(calc_href)}">credit calculator for a 10-second Kling 3.0 clip</a>.</li>
<li><b>Open the model page.</b> Compare the sale rate with every other route on the <a href="{e(root('/models/kling-3-0/'))}">Kling 3.0 model page</a>, or see <a href="{e(kling_href)}">where Kling 3.0 is cheapest</a>.</li>
</ul>
</div>"""

    body = f"""<p class="small"><a href="{root("/guides/")}">Guides</a> › Higgsfield promo codes</p>
<h1>{e(PHRASE)}</h1>
<p class="lead">{lead}</p>
<p class="small">Last checked {e(LAST)}. Higgsfield’s pages and official accounts were read {e(CHECKED_WHEN)}. This is a living page: when a deal ends it moves to the ended list, and a code is added only after it appears on an official Higgsfield channel.</p>
{takeaways}

<h2>{e(QUESTION)}</h2>
<p>{e(a_q)}</p>
<p>Checked: {pricing} · {help_codes} · {help_prices} · {changelog} · {x_ai} and {x_hf} posts since Nov 1, 2026.</p>

<h2>Current Higgsfield deals</h2>
<p>Only deals from Higgsfield’s own pages or official accounts. Each per-second example is Kling 3.0 at 720p, audio not stated, and assumes every credit you pay for is used, at about 7.5 credits per 5-second clip (Higgsfield labels it ~7). Prices exclude VAT and local taxes, which Higgsfield adds at checkout.</p>
{current_table}
<p class="small">The Ultra 6K annual card shows $258 crossed out, while 12 × ($258 − $95) would be $1,956, not the “Save $1,860” on the same card; the monthly 6K list price is $250. Both figures are copied as shown. Per-second rates for every model on the sale are in <a href="{e(bf_href)}">Higgsfield Black Friday 2026: what you save per second</a>.</p>

<h2>Is there a Higgsfield AI discount code for Black Friday?</h2>
<p>{e(a_discount)}</p>

<h2>When does the Higgsfield Black Friday sale end?</h2>
<p>{e(a_end)}</p>

<h2>How do I use a Higgsfield promo code?</h2>
<p>{e(a_how)} Source: {help_codes}, dated Aug 3, 2026.</p>

<h2>Where do real Higgsfield promo codes come from?</h2>
<p>{e(a_where)} Source: {help_codes}.</p>

<h2>Does the discount last after the first payment?</h2>
<p>{e(a_renew)} Sources: {help_prices}, dated Aug 1, 2026 · {changelog}, Nov 11, 2026. What each plan costs at its standard price is in <a href="{e(pricing_href)}">Higgsfield pricing explained</a> and <a href="{e(worth_href)}">is Higgsfield worth it?</a>. To compare other tools by cost per second, see <a href="{e(root("/guides/higgsfield-alternatives/"))}">Higgsfield alternatives</a>.</p>

<h2>Which Higgsfield deals have ended?</h2>
<p>{e(a_old)}</p>
{expired_table}

<h2>Affiliate disclosure</h2>
<p>Higgsfield links on this page are affiliate links (parameter <code>fpr=emmanuel-bbfe0e</code>) and use <code>rel="sponsored nofollow"</code>. If you buy through one, VidFare may earn a commission, at no extra cost to you. That never decides which deals are listed or their order. Every live deal we track, from every vendor, is on the <a href="{e(deals_href)}">deals page</a>.</p>

<h2>What is confirmed, and what is not?</h2>
<p><b>Confirmed {e(CHECKED_WHEN)}:</b> the annual and monthly plan card prices above, the Business monthly seat prices, the Ultra 9K prices, the sale end time and the Kling 4.0 launch end time in the page’s embedded records (re-read {e(RECHECK_WHEN)}), the countdown reading, the help center’s promocode steps and renewal rule, the changelog entries, and the official X posts linked here. <b>Unknown:</b> whether the sale is extended past its stated end; what an annual plan renews at after the first year; the Business annual prices as shown on the cards (we read them from the plan data only); the tax-inclusive checkout total; whether the referral discount combines with the sale; whether the MCP trial is still offered; and any code shared privately on Discord or by Support.</p>
{next_steps}
{g["how_block"]()}
"""

    if "sora" in body.lower() or "sora" in description(g).lower() or "sora" in PHRASE.lower():
        raise SystemExit(f"{PATH} source would name the banned model")
    title = g["page_title"](PHRASE)
    desc = description(g)
    g["guide_page"](PATH, title, desc, body, faqs)
    return PATH
