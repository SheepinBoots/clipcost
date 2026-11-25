"""Checks for /guides/is-kling-ai-free/ after a site build."""
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import is_kling_free_guide as guide

PAGE = os.path.join(ROOT, "dist/guides/is-kling-ai-free/index.html")
PRICES = os.path.join(ROOT, "data/prices.json")


def visible(raw):
    text = html.unescape(re.sub(r"<script[^>]*>.*?</script>", " ", raw, flags=re.S | re.I))
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text)


def main():
    if not os.path.isfile(PAGE):
        raise SystemExit(f"{PAGE} is missing; build the site first")
    raw = open(PAGE, encoding="utf-8").read()
    text = visible(raw)
    db = json.load(open(PRICES, encoding="utf-8"))
    errors = []

    title = html.unescape(re.search(r"<title>(.*?)</title>", raw).group(1))
    desc = html.unescape(re.search(r'<meta name="description" content="(.*?)"', raw).group(1))
    if len(title) > 60:
        errors.append(f"title is {len(title)} characters: {title}")
    if len(desc) > 160:
        errors.append(f"meta is {len(desc)} characters: {desc}")
    if "sora" in raw.lower():
        errors.append("page names the banned model")

    rows = [
        r
        for r in db["rows"]
        if r.get("model") == "kling-3-0"
        and r.get("usd_per_second") is not None
        and r.get("status") != "discontinued"
    ]
    rows.sort(key=lambda r: (float(r["usd_per_second"]), r["id"]))
    cheapest, nxt = rows[0], rows[1]
    from decimal import Decimal, ROUND_HALF_UP

    def rate_money(v):
        d = Decimal(str(v))
        places = 3 if abs(d) >= Decimal("0.1") else 4
        text = f"{abs(d.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)):.{places}f}"
        whole, frac = text.split(".")
        frac = frac.rstrip("0").ljust(2, "0")
        return f"${whole}.{frac}"

    cheap_s = rate_money(cheapest["usd_per_second"])
    next_s = rate_money(nxt["usd_per_second"])
    if cheap_s not in text:
        errors.append(f"cheapest rate {cheap_s} missing")
    if next_s not in text:
        errors.append(f"next-cheapest rate {next_s} missing")
    if "next-cheapest catalog row" not in text:
        errors.append("next-cheapest wording missing")
    if "two cheapest" in text.lower():
        errors.append("page still says two cheapest")

    # Table body order must follow the selected sorted subset.
    table = re.search(r'id="prices".*?</table>', raw, re.S)
    if not table:
        errors.append("price table missing")
    else:
        amts = [float(a) for a in re.findall(r"<td>\$([0-9.]+)</td>\s*<td>\$[0-9.]+</td>", table.group(0))]
        if amts != sorted(amts):
            errors.append(f"price table is not in price order: {amts}")
        if cheapest["platform"] not in table.group(0):
            errors.append("cheapest platform missing from the table")

    # Official static-document facts kept; unverifiable JS claims dropped.
    for needle in (
        "no monthly credits",
        "Jul 28, 2026",
        "33 720p videos",
        "30 credits per second",
        "llms.txt",
    ):
        if needle not in text:
            errors.append(f"missing official-document wording: {needle}")
    for banned in (
        "valid 31 days",
        "monthly free credits on login",
        "Limited-Time 35%",
        "Sign In to Claim Gift",
        "Terms of Paid Service, effective",
    ):
        if banned.lower() in text.lower():
            errors.append(f"unverifiable claim still present: {banned}")

    # Mid and end signup marks.
    if 'data-vf-event="newsletter-signup-inline"' not in raw:
        errors.append("mid signup missing")
    if 'data-vf-event="newsletter-signup"' not in raw:
        errors.append("end signup missing")
    # GoatCounter event names are data-vf-event plus the page path, wired in JS.
    if 'data-vf-event="newsletter-signup-inline"' not in raw:
        errors.append("mid signup data-vf-event missing")
    if 'id="newsletter-inline"' not in raw:
        errors.append("mid signup box missing")
    if 'id="newsletter"' not in raw:
        errors.append("end signup box missing")

    canon = re.search(r'<link rel="canonical" href="([^"]+)"', raw)
    if not canon or canon.group(1) != "https://vidfare.com/guides/is-kling-ai-free/":
        errors.append(f"canonical is {canon.group(1) if canon else None}")

    if errors:
        raise SystemExit("is_kling_free_guide errors:\n- " + "\n- ".join(errors))
    print("test_is_kling_free_guide: ok")


if __name__ == "__main__":
    main()
