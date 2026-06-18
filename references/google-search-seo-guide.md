# Google Search SEO Guide

Use this reference when the task needs Google-specific SEO guidance. Prefer the live official docs when the user asks for current or latest SEO rules.

## Official Sources

- SEO Starter Guide: https://developers.google.com/search/docs/fundamentals/seo-starter-guide
- Developer SEO guide: https://developers.google.com/search/docs/fundamentals/get-started-developers
- Helpful content guidance: https://developers.google.com/search/docs/fundamentals/creating-helpful-content
- Sitemaps: https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
- Structured data introduction: https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data
- AI features and your website: https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
- JavaScript SEO basics: https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics
- Mobile-first indexing: https://developers.google.com/search/docs/crawling-indexing/mobile/mobile-sites-mobile-first-indexing
- Core Web Vitals: https://developers.google.com/search/docs/appearance/core-web-vitals
- FAQ rich result removal: https://developers.google.com/search/updates#removing-faq-rich-result

## Working Principles

- SEO helps search engines understand content and helps users decide whether to visit.
- Search improvements are not guaranteed to produce immediate or noticeable ranking changes.
- Google discovers URLs through links, sitemaps, and redirects. Make important pages discoverable through crawlable links.
- Build secure, fast, accessible, mobile-friendly pages. Technical SEO and user experience overlap.
- Use people-first content: useful, original, trustworthy pages for real users before search engines.
- Google says optimization for AI search features remains rooted in core Search quality and ranking systems; do not treat "AI SEO" as a separate trick.
- Google can process JavaScript, but rendered output still matters; check the rendered DOM when important search signals are inserted client-side.
- Google primarily uses the mobile version of content for indexing and ranking, so mobile pages need equivalent important content and metadata.
- Core Web Vitals measure real-world loading, interactivity, and visual stability; good scores support user experience and can matter for Search, but they do not guarantee rankings.

## Crawlability And Links

- Use normal anchor links with `href` attributes for important navigation and internal discovery.
- Link text should describe the destination. Avoid vague labels when a useful phrase fits naturally.
- Avoid relying only on JavaScript-only interactions, forms, or search boxes for discoverability of core pages.
- Ensure important resources are not blocked from Googlebot when they are needed to render or understand the page.
- Check page-level and HTTP header index controls. Important pages should not be blocked by `<meta name="robots">`, Googlebot-specific meta tags, or `X-Robots-Tag` headers.
- For JavaScript-rendered pages, inspect direct URL loads and rendered HTML for route-specific titles, canonicals, links, structured data, and visible copy.

## Canonical URLs And Duplicates

- Pick the preferred URL for each page and make internal links, canonicals, and sitemap URLs agree.
- If the same content exists at multiple URLs, use redirects and/or canonical tags to make the preferred URL explicit.
- Self-referencing canonicals are useful on canonical pages.
- Do not assume Google will choose the same canonical you prefer when signals conflict.

## Sitemaps

- Include canonical URLs in sitemaps, not redirecting or duplicate variants.
- Submit sitemaps in Google Search Console when available.
- Add a `Sitemap: https://example.com/sitemap.xml` hint in `robots.txt` for discoverability.
- A sitemap is a hint, not a guarantee of indexing.
- Standard sitemap limits are 50 MB uncompressed or 50,000 URLs per sitemap; use a sitemap index above that.

## Structured Data

- JSON-LD is usually the easiest format to maintain.
- Structured data should not describe hidden or misleading page-specific content. Entity-level markup should match the public brand, site, app, or organization identity.
- Prefer conservative types that match the page: `Organization`, `WebSite`, `SoftwareApplication`, and `BreadcrumbList`.
- Do not recommend `FAQPage` JSON-LD for Google rich-result visibility. Google no longer shows FAQ rich results in Search as of May 7, 2026, so ordinary sites should not add FAQ structured data just because they have visible FAQ copy.
- Validate with Google's Rich Results Test and inspect Search Console enhancement reports when available.
- Structured data can help Google understand content, but it does not guarantee rich results.

## Audit Prompts To Answer

- Can Google discover every important URL from links or the sitemap?
- Are important URLs free from accidental `noindex` or `X-Robots-Tag` blocks?
- Does each page have one clear search intent and enough useful visible content to satisfy it?
- Are title, description, H1, canonical, internal links, and sitemap URL all aligned?
- Do images and structured data add true context instead of keywords?
- Is the live deployed page the same SEO surface that the source code promises?
