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
INLINE_MARK = '<section class="news news-inline" id="newsletter-inline">'
KIT_ACTION = "https://app.kit.com/forms/10170819/subscriptions"
# Auto-confirm is on in Kit: the success message says the signup counted.
SUCCESS_PHRASE = "VidFare Weekly lands on Fridays. If it isn&#x27;t in your inbox, check Promotions or spam."
RECAPTCHA_OPTION = "&quot;recaptcha&quot;:{&quot;enabled&quot;:true}"
RECAPTCHA_NOTE = "This site is protected by reCAPTCHA and the Google"
# Double opt-in copy that must not come back.
OLD_COPY = ("You are not subscribed until you confirm", "confirmation link", "news-confirm",
            "check your spam or Promotions folder")
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
        is_index = rel.replace("\\", "/") == "guides/index.html"
        check(NEWS_MARK in main, f"{rel} is missing the newsletter signup")
        check(main.count(NEWS_MARK) == 1, f"{rel} should have one end-of-guide newsletter signup")
        leftover = leftover_after_news(main)
        check(leftover == "", f"{rel} newsletter signup is not at the end of the guide: {leftover!r}")
        check(KIT_ACTION in html, f"{rel} is not the existing Kit form")
        check('data-vf-event="newsletter-signup"' in html, f"{rel} end-of-guide form is not marked newsletter-signup")
        check_note(html, rel)
        # Default guide pitch; deals gets its own heading.
        check("Get the weekly price-drop email" in main, f"{rel} is missing the default newsletter heading")
        if is_index:
            check(INLINE_MARK not in main, f"{rel} should not have the mid-guide newsletter signup")
            check(html.count("<form") == 1, f"{rel} should contain only the newsletter form")
            continue
        check(INLINE_MARK in main, f"{rel} is missing the inline newsletter signup")
        check(main.count(INLINE_MARK) == 1, f"{rel} should have one inline newsletter signup")
        check(html.count("<form") == 2, f"{rel} should contain the inline and end-of-guide newsletter forms")
        check(html.count(KIT_ACTION) == 2, f"{rel} inline form is not the existing Kit form")
        check('data-vf-event="newsletter-signup-inline"' in html, f"{rel} inline form is not marked newsletter-signup-inline")
        check(html.count(RECAPTCHA_OPTION) == 2, f"{rel} both forms need reCAPTCHA enabled in data-options")
        check(html.count(RECAPTCHA_NOTE) == 2, f"{rel} both forms need the reCAPTCHA notice")
        check("Prices change every week. Get the changes by email." in main, f"{rel} is missing the compact inline signup heading")
        check("One free email every Friday with price drops, new deals and when they end. Unsubscribe anytime." in main, f"{rel} is missing the compact inline signup line")
        inline = main[main.find(INLINE_MARK):]
        inline = inline[:inline.find("</section>") + len("</section>")]
        check("<h1" not in inline and "<h2" not in inline, f"{rel} inline signup should not add an h1 or h2")
        inline_at = main.find(INLINE_MARK)
        news_at = main.find(NEWS_MARK)
        check(0 <= inline_at < news_at, f"{rel} inline signup must sit before the end-of-guide box")
        before = main[:inline_at]
        check("</table>" in before or "<h2" in before, f"{rel} inline signup was not placed after a table or major section")
        if rel.replace("\\", "/") == "guides/grok-imagine-video-cost/index.html":
            check("Worked clip totals are official output" in before,
                  f"{rel} table note should stay attached above the inline signup")
            check("Worked clip totals are official output" not in main[inline_at:news_at],
                  f"{rel} table note was left below the inline signup")
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
    check_note(html, "deals/index.html")
    # The archived list stays below the signup, so the form is not buried after past deals.
    check(past_at > news_at, "past deals should stay below the newsletter signup")


def check_note(html, rel):
    """Every signup box has the auto-confirm success message, reCAPTCHA on in data-options, and the notice by the button."""
    news = html
    if NEWS_MARK in html:
        start = html.find(NEWS_MARK)
        rest = html[start:]
        end = rest.find("</section>")
        news = rest[: end + len("</section>")] if end != -1 else rest
    check(SUCCESS_PHRASE in news, f"{rel} newsletter box is missing the auto-confirm success message")
    check(RECAPTCHA_OPTION in news, f"{rel} newsletter box does not enable reCAPTCHA in data-options")
    check('class="small news-legal"' in news and RECAPTCHA_NOTE in news, f"{rel} reCAPTCHA notice is not next to the subscribe button")
    check("api.js?render=" in news and "ck.5.js" in news, f"{rel} reCAPTCHA helper or ck.5.js is missing")
    check(news.find("api.js?render=") < news.find("ck.5.js"), f"{rel} reCAPTCHA helper must run before ck.5.js")
    for old in OLD_COPY:
        check(old not in html, f"{rel} still has the old double opt-in copy: {old}")
    check("sora" not in html.lower(), f"{rel} names Sora")


def test_home_and_newsletter_page():
    home = os.path.join(DIST, "index.html")
    check(os.path.isfile(home), "home page was not built")
    if os.path.isfile(home):
        html = open(home, encoding="utf-8").read()
        check(NEWS_MARK in html, "home page is missing the newsletter signup")
        check(html.count(NEWS_MARK) == 1, "home page should have one newsletter signup")
        check_note(html, "index.html")
    path = os.path.join(DIST, "newsletter", "index.html")
    check(os.path.isfile(path), "/newsletter/ was not built")
    if os.path.isfile(path):
        html = open(path, encoding="utf-8").read()
        check(NEWS_MARK in html, "/newsletter/ is missing the newsletter signup")
        check(html.count(NEWS_MARK) == 1, "/newsletter/ should have one newsletter signup")
        check_note(html, "newsletter/index.html")


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
    test_home_and_newsletter_page()
    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print(f"ok: newsletter signup placement, auto-confirm copy and reCAPTCHA ({len(list(guide_pages()))} guides + /deals/ + home + /newsletter/, with inline mid-guide box)")
