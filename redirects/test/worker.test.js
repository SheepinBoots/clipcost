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

test("/about-us and /about-us/ 301 to https://vidfare.com/about/", async () => {
  globalThis.fetch = async () => {
    throw new Error("origin should not be fetched for a redirect");
  };

  for (const url of ["https://vidfare.com/about-us", "https://vidfare.com/about-us/"]) {
    const res = await worker.fetch(new Request(url));
    assert.equal(res.status, 301, url);
    assert.equal(res.headers.get("location"), "https://vidfare.com/about/", url);
    assert.equal(await res.text(), "", url);
  }
});

test("query strings are preserved on the 301 Location", async () => {
  globalThis.fetch = async () => {
    throw new Error("origin should not be fetched for a redirect");
  };

  const cases = [
    ["https://vidfare.com/about-us?utm_source=reddit", "https://vidfare.com/about/?utm_source=reddit"],
    ["https://vidfare.com/about-us/?ref=1&x=2", "https://vidfare.com/about/?ref=1&x=2"],
  ];

  for (const [url, location] of cases) {
    const res = await worker.fetch(new Request(url));
    assert.equal(res.status, 301, url);
    assert.equal(res.headers.get("location"), location, url);
  }
});

test("other paths pass through to the origin unchanged", async () => {
  const cases = [
    ["https://vidfare.com/", "<html>home</html>", { "content-type": "text/html" }],
    ["https://vidfare.com/about/", "about", { "content-type": "text/html" }],
    ["https://vidfare.com/about-user", "nope", { "content-type": "text/html" }],
    ["https://vidfare.com/about-us/extra", "nested", { "content-type": "text/html" }],
    ["https://vidfare.com/about-us-team", "suffix", { "content-type": "text/html" }],
  ];

  for (const [url, body, headers] of cases) {
    const upstream = origin(body, { status: 200, headers });
    const seen = [];
    globalThis.fetch = async (request) => {
      seen.push(request);
      return upstream;
    };
    const req = new Request(url);
    const res = await worker.fetch(req);
    assert.equal(seen.length, 1, url);
    assert.equal(seen[0], req, url);
    assert.equal(res, upstream, url);
    assert.equal(res.status, 200, url);
    assert.equal(await res.text(), body, url);
  }
});
