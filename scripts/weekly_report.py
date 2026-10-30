#!/usr/bin/env python3
"""Weekly AI-video price reports.

The durable log is data/price_changes.jsonl (schema version 1). Each line is
one JSON object. A later monthly roundup can group lines by calendar month of
`date` without another data source. This module does not build that page.

Kinds:
  price          A verified dollars-per-second change. Counts toward the
                 two-change minimum. Fields: model, platform, plan_tier,
                 resolution, audio (on/off/not listed), old_usd_per_second,
                 new_usd_per_second, source_url, date (the date checked).
  promo_started  A promo the repo recorded as newly started. Counts.
  promo_ended    A promo the repo recorded as ended. Counts.
  added          A model or platform added after the baseline. Does not count.
  note           Backfill notes. Ignored by reports.

Publication:
  A report closes on Friday and covers the ISO week to date (Monday through
  that Friday), plus verified changes rolled forward from weeks that did not
  qualify. Per-second price changes, promo starts, and promo ends all count
  toward the minimum of two. The first report is the week of 2026-10-26
  (Friday 2026-10-30). Nothing is published before that Friday, so the first
  edition includes changes recorded since the 2026-10-20 baseline. The page
  states that covered range. Later reports start the day after the previous
  report's Friday. Saturday and Sunday after a published Friday wait for the
  next one. Weeks that do not qualify are not given a page.

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
# Tracker baseline in data/changes.json. The first report starts here.
BASELINE = datetime.date(2026, 10, 20)
# First Friday a weekly report may be published. Earlier weeks roll forward.
FIRST_REPORT_FRIDAY = datetime.date(2026, 10, 30)
TIER_RESOLUTIONS = {"Pro tier", "Pro", "Standard"}
MISSING_RESOLUTIONS = {"", "—", "-", "–"}
COUNT_KINDS = {"price", "promo_started", "promo_ended"}
CATALOG_KINDS = {"promo_started", "promo_ended", "added"}
INDEX_H1 = "AI video price change reports"
INDEX_DESCRIPTION = (
    "Friday reports of AI video price changes and promo starts and ends for each ISO week. "
    "A week is published when VidFare has checked at least two of those changes. "
    "A week with fewer changes is skipped, and those changes are included in the next report that reaches two."
)
NO_PRICE_NOTE = "No per-second price changes this week"


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


def countable(events):
    """Price changes and verified promo starts and ends on or after the baseline."""
    chosen = []
    for event in events:
        if event.get("kind") not in COUNT_KINDS or not event.get("date"):
            continue
        if parse_date(event["date"]) < BASELINE:
            continue
        chosen.append(event)
    return chosen


def _rolled_from(pending, year, week):
    rolled = {}
    for event in pending:
        rolled_year, rolled_week, _ = parse_date(event["date"]).isocalendar()
        key = (rolled_year, rolled_week)
        rolled[key] = rolled.get(key, 0) + 1
    return [
        {
            "iso_year": rolled_year,
            "iso_week": rolled_week,
            "week_start": datetime.date.fromisocalendar(rolled_year, rolled_week, 1).isoformat(),
            "count": count,
        }
        for (rolled_year, rolled_week), count in sorted(rolled.items())
        if (rolled_year, rolled_week) != (year, week)
    ]


def assign(events, as_of):
    """Published reports and countable changes still waiting, as of a calendar date.

    A week closes on its Friday. The report includes countable changes dated
    Monday through Friday, plus any still-waiting changes from earlier dates.
    No week is published before FIRST_REPORT_FRIDAY. Those changes roll into
    the first report, whose covered range starts at the baseline.
    """
    as_of = parse_date(as_of)
    pending = []
    consumed = set()
    reports = []
    ordered = sorted(countable(events), key=lambda event: (event.get("date") or "", event.get("id") or ""))
    if ordered:
        cursor, _friday = week_bounds(ordered[0]["date"])
        prior_through = None
        while True:
            monday, friday = week_bounds(cursor)
            if friday > as_of:
                break
            fresh = []
            for event in ordered:
                if event["id"] in consumed or event in pending:
                    continue
                day = parse_date(event["date"])
                if monday <= day <= friday:
                    fresh.append(event)
            chosen = list(pending) + fresh
            if len(chosen) >= MIN_CHANGES and friday >= FIRST_REPORT_FRIDAY:
                year, week, _ = monday.isocalendar()
                covered_from = BASELINE if prior_through is None else prior_through + datetime.timedelta(days=1)
                earliest = min(parse_date(event["date"]) for event in chosen)
                if earliest < covered_from:
                    covered_from = earliest
                reports.append({
                    "id": week_id(year, week),
                    "iso_year": year,
                    "iso_week": week,
                    "week_start": monday.isoformat(),
                    "through": friday.isoformat(),
                    "covered_from": covered_from.isoformat(),
                    "covered_through": friday.isoformat(),
                    "first": prior_through is None,
                    "changes": chosen,
                    "rolled_from": _rolled_from(pending, year, week),
                })
                consumed.update(event["id"] for event in chosen)
                pending = []
                prior_through = friday
            else:
                pending = chosen
            weekend_end = min(friday + datetime.timedelta(days=2), as_of)
            pending_ids = {event["id"] for event in pending}
            for event in ordered:
                if event["id"] in consumed or event["id"] in pending_ids:
                    continue
                day = parse_date(event["date"])
                if friday < day <= weekend_end:
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


def range_phrase(start, end):
    """'Oct 20 to Oct 30, 2026'. The month is repeated so the span cannot be misread."""
    start = parse_date(start)
    end = parse_date(end)
    if start.year == end.year:
        return f"{start.strftime('%b')} {start.day} to {end.strftime('%b')} {end.day}, {end.year}"
    return f"{long_date(start)} to {long_date(end)}"


def change_counts(report):
    changes = report.get("changes") or []
    return {
        "price": sum(1 for event in changes if event.get("kind") == "price"),
        "promo_started": sum(1 for event in changes if event.get("kind") == "promo_started"),
        "promo_ended": sum(1 for event in changes if event.get("kind") == "promo_ended"),
    }


def report_description(report):
    counts = change_counts(report)
    sentence = (
        f"This report covers {range_phrase(report['covered_from'], report['covered_through'])}. "
        f"Counted changes: {counts['price']} per-second price changes, "
        f"{counts['promo_started']} promos started, and {counts['promo_ended']} promos ended."
    )
    if report.get("first"):
        sentence += (
            " No earlier weekly report was published, so this first edition includes verified "
            f"changes recorded since the {long_date(BASELINE)} baseline."
        )
    return sentence


def report_paragraphs(report):
    paragraphs = []
    if change_counts(report)["price"]:
        paragraphs.append(
            "Before and after are dollars per second of finished video. "
            "The percent is the change from the old rate to the new rate. "
            "The source link is the vendor page the rate was checked against."
        )
    paragraphs.append(
        "Each promo line links to the vendor page or post it was checked against, "
        "with the date checked and the start or end date when the vendor gave one."
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
            f"It is not published before then. Qualifying changes recorded so far: {waiting}.{rolled}"
        )
    elif this_id not in published:
        if waiting == 0:
            waiting_text = "No qualifying change is recorded for it."
        elif waiting == 1:
            waiting_text = "1 qualifying change is still waiting."
        else:
            waiting_text = f"{waiting} qualifying changes are still waiting."
        paragraphs.append(
            f"The week of {long_date(monday)} (through {long_date(friday)}) is not published. "
            f"{waiting_text} A report needs at least {MIN_CHANGES} changes."
        )
    else:
        noun = "report" if len(result["reports"]) == 1 else "reports"
        paragraphs.append(
            f"{len(result['reports'])} weekly {noun} published through {long_date(as_of)}. "
            f"Qualifying changes still waiting: {waiting}."
        )
    added = sum(1 for event in events if event.get("kind") == "added")
    paragraphs.append(
        "Per-second price changes, promo starts, and promo ends count toward the two-change minimum. "
        f"New models or platforms recorded: {added}. Those do not count."
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


def _of_kind(report, kind):
    rows = [event for event in report.get("changes") or [] if event.get("kind") == kind]
    rows.sort(key=lambda event: (event.get("date") or "", event.get("id") or ""))
    return rows


def render_report_body(report, events, prior_through=None, link_fn=None):
    catalog = catalog_for(events, report["through"], prior_through)
    # Promo sections list only the changes assigned to this report.
    started = _of_kind(report, "promo_started")
    ended = _of_kind(report, "promo_ended")
    price_rows = _of_kind(report, "price")
    parts = [
        f"<h1>{_escape(report_h1(report))}</h1>",
        f'<p class="lead">{_escape(report_description(report))}</p>',
    ]
    for paragraph in report_paragraphs(report):
        parts.append(f"<p>{_escape(paragraph)}</p>")
    parts.append("<h2>Price changes</h2>")
    if price_rows:
        parts.append(render_change_table(price_rows, link_fn))
    else:
        parts.append(f"<p>{_escape(NO_PRICE_NOTE)}</p>")
    if catalog["added"]:
        parts.append("<h2>New models and platforms</h2>")
        parts.append(_section_note(catalog["added"], report["week_start"]))
        parts.append(_event_list(catalog["added"], _added_sentence, link_fn))
    parts.append("<h2>Promos started</h2>")
    if started:
        parts.append(_section_note(started, report["week_start"]))
        parts.append(_event_list(started, _promo_sentence, link_fn))
    else:
        parts.append("<p>No promo started in this span.</p>")
    parts.append("<h2>Promos ended</h2>")
    if ended:
        parts.append(_section_note(ended, report["week_start"]))
        parts.append(_event_list(ended, _promo_sentence, link_fn))
    else:
        parts.append("<p>No promo ended in this span.</p>")
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
