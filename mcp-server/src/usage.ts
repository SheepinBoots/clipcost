/**
 * Anonymous tool-request counts.
 *
 * A point is the tool name and success or error. The engine adds the time.
 * Nothing from the caller is stored: no arguments, prompt, address, or header.
 */

export const KNOWN_TOOLS = [
  "list_models",
  "get_model_prices",
  "estimate_cost",
  "cheapest_options",
  "list_deals",
] as const;

const KNOWN = new Set<string>(KNOWN_TOOLS);

export type UsageOutcome = "success" | "error";

export interface UsageDataset {
  writeDataPoint(event: { blobs?: string[]; doubles?: number[] }): void;
}

export function skipUsage(request: Request): boolean {
  if (request.headers.get("x-vidfare-test") === "1") return true;
  if (request.method !== "POST") return true;
  let host = "";
  try {
    host = new URL(request.url).hostname.toLowerCase();
  } catch {
    return true;
  }
  return host === "localhost" || host === "127.0.0.1" || host === "::1" || host === "[::1]" || host === "0.0.0.0";
}

export function toolCalls(body: unknown): string[] {
  const messages = Array.isArray(body) ? body : [body];
  const names: string[] = [];
  for (const message of messages) {
    if (!message || typeof message !== "object") continue;
    if ((message as { method?: unknown }).method !== "tools/call") continue;
    const params = (message as { params?: { name?: unknown } }).params;
    const name = params && typeof params.name === "string" ? params.name : "";
    names.push(KNOWN.has(name) ? name : "unknown");
  }
  return names;
}

export function toolCallsFromText(text: string): string[] {
  if (!text.trim()) return [];
  try {
    return toolCalls(JSON.parse(text));
  } catch {
    return [];
  }
}

export function outcomesFrom(body: unknown, count: number): UsageOutcome[] {
  const messages = Array.isArray(body) ? body : [body];
  const outcomes: UsageOutcome[] = [];
  for (const message of messages) {
    if (!message || typeof message !== "object") continue;
    const record = message as { error?: unknown; result?: { isError?: unknown } };
    if (!("result" in record) && !("error" in record)) continue;
    if (record.error) {
      outcomes.push("error");
      continue;
    }
    if (record.result && typeof record.result === "object" && record.result.isError === true) {
      outcomes.push("error");
      continue;
    }
    outcomes.push("success");
  }
  if (outcomes.length !== count) return Array.from({ length: count }, () => "error");
  return outcomes;
}

export function outcomesFromText(text: string, contentType: string, count: number): UsageOutcome[] {
  try {
    let body: unknown;
    if (contentType.includes("text/event-stream")) {
      const parsed = text.split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trim())
        .filter(Boolean)
        .map((line) => JSON.parse(line) as unknown);
      body = parsed.length === 1 ? parsed[0] : parsed;
    } else {
      body = JSON.parse(text);
    }
    return outcomesFrom(body, count);
  } catch {
    return Array.from({ length: count }, () => "error");
  }
}

/** One point per tool call. A throw or a missing binding is ignored. */
export function writeUsage(dataset: UsageDataset | undefined, tool: string, outcome: UsageOutcome): void {
  try {
    dataset?.writeDataPoint({
      blobs: [tool, outcome],
      doubles: [1],
    });
  } catch {
    // The count is optional. The tool response is already decided.
  }
}

export async function tallyResponse(
  response: Response,
  tools: string[],
  dataset: UsageDataset | undefined,
): Promise<void> {
  try {
    if (!response.ok) {
      for (const tool of tools) writeUsage(dataset, tool, "error");
      return;
    }
    const text = await response.text();
    const outcomes = outcomesFromText(text, response.headers.get("content-type") || "", tools.length);
    tools.forEach((tool, index) => writeUsage(dataset, tool, outcomes[index] ?? "error"));
  } catch {
    // Reading the copy failed. Do not write a guess, and do not surface this.
  }
}
