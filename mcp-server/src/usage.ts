/**
 * Anonymous request counts for Workers Analytics Engine.
 *
 * A point is a coarse bucket: JSON-RPC method, tool name, client class,
 * argument names, HTTP method, and status class. The engine adds the time.
 * The sampling index is the method bucket. It is not a person or address.
 *
 * Never stored: IP addresses, the raw user agent, header values, request or
 * response bodies, argument values, session ids, account names, or the raw
 * tool name. An alias is stored as the canonical tool plus an "alias" marker.
 */

import { resolveToolName, type KnownTool } from "./tool-names.ts";

export { KNOWN_TOOLS } from "./tool-names.ts";

/** Above this many JSON-RPC messages, one point with method `batch` is written. */
export const BATCH_LOG_LIMIT = 20;

const CLIENT_MAX = 40;
const UA_SCAN_MAX = 512;
const LAYOUT = "v2";

const HTTP_METHODS = new Set(["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]);
const ARG_NAME = /^[a-z][a-z0-9_]{0,31}$/;

export interface UsageDataPoint {
  indexes?: string[];
  blobs?: string[];
  doubles?: number[];
}

export interface UsageDataset {
  writeDataPoint(event: UsageDataPoint): void;
}

export interface UsageInput {
  httpMethod: string;
  status: number;
  userAgent: string | null;
  bodyText: string;
}

type MessageLog = {
  method: string;
  tool: string;
  args: string;
  client: string | null;
  alias: boolean;
};

const PROBE_KEYS: ReadonlyArray<readonly [string, string]> = [
  ["mcpbeat", "mcpbeat"],
  ["agentrank", "agentrank"],
  ["alalanet", "alalanet"],
  ["everymcp", "everymcp"],
  ["mcptry", "mcptry"],
  ["mcpwatch", "mcpwatch"],
  ["glama", "glama"],
  ["smithery", "smithery"],
  ["pulsemcp", "pulsemcp"],
  ["mcp-so", "mcpso"],
  ["mcpso", "mcpso"],
  ["histor", "histor"],
  ["uptimerobot", "uptimerobot"],
  ["pingdom", "pingdom"],
  ["kube-probe", "kube-probe"],
  ["googlehc", "googlehc"],
  ["checkly", "checkly"],
  ["statuscake", "statuscake"],
  ["betterstack", "betterstack"],
  ["better-uptime", "betterstack"],
];

const AI_KEYS: ReadonlyArray<readonly [string, string]> = [
  ["chatgpt", "chatgpt"],
  ["openai", "openai"],
  ["anthropic", "claude"],
  ["claude", "claude"],
  ["cursor", "cursor"],
  ["github-copilot", "copilot"],
  ["copilot", "copilot"],
  ["perplexity", "perplexity"],
  ["windsurf", "windsurf"],
  ["gemini", "gemini"],
  ["deepseek", "deepseek"],
  ["mistral", "mistral"],
  ["grok", "grok"],
  ["xai", "grok"],
  ["cline", "cline"],
  ["replit", "replit"],
  ["devin", "devin"],
  ["aider", "aider"],
  ["codex", "codex"],
];

const GENERIC_KEYS: ReadonlyArray<readonly [string, string]> = [
  ["python-httpx", "python-httpx"],
  ["python-requests", "python-requests"],
  ["go-http-client", "go-http-client"],
  ["coda-agent-runtime", "coda-agent-runtime"],
  ["undici", "undici"],
  ["talaria", "talaria"],
  ["node-fetch", "node"],
  ["node", "node"],
  ["curl", "curl"],
];

const UA_RULES: ReadonlyArray<{ re: RegExp; label: string; probe: boolean }> = [
  { re: /mcpbeat/i, label: "probe:mcpbeat", probe: true },
  { re: /agentrank/i, label: "probe:agentrank", probe: true },
  { re: /alalanet/i, label: "probe:alalanet", probe: true },
  { re: /everymcp/i, label: "probe:everymcp", probe: true },
  { re: /mcptry/i, label: "probe:mcptry", probe: true },
  { re: /mcpwatch/i, label: "probe:mcpwatch", probe: true },
  { re: /glama/i, label: "probe:glama", probe: true },
  { re: /smithery/i, label: "probe:smithery", probe: true },
  { re: /pulsemcp/i, label: "probe:pulsemcp", probe: true },
  { re: /mcp\.so/i, label: "probe:mcpso", probe: true },
  { re: /(?:^|[^a-z0-9])histor(?:[^a-z0-9]|$)/i, label: "probe:histor", probe: true },
  { re: /uptimerobot/i, label: "probe:uptimerobot", probe: true },
  { re: /pingdom/i, label: "probe:pingdom", probe: true },
  { re: /kube-probe/i, label: "probe:kube-probe", probe: true },
  { re: /googlehc/i, label: "probe:googlehc", probe: true },
  { re: /checkly/i, label: "probe:checkly", probe: true },
  { re: /statuscake/i, label: "probe:statuscake", probe: true },
  { re: /better\s*uptime|betterstack/i, label: "probe:betterstack", probe: true },
  { re: /chatgpt/i, label: "ai:chatgpt", probe: false },
  { re: /openai/i, label: "ai:openai", probe: false },
  { re: /anthropic|claude/i, label: "ai:claude", probe: false },
  { re: /cursor/i, label: "ai:cursor", probe: false },
  { re: /copilot/i, label: "ai:copilot", probe: false },
  { re: /perplexity/i, label: "ai:perplexity", probe: false },
  { re: /windsurf/i, label: "ai:windsurf", probe: false },
  { re: /gemini/i, label: "ai:gemini", probe: false },
  { re: /deepseek/i, label: "ai:deepseek", probe: false },
  { re: /mistral/i, label: "ai:mistral", probe: false },
  { re: /(?:^|[^a-z0-9])grok(?:[^a-z0-9]|$)/i, label: "ai:grok", probe: false },
  { re: /(?:^|[^a-z0-9])xai(?:[^a-z0-9]|$)/i, label: "ai:grok", probe: false },
  { re: /cline/i, label: "ai:cline", probe: false },
  { re: /replit/i, label: "ai:replit", probe: false },
  { re: /devin/i, label: "ai:devin", probe: false },
  { re: /aider/i, label: "ai:aider", probe: false },
  { re: /python-httpx/i, label: "generic:python-httpx", probe: false },
  { re: /python-requests/i, label: "generic:python-requests", probe: false },
  { re: /go-http-client/i, label: "generic:go-http-client", probe: false },
  { re: /coda-agent-runtime/i, label: "generic:coda-agent-runtime", probe: false },
  { re: /undici/i, label: "generic:undici", probe: false },
  { re: /talaria/i, label: "generic:talaria", probe: false },
  { re: /(?:^|[^a-z0-9])curl(?:\/|\s|$)/i, label: "generic:curl", probe: false },
  { re: /node-fetch|(?:^|[^a-z0-9])node(?:\/|\s|$)/i, label: "generic:node", probe: false },
];

export function skipUsage(request: Request): boolean {
  if (request.headers.get("x-vidfare-test") === "1") return true;
  let host = "";
  try {
    host = new URL(request.url).hostname.toLowerCase();
  } catch {
    return true;
  }
  return host === "localhost" || host === "127.0.0.1" || host === "::1" || host === "[::1]" || host === "0.0.0.0";
}

export function bucketUserAgent(userAgent: string | null): { label: string; likelyProbe: boolean } {
  if (!userAgent) return { label: "other", likelyProbe: false };
  const sample = userAgent.trim().slice(0, UA_SCAN_MAX);
  if (!sample) return { label: "other", likelyProbe: false };
  for (const rule of UA_RULES) {
    if (rule.re.test(sample)) return { label: rule.label, likelyProbe: rule.probe };
  }
  return { label: "other", likelyProbe: false };
}

/**
 * Coarse label from initialize `clientInfo`, or null when name and version
 * are both absent. Known products map to a fixed bucket. Anything else is
 * `client:` plus a normalised slug, truncated to 40 characters. An email,
 * IP address, or UUID becomes `other`.
 */
export function clientLabelFromInfo(name: unknown, version: unknown): string | null {
  const nameText = clipString(name, 80);
  const versionText = clipString(version, 32);
  if (!nameText && !versionText) return null;
  if (!nameText || isPersonal(nameText)) return "other";
  const slug = normalizeSlug(nameText);
  if (!slug) return "other";
  const known = knownBucket(slug);
  if (known) return known;
  let label = `client:${slug}`;
  const versionSlug = versionText ? safeVersion(versionText) : "";
  if (versionSlug) {
    const withVersion = `${label}@${versionSlug}`;
    if (withVersion.length <= CLIENT_MAX) label = withVersion;
  }
  return fitClient(label);
}

export function buildUsagePoints(input: UsageInput): UsageDataPoint[] {
  const ua = bucketUserAgent(input.userAgent);
  const httpMethod = httpBucket(input.httpMethod);
  const status = statusBucket(input.status);
  const probeBlob = ua.likelyProbe ? "1" : "0";
  const messages = messagesFrom(input.bodyText);
  return messages.map((message) => {
    const client = message.client || ua.label;
    const method = message.method;
    const blobs = [method, message.tool, fitClient(client), message.args, httpMethod, status, probeBlob, LAYOUT];
    if (message.alias) blobs.push("alias");
    return {
      indexes: [method],
      blobs,
      doubles: [ua.likelyProbe ? 1 : 0],
    };
  });
}

/** Fire-and-forget. A missing binding or a throw is ignored. Nothing is awaited. */
export function writeUsagePoints(dataset: UsageDataset | undefined, points: UsageDataPoint[]): void {
  for (const point of points) {
    try {
      const result = dataset?.writeDataPoint(point) as unknown;
      if (result && typeof (result as { then?: unknown }).then === "function") {
        void (result as Promise<unknown>).catch(() => {});
      }
    } catch {
      // The count is optional. The response is already decided.
    }
  }
}

function messagesFrom(text: string): MessageLog[] {
  const trimmed = text.trim();
  if (!trimmed) return [blankMessage("other")];
  try {
    const parsed = JSON.parse(trimmed) as unknown;
    if (Array.isArray(parsed)) {
      if (parsed.length === 0) return [blankMessage("other")];
      if (parsed.length > BATCH_LOG_LIMIT) return [blankMessage("batch")];
      return parsed.map((message) => messageLog(message));
    }
    return [messageLog(parsed)];
  } catch {
    return [blankMessage("other")];
  }
}

function blankMessage(method: string): MessageLog {
  return { method, tool: "none", args: "", client: null, alias: false };
}

function messageLog(message: unknown): MessageLog {
  if (!message || typeof message !== "object" || Array.isArray(message)) return blankMessage("other");
  const record = message as { method?: unknown; params?: unknown };
  const method = rpcBucket(record.method);
  const params = record.params;
  if (method === "tools/call") {
    const name = params && typeof params === "object"
      ? (params as { name?: unknown }).name
      : undefined;
    const resolved = typeof name === "string" ? resolveToolName(name) : null;
    const tool: KnownTool | "unknown" = resolved && resolved.kind !== "unknown" ? resolved.name : "unknown";
    const args = params && typeof params === "object"
      ? argumentNames((params as { arguments?: unknown }).arguments)
      : "";
    return { method, tool, args, client: null, alias: resolved?.kind === "alias" };
  }
  if (method === "initialize" && params && typeof params === "object") {
    const info = (params as { clientInfo?: unknown }).clientInfo;
    if (info && typeof info === "object") {
      const client = clientLabelFromInfo(
        (info as { name?: unknown }).name,
        (info as { version?: unknown }).version,
      );
      return { method, tool: "none", args: "", client, alias: false };
    }
  }
  return { method, tool: "none", args: "", client: null, alias: false };
}

function rpcBucket(method: unknown): string {
  if (method === "initialize" || method === "tools/list" || method === "tools/call") return method;
  if (typeof method === "string" && method.startsWith("notifications/")) return "notifications/*";
  return "other";
}

function argumentNames(args: unknown): string {
  if (!args || typeof args !== "object" || Array.isArray(args)) return "";
  const names = [...new Set(Object.keys(args).map((key) => key.toLowerCase()).filter((key) => ARG_NAME.test(key)))].sort();
  let joined = "";
  for (const name of names) {
    const next = joined ? `${joined},${name}` : name;
    if (next.length > 80 || joined.split(",").length >= 12) break;
    joined = next;
  }
  return joined;
}

function httpBucket(method: string): string {
  const upper = method.toUpperCase();
  return HTTP_METHODS.has(upper) ? upper : "other";
}

function statusBucket(status: number): string {
  if (status >= 200 && status < 300) return "2xx";
  if (status >= 300 && status < 400) return "3xx";
  if (status >= 400 && status < 500) return "4xx";
  if (status >= 500 && status < 600) return "5xx";
  return "other";
}

function knownBucket(slug: string): string | null {
  return matchKeys(slug, PROBE_KEYS, "probe:")
    || matchKeys(slug, GENERIC_KEYS, "generic:")
    || matchKeys(slug, AI_KEYS, "ai:");
}

function matchKeys(slug: string, entries: ReadonlyArray<readonly [string, string]>, prefix: string): string | null {
  let best: { key: string; name: string } | null = null;
  for (const [key, name] of entries) {
    if (slug === key || slug.startsWith(`${key}-`)) {
      if (!best || key.length > best.key.length) best = { key, name };
    }
  }
  return best ? `${prefix}${best.name}` : null;
}

function clipString(value: unknown, max: number): string {
  if (typeof value !== "string") return "";
  return value.trim().slice(0, max);
}

function isPersonal(value: string): boolean {
  if (value.includes("@")) return true;
  if (/\b(?:\d{1,3}\.){3}\d{1,3}\b/.test(value)) return true;
  if (/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i.test(value)) return true;
  return false;
}

function normalizeSlug(raw: string): string {
  let text = raw;
  try {
    text = raw.normalize("NFKC");
  } catch {
    text = raw;
  }
  return text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

function safeVersion(raw: string): string {
  let value = raw.trim().toLowerCase();
  if (/^v[0-9]/.test(value)) value = value.slice(1);
  if (!/^[0-9][0-9a-z._-]{0,15}$/.test(value)) return "";
  return value;
}

function fitClient(label: string): string {
  if (label.length <= CLIENT_MAX) return label;
  const cut = label.slice(0, CLIENT_MAX).replace(/[-@._:]+$/g, "");
  return cut || "other";
}
