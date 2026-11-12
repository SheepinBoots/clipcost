"""Guide: The cheapest way to use Seedance 2.5.

Imported by scripts/build_site.py. Every ranked dollars-per-second figure
comes from data/prices.json (checked rows) or, for live unlimited windows,
from data/deals.json via seedance_unlimited_guide.live_windows. Extra
vendor-page facts that are not catalog rows are labeled as such and cited.
"""
import seedance_unlimited_guide as unlimited

PATH = "/guides/cheapest-seedance-2-5/"
LABEL = "Cheapest Seedance 2.5"
PHRASE = "The cheapest way to use Seedance 2.5"
QUESTION = "What is the cheapest way to use Seedance 2.5?"
MODEL = "seedance-2-5"
UNLIMITED_PATH = "/guides/seedance-2-5-unlimited/"
RES_ORDER = {"480p": 0, "720p": 1, "1080p": 2}

# Official pages checked for this guide on 2026-11-12 PT.
HF_API = "https://open.higgsfield.ai/pricing"
HF_PLANS = "https://higgsfield.ai/pricing"
MAG = "https://www.magnific.com/pricing"
ATLAS = "https://www.atlascloud.ai/pricing"
RUNWAY = "https://docs.dev.runwayml.com/guides/pricing/"
FAL = "https://fal.ai/models/bytedance/seedance-2.5/text-to-video"
REP = "https://replicate.com/bytedance/seedance-2.5"
KREA = "https://www.krea.ai/pricing"
BYTE = "https://seed.bytedance.com/en/seedance"

# Atlas also lists estimated SR/ESR modes on the same pricing page. These are
# not in the catalog's three standard Seedance 2.5 Atlas rows.
ATLAS_EXTRA = [
    ("720p", "SR", 0.2193),
    ("720p", "ESR", 0.2515),
    ("1080p", "SR", 0.4056),
    ("1080p", "ESR", 0.4507),
]


def _src(g, url, text="source"):
    e = g["e"]
    href, rel = g["outbound"](url)
    return f'<a href="{e(href)}" rel="{rel}" target="_blank">{e(text)}</a>'


def _model_rows(g):
    return [r for r in g["rows"] if r.get("model") == MODEL]


def _stated_res(r):
    res = r.get("resolution") or ""
    if res in RES_ORDER:
        return res
    return None


def _published_api(g):
    rows = [
        r for r in _model_rows(g)
        if r.get("kind") == "api" and g["rate_label"](r) == "published rate"
    ]
    if not rows:
        return None
    return sorted(rows, key=lambda r: (r["usd_per_second"], r["id"]))[0]


def _rows_for_res(g, res):
    return sorted(
        [r for r in _model_rows(g) if _stated_res(r) == res],
        key=lambda r: (r["usd_per_second"], r["id"]),
    )


def _unstated_rows(g):
    return sorted(
        [r for r in _model_rows(g) if _stated_res(r) is None],
        key=lambda r: (r["usd_per_second"], r["id"]),
    )


def cheapest_at(g, res, kind=None, published_only=False):
    rows = _rows_for_res(g, res)
    if kind:
        rows = [r for r in rows if r.get("kind") == kind]
    if published_only:
        rows = [r for r in rows if g["rate_label"](r) == "published rate"]
    return rows[0] if rows else None


def checked_pt(date):
    """Turn an ISO date (YYYY-MM-DD) into a short PT label."""
    if not date:
        return "date not stated"
    parts = str(date).split("-")
    if len(parts) != 3:
        return f"{date} PT"
    year, month, day = parts
    months = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    try:
        label = f"{months[int(month) - 1]} {int(day)}, {year} PT"
    except (ValueError, IndexError):
        return f"{date} PT"
    return label


def blurb(g):
    best = _published_api(g)
    if not best:
        return "Seedance 2.5 APIs, credit plans, and live unlimited windows ranked by effective dollars per second."
    rate = g["rate_money"](best["usd_per_second"])
    res = g["shown_resolution"](best)
    return (
        f"The cheapest published Seedance 2.5 rate in the catalog is {rate}/s on "
        f"{best['platform']} ({res}, {best['variant']}). Credit-plan rates assume every paid credit is used. "
        "Unlimited windows are capped; they are not $0/s."
    )


def description(g, best):
    rate = g["rate_money"](best["usd_per_second"]) if best else None
    last = g["LAST"]
    res = g["shown_resolution"](best) if best else ""
    options = []
    if rate:
        if "non_video_in" in (best.get("variant") or ""):
            options.append(
                f"Cheapest published Seedance 2.5 is {rate}/s on {best['platform']} "
                f"({res}, no video input). APIs, credit plans, and current unlimited windows. "
                f"Last checked {last}."
            )
        options.append(
            f"Cheapest published Seedance 2.5 is {rate}/s on {best['platform']} ({res}). "
            f"APIs, credit plans, and current unlimited windows. Last checked {last}."
        )
    options.append(
        f"Seedance 2.5 ranked by effective $/s: APIs, credit plans, and current unlimited windows. "
        f"Last checked {last}."
    )
    for text in options:
        if len(text) <= 160:
            return text
    raise SystemExit(f"{PATH} meta description is over 160 characters")


def render(g):
    e, root, LAST = g["e"], g["root"], g["LAST"]
    rate_money, rate_label = g["rate_money"], g["rate_label"]
    plat_link, outbound = g["plat_link"], g["outbound"]
    shown_resolution = g["shown_resolution"]
    assumption_html = g["assumption_html"]
    tag, deal_badges = g["tag"], g["deal_badges"]
    models = g["models"]

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
    name = models[MODEL]["name"]

    all_rows = _model_rows(g)
    if not all_rows:
        raise SystemExit(f"{PATH} needs at least one {MODEL} price row")
    best = _published_api(g)
    if best is None:
        raise SystemExit(f"{PATH} needs a published Seedance 2.5 API rate")

    dates = [r.get("checked") or "" for r in all_rows]
    for item in g["db"].get("unverified") or []:
        blob = ((item.get("item") or "") + " " + (item.get("reason") or "")).lower()
        if "seedance 2.5" in blob:
            dates.append(g["db"].get("last_full_check") or "")
    ws = unlimited.live_windows(g)
    for w in ws:
        dates.append(w["deal"].get("verified_date") or "")
    offers_checked = max(d for d in dates if d) if any(dates) else LAST
    g["SITEMAP_LASTMOD"][PATH] = offers_checked

    def src(url, text="source"):
        return _src(g, url, text)

    def kind_label(r):
        if r.get("kind") == "plan":
            return "credit plan"
        label = rate_label(r)
        if label == "estimated from credit plan":
            return "API estimate"
        if label == "from credit plan":
            return "credit plan"
        if r.get("status") == "estimate":
            return "API estimate"
        return "pay-as-you-go API"

    def row_html(r):
        plan = ""
        if r.get("kind") == "plan" and r.get("plan_name"):
            plan = f" · {e(r['plan_name'])}"
        return (
            "<tr>"
            f"<td>{plat_link(r['platform'], r['source_url'])}{plan}</td>"
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

    def table_for(res_rows, empty="No catalog row at this resolution."):
        if not res_rows:
            return f"<p>{e(empty)}</p>"
        body = "".join(row_html(r) for r in res_rows)
        return f'<div class="tblwrap fit"><table>{head}<tbody>{body}</tbody></table></div>'

    # ----- lead -----
    best_rate = rate_money(best["usd_per_second"])
    mode_note = ""
    if "non_video_in" in (best.get("variant") or ""):
        mode_note = " That figure is a published rate for output video with no video input."
    elif best.get("note"):
        mode_note = " " + best["note"].rstrip(".") + "."
    lead = (
        f"The cheapest published {name} rate in the catalog today is {best_rate}/s "
        f"on {best['platform']} ({shown_resolution(best)}, {best['variant']}), "
        f"checked {checked_pt(best.get('checked'))}."
        + mode_note +
        " Credit-plan rates below assume every paid credit is used in full. "
        "Unlimited windows have time, clip, and resolution caps; they are not treated as $0/s. "
        "Affiliate links never change this price order."
    )

    # ----- who it suits (computed from the same rows, no invented rates) -----
    p480 = cheapest_at(g, "480p", kind="plan")
    p720 = cheapest_at(g, "720p", kind="plan")
    p1080 = cheapest_at(g, "1080p", kind="plan")
    a480 = cheapest_at(g, "480p")
    a720 = cheapest_at(g, "720p")
    a1080 = cheapest_at(g, "1080p")

    def clause(r):
        if r is None:
            return "no catalog row"
        return f"{rate_money(r['usd_per_second'])}/s on {r['platform']} ({kind_label(r)}, {shown_resolution(r)}, {r['variant']})"

    # ----- unlimited break-even vs cheapest same-res catalog API -----
    def break_even(w):
        res = w.get("resolution")
        api = cheapest_at(g, res, kind="api") or cheapest_at(g, res)
        checkout = w.get("checkout")
        if api is None or checkout is None or not api.get("usd_per_second"):
            return None, api
        seconds = checkout / api["usd_per_second"]
        return seconds, api

    unl_rows = []
    for w in ws:
        seconds, api = break_even(w)
        deal = w["deal"]
        href, rel = g["outbound"](deal.get("url") or HF_PLANS)
        plan = w.get("plan") or ""
        billing = w.get("billing") or ""
        caps = []
        if w.get("days"):
            caps.append(f"{w['days']} days")
        if w.get("max_clip_seconds"):
            caps.append(f"{w['max_clip_seconds']}-second clips")
        if w.get("resolution"):
            caps.append(w["resolution"])
        be = "not computed"
        if seconds is not None:
            be = (
                f"{seconds:,.0f} seconds at {rate_money(api['usd_per_second'])}/s "
                f"({api['platform']}, {shown_resolution(api)})"
            )
        unl_rows.append(
            "<tr>"
            f'<td><a href="{e(href)}" rel="{rel}" target="_blank">{e(deal.get("title") or deal["id"])}</a></td>'
            f"<td>{e(plan)} {e(billing)}</td>"
            f"<td>{e(w.get('price_text') or '')}</td>"
            f"<td>{e(', '.join(caps))}</td>"
            f"<td>{e(be)}</td>"
            f"<td>{e(checked_pt(deal.get('verified_date')))}</td>"
            "</tr>"
        )

    unl_table = ""
    if unl_rows:
        unl_head = (
            "<thead><tr><th>Offer</th><th>Plan</th><th>Checkout</th>"
            "<th>Caps</th><th>Break-even vs cheapest same-res catalog API</th>"
            "<th>Checked</th></tr></thead>"
        )
        unl_table = (
            f'<div class="tblwrap fit"><table>{unl_head}<tbody>{"".join(unl_rows)}</tbody></table></div>'
        )
    else:
        unl_table = "<p>No live unlimited Seedance 2.5 window is in the deal data today.</p>"

    # Higgsfield plan credits remain unverified for $/s
    hf_gap = None
    for item in g["db"].get("unverified") or []:
        if "Higgsfield Seedance 2.5 per-clip credits" in (item.get("item") or ""):
            hf_gap = item
            break

    atlas_bits = []
    by_res = {}
    for res, mode, usd in ATLAS_EXTRA:
        by_res.setdefault(res, []).append((mode, usd))
    for res, modes in by_res.items():
        catalog = cheapest_at(g, res, kind="api")
        parts = ", ".join(f"{mode} {rate_money(usd)}/s" for mode, usd in modes)
        atlas_bits.append(
            f"At {res}, Atlas also lists estimated {parts} on the same pricing page "
            f"({src(ATLAS, 'Atlas Cloud pricing')}, checked {checked_pt('2026-11-12')}). "
            + (
                f"The catalog's standard Atlas {res} estimate is {rate_money(catalog['usd_per_second'])}/s."
                if catalog
                else "Those modes are not in the catalog's standard Atlas Seedance 2.5 rows."
            )
        )

    # FAQs — visible text must match JSON-LD; no 'subscribe' substring.
    q1 = QUESTION
    a1 = (
        f"The cheapest published rate in the catalog is {best_rate}/s on {best['platform']} "
        f"({shown_resolution(best)}, {best['variant']}), checked {checked_pt(best.get('checked'))} "
        f"on the official model page. Credit-plan dollars per second assume every paid credit is used. "
        "A live unlimited window can cost less per second only after you generate more than the "
        "break-even seconds against the cheapest same-resolution catalog API, and only inside its caps. "
        "Unused credits, failed generations, minimum charges, and token-billing variance all raise the real rate."
    )
    q2 = "What is the cheapest option at 480p, 720p, and 1080p?"
    a2_parts = []
    for res, row in (("480p", a480), ("720p", a720), ("1080p", a1080)):
        if row is None:
            a2_parts.append(f"No catalog row is labeled {res}.")
        else:
            a2_parts.append(
                f"At {res}, the lowest catalog rate is {clause(row)}, "
                f"checked {checked_pt(row.get('checked'))}."
            )
    a2 = " ".join(a2_parts)
    if any(_unstated_rows(g)):
        u = _unstated_rows(g)[0]
        a2 += (
            f" Higgsfield API also publishes a list price from {rate_money(u['usd_per_second'])}/s "
            f"for five modes up to 1080p; the list does not state the resolution of the cheapest mode."
        )
    q3 = "Do credit plans beat the APIs if every credit is used?"
    plan_bits = []
    for res, row in (("480p", p480), ("720p", p720), ("1080p", p1080)):
        api = cheapest_at(g, res, kind="api", published_only=True) or cheapest_at(g, res, kind="api")
        if row and api:
            cheaper = "lower than" if row["usd_per_second"] < api["usd_per_second"] else "higher than"
            plan_bits.append(
                f"At {res}, the cheapest catalog plan rate is {rate_money(row['usd_per_second'])}/s "
                f"on {row['platform']} ({row.get('plan_name') or row['variant']}), which is {cheaper} "
                f"the cheapest catalog API rate of {rate_money(api['usd_per_second'])}/s on {api['platform']}."
            )
        elif row:
            plan_bits.append(
                f"At {res}, the cheapest catalog plan rate is {rate_money(row['usd_per_second'])}/s "
                f"on {row['platform']}."
            )
    a3 = (
        " ".join(plan_bits) + " "
        "Those plan figures are Magnific annual plans, with credits granted per year and valid for one year. "
        "Unused credits raise the effective dollars per second. Higgsfield plan credits for Seedance 2.5 "
        "are not turned into a dollars-per-second figure because the plan page does not state clip length and resolution."
    )
    q4 = "Are the unlimited windows the cheapest way?"
    if ws:
        a4 = (
            f"{len(ws)} live Higgsfield windows are in the deal data, with clip, resolution, and time caps. "
            "They are not $0/s. Break-even seconds below use checkout ÷ the cheapest same-resolution catalog API. "
            f"The full cap-by-cap comparison is in the {name} unlimited guide."
        )
    else:
        a4 = (
            "No live unlimited Seedance 2.5 window is in the deal data today. "
            f"See the {name} unlimited guide for ended windows and the method."
        )
    q5 = "How do we calculate this?"
    a5 = g["HOW_PLAIN"]

    faqs = [(q1, a1), (q2, a2), (q3, a3), (q4, a4), (q5, a5)]

    unstated_html = table_for(
        _unstated_rows(g),
        "No catalog row has an unstated resolution.",
    )

    gap_bits = []
    if hf_gap:
        gap_bits.append(
            f"{hf_gap.get('item')}: {hf_gap.get('reason')} "
            f"({src(HF_PLANS, 'Higgsfield pricing')}, catalog note). "
            "The Plus card rendered on Nov 12, 2026 PT lists 1,200 credits per month and 80 Seedance 2.5 videos, still without clip length or resolution."
        )
    gap_bits.append(
        f"Krea's pricing page lists approximate Seedance 2.5 video counts (including “Seedance 2.5 5s, 720p, no video reference” and marketing lines such as “~16 Seedance 2.5 videos” on the $9 plan). "
        f"Those counts are tildes, and the page does not give a single credits-per-clip figure this catalog can convert into dollars per second "
        f"({src(KREA, 'Krea pricing')}, checked {checked_pt('2026-11-12')})."
    )
    gap_bits.append(
        f"ByteDance's Seedance page does not publish a self-serve dollars-per-second rate "
        f"({src(BYTE, 'ByteDance Seedance')}, checked {checked_pt('2026-11-12')})."
    )
    gap_bits.append(
        f"Replicate lists 480p and 720p only. There is no 1080p rate on the official model page "
        f"({src(REP, 'Replicate Seedance 2.5')}, checked {checked_pt('2026-11-12')})."
    )
    gap_bits.append(
        f"Higgsfield API's list says “from {rate_money(next(r['usd_per_second'] for r in _unstated_rows(g)))}/s” for five modes up to 1080p. "
        "The resolution of the cheapest mode is not stated on that list, so that row is not ranked as a 480p, 720p, or 1080p rate. "
        f"A “Compare with others” table on the same page lists $0.118/s for Text to Video / Image to Video and $0.139/s for Reference to Video / Video Edit / Video Extend, but the table itself says the comparison is based on prices as of 16 September, 2026 "
        f"({src(HF_API, 'Higgsfield API pricing')}, checked {checked_pt('2026-11-12')})."
    )

    hidden = [
        (
            "Failed generations",
            "The vendor pages checked today do not state a single, clear refund or no-charge policy for failed Seedance 2.5 generations. Treat that cost as unknown. A failed job that still bills raises every rate below.",
        ),
        (
            "Runway minimum and input video",
            f"Runway bills seedance2_5 at 20 / 30 / 68 credits per second of output at 480p / 720p / 1080p, plus 10 / 15 / 34 credits per second of input and reference video, with an 80 credit minimum per generation. Credits are $0.01 each, so the minimum is $0.80 before any output length, and a short clip with input video costs more than the catalog output-only rate. A preview (draft: true) bills at the 480p rate; enhancing that preview to 1080p is a second, separate 1080p charge. Sales tax may apply. "
            f"({src(RUNWAY, 'Runway API pricing')}, checked {checked_pt('2026-11-12')}).",
        ),
        (
            "Magnific credits expire",
            f"Magnific annual plans grant credits per year (“Credits valid for 1 year, no monthly resets”). The catalog $/s figures assume those credits are used in full. Leftover credits raise the effective rate. Prices exclude VAT and local taxes. The page says you can top up credits anytime; it does not state a minimum top-up on the pricing page checked today. "
            f"({src(MAG, 'Magnific pricing')}, checked {checked_pt('2026-11-12')}).",
        ),
        (
            "fal and Atlas token billing",
            f"fal publishes roughly $0.2205 / $0.4730 / $1.164 per second at 480p / 720p / 1080p, billed by tokens. The token count is a function of output size, duration, and (for some endpoints) input video duration, so the invoice can differ from the per-second estimate "
            f"({src(FAL, 'fal Seedance 2.5')}, checked {checked_pt('2026-11-12')}). "
            f"Atlas labels its listed rates “(estimated)” and says the final charge uses actual completion tokens after the task finishes. Reference-to-video requests that include a reference video are billed on output plus reference-video tokens "
            f"({src(ATLAS, 'Atlas Cloud pricing')}, checked {checked_pt('2026-11-12')}).",
        ),
        (
            "Higgsfield API funds and list price",
            f"Higgsfield API's Seedance 2.5 list price is “from” $0.118/s. Concurrent generation limits count only funds added in the past 28 days. The pricing page checked today does not state a minimum top-up or a failed-generation refund rule. "
            f"({src(HF_API, 'Higgsfield API pricing')}, checked {checked_pt('2026-11-12')}).",
        ),
    ]

    hidden_html = "".join(
        f"<h3>{e(title)}</h3><p>{body}</p>" for title, body in hidden
    )

    body = f"""<p class="small"><a href="{root("/guides/")}">Guides</a> › Cheapest Seedance 2.5</p>
<h1>{e(PHRASE)}</h1>
<p class="lead">{e(lead)}</p>
{g["checked_line"]()}
<p>Related: <a href="{root(UNLIMITED_PATH)}">unlimited Seedance 2.5 plans compared</a> · <a href="{root("/models/seedance-2-5/")}">{e(name)} model page</a> · <a href="{root("/guides/cheapest-ai-video-generator/")}">cheapest AI video generator by model</a> · <a href="{root("/calculator/")}">credit calculator</a>.</p>

<h2>{e(q1)}</h2>
<p>{e(a1)}</p>
<h2>{e(q2)}</h2>
<p>{e(a2)}</p>

<h2>480p</h2>
<p>Lowest catalog dollars per second first. Plan rates assume every paid credit is used. Estimates stay labeled.</p>
{table_for(_rows_for_res(g, "480p"))}
<p>Who this resolution suits: a casual user who wants a published pay-as-you-go rate can start with the cheapest published 480p API and stop when the work is done. A credit plan at this resolution only beats that API if you will actually use the yearly credits. The live monthly Plus unlimited window at 480p is capped (clip length and days); use the break-even table below rather than treating it as free.</p>

<h2>720p</h2>
<p>Lowest catalog dollars per second first.</p>
{table_for(_rows_for_res(g, "720p"))}
<p>{atlas_bits[0] if atlas_bits else ""} Those SR and ESR figures are still estimates, not catalog rows, and they are not used to reorder the table above.</p>
<p>Who this resolution suits: volume users who will finish yearly Magnific credits can compare that plan rate with the cheapest published 720p API. Casual use still favors a pay-as-you-go API so unused credits do not inflate the rate. Live unlimited windows at 720p need the break-even seconds below, inside their clip and day caps.</p>

<h2>1080p</h2>
<p>Lowest catalog dollars per second first. Replicate does not list a 1080p rate.</p>
{table_for(_rows_for_res(g, "1080p"))}
<p>{atlas_bits[1] if len(atlas_bits) > 1 else ""} Those SR and ESR figures are still estimates, not catalog rows, and they are not used to reorder the table above. Atlas also lists estimated 1440p and 4K modes on the same page; those resolutions have no other catalog Seedance 2.5 rows to rank against.</p>
<p>Who this resolution suits: 1080p is the expensive tier in this catalog. A token-billed estimate can undercut a published credit API, but the invoice may move. A Magnific annual plan at 1080p is only cheaper than paying as you go if the yearly credits are used. The live annual Ultra unlimited window at 1080p is time-capped; see break-even below.</p>

<h2>List price with no stated resolution</h2>
<p>This catalog row is a published “from” price. It is not ranked inside a 480p, 720p, or 1080p table because the official list does not name the cheapest mode's resolution.</p>
{unstated_html}

<h2>Current unlimited windows</h2>
<p>These are live Higgsfield windows from the deal data, not a second copy of the unlimited guide. Break-even seconds are checkout divided by the cheapest same-resolution catalog API rate. That is the output you would need at that API rate before the window costs less than paying as you go. Caps still apply, and this is not $0/s. Full comparison: <a href="{root(UNLIMITED_PATH)}">unlimited Seedance 2.5 plans compared</a>.</p>
{unl_table}
<p class="small">Affiliate links never change this price order. Higgsfield links use the <code>fpr=emmanuel-bbfe0e</code> tag and are marked sponsored.</p>

<h2>Hidden costs</h2>
{hidden_html}

<h2>What is confirmed, and what is not</h2>
<p><b>Confirmed today (Nov 12, 2026 PT) on the vendors' own pages, and matching the catalog rows used above:</b> Replicate's four published per-second rates of $0.1028 (non_video_in, 480p), $0.4304 (video_in, 480p), $0.2312 (non_video_in, 720p), and $0.9676 (video_in, 720p), which the tables show with the site's usual rounding; Higgsfield API's list price from $0.118/s for five modes up to 1080p; Magnific Draft 480p at 800 credits/4s, 720p at 1,760 credits/4s, and 1080p at 4,400 credits/4s, with annual plan prices of $14.50 / $33.75 / $82.50 per month billed yearly and credits valid for one year; Runway's 20 / 30 / 68 credits per second of output at 480p / 720p / 1080p and $0.01 per credit; fal's roughly $0.2205 / $0.4730 / $1.164 per second estimates; Atlas's standard $0.1397 / $0.3005 / $0.5914 per second estimates at 480p / 720p / 1080p; and the live unlimited windows already stored in the deal data (11.11 sale ending Nov 15, 2026, plus the Business Scale windows with no stated end date).</p>
<p><b>Confirmed on a vendor page today, but not a catalog row:</b> Atlas estimated SR and ESR modes cited above; Krea's approximate Seedance 2.5 video counts; Higgsfield Plus listing 80 Seedance 2.5 videos on 1,200 credits without a clip length or resolution; Runway's 80-credit minimum, input-video add-on credits, and draft preview billing; fal's and Atlas's token formulas; Magnific credit validity and VAT exclusion.</p>
<p><b>Unknown:</b> a uniform failed-generation refund rule; minimum top-ups on Higgsfield API, fal, Atlas, Replicate, and Magnific (top-ups are offered on Magnific, but no minimum was stated on the pricing page); whether Higgsfield API's cheapest “from” mode is 480p; a Replicate 1080p rate; a Krea or Higgsfield plan dollars-per-second figure for Seedance 2.5; a public ByteDance self-serve rate. Invented figures are not shown for those gaps.</p>
<ul class="small">{"".join(f"<li>{bit}</li>" for bit in gap_bits)}</ul>

<h2>{e(q3)}</h2>
<p>{e(a3)}</p>
<h2>{e(q4)}</h2>
<p>{e(a4)} <a href="{root(UNLIMITED_PATH)}">Unlimited Seedance 2.5 plans compared</a>.</p>
{g["how_block"]()}
"""

    title = g["page_title"](PHRASE)
    desc = description(g, best)
    g["guide_page"](PATH, title, desc, body, faqs)
    return PATH
