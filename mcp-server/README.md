# VidFare MCP server

Public, read-only [Model Context Protocol](https://modelcontextprotocol.io) server for the VidFare price catalog. It speaks Streamable HTTP at `/mcp`, with no authentication. A client such as ChatGPT, Claude, or Cursor can list models, read prices, estimate a clip, and list deals. Every result includes the VidFare source URL, the last-checked date, and a vidfare.com page link. Those vidfare.com links also carry `utm_source=mcp&utm_medium=tool&utm_campaign=vidfare_mcp`.

The Worker is live at `https://mcp.vidfare.com/mcp`. Do not run `wrangler login` or `wrangler deploy` from this repository.

## Data

The Worker fetches only:

- `https://vidfare.com/data/prices.json`
- `https://vidfare.com/deals.json` (the same JSON is also published at `/data/deals.json`)

Responses are cached for 5 minutes. If a fetch fails, or the catalog does not state a price for the request, the tool says so and does not fill in a number.

## Tools

| Tool | Arguments |
| --- | --- |
| `list_models` | none |
| `get_model_prices` | `model` (required), `provider`, `resolution` |
| `estimate_cost` | `model`, `seconds` (required). Optional: `resolution`, `audio` (`with`, `without`, `on`, `off`), `input` (`t2v`, `i2v`, `ref2v`, `v2v`, `extend`, `lip-sync`), `plan`, `provider`, `used` (1–100, default 100), `apply_deals` (default false), `window_seconds` (default 60) |
| `cheapest_options` | `seconds`, `resolution` (both required). Optional: `audio`, `input`, `used`, `apply_deals` |
| `list_deals` | `status`: `live` (default), `upcoming`, `ended`, or `all` |

`estimate_cost` uses the same row filter as the credit calculator (`scripts/variations.py`) and the same plan math as the calculator script: plan price ÷ credits × credits per clip, divided again by the share of credits actually used. API rows are billed seconds times the stated dollars per second. `scripts/test_mcp_parity.py` checks that against the site code.

## Usage counts

Each request writes one Workers Analytics Engine point per JSON-RPC message. A batch of up to 20 messages writes one point each. A longer batch writes a single point with method `batch`. The write is `env.USAGE?.writeDataPoint(...)` with no `await`. A missing binding or a throw is ignored, so logging cannot change the response. Workers Analytics Engine is on the free tier. The dataset is created on the first write. There is no public stats URL.

Points written before this layout used blob1 as the tool name and blob2 as `success` or `error`. New points set blob8 to `v2`. Queries below keep those layouts apart.

`index1` is the JSON-RPC method bucket. It is the sampling key. It is not a person, address, or client name.

| Field | Values |
| --- | --- |
| blob1 `method` | `initialize`, `tools/list`, `tools/call`, `notifications/*`, `other`, or `batch` |
| blob2 `tool` | A known tool name on `tools/call`, otherwise `unknown`. `none` for every other method |
| blob3 `client` | Coarse client bucket, at most 40 characters. See below |
| blob4 `args` | Comma-separated argument names on `tools/call`, such as `model,seconds`. Empty when there are none. Never the values |
| blob5 `http` | `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`, or `other` |
| blob6 `status` | `2xx`, `3xx`, `4xx`, `5xx`, or `other` |
| blob7 `probe` | `1` when the user-agent bucket is a known probe, otherwise `0` |
| double1 | The same probe flag as a number, `1` or `0` |
| blob8 | Layout marker `v2` |

On `initialize`, blob3 comes from `params.clientInfo.name` and a short version when those are present. The name is lowercased, punctuation becomes hyphens, and the label is cut to 40 characters. A recognisable product becomes a fixed bucket such as `ai:cursor`, `ai:claude`, `ai:chatgpt`, or `ai:openai`. An email address, IP, or UUID becomes `other`. Every other request uses the user-agent bucket instead, and the raw user agent is never stored.

User-agent buckets:

- `probe:<name>` for directory and liveness probes: mcpbeat, AgentRank, alalanet, histor, EveryMCP, mcptry, Glama, MCPWatch, and similar checkers (Smithery, PulseMCP, mcp.so, UptimeRobot, Pingdom, Checkly, StatusCake, Better Stack, kube-probe, GoogleHC).
- `ai:<name>` for known AI clients: ChatGPT, OpenAI, Claude, Anthropic, Cursor, Copilot, Perplexity, Windsurf, Gemini, DeepSeek, Mistral, Grok, Cline, Replit, Devin, Aider.
- `generic:<lib>` for node, python-httpx, python-requests, Go-http-client, undici, coda-agent-runtime, Talaria, and curl.
- `other` when none of those match.

`likely_probe` follows the user-agent bucket, including when `initialize` also sent a client name. An empty user agent is `other` and not a probe.

Not stored: IP addresses, the raw user agent, any other header, the request or response body, argument values, the question, session ids, and country. Counts are requests, not unique people, visits, or sponsor impressions. A retry adds another point. Requests with `X-VidFare-Test: 1`, and requests to localhost or `127.0.0.1` (`wrangler dev`), are not written.

`wrangler.jsonc` binds `USAGE` to the dataset `vidfare_mcp_usage`. Deploying that binding uses the existing Worker deploy token (Workers Scripts Edit or Workers Admin, Workers Routes Edit, and Zone Read). It does not need Analytics Read. Reading the counts does. Create a separate token with **Account → Account Analytics → Read**, scoped to the VidFare account. Do not put that token in the repo.

Daily counts for the last 7 days, by method, tool, and client bucket, with probe and non-probe splits. `SUM(_sample_interval)` is the count:

```bash
curl "https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/analytics_engine/sql" \
  --header "Authorization: Bearer <API_TOKEN>" \
  --data "SELECT toDate(timestamp) AS day, blob1 AS method, blob2 AS tool, blob3 AS client, SUM(_sample_interval) AS requests, SUM(_sample_interval * double1) AS probes, SUM(_sample_interval) - SUM(_sample_interval * double1) AS non_probes FROM vidfare_mcp_usage WHERE blob8 = 'v2' AND timestamp > NOW() - INTERVAL '7' DAY GROUP BY day, method, tool, client ORDER BY day, method, tool, client"
```

The same query is what `scripts/mcp_usage.py` runs (default 30 days):

```bash
CLOUDFLARE_ACCOUNT_ID=... CLOUDFLARE_API_TOKEN=... python3 scripts/mcp_usage.py
```

## Local

```bash
cd mcp-server
npm install
npm test
npx wrangler dev
```

`wrangler dev` stays on this machine. It does not deploy.

Cursor can use [`mcp-server/.mcp.json`](.mcp.json). Put the same JSON in a project's `.cursor/mcp.json`. The URL is `https://mcp.vidfare.com/mcp`.

## Registry

[`server.json`](server.json) is the MCP Registry document. The name is `com.vidfare/vidfare`. The remote is `streamable-http` at `https://mcp.vidfare.com/mcp`.

Namespace verification for `com.vidfare` is HTTP. The site serves the published proof record at `https://vidfare.com/.well-known/mcp-registry-auth`. The file is one line, `v=MCPv1; k=ed25519; p=<public key>`. The private key is not in this repo.

The site build copies the file into `dist/.well-known/` and writes `dist/.nojekyll`. `actions/upload-pages-artifact` leaves dot paths out unless `include-hidden-files` is true. Both deploy workflows set that, so the URL answers 200 with no redirect.

## Deploy later

Token, one Cloudflare account (the account that owns vidfare.com) and one zone (`vidfare.com` only):

| Scope | Permission | Why |
| --- | --- | --- |
| Account, Workers product | Workers Admin | The first `wrangler deploy` creates the Worker. A token that can only edit an existing Worker cannot create this one. In the legacy token form this permission is still labeled Account → Workers Scripts → Edit; that legacy permission also creates scripts. If the new role picker is shown, choose Workers Admin on the Workers product, not Editor. |
| Zone `vidfare.com` | Workers Routes → Edit | Attaches the custom domain `mcp.vidfare.com`. Current docs call this Workers Routes Write. |
| Zone `vidfare.com` | Zone → Read | Wrangler looks up the zone id for `vidfare.com`. |

Do not add Workers KV, R2, Tail, Account Settings, DNS, or user membership permissions. The only binding is the Analytics Engine dataset `vidfare_mcp_usage`.

DNS record on `vidfare.com`, created in the dashboard (the token above does not edit DNS):

| Type | Name | Content | Proxy |
| --- | --- | --- | --- |
| AAAA | `mcp` | `100::` | Proxied |

That is the proxied hostname a Worker custom domain uses. `wrangler.jsonc` sets the route to custom domain `mcp.vidfare.com`. After the record exists, `npx wrangler deploy` from this directory publishes the Worker. It still needs `CLOUDFLARE_API_TOKEN` in the environment, not in the repo.
