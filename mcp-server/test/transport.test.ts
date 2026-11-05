import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import test from "node:test";
import { fileURLToPath } from "node:url";

const port = 8787;
const endpoint = `http://127.0.0.1:${port}/mcp`;

test("streamable http smoke test against wrangler dev", { timeout: 180000 }, async () => {
  const child = spawn("npx", ["wrangler", "dev", "--port", String(port), "--ip", "127.0.0.1", "--local"], {
    cwd: fileURLToPath(new URL("..", import.meta.url)),
    env: { ...process.env, CI: "1", WRANGLER_SEND_METRICS: "false" },
    stdio: ["ignore", "pipe", "pipe"],
    detached: true,
  });
  let logs = "";
  child.stdout.on("data", (chunk) => { logs += chunk; });
  child.stderr.on("data", (chunk) => { logs += chunk; });
  try {
    await waitForReady(child, () => logs);
    const headers = {
      "content-type": "application/json",
      accept: "application/json, text/event-stream",
      "mcp-protocol-version": "2025-11-25",
    };
    const init = await post({
      jsonrpc: "2.0",
      id: 1,
      method: "initialize",
      params: {
        protocolVersion: "2025-11-25",
        capabilities: {},
        clientInfo: { name: "vidfare-smoke", version: "1.0.0" },
      },
    }, headers);
    assert.equal(init.status, 200, logs.slice(-2000));
    const initBody = await readBody(init);
    assert.equal(initBody.id, 1);
    assert.ok(initBody.result.serverInfo);
    assert.equal(initBody.result.serverInfo.name, "VidFare");

    const listed = await post({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} }, headers);
    const listBody = await readBody(listed);
    const names = listBody.result.tools.map((tool: { name: string }) => tool.name);
    assert.deepEqual(names, ["list_models", "get_model_prices", "estimate_cost", "cheapest_options", "list_deals"]);

    const request = {
      jsonrpc: "2.0",
      id: 3,
      method: "tools/call",
      params: {
        name: "estimate_cost",
        arguments: { model: "wan-3-0", seconds: 10, resolution: "720p", provider: "fal" },
      },
    };
    const called = await post(request, headers);
    const callBody = await readBody(called);
    assert.notEqual(callBody.result.isError, true);
    const text = callBody.result.content[0].text as string;
    const data = JSON.parse(text);
    assert.equal(data.missing, false);
    const fal = data.priced.find((row: { platform: string }) => row.platform === "fal");
    assert.ok(fal, text.slice(0, 500));
    assert.equal(fal.total_usd, 1);
    assert.match(data.citation.page, /utm_source=mcp/);
    assert.match(data.citation.page, /model=wan-3-0/);
    assert.match(data.citation.source_url, /vidfare\.com\/data\/prices\.json/);
    mkdirSync("/opt/cursor/artifacts", { recursive: true });
    writeFileSync("/opt/cursor/artifacts/mcp-estimate-sample.json", JSON.stringify({
      request: { method: "POST", url: endpoint, headers, body: request },
      response: { status: called.status, body: callBody },
    }, null, 2));
  } finally {
    try {
      process.kill(-child.pid, "SIGTERM");
    } catch {
      child.kill("SIGTERM");
    }
    await new Promise((resolve) => {
      const timer = setTimeout(resolve, 5000);
      child.once("exit", () => {
        clearTimeout(timer);
        resolve(undefined);
      });
    });
  }
});

function post(body: unknown, headers: Record<string, string>) {
  return fetch(endpoint, { method: "POST", headers, body: JSON.stringify(body) });
}

async function readBody(response: Response) {
  const raw = await response.text();
  if (raw.startsWith("event:") || raw.includes("\ndata:")) {
    const data = raw.split("\n").filter((line) => line.startsWith("data:")).map((line) => line.slice(5).trim()).filter(Boolean).at(-1);
    return JSON.parse(data || "{}");
  }
  return JSON.parse(raw);
}

async function waitForReady(child: ReturnType<typeof spawn>, logs: () => string) {
  const started = Date.now();
  while (Date.now() - started < 150000) {
    if (logs().includes("Ready") || logs().includes(`127.0.0.1:${port}`)) {
      try {
        const probe = await fetch(`http://127.0.0.1:${port}/`, { signal: AbortSignal.timeout(2000) });
        if (probe.ok) return;
      } catch {
        // The process has printed a port before the socket accepts.
      }
    }
    if (child.exitCode != null) throw new Error(`wrangler exited ${child.exitCode}\n${logs().slice(-4000)}`);
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error(`wrangler dev did not become ready\n${logs().slice(-4000)}`);
}
