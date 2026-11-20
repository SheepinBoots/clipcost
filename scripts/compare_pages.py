"""Model-vs-model price comparison pages under /compare/.

Imported by scripts/build_site.py. One config entry in PAIRS is one page. Every
number comes from data/prices.json at build time, so each page rebuilds with the
daily price run and needs no hand edits.

Rules
- Rows are the current rows of prices.json (expired promos and discontinued rows
  are already gone in build_site's `rows`).
- "Cheapest" at a resolution is the lowest usd_per_second among rows whose stated
  resolution is exactly that tier. Ties keep the first row in file order.
  Affiliate links play no part: rows are ordered by usd_per_second only.
- A clip total is usd_per_second x seconds. When the seconds pass the model's
  longest single clip (the cap), the total is shown with the number of clips it
  needs. It is never shown as one clip.
- Caps: the max_seconds stated in the rows' variation data when every stating row
  agrees; otherwise the config value. A disagreement is reported by cap_info().
- Stale guard: a page whose oldest shown row was checked more than STALE_DAYS days
  before the build date gets a visible notice, robots noindex, and is left out of
  the sitemap and llms.txt. The daily run re-checks every source, so 7 days means a
  week of failed checks on at least one row.
"""
import datetime
import math

import timefmt

STALE_DAYS = 7
SECONDS = (5, 10, 15, 30)
RESOLUTIONS = ("720p", "1080p")
BRAND_SUFFIX = " | VidFare"

# One entry per page. Later pairs are new entries here.
PAIRS = [
    {
        "path": "/compare/kling-3-0-vs-seedance-2-5/",
        "a": "kling-3-0",
        "b": "seedance-2-5",
        "title": "Kling 3.0 vs Seedance 2.5 Prices Compared",
        "h1": "Kling 3.0 vs Seedance 2.5 prices compared",
        "description": ("Kling 3.0 and Seedance 2.5 price per second at 720p and 1080p, with 5s to 30s "
                        "clip totals, on the platforms that sell both. Rebuilt daily."),
        "resolutions": RESOLUTIONS,
        "seconds": SECONDS,
        # Longest single clip, used when the rows do not state one.
        "caps": {"kling-3-0": 15, "seedance-2-5": 30},
    },
    {
        "path": "/compare/wan-3-0-vs-kling-3-0/",
        "a": "wan-3-0",
        "b": "kling-3-0",
        "title": "Wan 3.0 vs Kling 3.0: Which Is Cheaper?",
        "h1": "Wan 3.0 vs Kling 3.0: which is cheaper?",
        "description": ("Wan 3.0 and Kling 3.0 price per second at 480p, 720p and 1080p, with 5s to 30s "
                        "clip totals, on the platforms that sell both. Rebuilt daily."),
        "resolutions": ("480p",) + RESOLUTIONS,
        "seconds": SECONDS,
        "caps": {"wan-3-0": 30, "kling-3-0": 15},
        "note": ("Wan 3.0 has a 480p option. We have no Kling 3.0 price at 480p, "
                 "so the 480p rows are Wan 3.0 only."),
    },
    {
        "path": "/compare/kling-3-0-vs-veo-3-1/",
        "a": "kling-3-0",
        "b": "veo-3-1",
        "title": "Kling 3.0 vs Veo 3.1 Prices Compared",
        "h1": "Kling 3.0 vs Veo 3.1 prices compared",
        "description": ("Kling 3.0 and Veo 3.1 price per second at 720p and 4K, with 5s to 30s "
                        "clip totals, on the platforms that sell both. Rebuilt daily."),
        "resolutions": ("720p", "4K"),
        "seconds": SECONDS,
        "caps": {"kling-3-0": 15, "veo-3-1": 8},
        "note": ("This page compares 720p and 4K. No platform that sells both models has a 1080p-only Veo 3.1 price: "
                 "fal and the Google Gemini API price Veo 3.1 Standard as one 720p/1080p rate, and the only "
                 "1080p-only Veo 3.1 rows are Veo 3.1 Fast and Lite on the Google Gemini API, which does not sell "
                 "Kling 3.0. Veo 3.1 makes clips of up to 8 seconds, so its 10s, 15s and 30s totals need more than one clip."),
    },
]


# ---------- pure helpers (tested directly) ----------

def title_of(pair):
    return pair["title"] + BRAND_SUFFIX


def res_of(r):
    """720p / 1080p / ... as written, lower-cased 4k. Tier names and dashes are not resolutions."""
    s = str(r.get("resolution") or "").strip()
    return s if s.lower() in ("480p", "720p", "1080p", "4k") else None


def stated_max(r):
    v = (((r.get("variation") or {}).get("duration") or {}).get("max_seconds"))
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def cap_info(rows, slug, fallback):
    """(cap, source, mismatch). source is 'data' or 'config'. mismatch is a text or ''."""
    stated = sorted({stated_max(r) for r in rows if r["model"] == slug and stated_max(r) is not None})
    if len(stated) == 1:
        cap = stated[0]
        mismatch = "" if fallback in (None, cap) else f"config says {fallback}s, data says {cap:g}s"
        return cap, "data", mismatch
    if len(stated) > 1:
        return fallback, "config", "rows disagree: " + ", ".join(f"{s:g}s" for s in stated)
    return fallback, "config", ""


def clips_needed(seconds, cap):
    return max(1, math.ceil(seconds / cap)) if cap else 1


def clip_total(rate, seconds, cap):
    """(total dollars, clips). Total is linear in seconds; clips > 1 when past the cap."""
    return rate * seconds, clips_needed(seconds, cap)


def shared_platforms(rows, a, b):
    """Platforms with a current row for both models, in the order they first appear."""
    seen = {}
    for r in rows:
        seen.setdefault(r["platform"], set()).add(r["model"])
    return [p for p, ms in seen.items() if a in ms and b in ms]


def cheapest_at(rows, slug, res):
    best = None
    for r in rows:
        if r["model"] == slug and res_of(r) == res:
            if best is None or r["usd_per_second"] < best["usd_per_second"]:
                best = r
    return best


def oldest_checked(rows):
    days = [r["checked"] for r in rows if r.get("checked")]
    return min(days) if days else None


def is_stale(rows, today, days=STALE_DAYS):
    """True when any row is older than `days` days on `today`, or there are no rows."""
    old = oldest_checked(rows)
    if old is None:
        return True
    return (datetime.date.fromisoformat(today) - datetime.date.fromisoformat(old)).days > days


def and_list(items):
    """'720p and 1080p'; '480p, 720p and 1080p'."""
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def day_text(day):
    d = datetime.date.fromisoformat(day)
    return f"{d.strftime('%b')} {d.day}, {d.year}"


def run_text(run_iso, last):
    """The daily check time, ET first with PT in brackets, when the run was on the catalog date.

    check_report.json's run is box-local Pacific time without an offset."""
    if not run_iso or not last or not str(run_iso).startswith(last):
        return day_text(last) if last else ""
    t = datetime.datetime.fromisoformat(run_iso).replace(tzinfo=timefmt.PT)
    return timefmt.et_pt(t)


def page_rows(rows, pair):
    """Rows shown in the platform table: shared platforms, both models, the pair's
    resolutions plus rows whose resolution is not listed. Sorted by resolution group,
    then $/s, then platform. Affiliate status is not a key."""
    plats = shared_platforms(rows, pair["a"], pair["b"])
    order = {res: i for i, res in enumerate(pair["resolutions"])}
    out = []
    for r in rows:
        if r["platform"] not in plats or r["model"] not in (pair["a"], pair["b"]):
            continue
        res = res_of(r)
        if res is None:
            out.append((len(order), r))
        elif res in order:
            out.append((order[res], r))
    out.sort(key=lambda x: (x[0], x[1]["usd_per_second"], x[1]["platform"]))
    return plats, [r for _, r in out]


def plan_short(tier):
    """'Ultra (annual)' -> 'Ultra annual'. 'not listed' -> ''."""
    t = (tier or "").strip()
    if not t or t == "not listed":
        return ""
    return t.replace(" (", " ").replace("(", "").replace(")", "")


def deal_name(title):
    """'Black Friday: Ultra annual ...' -> 'Black Friday price'. No prefix -> 'deal price'."""
    head = (title or "").split(":", 1)
    return (head[0].strip() + " price") if len(head) == 2 and head[0].strip() else "deal price"


def seller_bits(r, tier, deal_names, rate_label):
    """Plan, deal, promo end and rate label, in that order, for the text next to a price."""
    bits = [b for b in [plan_short(tier)] if b]
    bits += deal_names
    if r.get("promo_until"):
        bits.append(f"promo until {r['promo_until']}")
    bits.append(rate_label)
    return bits


def seller_text(r, tier, deal_names, rate_label, regular=""):
    """'on Higgsfield (Ultra annual, Black Friday price, estimated from credit plan)'.

    A sale price gets its regular price after a semicolon:
    '... Black Friday price, estimated from credit plan; regular $0.1505/s on Higgsfield, Ultra monthly at $129/mo)'."""
    tail = f"; {regular}" if regular else ""
    return f"on {r['platform']} ({', '.join(seller_bits(r, tier, deal_names, rate_label))}{tail})"


def sale_adjustment(r, adjs):
    """The deal adjustment that sets this row's own price, when that deal is a sale.

    A sale is a deal that is not standing (an end date or a time-limited offer) and
    whose deal price is the row's price, with a higher regular price. Standing annual
    discounts and unlimited windows are not sales. A deal that only touches the row
    through its full-price plan (e.g. the monthly row of an annual sale) is not either.
    """
    for adj in adjs:
        if adj.get("type") == "unlimited_window" or adj.get("standing"):
            continue
        usd, reg = adj.get("usd"), adj.get("list_usd")
        if usd is None or reg is None or reg <= usd:
            continue
        if abs(usd - r["usd_per_second"]) <= 1e-4 * max(1.0, usd) + 5e-6:
            return adj
    return None


def is_promo(r, adjs):
    """True when the row's price is a sale or promo price."""
    return bool(r.get("promo_until")) or sale_adjustment(r, adjs) is not None


def regular_for(r, adjs, rows, adjs_of):
    """What a promo row costs without the sale, from the data only.

    Returns None for a row that is not on sale, else one of
      {"kind": "regular", "usd": list $/s, "price_before": $/mo or None, "plan_before": plan name or None}
        (the deal's prior price, or the row's own list rate)
      {"kind": "nosale", "row": cheapest non-promo row of the same model and resolution}
      {"kind": "none"} (the data has neither; nothing is invented)
    """
    if not is_promo(r, adjs):
        return None
    adj = sale_adjustment(r, adjs)
    if adj is not None:
        return {"kind": "regular", "usd": adj["list_usd"], "price_before": adj.get("price_before"),
                "plan_before": adj.get("plan_before")}
    if r.get("list_usd_per_second") and r["list_usd_per_second"] > r["usd_per_second"]:
        return {"kind": "regular", "usd": r["list_usd_per_second"], "price_before": None, "plan_before": None}
    res = res_of(r)
    best = None
    for x in rows:
        if x is r or x["model"] != r["model"] or res_of(x) != res:
            continue
        if is_promo(x, adjs_of(x)):
            continue
        if best is None or x["usd_per_second"] < best["usd_per_second"]:
            best = x
    return {"kind": "nosale", "row": best} if best else {"kind": "none"}


def same_seller(rows, pair):
    """[(res, platform, row_a, row_b)]: cheapest row of each model on one platform at one resolution."""
    out = []
    plats = shared_platforms(rows, pair["a"], pair["b"])
    for res in reversed(pair["resolutions"]):
        for p in plats:
            on = [r for r in rows if r["platform"] == p and res_of(r) == res]
            ra = cheapest_at(on, pair["a"], res)
            rb = cheapest_at(on, pair["b"], res)
            if ra and rb:
                out.append((res, p, ra, rb))
    return out


def links_html(slug, root, nl=False):
    """Small link line for a model page or the calculator ('*' = every pair)."""
    hits = [p for p in PAIRS if slug == "*" or slug in (p["a"], p["b"])]
    if not hits:
        return ""
    links = " · ".join(f'<a href="{root(p["path"])}">{p["title"]}</a>' for p in hits)
    return f'<p class="small">Compare: {links}.</p>' + ("\n" if nl else "")


# ---------- page ----------

def _table(inner, tid):
    """Same wrapper as the Price Index tables: scrolls at desktop, stacks on a phone (_css)."""
    return f'<div class="tblwrap"><table id="{tid}">{inner}</table></div>'


def _css(ids):
    sel = lambda suf: ",".join(f"{t}{suf}" for t in ids)
    return (
        "<style>" + sel(" td.num .small") + "{white-space:normal}"
        + "@media(max-width:600px){"
        + sel(" thead") + "{display:none}"
        + ",".join(f"{t},{t} tbody,{t} tr,{t} th,{t} td" for t in ids) + "{display:block;width:auto}"
        + sel(" tr") + "{border-bottom:1px solid var(--line);padding:8px 0}"
        + sel(" tbody tr:last-child") + "{border-bottom:0}"
        + sel(" th") + "{position:static;background:none;border:0;padding:4px 12px;color:var(--txt);white-space:normal;cursor:auto}"
        + sel(" td") + "{border:0;padding:3px 12px}"
        + sel(" .tag") + "{white-space:normal}"
        + sel(" td::before") + "{content:attr(data-label) \": \";color:var(--mut);font-size:13px}"
        + "}</style>"
    )


class Labels:
    """Seller, plan, deal and regular-price text for rows, shared by /compare/ and /cost/ pages.

    `rows` is the pool searched for "cheapest without a sale" when a sale row has no regular price.
    """

    def __init__(self, g, rows, today):
        self.g, self.rows, self.today = g, rows, today
        self.e, self.rate_money, self.two = g["e"], g["rate_money"], g["_money_places"]
        self._adj = {}

    def plan_text(self, r):
        return self.g["shown_tier"](r)

    def adjs_of(self, r):
        """Deal adjustments for a row, with the deal's pre-sale plan price added."""
        g = self.g
        if id(r) not in self._adj:
            out = []
            for adj in g["dealmod"].row_adjustments(r, g["LIVE_DEALS"], g["plans"], self.today):
                adj = dict(adj)
                deal = g["DEAL_BY_ID"].get(adj["deal_id"]) or {}
                pair_ = g["dealmod"]._pair_for_row(deal, r) if deal else None
                adj["price_before"] = (pair_ or {}).get("price_before")
                full = g["plans"].get((pair_ or {}).get("full_plan_id") or "") or {}
                adj["plan_before"] = full.get("plan")
                out.append(adj)
            self._adj[id(r)] = out
        return self._adj[id(r)]

    def regular_text(self, r, secs=None):
        """'' for a row not on sale; else its regular price, or the cheapest non-sale row, from the data."""
        two, rate_money = self.two, self.rate_money
        info = regular_for(r, self.adjs_of(r), self.rows, self.adjs_of)
        if info is None:
            return ""
        if info["kind"] == "regular":
            amt = two(info["usd"] * secs, 2) if secs else f"{rate_money(info['usd'])}/s"
            plan = plan_short(info.get("plan_before") or self.plan_text(r))  # no separate full-price plan: same plan
            where = r["platform"] + (f", {plan}" if plan else "")
            before = f" at ${info['price_before']:g}/mo" if info.get("price_before") and not secs else ""
            return f"regular {amt} on {where}{before}"
        if info["kind"] == "nosale":
            x = info["row"]
            amt = two(x["usd_per_second"] * secs, 2) if secs else f"{rate_money(x['usd_per_second'])}/s"
            p = plan_short(self.plan_text(x))
            return f"cheapest without a sale: {amt} on {x['platform']}" + (f" ({p})" if p else "")
        return "no regular price in our data"

    def deals_of(self, r):
        names = []
        for adj in self.adjs_of(r):
            if adj["type"] == "unlimited_window":
                names.append("unlimited window on sale")
            else:
                names.append(deal_name(self.g["DEAL_BY_ID"][adj["deal_id"]].get("title")))
        return names

    def seller(self, r):
        return seller_text(r, self.plan_text(r), self.deals_of(r), self.g["rate_label"](r), self.regular_text(r))

    def seller_html(self, r, regular=False):
        """'on <a>Higgsfield</a> (Ultra annual, Black Friday price, ...)' with the vendor link.
        regular=True (headline) adds the regular price of a sale row."""
        g, e = self.g, self.e
        bits = seller_bits(r, self.plan_text(r), self.deals_of(r), g["rate_label"](r))
        reg = self.regular_text(r) if regular else ""
        return (f'on {g["plat_link"](r["platform"], r["source_url"])} <span class="small">({e(", ".join(bits))}'
                + (f'; <span class="regular">{e(reg)}</span>' if reg else "") + ')</span>')

    def seller_short(self, r):
        p = plan_short(self.plan_text(r))
        return r["platform"] + (f", {p}" if p else "")


def render_pair(g, pair):
    e, root, rate_money = g["e"], g["root"], g["rate_money"]
    models, rows, TODAY, LAST = g["models"], g["rows"], g["TODAY"], g["LAST"]
    two = g["_money_places"]
    A, B = pair["a"], pair["b"]
    name = {A: models[A]["name"], B: models[B]["name"]}
    caps, cap_src, mismatches = {}, {}, {}
    for s in (A, B):
        caps[s], cap_src[s], mismatches[s] = cap_info(rows, s, pair["caps"].get(s))

    plats, prow = page_rows(rows, pair)
    picks = {(res, s): cheapest_at(rows, s, res) for res in pair["resolutions"] for s in (A, B)}
    shown = prow + [r for r in picks.values() if r is not None and r not in prow]
    stale = is_stale(shown, TODAY, STALE_DAYS)
    old = oldest_checked(shown)
    run = run_text(g.get("CHECK_RUN"), LAST)

    def labels(r):
        promo = f' <span class="small">until {e(r["promo_until"])}</span>' if r.get("promo_until") else ""
        return g["tag"](r) + promo + g["deal_badges"](r)

    def total_cell(r, secs, label, who=True):
        cap = stated_max(r) or caps[r["model"]]
        total, n = clip_total(r["usd_per_second"], secs, cap)
        more = f'<br><span class="small">{n} clips (max {cap:g}s each)</span>' if n > 1 else ""
        reg = regular_text(r, secs) if who else ""
        reg_html = f'<br><span class="small regular">{e(reg)}</span>' if reg else ""
        return (f'<td data-label="{label}" class="num">{two(total, 2)}'
                + (f'<br><span class="small">{e(seller_short(r))}</span>' if who else "") + f'{reg_html}{more}</td>')

    lab = Labels(g, rows, TODAY)
    plan_text, adjs_of, regular_text, deals_of = lab.plan_text, lab.adjs_of, lab.regular_text, lab.deals_of
    seller, seller_html, seller_short = lab.seller, lab.seller_html, lab.seller_short

    # Headline: cheapest per model per resolution, anywhere.
    hrows = []
    for res in pair["resolutions"]:
        for s in (A, B):
            r = picks[(res, s)]
            if r is None:
                hrows.append(f'<tr><th scope="row">{e(name[s])}, {e(res)}</th><td data-label="Cheapest $/s" colspan="{1 + len(pair["seconds"])}">No {e(res)} price in our data.</td></tr>')
                continue
            hrows.append(
                f'<tr><th scope="row">{e(name[s])}, {e(res)}</th>'
                f'<td data-label="Cheapest $/s"><b>{rate_money(r["usd_per_second"])}/s</b> {seller_html(r, regular=True)}{g["deal_badges"](r)}'
                f'<div class="small">Resolution {e(res)} · audio {e(g["shown_audio"](r))} · checked {e(r["checked"])} · {g["source_link"](r)}</div></td>'
                + "".join(total_cell(r, secs, f"{secs}s clip") for secs in pair["seconds"]) + "</tr>"
            )
    sec_heads = "".join(f'<th scope="col">{s}s clip</th>' for s in pair["seconds"])
    headline = _table(
        f'<thead><tr><th scope="col">Model, resolution</th><th scope="col">Cheapest $/s</th>{sec_heads}</tr></thead>'
        f'<tbody>{"".join(hrows)}</tbody>', "cmp-headline")

    # Platform table
    prow_html = []
    for r in prow:
        res = res_of(r) or "not listed"
        prow_html.append(
            f'<tr><th scope="row">{e(r["platform"])}<br><span class="small">Plan or tier: {e(plan_text(r))} · {e(r["variant"])}</span></th>'
            f'<td data-label="Model"><a href="{root("/models/" + r["model"] + "/")}">{e(name[r["model"]])}</a></td>'
            f'<td data-label="Resolution">{e(res)}</td>'
            f'<td data-label="Audio">{e(g["shown_audio"](r))}</td>'
            f'<td data-label="$/s"><b>{rate_money(r["usd_per_second"])}/s</b> {seller_html(r)}{g["deal_badges"](r)}{g["assumption_html"](r)}</td>'
            + "".join(total_cell(r, secs, f"{secs}s clip", who=False) for secs in pair["seconds"])
            + f'<td data-label="Checked" class="small">{e(r["checked"])}<br>{g["source_link"](r)}</td></tr>'
        )
    ptable = _table(
        '<thead><tr><th scope="col">Seller and plan</th><th scope="col">Model</th>'
        '<th scope="col">Resolution</th><th scope="col">Audio</th><th scope="col">$/s, seller, plan and label</th>'
        f'{sec_heads}<th scope="col">Checked</th></tr></thead><tbody>{"".join(prow_html)}</tbody>', "cmp-platforms")

    like = same_seller(rows, pair)
    same_res = []
    for p in plats:
        both = [res for res in pair["resolutions"] if any(x[0] == res and x[1] == p for x in like)]
        if both:
            same_res.append(f"{p} ({', '.join(both)})")
    same_text = (f"{len(same_res)} of them {'lists' if len(same_res) == 1 else 'list'} both models at the same resolution: {', '.join(same_res)}." if same_res
                 else "None of them list both models at the same resolution.")
    unlisted = sum(1 for r in prow if res_of(r) is None)

    def clip_cost(r, secs, where):
        """'$0.58 on Higgsfield (regular $1.51)' for the lead's clip totals."""
        reg = regular_text(r, secs)
        return f"{two(r['usd_per_second'] * secs, 2)} on {where}" + (f" ({reg})" if reg else "")

    # Lead
    def pick_text(res):
        ra, rb = picks[(res, A)], picks[(res, B)]
        if not ra or not rb:
            return ""
        secs = 10 if 10 in pair["seconds"] else pair["seconds"][0]
        return (f"At {res}, the cheapest {name[A]} is {rate_money(ra['usd_per_second'])}/s {seller(ra)} "
                f"and the cheapest {name[B]} is {rate_money(rb['usd_per_second'])}/s {seller(rb)}, "
                f"so a {secs}-second clip costs {clip_cost(ra, secs, ra['platform'])} "
                f"vs {clip_cost(rb, secs, rb['platform'])}. ")
    lead = "".join(pick_text(res) for res in reversed(pair["resolutions"])) + f"Prices last checked {run}."
    secs10 = 10 if 10 in pair["seconds"] else pair["seconds"][0]
    if like:
        same_line = "On the same seller: " + " ".join(
            f"At {res}, {name[A]} is {rate_money(ra['usd_per_second'])}/s {seller(ra)} and {name[B]} is "
            f"{rate_money(rb['usd_per_second'])}/s {seller(rb)}, so a {secs10}-second clip costs "
            f"{clip_cost(ra, secs10, p)} vs {clip_cost(rb, secs10, p)}."
            for res, p, ra, rb in like)
    else:
        same_line = (f"On the same seller: no platform in our data sells both {name[A]} and {name[B]} at the same "
                     f"resolution ({and_list(pair['resolutions'])}), so there is no like-for-like price.")

    cap_lines = []
    for s in (A, B):
        src = "as stated in our price data" if cap_src[s] == "data" else "per the vendor docs; our price rows do not state it"
        cap_lines.append(f"{name[s]}: up to {caps[s]:g}s per clip ({src}).")
    cap_note = " ".join(cap_lines)

    stale_html = ""
    if stale:
        stale_html = (f'<p class="disclose"><b>Stale data:</b> at least one price on this page was last checked '
                      f'{e(day_text(old)) if old else "never"}, more than {STALE_DAYS} days ago. Check the vendor pages before you buy. '
                      f'This page is hidden from search until the prices are re-checked.</p>')

    plat_list = ", ".join(plats)
    method = f"""<h2 id="method">How these numbers work</h2>
<ul>
<li>Each price is one row of our <a href="{root("/data/")}">price data</a>, copied from the vendor page linked in its row, with the date we checked it.</li>
<li>Clip totals are the price per second × the clip length. A length longer than a model's longest single clip needs more than one clip, and the row says how many. {e(cap_note)}</li>
<li>Credit-plan rows {e(g["CREDIT_USE"])}. Unused credits make the real cost per second higher. Rows labelled estimated are not list prices.</li>
<li>Plan or tier, resolution and audio are shown as the vendor states them. "Not listed" and "not stated" mean the vendor page does not say.</li>
<li>Rows are ordered by price per second only. Affiliate links never change the order.</li>
<li>This page rebuilds with every daily price check. If any row on it goes more than {STALE_DAYS} days without a check, the page shows a notice and is hidden from search until it is re-checked. Oldest check on this page: {e(day_text(old)) if old else "none"}.</li>
</ul>"""

    body = f"""<p class="small"><a href="{root("/")}">Prices</a> › Compare › {e(pair["h1"])}</p>
<h1>{e(pair["h1"])}</h1>
{g["byline_html"]()}
{stale_html}
<p class="lead">{e(lead)}</p>
<p id="same-seller">{e(same_line)}</p>
<p class="small">{e(pair["description"])}</p>
{f'<p>{e(pair["note"])}</p>' + chr(10) if pair.get("note") else ""}{g["partner_lines_html"](pair["path"])}
<h2 id="cheapest">Cheapest price at {and_list(pair["resolutions"])}</h2>
<p class="small">The lowest price per second for each model at each resolution, on any platform we track, and what a {", ".join(f"{s}s" for s in pair["seconds"])} clip costs at that rate.</p>
{headline}
<h2 id="platforms">Platforms that sell both: {len(plats)}</h2>
<p>{e(plat_list)} sell both {e(name[A])} and {e(name[B])}. {e(same_text)} {unlisted and e(f"{unlisted} rows on these platforms name a tier but not a resolution, so they are shown as not listed.") or ""}</p>
{ptable}
<p class="small">See every price on the <a href="{root("/models/" + A + "/")}">{e(name[A])}</a> and <a href="{root("/models/" + B + "/")}">{e(name[B])}</a> pages, or check a credit plan in the <a href="{root("/calculator/")}">credit calculator</a>.</p>
{method}
{g["news_box"]()}"""

    ld = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": pair["h1"],
        "description": pair["description"],
        "url": g["SITE_URL"] + pair["path"],
        "dateModified": LAST,
        "about": [{"@type": "Thing", "name": name[A]}, {"@type": "Thing", "name": name[B]}],
        "publisher": {"@type": "Organization", "@id": g["ORG_ID"], "name": g["BRAND"], "url": g["SITE_URL"] + "/"},
    }
    head = _css(("#cmp-headline", "#cmp-platforms")) + g["ld_join"](
        ld, g["breadcrumb_ld"]([("Prices", "/"), (pair["h1"], pair["path"])]))
    g["page"](pair["path"], title_of(pair), pair["description"], body, "", head,
              robots="noindex,follow" if stale else "index,follow")
    if not stale:
        g["SITEMAP_LASTMOD"][pair["path"]] = LAST
    regulars = {k: regular_text(r) for k, r in picks.items() if r is not None}
    sales = {k: deals_of(r) for k, r in picks.items() if r is not None and regulars.get(k)}
    return {"path": pair["path"], "stale": stale, "platforms": plats, "picks": picks,
            "regulars": regulars, "sales": sales,
            "caps": caps, "mismatches": {s: m for s, m in mismatches.items() if m}, "oldest": old}


def render(g):
    out = [render_pair(g, p) for p in PAIRS]
    g["COMPARE_PAGES"] = out
    return out


def sitemap_paths(g):
    return [p["path"] for p in g.get("COMPARE_PAGES", []) if not p["stale"]]


def llms_lines(g):
    lines = []
    rm = g["rate_money"]
    for pair, built in zip(PAIRS, g.get("COMPARE_PAGES", [])):
        if built["stale"]:
            continue
        bits = []
        for res in pair["resolutions"]:
            for s in (pair["a"], pair["b"]):
                r = built["picks"].get((res, s))
                if r:
                    extra = [plan_short(g["shown_tier"](r))] + built.get("sales", {}).get((res, s), [])
                    if r.get("promo_until"):
                        extra.append(f"promo until {r['promo_until']}")
                    extra = ", ".join(x for x in extra if x)
                    reg = built.get("regulars", {}).get((res, s), "")
                    inner = extra + (f"; {reg}" if reg and extra else reg)
                    bits.append(f"{g['models'][s]['name']} {res} from {rm(r['usd_per_second'])}/s on {r['platform']}"
                                + (f" ({inner})" if inner else ""))
        lines.append(f"- [{pair['title']}]({g['SITE_URL']}{pair['path']}): {'; '.join(bits)}. "
                     f"5s to 30s clip totals on the {len(built['platforms'])} platforms that sell both.")
    return lines
