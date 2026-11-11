/**
 * Canonical read-only tools. tools/list publishes these names only.
 *
 * Protocol 2025-11-25 lists an unknown tool as JSON-RPC -32602. This server
 * answers with a CallToolResult (isError: true) instead. Claude Desktop
 * replaces a protocol error with a generic line, so the model never sees
 * which tools exist. isError text is what that client passes through.
 * Cursor and Claude Code also show that text. They can read a protocol
 * error's message too, but Claude Code drops error.data, so the tool list
 * has to be in the text either way.
 *
 * Aliases are case-insensitive, and hyphens, underscores, and spaces are
 * ignored, including camelCase boundaries. The remaining letters and digits
 * must equal a canonical name with its separators removed. Any other
 * character, or a different spelling, is not an alias. There is no
 * edit-distance matching.
 */

export const DOCS_URL = "https://vidfare.com/mcp/";
export const TOOL_NAME_MAX = 64;

export const TOOLS = [
  {
    name: "list_models",
    description: "List the AI video models VidFare tracks, with the cheapest current dollars per second for each.",
  },
  {
    name: "get_model_prices",
    description: "List current VidFare prices for one model.",
  },
  {
    name: "estimate_cost",
    description: "Cost of one clip from the VidFare calculator.",
  },
  {
    name: "cheapest_options",
    description: "Cheapest stated VidFare price for a clip length and resolution, overall and per model.",
  },
  {
    name: "list_deals",
    description: "List VidFare deals copied from vendor pages and official accounts.",
  },
] as const;

export const KNOWN_TOOLS = TOOLS.map((tool) => tool.name);

export type KnownTool = (typeof KNOWN_TOOLS)[number];

const ALIAS_CHARS = /^[A-Za-z0-9 _-]+$/;

export type ToolResolution =
  | { kind: "exact"; name: KnownTool }
  | { kind: "alias"; name: KnownTool }
  | { kind: "unknown" };

const ALIAS_INDEX = aliasIndex();

export function sanitizeToolName(raw: string): string {
  const stripped = raw.replace(/\p{Cc}/gu, "");
  return stripped.replace(/[^A-Za-z0-9_.-]/g, "").slice(0, TOOL_NAME_MAX);
}

export function resolveToolName(raw: string): ToolResolution {
  const exact = KNOWN_TOOLS.find((name) => name === raw);
  if (exact) return { kind: "exact", name: exact };
  const key = aliasKey(raw);
  if (!key) return { kind: "unknown" };
  const canonical = ALIAS_INDEX.get(key);
  if (!canonical) return { kind: "unknown" };
  return { kind: "alias", name: canonical };
}

export function unknownToolMessage(requested: string): string {
  return `Unknown tool: ${requested}. Valid tools: ${KNOWN_TOOLS.join(", ")}. Call tools/list for schemas. Docs: ${DOCS_URL}`;
}

export function unknownToolData(requested: string) {
  return {
    requested_tool: requested,
    valid_tools: TOOLS.map((tool) => ({ name: tool.name, description: tool.description })),
    hint: "tools/list" as const,
    docs: DOCS_URL,
  };
}

export function unknownToolResult(id: string | number, rawName: string) {
  const requested = sanitizeToolName(rawName);
  const data = unknownToolData(requested);
  return {
    jsonrpc: "2.0" as const,
    id,
    result: {
      content: [{ type: "text" as const, text: unknownToolMessage(requested) }],
      structuredContent: data,
      isError: true as const,
    },
  };
}

function aliasIndex(): Map<string, KnownTool> {
  const groups = new Map<string, KnownTool[]>();
  for (const name of KNOWN_TOOLS) {
    const key = aliasKey(name);
    if (!key) continue;
    const list = groups.get(key) ?? [];
    list.push(name);
    groups.set(key, list);
  }
  const index = new Map<string, KnownTool>();
  for (const [key, names] of groups) {
    if (names.length === 1) index.set(key, names[0]);
  }
  return index;
}

function aliasKey(name: string): string | null {
  if (!name || !ALIAS_CHARS.test(name)) return null;
  const trimmed = name.trim();
  if (!trimmed) return null;
  const spaced = trimmed
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/([A-Z]+)([A-Z][a-z])/g, "$1 $2");
  const key = spaced.toLowerCase().replace(/[\s_-]+/g, "");
  return key || null;
}
