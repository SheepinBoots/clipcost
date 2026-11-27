# VidFare sponsor slots

Paid partner copy and the open-spot house ad both live in `data/sponsors.json`.
The build reads that file only; swapping or removing a sponsor is an edit there.

## Records

- `house` — the open-spot ad shown when no paid partner is active. It is labelled
  "This spot is open", links internally to `/advertise/`, and must not use
  `rel="sponsored"`, `target="_blank"`, or an affiliate disclosure.
- `partner` — the paid sponsor record. Leave it empty and `active: false` when
  the spot is open. To place a sponsor later, fill this record and set
  `active` to `true`. `home`, `model:default`, and `guide` already `ref` this
  record, so that is the one edit.
- `home`, `model:default`, and `guide` — placement stubs. They `ref` `partner`
  (or `house`). An unfilled partner ref falls back to `house`.
- `deals` — stays empty unless a sponsor has a real offer. It never falls back
  to the house ad.

A paid `partner` record uses these fields:

```json
{
  "name": "Example Tool",
  "url": "https://example.com/?ref=vidfare",
  "tagline": "A short description the partner approved, kept verbatim.",
  "logo": "/example.png",
  "disclosure": "Affiliate link: VidFare may earn a commission.",
  "cta": "Try Example Tool",
  "active": true
}
```

`logo` is a file under `src/`, copied into `dist/`. Remote `http(s)` logo URLs
are rejected. Optional `label` defaults to "Sponsor". Optional `kind` is
`"house"` for the open-spot ad.

## Placement and tracking

The same component renders on the home page, every model page, every
individual `/guides/<slug>/` page, and the hub pages that use the house
fallback (including `/guides/` and `/deals/` while the deals slot is empty).
The open-spot box links to `/advertise/` and carries
`data-goatcounter-click="sponsor-box-click"`. A paid sponsor's outbound link
carries `data-goatcounter-click="sponsor-out-<slug>"`, where `<slug>` is the
sponsor name. `data-vf-sponsor` is still `home`, `model-<slug>`, `guide-<slug>`,
or the `house-` form of those ids. See `docs/analytics.md`.

Sponsor and house boxes sit outside the price tables and never change price
order. `scripts/test_sponsors.py` checks that.

## Partner lines (affiliates, not the paid Sponsor box)

A compact labelled "Partner" line can appear under the house (or paid) Sponsor
box on every individual model page and on opted-in guides. It is not a price
row, it is not inside a table, and it never changes rankings or price order.
It also never replaces the Sponsor box: leave the paid `partner` record empty
and `active: false` while the spot is open.

Partner lines live in the `partners` list in `data/sponsors.json`. Turning one
off is a single edit: set that record's `active` to `false`. Each record uses:

```json
{
  "id": "pixeldojo",
  "name": "PixelDojo",
  "active": true,
  "url": "https://pixeldojo.ai/?a=pdnpo8l5",
  "label": "Partner",
  "blurb": "PixelDojo is an AI image and video generator.",
  "disclosure": "Affiliate link: VidFare may earn a commission",
  "on_models": true,
  "guides": ["cheapest-ai-video-generator"]
}
```

The PixelDojo blurb is a short factual description taken from the official
title on https://pixeldojo.ai/ (checked 2026-11-17). It makes no price claims.

PixelDojo currently appears on every `/models/<slug>/` page and on these
guides (generators, alternatives, cheapest, or free tools):

- ai-video-generator-apps
- best-ai-video-generator
- cheapest-ai-video-generator
- cheapest-kling-3-0
- cheapest-seedance-2-5
- cheapest-wan-3-0
- free-ai-video-generators
- free-image-to-video-ai
- free-text-to-video-ai
- grok-imagine-video-cost
- higgsfield-alternatives
- higgsfield-vs-kling
- higgsfield-vs-runway
- is-higgsfield-worth-it
- seedance-2-5-unlimited
- wan-3-0-unlimited

It does not appear on the home page, `/deals/`, the `/guides/` or `/models/`
indexes, or pricing/promo/budget guides (fal-ai-pricing, google-flow-credits-calculator,
higgsfield-black-friday, higgsfield-pricing, higgsfield-promo-code, kling-ai-pricing,
runway-pricing, ai-video-project-budget).

The name is the only link. It uses `rel="sponsored nofollow noopener"` and
`data-vf-partner="<id>"`. Clicks are counted as `partner-click/<id>/<page>`,
separate from `sponsor-click` and `outbound-affiliate`. See `docs/analytics.md`.

`scripts/test_partners.py` and `scripts/test_sponsors.py` check placement,
the house ad staying PixelDojo-free, and unchanged price-table order.
