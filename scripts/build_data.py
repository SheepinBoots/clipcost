#!/usr/bin/env python3
"""Seed data/prices.json from vendor-stated numbers collected 2026-10-20.
Every row carries the source URL, checked date and the 'needle' patterns the
daily scraper (update_prices.py) re-checks. {N} = number that is checked,
{X} = any number (ignored). Run once; afterwards update_prices.py maintains it."""
import json, os
CHECKED = "2026-10-20"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOURCES = {
 "hf_plans":   {"name":"Higgsfield plans","url":"https://higgsfield.ai/pricing","fetch":"render"},
 "hf_api":     {"name":"Higgsfield API pricing","url":"https://open.higgsfield.ai/pricing","fetch":"static"},
 "hf_api_wan": {"name":"Higgsfield API: Wan 3.0 Prime","url":"https://open.higgsfield.ai/models/alibaba/wan-3.0-prime/text-to-video","fetch":"static"},
 "fal_wan3":   {"name":"fal: Wan 3.0","url":"https://fal.ai/models/alibaba/wan-3.0/text-to-video","fetch":"static"},
 "fal_wan3p":  {"name":"fal: Wan 3.0 Prime","url":"https://fal.ai/models/alibaba/wan-3.0-prime/text-to-video","fetch":"static"},
 "fal_kling3": {"name":"fal: Kling 3.0 Pro","url":"https://fal.ai/models/fal-ai/kling-video/v3/pro/text-to-video","fetch":"static"},
 "fal_seed25": {"name":"fal: Seedance 2.5","url":"https://fal.ai/models/bytedance/seedance-2.5/text-to-video","fetch":"static"},
 "fal_veo31":  {"name":"fal: Veo 3.1","url":"https://fal.ai/models/fal-ai/veo3.1","fetch":"static"},
 "fal_pricing":{"name":"fal pricing table","url":"https://fal.ai/pricing","fetch":"static"},
 "rep_wan3":   {"name":"Replicate: Wan 3.0","url":"https://replicate.com/alibaba/wan-3","fetch":"static"},
 "runway":     {"name":"Runway API pricing","url":"https://docs.dev.runwayml.com/guides/pricing/","fetch":"static"},
 "kling_api":  {"name":"Kling official API pricing","url":"https://kling.ai/document-api/pricing/base/video.md","fetch":"static"},
 "gemini":     {"name":"Google Gemini API pricing","url":"https://ai.google.dev/gemini-api/docs/pricing","fetch":"static"},
 "atlas":      {"name":"Atlas Cloud pricing","url":"https://www.atlascloud.ai/pricing","fetch":"static","next_flight":True},
 "krea":       {"name":"Krea plans","url":"https://www.krea.ai/pricing","fetch":"static"},
 "magnific":   {"name":"Magnific (ex-Freepik) plans","url":"https://www.magnific.com/pricing","fetch":"static"},
 "kling_app":  {"name":"Kling app subscriptions","url":"https://kling.ai/pricing","fetch":"manual",
                "note":"Pricing renders client-side behind region/login; not captured. Check by hand."},
}

MODELS = {
 "wan-3-0-prime":{"name":"Wan 3.0 Prime","maker":"Alibaba"},
 "wan-3-0":{"name":"Wan 3.0","maker":"Alibaba"},
 "kling-3-0":{"name":"Kling 3.0","maker":"Kuaishou"},
 "seedance-2-5":{"name":"Seedance 2.5","maker":"ByteDance"},
 "veo-3-1":{"name":"Veo 3.1","maker":"Google"},
 "gemini-omni-flash":{"name":"Gemini Omni Flash 1.1","maker":"Google"},
 "minimax-hailuo":{"name":"MiniMax Hailuo / H3","maker":"MiniMax"},
 "runway-gen-4":{"name":"Runway Gen-4.x","maker":"Runway"},
 "grok-imagine":{"name":"Grok Imagine Video 1.5","maker":"xAI"},
}

rows = []
def api(model, variant, platform, src, usd, res, needle, audio=None, status="verified", note="", promo_until=None, unit_mult=1.0, raw=None):
    rows.append(dict(model=model, variant=variant, platform=platform, kind="api", resolution=res, audio=audio,
        usd_per_second=round(usd,5), status=status, promo_until=promo_until, source=src,
        math=None, checks=[{"needle":needle,"expect":raw if raw is not None else usd}], note=note))

# ---------- Higgsfield API ----------
P="Higgsfield API"
for res,v in [("480p",0.0272),("720p",0.056),("1080p",0.112)]:
    api("wan-3-0-prime","Text/Image/Reference to video",P,"hf_api_wan",v,res,("Video costs " if res=="480p" else "")+"${N} per second at "+res,
        status="promo",promo_until="2026-11-01",
        note="60% launch discount until Nov 1. Page ties 480p rate to 1-2s clips and 720p/1080p rates to 30s clips.")
api("wan-3-0-prime","List price (lowest mode)",P,"hf_api",0.068,"480p","Wan 3.0 Prime 3 modes 2–30s · Up to 1080p List price from ${N} / s",
    note="Undiscounted list price; 'from' = cheapest mode.")
api("wan-3-0","Text to video",P,"hf_api_wan",0.02,"480p","Wan 3.0 Text to Video ${N} –",status="promo",promo_until="2026-11-01",note="60% launch discount; low end of the stated 480p–1080p range.")
api("wan-3-0","Text to video",P,"hf_api_wan",0.08,"1080p","Wan 3.0 Text to Video ${X} – ${N} / sec",status="promo",promo_until="2026-11-01",note="60% launch discount; high end of the stated range.")
api("kling-3-0","List price (lowest mode)",P,"hf_api",0.084,"lowest mode","Kling 3.0 10 modes 3–15s · Up to 1080p List price from ${N} / s",note="'From' price; resolution of cheapest mode not stated on the list.")
api("seedance-2-5","List price (lowest mode)",P,"hf_api",0.206,"lowest mode","Seedance 2.5 5 modes 4–30s · Up to 1080p List price from ${N} / s",note="'From' price; resolution of cheapest mode not stated on the list.")

# ---------- fal ----------
P="fal"
for res,v in [("480p",0.05),("720p",0.10),("1080p",0.20)]:
    api("wan-3-0","Text to video",P,"fal_wan3",v,res,"${N} "+res+" ,")  # last has no comma; handled below
rows[-1]["checks"][0]["needle"]="or ${N} 1080p"
for res,v in [("480p",0.068),("720p",0.14),("1080p",0.28)]:
    api("wan-3-0-prime","Text to video",P,"fal_wan3p",v,res,"${N} at "+res)
api("kling-3-0","Pro, audio off",P,"fal_kling3",0.112,"Pro tier","charged ${N} (audio off)",audio=False)
api("kling-3-0","Pro, audio on",P,"fal_kling3",0.168,"Pro tier","(audio off) or ${N} (audio on)",audio=True)
api("seedance-2-5","Text to video (token-billed)",P,"fal_seed25",0.2205,"480p","For 480p, your request will cost roughly ${N} per second",audio=True,status="estimate",note="fal says 'roughly': billed by tokens (16:9, 24fps).")
api("seedance-2-5","Text to video (token-billed)",P,"fal_seed25",0.4730,"720p","for 720p, you will be charged roughly ${N} per second",audio=True,status="estimate",note="fal says 'roughly': billed by tokens.")
api("seedance-2-5","Text to video (token-billed)",P,"fal_seed25",1.164,"1080p","for 1080p, roughly ${N} per second",audio=True,status="estimate",note="fal says 'roughly': billed by tokens.")
api("veo-3-1","Standard, no audio",P,"fal_veo31",0.20,"720p/1080p","charged ${N} without audio or ${X} with audio for 720p or 1080p",audio=False)
api("veo-3-1","Standard, with audio",P,"fal_veo31",0.40,"720p/1080p","without audio or ${N} with audio for 720p or 1080p",audio=True)
api("minimax-hailuo","MiniMax H3 Max",P,"fal_pricing",0.05,"default","MiniMax H3 Max seconds ${N}",note="From fal's pricing table (default settings).")
api("minimax-hailuo","MiniMax H3 Max Turbo",P,"fal_pricing",0.025,"default","H3 Max Turbo seconds ${N}",note="From fal's pricing table (default settings).")
api("grok-imagine","Grok Imagine Video",P,"fal_pricing",0.05,"default","Grok Imagine Video seconds ${N}",note="From fal's pricing table (default settings).")

# ---------- Replicate ----------
for res,v in [("480p",0.05),("720p",0.10),("1080p",0.20)]:
    api("wan-3-0","alibaba/wan-3","Replicate","rep_wan3",v,res,res+": ${N} per second",
        note="Replicate's pricing page banner says 'Wan 3.0 is 30% off this week' - discount not shown on the model page, so not applied.")

# ---------- Runway API (credits at $0.01) ----------
R=[("wan-3-0","wan3 (480p)","480p",5,None),("wan-3-0","wan3 (720p)","720p",10,None),("wan-3-0","wan3 (1080p)","1080p",20,None),
   ("wan-3-0-prime","wan3_prime (480p)","480p",6.8,None),("wan-3-0-prime","wan3_prime (720p)","720p",14,None),("wan-3-0-prime","wan3_prime (1080p)","1080p",28,None),
   ("kling-3-0","kling3.0_standard (no audio)","Standard",9,False),("kling-3-0","kling3.0_standard (audio)","Standard",13,True),
   ("kling-3-0","kling3.0_pro (no audio)","Pro",12,False),("kling-3-0","kling3.0_pro (audio)","Pro",17,True),("kling-3-0","kling3.0_4k","4K",43,None),
   ("seedance-2-5","seedance2_5 (480p)","480p",20,True),("seedance-2-5","seedance2_5 (720p)","720p",30,True),("seedance-2-5","seedance2_5 (1080p)","1080p",68,True),
   ("veo-3-1","veo3.1 (audio)","—",40,True),("veo-3-1","veo3.1 (no audio)","—",20,False),("veo-3-1","veo3.1_fast (audio)","—",15,True),("veo-3-1","veo3.1_fast (no audio)","—",10,False),
   ("runway-gen-4","gen4.5","—",12,None),("runway-gen-4","gen4_turbo","—",5,None),
   ("minimax-hailuo","hailuo3 (768P)","768p",10,None),("minimax-hailuo","hailuo3 (2K)","2K",15,None),("minimax-hailuo","h3_max (480p)","480p",5,None),("minimax-hailuo","h3_max (768p)","768p",8,None),
   ("grok-imagine","grok_imagine_1_5 (480p)","480p",10,None),("grok-imagine","grok_imagine_1_5 (720p)","720p",16,None),("grok-imagine","grok_imagine_1_5 (1080p)","1080p",29,None),
   ("grok-imagine","grok_imagine_1_5_lite (480p)","480p",2,None),("grok-imagine","grok_imagine_1_5_lite (720p)","720p",3,None),
   ("gemini-omni-flash","gemini_omni_flash_1.1 (720p)","720p",10,None),("gemini-omni-flash","gemini_omni_flash_1.1 (1080p)","1080p",15,None)]
for m,key,res,cr,aud in R:
    notes={"seedance2_5":"80-credit ($0.80) minimum per generation; input/reference video billed extra.","hailuo3":"+2 credits per reference image/start frame.","grok_imagine_1_5":"+1 credit per image/audio reference.","gemini_omni":"+1 credit per reference image."}
    n=next((v for k,v in notes.items() if key.startswith(k)),"")
    api(m,key,"Runway API","runway",cr*0.01,res,key+" {N} credits",audio=aud,raw=cr,
        note=("Runway credits are $0.01 each. "+n).strip())
    rows[-1]["math"]=f"{cr} credits/s × $0.01 = ${cr*0.01:.3f}/s"

# ---------- Kling official API ----------
K=[("Kling 3.0, no audio","720p",False,0.084,"Kling 3.0 | No Native Audio | Per second (Total duration = Output duration) | {X} Units (${N}) /s"),
   ("Kling 3.0, no audio","1080p",False,0.112,"Kling 3.0 | No Native Audio | Per second (Total duration = Output duration) | {X} Units (${X}) /s | {X} Units (${N}) /s"),
   ("Kling 3.0, no audio","4K",False,0.42,"Kling 3.0 | No Native Audio | Per second (Total duration = Output duration) | {X} Units (${X}) /s | {X} Units (${X}) /s | {X} Units (${N}) /s"),
   ("Kling 3.0, audio","720p",True,0.126,"Kling 3.0 | With Native Audio | Per second (Total duration = Output duration) | {X} Units (${N}) /s"),
   ("Kling 3.0, audio","1080p",True,0.168,"Kling 3.0 | With Native Audio | Per second (Total duration = Output duration) | {X} Units (${X}) /s | {X} Units (${N}) /s"),
   ("Kling 3.0 Turbo, audio","720p",True,0.112,"Kling 3.0 Turbo | With Native Audio | Per second (Total duration = Output duration) | {X} Units (${N}) /s"),
   ("Kling 3.0 Turbo, audio","1080p",True,0.14,"Kling 3.0 Turbo | With Native Audio | Per second (Total duration = Output duration) | {X} Units (${X}) /s | {X} Unit (${N}) /s")]
for v,res,aud,usd,nd in K: api("kling-3-0",v,"Kling API","kling_api",usd,res,nd,audio=aud,note="Official Kling resource-package rate.")

# ---------- Google Gemini API ----------
G=[("veo-3-1","Veo 3.1 Standard (audio)","720p/1080p",0.40,"Veo 3.1 Standard video with audio price (default) Not available ${N} (720p and 1080p)"),
   ("veo-3-1","Veo 3.1 Standard (audio)","4K",0.60,"(720p and 1080p) ${N} (4k)"),
   ("veo-3-1","Veo 3.1 Fast (audio)","720p",0.10,"Veo 3.1 Fast video with audio price (default) Not available ${N} (720p)"),
   ("veo-3-1","Veo 3.1 Fast (audio)","1080p",0.12,"Veo 3.1 Fast video with audio price (default) Not available ${X} (720p) ${N} (1080p)"),
   ("veo-3-1","Veo 3.1 Lite (audio)","720p",0.05,"Veo 3.1 Lite video with audio price (default) Not available ${N} (720p)"),
   ("veo-3-1","Veo 3.1 Lite (audio)","1080p",0.08,"Veo 3.1 Lite video with audio price (default) Not available ${X} (720p) ${N} (1080p)")]
VEO_DOCS = "https://ai.google.dev/gemini-api/docs/veo"
for m,v,res,usd,nd in G:
    api(m,v,"Google Gemini API","gemini",usd,res,nd,audio=True,status="discontinued",
        note="Shut down on October 22, 2026. veo-3.1-generate-preview, veo-3.1-fast-generate-preview, and veo-3.1-lite-generate-preview are off. "+VEO_DOCS)
    rows[-1]["discontinued_on"] = "2026-10-22"
    rows[-1]["source_url"] = VEO_DOCS
api("gemini-omni-flash","gemini-omni-1.1-flash","Google Gemini API","gemini",0.10,"720p","effective price of approximately ${N} per second",status="estimate",note="Token-billed; Google states 'approximately $0.10 per second' of 720p.")

# ---------- Atlas Cloud ----------
A=[("seedance-2-5","Seedance 2.5 T2V","480p",0.1397,"480p Estimated → /s (estimated) ${N}"),
   ("seedance-2-5","Seedance 2.5 T2V","720p",0.3005,"720p Estimated → /s (estimated) ${N}"),
   ("seedance-2-5","Seedance 2.5 T2V","1080p",0.5914,"1080p Estimated → /s (estimated) ${N}")]
for m,v,res,usd,nd in A: api(m,v,"Atlas Cloud","atlas",usd,res,nd,status="estimate",note="Atlas labels these '(estimated)': billed on actual video tokens.")
api("minimax-hailuo","MiniMax H3 Fast T2V","Atlas Cloud","atlas",0.0437,"480P","MiniMax H3 Fast Text-to-Video Video 1 Price Our Price (USD) Start from ${N}/s")
api("gemini-omni-flash","Gemini Omni 1.1 Flash T2V","Atlas Cloud","atlas",0.099,"720p","Gemini Omni 1.1 Flash Text-to-Video\",\"tags\":[\"video\",\"google\",\"text\",\"text-to-video\",\"text to video\",\"gemini\",\"omni\",\"flash\",\"to\"],\"discount\":\"0.9\",\"billing_category\":\"output_duration\",\"billing_label\":\"Billed by output duration\",\"lowest_price_text\":\"720P as low as ${N} /s")

# ---------- Subscription plans ----------
PLANS = {
 # Higgsfield: prices verified on higgsfield.ai/pricing
 "hf-starter":{"platform":"Higgsfield","plan":"Starter","usd_month":19,"billing":"monthly or annual (same price)","credits_month":270,"source":"hf_plans",
   "checks":[{"needle":"Starter ${N}/month","expect":19},{"needle":"Fixed amount of {N} credits/mo $19","expect":270}]},
 "hf-plus-annual":{"platform":"Higgsfield","plan":"Plus (annual)","usd_month":47,"billing":"annual","credits_month":1200,"source":"hf_plans",
   "checks":[{"needle":"Plus ${N}/month","expect":47},{"needle":"Fixed amount of {N} credits/mo $59","expect":1200}]},
 "hf-plus-monthly":{"platform":"Higgsfield","plan":"Plus (monthly)","usd_month":59,"billing":"monthly","credits_month":1200,"source":"hf_plans",
   "checks":[{"needle":"${N} $47 per month, billed annually","expect":59}]},
 "hf-ultra-annual":{"platform":"Higgsfield","plan":"Ultra (annual)","usd_month":99,"billing":"annual","credits_month":3000,"source":"hf_plans",
   "checks":[{"needle":"Ultra BEST VALUE ${N}/month","expect":99},{"needle":"Seedance 2.5 videos {N} 6,000 9,000","expect":3000}]},
 "hf-ultra-monthly":{"platform":"Higgsfield","plan":"Ultra (monthly)","usd_month":129,"billing":"monthly","credits_month":3000,"source":"hf_plans",
   "checks":[{"needle":"${N} $99 per month, billed annually","expect":129}]},
 # Krea: units per month
 "krea-basic-yearly":{"platform":"Krea","plan":"Basic (yearly)","usd_month":5,"billing":"yearly","credits_month":5000,"source":"krea",
   "checks":[{"needle":"Seedance 2.0 Fast videos ${X} ${N} /month","expect":5},{"needle":"Basic {N} units / month","expect":5000}]},
 "krea-pro-monthly":{"platform":"Krea","plan":"Pro (monthly)","usd_month":35,"billing":"monthly","credits_month":20000,"source":"krea",
   "checks":[{"needle":"~65 Seedance 2.5 videos ${N} ${X} /month","expect":35},{"needle":"Pro {N} units / month","expect":20000}]},
 "krea-pro-yearly":{"platform":"Krea","plan":"Pro (yearly)","usd_month":21,"billing":"yearly","credits_month":20000,"source":"krea",
   "checks":[{"needle":"~65 Seedance 2.5 videos ${X} ${N} /month","expect":21}]},
 # Magnific: credits per YEAR, annual billing
 "mag-premium":{"platform":"Magnific","plan":"Premium (annual)","usd_month":14.50,"billing":"annual","credits_month":20000,"source":"magnific",
   "credits_note":"240K credits/year (= 20,000/month avg); credits valid 1 year",
   "checks":[{"needle":"stock content ${X} ${N} /month","expect":14.50},{"needle":"Premium assets {N} credits /year","expect":240000}]},
 "mag-premium-plus":{"platform":"Magnific","plan":"Premium+ (annual)","usd_month":33.75,"billing":"annual","credits_month":50000,"source":"magnific",
   "credits_note":"600K credits/year (= 50,000/month avg)",
   "checks":[{"needle":"full AI access ${X} ${N} /month","expect":33.75},{"needle":"UNLIMITED generations {N} credits /year","expect":600000}]},
 "mag-pro":{"platform":"Magnific","plan":"Pro (annual)","usd_month":82.50,"billing":"annual","credits_month":125000,"source":"magnific",
   "credits_note":"1.5M credits/year (= 125,000/month avg)",
   "checks":[{"needle":"content production ${X} ${N} /month","expect":82.50},{"needle":"Everything in Premium+ , and: {N} credits /year","expect":1500000}]},
}

# per-clip credit costs: (model, variant, res, credits, clip_s, needle, approx, audio)
CLIPS = {
 "Higgsfield":[
  ("wan-3-0-prime","Wan 3.0 Prime","480p",7.5,5,"Wan 3.0 Prime 480p {N} credits/5s",False,None),
  ("wan-3-0-prime","Wan 3.0 Prime","720p",15,5,"Wan 3.0 Prime 720p {N} credits/5s",False,None),
  ("wan-3-0-prime","Wan 3.0 Prime","1080p",30,5,"Wan 3.0 Prime 1080p {N} credits/5s",False,None),
  ("wan-3-0","Wan 3.0","480p",5,5,"Wan 3.0 480p {N} credits/5s",False,None),
  ("wan-3-0","Wan 3.0","720p",8.75,5,"Wan 3.0 720p {N} credits/5s",False,None),
  ("wan-3-0","Wan 3.0","1080p",17.5,5,"Wan 3.0 1080p {N} credits/5s",False,None),
  ("kling-3-0","Kling 3.0","720p",7,5,"Kling 3.0 720p ~{N} credits/5s",True,None),
  ("kling-3-0","Kling 3.0","1080p",8,5,"Kling 3.0 1080p ~{N} credits/5s",True,None),
  ("kling-3-0","Kling 3.0","4K",30,5,"Kling 3.0 4K ~{N} credits/5s",True,None),
  ("veo-3-1","Veo 3.1","720p",40,4,"Google Veo 3.1 720p ~{N} credits/4s",True,None),
  ("veo-3-1","Veo 3.1 Fast","720p",16,4,"Google Veo 3.1 Fast 720p ~{N} credits/4s",True,None),
  ("minimax-hailuo","Hailuo 2.3","768p",6,6,"Minimax Hailuo 2.3 768p ~{N} credits/6s",True,None),
 ],
 "Krea":[  # units per clip derived = Pro units (20,000) / Krea's approx clip count in the Pro column
  ("wan-3-0-prime","Wan 3.0 Prime","480p",20000/198,2,"Wan 3.0 Prime 2s, 480p ~{X} videos ~{N} videos",True,None,198),
  ("wan-3-0","Wan 3.0","480p",20000/180,2,"Wan 3.0 2s, 480p ~{X} videos ~{N} videos",True,None,180),
  ("kling-3-0","Kling 3.0 Standard","—",20000/107,3,"Kling 3.0 3s, standard mode, audio off ~{X} videos ~{N} videos",True,False,107),
  ("veo-3-1","Veo 3.1 Fast","720p",20000/84,4,"Veo 3.1 Fast 4s, 720p, audio off ~{X} videos ~{N} videos",True,False,84),
  ("veo-3-1","Veo 3.1 Lite","720p",20000/225,4,"Veo 3.1 Lite 4s, 720p ~{X} videos ~{N} videos",True,None,225),
  ("minimax-hailuo","Hailuo 2.3","768p",20000/96,6,"Hailuo 2.3 6s, 768p ~{X} videos ~{N} videos",True,None,96),
  ("minimax-hailuo","MiniMax H3 Max","480p",20000/154,5,"MiniMax H3 Max 5s, 480p, no reference images, no reference video ~{X} videos ~{N} videos",True,None,154),
  ("runway-gen-4","Runway Gen-4.5","—",20000/112,2,"Runway Gen-4.5 2s ~{X} videos ~{N} videos",True,None,112),
 ],
 "Magnific":[
  ("kling-3-0","Kling 3.0 Pro","1080p",450,5,"Kling 3.0 Pro 1080p {N} credits/5s",False,None),
  ("seedance-2-5","Seedance 2.5","720p",1760,4,"Seedance 2.5 720p {N} credits/4s",False,None),
  ("seedance-2-5","Seedance 2.5","1080p",4400,4,"Seedance 2.5 1080p {N} credits/4s",False,None),
  ("seedance-2-5","Seedance 2.5 Draft","480p",800,4,"Seedance 2.5 Draft 480p New {N} credits/4s",False,None),
  ("veo-3-1","Veo 3.1 4K w/audio","4K",2080,4,"Google Veo 3.1 4K w/audio {N} credits/4s",False,True),
  ("gemini-omni-flash","Gemini Omni 1.1","—",720,3,"Gemini Omni 1.1 New {N} credits/3s",False,None),
  ("minimax-hailuo","MiniMax H3 Max Turbo","768p",200,5,"MiniMax H3 Max Turbo 768p New {N} credits/5s",False,None),
 ],
}
PLAN_KEYS={"Higgsfield":["hf-starter","hf-plus-annual","hf-plus-monthly","hf-ultra-annual","hf-ultra-monthly"],
           "Krea":["krea-basic-yearly","krea-pro-monthly","krea-pro-yearly"],
           "Magnific":["mag-premium","mag-premium-plus","mag-pro"]}
CLIP_SRC={"Higgsfield":"hf_plans","Krea":"krea","Magnific":"magnific"}

# Higgsfield's compare table also gives yearly clip counts per plan; they show Starter
# cannot use some models, and imply exact credit costs where the label says "~".
EXCLUDE={("kling-3-0","1080p"):["hf-starter"],("kling-3-0","4K"):["hf-starter"],("veo-3-1","720p"):["hf-starter"]}
DERIVED={("Higgsfield","kling-3-0","720p"):(7.5,"Higgsfield labels it ~7 credits/5s; its yearly counts (Plus 1,920 clips for 14,400 credits) imply 7.5 credits, used here."),
         ("Higgsfield","kling-3-0","1080p"):(8.75,"Higgsfield labels it ~8 credits/5s; its yearly counts (Plus 1,645 clips for 14,400 credits) imply 8.75 credits, used here.")}
for platform, clips in CLIPS.items():
    for c in clips:
        m,var,res,cred,secs,needle,approx,aud=c[:8]
        cnt=c[8] if len(c)>8 else None
        label_cred=cred; dnote=""
        if (platform,m,res) in DERIVED: cred,dnote=DERIVED[(platform,m,res)]
        for pk in PLAN_KEYS[platform]:
            if platform=="Higgsfield" and pk in EXCLUDE.get((m,res),[]): continue
            p=PLANS[pk]
            per_credit=p["usd_month"]/p["credits_month"]
            clip_usd=per_credit*cred
            ups=clip_usd/secs
            unit="units" if platform=="Krea" else "credits"
            math=(f"${p['usd_month']:g}/mo ÷ {p['credits_month']:,} {unit} = ${per_credit:.5f}/{unit[:-1]}; "
                  f"{'~' if approx else ''}{cred:.1f} {unit}/clip ({secs}s) → ${clip_usd:.3f}/clip → ${ups:.4f}/s")
            if platform=="Krea":
                math=f"Krea says ~{cnt} clips on Pro (20,000 units) → ~{cred:.0f} units/clip. "+math
            if platform=="Magnific":
                math=f"{p['credits_note']}. "+math
            st="estimate" if approx else "verified"
            note=""
            if platform=="Higgsfield": note="Plus/Ultra also include 7-day unlimited Kling 3.0 (per pricing page); unused credits do not roll over per plan terms." if m=="kling-3-0" else ""
            if platform=="Krea": note="Krea publishes only approximate clip counts ('~'); per-clip units are derived."
            if platform=="Magnific": note="Annual billing; credits granted per year, valid 1 year."
            if dnote: note=(dnote+" "+note).strip()
            checks=[{"needle":needle,"expect":cnt if cnt else label_cred}]
            rows.append(dict(model=m,variant=var,platform=platform,kind="plan",plan=pk,plan_name=p["plan"],
                resolution=res,audio=aud,clip_seconds=secs,credits_per_clip=cred,usd_per_clip=round(clip_usd,4),
                usd_per_second=round(ups,5),status=st,promo_until=None,source=CLIP_SRC[platform],math=math,checks=checks,note=note))

for i,r in enumerate(rows):
    r["id"]=f"r{i+1:03d}"; r["checked"]=CHECKED; r["source_url"]=r.get("source_url") or SOURCES[r["source"]]["url"]
for p in PLANS.values(): p["checked"]=CHECKED; p["source_url"]=SOURCES[p["source"]]["url"]

out={"generated":CHECKED,"currency":"USD","sources":SOURCES,"models":MODELS,"plans":PLANS,"rows":rows,
     "unverified":[
       {"item":"Kling app (kling.ai) consumer subscription prices","reason":"pricing not rendered without login/region; check manually"},
       {"item":"Replicate Wan 3.0 '30% off this week' banner","reason":"discount not reflected on model page; not applied"},
       {"item":"Replicate Wan 3.0 Prime (alibaba/wan-3-prime)","reason":"model page shows no static price"},
       {"item":"Higgsfield Seedance 2.5 per-clip credits","reason":"plan page only says '~80 Seedance 2.5 videos' for 1,200 credits without clip length/resolution"},
       {"item":"Higgsfield Kling 3.0 credits","reason":"compare table says ~7 credits/5s at 720p, plan quiz says ≈14 credits per 8s 720p; both approximate"},
       {"item":"Krea Max plan per-clip counts","reason":"count column appears to assume a 40k pack, price for that pack not shown; Max omitted"},
       {"item":"Kling 4.0","reason":"official API page lists per-second rates, but input video changes the billed duration, so no single $/s is in the table"}]}
os.makedirs(os.path.join(ROOT,"data"),exist_ok=True)
json.dump(out,open(os.path.join(ROOT,"data","prices.json"),"w"),indent=1,ensure_ascii=False)
print(len(rows),"rows")
