import assert from "node:assert/strict";
import test from "node:test";
import worker from "../src/index.ts";
import type { UsageDataset } from "../src/usage.ts";

const CLAIM = '{"$schema":"https://glama.ai/mcp/schemas/connector.json","claim":"glama_claim_AzGr6ysbXyOX7w20aPWp9fcSiauXq9W9"}';

function recording() {
  const points: Array<{ blobs?: string[]; doubles?: number[] }> = [];
  const dataset: UsageDataset & { points: typeof points } = {
    points,
    writeDataPoint(event) {
      points.push(event);
    },
  };
  return dataset;
}

async function send(request: Request, dataset = recording()) {
  const jobs: Promise<unknown>[] = [];
  const response = await worker.fetch(request, { USAGE: dataset }, {
    waitUntil(job) {
      jobs.push(Promise.resolve(job).catch(() => {}));
    },
  });
  const text = await response.text();
  await Promise.all(jobs);
  return { response, text, dataset };
}

test("GET /mcp/.well-known/glama.json is the claim, with no redirect", async () => {
  const { response, text, dataset } = await send(new Request("https://mcp.vidfare.com/mcp/.well-known/glama.json"));
  assert.equal(response.status, 200);
  assert.equal(response.headers.get("location"), null);
  assert.equal(response.headers.get("content-type"), "application/json");
  assert.equal(response.headers.get("access-control-allow-origin"), "*");
  assert.equal(text, CLAIM);
  assert.equal(dataset.points.length, 1);
  assert.equal(dataset.points[0].blobs?.[0], "other");
  assert.equal(dataset.points[0].blobs?.[4], "GET");
  assert.equal(dataset.points[0].blobs?.[5], "2xx");
  const stored = JSON.stringify(dataset.points);
  assert.equal(stored.includes("glama_claim"), false);
  assert.equal(stored.includes("AzGr6ysbXyOX7w20aPWp9fcSiauXq9W9"), false);
});

test("HEAD /mcp/.well-known/glama.json uses the same headers", async () => {
  const { response, text, dataset } = await send(new Request("https://mcp.vidfare.com/mcp/.well-known/glama.json", { method: "HEAD" }));
  assert.equal(response.status, 200);
  assert.equal(response.headers.get("location"), null);
  assert.equal(response.headers.get("content-type"), "application/json");
  assert.equal(response.headers.get("access-control-allow-origin"), "*");
  assert.equal(text, "");
  assert.equal(dataset.points.length, 1);
  assert.equal(dataset.points[0].blobs?.[4], "HEAD");
  assert.equal(JSON.stringify(dataset.points).includes("glama_claim"), false);
});
