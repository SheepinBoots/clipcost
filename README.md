<img src="src/logo-512.png" alt="VidFare" width="96" height="96">

# VidFare

What every AI video second costs, everywhere.

**[https://vidfare.com/](https://vidfare.com/)**

VidFare is an AI-video price tracker for people choosing where to generate AI video. Made by Emmanuel Gonzalez.

## What it tracks

The last full check, on 2026-10-28, lists 184 current prices for 9 models on 10 platforms. That count is the live [llms.txt](https://vidfare.com/llms.txt), built from [`data/prices.json`](data/prices.json).

Models: Wan 3.0 Prime, Wan 3.0, Kling 3.0, Seedance 2.5, Veo 3.1, Gemini Omni Flash 1.1, MiniMax Hailuo / H3, Runway Gen-4.x, and Grok Imagine Video 1.5.

Platforms: Atlas Cloud, fal, Google Gemini API, Higgsfield, Higgsfield API, Kling API, Krea, Magnific, Replicate, and Runway API.

Vendor pricing pages are re-checked daily at 15:17 UTC. When a figure changes, the data in this repo is updated and the site is rebuilt.

- [Deals](https://vidfare.com/deals/) lists live discounts, plan sales, promo codes, and unlimited windows taken from vendor pages and official accounts. The same list is [deals.json](https://vidfare.com/deals.json) ([`data/deals.json`](data/deals.json)).
- The [credit calculator](https://vidfare.com/calculator/) turns a plan's monthly credits into a clip count and a cost per second.
- [llms.txt](https://vidfare.com/llms.txt) is a plain-text summary of the cheapest current price for each model and platform.
- [prices.json](https://vidfare.com/data/prices.json) ([`data/prices.json`](data/prices.json)) is the catalog: model, platform, variant, resolution, dollars per second, status, source, and the date checked. Each row also has a `variation` object: audio (`with`, `without`, or `not stated`), input (`not stated` or a list of `t2v`, `i2v`, `ref2v`, `v2v`, `extend`, `lip-sync`), and duration (min, max, allowed lengths, the clip length a credit price is for, and per-second rates by length). A stated value is copied from the vendor page. If the page does not say it, the field stays not stated, including when a value would only be an inference. The same page is re-checked through the row's needles, including phrase checks. `variation_schema` in the file restates those fields.

## How the numbers work

API rows use the vendor's stated dollars per second. Credit plans are converted from the vendor's plan price, credit allowance, credits per clip, and clip length. That conversion assumes every paid credit is used. When the vendor says "~", "roughly", or "estimated", the row is labelled an estimate. Of the 184 current prices, 116 are vendor-stated, 57 are estimates, and 11 are promos. The method is on the [about page](https://vidfare.com/about/).

## Site address

The site is published at [https://vidfare.com/](https://vidfare.com/). The repository name is still clipcost, from before the VidFare rename.

## Report a wrong price

Open a [GitHub issue](https://github.com/SheepinBoots/clipcost/issues/new).

## Build

`python3 scripts/build_site.py` writes the static site into `dist/`.

Weekly price reports live at `/reports/` and `/reports/YYYY-wNN/`. `REPORTS_ENABLED` in `scripts/build_site.py` is on, so a qualifying week is included in the deployed site. A Friday run (13:30 UTC, with the 15:17 UTC refresh as the backstop) covers the ISO week through that Friday. The week is published only when [`data/price_changes.jsonl`](data/price_changes.jsonl) has at least two qualifying changes. A per-second price change, a promo start, and a promo end each count. A shorter week is skipped and those changes roll forward. The first edition is the week of Oct 26, 2026 (2026-w44) and includes verified changes since the Oct 20 baseline. `python3 scripts/preview_report.py` writes the current eligible report into `preview/`.

## MCP server

A read-only MCP server for ChatGPT, Claude, and Cursor lives in [`mcp-server`](mcp-server/). It is live at `https://mcp.vidfare.com/mcp`. It reads the live [prices.json](https://vidfare.com/data/prices.json) and [deals.json](https://vidfare.com/deals.json), keeps them for five minutes, and does not invent a price. The docs page is [/mcp/](https://vidfare.com/mcp/).

`src/.well-known/mcp-registry-auth` is a placeholder. At publish time, replace that whole line with the `v=MCPv1; k=ed25519; p=...` proof record from `mcp-publisher login http`. The build copies it to `dist/.well-known/mcp-registry-auth` and writes `dist/.nojekyll`. Both Pages workflows set `include-hidden-files: true`, because the artifact upload otherwise drops those dot paths. Registry metadata is [`mcp-server/server.json`](mcp-server/server.json). A Cursor example is [`mcp-server/.mcp.json`](mcp-server/.mcp.json).

## License

MIT (see LICENSE)
