#!/usr/bin/env python3
"""ClipCost daily price checker.

Re-fetches every source in data/prices.json, re-reads each tracked number using
the row's 'needle' pattern and compares it with the stored value.

  python3 scripts/update_prices.py            # check only, write data/check_report.json
  python3 scripts/update_prices.py --apply    # also update API rows that changed and log them
  python3 scripts/update_prices.py --only fal_wan3,runway

Exit code: 0 = nothing changed, 1 = changes or missing numbers found (review!), 2 = fetch errors.
'render' sources need Chrome + node (scripts/render.mjs, puppeteer-core). 'manual' sources are listed for a human.
"""
import json, re, sys, os, subprocess, datetime, argparse
import requests
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "prices.json")
CHANGES = os.path.join(ROOT, "data", "changes.json")
REPORT = os.path.join(ROOT, "data", "check_report.json")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36 ClipCostBot/0.1"
NUM = r"(\d[\d,]*(?:\s?\.\s?\d+)?\s?[KM]?)"
XNUM = r"\d[\d,]*(?:\s?\.\s?\d+)?\s?[KM]?"

def collapse(t): return re.sub(r"\s+", " ", t)

def fetch(src):
    if src["fetch"] == "static":
        r = requests.get(src["url"], headers={"User-Agent": UA}, timeout=40)
        r.raise_for_status()
        return collapse(BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True))
    if src["fetch"] == "render":
        out = subprocess.run(["node", os.path.join(ROOT, "scripts", "render.mjs"), src["url"], "5000"],
                             capture_output=True, text=True, timeout=150)
        if len(out.stdout) < 500: raise RuntimeError("render returned too little text")
        return collapse(out.stdout)
    raise RuntimeError("manual source")

def needle_re(needle):
    parts = re.split(r"(\{N\}|\{X\})", needle)
    rx = ""
    for p in parts:
        if p == "{N}": rx += NUM
        elif p == "{X}": rx += XNUM
        else: rx += r"\s*".join(re.escape(w) for w in p.split(" ")) if p.strip() else r"\s*"
    return re.compile(rx)

def parse(s):
    s = s.replace(" ", "").replace(",", "")
    mult = 1
    if s.endswith("K"): mult, s = 1e3, s[:-1]
    elif s.endswith("M"): mult, s = 1e6, s[:-1]
    return float(s) * mult

def check(text, chk):
    m = needle_re(chk["needle"]).search(text)
    if not m: return "missing", None
    v = parse(m.group(1))
    return ("ok" if abs(v - float(chk["expect"])) <= 1e-9 * max(1, abs(v)) else "changed"), v

def stamp_checked(db, texts, findings, today):
    """Re-date rows whose own checks passed. A plan-price finding blocks rows derived from that plan."""
    bad = {f["id"] for f in findings}
    bad_plans = {f["id"] for f in findings if f.get("kind") == "plan"}
    for r in db["rows"]:
        if r.get("source") not in texts or r["id"] in bad: continue
        if r.get("kind") == "plan" and r.get("plan") in bad_plans: continue
        r["checked"] = today
    for pid, p in db["plans"].items():
        if p.get("source") in texts and pid not in bad_plans:
            p["checked"] = today

def expire_promos(db, today, log):
    """Remove promo rows whose end date has passed and record that in the change log."""
    kept, expired = [], []
    for r in db["rows"]:
        if r.get("promo_until") and r["promo_until"] < today:
            expired.append(r)
            log.append({"date": today, "row": r["id"], "model": r.get("model"), "platform": r.get("platform"),
                        "variant": r.get("variant"), "resolution": r.get("resolution"), "source_url": r.get("source_url"),
                        "promo_until": r["promo_until"], "type": "promo_expired",
                        "text": f"{r.get('variant')} promo ended {r['promo_until']}."})
        else:
            kept.append(r)
    db["rows"] = kept
    return expired

def full_check_succeeded(db, report, only):
    if only: return False
    for sid, src in db["sources"].items():
        if src.get("fetch") == "manual": continue
        if report["sources"].get(sid, {}).get("status") != "fetched": return False
    return True

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true"); ap.add_argument("--only")
    a = ap.parse_args()
    db = json.load(open(DATA))
    today = datetime.date.today().isoformat()
    only = set(a.only.split(",")) if a.only else None
    texts, report = {}, {"run": datetime.datetime.now().isoformat(timespec="seconds"), "sources": {}, "findings": []}
    for sid, src in db["sources"].items():
        if only and sid not in only: continue
        if src["fetch"] == "manual":
            report["sources"][sid] = {"status": "manual", "url": src["url"], "note": src.get("note", "")}; continue
        try:
            texts[sid] = fetch(src); report["sources"][sid] = {"status": "fetched", "chars": len(texts[sid])}
        except Exception as e:
            report["sources"][sid] = {"status": "error", "error": str(e)[:200]}
        print(f"{sid:12s} {report['sources'][sid]['status']}", file=sys.stderr)

    log = json.load(open(CHANGES)) if os.path.exists(CHANGES) else []
    items = [("row", r) for r in db["rows"]] + [("plan", dict(p, id=k)) for k, p in db["plans"].items()]
    counts = {"ok": 0, "changed": 0, "missing": 0, "skipped": 0}
    for kind, it in items:
        if it["source"] not in texts: counts["skipped"] += 1; continue
        for chk in it["checks"]:
            st, v = check(texts[it["source"]], chk)
            counts[st] += 1
            if st == "ok": continue
            f = {"kind": kind, "id": it["id"], "source": it["source"], "status": st, "needle": chk["needle"],
                 "old": chk["expect"], "new": v, "model": it.get("model"), "platform": it.get("platform"), "variant": it.get("variant", it.get("plan"))}
            report["findings"].append(f)
            if st == "changed" and a.apply and kind == "row" and it["kind"] == "api":
                row = next(r for r in db["rows"] if r["id"] == it["id"])
                old_usd = row["usd_per_second"]
                factor = old_usd / chk["expect"] if chk["expect"] else 1
                chk_db = next(c for c in row["checks"] if c["needle"] == chk["needle"])
                chk_db["expect"] = v; row["usd_per_second"] = round(v * factor, 5); row["checked"] = today
                log.append({"date": today, "row": row["id"], "model": row["model"], "platform": row["platform"],
                            "variant": row["variant"], "resolution": row["resolution"], "old_usd_per_second": old_usd,
                            "new_usd_per_second": row["usd_per_second"], "source_url": row["source_url"], "type": "price"})
    # Re-date only rows whose own checks passed. Plan rows stay stale when the plan price itself changed.
    stamp_checked(db, texts, report["findings"], today)
    expired = expire_promos(db, today, log)
    for r in expired:
        report["findings"].append({"kind": "row", "id": r["id"], "status": "promo_expired", "promo_until": r["promo_until"]})
    if full_check_succeeded(db, report, only):
        db["last_full_check"] = today
    report["counts"] = counts
    json.dump(report, open(REPORT, "w"), indent=1, ensure_ascii=False)
    json.dump(db, open(DATA, "w"), indent=1, ensure_ascii=False)
    json.dump(log, open(CHANGES, "w"), indent=1, ensure_ascii=False)
    print(json.dumps(counts), file=sys.stderr)
    for f in report["findings"]: print("FLAG", json.dumps(f, ensure_ascii=False), file=sys.stderr)
    errs = any(s["status"] == "error" for s in report["sources"].values())
    sys.exit(2 if errs else (1 if report["findings"] else 0))

if __name__ == "__main__": main()
