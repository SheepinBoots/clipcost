#!/usr/bin/env python3
"""Build the static ClipCost site from data/*.json into dist/."""
import json, os, shutil, html, datetime
from urllib.parse import urlparse
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
rows, models, plans, sources = db["rows"], db["models"], db["plans"], db["sources"]
today = datetime.date.today()
MONTH = today.strftime("%b %Y")
LAST = max(r["checked"] for r in rows)

# TODO(affiliate): swap placeholder params for real tracking links after approval.
AFF = {
 "Higgsfield": "https://higgsfield.ai/pricing?ref=TODO_HIGGSFIELD_AFFILIATE_ID",
 "Higgsfield API": "https://open.higgsfield.ai/pricing?ref=TODO_HIGGSFIELD_AFFILIATE_ID",
 "Krea": "https://www.krea.ai/pricing?via=TODO_KREA_AFFILIATE_ID",
 "Magnific": "https://www.magnific.com/pricing?ref=TODO_MAGNIFIC_AFFILIATE_ID",
}
def plat_link(p, url):
    if p in AFF: return f'<a href="{AFF[p]}" rel="sponsored nofollow noopener" target="_blank" data-affiliate="TODO">{html.escape(p)}</a>'
    return f'<a href="{url}" rel="nofollow noopener" target="_blank">{html.escape(p)}</a>'
e = html.escape
def money(v):
    return f"${v:.3f}" if v >= 0.01 else f"${v:.4f}"

def page(path, title, desc, body, active=""):
    canon = SITE_URL + path
    navs = [("/", "Prices"), ("/calculator/", "Credit calculator"), ("/changes/", "Price changes"), ("/newsletter/", "Newsletter"), ("/about/", "About")]
    nav = "".join(f'<a href="{root(h)}"{" class=on" if h==active else ""}>{t}</a>' for h, t in navs)
    modlinks = " · ".join(f'<a href="{root(f"/models/{s}/")}">{e(m["name"])}</a>' for s, m in models.items())
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canon}"><meta name="robots" content="index,follow">
<meta property="og:type" content="website"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canon}"><meta property="og:site_name" content="ClipCost"><meta name="twitter:card" content="summary">
<meta name="theme-color" content="#0b0d12"><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%235ce1a8'/%3E%3Ctext x='16' y='22' font-size='16' text-anchor='middle' font-family='sans-serif' font-weight='800' fill='%2306281b'%3E$%3C/text%3E%3C/svg%3E">
<link rel="stylesheet" href="{root("/style.css")}"></head><body>
<header class="top"><div class="wrap"><a class="logo" href="{root("/")}">Clip<span>Cost</span></a><nav>{nav}</nav></div></header>
<main class="wrap">{body}</main>
<footer><div class="wrap"><p><b>Models:</b> {modlinks}</p>
<p>Prices are copied from each vendor's own pricing page, with the date we checked. Always confirm on the vendor's page before you buy. Some links are affiliate links (<a href="{root("/about/#disclosure")}">disclosure</a>).</p>
<p>© {today.year} ClipCost · Data last checked {LAST}</p></div></footer></body></html>"""
    out = os.path.join(DIST, path.strip("/"), "index.html") if path.endswith("/") else os.path.join(DIST, path.strip("/"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w").write(doc)

def tag(st): return f'<span class="tag {st}">{ {"verified":"vendor-stated","estimate":"approx.","promo":"promo"}[st] }</span>'

def row_html(r):
    m = models[r["model"]]["name"]
    what = e(r["variant"]) + (f' · <span class="small">{e(r["plan_name"])}</span>' if r["kind"] == "plan" else "")
    aud = "" if r.get("audio") is None else (" · audio" if r["audio"] else " · no audio")
    extra = e(r["math"]) if r.get("math") else ""
    if r.get("note"): extra += (" " if extra else "") + e(r["note"])
    promo = f' <span class="small">until {r["promo_until"]}</span>' if r.get("promo_until") else ""
    return (f'<tr><td><a href="{root(f"/models/{r["model"]}/")}">{e(m)}</a></td><td>{plat_link(r["platform"], r["source_url"])}</td>'
            f'<td>{what}</td><td>{e(r["resolution"])}{aud}</td><td class="num">{money(r["usd_per_second"])}</td>'
            f'<td>{tag(r["status"])}{promo}</td><td class="math">{extra}</td>'
            f'<td class="small"><a href="{r["source_url"]}" rel="nofollow noopener" target="_blank">source</a><br>{r["checked"]}</td></tr>')

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
os.makedirs(os.path.join(DIST, "data")); shutil.copy(os.path.join(ROOT, "data", "prices.json"), os.path.join(DIST, "data"))

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
              f'<a class="go" href="{root(f"/models/{slug}/")}">All {len(rs)} prices →</a></div>')
opts = lambda vals: "".join(f'<option value="{e(v)}">{e(l)}</option>' for v, l in vals)
platforms = sorted({r["platform"] for r in rows})
ver = sum(r["status"] == "verified" for r in rows)
home = f"""<h1>AI video cost per second, compared</h1>
<p class="lead">{len(rows)} prices for {len(models)} video models on {len(platforms)} platforms, from Higgsfield plans to the fal, Runway and Kling APIs. Everything is converted to <b>dollars per second of video</b>, and the math is shown for credit plans. Checked {LAST}.</p>
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
const BASE={json.dumps(BASE)};
const AFF={json.dumps(AFF)};
const MODELS={json.dumps({k:v["name"] for k,v in models.items()})};
let DATA=[];fetch(BASE+'/data/prices.json').then(r=>r.json()).then(d=>{{DATA=d.rows;render();}});
let sortK='usd_per_second',dir=1;
const $=id=>document.getElementById(id);
function esc(s){{return String(s??'').replace(/[&<>"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]))}}
function money(v){{return '$'+(v>=0.01?v.toFixed(3):v.toFixed(4))}}
function tag(s){{return `<span class="tag ${{s}}">${{{{verified:'vendor-stated',estimate:'approx.',promo:'promo'}}[s]}}</span>`}}
function plat(r){{const a=AFF[r.platform];return a?`<a href="${{a}}" rel="sponsored nofollow noopener" target="_blank" data-affiliate="TODO">${{esc(r.platform)}}</a>`:`<a href="${{r.source_url}}" rel="nofollow noopener" target="_blank">${{esc(r.platform)}}</a>`}}
function render(){{
 const fm=$('fModel').value,fp=$('fPlat').value,fk=$('fKind').value,fr=$('fRes').value.trim().toLowerCase();
 let rs=DATA.filter(r=>(!fm||r.model==fm)&&(!fp||r.platform==fp)&&(!fk||r.kind==fk)&&(!fr||String(r.resolution).toLowerCase().includes(fr))&&!($('fPromo').checked&&r.status=='promo')&&!($('fEst').checked&&r.status=='estimate'));
 rs.sort((a,b)=>{{let x=a[sortK],y=b[sortK];if(sortK=='model'){{x=MODELS[x];y=MODELS[y]}}return (x>y?1:x<y?-1:0)*dir}});
 document.querySelector('#prices tbody').innerHTML=rs.map(r=>{{
  const what=esc(r.variant)+(r.kind=='plan'?` · <span class="small">${{esc(r.plan_name)}}</span>`:'');
  const aud=r.audio==null?'':(r.audio?' · audio':' · no audio');
  const extra=[r.math,r.note].filter(Boolean).map(esc).join(' ');
  const promo=r.promo_until?` <span class="small">until ${{r.promo_until}}</span>`:'';
  return `<tr><td><a href="${{BASE}}/models/${{r.model}}/">${{esc(MODELS[r.model])}}</a></td><td>${{plat(r)}}</td><td>${{what}}</td><td>${{esc(r.resolution)}}${{aud}}</td><td class="num">${{money(r.usd_per_second)}}</td><td>${{tag(r.status)}}${{promo}}</td><td class="math">${{extra}}</td><td class="small"><a href="${{r.source_url}}" rel="nofollow noopener" target="_blank">source</a><br>${{r.checked}}</td></tr>`}}).join('');
 $('count').textContent=rs.length+' rows';
 document.querySelectorAll('#prices th').forEach(th=>{{th.classList.remove('sorted-asc','sorted-desc');if(th.dataset.k==sortK)th.classList.add(dir>0?'sorted-asc':'sorted-desc')}});
}}
['fModel','fPlat','fKind','fRes','fPromo','fEst'].forEach(id=>$(id).addEventListener('input',render));
document.querySelectorAll('#prices th[data-k]').forEach(th=>th.addEventListener('click',()=>{{const k=th.dataset.k;dir=(sortK==k)?-dir:1;sortK=k;render()}}));
</script>"""
page("/", f"AI Video Cost Per Second ({MONTH}): Wan 3.0, Kling 3.0, Veo 3.1, Seedance 2.5 | ClipCost",
     f"Compare what AI video costs per second across Higgsfield, fal, Runway, Kling, Krea, Magnific, Replicate and Atlas Cloud. {len(rows)} sourced prices, checked {LAST}.", home, "/")

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
    body = f"""<p class="small"><a href="{root("/")}">Prices</a> › {e(m['name'])}</p>
<h1>{e(m['name'])} price per second ({MONTH})</h1>
<p class="lead">{e(m['maker'])}'s {e(m['name'])} on {len({r['platform'] for r in rs})} platforms, all converted to dollars per second of video. Checked {LAST}.</p>
<div class="cards"><div class="card"><h3>Cheapest today</h3><div class="big">{money(c['usd_per_second'])}<span class="small">/s</span></div><div class="sub">{e(c['platform'])} · {e(c['resolution'])} {tag(c['status'])}</div><div class="sub">≈ {clip5} for a 5s clip</div></div>
<div class="card"><h3>Cheapest by resolution</h3><ul class="small" style="padding-left:18px;margin:6px 0">{resl}</ul></div></div>
{summary}
<h2>All {e(m['name'])} prices</h2>
<div class="tblwrap"><table>{THEAD.replace(' data-k="model"','').replace(' data-k=',' data-x=')}<tbody>{"".join(row_html(r) for r in rs)}</tbody></table></div>
<p class="small">Plan rows assume you use every credit you pay for. Unused credits make the real cost per second higher. Use the <a href="{root("/calculator/")}">credit calculator</a> to check a plan.</p>
{news_box()}
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
<label class="small" for="used">% of credits you actually use</label><br><input id="used" type="number" min="1" max="100" value="100" style="width:100px"> %
<div style="margin-top:14px"><div class="small">Plan price</div><div class="kpi" id="kPrice"></div>
<div class="small" style="margin-top:8px">Credits per month</div><div class="kpi" id="kCred"></div>
<div class="small" style="margin-top:8px">Cost per credit</div><div class="kpi" id="kPer"></div></div>
<p class="small" id="pNote"></p><p id="pLink"></p></div>
<div><div class="tblwrap"><table id="ct"><thead><tr><th>Model</th><th>Res.</th><th>Clip</th><th>Credits/clip</th><th>Clips / month</th><th>$ / clip</th><th>$ / sec</th></tr></thead><tbody></tbody></table></div>
<p class="small">"~" = the platform gives an approximate credit cost. Using fewer of your credits raises the real cost of each clip.</p></div></div>
<script>
const BASE={json.dumps(BASE)};const AFF={json.dumps(AFF)};const MODELS={json.dumps({k:v["name"] for k,v in models.items()})};
fetch(BASE+'/data/prices.json').then(r=>r.json()).then(d=>{{
 const $=id=>document.getElementById(id);
 const esc=s=>String(s??'').replace(/[&<>]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[c]));
 const pk=new URLSearchParams(location.search).get('plan');if(pk&&d.plans[pk])$('plan').value=pk;
 function go(){{const k=$('plan').value,p=d.plans[k],u=Math.max(1,Math.min(100,+$('used').value||100))/100;
  const per=p.usd_month/p.credits_month;
  $('kPrice').textContent='$'+p.usd_month+'/mo';$('kCred').textContent=p.credits_month.toLocaleString();$('kPer').textContent='$'+per.toFixed(5);
  $('pNote').textContent=(p.credits_note||'')+' Billing: '+p.billing+'. Checked '+p.checked+'.';
  $('pLink').innerHTML=`<a class="btn" href="${{AFF[p.platform]||p.source_url}}" rel="sponsored nofollow noopener" target="_blank" data-affiliate="TODO">See ${{esc(p.platform)}} plans</a> <a class="small" href="${{p.source_url}}" rel="nofollow noopener" target="_blank">source</a>`;
  const rs=d.rows.filter(r=>r.plan==k).sort((a,b)=>a.usd_per_second-b.usd_per_second);
  $('ct').querySelector('tbody').innerHTML=rs.map(r=>{{const clips=Math.floor(p.credits_month*u/r.credits_per_clip);const pc=r.usd_per_clip/u;
   return `<tr><td><a href="${{BASE}}/models/${{r.model}}/">${{esc(r.variant)}}</a></td><td>${{esc(r.resolution)}}</td><td>${{r.clip_seconds}}s</td><td>${{r.status=='estimate'?'~':''}}${{(+r.credits_per_clip).toFixed(r.credits_per_clip%1?2:0)}}</td><td class="num">${{clips.toLocaleString()}}</td><td class="num">$${{pc.toFixed(3)}}</td><td class="num">$${{(pc/r.clip_seconds).toFixed(4)}}</td></tr>`}}).join('');
  history.replaceState(null,'','?plan='+k);}}
 $('plan').addEventListener('input',go);$('used').addEventListener('input',go);go();}});
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
    src = f' <a class="small" href="{c["source_url"]}" rel="nofollow noopener" target="_blank">source</a>' if c.get("source_url") else ""
    items += f'<li><span class="pill">{c["date"]}</span> <span class="pill">{e(c.get("type","")).upper()}</span> {txt}{src}</li>'
page("/changes/", f"AI Video Price Changes Log ({MONTH}) | ClipCost",
     "Every AI video price change we detect, with dates and sources: Wan, Kling, Veo, Seedance, Runway, Higgsfield and more.",
     f"""<h1>Price changes log</h1><p class="lead">A daily script re-checks every source and logs each price change here with the date and a link to the source.</p>
<ul class="log" style="padding-left:0;list-style:none">{items}</ul>{news_box()}""", "/changes/")

# ---------- Newsletter ----------
page("/newsletter/", "ClipCost Weekly: AI video price drops & new models", "One short email a week: AI video price changes, new models and the cheapest way to run them.",
     f"""<h1>ClipCost Weekly</h1><p class="lead">One short email every Monday: which AI video prices changed, which new models launched, and the cheapest way to run each one right now. Written from the same data as this site.</p>{news_box()}""", "/newsletter/")

# ---------- About ----------
srcl = "".join(f'<li><a href="{s["url"]}" rel="nofollow noopener" target="_blank">{e(s["name"])}</a>{" (checked by hand)" if s["fetch"]=="manual" else ""}</li>' for s in sources.values())
unv = "".join(f'<li>{e(u["item"])}: <span class="small">{e(u["reason"])}</span></li>' for u in db["unverified"])
page("/about/", "About ClipCost: methodology & affiliate disclosure", "How ClipCost collects and normalizes AI video prices, and how the site is funded.",
     f"""<h1>About ClipCost</h1>
<p class="lead">ClipCost tracks what AI video generation actually costs, per second of finished video, across every place you can run a model.</p>
<h2>How the numbers work</h2>
<ul><li>Every price comes from the vendor's own pricing or model page, saved with a source link and the date we checked it.</li>
<li><b>APIs</b>: we use the vendor's stated $ per second. Runway credits are $0.01 each.</li>
<li><b>Credit plans</b>: plan price ÷ credits = $ per credit; × credits per clip ÷ clip length = $ per second. That assumes you use all your credits.</li>
<li>If a vendor says "~", "roughly" or "estimated", we label the row <i>approx.</i> If we can't confirm a price, we leave it out rather than guess.</li>
<li>Prices exclude VAT/sales tax and change often. Always confirm on the vendor's page before paying.</li></ul>
<h2>Sources we check</h2><ul class="small">{srcl}</ul>
<h2>Not included yet (unconfirmed)</h2><ul class="small">{unv}</ul>
<h2 id="disclosure">Affiliate disclosure</h2>
<div class="disclose">Some links on ClipCost are affiliate links. If you sign up through them we may earn a commission, at no extra cost to you. Affiliate status never changes the order of the tables: rows are always sorted by price.</div>
<p class="small">Contact: TODO-add-contact-email</p>""", "/about/")

# ---------- 404, robots, sitemap ----------
page("/404.html", "Page not found | ClipCost", "Page not found.", f'<h1>Page not found</h1><p><a href="{root("/")}">Back to the price table</a></p>')
open(os.path.join(DIST, "robots.txt"), "w").write(f"User-agent: *\nAllow: {root('/')}\nSitemap: {SITE_URL}/sitemap.xml\n")
urls = ["/", "/calculator/", "/changes/", "/newsletter/", "/about/"] + [f"/models/{s}/" for s in models]
open(os.path.join(DIST, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    "".join(f"  <url><loc>{SITE_URL}{u}</loc><lastmod>{LAST}</lastmod></url>\n" for u in urls) + "</urlset>\n")
print("built", len(urls), "pages into", DIST)
