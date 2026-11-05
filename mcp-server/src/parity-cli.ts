/**
 * stdin: { today, pricesPath, dealsPath, cases, costs }
 * stdout: { quotes, map, costs }
 * Used by scripts/test_mcp_parity.py.
 */
import { readFileSync } from "node:fs";
import { calculatorMap } from "./deals.ts";
import { quote, type PriceRow } from "./quote.ts";
import { runTool, type Catalog, type DealsFile, type PricesFile } from "./tools.ts";

type Input = {
  today: string;
  pricesPath: string;
  dealsPath: string;
  cases: Array<{ id: string; seconds?: number | null; audio?: string | null; input?: string | null; resolution?: string | null }>;
  costs?: Array<Record<string, unknown>>;
};

const input = JSON.parse(readFileSync(0, "utf8")) as Input;
const prices = JSON.parse(readFileSync(input.pricesPath, "utf8")) as PricesFile;
const deals = JSON.parse(readFileSync(input.dealsPath, "utf8")) as DealsFile;
const rows = new Map((prices.rows ?? []).map((row) => [row.id, row as PriceRow]));
const quotes = input.cases.map((item) => {
  const row = rows.get(item.id);
  if (!row) return { id: item.id, status: "missing" };
  const result = quote(row, {
    seconds: item.seconds ?? null,
    audio: item.audio ?? null,
    inputType: item.input ?? null,
    resolution: item.resolution ?? null,
  });
  return { id: item.id, ...result };
});
const map = calculatorMap(deals.deals ?? [], prices.plans ?? {}, input.today);
const catalog: Catalog = {
  prices,
  deals,
  today: input.today,
  fromCache: false,
  pricesUrl: "https://vidfare.com/data/prices.json",
  dealsUrl: "https://vidfare.com/deals.json",
};
const costs = (input.costs ?? []).map((args) => runTool("estimate_cost", args, catalog).data);
process.stdout.write(JSON.stringify({ quotes, map, costs }));
