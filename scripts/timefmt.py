"""Visible timestamps: Eastern time first, Pacific in brackets.

"Nov 16, 2026, 8:34 AM ET (5:34 AM PT)". zoneinfo handles EST/EDT and
PST/PDT; the labels stay plain "ET" and "PT". Inputs are ISO 8601 strings
with an offset (or "Z") or aware datetimes, so the instant never changes.
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
PT = ZoneInfo("America/Los_Angeles")


def _aware(when):
    if isinstance(when, str):
        when = datetime.fromisoformat(when.replace("Z", "+00:00"))
    if when.tzinfo is None:
        raise ValueError("timestamp needs a UTC offset")
    return when


def _clock(t, ampm=True):
    hour = t.strftime("%I").lstrip("0") or "12"
    return f"{hour}:{t.strftime('%M')}" + (f" {t.strftime('%p')}" if ampm else "")


def _date(t, long_month=False):
    return f"{t.strftime('%B' if long_month else '%b')} {t.day}, {t.year}"


def _span(a, b):
    if b is None:
        return _clock(a)
    same_half = a.strftime("%p") == b.strftime("%p")
    return f"{_clock(a, ampm=not same_half)}–{_clock(b)}"


def et_pt(start, end=None, long_month=False):
    """'Nov 17, 2026, 9:49–9:57 AM ET (6:49–6:57 AM PT)' for an instant or a same-day range."""
    s = _aware(start)
    e = _aware(end) if end is not None else None
    se, ee = s.astimezone(ET), (e.astimezone(ET) if e else None)
    sp, ep = s.astimezone(PT), (e.astimezone(PT) if e else None)
    pt = _span(sp, ep)
    if sp.date() != se.date():
        pt = f"{_date(sp, long_month)}, {pt}"
    return f"{_date(se, long_month)}, {_span(se, ee)} ET ({pt} PT)"


def et_clock(when):
    """'7:00 PM ET (4:00 PM PT)' without the date."""
    t = _aware(when)
    return f"{_clock(t.astimezone(ET))} ET ({_clock(t.astimezone(PT))} PT)"


def now_utc_iso():
    """The current instant as ISO 8601 UTC with a Z, e.g. '2026-11-20T21:26:29Z'. For stored run stamps."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def us_today():
    """Today's date in US Pacific time, whatever time zone the machine (or CI runner) uses."""
    return datetime.now(PT).date()


def run_instant(run, now=None):
    """An aware datetime for a price-check run stamp, or None when it cannot be placed safely.

    A stamp with an offset or Z is exact. An old stamp without one was written in box-local Pacific
    time by a manual run, or in UTC by a CI runner: read it as Pacific unless that lands in the future,
    then as UTC. A stamp that is still in the future either way is never shown (None).
    """
    if not run:
        return None
    now = now or datetime.now(timezone.utc)
    try:
        t = datetime.fromisoformat(str(run).replace("Z", "+00:00"))
    except ValueError:
        return None
    if t.tzinfo is not None:
        return t if t <= now else None
    for tz in (PT, timezone.utc):
        cand = t.replace(tzinfo=tz)
        if cand <= now:
            return cand
    return None


_MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def utc_clock(hour, minute=0, on=None):
    """A fixed UTC wall time (e.g. a cron at 15:17 UTC) as '10:17 AM ET (7:17 AM PT)' on the date `on`
    (default: today in US Pacific). The ET and PT clocks follow daylight saving for that date."""
    import datetime as _dt
    day = on or us_today()
    t = _dt.datetime(day.year, day.month, day.day, hour, minute, tzinfo=timezone.utc)
    return et_clock(t)


def utc_span(h1, h2, on=None):
    """A UTC hour range such as Google's '2–5 pm UTC' as '9 AM–12 PM ET (6–9 AM PT)' on the date `on`."""
    import datetime as _dt
    day = on or us_today()
    a = _dt.datetime(day.year, day.month, day.day, h1, tzinfo=timezone.utc)
    b = _dt.datetime(day.year, day.month, day.day, h2, tzinfo=timezone.utc)

    def hr(t):
        return (t.strftime("%I").lstrip("0") or "12") + (t.strftime(":%M") if t.minute else "") + " " + t.strftime("%p")

    def span(x, y):
        if x.strftime("%p") == y.strftime("%p"):
            return hr(x).rsplit(" ", 1)[0] + "–" + hr(y)
        return hr(x) + "–" + hr(y)
    return f"{span(a.astimezone(ET), b.astimezone(ET))} ET ({span(a.astimezone(PT), b.astimezone(PT))} PT)"


def day_label(date):
    """A date-only label ('2026-11-23' -> 'Nov 23, 2026'). Dates carry no clock, so no zone is attached."""
    if not date:
        return "date not stated"
    parts = str(date).split("-")
    try:
        return f"{_MONTHS[int(parts[1]) - 1]} {int(parts[2])}, {parts[0]}"
    except (ValueError, IndexError):
        return str(date)


def normalize_utc_mentions(text, year=None):
    """Rewrite our own 'Nov 15 00:00 UTC (Nov 14, 4 pm PT)' style mentions as ET first with PT in brackets.

    Only the UTC-first clock pattern is rewritten; quoted vendor text keeps its own words elsewhere."""
    import re as _re
    import datetime as _dt
    if not text or "UTC" not in text:
        return text
    pat = _re.compile(r"\b(" + "|".join(_MONTHS) + r")[a-z]* (\d{1,2})(?:, (\d{4}))? (\d{1,2}):(\d{2}) UTC(?: \([^)]*\))?")

    def sub(m):
        y = int(m.group(3) or year or us_today().year)
        t = _dt.datetime(y, _MONTHS.index(m.group(1)[:3]) + 1, int(m.group(2)), int(m.group(4)), int(m.group(5)), tzinfo=timezone.utc)
        return et_pt(t)
    return pat.sub(sub, text)
