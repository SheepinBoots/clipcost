# VidFare analytics (GoatCounter, cookie-free)

VidFare counts visits with the existing GoatCounter snippet
(`https://gc.zgo.at/count.js`, site `vidfare.goatcounter.com`, dashboard in
Pacific time). On top of page views, one small static script,
`/vf-events.js` (source: `src/vf-events.js`), sends a few **events** with
`goatcounter.count({path, title, event: true})`.

## Privacy guarantees

- No cookies, no `localStorage`, `sessionStorage` or IndexedDB, no browser
  fingerprinting code of our own. `test_analytics.py` fails if the script uses any of them.
- No Google Analytics or other trackers. No demographics. No consent banner is
  needed because nothing is stored on the visitor's device.
- Event names contain only page slugs, vendor slugs, slot ids and campaign
  slugs. Never an email address or anything typed into a form. The newsletter
  event fires on submit and does not read the email field.
- If count.js is blocked or has not loaded, the script does nothing. Links and
  forms work exactly as before. The script never calls `preventDefault`;
  count.js sends with `navigator.sendBeacon`, so outbound clicks are not delayed.

## Events

`<page>` is the page slug: `/` → `home`, `/models/kling-3-0/` → `models-kling-3-0`,
`/guides/seedance-2-5-unlimited/` → `guides-seedance-2-5-unlimited`, the 404 page → `404`.
The build writes it on the script tag (`data-vf-page`).

| Event path | Trigger |
|---|---|
| `newsletter-signup/<page>` | The end-of-page Kit newsletter form (`data-vf-event="newsletter-signup"`) is submitted on `<page>`. This counts submit attempts that pass the browser's email check. It does not count confirmed subscribers; Kit's double opt-in still applies. |
| `newsletter-signup-inline/<page>` | The compact mid-page Kit form (`data-vf-event="newsletter-signup-inline"`) is submitted on `<page>`. On guides it sits after the first price table; on model pages after the live deals section (before the guide links and the price table); on the home page before All prices; on /compare/ pages after the cheapest-price section; on /cost/ pages after the first ranking section; on /price-index/ after the chart. Same form and confirmation flow; a separate event so the two boxes can be compared. The build writes this attribute in the markup so `annotate()` does not relabel it as `newsletter-signup`. |
| `outbound/<vendor>/<page>` | Click (or middle-click) on a link to a vendor or deal page that is not an affiliate link. |
| `outbound-affiliate/<vendor>/<page>` | Same, but the link is an affiliate link: `rel="sponsored"` (outside a sponsor slot) or a referral `fpr=` parameter. Today that is the Higgsfield referral links. |
| `sponsor-click/<slot>/<page>` | Click inside a sponsor slot (`aside[data-sponsor]`). Slot ids: `home`, `deals`, `model-<slug>`, `guide-<slug>` for a paid partner, and `house-home`, `house-model-<slug>`, `house-guide-<slug>` for the open-spot house ad. Clicks are counted by `/vf-events.js` with `goatcounter.count({path, title, event: true})`, using the link's `data-vf-sponsor` attribute. A house ad links to `/advertise/` but is still counted as `sponsor-click/house-...` when that attribute is present, so placements stay comparable. Other `/advertise/` links (footer, compact placeholders) stay `advertise-cta`. Do not also add GoatCounter's `data-goatcounter-click` attribute; that would double-count the same click. |
| `partner-click/<partner>/<page>` | Click on a labelled Partner line (`aside.partner-line[data-partner]`, link `data-vf-partner`). Today that is PixelDojo (`partner-click/pixeldojo/<page>`). These links also have `rel="sponsored"`, but `/vf-events.js` counts them as `partner-click` and returns before `outbound-affiliate` or `sponsor-click`, so PixelDojo clicks stay separate from the paid Sponsor box and from other affiliate links. The build writes `data-vf-partner` in the markup; `annotate()` leaves those tags alone. |
| `advertise-cta/<cta>/<page>` | Click on a link to `/advertise/` or on the sponsorship email. `<cta>` is `footer-link`, `inline-link`, `email` (the email on /advertise/), `sponsorship-email` (on /contact/), or `sponsor-slot-<slot>` (an empty "sponsor this spot" placeholder). |
| `campaign/<source>/<medium>/<campaign>` | A page is opened with `utm_campaign` (or `campaign`) in the URL. Keeps `utm_medium`, which GoatCounter does not store. Sent again if the same tagged URL is reloaded. |

The event **title** is readable text with more detail, for example
`Affiliate click: higgsfield (kling-3-0) on models-kling-3-0`. When the
clicked link sits in a model's price row or on a model page, the model slug is in the title.

### How links are classified

- `scripts/build_site.py` calls `scripts/analytics.py` `annotate()` on every page it
  writes. It only adds attributes (layout is unchanged):
  `data-vf-vendor`, `data-vf-model` (model pages), `data-vf-affiliate="1"`,
  `data-vf-sponsor`, `data-vf-partner` (written by the partner-line markup, not by `annotate()`), `data-vf-cta`, and `data-vf-event` on newsletter forms (`newsletter-signup` on the end-of-page box, added by `annotate()`; `newsletter-signup-inline` on the compact mid-guide box, written in the markup).
- Vendor slugs come from the hostnames in `data/prices.json` (`platform`) and
  `data/deals.json` (`vendor`), for example `higgsfield`, `higgsfield-api`,
  `krea`, `magnific`, `fal`, `runway`, `runway-api`, `kling-api`, `replicate`,
  `atlas-cloud`, `google-gemini-api`. The same map is built into `/vf-events.js`.
- Links the price table renders in the browser have no build attributes, so
  the script classifies them at click time with the same host map and the
  same affiliate rule. Any other external link (a directory badge, docs) is
  counted as `outbound/<hostname-slug>/<page>`, for example `outbound/twelve-tools/home`.

## Where to read the numbers in GoatCounter

Sign in at <https://vidfare.goatcounter.com> (box browser, owner account).

- **Dashboard → Pages widget.** Events are listed in the same list as page
  paths; event paths are the ones without a leading `/`. Type a prefix in the path filter box to narrow them, for example:
  - `newsletter-signup` → end-of-page sign-up submits; the part after `/` is the page.
  - `newsletter-signup-inline` → compact mid-guide sign-up submits, so the two boxes can be compared after a week.
  - `outbound-affiliate` → affiliate clicks by vendor and page.
  - `outbound/` → non-affiliate vendor and deal clicks.
  - `sponsor-click` and `advertise-cta` → sponsor and /advertise/ interest.
  - `partner-click` → labelled Partner line clicks, for example `partner-click/pixeldojo/models-wan-3-0`.
  - `campaign/` → landings per source/medium/campaign.
  Click a row to see its title and its chart over the selected date range.
- **Campaigns widget.** GoatCounter reads `utm_campaign` (or `campaign`) from
  the page-view URL and lists each campaign name here automatically. No setup is needed.
- **Referrers widget.** `utm_source` (or `ref` / `src` / `source`) is used as the
  referrer, so `reddit`, `newsletter`, `directory` and `x` show up as sources.
- **Totals / Visitors.** GoatCounter counts unique visitors with a short-lived,
  server-side session hash, not a cookie. A double click in quick succession
  may count once.
- **Export.** Settings → Export gives a CSV of all hits, events included, for counting outside the dashboard.

GoatCounter ignores hits from `localhost`/`127.0.0.1`, so testing a local build
does not pollute the numbers.

## UTM convention

Every link we post off-site to VidFare gets three parameters:

| Channel | `utm_source` | `utm_medium` |
|---|---|---|
| Reddit posts and comments | `reddit` | `social` |
| X posts | `x` | `social` |
| VidFare Weekly newsletter | `newsletter` | `email` |
| Directory and awesome-list listings | `directory` | `referral` |

`utm_campaign` is a slug (lowercase letters, digits, `-`) naming the post, issue
or listing, for example `cheapest-kling-nov26`, `weekly-2026-11-13`, `dang-ai`.
Optional `utm_content` tells two links in the same post apart.

Use the helper instead of typing parameters:

```
python3 scripts/utm.py https://vidfare.com/deals/ --source reddit --medium social --campaign "Cheapest Kling Nov26"
# https://vidfare.com/deals/?utm_source=reddit&utm_medium=social&utm_campaign=cheapest-kling-nov26

python3 scripts/utm.py https://vidfare.com/ --source newsletter --campaign weekly-2026-11-13
# https://vidfare.com/?utm_source=newsletter&utm_medium=email&utm_campaign=weekly-2026-11-13

python3 scripts/utm.py https://vidfare.com/models/kling-3-0/ --source directory --campaign dang-ai --content listing
```

It rejects unknown sources, a medium that does not match the source, an
empty campaign and non-vidfare.com URLs (`--any-host` overrides the last one).
Existing `utm_*`, `ref` and `campaign` parameters are replaced. In Python:
`from utm import utm_url`.

### How a campaign is recorded

1. count.js sends the page view with the page's query string (`q = location.search`).
   GoatCounter takes `utm_campaign` into the **Campaigns** widget and `utm_source`
   into **Referrers**. The page path itself stays clean because count.js uses the
   canonical URL.
2. `vf-events.js` also sends `campaign/<source>/<medium>/<campaign>` once count.js
   is ready (it retries for up to 10 seconds), so the medium is recorded and campaigns
   can be filtered in the Pages widget like any other event.

## Tests

`python3 scripts/test_analytics.py` (after `python3 scripts/build_site.py`) checks
that every counted page loads `/vf-events.js`, that vendor, affiliate, sponsor, partner,
/advertise/ links and newsletter forms carry their attributes, that the script
stores nothing in the browser, and the `utm.py` output.
