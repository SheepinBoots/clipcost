# vidfare-redirects

Cloudflare Worker that sends a permanent 301 from a few typo / alternate paths on VidFare to their canonical URLs. Query strings are kept. Paths that are not in the redirect map pass through to the origin (GitHub Pages).

GitHub Pages cannot issue a 301, so this runs as a Worker on the Cloudflare-proxied apex `vidfare.com` (orange cloud, SSL mode Full), the same setup used by `json-noindex/`.

Current map:

- `/about-us` and `/about-us/` → `https://vidfare.com/about/`

## Routes

The route in `wrangler.toml` is:

- `vidfare.com/about-us*`

Cloudflare matches the entire request URL, including the query string, and route patterns cannot include query parameters. Exact patterns `vidfare.com/about-us` and `vidfare.com/about-us/` would therefore miss `/about-us?utm=…`, which would 404 on GitHub Pages. A trailing `*` is required for those query-string requests to reach this Worker.

That `*` also matches suffixes such as `/about-user` or `/about-us/foo`. The Worker only 301s the two exact pathnames above and passes every other path through, so those suffixes are not redirected. A new redirect needs a new map entry and, if it is not already covered, a new route.

## Deploy

Do not deploy until the pull request is approved and merged.

From this directory, with an API token that has Workers Scripts and Workers Routes edit:

```bash
cd redirects && CLOUDFLARE_ACCOUNT_ID=<account> npx wrangler@4 deploy
```

## Verify

```bash
curl -sI https://vidfare.com/about-us
curl -sI https://vidfare.com/about-us/
curl -sI 'https://vidfare.com/about-us?utm_source=test'
```

Each response should be `301` with `Location: https://vidfare.com/about/` (query string preserved when present). `/about-us/extra` should not redirect.

## Test

```bash
cd redirects && npm test
```

The test mocks `fetch`. It checks the 301s, query-string preservation, and that other paths pass through to the origin.
