#!/usr/bin/env python3
"""Data pages (/compare/, /cost/, /platforms/) carry a visible FAQ and a FAQPage whose questions and answers match it.

Run after the build: python3 scripts/build_site.py && python3 scripts/test_data_page_faq.py
"""
import html as h, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare_pages as cp, cost_pages as cost, platform_pages as plat
DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dist")
errors = []
paths = [p["path"] for p in cp.PAIRS + cost.COST_PAGES + plat.PLATFORM_PAGES]
for path in paths:
    src = open(os.path.join(DIST, path.strip("/"), "index.html"), encoding="utf-8").read()
    faq = [json.loads(m) for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', src, re.S)]
    faq = [o for o in faq if o.get("@type") == "FAQPage"]
    if len(faq) != 1:
        errors.append(f"{path}: {len(faq)} FAQPage blocks, want 1"); continue
    block = src.split("<h2>FAQ</h2>", 1)
    if len(block) != 2:
        errors.append(f"{path}: no visible FAQ"); continue
    visible = h.unescape(re.sub(r"<[^>]+>", "", block[1].split("</div>", 1)[0]))
    for q in faq[0]["mainEntity"]:
        if q["name"] not in visible or q["acceptedAnswer"]["text"] not in visible:
            errors.append(f"{path}: FAQPage question not shown as written: {q['name']}")
    if len(faq[0]["mainEntity"]) < 2:
        errors.append(f"{path}: FAQ too short")
if errors:
    print("\n".join(errors)); sys.exit(1)
print(f"data page FAQ ok ({len(paths)} pages)")
