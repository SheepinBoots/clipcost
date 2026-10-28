#!/usr/bin/env python3
"""VidFare deals: load, expire, deal-adjusted $/s, and pricing-page diffs.

Deal-adjusted rates are shown beside list prices. They never replace the
stored row price. Unlimited windows are a break-even second count, not $0/s.
"""
import hashlib, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEALS_PATH = os.path.join(ROOT, "data", "deals.json")
SNAPSHOT_DIR = os.path.join(ROOT, "data", "deal_snapshots")
CANDIDATES_PATH = os.path.join(ROOT, "data", "deal_candidates.json")

TYPES = (
    "percent_off",
    "plan_sale",
    "promo_code",
    "bonus_credits",
    "unlimited_window",
    "api_promo",
)

# Vendor name on a deal -> platform strings used on price rows.
PLATFORMS = {
    "Higgsfield": ["Higgsfield"],
    "Higgsfield API": ["Higgsfield API"],
    "Krea": ["Krea"],
    "Magnific": ["Magnific"],
    "Runway": ["Runway", "Runway API"],
    "fal": ["fal"],
}

OFFER_RE = re.compile(
    r".{0,80}(?:\d+\s*%\s*off|%\s*off|\bsale\b|unlimited|promo(?:tion| code)?|bonus credits?|\bdiscount\b).{0,80}",
    re.I,
)


def load(path=DEALS_PATH):
    with open(path) as f:
        doc = json.load(f)
    doc.setdefault("deals", [])
    doc.setdefault("history", [])
    doc.setdefault("watch", [])
    return doc


def save(doc, path=DEALS_PATH):
    with open(path, "w") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write("\n")


def conditions(deal):
    base = {
        "new_users_only": False,
        "annual_only": False,
        "first_months": None,
        "max_resolution": None,
        "web_only": False,
        "code": None,
        "standing": False,
    }
    base.update(deal.get("conditions") or {})
    return base


def effective_status(deal, today):
    """Live deals past their end date are archived. History stays ended."""
    status = deal.get("status") or "unconfirmed"
    end = deal.get("end")
    if status == "live" and end and end < today:
        return "ended"
    return status


def is_current(deal, today):
    return effective_status(deal, today) == "live"


def expire_deals(doc, today, log):
    """Move live deals whose end date has passed to the archive. Keep the record."""
    moved = []
    for deal in doc.get("deals", []):
        if deal.get("status") == "live" and deal.get("end") and deal["end"] < today:
            deal["status"] = "ended"
            moved.append(deal)
            log.append({
                "date": today,
                "type": "deal_ended",
                "deal": deal["id"],
                "vendor": deal.get("vendor"),
                "source_url": deal.get("source_url"),
                "text": f"{deal.get('title') or deal['id']} ended {deal['end']}.",
            })
    return moved


def vendor_platforms(vendor):
    return PLATFORMS.get(vendor, [vendor])


def pairs(deal):
    if deal.get("price_pairs"):
        return list(deal["price_pairs"])
    if any(deal.get(k) is not None for k in ("price_before", "price_after", "full_plan_id", "deal_plan_id")):
        return [{
            "plan": (deal.get("plans") or [None])[0],
            "full_plan_id": deal.get("full_plan_id"),
            "deal_plan_id": deal.get("deal_plan_id"),
            "price_before": deal.get("price_before"),
            "price_after": deal.get("price_after"),
            "percent": deal.get("percent"),
        }]
    return []


def plan_name_matches(plan_name, wanted):
    name = plan_name or ""
    for label in wanted:
        if name == label or name.startswith(label + " ") or name.startswith(label + "("):
            return True
    return False


def pair_ids(deal):
    ids = set(deal.get("plan_ids") or [])
    for pair in pairs(deal):
        if pair.get("full_plan_id"):
            ids.add(pair["full_plan_id"])
        if pair.get("deal_plan_id"):
            ids.add(pair["deal_plan_id"])
    return ids


def row_matches(deal, row):
    """True when a deal should badge this price row."""
    if deal.get("show_on_rows") is False:
        return False
    if deal["id"] in (row.get("deal_ids") or []):
        return True
    if row.get("platform") not in vendor_platforms(deal.get("vendor")):
        return False
    # An unlimited offer for a model we don't catalog must not badge other models.
    models = deal.get("models") or []
    if deal.get("type") == "unlimited_window" and not models and not (deal.get("variants") or []):
        return False
    if models and row.get("model") not in models:
        return False
    variants = deal.get("variants") or []
    if variants and row.get("variant") not in variants:
        return False
    cond = conditions(deal)
    cap = cond.get("max_resolution")
    if cap and str(row.get("resolution") or "").lower() != str(cap).lower():
        return False
    wanted = deal.get("plans") or []
    ids = pair_ids(deal)
    constrained = bool(models or wanted or ids or variants or cap)
    if not constrained:
        return False
    if wanted or ids:
        if row.get("plan") in ids:
            return True
        if wanted and plan_name_matches(row.get("plan_name"), wanted):
            return True
        return False
    return True


def _per_second(price, credits, row):
    return price / credits * row["credits_per_clip"] / row["clip_seconds"]


def _pair_for_row(deal, row):
    for pair in pairs(deal):
        if row.get("plan") and row["plan"] in (pair.get("full_plan_id"), pair.get("deal_plan_id")):
            return pair
    return None


def blended_price(price_after, price_before, first_months):
    """12-month average monthly price: N months at the sale, then the full price."""
    n = int(first_months)
    return (n * price_after + (12 - n) * price_before) / 12


def adjustment(deal, row, plans):
    """Deal-adjusted math for one row.

    Returns None when the deal does not change how this row should be read.
    `usd` is None for unlimited windows (break-even seconds instead of $0).
    """
    if not row_matches(deal, row):
        return None
    math = deal.get("math")
    cond = conditions(deal)
    base = {
        "deal_id": deal["id"],
        "type": deal["type"],
        "title": deal.get("title") or deal["id"],
        "usd": None,
        "list_usd": None,
        "blended_usd": None,
        "breakeven_seconds": None,
        "plan_price": None,
        "percent": deal.get("percent"),
        "end": deal.get("end"),
        "end_is_estimate": bool(deal.get("end_is_estimate")),
        "standing": bool(cond.get("standing")),
        "code": cond.get("code"),
        "label": "",
        "web_only": bool(cond.get("web_only")),
    }
    if math == "none":
        return None

    if math == "stated" or (
        math is None and deal["type"] in ("api_promo", "percent_off")
        and deal["id"] in (row.get("deal_ids") or [])
        and row.get("list_usd_per_second") is not None
    ):
        if row.get("list_usd_per_second") is None:
            return None
        base["usd"] = row["usd_per_second"]
        base["list_usd"] = row["list_usd_per_second"]
        pct = deal.get("percent")
        base["label"] = f"{pct:g}% off the list rate" if pct is not None else "discounted rate from the vendor page"
        return base

    if math == "percent_of_list":
        list_usd = row.get("list_usd_per_second", row.get("usd_per_second"))
        pct = deal.get("percent")
        if list_usd is None or pct is None:
            return None
        base["list_usd"] = list_usd
        base["usd"] = list_usd * (1 - pct / 100.0)
        base["label"] = f"{pct:g}% off the list rate"
        return base

    if math == "plan_price" or (math is None and deal["type"] in ("plan_sale", "promo_code")):
        pair = _pair_for_row(deal, row)
        plan = plans.get(row.get("plan") or "")
        if not pair or not plan or pair.get("price_after") is None:
            return None
        credits = plan["credits_month"]
        deal_usd = _per_second(pair["price_after"], credits, row)
        list_usd = _per_second(pair["price_before"], credits, row) if pair.get("price_before") is not None else row["usd_per_second"]
        base["usd"] = deal_usd
        base["list_usd"] = list_usd
        base["plan_price"] = pair["price_after"]
        n = cond.get("first_months")
        if n and pair.get("price_before") is not None:
            blended = blended_price(pair["price_after"], pair["price_before"], n)
            base["blended_usd"] = _per_second(blended, credits, row)
            base["label"] = (
                f"first {n} months at ${pair['price_after']:g}/mo, then ${pair['price_before']:g}/mo"
            )
        elif cond.get("annual_only") or cond.get("standing"):
            before = pair.get("price_before")
            base["label"] = (
                f"annual billing ${pair['price_after']:g}/mo"
                + (f" vs ${before:g}/mo monthly" if before is not None else "")
            )
        else:
            base["label"] = f"sale price ${pair['price_after']:g}/mo"
        if cond.get("code"):
            base["label"] += f", code {cond['code']}"
        return base

    if math == "bonus" or (math is None and deal["type"] == "bonus_credits"):
        plan = plans.get(row.get("plan") or "")
        bonus = deal.get("bonus_credits")
        if not plan or not bonus:
            return None
        price = plan["usd_month"]
        credits = plan["credits_month"] + bonus
        base["usd"] = _per_second(price, credits, row)
        base["list_usd"] = row["usd_per_second"]
        base["label"] = f"includes {bonus:g} bonus credits"
        return base

    if math == "unlimited" or (math is None and deal["type"] == "unlimited_window"):
        if row.get("kind") != "plan":
            return None
        plan = plans.get(row.get("plan") or "")
        normal = row.get("usd_per_second") or 0
        if not plan or normal <= 0:
            return None
        price = plan["usd_month"]
        base["plan_price"] = price
        base["list_usd"] = normal
        base["breakeven_seconds"] = price / normal
        days = cond.get("signup_window_days")
        where = row.get("plan_name") or plan.get("plan") or "this plan"
        window = f" for {days} days" if days else ""
        base["label"] = (
            f"Unlimited{window} on {where} (${price:g}). "
            f"Worth it after {base['breakeven_seconds']:.0f} seconds versus {normal:g}/s."
        )
        return base
    return None


def row_adjustments(row, deals, plans, today):
    out = []
    for deal in deals:
        if not is_current(deal, today):
            continue
        adj = adjustment(deal, row, plans)
        if adj:
            out.append(adj)
    return out


def best_deal_price(rows, deals, plans, today):
    """Lowest deal-adjusted $/s for a set of rows. Ignores unlimited (no $0)."""
    best = None
    for row in rows:
        for adj in row_adjustments(row, deals, plans, today):
            if adj["usd"] is None:
                continue
            if best is None or adj["usd"] < best["usd"]:
                best = dict(adj, row=row)
    return best


def stated_examples(deal, rows, limit=4):
    examples = []
    for row in rows:
        if deal["id"] not in (row.get("deal_ids") or []):
            continue
        if row.get("list_usd_per_second") is None:
            continue
        examples.append({
            "label": f"{row.get('variant')} {row.get('resolution')}".strip(),
            "usd": row["usd_per_second"],
            "list_usd": row["list_usd_per_second"],
            "platform": row.get("platform"),
            "model": row.get("model"),
        })
    examples.sort(key=lambda e: e["usd"])
    return examples[:limit]


def plan_examples(deal, rows, plans, limit=4):
    examples = []
    for pair in pairs(deal):
        if pair.get("price_after") is None:
            continue
        item = {
            "label": pair.get("plan") or "Plan",
            "price_before": pair.get("price_before"),
            "price_after": pair.get("price_after"),
            "percent": pair.get("percent", deal.get("percent")),
        }
        sample = None
        for row in rows:
            if row.get("plan") not in (pair.get("full_plan_id"), pair.get("deal_plan_id")):
                continue
            if row.get("kind") != "plan":
                continue
            adj = adjustment(dict(deal, math="plan_price"), row, plans)
            if not adj or adj["usd"] is None:
                continue
            if sample is None or adj["usd"] < sample["usd"]:
                sample = {
                    "model": row.get("model"),
                    "resolution": row.get("resolution"),
                    "usd": adj["usd"],
                    "list_usd": adj["list_usd"],
                    "blended_usd": adj["blended_usd"],
                }
        if sample:
            item.update(sample)
        examples.append(item)
    return examples[:limit]


def unlimited_examples(deal, rows, plans, limit=5):
    """One break-even per qualifying plan, using that plan's cheapest matching row."""
    best = {}
    probe = dict(deal, math="unlimited", show_on_rows=True)
    for row in rows:
        adj = adjustment(probe, row, plans)
        if not adj or adj["breakeven_seconds"] is None:
            continue
        key = row.get("plan") or row.get("plan_name")
        prev = best.get(key)
        if prev is None or adj["list_usd"] < prev["list_usd"]:
            best[key] = {
                "plan": row.get("plan_name") or key,
                "plan_price": adj["plan_price"],
                "list_usd": adj["list_usd"],
                "breakeven_seconds": adj["breakeven_seconds"],
                "model": row.get("model"),
                "resolution": row.get("resolution"),
                "label": adj["label"],
            }
    examples = sorted(best.values(), key=lambda e: e["breakeven_seconds"])
    return examples[:limit]


def calculator_map(deals, plans, today):
    """Per-plan overrides for the calculator's "apply today's deals" toggle."""
    out = {}
    live = [d for d in deals if is_current(d, today)]
    for pid, plan in plans.items():
        entry = {"price": None, "bonus_credits": 0, "blended_price": None, "notes": [], "unlimited": []}
        for deal in live:
            math = deal.get("math")
            cond = conditions(deal)
            if deal["type"] in ("plan_sale", "promo_code") and math != "none":
                for pair in pairs(deal):
                    if pair.get("full_plan_id") == pid and pair.get("price_after") is not None:
                        entry["price"] = pair["price_after"]
                        note = f"{deal.get('title')}: ${pair['price_after']:g}/mo instead of ${pair['price_before']:g}/mo"
                        n = cond.get("first_months")
                        if n and pair.get("price_before") is not None:
                            blended = blended_price(pair["price_after"], pair["price_before"], n)
                            entry["blended_price"] = round(blended, 2)
                            note += (
                                f". First {n} months, then ${pair['price_before']:g}/mo. "
                                f"12-month blended ${blended:.2f}/mo."
                            )
                        if cond.get("code"):
                            note += f" Code {cond['code']}."
                        entry["notes"].append(note)
                    elif pair.get("deal_plan_id") == pid:
                        entry["notes"].append(f"{deal.get('title')} is already the price of this plan.")
            if deal["type"] == "bonus_credits" and deal.get("bonus_credits") and math != "none":
                if plan.get("platform") in vendor_platforms(deal.get("vendor")) and plan_name_matches(plan.get("plan"), deal.get("plans") or []):
                    entry["bonus_credits"] += deal["bonus_credits"]
                    entry["notes"].append(f"{deal.get('title')}: +{deal['bonus_credits']:g} credits.")
            if deal["type"] == "unlimited_window" and math != "none":
                if plan.get("platform") not in vendor_platforms(deal.get("vendor")):
                    continue
                wanted = deal.get("plans") or []
                if wanted and not plan_name_matches(plan.get("plan"), wanted):
                    continue
                if not wanted and not (deal.get("models") or []):
                    continue
                entry["unlimited"].append({
                    "id": deal["id"],
                    "title": deal.get("title"),
                    "models": deal.get("models") or [],
                    "variants": deal.get("variants") or [],
                    "max_resolution": cond.get("max_resolution"),
                    "days": cond.get("signup_window_days"),
                    "web_only": bool(cond.get("web_only")),
                    "end": deal.get("end"),
                    "end_is_estimate": bool(deal.get("end_is_estimate")),
                })
        if entry["price"] is not None or entry["bonus_credits"] or entry["unlimited"] or entry["notes"]:
            out[pid] = entry
    return out


def normalize_snippet(text):
    return re.sub(r"\s+", " ", text).strip()


def extract_snippets(text, limit=40):
    found = []
    seen = set()
    for match in OFFER_RE.finditer(text or ""):
        raw = normalize_snippet(match.group(0))
        if len(raw) < 8:
            continue
        key = raw.lower()
        if key in seen:
            continue
        seen.add(key)
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
        found.append({"sha": digest, "text": raw[:240]})
        if len(found) >= limit:
            break
    return found


def scan_pricing_pages(fetch, doc, today):
    """Diff offer snippets on vendor pricing pages.

    New or removed text is written to deal_candidates.json. Nothing is added
    to the live deals list. The first successful fetch of a page stores a
    baseline and reports no candidates.
    """
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    candidates = []
    pages = []
    for page in doc.get("watch") or []:
        info = {"id": page["id"], "vendor": page.get("vendor"), "url": page["url"], "status": "fetched"}
        path = os.path.join(SNAPSHOT_DIR, page["id"] + ".json")
        try:
            text = fetch(page)
        except Exception as exc:
            info["status"] = "error"
            info["error"] = str(exc)[:200]
            pages.append(info)
            continue
        current = extract_snippets(text)
        info["snippets"] = len(current)
        current_map = {s["sha"]: s["text"] for s in current}
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump({"id": page["id"], "url": page["url"], "saved": today, "snippets": current}, f, indent=1)
                f.write("\n")
            info["baseline"] = True
            pages.append(info)
            continue
        previous = json.load(open(path))
        prev_map = {s["sha"]: s["text"] for s in previous.get("snippets") or []}
        for sha, snippet in current_map.items():
            if sha not in prev_map:
                candidates.append({
                    "status": "unconfirmed",
                    "vendor": page.get("vendor"),
                    "url": page["url"],
                    "sha": sha,
                    "snippet": snippet,
                    "seen": today,
                })
        for sha, snippet in prev_map.items():
            if sha not in current_map:
                candidates.append({
                    "status": "possible_end",
                    "vendor": page.get("vendor"),
                    "url": page["url"],
                    "sha": sha,
                    "snippet": snippet,
                    "seen": today,
                })
        with open(path, "w") as f:
            json.dump({"id": page["id"], "url": page["url"], "saved": today, "snippets": current}, f, indent=1)
            f.write("\n")
        pages.append(info)
    report = {
        "generated": today,
        "note": "Unconfirmed. These snippets are not published as deals.",
        "pages": pages,
        "candidates": candidates,
    }
    with open(CANDIDATES_PATH, "w") as f:
        json.dump(report, f, indent=1, ensure_ascii=False)
        f.write("\n")
    return report
