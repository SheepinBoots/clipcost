/**
 * Tool handlers. They read a catalog object and never fetch the network.
 * Dollar amounts for credit plans use the calculator formulas. API totals are
 * billed seconds times the stated dollars per second. Missing prices stay missing.
 */

import { calculatorMap, type Deal, type PlanDeal, type PlanRecord, unlimitedHit } from "./deals.ts";
import { stampVidfareLinks, withUtm } from "./links.ts";
import { clipCount, currentRow, isNum, money, quote, type PriceRow } from "./quote.ts";

export const PRICES_URL = "https://vidfare.com/data/prices.json";
export const DEALS_URL = "https://vidfare.com/deals.json";
export const SITE = "https://vidfare.com";

const AUDIO: Record<string, string> = { with: "with", without: "without", on: "with", off: "without" };
const INPUTS = new Set(["t2v", "i2v", "ref2v", "v2v", "extend", "lip-sync"]);

export type PricesFile = {
  models?: Record<string, { name?: string; maker?: string }>;
  plans?: Record<string, PlanRecord>;
  rows?: PriceRow[];
  last_full_check?: string;
  generated?: string;
};

export type DealsFile = {
  updated?: string;
  deals?: Deal[];
  upcoming?: Deal[];
  archive?: Deal[];
  history?: Deal[];
};

export type Catalog = {
  prices: PricesFile;
  deals: DealsFile;
  today: string;
  fromCache: boolean;
  pricesUrl: string;
  dealsUrl: string;
};

type ToolResult = { isError?: boolean; data: Record<string, unknown> };

export function runTool(name: string, args: Record<string, unknown>, catalog: Catalog): ToolResult {
  const handlers: Record<string, (args: Record<string, unknown>, catalog: Catalog) => ToolResult> = {
    list_models: listModels,
    get_model_prices: getModelPrices,
    estimate_cost: estimateCost,
    cheapest_options: cheapestOptions,
    list_deals: listDeals,
  };
  const handler = handlers[name];
  if (!handler) {
    return fail(catalog, "That tool is not on this server.", sitePage("/mcp/"));
  }
  const result = handler(args ?? {}, catalog);
  return { isError: result.isError, data: stampVidfareLinks(result.data) };
}

function fail(catalog: Catalog, message: string, page: string, source = catalog.pricesUrl): ToolResult {
  return {
    isError: true,
    data: {
      missing: true,
      message,
      citation: citation(catalog, source, page, lastChecked(catalog)),
    },
  };
}

function citation(catalog: Catalog, source: string, page: string, checked: string) {
  return {
    source_url: withUtm(source),
    last_checked: checked || "not stated",
    page: withUtm(page),
    from_cache: catalog.fromCache,
  };
}

function lastChecked(catalog: Catalog): string {
  return catalog.prices.last_full_check || catalog.prices.generated || "";
}

function sitePage(path: string): string {
  return SITE + path;
}

function modelsOf(catalog: Catalog) {
  return catalog.prices.models ?? {};
}

function plansOf(catalog: Catalog) {
  return catalog.prices.plans ?? {};
}

function rowsOf(catalog: Catalog): PriceRow[] {
  return (catalog.prices.rows ?? []).filter((row) => currentRow(row, catalog.today));
}

function resolveModel(catalog: Catalog, raw: unknown): { slug: string; name: string; maker: string } | null {
  const text = typeof raw === "string" ? raw.trim() : "";
  if (!text) return null;
  const models = modelsOf(catalog);
  if (models[text]) return { slug: text, name: models[text].name || text, maker: models[text].maker || "" };
  const lower = text.toLowerCase();
  for (const [slug, model] of Object.entries(models)) {
    if ((model.name || "").toLowerCase() === lower) return { slug, name: model.name || slug, maker: model.maker || "" };
  }
  return null;
}

function normalizeAudio(raw: unknown): { ok: true; value: string | null } | { ok: false; message: string } {
  if (raw == null || raw === "") return { ok: true, value: null };
  const key = String(raw).trim().toLowerCase();
  if (!AUDIO[key]) return { ok: false, message: "Audio must be with, without, on, or off. VidFare does not guess a price for any other value." };
  return { ok: true, value: AUDIO[key] };
}

function readInput(raw: unknown): { ok: true; value: string | null } | { ok: false; message: string } {
  if (raw == null || raw === "") return { ok: true, value: null };
  const key = String(raw).trim().toLowerCase();
  if (!INPUTS.has(key)) {
    return { ok: false, message: "Input must be t2v, i2v, ref2v, v2v, extend, or lip-sync. VidFare does not guess a price for any other value." };
  }
  return { ok: true, value: key };
}

function readSeconds(raw: unknown, required: boolean): { ok: true; value: number | null } | { ok: false; message: string } {
  if (raw == null || raw === "") {
    if (required) return { ok: false, message: "seconds is required and must be a whole number of 1 or more. No cost is estimated." };
    return { ok: true, value: null };
  }
  const n = typeof raw === "number" ? raw : Number(String(raw).trim());
  if (!Number.isInteger(n) || n < 1) {
    return { ok: false, message: "seconds must be a whole number of 1 or more. No cost is estimated." };
  }
  return { ok: true, value: n };
}

function readUsed(raw: unknown): { ok: true; value: number } | { ok: false; message: string } {
  if (raw == null || raw === "") return { ok: true, value: 100 };
  const n = typeof raw === "number" ? raw : Number(String(raw).trim());
  if (!Number.isInteger(n) || n < 1 || n > 100) {
    return { ok: false, message: "used must be a whole number from 1 to 100, the percent of credits used. No cost is estimated." };
  }
  return { ok: true, value: n };
}

function readWindow(raw: unknown): { ok: true; value: number } | { ok: false; message: string } {
  if (raw == null || raw === "") return { ok: true, value: 60 };
  const n = typeof raw === "number" ? raw : Number(String(raw).trim());
  if (!Number.isInteger(n) || n < 1) return { ok: false, message: "window_seconds must be a whole number of 1 or more." };
  return { ok: true, value: n };
}

function textOpt(raw: unknown): string | null {
  if (raw == null) return null;
  const text = String(raw).trim();
  return text || null;
}

function calculatorQuery(opts: {
  model?: string | null;
  plan?: string | null;
  provider?: string | null;
  resolution?: string | null;
  seconds?: number | null;
  audio?: string | null;
  input?: string | null;
  used?: number | null;
}): string {
  const params = new URLSearchParams();
  if (opts.plan) params.set("plan", opts.plan);
  if (opts.model) params.set("model", opts.model);
  if (opts.provider) params.set("provider", opts.provider);
  if (opts.resolution) params.set("resolution", opts.resolution);
  if (opts.seconds != null) params.set("seconds", String(opts.seconds));
  if (opts.audio) params.set("audio", opts.audio);
  if (opts.input) params.set("input", opts.input);
  if (opts.used != null && opts.used !== 100) params.set("used", String(opts.used));
  const qs = params.toString();
  return sitePage("/calculator/" + (qs ? "?" + qs : ""));
}

function modelPage(slug: string): string {
  return sitePage(`/models/${slug}/`);
}

function dealGroups(catalog: Catalog): { live: Deal[]; upcoming: Deal[]; ended: Deal[]; updated: string } {
  const doc = catalog.deals;
  const today = catalog.today;
  const published = Array.isArray(doc.archive) || Array.isArray(doc.upcoming) || Array.isArray(doc.history);
  if (published) {
    const live = (doc.deals ?? []).filter((deal) => (deal.status || "live") === "live" && (!deal.end || deal.end >= today) && (!deal.start || deal.start <= today));
    const upcoming = (doc.upcoming ?? []).filter((deal) => !deal.start || deal.start > today);
    const ended = [...(doc.archive ?? []), ...(doc.history ?? [])];
    return { live, upcoming, ended, updated: doc.updated || "" };
  }
  const live: Deal[] = [];
  const upcoming: Deal[] = [];
  const ended: Deal[] = [];
  for (const deal of doc.deals ?? []) {
    const status = deal.status || "unconfirmed";
    if (status === "live" && deal.end && deal.end < today) ended.push({ ...deal, status: "ended" });
    else if (status === "live" && deal.start && deal.start > today) upcoming.push({ ...deal, status: "upcoming" });
    else if (status === "live") live.push(deal);
    else if (status === "upcoming") upcoming.push(deal);
    else ended.push(deal);
  }
  for (const deal of doc.history ?? []) ended.push(deal);
  return { live, upcoming, ended, updated: doc.updated || "" };
}

function listModels(_args: Record<string, unknown>, catalog: Catalog): ToolResult {
  const rows = rowsOf(catalog);
  const models = Object.entries(modelsOf(catalog)).map(([slug, model]) => {
    const mine = rows.filter((row) => row.model === slug && isNum(row.usd_per_second));
    const best = mine.length ? mine.reduce((a, b) => (a.usd_per_second! < b.usd_per_second! ? a : b)) : null;
    return {
      slug,
      name: model.name || slug,
      maker: model.maker || "",
      page: modelPage(slug),
      cheapest_usd_per_second: best ? best.usd_per_second : null,
      cheapest_display: best ? money(best.usd_per_second!) + "/s" : null,
      cheapest_platform: best?.platform ?? null,
      cheapest_variant: best?.variant ?? null,
      vendor_source_url: best?.source_url ?? null,
      checked: best?.checked ?? null,
      missing: !best,
      message: best ? undefined : "VidFare has no current price for this model.",
    };
  });
  return {
    data: {
      models,
      count: models.length,
      citation: citation(catalog, catalog.pricesUrl, sitePage("/models/"), lastChecked(catalog)),
    },
  };
}

function getModelPrices(args: Record<string, unknown>, catalog: Catalog): ToolResult {
  const model = resolveModel(catalog, args.model);
  if (!model) return fail(catalog, "That model is not in the VidFare catalog. No price is shown.", sitePage("/models/"));
  const provider = textOpt(args.provider);
  const resolution = textOpt(args.resolution);
  let rows = rowsOf(catalog).filter((row) => row.model === model.slug);
  if (provider) rows = rows.filter((row) => (row.platform || "").toLowerCase() === provider.toLowerCase());
  if (resolution) rows = rows.filter((row) => {
    const result = quote(row, { resolution });
    return result.status === "match" || result.status === "unknown";
  });
  const prices = rows
    .sort((a, b) => (a.usd_per_second ?? Infinity) - (b.usd_per_second ?? Infinity))
    .map((row) => rowPrice(catalog, row, model.slug));
  const page = modelPage(model.slug);
  return {
    data: {
      model: model.slug,
      model_name: model.name,
      provider: provider,
      resolution: resolution,
      count: prices.length,
      missing: prices.length === 0,
      message: prices.length ? undefined : "VidFare has no current price for that combination.",
      prices,
      citation: citation(catalog, catalog.pricesUrl, page, lastChecked(catalog)),
    },
  };
}

function rowPrice(catalog: Catalog, row: PriceRow, slug: string) {
  const plans = plansOf(catalog);
  const plan = row.plan ? plans[row.plan] : undefined;
  const page = row.plan
    ? calculatorQuery({
      model: slug,
      plan: row.plan,
      provider: plan?.platform || row.platform || null,
      resolution: shownResolution(row),
    })
    : modelPage(slug);
  return {
    id: row.id ?? null,
    variant: row.variant ?? null,
    platform: row.platform ?? null,
    kind: row.kind ?? null,
    plan: row.plan ?? null,
    resolution: row.resolution ?? null,
    audio: row.variation?.audio ?? "not stated",
    input: row.variation?.input ?? "not stated",
    status: row.status ?? null,
    usd_per_second: isNum(row.usd_per_second) ? row.usd_per_second : null,
    display: isNum(row.usd_per_second) ? money(row.usd_per_second) + "/s" : null,
    vendor_source_url: row.source_url ?? null,
    checked: row.checked ?? null,
    page,
    length: lengthNote(row),
  };
}

function shownResolution(row: PriceRow): string | null {
  const res = String(row.resolution ?? "").trim();
  if (!res || res === "—" || res === "-" || res === "–" || res === "Pro tier" || res === "Pro" || res === "Standard") return "not listed";
  return res;
}

function lengthNote(row: PriceRow): string {
  const duration = row.variation?.duration ?? {};
  if (Array.isArray(duration.rate_by_length)) return "The page states different per-second rates by length.";
  if (isNum(duration.priced_seconds)) return `Priced at ${duration.priced_seconds}s.`;
  if (isNum(duration.min_seconds) && isNum(duration.max_seconds)) return `${duration.min_seconds}–${duration.max_seconds}s.`;
  if (isNum(duration.max_seconds)) return `Up to ${duration.max_seconds}s.`;
  if (row.variation?.length_changes_price === false) return "The page states a per-second rate that does not change with length.";
  return "Length is not stated.";
}

function estimateCost(args: Record<string, unknown>, catalog: Catalog): ToolResult {
  const model = resolveModel(catalog, args.model);
  if (!model) return fail(catalog, "That model is not in the VidFare catalog. No cost is estimated.", sitePage("/calculator/"));
  const seconds = readSeconds(args.seconds, true);
  if (!seconds.ok) return fail(catalog, seconds.message, calculatorQuery({ model: model.slug }));
  const audio = normalizeAudio(args.audio);
  if (!audio.ok) return fail(catalog, audio.message, calculatorQuery({ model: model.slug, seconds: seconds.value }));
  const input = readInput(args.input);
  if (!input.ok) return fail(catalog, input.message, calculatorQuery({ model: model.slug, seconds: seconds.value }));
  const used = readUsed(args.used);
  if (!used.ok) return fail(catalog, used.message, calculatorQuery({ model: model.slug, seconds: seconds.value }));
  const windowSeconds = readWindow(args.window_seconds);
  if (!windowSeconds.ok) return fail(catalog, windowSeconds.message, calculatorQuery({ model: model.slug, seconds: seconds.value }));
  const resolution = textOpt(args.resolution);
  const planArg = textOpt(args.plan);
  const providerArg = textOpt(args.provider);
  const plans = plansOf(catalog);
  let planId: string | null = null;
  let providerForLink: string | null = null;
  let platformFilter: string | null = null;
  const notes: string[] = [];
  if (planArg) {
    if (!plans[planArg]) {
      return fail(catalog, "That plan is not in the VidFare catalog. No cost is estimated.", calculatorQuery({ model: model.slug, seconds: seconds.value }));
    }
    planId = planArg;
    providerForLink = plans[planArg].platform || null;
    if (providerArg && providerForLink && providerArg.toLowerCase() !== providerForLink.toLowerCase()) {
      notes.push("The plan id was used. The provider name does not match that plan, so it was not applied.");
      providerForLink = plans[planArg].platform || null;
    }
  } else if (providerArg) {
    const hit = Object.keys(plans).find((id) => (plans[id].platform || "").toLowerCase() === providerArg.toLowerCase());
    if (hit) {
      planId = hit;
      providerForLink = plans[hit].platform || providerArg;
      notes.push(`Provider ${providerForLink} selects ${plans[hit].plan}, the first ${providerForLink} plan in the catalog, the same way the calculator does.`);
    } else {
      const platforms = new Set(rowsOf(catalog).map((row) => row.platform || ""));
      const found = [...platforms].find((name) => name.toLowerCase() === providerArg.toLowerCase());
      if (!found) {
        return fail(catalog, "That provider is not in the VidFare catalog. No cost is estimated.", calculatorQuery({ model: model.slug, seconds: seconds.value }));
      }
      platformFilter = found;
      providerForLink = null;
    }
  }
  const applyDeals = args.apply_deals === true;
  const groups = dealGroups(catalog);
  const map = applyDeals ? calculatorMap(groups.live, plans, catalog.today) : {};
  let rows = rowsOf(catalog).filter((row) => row.model === model.slug);
  if (planId) rows = rows.filter((row) => row.plan === planId);
  else if (platformFilter) rows = rows.filter((row) => row.platform === platformFilter);
  const priced = [];
  const notPriced = [];
  for (const row of rows) {
    const judged = quote(row, { seconds: seconds.value, audio: audio.value, inputType: input.value, resolution });
    if (judged.status === "not_offered" || judged.status === "not_stated" || !isNum(judged.usd_per_second)) {
      notPriced.push({
        id: row.id ?? null,
        platform: row.platform ?? null,
        variant: row.variant ?? null,
        resolution: row.resolution ?? null,
        quote_status: judged.status,
        detail: judged.detail,
      });
      continue;
    }
    priced.push(priceRow(catalog, row, judged, {
      seconds: seconds.value!,
      used: used.value,
      windowSeconds: windowSeconds.value,
      deal: row.plan ? map[row.plan] : undefined,
      applyDeals,
      modelSlug: model.slug,
    }));
  }
  priced.sort((a, b) => (a.total_usd ?? Infinity) - (b.total_usd ?? Infinity) || String(a.platform).localeCompare(String(b.platform)));
  const page = calculatorQuery({
    model: model.slug,
    plan: planId,
    provider: providerForLink,
    resolution,
    seconds: seconds.value,
    audio: audio.value,
    input: input.value,
    used: used.value,
  });
  if (!priced.length) {
    notes.push("VidFare does not state a price for this combination. Nothing here is estimated.");
  } else if (priced.some((row) => row.quote_status === "unknown")) {
    notes.push("A row marked not stated by vendor is listed because the vendor page did not state audio or input. The dollars are that row's listed rate, not a guessed one.");
  }
  return {
    data: {
      model: model.slug,
      model_name: model.name,
      seconds: seconds.value,
      resolution,
      audio: audio.value,
      input: input.value,
      plan: planId,
      provider: platformFilter || providerForLink,
      used_percent: used.value,
      apply_deals: applyDeals,
      priced,
      not_priced: notPriced,
      missing: priced.length === 0,
      message: notes.filter(Boolean).join(" ") || undefined,
      citation: citation(catalog, catalog.pricesUrl, page, lastChecked(catalog)),
    },
  };
}

function priceRow(
  catalog: Catalog,
  row: PriceRow,
  judged: { status: string; usd_per_second?: number; detail: string },
  opts: { seconds: number; used: number; windowSeconds: number; deal?: PlanDeal; applyDeals: boolean; modelSlug: string },
) {
  const plans = plansOf(catalog);
  const base = {
    id: row.id ?? null,
    variant: row.variant ?? null,
    platform: row.platform ?? null,
    kind: row.kind ?? null,
    resolution: row.resolution ?? null,
    quote_status: judged.status,
    detail: judged.detail || undefined,
    vendor_source_url: row.source_url ?? null,
    checked: row.checked ?? null,
    page: row.plan
      ? calculatorQuery({ model: opts.modelSlug, plan: row.plan, provider: plans[row.plan]?.platform || row.platform, resolution: shownResolution(row), seconds: opts.seconds, used: opts.used })
      : modelPage(opts.modelSlug),
  };
  if (row.kind === "plan" && row.plan && plans[row.plan]) {
    const figures = planFigures(plans[row.plan], row, opts.used / 100, opts.applyDeals ? opts.deal : undefined, opts.windowSeconds);
    if (!figures.ok) {
      return { ...base, total_usd: null, missing: true, message: figures.message };
    }
    const perSecond = figures.usd_per_second;
    const flat = row.variation?.length_changes_price === false || Array.isArray(row.variation?.duration?.rate_by_length);
    const rate = Array.isArray(row.variation?.duration?.rate_by_length) && isNum(judged.usd_per_second)
      ? judged.usd_per_second
      : perSecond;
    const total = rate == null ? null : flat ? rate * opts.seconds : figures.usd_per_clip;
    return {
      ...base,
      ...figures.public,
      usd_per_second: rate,
      display: rate == null ? null : money(rate) + "/s",
      total_usd: total,
      total_display: total == null ? null : money(total),
      assumption: row.status === "estimate"
        ? "Estimate: assumes every credit you pay for is used."
        : "Assumes every credit you pay for is used.",
    };
  }
  const rate = judged.usd_per_second as number;
  const total = rate * opts.seconds;
  return {
    ...base,
    usd_per_second: rate,
    display: money(rate) + "/s",
    total_usd: total,
    total_display: money(total),
    basis: "Billed seconds times this row's dollars per second.",
    assumption: row.status === "estimate" ? (row.note ? `Estimate: ${row.note}` : "Estimate: the vendor marks this rate as approximate.") : undefined,
  };
}

function planFigures(plan: PlanRecord, row: PriceRow, usedFraction: number, deal: PlanDeal | undefined, windowSeconds: number) {
  const price = deal && deal.price != null ? deal.price : plan.usd_month;
  const bonus = deal?.bonus_credits ?? 0;
  const credits = (plan.credits_month ?? 0) + bonus;
  if (!isNum(price) || !credits || !isNum(row.credits_per_clip) || row.credits_per_clip <= 0 || !isNum(row.clip_seconds) || row.clip_seconds <= 0) {
    return { ok: false as const, message: "This plan row does not state the price, credits, or clip length, so no cost is estimated." };
  }
  const clips = clipCount(credits * usedFraction, row.credits_per_clip);
  const unit = price / credits;
  const usdPerClip = unit * row.credits_per_clip / usedFraction;
  const usdPerSecond = clips > 0 ? usdPerClip / row.clip_seconds : null;
  let unlimited = null;
  const hit = unlimitedHit(deal, row);
  if (hit && usdPerSecond != null && usdPerSecond > 0) {
    const normal = unit * row.credits_per_clip / row.clip_seconds;
    unlimited = {
      title: hit.title ?? null,
      breakeven_seconds: Math.round(price / normal),
      effective_usd_per_second: price / windowSeconds,
      effective_display: money(price / windowSeconds) + "/s",
      note: "Effective $/s for an unlimited window is the plan price divided by the seconds you make. It is not $0.",
    };
  }
  let blended = null;
  if (deal && deal.blended_price != null && clips > 0) {
    blended = (deal.blended_price / credits) * row.credits_per_clip / usedFraction / row.clip_seconds;
  }
  return {
    ok: true as const,
    usd_per_second: usdPerSecond,
    usd_per_clip: clips > 0 ? usdPerClip : null,
    public: {
      plan: row.plan,
      plan_name: plan.plan ?? row.plan_name ?? null,
      plan_price_usd: price,
      credits_month: credits,
      used_percent: Math.round(usedFraction * 100),
      usd_per_credit: unit,
      clips_per_month: clips,
      usd_per_clip: clips > 0 ? usdPerClip : null,
      usd_per_clip_display: clips > 0 ? money(usdPerClip) : null,
      blended_usd_per_second: blended,
      unlimited,
      deals_applied: Boolean(deal && (deal.price != null || deal.bonus_credits || deal.unlimited.length)),
      deal_notes: deal?.notes ?? [],
    },
  };
}

function cheapestOptions(args: Record<string, unknown>, catalog: Catalog): ToolResult {
  const seconds = readSeconds(args.seconds, true);
  if (!seconds.ok) return fail(catalog, seconds.message, sitePage("/"));
  const resolution = textOpt(args.resolution);
  if (!resolution) return fail(catalog, "resolution is required. VidFare does not rank a cheapest price without one.", sitePage("/"));
  const audio = normalizeAudio(args.audio);
  if (!audio.ok) return fail(catalog, audio.message, sitePage("/"));
  const input = readInput(args.input);
  if (!input.ok) return fail(catalog, input.message, sitePage("/"));
  const used = readUsed(args.used);
  if (!used.ok) return fail(catalog, used.message, sitePage("/"));
  const priced: Array<Record<string, unknown>> = [];
  const omitted: Array<Record<string, unknown>> = [];
  for (const [slug, model] of Object.entries(modelsOf(catalog))) {
    const result = estimateCost({
      model: slug,
      seconds: seconds.value,
      resolution,
      audio: audio.value,
      input: input.value,
      used: used.value,
      apply_deals: args.apply_deals === true,
    }, catalog);
    const rows = (result.data.priced as Array<Record<string, unknown>> | undefined) ?? [];
    const stated = rows.filter((row) => row.quote_status === "match" && typeof row.total_usd === "number");
    if (!stated.length) {
      omitted.push({
        model: slug,
        model_name: model.name || slug,
        message: "VidFare does not state a price for this model at that length and resolution.",
      });
      continue;
    }
    stated.sort((a, b) => (a.total_usd as number) - (b.total_usd as number));
    priced.push({ model: slug, model_name: model.name || slug, ...stated[0] });
  }
  priced.sort((a, b) => {
    const left = typeof a.total_usd === "number" ? a.total_usd : Infinity;
    const right = typeof b.total_usd === "number" ? b.total_usd : Infinity;
    return left - right;
  });
  const page = calculatorQuery({ seconds: seconds.value, resolution, audio: audio.value, input: input.value, used: used.value });
  return {
    data: {
      seconds: seconds.value,
      resolution,
      audio: audio.value,
      input: input.value,
      cheapest: priced[0] ?? null,
      by_model: priced,
      omitted,
      missing: priced.length === 0,
      message: priced.length
        ? "Cheapest is the lowest stated total. Rows the vendor did not state for this length or resolution are omitted."
        : "VidFare does not state a price for this length and resolution. Nothing is ranked.",
      citation: citation(catalog, catalog.pricesUrl, priced.length && priced[0].model ? modelPage(String(priced[0].model)) : page, lastChecked(catalog)),
    },
  };
}

function listDeals(args: Record<string, unknown>, catalog: Catalog): ToolResult {
  const wanted = textOpt(args.status) || "live";
  if (!["live", "upcoming", "ended", "all"].includes(wanted)) {
    return fail(catalog, "status must be live, upcoming, ended, or all.", sitePage("/deals/"), catalog.dealsUrl);
  }
  const groups = dealGroups(catalog);
  const selected = wanted === "all"
    ? [...groups.live, ...groups.upcoming, ...groups.ended]
    : wanted === "live" ? groups.live : wanted === "upcoming" ? groups.upcoming : groups.ended;
  const deals = selected.map((deal) => ({
    id: deal.id ?? null,
    vendor: deal.vendor ?? null,
    type: deal.type ?? null,
    title: deal.title ?? null,
    models: deal.models ?? [],
    plans: deal.plans ?? [],
    percent: deal.percent ?? null,
    bonus_credits: deal.bonus_credits ?? null,
    price_before: deal.price_before ?? null,
    price_after: deal.price_after ?? null,
    start: deal.start ?? null,
    end: deal.end ?? null,
    end_is_estimate: Boolean(deal.end_is_estimate),
    end_note: deal.end ? undefined : "No end date is stated.",
    status: deal.status ?? wanted,
    vendor_source_url: deal.source_url ?? null,
    source_quote: deal.source_quote ?? null,
    verified_date: deal.verified_date ?? null,
    notes: deal.notes ?? null,
    page: deal.id ? sitePage(`/deals/#${deal.id}`) : sitePage("/deals/"),
  }));
  const checked = groups.updated || selected.map((deal) => deal.verified_date).filter(Boolean).sort().at(-1) || "";
  return {
    data: {
      status: wanted,
      count: deals.length,
      missing: deals.length === 0,
      message: deals.length ? undefined : "VidFare has no deals in that group.",
      deals,
      citation: citation(catalog, catalog.dealsUrl, sitePage("/deals/"), checked),
    },
  };
}
