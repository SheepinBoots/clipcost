import guide_tables
"""Guide: Best AI video generator by value.

Imported by scripts/build_site.py. Quality scores were read from
Artificial Analysis AA-Video-T2V v2.1 and AA-Video-I2V v2.1 on 2026-11-16.
Cost figures come from data/prices.json (last full check 2026-11-15).
This page never names Sora.
"""
from decimal import Decimal, ROUND_HALF_UP

PATH = "/guides/best-ai-video-generator/"
LABEL = "Best AI video generator"
PHRASE = "Best AI video generator by value"
QUESTION = "What is the best AI video generator when you count quality and cost?"
CHECKED = "2026-11-16"
POLICY_CHECKED = "2026-11-18"
POLICY_CHECKED_WHEN = "Nov 18, 2026"
CHECKED_WHEN = "Nov 16, 2026, 8:08 AM ET (5:08 AM PT)"

AA_T2V = "https://artificialanalysis.ai/video/leaderboard/text-to-video"
AA_I2V = "https://artificialanalysis.ai/video/leaderboard/image-to-video"
FLOW_CREDITS = "https://support.google.com/flow/answer/16526234?hl=en"
KLING_API = "https://kling.ai/document-api/pricing/base/video.md"
HF_WAN = "https://open.higgsfield.ai/models/alibaba/wan-3.0/text-to-video"
HF_PRIME = "https://open.higgsfield.ai/models/alibaba/wan-3.0-prime/text-to-video"
XAI_GROK = "https://x.ai/grok"
RUNWAY_API = "https://docs.dev.runwayml.com/guides/pricing/"
REPLIT_SEEDANCE = "https://replicate.com/bytedance/seedance-2.5"
GEMINI_PRICING = "https://ai.google.dev/gemini-api/docs/pricing"
FAL_H3 = "https://fal.ai/models/minimax/h3-max-turbo/text-to-video"

# Catalog row ids for the cheapest current paid step (promo r194 ended Nov 15).
ROW_WAN = "r096"
ROW_PRIME = "r081"
ROW_KLING = "r111"
ROW_SEEDANCE = "r202"
ROW_VEO = "r127"
ROW_OMNI = "r199"
ROW_HAILUO = "r023"  # fal H3 Max Turbo 480p standard rate, resumes Nov 16
ROW_HAILUO_PLAN = "r132"  # cheaper estimate, Hailuo 2.3 not H3
ROW_GROK = "r055"
ROW_RUNWAY = "r047"

# AA-Video-T2V v2.1, overall, with audio, checked CHECKED.
# elo, plus_minus, ci_low, ci_high, range, samples, released, exact label on the board
AA_T2V_SCORES = {
    "wan-3-0": (1174, 13, 1161, 1187, "1-2", 8089, "Aug 2026", "Wan 3.0"),
    "minimax-hailuo": (1159, 13, 1146, 1172, "2-6", 8225, "Jul 2026", "MiniMax H3 (768p)"),
    "seedance-2-5": (1156, 13, 1143, 1169, "3-7", 8214, "Jul 2026", "Dreamina Seedance 2.5"),
    "gemini-omni-flash": (1151, 14, 1137, 1165, "3-8", 5634, "Nov 2026", "Gemini Omni Flash 1.2"),
    "grok-imagine": (1051, 13, 1038, 1064, "15-17", 6073, "May 2026", "Grok Imagine Video 1.5"),
    "kling-3-0": (1000, 0, 1000, 1000, "22", 6950, "Feb 2026", "Kling 3.0 1080p (Pro)"),
    "veo-3-1": (963, 14, 949, 977, "25-26", 5334, "Jan 2026", "Veo 3.1"),
}

# Additional listed variants (not used as the model's headline score).
AA_T2V_VARIANTS = {
    "minimax-hailuo-max": (1143, 14, 1129, 1157, "5-11", 4549, "Aug 2026", "MiniMax H3 Max"),
    "gemini-omni-flash-1.1": (1125, 12, 1113, 1137, "10-14", 8550, "Aug 2026", "Gemini Omni Flash 1.1"),
    "grok-imagine-lite": (987, 13, 974, 1000, "23-24", 8334, "Aug 2026", "Grok Imagine Video 1.5 Lite"),
    "kling-3-0-omni": (1016, 14, 1002, 1030, "21", 5685, "Feb 2026", "Kling 3.0 Omni 1080p (Pro)"),
    "veo-3-1-fast": (954, 14, 940, 968, "25-28", 6263, "Jan 2026", "Veo 3.1 Fast"),
    "veo-3-1-lite": (949, 14, 935, 963, "25-29", 5214, "Mar 2026", "Veo 3.1 Lite"),
}

# AA-Video-I2V v2.1 headline scores for models we track.
AA_I2V_SCORES = {
    "seedance-2-5": (1161, 15, 1146, 1176, "1-2", 6611, "Jul 2026", "Dreamina Seedance 2.5"),
    "minimax-hailuo": (1134, 14, 1120, 1148, "3-6", 6594, "Jul 2026", "MiniMax H3 (768p)"),
    "wan-3-0": (1109, 14, 1095, 1123, "8-13", 6761, "Aug 2026", "Wan 3.0"),
    "gemini-omni-flash": (1085, 15, 1070, 1100, "14", 5096, "Nov 2026", "Gemini Omni Flash 1.2"),
    "grok-imagine": (1047, 14, 1033, 1061, "17-19", 6806, "May 2026", "Grok Imagine Video 1.5"),
    "kling-3-0": (1000, 0, 1000, 1000, "22-24", 4903, "Feb 2026", "Kling 3.0 1080p (Pro)"),
    "veo-3-1": (955, 15, 940, 970, "25-27", 4950, "Jan 2026", "Veo 3.1"),
}

# Official capability notes: only facts tied to a source we cite on the page.
# length, resolution, audio, source_label key
OFFICIAL_SPECS = {
    "wan-3-0": (
        "2–30 seconds on the Higgsfield API model page",
        "480p, 720p, or 1080p on the Higgsfield API model page",
        "Unknown. Catalog rows mark audio as not stated. The model does appear on Artificial Analysis’s with-audio text-to-video board.",
        "hf_wan",
    ),
    "wan-3-0-prime": (
        "2–30 seconds on the Higgsfield API model page",
        "480p, 720p, or 1080p on the Higgsfield API model page",
        "Unknown. Catalog rows mark audio as not stated. The model is not on the Artificial Analysis boards we opened Nov 16, 2026.",
        "hf_prime",
    ),
    "kling-3-0": (
        "Unknown on the official API pricing table (it bills per second of output; a clip length is not printed there)",
        "720p, 1080p, or 4K on the official API pricing table",
        "Yes, as a billed option. Official API rates are listed with and without native audio (4K is the same either way)",
        "kling_api",
    ),
    "seedance-2-5": (
        "4–30 seconds on the Replicate model page for the official billed-by-property rate",
        "The cheapest catalog row is 480p; the same official page is the source for that row",
        "Unknown on the cheapest catalog row (audio is marked not stated)",
        "seedance",
    ),
    "veo-3-1": (
        "Veo 3.1 Lite: 4, 6, or 8 seconds. Veo 3.1 Quality: 8 seconds. From Google Flow credit help.",
        "Lite: 720p for all users, from Google Flow credit help. Higher paid Veo rows in the catalog include 1080p.",
        "Unknown as a single rule. Some official and catalog Veo rows are labeled with audio, some without.",
        "flow",
    ),
    "gemini-omni-flash": (
        "Up to 10 seconds for all users, and up to 15 seconds on Google AI Plus, Pro, and Ultra, from Google Flow credit help. The Gemini API pricing note also states a 15-second maximum.",
        "360p or 720p on Google Flow for Omni Flash 1.2. Catalog API pricing is stated for 720p.",
        "Unknown. Catalog rows mark audio as not stated. The model appears on Artificial Analysis’s with-audio text-to-video board.",
        "flow",
    ),
    "minimax-hailuo": (
        "Unknown on the official fal H3 Max Turbo model page used for the standard-rate catalog row",
        "The standard-rate catalog row is 480p; other catalog rows go up to 768p, 1080p, and 2K",
        "Unknown. Catalog rows mark audio as not stated. MiniMax H3 appears on Artificial Analysis’s with-audio boards.",
        "fal_h3",
    ),
    "runway-gen-4": (
        "Unknown on the official API pricing document (rates are per second; a maximum clip length is not printed on that page)",
        "Unknown on the official API pricing document for Gen-4 Turbo (the catalog row leaves resolution blank)",
        "Unknown on the official API pricing document",
        "runway_api",
    ),
    "grok-imagine": (
        "Up to 15 seconds, from the x.ai/grok product page",
        "The product page lists text-to-video up to 15 seconds at 720p, and a separate Imagine blurb says up to 2K. Which of those is the hard cap is not pinned down. The cheapest catalog row is 480p.",
        "Unknown as a single official rule. Some catalog rows are labeled with audio.",
        "xai",
    ),
}


def _src(g, url, text="source"):
    e = g["e"]
    href, rel = g["outbound"](url)
    return f'<a href="{e(href)}" rel="{rel}" target="_blank">{e(text)}</a>'


def usd(v, places=2):
    q = Decimal("1").scaleb(-places)
    n = Decimal(str(v)).quantize(q, rounding=ROUND_HALF_UP)
    text = f"{abs(n):.{places}f}"
    return f"${text}"


def row_by_id(rows, rid):
    for r in rows:
        if r.get("id") == rid:
            return r
    return None


def paid_phrase(g, r):
    rate_money = g["rate_money"]
    rate = rate_money(r["usd_per_second"]) + "/s"
    status = g["rate_label"](r)
    plat = r.get("platform") or "not stated"
    plan = guide_tables.plan_label(r)
    tier = g["shown_tier"](r)
    variant = r.get("variant") or r.get("model") or "model not stated"
    res = g["shown_resolution"](r)
    audio = g["audio_phrase"](r)
    return f"{rate} {status} · {plat} · plan: {plan} · tier: {tier} · {variant} · {res} · {audio}"


def elo_phrase(score):
    elo, pm, lo, hi, rng, samples, released, label = score
    if pm == 0:
        return (
            f"{label}: Elo {elo} (anchor, fixed as the reference point on this board), "
            f"rank range {rng}, {samples:,} samples, released {released}"
        )
    return (
        f"{label}: Elo {elo} ±{pm} (95% interval {lo}–{hi}), "
        f"rank range {rng}, {samples:,} samples, released {released}"
    )


def blurb(g):
    return (
        "Nine models compared on Artificial Analysis Elo and our cost per second, "
        "so you can pick by value, not by price alone."
    )


def description(g):
    last = __import__("timefmt").day_label(g.get("LAST") or CHECKED)
    text = (
        "Nine models compared on Artificial Analysis Elo and our cost per second, "
        f"with resolution, length, and audio. Last checked {last}."
    )
    if len(text) > 160:
        raise SystemExit(f"{PATH} meta description is over 160 characters: {len(text)}")
    return text


def render(g):
    e, root, LAST = g["e"], g["root"], g["LAST"]
    rate_money = g["rate_money"]
    outbound = g["outbound"]
    rows = g["rows"]

    def pick_model(slug, fallback_id=None):
        rs = guide_tables.active_rows(g, model=slug)
        if fallback_id:
            exact = [r for r in rs if r["id"] == fallback_id]
            if exact:
                return exact[0]
        return rs[0] if rs else row_by_id(rows, fallback_id)

    paid_picks = guide_tables.cheapest_by_model(g)
    by_slug = {r["model"]: r for r in paid_picks}
    hailuo_h3 = pick_model("minimax-hailuo", ROW_HAILUO)
    hailuo_plan = by_slug.get("minimax-hailuo") or pick_model("minimax-hailuo", ROW_HAILUO_PLAN)
    cost_picks = {
        "wan-3-0": by_slug.get("wan-3-0") or pick_model("wan-3-0", ROW_WAN),
        "wan-3-0-prime": by_slug.get("wan-3-0-prime") or pick_model("wan-3-0-prime", ROW_PRIME),
        "kling-3-0": by_slug.get("kling-3-0") or pick_model("kling-3-0", ROW_KLING),
        "seedance-2-5": by_slug.get("seedance-2-5") or pick_model("seedance-2-5", ROW_SEEDANCE),
        "veo-3-1": by_slug.get("veo-3-1") or pick_model("veo-3-1", ROW_VEO),
        "gemini-omni-flash": by_slug.get("gemini-omni-flash") or pick_model("gemini-omni-flash", ROW_OMNI),
        "minimax-hailuo": hailuo_h3,
        "runway-gen-4": by_slug.get("runway-gen-4") or pick_model("runway-gen-4", ROW_RUNWAY),
        "grok-imagine": by_slug.get("grok-imagine") or pick_model("grok-imagine", ROW_GROK),
    }
    found = {
        ROW_WAN: cost_picks["wan-3-0"],
        ROW_PRIME: cost_picks["wan-3-0-prime"],
        ROW_KLING: cost_picks["kling-3-0"],
        ROW_SEEDANCE: cost_picks["seedance-2-5"],
        ROW_VEO: cost_picks["veo-3-1"],
        ROW_OMNI: cost_picks["gemini-omni-flash"],
        ROW_HAILUO: hailuo_h3,
        ROW_HAILUO_PLAN: hailuo_plan,
        ROW_GROK: cost_picks["grok-imagine"],
        ROW_RUNWAY: cost_picks["runway-gen-4"],
    }
    row_dates = [r["checked"] for r in list(cost_picks.values()) + [hailuo_plan] if r and r.get("checked")]
    dates = [CHECKED, LAST] + row_dates
    g["SITEMAP_LASTMOD"][PATH] = max(dates)
    rows_checked = f"rows checked {max(row_dates)}" if row_dates else "row check dates not stored"
    paid_table = guide_tables.price_table(g, paid_picks, table_id="prices", include_model=True, min_width=1180)

    def src(url, text="source"):
        return _src(g, url, text)

    def row_src(r):
        href, rel = outbound(r["source_url"])
        link = f'<a href="{e(href)}" rel="{rel}" target="_blank">source</a>'
        return f'{link}, catalog row {e(r["id"])}, checked {e(__import__("timefmt").day_label(r.get("checked")))}'

    t2v_src = src(AA_T2V, "Artificial Analysis AA-Video-T2V v2.1 leaderboard")
    i2v_src = src(AA_I2V, "Artificial Analysis AA-Video-I2V v2.1 leaderboard")
    flow_src = src(FLOW_CREDITS, "Google Flow credit help")
    kling_api_src = src(KLING_API, "official Kling API pricing")
    hf_wan_src = src(HF_WAN, "Higgsfield API Wan 3.0 model page")
    hf_prime_src = src(HF_PRIME, "Higgsfield API Wan 3.0 Prime model page")
    xai_src = src(XAI_GROK, "x.ai/grok")
    runway_api_src = src(RUNWAY_API, "official Runway API pricing document")
    seedance_src = src(REPLIT_SEEDANCE, "Replicate Seedance 2.5 model page")
    gemini_src = src(GEMINI_PRICING, "Gemini API pricing")
    fal_src = src(FAL_H3, "fal MiniMax H3 Max Turbo model page")

    src_map = {
        "hf_wan": hf_wan_src,
        "hf_prime": hf_prime_src,
        "kling_api": kling_api_src,
        "seedance": seedance_src,
        "flow": flow_src,
        "fal_h3": fal_src,
        "runway_api": runway_api_src,
        "xai": xai_src,
    }

    cheap_href = root("/guides/cheapest-ai-video-generator/")
    free_href = root("/guides/free-ai-video-generators/")
    wan_href = root("/guides/cheapest-wan-3-0/")
    kling_href = root("/guides/kling-ai-pricing/")
    runway_href = root("/guides/runway-pricing/")
    seedance_href = root("/guides/cheapest-seedance-2-5/")
    grok_href = root("/guides/grok-imagine-video-cost/")
    hf_href = root("/guides/higgsfield-pricing/")
    budget_href = root("/guides/ai-video-project-budget/")
    flow_href = root("/guides/google-flow-credits-calculator/")
    calc_href = root("/calculator/")

    model_hrefs = {
        "wan-3-0": root("/models/wan-3-0/"),
        "wan-3-0-prime": root("/models/wan-3-0-prime/"),
        "kling-3-0": root("/models/kling-3-0/"),
        "seedance-2-5": root("/models/seedance-2-5/"),
        "veo-3-1": root("/models/veo-3-1/"),
        "gemini-omni-flash": root("/models/gemini-omni-flash/"),
        "minimax-hailuo": root("/models/minimax-hailuo/"),
        "runway-gen-4": root("/models/runway-gen-4/"),
        "grok-imagine": root("/models/grok-imagine/"),
    }
    names = {
        "wan-3-0": "Wan 3.0",
        "wan-3-0-prime": "Wan 3.0 Prime",
        "kling-3-0": "Kling 3.0",
        "seedance-2-5": "Seedance 2.5",
        "veo-3-1": "Veo 3.1",
        "gemini-omni-flash": "Gemini Omni Flash",
        "minimax-hailuo": "MiniMax Hailuo / H3",
        "runway-gen-4": "Runway Gen-4",
        "grok-imagine": "Grok Imagine",
    }
    cost_row = {
        "wan-3-0": found[ROW_WAN],
        "wan-3-0-prime": found[ROW_PRIME],
        "kling-3-0": found[ROW_KLING],
        "seedance-2-5": found[ROW_SEEDANCE],
        "veo-3-1": found[ROW_VEO],
        "gemini-omni-flash": found[ROW_OMNI],
        "minimax-hailuo": found[ROW_HAILUO],
        "runway-gen-4": found[ROW_RUNWAY],
        "grok-imagine": found[ROW_GROK],
    }

    # Order: published T2V Elo high to low, then unknown.
    order = [
        "wan-3-0",
        "minimax-hailuo",
        "seedance-2-5",
        "gemini-omni-flash",
        "grok-imagine",
        "kling-3-0",
        "veo-3-1",
        "wan-3-0-prime",
        "runway-gen-4",
    ]

    body_rows = []
    for slug in order:
        score = AA_T2V_SCORES.get(slug)
        if score:
            quality = e(elo_phrase(score)) + f". {t2v_src}."
        else:
            quality = (
                "Unknown. This model was not listed on the AA-Video-T2V v2.1 or "
                f"AA-Video-I2V v2.1 boards we opened Nov 16, 2026. {t2v_src} · {i2v_src}."
            )
        length, res, audio, sk = OFFICIAL_SPECS[slug]
        official = src_map[sk]
        r = cost_row[slug]
        cost = e(paid_phrase(g, r)) + f". {row_src(r)}."
        if slug == "minimax-hailuo":
            plan = found[ROW_HAILUO_PLAN]
            cost += (
                f" A catalog promo row (r194) at a lower fal rate ended November 15, 2026; "
                f"this guide uses the standard rate, which the vendor page says resumes "
                f"November 16. A cheaper non-promo estimate also exists: "
                f"{e(paid_phrase(g, plan))}. {row_src(plan)}. That estimate is Hailuo 2.3, "
                f"not the MiniMax H3 row on the leaderboard."
            )
        name = f'<a href="{e(model_hrefs[slug])}">{e(names[slug])}</a>'
        if sk == "flow":
            length_cell, res_cell, audio_cell = e(length), e(res), e(audio)
        else:
            length_cell = f"{e(length)}. {official}."
            res_cell = f"{e(res)}. {official}."
            audio_cell = f"{e(audio)}. {official}."
        body_rows.append(
            "<tr>"
            f"<td>{name}</td>"
            f"<td>{quality}</td>"
            f"<td>{length_cell}</td>"
            f"<td>{res_cell}</td>"
            f"<td>{audio_cell}</td>"
            f"<td>{cost}</td>"
            "</tr>"
        )

    table = f"""<div class="tblwrap" id="best-value-table">
<table style="min-width:1080px;width:1080px">
<thead><tr>
<th>Model</th>
<th>Quality (Artificial Analysis Elo)</th>
<th>Official max length</th>
<th>Official resolution</th>
<th>Native audio</th>
<th>Cheapest catalog rate we track</th>
</tr></thead>
<tbody>
{"".join(body_rows)}
</tbody>
</table>
</div>"""

    wan = found[ROW_WAN]
    hailuo = found[ROW_HAILUO]
    omni = found[ROW_OMNI]
    seedance = found[ROW_SEEDANCE]
    grok = found[ROW_GROK]
    veo = found[ROW_VEO]
    kling = found[ROW_KLING]

    a_best = (
        "Among the nine models this site tracks, Wan 3.0 has the highest published "
        "text-to-video Elo on AA-Video-T2V v2.1: 1174 ±13, rank range 1–2. That "
        "range overlaps Utopai X, which we do not track. MiniMax H3 (768p) at 1159, "
        "Dreamina Seedance 2.5 at 1156, and Gemini Omni Flash 1.2 at 1151 also have "
        "overlapping 95% intervals, so this site does not treat those four as a "
        "settled 1–2–3–4 finish. Wan 3.0 is also the cheapest of that high-Elo group "
        f"in our catalog, at {rate_money(wan['usd_per_second'])}/s on {wan['platform']} "
        f"({guide_tables.plan_label(wan)}, tier {g['shown_tier'](wan)}) at {g['shown_resolution'](wan)}, "
        f"{guide_tables.audio_label(g, wan)}, if you use every credit you "
        "pay for. If you only want the lowest dollar figure, use the cheapest-by-model "
        "guide instead."
    )

    a_quality = (
        "Artificial Analysis’s AA-Video-T2V v2.1 board ranks models on generating "
        "video with audio from a text prompt, using Elo from pairwise human "
        "preference votes. The page was opened Nov 16, 2026 without signing in. Scores "
        "below are copied from that board, including the 95% interval, rank range, "
        "and sample count. Models that are not listed are marked unknown. We do "
        "not invent Elo numbers. A separate image-to-video board, AA-Video-I2V v2.1, "
        "is cited where it changes the picture, especially for Seedance 2.5."
    )

    a_cost = (
        "Every dollar-per-second figure is the cheapest current catalog row we "
        "track for that model, with its platform, plan or API, variant, resolution, "
        "audio, and rate label. Credit-plan figures assume you use every credit you "
        "pay for. A fal promo for MiniMax H3 Max Turbo ended November 15, 2026, so "
        "this guide uses the standard fal rate that the vendor page says resumes "
        "November 16, plus a cheaper Hailuo 2.3 plan estimate that is not the H3 "
        "leaderboard row."
    )

    a_use = (
        "For the highest published text-to-video quality among models we track, "
        "and the best value in that high-Elo group: Wan 3.0. For image-to-video "
        "quality: Seedance 2.5 leads AA-Video-I2V v2.1, but it is the most expensive "
        "model we track. For a cheaper high-Elo alternative: MiniMax H3 or Gemini "
        "Omni Flash 1.2, whose intervals overlap Wan 3.0’s neighbors. For a low-cost "
        "draft: Grok Imagine 1.5 Lite in the catalog at a lower Elo. For a model "
        "with no public Elo: Runway Gen-4 and Wan 3.0 Prime are unknown on the "
        "boards we opened, so this page does not rank them on quality."
    )

    a_unknown = (
        "Unknown, and not guessed: Artificial Analysis Elo for Wan 3.0 Prime and "
        "Runway Gen-4, which were not on the boards we opened; official maximum "
        "clip length for Kling 3.0, Runway Gen-4, and MiniMax H3 Max Turbo on the "
        "pages cited for those rows; official resolution on the Runway Gen-4 Turbo "
        "API pricing document; and native audio as a vendor-stated yes-or-no for "
        "Wan 3.0, Wan 3.0 Prime, Seedance 2.5 on the cheapest row, Gemini Omni Flash, "
        "MiniMax H3, Runway Gen-4, and Grok Imagine as a single official rule. "
        "Elo intervals that overlap are not treated as a settled rank order."
    )

    q_audio = "Which of the models we cover can add audio or sound?"
    a_audio = (
        f"The official length and audio table on this page, last read {CHECKED_WHEN}, is the source for these yes-or-no calls. "
        "Of the nine models we cover, only Kling 3.0 has a clear official yes: native audio is a billed option on the official API pricing table. "
        "Veo 3.1 is mixed: some official and catalog rows are labeled with audio, some without. "
        "For Wan 3.0, Wan 3.0 Prime, Seedance 2.5 on the cheapest catalog row, Gemini Omni Flash, MiniMax Hailuo, Runway Gen-4, and Grok Imagine, "
        "the official pages used for that table do not state a single yes-or-no audio rule. "
        "Those vendor audio pages were not all re-opened on Nov 16, 2026."
    )
    q_longest = "Which of the models we cover can make the longest clip?"
    a_longest = (
        f"The official length table on this page, last read {CHECKED_WHEN}, lists a 30-second maximum for Wan 3.0, Wan 3.0 Prime, and Seedance 2.5. "
        "Those three vendor pages were not re-opened on Nov 16, 2026. "
        f"We re-checked two shorter official caps on {POLICY_CHECKED_WHEN}: "
        "Grok Imagine is up to 15 seconds on the official product page, and Google Flow Help lists Veo 3.1 Lite and Fast at 4, 6, or 8 seconds, "
        "and Veo 3.1 Quality at 8 seconds. "
        "Gemini Omni Flash is listed at up to 10 seconds for all users, and up to 15 seconds on Google AI Plus, Pro, and Ultra, from that same Nov 16 Flow-help citation. "
        "Official maximum clip lengths for Kling 3.0, MiniMax Hailuo, and Runway Gen-4 were not printed on the vendor pages used for that table."
    )
    q_prices = "What is the cheapest per-second price for each covered model?"
    cheapest_all = paid_picks[0]
    a_prices = (
        f"Every dollar-per-second figure in the table below comes from data/prices.json ({rows_checked}), "
        f"sorted cheapest first. The lowest rate we track is {rate_money(cheapest_all['usd_per_second'])}/s "
        f"for {names[cheapest_all['model']]} on {cheapest_all['platform']} ({guide_tables.plan_label(cheapest_all)}, "
        f"tier {g['shown_tier'](cheapest_all)}, {g['shown_resolution'](cheapest_all)}, "
        f"{guide_tables.audio_label(g, cheapest_all)}), {g['rate_label'](cheapest_all)}."
    )
    faqs = [
        (QUESTION, a_best),
        (q_prices, a_prices),
        ("How do you measure quality?", a_quality),
        ("How do you measure cost?", a_cost),
        ("Which model is best for each use?", a_use),
        (q_audio, a_audio),
        (q_longest, a_longest),
        ("What is confirmed, and what is not?", a_unknown),
    ]
    for q, a in faqs:
        raw = (q + " " + a).lower()
        for bad in ("subscribe", "newsletter", "buttondown"):
            if bad in raw:
                raise SystemExit(f"{PATH} FAQ text contains {bad}")

    lead = (
        f"The cheapest model is not always the best one to actually use. This guide "
        f"ranks the nine models we track on published quality and on cost, and it "
        f"leaves quality blank when there is no public score. Quality scores were "
        f"read {e(CHECKED_WHEN)} from {t2v_src}, which uses Elo from pairwise human "
        f"preference votes on text-to-video with audio. Cost comes from our catalog, "
        f"not from Artificial Analysis’s API $/minute column. If you only want the "
        f"lowest dollar figure, see <a href=\"{e(cheap_href)}\">the cheapest AI video "
        f"generator by model</a>."
    )

    body = f"""<p class="small"><a href="{root("/guides/")}">Guides</a> › Best AI video generator</p>
<h1>{e(PHRASE)}</h1>
<p class="lead">{lead}</p>
<p class="small">Last checked {e(LAST)}. Official quality scores were read {e(CHECKED_WHEN)}. Catalog paid-step rows use the date on each row. Affiliate links never change this price order. Every dollar-per-second figure below states its seller, plan, tier, resolution, audio, usage assumption, and source.</p>

<div class="card" id="takeaways">
<h2>Key takeaways</h2>
<ul>
<li><b>Top T2V Elo &amp; value.</b> <a href="{e(model_hrefs['wan-3-0'])}">Wan 3.0</a> leads AA-Video-T2V v2.1 at 1174 ±13 and costs {e(rate_money(wan['usd_per_second']))}/s on {e(wan['platform'])} ({e(guide_tables.plan_label(wan))}, {e(g['shown_resolution'](wan))}, {e(guide_tables.audio_label(g, wan))}).</li>
<li><b>Top I2V Elo.</b> <a href="{e(model_hrefs['seedance-2-5'])}">Seedance 2.5</a> leads AA-Video-I2V v2.1 at 1161 ±15, from {e(rate_money(seedance['usd_per_second']))}/s on {e(seedance['platform'])} ({e(g['shown_resolution'](seedance))}, {e(guide_tables.audio_label(g, seedance))}).</li>
<li><b>Cheapest catalog rate overall.</b> {e(rate_money(cheapest_all['usd_per_second']))}/s for {e(names[cheapest_all['model']])} on {e(cheapest_all['platform'])} ({e(guide_tables.plan_label(cheapest_all))}, {e(g['shown_resolution'](cheapest_all))}, {e(guide_tables.audio_label(g, cheapest_all))}), checked {e(__import__("timefmt").day_label(cheapest_all.get("checked")))}.</li>
<li><b>Unranked on quality.</b> Runway Gen-4 and Wan 3.0 Prime were absent from the AA boards opened Nov 16, 2026, so quality stays unknown.</li>
</ul>
</div>

<h2>{e(q_prices)}</h2>
<p>{e(a_prices)}</p>
{paid_table}
<p class="small">Every row above comes from data/prices.json, sorted by dollars per second. Affiliate links never change this price order.</p>

<h2>{e(QUESTION)}</h2>
<p>{e(a_best)}</p>

<h2>How do you measure quality?</h2>
<p>{e(a_quality)} {t2v_src}, opened {e(CHECKED_WHEN)}. {i2v_src} was opened at the same time. Official length, resolution, and audio are taken only from the vendor pages cited in each cell. Anything those pages do not state is marked unknown.</p>
{table}
<p class="small">Artificial Analysis’s pricing footnote says its $/minute column is the model creator’s API cost for one minute at the settings they benchmark (1080p where offered). This site does not use that column for ranking. Our dollar-per-second figures are the catalog rows above, each with a vendor URL.</p>

<h2>How do you measure cost?</h2>
<p>{e(a_cost)}</p>

<h2>Which model is best for each use?</h2>
<p>{e(a_use)}</p>
<ul>
<li><b>Highest published text-to-video quality, and the best value in that group.</b> <a href="{e(model_hrefs['wan-3-0'])}">Wan 3.0</a> at Elo 1174 ±13 (range 1–2) on {t2v_src}, and {e(paid_phrase(g, wan))} in our catalog. {row_src(wan)}. See <a href="{e(wan_href)}">the cheapest way to use Wan 3.0</a>.</li>
<li><b>Image-to-video quality.</b> <a href="{e(model_hrefs['seedance-2-5'])}">Seedance 2.5</a> leads {i2v_src} at Elo 1161 ±15 (range 1–2). It is also the most expensive model we track: {e(paid_phrase(g, seedance))}. {row_src(seedance)}. See <a href="{e(seedance_href)}">the cheapest way to use Seedance 2.5</a>.</li>
<li><b>A close high-Elo alternative.</b> MiniMax H3 (768p) and Gemini Omni Flash 1.2 overlap the top group’s intervals on the text-to-video board. The standard fal rate for H3 Max Turbo is {e(paid_phrase(g, hailuo))}. {row_src(hailuo)}. Omni Flash 1.2 is {e(paid_phrase(g, omni))}. {row_src(omni)}. {gemini_src}.</li>
<li><b>A lower-cost draft.</b> Grok Imagine 1.5 sits lower on the text-to-video board (Elo 1051 ±13, range 15–17), and the Lite variant is lower still (Elo 987 ±13). The cheapest catalog row is {e(paid_phrase(g, grok))}. {row_src(grok)}. See <a href="{e(grok_href)}">how much a Grok Imagine video costs</a>.</li>
<li><b>If you only care about price.</b> Do not use this page as a price-only ranking. Use <a href="{e(cheap_href)}">the cheapest AI video generator by model</a> instead. Veo 3.1 Lite, for example, is inexpensive in the catalog at {e(paid_phrase(g, veo))}, but its text-to-video Elo is 949 ±14, well below the top group. {row_src(veo)}.</li>
<li><b>No public quality score.</b> <a href="{e(model_hrefs['runway-gen-4'])}">Runway Gen-4</a> and <a href="{e(model_hrefs['wan-3-0-prime'])}">Wan 3.0 Prime</a> were not on the Artificial Analysis boards we opened Nov 16, 2026, so their quality is unknown here. Their catalog rates are still listed in the table. See <a href="{e(runway_href)}">Runway pricing per second</a>.</li>
</ul>
<p>Related: <a href="{e(kling_href)}">Kling AI pricing and credits</a> · <a href="{e(hf_href)}">Higgsfield pricing explained</a> · <a href="{e(flow_href)}">Google Flow credits calculator</a> · <a href="{e(free_href)}">free AI video generators: what you get</a> · <a href="{e(budget_href)}">project budget calculator</a> · <a href="{e(calc_href)}">credit calculator</a>.</p>

<h2>{e(q_audio)}</h2>
<p>{e(a_audio)} The cell-by-cell sources are in the official length, resolution, and audio table above, last read {e(CHECKED_WHEN)}.</p>

<h2>{e(q_longest)}</h2>
<p>{e(a_longest)} Sources re-read {e(POLICY_CHECKED_WHEN)}: {xai_src} for the 15-second Grok Imagine cap, and {flow_src} for Veo 3.1 Lite, Fast, and Quality lengths. Wan, Seedance, and Omni Flash length citations stay dated {e(CHECKED_WHEN)} in the table above.</p>

<h2>What is confirmed, and what is not?</h2>
<p>{e(a_unknown)}</p>
<p><b>Confirmed {e(CHECKED_WHEN)} on Artificial Analysis:</b> the Elo figures, intervals, rank ranges, and sample counts in the table, from {t2v_src} and {i2v_src}. <b>Confirmed in the catalog ({e(rows_checked)}):</b> the paid-step $/s figures, each with its vendor URL, usage assumption, tier, resolution, and audio.</p>
<p class="small">Affiliate links never change this price order.</p>
{g["how_block"]()}
"""

    if "sora" in body.lower() or "sora" in description(g).lower() or "sora" in PHRASE.lower():
        raise SystemExit(f"{PATH} source would name Sora")

    title = g["page_title"](PHRASE)
    desc = description(g)
    g["guide_page"](PATH, title, desc, body, faqs)
    return PATH
