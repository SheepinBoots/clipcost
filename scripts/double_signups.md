# Double signups: the 45 pages, and one proposed fix

On today's `origin/main` (3ae251d), 45 pages render both the mid-page Kit signup (`#newsletter-inline`, event `newsletter-signup-inline`) and the end-of-page signup (`#newsletter`, event `newsletter-signup`). Both are the same form (Kit 10170819).

This file is a review note. It is not published on the site. Nothing in this PR changes the layout.

## The 45 pages

### Data pages (11)

- /compare/kling-3-0-vs-seedance-2-5/
- /compare/kling-3-0-vs-veo-3-1/
- /compare/seedance-2-5-vs-veo-3-1/
- /compare/wan-3-0-vs-kling-3-0/
- /compare/wan-3-0-vs-wan-3-0-prime/
- /cost/10-second/
- /cost/1080p/
- /cost/30-second/
- /platforms/krea/
- /platforms/magnific/
- /price-index/

Mid-box position on these pages is about 14–46% of the main column, with a full section between it and the end box.

### Model pages (9)

- /models/gemini-omni-flash/
- /models/grok-imagine/
- /models/kling-3-0/
- /models/minimax-hailuo/
- /models/runway-gen-4/
- /models/seedance-2-5/
- /models/veo-3-1/
- /models/wan-3-0/
- /models/wan-3-0-prime/

On current main the mid box sits above the price table. If [PR #90](https://github.com/SheepinBoots/clipcost/pull/90) is merged, it moves to just below the table, so the mid and end boxes would be only a short link line apart.

### Guides (25)

Mid-box position as a percentage of the main column (today's build):

| Page | Mid box at |
| --- | ---: |
| /guides/is-higgsfield-worth-it/ | 3.8% |
| /guides/ai-video-project-budget/ | 6.3% |
| /guides/higgsfield-pricing/ | 7.4% |
| /guides/kling-ai-pricing/ | 10.4% |
| /guides/runway-pricing/ | 11.9% |
| /guides/grok-imagine-video-cost/ | 14.9% |
| /guides/fal-ai-pricing/ | 16.6% |
| /guides/seedance-2-5-unlimited/ | 19.0% |
| /guides/google-flow-credits-calculator/ | 22.7% |
| /guides/free-ai-video-generator-no-sign-up/ | 23.6% |
| /guides/cheapest-kling-3-0/ | 23.6% |
| /guides/cheapest-seedance-2-5/ | 25.5% |
| /guides/higgsfield-alternatives/ | 26.9% |
| /guides/cheapest-wan-3-0/ | 29.1% |
| /guides/higgsfield-vs-runway/ | 31.3% |
| /guides/higgsfield-vs-kling/ | 31.4% |
| /guides/higgsfield-promo-code/ | 40.2% |
| /guides/higgsfield-black-friday/ | 42.9% |
| /guides/free-text-to-video-ai/ | 47.6% |
| /guides/ai-video-generator-apps/ | 52.2% |
| /guides/best-ai-video-generator/ | 56.5% |
| /guides/free-image-to-video-ai/ | 58.7% |
| /guides/cheapest-ai-video-generator/ | 58.6% |
| /guides/free-ai-video-generators/ | 61.3% |
| /guides/wan-3-0-unlimited/ | 68.2% |

On the short guides at the top of that list, the mid box appears almost immediately, so the two signups are close together.

## Pages that do not have two signups

End signup only: `/`, `/deals/`, `/deals/black-friday/`, `/calculator/`, `/guides/`, `/changes/`, `/newsletter/`.

No signup: `/about/`, `/advertise/`, `/contact/`, `/contact-us/`, `/data/`, `/models/`, `/mcp/`, and the weekly reports (until [PR #92](https://github.com/SheepinBoots/clipcost/pull/92) adds one end signup there).

## Proposed one fix

Keep the end-of-page signup on every page that already has one.

Keep the mid-page signup only when at least one full section (a heading plus a table or a comparable block) sits between the two boxes. Otherwise omit the mid box.

That is one check in the mid-signup inserter (`insert_guide_inline_signup` and the data-page / model-page placements), not 45 hand edits. On today's build it would drop the mid box on the short guides where it lands very early. If PR #90 is merged, the same rule would also drop the mid box on the 9 model pages.

This PR does not apply that rule. It is here so the 45 pages and the proposed fix can be reviewed together.
