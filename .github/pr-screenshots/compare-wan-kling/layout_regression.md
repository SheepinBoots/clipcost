Layout regression: live https://vidfare.com (main 442f548) vs local build of branch site/compare-wan-kling, Playwright Chrome

| Viewport | Page | Height live → local | Width | Header | Main | Footer | Footer last line | Result |
|---|---|---|---|---|---|---|---|---|
| desktop | /models/kling-3-0/ | 13661 | 1280 | 59 | 13264 | 275 | 22 | same |
| desktop | /models/wan-3-0/ | 8962 → 8995 | 1280 | 59 | 8565 → 8598 | 275 | 22 | changed: height, main |
| desktop | /calculator/ | 1827 | 1280 | 59 | 1409 | 275 | 22 | same |
| mobile | /models/kling-3-0/ | 16723 → 16744 | 390 | 142 | 15962 → 15982 | 557 | 43 | changed: height, main |
| mobile | /models/wan-3-0/ | 14649 → 14682 | 390 | 142 | 13888 → 13921 | 557 | 43 | changed: height, main |
| mobile | /calculator/ | 4387 → 4407 | 390 | 142 | 3604 → 3625 | 557 | 43 | changed: height, main |
