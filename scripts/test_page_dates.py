#!/usr/bin/env python3
"""Page lastmod follows a content hash, not the catalog check date."""
import json
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import page_dates  # noqa: E402
import timefmt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TODAY = timefmt.us_today().isoformat()

SAMPLE = """<!doctype html><html><head><title>T</title>
<script type="application/ld+json">{"@type": "WebPage", "datePublished": "2026-10-20", "dateModified": "2026-11-27"}</script>
<script type="application/ld+json">{"@type": "Dataset", "dateModified": "2026-11-27", "temporalCoverage": "2026-11-27"}</script>
</head><body>
<p>Price is $0.12 per second.</p>
<div class="small">Checked 2026-11-27. From a credit plan (checked 2026-11-27, https://example.com).</div>
<p class="small">Last checked 2026-11-27. The oldest row check on this page is Nov 22, 2026.</p>
<p>Last updated 2026-11-27.</p>
<p>No live deals as of Nov 27, 2026.</p>
<section id="ending"><h2>Deals ending by Dec 4, 2026</h2>
<div data-deal-end="2026-11-27"><span class="ends">until November 27, 2026, 7:00 PM ET (4:00 PM PT)</span></div>
</section>
<table><tr><td><a href="https://example.com">source</a><br>2026-11-27</td></tr></table>
<footer><p>© 2026 VidFare · Data last checked 2026-11-27 · <a href="/data/">Price data</a></p></footer>
</body></html>
"""


def assert_ok(cond, msg, errors):
    if not cond:
        errors.append(msg)


def test_strip_leaves_content_dates():
    errors = []
    stripped = page_dates.strip_volatile(SAMPLE)
    assert_ok("until November 27, 2026, 7:00 PM ET (4:00 PM PT)" in stripped, "deal end date was stripped", errors)
    assert_ok('data-deal-end="2026-11-27"' in stripped, "data-deal-end was stripped", errors)
    assert_ok("$0.12 per second" in stripped, "price text was stripped", errors)
    assert_ok("Data last checked 2026-11-27" not in stripped, "footer check date remained", errors)
    assert_ok('"dateModified": "2026-11-27"' not in stripped, "JSON-LD dateModified remained", errors)
    assert_ok('"datePublished": "2026-10-20"' not in stripped, "JSON-LD datePublished remained", errors)
    assert_ok("Checked 2026-11-27" not in stripped, "row checked date remained", errors)
    assert_ok("<br>2026-11-27</td>" not in stripped, "source-column checked date remained", errors)
    assert_ok("Last updated 2026-11-27." not in stripped, "visible Last updated remained", errors)
    assert_ok("Deals ending by Dec 4, 2026" not in stripped, "rolling 7-day heading remained", errors)
    assert_ok("as of Nov 27, 2026" not in stripped, "as-of today remained", errors)
    # Dataset dateModified is stripped as a JSON-LD field, but only the date value.
    assert_ok("Dataset" in stripped, "Dataset node was dropped", errors)
    return errors


def test_hash_ignores_volatile_dates():
    errors = []
    other = SAMPLE.replace("2026-11-27", "2026-11-28").replace("Nov 27, 2026", "Nov 28, 2026").replace("Dec 4, 2026", "Dec 5, 2026")
    # The replacements above also change the deal end date. Put the deal end back.
    other = other.replace('data-deal-end="2026-11-28"', 'data-deal-end="2026-11-27"')
    other = other.replace("until November 28, 2026, 7:00 PM ET", "until November 27, 2026, 7:00 PM ET")
    assert_ok(page_dates.content_hash(SAMPLE) == page_dates.content_hash(other),
              "hash changed when only check/update/clock dates changed", errors)
    priced = SAMPLE.replace("$0.12 per second", "$0.24 per second")
    assert_ok(page_dates.content_hash(SAMPLE) != page_dates.content_hash(priced),
              "hash ignored a price change", errors)
    extended = SAMPLE.replace("until November 27, 2026, 7:00 PM ET", "until November 28, 2026, 7:00 PM ET")
    extended = extended.replace('data-deal-end="2026-11-27"', 'data-deal-end="2026-11-28"')
    assert_ok(page_dates.content_hash(SAMPLE) != page_dates.content_hash(extended),
              "hash ignored a deal end-date change", errors)
    return errors


def _write_site(tmp, about_html, model_html, about_mod="2026-10-20", model_mod="2026-10-20"):
    root = Path(tmp)
    dist = root / "dist"
    (root / "data").mkdir(parents=True)
    (dist / "about").mkdir(parents=True)
    (dist / "models" / "kling-3-0").mkdir(parents=True)
    dates = {
        "/about/": {"published": "2026-10-20", "modified": about_mod},
        "/models/kling-3-0/": {"published": "2026-10-20", "modified": model_mod},
    }
    (root / "data" / "page_dates.json").write_text(json.dumps(dates, indent=1) + "\n")
    (dist / "about" / "index.html").write_text(about_html)
    (dist / "models" / "kling-3-0" / "index.html").write_text(model_html)
    (dist / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'  <url><loc>https://vidfare.com/about/</loc><lastmod>{about_mod}</lastmod></url>\n'
        f'  <url><loc>https://vidfare.com/models/kling-3-0/</loc><lastmod>{model_mod}</lastmod></url>\n'
        "</urlset>\n"
    )
    return root, dist


def _mods(dist):
    sm = (dist / "sitemap.xml").read_text()
    about = (dist / "about" / "index.html").read_text()
    model = (dist / "models" / "kling-3-0" / "index.html").read_text()
    return {
        "sm_about": "https://vidfare.com/about/</loc><lastmod>2026-10-20</lastmod>" in sm,
        "sm_model_old": "https://vidfare.com/models/kling-3-0/</loc><lastmod>2026-10-20</lastmod>" in sm,
        "sm_model_today": f"https://vidfare.com/models/kling-3-0/</loc><lastmod>{TODAY}</lastmod>" in sm,
        "about_ld": '"dateModified": "2026-10-20"' in about,
        "about_dataset": '"@type": "Dataset"' in about and f'"dateModified": "{TODAY}"' not in about.split('"@type": "Dataset"')[1][:400] if '"@type": "Dataset"' in about else True,
        "model_ld_today": f'"@type": "WebPage", "datePublished": "2026-10-20", "dateModified": "{TODAY}"' in model
            or f'"dateModified": "{TODAY}"' in model,
        "about_visible": "Last updated 2026-10-20." in about,
    }


def test_apply_seeds_then_bumps_only_changed_pages():
    errors = []
    about = SAMPLE.replace("$0.12 per second", "About VidFare")
    model = SAMPLE
    with tempfile.TemporaryDirectory() as tmp:
        root, dist = _write_site(tmp, about, model)
        page_dates.invalidate()
        urls = ["/about/", "/models/kling-3-0/"]
        # First pass stores hashes and keeps the seeded lastmod.
        page_dates.apply_to_dist(str(root), str(dist), urls, TODAY)
        dates = json.loads((root / "data" / "page_dates.json").read_text())
        assert_ok(dates["/about/"]["modified"] == "2026-10-20", "first pass reset /about/ lastmod", errors)
        assert_ok(dates["/models/kling-3-0/"]["modified"] == "2026-10-20", "first pass reset model lastmod", errors)
        assert_ok(dates["/about/"].get("hash") and dates["/models/kling-3-0/"].get("hash"),
                  "first pass did not store hashes", errors)
        first_about_hash = dates["/about/"]["hash"]
        # Second pass with no content change is a no-op for dates.
        page_dates.invalidate()
        page_dates.apply_to_dist(str(root), str(dist), urls, TODAY)
        dates2 = json.loads((root / "data" / "page_dates.json").read_text())
        sm1_after = (dist / "sitemap.xml").read_text()
        about1 = (dist / "about" / "index.html").read_text()
        model1 = (dist / "models" / "kling-3-0" / "index.html").read_text()
        assert_ok(dates2 == dates, "second pass changed page_dates.json", errors)
        # Third pass: only the model page's price changes.
        priced = model.replace("$0.12 per second", "$0.24 per second")
        # Keep the same stored lastmod chrome so the hash sees only the price.
        (dist / "models" / "kling-3-0" / "index.html").write_text(priced)
        page_dates.invalidate()
        page_dates.apply_to_dist(str(root), str(dist), urls, TODAY)
        dates3 = json.loads((root / "data" / "page_dates.json").read_text())
        sm = (dist / "sitemap.xml").read_text()
        about3 = (dist / "about" / "index.html").read_text()
        model3 = (dist / "models" / "kling-3-0" / "index.html").read_text()
        assert_ok(dates3["/about/"]["modified"] == "2026-10-20", "price change bumped /about/", errors)
        assert_ok(dates3["/about/"]["hash"] == first_about_hash, "price change altered /about/ hash", errors)
        assert_ok(dates3["/models/kling-3-0/"]["modified"] == TODAY, "price change did not bump the model page", errors)
        assert_ok(dates3["/models/kling-3-0/"]["hash"] != dates["/models/kling-3-0/"]["hash"],
                  "price change did not update the model hash", errors)
        assert_ok(f"<loc>https://vidfare.com/about/</loc><lastmod>2026-10-20</lastmod>" in sm,
                  "sitemap lastmod for /about/ moved", errors)
        assert_ok(f"<loc>https://vidfare.com/models/kling-3-0/</loc><lastmod>{TODAY}</lastmod>" in sm,
                  "sitemap lastmod for the model page did not move to today", errors)
        assert_ok('"dateModified": "2026-10-20"' in about3, "about dateModified moved", errors)
        assert_ok(f'"dateModified": "{TODAY}"' in model3, "model WebPage dateModified did not move to today", errors)
        # Dataset dateModified on the about fixture is a catalog stamp, not the page lastmod.
        # The fixture's Dataset still has 2026-11-27; apply must not rewrite it to TODAY.
        assert_ok('"@type": "Dataset", "dateModified": "2026-11-27"' in about3
                  or '"@type": "Dataset", "dateModified": "2026-11-27"' in about3.replace(" ", ""),
                  "Dataset dateModified was rewritten as the page lastmod", errors)
        assert_ok("Last updated 2026-10-20." in about3, "about visible Last updated moved", errors)
        assert_ok(f"Last updated {TODAY}." in model3, "model visible Last updated did not move to today", errors)
        assert_ok(about3 == about1 or "Last updated 2026-10-20." in about3, "about html changed unexpectedly", errors)
        # Fourth pass after the price change is stable.
        page_dates.invalidate()
        page_dates.apply_to_dist(str(root), str(dist), urls, TODAY)
        assert_ok((dist / "sitemap.xml").read_text() == sm, "rebuild after price change altered sitemap lastmod", errors)
        assert_ok((dist / "models" / "kling-3-0" / "index.html").read_text() == model3,
                  "rebuild after price change altered model dateModified", errors)
    return errors


def test_dist_apply_twice_is_stable():
    """If dist is already built, apply() twice must not move lastmod or dateModified."""
    errors = []
    dist = ROOT / "dist"
    sitemap = dist / "sitemap.xml"
    dates_file = ROOT / "data" / "page_dates.json"
    if not sitemap.is_file() or not dates_file.is_file():
        return errors
    dates = json.loads(dates_file.read_text())
    urls = [p for p in dates if (dist / p.lstrip("/") / "index.html").is_file() or (p == "/" and (dist / "index.html").is_file())]
    # Homepage lives at dist/index.html; html_path uses dist + path + index.html
    # which for "/" is dist/index.html. Good.
    sample = ("/", "/about/", "/deals/", "/guides/higgsfield-black-friday/", "/reports/2026-w47/")

    def date_modified_values(path):
        fp = dist / "index.html" if path == "/" else dist / path.lstrip("/") / "index.html"
        return re.findall(r'"dateModified": "(\d{4}-\d{2}-\d{2})"', fp.read_text())

    page_dates.invalidate()
    page_dates.apply_to_dist(str(ROOT), str(dist), urls, TODAY)
    mid_sm = sitemap.read_text()
    mid_dates = dates_file.read_text()
    mid_ld = {path: date_modified_values(path) for path in sample if (dist / "index.html" if path == "/" else dist / path.lstrip("/") / "index.html").is_file()}
    page_dates.invalidate()
    page_dates.apply_to_dist(str(ROOT), str(dist), urls, TODAY)
    after_sm = sitemap.read_text()
    after_dates = dates_file.read_text()
    assert_ok(mid_sm == after_sm, "second apply() changed sitemap lastmod", errors)
    assert_ok(mid_dates == after_dates, "second apply() changed page_dates.json", errors)
    for path, want in mid_ld.items():
        assert_ok(date_modified_values(path) == want, f"second apply() changed dateModified on {path}", errors)
    return errors


def main():
    page_dates.invalidate()
    errors = []
    for fn in (
        test_strip_leaves_content_dates,
        test_hash_ignores_volatile_dates,
        test_apply_seeds_then_bumps_only_changed_pages,
        test_dist_apply_twice_is_stable,
    ):
        errors.extend(fn() or [])
        page_dates.invalidate()
    if errors:
        print("page_dates:\n- " + "\n- ".join(errors))
        raise SystemExit(1)
    print("ok page_dates")


if __name__ == "__main__":
    main()
