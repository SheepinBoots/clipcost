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
    promo_ids = {event["id"] for event in log if event["kind"] in ("promo_started", "promo_ended")}
    assert promo_ids == {
        "promo_ended:deal:hf-wan3-unlimited-7d:2026-10-20",
        "promo_started:deal:runway-kling4-unlimited-3d:2026-10-21",
        "promo_started:deal:runway-kling4-25:2026-10-21",
        "promo_started:deal:mag-premium-annual-50:2026-10-23",
        "promo_started:deal:runway-api-kling4-20:2026-10-25",
        "promo_ended:deal:mag-premium-annual-50:2026-10-26",
    }
    higgs = next(event for event in log if event["id"].startswith("promo_ended:deal:hf-wan3"))
    assert higgs["end_is_estimate"] is True
    assert higgs["source_url"].startswith("https://")
    launch = wr.assign(log, "2026-10-30")
    assert launch["reports"] == []
    assert launch["pending"] == []

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
    assert desc.startswith("2 real price changes")
    ld = wr.report_jsonld(report, "https://sheepinboots.github.io/clipcost/reports/2026-w44/")
    assert ld["headline"] == wr.report_h1(report)
    assert ld["description"] == desc
    assert ld["@type"] == "Article"

    index = wr.render_index_body(launch, log)
    assert "AI video price change reports" in index
    assert wr.INDEX_DESCRIPTION in index
    assert "week of Oct 26, 2026" in index
    assert "is not published" in index
    assert "Promo starts and ends recorded: 6" in index
    assert "newsletter" not in index.lower()
    index_ld = wr.index_jsonld("https://sheepinboots.github.io/clipcost/reports/")
    assert index_ld["name"] == wr.INDEX_H1
    assert index_ld["description"] == wr.INDEX_DESCRIPTION

    rolled_body = wr.render_report_body(week44["reports"][0], log, None)
    assert "Promos started" in rolled_body
    assert "Promos ended" in rolled_body
    assert "estimated" in rolled_body
    assert "New models and platforms" not in rolled_body

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
    assert "is not published" in html
    assert "newsletter" not in html.lower()
    assert '"@type": "CollectionPage"' in html
    assert wr.INDEX_DESCRIPTION in html.split('application/ld+json">', 1)[1]
    assert not os.path.isdir(os.path.join(ROOT, "dist", "reports"))
    assert not os.path.exists(os.path.join(preview, "clipcost", "reports", "2026-w44", "index.html"))
    print("ok", page)


if __name__ == "__main__":
    main()
