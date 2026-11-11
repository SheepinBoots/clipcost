import assert from "node:assert/strict";
import { afterEach, test } from "node:test";
import worker from "../src/index.js";

const realFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = realFetch;
});

function origin(body, { status = 200, headers = {} } = {}) {
  return new Response(body, { status, headers });
}

test("json responses get X-Robots-Tag noindex and keep CORS", async () => {
  const seen = [];
  globalThis.fetch = async (request) => {
    seen.push(request);
    return origin('{"ok":true}', {
      headers: {
        "access-control-allow-origin": "*",
        "access-control-allow-methods": "GET, HEAD",
        "content-type": "application/json",
        "cache-control": "public, max-age=300",
      },
    });
  };

  const req = new Request("https://vidfare.com/data/prices.json");
  const res = await worker.fetch(req);

  assert.equal(seen.length, 1);
  assert.equal(seen[0], req);
  assert.equal(res.status, 200);
  assert.equal(res.headers.get("x-robots-tag"), "noindex");
  assert.equal(res.headers.get("access-control-allow-origin"), "*");
  assert.equal(res.headers.get("access-control-allow-methods"), "GET, HEAD");
  assert.equal(res.headers.get("content-type"), "application/json");
  assert.equal(res.headers.get("cache-control"), "public, max-age=300");
  assert.equal(await res.text(), '{"ok":true}');
});

test("deals.json and a json path with a query get the header", async () => {
  globalThis.fetch = async () => origin("[]", { status: 200, headers: { "content-type": "application/json" } });

  for (const url of ["https://vidfare.com/deals.json", "https://vidfare.com/data/prices.json?x=1"]) {
    const res = await worker.fetch(new Request(url));
    assert.equal(res.headers.get("x-robots-tag"), "noindex", url);
    assert.equal(res.headers.get("content-type"), "application/json", url);
  }
});

test("an existing robots tag on json is replaced with noindex", async () => {
  globalThis.fetch = async () =>
    origin("{}", { headers: { "x-robots-tag": "noindex, nofollow", "content-type": "application/json" } });
  const res = await worker.fetch(new Request("https://vidfare.com/data/prices.json"));
  assert.equal(res.headers.get("x-robots-tag"), "noindex");
});

test("non-json responses are returned unchanged", async () => {
  const cases = [
    ["https://vidfare.com/", "<html></html>", { "content-type": "text/html" }],
    ["https://vidfare.com/deals/", "deals", { "content-type": "text/html" }],
    ["https://vidfare.com/data/price_changes.jsonl", "{}\n", { "content-type": "application/x-ndjson" }],
    ["https://vidfare.com/data/", "index", { "content-type": "text/html", "access-control-allow-origin": "*" }],
  ];

  for (const [url, body, headers] of cases) {
    const upstream = origin(body, { status: 200, headers });
    globalThis.fetch = async () => upstream;
    const res = await worker.fetch(new Request(url));
    assert.equal(res, upstream, url);
    assert.equal(res.headers.get("x-robots-tag"), null, url);
    assert.equal(res.headers.get("access-control-allow-origin"), headers["access-control-allow-origin"] ?? null, url);
    assert.equal(await res.text(), body, url);
  }
});
