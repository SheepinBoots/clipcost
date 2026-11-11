#!/usr/bin/env python3
"""GoatCounter events and UTM helper.

Checks the built dist/ (run scripts/build_site.py first):
- every HTML page that loads count.js also loads /vf-events.js with its page slug
- outbound vendor links carry data-vf-vendor, affiliate links data-vf-affiliate
- sponsor slot links and /advertise/ CTAs carry data-vf-sponsor / data-vf-cta
- every newsletter form is marked data-vf-event="newsletter-signup"
- the events script stores nothing in the browser and uses no Google Analytics
- scripts/utm.py output and validation
"""
import contextlib
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analytics  # noqa: E402
import utm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
errors = []


def check(cond, msg):
    if not cond:
        errors.append(msg)


def strip_scripts(doc):
    return re.sub(r"<script\b.*?</script>", "", doc, flags=re.S | re.I)


def html_pages():
    for dirpath, _, files in os.walk(DIST):
        for name in files:
            if name.endswith(".html"):
                path = os.path.join(dirpath, name)
                rel = "/" + os.path.relpath(path, DIST).replace(os.sep, "/")
                rel = rel[: -len("index.html")] if rel.endswith("/index.html") else rel
                yield rel, open(path, encoding="utf-8").read()


def test_script_file():
    path = os.path.join(DIST, "vf-events.js")
    check(os.path.isfile(path), "dist/vf-events.js is missing")
    if not os.path.isfile(path):
        return
    js = open(path, encoding="utf-8").read()
    check(analytics.HOSTS_PLACEHOLDER not in js, "vf-events.js still has the host placeholder")
    for banned in ("document.cookie", "localStorage", "sessionStorage", "googletagmanager", "google-analytics", "gtag(", "indexedDB"):
        check(banned not in js, f"vf-events.js uses {banned}")
    check("event: true" in js and "goatcounter.count" in js, "vf-events.js does not send goatcounter events")
    check("typeof window.goatcounter.count === 'function'" in js, "vf-events.js has no guard for a missing count.js")
    check("preventDefault" not in js, "vf-events.js must not block navigation or form submit")
    for pattern in ("newsletter-signup/", "'outbound-affiliate'", "'outbound'", "sponsor-click/", "advertise-cta/", "campaign/"):
        check(pattern in js, f"vf-events.js is missing the {pattern} event")
    hosts = json.loads(re.search(r"var HOSTS = (\{.*?\});", js).group(1))
    check(hosts.get("higgsfield.ai") == "higgsfield", "host map lacks higgsfield.ai")
    check("x.com" not in hosts, "host map maps x.com to a vendor")
    check("sora" not in js.lower(), "vf-events.js mentions Sora")


def test_pages():
    pages = dict(html_pages())
    counted = 0
    for rel, doc in pages.items():
        if "gc.zgo.at/count.js" not in doc:
            continue
        counted += 1
        tag = f'<script defer src="/vf-events.js" data-vf-page="{analytics.page_slug(rel)}"></script>'
        check(tag in doc, f"{rel} does not load vf-events.js with data-vf-page")
        check(doc.find("gc.zgo.at/count.js") < doc.find("/vf-events.js"), f"{rel} loads vf-events.js before count.js")
        check("googletagmanager" not in doc and "google-analytics.com" not in doc, f"{rel} has Google Analytics")
        body = strip_scripts(doc[doc.find("<body"):])
        footer_at = body.find("<footer")
        for m in re.finditer(r"<a\b[^>]*>", body):
            a = m.group(0)
            href = (re.search(r'href="([^"]*)"', a) or [None, ""])[1]
            if "sponsored" in (re.search(r'rel="([^"]*)"', a) or [None, ""])[1] and "data-sponsor" not in body[max(0, m.start() - 400):m.start()]:
                check('data-vf-affiliate="1"' in a and "data-vf-vendor=" in a, f"{rel} affiliate link not marked: {a[:120]}")
            if href.startswith("http") and analytics.vendor_known(href, analytics_hosts):
                check("data-vf-vendor=" in a, f"{rel} vendor link not marked: {a[:120]}")
            if href.rstrip("/") == "/advertise":
                want = "footer-link" if m.start() > footer_at > -1 else None
                check("data-vf-cta=" in a, f"{rel} /advertise/ link has no data-vf-cta")
                if want:
                    check(f'data-vf-cta="{want}"' in a, f"{rel} footer advertise link id")
        for m in re.finditer(r"<form\b[^>]*>", body):
            f = m.group(0)
            if "kit.com/forms" in f or "data-sv-form" in f:
                check('data-vf-event="newsletter-signup"' in f, f"{rel} newsletter form not marked")
    check(counted >= 25, f"only {counted} pages load count.js")
    home = pages.get("/", "")
    check(home.count('data-vf-event="newsletter-signup"') == 1, "home newsletter form not marked once")
    check('data-vf-affiliate="1"' in home, "home has no affiliate-marked link")
    kling = pages.get("/models/kling-3-0/", "")
    check('data-vf-model="kling-3-0"' in kling, "model page links lack data-vf-model")
    ad = pages.get("/advertise/", "")
    check('data-vf-cta="email"' in ad, "/advertise/ email CTA not marked")
    check('data-vf-page="404"' in pages.get("/404.html", ""), "404 page slug")
    deals = pages.get("/deals/", "")
    check(re.search(r'class="btn"[^>]*data-vf-vendor="', deals) is not None, "deal buttons not marked")


def test_annotate_sponsor_and_layout():
    hosts = {"higgsfield.ai": "higgsfield", "krea.ai": "krea"}
    doc = ('<html><body><main>'
           '<aside class="sponsor" data-sponsor="model:kling-3-0"><span class="sponsor-label">Sponsor</span>'
           '<a href="https://example.com/tool" rel="sponsored nofollow noopener" target="_blank">Example</a></aside>'
           '<aside class="sponsor is-open" data-sponsor="home"><a class="sponsor-open" href="/advertise/">Your tool</a></aside>'
           '<a href="https://higgsfield.ai/pricing?fpr=x" rel="sponsored nofollow noopener">HF</a>'
           '<a href="https://www.krea.ai/pricing" rel="nofollow noopener">Krea</a>'
           '<a href="https://twelve.tools">Twelve</a>'
           '<script>const t=`<a href="https://krea.ai/x">`;</script>'
           '</main><footer><a href="/advertise/">Advertise</a></footer></body></html>')
    out = analytics.annotate(doc, "/models/kling-3-0/", hosts, model="kling-3-0")
    check('data-vf-sponsor="model-kling-3-0"' in out, "sponsor slot link not marked")
    check('Example</a>' in out and 'data-vf-affiliate' not in out.split("Example")[0], "sponsor link marked as affiliate")
    check('data-vf-cta="sponsor-slot-home"' in out, "house sponsor link CTA id")
    check('data-vf-vendor="higgsfield" data-vf-model="kling-3-0" data-vf-affiliate="1"' in out, "affiliate attrs")
    check('<a href="https://www.krea.ai/pricing" rel="nofollow noopener" data-vf-vendor="krea" data-vf-model="kling-3-0">' in out, "vendor attrs")
    check('<a href="https://twelve.tools">Twelve</a>' in out, "unknown hosts must stay unchanged")
    check('`<a href="https://krea.ai/x">`' in out, "script templates must not be changed")
    check('data-vf-cta="footer-link"' in out, "footer advertise link")
    # Only attributes are added: removing data-vf-* gives back the input.
    check(re.sub(r' data-vf-[a-z-]+="[^"]*"', "", out) == doc, "annotate changed more than data-vf-* attributes")


def test_slugs():
    check(analytics.page_slug("/") == "home", "home slug")
    check(analytics.page_slug("/models/kling-3-0/") == "models-kling-3-0", "model slug")
    check(analytics.page_slug("/guides/seedance-2-5-unlimited/") == "guides-seedance-2-5-unlimited", "guide slug")
    check(analytics.page_slug("/404.html") == "404", "404 slug")
    check(analytics.vendor_for("https://open.higgsfield.ai/pricing", {"higgsfield.ai": "higgsfield", "open.higgsfield.ai": "higgsfield-api"}) == "higgsfield-api", "exact host wins")
    check(analytics.vendor_for("https://app.higgsfield.ai/x", {"higgsfield.ai": "higgsfield"}) == "higgsfield", "parent host")
    check(analytics.vendor_for("https://new.example.org/", {}) == "new-example-org", "hostname fallback")


def test_utm():
    u = utm.utm_url("https://vidfare.com/deals/", "reddit", "Black Friday 2026!", "social")
    check(u == "https://vidfare.com/deals/?utm_source=reddit&utm_medium=social&utm_campaign=black-friday-2026", f"utm reddit: {u}")
    u = utm.utm_url("https://vidfare.com/?utm_source=old&ref=x&a=1#t", "newsletter", "weekly-2026-11-13")
    check(u == "https://vidfare.com/?a=1&utm_source=newsletter&utm_medium=email&utm_campaign=weekly-2026-11-13#t", f"utm newsletter: {u}")
    u = utm.utm_url("https://vidfare.com/models/kling-3-0/", "directory", "Dang AI", content="listing")
    check(u.endswith("utm_source=directory&utm_medium=referral&utm_campaign=dang-ai&utm_content=listing"), f"utm directory: {u}")
    check("utm_medium=social" in utm.utm_url("https://vidfare.com", "x", "launch"), "utm x")
    for args, kw in ((("https://vidfare.com/", "facebook", "a"), {}),
                     (("https://vidfare.com/", "reddit", "a", "email"), {}),
                     (("https://vidfare.com/", "reddit", "!!!"), {}),
                     (("https://example.com/", "reddit", "a"), {}),
                     (("vidfare.com/", "reddit", "a"), {})):
        try:
            utm.utm_url(*args, **kw)
            errors.append(f"utm_url{args} should fail")
        except ValueError:
            pass
    check(utm.utm_url("https://example.com/", "reddit", "a", any_host=True).startswith("https://example.com/?utm_source=reddit"), "any_host")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = utm.main(["https://vidfare.com/", "--source", "reddit", "--campaign", "x"])
    check(rc == 0 and buf.getvalue().strip() == "https://vidfare.com/?utm_source=reddit&utm_medium=social&utm_campaign=x", "utm CLI output")


def test_docs():
    path = os.path.join(ROOT, "docs", "analytics.md")
    check(os.path.isfile(path), "docs/analytics.md is missing")
    if os.path.isfile(path):
        doc = open(path, encoding="utf-8").read()
        for needle in ("newsletter-signup/", "outbound/", "outbound-affiliate/", "sponsor-click/", "advertise-cta/", "campaign/", "utm_campaign", "Campaigns", "scripts/utm.py"):
            check(needle in doc, f"docs/analytics.md does not mention {needle}")
        check("sora" not in doc.lower(), "docs mention Sora")


if __name__ == "__main__":
    analytics_hosts = json.loads(re.search(r"var HOSTS = (\{.*?\});", open(os.path.join(DIST, "vf-events.js"), encoding="utf-8").read()).group(1)) if os.path.isfile(os.path.join(DIST, "vf-events.js")) else {}
    for fn in (test_script_file, test_pages, test_annotate_sponsor_and_layout, test_slugs, test_utm, test_docs):
        fn()
    if errors:
        raise SystemExit("analytics check failed:\n- " + "\n- ".join(errors))
    print("ok analytics: events script on every counted page, link/form attributes, sponsor/advertise ids, UTM helper")
