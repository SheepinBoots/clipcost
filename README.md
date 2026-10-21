# ClipCost

AI video cost-per-second tracker. Static site in `dist/`, data in `data/`.
Live at https://sheepinboots.github.io/clipcost/

## Layout
- `data/prices.json` – every price row: model, platform, variant, resolution, $/s, status (verified / estimate / promo), math for credit plans, source URL, checked date, and the `checks` patterns the scraper re-reads.
- `data/deals.json` – live deals and 2025 holiday history. Types: `percent_off`, `plan_sale`, `promo_code`, `bonus_credits`, `unlimited_window`, `api_promo`. A deal is published only when its source is a vendor page or official account.
- `data/deal_candidates.json` – unconfirmed "% off" / sale snippets from the daily pricing-page diff. Not shown on the site.
- `data/deal_snapshots/` – yesterday's offer snippets, so the next run can flag new or removed text.
- `data/changes.json` – the price-change log (feeds /changes/).
- `data/check_report.json` – output of the latest check run.
- `scripts/build_data.py` – SEED ONLY. Rebuilds prices.json from the 2026-10-20 research and wipes later updates. Edit it only to add rows or sources.
- `scripts/update_prices.py` – daily checker. `--apply` updates changed API rows and logs them. Exit 0 includes those applied API changes. Exit 1 = a missing number or a change that was not applied. Exit 2 = fetch error.
- `scripts/render.mjs` – headless Chrome render for JS-only pages (Higgsfield plans).
- `scripts/deals.py` – deal-adjusted $/s, expiry, and the pricing-page snippet diff.
- `scripts/build_site.py` – builds dist/ (home, deals, Black Friday stub, 9 model pages, calculator, changes, newsletter, about, 404, sitemap.xml, robots.txt, deals.json, deals.xml). `SITE_URL` is the GitHub Pages URL; internal links, assets, the sitemap and robots.txt use its `/clipcost` path.
- `scripts/daily.sh` – update_prices --apply, then build_site. This is the daily routine.
- `scripts/check_site.mjs` – crawls http://localhost:8077, checks links and JS errors, saves home.png / home-mobile.png.

## Run locally
    npm install            # puppeteer-core (uses /usr/bin/google-chrome)
    python3 scripts/build_site.py
    cd dist && python3 -m http.server 8077

## Deploy
`.github/workflows/pages.yml` builds `dist/` and deploys it with GitHub Pages on every push to `main`, on manual dispatch, and daily at 13:17 UTC. Manual dispatch and the daily run install the price-check dependencies (Python packages and Chrome for headless-rendered sources), run `update_prices.py --apply`, commit any data changes to `main`, then build and deploy. A push only deploys the data already in the repo. A failed source fetch does not block the deploy. The price check also diffs vendor pricing pages for new "% off" or sale text and writes `data/deal_candidates.json`. That report is not published as a deal. Deals past their end date move to the archive.

## TODO before launch
- NEWSLETTER_ACTION in scripts/build_site.py
- Krea and Magnific affiliate IDs (links are the official pricing pages until then)
- Contact email on /about/
- Manual sources: Kling app subscriptions (kling.ai/pricing)
