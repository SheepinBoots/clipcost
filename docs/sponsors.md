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

The same component renders on the home page, every model page, and every
individual `/guides/<slug>/` page (not the `/guides/` index, and not `/deals/`
unless that slot is filled). Clicks are counted per placement as
`sponsor-click/<slot>/<page>` with `data-vf-sponsor` set to `home`,
`model-<slug>`, `guide-<slug>`, or the `house-` form of those ids. See
`docs/analytics.md`.

Sponsor and house boxes sit outside the price tables and never change price
order. `scripts/test_sponsors.py` checks that.
