"""ET-first timestamp formatter: EST and EDT, PT in brackets, no Caracas."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from timefmt import et_clock, et_pt  # noqa: E402

CASES = [
    # EST / PST (November)
    (("2026-11-16T09:34:00-04:00",), {}, "Nov 16, 2026, 8:34 AM ET (5:34 AM PT)"),
    (("2026-11-17T10:49:00-04:00", "2026-11-17T10:57:00-04:00"), {}, "Nov 17, 2026, 9:49–9:57 AM ET (6:49–6:57 AM PT)"),
    (("2026-11-17T16:50:00-04:00", "2026-11-17T16:53:00-04:00"), {}, "Nov 17, 2026, 3:50–3:53 PM ET (12:50–12:53 PM PT)"),
    (("2026-11-20T00:00:00Z",), {"long_month": True}, "November 19, 2026, 7:00 PM ET (4:00 PM PT)"),
    # EDT / PDT (July)
    (("2026-07-01T12:00:00Z",), {}, "Jul 1, 2026, 8:00 AM ET (5:00 AM PT)"),
    # ET and PT on different days
    (("2026-11-18T04:30:00Z",), {}, "Nov 17, 2026, 11:30 PM ET (8:30 PM PT)"),
    (("2026-11-18T06:30:00Z",), {}, "Nov 18, 2026, 1:30 AM ET (Nov 17, 2026, 10:30 PM PT)"),
]
errors = []
for args, kw, want in CASES:
    got = et_pt(*args, **kw)
    if got != want:
        errors.append(f"{args}: {got!r} != {want!r}")
    if "Caracas" in got:
        errors.append(f"{args}: names Caracas")
# Mar 8, 2026, 08:00 UTC: ET is already on EDT, PT is still on PST.
if et_clock("2026-03-08T08:00:00Z") != "4:00 AM ET (12:00 AM PT)":
    errors.append("DST edge: " + et_clock("2026-03-08T08:00:00Z"))
try:
    et_pt("2026-11-16T09:34:00")
    errors.append("naive timestamp accepted")
except ValueError:
    pass
if errors:
    print("timefmt:\n- " + "\n- ".join(errors))
    raise SystemExit(1)
print("ok timefmt")

# The built site and the deal notes never name Caracas.
ROOT = Path(__file__).resolve().parent.parent
hits = [str(p.relative_to(ROOT)) for p in (ROOT / "dist").rglob("*") if p.is_file() and p.suffix in (".html", ".txt", ".xml", ".json") and "Caracas" in p.read_text(errors="ignore")]
if "Caracas" in (ROOT / "data" / "deals.json").read_text():
    hits.append("data/deals.json")
if hits:
    print("Caracas still in: " + ", ".join(sorted(hits)[:10]))
    raise SystemExit(1)
print("ok no Caracas in dist or deal notes")
