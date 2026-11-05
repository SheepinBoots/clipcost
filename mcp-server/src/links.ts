/** VidFare links returned by tools carry these campaign parameters. */
export const UTM = {
  utm_source: "mcp",
  utm_medium: "tool",
  utm_campaign: "vidfare_mcp",
} as const;

const HOSTS = new Set(["vidfare.com", "www.vidfare.com"]);

export function withUtm(url: string): string {
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return url;
  }
  if (!HOSTS.has(parsed.hostname.toLowerCase())) return url;
  for (const [key, value] of Object.entries(UTM)) {
    if (!parsed.searchParams.has(key)) parsed.searchParams.set(key, value);
  }
  return parsed.toString();
}

export function stampVidfareLinks<T>(value: T): T {
  return rewrite(value) as T;
}

function rewrite(value: unknown): unknown {
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (trimmed !== value) return value;
    if (!/^https?:\/\//i.test(trimmed)) return value;
    return withUtm(trimmed);
  }
  if (Array.isArray(value)) return value.map(rewrite);
  if (value && typeof value === "object") {
    const out: Record<string, unknown> = {};
    for (const [key, item] of Object.entries(value)) out[key] = rewrite(item);
    return out;
  }
  return value;
}
