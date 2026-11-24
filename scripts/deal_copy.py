"""Deal-driven guide copy.

Guides must not hardcode sale wording. They ask this module whether a deal is
live (from data/deals.json, using deals.is_current, which also honors an exact
ends_at) and get the end label in the site's ET-first format. When a deal has
ended, the same helpers give "ended" wording so stale sale text never ships.
"""
import deals as dealmod
from timefmt import et_pt

HF_BF_IDS = (
    "hf-plus-annual",
    "hf-ultra-annual",
    "hf-plus-monthly-first",
    "hf-ultra-monthly-first",
    "hf-ultra-6k-annual",
    "hf-ultra-9k-annual",
    "hf-ultra-6k-monthly-first",
    "hf-ultra-9k-monthly-first",
)


def _deals_by_id(g):
    """Deal records from the build globals, or straight from data/deals.json."""
    if "DEAL_BY_ID" not in g:
        import json
        import os
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "deals.json")
        doc = json.load(open(path, encoding="utf-8"))
        records = doc["deals"] if isinstance(doc, dict) else doc
        g["DEAL_BY_ID"] = {d["id"]: d for d in records}
    return g["DEAL_BY_ID"]


def _today(g):
    if not g.get("TODAY"):
        from timefmt import us_today
        g["TODAY"] = us_today().isoformat()
    return g["TODAY"]


def deal(g, deal_id):
    return _deals_by_id(g).get(deal_id)


def is_live(g, deal_id):
    d = deal(g, deal_id)
    return bool(d) and dealmod.is_current(d, _today(g))


def end_label(d, long_month=False):
    """ET-first end label, e.g. 'Nov 24, 2026, 7:00 PM ET (4:00 PM PT)'. None if unknown."""
    if not d:
        return None
    if d.get("ends_at"):
        return et_pt(str(d["ends_at"]), long_month=long_month)
    if d.get("end"):
        return str(d["end"]) + (" (estimated)" if d.get("end_is_estimate") else "")
    return None


def hf_bf(g):
    """State of the Higgsfield Black Friday sale from deals.json."""
    records = [deal(g, i) for i in HF_BF_IDS]
    records = [d for d in records if d]
    live = [d for d in records if dealmod.is_current(d, _today(g))]
    anchor = deal(g, "hf-plus-annual") or (records[0] if records else None)
    return {
        "live": bool(live),
        "deals": {d["id"]: d for d in records},
        "live_ids": [d["id"] for d in live],
        "end": end_label(anchor),
        "end_long": end_label(anchor, long_month=True),
        "ends_at": (anchor or {}).get("ends_at"),
        "source_url": (anchor or {}).get("source_url") or "https://higgsfield.ai/pricing",
        "verified": (anchor or {}).get("verified_date"),
    }


def price_after(state, deal_id):
    d = state["deals"].get(deal_id) or {}
    v = d.get("price_after")
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def price_before(state, deal_id):
    d = state["deals"].get(deal_id) or {}
    v = d.get("price_before")
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def plan_month(g, plan_id):
    """Current catalog plan price ($/mo) from prices.json, or None."""
    p = (g.get("plans") or {}).get(plan_id) or {}
    v = p.get("usd_month")
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def money(v):
    return "unknown" if v is None else f"${v:g}"


def hf_phases_text(state):
    """Past Black Friday phases recorded on the anchor deal (deals.json "phases")."""
    anchor = state["deals"].get("hf-plus-annual") or {}
    bits = []
    for ph in anchor.get("phases") or []:
        if ph.get("ends_at"):
            bits.append(f"{ph.get('label')} ended {et_pt(ph['ends_at'])}")
    return bits


def hf_sale_sentence(state):
    """One plain-text sentence about the Higgsfield Black Friday sale, from deals.json."""
    if state["live"]:
        pa, ua = price_after(state, "hf-plus-annual"), price_after(state, "hf-ultra-annual")
        return (f"Higgsfield's Black Friday sale is live on its pricing page until {state['end']}: "
                f"Plus annual {money(pa)}/mo and Ultra 3K annual {money(ua)}/mo, billed yearly.")
    phases = hf_phases_text(state)
    tail = (" Earlier phase: " + "; ".join(phases) + ".") if phases else ""
    return (f"Higgsfield's Black Friday sale has ended. The last sale phase ended {state['end']}, "
            f"per the sale record on Higgsfield's pricing page, rechecked {state['verified']}.{tail}")


def hf_current_prices(g):
    """Current Higgsfield individual plan prices from prices.json plan records (source and date kept)."""
    out = []
    for pid, label in (("hf-starter", "Starter"), ("hf-plus-monthly", "Plus, monthly billing"),
                       ("hf-plus-annual", "Plus, annual billing"), ("hf-ultra-monthly", "Ultra 3K, monthly billing"),
                       ("hf-ultra-annual", "Ultra 3K, annual billing")):
        p = (g.get("plans") or {}).get(pid) or {}
        out.append({"id": pid, "label": label, "usd_month": plan_month(g, pid),
                    "credits": p.get("credits_month"), "checked": p.get("checked"),
                    "source_url": p.get("source_url") or "https://higgsfield.ai/pricing"})
    return out


def hf_prices_sentence(g):
    bits = []
    for p in hf_current_prices(g):
        cr = f", {p['credits']:,} credits/month" if isinstance(p.get("credits"), int) else ""
        bits.append(f"{p['label']} {money(p['usd_month'])}/mo{cr}")
    checked = max((p["checked"] for p in hf_current_prices(g) if p.get("checked")), default="unknown")
    return "Current plan prices on Higgsfield's pricing page (checked " + checked + "): " + "; ".join(bits) + "."
