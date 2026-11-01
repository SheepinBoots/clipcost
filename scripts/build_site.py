#!/usr/bin/env python3
"""Build the static VidFare site from data/*.json into dist/."""
import json, os, shutil, html, datetime, sys, email.utils, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deals as dealmod
import weekly_report
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlparse, urlsplit, urlunsplit, parse_qsl, urlencode, quote
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
SITE_URL = "https://sheepinboots.github.io/clipcost"
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
# GitHub project Pages serves this site under the path in SITE_URL ("" for a bare domain).
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
    """Absolute site path, including the GitHub Pages project prefix."""
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

def page(path, title, desc, body, active="", extra_head="", dest=None, reports_nav=None, robots="index,follow", canonical=True, before_count=""):
    canon = SITE_URL + path
    show_reports = REPORTS_ENABLED if reports_nav is None else reports_nav
    navs = [("/", "Prices"), ("/deals/", "Deals"), ("/calculator/", "Credit calculator"), ("/guides/", "Guides"), ("/changes/", "Price changes")]
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
<link rel="stylesheet" href="{root("/style.css")}">{extra_head}</head><body>
<header class="top"><div class="wrap"><a class="logo" href="{root("/")}">Vid<span>Fare</span></a><nav>{nav}</nav></div></header>
<main class="wrap">{body}</main>
<footer><div class="wrap"><p><b>Models:</b> {modlinks}</p>
<p><b>Guides:</b> {guidelinks}</p>
<p>Prices are copied from each vendor's own pricing page, with the date we checked. Always confirm on the vendor's page before you buy. Some links are affiliate links (<a href="{root("/about/#disclosure")}">disclosure</a>).</p>
<p>© {today.year} {BRAND} · Data last checked {LAST} · <a href="{root("/advertise/")}">Advertise</a></p></div></footer>
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
             ld_script(weekly_report.report_jsonld(report, SITE_URL + path)),
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
    """on / off / not listed. False in the data is the vendor's audio-off rate."""
    if r.get("audio") is True:
        return "on"
    if r.get("audio") is False:
        return "off"
    return "not listed"

def audio_phrase(r):
    word = shown_audio(r)
    if word == "not listed":
        return "not listed"
    return "audio " + word

def spec_phrase(r):
    aud = shown_audio(r)
    aud_bit = "audio not listed" if aud == "not listed" else f"audio {aud}"
    tier = shown_tier(r)
    # "Pro tier" already ends in tier. Prefixing it reads as "plan tier Pro tier".
    tier_bit = tier if tier.lower().endswith("tier") else f"plan tier {tier}"
    return f"{tier_bit}, resolution {shown_resolution(r)}, {aud_bit}"

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
            f'<td>{e(r["variant"])}</td><td>{e(shown_tier(r))}</td><td>{e(shown_resolution(r))}</td><td>{e(audio_phrase(r))}</td>'
            f'<td class="num">{show(r["usd_per_second"])}{assumption_html(r)}</td>'
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

def retired_table(rs, thead=None):
    """Record of rates that are off sale. Not used for cheapest picks."""
    if not rs: return ""
    head = thead or THEAD
    body = "".join(row_html(r) for r in sorted(rs, key=lambda r: (r["model"], r["usd_per_second"])))
    return (f'<h2>Discontinued</h2>'
            f'<p class="small">These rates are off sale. The last price we recorded stays here, and these rows are left out of cheapest picks and the live table.</p>'
            f'<div class="tblwrap"><table id="retired">{head}<tbody>{body}</tbody></table></div>')

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

def guide_page(path, title, desc, body, faqs):
    raw = json.dumps(faqs, ensure_ascii=False).lower()
    for bad in ("subscribe", "newsletter", "buttondown"):
        if bad in raw:
            raise SystemExit(f"{path} FAQ text contains {bad}")
    page(path, title, desc, body, "/guides/", ld_script(guide_faq_ld(path, faqs)))

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
<label class="chk"><input type="checkbox" id="fPromo"> hide promos</label>
<label class="chk"><input type="checkbox" id="fEst"> hide approximations</label>
<span class="small" id="count"></span></div>
<div class="tblwrap"><table id="prices">{THEAD}<tbody>{"".join(row_html(r) for r in sorted(rows, key=lambda r: r["usd_per_second"]))}</tbody></table></div>
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
function audioOf(r){{if(r.audio===true)return 'audio on';if(r.audio===false)return 'audio off';return 'not listed'}}
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
  return `<tr><td><a href="${{BASE}}/models/${{r.model}}/">${{esc(MODELS[r.model])}}</a></td><td>${{plat(r)}}</td><td>${{esc(r.variant)}}</td><td>${{esc(tierOf(r))}}</td><td>${{esc(resOf(r))}}</td><td>${{esc(audioOf(r))}}</td><td class="num">${{money(r.usd_per_second)}}${{assumeHtml}}</td><td>${{tag(r.status)}}${{promo}}${{badges}}${{disc}}</td><td class="math">${{extra}}</td><td class="small"><a href="${{esc(srcHref)}}" rel="${{srcRel}}" target="_blank">source</a><br>${{r.checked}}</td></tr>`}}).join('');
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
    note = f'<p class="small">{e(deal["notes"])}</p>' if deal.get("notes") else ""
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
<div class="tblwrap"><table>{THEAD.replace(' data-k="model"','').replace(' data-k=',' data-x=')}<tbody>{"".join(row_html(r) for r in rs)}</tbody></table></div>
<p class="small">Plan rows assume you use every credit you pay for. Unused credits make the real cost per second higher. Use the <a href="{root("/calculator/")}">credit calculator</a> to check a plan. Deal badges use the vendor's checkout price or stated rate. An unlimited window is a break-even second count, not $0/s.</p>
{retired_table([r for r in retired_rows if r["model"] == slug], THEAD.replace(' data-k="model"','').replace(' data-k=',' data-x='))}
{faq_html(faqs)}
{news_box()}
{tick_script()}
{ld_script(faq_ld(slug, faqs))}"""
    page(f"/models/{slug}/", f"{m['name']} price per second ({MONTH}): cheapest way to run it | {BRAND}",
         f"{m['name']} costs from {money(c['usd_per_second'])}/s ({c['platform']}, {spec_phrase(c)}). Compare {len(rs)} sourced prices across APIs and credit plans.", body)

model_items = "".join(
    f'<li><a href="{root(f"/models/{slug}/")}">{e(m["name"])}</a></li>'
    for slug, m in models.items()
)
page("/models/", f"AI video models | {BRAND}",
     f"Every AI video model {BRAND} prices, with a page of sourced cost-per-second comparisons.",
     f'<h1>Models</h1><p class="lead">Every model {BRAND} tracks, with sourced prices per second of video.</p><ul class="model-index">{model_items}</ul>')

# ---------- Calculator ----------
plan_opts = ""
for plat in sorted({p["platform"] for p in plans.values()}):
    plan_opts += f'<optgroup label="{e(plat)}">' + "".join(f'<option value="{k}">{e(p["plan"])}: ${p["usd_month"]:g}/mo</option>' for k, p in plans.items() if p["platform"] == plat) + "</optgroup>"
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
calc = f"""<h1>AI video credit calculator</h1>
<p class="lead">{calc_lead}</p>
<p>Pricing a finished video from dollars per second? Use the <a href="{root("/guides/ai-video-project-budget/")}">project budget calculator</a>.</p>
<div class="calc"><div class="card">
<label class="small" for="plan">Plan</label><br><select id="plan" style="width:100%;margin:6px 0 12px">{plan_opts}</select>
<label class="small" for="used">% of credits you actually use</label><br><input id="used" type="number" value="100" style="width:100px" aria-describedby="usedMsg"> %
<p class="small" id="usedMsg" role="status"></p>
<label class="chk" style="margin-top:8px"><input type="checkbox" id="applyDeals"> apply today's deals</label>
<div id="dealBox" hidden>
<label class="small" for="windowSecs">Seconds you'll make during an unlimited window</label><br>
<input id="windowSecs" type="number" min="1" value="60" style="width:100px">
<p class="small" id="dealEff"></p>
</div>
<div style="margin-top:14px"><div class="small">Plan price</div><div class="kpi" id="kPrice"></div>
<div class="small" style="margin-top:8px">Credits per month</div><div class="kpi" id="kCred"></div>
<div class="small" style="margin-top:8px">Cost per credit</div><div class="kpi" id="kPer"></div></div>
<p class="small" id="pNote"></p><p id="pLink"></p></div>
<div><div class="tblwrap"><table id="ct"><thead><tr><th>Model</th><th>Plan tier</th><th>Resolution</th><th>Audio</th><th>Clip</th><th>Credits/clip</th><th>Clips / month</th><th>$ / clip</th><th>$ / sec</th></tr></thead><tbody></tbody></table></div>
<p class="small">"~" = the platform gives an approximate credit cost. Using fewer of your credits raises the real cost of each clip.</p></div></div>
<script>
const BASE={json.dumps(BASE)};const AFF={json.dumps(AFF)};const MODELS={json.dumps({k:v["name"] for k,v in models.items()})};
const DEALMAP={json.dumps(CALC_DEALS)};
fetch(BASE+'/data/prices.json').then(r=>r.json()).then(d=>{{
 const $=id=>document.getElementById(id);
 const esc=s=>String(s??'').replace(/[&<>]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[c]));
 const pk=new URLSearchParams(location.search).get('plan');if(pk&&d.plans[pk])$('plan').value=pk;
 function hf(url){{try{{const u=new URL(url);const h=u.hostname;if(h!=='higgsfield.ai'&&!h.endsWith('.higgsfield.ai'))return null;if(h==='higgsfield.ai'&&(u.pathname===''||u.pathname==='/'))return {json.dumps(HF_BASE)};u.searchParams.delete('ref');u.searchParams.set('fpr',{json.dumps(HF_FPR)});return u.toString()}}catch(e){{return null}}}}
 function money(v){{const n=Math.round(Number(v)*100000);const neg=n<0,a=Math.abs(n),whole=Math.floor(a/100000);let digits=String(a%100000).padStart(5,'0').replace(/0+$/,'');if(digits.length<2)digits=String(a%100000).padStart(5,'0').slice(0,2);return (neg?'-':'')+'$'+whole+'.'+digits}}
 function tierOf(r){{const name=String(r.plan_name||'').trim();if(name)return name;const res=String(r.resolution||'').trim();if(res==='Pro tier'||res==='Pro'||res==='Standard')return res;return 'not listed'}}
 function resOf(r){{const res=String(r.resolution||'').trim();if(!res||res==='—'||res==='-'||res==='–'||res==='Pro tier'||res==='Pro'||res==='Standard')return 'not listed';return res}}
 function audioOf(r){{if(r.audio===true)return 'audio on';if(r.audio===false)return 'audio off';return 'not listed'}}
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
 function go(){{const k=$('plan').value,p=d.plans[k],u=readUsed();
  const map=$('applyDeals').checked?DEALMAP[k]:null;
  const price=map&&map.price!=null?map.price:p.usd_month;
  const credits=p.credits_month+(map&&map.bonus_credits?map.bonus_credits:0);
  const per=price/credits;
  const scale=(price/p.usd_month)*(p.credits_month/credits);
  $('kPrice').textContent='$'+price+'/mo';$('kCred').textContent=credits.toLocaleString();$('kPer').textContent='$'+per.toFixed(5);
  let note=(p.credits_note||'')+' Billing: '+p.billing+'. Checked '+p.checked+'.';
  if(map&&map.notes&&map.notes.length) note+=' '+map.notes.join(' ');
  $('pNote').textContent=note;
  const hasUn=!!(map&&map.unlimited&&map.unlimited.length);
  $('dealBox').hidden=!hasUn;
  const tracked=hf(p.source_url),href=tracked||AFF[p.platform]||p.source_url,rel=(tracked||AFF[p.platform])?'sponsored nofollow noopener':'nofollow noopener';
  const srcRel=tracked?'sponsored nofollow noopener':'nofollow noopener';
  $('pLink').innerHTML=`<a class="btn" href="${{esc(href)}}" rel="${{rel}}" target="_blank">See ${{esc(p.platform)}} plans</a> <a class="small" href="${{esc(tracked||p.source_url)}}" rel="${{srcRel}}" target="_blank">source</a>`;
  if(u==null){{$('ct').querySelector('tbody').innerHTML='<tr><td colspan="9">Enter a whole number from 1 to 100.</td></tr>';return}}
  const secs=Math.max(1, Number($('windowSecs').value)||1);
  const rs=d.rows.filter(r=>r.plan==k&&current(r)).sort((a,b)=>a.usd_per_second-b.usd_per_second);
  $('ct').querySelector('tbody').innerHTML=rs.map(r=>{{const clips=clipCount(credits*u,r.credits_per_clip);const pc=(r.usd_per_clip*scale)/u;
   const priceCell=clips>0?money(pc):'—', perSec=clips>0?money(pc/r.clip_seconds):'—';
   let extra='';
   const hit=unlimitedHit(map, r);
   if(hit&&r.usd_per_second>0){{
     const normal=r.usd_per_second*scale;
     const be=Math.round(price/normal);
     extra=`<div class="small">Unlimited: worth it after ${{be}}s. At ${{secs}}s in the window, ${{money(price/secs)}}/s effective.</div>`;
   }}
   if(map&&map.blended_price!=null&&clips>0){{
     const bscale=(map.blended_price/p.usd_month)*(p.credits_month/credits);
     extra+=`<div class="small">12-month blended ${{money((r.usd_per_clip*bscale)/u/r.clip_seconds)}}/s</div>`;
   }}
   const assume=assumptionOf(r);
   const assumeHtml=assume?`<div class="assume">${{esc(assume)}}</div>`:'';
   return `<tr><td><a href="${{BASE}}/models/${{r.model}}/">${{esc(r.variant)}}</a></td><td>${{esc(tierOf(r))}}</td><td>${{esc(resOf(r))}}</td><td>${{esc(audioOf(r))}}</td><td>${{r.clip_seconds}}s</td><td>${{r.status=='estimate'?'~':''}}${{(+r.credits_per_clip).toFixed(r.credits_per_clip%1?2:0)}}</td><td class="num">${{clips.toLocaleString()}}</td><td class="num">${{priceCell}}</td><td class="num">${{perSec}}${{extra}}${{assumeHtml}}</td></tr>`}}).join('');
  if(hasUn) $('dealEff').textContent='Effective $/s for an unlimited window is the plan price divided by the seconds you make. It is not $0.';
  history.replaceState(null,'','?plan='+k);}}
 $('plan').addEventListener('input',go);$('used').addEventListener('input',go);
 $('applyDeals').addEventListener('input',go);$('windowSecs').addEventListener('input',go);go();}});
</script>{news_box()}"""
page("/calculator/", f"AI Video Credit Calculator ({MONTH}): Higgsfield, Krea, Magnific | {BRAND}",
     "How many Wan 3.0, Kling 3.0, Veo 3.1 or Seedance 2.5 clips does your Higgsfield, Krea or Magnific plan buy? Cost per clip and per second.", calc, "/calculator/", ld_script(calc_ld))

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
    items += f'<li><span class="pill">{c["date"]}</span> <span class="pill">{e(c.get("type","")).upper()}</span> {txt}{src}</li>'
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
<div class="disclose"><b>Disclosure.</b> Higgsfield links on this page are affiliate links (parameter <code>fpr=emmanuel-bbfe0e</code>) and use <code>rel="sponsored nofollow"</code>. If you sign up through them, {BRAND} may earn a commission, at no extra cost to you. Links to Krea, Magnific, Runway, fal, and other vendors are the official URLs, with no affiliate tag. Deals are listed only when the vendor's own page or official account is the source. Order is the end date, not who pays us. See the <a href="{root("/about/#disclosure")}">full disclosure</a>.</div>
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
        offer = {
            "@type": "Offer",
            "name": deal.get("title") or deal["id"],
            "url": f"{SITE_URL}/deals/#{deal['id']}",
            "description": " · ".join(bit for bit in bits if bit),
            "seller": {"@type": "Organization", "name": deal.get("vendor") or ""},
        }
        if deal.get("end"):
            offer["priceValidUntil"] = deal["end"]
        elements.append({
            "@type": "ListItem",
            "position": i,
            "name": deal.get("title") or deal["id"],
            "url": f"{SITE_URL}/deals/#{deal['id']}",
            "item": offer,
        })
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Live AI video deals",
        "numberOfItems": len(elements),
        "itemListElement": elements,
    }

page("/deals/", f"AI video deals ({MONTH}): Higgsfield, Krea, fal, Runway, Magnific | {BRAND}",
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
<div class="disclose">Higgsfield links elsewhere on {BRAND} can be affiliate links. The posts linked on this page are the vendors' own X accounts. <a href="{root("/about/#disclosure")}">Disclosure</a>.</div>
"""
page("/deals/black-friday/", f"AI video Black Friday 2026 (stub) and 2025 holiday deals | {BRAND}",
     "A stub for 2026 AI video holiday sales, plus dated 2025 examples from Higgsfield, Krea, and Magnific.",
     bf_body, "/deals/")

def write_feeds():
    def slim(deal, status):
        row = {
            "id": deal["id"], "vendor": deal.get("vendor"), "type": deal.get("type"),
            "title": deal.get("title"), "models": deal.get("models") or [], "plans": deal.get("plans") or [],
            "conditions": dealmod.conditions(deal), "percent": deal.get("percent"),
            "bonus_credits": deal.get("bonus_credits"), "price_before": deal.get("price_before"),
            "price_after": deal.get("price_after"), "price_pairs": deal.get("price_pairs"),
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
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<rss version=\"2.0\">\n<channel>\n"
        f"  <title>{BRAND} deals</title>\n"
        f"  <link>{SITE_URL}/deals/</link>\n"
        "  <description>Live AI video deals from vendor pages and official accounts.</description>\n"
        f"  <lastBuildDate>{built}</lastBuildDate>\n"
        + "\n".join(items) + "\n</channel>\n</rss>\n"
    )
    open(os.path.join(DIST, "deals.xml"), "w").write(rss)

write_feeds()

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
    """Send /clipcost/newsletter* (except the coming-soon URL itself) to /newsletter/."""
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
        f"- [prices.json]({SITE_URL}/data/prices.json): the price catalog this page is built from.",
        f"- [deals.json]({SITE_URL}/deals.json): the live and archived deals.",
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
urls = ["/", "/deals/", "/deals/black-friday/", "/calculator/"]
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
    if "Pro tier, resolution not listed, audio off" not in fal_line or "plan tier Pro tier" in fal_line:
        errors.append("llms.txt Kling fal line does not read as Pro tier with audio off")
    if "plan tier Standard" not in llms:
        errors.append("llms.txt dropped the plan tier prefix for a name that does not end in tier")
    estimate_line = "Estimate: " + CREDIT_USE
    for rel in ("index.html", "models/kling-3-0/index.html"):
        page_html = open(os.path.join(DIST, rel), encoding="utf-8").read()
        if estimate_line not in page_html:
            errors.append(f"{rel} is missing the credit-plan estimate assumption")
        pro_rows = [part.split("</tr>", 1)[0] for part in page_html.split("<tr>") if "Pro, audio off" in part]
        if not pro_rows or ">Pro tier<" not in pro_rows[0] or ">audio off<" not in pro_rows[0] or ">not listed<" not in pro_rows[0]:
            errors.append(f"{rel} Kling Pro audio-off row is missing plan tier, resolution, or audio")
        if ">Plan tier</th>" not in page_html or ">Resolution</th>" not in page_html or ">Audio</th>" not in page_html:
            errors.append(f"{rel} price table is missing plan tier, resolution, or audio headings")
    kling_page = open(os.path.join(DIST, "models", "kling-3-0", "index.html"), encoding="utf-8").read()
    if "Pro tier, resolution not listed, audio off" not in kling_page or "plan tier Pro tier" in kling_page:
        errors.append("Kling model page comparison does not read as Pro tier with audio off")
    if "plan tier Standard, resolution not listed, audio off" not in kling_page:
        errors.append("Kling model page dropped the plan tier prefix for Standard")
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
    if errors:
        raise SystemExit("site audit failed:\n- " + "\n- ".join(errors))

audit_site()
write_report_preview()
print("built", len(urls), "pages into", DIST)
