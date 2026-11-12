"""Guide: Is Wan 3.0 unlimited really unlimited?

Imported by scripts/build_site.py. Live and ended unlimited-window deals come
from data/deals.json. API and plan dollars-per-second come from data/prices.json.
The page states plainly that no vendor in that catalog currently sells Wan 3.0
or Wan 3.0 Prime as unlimited, and it invents no live offer.
"""
PATH = "/guides/wan-3-0-unlimited/"
LABEL = "Wan 3.0 unlimited"
PHRASE = "Is Wan 3.0 unlimited really unlimited?"
QUESTION = "Is Wan 3.0 unlimited really unlimited?"
ENDED_ID = "hf-wan3-unlimited-7d"
CHANGELOG = "https://higgsfield.ai/creator-hub/changelog"
PRICING = "https://higgsfield.ai/pricing"
HELP_UNL = "https://higgsfield.ai/creator-hub/help-center/credits/what-are-unlimited-models-and-which-plans-include-them"
HELP_MCP = "https://higgsfield.ai/creator-hub/help-center/integrations/what-is-higgsfield-mcp"
WAN_PLANS = "https://create.wan.video/pricing?whereToMemberShip=membership_plans"
WAN_HOME = "https://wan.video/"
ALI_PRICING = "https://www.alibabacloud.com/help/en/model-studio/model-pricing"
KREA_PRICING = "https://www.krea.ai/pricing"
KREA_WAN = "https://www.krea.ai/models/wan30"
MAGNIFIC = "https://www.magnific.com/pricing"
RUNWAY = "https://runway.com/pricing"
HF_API = "https://open.higgsfield.ai/pricing"
HF_API_WAN = "https://open.higgsfield.ai/models/alibaba/wan-3.0/text-to-video"
FAL_WAN = "https://fal.ai/models/alibaba/wan-3.0/text-to-video"
REP_WAN = "https://replicate.com/alibaba/wan-3"
BONUS_BLOG = "https://higgsfield.ai/blog/higgsfield-7-day-unlimited-bonus"

# Catalog API rows used as the cheapest published Wan 3.0 / Prime rate at each res.
CHEAP_API = {
    ("wan-3-0", "480p"): "r025",
    ("wan-3-0", "720p"): "r026",
    ("wan-3-0", "1080p"): "r027",
    ("wan-3-0-prime", "480p"): "r001",
    ("wan-3-0-prime", "720p"): "r002",
    ("wan-3-0-prime", "1080p"): "r003",
}
# Representative plan rows: cheapest Higgsfield credit-plan rate (Ultra 3K annual).
PLAN_EXAMPLES = {
    ("wan-3-0", "480p"): "r096",
    ("wan-3-0-prime", "480p"): "r081",
}


def _src(g, url, text="source"):
    e = g["e"]
    href, rel = g["outbound"](url)
    return f'<a href="{e(href)}" rel="{rel}" target="_blank">{e(text)}</a>'


def _row(g, rid):
    for r in g["rows"]:
        if r.get("id") == rid:
            return r
    return None


def _ended(g):
    return g["DEAL_BY_ID"].get(ENDED_ID)


def _live_wan_unlimited(g):
    dealmod, today = g["dealmod"], g["TODAY"]
    out = []
    for d in g["deal_doc"]["deals"]:
        models = d.get("models") or []
        if d.get("type") != "unlimited_window":
            continue
        if "wan-3-0" not in models and "wan-3-0-prime" not in models:
            continue
        if dealmod.is_current(d, today):
            out.append(d)
    return out


def cheapest_api(g, model, resolution):
    rows = [
        r for r in g["rows"]
        if r.get("model") == model and r.get("kind") == "api" and r.get("resolution") == resolution
    ]
    if not rows:
        return None
    return sorted(rows, key=lambda r: (r["usd_per_second"], r["id"]))[0]


def blurb(g):
    live = _live_wan_unlimited(g)
    r096 = _row(g, "r096")
    rate = g["rate_money"](r096["usd_per_second"]) if r096 else None
    if live:
        return (
            f"{len(live)} live Wan 3.0 or Wan 3.0 Prime unlimited-window deal"
            f"{'s' if len(live) != 1 else ''} "
            "are in the deals file. Read the caps before treating any of them as $0/s."
        )
    bit = f" The cheapest Wan 3.0 plan rate in the catalog today is {rate}/s at 480p on Ultra annual." if rate else ""
    return (
        "No vendor we track currently sells Wan 3.0 or Wan 3.0 Prime as unlimited. "
        "Higgsfield's 7-day window ended in October (the Oct 20 end is an estimate)."
        + bit
    )


def render(g):
    e, LAST = g["e"], g["LAST"]
    ended = _ended(g)
    live = _live_wan_unlimited(g)
    if ended is None:
        raise SystemExit(f"{PATH} missing ended deal {ENDED_ID}")
    if live:
        raise SystemExit(
            f"{PATH} found live Wan unlimited deal(s) {[d['id'] for d in live]}; "
            "update the guide before publishing a page that says none are live"
        )

    rows_by_id = {r["id"]: r for r in g["rows"]}
    for label, mapping, must_be_cheapest in (
        ("API", CHEAP_API, True),
        ("plan", PLAN_EXAMPLES, False),
    ):
        for (model, res), rid in mapping.items():
            r = rows_by_id.get(rid)
            if not r:
                raise SystemExit(f"{PATH} missing catalog row {rid}")
            if r["model"] != model or r.get("resolution") != res:
                raise SystemExit(f"{PATH} row {rid} is not {model} {res}")
            if must_be_cheapest:
                best = cheapest_api(g, model, res)
                if not best or best["id"] != rid:
                    got = best["id"] if best else "none"
                    raise SystemExit(f"{PATH} cheapest {model} {res} API is {got}, not {rid}")

    as_of = max(filter(None, [ended.get("verified_date"), LAST]))
    g["SITEMAP_LASTMOD"][PATH] = as_of

    desc = (
        "No vendor we track sells Wan 3.0 as unlimited today. "
        "Higgsfield's 7-day window ended in October, with 30-second and 1080p caps. "
        "Here is the per-second math."
    )
    if len(desc) > 160:
        raise SystemExit(f"{PATH} description is {len(desc)} characters")

    def rate(rid):
        return g["rate_money"](rows_by_id[rid]["usd_per_second"])

    def checked(rid):
        return rows_by_id[rid]["checked"]

    def src_row(rid, label="source"):
        r = rows_by_id[rid]
        return _src(g, r["source_url"], label)

    def plat(rid):
        return rows_by_id[rid]["platform"]

    api_head = "<thead><tr><th>Model</th><th>Resolution</th><th>Cheapest API in the catalog</th><th>Checked</th></tr></thead>"
    api_rows = []
    for (model, res), rid in CHEAP_API.items():
        name = "Wan 3.0 Prime" if model == "wan-3-0-prime" else "Wan 3.0"
        api_rows.append(
            "<tr>"
            f"<td>{e(name)}</td><td>{e(res)}</td>"
            f"<td><b>{e(rate(rid))}/s</b> on {e(plat(rid))}</td>"
            f"<td>{e(checked(rid))}. {src_row(rid)}</td>"
            "</tr>"
        )
    api_table = f'<div class="tblwrap fit"><table>{api_head}<tbody>{"".join(api_rows)}</tbody></table></div>'

    # Higgsfield Ultra 3K annual vs the cheapest API at 480p, for current credit pricing.
    plan_bits = []
    for model, label, prid, aid in (
        ("wan-3-0", "Wan 3.0 480p", "r096", "r025"),
        ("wan-3-0-prime", "Wan 3.0 Prime 480p", "r081", "r001"),
    ):
        plan_bits.append(
            f"{label} on Higgsfield Ultra 3K annual is {rate(prid)}/s "
            f"(catalog {prid}, checked {checked(prid)}, {src_row(prid, 'Higgsfield pricing page')}), "
            f"assuming every paid credit is used. The cheapest {label.split(' 480p')[0]} API "
            f"at 480p is {rate(aid)}/s on {plat(aid)} (catalog {aid}, checked {checked(aid)}, {src_row(aid)})."
        )

    faqs = [
        (
            "Is there an unlimited Wan 3.0 plan right now?",
            "Not among the vendors in our price catalog and deals file. "
            "On Nov 12, 2026, Higgsfield's pricing page listed Wan 3.0 and Wan 3.0 Prime only at credit rates. "
            "Alibaba's Wan membership page sells credit plans, not an unlimited plan. "
            "Krea, Magnific, Runway, fal, and Replicate also do not sell Wan 3.0 as unlimited on the pages we checked that day.",
        ),
        (
            "What limits did Higgsfield's 7-day Wan 3.0 window have?",
            "Higgsfield's Oct 13, 2026 changelog, with terms as of that date, offered a free week of Wan 3.0 and Wan 3.0 Prime on individual plans from Pro and above, monthly or annual. "
            "Clips were up to 30 seconds at up to 1080p, in a shared queue, so speed depended on load. "
            "An upgrade from Basic or Starter started the 7 days from that moment. "
            "The window is not on the pricing page today. The recorded end date, Oct 20, 2026, is an estimate from a check the next day.",
        ),
        (
            "How would a break-even against the API work?",
            "Break-even seconds are the amount you pay for the window, divided by the cheapest Wan 3.0 API dollars per second at the same resolution in the price catalog. "
            "Higgsfield's week was a bonus on an existing Pro-or-higher plan, not a separately priced unlimited plan, and it has ended, so this page does not invent a checkout figure or a $0/s rate for it. "
            "The cheapest Wan 3.0 API rates in the catalog today are $0.035/s at 480p, $0.07/s at 720p, and $0.14/s at 1080p on Replicate.",
        ),
        (
            "Does Alibaba sell unlimited Wan 3.0?",
            "No. The official membership page at create.wan.video lists a Free plan at $0 with daily check-in credits, Pro at $5/month billed yearly (300 credits/month), and Premium at $20/month billed yearly (1,200 credits/month). "
            "None of those cards say unlimited. Model Studio bills wan3.0-video per second and offers a 30-second free quota in Singapore only, not an unlimited plan.",
        ),
        (
            "Does Krea's Unlimited relaxed generations include Wan 3.0?",
            "The Max and Business cards list “Unlimited relaxed generations,” but the pricing table still gives finite approximate clip counts for Wan 3.0 (for example, ~45 / ~180 / ~360 two-second 480p clips on Basic, Pro, and Max). "
            "The Wan 3.0 model page does not say that model is covered by the unlimited-relaxed feature. This guide does not treat Krea as an unlimited Wan 3.0 plan.",
        ),
    ]

    body = f"""
<p class="small"><a href="{g['root']('/guides/')}">Guides</a> › Wan 3.0 unlimited</p>
<h1>{e(PHRASE)}</h1>
<p class="lead">{e(desc)}</p>
<p class="small">Last checked {e(LAST)}.</p>
<p>Checked 2026-11-12 on the vendors' own pages linked below. Prices exclude VAT and local taxes, which are added at checkout. Always confirm the price on the vendor's page before you buy.</p>

<h2>What is confirmed, and what is not</h2>
<p>Confirmed: none of the vendors in our catalog currently sell Wan 3.0 or Wan 3.0 Prime as an unlimited plan or an unlimited window. Higgsfield's pricing page today lists those two models only in the credit-rate compare table. Its 11.11 unlimited cards name Seedance 2.5 for video, plus image models, and do not name Wan 3.0. Alibaba's official membership plans run on credits. The last Wan 3.0 unlimited window we recorded, on Higgsfield, has ended.</p>
<p>Not announced: a new Wan 3.0 or Wan 3.0 Prime unlimited sale on Higgsfield, on create.wan.video, or on the other vendor pages checked for this guide. Unknown: whether Higgsfield currently sells a paid Unlimited Models Marketplace bundle for Wan 3.0, because that catalog is inside an account and was not visible on the public pricing page. The Oct 20, 2026 end date for the last Higgsfield window is an estimate; Higgsfield's changelog did not print a calendar end time for the week.</p>

<h2>Higgsfield's 7-day window, now ended</h2>
<p>On Oct 13, 2026, Higgsfield's {_src(g, CHANGELOG, "changelog")} posted “Unlimited Wan 3.0 for 7 days and 60% off on the API,” with terms as of that date. It offered a free week of Wan 3.0 and Wan 3.0 Prime for subscribers. Official limits from that entry:</p>
<ul>
<li>Clips up to 30 seconds, at up to 1080p.</li>
<li>A shared queue, so speed depended on load.</li>
<li>Availability: individual plans from Pro and above, monthly or annual.</li>
<li>Upgrading from Basic or Starter during the offer started the 7 days from that moment.</li>
<li>A separate Higgsfield API discount, until Oct 31, 2026, billed per second, not as unlimited.</li>
</ul>
<p>A check on Oct 21, 2026 found the pricing page listing Wan 3.0 only at credit rates, so the window was archived with an estimated end of Oct 20 (seven days after the changelog entry). Rechecked 2026-11-12 on the rendered {_src(g, PRICING, "Higgsfield pricing page")}: Plus and Ultra cards still list 14-day unlimited Seedance 2.5 and 60-day unlimited image models (Nano Banana Pro, Seedream 5.0 Pro, GPT Image 2.5, GPT Image 2.6, and, when expanded, Nano Banana, Kling O1 Image, Seedream 4.5, Seedream 5.0 Lite, and Flux.2 Pro). Wan 3.0 is 5 / 8.75 / 17.5 credits per 5 seconds at 480p / 720p / 1080p; Wan 3.0 Prime is 7.5 / 15 / 30 credits per 5 seconds. Higgsfield's Oct 30 {_src(g, BONUS_BLOG, "7-day unlimited bonus post")} describes a later Seedance 2.5 and image-model bonus and does not mention Wan 3.0.</p>
<p>Higgsfield's help article {_src(g, HELP_UNL, "What are Unlimited models?")} (checked 2026-11-12) is the current general rulebook, not the Oct 13 offer text. It says unlimited generations do not deduct credits while access is active; you have to switch the Unlimited toggle on, or the job uses credits and the priority queue; unlimited jobs run in the standard queue, and speed and concurrency may vary at peak times; access applies only on higgsfield.ai; and it is for personal, human use (automation, scripting, credential sharing, and reselling are prohibited). A companion article, {_src(g, HELP_MCP, "What is Higgsfield MCP?")}, says MCP, CLI, Canvas, Supercomputer, and other automated tools always deduct credits. The help article's marketplace table (1 video at a time, up to 15 seconds, for purchased video bundles) is about those in-account bundles, not the Oct 13 changelog caps of 30 seconds and 1080p.</p>
<p>Because the week was a bonus on an existing Pro-or-higher plan, not a separately priced unlimited SKU, and because it has ended, this page does not invent a checkout price or an effective $0/s rate for it. If a priced window comes back, break-even seconds are that checkout price divided by the cheapest same-resolution Wan 3.0 API rate in the catalog, below.</p>

<h2>Alibaba's official Wan site and API are not unlimited</h2>
<p>Checked 2026-11-12 on {_src(g, WAN_PLANS, "create.wan.video membership plans")} and {_src(g, WAN_HOME, "wan.video")}. The membership page lists:</p>
<ul>
<li>Free: US$0/month, daily check-in to earn free credits, 1 video and 1 image at a time. The page does not say how many credits a check-in gives, or how many credits a Wan 3.0 clip costs, so this site does not turn the Free plan into dollars per second.</li>
<li>Pro: US$5/month billed yearly (the monthly price is shown as $10), 300 credits per month, up to 3 videos at a time, watermark-free downloads, 1080p, and 10–30 second videos.</li>
<li>Premium: US$20/month billed yearly (the monthly price is shown as $40), 1,200 credits per month, up to 8 videos and 5 images at a time, with the same 1080p and 10–30 second features.</li>
</ul>
<p>None of those cards say unlimited. The page also says the first month or year is non-refundable after activation, and that the purchase is for model creation on create.wan.video only; the API is a separate purchase. Because the page does not state credits per Wan 3.0 second, those plans are not converted to $/s here.</p>
<p>Alibaba Cloud {_src(g, ALI_PRICING, "Model Studio pricing")} (checked 2026-11-12) bills wan3.0-video and wan3.0-video-prime per second of input plus output. For International (Singapore) it prints list prices of $0.05 / $0.10 / $0.20 per second at 480p / 720p / 1080p for wan3.0-video, each labeled “Limited-time 30% off,” and $0.068 / $0.14 / $0.28 per second for wan3.0-video-prime, with no free quota on Prime. The page does not print the 30% off dollar amounts next to those list prices, so this guide does not invent them. wan3.0-video has a 30-second free quota in Singapore only, valid for 90 days from Model Studio activation, model release, or application approval, whichever is later. That is a 30-second quota, not an unlimited plan. Failed requests are not billed and do not consume the quota. These official API prices are not rows in our price catalog; the break-even table below uses the cheapest catalog API at each resolution.</p>

<h2>Other vendors we already track</h2>
<p>Each of these pages was checked 2026-11-12. None of them sell Wan 3.0 or Wan 3.0 Prime as unlimited:</p>
<ul>
<li>{_src(g, KREA_PRICING, "Krea pricing")} and the {_src(g, KREA_WAN, "Wan 3.0 model page")}: Max and Business list “Unlimited relaxed generations,” but the pricing table still counts Wan 3.0 in compute units, with approximate clip counts (Wan 3.0 at 2s, 480p: ~45 / ~180 / ~360 on Basic, Pro, and Max). The model page does not say Wan 3.0 is included in that unlimited-relaxed feature.</li>
<li>{_src(g, MAGNIFIC, "Magnific pricing")}: the Unlimited tags are on Kling 2.5 and image models. Wan appears in the footer model list, but there is no Wan 3.0 unlimited row, and our catalog has no Magnific Wan 3.0 prices.</li>
<li>{_src(g, RUNWAY, "Runway pricing")}: no Wan 3.0 listing. The Unlimited label we saw was on 4K video upscaling.</li>
<li>{_src(g, HF_API, "Higgsfield API pricing")} and the {_src(g, HF_API_WAN, "Wan 3.0 API model page")}: standard self-serve rates, billed per output second (Wan 3.0 $0.0375 / $0.075 / $0.15 at 480p / 720p / 1080p; Prime $0.051 / $0.105 / $0.21). No unlimited plan.</li>
<li>{_src(g, FAL_WAN, "fal Wan 3.0")} and {_src(g, REP_WAN, "Replicate alibaba/wan-3")}: pay-as-you-go API pages, not unlimited plans. Replicate is the cheapest Wan 3.0 API in our catalog, at the rates in the table below (checked {e(checked('r025'))}).</li>
</ul>

<h2>What you actually pay per second today</h2>
<p>With no live unlimited window, Wan 3.0 and Wan 3.0 Prime cost the catalog rates below. Credit-plan figures assume every paid credit is used; unused credits make the real cost higher. Affiliate links never change this price order.</p>
{api_table}
<p>{e(plan_bits[0])} {e(plan_bits[1])} See the <a href="{e(g['root']('/guides/cheapest-wan-3-0/'))}">cheapest Wan 3.0 guide</a>, the <a href="{e(g['root']('/models/wan-3-0/'))}">Wan 3.0</a> and <a href="{e(g['root']('/models/wan-3-0-prime/'))}">Wan 3.0 Prime</a> model pages, and <a href="{e(g['root']('/guides/seedance-2-5-unlimited/'))}">unlimited Seedance 2.5 plans compared</a> for the windows Higgsfield is actually selling this week.</p>
{g['faq_html'](faqs)}
<div class="disclose">Some Higgsfield links on this page are affiliate links. <a class="tap" href="{e(g['root']('/about/#disclosure'))}">Disclosure</a>.</div>
"""
    title = g["page_title"](PHRASE)
    if len(title) > 60:
        raise SystemExit(f"{PATH} title is {len(title)} characters")
    g["guide_page"](PATH, title, desc, body, faqs)
    return {"title": title, "desc": desc, "path": PATH}
