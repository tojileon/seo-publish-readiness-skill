# Search Intent Expansion

Use this reference when the user asks for search terms, keyword/page fit, new page opportunities, content changes for SEO, or broad page strategy. Do not force this workflow into narrow technical indexing, sitemap, canonical, or deploy-readiness checks.

## Evidence Order

Prefer evidence that reflects the user's actual site and audience:

1. Google Search Console queries, pages, impressions, clicks, and indexing state, when accessible.
2. The live site: sitemap, headings, titles, internal links, visible copy, and structured data.
3. Product truth sources: app store listing, docs, README, pricing, privacy, support, and feature pages.
4. Live web search results when current search context matters.
5. Clearly labeled inference from product positioning when direct query data is unavailable.

Do not invent search volume, competition, CPC, or ranking certainty. If a tool or search result claims a number, cite it and treat it as directional.

## Workflow

1. Inventory the current pages and their intended search intents.
2. Extract seed terms from the product category, user jobs, features, audience segments, and problem language.
3. Expand terms with Search Console data or live search when available.
4. Cluster terms by intent:
   - Same job, same audience, same page can satisfy it: modify an existing page.
   - Same broad job but different language: fold into headings, FAQ, examples, internal anchors, or supporting copy.
   - Different user, problem, or decision stage: consider a focused page.
   - Keyword-only variation with no new user need: reject it.
5. Map each intent to one canonical page.
6. Recommend content changes with proof the product can actually support.

## Output Table

Include this table for content strategy, search-term, keyword/page-fit, new-page, and broad page-strategy work. Skip it for technical-only publish-readiness checks unless content fit is directly tied to a finding. Use this format for keyword/page strategy:

| Search intent | Evidence | Existing page fit | Recommendation | Confidence |
|---|---|---|---|---|
| invoice generator | site copy + sitemap + live SERP | strong page exists | Improve existing page title/H1/examples; do not create duplicate | High |
| free invoice template | related user language | partial fit to invoice page | Fold phrase naturally into invoice page copy or examples | Medium |
| recurring invoice software | distinct workflow and decision stage | focused page exists or justified | Create or strengthen a dedicated page only if copy can address recurring billing specifically | Medium |

## Page Decision Rules

- Improve existing pages when the intent can be satisfied by a current canonical page.
- Create a new page only when it has a distinct audience, job-to-be-done, proof points, and internal-link path.
- Reject pages that only swap synonyms into the same template.
- Avoid medical, financial, legal, or safety claims unless the site can support them with visible facts and appropriate disclaimers.
- Keep titles, H1s, internal links, canonicals, and sitemap entries aligned with the chosen page.

## Content Modification Ideas

Useful existing-page changes include:

- Clearer title and meta description for the page's primary intent.
- H1 and H2 language that mirrors real user jobs without stuffing keywords.
- Examples and use cases that prove the product fits the search intent.
- FAQ entries only when they answer real questions visible on the page. Do not add FAQ structured data by default; Google restricts FAQ rich-result visibility to a narrow set of authoritative government and health sites.
- Internal links from hub pages using user-facing anchor text.
- Alt text that describes product screenshots or proof, not a keyword list.
