# Search Intent Expansion

Use this reference for SEO audits, publish-readiness audits, product-site audits, landing-page audits, sitemap/page-inventory audits, visible-content reviews, search terms, keyword/page fit, new page opportunities, content changes for SEO, focused SEO landing pages, live target-query checks, or broad page strategy. The Search Intent Map is the default keyword/page-fit table for SEO work. Skip it only when the user explicitly asks for technical-only indexing, sitemap, robots, canonical, redirect, or deploy checks, or when there is no page/content surface to assess.

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

## Default Audit Table

Include a compact Search Intent Map for any SEO-facing audit unless there is an explicit technical-only scope. If Search Console or live search data is unavailable, infer conservatively from:

- Page URL slugs, titles, H1s, headings, and meta descriptions.
- Sitemap and navigation labels.
- Visible product/app copy, screenshots, feature names, pricing, FAQ, support, and docs.
- App Store, README, or product documentation when available.

Also include the table in an otherwise technical audit when any of these are true:

- The sitemap or route inventory includes focused landing pages built for named search intents.
- The report checks live search results for target queries.
- The findings mention that focused pages are not yet visible for exact search samples.
- The audit recommends creating, keeping, merging, renaming, or modifying SEO pages.

Keep the table compact. The goal is to verify page-to-intent fit and avoid missing obvious keyword/page mismatches, not to turn every audit into a full keyword-research project.

## Output Table

Use this format for keyword/page strategy:

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
- FAQ entries only when they answer real questions visible on the page. Do not add FAQ structured data for Google SEO benefit; Google no longer shows FAQ rich results in Search.
- Internal links from hub pages using user-facing anchor text.
- Alt text that describes informative product screenshots or proof, not a keyword list; keep decorative or duplicate screenshots empty when nearby accessible/visible context already describes them.
