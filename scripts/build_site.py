#!/usr/bin/env python3
"""Build the static VidFare site from data/*.json into dist/."""
import json, os, re, shutil, html, datetime, sys, email.utils, struct, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deals as dealmod
import notify_indexnow
import variations as variations
import weekly_report
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlparse, urlsplit, urlunsplit, parse_qsl, urlencode, quote
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
SITE_URL = "https://vidfare.com"
BRAND = "VidFare"
TAGLINE = "What every AI video second costs, everywhere."
OG_IMAGE = SITE_URL + "/og.png"
LOGO_URL = SITE_URL + "/logo-512.png"
ORG_ID = SITE_URL + "/#organization"
OG_ALT = BRAND + ". " + TAGLINE
# The Kit form is live. The header nav stays as it is on the live site, so a
# Newsletter item is not added. /newsletter/ is a normal page and is in the sitemap.
CONTACT_EMAIL = "hello@vidfare.com"
NEWSLETTER_ENABLED = True
# Kit (ConvertKit) signup. Every page renders news_box() from these three
# values. Swap the account form here, then rebuild dist. Nothing else
# should hardcode the id, uid, or action URL.
KIT_FORM_ID = "10170819"
KIT_FORM_UID = "6ef7eafdbe"
KIT_FORM_ACTION = "https://app.kit.com/forms/10170819/subscriptions"
# Weekly /reports/ pages. On for the live site. A week is still withheld when
# it has fewer than two qualifying changes (per-second price changes, promo
# starts, and promo ends).
REPORTS_ENABLED = True
# Credit-plan $/s is plan price ÷ credits × credits per clip ÷ seconds (scripts/build_data.py).
# The about page states the assumption that math uses: every credit paid for is used.
CREDIT_USE = "assumes every credit you pay for is used"
# These resolution values are model tiers, not pixel sizes. build_data.py stores them in resolution.
TIER_RESOLUTIONS = {"Pro tier", "Pro", "Standard"}
MISSING_RESOLUTIONS = {"", "—", "-", "–"}
# Path prefix under SITE_URL. Empty on https://vidfare.com, so links and assets stay at /.
BASE = urlparse(SITE_URL).path.rstrip("/")
# Search guides. Every dollar figure on these pages is rendered from data/prices.json.
GUIDE_LINKS = [
    ("/guides/", "All guides"),
    ("/guides/cheapest-wan-3-0/", "Cheapest Wan 3.0"),
    ("/guides/cheapest-ai-video-generator/", "Cheapest by model"),
    ("/guides/is-higgsfield-worth-it/", "Higgsfield plans"),
    ("/guides/ai-video-project-budget/", "Project budget"),
]
HF_PLATFORMS = {"Higgsfield", "Higgsfield API"}

def root(path):
    """Site path. Includes a prefix only when SITE_URL has one."""
    if path.startswith(("http://", "https://", "mailto:", "#")):
        return path
    if not path.startswith("/"):
        path = "/" + path
    return BASE + path
db = json.load(open(os.path.join(ROOT, "data", "prices.json")))
changes = json.load(open(os.path.join(ROOT, "data", "changes.json")))
sponsors = json.load(open(os.path.join(ROOT, "data", "sponsors.json")))
models, plans, sources = db["models"], db["plans"], db["sources"]
today = datetime.date.today()
TODAY = today.isoformat()
MONTH = today.strftime("%b %Y")
TITLE_LIMIT = 60
AGENT_H1 = "Let your AI agent check AI video prices before it generates."
HOME_TITLE = "Let your AI agent check AI video prices | VidFare"
HOME_DESC = (
    "Let your AI agent check current AI video prices and live deals before it generates. "
    "The dollars-per-second table stays on the page for people to compare."
)
MCP_TITLE = "Connect an AI agent to VidFare prices | VidFare"
MCP_DESC = (
    "Paste a prompt, then connect ChatGPT, Claude, or Cursor to the VidFare MCP server. "
    "Your agent checks current per-second prices and deals, and cites vidfare.com."
)
AGENT_PROMPT = (
    "Before you recommend an AI video model or generate a video, use the VidFare MCP tools to check current prices. "
    "Call cheapest_options or estimate_cost for the length and resolution I need, call list_deals for active discounts, "
    "and use get_model_prices or list_models for details. Give me the per-second price and total cost for the top options, "
    "mention any live deal, and cite vidfare.com as the source with the date the prices were checked."
)
MCP_ENDPOINT = "https://mcp.vidfare.com/mcp"
MCP_CURSOR = '{"mcpServers":{"vidfare":{"url":"https://mcp.vidfare.com/mcp"}}}'
MCP_PRIVACY = "Anonymous usage counts (method, tool name, coarse client type) are logged; no IPs or request contents."

def page_title(phrase, with_month=True, with_brand=True):
    """Keep phrase whole. Drop the month, then the brand, if the title would pass 60 characters."""
    month = f" ({MONTH})" if with_month else ""
    brand = f" | {BRAND}" if with_brand else ""
    title = f"{phrase}{month}{brand}"
    if len(title) <= TITLE_LIMIT:
        return title
    if with_month:
        return page_title(phrase, False, with_brand)
    if with_brand:
        return page_title(phrase, False, False)
    return phrase
def discontinued(r):
    """A row is off sale once its status says so, or its shutdown date is before today."""
    if r.get("status") == "discontinued": return True
    end = r.get("discontinued_on")
    return bool(end and end < TODAY)
def current(r):
    """Drop expired promos and discontinued rows from rankings and the live table."""
    if discontinued(r): return False
    if r.get("promo_until") and r["promo_until"] < TODAY: return False
    return True
rows = [r for r in db["rows"] if current(r)]
retired_rows = [r for r in db["rows"] if discontinued(r)]
LAST = db.get("last_full_check") or min(r["checked"] for r in db["rows"])
# Per-URL sitemap dates. Pages not listed here use LAST, which is the catalog check, not the build clock.
SITEMAP_LASTMOD = {}
deal_doc = dealmod.load()
LIVE_DEALS = [d for d in deal_doc["deals"] if dealmod.is_current(d, TODAY)]
UPCOMING_DEALS = [d for d in deal_doc["deals"] if dealmod.is_upcoming(d, TODAY)]
ARCHIVED = [d for d in deal_doc["deals"] if not dealmod.is_current(d, TODAY) and not dealmod.is_upcoming(d, TODAY)]
HISTORY = list(deal_doc.get("history") or [])
DEAL_BY_ID = {d["id"]: d for d in deal_doc["deals"]}
CALC_DEALS = dealmod.calculator_map(deal_doc["deals"], plans, TODAY)

# Higgsfield referral is approved. Krea and Magnific use their official URLs until affiliate IDs exist.
HF_FPR = "emmanuel-bbfe0e"
HF_BASE = "https://higgsfield.ai?fpr=" + HF_FPR
AFF = {
 "Higgsfield": HF_BASE,
 "Higgsfield API": "https://open.higgsfield.ai?fpr=" + HF_FPR,
}
def is_higgsfield(url):
    host = (urlsplit(url or "").hostname or "").lower()
    return host == "higgsfield.ai" or host.endswith(".higgsfield.ai")

def with_fpr(url):
    """Higgsfield affiliate URL: homepage uses the approved base; other pages keep their path."""
    if not url or not is_higgsfield(url):
        return url
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    if host == "higgsfield.ai" and parts.path in ("", "/"):
        return HF_BASE
    pairs = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k not in ("fpr", "ref")]
    pairs.append(("fpr", HF_FPR))
    return urlunsplit((parts.scheme or "https", parts.netloc, parts.path, urlencode(pairs), parts.fragment))

def outbound(url):
    """Return (href, rel) for an external link, tagging approved Higgsfield URLs as affiliate."""
    if is_higgsfield(url):
        return with_fpr(url), "sponsored nofollow noopener"
    return url, "nofollow noopener"

def json_link(path, label):
    """Fetchable data file. nofollow so the link is not a hint to index the JSON."""
    return f'<a href="{html.escape(root(path))}" rel="nofollow">{html.escape(label)}</a>'

def plat_link(p, url):
    if p in ("Higgsfield", "Higgsfield API") or is_higgsfield(url):
        href = with_fpr(url) if is_higgsfield(url) else AFF.get(p, HF_BASE)
        return f'<a href="{html.escape(href)}" rel="sponsored nofollow noopener" target="_blank">{html.escape(p)}</a>'
    if p in AFF: return f'<a href="{AFF[p]}" rel="sponsored nofollow noopener" target="_blank" data-affiliate="TODO">{html.escape(p)}</a>'
    return f'<a href="{html.escape(url)}" rel="nofollow noopener" target="_blank">{html.escape(p)}</a>'
e = html.escape
HOUSE_LINE = "Your tool here: sponsor this spot"
SPONSOR_REL = "sponsored nofollow noopener"
EDITOR_NAME = "Emmanuel Gonzalez"
EDITOR_LD = {"@type": "Person", "name": EDITOR_NAME}

def sponsor_record(slot_id):
    """home, deals, or model:<slug>. A missing model slot uses model:default."""
    rec = sponsors.get(slot_id)
    if rec is None and slot_id.startswith("model:"):
        rec = sponsors.get("model:default")
    return rec or {}

def sponsor_filled(rec):
    return bool(rec.get("active") and (rec.get("name") or "").strip() and (rec.get("url") or "").strip())

def render_sponsor(slot_id, rec, featured=False):
    cls = "sponsor"
    if featured:
        cls += " sponsor-featured"
    if not sponsor_filled(rec):
        cls += " is-open"
    bits = ['<span class="sponsor-label">Sponsor</span>']
    if featured:
        bits.append('<span class="sponsor-kicker">Featured</span>')
    if sponsor_filled(rec):
        bits.append(
            f'<a href="{e(rec["url"].strip())}" rel="{SPONSOR_REL}" target="_blank">{e(rec["name"].strip())}</a>'
        )
        tagline = (rec.get("tagline") or "").strip()
        if tagline:
            bits.append(f'<span class="sponsor-line">{e(tagline)}</span>')
    else:
        bits.append(f'<a class="sponsor-open" href="{root("/advertise/")}">{HOUSE_LINE}</a>')
    return f'<aside class="{cls}" data-sponsor="{e(slot_id)}">{"".join(bits)}</aside>'

def sponsor_slot(slot_id, featured=False):
    """Filled placements stay. An empty house placeholder is not rendered."""
    rec = sponsor_record(slot_id)
    if not sponsor_filled(rec):
        return ""
    return render_sponsor(slot_id, rec, featured)

def public_gap(item):
    """Public wording for a price the catalog does not include. The data reason stays in the file."""
    name = (item.get("item") or "").strip().rstrip(".")
    reason = (item.get("reason") or "").strip().rstrip(".")
    known = {
        "pricing not rendered without login/region; check manually":
            "The pricing page did not show a price without a login or a region, so there is no dollars-per-second row.",
        "discount not reflected on model page; not applied":
            "The model page did not show that discount on the price, so it is not in the table.",
        "model page shows no static price":
            "The model page did not show a static price, so there is no row.",
        "plan page only says '~80 Seedance 2.5 videos' for 1,200 credits without clip length/resolution":
            "The plan page says '~80 Seedance 2.5 videos' for 1,200 credits and does not give clip length or resolution, so there is no dollars-per-second row.",
        "compare table says ~7 credits/5s at 720p, plan quiz says ≈14 credits per 8s 720p; both approximate":
            "The compare table says ~7 credits/5s at 720p and the plan quiz says ≈14 credits per 8s 720p. Those two figures disagree, so neither is a dollars-per-second row.",
        "count column appears to assume a 40k pack, price for that pack not shown; Max omitted":
            "The count column uses a 40k pack whose price is not shown, so Max has no row.",
        "official API page lists per-second rates, but input video changes the billed duration, so no single $/s is in the table":
            "The official API page lists per-second rates, and input video changes the billed duration, so there is no single dollars-per-second row.",
    }
    sentence = known.get(reason)
    if sentence is None:
        cleaned = reason.replace("check manually", "not shown on the fetched page")
        cleaned = cleaned.replace("price file", "price table")
        cleaned = cleaned.replace("when site built", "on the date checked")
        if cleaned:
            sentence = cleaned[0].upper() + cleaned[1:]
            if not sentence.endswith("."):
                sentence += "."
        else:
            sentence = "No dollars-per-second row."
    return f"{name}: {sentence}" if name else sentence
def money(v):
    """Shared with the page scripts: up to 5 decimals, half up, trailing zeros trimmed to 2."""
    n = int((Decimal(str(v)) * Decimal(100000)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    neg = n < 0
    n = abs(n)
    whole, frac = divmod(n, 100000)
    digits = f"{frac:05d}".rstrip("0")
    if len(digits) < 2:
        digits = f"{frac:05d}"[:2]
    return f"{'-' if neg else ''}${whole}.{digits}"

def _money_places(v, places, min_digits=2):
    """Half-up display. Calculations stay at full precision; only the shown text is rounded."""
    q = Decimal("1").scaleb(-places)
    n = Decimal(str(v)).quantize(q, rounding=ROUND_HALF_UP)
    neg = n < 0
    text = f"{abs(n):.{places}f}"
    whole, frac = text.split(".")
    frac = frac.rstrip("0")
    if len(frac) < min_digits:
        frac = frac.ljust(min_digits, "0")
    return f"{'-' if neg else ''}${whole}.{frac}"

def clip_money(v):
    """Calculator $/clip: 4 decimal places, half up. $/sec stays on money() at 5."""
    return _money_places(v, 4)

def rate_money(v):
    """$/s on the guides: 4 decimal places under $0.10, otherwise 3. At most 4 decimals."""
    places = 3 if abs(Decimal(str(v))) >= Decimal("0.1") else 4
    return _money_places(v, places)

def cost_money(v):
    """Dollar totals and per-1,000-credit costs: 2 decimal places."""
    return _money_places(v, 2, min_digits=2)

def ld_script(obj):
    raw = json.dumps(obj, ensure_ascii=False).replace("<", "\\u003c")
    return f'<script type="application/ld+json">{raw}</script>'

def ld_join(*objs):
    return "".join(ld_script(obj) for obj in objs)

def breadcrumb_ld(crumbs):
    """crumbs are (visible name, site path) in order, matching the on-page trail."""
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": name, "item": SITE_URL + path}
            for i, (name, path) in enumerate(crumbs, 1)
        ],
    }

def item_list_ld(name, entries):
    """entries are (visible name, site path)."""
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": name,
        "numberOfItems": len(entries),
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": label, "url": SITE_URL + path}
            for i, (label, path) in enumerate(entries, 1)
        ],
    }

def rfc822_day(day):
    """UTC midnight of a real calendar date. Not the build clock."""
    dt = datetime.datetime.combine(
        datetime.date.fromisoformat(day), datetime.time(0, 0), datetime.timezone.utc)
    return email.utils.formatdate(dt.timestamp(), usegmt=True)

def change_anchor(change):
    bits = [
        change.get("date") or "",
        change.get("type") or "",
        str(change.get("row") or ""),
        change.get("model") or "",
        change.get("platform") or "",
        change.get("variant") or "",
        change.get("resolution") or "",
        change.get("text") or "",
    ]
    return "change-" + hashlib.sha1("\n".join(bits).encode()).hexdigest()[:16]

def change_plain(change):
    if change.get("type") == "price" and change.get("model") in models:
        return (
            f"{models[change['model']]['name']} on {change.get('platform') or ''} "
            f"({change.get('variant') or ''}, {change.get('resolution') or ''}): "
            f"{money(change.get('old_usd_per_second'))} → {money(change.get('new_usd_per_second'))}/s"
        )
    return change.get("text") or change.get("type") or "Price change"

def with_affiliate_note(body):
    """Short disclosure under the title on pages that contain affiliate links."""
    if 'rel="sponsored' not in body:
        return body
    if 'id="disclosure"' in body or "/about/#disclosure" in body:
        return body
    note = affiliate_note_html()
    marker = byline_html()
    if marker in body:
        return body.replace(marker, marker + note, 1)
    end = body.find("</h1>")
    if end == -1:
        return note + body
    end += len("</h1>")
    return body[:end] + note + body[end:]

def page(path, title, desc, body, active="", extra_head="", dest=None, reports_nav=None, robots="index,follow", canonical=True, before_count=""):
    body = with_affiliate_note(body)
    canon = SITE_URL + path
    show_reports = REPORTS_ENABLED if reports_nav is None else reports_nav
    navs = [("/", "Prices"), ("/deals/", "Deals"), ("/calculator/", "Credit calculator"), ("/guides/", "Guides"), ("/changes/", "Price changes"), ("/data/", "Data")]
    if show_reports:
        navs.append(("/reports/", "Reports"))
    navs.append(("/about/", "About"))
    nav = "".join(f'<a href="{root(h)}"{" class=on" if h==active else ""}>{t}</a>' for h, t in navs)
    modlinks = " · ".join(f'<a href="{root(f"/models/{s}/")}">{e(m["name"])}</a>' for s, m in models.items())
    guidelinks = " · ".join(f'<a href="{root(h)}">{label}</a>' for h, label in GUIDE_LINKS)
    canon_html = f'<link rel="canonical" href="{canon}">' if canonical else ""
    og_url_html = f'<meta property="og:url" content="{canon}">' if canonical else ""
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="google-site-verification" content="nlx0gVcAU_holiR5TLbIUc0ECk-VPLUPKHiVqlGNCIM" />
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
{canon_html}<meta name="robots" content="{robots}">
<meta property="og:type" content="website"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
{og_url_html}<meta property="og:site_name" content="{BRAND}">
<meta property="og:image" content="{OG_IMAGE}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="{e(OG_ALT)}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(desc)}"><meta name="twitter:image" content="{OG_IMAGE}">
<meta name="theme-color" content="#0b0d12"><link rel="icon" href="{root("/favicon.ico")}" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="{root("/favicon-32.png")}"><link rel="icon" type="image/svg+xml" href="{root("/logo.svg")}"><link rel="apple-touch-icon" href="{root("/logo-512.png")}">
<link rel="alternate" type="application/rss+xml" title="{BRAND}" href="{root("/feed.xml")}">
<link rel="stylesheet" href="{root("/style.css")}">{extra_head}</head><body>
<header class="top"><div class="wrap"><a class="logo" href="{root("/")}">Vid<span>Fare</span></a><nav>{nav}</nav></div></header>
<main class="wrap">{body}</main>
<footer><div class="wrap"><p><b>Models:</b> {modlinks}</p>
<p><b>Guides:</b> {guidelinks}</p>
<p>Prices are copied from each vendor's own pricing page, with the date we checked. Always confirm on the vendor's page before you buy. Some links are affiliate links (<a class="disc" href="{root("/about/#disclosure")}">disclosure</a>).</p>
<p>© {today.year} {BRAND} · Data last checked {LAST} · <a href="{root("/data/")}">Price data</a> · <a href="{root("/advertise/")}">Advertise</a> · <a href="{root("/contact/")}">Contact</a> · <a href="https://twelve.tools">Twelve Tools</a></p></div></footer>
{before_count}<script data-goatcounter="https://vidfare.goatcounter.com/count"
        async src="https://gc.zgo.at/count.js"></script>
</body></html>"""
    base_dir = DIST if dest is None else dest
    out = os.path.join(base_dir, path.strip("/"), "index.html") if path.endswith("/") else os.path.join(base_dir, path.strip("/"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w").write(doc)

def write_report_pages(dest, as_of, reports_nav=None, public_log=False):
    """Write /reports/ and any week that has at least two qualifying changes."""
    events = weekly_report.load()
    result = weekly_report.assign(events, as_of)
    paths = ["/reports/"]
    record_dates = dest in (None, DIST)
    if record_dates:
        SITEMAP_LASTMOD["/reports/"] = weekly_report.index_content_date(result, events, as_of) or LAST
    page("/reports/", f"{weekly_report.INDEX_H1} | {BRAND}", weekly_report.INDEX_DESCRIPTION,
         weekly_report.render_index_body(result, events, href_fn=root, public_log=public_log),
         "/reports/", ld_script(weekly_report.index_jsonld(SITE_URL + "/reports/")),
         dest=dest, reports_nav=reports_nav)
    prior = None
    for report in result["reports"]:
        path = f"/reports/{report['id']}/"
        headline = weekly_report.report_h1(report)
        description = weekly_report.report_meta(report)
        modified = weekly_report.report_content_date(report, events, prior)
        if record_dates:
            SITEMAP_LASTMOD[path] = modified
        body = weekly_report.render_report_body(
            report, events, prior, link_fn=lambda url: outbound(url))
        linked = weekly_report.report_jsonld(report, SITE_URL + path)
        linked["dateModified"] = modified
        page(path, f"{headline} | {BRAND}", description, body, "/reports/",
             ld_join(
                 linked,
                 breadcrumb_ld([("Reports", "/reports/"), (headline, path)]),
             ),
             dest=dest, reports_nav=reports_nav)
        paths.append(path)
        prior = report["through"]
    if public_log and os.path.isfile(weekly_report.PATH):
        os.makedirs(os.path.join(dest, "data"), exist_ok=True)
        shutil.copy(weekly_report.PATH, os.path.join(dest, "data", "price_changes.jsonl"))
    return paths

def write_report_preview():
    """Local preview only. Dist stays gated by REPORTS_ENABLED."""
    if os.environ.get("VIDFARE_REPORT_PREVIEW") != "1":
        return
    raw = os.environ.get("VIDFARE_AS_OF")
    as_of = datetime.date.fromisoformat(raw) if raw else today
    preview_root = os.environ.get("VIDFARE_PREVIEW_DIR") or os.path.join(ROOT, "preview")
    site_name = BASE.strip("/")
    site = os.path.join(preview_root, site_name) if site_name else preview_root
    if os.path.isdir(site):
        shutil.rmtree(site)
    os.makedirs(site, exist_ok=True)
    for name in ("style.css", "og.png", "favicon-32.png", "logo.svg", "logo-512.png", "logo-240.png", "favicon.ico"):
        src = os.path.join(DIST, name)
        if os.path.isfile(src):
            shutil.copy(src, os.path.join(site, name))
    paths = write_report_pages(site, as_of, reports_nav=True, public_log=False)
    events = weekly_report.load()
    result = weekly_report.assign(events, as_of)
    lines = [
        f"as_of: {as_of.isoformat()}",
        f"published: {', '.join(report['id'] for report in result['reports']) or 'none'}",
        f"pending_price_changes: {len(result['pending'])}",
        f"price_changes_in_log: {len(weekly_report.prices(events))}",
        "pages:",
    ]
    for path in paths:
        lines.append("  " + os.path.join(site, path.strip("/"), "index.html"))
    os.makedirs(preview_root, exist_ok=True)
    open(os.path.join(preview_root, "STATUS.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

def rate_label(r):
    """Visible origin of a $/s figure. A credit-plan estimate is never called a published rate."""
    if r.get("kind") == "plan":
        if r.get("status") == "estimate":
            return "estimated from credit plan"
        return "from credit plan"
    status = r.get("status")
    if status == "estimate":
        return "estimated rate"
    if status == "promo":
        return "promo"
    if status == "discontinued":
        return "discontinued"
    return "published rate"

def tag(r):
    status = r.get("status") if isinstance(r, dict) else r
    label = rate_label(r) if isinstance(r, dict) else {
        "verified": "published rate",
        "estimate": "estimated rate",
        "promo": "promo",
        "discontinued": "discontinued",
    }.get(status, status)
    return f'<span class="tag {status}">{e(label)}</span>'

def source_link(r):
    href, rel = outbound(r["source_url"])
    return f'<a href="{e(href)}" rel="{rel}" target="_blank">source</a>'

def checked_source(r):
    return f'<div class="small">Checked {e(r["checked"])}. {source_link(r)}.</div>'

def byline_html():
    return f'<p class="byline">Edited by {e(EDITOR_NAME)}</p>'

def affiliate_note_html():
    return (
        f'<p class="disclose">Some links on this page are affiliate links. '
        f'<a class="tap" href="{root("/about/#disclosure")}">Affiliate disclosure</a>.</p>'
    )

def ends_fallback(deal):
    cond = dealmod.conditions(deal)
    if not deal.get("end"):
        return "standing price" if cond.get("standing") else "no end date given"
    est = " (estimated)" if deal.get("end_is_estimate") else ""
    return f"until {deal['end']}{est}"

def when_label(deal):
    """Upcoming offers show the start date. Live offers show the end."""
    start = deal.get("start")
    if start and start > TODAY:
        return f"starts {start}"
    return ends_fallback(deal)

def deal_attrs(deal):
    cond = dealmod.conditions(deal)
    return (f'data-deal-end="{e(deal.get("end") or "")}" data-deal-est="{1 if deal.get("end_is_estimate") else 0}" '
            f'data-deal-standing="{1 if cond.get("standing") else 0}" data-deal-start="{e(deal.get("start") or "")}"')

def deal_badges(r):
    bits = []
    for adj in dealmod.row_adjustments(r, LIVE_DEALS, plans, TODAY):
        deal = DEAL_BY_ID[adj["deal_id"]]
        if adj["type"] == "unlimited_window":
            label = "Unlimited"
        elif adj["percent"] is not None:
            label = f"DEAL −{adj['percent']:g}%"
        else:
            label = "DEAL"
        bits.append(
            f'<a class="tag deal" href="{root("/deals/")}#{e(deal["id"])}" {deal_attrs(deal)}>'
            f'{label} · <span class="ends">{e(ends_fallback(deal))}</span></a>'
        )
    return (" " + "".join(bits)) if bits else ""

def deal_price_line(rs):
    """Name the deal row's variant and origin. A higher price on another plan is not a cut on the headline."""
    best = dealmod.best_deal_price(rs, LIVE_DEALS, plans, TODAY)
    if not best:
        return ""
    deal = DEAL_BY_ID[best["deal_id"]]
    row = best["row"]
    headline = cheapest(rs)
    compared = ""
    if best.get("list_usd") is not None and abs(best["list_usd"] - best["usd"]) > 1e-9:
        compared = f" versus {money(best['list_usd'])}/s at the price this deal compares"
        if best.get("label"):
            compared += f" ({best['label']})"
    detail = (
        f'{e(row["variant"])} on {e(row["platform"])} ({e(spec_phrase(row))}), {e(rate_label(row))}: '
        f'{money(best["usd"])}/s{compared}. Checked {e(row["checked"])}. {source_link(row)}.'
    )
    if headline and row.get("id") != headline.get("id"):
        if best["usd"] + 1e-12 < headline["usd_per_second"]:
            prefix = (
                f'Lower live-deal price on a different option, not a cut on '
                f'{e(headline["variant"])} at {money(headline["usd_per_second"])}/s'
            )
        else:
            prefix = (
                f'Different option, not a cut on {e(headline["variant"])} '
                f'at {money(headline["usd_per_second"])}/s'
            )
    else:
        prefix = "With this live deal"
    return (
        f'<div class="sub" {deal_attrs(deal)}>{prefix}: {detail} '
        f'<span class="ends">{e(ends_fallback(deal))}</span></div>'
    )

TICK_JS = """
function clipDays(end){const p=end.split('-').map(Number);const e=new Date(p[0],p[1]-1,p[2]);const t=new Date();t.setHours(0,0,0,0);return Math.round((e-t)/86400000)}
function clipWhen(end, est, standing){
  if(!end) return standing?'standing price':'limited time, no end date given';
  const days=clipDays(end); if(days<0) return null;
  const x=est?' (estimated)':'';
  if(days===0) return 'ends today'+x;
  return 'ends in '+days+' day'+(days===1?'':'s')+x;
}
function clipTick(){
  const live=document.getElementById('liveDeals');
  const upcoming=document.getElementById('upcomingDeals');
  if(live && upcoming){
    upcoming.querySelectorAll('[data-deal-card]').forEach(card=>{
      const start=card.getAttribute('data-deal-start')||'';
      if(start && clipDays(start)<=0) live.appendChild(card);
    });
    const section=document.getElementById('upcoming');
    if(section) section.hidden=upcoming.querySelector('[data-deal-card]')===null;
  }
  document.querySelectorAll('[data-deal-end]').forEach(el=>{
    const start=el.getAttribute('data-deal-start')||'';
    if(start && clipDays(start)>0){
      const days=clipDays(start);
      const txt='starts in '+days+' day'+(days===1?'':'s');
      const slot=el.querySelector('.ends');
      if(slot) slot.textContent=txt;
      else if(el.classList.contains('when')) el.textContent=txt;
      return;
    }
    const end=el.getAttribute('data-deal-end')||'';
    const txt=clipWhen(end, el.getAttribute('data-deal-est')==='1', el.getAttribute('data-deal-standing')==='1');
    const card=el.closest('[data-deal-card]');
    if(txt===null){
      if(card && card.getAttribute('data-archive')!=='1') card.classList.add('is-past');
      else if(!card) el.classList.add('is-past');
      return;
    }
    const slot=el.querySelector('.ends');
    if(slot) slot.textContent=txt;
    else if(el.classList.contains('when')) el.textContent=txt;
  });
  const strip=document.getElementById('ending');
  if(strip){
    strip.querySelectorAll('[data-deal-card]').forEach(card=>{
      const end=card.getAttribute('data-deal-end')||'';
      if(!end || clipDays(end)<0 || clipDays(end)>7) card.classList.add('is-past');
    });
    strip.hidden=[...strip.querySelectorAll('[data-deal-card]')].every(c=>c.classList.contains('is-past'));
  }
  if(typeof filterDeals==='function') filterDeals();
}
document.addEventListener('DOMContentLoaded', clipTick);
"""

def tick_script():
    return f"<script>{TICK_JS}</script>"

def shown_tier(r):
    """Subscription plan name, or a model tier stored in the resolution field. Otherwise not listed."""
    name = (r.get("plan_name") or "").strip()
    if name:
        return name
    res = str(r.get("resolution") or "").strip()
    if res in TIER_RESOLUTIONS:
        return res
    return "not listed"

def shown_resolution(r):
    res = str(r.get("resolution") or "").strip()
    if res in MISSING_RESOLUTIONS or res in TIER_RESOLUTIONS:
        return "not listed"
    return res

def shown_audio(r):
    """with / without / not stated. Taken from variation when the page was re-read."""
    stated = ((r.get("variation") or {}).get("audio"))
    if stated in ("with", "without", "not stated"):
        return stated
    if r.get("audio") is True:
        return "with"
    if r.get("audio") is False:
        return "without"
    return "not stated"

def audio_phrase(r):
    word = shown_audio(r)
    if word == "not stated":
        return "not stated"
    return word + " audio"

def input_phrase(r):
    stated = (r.get("variation") or {}).get("input")
    if not stated or stated == "not stated":
        return "not stated"
    return ", ".join(variations.INPUT_LABELS.get(x, x) for x in stated)

def length_phrase(r):
    dur = ((r.get("variation") or {}).get("duration") or {})
    rates = dur.get("rate_by_length")
    if isinstance(rates, list) and rates:
        return "; ".join(f"{tier['label']} {money(tier['usd_per_second'])}/s" for tier in rates)
    priced = dur.get("priced_seconds")
    if isinstance(priced, (int, float)) and not isinstance(priced, bool):
        return f"priced at {priced:g}s"
    lo, hi = dur.get("min_seconds"), dur.get("max_seconds")
    if isinstance(lo, (int, float)) and isinstance(hi, (int, float)) and not isinstance(lo, bool):
        return f"{lo:g}–{hi:g}s"
    if isinstance(hi, (int, float)) and not isinstance(hi, bool):
        return f"up to {hi:g}s"
    if isinstance(lo, (int, float)) and not isinstance(lo, bool):
        return f"from {lo:g}s"
    return "not stated"

def modifier_phrase(r):
    mods = (r.get("variation") or {}).get("modifiers")
    if not isinstance(mods, list) or not mods:
        return ""
    bits = []
    for mod in mods:
        usd = mod.get("usd_per_second")
        if isinstance(usd, (int, float)) and not isinstance(usd, bool):
            bits.append(f"{mod['label']} {money(usd)}/s")
        else:
            bits.append(mod["label"])
    return "; ".join(bits)

def fact_lines(r):
    """Audio, input, and length. Not-stated stays visible so a blank is not a guess."""
    extra = modifier_phrase(r)
    also = f'<div class="small">Also: {e(extra)}</div>' if extra else ""
    return (
        f'{e(audio_phrase(r))}'
        f'<div class="small">Input: {e(input_phrase(r))}</div>'
        f'<div class="small">Length: {e(length_phrase(r))}</div>'
        f'{also}'
    )

def spec_phrase(r):
    tier = shown_tier(r)
    # "Pro tier" already ends in tier. Prefixing it reads as "plan tier Pro tier".
    tier_bit = tier if tier.lower().endswith("tier") else f"plan tier {tier}"
    aud = shown_audio(r)
    aud_bit = "audio not stated" if aud == "not stated" else aud + " audio"
    inp = input_phrase(r)
    inp_bit = "input not stated" if inp == "not stated" else "input " + inp
    length = length_phrase(r)
    length_bit = "length not stated" if length == "not stated" else length
    return ", ".join([tier_bit, f"resolution {shown_resolution(r)}", aud_bit, inp_bit, length_bit])

def assumption_text(r):
    """Usage assumption for a credit plan, or the vendor basis for a flagged estimate. Empty otherwise."""
    if r.get("kind") == "plan":
        kind = "Estimated from credit plan. " if r.get("status") == "estimate" else "From credit plan. "
        return kind + "Assumes every credit you pay for is used."
    if r.get("status") == "estimate":
        note = (r.get("note") or "").strip()
        if note:
            return "Estimated rate. " + note
        return "Estimated rate. The vendor marks this rate as approximate."
    return ""

def assumption_html(r):
    text = assumption_text(r)
    if not text:
        return ""
    return f'<div class="assume">{e(text)}</div>'

def row_html(r, fmt=None):
    show = fmt or money
    m = models[r["model"]]["name"]
    extra = e(r["math"]) if r.get("math") else ""
    if r.get("note"): extra += (" " if extra else "") + e(r["note"])
    promo = f' <span class="small">until {r["promo_until"]}</span>' if r.get("promo_until") else ""
    disc = f' <span class="small">discontinued {e(r["discontinued_on"])}</span>' if r.get("discontinued_on") else ""
    return (f'<tr><td><a href="{root(f"/models/{r["model"]}/")}">{e(m)}</a></td><td>{plat_link(r["platform"], r["source_url"])}</td>'
            f'<td>{e(r["variant"])}</td><td>{e(shown_tier(r))}</td><td>{e(shown_resolution(r))}</td><td>{fact_lines(r)}</td>'
            f'<td class="num"><span class="amt">{show(r["usd_per_second"])}</span>{assumption_html(r)}</td>'
            f'<td>{tag(r)}{promo}{deal_badges(r)}{disc}</td><td class="math">{extra}</td>'
            f'<td class="small"><a href="{html.escape(outbound(r["source_url"])[0])}" rel="{outbound(r["source_url"])[1]}" target="_blank">source</a><br>{r["checked"]}</td></tr>')

THEAD = ('<thead><tr><th data-k="model">Model</th><th data-k="platform">Where</th><th data-k="variant">Variant / plan</th>'
         '<th>Plan tier</th><th data-k="resolution">Resolution</th><th>Audio</th>'
         '<th data-k="usd_per_second">$ / sec</th><th data-k="status">Status</th><th>How we got it</th><th data-k="checked">Source</th></tr></thead>')

def cheapest(rs, allow_promo=True):
    rs = [r for r in rs if not discontinued(r) and (allow_promo or r["status"] != "promo")]
    return min(rs, key=lambda r: r["usd_per_second"]) if rs else None

def price_fact(r, platform=True):
    """One price sentence. The dollar amount is the same money() string as the table."""
    where = f" on {r['platform']}" if platform else ""
    text = (
        f"{money(r['usd_per_second'])}/s{where} for {r['variant']}, {spec_phrase(r)}, "
        f"{status_phrase(r)} (checked {r['checked']}, {r['source_url']})"
    )
    assump = assumption_text(r)
    if assump:
        text += ". " + assump.rstrip(".")
    return text

def model_faqs(m, rs, clip5):
    """2–4 Q&As from current rows. Visible text and FAQPage JSON-LD share these strings."""
    name = m["name"]
    c = cheapest(rs)
    faqs = [(
        f"What's the cheapest way to run {name} per second?",
        price_fact(c) + ".",
    )]
    p720 = cheapest([r for r in rs if str(r.get("resolution") or "").strip().lower() == "720p"])
    if p720 and len(faqs) < 4:
        faqs.append((
            f"What's the cheapest 720p option for {name}?",
            price_fact(p720) + ".",
        ))
    if len(faqs) < 4:
        faqs.append((
            f"How much does {name} cost per second?",
            f"As of {c['checked']}, from {money(c['usd_per_second'])}/s ({c['platform']}, {c['variant']}, {shown_resolution(c)}, {status_phrase(c)}, checked {c['checked']}, {c['source_url']}). A 5-second clip at that rate costs about {clip5}.",
        ))
    if len(faqs) < 4:
        c2 = cheapest(rs, False)
        if c2 and c2 is not c:
            faqs.append((
                f"What's the cheapest non-promo price for {name}?",
                price_fact(c2) + ".",
            ))
        else:
            api = cheapest([r for r in rs if r["kind"] == "api"], False)
            if api and api is not c:
                faqs.append((
                    f"What's the cheapest pay-as-you-go API price for {name}?",
                    price_fact(api) + ".",
                ))
    return faqs

def faq_html(faqs):
    blocks = "".join(f"<h3>{e(q)}</h3><p>{e(a)}</p>" for q, a in faqs)
    return f'<h2>FAQ</h2><div class="faq">{blocks}</div>'

def faq_ld(slug, faqs):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "url": f"{SITE_URL}/models/{slug}/",
        "author": EDITOR_LD,
        "editor": EDITOR_LD,
        "publisher": {"@type": "Organization", "name": BRAND, "url": SITE_URL + "/", "logo": LOGO_URL},
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in faqs
        ],
    }

def wide_table(inner, attrs=""):
    """Price table that scrolls sideways on a phone. The hint is hidden at desktop width."""
    return (f'<div class="widewrap"><p class="swipehint">Swipe</p>'
            f'<div class="tblwrap wide"><table{attrs}>{inner}</table></div></div>')

def retired_table(rs, thead=None):
    """Record of rates that are off sale. Not used for cheapest picks."""
    if not rs: return ""
    head = thead or THEAD
    body = "".join(row_html(r) for r in sorted(rs, key=lambda r: (r["model"], r["usd_per_second"])))
    return (f'<h2>Discontinued</h2>'
            f'<p class="small">These rates are off sale. The last price we recorded stays here, and these rows are left out of cheapest picks and the live table.</p>'
            f'{wide_table(head + "<tbody>" + body + "</tbody>", " id=\"retired\"")}')

KIT_SUCCESS = "Thanks! Check your inbox to confirm your subscription."

def news_box():
    """Kit signup. ck.5.js fills data-element success and errors. The form still posts if that script does not load."""
    if not NEWSLETTER_ENABLED:
        return ""
    # ck.5.js reads data-options and, on success, replaces [data-element=fields]
    # with a formkit-alert[data-element=success] whose text is success_message.
    # On failure it appends list items to [data-element=errors]. Double opt-in stays:
    # the message asks for the confirmation email, and the form action is unchanged.
    options = e(json.dumps({
        "settings": {
            "after_subscribe": {
                "action": "message",
                "success_message": KIT_SUCCESS,
                "redirect_url": "",
            }
        }
    }, separators=(",", ":")))
    return f"""<section class="news" id="newsletter"><h2 style="margin-top:0">Get the weekly price-drop email</h2>
<p class="small" style="margin:0">VidFare Weekly: one email every Friday with the AI video models that got cheaper that week. Free, unsubscribe anytime.</p>
<form action="{KIT_FORM_ACTION}" class="seva-form formkit-form" method="post" data-sv-form="{KIT_FORM_ID}" data-uid="{KIT_FORM_UID}" data-format="inline" data-version="5" data-options="{options}">
<div class="formkit-notices" aria-live="polite">
<ul class="formkit-alert formkit-alert-error" data-element="errors" data-group="alert"></ul>
<div data-element="fields" class="seva-fields formkit-fields">
<label class="small" for="newsEmail">Email address</label>
<div class="news-row"><input id="newsEmail" type="email" name="email_address" required placeholder="you@email.com" aria-label="Email address"><button class="btn" data-element="submit" type="submit">Subscribe</button></div>
</div>
</div>
</form>
<p class="small">Check your inbox to confirm. You are not subscribed until you confirm.</p>
<script src="https://f.convertkit.com/ckjs/ck.5.js"></script></section>"""

shutil.rmtree(DIST, ignore_errors=True); os.makedirs(DIST)
shutil.copy(os.path.join(ROOT, "src", "style.css"), DIST)
shutil.copy(os.path.join(ROOT, "src", "og.png"), os.path.join(DIST, "og.png"))
for _f in ("favicon-32.png", "logo.svg", "logo-512.png", "logo-240.png"):
    shutil.copy(os.path.join(ROOT, "src", _f), os.path.join(DIST, _f))

def write_favicon_ico(src_png, dest_ico):
    """Write favicon.ico from the site PNG. The ICO stores that PNG as its image."""
    png = open(src_png, "rb").read()
    if png[:8] != b"\x89PNG\r\n\x1a\n" or png[12:16] != b"IHDR":
        raise SystemExit(f"{src_png} is not a PNG")
    width, height = struct.unpack(">II", png[16:24])
    if not width or not height or width > 256 or height > 256:
        raise SystemExit(f"{src_png} is {width}x{height}; favicon.ico needs a side of 1–256")
    # A side of 256 is stored as 0 in the directory entry.
    entry = struct.pack(
        "<BBBBHHII",
        width % 256,
        height % 256,
        0,
        0,
        1,
        32,
        len(png),
        22,
    )
    open(dest_ico, "wb").write(struct.pack("<HHH", 0, 1, 1) + entry + png)

write_favicon_ico(os.path.join(ROOT, "src", "favicon-32.png"), os.path.join(DIST, "favicon.ico"))
shutil.copy(os.path.join(ROOT, "src", "google43692aaea77cfb47.html"), DIST)
# Actions deploys ignore a repo-root CNAME. The file still has to be in dist,
# which is the directory the Pages artifact uploads.
cname_host = urlparse(SITE_URL).hostname or ""
open(os.path.join(DIST, "CNAME"), "w").write(cname_host + "\n")
open(os.path.join(ROOT, "CNAME"), "w").write(cname_host + "\n")
# upload-pages-artifact omits dot paths unless include-hidden-files is true.
# .nojekyll also stops a Jekyll publish from skipping .well-known.
open(os.path.join(DIST, ".nojekyll"), "w").write("")
auth_src = os.path.join(ROOT, "src", ".well-known", "mcp-registry-auth")
auth_dir = os.path.join(DIST, ".well-known")
os.makedirs(auth_dir, exist_ok=True)
shutil.copy(auth_src, os.path.join(auth_dir, "mcp-registry-auth"))
indexnow_key = notify_indexnow.KEY
open(os.path.join(DIST, indexnow_key + ".txt"), "w").write(indexnow_key + "\n")
os.makedirs(os.path.join(DIST, "data")); shutil.copy(os.path.join(ROOT, "data", "prices.json"), os.path.join(DIST, "data"))

def stamp_published_prices():
    """Add row deal links for the published JSON. Source data keeps explicit promo links only."""
    path = os.path.join(DIST, "data", "prices.json")
    pub = json.load(open(path))
    for r in pub["rows"]:
        ids = list(r.get("deal_ids") or [])
        for deal in LIVE_DEALS:
            if deal["id"] in ids:
                continue
            if dealmod.adjustment(deal, r, plans):
                ids.append(deal["id"])
        if ids:
            r["deal_ids"] = ids
    with open(path, "w") as f:
        json.dump(pub, f, indent=1, ensure_ascii=False)
        f.write("\n")

stamp_published_prices()

def model_rows(slug):
    return [r for r in rows if r["model"] == slug]

def model_pick(slug, allow_promo=True):
    """Same pick as the homepage cards: cheapest() on the current rows for one model."""
    return cheapest(model_rows(slug), allow_promo)

def overall_pick(allow_promo=True):
    """Lowest homepage pick across models. Ties keep the earlier model in the catalog."""
    best = None
    best_i = None
    for i, slug in enumerate(models):
        picked = model_pick(slug, allow_promo)
        if not picked:
            continue
        if best is None or picked["usd_per_second"] < best["usd_per_second"] or (
            picked["usd_per_second"] == best["usd_per_second"] and i < best_i
        ):
            best = picked
            best_i = i
    return best

def status_phrase(r):
    label = rate_label(r)
    if r.get("status") == "promo" and r.get("promo_until"):
        return f"a promo until {r['promo_until']}"
    if r.get("status") == "promo":
        return "a promo"
    if label == "published rate":
        return "a published rate"
    if label == "estimated from credit plan":
        return "estimated from a credit plan"
    if label == "from credit plan":
        return "from a credit plan"
    if label == "estimated rate":
        return "an estimated rate"
    return label

def rate_clause(r):
    """One plain-text price clause. The shown $/s is display-rounded; the row value is unchanged."""
    bit = (
        f"{rate_money(r['usd_per_second'])} per second for {r['variant']} on {r['platform']} "
        f"({spec_phrase(r)}), {status_phrase(r)} (checked {r['checked']}, {r['source_url']})"
    )
    extra = assumption_text(r)
    if extra:
        bit += ". " + extra.rstrip(".")
    return bit

def plan_short_name(name):
    """'Ultra (annual)' reads as 'Ultra annual' in a short comparison."""
    return (name or "").strip().replace(" (", " ").replace(")", "")

def credit_use_assumed(r):
    return "credit you pay for is used" in (assumption_text(r) or "").lower()

def higgsfield_intro(lo, hi):
    """Two sentences. Rates are display-rounded; plan, model, and resolution come from the rows."""
    low = (
        f"{rate_money(lo['usd_per_second'])}/s ({plan_short_name(lo.get('plan_name'))}, "
        f"{shown_resolution(lo)}, {status_phrase(lo)}, checked {lo['checked']}, {lo['source_url']})"
    )
    high_bits = (
        f"{plan_short_name(hi.get('plan_name'))}, {models[hi['model']]['name']} {shown_resolution(hi)}, "
        f"{status_phrase(hi)}, checked {hi['checked']}, {hi['source_url']}"
    )
    text = f"Higgsfield plan rates we track run from {low} to {rate_money(hi['usd_per_second'])}/s ({high_bits})."
    if credit_use_assumed(lo) and credit_use_assumed(hi):
        text += " Both assume every credit you pay for is used."
    return text

def outside_higgsfield(r):
    return r["platform"] not in HF_PLATFORMS

def res_key(r):
    return shown_resolution(r).lower()

def first_min(rs):
    """cheapest(), kept as a named helper for filtered sets."""
    return cheapest(rs)

def row_order(r):
    return r["id"]

def checked_line():
    return f'<p class="small">Last checked {e(LAST)}.</p>'

HOW_PLAIN = (
    "Each dollar figure is a current price row, with the vendor page and the date that page was checked. "
    "A published rate is a dollars-per-second figure on that page, or an API credit count times the credit price the page states. "
    f"A credit-plan figure is plan price ÷ credits × credits per clip ÷ seconds, and it {CREDIT_USE}. "
    'When the vendor marks that count with "~", "roughly", or "estimated", the row is labelled estimated from credit plan and is not a list price. '
    "A promo shows its end date when the vendor gave one. "
    f"The full method is on the about page ({SITE_URL}/about/)."
)
BUDGET_HOW = (
    HOW_PLAIN
    + " Billed seconds are finished minutes times 60 times the retry multiplier. "
    "The estimated total is billed seconds times that row's dollars per second. "
    "A credit-plan rate already spreads the plan price across its credits."
)

def how_block(text=None):
    plain = HOW_PLAIN if text is None else text
    html_text = e(plain).replace(
        e(SITE_URL + "/about/"),
        f'<a href="{root("/about/")}">{e(SITE_URL + "/about/")}</a>',
    )
    return f"<h2>How do we calculate this?</h2><p>{html_text}</p>"

def guide_faq_html(faqs):
    return "".join(f"<h2>{e(q)}</h2><p>{e(a)}</p>" for q, a in faqs)

def guide_faq_ld(path, faqs):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "url": SITE_URL + path,
        "author": EDITOR_LD,
        "editor": EDITOR_LD,
        "publisher": {"@type": "Organization", "name": BRAND, "url": SITE_URL + "/", "logo": LOGO_URL},
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in faqs
        ],
    }

GUIDE_CRUMBS = {
    "/guides/cheapest-wan-3-0/": "Wan 3.0",
    "/guides/cheapest-ai-video-generator/": "Cheapest by model",
    "/guides/is-higgsfield-worth-it/": "Higgsfield",
    "/guides/ai-video-project-budget/": "Project budget",
}

def guide_crosslinks(path):
    """One line under the title. Only guides whose prices the report or the holiday page uses."""
    linked = {
        "/guides/",
        "/guides/cheapest-wan-3-0/",
        "/guides/cheapest-ai-video-generator/",
        "/guides/is-higgsfield-worth-it/",
        "/guides/ai-video-project-budget/",
    }
    if path not in linked:
        return ""
    return crosslink_html(bool(LATEST_REPORT), bool(HOLIDAY_MODEL_SLUGS))

def guide_page(path, title, desc, body, faqs):
    end = body.find("</h1>")
    if end != -1 and byline_html() not in body:
        end += len("</h1>")
        body = body[:end] + byline_html() + body[end:]
    note = guide_crosslinks(path)
    if note and note not in body:
        marker = byline_html()
        if marker in body:
            body = body.replace(marker, marker + note, 1)
        else:
            body = note + body
    raw = json.dumps(faqs, ensure_ascii=False).lower()
    for bad in ("subscribe", "newsletter", "buttondown"):
        if bad in raw:
            raise SystemExit(f"{path} FAQ text contains {bad}")
    blocks = [guide_faq_ld(path, faqs)]
    if path == "/guides/":
        blocks.append(item_list_ld("Guides", [
            ("What is the cheapest way to use Wan 3.0?", "/guides/cheapest-wan-3-0/"),
            ("What is the cheapest AI video generator right now?", "/guides/cheapest-ai-video-generator/"),
            ("Is Higgsfield worth it?", "/guides/is-higgsfield-worth-it/"),
            ("How much does a 3-minute AI video cost?", "/guides/ai-video-project-budget/"),
        ]))
    elif path in GUIDE_CRUMBS:
        blocks.append(breadcrumb_ld([("Guides", "/guides/"), (GUIDE_CRUMBS[path], path)]))
    page(path, title, desc, body, "/guides/", ld_join(*blocks))

def cheap_card(title, r, alt=None):
    alt_html = ""
    if alt is not None and alt is not r:
        alt_html = (
            f'<div class="sub">Without promos: {rate_money(alt["usd_per_second"])}/s for {e(alt["variant"])} '
            f'on {e(alt["platform"])} ({e(spec_phrase(alt))}), {e(rate_label(alt))}. '
            f'Checked {e(alt["checked"])}. {source_link(alt)}.</div>'
        )
        if assumption_text(alt):
            alt_html += assumption_html(alt)
    promo = ""
    if r.get("status") == "promo" and r.get("promo_until"):
        promo = f' <span class="small">until {e(r["promo_until"])}</span>'
    math = ""
    if r.get("kind") == "api" and (r.get("math") or "").strip():
        math = f'<div class="assume">{e(r["math"].strip())}</div>'
    return (
        f'<div class="card"><h3>{e(title)}</h3>'
        f'<div class="big">{rate_money(r["usd_per_second"])}<span class="small">/s</span></div>'
        f'{assumption_html(r)}{math}'
        f'<div class="sub">{e(r["platform"])} · {e(r["variant"])} · {e(spec_phrase(r))} {tag(r)}{promo}</div>'
        f'{checked_source(r)}'
        f'{deal_badges(r)}{alt_html}</div>'
    )

def wan_blurb():
    base = model_pick("wan-3-0")
    prime = model_pick("wan-3-0-prime")
    return f"Wan 3.0 from {rate_clause(base)}. Wan 3.0 Prime from {rate_clause(prime)}."

def cheapest_blurb():
    best = overall_pick()
    return f"The lowest rate we track is {rate_clause(best)}."

def higgsfield_plan_rows():
    return [r for r in rows if r["platform"] == "Higgsfield"]

def hf_blurb():
    picked = cheapest(higgsfield_plan_rows())
    if not picked:
        return "No Higgsfield plan rate is in the current price data."
    return f"The lowest Higgsfield plan rate we track is {rate_clause(picked)}."

def budget_blurb():
    return "Enter finished minutes and a retry multiplier to price each tracked dollars-per-second rate."

def home_guides_html():
    blurbs = {
        "/guides/cheapest-wan-3-0/": wan_blurb,
        "/guides/cheapest-ai-video-generator/": cheapest_blurb,
        "/guides/is-higgsfield-worth-it/": hf_blurb,
        "/guides/ai-video-project-budget/": budget_blurb,
    }
    items = []
    for path, label in GUIDE_LINKS:
        if path == "/guides/":
            continue
        items.append(f'<li><a href="{root(path)}">{e(label)}</a>: {e(blurbs[path]())}</li>')
    return (
        '<h2>Guides</h2>'
        '<p class="small">Written from the same price rows as the table below.</p>'
        f'<ul>{"".join(items)}</ul>'
    )

# ---------- Home ----------
cards = ""
for slug, m in models.items():
    rs = [r for r in rows if r["model"] == slug]
    c = cheapest(rs); c2 = cheapest(rs, False)
    alt = ""
    if c2 and c2 is not c:
        alt = (
            f'<div class="sub">Without promos: {money(c2["usd_per_second"])}/s for {e(c2["variant"])} '
            f'on {e(c2["platform"])} ({e(spec_phrase(c2))}), {e(rate_label(c2))}. '
            f'Checked {e(c2["checked"])}. {source_link(c2)}.</div>'
        )
        if assumption_text(c2):
            alt += assumption_html(c2)
    math = ""
    if c.get("kind") == "api" and (c.get("math") or "").strip():
        math = f'<div class="assume">{e(c["math"].strip())}</div>'
    cards += (f'<div class="card"><h3>{e(m["name"])}</h3><div class="big">{money(c["usd_per_second"])}<span class="small">/s</span></div>'
              f'{assumption_html(c)}{math}'
              f'<div class="sub">{e(c["platform"])} · {e(c["variant"])} · {e(spec_phrase(c))} {tag(c)}</div>'
              f'{checked_source(c)}{alt}'
              f'{deal_price_line(rs)}'
              f'<a class="go" href="{root(f"/models/{slug}/")}">All {len(rs)} prices →</a></div>')
opts = lambda vals: "".join(f'<option value="{e(v)}">{e(l)}</option>' for v, l in vals)
platforms = sorted({r["platform"] for r in rows})
n_published = sum(rate_label(r) == "published rate" for r in rows)
n_plan = sum(rate_label(r) == "from credit plan" for r in rows)
n_plan_est = sum(rate_label(r) == "estimated from credit plan" for r in rows)
n_api_est = sum(rate_label(r) == "estimated rate" for r in rows)
n_promo = sum(r["status"] == "promo" for r in rows)
def ending_strip():
    soon = []
    for deal in LIVE_DEALS:
        if not deal.get("end"):
            continue
        days = (datetime.date.fromisoformat(deal["end"]) - today).days
        if 0 <= days <= 7:
            soon.append((days, deal))
    soon.sort(key=lambda item: (item[0], item[1]["vendor"]))
    if not soon:
        return ""
    cards_html = ""
    for days, deal in soon:
        href, rel = outbound(deal.get("link_url") or deal["source_url"])
        cards_html += (
            f'<a class="card dealcard" data-deal-card data-vendor="{e(deal["vendor"])}" data-type="{e(deal["type"])}" '
            f'{deal_attrs(deal)} href="{root("/deals/")}#{e(deal["id"])}">'
            f'<h3>{e(deal["title"])}</h3><div class="when"><span class="ends">{e(ends_fallback(deal))}</span></div>'
            f'<div class="sub">{e(deal["vendor"])}</div></a>'
        )
    return f'<section class="strip" id="ending"><h2>Deals ending this week</h2><div class="dealgrid">{cards_html}</div><p class="small"><a href="{root("/deals/")}">All deals</a></p></section>'

HOLIDAY_NEEDLES = ("black friday", "cyber monday", "cyber week", "cyber weekend", "holiday sale", "11.11")

def deal_blob(deal):
    return " ".join([
        deal.get("title") or "",
        deal.get("notes") or "",
        deal.get("source_quote") or "",
    ]).lower()

def is_holiday_named(deal):
    blob = deal_blob(deal)
    return any(needle in blob for needle in HOLIDAY_NEEDLES)

def catalog_touch(deal):
    """Catalog models this deal names or adjusts. Empty when the price table has no row for it."""
    found = set()
    for slug in deal.get("models") or []:
        if slug in models:
            found.add(slug)
    for row in rows:
        if deal.get("id") in (row.get("deal_ids") or []) or dealmod.adjustment(deal, row, plans):
            if row.get("model") in models:
                found.add(row["model"])
    return found

def featured_deal_slugs():
    slugs = set()
    for deal in LIVE_DEALS:
        touched = catalog_touch(deal)
        if is_holiday_named(deal) or (deal.get("end") and touched):
            slugs |= touched
    return slugs

REPORT_EVENTS = weekly_report.load() if REPORTS_ENABLED else []
REPORT_RESULT = weekly_report.assign(REPORT_EVENTS, today) if REPORTS_ENABLED else {"reports": [], "pending": []}
LATEST_REPORT = REPORT_RESULT["reports"][-1] if REPORT_RESULT.get("reports") else None

def report_model_slugs(report):
    if not report:
        return set()
    published = REPORT_RESULT.get("reports") or []
    index = next((i for i, item in enumerate(published) if item.get("id") == report.get("id")), 0)
    prior = published[index - 1]["through"] if index else None
    slugs = set()
    for event in report.get("changes") or []:
        if event.get("model") in models:
            slugs.add(event["model"])
        deal = DEAL_BY_ID.get(event.get("deal_id") or "")
        if deal:
            for slug in deal.get("models") or []:
                if slug in models:
                    slugs.add(slug)
    catalog = weekly_report.catalog_for(REPORT_EVENTS, report["through"], prior)
    for event in catalog.get("added") or []:
        if event.get("model") in models:
            slugs.add(event["model"])
    return slugs

REPORT_MODEL_SLUGS = report_model_slugs(LATEST_REPORT)
HOLIDAY_MODEL_SLUGS = featured_deal_slugs()

def crosslink_html(include_report, include_holiday, report_label="Latest weekly report"):
    bits = []
    if include_report and LATEST_REPORT:
        bits.append(f'<a href="{root(f"/reports/{LATEST_REPORT["id"]}/")}">{e(report_label)}</a>')
    if include_holiday:
        bits.append(f'<a href="{root("/deals/black-friday/")}">Black Friday and holiday deals</a>')
    if not bits:
        return ""
    return '<p class="small">' + " · ".join(bits) + "</p>"

home = f"""<h1>{e(AGENT_H1)}</h1>
<p class="tagline">{e(TAGLINE)}</p>
<section class="strip" id="for-agents">
<h2>What an agent can ask</h2>
<p>The MCP server reads these prices and the deals on this site. It does not invent a price. An agent can ask for:</p>
<ul>
<li>the cheapest model for a length and resolution, such as 5 seconds at 720p</li>
<li>current deals</li>
<li>a cost estimate for a project</li>
</ul>
<p><a href="{root("/mcp/")}">Connect your agent</a></p>
</section>
<p class="lead">{len(rows)} prices for {len(models)} video models on {len(platforms)} platforms, from Higgsfield plans to the fal, Runway and Kling APIs. Everything is converted to <b>dollars per second of video</b>, and the math is shown for credit plans. Checked {LAST}. The table below stays for people.</p>
{sponsor_slot("home")}
{ending_strip()}
<h2>Cheapest way to run each model today</h2><div class="cards">{cards}</div>
<p class="small">The lowest $/s for each model at any resolution, including temporary promos (labelled). Low-res tiers are usually the cheapest, so check the resolution.</p>
{home_guides_html()}
{crosslink_html(True, True)}
<h2>All prices</h2>
<div class="filters">
<select id="fModel" aria-label="Model"><option value="">All models</option>{opts([(s, m["name"]) for s, m in models.items()])}</select>
<select id="fPlat" aria-label="Platform"><option value="">All platforms</option>{opts([(p, p) for p in platforms])}</select>
<select id="fKind" aria-label="Type"><option value="">API + plans</option><option value="api">Pay-as-you-go API</option><option value="plan">Subscription plans</option></select>
<input id="fRes" placeholder="Resolution e.g. 720p" aria-label="Resolution" size="16">
<label class="chk" for="fPromo"><input type="checkbox" id="fPromo"> hide promos</label>
<label class="chk" for="fEst"><input type="checkbox" id="fEst"> hide estimates</label>
<span class="small" id="count"></span></div>
{wide_table(THEAD + "<tbody>" + "".join(row_html(r) for r in sorted(rows, key=lambda r: r["usd_per_second"])) + "</tbody>", ' id="prices"')}
<p class="small"><span class="tag verified">published rate</span> = the vendor states this dollars per second, or states an API credit count and a credit price (Runway credits are $0.01). <span class="tag verified">from credit plan</span> = plan price ÷ credits × credits per clip ÷ seconds, using a credit count the vendor stated exactly. It is not a list price per second. <span class="tag estimate">estimated from credit plan</span> = the same credit-plan math when the vendor marks the count with "~", "roughly", or "estimated". <span class="tag estimate">estimated rate</span> = an API price the vendor calls approximate. <span class="tag promo">promo</span> = a temporary discount, with the end date when the vendor gave one. <span class="tag discontinued">discontinued</span> = the vendor has shut the endpoint down; the last recorded rate is not a current price. Of {len(rows)} live rows: {n_published} published rates, {n_plan} from a credit plan, {n_plan_est} estimated from a credit plan, {n_api_est} estimated API rates, {n_promo} promos.</p>
{news_box()}
{retired_table(retired_rows)}
<script>
{TICK_JS}
const BASE={json.dumps(BASE)};
const AFF={json.dumps(AFF)};
const MODELS={json.dumps({k:v["name"] for k,v in models.items()})};
const DEALS={json.dumps([{
    "id": d["id"], "percent": d.get("percent"), "end": d.get("end") or "",
    "end_is_estimate": bool(d.get("end_is_estimate")),
    "standing": bool(dealmod.conditions(d).get("standing")), "type": d["type"],
} for d in LIVE_DEALS])};
let DATA=[];fetch(BASE+'/data/prices.json').then(r=>r.json()).then(d=>{{DATA=d.rows;render();}});
let sortK='usd_per_second',dir=1;
const $=id=>document.getElementById(id);
function esc(s){{return String(s??'').replace(/[&<>"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]))}}
function money(v){{const n=Math.round(Number(v)*100000);const neg=n<0,a=Math.abs(n),whole=Math.floor(a/100000);let digits=String(a%100000).padStart(5,'0').replace(/0+$/,'');if(digits.length<2)digits=String(a%100000).padStart(5,'0').slice(0,2);return (neg?'-':'')+'$'+whole+'.'+digits}}
function rateLabel(r){{if(r.kind==='plan')return r.status==='estimate'?'estimated from credit plan':'from credit plan';if(r.status==='estimate')return 'estimated rate';if(r.status==='promo')return 'promo';if(r.status==='discontinued')return 'discontinued';return 'published rate'}}
function tag(r){{const s=r.status;return `<span class="tag ${{s}}">${{esc(rateLabel(r))}}</span>`}}
function current(r){{const today=new Date().toISOString().slice(0,10);if(r.status==='discontinued')return false;if(r.promo_until&&r.promo_until<today)return false;if(r.discontinued_on&&r.discontinued_on<today)return false;return true}}
function hf(url){{try{{const u=new URL(url);const h=u.hostname;if(h!=='higgsfield.ai'&&!h.endsWith('.higgsfield.ai'))return null;if(h==='higgsfield.ai'&&(u.pathname===''||u.pathname==='/'))return {json.dumps(HF_BASE)};u.searchParams.delete('ref');u.searchParams.set('fpr',{json.dumps(HF_FPR)});return u.toString()}}catch(e){{return null}}}}
function plat(r){{const tracked=hf(r.source_url);if(tracked)return `<a href="${{esc(tracked)}}" rel="sponsored nofollow noopener" target="_blank">${{esc(r.platform)}}</a>`;const a=AFF[r.platform];return a?`<a href="${{esc(a)}}" rel="sponsored nofollow noopener" target="_blank" data-affiliate="TODO">${{esc(r.platform)}}</a>`:`<a href="${{esc(r.source_url)}}" rel="nofollow noopener" target="_blank">${{esc(r.platform)}}</a>`}}
function tierOf(r){{const name=String(r.plan_name||'').trim();if(name)return name;const res=String(r.resolution||'').trim();if(res==='Pro tier'||res==='Pro'||res==='Standard')return res;return 'not listed'}}
function resOf(r){{const res=String(r.resolution||'').trim();if(!res||res==='—'||res==='-'||res==='–'||res==='Pro tier'||res==='Pro'||res==='Standard')return 'not listed';return res}}
function audioOf(r){{const a=r.variation&&r.variation.audio;if(a==='with')return 'with audio';if(a==='without')return 'without audio';return 'not stated'}}
function inputOf(r){{const inp=r.variation&&r.variation.input;const names={{t2v:'text-to-video',i2v:'image-to-video',ref2v:'reference',v2v:'video-to-video',extend:'extend','lip-sync':'lip-sync'}};if(!inp||inp==='not stated')return 'not stated';return inp.map(x=>names[x]||x).join(', ')}}
function lengthOf(r){{const d=(r.variation&&r.variation.duration)||{{}};if(Array.isArray(d.rate_by_length))return d.rate_by_length.map(t=>t.label+' '+money(t.usd_per_second)+'/s').join('; ');if(typeof d.priced_seconds==='number')return 'priced at '+d.priced_seconds+'s';if(typeof d.min_seconds==='number'&&typeof d.max_seconds==='number')return d.min_seconds+'\u2013'+d.max_seconds+'s';if(typeof d.max_seconds==='number')return 'up to '+d.max_seconds+'s';if(typeof d.min_seconds==='number')return 'from '+d.min_seconds+'s';return 'not stated'}}
function modifierOf(r){{const mods=r.variation&&r.variation.modifiers; if(!Array.isArray(mods)) return ''; return mods.map(m=>typeof m.usd_per_second==='number'?m.label+' '+money(m.usd_per_second)+'/s':m.label).join('; ')}}
function factLines(r){{const also=modifierOf(r); return esc(audioOf(r))+'<div class="small">Input: '+esc(inputOf(r))+'</div><div class="small">Length: '+esc(lengthOf(r))+'</div>'+(also?'<div class="small">Also: '+esc(also)+'</div>':'')}}
function assumptionOf(r){{if(r.kind==='plan')return (r.status==='estimate'?'Estimated from credit plan. ':'From credit plan. ')+'Assumes every credit you pay for is used.';if(r.status==='estimate'){{const note=String(r.note||'').trim();return note?'Estimated rate. '+note:'Estimated rate. The vendor marks this rate as approximate.'}}return ''}}
function render(){{
 const fm=$('fModel').value,fp=$('fPlat').value,fk=$('fKind').value,fr=$('fRes').value.trim().toLowerCase();
 let rs=DATA.filter(r=>current(r)&&(!fm||r.model==fm)&&(!fp||r.platform==fp)&&(!fk||r.kind==fk)&&(!fr||String(r.resolution).toLowerCase().includes(fr))&&!($('fPromo').checked&&r.status=='promo')&&!($('fEst').checked&&r.status=='estimate'));
 rs.sort((a,b)=>{{let x=a[sortK],y=b[sortK];if(sortK=='model'){{x=MODELS[x];y=MODELS[y]}}return (x>y?1:x<y?-1:0)*dir}});
 document.querySelector('#prices tbody').innerHTML=rs.map(r=>{{
  const extra=[r.math,r.note].filter(Boolean).map(esc).join(' ');
  const promo=r.promo_until?` <span class="small">until ${{r.promo_until}}</span>`:'';
  const disc=r.discontinued_on?` <span class="small">discontinued ${{esc(r.discontinued_on)}}</span>`:'';
  const badges=(r.deal_ids||[]).map(id=>{{
    const d=DEALS.find(x=>x.id===id); if(!d||typeof clipWhen!=='function') return '';
    const when=clipWhen(d.end||'', !!d.end_is_estimate, !!d.standing); if(when===null) return '';
    const label=d.type==='unlimited_window'?'Unlimited':(d.percent!=null?`DEAL −${{d.percent}}%`:'DEAL');
    return `<a class="tag deal" href="${{BASE}}/deals/#${{d.id}}" data-deal-end="${{d.end||''}}" data-deal-est="${{d.end_is_estimate?1:0}}" data-deal-standing="${{d.standing?1:0}}">${{label}} · <span class="ends">${{when}}</span></a>`;
  }}).join('');
  const src=hf(r.source_url),srcHref=src||r.source_url,srcRel=src?'sponsored nofollow noopener':'nofollow noopener';
  const assume=assumptionOf(r);
  const assumeHtml=assume?`<div class="assume">${{esc(assume)}}</div>`:'';
  return `<tr><td><a href="${{BASE}}/models/${{r.model}}/">${{esc(MODELS[r.model])}}</a></td><td>${{plat(r)}}</td><td>${{esc(r.variant)}}</td><td>${{esc(tierOf(r))}}</td><td>${{esc(resOf(r))}}</td><td>${{factLines(r)}}</td><td class="num"><span class="amt">${{money(r.usd_per_second)}}</span>${{assumeHtml}}</td><td>${{tag(r)}}${{promo}}${{badges}}${{disc}}</td><td class="math">${{extra}}</td><td class="small"><a href="${{esc(srcHref)}}" rel="${{srcRel}}" target="_blank">source</a><br>${{r.checked}}</td></tr>`}}).join('');
 $('count').textContent=rs.length+' rows';
 document.querySelectorAll('#prices th').forEach(th=>{{th.classList.remove('sorted-asc','sorted-desc');if(th.dataset.k==sortK)th.classList.add(dir>0?'sorted-asc':'sorted-desc')}});
 if(window.clipTick) clipTick();
}}
['fModel','fPlat','fKind','fRes','fPromo','fEst'].forEach(id=>$(id).addEventListener('input',render));
document.querySelectorAll('#prices th[data-k]').forEach(th=>th.addEventListener('click',()=>{{const k=th.dataset.k;dir=(sortK==k)?-dir:1;sortK=k;render()}}));
</script>
{tick_script()}"""
home_ld = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "Organization",
            "@id": ORG_ID,
            "name": BRAND,
            "url": SITE_URL + "/",
            "logo": LOGO_URL,
            "founder": {"@type": "Person", "name": "Emmanuel Gonzalez"},
        },
        {
            "@type": "WebSite",
            "name": BRAND,
            "url": SITE_URL + "/",
            "description": HOME_DESC,
            "image": LOGO_URL,
            "publisher": {"@id": ORG_ID},
        },
        {
            "@type": "Dataset",
            "name": f"{BRAND} AI video prices",
            "description": (
                f"{len(rows)} current prices in USD per second of finished video, "
                f"for {len(models)} models on {len(platforms)} platforms. Last full check {LAST}."
            ),
            "url": SITE_URL + "/",
            "dateModified": LAST,
            "creator": {"@id": ORG_ID},
            "distribution": {
                "@type": "DataDownload",
                "encodingFormat": "application/json",
                "contentUrl": SITE_URL + "/data/prices.json",
            },
            "temporalCoverage": LAST,
            "isAccessibleForFree": True,
            "keywords": [m["name"] for m in models.values()],
        },
    ],
}
page("/", HOME_TITLE, HOME_DESC, home, "/", ld_script(home_ld))

def cond_bits(deal):
    c = dealmod.conditions(deal)
    bits = []
    if c.get("new_users_only"): bits.append("new users only")
    if c.get("annual_only"): bits.append("annual billing")
    if c.get("first_months"): bits.append(f"first {c['first_months']} months")
    if c.get("free_months"): bits.append(f"{c['free_months']} months free")
    if c.get("signup_window_days"): bits.append(f"{c['signup_window_days']} days from signup")
    if c.get("max_resolution"): bits.append(f"capped at {c['max_resolution']}")
    if c.get("web_only"): bits.append("web app only")
    if c.get("code"): bits.append(f"code {c['code']}")
    if c.get("standing"): bits.append("standing price")
    return bits

def example_items(deal, rowset):
    math = deal.get("math")
    items = []
    if math == "stated":
        for ex in dealmod.stated_examples(deal, rowset, 4):
            items.append(f"{ex['label']}: {money(ex['usd'])}/s, list {money(ex['list_usd'])}/s")
    elif math == "plan_price":
        for ex in dealmod.plan_examples(deal, rowset, plans, 4):
            if ex.get("price_before") is not None and ex.get("price_after") is not None:
                price = f"${ex['price_before']:g} → ${ex['price_after']:g}/mo"
            elif ex.get("price_after") is not None:
                price = f"${ex['price_after']:g}/mo"
            else:
                price = "checkout price not listed"
            extra = ""
            if ex.get("usd") is not None:
                name = models.get(ex.get("model") or "", {}).get("name", "")
                variant = ex.get("variant") or ""
                res = str(ex.get("resolution") or "").strip()
                res_bit = "resolution not listed" if res in MISSING_RESOLUTIONS else res
                origin = rate_label({"kind": ex.get("kind"), "status": ex.get("status")})
                extra = (
                    f" · {name}, {variant}, {res_bit}: {money(ex['usd'])}/s vs {money(ex['list_usd'])}/s"
                    f" ({origin})"
                )
                if ex.get("blended_usd") is not None:
                    extra += f" · 12-month blended {money(ex['blended_usd'])}/s"
            items.append(f"{ex['label']}: {price}{extra}")
    elif math == "unlimited":
        for ex in dealmod.unlimited_examples(deal, rowset, plans, 6):
            name = models.get(ex.get("model") or "", {}).get("name", ex.get("model") or "")
            items.append(
                f"Unlimited on {ex['plan']} (${ex['plan_price']:g}) versus {name} {ex.get('resolution')} "
                f"at {money(ex['list_usd'])}/s. Worth it after {ex['breakeven_seconds']:.0f} seconds."
            )
    return items

def deal_source_urls(deal):
    """Primary source_url, then any extra citations in sources."""
    urls = []
    primary = deal.get("source_url")
    if primary:
        urls.append(primary)
    for extra in deal.get("sources") or []:
        url = extra.get("url") if isinstance(extra, dict) else extra
        if url and url not in urls:
            urls.append(url)
    return urls

def deal_source_links(deal):
    links = []
    for url in deal_source_urls(deal):
        href, rel = outbound(url)
        links.append(f'<a class="small" href="{e(href)}" rel="{rel}" target="_blank">source</a>')
    return " ".join(links)

_URL_RE = re.compile(r"https?://[^\s<>\"']+")

def linkify_note(text, vendor=""):
    """Turn a bare URL in a deal note into a short link. The visible words are not the URL."""
    parts = []
    last = 0
    for match in _URL_RE.finditer(text or ""):
        parts.append(e(text[last:match.start()]))
        url = match.group(0)
        tail = ""
        while url and url[-1] in ".,);":
            tail = url[-1] + tail
            url = url[:-1]
        host = (urlparse(url).hostname or "").lower()
        if host == "x.com" or host.endswith(".x.com") or host == "twitter.com" or host.endswith(".twitter.com"):
            label = f"{vendor}'s post" if vendor else "post"
        else:
            label = host[4:] if host.startswith("www.") else (host or "link")
        href, rel = outbound(url)
        parts.append(f'<a href="{e(href)}" rel="{rel}" target="_blank">{e(label)}</a>')
        parts.append(e(tail))
        last = match.end()
    parts.append(e(text[last:] if text else ""))
    return "".join(parts)

def deal_card(deal, archive=False, rowset=None):
    href, rel = outbound(deal.get("link_url") or deal["source_url"])
    bits = cond_bits(deal)
    examples = [] if archive else example_items(deal, rows if rowset is None else rowset)
    ex_html = ("<ul class='ex'>" + "".join(f"<li>{e(item)}</li>" for item in examples) + "</ul>") if examples else ""
    if archive and deal.get("end"):
        when = f"Ended {deal['end']}" + (" (estimated)" if deal.get("end_is_estimate") else "")
    elif archive and deal.get("start"):
        when = f"Ended · posted {deal['start']}"
    elif archive:
        when = "Ended"
    else:
        when = None
    when_html = e(when) if archive else f'<span class="ends">{e(when_label(deal))}</span>'
    attrs = ' data-archive="1"' if archive else " " + deal_attrs(deal)
    pct = f' <span class="tag deal">−{deal["percent"]:g}%</span>' if deal.get("percent") is not None else ""
    quote = f'<blockquote class="small">“{e(deal.get("source_quote") or "")}”</blockquote>' if deal.get("source_quote") else ""
    note = f'<p class="small">{linkify_note(deal["notes"], deal.get("vendor") or "")}</p>' if deal.get("notes") else ""
    cond = f'<p class="small">{e(" · ".join(bits))}</p>' if bits else ""
    season = f' <span class="tag">2025</span>' if deal.get("season") == "2025" else ""
    return (
        f'<article class="card dealcard" data-deal-card{attrs} data-vendor="{e(deal["vendor"])}" '
        f'data-type="{e(deal["type"])}" id="{e(deal["id"])}">'
        f'<h3>{e(deal.get("title") or deal["id"])}{pct}{season}</h3>'
        f'<div class="when">{when_html}</div>'
        f'<div class="sub">{e(deal["vendor"])} · {e(deal["type"].replace("_", " "))}</div>'
        f'{cond}{quote}{ex_html}{note}'
        f'<p><a class="btn" href="{e(href)}" rel="{rel}" target="_blank">View offer</a> '
        f'{deal_source_links(deal)}</p>'
        f'</article>'
    )

def deals_for_model(slug, rs):
    found = []
    for deal in LIVE_DEALS:
        if deal.get("show_on_rows") is False and slug not in (deal.get("models") or []):
            continue
        if slug in (deal.get("models") or []) or any(dealmod.adjustment(deal, r, plans) for r in rs):
            found.append(deal)
    return found

def model_spread(m, rs):
    """One paragraph from the rows: platforms, resolutions, variants, and the low and high prices."""
    lo = min(rs, key=lambda r: (r["usd_per_second"], r["id"]))
    hi = max(rs, key=lambda r: (r["usd_per_second"], r["id"]))
    plats = sorted({r["platform"] for r in rs})
    ress, variants, counts = [], [], {}
    for r in rs:
        res = shown_resolution(r)
        if res not in ress:
            ress.append(res)
        if r["variant"] not in variants:
            variants.append(r["variant"])
        label = rate_label(r)
        counts[label] = counts.get(label, 0) + 1
    if len(variants) <= 6:
        variant_bit = "Variants: " + ", ".join(variants) + "."
    else:
        variant_bit = f"{len(variants)} variants are in the table."
    high = ""
    if hi["id"] != lo["id"]:
        high = (
            f' Highest is {money(hi["usd_per_second"])}/s for {e(hi["variant"])} on {e(hi["platform"])}, '
            f'{e(rate_label(hi))}, checked {e(hi["checked"])}, {source_link(hi)}.'
        )
    labels = ", ".join(f"{n} {label}" for label, n in counts.items())
    return (
        f'{e(m["name"])} has {len(rs)} current prices on {len(plats)} platforms ({e(", ".join(plats))}). '
        f'Resolutions in the table: {e(", ".join(ress))}. {e(variant_bit)} '
        f'Lowest is {money(lo["usd_per_second"])}/s for {e(lo["variant"])} on {e(lo["platform"])}, '
        f'{e(rate_label(lo))}, checked {e(lo["checked"])}, {source_link(lo)}.{high} '
        f'Labels: {e(labels)}.'
    )

def compared_sentence(prefix, r):
    promo = f", a promo until {e(r['promo_until'])}" if r.get("status") == "promo" and r.get("promo_until") else ""
    assump = f" {e(assumption_text(r))}" if assumption_text(r) else ""
    return (
        f"{prefix}{money(r['usd_per_second'])}/s for {e(r['variant'])} on {e(r['platform'])} "
        f"({e(spec_phrase(r))}), {e(rate_label(r))}{promo}, checked {e(r['checked'])}, {source_link(r)}.{assump}"
    )

# ---------- Model pages ----------
for slug, m in models.items():
    rs = sorted([r for r in rows if r["model"] == slug], key=lambda r: r["usd_per_second"])
    c = cheapest(rs); c2 = cheapest(rs, False)
    byres = {}
    for r in rs: byres.setdefault(r["resolution"], r)
    def res_item(k, v):
        heading = k if str(k).strip() not in MISSING_RESOLUTIONS else "not listed"
        tail = f" {e(assumption_text(v))}" if assumption_text(v) else ""
        return (f'<li><b>{e(heading)}</b>: {money(v["usd_per_second"])}/s for {e(v["variant"])} on {e(v["platform"])} '
                f'({e(spec_phrase(v))}) {tag(v)}{tail} Checked {e(v["checked"])}. {source_link(v)}.</li>')
    resl = "".join(res_item(k, v) for k, v in byres.items())
    api_rs = [r for r in rs if r["kind"] == "api"]; plan_rs = [r for r in rs if r["kind"] == "plan"]
    ca = cheapest(api_rs, False); cp = cheapest(plan_rs, False)
    extra_bits = []
    if c2 is not None and c2 is not c:
        extra_bits.append(compared_sentence("Without promos, the cheapest is ", c2))
    if ca is not None and ca is not c:
        extra_bits.append(compared_sentence("Cheapest pay-as-you-go API: ", ca))
    if cp is not None and cp is not c:
        extra_bits.append(compared_sentence("Cheapest subscription: ", cp))
    summary = f"<p>{' '.join(extra_bits)}</p>" if extra_bits else ""
    clip5 = money(c["usd_per_second"] * 5)
    faqs = model_faqs(m, rs, clip5)
    model_deals = deals_for_model(slug, rs)
    deals_html = ""
    if model_deals:
        deals_html = '<h2>Live deals for this model</h2><div class="dealgrid">' + "".join(deal_card(d, rowset=rs) for d in model_deals) + "</div>"
    soon = [d for d in UPCOMING_DEALS if slug in (d.get("models") or [])]
    if soon:
        deals_html += '<h2>Starting soon</h2><div class="dealgrid">' + "".join(deal_card(d, rowset=rs) for d in soon) + "</div>"
    card_math = ""
    if c.get("kind") == "api" and (c.get("math") or "").strip():
        card_math = f'<div class="assume">{e(c["math"].strip())}</div>'
    cross = crosslink_html(
        slug in REPORT_MODEL_SLUGS,
        slug in HOLIDAY_MODEL_SLUGS,
        weekly_report.report_h1(LATEST_REPORT) if LATEST_REPORT else "",
    )
    cross_html = (cross + "\n") if cross else ""
    body = f"""<p class="small"><a href="{root("/")}">Prices</a> › {e(m['name'])}</p>
<h1>{e(m['name'])} price per second ({MONTH})</h1>
{byline_html()}
<p class="lead">{model_spread(m, rs)}</p>
{cross_html}<div class="cards"><div class="card"><h3>Cheapest today</h3><div class="big">{money(c['usd_per_second'])}<span class="small">/s</span></div>{assumption_html(c)}{card_math}<div class="sub">{e(c['platform'])} · {e(c['variant'])} · {e(spec_phrase(c))} {tag(c)}</div>{checked_source(c)}<div class="sub">≈ {clip5} for a 5s clip</div>{deal_price_line(rs)}</div>
<div class="card"><h3>Cheapest by resolution</h3><ul class="small" style="padding-left:18px;margin:6px 0">{resl}</ul></div></div>
{summary}
{sponsor_slot("model:" + slug)}
{deals_html}
<h2>All {e(m['name'])} prices</h2>
{wide_table(THEAD.replace(' data-k="model"','').replace(' data-k=',' data-x=') + "<tbody>" + "".join(row_html(r) for r in rs) + "</tbody>")}
<p class="small">A row labelled estimated from credit plan is not a list price. Plan rows assume you use every credit you pay for. Unused credits make the real cost per second higher. Use the <a href="{root(f"/calculator/?model={slug}")}">credit calculator for {e(m["name"])}</a> to check a plan. Deal badges use the vendor's checkout price or stated rate. An unlimited window is a break-even second count, not $0/s.</p>
{news_box()}
{retired_table([r for r in retired_rows if r["model"] == slug], THEAD.replace(' data-k="model"','').replace(' data-k=',' data-x='))}
{faq_html(faqs)}
{tick_script()}
{ld_join(faq_ld(slug, faqs), breadcrumb_ld([("Prices", "/"), (m["name"], f"/models/{slug}/")]))}"""
    page(f"/models/{slug}/", page_title(f"{m['name']} Price Per Second"),
         f"{m['name']} costs from {money(c['usd_per_second'])}/s ({c['platform']}, {c['variant']}, {rate_label(c)}). Compare {len(rs)} sourced prices across APIs and credit plans.", body)

model_items = "".join(
    f'<li><a href="{root(f"/models/{slug}/")}">{e(m["name"])}</a></li>'
    for slug, m in models.items()
)
page("/models/", f"AI video models | {BRAND}",
     f"Every AI video model {BRAND} prices, with a page of sourced cost-per-second comparisons.",
     f'<h1>Models</h1><p class="lead">Every model {BRAND} tracks, with sourced prices per second of video.</p><ul class="model-index">{model_items}</ul>',
     extra_head=ld_script(item_list_ld("Models", [(m["name"], f"/models/{slug}/") for slug, m in models.items()])))

# ---------- Calculator ----------
def js_round(n):
    """Math.round for positive numbers."""
    return int(n + 0.5)

def clip_count(credits, per):
    raw = credits / per
    nearest = js_round(raw)
    return nearest if abs(raw - nearest) < 0.005 else int(raw)

def credits_text(v):
    if abs(v - round(v)) < 1e-9 and abs(v % 1) < 1e-9:
        return str(int(round(v)))
    return f"{v:.2f}"

def grouped_int(n):
    return f"{int(round(n)):,}"

def calc_fn(text):
    """Footnote marker. The full sentence is under the table and in the tooltip."""
    if not text:
        return ""
    mark = "†" if text.startswith("Estimate") else "*"
    return f'<a class="fn" href="#calcNotes" title="{e(text)}">{mark}</a>'

def calc_notes_html(texts):
    seen = []
    for text in texts:
        if text and text not in seen:
            seen.append(text)
    return " ".join(("†" if text.startswith("Estimate") else "*") + " " + e(text) for text in seen)

def calc_lab(label, value):
    """Visible on the phone cards. Hidden on desktop so the table stays unlabeled."""
    return f'<span class="lab">{e(label)} </span>{value}'

def calc_source_html(plan):
    """Same links the calculator script writes for the selected plan."""
    src = plan["source_url"]
    tracked = with_fpr(src) if is_higgsfield(src) else None
    href = tracked or AFF.get(plan["platform"]) or src
    rel = "sponsored nofollow noopener" if (tracked or AFF.get(plan["platform"])) else "nofollow noopener"
    src_rel = "sponsored nofollow noopener" if tracked else "nofollow noopener"
    src_href = tracked or src
    return (
        f'<a class="btn" href="{e(href)}" rel="{rel}" target="_blank">See {e(plan["platform"])} plans</a> '
        f'<a class="small" href="{e(src_href)}" rel="{src_rel}" target="_blank">source</a>'
    )

def calc_rows_html(plan_id):
    """Default 100% usage, deals off. Matches the script's first paint after prices.json loads."""
    plan = plans[plan_id]
    price = plan["usd_month"]
    credits = plan["credits_month"]
    bits = []
    chosen = sorted((r for r in rows if r.get("plan") == plan_id), key=lambda r: r["usd_per_second"])
    for r in chosen:
        clips = clip_count(credits, r["credits_per_clip"])
        unit = price / credits
        pc = unit * r["credits_per_clip"]
        price_cell = clip_money(pc) if clips > 0 else "—"
        per_sec = money(pc / r["clip_seconds"]) if clips > 0 else "—"
        cred = ("~" if r["status"] == "estimate" else "") + credits_text(r["credits_per_clip"])
        also = modifier_phrase(r)
        note = assumption_text(r)
        bits.append(
            f'<tr><td><a href="{root(f"/models/{r["model"]}/")}">{e(r["variant"])}</a>{calc_fn(note)}'
            f'<div class="meta">Input: {e(input_phrase(r))}</div>'
            f'<div class="meta">Length: {e(length_phrase(r))}</div>'
            + (f'<div class="meta also">Also: {e(also)}</div>' if also else "")
            + "</td>"
            f'<td>{calc_lab("Plan tier", e(shown_tier(r)))}</td>'
            f'<td>{calc_lab("Resolution", e(shown_resolution(r)))}</td>'
            f'<td>{calc_lab("Audio", e(audio_phrase(r)))}</td>'
            f'<td class="num">{calc_lab("Clip", str(r["clip_seconds"]) + "s")}</td>'
            f'<td>{calc_lab("Credits/clip", cred)}</td>'
            f'<td class="num">{calc_lab("Clips", grouped_int(clips))}</td>'
            f'<td class="num">{calc_lab("$/clip", price_cell)}</td>'
            f'<td class="num"><span class="amt">{per_sec}</span><div class="assume">{e(rate_label(r))}</div></td></tr>'
        )
    per = price / credits
    note = (plan.get("credits_note") or "") + f" Billing: {plan['billing']}. Checked {plan['checked']}."
    return {
        "price": f"${price:g}/mo",
        "credits": grouped_int(credits),
        "per": f"${per:.5f}",
        "note": note,
        "link": calc_source_html(plan),
        "rows": "".join(bits),
        "notes": calc_notes_html(assumption_text(r) for r in chosen),
    }

plan_opts = ""
default_plan_id = None
for plat in sorted({p["platform"] for p in plans.values()}):
    keys = [k for k, p in plans.items() if p["platform"] == plat]
    if default_plan_id is None and keys:
        default_plan_id = keys[0]
    plan_opts += f'<optgroup label="{e(plat)}">' + "".join(f'<option value="{k}">{e(plans[k]["plan"])}: ${plans[k]["usd_month"]:g}/mo</option>' for k in keys) + "</optgroup>"
calc_seed = calc_rows_html(default_plan_id)
calc_lead = "Pick a plan to see how many clips its credits buy each month and what each clip really costs. Credit costs come from each platform's own pricing page."
calc_ld = {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    "name": f"{BRAND} credit-plan calculator",
    "description": calc_lead,
    "url": SITE_URL + "/calculator/",
    "applicationCategory": "UtilitiesApplication",
    "operatingSystem": "Web",
    "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
}
calc_res_opts = '<option value="">Any</option>' + "".join(
    f'<option value="{e(res)}">{e(res)}</option>'
    for res in dict.fromkeys(
        shown_resolution(r) for r in rows if r.get("plan") == default_plan_id and not discontinued(r)
    )
)
calc = f"""<h1>AI video credit calculator</h1>
<p class="lead">{calc_lead}</p>
<p>Pricing a finished video from dollars per second? Use the <a href="{root("/guides/ai-video-project-budget/")}">project budget calculator</a>.</p>
<div class="calc"><div class="card">
<div class="field"><label class="small" for="plan">Plan</label><select id="plan">{plan_opts}</select></div>
<div class="field"><label class="small" for="used">% of credits you actually use</label><span class="ctl"><input id="used" type="number" value="100" style="width:100px" aria-describedby="usedMsg"> %</span></div>
<p class="small" id="usedMsg" role="status"></p>
<div class="field"><label class="small" for="resPick">Resolution</label><select id="resPick">{calc_res_opts}</select></div>
<div class="field"><label class="small" for="secs">Clip length (seconds)</label><input id="secs" type="number" min="1" step="1" placeholder="Any" style="width:100px"></div>
<div class="field"><label class="small" for="audioPick">Audio</label><select id="audioPick"><option value="">Any</option><option value="with">with audio</option><option value="without">without audio</option></select></div>
<div class="field"><label class="small" for="inputPick">Input</label><select id="inputPick"><option value="">Any</option><option value="t2v">text-to-video</option><option value="i2v">image-to-video</option><option value="ref2v">reference</option><option value="v2v">video-to-video</option><option value="extend">extend</option><option value="lip-sync">lip-sync</option></select></div>
<label class="chk" for="applyDeals"><input type="checkbox" id="applyDeals"> apply today's deals</label>
<p class="small" id="calcMsg"></p>
<div id="dealBox" hidden>
<label class="small" for="windowSecs">Seconds you'll make during an unlimited window</label><br>
<input id="windowSecs" type="number" min="1" value="60" style="width:100px">
<p class="small" id="dealEff"></p>
</div>
<div style="margin-top:14px"><div class="small">Plan price</div><div class="kpi" id="kPrice">{calc_seed["price"]}</div>
<div class="small" style="margin-top:8px">Credits per month</div><div class="kpi" id="kCred">{calc_seed["credits"]}</div>
<div class="small" style="margin-top:8px">Cost per credit</div><div class="kpi" id="kPer">{calc_seed["per"]}</div></div>
<p class="small" id="pNote">{e(calc_seed["note"])}</p><p id="pLink">{calc_seed["link"]}</p></div>
<div><div class="tblwrap"><table id="ct"><thead><tr><th>Model</th><th>Plan tier</th><th>Resolution</th><th>Audio</th><th>Clip</th><th>Credits/clip</th><th>Clips / month</th><th>$ / clip</th><th>$ / sec</th></tr></thead><tbody>{calc_seed["rows"]}</tbody></table></div>
<p class="small" id="modelNote"></p>
<p><button type="button" class="btn" id="copyLink">Copy link to this result</button> <span class="small" id="copyMsg" role="status"></span></p>
<p class="small" id="calcNotes">{calc_seed["notes"]}</p>
<p class="small">"~" = the platform gives an approximate credit cost. A figure labelled estimated from credit plan is not a list price. Using fewer of your credits raises the real cost of each clip.</p></div></div>
<script>
const BASE={json.dumps(BASE)};const AFF={json.dumps(AFF)};const MODELS={json.dumps({k:v["name"] for k,v in models.items()})};
const DEALMAP={json.dumps(CALC_DEALS)};
const EMBED={json.dumps({"plans": plans, "rows": [r for r in db["rows"] if r.get("plan")]}, separators=(",", ":"))};
let render=()=>{{}};
function start(d){{
 const $=id=>document.getElementById(id);
 const esc=s=>String(s??'').replace(/[&<>]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[c]));
 function parseQuery(qs){{
  const out={{}};
  const model=qs.get('model')||''; if(MODELS[model]) out.model=model;
  const plan=qs.get('plan')||''; if(d.plans[plan]) out.plan=plan;
  const provider=(qs.get('provider')||qs.get('platform')||'').trim().toLowerCase();
  if(provider&&!out.plan){{ const hit=Object.keys(d.plans).find(id=>(d.plans[id].platform||'').toLowerCase()===provider); if(hit) out.plan=hit; }}
  const secRaw=(qs.get('seconds')||qs.get('sec')||'').trim(); if(/^\\d+$/.test(secRaw)&&Number(secRaw)>=1) out.seconds=Number(secRaw);
  const audio=(qs.get('audio')||'').trim().toLowerCase();
  if(audio==='with'||audio==='on') out.audio='with'; else if(audio==='without'||audio==='off') out.audio='without';
  const input=(qs.get('input')||'').trim().toLowerCase();
  if(['t2v','i2v','ref2v','v2v','extend','lip-sync'].indexOf(input)>=0) out.input=input;
  const used=(qs.get('used')||'').trim(); if(/^\\d+$/.test(used)){{ const n=Number(used); if(n>=1&&n<=100) out.used=n; }}
  out.resolution=(qs.get('resolution')||qs.get('res')||'').trim();
  return out;
 }}
 const initial=parseQuery(new URLSearchParams(location.search));
 if(initial.plan) $('plan').value=initial.plan;
 if(initial.used) $('used').value=String(initial.used);
 if(initial.seconds) $('secs').value=String(initial.seconds);
 if(initial.audio) $('audioPick').value=initial.audio;
 if(initial.input) $('inputPick').value=initial.input;
 let modelFilter=initial.model||'';
 function hf(url){{try{{const u=new URL(url);const h=u.hostname;if(h!=='higgsfield.ai'&&!h.endsWith('.higgsfield.ai'))return null;if(h==='higgsfield.ai'&&(u.pathname===''||u.pathname==='/'))return {json.dumps(HF_BASE)};u.searchParams.delete('ref');u.searchParams.set('fpr',{json.dumps(HF_FPR)});return u.toString()}}catch(e){{return null}}}}
 function money(v){{const n=Math.round(Number(v)*100000);const neg=n<0,a=Math.abs(n),whole=Math.floor(a/100000);let digits=String(a%100000).padStart(5,'0').replace(/0+$/,'');if(digits.length<2)digits=String(a%100000).padStart(5,'0').slice(0,2);return (neg?'-':'')+'$'+whole+'.'+digits}}
 function clipMoney(v){{const n=Math.round(Number(v)*10000);const neg=n<0,a=Math.abs(n),whole=Math.floor(a/10000);let digits=String(a%10000).padStart(4,'0').replace(/0+$/,'');if(digits.length<2)digits=String(a%10000).padStart(4,'0').slice(0,2);return (neg?'-':'')+'$'+whole+'.'+digits}}
 const lab=(label,value)=>`<span class="lab">${{esc(label)}} </span>${{value}}`;
 function tierOf(r){{const name=String(r.plan_name||'').trim();if(name)return name;const res=String(r.resolution||'').trim();if(res==='Pro tier'||res==='Pro'||res==='Standard')return res;return 'not listed'}}
 function resOf(r){{const res=String(r.resolution||'').trim();if(!res||res==='—'||res==='-'||res==='–'||res==='Pro tier'||res==='Pro'||res==='Standard')return 'not listed';return res}}
 function audioOf(r){{const a=r.variation&&r.variation.audio;if(a==='with')return 'with audio';if(a==='without')return 'without audio';return 'not stated'}}
 function inputOf(r){{const inp=r.variation&&r.variation.input;const names={{t2v:'text-to-video',i2v:'image-to-video',ref2v:'reference',v2v:'video-to-video',extend:'extend','lip-sync':'lip-sync'}};if(!inp||inp==='not stated')return 'not stated';return inp.map(x=>names[x]||x).join(', ')}}
 function lengthOf(r){{const d=(r.variation&&r.variation.duration)||{{}};if(Array.isArray(d.rate_by_length))return d.rate_by_length.map(t=>t.label+' '+money(t.usd_per_second)+'/s').join('; ');if(typeof d.priced_seconds==='number')return 'priced at '+d.priced_seconds+'s';if(typeof d.min_seconds==='number'&&typeof d.max_seconds==='number')return d.min_seconds+'\u2013'+d.max_seconds+'s';if(typeof d.max_seconds==='number')return 'up to '+d.max_seconds+'s';if(typeof d.min_seconds==='number')return 'from '+d.min_seconds+'s';return 'not stated'}}
 function modifierOf(r){{const mods=r.variation&&r.variation.modifiers; if(!Array.isArray(mods)) return ''; return mods.map(m=>typeof m.usd_per_second==='number'?m.label+' '+money(m.usd_per_second)+'/s':m.label).join('; ')}}
 function assumptionOf(r){{if(r.kind==='plan')return (r.status==='estimate'?'Estimated from credit plan. ':'From credit plan. ')+'Assumes every credit you pay for is used.';if(r.status==='estimate'){{const note=String(r.note||'').trim();return note?'Estimated rate. '+note:'Estimated rate. The vendor marks this rate as approximate.'}}return ''}}
 function clipCount(credits, per){{const raw=credits/per, nearest=Math.round(raw);return Math.abs(raw-nearest)<0.005?nearest:Math.floor(raw)}}
 function current(r){{const today=new Date().toISOString().slice(0,10);if(r.status==='discontinued')return false;if(r.promo_until&&r.promo_until<today)return false;if(r.discontinued_on&&r.discontinued_on<today)return false;return true}}
 function readUsed(){{const el=$('used'), raw=String(el.value).trim();
  if(raw===''||!Number.isFinite(Number(raw))){{$('usedMsg').textContent='Enter a whole number from 1 to 100.';return null}}
  const n=Number(raw);
  if(Number.isInteger(n)&&n>=1&&n<=100){{$('usedMsg').textContent='';return n/100}}
  const use=Math.min(100,Math.max(1,Math.round(n)||1));
  el.value=String(use);
  $('usedMsg').textContent='Enter a whole number from 1 to 100. Using '+use+'%.';
  return use/100}}
 function unlimitedHit(map, r){{
  if(!map||!map.unlimited) return null;
  return map.unlimited.find(un=>{{
    if(un.models&&un.models.length&&un.models.indexOf(r.model)<0) return false;
    if(un.variants&&un.variants.length&&un.variants.indexOf(r.variant)<0) return false;
    if(un.max_resolution&&String(r.resolution).toLowerCase()!==String(un.max_resolution).toLowerCase()) return false;
    if((!un.models||!un.models.length)&&(!un.variants||!un.variants.length)) return false;
    return true;
  }})||null;
 }}
 function unlistedRes(res){{const raw=String(res||'').trim(); return raw===''||raw==='\u2014'||raw==='-'||raw==='\u2013'||raw==='Pro tier'||raw==='Pro'||raw==='Standard'}}
 function quoteRow(r, seconds, audio, inputType, resolution){{
  const v=r.variation||{{}}, dur=v.duration||{{}};
  if(resolution){{
    if(String(resolution).toLowerCase()==='not listed'){{ if(!unlistedRes(r.resolution)) return {{status:'not_offered'}} }}
    else if(String(r.resolution||'').toLowerCase().indexOf(String(resolution).toLowerCase())<0) return {{status:'not_offered'}};
  }}
  let unknown=false;
  if(audio){{const have=v.audio||'not stated'; if(have==='not stated') unknown=true; else if(have!==audio) return {{status:'not_offered'}}}}
  if(inputType){{const have=v.input; if(!have||have==='not stated') unknown=true; else if(have.indexOf(inputType)<0) return {{status:'not_offered'}}}}
  if(seconds!=null){{
    if((typeof dur.min_seconds==='number'&&seconds<dur.min_seconds)||(typeof dur.max_seconds==='number'&&seconds>dur.max_seconds)) return {{status:'not_offered'}};
    if(Array.isArray(dur.rate_by_length)){{
      if(!dur.rate_by_length.find(t=>(t.seconds||[]).map(Number).indexOf(Number(seconds))>=0)) return {{status:'not_stated'}};
    }} else if(v.length_changes_price!==false){{
      if(typeof dur.priced_seconds==='number'){{ if(Number(seconds)!==Number(dur.priced_seconds)) return {{status:'not_stated'}} }}
      else return {{status:'not_stated'}};
    }}
  }}
  return unknown?{{status:'unknown'}}:{{status:'match'}};
 }}
 let picksRead=false;
 render=function(){{const k=$('plan').value,p=d.plans[k],u=readUsed();
  const map=$('applyDeals').checked?DEALMAP[k]:null;
  const price=map&&map.price!=null?map.price:p.usd_month;
  const credits=p.credits_month+(map&&map.bonus_credits?map.bonus_credits:0);
  const per=price/credits;
  $('kPrice').textContent='$'+price+'/mo';$('kCred').textContent=credits.toLocaleString();$('kPer').textContent='$'+per.toFixed(5);
  let note=(p.credits_note||'')+' Billing: '+p.billing+'. Checked '+p.checked+'.';
  if(map&&map.notes&&map.notes.length) note+=' '+map.notes.join(' ');
  $('pNote').textContent=note;
  const tracked=hf(p.source_url),href=tracked||AFF[p.platform]||p.source_url,rel=(tracked||AFF[p.platform])?'sponsored nofollow noopener':'nofollow noopener';
  const srcRel=tracked?'sponsored nofollow noopener':'nofollow noopener';
  $('pLink').innerHTML=`<a class="btn" href="${{esc(href)}}" rel="${{rel}}" target="_blank">See ${{esc(p.platform)}} plans</a> <a class="small" href="${{esc(tracked||p.source_url)}}" rel="${{srcRel}}" target="_blank">source</a>`;
  const rsAll=d.rows.filter(r=>r.plan==k&&current(r)&&(!modelFilter||r.model===modelFilter));
  $('modelNote').textContent=modelFilter?('Showing '+MODELS[modelFilter]+' only.'):'';
  const resVals=[''].concat([...new Set(rsAll.map(r=>resOf(r)))]);
  const have=[...$('resPick').options].map(o=>o.value);
  const keep=$('resPick').value;
  if(have.join('|')!==resVals.join('|')) $('resPick').innerHTML=resVals.map(v=>`<option value="${{esc(v)}}">${{v?esc(v):'Any'}}</option>`).join('');
  if(!picksRead){{picksRead=true; const want=(initial.resolution||'').toLowerCase(); const hit=resVals.find(v=>v.toLowerCase()===want); if(hit) $('resPick').value=hit;}}
  else if(resVals.indexOf(keep)>=0) $('resPick').value=keep;
  const anyUn=!!(map&&map.unlimited&&map.unlimited.length&&rsAll.some(r=>unlimitedHit(map,r)));
  $('dealBox').hidden=!anyUn;
  if(anyUn) $('dealEff').textContent='Effective $/s for an unlimited window is the plan price divided by the seconds you make. It is not $0.';
  if(u==null){{$('ct').querySelector('tbody').innerHTML='<tr><td colspan="9">Enter a whole number from 1 to 100.</td></tr>';return}}
  const secs=Math.max(1, Number($('windowSecs').value)||1);
  const rawClip=String($('secs').value||'').trim();
  const clipSecs=rawClip===''?null:Math.max(1, Math.round(Number(rawClip))||1);
  const wantRes=$('resPick').value, wantAudio=$('audioPick').value, wantInput=$('inputPick').value;
  const judged=rsAll.map(r=>({{r, q:quoteRow(r, clipSecs, wantAudio, wantInput, wantRes)}}));
  const shown=judged.filter(x=>x.q.status==='match'||x.q.status==='unknown').sort((a,b)=>a.r.usd_per_second-b.r.usd_per_second);
  const unknownN=judged.filter(x=>x.q.status==='unknown').length, stated=judged.filter(x=>x.q.status==='not_stated').length, missed=judged.filter(x=>x.q.status==='not_offered').length;
  const rowsPhrase=(n, one, many)=>n+(n===1?' row '+one:' rows '+many);
  let msg='';
  if(!shown.length) msg='That combination is not offered, or the page does not state a price for it, for this plan.';
  else {{
    const bits=[];
    const unknownField=wantAudio&&wantInput?'audio or input':wantAudio?'audio':wantInput?'input':'audio or input';
    if(unknownN) bits.push(rowsPhrase(unknownN, 'does not state '+unknownField+', so it is marked not stated by vendor.', 'do not state '+unknownField+', so they are marked not stated by vendor.'));
    if(stated) bits.push(rowsPhrase(stated, 'does not state this length, so it is not priced.', 'do not state this length, so they are not priced.'));
    if(missed) bits.push(rowsPhrase(missed, 'offers a different combination.', 'offer a different combination.'));
    msg=bits.join(' ');
  }}
  $('calcMsg').textContent=msg;
  $('ct').querySelector('tbody').innerHTML=shown.map(({{r,q}})=>{{const clips=clipCount(credits*u,r.credits_per_clip);const unit=price/credits;const pc=unit*r.credits_per_clip/u;
   const priceCell=clips>0?clipMoney(pc):'—', perSec=clips>0?money(pc/r.clip_seconds):'—';
   let extra='';
   const hit=unlimitedHit(map, r);
   if(hit&&r.credits_per_clip>0&&r.clip_seconds>0){{
     const normal=unit*r.credits_per_clip/r.clip_seconds;
     const be=Math.round(price/normal);
     extra=`<div class="small">Unlimited: worth it after ${{be}}s. At ${{secs}}s in the window, ${{money(price/secs)}}/s effective.</div>`;
   }}
   if(map&&map.blended_price!=null&&clips>0&&r.clip_seconds>0){{
     extra+=`<div class="small">12-month blended ${{money((map.blended_price/credits)*r.credits_per_clip/u/r.clip_seconds)}}/s</div>`;
   }}
   const assume=assumptionOf(r);
   const fn=assume?`<a class="fn" href="#calcNotes" title="${{esc(assume)}}">${{assume.indexOf('Estimate')===0?'†':'*'}}</a>`:'';
   const cred=(r.status=='estimate'?'~':'')+(+r.credits_per_clip).toFixed(r.credits_per_clip%1?2:0);
   const also=modifierOf(r);
   const mark=q.status==='unknown'?'<div class="meta">not stated by vendor</div>':'';
   const dealNote=extra?`<div class="meta also">${{extra.replace(/<\\/?div[^>]*>/g,'')}}</div>`:'';
   const origin=r.kind==='plan'?(r.status==='estimate'?'estimated from credit plan':'from credit plan'):(r.status==='estimate'?'estimated rate':'published rate');
   return `<tr><td><a href="${{BASE}}/models/${{r.model}}/">${{esc(r.variant)}}</a>${{fn}}<div class="meta">Input: ${{esc(inputOf(r))}}</div><div class="meta">Length: ${{esc(lengthOf(r))}}</div>${{also?'<div class="meta also">Also: '+esc(also)+'</div>':''}}${{dealNote}}${{mark}}</td><td>${{lab('Plan tier',esc(tierOf(r)))}}</td><td>${{lab('Resolution',esc(resOf(r)))}}</td><td>${{lab('Audio',esc(audioOf(r)))}}</td><td class="num">${{lab('Clip',r.clip_seconds+'s')}}</td><td>${{lab('Credits/clip',cred)}}</td><td class="num">${{lab('Clips',clips.toLocaleString())}}</td><td class="num">${{lab('$/clip',priceCell)}}</td><td class="num"><span class="amt">${{perSec}}</span><div class="assume">${{esc(origin)}}</div></td></tr>`}}).join('');
  const noteSeen=[];
  shown.forEach(({{r}})=>{{const t=assumptionOf(r); if(t&&noteSeen.indexOf(t)<0) noteSeen.push(t);}});
  $('calcNotes').innerHTML=noteSeen.map(t=>(t.indexOf('Estimate')===0?'†':'*')+' '+esc(t)).join(' ');
  const q=new URLSearchParams(); q.set('plan', k);
  if(modelFilter) q.set('model', modelFilter);
  if(p.platform) q.set('provider', p.platform);
  if(wantRes) q.set('resolution', wantRes); if(clipSecs!=null) q.set('seconds', String(clipSecs)); if(wantAudio) q.set('audio', wantAudio); if(wantInput) q.set('input', wantInput);
  history.replaceState(null,'','?'+q);}};
 if(!start.bound){{
  start.bound=true;
  const call=()=>render();
  $('plan').addEventListener('input',call);$('used').addEventListener('input',call);
  $('applyDeals').addEventListener('input',call);$('windowSecs').addEventListener('input',call);
  $('resPick').addEventListener('input',call);$('secs').addEventListener('input',call);
  $('audioPick').addEventListener('input',call);$('inputPick').addEventListener('input',call);
  $('copyLink').addEventListener('click',()=>{{
   const url=location.href;
   const show=text=>{{$('copyMsg').textContent=text;}};
   if(navigator.clipboard&&navigator.clipboard.writeText) navigator.clipboard.writeText(url).then(()=>show('Link copied.')).catch(()=>show(url));
   else show(url);
  }});
 }}
 render();
}}
try{{ start(EMBED); }} finally {{ document.documentElement.classList.remove('calc-hold'); }}
fetch(BASE+'/data/prices.json').then(r=>r.json()).then(d=>{{
 const slim=x=>JSON.stringify({{plans:x.plans,rows:(x.rows||[]).filter(r=>r.plan)}});
 if(slim(d)!==slim(EMBED)) start(d);
}}).catch(()=>{{}});
</script>{news_box()}"""
page("/calculator/", page_title("AI Video Credit Calculator"),
     "How many Wan 3.0, Kling 3.0, Veo 3.1 or Seedance 2.5 clips does your Higgsfield, Krea or Magnific plan buy? Cost per clip and per second.", calc, "/calculator/",
     '<script>if(location.search){var k=["model","seconds","sec","resolution","res","audio","input","plan","provider","platform","used"],q=new URLSearchParams(location.search);for(var i=0;i<k.length;i++){if(q.get(k[i])){document.documentElement.classList.add("calc-hold");break}}}</script><style>html.calc-hold body{visibility:hidden}</style>' + ld_script(calc_ld))

# ---------- Changes ----------
items = ""
for c in sorted(changes, key=lambda c: c["date"], reverse=True):
    if c.get("type") == "price":
        txt = f'{e(models[c["model"]]["name"])} on {e(c["platform"])} ({e(c["variant"])}, {e(c["resolution"])}): {money(c["old_usd_per_second"])} → <b>{money(c["new_usd_per_second"])}</b>/s'
    else:
        txt = e(c["text"])
    if c.get("source_url"):
        href, rel = outbound(c["source_url"])
        src = f' <a class="small" href="{e(href)}" rel="{rel}" target="_blank">source</a>'
    else:
        src = ""
    items += f'<li id="{change_anchor(c)}"><span class="pill">{c["date"]}</span> <span class="pill">{e(c.get("type","")).upper()}</span> {txt}{src}</li>'
page("/changes/", f"AI Video Price Changes Log ({MONTH}) | {BRAND}",
     "Every AI video price change we detect, with dates and sources: Wan, Kling, Veo, Seedance, Runway, Higgsfield and more.",
     f"""<h1>Price changes log</h1><p class="lead">A daily script re-checks every source and logs each price change here with the date and a link to the source.</p>
<ul class="log" style="padding-left:0;list-style:none">{items}</ul>{news_box()}""", "/changes/")

# ---------- Newsletter ----------
if NEWSLETTER_ENABLED:
    page("/newsletter/", f"{BRAND} Weekly: AI video price drops & new models", "One short email a week: AI video price changes, new models and the cheapest way to run them.",
         f"""<h1>{BRAND} Weekly</h1><p class="lead">One short email every Friday: which AI video prices changed, which new models launched, and the cheapest way to run each one right now. Written from the same data as this site.</p>{news_box()}""", "/newsletter/")
else:
    page("/newsletter/", f"Newsletter coming soon | {BRAND}",
         "The VidFare newsletter is not open yet.",
         f"""<h1>Newsletter coming soon</h1>
<p>The weekly email is not open yet.</p>
<p><a href="{root("/")}">Home</a> · <a href="{root("/deals/")}">Deals</a> · <a href="{root("/changes/")}">Price changes</a></p>""",
         robots="noindex")

# ---------- About ----------
srcl = "".join(
    f'<li><a href="{e(outbound(s["url"])[0])}" rel="{outbound(s["url"])[1]}" target="_blank">{e(s["name"])}</a>'
    f'{" (not in the daily fetch)" if s["fetch"]=="manual" else ""}</li>'
    for s in sources.values()
)
unv = "".join(f'<li>{e(public_gap(u))}</li>' for u in db["unverified"])
about_ld = {
    "@context": "https://schema.org",
    "@type": "AboutPage",
    "url": SITE_URL + "/about/",
    "author": EDITOR_LD,
    "editor": EDITOR_LD,
}
page("/about/", f"About {BRAND}: methodology & affiliate disclosure", f"How {BRAND} collects and normalizes AI video prices, and how the site is funded.",
     f"""<h1>About {BRAND}</h1>
{byline_html()}
<p class="lead">{BRAND} tracks what AI video generation actually costs, per second of finished video, across every place you can run a model. {e(TAGLINE)}</p>
<p>Made by Emmanuel Gonzalez.</p>
<h2>How the numbers work</h2>
<ul><li>Every price comes from the vendor's own pricing or model page, saved with a source link and the date we checked it.</li>
<li><b>Published rate</b>: the vendor states dollars per second, or states an API credit count and a credit price. Runway API rows are credits per second times $0.01, the credit price on the Runway API pricing page.</li>
<li><b>From credit plan</b>: plan price ÷ credits = $ per credit; × credits per clip ÷ clip length = $ per second. That assumes you use all your credits. It is not a list price per second.</li>
<li><b>Estimated from credit plan</b>: the same math when the vendor says "~", "roughly", or "estimated" for the clip count. That label is not a list price. If a price cannot be confirmed, it is left out.</li>
<li><b>Audio, input, and length</b> are copied from the vendor page. Audio is with audio, without audio, or not stated. Input is text-to-video, image-to-video, reference, video-to-video, extend, or lip-sync when that mode is named for the price. Length is the clip the credit price is for, a stated min and max, or a per-second rate the page ties to a length. If the page does not say it, the field stays not stated. A value is not inferred from a nearby sentence or from another row. A different stated price becomes its own row.</li>
<li>When a vendor shuts an endpoint down, that row is marked <i>discontinued</i> and kept under Discontinued with the last recorded rate. It is not used for cheapest picks.</li>
<li>Prices exclude VAT/sales tax and change often. Always confirm on the vendor's page before paying.</li>
<li><b>Deals</b> are a separate list. A discounted $/s uses the vendor's stated rate or the checkout plan price ÷ credits. A code that lasts the first N months also shows a 12-month blended rate. Unlimited windows show how many seconds of video cover the plan price. They are not listed at $0/s. A deal on one variant is labelled with that variant, so it is not read as a discount on a different row.</li></ul>
<h2>How we source and check prices</h2>
<p>Each row keeps the vendor page it came from and the date that page last matched its check. The daily job is <code>scripts/update_prices.py --apply</code>. GitHub Actions runs it at 15:17 UTC every day, and again at 13:30 UTC on Fridays, then rebuilds the site from the data files.</p>
<ul>
<li>A source marked static is downloaded and read as page text. Some of those pages also keep a price in a script payload, and the check reads that payload when the row is set up for it.</li>
<li>A source marked render is opened in Chrome and read after the page loads. Higgsfield plans are one of these.</li>
<li>A source marked manual is not fetched. Kling app subscriptions are that source. The pricing page did not show prices without a login or a region, so those subscriptions are not in the table.</li>
<li>Each row and each plan has a needle: the phrase and the number stored for it. The check searches the fetched text for that phrase and compares the number with the stored value.</li>
<li>When an API row's number has changed, the job updates that row's dollars per second by the same factor and writes the old and new figures to the price-change log. A credit-plan row is not rewritten by that step. A plan whose price or credit count changed is flagged, and its dollars per second stay as stored.</li>
<li>A row whose needles still match is stamped with that day's date. A credit-plan row is not stamped when its plan failed the check.</li>
<li>A promo whose end date has passed is removed from the live table and recorded as ended. A live deal past its end date is marked ended.</li>
<li>The same run looks for new or removed sale-like sentences on the watched pricing pages. Those sentences are saved as unconfirmed candidates. They are not added to the deals list, and they do not change a price.</li>
<li>When every source except the manual one was fetched, <code>last_full_check</code> becomes that date.</li>
</ul>
<p>The check compares stored numbers with the fetched page. It does not add a price the page did not state.</p>
<h2>Sources we check</h2><ul class="small">{srcl}</ul>
<h2>Not in the price table</h2><ul class="small">{unv}</ul>
<h2 id="disclosure">Affiliate disclosure</h2>
<div class="disclose">Some links on {BRAND} are affiliate links. If you sign up through them we may earn a commission, at no extra cost to you. Affiliate status never changes the order of the tables: rows are always sorted by price. Sponsored placements are labelled "Sponsor" and never affect the price order.</div>
<p class="small">Contact: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>.</p>
<p class="small">Directories: <a href="https://dang.ai">Dang.ai</a>.</p>""", "/about/", ld_script(about_ld))

# ---------- Deals ----------
def deal_sort(deal):
    return (deal.get("end") is None, deal.get("end") or "9999-99-99", deal.get("vendor") or "", deal.get("title") or "")

live_sorted = sorted(LIVE_DEALS, key=deal_sort)
upcoming_sorted = sorted(UPCOMING_DEALS, key=lambda d: (d.get("start") or "", d.get("vendor") or "", d.get("title") or ""))
vendors = sorted({d["vendor"] for d in live_sorted + upcoming_sorted})
types = sorted({d["type"] for d in live_sorted + upcoming_sorted})
live_html = "".join(deal_card(d) for d in live_sorted) or "<p>No live deals right now.</p>"
upcoming_html = ""
if upcoming_sorted:
    upcoming_html = (
        '<section id="upcoming"><h2>Starting soon</h2>'
        '<p class="small">Verified offers that have not started. They are not applied to current prices. '
        'On the start date they join the live list.</p>'
        '<div class="dealgrid" id="upcomingDeals">'
        + "".join(deal_card(d) for d in upcoming_sorted)
        + "</div></section>"
    )
archive_sorted = sorted(ARCHIVED, key=lambda d: d.get("end") or "", reverse=True)
archive_html = "".join(deal_card(d, archive=True) for d in archive_sorted) or "<p class='small'>No tracked deal has expired yet. Older holiday sales are on the Black Friday page, labeled 2025.</p>"
deals_body = f"""<h1>AI video deals</h1>
<p class="lead">Offers copied from vendor pricing pages and official accounts. Countdowns use your clock, so they stay right between daily builds. A deal with no end date is not given a guessed one. An offer that starts later is listed under Starting soon and is not a current price.</p>
{sponsor_slot("deals", featured=True)}
<div class="disclose"><b>Disclosure.</b> Higgsfield links on this page are affiliate links (parameter <code>fpr=emmanuel-bbfe0e</code>) and use <code>rel="sponsored nofollow"</code>. If you sign up through them, {BRAND} may earn a commission, at no extra cost to you. Links to Krea, Magnific, Runway, fal, and other vendors are the official URLs, with no affiliate tag. Deals are listed only when the vendor's own page or official account is the source. Order is the end date, not who pays us. See the <a class="tap" href="{root("/about/#disclosure")}">full disclosure</a>.</div>
<div class="filters">
<select id="dVendor" aria-label="Vendor"><option value="">All vendors</option>{"".join(f'<option value="{e(v)}">{e(v)}</option>' for v in vendors)}</select>
<select id="dType" aria-label="Deal type"><option value="">All types</option>{"".join(f'<option value="{e(t)}">{e(t.replace("_", " "))}</option>' for t in types)}</select>
<span class="small" id="dCount"></span>
</div>
{upcoming_html}
<div class="dealgrid" id="liveDeals">{live_html}</div>
<h2>When these vendors run sales</h2>
<p>Launch weeks are the usual pattern: a new video model is unlimited on credit plans and 30–75% off on APIs for one to four weeks. The holiday window, about Nov 20 through Jan 8, is the long one. In 2025 Higgsfield posted several waves, Magnific used a 50% code, and Krea posted 40% off yearly plans. End dates move. They get extended, reopened, or left as "limited time." If a page does not name an end date, this site does not invent one. <a href="{root("/deals/black-friday/")}">Black Friday and holiday deals</a>.</p>
<h2>Past deals</h2>
<div class="dealgrid" id="archive">{archive_html}</div>
<p class="small"><a href="{root("/deals.xml")}">Deals RSS</a> · {json_link("/deals.json", "deals.json")}</p>
{news_box()}
{tick_script()}
<script>
function filterDeals(){{
  const v=document.getElementById('dVendor').value, t=document.getElementById('dType').value;
  let n=0;
  document.querySelectorAll('#liveDeals [data-deal-card], #upcomingDeals [data-deal-card]').forEach(card=>{{
    const hide=(v&&card.dataset.vendor!==v)||(t&&card.dataset.type!==t);
    card.classList.toggle('is-filtered', hide);
    if(!hide && !card.classList.contains('is-past') && card.parentElement && card.parentElement.id==='liveDeals') n++;
  }});
  const count=document.getElementById('dCount');
  if(count) count.textContent=n+' live';
}}
document.getElementById('dVendor').addEventListener('input', filterDeals);
document.getElementById('dType').addEventListener('input', filterDeals);
document.addEventListener('DOMContentLoaded', filterDeals);
filterDeals();
</script>"""
def deals_item_list(deals):
    elements = []
    for i, deal in enumerate(deals, 1):
        bits = [deal.get("vendor") or "", (deal.get("type") or "").replace("_", " ")]
        if deal.get("percent") is not None:
            bits.append(f"{deal['percent']:g}% off")
        if deal.get("end"):
            est = " (estimated)" if deal.get("end_is_estimate") else ""
            bits.append(f"ends {deal['end']}{est}")
        else:
            bits.append("no end date given")
        item = {
            "@type": "ListItem",
            "position": i,
            "name": deal.get("title") or deal["id"],
            "url": f"{SITE_URL}/deals/#{deal['id']}",
        }
        price = deal.get("price_after")
        if isinstance(price, (int, float)) and not isinstance(price, bool):
            offer = {
                "@type": "Offer",
                "name": deal.get("title") or deal["id"],
                "url": f"{SITE_URL}/deals/#{deal['id']}",
                "description": " · ".join(bit for bit in bits if bit),
                "price": f"{price:g}",
                "priceCurrency": "USD",
                "seller": {"@type": "Organization", "name": deal.get("vendor") or ""},
            }
            if deal.get("end"):
                offer["priceValidUntil"] = deal["end"]
            item["item"] = offer
        elements.append(item)
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Live AI video deals",
        "numberOfItems": len(elements),
        "itemListElement": elements,
    }

page("/deals/", page_title("AI Video Deals"),
     "Live AI video discounts, plan sales, promo codes, and unlimited windows, with end dates and the $/s math.",
     deals_body, "/deals/",
     extra_head=(f'<link rel="alternate" type="application/rss+xml" title="{BRAND} deals" href="{root("/deals.xml")}">'
                 + ld_script(deals_item_list(live_sorted))))

hist_sorted = sorted(HISTORY, key=lambda d: d.get("start") or "")

def _note_sentence(text, needle):
    for part in re.split(r"(?<=[.!?])\s+", (text or "").strip()):
        if needle.lower() in part.lower():
            return part.strip()
    return ""

def _plain_date(value, estimate=False):
    if not value:
        return "not stated"
    text = str(value)
    if estimate:
        text += " (estimated)"
    return text

def _money_field(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"${value:g}/mo"
    return "not stated"

def _per_second_pairs(deal):
    """One before/after pair per catalog option. Monthly and annual rows that match are one pair."""
    found = {}
    for row in rows:
        adj = dealmod.adjustment(deal, row, plans)
        if not adj or adj.get("usd") is None or adj.get("list_usd") is None:
            continue
        key = (
            row.get("model"),
            row.get("variant"),
            shown_resolution(row),
            shown_audio(row),
            input_phrase(row),
        )
        previous = found.get(key)
        if previous is not None:
            same = (
                abs(previous[1]["usd"] - adj["usd"]) < 1e-9
                and abs(previous[1]["list_usd"] - adj["list_usd"]) < 1e-9
            )
            if not same:
                key = key + (row.get("plan"),)
                previous = found.get(key)
        prefer = row.get("plan") == deal.get("deal_plan_id")
        if previous is None or (prefer and previous[0].get("plan") != deal.get("deal_plan_id")):
            found[key] = (row, adj)
    items = list(found.values())
    items.sort(key=lambda item: (
        models.get(item[0].get("model"), {}).get("name") or "",
        str(item[0].get("resolution") or ""),
        item[0].get("variant") or "",
        item[0].get("id") or "",
    ))
    return items

def _stated_rows(deal):
    matched = [
        row for row in rows
        if deal.get("id") in (row.get("deal_ids") or []) and row.get("list_usd_per_second") is not None
    ]
    matched.sort(key=lambda row: (row.get("usd_per_second") or 0, row.get("id") or ""))
    return matched

def _rate_table(pairs, dates, before_label="Before $/s", after_label="After $/s", extra_note=""):
    if not pairs:
        return "<p>The catalog does not have a before and after dollars per second for this offer.</p>"
    body = []
    for row, before, after in pairs:
        if row.get("checked"):
            dates.append(row["checked"])
        name = models.get(row.get("model"), {}).get("name", row.get("model") or "")
        label = f"{name}, {row.get('variant') or ''}, {shown_resolution(row)}"
        audio = shown_audio(row)
        if audio != "not stated":
            label += f", {audio} audio"
        source = ""
        if row.get("source_url"):
            href, rel = outbound(row["source_url"])
            source = f'<a href="{e(href)}" rel="{rel}" target="_blank">source</a>'
        body.append(
            "<tr>"
            f"<td>{e(label)}</td>"
            f'<td class="num">{money(before)}</td>'
            f'<td class="num">{money(after)}</td>'
            f"<td>{e(rate_label(row))}</td>"
            f"<td>{e(row.get('checked') or '')}</td>"
            f'<td class="small">{source}</td>'
            "</tr>"
        )
    labels = {rate_label(row) for row, _before, _after in pairs}
    note = extra_note
    if note and not note.endswith(" "):
        note += " "
    note += "Before and after are dollars per second of finished video."
    if any("credit plan" in label for label in labels):
        note += (
            " A credit-plan row is plan price ÷ credits × credits per clip ÷ seconds, "
            "and it assumes every paid credit is used."
        )
    if "promo" in labels:
        note += " A promo row's before figure is the list rate stored on that row."
    return (
        '<div class="tblwrap"><table><thead><tr>'
        f"<th>Row</th><th>{e(before_label)}</th><th>{e(after_label)}</th>"
        "<th>How the rate is labeled</th><th>Checked</th><th>Source</th>"
        "</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table></div>"
        + f'<p class="small">{e(note)}</p>'
    )

def _plan_facts(deal, dates):
    if deal.get("verified_date"):
        dates.append(deal["verified_date"])
    sale_11 = bool(_note_sentence(deal.get("notes") or "", "11.11"))
    if sale_11:
        items = [
            f"<li>Monthly billing: {_money_field(deal.get('price_before'))}</li>",
            f"<li>Annual billing under the 11.11 sale: {_money_field(deal.get('price_after'))}</li>",
        ]
    else:
        items = [
            f"<li>Plan price before: {_money_field(deal.get('price_before'))}</li>",
            f"<li>Plan price after: {_money_field(deal.get('price_after'))}</li>",
        ]
    full = plans.get(deal.get("full_plan_id") or "") or {}
    annual = plans.get(deal.get("deal_plan_id") or "") or {}
    if isinstance(full.get("usd_month"), (int, float)) and not isinstance(full.get("usd_month"), bool):
        items.append(f"<li>Monthly price on the plan record: ${full['usd_month']:g}/mo</li>")
    if isinstance(annual.get("usd_month"), (int, float)) and not isinstance(annual.get("usd_month"), bool):
        items.append(f"<li>Annual price on the plan record: ${annual['usd_month']:g}/mo</li>")
    credits = annual.get("credits_month")
    if isinstance(credits, (int, float)) and not isinstance(credits, bool):
        items.append(f"<li>Credits on the annual plan record: {int(credits):,} per month</li>")
    if deal.get("percent") is not None:
        items.append(f"<li>Percent on the deal record: {deal['percent']:g}%</li>")
    items.append(f"<li>Start date: {e(_plain_date(deal.get('start')))}</li>")
    if sale_11:
        items.append("<li>The 11.11 sale ends Nov 15, per Higgsfield's pricing page.</li>")
    elif deal.get("end"):
        items.append(f"<li>End date: {e(_plain_date(deal.get('end'), deal.get('end_is_estimate')))}</li>")
    else:
        items.append("<li>End date: not stated in the end field</li>")
    note = _note_sentence(deal.get("notes") or "", "11.11")
    if note and not sale_11:
        items.append(f"<li>Check note: {e(note)}</li>")
    items.append(f"<li>Verified: {e(deal.get('verified_date') or 'not stated')}</li>")
    if dealmod.conditions(deal).get("standing"):
        items.append("<li>The deal record marks this as a standing price.</li>")
    source_url = deal.get("source_url") or deal.get("link_url")
    if source_url:
        href, rel = outbound(source_url)
        items.append(f'<li>Source: <a href="{e(href)}" rel="{rel}" target="_blank">source</a></li>')
    items.append(f'<li><a href="{root("/deals/")}#{e(deal["id"])}">Full deal record</a></li>')
    return "<ul>" + "".join(items) + "</ul>"

def _deal_pairs(deal):
    stated = _stated_rows(deal)
    if stated:
        return [(row, row["list_usd_per_second"], row["usd_per_second"]) for row in stated]
    return [(row, adj["list_usd"], adj["usd"]) for row, adj in _per_second_pairs(deal)]

bf_dates = []
holiday_live = [deal for deal in live_sorted if is_holiday_named(deal)]
dated_live = [deal for deal in live_sorted if deal.get("end") and not is_holiday_named(deal)]
open_live = [deal for deal in live_sorted if not deal.get("end") and not is_holiday_named(deal)]
titled = [
    deal for deal in holiday_live
    if "black friday" in (deal.get("title") or "").lower() or "cyber monday" in (deal.get("title") or "").lower()
]
note_11 = ""
for deal in holiday_live:
    note_11 = _note_sentence(deal.get("notes") or "", "11.11")
    if note_11:
        break
holiday_html = []
if not holiday_live:
    holiday_html.append("<p>No live deal in the file uses Black Friday, Cyber Monday, holiday-sale, or 11.11 wording.</p>")
elif not titled:
    holiday_html.append("<p>No live deal has Black Friday or Cyber Monday in its title.</p>")
else:
    names = ", ".join(deal.get("title") or deal["id"] for deal in titled)
    holiday_html.append(f"<p>Live deals titled as Black Friday or Cyber Monday: {e(names)}.</p>")
for deal in holiday_live:
    holiday_html.append(f"<h3>{e(deal.get('title') or deal['id'])}</h3>")
    holiday_html.append(f'<p class="small">{e(deal.get("vendor") or "")}</p>')
    if deal.get("source_quote"):
        holiday_html.append(f'<blockquote class="small">“{e(deal["source_quote"])}”</blockquote>')
    holiday_html.append(_plan_facts(deal, bf_dates))
    pairs = _deal_pairs(deal)
    if pairs:
        if _note_sentence(deal.get("notes") or "", "11.11"):
            holiday_html.append("<p><b>Per second, monthly billing vs annual billing under the 11.11 sale</b></p>")
            holiday_html.append(_rate_table(
                pairs, bf_dates,
                "Monthly billing $/s",
                "Annual billing $/s",
                "Before is monthly billing. After is annual billing under the 11.11 sale, which ends Nov 15 per Higgsfield's pricing page.",
            ))
        else:
            holiday_html.append("<p><b>Per second, from the price catalog</b></p>")
            holiday_html.append(_rate_table(pairs, bf_dates))
    else:
        holiday_html.append("<p>The catalog does not have a before and after dollars per second for this offer.</p>")
dated_html = [
    "<p>These are the other live deals that have an end date. "
    "They are not titled as Black Friday or Cyber Monday. "
    "A per-second before and after is shown only when the catalog has both numbers.</p>"
]
plain_rows = []
for deal in dated_live:
    if deal.get("verified_date"):
        bf_dates.append(deal["verified_date"])
    pairs = _deal_pairs(deal)
    if not pairs:
        plain_rows.append(deal)
        continue
    start = _plain_date(deal.get("start"))
    end = _plain_date(deal.get("end"), deal.get("end_is_estimate"))
    source_url = deal.get("source_url") or deal.get("link_url")
    source = ""
    if source_url:
        href, rel = outbound(source_url)
        source = f'<a href="{e(href)}" rel="{rel}" target="_blank">source</a>'
    dated_html.append(f"<h3>{e(deal.get('title') or deal['id'])}</h3>")
    dated_html.append(
        f'<p class="small">{e(deal.get("vendor") or "")}. '
        f"Start {e(start)}. End {e(end)}. "
        f'Verified {e(deal.get("verified_date") or "not stated")}. {source}. '
        f'<a href="{root("/deals/")}#{e(deal["id"])}">Full deal record</a>.</p>'
    )
    if deal.get("source_quote"):
        dated_html.append(f'<blockquote class="small">“{e(deal["source_quote"])}”</blockquote>')
    dated_html.append(_rate_table(pairs, bf_dates))
if plain_rows:
    body_rows = []
    for deal in plain_rows:
        source_url = deal.get("source_url") or deal.get("link_url")
        source = ""
        if source_url:
            href, rel = outbound(source_url)
            source = f'<a href="{e(href)}" rel="{rel}" target="_blank">source</a>'
        body_rows.append(
            "<tr>"
            f'<td><a href="{root("/deals/")}#{e(deal["id"])}">{e(deal.get("title") or deal["id"])}</a>'
            f'<div class="small">{e(deal.get("vendor") or "")}</div></td>'
            f"<td>{e(_plain_date(deal.get('start')))}</td>"
            f"<td>{e(_plain_date(deal.get('end'), deal.get('end_is_estimate')))}</td>"
            f"<td>{e(deal.get('verified_date') or '')}</td>"
            f'<td class="small">{source}</td>'
            "<td>not stored</td>"
            "</tr>"
        )
    dated_html.append(
        '<div class="tblwrap"><table><thead><tr>'
        "<th>Offer</th><th>Start</th><th>End</th><th>Verified</th><th>Source</th><th>Before and after $/s</th>"
        "</tr></thead><tbody>"
        + "".join(body_rows)
        + "</tbody></table></div>"
        '<p class="small">“not stored” means this deal has no before and after dollars per second in the catalog.</p>'
    )
if not dated_live:
    dated_html.append("<p>No other live deal has an end date.</p>")
for deal in hist_sorted:
    if deal.get("verified_date"):
        bf_dates.append(deal["verified_date"])
content_dates = [day for day in bf_dates if day]
BF_CONTENT_DATE = max(content_dates) if content_dates else (deal_doc.get("updated") or LAST)
SITEMAP_LASTMOD["/deals/black-friday/"] = BF_CONTENT_DATE
file_updated = deal_doc.get("updated") or ""
if file_updated and file_updated != BF_CONTENT_DATE:
    updated_line = (
        f"Last updated {BF_CONTENT_DATE}. That is the newest verified or checked date in the sections below. "
        f"The deals file updated field is {file_updated}."
    )
else:
    updated_line = f"Last updated {BF_CONTENT_DATE}."
status_bits = []
if not titled:
    status_bits.append("No live deal is titled Black Friday or Cyber Monday.")
if note_11:
    status_bits.append("Higgsfield's 11.11 sale ends Nov 15.")
eleven = [
    deal for deal in holiday_live
    if _note_sentence(deal.get("notes") or "", "11.11")
    and isinstance(deal.get("price_before"), (int, float)) and not isinstance(deal.get("price_before"), bool)
    and isinstance(deal.get("price_after"), (int, float)) and not isinstance(deal.get("price_after"), bool)
]
if eleven:
    bits = []
    for deal in eleven:
        plan_name = (deal.get("plans") or ["Plan"])[0]
        bits.append(f"{plan_name} ${deal['price_before']:g} to ${deal['price_after']:g}/mo")
    status_bits.append(", ".join(bits) + ", monthly vs annual.")
bf_desc = " ".join(status_bits)
if len(bf_desc) > 160:
    raise SystemExit(f"black friday description is {len(bf_desc)} characters")
bf_faqs = [
    (
        "How are prices checked?",
        "Each price and deal is copied from the vendor's own pricing page or an official post. "
        "The page keeps that source link and the date it was checked. A daily check runs at 15:17 UTC. "
        "This page only shows offers that are in the deals file or the price catalog.",
    ),
    (
        "How is the per-second price computed?",
        "When the vendor states dollars per second, that rate is shown. A credit plan is plan price divided by credits, "
        "times credits per clip, divided by seconds. That math assumes every paid credit is used. "
        "A figure the vendor marks with a tilde, roughly, or estimated is labeled an estimate. "
        "If the catalog does not have both a before and an after rate, this page does not fill one in.",
    ),
    (
        "When does this page update?",
        "The page is rebuilt from the deals file and the price catalog after those files change. "
        f"The deals file updated field is {file_updated or 'not stated'}. "
        f"The newest verified or checked date on this page is {BF_CONTENT_DATE}. "
        "An end date is shown only when the deal record or its check note states one.",
    ),
]
bf_faq_ld = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "url": SITE_URL + "/deals/black-friday/",
    "mainEntity": [
        {"@type": "Question", "name": question, "acceptedAnswer": {"@type": "Answer", "text": answer}}
        for question, answer in bf_faqs
    ],
}
lead = (
    "Black Friday, Cyber Monday, and other holiday-sale wording in the deals file, "
    "then the live deals that have an end date. "
    "A per-second before and after appears only when the price catalog has both rates."
)
bf_body = (
    f'<p class="small"><a href="{root("/deals/")}">Deals</a> › Black Friday</p>'
    "<h1>AI video Black Friday and holiday deals</h1>"
    f'<p class="lead">{e(lead)}</p>'
    f"<p>{e(updated_line)}</p>"
    "<h2>Holiday-sale wording in the current deals</h2>"
    + "".join(holiday_html)
    + "<h2>Other live deals with an end date</h2>"
    + "".join(dated_html)
    + news_box()
    + f'<p>{len(open_live)} other live deals have no end date in the record. '
    f'They are not listed here as a holiday sale. <a href="{root("/deals/")}">All live deals</a>.</p>'
    + faq_html(bf_faqs)
    + "<h2>2025 Black Friday and holiday sales</h2>"
    + f"<p>The history list has {len(hist_sorted)} past offers. Each card is that record, with its source. They are not current prices.</p>"
    + '<div class="dealgrid">'
    + "".join(deal_card(deal, archive=True) for deal in hist_sorted)
    + "</div>"
    + f'<div class="disclose">Higgsfield links elsewhere on {BRAND} can be affiliate links. '
    "The posts and pricing pages linked here are the vendors' own sources. "
    f'<a class="tap" href="{root("/about/#disclosure")}">Disclosure</a>.</div>'
)
page("/deals/black-friday/", page_title("AI Video Black Friday Deals"),
     bf_desc, bf_body, "/deals/",
     extra_head=ld_join(
         breadcrumb_ld([("Deals", "/deals/"), ("Black Friday", "/deals/black-friday/")]),
         bf_faq_ld,
     ))

def write_feeds():
    def slim(deal, status):
        row = {
            "id": deal["id"], "vendor": deal.get("vendor"), "type": deal.get("type"),
            "title": deal.get("title"), "models": deal.get("models") or [], "plans": deal.get("plans") or [],
            "conditions": dealmod.conditions(deal), "percent": deal.get("percent"),
            "bonus_credits": deal.get("bonus_credits"),             "price_before": deal.get("price_before"),
            "price_after": deal.get("price_after"), "price_pairs": deal.get("price_pairs"),
            "full_plan_id": deal.get("full_plan_id"), "deal_plan_id": deal.get("deal_plan_id"),
            "math": deal.get("math"), "variants": deal.get("variants") or [],
            "start": deal.get("start"), "end": deal.get("end"),
            "end_is_estimate": bool(deal.get("end_is_estimate")), "status": status,
            "source_url": deal.get("source_url"), "source_quote": deal.get("source_quote"),
            "verified_date": deal.get("verified_date"), "notes": deal.get("notes"),
            "examples": [] if status != "live" else example_items(deal, rows),
        }
        if deal.get("sources"):
            row["sources"] = deal["sources"]
        return row
    payload = {
        "updated": TODAY,
        "deals": [slim(d, "live") for d in live_sorted],
        "upcoming": [slim(d, "upcoming") for d in upcoming_sorted],
        "archive": [slim(d, "ended") for d in archive_sorted],
        "history": [slim(d, "ended") for d in hist_sorted],
    }
    raw = json.dumps(payload, indent=1, ensure_ascii=False) + "\n"
    for path in (os.path.join(DIST, "deals.json"), os.path.join(DIST, "data", "deals.json")):
        open(path, "w").write(raw)
    items = []
    for deal in live_sorted:
        day = deal.get("start") or deal.get("verified_date") or TODAY
        dt = datetime.datetime.fromisoformat(day).replace(tzinfo=datetime.timezone.utc)
        pub_date = email.utils.formatdate(dt.timestamp(), usegmt=True)
        desc = e(deal.get("source_quote") or deal.get("title") or "")
        if deal.get("end"):
            desc += e(" Ends " + deal["end"] + (" (estimated)." if deal.get("end_is_estimate") else "."))
        else:
            desc += " No end date given."
        link = f"{SITE_URL}/deals/#{deal['id']}"
        items.append(
            f"  <item>\n    <title>{e(deal.get('title') or deal['id'])}</title>\n"
            f"    <link>{e(link)}</link>\n    <guid isPermaLink=\"true\">{e(link)}</guid>\n"
            f"    <pubDate>{pub_date}</pubDate>\n    <description>{desc}</description>\n  </item>"
        )
    built = email.utils.formatdate(datetime.datetime.now(datetime.timezone.utc).timestamp(), usegmt=True)
    rss = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<rss version=\"2.0\" xmlns:atom=\"http://www.w3.org/2005/Atom\">\n<channel>\n"
        f"  <title>{BRAND} deals</title>\n"
        f"  <link>{SITE_URL}/deals/</link>\n"
        f"  <atom:link href=\"{SITE_URL}/deals.xml\" rel=\"self\" type=\"application/rss+xml\"/>\n"
        "  <description>Live AI video deals from vendor pages and official accounts.</description>\n"
        f"  <lastBuildDate>{built}</lastBuildDate>\n"
        + "\n".join(items) + "\n</channel>\n</rss>\n"
    )
    open(os.path.join(DIST, "deals.xml"), "w").write(rss)

write_feeds()

def feed_items():
    """Price changes, published weekly reports, and live deals. Dates come from the records."""
    items = []
    for change in changes:
        day = change.get("date")
        if not day:
            continue
        anchor = change_anchor(change)
        link = f"{SITE_URL}/changes/#{anchor}"
        items.append({
            "title": change_plain(change),
            "link": link,
            "guid": link,
            "date": day,
            "description": change_plain(change),
            "category": "price change",
        })
    if REPORTS_ENABLED:
        result = weekly_report.assign(weekly_report.load(), today)
        for report in result["reports"]:
            path = f"/reports/{report['id']}/"
            link = SITE_URL + path
            items.append({
                "title": weekly_report.report_h1(report),
                "link": link,
                "guid": link,
                "date": report["through"],
                "description": weekly_report.report_description(report),
                "category": "report",
            })
    for deal in live_sorted:
        day = deal.get("start") or deal.get("verified_date")
        if not day:
            continue
        link = f"{SITE_URL}/deals/#{deal['id']}"
        title = deal.get("title") or deal["id"]
        desc = deal.get("source_quote") or title
        if deal.get("end"):
            desc += " Ends " + deal["end"] + (" (estimated)." if deal.get("end_is_estimate") else ".")
        else:
            desc += " No end date given."
        items.append({
            "title": title,
            "link": link,
            "guid": link,
            "date": day,
            "description": desc,
            "category": "deal",
        })
    items.sort(key=lambda item: (item["date"], item["guid"]), reverse=True)
    return items

def write_site_feed():
    import xml.etree.ElementTree as ET
    items = feed_items()
    atom = "http://www.w3.org/2005/Atom"
    ET.register_namespace("atom", atom)
    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "{%s}link" % atom, {
        "href": SITE_URL + "/feed.xml",
        "rel": "self",
        "type": "application/rss+xml",
    })
    ET.SubElement(channel, "title").text = BRAND
    ET.SubElement(channel, "link").text = SITE_URL + "/"
    ET.SubElement(channel, "description").text = "Price changes, weekly reports, and live deals."
    latest = max((item["date"] for item in items), default=LAST)
    ET.SubElement(channel, "lastBuildDate").text = rfc822_day(latest)
    for item in items:
        node = ET.SubElement(channel, "item")
        ET.SubElement(node, "title").text = item["title"]
        ET.SubElement(node, "link").text = item["link"]
        ET.SubElement(node, "guid", {"isPermaLink": "true"}).text = item["guid"]
        ET.SubElement(node, "pubDate").text = rfc822_day(item["date"])
        ET.SubElement(node, "description").text = item["description"]
        ET.SubElement(node, "category").text = item["category"]
    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ")
    path = os.path.join(DIST, "feed.xml")
    tree.write(path, encoding="UTF-8", xml_declaration=True)
    text = open(path, encoding="utf-8").read()
    if not text.endswith("\n"):
        open(path, "a", encoding="utf-8").write("\n")

# ---------- Advertise ----------
AD_MAIL = "mailto:" + CONTACT_EMAIL + "?subject=" + quote("VidFare sponsorship")
ad_desc = (
    "Sponsor a labelled spot on VidFare, where people compare where to generate AI video. "
    "Home banner, model page box, and the deals featured spot. Rates on request."
)
ad_spots = """<li><b>Home banner.</b> Under the intro on the homepage, above the price table.</li>
<li><b>Model page box.</b> On each model page, after the cheapest-today summary and before the price table.</li>
<li><b>Deals featured spot.</b> At the top of the deals page, separate from the real deals.</li>"""
if NEWSLETTER_ENABLED:
    ad_spots += """
<li><b>Newsletter sponsor line.</b> Coming soon.</li>"""
ad_body = f"""<h1>Advertise on VidFare</h1>
<p class="lead">Labelled placements next to the price comparison. They stay out of the price tables and the deals list.</p>
<h2>Who visits</h2>
<p>People comparing where to generate AI video: which model, which platform, and what a second of finished video costs.</p>
<h2>Available spots</h2>
<ul>
{ad_spots}
</ul>
<h2>Rules</h2>
<ul>
<li>Placements are clearly labelled "Sponsor".</li>
<li>A placement never changes the price order or the rankings.</li>
<li>Relevant AI video and creator tools only.</li>
<li>VidFare may decline a placement.</li>
</ul>
<p>Rates on request. Email <a href="{e(AD_MAIL)}">{CONTACT_EMAIL}</a>.</p>"""
ad_ld = {
    "@context": "https://schema.org",
    "@type": "WebPage",
    "name": "Advertise on VidFare",
    "description": ad_desc,
    "url": SITE_URL + "/advertise/",
    "isPartOf": {"@type": "WebSite", "name": BRAND, "url": SITE_URL + "/"},
    "publisher": {"@id": ORG_ID},
}
page("/advertise/", f"Advertise on VidFare | {BRAND}", ad_desc, ad_body, "", ld_script(ad_ld))

# ---------- Contact ----------
# Title stays under the 60-character audit. "Contact VidFare" is 15 characters.
CONTACT_TITLE = "Contact VidFare"
contact_desc = (
    f"Email {CONTACT_EMAIL} about a VidFare price, a deal, or the site. "
    "Sponsorships use the same email."
)
contact_body = f"""<h1>Contact VidFare</h1>
<p class="lead">Questions about a price, a deal, or this site.</p>
<p>Email <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>.</p>
<p>Sponsorships: email <a href="{e(AD_MAIL)}">{CONTACT_EMAIL}</a>.</p>
<p><a href="{root("/advertise/")}">Advertise</a> · <a href="{root("/about/")}">About</a></p>"""
contact_ld = {
    "@context": "https://schema.org",
    "@type": "ContactPage",
    "name": CONTACT_TITLE,
    "description": contact_desc,
    "url": SITE_URL + "/contact/",
    "isPartOf": {"@type": "WebSite", "name": BRAND, "url": SITE_URL + "/"},
    "publisher": {"@id": ORG_ID},
}
page("/contact/", CONTACT_TITLE, contact_desc, contact_body, "", ld_script(contact_ld))

def write_contact_redirect():
    """GitHub Pages has no server redirects.

    A request for /contact-us (no slash) is a 301 to /contact-us/. This file
    is that directory index: a meta refresh to /contact/, with a plain link
    when the refresh does not run.
    """
    dest = root("/contact/")
    canon = SITE_URL + "/contact/"
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Contact</title>
<meta http-equiv="refresh" content="0; url={e(dest)}">
<link rel="canonical" href="{e(canon)}">
<meta name="robots" content="noindex">
</head><body>
<p><a href="{e(dest)}">Contact</a></p>
</body></html>
"""
    out = os.path.join(DIST, "contact-us", "index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w").write(doc)

write_contact_redirect()

# ---------- 404, robots, sitemap ----------
# Count a missing URL as its own path. GoatCounter reads this before count.js.
GOAT_404 = "<script>window.goatcounter={path:function(){return '404:'+location.pathname+location.search}}</script>\n"

def newsletter_redirect_script():
    """Send other newsletter URLs to the coming-soon page."""
    dest = root("/newsletter/")
    prefix = BASE + "/newsletter"
    return (
        "<script>(function(){var p=location.pathname,d="
        + json.dumps(dest)
        + ",pre="
        + json.dumps(prefix)
        + ";if(p.indexOf(pre)===0&&p!==d)location.replace(d)})();</script>"
    )

sample_models = list(models.items())[:4]
model_help = "".join(
    f'<li><a href="{root(f"/models/{slug}/")}">{e(m["name"])}</a></li>'
    for slug, m in sample_models
)
not_found_body = f"""<h1>Page not found</h1>
<p>That address is not a page on {BRAND}.</p>
<ul>
<li><a href="{root("/")}">Home</a></li>
<li><a href="{root("/deals/")}">Deals</a></li>
<li><a href="{root("/calculator/")}">Credit calculator</a></li>
<li><a href="{root("/guides/")}">Guides</a></li>
<li><a href="{root("/changes/")}">Price changes</a></li>
</ul>
<h2>A few model pages</h2>
<ul>{model_help}</ul>"""
page("/404.html", f"Page not found | {BRAND}", "Page not found.", not_found_body,
     extra_head=newsletter_redirect_script(), robots="noindex", canonical=False, before_count=GOAT_404)

report_paths = write_report_pages(DIST, today, public_log=True) if REPORTS_ENABLED else []
write_site_feed()

def write_llms():
    """Plain summary for AI search. Every price is the cheapest current row for that model and platform."""
    lines = [
        f"# {BRAND}",
        "",
        f"> {TAGLINE}",
        "",
        (
            f"{BRAND} compares AI video generation prices in dollars per second of finished video, "
            f"across APIs and credit plans. Figures are copied from each vendor's own pricing page. "
            f"Audio, input type, and clip length are filled in only when that page states them. Otherwise the field is not stated. "
            f"Last full check: {LAST}. {len(rows)} current prices."
        ),
        "",
        "## Cheapest current price by model and platform",
        "",
    ]
    for slug, m in models.items():
        rs = [r for r in rows if r["model"] == slug]
        if not rs:
            continue
        best = cheapest(rs)
        lines.append(f"### {m['name']}")
        lines.append("")
        lines.append(
            f"- [{m['name']} prices]({SITE_URL}/models/{slug}/): cheapest overall "
            f"{price_fact(best)}."
        )
        by_plat = {}
        for r in rs:
            cur = by_plat.get(r["platform"])
            if cur is None or r["usd_per_second"] < cur["usd_per_second"]:
                by_plat[r["platform"]] = r
        for plat in sorted(by_plat, key=lambda p: (by_plat[p]["usd_per_second"], p)):
            lines.append(f"- {plat}: {price_fact(by_plat[plat], platform=False)}.")
        lines.append("")
    lines += [
        "## Deals",
        "",
        f"- [AI video deals]({SITE_URL}/deals/): live discounts, plan sales, promo codes, and unlimited windows, with end dates when the vendor gave one.",
        "",
        "## Guides",
        "",
        f"- [Guides]({SITE_URL}/guides/): comparisons built from the same price rows.",
        f"- [Cheapest way to use Wan 3.0]({SITE_URL}/guides/cheapest-wan-3-0/): {wan_blurb()}",
        f"- [Cheapest AI video generator]({SITE_URL}/guides/cheapest-ai-video-generator/): {cheapest_blurb()}",
        f"- [Higgsfield plan rates]({SITE_URL}/guides/is-higgsfield-worth-it/): {hf_blurb()}",
        f"- [Project budget]({SITE_URL}/guides/ai-video-project-budget/): {budget_blurb()}",
        "",
        "## Data",
        "",
        f"- [Price data]({SITE_URL}/data/): how to read prices.json, share a calculator link, and credit VidFare.",
        f"- [prices.json]({SITE_URL}/data/prices.json): the price catalog. CORS is open. A full check updates last_full_check.",
        f"- Calculator link: {SITE_URL}/calculator/?model=kling-3-0&seconds=10 — model is the /models/<slug>/ slug. Optional: resolution, audio (with or without), input (t2v, i2v, ref2v, v2v, extend, lip-sync), plan, provider, seconds, used.",
        f"- [deals.json]({SITE_URL}/deals.json): the live and archived deals. The same file is also at {SITE_URL}/data/deals.json.",
        "- JSON files at those URLs are data downloads for scripts and agents, not HTML pages.",
        f"- [Connect an agent]({SITE_URL}/mcp/): the live read-only MCP server at {MCP_ENDPOINT} for ChatGPT, Claude, and Cursor. An agent can check current prices and deals before it recommends or generates a video. It reads prices.json and deals.json and does not invent a price.",
        "- MCP tools: list_models (each model and its cheapest current dollars per second); get_model_prices (one model, with an optional provider and resolution); estimate_cost (one clip, using the credit calculator's inputs); cheapest_options (lowest stated price for a length and resolution); list_deals (live deals, or upcoming, ended, or all).",
        f"- [feed.xml]({SITE_URL}/feed.xml): RSS of price changes, weekly reports, and live deals.",
        "",
        f"Advertise: {SITE_URL}/advertise/ — labelled sponsor placements. They never change the price order.",
        "",
    ]
    if report_paths:
        lines += [
            "## Weekly price reports",
            "",
            "Published on Friday when at least two verified changes were checked. A change is a per-second price move, a promo start, or a promo end. A shorter week rolls forward.",
            "",
        ]
        for path in report_paths:
            lines.append(f"- {SITE_URL}{path}")
        lines.append("")
    open(os.path.join(DIST, "llms.txt"), "w").write("\n".join(lines))

import guide_pages
guide_pages.render(globals())
write_llms()
# GitHub Pages serves vidfare.com and ignores a _headers file. JSON stays
# fetchable. A noindex response header has to be set on the host that answers
# the request. Do not add a _headers file that Pages will not apply.
open(os.path.join(DIST, "robots.txt"), "w").write(f"User-agent: *\nAllow: {root('/')}\nSitemap: {SITE_URL}/sitemap.xml\n")
def _keys_in_order(records):
    found = []
    for record in records:
        if not isinstance(record, dict):
            continue
        for key in record:
            if key not in found:
                found.append(key)
    return found

FIELD_HELP = {
    "generated": "Date this catalog file was first assembled.",
    "currency": "Currency for every dollar amount. It is USD.",
    "sources": "The vendor pages the daily check reads. Each one has a name, a URL, and how the page is fetched.",
    "models": "The models in the catalog. The key is the slug used on /models/<slug>/ and in calculator links.",
    "plans": "Credit plans the calculator can select. The key is the plan id used as ?plan=.",
    "rows": "One object per price. This is the list to read.",
    "unverified": "Things we looked for and could not confirm, so they are not prices.",
    "last_full_check": "Date of the last daily check that fetched every source.",
    "variation_schema": "A short reminder of what the variation object on a row means.",
    "name": "Display name.",
    "maker": "Company that makes the model.",
    "url": "Page the check reads.",
    "fetch": "How that page is read: static HTML, a rendered browser, or by hand.",
    "ready": "Whether that source is included in the daily check.",
    "note": "A short note from the source page or the check.",
    "platform": "Where the price is sold, such as fal or Higgsfield.",
    "plan": "On a plan record, the plan name. On a row, the plan id when the price is a credit plan.",
    "usd_month": "What the plan costs per month, in dollars.",
    "billing": "Whether the plan is billed monthly, yearly, or annually.",
    "credits_month": "Credits, or units, the plan includes for a month.",
    "credits_note": "Extra note when credits are granted per year and shown as a monthly average.",
    "source": "Which entry in sources this record is checked against.",
    "checks": "Needles the daily check looks for on the source page. A phrase check only confirms the words are still there.",
    "checked": "Date this record was last confirmed.",
    "source_url": "The page this price came from.",
    "model": "Model slug.",
    "variant": "The specific mode or plan row, in the vendor's words.",
    "kind": "api for a pay-as-you-go rate, or plan for a credit-plan rate.",
    "resolution": "Resolution or tier the vendor stated. An em dash means the page did not list one.",
    "audio": "Older true/false flag. Prefer variation.audio, which is with, without, or not stated.",
    "usd_per_second": "Dollars per second of finished video.",
    "list_usd_per_second": "The vendor's undiscounted dollars per second, when a promo row has one.",
    "status": "verified, estimate, promo, or discontinued.",
    "promo_until": "End date of a promo, when the vendor gave one.",
    "math": "How a credit-plan row was turned into dollars per second.",
    "id": "Stable id for the row.",
    "deal_ids": "Live deals that apply to this row.",
    "discontinued_on": "Date the vendor shut this endpoint down.",
    "plan_name": "Plan name shown in the table.",
    "clip_seconds": "Clip length the credit price is for.",
    "credits_per_clip": "Credits, or units, one clip costs.",
    "usd_per_clip": "Dollars for one clip at that length, before display rounding.",
    "variation": "What the vendor page actually said about audio, input type, and clip length.",
    "audio_changes_price": "True, false, or not stated. Not stated means the page did not say.",
    "length_changes_price": "True, false, or not stated.",
    "input_changes_price": "True, false, or not stated.",
    "modifiers": "Extra charges the page states on top of the headline rate, or not stated.",
    "min_seconds": "Shortest clip the page allows, or not stated.",
    "max_seconds": "Longest clip the page allows, or not stated.",
    "allowed_seconds": "Clip lengths the page lists, or not stated.",
    "priced_seconds": "The clip length this credit price is for, or not stated.",
    "rate_by_length": "Per-second rates the page ties to particular lengths, or not stated.",
    "input": "t2v, i2v, ref2v, v2v, extend, lip-sync, or not stated.",
}
FIELD_HELP["audio"] = "Inside variation: with, without, or not stated. The older row field is the true/false flag."

def _field_table(keys):
    return "".join(
        f"<tr><td><code>{e(key)}</code></td><td>{e(FIELD_HELP.get(key, 'Included in the file.'))}</td></tr>"
        for key in keys
    )

row_keys = _keys_in_order(db["rows"])
plan_keys = _keys_in_order(plans.values())
model_keys = _keys_in_order(models.values())
source_keys = _keys_in_order(sources.values())
variation_keys = _keys_in_order(r.get("variation") or {} for r in db["rows"])
duration_keys = _keys_in_order((r.get("variation") or {}).get("duration") or {} for r in db["rows"])
checked_on = db.get("last_full_check") or LAST
data_examples = [
    ("/calculator/?model=kling-3-0&seconds=10", "Kling 3.0, 10 second clips."),
    ("/calculator/?model=wan-3-0&resolution=480p&seconds=5&provider=Higgsfield", "Wan 3.0 at 480p for 5 seconds on a Higgsfield plan."),
    ("/calculator/?model=veo-3-1&audio=with&seconds=4&provider=Magnific", "Veo 3.1 with audio, 4 seconds, on a Magnific plan."),
]
data_ld = {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": f"{BRAND} AI video prices",
    "description": (
        f"Dollars per second for AI video models, copied from vendor pricing pages. "
        f"Free to use if you credit and link {BRAND} (vidfare.com). Updated by the daily price check."
    ),
    "url": SITE_URL + "/data/",
    "isAccessibleForFree": True,
    "creator": {"@type": "Person", "name": "Emmanuel Gonzalez"},
    "distribution": {
        "@type": "DataDownload",
        "encodingFormat": "application/json",
        "contentUrl": SITE_URL + "/data/prices.json",
    },
    "temporalCoverage": checked_on,
}
data_body = f"""<h1>Price data</h1>
<p class="lead">The prices on {BRAND} are a public JSON file. You can read it from a script or an AI agent. You do not need an account or a key.</p>
<h2>The file</h2>
<p>{json_link("/data/prices.json", "https://vidfare.com/data/prices.json")}</p>
<p>CORS is already open, so a browser page on another site can fetch it. The daily price check reads the vendor pages and updates this file. <code>last_full_check</code> is the date of the last check that fetched every source. Right now that date is {e(checked_on)}.</p>
<h2>What is in the file</h2>
<table><thead><tr><th>Field</th><th>Meaning</th></tr></thead><tbody>{_field_table(list(db.keys()))}</tbody></table>
<h2>Each price row</h2>
<p>Read <code>rows</code>. A row is one price for one model, on one platform, at one resolution.</p>
<table><thead><tr><th>Field</th><th>Meaning</th></tr></thead><tbody>{_field_table(row_keys)}</tbody></table>
<h2>Audio, input, and length</h2>
<p><code>variation</code> records only what the vendor page stated. If the page did not say, the value is <code>not stated</code>.</p>
<table><thead><tr><th>Field</th><th>Meaning</th></tr></thead><tbody>{_field_table(variation_keys)}</tbody></table>
<p>Inside <code>duration</code>:</p>
<table><thead><tr><th>Field</th><th>Meaning</th></tr></thead><tbody>{_field_table(duration_keys)}</tbody></table>
<h2>Models, plans, and sources</h2>
<p>Model fields: {", ".join(f"<code>{e(k)}</code>" for k in model_keys)}.</p>
<p>Plan fields: {", ".join(f"<code>{e(k)}</code>" for k in plan_keys)}.</p>
<p>Source fields: {", ".join(f"<code>{e(k)}</code>" for k in source_keys)}.</p>
<h2>Share a calculator link</h2>
<p>Open <a href="{root("/calculator/")}">/calculator/</a> with a query string. Unknown parameters are ignored. The model slug is the same one used on <a href="{root("/models/")}">/models/&lt;slug&gt;/</a>.</p>
<ul>
<li><code>model</code> such as <code>kling-3-0</code></li>
<li><code>seconds</code> clip length</li>
<li><code>resolution</code> such as <code>480p</code> or <code>not listed</code></li>
<li><code>audio</code> <code>with</code> or <code>without</code> (<code>on</code> and <code>off</code> also work)</li>
<li><code>input</code> <code>t2v</code>, <code>i2v</code>, <code>ref2v</code>, <code>v2v</code>, <code>extend</code>, or <code>lip-sync</code></li>
<li><code>plan</code> a plan id, or <code>provider</code> <code>Higgsfield</code>, <code>Krea</code>, or <code>Magnific</code></li>
<li><code>used</code> percent of credits used, from 1 to 100</li>
</ul>
<ul>
{"".join(f'<li><a href="{root(path)}"><code>{e(path)}</code></a> {e(label)}</li>' for path, label in data_examples)}
</ul>
<p>Changing the calculator updates the address bar, so the URL you see is the one to share. Each model page also links to the calculator with that model filled in.</p>
<h2>RSS</h2>
<p>Price changes, weekly reports, and live deals are in <a href="{root("/feed.xml")}">/feed.xml</a>.</p>
<h2>Using the data</h2>
<p>Free to use. Please credit and link {BRAND} (vidfare.com). The code in the GitHub repository is MIT. The price data is free to use with that credit.</p>
<h2>Ask an assistant</h2>
<p>The same files can be queried through the live read-only MCP server at <a href="{MCP_ENDPOINT}"><code>{MCP_ENDPOINT}</code></a>. How to connect ChatGPT, Claude, and Cursor is on <a href="{root("/mcp/")}">the MCP page</a>. It reads this file and {json_link("/deals.json", "deals.json")}. It does not replace either file, and it does not invent a price.</p>
"""
page("/data/", page_title("Price data for developers"),
     f"How to read the public {BRAND} price file, share a calculator link, and credit the data.",
     data_body, "/data/", ld_script(data_ld))

def copy_prompt_block(text):
    """Visible prompt plus a Copy button. The text stays selectable if script is blocked."""
    script = """<script>
(function () {
  var btn = document.getElementById("copy-prompt");
  var node = document.getElementById("vidfare-prompt");
  var status = document.getElementById("copy-status");
  if (!btn || !node) return;
  function say(message) {
    if (status) status.textContent = message;
  }
  function selectPrompt() {
    var range = document.createRange();
    range.selectNodeContents(node);
    var sel = window.getSelection();
    if (!sel) return;
    sel.removeAllRanges();
    sel.addRange(range);
  }
  function fallback(value) {
    var area = document.createElement("textarea");
    area.value = value;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.top = "0";
    area.style.left = "0";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.focus();
    area.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (err) { ok = false; }
    document.body.removeChild(area);
    if (!ok) selectPrompt();
    say(ok ? "Copied." : "Select the prompt and copy it.");
  }
  btn.addEventListener("click", function () {
    var value = node.textContent || "";
    var writer = navigator.clipboard && navigator.clipboard.writeText;
    var pending = writer ? writer.call(navigator.clipboard, value) : null;
    if (pending && typeof pending.then === "function") {
      pending.then(function () { say("Copied."); }, function () { fallback(value); });
      return;
    }
    fallback(value);
  });
})();
</script>"""
    return (
        '<div class="promptbox">'
        f'<pre id="vidfare-prompt" tabindex="0" aria-label="Prompt to paste into your agent">{e(text)}</pre>'
        '<p><button type="button" class="btn" id="copy-prompt" aria-controls="vidfare-prompt">Copy</button></p>'
        '<p class="small" id="copy-status" role="status" aria-live="polite"></p>'
        "<noscript><p class=\"small\">Select the prompt and copy it.</p></noscript>"
        "</div>"
        + script
    )

mcp_models = ", ".join(e(m["name"]) for m in models.values())
mcp_ld = {
    "@context": "https://schema.org",
    "@type": "WebPage",
    "name": AGENT_H1,
    "url": SITE_URL + "/mcp/",
    "description": MCP_DESC,
    "isPartOf": {"@type": "WebSite", "name": BRAND, "url": SITE_URL + "/"},
}
mcp_body = f"""<h1>{e(AGENT_H1)}</h1>
<p class="lead">Connect ChatGPT, Claude, or Cursor, then paste the prompt below. The server is public and read-only. It reads {json_link("/data/prices.json", "prices.json")} and {json_link("/deals.json", "deals.json")}. It does not invent a price. Answers include the source, the date last checked, and a link back to {BRAND}.</p>
<h2>Prompt</h2>
<p>Paste this into your agent after VidFare is connected.</p>
{copy_prompt_block(AGENT_PROMPT)}
<h2>Connect</h2>
<p><b>Live.</b> Use <code>{MCP_ENDPOINT}</code>. No key and no sign-in.</p>
<h2>ChatGPT</h2>
<p>Open Settings, then Connectors. Turn on developer mode if custom connectors are hidden. Add a custom connector with <code>{MCP_ENDPOINT}</code>.</p>
<h2>Claude</h2>
<p>Add a custom connector with <code>{MCP_ENDPOINT}</code>.</p>
<h2>Cursor</h2>
<p>Save this as <code>.cursor/mcp.json</code> for one project, or as <code>~/.cursor/mcp.json</code> for every project.</p>
<pre class="snippet"><code>{e(MCP_CURSOR)}</code></pre>
<p class="small">The same object is in <code>mcp-server/.mcp.json</code> in the repository. There is no API key.</p>
<h2>Models</h2>
<p>{mcp_models}.</p>
<h2>Tools</h2>
<ul>
<li><code>list_models</code> lists each model and its cheapest current dollars per second.</li>
<li><code>get_model_prices</code> takes a model, and optionally a provider and a resolution.</li>
<li><code>estimate_cost</code> takes a model and seconds, plus the calculator inputs: resolution, audio, input, plan, provider, and percent of credits used.</li>
<li><code>cheapest_options</code> takes seconds and a resolution.</li>
<li><code>list_deals</code> lists live deals. Ask for upcoming, ended, or all to see the other groups.</li>
</ul>
<p class="small">{MCP_PRIVACY} The question and argument values are not stored.</p>
<h2>The price file is still here</h2>
<p>Scripts that fetch JSON can keep using <a href="{root("/data/")}">the data page</a>. The MCP server is another way to read the same catalog.</p>
"""
page("/mcp/", MCP_TITLE, MCP_DESC, mcp_body, "", ld_script(mcp_ld))

urls = ["/", "/deals/", "/deals/black-friday/", "/calculator/", "/data/", "/mcp/"]
urls += [path for path, _label in GUIDE_LINKS]
if NEWSLETTER_ENABLED:
    urls.append("/newsletter/")
urls += ["/changes/", "/about/", "/advertise/", "/contact/"]
if report_paths:
    urls.extend(report_paths)
urls += ["/models/"] + [f"/models/{s}/" for s in models]
open(os.path.join(DIST, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    "".join(f"  <url><loc>{SITE_URL}{u}</loc><lastmod>{SITEMAP_LASTMOD.get(u) or LAST}</lastmod></url>\n" for u in urls) + "</urlset>\n")
def check_sponsor_renderer():
    live = render_sponsor(
        "home",
        {"name": "Example Tool", "url": "https://example.com/tool", "tagline": "A short line", "active": True},
    )
    if f'rel="{SPONSOR_REL}"' not in live or "Example Tool" not in live or "A short line" not in live:
        raise SystemExit("active sponsor markup missing rel, name, or tagline")
    if ">Sponsor<" not in live and "Sponsor</span>" not in live:
        raise SystemExit("active sponsor markup is not labelled Sponsor")
    if "<table" in live or "dealgrid" in live or "data-deal-card" in live:
        raise SystemExit("sponsor markup must not be a table or a deal card")
    empty = render_sponsor("deals", {"name": "", "url": "", "tagline": "", "active": False}, featured=True)
    if HOUSE_LINE not in empty or f'href="{root("/advertise/")}"' not in empty or "Featured" not in empty:
        raise SystemExit("empty sponsor markup should still describe the advertise page")
    if "sponsored" in empty:
        raise SystemExit("the house placeholder is not an outbound sponsor link")
    if sponsor_slot("deals", featured=True):
        raise SystemExit("an empty sponsor slot should be omitted from the page")
    blank = render_sponsor("home", {"name": " ", "url": "https://example.com", "tagline": "", "active": True})
    if HOUSE_LINE not in blank:
        raise SystemExit("an active slot with an empty name is treated as empty")
    if sponsor_slot("home"):
        raise SystemExit("home placeholder should be omitted while the slot is empty")
    if sponsor_record("model:not-a-real-model") is not sponsors.get("model:default"):
        raise SystemExit("model pages should fall back to model:default")

def mcp_link_errors():
    """Site links to /mcp/ or the registry file must be files this build wrote."""
    import re
    targets = []
    for dirpath, _, filenames in os.walk(DIST):
        for name in filenames:
            if not name.endswith((".html", ".xml", ".txt")):
                continue
            path = os.path.join(dirpath, name)
            text = open(path, encoding="utf-8").read()
            rel = os.path.relpath(path, DIST)
            for match in re.finditer(r'(?:href|loc)="([^"]+)"|\((https://vidfare\.com[^)\s]+)\)', text):
                raw = match.group(1) or match.group(2)
                site_path = None
                if raw.startswith(SITE_URL + "/"):
                    site_path = raw[len(SITE_URL):]
                elif raw.startswith("/") and not raw.startswith("//"):
                    site_path = raw
                if site_path is None:
                    continue
                site_path = site_path.split("#", 1)[0].split("?", 1)[0]
                if site_path.rstrip("/") not in ("/mcp", "/.well-known/mcp-registry-auth"):
                    if not site_path.startswith("/.well-known/"):
                        continue
                targets.append((rel, site_path))
    errors = []
    seen = set()
    for rel, site_path in targets:
        key = (rel, site_path)
        if key in seen:
            continue
        seen.add(key)
        bare = site_path.lstrip("/")
        if site_path.endswith("/"):
            dest = os.path.join(DIST, bare, "index.html")
        else:
            dest = os.path.join(DIST, bare)
        if not os.path.isfile(dest):
            errors.append(f"{rel} links to {site_path}, which this build did not write")
    if not any(site_path.rstrip("/") == "/mcp" for _, site_path in seen):
        errors.append("no built page links to /mcp/")
    return errors

def contact_redirect_errors(raw):
    """The /contact-us/ file is a meta refresh, not a normal page."""
    errors = []
    dest = root("/contact/")
    canon = f'<link rel="canonical" href="{SITE_URL}/contact/">'
    refresh = f'<meta http-equiv="refresh" content="0; url={dest}">'
    if refresh not in raw:
        errors.append("contact-us redirect is missing the meta refresh to /contact/")
    if canon not in raw or raw.count('rel="canonical"') != 1:
        errors.append("contact-us canonical must be https://vidfare.com/contact/")
    if 'name="robots" content="noindex"' not in raw:
        errors.append("contact-us robots must be noindex")
    if f'<a href="{dest}">Contact</a>' not in raw:
        errors.append("contact-us redirect is missing the plain fallback link")
    if "<form" in raw.lower() or "tel:" in raw.lower():
        errors.append("contact-us redirect must not include a form or phone link")
    if "sora" in raw.lower():
        errors.append("contact-us redirect names Sora")
    if "emmanueldevgonzalez@gmail.com" in raw:
        errors.append("contact-us redirect still uses the Gmail address")
    return errors

def social_meta_errors(label, raw, title, desc):
    """Home and MCP titles stay within 60 characters, descriptions within 150–160."""
    errors = []
    if len(title) > TITLE_LIMIT:
        errors.append(f"{label} title is {len(title)} characters")
    if not 150 <= len(desc) <= 160:
        errors.append(f"{label} description is {len(desc)} characters")
    expected = [
        f"<title>{e(title)}</title>",
        f'<meta name="description" content="{e(desc)}">',
        f'<meta property="og:title" content="{e(title)}">',
        f'<meta property="og:description" content="{e(desc)}">',
        f'<meta name="twitter:title" content="{e(title)}">',
        f'<meta name="twitter:description" content="{e(desc)}">',
    ]
    for snippet in expected:
        if snippet not in raw:
            errors.append(f"{label} social tags do not match the title and description")
            break
    return errors

def audit_site():
    """Fail the build if a page breaks the HTML or sponsor rules."""
    from html.parser import HTMLParser

    check_sponsor_renderer()
    errors = []
    required = ("name", "url", "tagline", "active")
    if not isinstance(sponsors, dict) or not sponsors:
        errors.append("data/sponsors.json must be a non-empty object of slots")
    for slot_id, rec in sponsors.items():
        if slot_id not in ("home", "deals") and not str(slot_id).startswith("model:"):
            errors.append(f"unknown sponsor slot id {slot_id}")
            continue
        if not isinstance(rec, dict) or any(key not in rec for key in required):
            errors.append(f"sponsor slot {slot_id} needs name, url, tagline, and active")
            continue
        if not isinstance(rec.get("active"), bool):
            errors.append(f"sponsor slot {slot_id} active must be true or false")

    class PageAudit(HTMLParser):
        void = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.stack = []
            self.h1 = 0
            self.title_parts = []
            self.in_title = False
            self.desc = None
            self.robots = None
            self.canonical = None
            self.bad_sponsor = []
            self.sponsor_ids = []
            self.sponsor_chunks = []
            self.sponsor_links = []
            self.in_sponsor = False
            self.jsonld = []
            self.in_jsonld = False
            self.jsonld_buf = []
            self.in_footer = False
            self.footer_advertise = False
            self.footer_contact = False
            self._link = None

        def handle_starttag(self, tag, attrs):
            ad = {k: ("" if v is None else v) for k, v in attrs}
            if tag == "h1":
                self.h1 += 1
            if tag == "title":
                self.in_title = True
            if tag == "footer":
                self.in_footer = True
            if tag == "meta" and ad.get("name", "").lower() == "description":
                self.desc = ad.get("content", "")
            if tag == "meta" and ad.get("name", "").lower() == "robots":
                self.robots = ad.get("content", "")
            if tag == "link" and ad.get("rel", "").lower() == "canonical":
                self.canonical = ad.get("href", "")
            if tag == "script" and ad.get("type", "").lower() == "application/ld+json":
                self.in_jsonld = True
                self.jsonld_buf = []
            href = ad.get("href", "")
            if tag == "a" and self.in_footer and href.rstrip("/").endswith("/advertise"):
                self.footer_advertise = True
            if tag == "a" and self.in_footer and href.rstrip("/").endswith("/contact"):
                self.footer_contact = True
            classes = ad.get("class", "").split()
            if tag == "aside" and "sponsor" in classes:
                for parent, pattrs in self.stack:
                    pclass = pattrs.get("class", "").split()
                    if (
                        parent in ("table", "tbody", "thead")
                        or "dealgrid" in pclass
                        or "data-deal-card" in pattrs
                        or pattrs.get("id") in ("liveDeals", "archive", "prices", "retired")
                    ):
                        self.bad_sponsor.append(ad.get("data-sponsor", "sponsor"))
                self.in_sponsor = True
                self.sponsor_ids.append(ad.get("data-sponsor", ""))
                self.sponsor_chunks.append([])
                self.sponsor_links.append([])
            if tag == "a" and self.in_sponsor:
                self._link = {"href": href, "rel": ad.get("rel", ""), "text": []}
            if tag not in self.void:
                self.stack.append((tag, ad))

        def handle_endtag(self, tag):
            if tag == "title":
                self.in_title = False
            if tag == "footer":
                self.in_footer = False
            if tag == "script" and self.in_jsonld:
                self.in_jsonld = False
                self.jsonld.append("".join(self.jsonld_buf))
            if tag == "a" and self._link is not None:
                self.sponsor_links[-1].append(self._link)
                self._link = None
            if tag == "aside" and self.in_sponsor:
                self.in_sponsor = False
            if tag in self.void:
                return
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == tag:
                    del self.stack[i:]
                    break

        def handle_data(self, data):
            if self.in_title:
                self.title_parts.append(data)
            if self.in_jsonld:
                self.jsonld_buf.append(data)
            if self.in_sponsor and self.sponsor_chunks:
                self.sponsor_chunks[-1].append(data)
            if self._link is not None:
                self._link["text"].append(data)

    def expected_slots(rel):
        if rel == "index.html":
            ids = ["home"]
        elif rel == "deals/index.html":
            ids = ["deals"]
        else:
            ids = []
            prefix = "models/"
            if rel.startswith(prefix) and rel.endswith("/index.html"):
                rest = rel[len(prefix):-len("index.html")].strip("/")
                if rest and "/" not in rest:
                    ids = ["model:" + rest]
        return [slot for slot in ids if sponsor_filled(sponsor_record(slot))]

    for dirpath, _, filenames in os.walk(DIST):
        for name in filenames:
            if not name.endswith(".html"):
                continue
            path = os.path.join(dirpath, name)
            raw = open(path, encoding="utf-8").read()
            if "<html" not in raw.lower():
                continue
            rel = os.path.relpath(path, DIST).replace(os.sep, "/")
            low = raw.lower()
            if rel == "contact-us/index.html":
                errors.extend(contact_redirect_errors(raw))
                continue
            coming_soon = rel == "newsletter/index.html" and not NEWSLETTER_ENABLED
            missing = rel == "404.html"
            if "nosnippet" in low or ("noindex" in low and not (coming_soon or missing)):
                errors.append(f"{rel} contains noindex or nosnippet")
            parser = PageAudit()
            parser.feed(raw)
            if parser.h1 != 1:
                errors.append(f"{rel} has {parser.h1} h1 elements")
            if not "".join(parser.title_parts).strip():
                errors.append(f"{rel} is missing a title")
            if not parser.desc:
                errors.append(f"{rel} is missing a meta description")
            if missing:
                if parser.robots != "noindex":
                    errors.append(f"{rel} robots must be noindex")
                if parser.canonical or 'rel="canonical"' in raw:
                    errors.append(f"{rel} must not have a canonical link")
                if 'property="og:url"' in raw:
                    errors.append(f"{rel} must not have og:url")
                if "index,follow" in raw:
                    errors.append(f"{rel} still asks crawlers to index")
            elif coming_soon:
                if parser.robots != "noindex":
                    errors.append(f"{rel} robots must be noindex")
                if parser.canonical != SITE_URL + "/newsletter/":
                    errors.append(f"{rel} is missing a canonical")
            else:
                if not parser.canonical or not parser.canonical.startswith(SITE_URL):
                    errors.append(f"{rel} is missing a canonical")
                if parser.robots != "index,follow":
                    errors.append(f"{rel} robots must be index,follow")
            if not missing and "window.goatcounter" in raw:
                errors.append(f"{rel} overrides the GoatCounter path")
            if not NEWSLETTER_ENABLED:
                signup = ("TODO-newsletter-endpoint" in raw or "Get the weekly price-drop email" in raw
                          or ">Newsletter<" in raw or "<form" in low)
                if coming_soon or missing:
                    if signup:
                        errors.append(f"{rel} still shows a newsletter signup or Newsletter link")
                elif signup or "/newsletter/" in raw or "newsletter" in low:
                    errors.append(f"{rel} still shows a newsletter signup or Newsletter link")
                for blob in parser.jsonld:
                    lowb = blob.lower()
                    if "newsletter" in lowb or "subscribe" in lowb or "buttondown" in lowb:
                        errors.append(f"{rel} JSON-LD implies a newsletter signup")
            ico_link = f'<link rel="icon" href="{root("/favicon.ico")}" sizes="any">'
            png_link = f'<link rel="icon" type="image/png" sizes="32x32" href="{root("/favicon-32.png")}">'
            if ico_link not in raw or png_link not in raw:
                errors.append(f"{rel} is missing the favicon.ico link next to the PNG icon")
            if not parser.footer_advertise:
                errors.append(f"{rel} footer is missing Advertise")
            if not parser.footer_contact:
                errors.append(f"{rel} footer is missing Contact")
            if HOUSE_LINE in raw:
                errors.append(f"{rel} shows an empty sponsor placeholder")
            if parser.bad_sponsor:
                errors.append(f"{rel} has a sponsor inside a table or deals list: {parser.bad_sponsor}")
            want = expected_slots(rel)
            if parser.sponsor_ids != want:
                errors.append(f"{rel} sponsor slots {parser.sponsor_ids} != {want}")
            for slot_id, chunks, links in zip(parser.sponsor_ids, parser.sponsor_chunks, parser.sponsor_links):
                text = "".join(chunks)
                if "Sponsor" not in text:
                    errors.append(f"{rel} slot {slot_id} is not labelled Sponsor")
                if slot_id == "deals" and "Featured" not in text:
                    errors.append(f"{rel} deals slot is missing Featured")
                if not links:
                    errors.append(f"{rel} slot {slot_id} has no link")
                for link in links:
                    href = link["href"]
                    ltext = "".join(link["text"]).strip()
                    if href.rstrip("/").endswith("/advertise"):
                        if ltext != HOUSE_LINE:
                            errors.append(f"{rel} slot {slot_id} placeholder text is {ltext!r}")
                        if href != root("/advertise/"):
                            errors.append(f"{rel} slot {slot_id} placeholder href is {href}")
                        if "sponsored" in link["rel"]:
                            errors.append(f"{rel} slot {slot_id} placeholder must not be rel=sponsored")
                    else:
                        if link["rel"] != SPONSOR_REL:
                            errors.append(f"{rel} slot {slot_id} sponsor link rel is {link['rel']!r}")
                        if not ltext:
                            errors.append(f"{rel} slot {slot_id} sponsor link has no name")

    ad_path = os.path.join(DIST, "advertise", "index.html")
    if not os.path.isfile(ad_path):
        errors.append("advertise page was not built")
    else:
        ad = open(ad_path, encoding="utf-8").read()
        if "<h1>Advertise on VidFare</h1>" not in ad:
            errors.append("advertise page h1")
        if AD_MAIL not in ad or CONTACT_EMAIL not in ad:
            errors.append("advertise page mailto")
        if "emmanueldevgonzalez@gmail.com" in ad:
            errors.append("advertise page still uses the Gmail address")
        if "Rates on request." not in ad:
            errors.append("advertise page rates line")
        if NEWSLETTER_ENABLED:
            if "Newsletter sponsor line" not in ad:
                errors.append("advertise page is missing the newsletter spot")
        elif "newsletter" in ad.lower():
            errors.append("advertise page mentions the newsletter while it is off")
        if '"@type": "WebPage"' not in ad:
            errors.append("advertise page JSON-LD WebPage")
        if f'<link rel="canonical" href="{SITE_URL}/advertise/">' not in ad:
            errors.append("advertise page canonical")
    contact_path = os.path.join(DIST, "contact", "index.html")
    if not os.path.isfile(contact_path):
        errors.append("contact page was not built")
    else:
        contact = open(contact_path, encoding="utf-8").read()
        if f"<title>{e(CONTACT_TITLE)}</title>" not in contact:
            errors.append("contact page title")
        if len(CONTACT_TITLE) > TITLE_LIMIT:
            errors.append(f"contact page title is {len(CONTACT_TITLE)} characters")
        if f'<meta name="description" content="{e(contact_desc)}">' not in contact:
            errors.append("contact page meta description")
        if f'<link rel="canonical" href="{SITE_URL}/contact/">' not in contact:
            errors.append("contact page canonical")
        if "<h1>Contact VidFare</h1>" not in contact:
            errors.append("contact page h1")
        mailtos = set(re.findall(r'href="(mailto:[^"]*)"', contact))
        allowed_mail = {f"mailto:{CONTACT_EMAIL}", AD_MAIL}
        if mailtos != allowed_mail:
            errors.append(f"contact page mailto links must be the public address and the sponsorship subject only: {sorted(mailtos)}")
        if f'href="{root("/advertise/")}"' not in contact or f'href="{root("/about/")}"' not in contact:
            errors.append("contact page is missing the advertise or about link")
        if "<form" in contact.lower() or "tel:" in contact.lower():
            errors.append("contact page must not include a form or phone link")
        if "sora" in contact.lower():
            errors.append("contact page names Sora")
        if "emmanueldevgonzalez@gmail.com" in contact:
            errors.append("contact page still uses the Gmail address")
        if 'name="robots" content="index,follow"' not in contact:
            errors.append("contact page robots must be index,follow")
    redirect_path = os.path.join(DIST, "contact-us", "index.html")
    if not os.path.isfile(redirect_path):
        errors.append("contact-us redirect was not built")
    sitemap = open(os.path.join(DIST, "sitemap.xml"), encoding="utf-8").read()
    if f"<loc>{SITE_URL}/contact/</loc>" not in sitemap:
        errors.append("sitemap is missing /contact/")
    if "contact-us" in sitemap:
        errors.append("sitemap includes /contact-us")
    if f"<loc>{SITE_URL}/data/</loc>" not in sitemap:
        errors.append("sitemap is missing /data/")
    if f"<loc>{SITE_URL}/mcp/</loc>" not in sitemap:
        errors.append("sitemap is missing /mcp/")
    for loc in re.findall(r"<loc>([^<]+)</loc>", sitemap):
        if loc.split("?", 1)[0].rstrip("/").endswith(".json"):
            errors.append(f"sitemap includes a JSON URL: {loc}")
    calc_html = open(os.path.join(DIST, "calculator", "index.html"), encoding="utf-8").read()
    calc_canon = re.search(r'<link rel="canonical" href="([^"]*)"', calc_html)
    if not calc_canon or calc_canon.group(1) != SITE_URL + "/calculator/":
        errors.append("calculator canonical must be https://vidfare.com/calculator/")
    if REPORTS_ENABLED:
        published_now = weekly_report.assign(weekly_report.load(), today)
        prior_through = None
        for report in published_now["reports"]:
            modified = weekly_report.report_content_date(report, weekly_report.load(), prior_through)
            report_path = f"/reports/{report['id']}/"
            if f"<loc>{SITE_URL}{report_path}</loc><lastmod>{modified}</lastmod>" not in sitemap:
                errors.append(f"sitemap lastmod for {report_path} should be {modified}")
            report_html = open(os.path.join(DIST, report_path.strip("/"), "index.html"), encoding="utf-8").read()
            if f'"dateModified": "{modified}"' not in report_html:
                errors.append(f"{report_path} dateModified should be {modified}")
            prior_through = report["through"]
        index_date = weekly_report.index_content_date(published_now, weekly_report.load(), today) or LAST
        if f"<loc>{SITE_URL}/reports/</loc><lastmod>{index_date}</lastmod>" not in sitemap:
            errors.append(f"sitemap lastmod for /reports/ should be {index_date}")
    bf_last = SITEMAP_LASTMOD.get("/deals/black-friday/")
    if not bf_last or f"<loc>{SITE_URL}/deals/black-friday/</loc><lastmod>{bf_last}</lastmod>" not in sitemap:
        errors.append("sitemap lastmod for /deals/black-friday/")
    for dirpath, _, filenames in os.walk(DIST):
        for name in filenames:
            if not name.endswith(".html"):
                continue
            raw = open(os.path.join(dirpath, name), encoding="utf-8").read()
            rel = os.path.relpath(os.path.join(dirpath, name), DIST)
            for tag in re.findall(r"<a\b[^>]*>", raw, re.I):
                for href in re.findall(r'href="([^"]*)"', tag):
                    target = href.split("?", 1)[0].split("#", 1)[0]
                    if target.endswith(".json") and "nofollow" not in tag.lower():
                        errors.append(f"{rel} links {href} without nofollow")
    mcp_page = os.path.join(DIST, "mcp", "index.html")
    if not os.path.isfile(mcp_page):
        errors.append("mcp page was not built")
    else:
        mcp_html = open(mcp_page, encoding="utf-8").read()
        if "https://mcp.vidfare.com/mcp" not in mcp_html:
            errors.append("mcp page is missing the endpoint")
        if "<b>Live.</b>" not in mcp_html:
            errors.append("mcp page is missing the live notice")
        if "coming soon" in mcp_html.lower() or "not deployed" in mcp_html.lower():
            errors.append("mcp page still says the server is not live")
        if f"<h1>{e(AGENT_H1)}</h1>" not in mcp_html:
            errors.append("mcp page h1")
        if AGENT_PROMPT not in mcp_html:
            errors.append("mcp page is missing the agent prompt")
        if 'id="copy-prompt"' not in mcp_html or 'id="vidfare-prompt"' not in mcp_html:
            errors.append("mcp page is missing the copy button")
        if e(MCP_CURSOR) not in mcp_html:
            errors.append("mcp page is missing the Cursor snippet")
        if MCP_PRIVACY not in mcp_html:
            errors.append("mcp page is missing the privacy line")
        if "plugin" in mcp_html.lower() or "sora" in mcp_html.lower():
            errors.append("mcp page names a plugin or Sora")
        for tool in ("list_models", "get_model_prices", "estimate_cost", "cheapest_options", "list_deals"):
            if f"<code>{tool}</code>" not in mcp_html:
                errors.append(f"mcp page is missing {tool}")
        errors.extend(social_meta_errors("mcp", mcp_html, MCP_TITLE, MCP_DESC))
    data_html = open(os.path.join(DIST, "data", "index.html"), encoding="utf-8").read()
    if f'href="{root("/mcp/")}"' not in data_html:
        errors.append("data page does not link to /mcp/")
    if "https://mcp.vidfare.com/mcp" not in data_html:
        errors.append("data page is missing the live MCP endpoint")
    if "coming soon" in data_html.lower():
        errors.append("data page still says the MCP server is coming soon")
    auth_file = os.path.join(DIST, ".well-known", "mcp-registry-auth")
    auth_body = open(auth_file, encoding="utf-8").read() if os.path.isfile(auth_file) else ""
    proof = "v=MCPv1; k=ed25519; p=ONNlWhbxQdLcq/vVLAzvHUwd/E1fGGZCcvb7B0M013c=\n"
    if auth_body != proof:
        errors.append("mcp-registry-auth is not the published proof record")
    if not os.path.isfile(os.path.join(DIST, ".nojekyll")):
        errors.append(".nojekyll is missing, so GitHub Pages can skip .well-known")
    if f"<loc>{SITE_URL}/advertise/</loc>" not in sitemap:
        errors.append("sitemap is missing /advertise/")
    if f"<loc>{SITE_URL}/models/</loc>" not in sitemap:
        errors.append("sitemap is missing /models/")
    indexnow_src = open(os.path.join(ROOT, "scripts", "notify_indexnow.py"), encoding="utf-8").read()
    for path, _label in GUIDE_LINKS:
        if f"<loc>{SITE_URL}{path}</loc>" not in sitemap:
            errors.append(f"sitemap is missing {path}")
        if (SITE_URL + path) not in indexnow_src:
            errors.append(f"IndexNow URL list is missing {path}")
        rel = path.strip("/") + "/index.html"
        guide_html = open(os.path.join(DIST, rel), encoding="utf-8").read()
        if f"Last checked {LAST}" not in guide_html:
            errors.append(f"{rel} is missing the last-checked date")
        if 'href="' + root("/about/") + '"' not in guide_html and path != "/guides/":
            errors.append(f"{rel} is missing the about-page link")
        if "<form" in guide_html.lower():
            errors.append(f"{rel} contains a form")
        if "fetch(" in guide_html:
            errors.append(f"{rel} makes a request")
    home_html = open(os.path.join(DIST, "index.html"), encoding="utf-8").read()
    errors.extend(social_meta_errors("home", home_html, HOME_TITLE, HOME_DESC))
    if f"<h1>{e(AGENT_H1)}</h1>" not in home_html:
        errors.append("home page h1")
    if 'id="for-agents"' not in home_html or f'href="{root("/mcp/")}"' not in home_html:
        errors.append("home page is missing the agent section link to /mcp/")
    prices_at = home_html.find('id="prices"')
    agents_at = home_html.find('id="for-agents"')
    news_at = home_html.find('<section class="news" id="newsletter">')
    if agents_at < 0 or prices_at < 0 or not agents_at < prices_at:
        errors.append("agent section must stay above the price table")
    if news_at < 0 or prices_at < 0 or not prices_at < news_at:
        errors.append("newsletter signup must stay under the price table")
    elif "<section" in home_html[prices_at:news_at]:
        errors.append("a section was inserted between the price table and the newsletter")
    if "sora" in home_html.lower() or "plugin" in home_html.lower():
        errors.append("home page names a plugin or Sora")
    home_nav = home_html.split("<nav>", 1)[-1].split("</nav>", 1)[0]
    if ">Contact<" in home_nav:
        errors.append("header nav must stay unchanged and not add Contact")
    if f'href="{root("/guides/")}">Guides</a>' not in home_nav:
        errors.append("nav is missing Guides")
    if f'href="{root("/data/")}">Data</a>' not in home_nav:
        errors.append("nav is missing Data")
    if "<b>Guides:</b>" not in home_html:
        errors.append("footer is missing Guides")
    budget_html = open(os.path.join(DIST, "guides", "ai-video-project-budget", "index.html"), encoding="utf-8").read()
    for label in ("1-minute explainer video", "3-minute music video", "10-minute short film"):
        if label not in budget_html:
            errors.append(f"budget page is missing the {label} preset")
    picked = overall_pick()
    if picked is not None:
        if cost_money(picked["usd_per_second"] * 3 * 60 * 3) not in budget_html:
            errors.append("budget page is missing the 3-minute total at the lowest rate")
        if cost_money(picked["usd_per_second"] * 1 * 60 * 3) not in budget_html:
            errors.append("budget page is missing the 1-minute total at the lowest rate")
    hf_html = open(os.path.join(DIST, "guides", "is-higgsfield-worth-it", "index.html"), encoding="utf-8").read()
    pro_named = any(
        p.get("platform") == "Higgsfield" and (p.get("plan") or "").strip().lower() in ("pro", "pro (monthly)", "pro (annual)")
        for p in plans.values()
    )
    if not pro_named and "not in our plan data" not in hf_html:
        errors.append("Higgsfield guide should say Pro is not in the plan data")
    hf_plan_rows = [r for r in rows if r["platform"] == "Higgsfield"]
    if hf_plan_rows:
        lo = min(hf_plan_rows, key=lambda r: (r["usd_per_second"], r["id"]))
        hi = max(hf_plan_rows, key=lambda r: (r["usd_per_second"], r["id"]))
        intro = higgsfield_intro(lo, hi)
        if intro not in hf_html:
            errors.append("Higgsfield intro mismatch: " + intro)
        if "used to $" in hf_html:
            errors.append("Higgsfield intro still joins the credit assumption to the next price")
    if "1,000 credits" not in hf_html:
        errors.append("Higgsfield guide is missing the per-1,000-credit section")
    if not any("cinema" in f"{r.get('variant') or ''} {models[r['model']]['name']}".lower() for r in rows):
        if "No Cinema Studio rate is in the price data." not in hf_html:
            errors.append("Higgsfield guide should note the missing Cinema Studio rate")
    llms = open(os.path.join(DIST, "llms.txt"), encoding="utf-8").read()
    if f"{SITE_URL}/advertise/" not in llms:
        errors.append("llms.txt does not mention /advertise/")
    if f"{SITE_URL}/mcp/" not in llms or "mcp.vidfare.com/mcp" not in llms:
        errors.append("llms.txt does not mention the MCP server")
    if "coming soon" in llms.lower():
        errors.append("llms.txt still says the MCP server is coming soon")
    for tool in ("list_models", "get_model_prices", "estimate_cost", "cheapest_options", "list_deals"):
        if tool not in llms:
            errors.append(f"llms.txt does not name {tool}")
    errors.extend(mcp_link_errors())
    models_index = os.path.join(DIST, "models", "index.html")
    if not os.path.isfile(models_index):
        errors.append("models index was not built")
    else:
        models_html = open(models_index, encoding="utf-8").read()
        if models_html.count("<h1") != 1:
            errors.append("models index must have one h1")
        if "gc.zgo.at/count.js" not in models_html or '<header class="top">' not in models_html or "<footer>" not in models_html:
            errors.append("models index is missing the site header, footer, or GoatCounter")
        try:
            listed = models_html.split('<ul class="model-index">', 1)[1].split("</ul>", 1)[0]
        except IndexError:
            listed = ""
            errors.append("models index is missing the model list")
        for slug, m in models.items():
            needle = f'<a href="{root(f"/models/{slug}/")}">{e(m["name"])}</a>'
            if needle not in listed:
                errors.append(f"models index is missing {m['name']}")
    not_found_html = open(os.path.join(DIST, "404.html"), encoding="utf-8").read()
    override = "window.goatcounter={path:function(){return '404:'+location.pathname+location.search}}"
    count_at = not_found_html.find('src="https://gc.zgo.at/count.js"')
    over_at = not_found_html.find(override)
    if over_at < 0 or count_at < 0 or over_at > count_at:
        errors.append("404 GoatCounter path override must come before count.js")
    if newsletter_redirect_script() not in not_found_html:
        errors.append("404 is missing the newsletter redirect")
    dest = root("/newsletter/")
    prefix = BASE + "/newsletter"
    for sample, want in (
        (prefix, True),
        (prefix + ".html", True),
        (dest, False),
        (root("/"), False),
        (root("/deals/"), False),
    ):
        got = sample.startswith(prefix) and sample != dest
        if got != want:
            errors.append(f"newsletter redirect for {sample} should be {want}")
    main404 = not_found_html.split("<main", 1)[-1].split("</main>", 1)[0]
    for href in (root("/"), root("/deals/"), root("/calculator/"), root("/changes/")):
        if f'href="{href}"' not in main404:
            errors.append(f"404 is missing a link to {href}")
    linked_models = sum(
        1 for slug, _m in sample_models
        if f'href="{root(f"/models/{slug}/")}"' in main404
    )
    if linked_models < 3:
        errors.append("404 should link a few model pages in the page body")
    if not NEWSLETTER_ENABLED:
        if "/newsletter/" in sitemap:
            errors.append("sitemap includes /newsletter/ while the newsletter is off")
        news_path = os.path.join(DIST, "newsletter", "index.html")
        if not os.path.isfile(news_path):
            errors.append("coming-soon newsletter page was not built")
        else:
            news_html = open(news_path, encoding="utf-8").read()
            if "<h1>Newsletter coming soon</h1>" not in news_html:
                errors.append("newsletter page is missing the coming soon heading")
            if "<form" in news_html.lower() or "TODO-newsletter-endpoint" in news_html:
                errors.append("newsletter page must not include a signup form")
            if "gc.zgo.at/count.js" not in news_html or "window.goatcounter" in news_html:
                errors.append("newsletter page should use the normal GoatCounter snippet")
            if '<header class="top">' not in news_html or "<footer>" not in news_html:
                errors.append("newsletter page is missing the site header or footer")
            main_news = news_html.split("<main", 1)[-1].split("</main>", 1)[0]
            for href in (root("/"), root("/deals/"), root("/changes/")):
                if f'href="{href}"' not in main_news:
                    errors.append(f"newsletter page is missing a link to {href}")
            nav = news_html.split("<nav>", 1)[-1].split("</nav>", 1)[0]
            if "newsletter" in nav.lower():
                errors.append("newsletter nav link is present while the newsletter is off")
        if "newsletter" in llms.lower() or "subscribe" in llms.lower():
            errors.append("llms.txt implies a newsletter signup")
    else:
        news_path = os.path.join(DIST, "newsletter", "index.html")
        news_html = open(news_path, encoding="utf-8").read() if os.path.isfile(news_path) else ""
        if f'action="{KIT_FORM_ACTION}"' not in news_html or "ck.5.js" not in news_html:
            errors.append("newsletter page is missing the Kit form")
        if "Check your inbox to confirm." not in news_html:
            errors.append("newsletter page is missing the confirm-inbox line")
        if "TODO-newsletter-endpoint" in news_html or "preventDefault" in news_html:
            errors.append("newsletter page still blocks the Kit form")
        if 'name="email_address"' not in news_html:
            errors.append("newsletter page email field")
        if f'data-sv-form="{KIT_FORM_ID}"' not in news_html or f'data-uid="{KIT_FORM_UID}"' not in news_html:
            errors.append("newsletter form id or uid changed")
        if 'data-element="errors"' not in news_html or 'data-element="fields"' not in news_html:
            errors.append("newsletter form is missing Kit success and error targets")
        if 'aria-live="polite"' not in news_html:
            errors.append("newsletter form is missing an aria-live region")
        if KIT_SUCCESS not in news_html:
            errors.append("newsletter form is missing the Kit success message")
        home_form = open(os.path.join(DIST, "index.html"), encoding="utf-8").read()
        for rel, text in (("home", home_form), ("newsletter", news_html)):
            if text.count(KIT_FORM_ACTION) != 1 or text.count('name="email_address"') != 1:
                errors.append(f"{rel} Kit form action or email field was duplicated or dropped")
    if weekly_report.format_usd("0.0272") != money("0.0272") or weekly_report.format_usd("0.1") != money("0.1"):
        errors.append("report dollar format drifted from the price table")
    if REPORTS_ENABLED:
        if not report_paths or "/reports/" not in report_paths:
            errors.append("reports index was not built")
        index_html = open(os.path.join(DIST, "reports", "index.html"), encoding="utf-8").read()
        if "<h1>AI video price change reports</h1>" not in index_html:
            errors.append("reports index h1")
        if weekly_report.INDEX_DESCRIPTION not in index_html:
            errors.append("reports index description")
        if ">Reports<" not in index_html:
            errors.append("reports nav link missing")
        published = weekly_report.assign(weekly_report.load(), today)["reports"]
        for report in published:
            rel = os.path.join("reports", report["id"], "index.html")
            report_html = open(os.path.join(DIST, rel), encoding="utf-8").read()
            headline = weekly_report.report_h1(report)
            if report_html.count("<h1>") != 1 or f"<h1>{headline}</h1>" not in report_html:
                errors.append(f"{rel} h1")
            if weekly_report.change_counts(report)["price"]:
                if "<table>" not in report_html or "Before" not in report_html or "After" not in report_html:
                    errors.append(f"{rel} price table")
            elif weekly_report.NO_PRICE_NOTE not in report_html:
                errors.append(f"{rel} missing the no-price-changes note")
            if f'"headline": "{headline}"' not in report_html:
                errors.append(f"{rel} JSON-LD headline")
            if "data-sponsor" in report_html:
                errors.append(f"{rel} must not put a sponsor in the report")
    else:
        if os.path.isdir(os.path.join(DIST, "reports")):
            errors.append("reports pages are published while REPORTS_ENABLED is false")
        if "/reports/" in sitemap or "/reports/" in llms:
            errors.append("reports URL is published while REPORTS_ENABLED is false")
        home = open(os.path.join(DIST, "index.html"), encoding="utf-8").read()
        if ">Reports<" in home:
            errors.append("Reports nav link is live while REPORTS_ENABLED is false")
    kling_llms = ""
    for chunk in llms.split("### "):
        if chunk.startswith("Kling 3.0"):
            kling_llms = chunk
            break
    fal_line = next((line for line in kling_llms.splitlines() if line.startswith("- fal:")), "")
    if "Pro tier, resolution not listed, without audio" not in fal_line or "plan tier Pro tier" in fal_line:
        errors.append("llms.txt Kling fal line does not read as Pro tier with audio off")
    if "plan tier Standard" not in llms:
        errors.append("llms.txt dropped the plan tier prefix for a name that does not end in tier")
    estimate_line = "Estimated from credit plan. Assumes every credit you pay for is used."
    for rel in ("index.html", "models/kling-3-0/index.html"):
        page_html = open(os.path.join(DIST, rel), encoding="utf-8").read()
        if estimate_line not in page_html:
            errors.append(f"{rel} is missing the credit-plan estimate assumption")
        if "published rate" not in page_html or "estimated from credit plan" not in page_html:
            errors.append(f"{rel} does not label published rates and credit-plan estimates")
        pro_rows = [
            part.split("</tr>", 1)[0]
            for part in page_html.split("<tr>")
            if "Pro, audio off" in part and "<td" in part.split("</tr>", 1)[0]
        ]
        if not pro_rows or ">Pro tier<" not in pro_rows[0] or ">without audio<" not in pro_rows[0] or ">not listed<" not in pro_rows[0]:
            errors.append(f"{rel} Kling Pro audio-off row is missing plan tier, resolution, or audio")
        if ">Plan tier</th>" not in page_html or ">Resolution</th>" not in page_html or ">Audio</th>" not in page_html:
            errors.append(f"{rel} price table is missing plan tier, resolution, or audio headings")
    kling_page = open(os.path.join(DIST, "models", "kling-3-0", "index.html"), encoding="utf-8").read()
    if "Pro tier, resolution not listed, without audio" not in kling_page or "plan tier Pro tier" in kling_page:
        errors.append("Kling model page comparison does not read as Pro tier with audio off")
    if "plan tier Standard, resolution not listed, without audio" not in kling_page:
        errors.append("Kling model page dropped the plan tier prefix for Standard")
    host = urlparse(SITE_URL).hostname or ""
    cname_dist = open(os.path.join(DIST, "CNAME"), encoding="utf-8").read().strip()
    cname_root = open(os.path.join(ROOT, "CNAME"), encoding="utf-8").read().strip()
    if cname_dist != host or cname_root != host:
        errors.append(f"CNAME must be {host}")
    key_file = os.path.join(DIST, notify_indexnow.KEY + ".txt")
    key_body = open(key_file, encoding="utf-8").read().strip() if os.path.isfile(key_file) else ""
    if key_body != notify_indexnow.KEY:
        errors.append("IndexNow key file is missing from the site root")
    if notify_indexnow.HOST != host or notify_indexnow.KEY_LOCATION != f"{SITE_URL}/{notify_indexnow.KEY}.txt":
        errors.append("IndexNow host or key location does not match the site")
    robots = open(os.path.join(DIST, "robots.txt"), encoding="utf-8").read()
    if f"Sitemap: {SITE_URL}/sitemap.xml" not in robots:
        errors.append("robots.txt sitemap is not the site URL")
    if not os.path.isfile(os.path.join(DIST, "google43692aaea77cfb47.html")):
        errors.append("Google verification file is missing")
    if 'name="google-site-verification"' not in home_html:
        errors.append("Google verification meta tag is missing")
    old_url_markers = ("/clipcost", "sheepinboots.github.io")
    for dirpath, _, filenames in os.walk(DIST):
        for name in filenames:
            path = os.path.join(dirpath, name)
            if not name.endswith((".html", ".xml", ".txt", ".json", ".css", ".js")) and name != "CNAME":
                continue
            text = open(path, encoding="utf-8").read()
            rel = os.path.relpath(path, DIST)
            for marker in old_url_markers:
                if marker in text:
                    errors.append(f"{rel} still contains {marker}")
                    break
    png_bytes = open(os.path.join(ROOT, "src", "favicon-32.png"), "rb").read()
    ico_path = os.path.join(DIST, "favicon.ico")
    ico_bytes = open(ico_path, "rb").read() if os.path.isfile(ico_path) else b""
    if not ico_bytes.startswith(b"\x00\x00\x01\x00") or png_bytes not in ico_bytes:
        errors.append("favicon.ico was not generated from favicon-32.png")
    about = open(os.path.join(DIST, "about", "index.html"), encoding="utf-8").read()
    if 'Sponsored placements are labelled "Sponsor" and never affect the price order.' not in about:
        errors.append("about disclosure is missing the sponsor sentence")
    if f'<p class="small">Contact: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>.</p>' not in about:
        errors.append("about page contact line")
    if "emmanueldevgonzalez@gmail.com" in about:
        errors.append("about page still uses the Gmail address")
    if "TODO-add-contact-email" in about:
        errors.append("about page still has the contact placeholder")
    if '<p class="small">Directories: <a href="https://dang.ai">Dang.ai</a>.</p>' not in about:
        errors.append("about page is missing the Dang.ai directory line")
    if "Edited by Emmanuel Gonzalez" not in about:
        errors.append("about page is missing the editor byline")
    if "How we source and check prices" not in about:
        errors.append("about page is missing the price-check description")
    if "check manually" in about.lower() or "checked by hand" in about.lower():
        errors.append("about page claims a manual check")
    runway = open(os.path.join(DIST, "models", "runway-gen-4", "index.html"), encoding="utf-8").read()
    if "gen4_turbo" not in runway or "$0.05" not in runway:
        errors.append("Runway page dropped the gen4_turbo price")
    if "0.09375" not in runway or "Runway Gen-4.5" not in runway:
        errors.append("Runway page dropped the Krea Gen-4.5 deal price")
    if "not a cut on gen4_turbo" not in runway:
        errors.append("Runway page still presents the Krea deal as the gen4_turbo price")
    if "estimated from credit plan" not in runway or "published rate" not in runway:
        errors.append("Runway page does not separate the published rate from the credit-plan estimate")
    cheap = open(os.path.join(DIST, "guides", "cheapest-ai-video-generator", "index.html"), encoding="utf-8").read()
    wan = open(os.path.join(DIST, "guides", "cheapest-wan-3-0", "index.html"), encoding="utf-8").read()
    for rel, text in (("cheapest guide", cheap), ("wan guide", wan)):
        visible = visible_page_text(text).lower()
        for phrase in ("price file", "check manually", "when the site is built", "when site built"):
            if phrase in visible:
                errors.append(f"{rel} still says {phrase!r}")
        if "Edited by Emmanuel Gonzalez" not in text:
            errors.append(f"{rel} is missing the editor byline")
    if visible_page_text(cheap).lower().count("the lowest rate we track is") != 1:
        errors.append("cheapest guide repeats the lowest-rate sentence")
    home_visible = visible_page_text(home_html)
    if "Affiliate disclosure" not in home_visible:
        errors.append("home page is missing the short affiliate disclosure")
    kling = open(os.path.join(DIST, "models", "kling-3-0", "index.html"), encoding="utf-8").read()
    if "Edited by Emmanuel Gonzalez" not in kling:
        errors.append("model page is missing the editor byline")
    for dirpath, _, filenames in os.walk(DIST):
        for name in filenames:
            if not name.endswith((".html", ".xml", ".txt", ".json")):
                continue
            path = os.path.join(dirpath, name)
            text = open(path, encoding="utf-8", errors="replace").read()
            if "emmanueldevgonzalez@gmail.com" in text:
                errors.append(os.path.relpath(path, DIST) + " still contains the Gmail address")
    if 'href="https://twelve.tools">Twelve Tools</a>' not in home_html.split("<footer>", 1)[-1]:
        errors.append("footer is missing the Twelve Tools link")
    for rel in ("deals.json", os.path.join("data", "deals.json")):
        feed = open(os.path.join(DIST, rel), encoding="utf-8").read()
        if "data-sponsor" in feed or "Your tool here" in feed or "sponsor this spot" in feed:
            errors.append(f"{rel} contains sponsor placement markup")
    import test_titles
    errors.extend(test_titles.title_errors(DIST))
    errors.extend(structured_data_errors())
    errors.extend(feed_errors())
    errors.extend(viewport_overflow_errors())
    errors.extend(variations.variation_errors(rows))
    if errors:
        raise SystemExit("site audit failed:\n- " + "\n- ".join(errors))

def visible_page_text(raw):
    """Text a reader sees. Inline tags are removed without inserting spaces."""
    import re
    cleaned = re.sub(r"(?is)<script\b[^>]*>.*?</script>", " ", raw)
    cleaned = re.sub(r"(?is)<style\b[^>]*>.*?</style>", " ", cleaned)
    cleaned = re.sub(r"(?is)<br\s*/?>", " ", cleaned)
    cleaned = re.sub(r"(?is)</(p|div|li|h1|h2|h3|tr|section|article)>", " ", cleaned)
    cleaned = re.sub(r"(?is)<[^>]+>", "", cleaned)
    cleaned = html.unescape(cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()

def norm_space(text):
    import re
    return re.sub(r"\s+", " ", text or "").strip()

def jsonld_nodes(node, out):
    if isinstance(node, list):
        for item in node:
            jsonld_nodes(item, out)
        return
    if not isinstance(node, dict):
        return
    out.append(node)
    if isinstance(node.get("@graph"), list):
        jsonld_nodes(node["@graph"], out)

def structured_data_errors():
    import re
    errors = []
    alternate = f'rel="alternate" type="application/rss+xml" title="{BRAND}" href="{root("/feed.xml")}"'
    for dirpath, _, filenames in os.walk(DIST):
        for name in filenames:
            if not name.endswith(".html"):
                continue
            path = os.path.join(dirpath, name)
            raw = open(path, encoding="utf-8").read()
            if "<html" not in raw.lower():
                continue
            rel = os.path.relpath(path, DIST).replace(os.sep, "/")
            if rel == "contact-us/index.html":
                continue
            if alternate not in raw:
                errors.append(f"{rel} is missing the feed.xml alternate link")
            visible = visible_page_text(raw)
            for match in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S):
                blob = html.unescape(match.group(1))
                try:
                    data = json.loads(blob)
                except json.JSONDecodeError as exc:
                    errors.append(f"{rel} JSON-LD is invalid: {exc}")
                    continue
                nodes = []
                jsonld_nodes(data, nodes)
                for node in nodes:
                    types = node.get("@type")
                    types = types if isinstance(types, list) else [types]
                    if "FAQPage" not in types:
                        continue
                    for question in node.get("mainEntity") or []:
                        q = norm_space((question or {}).get("name") or "")
                        answer = (question or {}).get("acceptedAnswer") or {}
                        a = norm_space(answer.get("text") if isinstance(answer, dict) else "")
                        if not q or not a:
                            errors.append(f"{rel} FAQ entry is missing a question or answer")
                            continue
                        if q not in visible or a not in visible:
                            errors.append(f"{rel} FAQ text is not on the page: {q[:80]}")
    return errors

def viewport_overflow_errors():
    """Fail when a sitemap page is wider than a 390px phone. Skip if Chrome is not installed."""
    import subprocess
    chrome = next((p for p in (
        os.environ.get("CHROME_PATH"), os.environ.get("CHROME_BIN"),
        "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/chromium",
    ) if p and os.path.isfile(p)), None)
    script = os.path.join(ROOT, "scripts", "check_viewport.mjs")
    if not chrome or not os.path.isdir(os.path.join(ROOT, "node_modules", "puppeteer-core")):
        print("viewport check skipped (Chrome or puppeteer-core is not installed)", file=sys.stderr)
        return []
    out = subprocess.run(["node", script, DIST, chrome], capture_output=True, text=True, timeout=180)
    text = (out.stdout or "") + (out.stderr or "")
    if out.returncode != 0:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return lines or ["viewport check failed"]
    return []

def feed_errors():
    import xml.etree.ElementTree as ET
    errors = []
    path = os.path.join(DIST, "feed.xml")
    if not os.path.isfile(path):
        return ["feed.xml was not built"]
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"feed.xml is not valid XML: {exc}"]
    if root.tag != "rss":
        errors.append("feed.xml root is not rss")
        return errors
    channel = root.find("channel")
    if channel is None:
        return ["feed.xml is missing a channel"]
    by_guid = {}
    for item in channel.findall("item"):
        fields = {tag: (item.find(tag).text or "").strip() if item.find(tag) is not None else "" for tag in ("title", "link", "guid", "pubDate", "category")}
        if any(not fields[tag] for tag in ("title", "link", "guid", "pubDate")):
            errors.append("feed item is missing title, link, guid, or pubDate")
            continue
        if fields["guid"] in by_guid:
            errors.append(f"feed guid is repeated: {fields['guid']}")
        parsed = email.utils.parsedate_to_datetime(fields["pubDate"])
        if parsed is None:
            errors.append(f"feed pubDate is not a date: {fields['pubDate']}")
            continue
        by_guid[fields["guid"]] = parsed.date().isoformat()
        if fields["category"] not in ("price change", "report", "deal"):
            errors.append(f"feed category {fields['category']!r} is not a price change, report, or deal")
    for change in changes:
        day = change.get("date")
        if not day:
            continue
        guid = f"{SITE_URL}/changes/#{change_anchor(change)}"
        if by_guid.get(guid) != day:
            errors.append(f"feed price change {guid} is dated {by_guid.get(guid)} instead of {day}")
    if REPORTS_ENABLED:
        for report in weekly_report.assign(weekly_report.load(), today)["reports"]:
            guid = f"{SITE_URL}/reports/{report['id']}/"
            if by_guid.get(guid) != report["through"]:
                errors.append(f"feed report {guid} is dated {by_guid.get(guid)} instead of {report['through']}")
    for deal in live_sorted:
        day = deal.get("start") or deal.get("verified_date")
        if not day:
            continue
        guid = f"{SITE_URL}/deals/#{deal['id']}"
        if by_guid.get(guid) != day:
            errors.append(f"feed deal {guid} is dated {by_guid.get(guid)} instead of {day}")
    if not any(item.find("category") is not None and item.find("category").text == "price change" for item in channel.findall("item")):
        errors.append("feed.xml has no price changes")
    if REPORTS_ENABLED and not any(item.find("category") is not None and item.find("category").text == "report" for item in channel.findall("item")):
        errors.append("feed.xml has no weekly reports")
    if not any(item.find("category") is not None and item.find("category").text == "deal" for item in channel.findall("item")):
        errors.append("feed.xml has no deals")
    errors.extend(atom_self_errors(path, SITE_URL + "/feed.xml"))
    errors.extend(atom_self_errors(os.path.join(DIST, "deals.xml"), SITE_URL + "/deals.xml"))
    return errors

def atom_self_errors(path, href):
    name = os.path.basename(path)
    if not os.path.isfile(path):
        return [f"{name} was not built"]
    text = open(path, encoding="utf-8").read()
    errors = []
    if "ns0" in text:
        errors.append(f"{name} uses the ns0 namespace prefix")
    if text.count('xmlns:atom="http://www.w3.org/2005/Atom"') != 1:
        errors.append(f"{name} should declare xmlns:atom once")
    compact = re.sub(r"\s+", " ", text)
    if f'<atom:link href="{href}" rel="self" type="application/rss+xml"' not in compact:
        errors.append(f"{name} is missing atom:link rel=self")
    return errors

audit_site()
write_report_preview()
print("built", len(urls), "pages into", DIST)
