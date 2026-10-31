"""Search guides for VidFare.

Imported by scripts/build_site.py after the price helpers exist. Every dollar
figure is rendered from the current price rows. This module does not hard-code
rates, plans, or counts.
"""
import json
from decimal import Decimal, ROUND_HALF_UP


def render(g):
    """Write /guides/ and the four guide pages. `g` is build_site's globals."""
    rows = g["rows"]
    models = g["models"]
    plans = g["plans"]
    db = g["db"]
    rate_money = g["rate_money"]
    cost_money = g["cost_money"]
    higgsfield_intro = g["higgsfield_intro"]
    e = g["e"]
    root = g["root"]
    tag = g["tag"]
    spec_phrase = g["spec_phrase"]
    shown_tier = g["shown_tier"]
    shown_resolution = g["shown_resolution"]
    audio_phrase = g["audio_phrase"]
    assumption_html = g["assumption_html"]
    assumption_text = g["assumption_text"]
    plat_link = g["plat_link"]
    outbound = g["outbound"]
    row_html = g["row_html"]
    THEAD = g["THEAD"]
    deal_badges = g["deal_badges"]
    tick_script = g["tick_script"]
    model_pick = g["model_pick"]
    model_rows = g["model_rows"]
    overall_pick = g["overall_pick"]
    rate_clause = g["rate_clause"]
    outside_higgsfield = g["outside_higgsfield"]
    res_key = g["res_key"]
    checked_line = g["checked_line"]
    HOW_PLAIN = g["HOW_PLAIN"]
    BUDGET_HOW = g["BUDGET_HOW"]
    how_block = g["how_block"]
    guide_page = g["guide_page"]
    cheap_card = g["cheap_card"]
    higgsfield_plan_rows = g["higgsfield_plan_rows"]
    BRAND = g["BRAND"]
    LAST = g["LAST"]
    SITE_URL = g["SITE_URL"]

    best = overall_pick()
    if best is None:
        raise SystemExit("guides need at least one current price row")

    def left_out(item, reason):
        """'Left out: Name (Reason).' The reason starts with a capital."""
        item = (item or "").strip().rstrip(".")
        reason = (reason or "").strip().rstrip(".")
        if reason:
            if reason[0].islower():
                reason = reason[0].upper() + reason[1:]
            return f"Left out: {item} ({reason})."
        return f"Left out: {item}."

    def source_toggle(r):
        parts = []
        if (r.get("math") or "").strip():
            parts.append(e(r["math"].strip()))
        if (r.get("note") or "").strip():
            parts.append(e(r["note"].strip()))
        href, rel = outbound(r["source_url"])
        link = f'<a href="{e(href)}" rel="{rel}" target="_blank">pricing page</a>'
        checked = e(r.get("checked") or "")
        body = " ".join(parts + [link, "· " + checked]).strip()
        return f'<details class="src"><summary>source</summary><div class="math">{body}</div></details>'

    def fit_table(head, row_htmls):
        return f'<div class="tblwrap fit"><table>{head}<tbody>{"".join(row_htmls)}</tbody></table></div>'

    def capped(head, visible_rows, extra_rows, summary):
        shown = fit_table(head, visible_rows)
        if not extra_rows:
            return shown
        return shown + f'<details class="more"><summary>{e(summary)}</summary>{fit_table(head, extra_rows)}</details>'

    def without_promo(r):
        """same = not a promo. A dollar amount is the promo row's list rate. — = promo with no list rate."""
        if r.get("status") != "promo":
            return "same"
        listed = r.get("list_usd_per_second")
        if listed is None:
            return "—"
        return rate_money(listed)

    def other_short(r):
        if r is None:
            return "—"
        promo = ""
        if r.get("status") == "promo" and r.get("promo_until"):
            promo = f' <span class="small">until {e(r["promo_until"])}</span>'
        return (
            f'{rate_money(r["usd_per_second"])}/s {e(r["platform"])} '
            f'{e(shown_resolution(r))}{promo} {tag(r["status"])}'
        )

    def row_index():
        return {r["id"]: i for i, r in enumerate(rows)}

    def by_price(rs):
        index = row_index()
        return sorted(rs, key=lambda r: (r["usd_per_second"], index[r["id"]]))

    def status_cell(r):
        promo = ""
        if r.get("status") == "promo" and r.get("promo_until"):
            promo = f' <span class="small">until {e(r["promo_until"])}</span>'
        return f'{tag(r["status"])}{promo}{deal_badges(r)}'

    def detail_html(r):
        extra = e(r["math"]) if r.get("math") else ""
        if r.get("note"):
            extra += (" " if extra else "") + e(r["note"])
        href, rel = outbound(r["source_url"])
        source = f'<a href="{e(href)}" rel="{rel}" target="_blank">source</a> · {e(r["checked"])}'
        return (extra + " " + source).strip()

    def other_cell(r):
        if r is None:
            return "not in our data"
        promo = ""
        if r.get("status") == "promo" and r.get("promo_until"):
            promo = f' <span class="small">until {e(r["promo_until"])}</span>'
        return (
            f'{rate_money(r["usd_per_second"])}/s on {plat_link(r["platform"], r["source_url"])}'
            f'<div class="small">{e(spec_phrase(r))} {tag(r["status"])}{promo}</div>'
            f'{assumption_html(r)}'
        )

    def plan_price_cell(r):
        pid = r.get("plan")
        if not pid or pid not in plans:
            return "not in our data"
        p = plans[pid]
        month = p.get("usd_month")
        credits = p.get("credits_month")
        if month is None or credits is None:
            return "not in our data"
        billing = (p.get("billing") or "").strip()
        bill = f" · {e(billing)}" if billing else ""
        credit_txt = f"{int(credits):,}" if float(credits).is_integer() else str(credits)
        return f"{cost_money(month)}/mo · {credit_txt} credits{bill}"

    def with_nonpromo(label, picked, alt):
        text = f"The cheapest {label} rate we track is {rate_clause(picked)}."
        if alt is not None and alt is not picked:
            text += f" Without promos, the cheapest {label} rate is {rate_clause(alt)}."
        return text

    def format_seconds(n):
        if float(n).is_integer():
            return f"{int(n):,}"
        return f"{n:,.2f}"

    def project_cost_sentence(minutes, mult=3):
        picked = overall_pick()
        finished = minutes * 60
        seconds = finished * mult
        total = picked["usd_per_second"] * seconds
        unit = "minute" if minutes == 1 else "minutes"
        return (
            f"{minutes:g} finished {unit} ({format_seconds(finished)} seconds) at {mult:g}x retries "
            f"is {format_seconds(seconds)} billed seconds. "
            f"At the lowest rate we track, {rate_clause(picked)}, that comes to {cost_money(total)}."
        )

    def count_text(n):
        """Counts derived from credit math, rounded half up to 2 decimal places."""
        q = Decimal(str(n)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        sign = "-" if q < 0 else ""
        whole, frac = f"{abs(q):.2f}".split(".")
        if frac == "00":
            return sign + f"{int(whole):,}"
        if frac.endswith("0"):
            return sign + f"{int(whole):,}.{frac[0]}"
        return sign + f"{int(whole):,}.{frac}"

    def credit_num(n):
        d = Decimal(str(n))
        if d == d.to_integral():
            return f"{int(d):,}"
        return format(d, "f").rstrip("0").rstrip(".")

    def non_hf_indexes():
        best_model = {}
        best_res = {}
        for r in rows:
            if not outside_higgsfield(r):
                continue
            cur = best_model.get(r["model"])
            if cur is None or r["usd_per_second"] < cur["usd_per_second"]:
                best_model[r["model"]] = r
            key = (r["model"], res_key(r))
            cur = best_res.get(key)
            if cur is None or r["usd_per_second"] < cur["usd_per_second"]:
                best_res[key] = r
        return best_model, best_res

    def crumb(tail):
        return f'<p class="small"><a href="{root("/guides/")}">Guides</a> › {e(tail)}</p>'

    def write_index():
        entries = [
            ("What is the cheapest way to use Wan 3.0?", "/guides/cheapest-wan-3-0/", g["wan_blurb"]()),
            ("What is the cheapest AI video generator right now?", "/guides/cheapest-ai-video-generator/", g["cheapest_blurb"]()),
            ("Is Higgsfield worth it?", "/guides/is-higgsfield-worth-it/", g["hf_blurb"]()),
            ("How much does a 3-minute AI video cost?", "/guides/ai-video-project-budget/", project_cost_sentence(3)),
        ]
        blocks = []
        faqs = []
        for question, path, answer in entries:
            blocks.append(
                f'<h2>{e(question)}</h2><p>{e(answer)} <a href="{root(path)}">Full guide</a></p>'
            )
            faqs.append((question, answer))
        faqs.append(("How do we calculate this?", HOW_PLAIN))
        body = (
            f'<p class="small"><a href="{root("/")}">Prices</a> › Guides</p>'
            "<h1>Guides</h1>"
            "<p class=\"lead\">Four comparisons built from the same price rows as the homepage.</p>"
            f"{checked_line()}"
            + "".join(blocks)
            + how_block()
        )
        guide_page(
            "/guides/",
            f"AI video price guides | {BRAND}",
            f"Cheapest Wan 3.0, cheapest model, Higgsfield plan rates, and a project budget. Built from VidFare price rows. Last checked {LAST}.",
            body,
            faqs,
        )

    def write_wan():
        base = model_pick("wan-3-0")
        prime = model_pick("wan-3-0-prime")
        if base is None or prime is None:
            raise SystemExit("Wan 3.0 guides need a current row for Wan 3.0 and Wan 3.0 Prime")
        base_alt = model_pick("wan-3-0", False)
        prime_alt = model_pick("wan-3-0-prime", False)
        wan_rs = by_price([r for r in rows if r["model"] in ("wan-3-0", "wan-3-0-prime")])
        have = {r["platform"] for r in wan_rs}
        tracked = sorted({r["platform"] for r in rows})
        parts = []
        missing = [p for p in tracked if p not in have]
        if missing:
            parts.append("No Wan 3.0 or Wan 3.0 Prime row for " + ", ".join(missing) + ".")
        base_plats = {r["platform"] for r in model_rows("wan-3-0")}
        prime_plats = {r["platform"] for r in model_rows("wan-3-0-prime")}
        only_base = sorted(base_plats - prime_plats)
        only_prime = sorted(prime_plats - base_plats)
        if only_base:
            parts.append("Wan 3.0 rows and no Wan 3.0 Prime row for " + ", ".join(only_base) + ".")
        if only_prime:
            parts.append("Wan 3.0 Prime rows and no Wan 3.0 row for " + ", ".join(only_prime) + ".")
        for item in db.get("unverified") or []:
            blob = ((item.get("item") or "") + " " + (item.get("reason") or "")).lower()
            if "wan" in blob:
                parts.append(left_out(item.get("item"), item.get("reason")))
        gap = " ".join(parts) if parts else "Every platform in the current price data has a Wan 3.0 or Wan 3.0 Prime row."
        lead = (
            f"The cheapest Wan 3.0 rate we track is {rate_clause(base)}. "
            f"The cheapest Wan 3.0 Prime rate is {rate_clause(prime)}."
        )
        q_base = "What is the cheapest way to use Wan 3.0?"
        q_prime = "What is the cheapest way to use Wan 3.0 Prime?"
        q_gap = "Which platforms have no Wan 3.0 price here?"
        a_base = with_nonpromo("Wan 3.0", base, base_alt)
        a_prime = with_nonpromo("Wan 3.0 Prime", prime, prime_alt)
        faqs = [
            (q_base, a_base),
            (q_prime, a_prime),
            (q_gap, gap),
            ("How do we calculate this?", HOW_PLAIN),
        ]
        wan_head = (
            "<thead><tr><th>Model</th><th>Where</th><th>Variant</th><th>Tier</th>"
            "<th>Res</th><th>Audio</th><th>$/s</th><th>Status</th><th>No promo</th><th>Source</th></tr></thead>"
        )
        wan_rows_html = []
        for r in wan_rs:
            promo_cell = without_promo(r)
            promo_cls = ' class="num"' if promo_cell.startswith("$") else ""
            wan_rows_html.append(
                "<tr>"
                f'<td><a href="{root(f"/models/{r["model"]}/")}">{e(models[r["model"]]["name"])}</a></td>'
                f'<td>{plat_link(r["platform"], r["source_url"])}</td>'
                f'<td>{e(r["variant"])}</td>'
                f'<td>{e(shown_tier(r))}</td>'
                f'<td>{e(shown_resolution(r))}</td>'
                f'<td>{e(audio_phrase(r))}</td>'
                f'<td class="num">{rate_money(r["usd_per_second"])}{assumption_html(r)}</td>'
                f'<td>{status_cell(r)}</td>'
                f'<td{promo_cls}>{promo_cell}</td>'
                f'<td>{source_toggle(r)}</td>'
                "</tr>"
            )
        wan_rest = wan_rows_html[15:]
        wan_table = capped(
            wan_head,
            wan_rows_html[:15],
            wan_rest,
            f"Show the other {len(wan_rest)} Wan prices",
        )
        body = f"""{crumb("Wan 3.0")}
<h1>Cheapest way to use Wan 3.0 (and Wan 3.0 Prime): API vs Higgsfield vs Krea vs others</h1>
<p class="lead">{e(lead)}</p>
{checked_line()}
<div class="cards">{cheap_card("Wan 3.0", base, base_alt)}{cheap_card("Wan 3.0 Prime", prime, prime_alt)}</div>
<h2>{e(q_base)}</h2><p>{e(a_base)}</p>
<h2>{e(q_prime)}</h2><p>{e(a_prime)}</p>
<h2>Every tracked Wan 3.0 and Wan 3.0 Prime price</h2>
<p>{len(wan_rs)} live rows, lowest dollars per second first. The first 15 are shown here.</p>
<p class="small">No promo: same means this row is not a promo. A dollar amount is the list rate stored on that promo row. — means the row is a promo and the price file has no list rate.</p>
{wan_table}
<h2>{e(q_gap)}</h2><p>{e(gap)}</p>
{how_block()}
{tick_script()}"""
        guide_page(
            "/guides/cheapest-wan-3-0/",
            f"Cheapest way to use Wan 3.0 (and Wan 3.0 Prime): API vs Higgsfield vs Krea vs others | {BRAND}",
            (
                f"Cheapest Wan 3.0 is {rate_money(base['usd_per_second'])}/s on {base['platform']} "
                f"({shown_resolution(base)}, {g['status_phrase'](base)}). "
                f"Wan 3.0 Prime is {rate_money(prime['usd_per_second'])}/s on {prime['platform']}. "
                f"Last checked {LAST}."
            ),
            body,
            faqs,
        )

    def write_cheapest():
        picks = []
        for i, (slug, meta) in enumerate(models.items()):
            picked = model_pick(slug)
            if picked is None:
                continue
            picks.append((picked["usd_per_second"], i, slug, meta, picked, model_pick(slug, False)))
        picks.sort()
        best_row = picks[0][4]
        alt = overall_pick(False)
        lead = f"The lowest rate we track is {rate_clause(best_row)}."
        if alt is not None and alt is not best_row:
            second = f"Without promos, the lowest rate is {rate_clause(alt)}."
        else:
            second = "Each model below is that homepage pick: the lowest live dollars per second, with a promo or an approximate row labelled when it wins."
        q = "What is the cheapest AI video generator right now?"
        q_each = "What is the cheapest option for each model?"
        answer = lead + " " + second
        head = (
            "<thead><tr><th>Model</th><th>$/s</th><th>Where</th><th>Tier</th>"
            "<th>Res</th><th>Audio</th><th>Status</th><th>No promo</th><th>Source</th></tr></thead>"
        )
        body_rows = []
        for _usd, _i, slug, meta, picked, alt_row in picks:
            if alt_row is None:
                without = "—"
            elif alt_row is picked:
                without = "same"
            else:
                without = other_short(alt_row)
            body_rows.append(
                f'<tr data-price-id="{e(picked["id"])}">'
                f'<td><a href="{root(f"/models/{slug}/")}">{e(meta["name"])}</a></td>'
                f'<td class="num">{rate_money(picked["usd_per_second"])}{assumption_html(picked)}</td>'
                f'<td>{plat_link(picked["platform"], picked["source_url"])}</td>'
                f'<td>{e(shown_tier(picked))}</td>'
                f'<td>{e(shown_resolution(picked))}</td>'
                f'<td>{e(audio_phrase(picked))}</td>'
                f'<td>{status_cell(picked)}</td>'
                f'<td>{without}</td>'
                f'<td>{source_toggle(picked)}</td>'
                "</tr>"
            )
        gap_items = db.get("unverified") or []
        if gap_items:
            gap_html = '<ul class="small">' + "".join(
                f'<li>{e(item["item"])}: {e(item["reason"])}</li>' for item in gap_items
            ) + "</ul>"
        else:
            gap_html = "<p>The price data has no separate unconfirmed-item list.</p>"
        faqs = [
            (q, answer),
            (q_each, "The table is one row per model: the lowest live dollars per second, the same pick as the homepage cards."),
            ("How do we calculate this?", HOW_PLAIN),
        ]
        body = f"""{crumb("Cheapest by model")}
<h1>Cheapest AI video generator right now, by model</h1>
<p class="lead">{e(lead)} {e(second)}</p>
{checked_line()}
<div class="cards">{cheap_card("Lowest rate we track", best_row, alt)}</div>
<h2>{e(q)}</h2><p>{e(answer)}</p>
<h2>{e(q_each)}</h2>
<p>One row per model, lowest dollars per second first. A promo keeps its end date.</p>
<p class="small">No promo: same means that pick is not a promo. Otherwise the cell is the cheapest non-promo rate. — means there is no non-promo row.</p>
{fit_table(head, body_rows)}
<h2>What prices are not in this list?</h2>
<p>These items are in the price file as unconfirmed, so they are not given a dollars-per-second row here.</p>
{gap_html}
{how_block()}
{tick_script()}"""
        guide_page(
            "/guides/cheapest-ai-video-generator/",
            f"Cheapest AI video generator right now, by model | {BRAND}",
            (
                f"The lowest rate we track is {rate_money(best_row['usd_per_second'])}/s for "
                f"{models[best_row['model']]['name']} on {best_row['platform']}. "
                f"Cheapest option for each model. Last checked {LAST}."
            ),
            body,
            faqs,
        )

    def write_higgsfield():
        plan_rows = higgsfield_plan_rows()
        api_rows = [r for r in rows if r["platform"] == "Higgsfield API"]
        best_model, best_res = non_hf_indexes()
        plan_order = {pid: i for i, pid in enumerate(plans)}
        model_order = {slug: i for i, slug in enumerate(models)}
        plan_rows = sorted(
            plan_rows,
            key=lambda r: (
                plan_order.get(r.get("plan"), 999),
                model_order.get(r["model"], 999),
                r["usd_per_second"],
                r["id"],
            ),
        )
        if plan_rows:
            lo = min(plan_rows, key=lambda r: (r["usd_per_second"], r["id"]))
            hi = max(plan_rows, key=lambda r: (r["usd_per_second"], r["id"]))
            lead = higgsfield_intro(lo, hi)
            q_worth = "Is Higgsfield worth it?"
            a_worth = (
                lead
                + " The table sets each plan rate next to the cheapest non-Higgsfield rate for that model."
            )
        else:
            lo = hi = None
            lead = "No Higgsfield plan rate is in the current price data. Nothing below invents one."
            q_worth = "Is Higgsfield worth it?"
            a_worth = lead
        q_plans = "What does each Higgsfield plan cost per second?"
        q_api = "What does the Higgsfield API cost per second?"
        q_gap = "Which models have no Higgsfield plan price?"
        parts = []
        plan_models = {r["model"] for r in plan_rows}
        api_models = {r["model"] for r in api_rows}
        no_hf = [models[s]["name"] for s in models if s not in plan_models and s not in api_models]
        api_only = [models[s]["name"] for s in models if s not in plan_models and s in api_models]
        if no_hf:
            parts.append("No Higgsfield plan or API row for " + ", ".join(no_hf) + ".")
        if api_only:
            parts.append("A Higgsfield API row and no Higgsfield plan row for " + ", ".join(api_only) + ".")
        by_plan = {}
        for r in plan_rows:
            by_plan.setdefault(r.get("plan"), set()).add(r["model"])
        union = set()
        for have in by_plan.values():
            union |= have
        for pid, p in plans.items():
            if p.get("platform") != "Higgsfield":
                continue
            missing_names = [models[s]["name"] for s in models if s in union and s not in by_plan.get(pid, set())]
            if missing_names:
                parts.append(f"{p['plan']}: no row for " + ", ".join(missing_names) + ".")
        for item in db.get("unverified") or []:
            blob = ((item.get("item") or "") + " " + (item.get("reason") or "")).lower()
            if "higgsfield" in blob:
                parts.append(left_out(item.get("item"), item.get("reason")))
        gap = " ".join(parts) if parts else "Every model we track has a Higgsfield plan row."
        plan_head = (
            "<thead><tr><th>Plan</th><th>Price</th><th>Model</th><th>Res</th><th>Audio</th>"
            "<th>$/s</th><th>Status</th><th>Other</th><th>Same res</th><th>Source</th></tr></thead>"
        )

        def plan_price_short(r):
            pid = r.get("plan")
            if not pid or pid not in plans or plans[pid].get("usd_month") is None:
                return "—"
            p = plans[pid]
            credits = p.get("credits_month")
            credit = f'<div class="small">{int(credits):,} credits</div>' if credits else ""
            return f'{cost_money(p["usd_month"])}/mo{credit}'

        def plan_tr(r):
            other = best_model.get(r["model"])
            same = best_res.get((r["model"], res_key(r)))
            return (
                f'<tr data-price-id="{e(r["id"])}">'
                f'<td>{e(r.get("plan_name") or "not listed")}</td>'
                f'<td>{plan_price_short(r)}</td>'
                f'<td><a href="{root(f"/models/{r["model"]}/")}">{e(models[r["model"]]["name"])}</a></td>'
                f'<td>{e(shown_resolution(r))}</td>'
                f'<td>{e(audio_phrase(r))}</td>'
                f'<td class="num">{rate_money(r["usd_per_second"])}{assumption_html(r)}</td>'
                f'<td>{status_cell(r)}</td>'
                f'<td>{other_short(other)}</td>'
                f'<td>{other_short(same)}</td>'
                f'<td>{source_toggle(r)}</td>'
                "</tr>"
            )

        plan_html = [plan_tr(r) for r in plan_rows]
        if plan_html:
            by_rate = sorted(plan_rows, key=lambda r: (r["usd_per_second"], r["id"]))
            plan_extra = plan_html if len(plan_html) > 10 else []
            plan_table = capped(
                plan_head,
                [plan_tr(r) for r in by_rate[:10]],
                plan_extra,
                f"Show all {len(plan_html)} plan rates",
            )
            plan_note = (
                "<p class=\"small\">The ten rows above are the lowest plan rates. Other is the cheapest rate for that model on a platform other than Higgsfield or the Higgsfield API. "
                "Same res is the cheapest of those at this row's resolution. — means that comparison is not in the data. "
                "An unlimited window stays a deal badge with its end date. The $/s column stays the credit rate.</p>"
            )
        else:
            plan_table = "<p>No Higgsfield plan row is in the current price data.</p>"
            plan_note = ""
        api_head = (
            "<thead><tr><th>Model</th><th>Res</th><th>Audio</th><th>$/s</th><th>Status</th>"
            "<th>Other</th><th>Same res</th><th>Source</th></tr></thead>"
        )
        api_html = []
        for r in by_price(api_rows):
            other = best_model.get(r["model"])
            same = best_res.get((r["model"], res_key(r)))
            api_html.append(
                f'<tr data-price-id="{e(r["id"])}">'
                f'<td><a href="{root(f"/models/{r["model"]}/")}">{e(models[r["model"]]["name"])}</a></td>'
                f'<td>{e(shown_resolution(r))}</td>'
                f'<td>{e(audio_phrase(r))}</td>'
                f'<td class="num">{rate_money(r["usd_per_second"])}{assumption_html(r)}</td>'
                f'<td>{status_cell(r)}</td>'
                f'<td>{other_short(other)}</td>'
                f'<td>{other_short(same)}</td>'
                f'<td>{source_toggle(r)}</td>'
                "</tr>"
            )
        if api_html:
            api_table = (
                "<p>These rows are Higgsfield API rates from the price data, not credit plans.</p>"
                + capped(
                    api_head,
                    api_html[:10],
                    api_html if len(api_html) > 10 else [],
                    f"Show all {len(api_html)} API rates",
                )
            )
        else:
            api_table = "<p>No Higgsfield API row is in the current price data.</p>"
        cards = ""
        if lo is not None:
            cards = f'<div class="cards">{cheap_card("Lowest plan rate", lo)}{cheap_card("Highest plan rate", hi)}</div>'

        def credit_specs(model_slug):
            specs = []
            seen = set()
            for r in plan_rows:
                if r["model"] != model_slug:
                    continue
                credits = r.get("credits_per_clip")
                clip_len = r.get("clip_seconds")
                if not credits or not clip_len:
                    continue
                key = (shown_resolution(r), credits, clip_len, r.get("status"))
                if key in seen:
                    continue
                seen.add(key)
                specs.append(r)
            specs.sort(key=lambda r: (r["credits_per_clip"], shown_resolution(r), r["id"]))
            return specs

        def spec_bits(r):
            credits = r["credits_per_clip"]
            clip_len = r["clip_seconds"]
            clips = 1000 / credits
            seconds = clips * clip_len
            return clips, seconds

        q_thousand = "Is Higgsfield Pro's 1,000 credits enough for Seedance, or should I use Kling instead?"
        pro_plans = [
            (pid, p) for pid, p in plans.items()
            if p.get("platform") == "Higgsfield" and (p.get("plan") or "").strip().lower() in ("pro", "pro (monthly)", "pro (annual)")
        ]
        hf_priced = []
        for pid, p in plans.items():
            if p.get("platform") != "Higgsfield":
                continue
            if p.get("usd_month") is None or not p.get("credits_month"):
                continue
            hf_priced.append((pid, p))
        kling_specs = credit_specs("kling-3-0")
        seed_specs = credit_specs("seedance-2-5")
        seed_gap = next(
            (
                item for item in (db.get("unverified") or [])
                if "higgsfield" in (item.get("item") or "").lower() and "seedance" in (item.get("item") or "").lower()
            ),
            None,
        )
        kling_gap = next(
            (
                item for item in (db.get("unverified") or [])
                if "higgsfield" in (item.get("item") or "").lower() and "kling" in (item.get("item") or "").lower()
            ),
            None,
        )
        thousand_plain_parts = []
        if pro_plans:
            pid, p = pro_plans[0]
            thousand_plain_parts.append(
                f"Higgsfield Pro in our plan data is {p['plan']}: {cost_money(p['usd_month'])} per month for {int(p['credits_month']):,} credits ({p.get('billing') or 'billing not listed'})."
            )
        else:
            thousand_plain_parts.append(
                "Higgsfield Pro's price and a 1,000-credit allowance are not in our plan data, so the figures below are per 1,000 credits on the plans we do track."
            )
        if kling_specs:
            lead_spec = next((r for r in kling_specs if shown_resolution(r).lower() == "720p"), kling_specs[0])
            clips, seconds = spec_bits(lead_spec)
            thousand_plain_parts.append(
                f"At the Kling 3.0 {shown_resolution(lead_spec)} credit rate we track "
                f"({credit_num(lead_spec['credits_per_clip'])} credits for a {credit_num(lead_spec['clip_seconds'])}-second clip, "
                f"{g['status_phrase'](lead_spec)}), 1,000 credits is about {count_text(clips)} clips, or {count_text(seconds)} seconds."
            )
        else:
            thousand_plain_parts.append("No Kling 3.0 credits-per-clip row is in the Higgsfield plan data, so there is no Kling second count.")
        if seed_specs:
            lead_spec = seed_specs[0]
            clips, seconds = spec_bits(lead_spec)
            thousand_plain_parts.append(
                f"At the Seedance 2.5 {shown_resolution(lead_spec)} credit rate we track "
                f"({credit_num(lead_spec['credits_per_clip'])} credits for a {credit_num(lead_spec['clip_seconds'])}-second clip, "
                f"{g['status_phrase'](lead_spec)}), 1,000 credits is about {count_text(clips)} clips, or {count_text(seconds)} seconds."
            )
        else:
            thousand_plain_parts.append(
                "Seedance 2.5 has no Higgsfield credits-per-clip row, so there is no Seedance second count from 1,000 credits."
            )
            if seed_gap:
                thousand_plain_parts.append(left_out(seed_gap.get("item"), seed_gap.get("reason")))
        if kling_gap:
            thousand_plain_parts.append(left_out(kling_gap.get("item"), kling_gap.get("reason")))
        seed_other = best_model.get("seedance-2-5")
        kling_other = best_model.get("kling-3-0")
        if kling_other:
            thousand_plain_parts.append(f"The cheapest Kling 3.0 rate outside Higgsfield is {rate_clause(kling_other)}.")
        else:
            thousand_plain_parts.append("No Kling 3.0 rate outside Higgsfield is in the current price data.")
        if seed_other:
            thousand_plain_parts.append(f"The cheapest Seedance 2.5 rate outside Higgsfield is {rate_clause(seed_other)}.")
        else:
            thousand_plain_parts.append("No Seedance 2.5 rate outside Higgsfield is in the current price data.")
        thousand_plain_parts.append(
            "Clip and second counts are 1,000 divided by credits per clip, rounded half up to 2 decimal places. The two rates are the comparison."
        )
        a_thousand = " ".join(thousand_plain_parts)

        price_rows_html = []
        for pid, p in hf_priced:
            rate = p["usd_month"] / p["credits_month"]
            price_rows_html.append(
                "<tr>"
                f"<td>{e(p['plan'])}</td>"
                f"<td class=\"num\">{cost_money(p['usd_month'])}/mo</td>"
                f"<td class=\"num\">{int(p['credits_month']):,}</td>"
                f"<td>{e(p.get('billing') or 'not listed')}</td>"
                f"<td class=\"num\">{rate_money(rate)}/credit</td>"
                f"<td class=\"num\">{cost_money(rate * 1000)}</td>"
                "</tr>"
            )
        if price_rows_html:
            thousand_price_table = (
                "<p>Cost of 1,000 credits on each Higgsfield plan we track. That is 1,000 times the plan price divided by its monthly credits.</p>"
                '<div class="tblwrap fit"><table><thead><tr><th>Plan</th><th>Price</th><th>Credits</th>'
                "<th>Billing</th><th>$/credit</th><th>1,000 credits</th></tr></thead><tbody>"
                + "".join(price_rows_html)
                + "</tbody></table></div>"
            )
        else:
            thousand_price_table = "<p>No Higgsfield plan in our data has both a price and a monthly credit amount, so there is no per-1,000-credit dollar rate.</p>"

        def spec_table(specs, caption):
            if not specs:
                return ""
            body_html = []
            for r in specs:
                clips, seconds = spec_bits(r)
                body_html.append(
                    f'<tr data-price-id="{e(r["id"])}">'
                    f'<td>{e(shown_resolution(r))}</td>'
                    f'<td class="num">{credit_num(r["credits_per_clip"])}</td>'
                    f'<td class="num">{credit_num(r["clip_seconds"])}s</td>'
                    f'<td class="num">{count_text(clips)}</td>'
                    f'<td class="num">{count_text(seconds)}</td>'
                    f'<td>{status_cell(r)}</td>'
                    f'<td>{source_toggle(r)}</td>'
                    "</tr>"
                )
            spec_head = (
                "<thead><tr><th>Res</th><th>Credits</th><th>Clip</th><th>Clips</th>"
                "<th>Seconds</th><th>Status</th><th>Source</th></tr></thead>"
            )
            return f"<p>{caption}</p>" + fit_table(spec_head, body_html)

        thousand_html = (
            f"<h2>{e(q_thousand)}</h2><p>{e(a_thousand)}</p>"
            + thousand_price_table
            + spec_table(kling_specs, "Kling 3.0 credit rates we track on Higgsfield plans. The same credits-per-clip figure is not repeated once per plan.")
            + spec_table(seed_specs, "Seedance 2.5 credit rates we track on Higgsfield plans.")
        )

        q_clip = "What does a Higgsfield clip actually cost in dollars?"
        lengths = sorted({r.get("clip_seconds") for r in plan_rows if r.get("clip_seconds")})
        length_text = ", ".join(f"{credit_num(n)}s" for n in lengths) if lengths else "none listed"
        cinema = [
            r for r in rows
            if "cinema" in f"{r.get('variant') or ''} {models[r['model']]['name']}".lower()
        ]
        clip_parts = [
            "The dollar cost of a Higgsfield clip is that row's dollars per clip: credits per clip times the plan's price per credit.",
            f"Tracked clip lengths on Higgsfield plans are {length_text}.",
        ]
        if 30 not in lengths:
            clip_parts.append("No Higgsfield plan row is 30 seconds long.")
        if not cinema:
            clip_parts.append("No Cinema Studio rate is in the price data.")
        else:
            clip_parts.append(f"Cinema rows in the price data: {len(cinema)}.")
        a_clip = " ".join(clip_parts)
        clip_body = []
        for r in plan_rows:
            credits = r.get("credits_per_clip")
            per_clip = r.get("usd_per_clip")
            clip_len = r.get("clip_seconds")
            credit_cell = credit_num(credits) if credits else "not in our data"
            clip_cell = f"{credit_num(clip_len)}s" if clip_len else "not in our data"
            dollar_cell = cost_money(per_clip) if per_clip is not None else "not in our data"
            clip_body.append((per_clip is None, per_clip if per_clip is not None else 0, r["id"], (
                f'<tr data-price-id="{e(r["id"])}">'
                f'<td>{e(r.get("plan_name") or "not listed")}</td>'
                f'<td><a href="{root(f"/models/{r["model"]}/")}">{e(models[r["model"]]["name"])}</a></td>'
                f'<td>{e(shown_resolution(r))}</td>'
                f'<td class="num">{clip_cell}</td>'
                f'<td class="num">{credit_cell}</td>'
                f'<td class="num">{dollar_cell}{assumption_html(r)}</td>'
                f'<td>{status_cell(r)}</td>'
                f'<td>{source_toggle(r)}</td>'
                "</tr>"
            )))
        if clip_body:
            clip_head = (
                "<thead><tr><th>Plan</th><th>Model</th><th>Res</th><th>Clip</th>"
                "<th>Credits</th><th>$/clip</th><th>Status</th><th>Source</th></tr></thead>"
            )
            clip_all = [html for _a, _b, _c, html in clip_body]
            clip_top = [html for _a, _b, _c, html in sorted(clip_body)[:10]]
            clip_table = capped(
                clip_head,
                clip_top,
                clip_all if len(clip_all) > 10 else [],
                f"Show all {len(clip_all)} clip prices",
            )
        else:
            clip_table = "<p>No Higgsfield plan row with a per-clip credit cost is in the current price data.</p>"
        clip_html = f"<h2>{e(q_clip)}</h2><p>{e(a_clip)}</p>{clip_table}"

        faqs = [
            (q_worth, a_worth),
            (q_plans, "The plan table lists every current Higgsfield credit-plan row, with the plan price and credit amount from the plan record when that record has both."),
            (q_api, "The API table lists every current Higgsfield API row. Those rates are separate from the credit plans."),
            (q_gap, gap),
            (q_thousand, a_thousand),
            (q_clip, a_clip),
            ("How do we calculate this?", HOW_PLAIN),
        ]
        desc_lo = rate_money(lo["usd_per_second"]) if lo is not None else "n/a"
        desc_hi = rate_money(hi["usd_per_second"]) if hi is not None else "n/a"
        body = f"""{crumb("Higgsfield")}
<h1>Is Higgsfield worth it? Every plan's real cost per second</h1>
<p class="lead">{e(lead)}</p>
{checked_line()}
{cards}
<h2>{e(q_worth)}</h2><p>{e(a_worth)}</p>
{thousand_html}
{clip_html}
<h2>{e(q_plans)}</h2>
<p>The ten lowest plan rates are listed first. Plan price and credits come from the plan record. The $/s column is the row's effective rate. A plan with no row for a model is left out.</p>
{plan_note}
{plan_table}
<h2>{e(q_api)}</h2>
{api_table}
<h2>{e(q_gap)}</h2><p>{e(gap)}</p>
{how_block()}
{tick_script()}"""
        guide_page(
            "/guides/is-higgsfield-worth-it/",
            f"Is Higgsfield worth it? Every plan's real cost per second | {BRAND}",
            (
                f"Higgsfield plan rates we track run from {desc_lo}/s to {desc_hi}/s, "
                f"next to the cheapest non-Higgsfield rate for the same model. Last checked {LAST}."
            ),
            body,
            faqs,
        )

    def budget_records():
        records = []
        for r in rows:
            detail = e(r["math"]) if r.get("math") else ""
            if r.get("note"):
                detail += (" " if detail else "") + e(r["note"])
            if r.get("checked"):
                detail = (detail + " " if detail else "") + e(f"Checked {r['checked']}.")
            href, rel = outbound(r["source_url"])
            link = f'<a href="{e(href)}" rel="{rel}" target="_blank">pricing page</a>'
            source_html = f'<details class="src"><summary>source</summary><div class="math">{(detail + " " + link).strip()}</div></details>'
            records.append({
                "id": r["id"],
                "model": r["model"],
                "platform_html": plat_link(r["platform"], r["source_url"]),
                "variant": r["variant"],
                "tier": shown_tier(r),
                "resolution": shown_resolution(r),
                "audio": audio_phrase(r),
                "usd": r["usd_per_second"],
                "status": r["status"],
                "promo_until": r.get("promo_until") or "",
                "assumption": assumption_text(r),
                "badges": deal_badges(r),
                "detail": detail,
                "source_html": source_html,
            })
        return records

    def budget_tr(rec, seconds):
        total = rec["usd"] * seconds
        promo = f' <span class="small">until {e(rec["promo_until"])}</span>' if rec["promo_until"] else ""
        assume = f'<div class="assume">{e(rec["assumption"])}</div>' if rec["assumption"] else ""
        return (
            f'<tr data-price-id="{e(rec["id"])}">'
            f'<td>{rec["platform_html"]}</td>'
            f'<td>{e(rec["variant"])}</td>'
            f'<td>{e(rec["tier"])}</td>'
            f'<td>{e(rec["resolution"])}</td>'
            f'<td>{e(rec["audio"])}</td>'
            f'<td class="num">{rate_money(rec["usd"])}{assume}</td>'
            f'<td class="num">{cost_money(total)}</td>'
            f'<td>{tag(rec["status"])}{promo}{rec["badges"]}</td>'
            f'<td>{rec["source_html"]}</td>'
            "</tr>"
        )

    def write_budget():
        picked = overall_pick()
        default_model = picked["model"]
        default_res = shown_resolution(picked)
        seconds = 3 * 60 * 3
        records = budget_records()
        opening = [
            rec for rec in records
            if rec["model"] == default_model and rec["resolution"] == default_res
        ]
        opening.sort(key=lambda rec: (rec["usd"], rec["id"]))
        model_opts = []
        for slug, meta in models.items():
            sel = " selected" if slug == default_model else ""
            model_opts.append(f'<option value="{e(slug)}"{sel}>{e(meta["name"])}</option>')
        q1 = "How much does a 1-minute AI explainer video cost?"
        q3 = "How much does a 3-minute AI music video cost?"
        q10 = "How much does a 10-minute AI short film cost?"
        a1 = project_cost_sentence(1)
        a3 = project_cost_sentence(3)
        a10 = project_cost_sentence(10)
        lead = (
            a3 + " The table prices every tracked platform for the model and resolution you pick."
        )
        open_line = (
            f"The table opens on {models[default_model]['name']} at {default_res}, "
            f"the lowest rate we track ({rate_money(picked['usd_per_second'])}/s on {picked['platform']})."
        )
        faqs = [
            (q1, a1),
            (q3, a3),
            (q10, a10),
            ("How do we calculate this?", BUDGET_HOW),
        ]
        head = (
            "<thead><tr><th>Where</th><th>Variant</th><th>Tier</th><th>Res</th><th>Audio</th>"
            "<th>$/s</th><th>Total</th><th>Status</th><th>Source</th></tr></thead>"
        )
        script = budget_script(g, records, {"model": default_model, "resolution": default_res})
        body = f"""{crumb("Project budget")}
<h1>AI video project budget</h1>
<p class="lead">{e(lead)}</p>
{checked_line()}
<p>{e(open_line)}</p>
<div class="filters">
<button type="button" class="btn" id="preset1">1-minute explainer video</button>
<button type="button" class="btn" id="preset3">3-minute music video</button>
<button type="button" class="btn" id="preset10">10-minute short film</button>
</div>
<div class="calc"><div class="card">
<label class="small" for="minutes">Finished minutes</label><br>
<input id="minutes" type="number" min="0" step="any" value="3" style="width:120px">
<label class="small" for="retries">Retries / re-rolls</label><br>
<input id="retries" type="number" min="0" step="any" value="3" style="width:120px">
<p class="small">Billed seconds = finished minutes × 60 × this multiplier. The default is 3.</p>
<label class="small" for="model">Model</label><br>
<select id="model" style="width:100%">{"".join(model_opts)}</select>
<label class="small" for="resolution">Resolution</label><br>
<select id="resolution" style="width:100%"></select>
<p class="small" id="budgetMsg" role="status"></p>
<div class="small" style="margin-top:8px">Seconds billed</div><div class="kpi" id="kSecs">{format_seconds(seconds)}</div>
</div></div>
<div class="tblwrap fit"><table id="budget">{head}<tbody>{"".join(budget_tr(rec, seconds) for rec in opening)}</tbody></table></div>
<p class="small">Each row prices the whole billed length at that row's rate. Credit-plan totals assume every credit you pay for is used. The total is that rate times billed seconds.</p>
<noscript><p>Turn on JavaScript to change the minutes, multiplier, model, or resolution. The rates are embedded in this page. The examples below are already filled in from the price data.</p></noscript>
<h2>{e(q1)}</h2><p>{e(a1)} The preset sets finished length to 1 minute (60 seconds) and leaves the multiplier, model, and resolution as they are.</p>
<h2>{e(q3)}</h2><p>{e(a3)} The preset sets finished minutes to 3 and leaves the multiplier, model, and resolution as they are.</p>
<h2>{e(q10)}</h2><p>{e(a10)} The preset sets finished minutes to 10 and leaves the multiplier, model, and resolution as they are.</p>
{how_block(BUDGET_HOW)}
{script}
{tick_script()}"""
        guide_page(
            "/guides/ai-video-project-budget/",
            f"AI video project budget calculator | {BRAND}",
            (
                f"Estimate an AI video from finished minutes, a retry multiplier, and tracked dollars per second. "
                f"3 finished minutes at 3x is {cost_money(picked['usd_per_second'] * seconds)} at the lowest rate we track. "
                f"Last checked {LAST}."
            ),
            body,
            faqs,
        )

    write_index()
    write_wan()
    write_cheapest()
    write_higgsfield()
    write_budget()


def budget_script(g, records, defaults):
    payload = json.dumps(records, ensure_ascii=False).replace("<", "\\u003c")
    models_json = json.dumps({k: v["name"] for k, v in g["models"].items()}, ensure_ascii=False).replace("<", "\\u003c")
    defaults_json = json.dumps(defaults, ensure_ascii=False).replace("<", "\\u003c")
    return (
        "<script>\n"
        "const ROWS=" + payload + ";\n"
        "const MODELS=" + models_json + ";\n"
        "const DEFAULTS=" + defaults_json + ";\n"
        + BUDGET_JS
        + "\n</script>"
    )


BUDGET_JS = r"""
const $=id=>document.getElementById(id);
function esc(s){return String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function rateMoney(v){const n=Number(v),neg=n<0,abs=Math.abs(n),places=abs>=0.1?3:4,q=Math.pow(10,places),rounded=Math.round(abs*q),whole=Math.floor(rounded/q);let frac=String(rounded%q).padStart(places,'0').replace(/0+$/,'');if(frac.length<2)frac=frac.padEnd(2,'0');return (neg?'-$':'$')+whole+'.'+frac;}
function costMoney(v){const neg=Number(v)<0,n=Math.round(Math.abs(Number(v))*100),whole=Math.floor(n/100),frac=String(n%100).padStart(2,'0');return (neg?'-$':'$')+whole+'.'+frac;}
function tag(s){const label={verified:'vendor-stated',estimate:'approx.',promo:'promo',discontinued:'discontinued'}[s]||s;return '<span class="tag '+esc(s)+'">'+esc(label)+'</span>';}
function rankRes(s){const m=/^(\d+(?:\.\d+)?)(p|k)$/i.exec(s);if(!m)return null;const n=Number(m[1]);return m[2].toLowerCase()==='k'?n*1000:n;}
function resolutions(model){
  const seen=new Set(), out=[];
  ROWS.forEach(r=>{if(r.model===model && !seen.has(r.resolution)){seen.add(r.resolution);out.push(r.resolution);}});
  out.sort((a,b)=>{const ra=rankRes(a), rb=rankRes(b);if(ra!=null&&rb!=null&&ra!==rb)return ra-rb;if(ra!=null&&rb==null)return -1;if(rb!=null&&ra==null)return 1;return a.localeCompare(b);});
  return out;
}
function cheapestResolution(model){
  let best=null;
  ROWS.forEach(r=>{if(r.model!==model)return;if(!best||r.usd<best.usd||(r.usd===best.usd&&r.id<best.id))best=r;});
  return best?best.resolution:'';
}
function fillResolutions(keep){
  const model=$('model').value;
  const list=resolutions(model);
  const prev=keep?$('resolution').value:null;
  let want;
  if(keep && prev==='') want='';
  else if(keep && prev && list.indexOf(prev)>=0) want=prev;
  else if(!keep && model===DEFAULTS.model && list.indexOf(DEFAULTS.resolution)>=0) want=DEFAULTS.resolution;
  else want=cheapestResolution(model);
  let html='<option value="">All resolutions</option>';
  list.forEach(res=>{html+='<option value="'+esc(res)+'">'+esc(res)+'</option>';});
  $('resolution').innerHTML=html;
  $('resolution').value=(want===''||list.indexOf(want)>=0)?want:cheapestResolution(model);
}
function readNum(id){
  const raw=String($(id).value).trim();
  if(raw===''||!Number.isFinite(Number(raw))||Number(raw)<0) return null;
  return Number(raw);
}
function render(){
  const minutes=readNum('minutes');
  const mult=readNum('retries');
  const msg=$('budgetMsg');
  if(minutes==null||mult==null){
    msg.textContent='Enter a finished length and a retry multiplier, each 0 or more.';
    $('kSecs').textContent='\u2014';
    $('budget').querySelector('tbody').innerHTML='<tr><td colspan="9">Enter a finished length and a retry multiplier, each 0 or more.</td></tr>';
    return;
  }
  msg.textContent='';
  const seconds=minutes*60*mult;
  const shown=Math.round(seconds*100)/100;
  $('kSecs').textContent=Number.isInteger(shown)?shown.toLocaleString('en-US'):String(shown);
  const model=$('model').value;
  const res=$('resolution').value;
  let rs=ROWS.filter(r=>r.model===model && (!res || r.resolution===res));
  rs.sort((a,b)=>a.usd-b.usd||a.id.localeCompare(b.id));
  if(!rs.length){
    $('budget').querySelector('tbody').innerHTML='<tr><td colspan="9">No tracked rate for that model and resolution.</td></tr>';
    return;
  }
  $('budget').querySelector('tbody').innerHTML=rs.map(r=>{
    const total=r.usd*seconds;
    const promo=r.promo_until?' <span class="small">until '+esc(r.promo_until)+'</span>':'';
    const assume=r.assumption?'<div class="assume">'+esc(r.assumption)+'</div>':'';
    return '<tr data-price-id="'+esc(r.id)+'"><td>'+r.platform_html+'</td><td>'+esc(r.variant)+'</td><td>'+esc(r.tier)+'</td><td>'+esc(r.resolution)+'</td><td>'+esc(r.audio)+'</td><td class="num">'+rateMoney(r.usd)+assume+'</td><td class="num">'+costMoney(total)+'</td><td>'+tag(r.status)+promo+r.badges+'</td><td>'+r.source_html+'</td></tr>';
  }).join('');
  if(window.clipTick) clipTick();
}
$('preset1').addEventListener('click',()=>{$('minutes').value='1';render();});
$('preset3').addEventListener('click',()=>{$('minutes').value='3';render();});
$('preset10').addEventListener('click',()=>{$('minutes').value='10';render();});
['minutes','retries','model','resolution'].forEach(id=>{
  $(id).addEventListener('input',()=>{if(id==='model')fillResolutions(true);render();});
});
fillResolutions(false);
render();
"""
