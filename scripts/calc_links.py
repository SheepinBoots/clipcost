"""Shareable /calculator/ query parameters.

Unknown or invalid values are dropped. The calculator script applies the same rules.
"""
AUDIO = {"with": "with", "without": "without", "on": "with", "off": "without"}
INPUTS = {"t2v", "i2v", "ref2v", "v2v", "extend", "lip-sync"}


def _text(raw, key):
    value = raw.get(key)
    if value is None:
        return ""
    return str(value).strip()


def _whole(raw, *keys):
    for key in keys:
        text = _text(raw, key)
        if text.isdigit():
            return int(text)
    return None


def parse_calc_params(raw, models, plans, resolutions):
    """Return only the parameters the calculator can apply.

    raw: mapping of query names to strings.
    models: iterable of model slugs.
    plans: dict of plan id to a record with a platform name.
    resolutions: iterable of resolution labels the table can select, plus "not listed".
    """
    models = set(models)
    resolutions = {str(item) for item in resolutions}
    resolutions.add("not listed")
    by_lower = {item.lower(): item for item in resolutions}
    out = {}

    model = _text(raw, "model")
    if model in models:
        out["model"] = model

    plan = _text(raw, "plan")
    if plan in plans:
        out["plan"] = plan

    provider = (_text(raw, "provider") or _text(raw, "platform")).lower()
    if provider and "plan" not in out:
        for pid, record in plans.items():
            if (record.get("platform") or "").lower() == provider:
                out["plan"] = pid
                out["provider"] = record.get("platform") or ""
                break
    elif provider and "plan" in out:
        platform = plans[out["plan"]].get("platform") or ""
        if platform.lower() == provider:
            out["provider"] = platform

    seconds = _whole(raw, "seconds", "sec")
    if seconds is not None and seconds >= 1:
        out["seconds"] = seconds

    resolution = _text(raw, "resolution") or _text(raw, "res")
    if resolution.lower() in by_lower:
        out["resolution"] = by_lower[resolution.lower()]

    audio = _text(raw, "audio").lower()
    if audio in AUDIO:
        out["audio"] = AUDIO[audio]

    kind = _text(raw, "input").lower()
    if kind in INPUTS:
        out["input"] = kind

    used = _whole(raw, "used")
    if used is not None and 1 <= used <= 100:
        out["used"] = used
    return out
