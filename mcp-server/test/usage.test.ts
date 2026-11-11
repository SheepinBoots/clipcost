import assert from "node:assert/strict";
import test from "node:test";
import worker from "../src/index.ts";
import { clearCatalogCache } from "../src/catalog.ts";
import {
  BATCH_LOG_LIMIT,
  bucketUserAgent,
  buildUsagePoints,
  clientLabelFromInfo,
  skipUsage,
  writeUsagePoints,
  type UsageDataPoint,
  type UsageDataset,
} from "../src/usage.ts";

const headers = {
  "content-type": "application/json",
  accept: "application/json, text/event-stream",
  "mcp-protocol-version": "2025-11-25",
};

function endpoint(body: unknown, extra: Record<string, string> = {}) {
  return new Request("https://mcp.vidfare.com/mcp", {
    method: "POST",
    headers: { ...headers, ...extra },
    body: JSON.stringify(body),
  });
}

function recording() {
  const points: UsageDataPoint[] = [];
  const dataset: UsageDataset & { points: UsageDataPoint[] } = {
    points,
    writeDataPoint(event) {
      points.push(event);
    },
  };
  return dataset;
}

async function send(request: Request, dataset?: UsageDataset) {
  const jobs: Promise<unknown>[] = [];
  const response = await worker.fetch(request, { USAGE: dataset }, {
    waitUntil(job) {
      jobs.push(Promise.resolve(job).catch(() => {}));
    },
  });
  const text = await response.text();
  await Promise.all(jobs);
  return { response, text };
}

function point(blobs: string[], probe: boolean, method = blobs[0]) {
  return {
    indexes: [method],
    blobs,
    doubles: [probe ? 1 : 0],
  };
}

test("user-agent buckets stay coarse and never keep the raw header", () => {
  const probes: Array<[string, string]> = [
    ["mcpbeat/1.2", "probe:mcpbeat"],
    ["AgentRank scanner", "probe:agentrank"],
    ["alalanet/0.4", "probe:alalanet"],
    ["compatible; histor/1.0", "probe:histor"],
    ["EveryMCP directory", "probe:everymcp"],
    ["mcptry/2", "probe:mcptry"],
    ["Glama/1.0 (+https://glama.ai/secret-path)", "probe:glama"],
    ["MCPWatch/3.1", "probe:mcpwatch"],
    ["SmitheryBot/1.0", "probe:smithery"],
    ["UptimeRobot/2.0", "probe:uptimerobot"],
  ];
  for (const [ua, label] of probes) {
    const bucket = bucketUserAgent(ua);
    assert.equal(bucket.label, label);
    assert.equal(bucket.likelyProbe, true);
    assert.equal(bucket.label.includes("secret-path"), false);
    assert.equal(JSON.stringify(bucket).includes(ua), false);
  }
  assert.equal(bucketUserAgent("not-historical").label, "other");

  const clients: Array<[string, string]> = [
    ["ChatGPT-User", "ai:chatgpt"],
    ["OpenAI/1.0", "ai:openai"],
    ["Claude-User", "ai:claude"],
    ["Anthropic-AI", "ai:claude"],
    ["Cursor/0.45.2", "ai:cursor"],
    ["GitHub-Copilot", "ai:copilot"],
  ];
  for (const [ua, label] of clients) {
    const bucket = bucketUserAgent(ua);
    assert.equal(bucket.label, label);
    assert.equal(bucket.likelyProbe, false);
  }

  const libs: Array<[string, string]> = [
    ["node", "generic:node"],
    ["node/20.11.0", "generic:node"],
    ["node-fetch/3.0", "generic:node"],
    ["python-httpx/0.27.0", "generic:python-httpx"],
    ["python-requests/2.32.3", "generic:python-requests"],
    ["Go-http-client/1.1", "generic:go-http-client"],
    ["undici", "generic:undici"],
    ["coda-agent-runtime/1", "generic:coda-agent-runtime"],
    ["Talaria/2", "generic:talaria"],
    ["curl/8.7.1", "generic:curl"],
  ];
  for (const [ua, label] of libs) {
    const bucket = bucketUserAgent(`${ua} SECRET-UA-TOKEN`);
    assert.equal(bucket.label, label);
    assert.equal(bucket.likelyProbe, false);
    assert.equal(bucket.label.includes("SECRET-UA-TOKEN"), false);
  }

  assert.deepEqual(bucketUserAgent(null), { label: "other", likelyProbe: false });
  assert.deepEqual(bucketUserAgent("   "), { label: "other", likelyProbe: false });
  const browser = bucketUserAgent("Mozilla/5.0 (Macintosh) AppleWebKit/537.36 Chrome/120.0.0.0");
  assert.equal(browser.label, "other");
  assert.equal(browser.likelyProbe, false);
  assert.equal(JSON.stringify(browser).includes("Mozilla"), false);
  assert.equal(JSON.stringify(browser).includes("Chrome"), false);
});

test("initialize clientInfo is normalised, truncated, and mapped to a known bucket", () => {
  assert.equal(clientLabelFromInfo("Cursor", "1.2.3"), "ai:cursor");
  assert.equal(clientLabelFromInfo("Claude Desktop", "1.0.0"), "ai:claude");
  assert.equal(clientLabelFromInfo("Anthropic", "2025.1"), "ai:claude");
  assert.equal(clientLabelFromInfo("ChatGPT", "9"), "ai:chatgpt");
  assert.equal(clientLabelFromInfo("OpenAI", "1"), "ai:openai");
  assert.equal(clientLabelFromInfo("Glama crawler", "1"), "probe:glama");
  assert.equal(clientLabelFromInfo("mcpbeat", "1"), "probe:mcpbeat");
  assert.equal(clientLabelFromInfo("python-httpx", "0.27"), "generic:python-httpx");
  assert.equal(clientLabelFromInfo("My Little Agent", "2.0.1"), "client:my-little-agent@2.0.1");
  assert.equal(clientLabelFromInfo("someone@example.com", "1.0.0"), "other");
  assert.equal(clientLabelFromInfo("203.0.113.9", "1"), "other");
  assert.equal(clientLabelFromInfo("11111111-2222-3333-4444-555555555555", "1"), "other");
  assert.equal(clientLabelFromInfo(undefined, "1.2.3"), "other");
  assert.equal(clientLabelFromInfo(undefined, undefined), null);
  const long = clientLabelFromInfo("A".repeat(200), "9".repeat(80));
  assert.ok(long);
  assert.ok(long.length <= 40);
  assert.equal(long.startsWith("client:"), true);
  assert.equal(long.includes("999"), false);
});

test("points keep method, tool, argument names, and buckets, and drop values", () => {
  const secret = "secret prompt wan-3-0 203.0.113.50";
  const call = buildUsagePoints({
    httpMethod: "POST",
    status: 200,
    userAgent: "Glama/1.0 extra-raw-ua",
    bodyText: JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method: "tools/call",
      params: {
        name: "not-a-tool",
        arguments: { model: "wan-3-0", prompt: secret, seconds: 5 },
      },
    }),
  });
  assert.deepEqual(call, [
    point(["tools/call", "unknown", "probe:glama", "model,prompt,seconds", "POST", "2xx", "1", "v2"], true),
  ]);
  assert.equal(JSON.stringify(call).includes("wan-3-0"), false);
  assert.equal(JSON.stringify(call).includes("secret"), false);
  assert.equal(JSON.stringify(call).includes("extra-raw-ua"), false);

  const known = buildUsagePoints({
    httpMethod: "POST",
    status: 200,
    userAgent: "curl/8.0",
    bodyText: JSON.stringify({
      method: "tools/call",
      params: { name: "estimate_cost", arguments: { model: "wan-3-0", seconds: 10 } },
    }),
  });
  assert.equal(known[0].blobs?.[1], "estimate_cost");
  assert.equal(known[0].blobs?.[2], "generic:curl");
  assert.equal(known[0].blobs?.[3], "model,seconds");
  assert.equal(known[0].doubles?.[0], 0);

  const init = buildUsagePoints({
    httpMethod: "POST",
    status: 200,
    userAgent: "mcpwatch/1 extra-raw-ua",
    bodyText: JSON.stringify({
      method: "initialize",
      params: { protocolVersion: "2025-11-25", clientInfo: { name: "Cursor", version: "0.45.0" } },
    }),
  });
  assert.equal(init[0].blobs?.[0], "initialize");
  assert.equal(init[0].blobs?.[2], "ai:cursor");
  assert.equal(init[0].blobs?.[6], "1");
  assert.equal(init[0].doubles?.[0], 1);
  assert.equal(init[0].indexes?.[0], "initialize");

  const listed = buildUsagePoints({
    httpMethod: "POST",
    status: 200,
    userAgent: null,
    bodyText: JSON.stringify({ method: "tools/list" }),
  });
  assert.equal(listed[0].blobs?.[0], "tools/list");
  assert.equal(listed[0].blobs?.[1], "none");
  assert.equal(listed[0].blobs?.[2], "other");

  const note = buildUsagePoints({
    httpMethod: "POST",
    status: 202,
    userAgent: "node",
    bodyText: JSON.stringify({ method: "notifications/user@example.com" }),
  });
  assert.equal(note[0].blobs?.[0], "notifications/*");
  assert.equal(JSON.stringify(note).includes("example.com"), false);
  assert.equal(JSON.stringify(note).includes("@"), false);

  const other = buildUsagePoints({
    httpMethod: "GET",
    status: 404,
    userAgent: "Mozilla/5.0",
    bodyText: "",
  });
  assert.deepEqual(other[0].blobs, ["other", "none", "other", "", "GET", "4xx", "0", "v2"]);

  const odd = buildUsagePoints({
    httpMethod: "TRACE",
    status: 101,
    userAgent: null,
    bodyText: "not json",
  });
  assert.equal(odd[0].blobs?.[0], "other");
  assert.equal(odd[0].blobs?.[4], "other");
  assert.equal(odd[0].blobs?.[5], "other");
  assert.equal(JSON.stringify(odd).includes("not json"), false);
});

test("a batch logs each message, and a long batch collapses to one batch point", () => {
  const batch = buildUsagePoints({
    httpMethod: "POST",
    status: 200,
    userAgent: "Claude-User",
    bodyText: JSON.stringify([
      { method: "initialize", params: { clientInfo: { name: "Claude", version: "1" } } },
      { method: "tools/call", params: { name: "list_models", arguments: { note: "hide me" } } },
    ]),
  });
  assert.equal(batch.length, 2);
  assert.equal(batch[0].blobs?.[0], "initialize");
  assert.equal(batch[0].blobs?.[2], "ai:claude");
  assert.equal(batch[1].blobs?.[0], "tools/call");
  assert.equal(batch[1].blobs?.[1], "list_models");
  assert.equal(batch[1].blobs?.[3], "note");
  assert.equal(JSON.stringify(batch).includes("hide me"), false);
  assert.equal(batch[0].doubles?.[0], 0);

  const huge = Array.from({ length: BATCH_LOG_LIMIT + 1 }, () => ({
    method: "tools/call",
    params: { name: "list_models", arguments: { model: "do-not-store" } },
  }));
  const collapsed = buildUsagePoints({
    httpMethod: "POST",
    status: 200,
    userAgent: "curl/8",
    bodyText: JSON.stringify(huge),
  });
  assert.equal(collapsed.length, 1);
  assert.equal(collapsed[0].blobs?.[0], "batch");
  assert.equal(collapsed[0].indexes?.[0], "batch");
  assert.equal(JSON.stringify(collapsed).includes("do-not-store"), false);
  assert.equal(JSON.stringify(collapsed).includes("list_models"), false);
});

test("a throwing or missing writeDataPoint does not change the response", async () => {
  const throwing: UsageDataset = {
    writeDataPoint() {
      throw new Error("analytics down");
    },
  };
  const init = {
    jsonrpc: "2.0",
    id: 1,
    method: "initialize",
    params: {
      protocolVersion: "2025-11-25",
      capabilities: {},
      clientInfo: { name: "Cursor", version: "1.0.0" },
    },
  };
  const plainInit = await send(endpoint(init, { "user-agent": "Cursor/1.0 secret-ua" }));
  const failedInit = await send(endpoint(init, { "user-agent": "Cursor/1.0 secret-ua" }), throwing);
  assert.equal(failedInit.response.status, plainInit.response.status);
  assert.equal(failedInit.text, plainInit.text);
  assert.equal(failedInit.text.includes("analytics down"), false);
  assert.equal(failedInit.text.includes("secret-ua"), false);

  const body = {
    jsonrpc: "2.0",
    id: 7,
    method: "tools/call",
    params: { name: "list_models", arguments: { note: "do not store" } },
  };
  clearCatalogCache();
  const plain = await send(endpoint(body));
  clearCatalogCache();
  const failed = await send(endpoint(body), throwing);
  assert.equal(failed.text, plain.text);
  assert.equal(failed.text.includes("analytics down"), false);
  assert.equal(failed.text.includes("do not store"), false);

  const dataset = recording();
  const counted = await send(endpoint(init, { "user-agent": "curl/8.0" }), dataset);
  assert.equal(counted.text, plainInit.text);
  assert.equal(dataset.points.length, 1);
  assert.equal(JSON.stringify(dataset.points).includes("secret"), false);
  const parsed = JSON.parse(counted.text);
  assert.equal(parsed.result.usage, undefined);

  assert.doesNotThrow(() => writeUsagePoints(undefined, buildUsagePoints({
    httpMethod: "GET",
    status: 200,
    userAgent: null,
    bodyText: "",
  })));
  assert.doesNotThrow(() => writeUsagePoints(throwing, dataset.points));
});

test("logged requests omit addresses, argument values, and raw headers", async () => {
  const dataset = recording();
  const body = {
    jsonrpc: "2.0",
    id: 3,
    method: "tools/call",
    params: { name: "not-a-tool", arguments: { prompt: "secret prompt", model: "wan-3-0" } },
  };
  const { text } = await send(endpoint(body, {
    "user-agent": "python-requests/2.32 SECRET-UA",
    "x-forwarded-for": "203.0.113.50",
    "cf-connecting-ip": "203.0.113.50",
    "mcp-session-id": "session-secret-id",
  }), dataset);
  assert.equal(dataset.points.length, 1);
  const stored = JSON.stringify(dataset.points);
  assert.equal(stored.includes("secret"), false);
  assert.equal(stored.includes("wan-3-0"), false);
  assert.equal(stored.includes("203.0.113.50"), false);
  assert.equal(stored.includes("SECRET-UA"), false);
  assert.equal(stored.includes("session-secret-id"), false);
  assert.equal(dataset.points[0].blobs?.[0], "tools/call");
  assert.equal(dataset.points[0].blobs?.[1], "unknown");
  assert.equal(dataset.points[0].blobs?.[2], "generic:python-requests");
  assert.equal(dataset.points[0].blobs?.[3], "model,prompt");
  assert.equal(dataset.points[0].blobs?.[6], "0");
  assert.equal(text.includes("secret prompt"), false);
  const without = await send(endpoint(body, {
    "user-agent": "python-requests/2.32 SECRET-UA",
    "x-forwarded-for": "203.0.113.50",
    "cf-connecting-ip": "203.0.113.50",
    "mcp-session-id": "session-secret-id",
  }));
  assert.equal(without.text, text);
});

test("initialize, tools/list, notifications, and non-POST requests are counted", async () => {
  const dataset = recording();
  await send(endpoint({
    jsonrpc: "2.0",
    id: 1,
    method: "initialize",
    params: { protocolVersion: "2025-11-25", capabilities: {}, clientInfo: { name: "t", version: "0" } },
  }, { "user-agent": "Mozilla/5.0 raw-ua" }), dataset);
  await send(endpoint({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} }), dataset);
  await send(endpoint({ jsonrpc: "2.0", method: "notifications/initialized" }), dataset);
  await send(new Request("https://mcp.vidfare.com/mcp", { method: "GET" }), dataset);
  await send(new Request("https://mcp.vidfare.com/", { method: "GET" }), dataset);
  await send(new Request("https://mcp.vidfare.com/mcp", { method: "OPTIONS" }), dataset);
  assert.deepEqual(dataset.points.map((item) => item.blobs?.[0]), [
    "initialize",
    "tools/list",
    "notifications/*",
    "other",
    "other",
    "other",
  ]);
  assert.equal(dataset.points[0].blobs?.[2], "client:t@0");
  assert.equal(JSON.stringify(dataset.points).includes("raw-ua"), false);
  assert.equal(JSON.stringify(dataset.points).includes("Mozilla"), false);
});

test("the test header and local wrangler are not counted", async () => {
  const dataset = recording();
  await send(endpoint({
    jsonrpc: "2.0",
    id: 5,
    method: "tools/call",
    params: { name: "list_models", arguments: { prompt: "skip me" } },
  }, { "x-vidfare-test": "1" }), dataset);
  await send(new Request("http://127.0.0.1:8787/mcp", {
    method: "POST",
    headers,
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: 6,
      method: "tools/call",
      params: { name: "not-a-tool", arguments: { prompt: "local" } },
    }),
  }), dataset);
  assert.equal(dataset.points.length, 0);
  assert.equal(skipUsage(new Request("http://localhost/mcp", { method: "POST" })), true);
  assert.equal(skipUsage(new Request("http://localhost/mcp", { method: "GET" })), true);
});
