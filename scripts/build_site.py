#!/usr/bin/env python3
"""Build the static ClipCost site from data/*.json into dist/."""
import json, os, shutil, html, datetime, sys, email.utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deals as dealmod
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlparse, urlsplit, urlunsplit, parse_qsl, urlencode
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
SITE_URL = "https://sheepinboots.github.io/clipcost"
NEWSLETTER_ACTION = "#TODO-newsletter-endpoint"  # TODO: Beehiiv/Buttondown/ConvertKit form action
# GitHub project Pages serves this site under the path in SITE_URL ("" for a bare domain).
BASE = urlparse(SITE_URL).path.rstrip("/")

def root(path):
    """Absolute site path, including the GitHub Pages project prefix."""
    if path.startswith(("http://", "https://", "mailto:", "#")):
        return path
    if not path.startswith("/"):
        path = "/" + path
    return BASE + path
db = json.load(open(os.path.join(ROOT, "data", "prices.json")))
changes = json.load(open(os.path.join(ROOT, "data", "changes.json")))
models, plans, sources = db["models"], db["plans"], db["sources"]
today = datetime.date.today()
TODAY = today.isoformat()
MONTH = today.strftime("%b %Y")
def current(r):
    """Drop expired promos and rows discontinued on or before yesterday."""
    if r.get("promo_until") and r["promo_until"] < TODAY: return False
    if r.get("discontinued_on") and r["discontinued_on"] < TODAY: return False
    return True
rows = [r for r in db["rows"] if current(r)]
LAST = db.get("last_full_check") or min(r["checked"] for r in db["rows"])
deal_doc = dealmod.load()
LIVE_DEALS = [d for d in deal_doc["deals"] if dealmod.is_current(d, TODAY)]
ARCHIVED = [d for d in deal_doc["deals"] if not dealmod.is_current(d, TODAY)]
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

def page(path, title, desc, body, active="", extra_head=""):
    canon = SITE_URL + path
    navs = [("/", "Prices"), ("/deals/", "Deals"), ("/calculator/", "Credit calculator"), ("/changes/", "Price changes"), ("/newsletter/", "Newsletter"), ("/about/", "About")]
    nav = "".join(f'<a href="{root(h)}"{" class=on" if h==active else ""}>{t}</a>' for h, t in navs)
    modlinks = " · ".join(f'<a href="{root(f"/models/{s}/")}">{e(m["name"])}</a>' for s, m in models.items())
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="google-site-verification" content="nlx0gVcAU_holiR5TLbIUc0ECk-VPLUPKHiVqlGNCIM" />
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canon}"><meta name="robots" content="index,follow">
<meta property="og:type" content="website"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canon}"><meta property="og:site_name" content="ClipCost"><meta name="twitter:card" content="summary">
<meta name="theme-color" content="#0b0d12"><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%235ce1a8'/%3E%3Ctext x='16' y='22' font-size='16' text-anchor='middle' font-family='sans-serif' font-weight='800' fill='%2306281b'%3E$%3C/text%3E%3C/svg%3E">
<link rel="stylesheet" href="{root("/style.css")}">{extra_head}</head><body>
<header class="top"><div class="wrap"><a class="logo" href="{root("/")}">Clip<span>Cost</span></a><nav>{nav}</nav></div></header>
<main class="wrap">{body}</main>
<footer><div class="wrap"><p><b>Models:</b> {modlinks}</p>
<p>Prices are copied from each vendor's own pricing page, with the date we checked. Always confirm on the vendor's page before you buy. Some links are affiliate links (<a href="{root("/about/#disclosure")}">disclosure</a>).</p>
<p>© {today.year} ClipCost · Data last checked {LAST}</p></div></footer></body></html>"""
    out = os.path.join(DIST, path.strip("/"), "index.html") if path.endswith("/") else os.path.join(DIST, path.strip("/"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w").write(doc)

def tag(st): return f'<span class="tag {st}">{ {"verified":"vendor-stated","estimate":"approx.","promo":"promo"}[st] }</span>'

def ends_fallback(deal):
    cond = dealmod.conditions(deal)
    if not deal.get("end"):
        return "standing price" if cond.get("standing") else "no end date given"
    est = " (estimated)" if deal.get("end_is_estimate") else ""
    return f"until {deal['end']}{est}"

def deal_attrs(deal):
    cond = dealmod.conditions(deal)
    return (f'data-deal-end="{e(deal.get("end") or "")}" data-deal-est="{1 if deal.get("end_is_estimate") else 0}" '
            f'data-deal-standing="{1 if cond.get("standing") else 0}"')

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
            f'({e(row["resolution"])}) · <span class="ends">{e(ends_fallback(deal))}</span></div>')

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
  document.querySelectorAll('[data-deal-end]').forEach(el=>{
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
}
document.addEventListener('DOMContentLoaded', clipTick);
"""

def tick_script():
    return f"<script>{TICK_JS}</script>"

def row_html(r):
    m = models[r["model"]]["name"]
    what = e(r["variant"]) + (f' · <span class="small">{e(r["plan_name"])}</span>' if r["kind"] == "plan" else "")
    aud = "" if r.get("audio") is None else (" · audio" if r["audio"] else " · no audio")
    extra = e(r["math"]) if r.get("math") else ""
    if r.get("note"): extra += (" " if extra else "") + e(r["note"])
    promo = f' <span class="small">until {r["promo_until"]}</span>' if r.get("promo_until") else ""
    disc = f' <span class="small">discontinued {e(r["discontinued_on"])}</span>' if r.get("discontinued_on") else ""
    return (f'<tr><td><a href="{root(f"/models/{r["model"]}/")}">{e(m)}</a></td><td>{plat_link(r["platform"], r["source_url"])}</td>'
            f'<td>{what}</td><td>{e(r["resolution"])}{aud}</td><td class="num">{money(r["usd_per_second"])}</td>'
            f'<td>{tag(r["status"])}{promo}{deal_badges(r)}{disc}</td><td class="math">{extra}</td>'
            f'<td class="small"><a href="{html.escape(outbound(r["source_url"])[0])}" rel="{outbound(r["source_url"])[1]}" target="_blank">source</a><br>{r["checked"]}</td></tr>')

THEAD = '<thead><tr><th data-k="model">Model</th><th data-k="platform">Where</th><th data-k="variant">Variant / plan</th><th data-k="resolution">Res.</th><th data-k="usd_per_second">$ / sec</th><th data-k="status">Status</th><th>How we got it</th><th data-k="checked">Source</th></tr></thead>'

def cheapest(rs, allow_promo=True):
    rs = [r for r in rs if allow_promo or r["status"] != "promo"]
    return min(rs, key=lambda r: r["usd_per_second"]) if rs else None

def news_box():
    return f"""<section class="news" id="newsletter"><h2 style="margin-top:0">Get the weekly price-drop email</h2>
<p class="small" style="margin:0">Every Monday: price changes, new models, and the cheapest way to run each one. Free, unsubscribe any time.</p>
<form action="{NEWSLETTER_ACTION}" method="post" onsubmit="event.preventDefault();this.querySelector('button').textContent='Thanks! (signup not connected yet)';">
<!-- TODO: point action at the newsletter provider (Beehiiv/Buttondown/ConvertKit) -->
<input type="email" name="email" required placeholder="you@email.com" aria-label="Email address"><button class="btn" type="submit">Subscribe</button></form></section>"""

shutil.rmtree(DIST, ignore_errors=True); os.makedirs(DIST)
shutil.copy(os.path.join(ROOT, "src", "style.css"), DIST)
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

# ---------- Home ----------
cards = ""
for slug, m in models.items():
    rs = [r for r in rows if r["model"] == slug]
    c = cheapest(rs); c2 = cheapest(rs, False)
    alt = ""
    if c2 and c2 is not c:
        alt = f'<div class="sub">Without promos: {money(c2["usd_per_second"])}/s on {e(c2["platform"])} {e(c2.get("plan_name") or "")} ({e(c2["resolution"])})</div>'
    cards += (f'<div class="card"><h3>{e(m["name"])}</h3><div class="big">{money(c["usd_per_second"])}<span class="small">/s</span></div>'
              f'<div class="sub">{e(c["platform"])} {e(c.get("plan_name") or "")} · {e(c["resolution"])} {tag(c["status"])}</div>{alt}'
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
<p class="lead">{len(rows)} prices for {len(models)} video models on {len(platforms)} platforms, from Higgsfield plans to the fal, Runway and Kling APIs. Everything is converted to <b>dollars per second of video</b>, and the math is shown for credit plans. Checked {LAST}.</p>
{ending_strip()}
<h2>Cheapest way to run each model today</h2><div class="cards">{cards}</div>
<p class="small">The lowest $/s for each model at any resolution, including temporary promos (labelled). Low-res tiers are usually the cheapest, so check the resolution.</p>
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
<p class="small"><span class="tag verified">vendor-stated</span> = the number is on the vendor's page (plan rows: plan price ÷ credits × credits per clip, all vendor-stated). <span class="tag estimate">approx.</span> = the vendor itself says "~", "roughly" or "estimated". <span class="tag promo">promo</span> = temporary discount with an end date. {ver} of {len(rows)} rows are vendor-stated.</p>
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
function tag(s){{return `<span class="tag ${{s}}">${{{{verified:'vendor-stated',estimate:'approx.',promo:'promo'}}[s]}}</span>`}}
function current(r){{const today=new Date().toISOString().slice(0,10);if(r.promo_until&&r.promo_until<today)return false;if(r.discontinued_on&&r.discontinued_on<today)return false;return true}}
function hf(url){{try{{const u=new URL(url);const h=u.hostname;if(h!=='higgsfield.ai'&&!h.endsWith('.higgsfield.ai'))return null;if(h==='higgsfield.ai'&&(u.pathname===''||u.pathname==='/'))return {json.dumps(HF_BASE)};u.searchParams.delete('ref');u.searchParams.set('fpr',{json.dumps(HF_FPR)});return u.toString()}}catch(e){{return null}}}}
function plat(r){{const tracked=hf(r.source_url);if(tracked)return `<a href="${{esc(tracked)}}" rel="sponsored nofollow noopener" target="_blank">${{esc(r.platform)}}</a>`;const a=AFF[r.platform];return a?`<a href="${{esc(a)}}" rel="sponsored nofollow noopener" target="_blank" data-affiliate="TODO">${{esc(r.platform)}}</a>`:`<a href="${{esc(r.source_url)}}" rel="nofollow noopener" target="_blank">${{esc(r.platform)}}</a>`}}
function render(){{
 const fm=$('fModel').value,fp=$('fPlat').value,fk=$('fKind').value,fr=$('fRes').value.trim().toLowerCase();
 let rs=DATA.filter(r=>current(r)&&(!fm||r.model==fm)&&(!fp||r.platform==fp)&&(!fk||r.kind==fk)&&(!fr||String(r.resolution).toLowerCase().includes(fr))&&!($('fPromo').checked&&r.status=='promo')&&!($('fEst').checked&&r.status=='estimate'));
 rs.sort((a,b)=>{{let x=a[sortK],y=b[sortK];if(sortK=='model'){{x=MODELS[x];y=MODELS[y]}}return (x>y?1:x<y?-1:0)*dir}});
 document.querySelector('#prices tbody').innerHTML=rs.map(r=>{{
  const what=esc(r.variant)+(r.kind=='plan'?` · <span class="small">${{esc(r.plan_name)}}</span>`:'');
  const aud=r.audio==null?'':(r.audio?' · audio':' · no audio');
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
  return `<tr><td><a href="${{BASE}}/models/${{r.model}}/">${{esc(MODELS[r.model])}}</a></td><td>${{plat(r)}}</td><td>${{what}}</td><td>${{esc(r.resolution)}}${{aud}}</td><td class="num">${{money(r.usd_per_second)}}</td><td>${{tag(r.status)}}${{promo}}${{badges}}${{disc}}</td><td class="math">${{extra}}</td><td class="small"><a href="${{esc(srcHref)}}" rel="${{srcRel}}" target="_blank">source</a><br>${{r.checked}}</td></tr>`}}).join('');
 $('count').textContent=rs.length+' rows';
 document.querySelectorAll('#prices th').forEach(th=>{{th.classList.remove('sorted-asc','sorted-desc');if(th.dataset.k==sortK)th.classList.add(dir>0?'sorted-asc':'sorted-desc')}});
 if(window.clipTick) clipTick();
}}
['fModel','fPlat','fKind','fRes','fPromo','fEst'].forEach(id=>$(id).addEventListener('input',render));
document.querySelectorAll('#prices th[data-k]').forEach(th=>th.addEventListener('click',()=>{{const k=th.dataset.k;dir=(sortK==k)?-dir:1;sortK=k;render()}}));
</script>
{tick_script()}"""
page("/", f"AI Video Cost Per Second ({MONTH}): Wan 3.0, Kling 3.0, Veo 3.1, Seedance 2.5 | ClipCost",
     f"Compare what AI video costs per second across Higgsfield, fal, Runway, Kling, Krea, Magnific, Replicate and Atlas Cloud. {len(rows)} sourced prices, checked {LAST}.", home, "/")

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

def deal_card(deal, archive=False, rowset=None):
    href, rel = outbound(deal.get("link_url") or deal["source_url"])
    src_href, src_rel = outbound(deal["source_url"])
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
    when_html = e(when) if archive else f'<span class="ends">{e(ends_fallback(deal))}</span>'
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
        f'<a class="small" href="{e(src_href)}" rel="{src_rel}" target="_blank">source</a></p>'
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
    resl = "".join(f'<li><b>{e(k)}</b>: {money(v["usd_per_second"])}/s on {e(v["platform"])} {e(v.get("plan_name") or v["variant"])} {tag(v["status"])}</li>' for k, v in byres.items())
    api_rs = [r for r in rs if r["kind"] == "api"]; plan_rs = [r for r in rs if r["kind"] == "plan"]
    ca = cheapest(api_rs, False); cp = cheapest(plan_rs, False)
    summary = f"<p>The cheapest price we found today is <b>{money(c['usd_per_second'])} per second</b> on <b>{e(c['platform'])}</b> ({e(c.get('plan_name') or c['variant'])}, {e(c['resolution'])})"
    summary += f", a promo that ends {c['promo_until']}." if c["status"] == "promo" else "."
    if c2 is not c: summary += f" Without promos, the cheapest is {money(c2['usd_per_second'])}/s on {e(c2['platform'])} ({e(c2.get('plan_name') or c2['variant'])}, {e(c2['resolution'])})."
    summary += "</p>"
    if ca: summary += f"<p>Cheapest pay-as-you-go API: {money(ca['usd_per_second'])}/s on {e(ca['platform'])} ({e(ca['variant'])}, {e(ca['resolution'])}). "
    if cp: summary += f"Cheapest subscription: {money(cp['usd_per_second'])}/s on {e(cp['platform'])} {e(cp['plan_name'])} ({e(cp['resolution'])}), which only holds if you use all your credits.</p>"
    clip5 = money(c["usd_per_second"] * 5)
    faq = [{"@type": "Question", "name": f"How much does {m['name']} cost per second?",
            "acceptedAnswer": {"@type": "Answer", "text": f"As of {LAST}, from ${c['usd_per_second']:.4f}/s ({c['platform']}, {c['resolution']}). A 5-second clip at that rate costs about {clip5}."}}]
    model_deals = deals_for_model(slug, rs)
    deals_html = ""
    if model_deals:
        deals_html = '<h2>Live deals for this model</h2><div class="dealgrid">' + "".join(deal_card(d, rowset=rs) for d in model_deals) + "</div>"
    body = f"""<p class="small"><a href="{root("/")}">Prices</a> › {e(m['name'])}</p>
<h1>{e(m['name'])} price per second ({MONTH})</h1>
<p class="lead">{e(m['maker'])}'s {e(m['name'])} on {len({r['platform'] for r in rs})} platforms, all converted to dollars per second of video. Checked {LAST}.</p>
<div class="cards"><div class="card"><h3>Cheapest today</h3><div class="big">{money(c['usd_per_second'])}<span class="small">/s</span></div><div class="sub">{e(c['platform'])} · {e(c['resolution'])} {tag(c['status'])}</div><div class="sub">≈ {clip5} for a 5s clip</div>{deal_price_line(rs)}</div>
<div class="card"><h3>Cheapest by resolution</h3><ul class="small" style="padding-left:18px;margin:6px 0">{resl}</ul></div></div>
{summary}
{deals_html}
<h2>All {e(m['name'])} prices</h2>
<div class="tblwrap"><table>{THEAD.replace(' data-k="model"','').replace(' data-k=',' data-x=')}<tbody>{"".join(row_html(r) for r in rs)}</tbody></table></div>
<p class="small">Plan rows assume you use every credit you pay for. Unused credits make the real cost per second higher. Use the <a href="{root("/calculator/")}">credit calculator</a> to check a plan. Deal badges use the vendor's checkout price or stated rate. An unlimited window is a break-even second count, not $0/s.</p>
{news_box()}
{tick_script()}
<script type="application/ld+json">{json.dumps({"@context":"https://schema.org","@type":"FAQPage","mainEntity":faq})}</script>"""
    page(f"/models/{slug}/", f"{m['name']} price per second ({MONTH}): cheapest way to run it | ClipCost",
         f"{m['name']} costs from {money(c['usd_per_second'])}/s ({c['platform']}, {c['resolution']}). Compare {len(rs)} sourced prices across APIs and credit plans.", body)

# ---------- Calculator ----------
plan_opts = ""
for plat in sorted({p["platform"] for p in plans.values()}):
    plan_opts += f'<optgroup label="{e(plat)}">' + "".join(f'<option value="{k}">{e(p["plan"])}: ${p["usd_month"]:g}/mo</option>' for k, p in plans.items() if p["platform"] == plat) + "</optgroup>"
calc = f"""<h1>AI video credit calculator</h1>
<p class="lead">Pick a plan to see how many clips its credits buy each month and what each clip really costs. Credit costs come from each platform's own pricing page.</p>
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
<div><div class="tblwrap"><table id="ct"><thead><tr><th>Model</th><th>Res.</th><th>Clip</th><th>Credits/clip</th><th>Clips / month</th><th>$ / clip</th><th>$ / sec</th></tr></thead><tbody></tbody></table></div>
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
 function clipCount(credits, per){{const raw=credits/per, nearest=Math.round(raw);return Math.abs(raw-nearest)<0.005?nearest:Math.floor(raw)}}
 function current(r){{const today=new Date().toISOString().slice(0,10);if(r.promo_until&&r.promo_until<today)return false;if(r.discontinued_on&&r.discontinued_on<today)return false;return true}}
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
  if(u==null){{$('ct').querySelector('tbody').innerHTML='<tr><td colspan="7">Enter a whole number from 1 to 100.</td></tr>';return}}
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
   return `<tr><td><a href="${{BASE}}/models/${{r.model}}/">${{esc(r.variant)}}</a></td><td>${{esc(r.resolution)}}</td><td>${{r.clip_seconds}}s</td><td>${{r.status=='estimate'?'~':''}}${{(+r.credits_per_clip).toFixed(r.credits_per_clip%1?2:0)}}</td><td class="num">${{clips.toLocaleString()}}</td><td class="num">${{priceCell}}</td><td class="num">${{perSec}}${{extra}}</td></tr>`}}).join('');
  if(hasUn) $('dealEff').textContent='Effective $/s for an unlimited window is the plan price divided by the seconds you make. It is not $0.';
  history.replaceState(null,'','?plan='+k);}}
 $('plan').addEventListener('input',go);$('used').addEventListener('input',go);
 $('applyDeals').addEventListener('input',go);$('windowSecs').addEventListener('input',go);go();}});
</script>{news_box()}"""
page("/calculator/", f"AI Video Credit Calculator ({MONTH}): Higgsfield, Krea, Magnific | ClipCost",
     "How many Wan 3.0, Kling 3.0, Veo 3.1 or Seedance 2.5 clips does your Higgsfield, Krea or Magnific plan buy? Cost per clip and per second.", calc, "/calculator/")

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
page("/changes/", f"AI Video Price Changes Log ({MONTH}) | ClipCost",
     "Every AI video price change we detect, with dates and sources: Wan, Kling, Veo, Seedance, Runway, Higgsfield and more.",
     f"""<h1>Price changes log</h1><p class="lead">A daily script re-checks every source and logs each price change here with the date and a link to the source.</p>
<ul class="log" style="padding-left:0;list-style:none">{items}</ul>{news_box()}""", "/changes/")

# ---------- Newsletter ----------
page("/newsletter/", "ClipCost Weekly: AI video price drops & new models", "One short email a week: AI video price changes, new models and the cheapest way to run them.",
     f"""<h1>ClipCost Weekly</h1><p class="lead">One short email every Monday: which AI video prices changed, which new models launched, and the cheapest way to run each one right now. Written from the same data as this site.</p>{news_box()}""", "/newsletter/")

# ---------- About ----------
srcl = "".join(f'<li><a href="{e(outbound(s["url"])[0])}" rel="{outbound(s["url"])[1]}" target="_blank">{e(s["name"])}</a>{" (checked by hand)" if s["fetch"]=="manual" else ""}</li>' for s in sources.values())
unv = "".join(f'<li>{e(u["item"])}: <span class="small">{e(u["reason"])}</span></li>' for u in db["unverified"])
page("/about/", "About ClipCost: methodology & affiliate disclosure", "How ClipCost collects and normalizes AI video prices, and how the site is funded.",
     f"""<h1>About ClipCost</h1>
<p class="lead">ClipCost tracks what AI video generation actually costs, per second of finished video, across every place you can run a model.</p>
<h2>How the numbers work</h2>
<ul><li>Every price comes from the vendor's own pricing or model page, saved with a source link and the date we checked it.</li>
<li><b>APIs</b>: we use the vendor's stated $ per second. Runway credits are $0.01 each.</li>
<li><b>Credit plans</b>: plan price ÷ credits = $ per credit; × credits per clip ÷ clip length = $ per second. That assumes you use all your credits.</li>
<li>If a vendor says "~", "roughly" or "estimated", we label the row <i>approx.</i> If we can't confirm a price, we leave it out rather than guess.</li>
<li>Prices exclude VAT/sales tax and change often. Always confirm on the vendor's page before paying.</li>
<li><b>Deals</b> are a separate list. A discounted $/s uses the vendor's stated rate or the checkout plan price ÷ credits. A code that lasts the first N months also shows a 12-month blended rate. Unlimited windows show how many seconds of video cover the plan price. They are not listed at $0/s.</li></ul>
<h2>Sources we check</h2><ul class="small">{srcl}</ul>
<h2>Not included yet (unconfirmed)</h2><ul class="small">{unv}</ul>
<h2 id="disclosure">Affiliate disclosure</h2>
<div class="disclose">Some links on ClipCost are affiliate links. If you sign up through them we may earn a commission, at no extra cost to you. Affiliate status never changes the order of the tables: rows are always sorted by price.</div>
<p class="small">Contact: TODO-add-contact-email</p>""", "/about/")

# ---------- Deals ----------
def deal_sort(deal):
    return (deal.get("end") is None, deal.get("end") or "9999-99-99", deal.get("vendor") or "", deal.get("title") or "")

live_sorted = sorted(LIVE_DEALS, key=deal_sort)
vendors = sorted({d["vendor"] for d in live_sorted})
types = sorted({d["type"] for d in live_sorted})
live_html = "".join(deal_card(d) for d in live_sorted) or "<p>No live deals right now.</p>"
archive_sorted = sorted(ARCHIVED, key=lambda d: d.get("end") or "", reverse=True)
archive_html = "".join(deal_card(d, archive=True) for d in archive_sorted) or "<p class='small'>No tracked deal has expired yet. Older holiday sales are on the Black Friday page, labeled 2025.</p>"
deals_body = f"""<h1>AI video deals</h1>
<p class="lead">Offers copied from vendor pricing pages and official accounts. Countdowns use your clock, so they stay right between daily builds. A deal with no end date is not given a guessed one.</p>
<div class="disclose"><b>Disclosure.</b> Higgsfield links on this page are affiliate links (parameter <code>fpr=emmanuel-bbfe0e</code>) and use <code>rel="sponsored nofollow"</code>. If you sign up through them, ClipCost may earn a commission, at no extra cost to you. Links to Krea, Magnific, Runway, fal, and other vendors are the official URLs, with no affiliate tag. Deals are listed only when the vendor's own page or official account is the source. Order is the end date, not who pays us. See the <a href="{root("/about/#disclosure")}">full disclosure</a>.</div>
<div class="filters">
<select id="dVendor" aria-label="Vendor"><option value="">All vendors</option>{"".join(f'<option value="{e(v)}">{e(v)}</option>' for v in vendors)}</select>
<select id="dType" aria-label="Deal type"><option value="">All types</option>{"".join(f'<option value="{e(t)}">{e(t.replace("_", " "))}</option>' for t in types)}</select>
<span class="small" id="dCount"></span>
</div>
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
  document.querySelectorAll('#liveDeals [data-deal-card]').forEach(card=>{{
    const hide=(v&&card.dataset.vendor!==v)||(t&&card.dataset.type!==t);
    card.classList.toggle('is-filtered', hide);
    if(!hide && !card.classList.contains('is-past')) n++;
  }});
  const count=document.getElementById('dCount');
  if(count) count.textContent=n+' live';
}}
document.getElementById('dVendor').addEventListener('input', filterDeals);
document.getElementById('dType').addEventListener('input', filterDeals);
document.addEventListener('DOMContentLoaded', filterDeals);
filterDeals();
</script>"""
page("/deals/", f"AI video deals ({MONTH}): Higgsfield, Krea, fal, Runway, Magnific | ClipCost",
     "Live AI video discounts, plan sales, promo codes, and unlimited windows, with end dates and the $/s math.",
     deals_body, "/deals/",
     extra_head=f'<link rel="alternate" type="application/rss+xml" title="ClipCost deals" href="{root("/deals.xml")}">')

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
<div class="disclose">Higgsfield links elsewhere on ClipCost can be affiliate links. The posts linked on this page are the vendors' own X accounts. <a href="{root("/about/#disclosure")}">Disclosure</a>.</div>
"""
page("/deals/black-friday/", "AI video Black Friday 2026 (stub) and 2025 holiday deals | ClipCost",
     "A stub for 2026 AI video holiday sales, plus dated 2025 examples from Higgsfield, Krea, and Magnific.",
     bf_body, "/deals/")

def write_feeds():
    def slim(deal, status):
        return {
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
    payload = {
        "updated": TODAY,
        "deals": [slim(d, "live") for d in live_sorted],
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
        "  <title>ClipCost deals</title>\n"
        f"  <link>{SITE_URL}/deals/</link>\n"
        "  <description>Live AI video deals from vendor pages and official accounts.</description>\n"
        f"  <lastBuildDate>{built}</lastBuildDate>\n"
        + "\n".join(items) + "\n</channel>\n</rss>\n"
    )
    open(os.path.join(DIST, "deals.xml"), "w").write(rss)

write_feeds()

# ---------- 404, robots, sitemap ----------
page("/404.html", "Page not found | ClipCost", "Page not found.", f'<h1>Page not found</h1><p><a href="{root("/")}">Back to the price table</a></p>')
open(os.path.join(DIST, "robots.txt"), "w").write(f"User-agent: *\nAllow: {root('/')}\nSitemap: {SITE_URL}/sitemap.xml\n")
urls = ["/", "/deals/", "/deals/black-friday/", "/calculator/", "/changes/", "/newsletter/", "/about/"] + [f"/models/{s}/" for s in models]
open(os.path.join(DIST, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    "".join(f"  <url><loc>{SITE_URL}{u}</loc><lastmod>{LAST}</lastmod></url>\n" for u in urls) + "</urlset>\n")
print("built", len(urls), "pages into", DIST)
