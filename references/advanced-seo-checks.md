# Advanced SEO Checks

Use this reference when the site is JavaScript-heavy, mobile-sensitive, multilingual, multi-regional, ecommerce, local-business, or when a broad audit needs page-experience coverage.

## Official Sources

- JavaScript SEO basics: https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics
- Mobile-first indexing: https://developers.google.com/search/docs/crawling-indexing/mobile/mobile-sites-mobile-first-indexing
- Core Web Vitals: https://developers.google.com/search/docs/appearance/core-web-vitals
- Page experience: https://developers.google.com/search/docs/appearance/page-experience
- Localized versions and `hreflang`: https://developers.google.com/search/docs/specialty/international/localized-versions
- Multi-regional sites: https://developers.google.com/search/docs/specialty/international/managing-multi-regional-sites
- Product structured data: https://developers.google.com/search/docs/appearance/structured-data/product
- Merchant listing structured data: https://developers.google.com/search/docs/appearance/structured-data/merchant-listing
- Local business structured data: https://developers.google.com/search/docs/appearance/structured-data/local-business

## Rendered DOM And JavaScript

- Compare server HTML with rendered HTML when the site uses React, Vue, Svelte, client-side routing, personalization, or delayed content loading.
- Important content, internal links, title, meta description, canonical URL, robots directives, and structured data should be visible in the HTML Google can render.
- Do not rely on buttons, form submissions, search boxes, or JavaScript-only click handlers for discovery of core indexable pages.
- If source and rendered DOM differ, cite both surfaces in findings and mark the live indexability risk explicitly.
- For client-side apps, check route-specific metadata on direct deep links, not just after in-app navigation.

## Mobile-First Indexing

- Check the mobile viewport, not only desktop screenshots.
- Mobile content should include the same primary text, links, media, structured data, robots directives, titles, descriptions, and canonicals expected for indexing.
- If separate mobile URLs exist, verify redirects, `rel=canonical`, `rel=alternate`, and sitemap entries across the desktop/mobile pair.
- Avoid URL fragments for core mobile pages because fragment-only states are not reliable indexable URLs.

## Page Experience And Core Web Vitals

- Treat Core Web Vitals as a user-experience and launch-readiness input, not as a guaranteed ranking lever.
- Check LCP, INP, and CLS for representative page templates when tooling is available through Lighthouse, PageSpeed Insights, Chrome UX Report, Search Console, or local browser traces.
- Flag SEO-relevant causes rather than just scores: oversized hero images, render-blocking assets, client-only content delays, layout shifts around media or ads, slow third-party scripts, and heavy hydration.
- Also check HTTPS, mobile usability, intrusive interstitials, and obviously broken rendering.
- If real-user data is unavailable, label lab measurements as lab data and avoid overclaiming.

## International And Multi-Regional Sites

- Use `hreflang` only for real localized or regional alternatives, not for generic keyword variants.
- Each alternate page should return `2xx`, be indexable, and reference the full alternate cluster, including itself.
- Canonicals should usually point to the page's own localized URL, not collapse all languages to one canonical.
- Include user-visible links to switch language or region so users can recover from imperfect geotargeting.
- In sitemaps, keep canonical URLs and `hreflang` alternates consistent with page tags.

## Ecommerce And Transactional Pages

- Product, merchant listing, offer, review, shipping, and return-policy markup should match visible page content and Google Search documentation for that rich-result type.
- Verify product pages expose useful visible details: name, image, price or pricing model, availability, shipping/returns when relevant, variants, support, and trust signals.
- Avoid marking up aggregate ratings, reviews, pricing, or availability that are not visible or are not about the specific product on the page.
- Check faceted navigation, sort parameters, tracking parameters, and pagination for duplicate/crawl-trap behavior before recommending new indexable URLs.

## Local Business And Location Pages

- Local pages need real location-specific usefulness: address/service area, contact path, hours, services, photos, policies, and proof that the business serves that area.
- Do not create doorway-style city pages that swap place names without distinct visible value.
- LocalBusiness markup must match visible public business identity and should not invent attributes.
