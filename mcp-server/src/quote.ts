/**
 * Price one catalog row the way the site calculator does.
 * Status rules match scripts/variations.py quote() and the calculator's quoteRow.
 * Plan dollar amounts match the calculator script in scripts/build_site.py.
 */

export const UNLISTED_RESOLUTIONS = new Set(["", "—", "-", "–", "Pro tier", "Pro", "Standard"]);

export type QuoteStatus = "match" | "unknown" | "not_offered" | "not_stated";

export type Quote = {
  status: QuoteStatus;
  usd_per_second?: number;
  detail: string;
};

type Duration = {
  min_seconds?: unknown;
  max_seconds?: unknown;
  priced_seconds?: unknown;
  rate_by_length?: unknown;
};

type Variation = {
  audio?: unknown;
  input?: unknown;
  duration?: Duration;
  length_changes_price?: unknown;
};

export type PriceRow = {
  id?: string;
  model?: string;
  variant?: string;
  platform?: string;
  kind?: string;
  plan?: string;
  plan_name?: string;
  resolution?: string;
  usd_per_second?: number;
  status?: string;
  promo_until?: string | null;
  discontinued_on?: string | null;
  source_url?: string;
  checked?: string;
  note?: string;
  clip_seconds?: number;
  credits_per_clip?: number;
  variation?: Variation;
};

export function isNum(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

export function resolutionMatches(row: PriceRow, resolution: string): boolean {
  const raw = String(row.resolution ?? "").trim();
  if (resolution.trim().toLowerCase() === "not listed") return UNLISTED_RESOLUTIONS.has(raw);
  return raw.toLowerCase().includes(resolution.toLowerCase());
}

export function quote(
  row: PriceRow,
  opts: { seconds?: number | null; audio?: string | null; inputType?: string | null; resolution?: string | null } = {},
): Quote {
  const variation = row.variation ?? {};
  const duration = variation.duration ?? {};
  const resolution = opts.resolution ?? null;
  if (resolution && !resolutionMatches(row, resolution)) {
    return { status: "not_offered", detail: `Resolution ${resolution} is not this row.` };
  }
  let unknown = false;
  if (opts.audio) {
    const have = typeof variation.audio === "string" && variation.audio ? variation.audio : "not stated";
    if (have === "not stated") unknown = true;
    else if (have !== opts.audio) return { status: "not_offered", detail: "This row is the other audio price." };
  }
  if (opts.inputType) {
    const have = variation.input;
    if (have === "not stated" || !have) unknown = true;
    else if (!Array.isArray(have) || !have.includes(opts.inputType)) {
      return { status: "not_offered", detail: "This row is a different input type." };
    }
  }
  let usd = row.usd_per_second;
  let detail = "";
  if (opts.seconds != null) {
    const lo = duration.min_seconds;
    const hi = duration.max_seconds;
    if ((isNum(lo) && opts.seconds < lo) || (isNum(hi) && opts.seconds > hi)) {
      return { status: "not_offered", detail: "That length is outside the range on the page." };
    }
    const rates = duration.rate_by_length;
    if (Array.isArray(rates)) {
      const tier = rates.find((item) => {
        const seconds = (item as { seconds?: unknown }).seconds;
        return Array.isArray(seconds) && seconds.map((value) => Math.trunc(Number(value))).includes(Math.trunc(opts.seconds as number));
      }) as { usd_per_second?: number; label?: string } | undefined;
      if (!tier || !isNum(tier.usd_per_second)) {
        return { status: "not_stated", detail: "The page gives a per-second rate for another length, not this one." };
      }
      usd = tier.usd_per_second;
      detail = tier.label || "";
    } else if (variation.length_changes_price === false) {
      detail = "";
    } else {
      const priced = duration.priced_seconds;
      if (isNum(priced) && Math.trunc(opts.seconds) === Math.trunc(priced)) {
        detail = `${formatG(priced)}s`;
      } else if (isNum(priced)) {
        return { status: "not_stated", detail: `The page prices this clip at ${formatG(priced)}s, not ${Math.trunc(opts.seconds)}s.` };
      } else {
        return { status: "not_stated", detail: "The page does not state a rate for that length." };
      }
    }
  }
  if (!isNum(usd)) return { status: "not_stated", detail: "The page does not state a dollars-per-second rate." };
  if (unknown) return { status: "unknown", usd_per_second: usd, detail: "not stated by vendor" };
  return { status: "match", usd_per_second: usd, detail };
}

function formatG(value: number): string {
  if (Number.isInteger(value)) return String(value);
  return String(value);
}

/** Math.round for the positive counts the calculator uses. */
export function clipCount(credits: number, per: number): number {
  const raw = credits / per;
  const nearest = Math.round(raw);
  return Math.abs(raw - nearest) < 0.005 ? nearest : Math.floor(raw);
}

/** Same display as the price tables: up to 5 decimals, half up, at least 2. */
export function money(value: number): string {
  const n = Math.round(Number(value) * 100000);
  const neg = n < 0;
  const abs = Math.abs(n);
  const whole = Math.floor(abs / 100000);
  let digits = String(abs % 100000).padStart(5, "0").replace(/0+$/, "");
  if (digits.length < 2) digits = String(abs % 100000).padStart(5, "0").slice(0, 2);
  return `${neg ? "-" : ""}$${whole}.${digits}`;
}

export function currentRow(row: PriceRow, today: string): boolean {
  if (row.status === "discontinued") return false;
  if (row.discontinued_on && row.discontinued_on < today) return false;
  if (row.promo_until && row.promo_until < today) return false;
  return true;
}
