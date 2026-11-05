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
# TODO: set True once the Buttondown form endpoint is live (see NEWSLETTER_ACTION).
# While False, the signup form, the Newsletter nav link, and the advertise-page
# newsletter spot are omitted. /newsletter/ is a noindex coming-soon page and
# stays out of sitemap.xml.
NEWSLETTER_ENABLED = False
NEWSLETTER_ACTION = "#TODO-newsletter-endpoint"  # TODO: Buttondown form action
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

def plat_link(p, url):
    if p in ("Higgsfield", "Higgsfield API") or is_higgsfield(url):
        href = with_fpr(url) if is_higgsfield(url) else AFF.get(p, HF_BASE)
        return f'<a href="{html.escape(href)}" rel="sponsored nofollow noopener" target="_blank">{html.escape(p)}</a>'
    if p in AFF: return f'<a href="{AFF[p]}" rel="sponsored nofollow noopener" target="_blank" data-affiliate="TODO">{html.escape(p)}</a>'
    return f'<a href="{html.escape(url)}" rel="nofollow noopener" target="_blank">{html.escape(p)}</a>'
e = html.escape
HOUSE_LINE = "Your tool here: sponsor this spot"
SPONSOR_REL = "sponsored nofollow noopener"

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
    return render_sponsor(slot_id, sponsor_record(slot_id), featured)
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

def page(path, title, desc, body, active="", extra_head="", dest=None, reports_nav=None, robots="index,follow", canonical=True, before_count=""):
    canon = SITE_URL + path
    show_reports = REPORTS_ENABLED if reports_nav is None else reports_nav
    navs = [("/", "Prices"), ("/deals/", "Deals"), ("/calculator/", "Credit calculator"), ("/guides/", "Guides"), ("/changes/", "Price changes"), ("/data/", "Data")]
    if NEWSLETTER_ENABLED:
        navs.append(("/newsletter/", "Newsletter"))
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
<p>© {today.year} {BRAND} · Data last checked {LAST} · <a href="{root("/data/")}">Price data</a> · <a href="{root("/advertise/")}">Advertise</a></p></div></footer>
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
    page("/reports/", f"{weekly_report.INDEX_H1} | {BRAND}", weekly_report.INDEX_DESCRIPTION,
         weekly_report.render_index_body(result, events, href_fn=root, public_log=public_log),
         "/reports/", ld_script(weekly_report.index_jsonld(SITE_URL + "/reports/")),
         dest=dest, reports_nav=reports_nav)
    prior = None
    for report in result["reports"]:
        path = f"/reports/{report['id']}/"
        headline = weekly_report.report_h1(report)
        description = weekly_report.report_description(report)
        body = weekly_report.render_report_body(
            report, events, prior, link_fn=lambda url: outbound(url))
        page(path, f"{headline} | {BRAND}", description, body, "/reports/",
             ld_join(
                 weekly_report.report_jsonld(report, SITE_URL + path),
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

def tag(st): return f'<span class="tag {st}">{ {"verified":"vendor-stated","estimate":"approx.","promo":"promo","discontinued":"discontinued"}[st] }</span>'

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
    best = dealmod.best_deal_price(rs, LIVE_DEALS, plans, TODAY)
    if not best:
        return ""
    deal = DEAL_BY_ID[best["deal_id"]]
    row = best["row"]
    return (f'<div class="sub" {deal_attrs(deal)}>With live deals: {money(best["usd"])}/s on {e(row["platform"])} '
            f'({e(spec_phrase(row))}) · <span class="ends">{e(ends_fallback(deal))}</span></div>')

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
        if r.get("status") == "estimate":
            return "Estimate: " + CREDIT_USE
        return "Assumes every credit you pay for is used"
    if r.get("status") == "estimate":
        note = (r.get("note") or "").strip()
        if note:
            return "Estimate: " + note
        return "Estimate: the vendor marks this rate as approximate"
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
            f'<td>{tag(r["status"])}{promo}{deal_badges(r)}{disc}</td><td class="math">{extra}</td>'
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
    text = f"{money(r['usd_per_second'])}/s{where}, {spec_phrase(r)} (checked {r['checked']})"
    if r.get("status") == "promo" and r.get("promo_until"):
        text += f", promo until {r['promo_until']}"
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
            f"As of {LAST}, from {money(c['usd_per_second'])}/s ({c['platform']}, {c['resolution']}). A 5-second clip at that rate costs about {clip5}.",
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

def news_box():
    # TODO: restore the signup by setting NEWSLETTER_ENABLED once Buttondown is live.
    if not NEWSLETTER_ENABLED:
        return ""
    return f"""<section class="news" id="newsletter"><h2 style="margin-top:0">Get the weekly price-drop email</h2>
<p class="small" style="margin:0">Every Monday: price changes, new models, and the cheapest way to run each one. Free, unsubscribe any time.</p>
<form action="{NEWSLETTER_ACTION}" method="post" onsubmit="event.preventDefault();this.querySelector('button').textContent='Thanks! (signup not connected yet)';">
<!-- TODO: point action at the Buttondown form endpoint -->
<input type="email" name="email" required placeholder="you@email.com" aria-label="Email address"><button class="btn" type="submit">Subscribe</button></form></section>"""

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
    st = r.get("status")
    if st == "promo" and r.get("promo_until"):
        return f"a promo until {r['promo_until']}"
    if st == "promo":
        return "a promo"
    if st == "estimate":
        return "an approximate rate"
    if st == "verified":
        return "a vendor-stated rate"
    return str(st or "a listed rate")

def rate_clause(r):
    """One plain-text price clause. The shown $/s is display-rounded; the row value is unchanged."""
    bit = (
        f"{rate_money(r['usd_per_second'])} per second on {r['platform']} "
        f"({spec_phrase(r)}), {status_phrase(r)} (checked {r['checked']})"
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
    low = f"{rate_money(lo['usd_per_second'])}/s ({plan_short_name(lo.get('plan_name'))}, {shown_resolution(lo)})"
    high_bits = f"{plan_short_name(hi.get('plan_name'))}, {models[hi['model']]['name']} {shown_resolution(hi)}"
    if hi.get("status") == "estimate":
        high_bits += ", approximate"
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
    "Every dollar figure on this page comes from the price rows when the site is built. "
    "API rows use the vendor's stated dollars per second. "
    f"Credit-plan rows use plan price ÷ credits × credits per clip ÷ seconds, and {CREDIT_USE}. "
    'A promo shows its end date. An approximate row is one the vendor marked with "~", "roughly", or "estimated". '
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

def guide_page(path, title, desc, body, faqs):
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
            f'<div class="sub">Without promos: {rate_money(alt["usd_per_second"])}/s on {e(alt["platform"])} '
            f'({e(spec_phrase(alt))})</div>'
        )
        if assumption_text(alt):
            alt_html += assumption_html(alt)
    promo = ""
    if r.get("status") == "promo" and r.get("promo_until"):
        promo = f' <span class="small">until {e(r["promo_until"])}</span>'
    return (
        f'<div class="card"><h3>{e(title)}</h3>'
        f'<div class="big">{rate_money(r["usd_per_second"])}<span class="small">/s</span></div>'
        f'{assumption_html(r)}'
        f'<div class="sub">{e(r["platform"])} · {e(spec_phrase(r))} {tag(r["status"])}{promo}</div>'
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
        alt = f'<div class="sub">Without promos: {money(c2["usd_per_second"])}/s on {e(c2["platform"])} ({e(spec_phrase(c2))})</div>'
        if assumption_text(c2):
            alt += assumption_html(c2)
    cards += (f'<div class="card"><h3>{e(m["name"])}</h3><div class="big">{money(c["usd_per_second"])}<span class="small">/s</span></div>'
              f'{assumption_html(c)}'
              f'<div class="sub">{e(c["platform"])} · {e(spec_phrase(c))} {tag(c["status"])}</div>{alt}'
              f'{deal_price_line(rs)}'
              f'<a class="go" href="{root(f"/models/{slug}/")}">All {len(rs)} prices →</a></div>')
opts = lambda vals: "".join(f'<option value="{e(v)}">{e(l)}</option>' for v, l in vals)
platforms = sorted({r["platform"] for r in rows})
ver = sum(r["status"] == "verified" for r in rows)
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

home = f"""<h1>AI video cost per second, compared</h1>
<p class="tagline">{e(TAGLINE)}</p>
<p class="lead">{len(rows)} prices for {len(models)} video models on {len(platforms)} platforms, from Higgsfield plans to the fal, Runway and Kling APIs. Everything is converted to <b>dollars per second of video</b>, and the math is shown for credit plans. Checked {LAST}.</p>
{sponsor_slot("home")}
{ending_strip()}
<h2>Cheapest way to run each model today</h2><div class="cards">{cards}</div>
<p class="small">The lowest $/s for each model at any resolution, including temporary promos (labelled). Low-res tiers are usually the cheapest, so check the resolution.</p>
{home_guides_html()}
<h2>All prices</h2>
<div class="filters">
<select id="fModel" aria-label="Model"><option value="">All models</option>{opts([(s, m["name"]) for s, m in models.items()])}</select>
<select id="fPlat" aria-label="Platform"><option value="">All platforms</option>{opts([(p, p) for p in platforms])}</select>
<select id="fKind" aria-label="Type"><option value="">API + plans</option><option value="api">Pay-as-you-go API</option><option value="plan">Subscription plans</option></select>
<input id="fRes" placeholder="Resolution e.g. 720p" aria-label="Resolution" size="16">
<label class="chk" for="fPromo"><input type="checkbox" id="fPromo"> hide promos</label>
<label class="chk" for="fEst"><input type="checkbox" id="fEst"> hide approximations</label>
<span class="small" id="count"></span></div>
{wide_table(THEAD + "<tbody>" + "".join(row_html(r) for r in sorted(rows, key=lambda r: r["usd_per_second"])) + "</tbody>", ' id="prices"')}
<p class="small"><span class="tag verified">vendor-stated</span> = the number is on the vendor's page (plan rows: plan price ÷ credits × credits per clip, all vendor-stated). <span class="tag estimate">approx.</span> = the vendor itself says "~", "roughly" or "estimated". <span class="tag promo">promo</span> = temporary discount with an end date. <span class="tag discontinued">discontinued</span> = the vendor has shut the endpoint down; the last recorded rate is not a current price. {ver} of {len(rows)} live rows are vendor-stated.</p>
{retired_table(retired_rows)}
{news_box()}
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
function tag(s){{return `<span class="tag ${{s}}">${{{{verified:'vendor-stated',estimate:'approx.',promo:'promo',discontinued:'discontinued'}}[s]||esc(s)}}</span>`}}
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
function assumptionOf(r){{if(r.kind==='plan')return r.status==='estimate'?'Estimate: assumes every credit you pay for is used':'Assumes every credit you pay for is used';if(r.status==='estimate'){{const note=String(r.note||'').trim();return note?'Estimate: '+note:'Estimate: the vendor marks this rate as approximate'}}return ''}}
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
  return `<tr><td><a href="${{BASE}}/models/${{r.model}}/">${{esc(MODELS[r.model])}}</a></td><td>${{plat(r)}}</td><td>${{esc(r.variant)}}</td><td>${{esc(tierOf(r))}}</td><td>${{esc(resOf(r))}}</td><td>${{factLines(r)}}</td><td class="num"><span class="amt">${{money(r.usd_per_second)}}</span>${{assumeHtml}}</td><td>${{tag(r.status)}}${{promo}}${{badges}}${{disc}}</td><td class="math">${{extra}}</td><td class="small"><a href="${{esc(srcHref)}}" rel="${{srcRel}}" target="_blank">source</a><br>${{r.checked}}</td></tr>`}}).join('');
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
            "description": TAGLINE,
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
page("/", f"Compare AI Video Cost Per Second ({MONTH}) | {BRAND}",
     f"Compare what AI video costs per second across Higgsfield, fal, Runway, Kling, Krea, Magnific, Replicate and Atlas Cloud. Checked {LAST}.",
     home, "/", ld_script(home_ld))

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
                extra = f" · {name} {ex.get('resolution') or ''} {money(ex['usd'])}/s vs {money(ex['list_usd'])}/s"
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

# ---------- Model pages ----------
for slug, m in models.items():
    rs = sorted([r for r in rows if r["model"] == slug], key=lambda r: r["usd_per_second"])
    c = cheapest(rs); c2 = cheapest(rs, False)
    byres = {}
    for r in rs: byres.setdefault(r["resolution"], r)
    def res_item(k, v):
        heading = k if str(k).strip() not in MISSING_RESOLUTIONS else "not listed"
        tail = f" {e(assumption_text(v).rstrip('.'))}." if assumption_text(v) else ""
        return (f'<li><b>{e(heading)}</b>: {money(v["usd_per_second"])}/s on {e(v["platform"])} '
                f'({e(spec_phrase(v))}) {tag(v["status"])}{tail}</li>')
    resl = "".join(res_item(k, v) for k, v in byres.items())
    api_rs = [r for r in rs if r["kind"] == "api"]; plan_rs = [r for r in rs if r["kind"] == "plan"]
    ca = cheapest(api_rs, False); cp = cheapest(plan_rs, False)
    summary = f"<p>The cheapest price we found today is <b>{money(c['usd_per_second'])} per second</b> on <b>{e(c['platform'])}</b> ({e(spec_phrase(c))})"
    summary += f", a promo that ends {c['promo_until']}." if c["status"] == "promo" else "."
    if assumption_text(c):
        summary += " " + e(assumption_text(c).rstrip(".")) + "."
    if c2 is not c:
        summary += f" Without promos, the cheapest is {money(c2['usd_per_second'])}/s on {e(c2['platform'])} ({e(spec_phrase(c2))})."
        if assumption_text(c2):
            summary += " " + e(assumption_text(c2).rstrip(".")) + "."
    summary += "</p>"
    more = []
    if ca:
        line = f"Cheapest pay-as-you-go API: {money(ca['usd_per_second'])}/s on {e(ca['platform'])} ({e(spec_phrase(ca))})."
        if assumption_text(ca):
            line += " " + e(assumption_text(ca).rstrip(".")) + "."
        more.append(line)
    if cp:
        line = f"Cheapest subscription: {money(cp['usd_per_second'])}/s on {e(cp['platform'])} ({e(spec_phrase(cp))})."
        if assumption_text(cp):
            line += " " + e(assumption_text(cp).rstrip(".")) + "."
        more.append(line)
    if more:
        summary += "<p>" + " ".join(more) + "</p>"
    clip5 = money(c["usd_per_second"] * 5)
    faqs = model_faqs(m, rs, clip5)
    model_deals = deals_for_model(slug, rs)
    deals_html = ""
    if model_deals:
        deals_html = '<h2>Live deals for this model</h2><div class="dealgrid">' + "".join(deal_card(d, rowset=rs) for d in model_deals) + "</div>"
    soon = [d for d in UPCOMING_DEALS if slug in (d.get("models") or [])]
    if soon:
        deals_html += '<h2>Starting soon</h2><div class="dealgrid">' + "".join(deal_card(d, rowset=rs) for d in soon) + "</div>"
    body = f"""<p class="small"><a href="{root("/")}">Prices</a> › {e(m['name'])}</p>
<h1>{e(m['name'])} price per second ({MONTH})</h1>
<p class="lead">{e(m['maker'])}'s {e(m['name'])} on {len({r['platform'] for r in rs})} platforms, all converted to dollars per second of video. Checked {LAST}.</p>
<div class="cards"><div class="card"><h3>Cheapest today</h3><div class="big">{money(c['usd_per_second'])}<span class="small">/s</span></div>{assumption_html(c)}<div class="sub">{e(c['platform'])} · {e(spec_phrase(c))} {tag(c['status'])}</div><div class="sub">≈ {clip5} for a 5s clip</div>{deal_price_line(rs)}</div>
<div class="card"><h3>Cheapest by resolution</h3><ul class="small" style="padding-left:18px;margin:6px 0">{resl}</ul></div></div>
{summary}
{sponsor_slot("model:" + slug)}
{deals_html}
<h2>All {e(m['name'])} prices</h2>
{wide_table(THEAD.replace(' data-k="model"','').replace(' data-k=',' data-x=') + "<tbody>" + "".join(row_html(r) for r in rs) + "</tbody>")}
<p class="small">Plan rows assume you use every credit you pay for. Unused credits make the real cost per second higher. Use the <a href="{root(f"/calculator/?model={slug}")}">credit calculator for {e(m["name"])}</a> to check a plan. Deal badges use the vendor's checkout price or stated rate. An unlimited window is a break-even second count, not $0/s.</p>
{retired_table([r for r in retired_rows if r["model"] == slug], THEAD.replace(' data-k="model"','').replace(' data-k=',' data-x='))}
{faq_html(faqs)}
{news_box()}
{tick_script()}
{ld_join(faq_ld(slug, faqs), breadcrumb_ld([("Prices", "/"), (m["name"], f"/models/{slug}/")]))}"""
    page(f"/models/{slug}/", page_title(f"{m['name']} Price Per Second"),
         f"{m['name']} costs from {money(c['usd_per_second'])}/s ({c['platform']}, {spec_phrase(c)}). Compare {len(rs)} sourced prices across APIs and credit plans.", body)

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
            f'<td class="num"><span class="amt">{per_sec}</span></td></tr>'
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
<p class="small">"~" = the platform gives an approximate credit cost. Using fewer of your credits raises the real cost of each clip.</p></div></div>
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
 function assumptionOf(r){{if(r.kind==='plan')return r.status==='estimate'?'Estimate: assumes every credit you pay for is used':'Assumes every credit you pay for is used';if(r.status==='estimate'){{const note=String(r.note||'').trim();return note?'Estimate: '+note:'Estimate: the vendor marks this rate as approximate'}}return ''}}
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
   return `<tr><td><a href="${{BASE}}/models/${{r.model}}/">${{esc(r.variant)}}</a>${{fn}}<div class="meta">Input: ${{esc(inputOf(r))}}</div><div class="meta">Length: ${{esc(lengthOf(r))}}</div>${{also?'<div class="meta also">Also: '+esc(also)+'</div>':''}}${{dealNote}}${{mark}}</td><td>${{lab('Plan tier',esc(tierOf(r)))}}</td><td>${{lab('Resolution',esc(resOf(r)))}}</td><td>${{lab('Audio',esc(audioOf(r)))}}</td><td class="num">${{lab('Clip',r.clip_seconds+'s')}}</td><td>${{lab('Credits/clip',cred)}}</td><td class="num">${{lab('Clips',clips.toLocaleString())}}</td><td class="num">${{lab('$/clip',priceCell)}}</td><td class="num"><span class="amt">${{perSec}}</span></td></tr>`}}).join('');
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
# TODO: the signup page and nav link come back when NEWSLETTER_ENABLED is True.
if NEWSLETTER_ENABLED:
    page("/newsletter/", f"{BRAND} Weekly: AI video price drops & new models", "One short email a week: AI video price changes, new models and the cheapest way to run them.",
         f"""<h1>{BRAND} Weekly</h1><p class="lead">One short email every Monday: which AI video prices changed, which new models launched, and the cheapest way to run each one right now. Written from the same data as this site.</p>{news_box()}""", "/newsletter/")
else:
    page("/newsletter/", f"Newsletter coming soon | {BRAND}",
         "The VidFare newsletter is not open yet.",
         f"""<h1>Newsletter coming soon</h1>
<p>The weekly email is not open yet.</p>
<p><a href="{root("/")}">Home</a> · <a href="{root("/deals/")}">Deals</a> · <a href="{root("/changes/")}">Price changes</a></p>""",
         robots="noindex")

# ---------- About ----------
srcl = "".join(f'<li><a href="{e(outbound(s["url"])[0])}" rel="{outbound(s["url"])[1]}" target="_blank">{e(s["name"])}</a>{" (checked by hand)" if s["fetch"]=="manual" else ""}</li>' for s in sources.values())
unv = "".join(f'<li>{e(u["item"])}: <span class="small">{e(u["reason"])}</span></li>' for u in db["unverified"])
about_ld = {
    "@context": "https://schema.org",
    "@type": "AboutPage",
    "url": SITE_URL + "/about/",
    "author": {"@type": "Person", "name": "Emmanuel Gonzalez"},
}
page("/about/", f"About {BRAND}: methodology & affiliate disclosure", f"How {BRAND} collects and normalizes AI video prices, and how the site is funded.",
     f"""<h1>About {BRAND}</h1>
<p class="lead">{BRAND} tracks what AI video generation actually costs, per second of finished video, across every place you can run a model. {e(TAGLINE)}</p>
<p>Made by Emmanuel Gonzalez.</p>
<h2>How the numbers work</h2>
<ul><li>Every price comes from the vendor's own pricing or model page, saved with a source link and the date we checked it.</li>
<li><b>APIs</b>: we use the vendor's stated $ per second. Runway credits are $0.01 each.</li>
<li><b>Credit plans</b>: plan price ÷ credits = $ per credit; × credits per clip ÷ clip length = $ per second. That assumes you use all your credits.</li>
<li>If a vendor says "~", "roughly" or "estimated", we label the row <i>approx.</i> If we can't confirm a price, we leave it out rather than guess.</li>
<li><b>Audio, input, and length</b> are copied from the vendor page. Audio is with audio, without audio, or not stated. Input is text-to-video, image-to-video, reference, video-to-video, extend, or lip-sync when that mode is named for the price. Length is the clip the credit price is for, a stated min and max, or a per-second rate the page ties to a length. If the page does not say it, the field stays not stated. A value is not inferred from a nearby sentence or from another row. A different stated price becomes its own row.</li>
<li>When a vendor shuts an endpoint down, that row is marked <i>discontinued</i> and kept under Discontinued with the last recorded rate. It is not used for cheapest picks.</li>
<li>Prices exclude VAT/sales tax and change often. Always confirm on the vendor's page before paying.</li>
<li><b>Deals</b> are a separate list. A discounted $/s uses the vendor's stated rate or the checkout plan price ÷ credits. A code that lasts the first N months also shows a 12-month blended rate. Unlimited windows show how many seconds of video cover the plan price. They are not listed at $0/s.</li></ul>
<h2>Sources we check</h2><ul class="small">{srcl}</ul>
<h2>Not included yet (unconfirmed)</h2><ul class="small">{unv}</ul>
<h2 id="disclosure">Affiliate disclosure</h2>
<div class="disclose">Some links on {BRAND} are affiliate links. If you sign up through them we may earn a commission, at no extra cost to you. Affiliate status never changes the order of the tables: rows are always sorted by price. Sponsored placements are labelled "Sponsor" and never affect the price order.</div>
<p class="small">Contact: TODO-add-contact-email</p>""", "/about/", ld_script(about_ld))

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
<p>Launch weeks are the usual pattern: a new video model is unlimited on credit plans and 30–75% off on APIs for one to four weeks. The holiday window, about Nov 20 through Jan 8, is the long one. In 2025 Higgsfield posted several waves, Magnific used a 50% code, and Krea posted 40% off yearly plans. End dates move. They get extended, reopened, or left as "limited time." If a page does not name an end date, this site does not invent one. <a href="{root("/deals/black-friday/")}">Black Friday 2026 stub, with 2025 dates</a>.</p>
<h2>Past deals</h2>
<div class="dealgrid" id="archive">{archive_html}</div>
<p class="small"><a href="{root("/deals.xml")}">Deals RSS</a> · <a href="{root("/deals.json")}">deals.json</a></p>
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
bf_body = f"""<p class="small"><a href="{root("/deals/")}">Deals</a> › Black Friday</p>
<h1>AI video Black Friday and holiday deals</h1>
<p class="lead">A stub for the 2026 holiday season, about Nov 20 through Jan 8. This page will be updated when 2026 offers are on the vendors' own sites. Nothing below is a live 2026 price.</p>
<div class="callout"><b>2025 history.</b> Every example on this page is a past sale. The year is 2025 (one Higgsfield wave ran through Jan 7, 2026). Dates and percents are from the vendors' official X accounts. They are not current codes.</div>
<div class="dealgrid">{"".join(deal_card(d, archive=True) for d in hist_sorted)}</div>
<h2>What 2025 looked like</h2>
<ul>
<li>Higgsfield posted a new "final call" every few days from Dec 3, 2025: 70% off, then 67% off, 80% off for three days, and 85% off from Dec 29 to Jan 7.</li>
<li>Magnific's Black Friday was 50% off every plan, including yearly, with code BFMAGNIFIC, Nov 24–28 2025.</li>
<li>Krea posted 40% off yearly plans on Nov 28 (Black Friday, "today only"), Dec 1 (Cyber Monday), and Dec 24 (up to 40% off Pro and Max).</li>
</ul>
<p class="small">Those codes and percents are expired. Check the <a href="{root("/deals/")}">live deals</a> page before you pay.</p>
<div class="disclose">Higgsfield links elsewhere on {BRAND} can be affiliate links. The posts linked on this page are the vendors' own X accounts. <a class="tap" href="{root("/about/#disclosure")}">Disclosure</a>.</div>
"""
page("/deals/black-friday/", page_title("AI Video Black Friday Deals"),
     "A stub for 2026 AI video holiday sales, plus dated 2025 examples from Higgsfield, Krea, and Magnific.",
     bf_body, "/deals/",
     extra_head=ld_script(breadcrumb_ld([("Deals", "/deals/"), ("Black Friday", "/deals/black-friday/")])))

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
AD_MAIL = "mailto:emmanueldevgonzalez@gmail.com?subject=" + quote("VidFare sponsorship")
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
<p>Rates on request. Email <a href="{e(AD_MAIL)}">emmanueldevgonzalez@gmail.com</a>.</p>"""
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
        f"- [Use VidFare with AI]({SITE_URL}/mcp/): the live read-only MCP server at https://mcp.vidfare.com/mcp for ChatGPT, Claude, and Cursor. It reads prices.json and deals.json and does not invent a price.",
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
<p><a href="{root("/data/prices.json")}">https://vidfare.com/data/prices.json</a></p>
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
<p>The same files can be queried through the live read-only MCP server at <a href="https://mcp.vidfare.com/mcp"><code>https://mcp.vidfare.com/mcp</code></a>. How to add it to ChatGPT, Claude, and Cursor is on <a href="{root("/mcp/")}">Use VidFare with AI</a>. It reads this file and <a href="{root("/deals.json")}">deals.json</a>. It does not replace either file, and it does not invent a price.</p>
"""
page("/data/", page_title("Price data for developers"),
     f"How to read the public {BRAND} price file, share a calculator link, and credit the data.",
     data_body, "/data/", ld_script(data_ld))

mcp_models = ", ".join(e(m["name"]) for m in models.values())
mcp_cursor = (
    '{\n  "mcpServers": {\n    "vidfare": {\n'
    '      "url": "https://mcp.vidfare.com/mcp"\n    }\n  }\n}'
)
mcp_ld = {
    "@context": "https://schema.org",
    "@type": "WebPage",
    "name": "Use VidFare with AI",
    "url": SITE_URL + "/mcp/",
    "description": f"How to query {BRAND} prices from ChatGPT, Claude, and Cursor.",
    "isPartOf": {"@type": "WebSite", "name": BRAND, "url": SITE_URL + "/"},
}
mcp_body = f"""<h1>Use VidFare with AI</h1>
<p class="lead">A public, read-only server so ChatGPT, Claude, and Cursor can look up {BRAND} prices and cite vidfare.com.</p>
<div class="callout"><b>Live.</b> Connect a client to <code>https://mcp.vidfare.com/mcp</code>. The server is public and read-only. No key and no sign-in.</div>
<p>It reads <a href="{root("/data/prices.json")}">prices.json</a> and <a href="{root("/deals.json")}">deals.json</a>. It does not scrape vendor sites, and it does not invent a price when those files do not state one. Answers include the source, the date last checked, and a link back to {BRAND}.</p>
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
<h2>ChatGPT</h2>
<ol>
<li>If you do not see a way to add a server, open Settings, then Apps or Security, and turn on Developer mode.</li>
<li>On the web, open Settings, then Apps, and create an app. In the desktop app, open Settings, then Plugins, then MCPs, and choose Add MCP server.</li>
<li>Name it VidFare. If it asks for a transport, choose Streamable HTTP.</li>
<li>Paste <code>https://mcp.vidfare.com/mcp</code>.</li>
<li>Leave the token, headers, and OAuth client empty. Save, then ask for a VidFare price.</li>
</ol>
<h2>Claude</h2>
<ol>
<li>Open Settings, then Connectors. On claude.ai that is Customize, then Connectors.</li>
<li>Choose Add custom connector.</li>
<li>Name it VidFare and paste <code>https://mcp.vidfare.com/mcp</code>.</li>
<li>Leave the OAuth client id and secret blank, then add it. If a sign-in window opens, close it. This server has no account.</li>
<li>Allow the tools. They only read public prices.</li>
</ol>
<h2>Cursor</h2>
<p>For one project, save this as <code>.cursor/mcp.json</code>. For every project, save it as <code>~/.cursor/mcp.json</code>. The same JSON also works as <code>.mcp.json</code>.</p>
<p><code style="white-space:pre-wrap">{e(mcp_cursor)}</code></p>
<p class="small">The copy in the repository is <code>mcp-server/.mcp.json</code>. Save the file. Cursor lists VidFare under Settings, then MCP. There is no API key.</p>
<h2>The price file is still here</h2>
<p>Scripts that fetch JSON can keep using <a href="{root("/data/")}">the data page</a>. The assistant server is another way to read the same catalog.</p>
"""
page("/mcp/", page_title("Use VidFare with AI"),
     f"How to connect ChatGPT, Claude, and Cursor to the live {BRAND} price server.",
     mcp_body, "", ld_script(mcp_ld))

urls = ["/", "/deals/", "/deals/black-friday/", "/calculator/", "/data/", "/mcp/"]
urls += [path for path, _label in GUIDE_LINKS]
if NEWSLETTER_ENABLED:
    urls.append("/newsletter/")
urls += ["/changes/", "/about/", "/advertise/"]
if report_paths:
    urls.extend(report_paths)
urls += ["/models/"] + [f"/models/{s}/" for s in models]
open(os.path.join(DIST, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    "".join(f"  <url><loc>{SITE_URL}{u}</loc><lastmod>{LAST}</lastmod></url>\n" for u in urls) + "</urlset>\n")
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
        raise SystemExit("empty sponsor slot should link to the advertise page")
    if "sponsored" in empty:
        raise SystemExit("the house placeholder is not an outbound sponsor link")
    blank = render_sponsor("home", {"name": " ", "url": "https://example.com", "tagline": "", "active": True})
    if HOUSE_LINE not in blank:
        raise SystemExit("an active slot with an empty name is treated as empty")
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
            return ["home"]
        if rel == "deals/index.html":
            return ["deals"]
        prefix = "models/"
        if rel.startswith(prefix) and rel.endswith("/index.html"):
            rest = rel[len(prefix):-len("index.html")].strip("/")
            if rest and "/" not in rest:
                return ["model:" + rest]
        return []

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
        if AD_MAIL not in ad or "emmanueldevgonzalez@gmail.com" not in ad:
            errors.append("advertise page mailto")
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
    sitemap = open(os.path.join(DIST, "sitemap.xml"), encoding="utf-8").read()
    if f"<loc>{SITE_URL}/data/</loc>" not in sitemap:
        errors.append("sitemap is missing /data/")
    if f"<loc>{SITE_URL}/mcp/</loc>" not in sitemap:
        errors.append("sitemap is missing /mcp/")
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
        if "<h1>Use VidFare with AI</h1>" not in mcp_html:
            errors.append("mcp page h1")
        for tool in ("list_models", "get_model_prices", "estimate_cost", "cheapest_options", "list_deals"):
            if f"<code>{tool}</code>" not in mcp_html:
                errors.append(f"mcp page is missing {tool}")
    data_html = open(os.path.join(DIST, "data", "index.html"), encoding="utf-8").read()
    if f'href="{root("/mcp/")}"' not in data_html:
        errors.append("data page does not link to /mcp/")
    if "https://mcp.vidfare.com/mcp" not in data_html:
        errors.append("data page is missing the live MCP endpoint")
    if "coming soon" in data_html.lower():
        errors.append("data page still says the MCP server is coming soon")
    auth_file = os.path.join(DIST, ".well-known", "mcp-registry-auth")
    auth_body = open(auth_file, encoding="utf-8").read() if os.path.isfile(auth_file) else ""
    if "PLACEHOLDER_REPLACE_AT_PUBLISH" not in auth_body or not auth_body.startswith("v=MCPv1;"):
        errors.append("site output is missing the mcp-registry-auth placeholder")
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
    home_nav = home_html.split("<nav>", 1)[-1].split("</nav>", 1)[0]
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
    estimate_line = "Estimate: " + CREDIT_USE
    for rel in ("index.html", "models/kling-3-0/index.html"):
        page_html = open(os.path.join(DIST, rel), encoding="utf-8").read()
        if estimate_line not in page_html:
            errors.append(f"{rel} is missing the credit-plan estimate assumption")
        pro_rows = [part.split("</tr>", 1)[0] for part in page_html.split("<tr>") if "Pro, audio off" in part]
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
