import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { UTM, withUtm } from "../src/links.ts";
import { runTool, type Catalog } from "../src/tools.ts";

const here = dirname(fileURLToPath(import.meta.url));
const prices = JSON.parse(readFileSync(join(here, "fixtures", "prices.json"), "utf8"));
const deals = JSON.parse(readFileSync(join(here, "fixtures", "deals.json"), "utf8"));

function catalog(over: Partial<Catalog> = {}): Catalog {
  return {
    prices,
    deals,
    today: "2026-11-05",
    fromCache: false,
    pricesUrl: "https://vidfare.com/data/prices.json",
    dealsUrl: "https://vidfare.com/deals.json",
    ...over,
  };
}

function vidfareUrls(value: unknown, found: string[] = []): string[] {
  if (typeof value === "string" && /^https?:\/\/(?:www\.)?vidfare\.com\//i.test(value)) found.push(value);
  else if (Array.isArray(value)) value.forEach((item) => vidfareUrls(item, found));
  else if (value && typeof value === "object") Object.values(value).forEach((item) => vidfareUrls(item, found));
  return found;
}

test("list_models returns the nine catalog models and a citation", () => {
  const result = runTool("list_models", {}, catalog());
  const models = result.data.models as Array<{ name: string; slug: string; cheapest_usd_per_second: number }>;
  assert.equal(models.length, 9);
  assert.deepEqual(models.map((model) => model.name), [
    "Wan 3.0 Prime",
    "Wan 3.0",
    "Kling 3.0",
    "Seedance 2.5",
    "Veo 3.1",
    "Gemini Omni Flash 1.1",
    "MiniMax Hailuo / H3",
    "Runway Gen-4.x",
    "Grok Imagine Video 1.5",
  ]);
  assert.ok(models.every((model) => typeof model.cheapest_usd_per_second === "number"));
  const citation = result.data.citation as { source_url: string; last_checked: string; page: string };
  assert.equal(citation.last_checked, "2026-11-05");
  assert.match(citation.page, /\/models\//);
  for (const url of vidfareUrls(result.data)) {
    const parsed = new URL(url);
    for (const [key, value] of Object.entries(UTM)) assert.equal(parsed.searchParams.get(key), value);
  }
});

test("get_model_prices filters provider and resolution and does not invent a miss", () => {
  const hit = runTool("get_model_prices", { model: "Kling 3.0", provider: "fal", resolution: "not listed" }, catalog());
  const prices = hit.data.prices as Array<{ platform: string; resolution: string; usd_per_second: number; vendor_source_url: string }>;
  assert.ok(prices.length >= 1);
  assert.ok(prices.every((row) => row.platform === "fal"));
  assert.ok(prices.every((row) => row.resolution === "Pro tier"));
  assert.ok(prices.every((row) => row.vendor_source_url.startsWith("https://fal.ai/")));
  assert.ok(!rowHasUtm(prices[0].vendor_source_url));
  const miss = runTool("get_model_prices", { model: "not-a-model" }, catalog());
  assert.equal(miss.isError, true);
  assert.equal(miss.data.missing, true);
  assert.equal(JSON.stringify(miss.data).includes("usd_per_second"), false);
  const empty = runTool("get_model_prices", { model: "kling-3-0", resolution: "12k" }, catalog());
  assert.equal(empty.data.missing, true);
  assert.deepEqual(empty.data.prices, []);
});

test("estimate_cost keeps calculator query params and adds the campaign", () => {
  const result = runTool("estimate_cost", {
    model: "wan-3-0",
    seconds: 10,
    resolution: "720p",
    provider: "fal",
    audio: "off",
  }, catalog());
  const page = (result.data.citation as { page: string }).page;
  const parsed = new URL(page);
  assert.equal(parsed.searchParams.get("model"), "wan-3-0");
  assert.equal(parsed.searchParams.get("seconds"), "10");
  assert.equal(parsed.searchParams.get("resolution"), "720p");
  assert.equal(parsed.searchParams.get("audio"), "without");
  for (const [key, value] of Object.entries(UTM)) assert.equal(parsed.searchParams.get(key), value);
  const priced = result.data.priced as Array<{ total_usd: number; usd_per_second: number; platform: string }>;
  const fal = priced.find((row) => row.platform === "fal");
  if (!fal) throw new Error("missing fal row");
  assert.equal(fal.usd_per_second, 0.1);
  assert.equal(fal.total_usd, 1);
});

test("withUtm does not drop or duplicate an existing campaign", () => {
  const once = withUtm("https://vidfare.com/calculator/?model=kling-3-0&seconds=10");
  const twice = withUtm(once);
  assert.equal(once, twice);
  const parsed = new URL(twice);
  assert.equal(parsed.searchParams.get("model"), "kling-3-0");
  assert.equal(parsed.searchParams.get("seconds"), "10");
  assert.equal(parsed.searchParams.get("utm_source"), "mcp");
  assert.equal(withUtm("https://fal.ai/pricing"), "https://fal.ai/pricing");
  const hash = new URL(withUtm("https://vidfare.com/deals/#hf-api-wan-60"));
  assert.equal(hash.hash, "#hf-api-wan-60");
  assert.equal(hash.searchParams.get("utm_campaign"), "vidfare_mcp");
});

test("a 10 second request does not price a clip the page only states at 5 seconds", () => {
  const result = runTool("estimate_cost", {
    model: "wan-3-0",
    seconds: 10,
    resolution: "480p",
    plan: "hf-starter",
  }, catalog());
  assert.equal(result.data.missing, true);
  assert.deepEqual(result.data.priced, []);
  const held = JSON.stringify(result.data);
  assert.equal(held.includes("total_usd"), false);
});

test("starter plan 5 second cost matches plan price divided by credits", () => {
  const result = runTool("estimate_cost", {
    model: "wan-3-0",
    seconds: 5,
    resolution: "480p",
    plan: "hf-starter",
    used: 100,
  }, catalog());
  const row = (result.data.priced as Array<{ usd_per_second: number; total_usd: number; clips_per_month: number }>)[0];
  const rate = (19 / 270) * 5 / 5;
  const clip = (19 / 270) * 5;
  assert.ok(Math.abs(row.usd_per_second - rate) < 1e-12);
  assert.ok(Math.abs(row.total_usd - clip) < 1e-12);
  assert.equal(row.clips_per_month, 54);
});

test("using fewer credits raises the clip cost and the share link keeps used", () => {
  const result = runTool("estimate_cost", {
    model: "wan-3-0",
    seconds: 5,
    resolution: "480p",
    plan: "hf-starter",
    used: 50,
  }, catalog());
  const row = (result.data.priced as Array<{ total_usd: number }>)[0];
  const full = (19 / 270) * 5;
  assert.ok(Math.abs(row.total_usd - full / 0.5) < 1e-12);
  const page = new URL((result.data.citation as { page: string }).page);
  assert.equal(page.searchParams.get("used"), "50");
  assert.equal(page.searchParams.get("plan"), "hf-starter");
});

test("cheapest_options omits a model with no stated price at that length", () => {
  const result = runTool("cheapest_options", { seconds: 10, resolution: "720p" }, catalog());
  const names = (result.data.by_model as Array<{ model_name: string }>).map((row) => row.model_name);
  assert.ok(names.length >= 1);
  const omitted = result.data.omitted as Array<{ message: string }>;
  assert.ok(omitted.length >= 1);
  assert.match(omitted[0].message, /does not state/);
  const cheapest = result.data.cheapest as { total_usd: number };
  assert.equal(typeof cheapest.total_usd, "number");
});

test("list_deals does not invent an end date", () => {
  const result = runTool("list_deals", { status: "live" }, catalog());
  const deals = result.data.deals as Array<{ end: string | null; end_note?: string; page: string; vendor_source_url: string }>;
  assert.ok(deals.length >= 1);
  for (const deal of deals) {
    if (!deal.end) assert.equal(deal.end_note, "No end date is stated.");
    assert.match(deal.page, /utm_source=mcp/);
    if (deal.vendor_source_url && !deal.vendor_source_url.includes("vidfare.com")) {
      assert.equal(rowHasUtm(deal.vendor_source_url), false);
    }
  }
  const citation = result.data.citation as { source_url: string; page: string };
  assert.match(citation.source_url, /vidfare\.com\/deals\.json/);
  assert.match(citation.page, /\/deals\//);
});

test("the published deals.json shape is read as live, upcoming, and ended", () => {
  const result = runTool("list_deals", { status: "all" }, catalog({
    deals: {
      updated: "2026-11-05",
      deals: [{ id: "live-one", status: "live", title: "A live sale", vendor: "fal", source_url: "https://fal.ai/live", verified_date: "2026-11-01", end: null }],
      upcoming: [{ id: "soon", status: "upcoming", title: "Starts later", vendor: "Krea", source_url: "https://www.krea.ai/pricing", start: "2026-12-01", end: "2026-12-02" }],
      archive: [{ id: "old", status: "ended", title: "Ended sale", vendor: "fal", source_url: "https://fal.ai/old", end: "2026-10-01" }],
      history: [],
    },
  }));
  const ids = (result.data.deals as Array<{ id: string }>).map((deal) => deal.id);
  assert.deepEqual(ids, ["live-one", "soon", "old"]);
});

test("an empty catalog says the data is missing", () => {
  const empty = catalog({ prices: { models: {}, plans: {}, rows: [] }, deals: { deals: [] } });
  const result = runTool("estimate_cost", { model: "wan-3-0", seconds: 10 }, empty);
  assert.equal(result.data.missing, true);
  assert.match(String(result.data.message), /not in the VidFare catalog/);
});

function rowHasUtm(url: string): boolean {
  return new URL(url).searchParams.has("utm_source");
}
