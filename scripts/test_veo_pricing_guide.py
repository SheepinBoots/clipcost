"""Checks for /guides/veo-3-1-pricing/ after a site build."""
import html
import json
import os
import re
import sys
from decimal import Decimal, ROUND_HALF_UP

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import veo_pricing_guide as guide

PAGE = os.path.join(ROOT, "dist/guides/veo-3-1-pricing/index.html")
PRICES = os.path.join(ROOT, "data/prices.json")


def visible(raw):
    text = html.unescape(re.sub(r"<script[^>]*>.*?</script>", " ", raw, flags=re.S | re.I))
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text)


def money(v):
    n = int((Decimal(str(v)) * Decimal(100000)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    neg = n < 0
    n = abs(n)
    whole, frac = divmod(n, 100000)
    digits = f"{frac:05d}".rstrip("0")
    if len(digits) < 2:
        digits = f"{frac:05d}"[:2]
    return f"{'-' if neg else ''}${whole}.{digits}"


def first_para_after(raw, heading):
    m = re.search(re.escape(f"<h2>{heading}</h2>") + r"\s*<p>(.*?)</p>", raw, re.S)
    if not m:
        return None
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))).strip()


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
    if re.search(r"\bUTC\b", text):
        errors.append("visible copy contains UTC")
    if "carries an end date" in text:
        errors.append("retirement section still says rows carry no end date")
    if "none of those rows has a retirement date" not in text:
        errors.append("retirement-date wording missing")

    rows = [
        r
        for r in db["rows"]
        if r.get("model") == "veo-3-1"
        and r.get("usd_per_second") is not None
        and r.get("status") != "discontinued"
    ]
    rows.sort(key=lambda r: (float(r["usd_per_second"]), r["id"]))
    if len(rows) != 19:
        errors.append(f"expected 19 current Veo 3.1 rows, catalog has {len(rows)}")

    # Catalog-precision $/s, including the three previously rounded cells.
    for rid in ("r126", "r172", "r122"):
        row = next(r for r in rows if r["id"] == rid)
        shown = money(row["usd_per_second"])
        if shown not in text:
            errors.append(f"{rid} catalog rate {shown} missing from the page")
    for banned, rid in (("$0.197", "r126"), ("$0.492", "r122")):
        if banned in text and money(next(r for r in rows if r["id"] == rid)["usd_per_second"]) != banned:
            errors.append(f"rounded rate {banned} still present (should be catalog precision)")
    # $0.343 without the trailing 2, as a standalone rate (not $0.3432).
    if re.search(r"\$0\.343(?!\d)", text):
        errors.append("rounded 4K rate $0.343 still present; catalog value is $0.3432")

    cheap = money(rows[0]["usd_per_second"])
    if cheap not in text:
        errors.append(f"cheapest rate {cheap} missing")
    if rows[0]["platform"] not in text:
        errors.append("cheapest platform missing")

    table = re.search(r'id="prices".*?</table>', raw, re.S)
    if not table:
        errors.append("price table missing")
    else:
        amts = [Decimal(a) for a in re.findall(r"<td>\$([0-9.]+)</td>", table.group(0))]
        # $ / sec is the 7th of 10 cells; grab every row's rate from the amt-sized values
        # More reliably: split rows.
        row_htmls = re.findall(r"<tr>(.*?)</tr>", table.group(0), re.S)[1:]  # skip header
        rates = []
        for rh in row_htmls:
            cells = re.findall(r"<td[^>]*>(.*?)</td>", rh, re.S)
            if len(cells) >= 7:
                rates.append(Decimal(re.search(r"\$([0-9.]+)", html.unescape(cells[6])).group(1)))
        expected = [Decimal(str(r["usd_per_second"])) for r in rows]
        # money() may trim zeros; compare by Decimal of displayed vs catalog after money parse
        expected_shown = [Decimal(money(r["usd_per_second"])[1:]) for r in rows]
        if rates != expected_shown:
            errors.append(f"price table order or values do not match catalog sort: {rates} vs {expected_shown}")
        if len(row_htmls) != len(rows):
            errors.append(f"price table has {len(row_htmls)} rows, catalog has {len(rows)}")

    # FAQ answers equal the visible first paragraphs.
    ld_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)
    faq = None
    for b in ld_blocks:
        obj = json.loads(b)
        if obj.get("@type") == "FAQPage":
            faq = obj
            break
    if not faq:
        errors.append("FAQPage JSON-LD missing")
    else:
        for ent in faq["mainEntity"]:
            name = ent["name"]
            ans = ent["acceptedAnswer"]["text"]
            vis = first_para_after(raw, name)
            if vis is None:
                errors.append(f"visible heading missing for FAQ {name!r}")
            elif vis != ans:
                errors.append(f"FAQ {name!r} does not match the visible paragraph")
            if "subscribe" in ans.lower() or "newsletter" in ans.lower():
                errors.append(f"FAQ {name!r} contains newsletter wording")

    if 'data-vf-event="newsletter-signup-inline"' not in raw or 'id="newsletter-inline"' not in raw:
        errors.append("mid signup missing")
    if 'data-vf-event="newsletter-signup"' not in raw or 'id="newsletter"' not in raw:
        errors.append("end signup missing")

    canon = re.search(r'<link rel="canonical" href="([^"]+)"', raw)
    if not canon or canon.group(1) != "https://vidfare.com/guides/veo-3-1-pricing/":
        errors.append(f"canonical is {canon.group(1) if canon else None}")

    if errors:
        raise SystemExit("veo_pricing_guide errors:\n- " + "\n- ".join(errors))
    print("test_veo_pricing_guide: ok")


if __name__ == "__main__":
    main()
