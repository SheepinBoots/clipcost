#!/usr/bin/env python3
"""Prove the MCP quote and deal map match the site calculator."""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deals as dealmod
import variations as V

PRICES = os.path.join(ROOT, "data", "prices.json")
DEALS = os.path.join(ROOT, "data", "deals.json")
TODAY = "2026-11-05"


def main():
    db = json.load(open(PRICES))
    deal_doc = dealmod.load(DEALS)
    cases = []
    for row in db["rows"]:
        rid = row["id"]
        cases.append({"id": rid})
        cases.append({"id": rid, "seconds": 10})
        cases.append({"id": rid, "resolution": "720p"})
        cases.append({"id": rid, "audio": "with"})
        cases.append({"id": rid, "input": "t2v", "seconds": 5})
    payload = {
        "today": TODAY,
        "pricesPath": PRICES,
        "dealsPath": DEALS,
        "cases": cases,
        "costs": [
            {"model": "wan-3-0", "seconds": 10, "resolution": "720p", "provider": "fal"},
            {"model": "wan-3-0", "seconds": 5, "resolution": "480p", "plan": "hf-starter"},
            {"model": "wan-3-0", "seconds": 10, "resolution": "480p", "plan": "hf-starter"},
        ],
    }
    proc = subprocess.run(
        ["npx", "tsx", "src/parity-cli.ts"],
        input=json.dumps(payload),
        text=True,
        cwd=os.path.join(ROOT, "mcp-server"),
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr or proc.stdout or "parity cli failed")
    got = json.loads(proc.stdout)
    rows = {row["id"]: row for row in db["rows"]}
    mismatches = []
    for case, result in zip(cases, got["quotes"]):
        expect = V.quote(
            rows[case["id"]],
            seconds=case.get("seconds"),
            audio=case.get("audio"),
            input_type=case.get("input"),
            resolution=case.get("resolution"),
        )
        if result.get("status") != expect["status"]:
            mismatches.append((case, "status", expect, result))
            continue
        if "usd_per_second" in expect or "usd_per_second" in result:
            ev = expect.get("usd_per_second")
            gv = result.get("usd_per_second")
            if ev is None or gv is None or abs(ev - gv) > 1e-12:
                mismatches.append((case, "usd", expect, result))
        if result.get("detail", "") != expect.get("detail", ""):
            mismatches.append((case, "detail", expect, result))
    if mismatches:
        sample = mismatches[0]
        raise SystemExit(f"{len(mismatches)} quote mismatches. First: {sample[0]} {sample[1]}\nexpect {sample[2]}\ngot {sample[3]}")

    expect_map = dealmod.calculator_map(deal_doc["deals"], db["plans"], TODAY)
    if _norm(expect_map) != _norm(got["map"]):
        raise SystemExit("calculator deal map does not match\n" + _first_diff(_norm(expect_map), _norm(got["map"])))

    priced = got["costs"][0]["priced"]
    fal = next(row for row in priced if row.get("platform") == "fal" and row.get("resolution") == "720p")
    if abs(fal["usd_per_second"] - 0.10) > 1e-12 or abs(fal["total_usd"] - 1.0) > 1e-12:
        raise SystemExit(f"fal 10s total is not 10 times $0.10/s: {fal}")
    starter = got["costs"][1]["priced"]
    if len(starter) != 1:
        raise SystemExit(f"hf-starter 5s 480p should price one row, got {len(starter)}")
    rate = (19 / 270) * 5 / 5
    clip = (19 / 270) * 5
    if abs(starter[0]["usd_per_second"] - rate) > 1e-12 or abs(starter[0]["total_usd"] - clip) > 1e-12:
        raise SystemExit(f"starter clip cost does not match the calculator formula: {starter[0]}")
    missing = got["costs"][2]
    if missing["priced"] or not missing["missing"]:
        raise SystemExit(f"a 10s clip on a 5s plan row must not be priced: {missing}")
    print(f"ok mcp parity {len(cases)} quotes, {len(expect_map)} plan deal maps")


def _norm(value):
    return json.loads(json.dumps(value, sort_keys=True))


def _first_diff(expect, got, path="$"):
    if type(expect) != type(got):
        return f"{path} type {type(expect).__name__} != {type(got).__name__}"
    if isinstance(expect, dict):
        for key in sorted(set(expect) | set(got)):
            if key not in expect:
                return f"{path}.{key} unexpected {got[key]!r}"
            if key not in got:
                return f"{path}.{key} missing, expected {expect[key]!r}"
            found = _first_diff(expect[key], got[key], path + "." + key)
            if found:
                return found
        return ""
    if isinstance(expect, list):
        if len(expect) != len(got):
            return f"{path} length {len(expect)} != {len(got)}"
        for i, (left, right) in enumerate(zip(expect, got)):
            found = _first_diff(left, right, f"{path}[{i}]")
            if found:
                return found
        return ""
    if expect != got:
        return f"{path} {expect!r} != {got!r}"
    return ""


if __name__ == "__main__":
    main()
