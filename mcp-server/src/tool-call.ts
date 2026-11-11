/**
 * Alias rewriting and the unknown-tool result for tools/call.
 * The original request body is left for usage logging.
 */

import { resolveToolName, unknownToolResult } from "./tool-names.ts";

const BODY_MAX = 65_536;

export interface PreparedCall {
  request: Request;
  /** JSON-RPC id key → raw tool name, for calls that are not a real tool or a safe alias. */
  unknown: Map<string, string>;
}

export async function prepareToolCall(request: Request): Promise<PreparedCall> {
  const unknown = new Map<string, string>();
  if (request.method !== "POST") return { request, unknown };
  let path = "";
  try {
    path = new URL(request.url).pathname;
  } catch {
    return { request, unknown };
  }
  if (path !== "/mcp") return { request, unknown };
  const declared = Number(request.headers.get("content-length") || "");
  if (Number.isFinite(declared) && declared > BODY_MAX) return { request, unknown };
  let text = "";
  try {
    text = await request.clone().text();
  } catch {
    return { request, unknown };
  }
  if (text.length > BODY_MAX) return { request, unknown };
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch {
    return { request, unknown };
  }
  let changed = false;
  const rewrite = (message: unknown): unknown => {
    const next = rewriteMessage(message, unknown);
    if (next !== message) changed = true;
    return next;
  };
  const body = Array.isArray(parsed) ? parsed.map(rewrite) : rewrite(parsed);
  if (!changed) return { request, unknown };
  const headers = new Headers(request.headers);
  headers.delete("content-length");
  return {
    request: new Request(request.url, { method: request.method, headers, body: JSON.stringify(body) }),
    unknown,
  };
}

export async function presentToolCall(response: Response, unknown: Map<string, string>): Promise<Response> {
  if (unknown.size === 0) return response;
  const type = (response.headers.get("content-type") || "").toLowerCase();
  if (response.status !== 200 || !type.includes("application/json")) return response;
  const text = await response.text();
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch {
    return copyResponse(response, text);
  }
  const next = rewriteResponse(parsed, unknown);
  if (next === undefined) return copyResponse(response, text);
  const headers = new Headers(response.headers);
  headers.delete("content-length");
  return new Response(JSON.stringify(next), {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

function rewriteMessage(message: unknown, unknown: Map<string, string>): unknown {
  if (!message || typeof message !== "object" || Array.isArray(message)) return message;
  const record = message as { method?: unknown; id?: unknown; params?: unknown };
  if (record.method !== "tools/call") return message;
  const params = record.params;
  if (!params || typeof params !== "object" || Array.isArray(params)) return message;
  const name = (params as { name?: unknown }).name;
  if (typeof name !== "string") return message;
  const resolved = resolveToolName(name);
  if (resolved.kind === "unknown") {
    const key = idKey(record.id);
    if (key != null) unknown.set(key, name);
    return message;
  }
  if (resolved.kind !== "alias") return message;
  return { ...record, params: { ...params, name: resolved.name } };
}

function rewriteResponse(parsed: unknown, unknown: Map<string, string>): unknown | undefined {
  if (Array.isArray(parsed)) {
    let changed = false;
    const next = parsed.map((item) => {
      const replaced = replaceOne(item, unknown);
      if (replaced !== item) changed = true;
      return replaced;
    });
    return changed ? next : undefined;
  }
  const replaced = replaceOne(parsed, unknown);
  return replaced === parsed ? undefined : replaced;
}

function replaceOne(message: unknown, unknown: Map<string, string>): unknown {
  if (!message || typeof message !== "object" || Array.isArray(message)) return message;
  const record = message as { id?: unknown; result?: { isError?: boolean }; error?: unknown };
  const key = idKey(record.id);
  if (key == null || !unknown.has(key)) return message;
  const failed = record.error != null || Boolean(record.result?.isError);
  if (!failed) return message;
  const id = record.id;
  if (typeof id !== "string" && typeof id !== "number") return message;
  return unknownToolResult(id, unknown.get(key) || "");
}

function idKey(id: unknown): string | null {
  if (typeof id === "string") return `s:${id}`;
  if (typeof id === "number" && Number.isFinite(id)) return `n:${id}`;
  return null;
}

function copyResponse(response: Response, text: string): Response {
  const headers = new Headers(response.headers);
  headers.delete("content-length");
  return new Response(text, { status: response.status, statusText: response.statusText, headers });
}
