import assert from "node:assert/strict";
import test from "node:test";
import worker from "../src/index.ts";
import { clearCatalogCache } from "../src/catalog.ts";
import {
  outcomesFromText,
  skipUsage,
  tallyResponse,
  toolCallsFromText,
  writeUsage,
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
  const points: Array<{ blobs?: string[]; doubles?: number[]; indexes?: string[] }> = [];
  const dataset: UsageDataset & { points: typeof points } = {
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
  return text;
}

test("only tools/call is counted, and only tool plus outcome are stored", async () => {
  const dataset = recording();
  await send(endpoint({ jsonrpc: "2.0", id: 1, method: "initialize", params: { protocolVersion: "2025-11-25", capabilities: {}, clientInfo: { name: "t", version: "0" } } }), dataset);
  await send(endpoint({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} }), dataset);
  await send(endpoint({ jsonrpc: "2.0", method: "notifications/initialized" }), dataset);
  await send(new Request("https://mcp.vidfare.com/mcp", { method: "GET" }), dataset);
  await send(new Request("https://mcp.vidfare.com/", { method: "GET" }), dataset);
  await send(new Request("https://mcp.vidfare.com/mcp", { method: "OPTIONS" }), dataset);
  await send(endpoint({ jsonrpc: "2.0", id: 3, method: "tools/call", params: { name: "not-a-tool", arguments: { prompt: "secret prompt", model: "wan-3-0" } } }), dataset);
  assert.equal(dataset.points.length, 1);
  assert.deepEqual(dataset.points[0], { blobs: ["unknown", "error"], doubles: [1] });
  assert.equal("indexes" in dataset.points[0], false);
  assert.equal(JSON.stringify(dataset.points).includes("secret"), false);
  assert.equal(JSON.stringify(dataset.points).includes("wan-3-0"), false);
});

test("a known tools/call is counted once and the response has no usage fields", async () => {
  clearCatalogCache();
  const dataset = recording();
  const text = await send(endpoint({
    jsonrpc: "2.0",
    id: 4,
    method: "tools/call",
    params: { name: "list_models", arguments: {} },
  }), dataset);
  assert.equal(dataset.points.length, 1);
  assert.deepEqual(Object.keys(dataset.points[0]).sort(), ["blobs", "doubles"]);
  assert.deepEqual(dataset.points[0].blobs?.[0], "list_models");
  assert.ok(dataset.points[0].blobs?.[1] === "success" || dataset.points[0].blobs?.[1] === "error");
  assert.deepEqual(dataset.points[0].doubles, [1]);
  const body = JSON.parse(text);
  assert.equal(body.result.usage, undefined);
  assert.equal(JSON.parse(body.result.content[0].text).usage, undefined);
});

test("the test header and local wrangler are not counted", async () => {
  const dataset = recording();
  await send(endpoint({ jsonrpc: "2.0", id: 5, method: "tools/call", params: { name: "list_models", arguments: { prompt: "skip me" } } }, { "x-vidfare-test": "1" }), dataset);
  await send(new Request("http://127.0.0.1:8787/mcp", {
    method: "POST",
    headers,
    body: JSON.stringify({ jsonrpc: "2.0", id: 6, method: "tools/call", params: { name: "not-a-tool", arguments: { prompt: "local" } } }),
  }), dataset);
  assert.equal(dataset.points.length, 0);
  assert.equal(skipUsage(new Request("http://localhost/mcp", { method: "POST" })), true);
});

test("a thrown counter does not change the response bytes", async () => {
  const throwing: UsageDataset = {
    writeDataPoint() {
      throw new Error("analytics down");
    },
  };
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
  assert.equal(failed, plain);
  assert.equal(failed.includes("analytics down"), false);
});

test("outcome parsing treats JSON-RPC errors and isError as errors", () => {
  assert.deepEqual(toolCallsFromText(JSON.stringify({ method: "tools/list" })), []);
  assert.deepEqual(toolCallsFromText(JSON.stringify({ method: "tools/call", params: { name: "estimate_cost" } })), ["estimate_cost"]);
  assert.deepEqual(
    outcomesFromText(JSON.stringify({ jsonrpc: "2.0", id: 1, error: { code: -32602, message: "bad" } }), "application/json", 1),
    ["error"],
  );
  assert.deepEqual(
    outcomesFromText(JSON.stringify({ jsonrpc: "2.0", id: 1, result: { isError: true, content: [] } }), "application/json", 1),
    ["error"],
  );
  assert.deepEqual(
    outcomesFromText(JSON.stringify({ jsonrpc: "2.0", id: 1, result: { content: [], isError: false } }), "application/json", 1),
    ["success"],
  );
});

test("tally swallows a dataset throw and leaves the response body untouched", async () => {
  const payload = JSON.stringify({ jsonrpc: "2.0", id: 1, result: { content: [{ type: "text", text: "{}" }], isError: false } });
  const response = new Response(payload, { status: 200, headers: { "content-type": "application/json" } });
  await tallyResponse(response.clone(), ["list_models"], {
    writeDataPoint() {
      throw new Error("nope");
    },
  });
  assert.equal(await response.text(), payload);
  assert.doesNotThrow(() => writeUsage({
    writeDataPoint() {
      throw new Error("nope");
    },
  }, "list_models", "success"));
});
