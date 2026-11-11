import assert from "node:assert/strict";
import test from "node:test";
import worker from "../src/index.ts";
import { clearCatalogCache } from "../src/catalog.ts";
import {
  DOCS_URL,
  KNOWN_TOOLS,
  TOOLS,
  resolveToolName,
  sanitizeToolName,
  unknownToolMessage,
} from "../src/tool-names.ts";
import { buildUsagePoints, type UsageDataPoint, type UsageDataset } from "../src/usage.ts";

const headers = {
  "content-type": "application/json",
  accept: "application/json, text/event-stream",
  "mcp-protocol-version": "2025-11-25",
};

const VALID = "Unknown tool: not-a-tool. Valid tools: list_models, get_model_prices, estimate_cost, cheapest_options, list_deals. Call tools/list for schemas. Docs: https://vidfare.com/mcp/";

function call(id: string | number, name: string, args: Record<string, unknown> = {}) {
  return {
    jsonrpc: "2.0",
    id,
    method: "tools/call",
    params: { name, arguments: args },
  };
}

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

async function send(body: unknown, dataset?: UsageDataset) {
  const jobs: Promise<unknown>[] = [];
  const response = await worker.fetch(endpoint(body), dataset ? { USAGE: dataset } : {}, {
    waitUntil(job) {
      jobs.push(Promise.resolve(job).catch(() => {}));
    },
  });
  const text = await response.text();
  await Promise.all(jobs);
  return { response, text, body: JSON.parse(text) as Record<string, unknown> };
}

test("sanitize strips controls and HTML, then caps at 64", () => {
  const raw = "\u0000\u0007<img src=x onerror=alert(1)>\n" + "B".repeat(200) + "\u009f";
  const clean = sanitizeToolName(raw);
  assert.equal(clean, "imgsrcxonerroralert1" + "B".repeat(44));
  assert.equal(clean.length, 64);
  assert.match(clean, /^[A-Za-z0-9_.-]+$/);
  assert.equal(clean.includes("<"), false);
  assert.equal(clean.includes("\n"), false);
  assert.equal(clean.includes("\u0000"), false);
  const capped = "A".repeat(64) + "<script>alert(1)</script>";
  assert.equal(sanitizeToolName(capped), "A".repeat(64));
  assert.equal(sanitizeToolName("<>\n\u0000"), "");
  assert.equal(sanitizeToolName("ok.name_1-2"), "ok.name_1-2");
});

test("aliases are only case and separator variants of the five tools", () => {
  const aliases: Array<[string, string]> = [
    ["cheapest-options", "cheapest_options"],
    ["CheapestOptions", "cheapest_options"],
    ["cheapestOptions", "cheapest_options"],
    ["CHEAPEST_OPTIONS", "cheapest_options"],
    ["GET_MODEL_PRICES", "get_model_prices"],
    ["getModelPrices", "get_model_prices"],
    ["get model prices", "get_model_prices"],
    ["get-model_prices", "get_model_prices"],
    ["estimate-cost", "estimate_cost"],
    ["estimateCost", "estimate_cost"],
    ["list-models", "list_models"],
    ["ListModels", "list_models"],
    ["LISTMODELS", "list_models"],
    [" list_models ", "list_models"],
    ["list__models", "list_models"],
    ["list-deals", "list_deals"],
  ];
  for (const [raw, canonical] of aliases) {
    assert.deepEqual(resolveToolName(raw), { kind: "alias", name: canonical });
  }
  for (const name of KNOWN_TOOLS) {
    assert.deepEqual(resolveToolName(name), { kind: "exact", name });
  }
  const rejected = [
    "cheapest_option",
    "cheapestoptionsx",
    "list_model",
    "list.models",
    "list/models",
    "estimate_costs",
    "get_model_price",
    "get_prices",
    "list_models!",
    "list_models\n",
    "",
    " ",
  ];
  for (const raw of rejected) assert.deepEqual(resolveToolName(raw), { kind: "unknown" });
});

test("an unknown tool returns a readable isError result listing the five tools", async () => {
  const { response, body } = await send(call(3, "not-a-tool", { prompt: "SECRET-PROMPT-VALUE" }));
  assert.equal(response.status, 200);
  assert.equal(response.headers.get("content-type"), "application/json");
  assert.equal(response.headers.get("access-control-allow-origin"), "*");
  assert.equal(body.error, undefined);
  assert.equal(body.jsonrpc, "2.0");
  assert.equal(body.id, 3);
  const result = body.result as {
    isError: boolean;
    content: Array<{ type: string; text: string }>;
    structuredContent: {
      requested_tool: string;
      valid_tools: Array<{ name: string; description: string }>;
      hint: string;
      docs: string;
    };
  };
  assert.equal(result.isError, true);
  assert.deepEqual(result.content, [{ type: "text", text: VALID }]);
  assert.equal(result.content[0].text, unknownToolMessage("not-a-tool"));
  assert.equal(result.structuredContent.requested_tool, "not-a-tool");
  assert.equal(result.structuredContent.hint, "tools/list");
  assert.equal(result.structuredContent.docs, DOCS_URL);
  assert.deepEqual(result.structuredContent.valid_tools, TOOLS.map((tool) => ({
    name: tool.name,
    description: tool.description,
  })));
  assert.deepEqual(result.structuredContent.valid_tools.map((tool) => tool.name), [...KNOWN_TOOLS]);
  for (const tool of result.structuredContent.valid_tools) {
    assert.equal(tool.description.includes("\n"), false);
    assert.ok(tool.description.length > 0);
  }
  const text = JSON.stringify(body);
  assert.equal(text.includes("SECRET-PROMPT-VALUE"), false);
});

test("a string id is echoed, and a hostile name is sanitized in the result", async () => {
  const raw = "\u0000\u0007<img src=x onerror=alert(1)>\n" + "B".repeat(200) + "\u009f";
  const clean = "imgsrcxonerroralert1" + "B".repeat(44);
  const dataset = recording();
  const { response, text, body } = await send(call("req-1", raw, { note: "do-not-store-arg" }), dataset);
  assert.equal(response.status, 200);
  assert.equal(body.id, "req-1");
  const result = body.result as {
    isError: boolean;
    content: Array<{ text: string }>;
    structuredContent: { requested_tool: string; valid_tools: Array<{ name: string }> };
  };
  assert.equal(result.isError, true);
  assert.equal(result.structuredContent.requested_tool, clean);
  assert.equal(result.structuredContent.requested_tool.length, 64);
  assert.equal(result.content[0].text, unknownToolMessage(clean));
  assert.deepEqual(result.structuredContent.valid_tools.map((tool) => tool.name), [...KNOWN_TOOLS]);
  assert.equal(text.includes("<"), false);
  assert.equal(text.includes(">"), false);
  assert.equal(text.includes("\u0000"), false);
  assert.equal(text.includes("onerror="), false);
  assert.equal(text.includes("alert(1)"), false);
  assert.equal(text.includes("B".repeat(80)), false);
  assert.equal(text.includes(raw), false);
  assert.equal(text.includes("do-not-store-arg"), false);
  assert.equal(dataset.points.length, 1);
  assert.equal(dataset.points[0].blobs?.[1], "unknown");
  assert.equal(dataset.points[0].blobs?.[7], "v2");
  assert.equal(dataset.points[0].blobs?.length, 8);
  const stored = JSON.stringify(dataset.points);
  assert.equal(stored.includes("imgsrcx"), false);
  assert.equal(stored.includes("<"), false);
  assert.equal(stored.includes("do-not-store-arg"), false);
  assert.equal(stored.includes("B".repeat(20)), false);
});

test("a name that sanitizes to empty is still an unknown-tool result", async () => {
  const { text, body } = await send(call(9, "<>\n\u0000"));
  const result = body.result as { content: Array<{ text: string }>; structuredContent: { requested_tool: string } };
  assert.equal(result.structuredContent.requested_tool, "");
  assert.equal(result.content[0].text, "Unknown tool: . Valid tools: list_models, get_model_prices, estimate_cost, cheapest_options, list_deals. Call tools/list for schemas. Docs: https://vidfare.com/mcp/");
  assert.equal(text.includes("<"), false);
  assert.equal(text.includes("\n"), false);
  assert.equal(text.includes("\u0000"), false);
});

test("safe aliases run the canonical read-only tool", { timeout: 120000 }, async () => {
  clearCatalogCache();
  const listed = await send({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} });
  const tools = (listed.body.result as { tools: Array<{ name: string; description: string; annotations?: { readOnlyHint?: boolean; destructiveHint?: boolean } }> }).tools;
  assert.deepEqual(tools.map((tool) => tool.name), [...KNOWN_TOOLS]);
  for (const tool of tools) {
    assert.equal(tool.annotations?.readOnlyHint, true);
    assert.equal(tool.annotations?.destructiveHint, false);
    const line = TOOLS.find((item) => item.name === tool.name);
    assert.ok(line);
    assert.equal(tool.description.startsWith(line.description), true);
  }

  const pairs: Array<[string, string, Record<string, unknown>]> = [
    ["list_models", "list-models", {}],
    ["list_models", "ListModels", {}],
    ["get_model_prices", "GET_MODEL_PRICES", { model: "kling-3-0" }],
    ["get_model_prices", "get model prices", { model: "wan-3-0" }],
    ["estimate_cost", "estimate-cost", { model: "wan-3-0" }],
    ["estimate_cost", "estimateCost", { model: "wan-3-0", seconds: 5 }],
    ["cheapest_options", "cheapest-options", { seconds: 5, resolution: "720p" }],
    ["cheapest_options", "CheapestOptions", { seconds: 5, resolution: "720p" }],
    ["list_deals", "list-deals", { status: "live" }],
  ];
  for (const [canonical, alias, args] of pairs) {
    clearCatalogCache();
    await send(call(4, canonical, args));
    const left = await send(call(4, canonical, args));
    const right = await send(call(4, alias, args));
    assert.equal(left.body.error, undefined);
    assert.equal(right.body.error, undefined);
    assert.deepEqual(right.body.result, left.body.result);
    const text = JSON.stringify(right.body);
    assert.equal(text.includes("Unknown tool:"), false);
    assert.equal(text.includes(alias), false);
  }
});

test("near misses stay unknown and a canonical call is unchanged", { timeout: 60000 }, async () => {
  for (const name of ["cheapest_option", "list.models", "estimate_costs", "get_model_price"]) {
    const { body } = await send(call(1, name));
    const result = body.result as { isError: boolean; content: Array<{ text: string }>; structuredContent: { requested_tool: string } };
    assert.equal(result.isError, true);
    assert.equal(result.structuredContent.requested_tool, name);
    assert.equal(result.content[0].text.includes("Valid tools: list_models, get_model_prices, estimate_cost, cheapest_options, list_deals."), true);
  }
  clearCatalogCache();
  const direct = await send(call(8, "list_models", {}));
  assert.equal(direct.body.error, undefined);
  const result = direct.body.result as { isError?: boolean; content: Array<{ text: string }> };
  assert.notEqual(result.isError, true);
  assert.equal(result.content[0].text.includes("Unknown tool:"), false);
  const data = JSON.parse(result.content[0].text) as { models?: unknown; citation?: { page?: string } };
  assert.ok(Array.isArray(data.models));
  assert.match(data.citation?.page || "", /vidfare\.com\/models\//);
});

test("usage logs unknown as unknown and an alias as the canonical tool", { timeout: 60000 }, async () => {
  const unknown = buildUsagePoints({
    httpMethod: "POST",
    status: 200,
    userAgent: "curl/8.0",
    bodyText: JSON.stringify(call(1, "\u0000<not-a-tool>", { model: "wan-3-0", prompt: "secret prompt" })),
  });
  assert.equal(unknown[0].blobs?.[1], "unknown");
  assert.equal(unknown[0].blobs?.[3], "model,prompt");
  assert.equal(unknown[0].blobs?.length, 8);
  assert.equal(unknown[0].blobs?.[7], "v2");
  assert.equal(JSON.stringify(unknown).includes("not-a-tool"), false);
  assert.equal(JSON.stringify(unknown).includes("secret"), false);
  assert.equal(JSON.stringify(unknown).includes("wan-3-0"), false);

  const alias = buildUsagePoints({
    httpMethod: "POST",
    status: 200,
    userAgent: "Cursor/1.0",
    bodyText: JSON.stringify(call(2, "GET_MODEL_PRICES", { model: "kling-3-0", seconds: 5 })),
  });
  assert.deepEqual(alias[0].blobs, [
    "tools/call",
    "get_model_prices",
    "ai:cursor",
    "model,seconds",
    "POST",
    "2xx",
    "0",
    "v2",
    "alias",
  ]);
  assert.equal(JSON.stringify(alias).includes("GET_MODEL_PRICES"), false);
  assert.equal(JSON.stringify(alias).includes("kling-3-0"), false);

  const exact = buildUsagePoints({
    httpMethod: "POST",
    status: 200,
    userAgent: null,
    bodyText: JSON.stringify(call(3, "list_models", {})),
  });
  assert.equal(exact[0].blobs?.length, 8);
  assert.equal(exact[0].blobs?.[1], "list_models");
  assert.equal(exact[0].blobs?.includes("alias"), false);

  const dataset = recording();
  await send([
    call("a", "no-such-tool", { prompt: "hide-me" }),
    call("b", "cheapest-options", { seconds: 5, resolution: "720p" }),
  ], dataset);
  assert.equal(dataset.points.length, 2);
  assert.equal(dataset.points[0].blobs?.[1], "unknown");
  assert.equal(dataset.points[0].blobs?.length, 8);
  assert.equal(dataset.points[1].blobs?.[1], "cheapest_options");
  assert.equal(dataset.points[1].blobs?.[8], "alias");
  assert.equal(dataset.points[1].blobs?.[7], "v2");
  const stored = JSON.stringify(dataset.points);
  assert.equal(stored.includes("no-such-tool"), false);
  assert.equal(stored.includes("cheapest-options"), false);
  assert.equal(stored.includes("hide-me"), false);
  assert.equal(stored.includes("720p"), false);
});
