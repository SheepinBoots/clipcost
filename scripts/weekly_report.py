#!/usr/bin/env python3
"""Weekly AI-video price reports.

The durable log is data/price_changes.jsonl (schema version 1). Each line is
one JSON object. A later monthly roundup can group lines by calendar month of
`date` without another data source. This module does not build that page.

Kinds:
  price          A verified dollars-per-second change. Only these count toward
                 the two-change minimum. Fields: model, platform, plan_tier,
                 resolution, audio (on/off/not listed), old_usd_per_second,
                 new_usd_per_second, source_url, date (the date checked).
  promo_started  A promo the repo recorded as newly started.
  promo_ended    A promo the repo recorded as ended.
  added          A model or platform added after the baseline.
  note           Backfill notes. Ignored by reports.

Publication:
  A report covers one ISO week, Monday through that Friday (the week to date
  when the Friday job runs). It is published only when at least two real price
  changes fall in that window, including changes rolled forward from weeks
  that did not qualify. Saturday and Sunday changes stay out of Friday's
  report and wait for the next one. Weeks that do not qualify are not given
  a page.

  python3 scripts/weekly_report.py --status
  python3 scripts/weekly_report.py --status --as-of 2026-10-30
"""
import datetime
import json
import os
import sys
from decimal import Decimal, ROUND_HALF_UP

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "price_changes.jsonl")
SCHEMA = 1
MIN_CHANGES = 2
TIER_RESOLUTIONS = {"Pro tier", "Pro", "Standard"}
MISSING_RESOLUTIONS = {"", "—", "-", "–"}
PRICE_KINDS = {"price"}
CATALOG_KINDS = {"promo_started", "promo_ended", "added"}
INDEX_H1 = "AI video price change reports"
INDEX_DESCRIPTION = (
    "Friday reports of AI video price changes for each ISO week. "
    "A week is published when VidFare has checked at least two real price changes. "
    "A week with fewer changes is skipped, and those changes are included in the next report that reaches two."
)


def format_usd(v):
    """Same rounding as the price tables: up to 5 decimals, half up, at least 2."""
    n = int((Decimal(str(v)) * Decimal(100000)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    neg = n < 0
    n = abs(n)
    whole, frac = divmod(n, 100000)
    digits = f"{frac:05d}".rstrip("0")
    if len(digits) < 2:
        digits = f"{frac:05d}"[:2]
    return f"{'-' if neg else ''}${whole}.{digits}"


def format_pct(old, new):
    """Percent change from old $/sec to new. None when the old rate is 0."""
    old_d = Decimal(str(old))
    new_d = Decimal(str(new))
    if old_d == 0:
        return None
    pct = ((new_d - old_d) / abs(old_d) * Decimal(100)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    if pct == pct.to_integral():
        return f"{int(pct):+}%"
    return f"{pct:+.1f}%"


def long_date(value):
    if isinstance(value, str):
        value = datetime.date.fromisoformat(value)
    return f"{value.strftime('%b')} {value.day}, {value.year}"


def parse_date(value):
    if isinstance(value, datetime.date):
        return value
    return datetime.date.fromisoformat(value)


def week_id(year, week):
    return f"{year}-w{week:02d}"


def week_bounds(day):
    """Monday and Friday of the ISO week that contains day."""
    year, week, _ = parse_date(day).isocalendar()
    monday = datetime.date.fromisocalendar(year, week, 1)
    friday = datetime.date.fromisocalendar(year, week, 5)
    return monday, friday


def plan_tier(row):
    name = (row.get("plan_name") or "").strip()
    if name:
        return name
    res = str(row.get("resolution") or "").strip()
    if res in TIER_RESOLUTIONS:
        return res
    return "not listed"


def resolution_label(row):
    res = str(row.get("resolution") or "").strip()
    if res in MISSING_RESOLUTIONS or res in TIER_RESOLUTIONS:
        return "not listed"
    return res


def audio_label(row):
    if row.get("audio") is True:
        return "on"
    if row.get("audio") is False:
        return "off"
    return "not listed"


def _num_token(value):
    return format(Decimal(str(value)).normalize(), "f")


def load(path=None):
    path = path or PATH
    if not os.path.exists(path):
        return []
    events = []
    with open(path, encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, 1):
            text = line.strip()
            if not text:
                continue
            try:
                event = json.loads(text)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{lineno}: invalid JSON ({exc})") from exc
            if not isinstance(event, dict) or "kind" not in event or "id" not in event:
                raise SystemExit(f"{path}:{lineno}: each line needs kind and id")
            events.append(event)
    return events


def append_event(event, path=None):
    """Append one event. Returns False when that id is already in the file."""
    path = path or PATH
    if event.get("v") != SCHEMA or not event.get("id") or not event.get("kind"):
        raise SystemExit("price log event needs v, id, and kind")
    existing = load(path) if os.path.exists(path) else []
    if any(item.get("id") == event["id"] for item in existing):
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return True


def price_record(db, row, old_usd, new_usd, date):
    """One verified $/sec change. `date` is the date the rate was checked."""
    model = row.get("model")
    name = ((db.get("models") or {}).get(model) or {}).get("name") or model or ""
    old_token = _num_token(old_usd)
    new_token = _num_token(new_usd)
    return {
        "v": SCHEMA,
        "kind": "price",
        "id": f"price:{date}:{row.get('id')}:{old_token}:{new_token}",
        "date": date,
        "model": model,
        "model_name": name,
        "platform": row.get("platform"),
        "plan_tier": plan_tier(row),
        "resolution": resolution_label(row),
        "audio": audio_label(row),
        "variant": row.get("variant"),
        "old_usd_per_second": float(Decimal(old_token)),
        "new_usd_per_second": float(Decimal(new_token)),
        "source_url": row.get("source_url"),
        "row_id": row.get("id"),
    }


def promo_ended_row(row, today):
    return {
        "v": SCHEMA,
        "kind": "promo_ended",
        "id": f"promo_ended:row:{row.get('id')}:{row.get('promo_until')}",
        "date": today,
        "checked": today,
        "ended": row.get("promo_until"),
        "end_is_estimate": False,
        "title": f"{row.get('variant') or row.get('id')} promo",
        "vendor": row.get("platform"),
        "platform": row.get("platform"),
        "model": row.get("model"),
        "source_url": row.get("source_url"),
        "row_id": row.get("id"),
    }


def promo_ended_deal(deal, today):
    return {
        "v": SCHEMA,
        "kind": "promo_ended",
        "id": f"promo_ended:deal:{deal.get('id')}:{deal.get('end')}",
        "date": today,
        "checked": today,
        "ended": deal.get("end"),
        "end_is_estimate": bool(deal.get("end_is_estimate")),
        "title": deal.get("title") or deal.get("id"),
        "vendor": deal.get("vendor"),
        "source_url": deal.get("source_url") or deal.get("link_url"),
        "deal_id": deal.get("id"),
    }


def prices(events):
    return [event for event in events if event.get("kind") == "price"]


def assign(events, as_of):
    """Published reports and price changes still waiting, as of a calendar date.

    A week closes on its Friday. The report includes price changes dated
    Monday through Friday, plus any still-waiting changes from earlier dates.
    """
    as_of = parse_date(as_of)
    pending = []
    consumed = set()
    reports = []
    ordered = sorted(prices(events), key=lambda event: (event.get("date") or "", event.get("id") or ""))
    if ordered:
        cursor, _friday = week_bounds(ordered[0]["date"])
        while True:
            monday, friday = week_bounds(cursor)
            if friday > as_of:
                break
            fresh = []
            for event in ordered:
                if event["id"] in consumed:
                    continue
                day = parse_date(event["date"])
                if monday <= day <= friday and event not in pending:
                    fresh.append(event)
            chosen = list(pending) + fresh
            if len(chosen) >= MIN_CHANGES:
                rolled = {}
                for event in pending:
                    year, week, _ = parse_date(event["date"]).isocalendar()
                    key = (year, week)
                    rolled[key] = rolled.get(key, 0) + 1
                year, week, _ = monday.isocalendar()
                reports.append({
                    "id": week_id(year, week),
                    "iso_year": year,
                    "iso_week": week,
                    "week_start": monday.isoformat(),
                    "through": friday.isoformat(),
                    "changes": chosen,
                    "rolled_from": [
                        {
                            "iso_year": rolled_year,
                            "iso_week": rolled_week,
                            "week_start": datetime.date.fromisocalendar(rolled_year, rolled_week, 1).isoformat(),
                            "count": count,
                        }
                        for (rolled_year, rolled_week), count in sorted(rolled.items())
                        if (rolled_year, rolled_week) != (year, week)
                    ],
                })
                consumed.update(event["id"] for event in chosen)
                pending = []
            else:
                pending = chosen
            weekend = []
            for event in ordered:
                if event["id"] in consumed:
                    continue
                day = parse_date(event["date"])
                if friday < day <= min(friday + datetime.timedelta(days=2), as_of):
                    weekend.append(event)
            pending_ids = {event["id"] for event in pending}
            for event in weekend:
                if event["id"] not in pending_ids:
                    pending.append(event)
                    pending_ids.add(event["id"])
            cursor = monday + datetime.timedelta(days=7)
    pending_ids = {event["id"] for event in pending}
    for event in ordered:
        if event["id"] in consumed or event["id"] in pending_ids:
            continue
        if parse_date(event["date"]) <= as_of:
            pending.append(event)
    pending.sort(key=lambda event: (event.get("date") or "", event.get("id") or ""))
    return {"as_of": as_of.isoformat(), "reports": reports, "pending": pending}


def catalog_for(events, through, prior_through=None):
    """Catalog events not yet shown on an earlier published report."""
    chosen = {"added": [], "promo_started": [], "promo_ended": []}
    for event in events:
        kind = event.get("kind")
        if kind not in CATALOG_KINDS or not event.get("date"):
            continue
        day = event["date"]
        if day > through:
            continue
        if prior_through and day <= prior_through:
            continue
        chosen[kind].append(event)
    for kind in chosen:
        chosen[kind].sort(key=lambda event: (event.get("date") or "", event.get("id") or ""))
    return chosen


def report_h1(report):
    return f"AI video price changes, week of {long_date(report['week_start'])}"


def report_description(report):
    count = len(report["changes"])
    noun = "price change" if count == 1 else "price changes"
    return (
        f"{count} real {noun} checked for the week of {long_date(report['week_start'])} "
        f"({long_date(report['week_start'])} through {long_date(report['through'])})."
    )


def report_paragraphs(report):
    paragraphs = []
    if report.get("rolled_from"):
        parts = [
            f"{item['count']} from the week of {long_date(item['week_start'])}"
            for item in report["rolled_from"]
        ]
        paragraphs.append(
            "This report also includes changes from earlier weeks that had fewer than 2 price changes: "
            + "; ".join(parts) + "."
        )
    paragraphs.append(
        "Before and after are dollars per second of finished video. "
        "The percent is the change from the old rate to the new rate. "
        "The source link is the vendor page the rate was checked against."
    )
    return paragraphs


def index_paragraphs(result, events):
    as_of = parse_date(result["as_of"])
    monday, friday = week_bounds(as_of)
    waiting = len(result["pending"])
    published = {report["id"] for report in result["reports"]}
    year, week, _ = as_of.isocalendar()
    this_id = week_id(year, week)
    paragraphs = []
    if as_of < friday:
        earlier = sum(1 for event in result["pending"] if (event.get("date") or "") < monday.isoformat())
        rolled = f" {earlier} of those are from an earlier week." if earlier else ""
        paragraphs.append(
            f"The week of {long_date(monday)} closes on Friday {long_date(friday)}. "
            f"It is not published before then. Price changes recorded so far: {waiting}.{rolled}"
        )
    elif this_id not in published:
        if waiting == 0:
            waiting_text = "No price change is recorded for it."
        elif waiting == 1:
            waiting_text = "1 price change is still waiting."
        else:
            waiting_text = f"{waiting} price changes are still waiting."
        paragraphs.append(
            f"The week of {long_date(monday)} (through {long_date(friday)}) is not published. "
            f"{waiting_text} A report needs at least {MIN_CHANGES} price changes."
        )
    else:
        noun = "report" if len(result["reports"]) == 1 else "reports"
        paragraphs.append(
            f"{len(result['reports'])} weekly {noun} published through {long_date(as_of)}. "
            f"Price changes still waiting: {waiting}."
        )
    promos = sum(1 for event in events if event.get("kind") in ("promo_started", "promo_ended"))
    added = sum(1 for event in events if event.get("kind") == "added")
    paragraphs.append(
        f"Promo starts and ends recorded: {promos}. New models or platforms recorded: {added}. "
        "Neither counts toward the two-change minimum."
    )
    return paragraphs


def _escape(text):
    return (str(text if text is not None else "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def _link(url, link_fn):
    if not url:
        return ""
    if link_fn:
        href, rel = link_fn(url)
    else:
        href, rel = url, "nofollow noopener"
    return f'<a href="{_escape(href)}" rel="{_escape(rel)}" target="_blank">source</a>'


def _promo_sentence(event):
    title = event.get("title") or event.get("deal_id") or event.get("id")
    vendor = event.get("vendor")
    sentence = f"{title}, {vendor}." if vendor else f"{title}."
    bits = []
    if event.get("started"):
        bits.append(f"Started {long_date(event['started'])}")
    if event.get("ended"):
        estimate = " (estimated)" if event.get("end_is_estimate") else ""
        bits.append(f"Ended {long_date(event['ended'])}{estimate}")
    bits.append(f"Checked {long_date(event.get('checked') or event['date'])}")
    return sentence + " " + ". ".join(bits) + "."


def _added_sentence(event):
    name = event.get("model_name") or event.get("model") or event.get("title") or "New row"
    where = event.get("platform") or ""
    what = event.get("what") or "row"
    sentence = f"{name} on {where}." if where else f"{name}."
    return f"{sentence} New {what}. Checked {long_date(event.get('checked') or event['date'])}."


def _section_note(items, week_start):
    if any((item.get("date") or "") < week_start for item in items):
        return "<p>Recorded on the dates below. Some are from earlier weeks that were not published on their own.</p>"
    return ""


def _event_list(items, sentence_fn, link_fn):
    rows = []
    for event in items:
        source = _link(event.get("source_url"), link_fn)
        source_html = f" {source}" if source else ""
        rows.append(
            f'<li><span class="pill">{_escape(event.get("date") or "")}</span> '
            f"{_escape(sentence_fn(event))}{source_html}</li>"
        )
    return '<ul class="log" style="padding-left:0;list-style:none">' + "".join(rows) + "</ul>"


def render_change_table(changes, link_fn=None):
    rows = []
    ordered = sorted(changes, key=lambda event: (
        event.get("date") or "",
        event.get("model_name") or "",
        event.get("platform") or "",
        event.get("resolution") or "",
        event.get("id") or "",
    ))
    for event in ordered:
        pct = format_pct(event.get("old_usd_per_second"), event.get("new_usd_per_second"))
        pct_text = pct if pct is not None else "n/a"
        variant = event.get("variant") or ""
        variant_html = f'<div class="small">{_escape(variant)}</div>' if variant else ""
        platform = event.get("platform") or ""
        source = _link(event.get("source_url"), link_fn)
        rows.append(
            "<tr>"
            f"<td>{_escape(event.get('model_name') or event.get('model') or '')}{variant_html}</td>"
            f"<td>{_escape(platform)}</td>"
            f"<td>{_escape(event.get('plan_tier') or 'not listed')}</td>"
            f"<td>{_escape(event.get('resolution') or 'not listed')}</td>"
            f"<td>{_escape(event.get('audio') or 'not listed')}</td>"
            f"<td class=\"num\">{_escape(format_usd(event.get('old_usd_per_second')))}</td>"
            f"<td class=\"num\">{_escape(format_usd(event.get('new_usd_per_second')))}</td>"
            f"<td class=\"num\">{_escape(pct_text)}</td>"
            f"<td>{_escape(event.get('date') or '')}</td>"
            f"<td class=\"small\">{source}</td>"
            "</tr>"
        )
    head = (
        "<thead><tr>"
        "<th>Model</th><th>Where</th><th>Plan tier</th><th>Resolution</th><th>Audio</th>"
        "<th>Before</th><th>After</th><th>Change</th><th>Checked</th><th>Source</th>"
        "</tr></thead>"
    )
    return f'<div class="tblwrap"><table>{head}<tbody>{"".join(rows)}</tbody></table></div>'


def render_report_body(report, events, prior_through=None, link_fn=None):
    catalog = catalog_for(events, report["through"], prior_through)
    parts = [
        f"<h1>{_escape(report_h1(report))}</h1>",
        f'<p class="lead">{_escape(report_description(report))}</p>',
    ]
    for paragraph in report_paragraphs(report):
        parts.append(f"<p>{_escape(paragraph)}</p>")
    parts.append("<h2>Price changes</h2>")
    parts.append(render_change_table(report["changes"], link_fn))
    if catalog["added"]:
        parts.append("<h2>New models and platforms</h2>")
        parts.append(_section_note(catalog["added"], report["week_start"]))
        parts.append(_event_list(catalog["added"], _added_sentence, link_fn))
    if catalog["promo_started"]:
        parts.append("<h2>Promos started</h2>")
        parts.append(_section_note(catalog["promo_started"], report["week_start"]))
        parts.append(_event_list(catalog["promo_started"], _promo_sentence, link_fn))
    if catalog["promo_ended"]:
        parts.append("<h2>Promos ended</h2>")
        parts.append(_section_note(catalog["promo_ended"], report["week_start"]))
        parts.append(_event_list(catalog["promo_ended"], _promo_sentence, link_fn))
    return "".join(parts)


def render_index_body(result, events, href_fn=None, public_log=False):
    parts = [
        f"<h1>{_escape(INDEX_H1)}</h1>",
        f'<p class="lead">{_escape(INDEX_DESCRIPTION)}</p>',
    ]
    for paragraph in index_paragraphs(result, events):
        parts.append(f"<p>{_escape(paragraph)}</p>")
    if public_log:
        log_href = "/data/price_changes.jsonl"
        if href_fn:
            log_href = href_fn(log_href)
        parts.append(
            f'<p class="small">Change log: <a href="{_escape(log_href)}">price_changes.jsonl</a>.</p>'
        )
    if result["reports"]:
        items = []
        for report in result["reports"]:
            title = report_h1(report)
            note = report_description(report)
            href = f"/reports/{report['id']}/"
            if href_fn:
                href = href_fn(href)
            items.append(
                f'<li><a href="{_escape(href)}">{_escape(title)}</a> '
                f'<span class="small">{_escape(note)}</span></li>'
            )
        parts.append('<ul class="log" style="padding-left:18px">' + "".join(items) + "</ul>")
    return "".join(parts)


def index_jsonld(canonical):
    return {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": INDEX_H1,
        "headline": INDEX_H1,
        "description": INDEX_DESCRIPTION,
        "url": canonical,
    }


def report_jsonld(report, canonical):
    headline = report_h1(report)
    description = report_description(report)
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": headline,
        "name": headline,
        "description": description,
        "datePublished": report["through"],
        "dateModified": report["through"],
        "url": canonical,
        "mainEntityOfPage": canonical,
        "author": {"@type": "Organization", "name": "VidFare"},
        "publisher": {"@type": "Organization", "name": "VidFare"},
    }


def status_payload(as_of=None, path=None):
    as_of = parse_date(as_of) if as_of else datetime.date.today()
    events = load(path)
    result = assign(events, as_of)
    monday, friday = week_bounds(as_of)
    return {
        "as_of": as_of.isoformat(),
        "weekday": as_of.strftime("%A"),
        "closes_week_today": as_of == friday,
        "week_id": week_id(*as_of.isocalendar()[:2]),
        "week_start": monday.isoformat(),
        "week_through": friday.isoformat(),
        "price_changes": len(prices(events)),
        "pending": len(result["pending"]),
        "published": [report["id"] for report in result["reports"]],
        "minimum": MIN_CHANGES,
        "reports_enabled_gate": "scripts/build_site.py REPORTS_ENABLED",
    }


def main():
    as_of = None
    args = sys.argv[1:]
    if "--as-of" in args:
        as_of = args[args.index("--as-of") + 1]
    if "--status" in args or len(args) == 0:
        print(json.dumps(status_payload(as_of), indent=2))
        return 0
    print("Use --status [--as-of YYYY-MM-DD], or scripts/preview_report.py to render HTML.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
