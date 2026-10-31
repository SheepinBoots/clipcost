#!/usr/bin/env python3
"""Week assignment, the price log, and report HTML."""
import datetime
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import weekly_report as wr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def price(date, row, old, new, model="Wan 3.0"):
    return {
        "v": 1,
        "kind": "price",
        "id": f"price:{date}:{row}:{old}:{new}",
        "date": date,
        "model": "wan-3-0",
        "model_name": model,
        "platform": "fal",
        "plan_tier": "not listed",
        "resolution": "720p",
        "audio": "off",
        "variant": "Text to video",
        "old_usd_per_second": old,
        "new_usd_per_second": new,
        "source_url": "https://example.com/pricing",
        "row_id": row,
    }


def main():
    assert wr.format_usd(0.0272) == "$0.0272"
    assert wr.format_usd(0.08) == "$0.08"
    assert wr.format_usd(0.1) == "$0.10"
    assert wr.format_usd(1) == "$1.00"
    assert wr.format_pct(0.05, 0.08) == "+60%"
    assert wr.format_pct(0.10, 0.08) == "-20%"
    assert wr.format_pct(0, 0.08) is None
    assert wr.long_date("2026-10-26") == "Oct 26, 2026"

    one = [price("2026-10-27", "r1", 0.10, 0.08)]
    early = wr.assign(one, "2026-10-29")
    assert early["reports"] == []
    assert len(early["pending"]) == 1
    closed = wr.assign(one, "2026-10-30")
    assert closed["reports"] == []
    assert len(closed["pending"]) == 1

    two = one + [price("2026-10-28", "r2", 0.20, 0.10)]
    before_friday = wr.assign(two, "2026-10-29")
    assert before_friday["reports"] == []
    assert len(before_friday["pending"]) == 2
    friday = wr.assign(two, "2026-10-30")
    assert [report["id"] for report in friday["reports"]] == ["2026-w44"]
    assert friday["reports"][0]["week_start"] == "2026-10-26"
    assert friday["reports"][0]["through"] == "2026-10-30"
    assert friday["reports"][0]["rolled_from"] == []
    assert len(friday["reports"][0]["changes"]) == 2
    assert friday["pending"] == []

    rolled = [price("2026-10-22", "r1", 0.10, 0.08), price("2026-10-27", "r2", 0.20, 0.10)]
    week43 = wr.assign(rolled, "2026-10-23")
    assert week43["reports"] == []
    assert len(week43["pending"]) == 1
    week44 = wr.assign(rolled, "2026-10-30")
    assert [report["id"] for report in week44["reports"]] == ["2026-w44"]
    assert len(week44["reports"][0]["changes"]) == 2
    assert week44["reports"][0]["rolled_from"] == [{
        "iso_year": 2026, "iso_week": 43, "week_start": "2026-10-19", "count": 1,
    }]

    weekend = two + [price("2026-10-31", "r3", 0.05, 0.04)]
    friday_only = wr.assign(weekend, "2026-10-30")
    assert [event["row_id"] for event in friday_only["reports"][0]["changes"]] == ["r1", "r2"]
    assert friday_only["pending"] == []
    next_friday = wr.assign(weekend, "2026-11-06")
    assert [report["id"] for report in next_friday["reports"]] == ["2026-w44"]
    assert [event["row_id"] for event in next_friday["pending"]] == ["r3"]

    log = wr.load()
    assert [event for event in log if event["kind"] == "price"] == []
    assert any(event["kind"] == "note" and "a4f84a1" in event["text"] for event in log)
    future_start = "promo_started:deal:fal-minimax-h3-30-nov:2026-11-01"
    promo_ids = {event["id"] for event in log if event["kind"] in ("promo_started", "promo_ended")}
    week_ids = {
        "promo_ended:deal:hf-wan3-unlimited-7d:2026-10-20",
        "promo_started:deal:runway-kling4-unlimited-3d:2026-10-21",
        "promo_started:deal:runway-kling4-25:2026-10-21",
        "promo_started:deal:mag-premium-annual-50:2026-10-23",
        "promo_started:deal:runway-api-kling4-20:2026-10-25",
        "promo_ended:deal:mag-premium-annual-50:2026-10-26",
        "promo_started:deal:hf-seedance-unlimited-7d:2026-10-30",
        "promo_started:deal:hf-kling4-launch:2026-10-21",
    }
    assert promo_ids == week_ids | {future_start}
    later = next(event for event in log if event["id"] == future_start)
    assert later["date"] == "2026-11-01" and later["started"] == "2026-11-01"
    assert later["checked"] == "2026-10-31" and later["vendor"] == "fal"
    higgs = next(event for event in log if event["id"].startswith("promo_ended:deal:hf-wan3"))
    assert higgs["end_is_estimate"] is True
    assert higgs["source_url"].startswith("https://")

    report = friday["reports"][0]
    body = wr.render_report_body(report, [])
    assert body.count("<h1>") == 1
    assert "AI video price changes, week of Oct 26, 2026" in body
    assert "$0.10" in body and "$0.08" in body and "-20%" in body
    assert "Plan tier" in body and "Resolution" in body and "Audio" in body
    assert "audio" not in body.lower() or "off" in body
    assert ">off<" in body
    assert "newsletter" not in body.lower()
    assert "Sponsor" not in body
    assert "<table>" in body
    desc = wr.report_description(report)
    assert "2 per-second price changes" in desc
    assert "Oct 20 to Oct 30, 2026" in desc
    ld = wr.report_jsonld(report, "https://sheepinboots.github.io/clipcost/reports/2026-w44/")
    assert ld["headline"] == wr.report_h1(report)
    assert ld["description"] == desc
    assert ld["@type"] == "Article"

    held = [price("2026-10-21", "a", 0.10, 0.08), price("2026-10-22", "b", 0.20, 0.10)]
    assert wr.assign(held, "2026-10-23")["reports"] == []
    first_prices = wr.assign(held, "2026-10-30")
    assert [item["id"] for item in first_prices["reports"]] == ["2026-w44"]
    assert first_prices["reports"][0]["covered_from"] == "2026-10-20"

    one_promo = [{
        "v": 1, "kind": "promo_started", "id": "promo_started:deal:only:2026-10-27",
        "date": "2026-10-27", "checked": "2026-10-27", "started": "2026-10-27",
        "title": "Only promo", "vendor": "fal", "source_url": "https://example.com/only", "deal_id": "only",
    }]
    assert wr.assign(one_promo, "2026-10-30")["reports"] == []
    added = [{
        "v": 1, "kind": "added", "id": "added:1", "date": "2026-10-27", "checked": "2026-10-27",
        "model": "wan-3-0", "model_name": "Wan 3.0", "platform": "fal", "what": "model",
        "source_url": "https://example.com/new",
    }, {
        "v": 1, "kind": "added", "id": "added:2", "date": "2026-10-28", "checked": "2026-10-28",
        "model": "kling-3-0", "model_name": "Kling 3.0", "platform": "fal", "what": "model",
        "source_url": "https://example.com/new2",
    }]
    assert wr.assign(added, "2026-10-30")["reports"] == []

    launch = wr.assign(log, "2026-10-30")
    assert [item["id"] for item in launch["reports"]] == ["2026-w44"]
    edition = launch["reports"][0]
    assert edition["covered_from"] == "2026-10-20"
    assert edition["covered_through"] == "2026-10-30"
    assert edition["first"] is True
    assert launch["pending"] == []
    assert {event["id"] for event in edition["changes"]} == week_ids
    held_start = wr.assign(log, "2026-11-06")
    assert [item["id"] for item in held_start["reports"]] == ["2026-w44"]
    assert [event["id"] for event in held_start["pending"]] == [future_start]
    assert wr.change_counts(edition) == {"price": 0, "promo_started": 6, "promo_ended": 2}
    assert sum(wr.change_counts(edition).values()) == 8
    launch_body = wr.render_report_body(edition, log)
    assert launch_body.count("<h1>") == 1
    assert "AI video price changes, week of Oct 26, 2026" in launch_body
    assert "Oct 20 to Oct 30, 2026" in launch_body
    assert wr.NO_PRICE_NOTE in launch_body
    assert "<h2>Promos started</h2>" in launch_body
    assert "<h2>Promos ended</h2>" in launch_body
    assert "estimated" in launch_body
    assert "https://www.magnific.com/pricing" in launch_body
    assert "https://x.com/higgsfield_ai/status/2110074247569924489" in launch_body
    assert "https://x.com/runwayml/status/2112925874144030784" in launch_body
    assert "https://x.com/RunwayMLDevs/status/2113711678399668463" in launch_body
    assert "https://x.com/higgsfield/status/2115929160447393797" in launch_body
    assert "7 days of unlimited Seedance 2.5 (zero credit cost) for new users" in launch_body
    assert "https://higgsfield.ai/creator-hub/changelog#kling-4" in launch_body
    assert "Kling 4.0 limited-time launch discount (amount shown at checkout)" in launch_body
    assert "New models and platforms" not in launch_body
    assert "newsletter" not in launch_body.lower()
    launch_desc = wr.report_description(edition)
    assert launch_desc == wr.report_jsonld(edition, "https://example.com")["description"]

    index = wr.render_index_body(launch, log)
    assert "AI video price change reports" in index
    assert wr.INDEX_DESCRIPTION in index
    assert "week of Oct 26, 2026" in index
    assert "/reports/2026-w44/" in index
    assert "count toward the two-change minimum" in index
    assert "newsletter" not in index.lower()
    index_ld = wr.index_jsonld("https://sheepinboots.github.io/clipcost/reports/")
    assert index_ld["name"] == wr.INDEX_H1
    assert index_ld["description"] == wr.INDEX_DESCRIPTION

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "price_changes.jsonl")
        record = wr.price_record(
            {"models": {"wan-3-0": {"name": "Wan 3.0"}}},
            {"id": "r9", "model": "wan-3-0", "platform": "fal", "variant": "Text to video",
             "resolution": "720p", "audio": False, "source_url": "https://example.com/p", "plan_name": "Pro"},
            0.2, 0.1, "2026-10-30",
        )
        assert record["plan_tier"] == "Pro"
        assert record["audio"] == "off"
        assert record["old_usd_per_second"] == 0.2
        assert wr.append_event(record, path) is True
        assert wr.append_event(record, path) is False
        assert len(wr.load(path)) == 1
        ended = wr.promo_ended_deal(
            {"id": "x", "end": "2026-11-01", "title": "Example", "vendor": "fal",
             "source_url": "https://example.com/d", "end_is_estimate": False},
            "2026-11-02",
        )
        assert wr.append_event(ended, path) is True

    preview = tempfile.mkdtemp(prefix="vidfare-preview-")
    subprocess.check_call(
        [sys.executable, os.path.join(ROOT, "scripts", "preview_report.py"),
         "--as-of", "2026-10-30", "--out", preview],
        cwd=ROOT,
    )
    page = os.path.join(preview, "clipcost", "reports", "index.html")
    html = open(page, encoding="utf-8").read()
    assert html.count("<h1>") == 1
    assert "<h1>AI video price change reports</h1>" in html
    assert wr.INDEX_DESCRIPTION in html
    assert f'<meta name="description" content="{wr.INDEX_DESCRIPTION}">' in html
    assert 'rel="canonical" href="https://sheepinboots.github.io/clipcost/reports/"' in html
    assert 'name="robots" content="index,follow"' in html
    assert "vidfare.goatcounter.com" in html
    assert "week of Oct 26, 2026" in html
    assert "/reports/2026-w44/" in html
    assert "newsletter" not in html.lower()
    assert '"@type": "CollectionPage"' in html
    assert wr.INDEX_DESCRIPTION in html.split('application/ld+json">', 1)[1]
    week = os.path.join(preview, "clipcost", "reports", "2026-w44", "index.html")
    week_html = open(week, encoding="utf-8").read()
    assert week_html.count("<h1>") == 1
    assert "<h1>AI video price changes, week of Oct 26, 2026</h1>" in week_html
    assert "Oct 20 to Oct 30, 2026" in week_html
    assert wr.NO_PRICE_NOTE in week_html
    assert "<h2>Promos started</h2>" in week_html
    assert "<h2>Promos ended</h2>" in week_html
    assert "https://www.magnific.com/pricing" in week_html
    assert 'rel="canonical" href="https://sheepinboots.github.io/clipcost/reports/2026-w44/"' in week_html
    assert 'name="robots" content="index,follow"' in week_html
    assert "vidfare.goatcounter.com" in week_html
    assert "newsletter" not in week_html.lower()
    assert '"@type": "Article"' in week_html
    assert wr.report_description(wr.assign(wr.load(), "2026-10-30")["reports"][0]) in week_html
    assert "https://x.com/higgsfield/status/2115929160447393797" in week_html
    assert "6 promos started" in week_html
    assert "2 promos ended" in week_html
    dist_week = os.path.join(ROOT, "dist", "reports", "2026-w44", "index.html")
    dist_html = open(dist_week, encoding="utf-8").read()
    assert dist_html.count("<h1>") == 1
    assert "<h1>AI video price changes, week of Oct 26, 2026</h1>" in dist_html
    assert "7 days of unlimited Seedance 2.5 (zero credit cost) for new users" in dist_html
    assert "Kling 4.0 limited-time launch discount (amount shown at checkout)" in dist_html
    assert "6 promos started" in dist_html
    assert "2 promos ended" in dist_html
    assert "newsletter" not in dist_html.lower()
    assert "vidfare.goatcounter.com" in dist_html
    print("ok", week)


if __name__ == "__main__":
    main()
