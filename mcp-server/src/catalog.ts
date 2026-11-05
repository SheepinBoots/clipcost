import { DEALS_URL, PRICES_URL, type Catalog, type DealsFile, type PricesFile } from "./tools.ts";

export const CACHE_SECONDS = 300;

type CacheLike = {
  match(request: Request): Promise<Response | undefined>;
  put(request: Request, response: Response): Promise<void>;
};

const memory = new Map<string, { at: number; body: unknown }>();

export class CatalogError extends Error {
  url: string;
  constructor(url: string, message: string) {
    super(message);
    this.url = url;
  }
}

export async function loadLiveCatalog(opts: {
  fetchImpl?: typeof fetch;
  cache?: CacheLike;
  now?: number;
  ttlMs?: number;
  today?: string;
} = {}): Promise<Catalog> {
  const ttl = opts.ttlMs ?? CACHE_SECONDS * 1000;
  const now = opts.now ?? Date.now();
  const fetchImpl = opts.fetchImpl ?? fetch;
  const [prices, pricesCached] = await getJson(PRICES_URL, fetchImpl, opts.cache, now, ttl);
  const [deals, dealsCached] = await getJson(DEALS_URL, fetchImpl, opts.cache, now, ttl);
  return {
    prices: prices as PricesFile,
    deals: deals as DealsFile,
    today: opts.today ?? new Date(now).toISOString().slice(0, 10),
    fromCache: pricesCached || dealsCached,
    pricesUrl: PRICES_URL,
    dealsUrl: DEALS_URL,
  };
}

async function getJson(
  url: string,
  fetchImpl: typeof fetch,
  cache: CacheLike | undefined,
  now: number,
  ttl: number,
): Promise<[unknown, boolean]> {
  const hit = memory.get(url);
  if (hit && now - hit.at < ttl) return [hit.body, true];
  const request = new Request(url, { method: "GET" });
  if (cache) {
    const cached = await cache.match(request);
    if (cached) {
      try {
        const body = await cached.json();
        memory.set(url, { at: now, body });
        return [body, true];
      } catch {
        // A cached body that is not JSON is ignored. The live file is fetched next.
      }
    }
  }
  let response: Response;
  try {
    response = await fetchImpl(url, { headers: { accept: "application/json" } });
  } catch (err) {
    throw new CatalogError(url, `VidFare data could not be loaded from ${url}. No price is estimated. ${err instanceof Error ? err.message : ""}`.trim());
  }
  if (!response.ok) {
    throw new CatalogError(url, `VidFare data could not be loaded from ${url} (HTTP ${response.status}). No price is estimated.`);
  }
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    throw new CatalogError(url, `VidFare data at ${url} was not JSON. No price is estimated.`);
  }
  if (!body || typeof body !== "object") {
    throw new CatalogError(url, `VidFare data at ${url} did not include a JSON object. No price is estimated.`);
  }
  memory.set(url, { at: now, body });
  if (cache) {
    const stored = new Response(JSON.stringify(body), {
      headers: { "content-type": "application/json", "cache-control": `public, max-age=${Math.floor(ttl / 1000)}` },
    });
    await cache.put(request, stored);
  }
  return [body, false];
}

export function clearCatalogCache(): void {
  memory.clear();
}
