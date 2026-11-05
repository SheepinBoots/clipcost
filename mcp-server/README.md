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

Namespace verification for `com.vidfare` is HTTP. The site serves `https://vidfare.com/.well-known/mcp-registry-auth`. The committed file is a placeholder:

```text
v=MCPv1; k=ed25519; p=PLACEHOLDER_REPLACE_AT_PUBLISH
```

Replace that entire line before publishing. `mcp-publisher login http` prints the real proof record (`v=MCPv1; k=ed25519; p=<public key>`) from the key you generate at publish time. The file body is that one line. Do not leave the placeholder, and do not add a comment: the registry reads the body. The private key stays with the publisher and is not committed.

The site build copies the file into `dist/.well-known/` and writes `dist/.nojekyll`. `actions/upload-pages-artifact` leaves dot paths out unless `include-hidden-files` is true. Both deploy workflows set that. The published file is `https://vidfare.com/.well-known/mcp-registry-auth`, with status 200 and no redirect.

## Deploy later

Token, one Cloudflare account (the account that owns vidfare.com) and one zone (`vidfare.com` only):

| Scope | Permission | Why |
| --- | --- | --- |
| Account, Workers product | Workers Admin | The first `wrangler deploy` creates the Worker. A token that can only edit an existing Worker cannot create this one. In the legacy token form this permission is still labeled Account → Workers Scripts → Edit; that legacy permission also creates scripts. If the new role picker is shown, choose Workers Admin on the Workers product, not Editor. |
| Zone `vidfare.com` | Workers Routes → Edit | Attaches the custom domain `mcp.vidfare.com`. Current docs call this Workers Routes Write. |
| Zone `vidfare.com` | Zone → Read | Wrangler looks up the zone id for `vidfare.com`. |

Do not add Workers KV, R2, Tail, Account Settings, DNS, or user membership permissions. The Worker has no bindings.

DNS record on `vidfare.com`, created in the dashboard (the token above does not edit DNS):

| Type | Name | Content | Proxy |
| --- | --- | --- | --- |
| AAAA | `mcp` | `100::` | Proxied |

That is the proxied hostname a Worker custom domain uses. `wrangler.jsonc` sets the route to custom domain `mcp.vidfare.com`. After the record exists, `npx wrangler deploy` from this directory publishes the Worker. It still needs `CLOUDFLARE_API_TOKEN` in the environment, not in the repo.
