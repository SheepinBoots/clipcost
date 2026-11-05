/**
 * "Apply today's deals" for the credit calculator.
 * Same rules as deals.calculator_map in scripts/deals.py.
 */

export type PlanRecord = {
  platform?: string;
  plan?: string;
  usd_month?: number;
  credits_month?: number;
  billing?: string;
  credits_note?: string;
  checked?: string;
  source_url?: string;
};

export type Deal = {
  id?: string;
  vendor?: string;
  type?: string;
  title?: string;
  models?: string[];
  plans?: string[];
  variants?: string[];
  full_plan_id?: string | null;
  deal_plan_id?: string | null;
  conditions?: Record<string, unknown>;
  percent?: number | null;
  bonus_credits?: number | null;
  price_before?: number | null;
  price_after?: number | null;
  price_pairs?: Array<Record<string, unknown>> | null;
  start?: string | null;
  end?: string | null;
  end_is_estimate?: boolean;
  status?: string;
  math?: string | null;
  source_url?: string;
  source_quote?: string;
  verified_date?: string;
  notes?: string;
  link_url?: string;
};

export type UnlimitedOffer = {
  id: string | null;
  title: string | null;
  models: string[];
  variants: string[];
  max_resolution: unknown;
  days: unknown;
  web_only: boolean;
  end: string | null;
  end_is_estimate: boolean;
};

export type PlanDeal = {
  price: number | null;
  bonus_credits: number;
  blended_price: number | null;
  notes: string[];
  unlimited: UnlimitedOffer[];
};

const PLATFORMS: Record<string, string[]> = {
  Higgsfield: ["Higgsfield"],
  "Higgsfield API": ["Higgsfield API"],
  Krea: ["Krea"],
  Magnific: ["Magnific"],
  Runway: ["Runway", "Runway API"],
  fal: ["fal"],
};

export function vendorPlatforms(vendor: string | undefined): string[] {
  if (!vendor) return [];
  return PLATFORMS[vendor] ?? [vendor];
}

export function conditions(deal: Deal): Record<string, unknown> {
  const base: Record<string, unknown> = {
    new_users_only: false,
    annual_only: false,
    first_months: null,
    max_resolution: null,
    web_only: false,
    code: null,
    standing: false,
  };
  return Object.assign(base, deal.conditions ?? {});
}

export function effectiveStatus(deal: Deal, today: string): string {
  const status = deal.status || "unconfirmed";
  if (status === "live" && deal.end && deal.end < today) return "ended";
  if (status === "live" && deal.start && deal.start > today) return "upcoming";
  return status;
}

export function isCurrent(deal: Deal, today: string): boolean {
  return effectiveStatus(deal, today) === "live";
}

function pairs(deal: Deal): Array<Record<string, unknown>> {
  if (Array.isArray(deal.price_pairs) && deal.price_pairs.length) return deal.price_pairs;
  if (["price_before", "price_after", "full_plan_id", "deal_plan_id"].some((key) => deal[key as keyof Deal] != null)) {
    return [{
      plan: (deal.plans || [null])[0],
      full_plan_id: deal.full_plan_id,
      deal_plan_id: deal.deal_plan_id,
      price_before: deal.price_before,
      price_after: deal.price_after,
      percent: deal.percent,
    }];
  }
  return [];
}

export function planNameMatches(planName: string | undefined, wanted: string[]): boolean {
  const name = planName || "";
  return wanted.some((label) => name === label || name.startsWith(label + " ") || name.startsWith(label + "("));
}

/** Python round(value, 2), half to even. */
export function pythonRound2(value: number): number {
  const sign = value < 0 ? -1 : 1;
  const scaled = Math.abs(value) * 100;
  const floor = Math.floor(scaled);
  const diff = scaled - floor;
  let picked = floor;
  if (diff > 0.5 + 1e-10) picked = floor + 1;
  else if (Math.abs(diff - 0.5) <= 1e-10) picked = floor % 2 === 0 ? floor : floor + 1;
  return (sign * picked) / 100;
}

function blendedPrice(priceAfter: number, priceBefore: number, firstMonths: number): number {
  const n = Math.trunc(firstMonths);
  return (n * priceAfter + (12 - n) * priceBefore) / 12;
}

export function calculatorMap(deals: Deal[], plans: Record<string, PlanRecord>, today: string): Record<string, PlanDeal> {
  const out: Record<string, PlanDeal> = {};
  const live = deals.filter((deal) => isCurrent(deal, today));
  for (const [pid, plan] of Object.entries(plans)) {
    const entry: PlanDeal = { price: null, bonus_credits: 0, blended_price: null, notes: [], unlimited: [] };
    for (const deal of live) {
      const math = deal.math;
      const cond = conditions(deal);
      if ((deal.type === "plan_sale" || deal.type === "promo_code") && math !== "none") {
        for (const pair of pairs(deal)) {
          if (pair.full_plan_id === pid && typeof pair.price_after === "number") {
            entry.price = pair.price_after;
            let note = `${deal.title}: $${formatG(pair.price_after)}/mo instead of $${formatG(pair.price_before as number)}/mo`;
            const months = cond.first_months;
            if (typeof months === "number" && typeof pair.price_before === "number") {
              const blended = blendedPrice(pair.price_after, pair.price_before, months);
              entry.blended_price = pythonRound2(blended);
              note += `. First ${months} months, then $${formatG(pair.price_before)}/mo. 12-month blended $${blended.toFixed(2)}/mo.`;
            }
            if (cond.code) note += ` Code ${cond.code}.`;
            entry.notes.push(note);
          } else if (pair.deal_plan_id === pid) {
            entry.notes.push(`${deal.title} is already the price of this plan.`);
          }
        }
      }
      if (deal.type === "bonus_credits" && deal.bonus_credits && math !== "none") {
        if (vendorPlatforms(deal.vendor).includes(plan.platform || "") && planNameMatches(plan.plan, deal.plans || [])) {
          entry.bonus_credits += deal.bonus_credits;
          entry.notes.push(`${deal.title}: +${formatG(deal.bonus_credits)} credits.`);
        }
      }
      if (deal.type === "unlimited_window" && math !== "none") {
        if (!vendorPlatforms(deal.vendor).includes(plan.platform || "")) continue;
        const wanted = deal.plans || [];
        if (wanted.length && !planNameMatches(plan.plan, wanted)) continue;
        if (!wanted.length && !(deal.models || []).length) continue;
        entry.unlimited.push({
          id: deal.id ?? null,
          title: deal.title ?? null,
          models: deal.models || [],
          variants: deal.variants || [],
          max_resolution: cond.max_resolution ?? null,
          days: cond.signup_window_days ?? null,
          web_only: Boolean(cond.web_only),
          end: deal.end ?? null,
          end_is_estimate: Boolean(deal.end_is_estimate),
        });
      }
    }
    if (entry.price != null || entry.bonus_credits || entry.unlimited.length || entry.notes.length) out[pid] = entry;
  }
  return out;
}

function formatG(value: number): string {
  if (Number.isInteger(value)) return String(value);
  return String(value);
}

export function unlimitedHit(map: PlanDeal | null | undefined, row: { model?: string; variant?: string; resolution?: string }) {
  if (!map?.unlimited?.length) return null;
  return map.unlimited.find((offer) => {
    if (offer.models.length && !offer.models.includes(row.model || "")) return false;
    if (offer.variants.length && !offer.variants.includes(row.variant || "")) return false;
    if (offer.max_resolution && String(row.resolution).toLowerCase() !== String(offer.max_resolution).toLowerCase()) return false;
    if (!offer.models.length && !offer.variants.length) return false;
    return true;
  }) ?? null;
}
