import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import Ajv from "ajv";
import addFormats from "ajv-formats";

const here = dirname(fileURLToPath(import.meta.url));
const server = JSON.parse(readFileSync(join(here, "..", "server.json"), "utf8"));

test("server.json matches the official MCP registry schema", async () => {
  const schemaUrl = server.$schema;
  assert.match(schemaUrl, /^https:\/\/static\.modelcontextprotocol\.io\/schemas\/[^/]+\/server\.schema\.json$/);
  const response = await fetch(schemaUrl);
  assert.equal(response.ok, true, `${schemaUrl} returned ${response.status}`);
  const schema = await response.json();
  const ajv = new Ajv({ allErrors: true, strict: false });
  addFormats(ajv);
  const validate = ajv.compile(schema);
  const ok = validate(server);
  assert.equal(ok, true, JSON.stringify(validate.errors, null, 2));
  assert.equal(server.name, "com.vidfare/vidfare");
  assert.equal(server.remotes[0].type, "streamable-http");
  assert.equal(server.remotes[0].url, "https://mcp.vidfare.com/mcp");
  assert.ok(server.description.length <= 100);
});

test("registry auth file is the published proof record", () => {
  const raw = readFileSync(join(here, "..", "..", "src", ".well-known", "mcp-registry-auth"), "utf8");
  assert.equal(raw, "v=MCPv1; k=ed25519; p=ONNlWhbxQdLcq/vVLAzvHUwd/E1fGGZCcvb7B0M013c=\n");
});
