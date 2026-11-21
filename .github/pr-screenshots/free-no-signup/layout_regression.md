# Layout regression

Local build of this branch vs live https://vidfare.com, measured in headless Chrome. Desktop viewport 1280×900. Mobile viewport 390×844. Horizontal overflow is `scrollWidth − innerWidth`.

The new guide is not on the live site. Shared chrome is compared on the free text-to-video guide and the homepage, which use the same header, footer, and type. The only intended chrome difference is one new footer link, “No sign-up”.

| Viewport | Page | Header | H1 | Main width | Footer | Footer last line | Sponsor box | Overflow | Mid-signup, share of page height |
|---|---|---|---|---|---|---|---|---|---|
| desktop | new guide (local) | 59 | 40px | 1180 | 297 | 22 | 115 | 0 | 0.324 |
| desktop | free text to video (local) | 59 | 40px | 1180 | 297 | 22 | 115 | 0 | 0.541 |
| desktop | free text to video (live) | 59 | 40px | 1180 | 275 | 22 | 115 | 0 | 0.543 |
| desktop | home (local) | 59 | 40px | 1180 | 297 | 22 | 115 | 0 | none (home has no mid signup) |
| desktop | home (live) | 59 | 40px | 1180 | 275 | 22 | 115 | 0 | none |
| mobile | new guide (local) | 142 | 26px | 390 | 578 | 43 | 185 | 0 | 0.309 |
| mobile | free text to video (local) | 142 | 26px | 390 | 578 | 43 | 185 | 0 | 0.474 |
| mobile | free text to video (live) | 142 | 26px | 390 | 557 | 43 | 185 | 0 | 0.475 |
| mobile | home (local) | 142 | 26px | 390 | 578 | 43 | 185 | 0 | none |
| mobile | home (live) | 142 | 26px | 390 | 557 | 43 | 185 | 0 | none |

H1 font on every row: `system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`.

Footer height is 22px taller on desktop and 21px taller on mobile on both the local guide and the local homepage. The last footer line is the same height as live. The extra height is the new “No sign-up” footer link wrapping onto another line. Header, type, main width, sponsor-box height, and overflow match the live guide.

The new page’s mid signup sits at 32% of the desktop page height and 31% of the mobile page height, after the no-account table and before the next section. The live free text-to-video guide places its own mid signup later because its first price table is longer. Both use the same inserter.
