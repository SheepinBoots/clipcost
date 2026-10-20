# ClipCost

AI video cost-per-second tracker. Static site in `dist/`, data in `data/`.
Live at https://sheepinboots.github.io/clipcost/

## Layout
- `data/prices.json` – every price row: model, platform, variant, resolution, $/s, status (verified / estimate / promo), math for credit plans, source URL, checked date, and the `checks` patterns the scraper re-reads.
- `data/changes.json` – the price-change log (feeds /changes/).
- `data/check_report.json` – output of the latest check run.
- `scripts/build_data.py` – SEED ONLY. Rebuilds prices.json from the 2026-10-20 research and wipes later updates. Edit it only to add rows or sources.
- `scripts/update_prices.py` – daily checker. `--apply` updates changed API rows and logs them. Exit 1 = review needed, exit 2 = fetch error.
- `scripts/render.mjs` – headless Chrome render for JS-only pages (Higgsfield plans).
- `scripts/build_site.py` – builds dist/ (home, 9 model pages, calculator, changes, newsletter, about, 404, sitemap.xml, robots.txt). `SITE_URL` is the GitHub Pages URL; internal links, assets, the sitemap and robots.txt use its `/clipcost` path.
- `scripts/daily.sh` – update_prices --apply, then build_site. This is the daily routine.
- `scripts/check_site.mjs` – crawls http://localhost:8077, checks links and JS errors, saves home.png / home-mobile.png.

## Run locally
    npm install            # puppeteer-core (uses /usr/bin/google-chrome)
    python3 scripts/build_site.py
    cd dist && python3 -m http.server 8077

## Deploy
`.github/workflows/pages.yml` builds `dist/` and deploys it with GitHub Pages on every push to `main`, on manual dispatch, and daily at 14:00 UTC. The daily run installs the price-check dependencies (Python packages and Chrome for headless-rendered sources), runs `update_prices.py --apply`, commits any data changes to `main`, then builds and deploys. A failed source fetch does not block the deploy.

## TODO before launch
- NEWSLETTER_ACTION in scripts/build_site.py
- AFF dict in build_site.py (affiliate IDs: Higgsfield, Krea, Magnific)
- Contact email on /about/
- Manual sources: Kling app subscriptions (kling.ai/pricing)
