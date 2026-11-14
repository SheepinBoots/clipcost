#!/usr/bin/env python3
"""Newsletter signup placement on guides and /deals/.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_newsletter_signup.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
NEWS_MARK = '<section class="news" id="newsletter">'
KIT_ACTION = "https://app.kit.com/forms/10170819/subscriptions"
errors = []


def check(cond, msg):
    if not cond:
        errors.append(msg)


def main_inner(html):
    return html.split("<main", 1)[-1].split("</main>", 1)[0]


def leftover_after_news(main):
    news_at = main.find(NEWS_MARK)
    if news_at < 0:
        return None
    rest = main[news_at + len(NEWS_MARK):]
    end = rest.find("</section>")
    after = rest[end + len("</section>"):] if end != -1 else rest
    return re.sub(
        r"<script\b[\s\S]*?</script>|<noscript\b[\s\S]*?</noscript>|\s+",
        "",
        after,
        flags=re.I,
    )


def guide_pages():
    guides = os.path.join(DIST, "guides")
    if not os.path.isdir(guides):
        return
    for dirpath, _, files in os.walk(guides):
        if "index.html" in files:
            rel = os.path.relpath(os.path.join(dirpath, "index.html"), DIST)
            yield rel, open(os.path.join(dirpath, "index.html"), encoding="utf-8").read()


def test_guides():
    found = list(guide_pages())
    check(len(found) >= 10, f"expected at least 10 guide pages, found {len(found)}")
    for rel, html in found:
        main = main_inner(html)
        check(NEWS_MARK in main, f"{rel} is missing the newsletter signup")
        check(main.count(NEWS_MARK) == 1, f"{rel} should have one newsletter signup")
        leftover = leftover_after_news(main)
        check(leftover == "", f"{rel} newsletter signup is not at the end of the guide: {leftover!r}")
        check(html.count("<form") == 1, f"{rel} should contain only the newsletter form")
        check(KIT_ACTION in html, f"{rel} is not the existing Kit form")
        check('data-vf-event="newsletter-signup"' in html, f"{rel} form is not marked newsletter-signup")
        # Default guide pitch; deals gets its own heading.
        check("Get the weekly price-drop email" in main, f"{rel} is missing the default newsletter heading")
        # FAQ JSON-LD must still not mention a newsletter.
        for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
            raw = m.group(1).lower()
            if '"@type": "faqpage"' in raw or '"@type":"faqpage"' in raw:
                for bad in ("subscribe", "newsletter", "buttondown"):
                    check(bad not in raw, f"{rel} FAQ JSON-LD contains {bad}")


def test_deals():
    path = os.path.join(DIST, "deals", "index.html")
    check(os.path.isfile(path), "deals page was not built")
    if not os.path.isfile(path):
        return
    html = open(path, encoding="utf-8").read()
    live_at = html.find('id="liveDeals"')
    news_at = html.find(NEWS_MARK)
    sales_at = html.find(">When these vendors run sales<")
    past_at = html.find(">Past deals<")
    check(0 <= live_at < news_at < sales_at < past_at,
          "deals newsletter signup must sit after the live deals list and before past deals")
    check(html.count(NEWS_MARK) == 1, "deals page should have one newsletter signup")
    check("Get price drops and deal deadlines every Friday" in html,
          "deals newsletter is missing the deadline pitch")
    check(KIT_ACTION in html, "deals page is not the existing Kit form")
    check('data-vf-event="newsletter-signup"' in html, "deals form is not marked newsletter-signup")
    # The archived list stays below the signup, so the form is not buried after past deals.
    check(past_at > news_at, "past deals should stay below the newsletter signup")


def test_kit_form_unchanged():
    src = open(os.path.join(ROOT, "scripts", "build_site.py"), encoding="utf-8").read()
    check('KIT_FORM_ID = "10170819"' in src, "Kit form id changed")
    check('KIT_FORM_UID = "6ef7eafdbe"' in src, "Kit form uid changed")
    check('KIT_FORM_ACTION = "https://app.kit.com/forms/10170819/subscriptions"' in src, "Kit form action changed")


if __name__ == "__main__":
    if not os.path.isdir(DIST):
        sys.exit("dist/ is missing; run python3 scripts/build_site.py first")
    test_kit_form_unchanged()
    test_guides()
    test_deals()
    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print(f"ok: newsletter signup placement ({len(list(guide_pages()))} guides + /deals/)")
