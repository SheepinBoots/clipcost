#!/usr/bin/env python3
"""Calculator quotes for stated audio, length, and input. At least 10 cases."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import variations as V

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = json.load(open(os.path.join(ROOT, "data", "prices.json")))
ROWS = {r["id"]: r for r in DB["rows"]}

def one(rid, **kwargs):
    return V.quote(ROWS[rid], **kwargs)

cases = []

def check(name, result, status, usd=None):
    cases.append(name)
    assert result["status"] == status, (name, result)
    if usd is not None:
        assert abs(result["usd_per_second"] - usd) < 1e-9, (name, result)

# Higgsfield Starter Wan 480p is priced at 5s.
hf = next(r["id"] for r in DB["rows"] if r.get("plan") == "hf-starter" and r["variant"] == "Wan 3.0" and r["resolution"] == "480p")
check("hf wan 5s", one(hf, seconds=5), "match", ROWS[hf]["usd_per_second"])
check("hf wan 10s not stated", one(hf, seconds=10), "not_stated")
check("hf wan 480p", one(hf, resolution="480p"), "match", ROWS[hf]["usd_per_second"])
check("hf wan 720p not this row", one(hf, resolution="720p"), "not_offered")

# fal Wan is a flat per-second rate.
fal = next(r["id"] for r in DB["rows"] if r["platform"] == "fal" and r["variant"] == "Text to video" and r["resolution"] == "720p" and r["model"] == "wan-3-0")
check("fal wan 5s", one(fal, seconds=5), "match", 0.10)
check("fal wan 30s", one(fal, seconds=30), "match", 0.10)
check("fal wan t2v", one(fal, input_type="t2v"), "match", 0.10)
check("fal wan i2v different input", one(fal, input_type="i2v"), "not_offered")
check("hf wan input unknown", one(hf, input_type="t2v"), "unknown", ROWS[hf]["usd_per_second"])

# fal Kling audio is two prices.
off = next(r["id"] for r in DB["rows"] if r["platform"] == "fal" and r["variant"] == "Pro, audio off")
on = next(r["id"] for r in DB["rows"] if r["platform"] == "fal" and r["variant"] == "Pro, audio on")
check("fal kling audio off", one(off, audio="without"), "match", 0.112)
check("fal kling audio on", one(on, audio="with"), "match", 0.168)
check("fal kling off row rejects on", one(off, audio="with"), "not_offered")

# Higgsfield API Wan Prime has a 2-30s range and does not price by length.
p480 = next(r["id"] for r in DB["rows"] if r["source"] == "hf_api_wan" and r["resolution"] == "480p" and r["model"] == "wan-3-0-prime")
p720 = next(r["id"] for r in DB["rows"] if r["source"] == "hf_api_wan" and r["resolution"] == "720p" and r["model"] == "wan-3-0-prime")
check("prime 480p at 1s below min", one(p480, seconds=1), "not_offered")
check("prime 480p at 2s", one(p480, seconds=2), "match", 0.051)
check("prime 720p at 30s", one(p720, seconds=30), "match", 0.105)
assert abs(one(p720, seconds=30)["usd_per_second"] * 30 - 3.15) < 1e-9
p1080 = next(r["id"] for r in DB["rows"] if r["source"] == "hf_api_wan" and r["resolution"] == "1080p" and r["model"] == "wan-3-0-prime")
check("prime 1080p at 30s", one(p1080, seconds=30), "match", 0.21)
assert abs(one(p1080, seconds=30)["usd_per_second"] * 30 - 6.3) < 1e-9
check("prime 720p at 40s not offered", one(p720, seconds=40), "not_offered")
check("prime 720p at 5s", one(p720, seconds=5), "match", 0.105)
assert ROWS[p480]["variation"]["length_changes_price"] is False
assert ROWS[p480]["variation"]["duration"]["rate_by_length"] == "not stated"
assert ROWS[p720]["variation"]["length_changes_price"] is False
assert ROWS[p720]["variation"]["duration"]["priced_seconds"] == "not stated"
assert ROWS[p720]["variation"]["duration"]["rate_by_length"] == "not stated"
assert ROWS[p480]["variation"]["duration"]["min_seconds"] == 2
assert ROWS[p480]["usd_per_second"] == 0.051
assert any("capped at 15 seconds" in m["label"] for m in ROWS["r048"]["variation"]["modifiers"])
assert any("1 credit per second of input video" in m["label"] for m in ROWS["r057"]["variation"]["modifiers"])

# Krea Kling is audio off at 3s. Magnific Veo is with audio at 4s.
krea = next(r["id"] for r in DB["rows"] if r.get("plan") == "krea-pro-monthly" and r["variant"] == "Kling 3.0 Standard")
check("krea kling audio off 3s", one(krea, audio="without", seconds=3), "match", ROWS[krea]["usd_per_second"])
check("krea kling audio on is the other price", one(krea, audio="with"), "not_offered")
check("hf wan audio unknown", one(hf, audio="with"), "unknown", ROWS[hf]["usd_per_second"])
mag = next(r["id"] for r in DB["rows"] if r.get("plan") == "mag-pro" and r["variant"] == "Veo 3.1 4K w/audio")
check("magnific veo with audio 4s", one(mag, audio="with", seconds=4), "match", ROWS[mag]["usd_per_second"])

# fal Veo generation cap is 8s, and the rate does not change by length inside that cap.
veo = next(r["id"] for r in DB["rows"] if r["platform"] == "fal" and r["model"] == "veo-3-1" and r["audio"] is False and r["resolution"] != "4K")
check("fal veo 5s", one(veo, seconds=5, audio="without"), "match", 0.20)
check("fal veo 30s not offered", one(veo, seconds=30), "not_offered")

unlisted = next(r["id"] for r in DB["rows"] if r["id"] == "r173")
check("unlisted resolution matches dash", one(unlisted, resolution="not listed"), "match", ROWS[unlisted]["usd_per_second"])
check("unlisted resolution rejects 720p", one(unlisted, resolution="720p"), "not_offered")
check("480p row is not the unlisted option", one(hf, resolution="not listed"), "not_offered")
seed480 = next(r["id"] for r in DB["rows"] if r["id"] == "r017")
seed1080 = next(r["id"] for r in DB["rows"] if r["id"] == "r019")
check("fal seedance 480p with audio", one(seed480, audio="with"), "match", ROWS[seed480]["usd_per_second"])
check("fal seedance 1080p audio unknown", one(seed1080, audio="with"), "unknown", ROWS[seed1080]["usd_per_second"])
assert ROWS["r017"]["variation"]["audio"] == "with"
assert ROWS["r018"]["variation"]["audio"] == "with"
assert ROWS["r019"]["variation"]["audio"] == "not stated"
assert ROWS["r067"]["variation"]["audio"] == "with"
assert "with audio" in " ".join(c["needle"] for c in ROWS["r067"]["checks"]).lower()
assert ROWS["r024"]["variation"]["audio_changes_price"] == "not stated"
assert ROWS["r039"]["variation"]["length_changes_price"] == "not stated"
assert any("80 credit minimum" in m["label"] for m in ROWS["r039"]["variation"]["modifiers"])
assert any("plus 10 credits" in m["label"] for m in ROWS["r039"]["variation"]["modifiers"])
assert "80-credit" not in (ROWS["r039"].get("note") or "")
assert any("plus 1 credit per image or audio reference" in m["label"] for m in ROWS["r052"]["variation"]["modifiers"])
assert "+1 credit" not in (ROWS["r052"].get("note") or "")
assert any("plus 1 credit per reference image" in m["label"] for m in ROWS["r057"]["variation"]["modifiers"])
assert ROWS["r017"]["usd_per_second"] == 0.2205
assert ROWS["r067"]["usd_per_second"] == 0.6

errs = V.variation_errors(DB["rows"])
assert not errs, errs
assert len(cases) >= 10, len(cases)
print(f"ok {len(cases)} calculator cases")
