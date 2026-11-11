# vidfare-json-noindex

Cloudflare Worker that sets `X-Robots-Tag: noindex` on VidFare's JSON data files so Google doesn't index them. The files stay fetchable, and CORS from the origin is left unchanged. Paths that do not end in `.json` pass through untouched.

This only works because the apex `vidfare.com` A records are Cloudflare-proxied (orange cloud, SSL mode Full) in front of GitHub Pages. That proxy was set up on Nov 11, 2026.

Routes, in `wrangler.toml`:

- `vidfare.com/deals.json*`
- `vidfare.com/data/*`

A new JSON path outside those routes needs a new route.

## Deploy

From this directory, with an API token that has Workers Scripts and Workers Routes edit:

```bash
cd json-noindex && CLOUDFLARE_ACCOUNT_ID=<account> npx wrangler@4 deploy
```

## Verify

```bash
curl -I https://vidfare.com/data/prices.json
```

The response includes `x-robots-tag: noindex`.

## Test

```bash
cd json-noindex && npm test
```

The test mocks `fetch`. It checks that `.json` responses get the header and other responses do not.
