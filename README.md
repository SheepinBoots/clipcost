<img src="src/logo-512.png" alt="VidFare" width="96" height="96">

# VidFare

What every AI video second costs, everywhere.

**[https://sheepinboots.github.io/clipcost/](https://sheepinboots.github.io/clipcost/)**

VidFare is an AI-video price tracker for people choosing where to generate AI video. Made by Emmanuel Gonzalez.

## What it tracks

The last full check, on 2026-10-28, lists 184 current prices for 9 models on 10 platforms. That count is the live [llms.txt](https://sheepinboots.github.io/clipcost/llms.txt), built from [`data/prices.json`](data/prices.json).

Models: Wan 3.0 Prime, Wan 3.0, Kling 3.0, Seedance 2.5, Veo 3.1, Gemini Omni Flash 1.1, MiniMax Hailuo / H3, Runway Gen-4.x, and Grok Imagine Video 1.5.

Platforms: Atlas Cloud, fal, Google Gemini API, Higgsfield, Higgsfield API, Kling API, Krea, Magnific, Replicate, and Runway API.

Vendor pricing pages are re-checked daily at 15:17 UTC. When a figure changes, the data in this repo is updated and the site is rebuilt.

- [Deals](https://sheepinboots.github.io/clipcost/deals/) lists live discounts, plan sales, promo codes, and unlimited windows taken from vendor pages and official accounts. The same list is [deals.json](https://sheepinboots.github.io/clipcost/deals.json) ([`data/deals.json`](data/deals.json)).
- The [credit calculator](https://sheepinboots.github.io/clipcost/calculator/) turns a plan's monthly credits into a clip count and a cost per second.
- [llms.txt](https://sheepinboots.github.io/clipcost/llms.txt) is a plain-text summary of the cheapest current price for each model and platform.
- [prices.json](https://sheepinboots.github.io/clipcost/data/prices.json) ([`data/prices.json`](data/prices.json)) is the catalog: model, platform, variant, resolution, dollars per second, status, source, and the date checked.

## How the numbers work

API rows use the vendor's stated dollars per second. Credit plans are converted from the vendor's plan price, credit allowance, credits per clip, and clip length. That conversion assumes every paid credit is used. When the vendor says "~", "roughly", or "estimated", the row is labelled an estimate. Of the 184 current prices, 116 are vendor-stated, 57 are estimates, and 11 are promos. The method is on the [about page](https://sheepinboots.github.io/clipcost/about/).

## The URL still says clipcost

VidFare was renamed from ClipCost. The repository name and the site URL still use clipcost.

## Report a wrong price

Open a [GitHub issue](https://github.com/SheepinBoots/clipcost/issues/new).

## Build

`python3 scripts/build_site.py` writes the static site into `dist/`.

Weekly price reports live at `/reports/` and `/reports/YYYY-wNN/`. `REPORTS_ENABLED` in `scripts/build_site.py` is on, so a qualifying week is included in the deployed site. A Friday run (13:30 UTC, with the 15:17 UTC refresh as the backstop) covers the ISO week through that Friday. The week is published only when [`data/price_changes.jsonl`](data/price_changes.jsonl) has at least two qualifying changes. A per-second price change, a promo start, and a promo end each count. A shorter week is skipped and those changes roll forward. The first edition is the week of Oct 26, 2026 (2026-w44) and includes verified changes since the Oct 20 baseline. `python3 scripts/preview_report.py` writes the current eligible report into `preview/`.

## License

MIT (see LICENSE)
