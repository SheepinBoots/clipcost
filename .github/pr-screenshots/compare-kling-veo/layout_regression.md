Layout check: live https://vidfare.com vs local build of site/compare-kling-3-0-vs-veo-3-1, Playwright Chrome

| Viewport | Page | Height | Width | Header | Main | Footer | Result |
|---|---|---|---|---|---|---|---|
| desktop | /models/kling-3-0/ | 13661 | 1280 | 59 | 13264 | 275 | same |
| desktop | /models/veo-3-1/ | 10723 → 10756 | 1280 | 59 | 10326 → 10359 | 275 | changed: height, main |
| desktop | /calculator/ | 1827 | 1280 | 59 | 1409 | 275 | same |
| desktop | /compare/kling-3-0-vs-veo-3-1/ (new) | 8545 | 1280 | 59 | 8148 | 275 | no horizontal overflow |
| mobile | /models/kling-3-0/ | 17131 → 17151 | 390 | 142 | 16369 → 16390 | 557 | changed: height, main |
| mobile | /models/veo-3-1/ | 16033 → 16066 | 390 | 142 | 15271 → 15305 | 557 | changed: height, main |
| mobile | /calculator/ | 4407 → 4427 | 390 | 142 | 3625 → 3645 | 557 | changed: height, main |
| mobile | /compare/kling-3-0-vs-veo-3-1/ (new) | 26614 | 390 | 142 | 25853 | 557 | no horizontal overflow |
