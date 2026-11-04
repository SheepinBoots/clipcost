"""Structured audio, input, and duration facts for each price row.

Values are copied from the vendor page that the row already cites. Anything that
page does not say stays "not stated". Phrase checks are the same needle mechanism
the daily refresh uses, so a stated fact disappears from the page as a miss.
"""
import json, os, re

INPUTS = ("t2v", "i2v", "ref2v", "v2v", "extend", "lip-sync")
INPUT_LABELS = {
    "t2v": "text-to-video",
    "i2v": "image-to-video",
    "ref2v": "reference",
    "v2v": "video-to-video",
    "extend": "extend",
    "lip-sync": "lip-sync",
}
SCHEMA = {
    "audio": "with, without, or not stated. A separate price for each is a separate row.",
    "input": "not stated, or a list of t2v, i2v, ref2v, v2v, extend, lip-sync when the page names that mode for this price.",
    "duration": {
        "min_seconds": "number or not stated",
        "max_seconds": "number or not stated",
        "allowed_seconds": "list of seconds or not stated",
        "priced_seconds": "the clip length this credit price is for, or not stated",
        "rate_by_length": "not stated, or a list of {label, seconds, usd_per_second} copied from the page",
    },
    "audio_changes_price": "true, false, or not stated",
    "length_changes_price": "true, false, or not stated",
    "input_changes_price": "true, false, or not stated",
    "modifiers": "not stated, or extra stated rates that are not the headline $/s",
}


def blank():
    return {
        "audio": "not stated",
        "input": "not stated",
        "duration": {
            "min_seconds": "not stated",
            "max_seconds": "not stated",
            "allowed_seconds": "not stated",
            "priced_seconds": "not stated",
            "rate_by_length": "not stated",
        },
        "audio_changes_price": "not stated",
        "length_changes_price": "not stated",
        "input_changes_price": "not stated",
        "modifiers": "not stated",
        "phrases": [],
    }


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def add_phrase(row, phrase):
    phrase = phrase.strip()
    if not phrase:
        return
    for chk in row.get("checks") or []:
        if chk.get("phrase") and chk.get("needle") == phrase:
            return
        needle = chk.get("needle") or ""
        if not chk.get("phrase") and phrase in needle.replace("{N}", "").replace("{X}", ""):
            return
    row.setdefault("checks", []).append({"needle": phrase, "phrase": True})


def plan_variation(row):
    v = blank()
    needle = " ".join(c.get("needle") or "" for c in row.get("checks") or [])
    low = needle.lower()
    secs = row.get("clip_seconds")
    if _num(secs) and (f"{secs:g}s" in low or f"credits/{secs:g}s" in low or f"/{secs:g}s" in low):
        v["duration"]["priced_seconds"] = int(secs) if float(secs).is_integer() else secs
    if "audio off" in low or "no audio" in low or "without audio" in low:
        v["audio"] = "without"
    elif "w/audio" in low or "with audio" in low or "audio on" in low:
        v["audio"] = "with"
    if "t2v" in low:
        v["input"] = ["t2v"]
    return v


def api_variation(row):
    v = blank()
    plat, variant, res = row.get("platform"), row.get("variant") or "", row.get("resolution") or ""
    model = row.get("model")

    if plat == "Higgsfield API" and model == "wan-3-0-prime" and row.get("source") == "hf_api_wan":
        v["input"] = ["t2v", "i2v", "ref2v"]
        v["input_changes_price"] = False
        v["duration"]["min_seconds"] = 2
        v["duration"]["max_seconds"] = 30
        # One example length is stated per resolution. That is not a claim that the rate changes with length.
        v["phrases"] += [
            "Wan 3.0 Prime Text to Video",
            "Wan 3.0 Prime Image to Video",
            "Wan 3.0 Prime Reference to Video",
            "2 – 30s",
        ]
        stated_length = {
            "720p": (0.084, "$0.084 per second at 720p for 30 second clips"),
            "1080p": (0.168, "$0.168 per second at 1080p for 30 second clips"),
        }
        if res in stated_length and abs(row.get("usd_per_second", 0) - stated_length[res][0]) < 1e-9:
            v["duration"]["priced_seconds"] = 30
            v["phrases"].append(stated_length[res][1])
        return v

    if plat == "Higgsfield API" and row.get("source") == "hf_api" and "List price" in variant:
        ranges = {
            "wan-3-0-prime": (2, 30, "2–30s"),
            "kling-3-0": (3, 15, "3–15s"),
            "seedance-2-5": (4, 30, "4–30s"),
        }
        if model in ranges:
            lo, hi, phrase = ranges[model]
            v["duration"]["min_seconds"] = lo
            v["duration"]["max_seconds"] = hi
            v["phrases"].append(phrase)
        return v

    if plat == "Higgsfield API" and model == "wan-3-0" and row.get("source") == "hf_api_wan":
        v["input"] = ["t2v", "i2v", "ref2v"]
        v["input_changes_price"] = False
        v["duration"]["min_seconds"] = 2
        v["duration"]["max_seconds"] = 30
        v["phrases"] += ["Wan 3.0 Text to Video", "Wan 3.0 Image to Video", "Wan 3.0 Reference to Video", "2 – 30s"]
        return v

    if plat == "fal" and model == "wan-3-0" and "Text to video" in variant:
        v["input"] = ["t2v"]
        v["length_changes_price"] = False
        v["phrases"] += ["Wan (Text to Video)", "For every second of video you generate, you will be charged"]
        return v

    if plat == "fal" and model == "wan-3-0-prime":
        v["input"] = ["t2v"]
        v["length_changes_price"] = False
        v["phrases"] += ["Text to Video", "Billing is calculated per second of video generated"]
        return v

    if plat == "fal" and model == "kling-3-0" and "audio" in variant.lower():
        v["input"] = ["t2v"]
        v["audio"] = "with" if row.get("audio") is True else "without"
        v["audio_changes_price"] = True
        v["length_changes_price"] = False
        v["phrases"] += ["Text to Video (pro)", "For every second of video you generated, you will be charged"]
        if v["audio"] == "with":
            v["modifiers"] = [{"label": "voice control with audio", "usd_per_second": 0.196}]
            v["phrases"].append("you will be charged $0.196")
        return v

    if plat == "fal" and model == "seedance-2-5":
        v["input"] = ["t2v"]
        v["duration"]["max_seconds"] = 30
        v["length_changes_price"] = False
        v["phrases"] += ["text-to-video", "up to 30 seconds", "per second of generated video"]
        if res in ("480p", "720p"):
            v["audio"] = "with"
            v["phrases"].append(f"{res} with audio")
        return v

    if plat == "fal" and model == "veo-3-1":
        v["audio"] = "with" if row.get("audio") is True else "without"
        v["audio_changes_price"] = True
        v["duration"]["max_seconds"] = 8
        v["length_changes_price"] = False
        v["phrases"] += ["without audio or $0.40 with audio", "up to 8 seconds of video"]
        if res == "4K":
            v["phrases"].append("At 4k, you will be charged")
        return v

    if plat == "fal" and model == "minimax-hailuo":
        v["input"] = ["t2v"]
        v["length_changes_price"] = False
        v["phrases"].append("Billing is calculated per second of video generated")
        if "Turbo" in variant:
            v["phrases"].append("text-to-video")
        else:
            v["phrases"].append("Text to Video")
        return v

    if plat == "fal" and model == "grok-imagine":
        v["input"] = ["t2v"]
        v["input_changes_price"] = False
        v["audio"] = "with"
        v["length_changes_price"] = False
        v["phrases"] += [
            "prompts with audio",
            "Cost scales linearly with duration",
            "No input images or references",
        ]
        return v

    if plat == "Replicate" and model == "wan-3-0":
        v["input"] = ["t2v", "i2v"]
        v["duration"]["min_seconds"] = 2
        v["duration"]["max_seconds"] = 30
        v["phrases"] += ["Text to video", "Image to video", "from 2 to 30"]
        return v

    if plat == "Runway API":
        v["length_changes_price"] = False
        v["phrases"].append("credits per second")
        low = variant.lower()
        if "no audio" in low:
            v["audio"] = "without"
            v["audio_changes_price"] = True
        elif "(audio)" in low:
            v["audio"] = "with"
            v["audio_changes_price"] = True
        if variant.startswith("seedance2_5"):
            # Output is priced per second, but an 80-credit minimum means a short clip costs more per second.
            v["length_changes_price"] = "not stated"
            v["input_changes_price"] = True
            extra = {"480p": 10, "720p": 15, "1080p": 34}.get(res)
            mods = []
            if extra:
                label = f"plus {extra} credits per second of input and reference video"
                mods.append({"label": label, "usd_per_second": "not stated"})
                v["phrases"].append(label)
            mods.append({"label": "80 credit minimum per generation", "usd_per_second": "not stated"})
            v["phrases"].append("80 credit minimum per generation")
            v["modifiers"] = mods
        if variant.startswith("hailuo3"):
            v["input_changes_price"] = True
            v["modifiers"] = [
                {"label": "plus 2 credits per reference image or keyframe", "usd_per_second": "not stated"},
                {"label": "reference video billed at the same per-second rate as output (capped at 15 seconds)", "usd_per_second": "not stated"},
            ]
            v["phrases"].append("2 credits per reference image")
            v["phrases"].append("reference video billed at the same per-second rate as output (capped at 15 seconds)")
        if variant.startswith("grok_imagine_1_5"):
            v["input_changes_price"] = True
            v["modifiers"] = [{"label": "plus 1 credit per image or audio reference", "usd_per_second": "not stated"}]
            v["phrases"].append("1 credit per image or audio reference")
        if variant.startswith("gemini_omni_flash"):
            v["input_changes_price"] = True
            v["modifiers"] = [
                {"label": "plus 1 credit per reference image", "usd_per_second": "not stated"},
                {"label": "and 1 credit per second of input video", "usd_per_second": "not stated"},
            ]
            v["phrases"].append("1 credit per reference image")
            v["phrases"].append("and 1 credit per second of input video")
        return v

    if plat == "Kling API":
        v["length_changes_price"] = False
        v["phrases"].append("Total duration = Output duration")
        if "no audio" in variant.lower():
            v["audio"] = "without"
            v["audio_changes_price"] = False if res == "4K" else True
        elif "audio" in variant.lower():
            v["audio"] = "with"
            v["audio_changes_price"] = False if res == "4K" else True
        if v["audio"] == "without":
            v["phrases"].append("No Native Audio")
        elif v["audio"] == "with":
            v["phrases"].append("With Native Audio")
        return v

    if plat == "Google Gemini API" and model == "veo-3-1":
        # Discontinued. The variant is "(audio)" and the pricing sentence is the with-audio price.
        if "(audio)" in variant.lower() or "with audio" in " ".join(c.get("needle") or "" for c in row.get("checks") or []).lower():
            v["audio"] = "with"
        return v

    if plat == "Google Gemini API" and model == "gemini-omni-flash":
        v["length_changes_price"] = False
        v["phrases"].append("approximately $0.10 per second")
        return v

    if plat == "Atlas Cloud":
        if "T2V" in variant or "Text-to-Video" in variant:
            v["input"] = ["t2v"]
        if model == "seedance-2-5":
            v["phrases"].append("Seedance 2.5 Text-to-Video")
        elif model == "minimax-hailuo":
            v["phrases"].append("MiniMax H3 Fast Text-to-Video")
        elif model == "gemini-omni-flash":
            v["phrases"].append("Gemini Omni 1.1 Flash Text-to-Video")
        return v

    return v


def classify(row):
    if row.get("kind") == "plan":
        return plan_variation(row)
    return api_variation(row)


def tidy_note(row):
    """Surcharges that now live in modifiers should not stay only in the note."""
    note = row.get("note") or ""
    for cut in (
        "+1 credit per image/audio reference.",
        "+1 credit per reference image.",
        "+2 credits per reference image/start frame.",
        "80-credit ($0.80) minimum per generation; input/reference video billed extra.",
    ):
        note = note.replace(cut, "")
    note = re.sub(r"\s{2,}", " ", note).strip()
    row["note"] = note

def widen_veo_4k_needle(row):
    """The 4K check is the rest of the with-audio sentence. Keep the $0.60 expectation."""
    if row.get("id") != "r067":
        return
    for chk in row.get("checks") or []:
        if chk.get("phrase"):
            continue
        if "with audio" in (chk.get("needle") or "").lower():
            continue
        if "(4k)" in (chk.get("needle") or "").lower():
            chk["needle"] = "Veo 3.1 Standard video with audio price (default) Not available {X} (720p and 1080p) ${N} (4k)"

def apply_variations(db):
    """Attach variation objects. Does not change usd_per_second."""
    headlines = []
    audio_clears = []
    for row in db["rows"]:
        before = row.get("usd_per_second")
        before_audio = row.get("audio")
        widen_veo_4k_needle(row)
        v = classify(row)
        phrases = v.pop("phrases")
        row["variation"] = v
        tidy_note(row)
        for phrase in phrases:
            add_phrase(row, phrase)
        if v["audio"] == "with":
            row["audio"] = True
        elif v["audio"] == "without":
            row["audio"] = False
        else:
            if before_audio is not None:
                audio_clears.append(row.get("id"))
            row["audio"] = None
        if row.get("usd_per_second") != before:
            headlines.append(row.get("id"))
    db["variation_schema"] = SCHEMA
    return {"headline_changes": headlines, "audio_cleared": audio_clears}


def _veo_4k_rows(db):
    if any(r.get("model") == "veo-3-1" and r.get("platform") == "fal" and r.get("resolution") == "4K" for r in db["rows"]):
        return []
    base = next(r for r in db["rows"] if r.get("id") == "r020")
    made = []
    nums = [int(r["id"][1:]) for r in db["rows"] if str(r.get("id", "")).startswith("r") and r["id"][1:].isdigit()]
    nxt = max(nums) + 1
    specs = [
        ("Standard, no audio", False, 0.40, "At 4k, you will be charged ${N} per second without audio"),
        ("Standard, with audio", True, 0.60, "without audio, or ${N} with"),
    ]
    for variant, audio, usd, needle in specs:
        row = {
            "model": "veo-3-1",
            "variant": variant,
            "platform": "fal",
            "kind": "api",
            "resolution": "4K",
            "audio": audio,
            "usd_per_second": usd,
            "status": "verified",
            "promo_until": None,
            "source": "fal_veo31",
            "math": None,
            "checks": [{"needle": needle, "expect": usd}],
            "note": "fal states the 4K rate in the same sentence as the 720p/1080p rates.",
            "id": f"r{nxt}",
            "checked": base.get("checked"),
            "source_url": base.get("source_url"),
        }
        nxt += 1
        made.append(row)
    return made


UNLISTED_RESOLUTIONS = {"", "—", "-", "–", "Pro tier", "Pro", "Standard"}

def resolution_matches(row, resolution):
    """'not listed' matches an empty or tier resolution, the same values the table shows as not listed."""
    raw = str(row.get("resolution") or "").strip()
    if str(resolution).strip().lower() == "not listed":
        return raw in UNLISTED_RESOLUTIONS
    return str(resolution).lower() in raw.lower()

def quote(row, seconds=None, audio=None, input_type=None, resolution=None):
    """Price one row for a calculator selection. None means no filter.

    status is match, unknown, not_offered, or not_stated.
    unknown keeps the row: audio or input was not stated, and nothing else contradicts the pick.
    usd_per_second is set on match and unknown. A length outside min/max is not_offered.
    """
    v = row.get("variation") or blank()
    dur = v.get("duration") or {}
    if resolution and not resolution_matches(row, resolution):
        return {"status": "not_offered", "detail": f"Resolution {resolution} is not this row."}
    unknown = False
    if audio:
        have = v.get("audio") or "not stated"
        if have == "not stated":
            unknown = True
        elif have != audio:
            return {"status": "not_offered", "detail": "This row is the other audio price."}
    if input_type:
        have = v.get("input")
        if have == "not stated" or not have:
            unknown = True
        elif input_type not in have:
            return {"status": "not_offered", "detail": "This row is a different input type."}
    usd = row["usd_per_second"]
    detail = ""
    if seconds is not None:
        lo, hi = dur.get("min_seconds"), dur.get("max_seconds")
        if (_num(lo) and seconds < lo) or (_num(hi) and seconds > hi):
            return {"status": "not_offered", "detail": "That length is outside the range on the page."}
        rates = dur.get("rate_by_length")
        if isinstance(rates, list):
            tier = next((t for t in rates if int(seconds) in [int(s) for s in t.get("seconds") or []]), None)
            if tier is None:
                return {"status": "not_stated", "detail": "The page gives a per-second rate for another length, not this one."}
            usd = tier["usd_per_second"]
            detail = tier.get("label") or ""
        elif v.get("length_changes_price") is False:
            detail = ""
        else:
            priced = dur.get("priced_seconds")
            if _num(priced) and int(seconds) == int(priced):
                detail = f"{priced:g}s"
            elif _num(priced):
                return {"status": "not_stated", "detail": f"The page prices this clip at {priced:g}s, not {int(seconds)}s."}
            else:
                return {"status": "not_stated", "detail": "The page does not state a rate for that length."}
    if unknown:
        return {"status": "unknown", "usd_per_second": usd, "detail": "not stated by vendor"}
    return {"status": "match", "usd_per_second": usd, "detail": detail}


def variation_errors(rows):
    errors = []
    for row in rows:
        v = row.get("variation")
        rid = row.get("id")
        if not isinstance(v, dict):
            errors.append(f"{rid} is missing variation")
            continue
        if v.get("audio") not in ("with", "without", "not stated"):
            errors.append(f"{rid} audio is {v.get('audio')!r}")
        inp = v.get("input")
        if inp != "not stated" and (not isinstance(inp, list) or not inp or any(x not in INPUTS for x in inp)):
            errors.append(f"{rid} input is {inp!r}")
        dur = v.get("duration")
        if not isinstance(dur, dict):
            errors.append(f"{rid} duration is missing")
            continue
        for key in ("min_seconds", "max_seconds", "allowed_seconds", "priced_seconds", "rate_by_length"):
            if key not in dur:
                errors.append(f"{rid} duration.{key} is missing")
        for key in ("audio_changes_price", "length_changes_price", "input_changes_price"):
            if v.get(key) not in (True, False, "not stated"):
                errors.append(f"{rid} {key} is {v.get(key)!r}")
        if "modifiers" not in v:
            errors.append(f"{rid} modifiers is missing")
        stated = []
        if v.get("audio") != "not stated":
            stated.append(v["audio"])
        if inp != "not stated":
            stated.append("input")
        if _num(dur.get("priced_seconds")):
            stated.append(f"{dur['priced_seconds']:g}s")
        if _num(dur.get("min_seconds")):
            stated.append(str(dur["min_seconds"]))
        if isinstance(dur.get("rate_by_length"), list):
            stated.append("rate")
        if v.get("length_changes_price") is False:
            stated.append("per second")
        needles = " ".join((c.get("needle") or "") for c in row.get("checks") or [])
        if stated and not any(c.get("phrase") or c.get("needle") for c in row.get("checks") or []):
            errors.append(f"{rid} states a fact without a check")
        if v.get("audio") == "without" and not any(w in needles.lower() for w in ("audio off", "no audio", "without audio", "no native audio")):
            errors.append(f"{rid} without-audio has no audio check")
        if v.get("audio") == "with" and not any(w in needles.lower() for w in ("audio on", "with audio", "w/audio", "native audio", "prompts with audio", "(audio)")):
            errors.append(f"{rid} with-audio has no audio check")
        for chk in row.get("checks") or []:
            if chk.get("phrase") and not (chk.get("needle") or "").strip():
                errors.append(f"{rid} has an empty phrase check")
    return errors


def verify_phrases(db, folder):
    """Return phrase checks that are not in a saved source fetch. Skips missing files."""
    missing = []
    texts = {}
    for name in os.listdir(folder):
        if name.endswith(".txt"):
            texts[name[:-4]] = open(os.path.join(folder, name), encoding="utf-8", errors="replace").read()
    for row in db["rows"]:
        src = row.get("source")
        if src not in texts:
            continue
        text = re.sub(r"\s+", " ", texts[src])
        for chk in row.get("checks") or []:
            if not chk.get("phrase"):
                continue
            words = chk["needle"].split()
            rx = r"\s+".join(re.escape(w) for w in words)
            if not re.search(rx, text):
                missing.append(f"{row.get('id')} {src}: {chk['needle']}")
    return missing
