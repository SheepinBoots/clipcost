import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/webStandardStreamableHttp.js";
import { z } from "zod";
import { CatalogError, loadLiveCatalog } from "./catalog.ts";
import { DEALS_URL, PRICES_URL, runTool, SITE } from "./tools.ts";
import { withUtm } from "./links.ts";
import { buildUsagePoints, skipUsage, writeUsagePoints, type UsageDataset } from "./usage.ts";

export interface Env {
  USAGE?: UsageDataset;
}

const INSTRUCTIONS = [
  "VidFare is a read-only catalog of AI video prices in dollars per second of finished video.",
  "Every tool result includes citation.source_url, citation.last_checked, and citation.page.",
  "Cite citation.page. That link is the VidFare page for the answer.",
  "If missing is true, or a price field is null, say VidFare does not have that figure.",
  "Do not invent a price, a resolution, or an end date that is not in the result.",
  `Prices are read from ${PRICES_URL}. Deals are read from ${DEALS_URL}.`,
].join(" ");

const audio = z.enum(["with", "without", "on", "off"]).optional()
  .describe("with or without audio. on and off are accepted. Omit to leave audio unset.");
const input = z.enum(["t2v", "i2v", "ref2v", "v2v", "extend", "lip-sync"]).optional()
  .describe("Input mode: t2v, i2v, ref2v, v2v, extend, or lip-sync. Omit to leave input unset.");
const seconds = z.number().int().min(1).describe("Clip length in whole seconds, at least 1.");
const resolution = z.string().optional()
  .describe("Resolution such as 480p, 720p, 1080p, or 4K. Use 'not listed' when the vendor page does not list one.");
const provider = z.string().optional()
  .describe("Platform name, such as fal, Higgsfield, Krea, or Magnific. A credit-plan platform selects that platform's first plan, the same way the calculator does.");
const used = z.number().int().min(1).max(100).optional()
  .describe("Percent of plan credits actually used, from 1 to 100. Defaults to 100.");
const applyDeals = z.boolean().optional()
  .describe("When true, apply today's credit-plan deals the way the calculator toggle does. Defaults to false.");

function textResult(data: Record<string, unknown>, isError = false) {
  return {
    content: [{ type: "text" as const, text: JSON.stringify(data, null, 2) }],
    structuredContent: data,
    isError,
  };
}

async function call(name: string, args: Record<string, unknown>) {
  try {
    const cache = (globalThis as { caches?: { default?: NonNullable<Parameters<typeof loadLiveCatalog>[0]>["cache"] } }).caches?.default;
    const catalog = await loadLiveCatalog({ cache });
    const result = runTool(name, args, catalog);
    return textResult(result.data, Boolean(result.isError));
  } catch (err) {
    const message = err instanceof CatalogError
      ? err.message
      : "VidFare data could not be loaded. No price is estimated.";
    const source = err instanceof CatalogError ? err.url : PRICES_URL;
    return textResult({
      missing: true,
      message,
      citation: {
        source_url: withUtm(source),
        last_checked: "not stated",
        page: withUtm(`${SITE}/data/`),
      },
    }, true);
  }
}

export function createServer(): McpServer {
  const mcp = new McpServer(
    { name: "VidFare", version: "1.0.0" },
    { instructions: INSTRUCTIONS },
  );
  mcp.registerTool("list_models", {
    title: "List models",
    description: "List the AI video models VidFare tracks, with the cheapest current dollars per second for each.",
    inputSchema: {},
    annotations: { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
  }, async () => call("list_models", {}));

  mcp.registerTool("get_model_prices", {
    title: "Get model prices",
    description: "List current VidFare prices for one model. provider and resolution are optional filters. Prices the catalog does not contain are omitted rather than guessed.",
    inputSchema: {
      model: z.string().describe("Model slug, such as wan-3-0 or kling-3-0, or the model name."),
      provider,
      resolution,
    },
    annotations: { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
  }, async (args) => call("get_model_prices", args));

  mcp.registerTool("estimate_cost", {
    title: "Estimate clip cost",
    description: "Cost of one clip from the VidFare calculator. Credit-plan rows use plan price ÷ credits × credits per clip, then the percent of credits used. API rows are billed seconds times the stated dollars per second. A length, resolution, audio value, or input the vendor page does not state is returned without a price.",
    inputSchema: {
      model: z.string().describe("Model slug, such as wan-3-0 or kling-3-0, or the model name."),
      seconds,
      resolution,
      audio,
      input,
      plan: z.string().optional().describe("Credit-plan id, such as hf-starter. Optional."),
      provider,
      used,
      apply_deals: applyDeals,
      window_seconds: z.number().int().min(1).optional()
        .describe("Seconds made during an unlimited window. Defaults to 60. Used only for the break-even note, which is not $0 per second."),
    },
    annotations: { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
  }, async (args) => call("estimate_cost", args));

  mcp.registerTool("cheapest_options", {
    title: "Cheapest options",
    description: "Cheapest stated VidFare price for a clip length and resolution, overall and per model. Rows the vendor does not state for that length or resolution are omitted.",
    inputSchema: {
      seconds,
      resolution: z.string().describe("Resolution such as 480p, 720p, 1080p, or 4K, or 'not listed'."),
      audio,
      input,
      used,
      apply_deals: applyDeals,
    },
    annotations: { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
  }, async (args) => call("cheapest_options", args));

  mcp.registerTool("list_deals", {
    title: "List deals",
    description: "List VidFare deals copied from vendor pages and official accounts. status is live, upcoming, ended, or all. Defaults to live. An end date is included only when the source stated one.",
    inputSchema: {
      status: z.enum(["live", "upcoming", "ended", "all"]).optional()
        .describe("Which deals to return. Defaults to live."),
    },
    annotations: { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
  }, async (args) => call("list_deals", args));
  return mcp;
}

function corsHeaders(request: Request): Headers {
  const headers = new Headers();
  headers.set("access-control-allow-origin", "*");
  headers.set("access-control-allow-methods", "GET, POST, DELETE, OPTIONS");
  headers.set(
    "access-control-allow-headers",
    request.headers.get("access-control-request-headers")
      || "content-type, accept, mcp-session-id, mcp-protocol-version, last-event-id",
  );
  headers.set("access-control-expose-headers", "mcp-session-id, mcp-protocol-version");
  return headers;
}

function withCors(response: Response, request: Request): Response {
  const headers = new Headers(response.headers);
  corsHeaders(request).forEach((value, key) => headers.set(key, value));
  return new Response(response.body, { status: response.status, statusText: response.statusText, headers });
}

const GLAMA_CLAIM = '{"$schema":"https://glama.ai/mcp/schemas/connector.json","claim":"glama_claim_AzGr6ysbXyOX7w20aPWp9fcSiauXq9W9"}';

function glamaClaim(request: Request): Response | null {
  const path = new URL(request.url).pathname;
  if (path !== "/mcp/.well-known/glama.json") return null;
  if (request.method !== "GET" && request.method !== "HEAD") return null;
  const headers = corsHeaders(request);
  headers.set("content-type", "application/json");
  return new Response(request.method === "HEAD" ? null : GLAMA_CLAIM, { status: 200, headers });
}

const USAGE_BODY_MAX = 65_536;

/** Classify a POST /mcp body. The original request body is left for the transport. */
async function usageBody(request: Request): Promise<string> {
  if (skipUsage(request) || request.method !== "POST") return "";
  let path = "";
  try {
    path = new URL(request.url).pathname;
  } catch {
    return "";
  }
  if (path !== "/mcp") return "";
  const declared = Number(request.headers.get("content-length") || "");
  if (Number.isFinite(declared) && declared > USAGE_BODY_MAX) return "";
  try {
    const text = await request.clone().text();
    return text.length > USAGE_BODY_MAX ? "" : text;
  } catch {
    return "";
  }
}

function logUsage(request: Request, status: number, env: Env, bodyText: string): void {
  if (skipUsage(request)) return;
  try {
    writeUsagePoints(env.USAGE, buildUsagePoints({
      httpMethod: request.method,
      status,
      userAgent: request.headers.get("user-agent"),
      bodyText,
    }));
  } catch {
    // Classification failed. The response is already decided.
  }
}

export default {
  async fetch(request: Request, env: Env = {}, ctx: { waitUntil?: (promise: Promise<unknown>) => void } = {}): Promise<Response> {
    const bodyText = await usageBody(request);
    const response = await dispatch(request, ctx);
    logUsage(request, response.status, env, bodyText);
    return response;
  },
};

async function dispatch(
  request: Request,
  ctx: { waitUntil?: (promise: Promise<unknown>) => void },
): Promise<Response> {
  const url = new URL(request.url);
  const claim = glamaClaim(request);
  if (claim) return claim;
  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders(request) });
  }
  if (url.pathname === "/") {
    const headers = corsHeaders(request);
    headers.set("content-type", "text/plain; charset=utf-8");
    return new Response(
      "VidFare MCP server. Streamable HTTP endpoint: /mcp\nDocs: https://vidfare.com/mcp/\n",
      { headers },
    );
  }
  if (url.pathname !== "/mcp") {
    const headers = corsHeaders(request);
    headers.set("content-type", "text/plain; charset=utf-8");
    return new Response("Not found. The MCP endpoint is /mcp\n", { status: 404, headers });
  }
  const mcp = createServer();
  const transport = new WebStandardStreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
    enableJsonResponse: true,
  });
  await mcp.connect(transport);
  const response = await transport.handleRequest(request);
  ctx.waitUntil?.(mcp.close());
  return withCors(response, request);
}
