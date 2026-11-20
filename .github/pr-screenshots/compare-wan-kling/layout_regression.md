Layout check: live https://vidfare.com vs local build of site/compare-wan-kling-v2 (rebased on main), Playwright Chrome

| Viewport | Page | height | width | header | main | footer | lead | same | headline | platforms | Result |
|---|---|---|---|---|---|---|---|---|---|---|
| desktop | /compare/kling-3-0-vs-seedance-2-5/ | 5008 → 5272 | 1280 | 59 | 4611 → 4875 | 275 | 195 → 279 | 50 | 455 → 634 | 2801 | changed: height, main, lead, headline |
| desktop | /compare/wan-3-0-vs-kling-3-0/ (local only, not live) | 8788 | 1280 | 59 | 8392 | 275 | 363 | 174 | 1077 | 5627 | no horizontal overflow |
| mobile | /compare/kling-3-0-vs-seedance-2-5/ | 13069 → 13461 | 390 | 142 | 12307 → 12700 | 557 | 418 → 586 | 149 | 1519 → 1743 | 8189 | changed: height, main, lead, headline |
| mobile | /compare/wan-3-0-vs-kling-3-0/ (local only, not live) | 26177 | 390 | 142 | 25416 | 557 | 753 | 570 | 2622 | 19392 | no horizontal overflow |
