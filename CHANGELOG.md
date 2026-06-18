# Changelog

All notable changes to this skill are tracked here.

## 0.4.3 - 2026-06-19

- Expanded `scripts/static_seo_audit.py` to report robots.txt allow/disallow state, recursive sitemap indexes, Open Graph/Twitter metadata, JSON-LD blocks and types, `hreflang`, viewport metadata, same-origin assets, JavaScript app signals, and missing-asset behavior.
- Added standard-library unit tests for helper parsing, sitemap-index recursion, and robots rule handling.
- Clarified that the no-dependency helper inspects HTTP/source HTML and should be paired with rendered desktop/mobile browser checks for JavaScript-heavy pages.

## 0.4.2 - 2026-06-19

- Made the compact Search Intent Map the default keyword/page-fit table for SEO audits, launch-readiness audits, product-site audits, landing-page audits, page-inventory audits, and visible-content reviews.
- Clarified that the Search Intent Map should be skipped only for explicit technical-only checks or when there is no page/content surface to assess.
- Added smoke coverage to catch regressions where a normal SEO readiness audit omits the keyword/page-fit table.

## 0.4.1 - 2026-06-19

- Require a compact Search Intent Map when a technical audit includes focused SEO landing pages or live target-query checks.
- Added smoke coverage for static launch audits that include focused search-intent pages inside the sitemap.

## 0.4.0 - 2026-06-19

- Added `scripts/static_seo_audit.py`, a no-dependency same-origin live-site helper for robots, sitemap, status, content type, canonical, metadata, H1, image alt, internal-link, and missing-URL checks.
- Added advanced guidance for JavaScript-rendered pages, mobile-first indexing, Core Web Vitals, page experience, multilingual or multi-regional sites, ecommerce pages, and local-business pages.
- Updated the static-site checklist to require representative template coverage and route-specific metadata checks for static app hosts.
- Expanded the core workflow so broad audits include rendered/mobile/page-experience risks without forcing content strategy into technical-only reviews.
- Added smoke-test scenarios for the helper script, rendered/mobile checks, and vertical-specific structured data.

## 0.3.2 - 2026-06-18

- Clarified safe URL traversal: same-origin URLs from source, sitemaps, robots, redirects, canonicals, and normal links may be crawled; cross-origin URLs need user approval.
- Removed `FAQPage` from generic structured-data recommendations and documented Google's restricted FAQ rich-result eligibility.
- Scoped the Search Intent Map to content strategy, keyword/page-fit, and broad page-strategy work instead of technical-only publish-readiness checks.
- Replaced product-specific examples with neutral examples suitable for public release.
- Added a behavior smoke-test matrix for crawl safety, structured data, Search Intent Map scope, and Search Console handoff behavior.

## 0.3.1 - 2026-06-18

- Made the Search Intent Map table required for full publish-readiness audits, not only explicit search-term or page-strategy requests.
- Clarified that site-derived or inferred search-intent rows should still be shown when Search Console or live search data is unavailable.

## 0.3.0 - 2026-06-18

- Added an explicit search-intent expansion workflow for related search terms, existing-page modifications, and new focused-page recommendations.
- Added `references/search-intent-expansion.md` with evidence order, intent clustering, page decision rules, and output-table format.

## 0.2.1 - 2026-06-18

- Added explicit static-hosting checks for nonexistent pages and assets returning `403` XML instead of clean `404` or `410` responses.
- Added missing-key behavior to the common findings list after live smoke testing.

## 0.2.0 - 2026-06-18

- Renamed the skill from `seo-audit` to `seo-publish-readiness` to make the public package more distinctive and better aligned with static/product-site launch checks.
- Updated install path, default prompt, UI display metadata, and README examples for `$seo-publish-readiness`.

## 0.1.3 - 2026-06-18

- Made Google Search Console sitemap submission an explicit audit output when a live sitemap exists and submission is not already confirmed.
- Added guidance to leave the exact sitemap URL and success checks when Search Console access is unavailable.

## 0.1.2 - 2026-06-18

- Moved installation before quick start so first-time users do not hit the example before setup instructions.
- Split validator instructions into a reusable validation section and kept the public-release checklist focused on release gates.

## 0.1.1 - 2026-06-18

- Added operating principles adapted from gstack: verify real surfaces, search official sources first, audit complete lakes, and keep user decisions explicit.
- Added untrusted page-content guidance for live-site audits.
- Added completion status labels for final SEO audit reports.
- Improved README scanability with a quick start and expected output section.

## 0.1.0 - 2026-06-18

- Added the initial `seo-audit` Codex skill.
- Added Google Search SEO guidance reference.
- Added static-site SEO and publish-readiness checklist.
- Added checks for crawlability, canonical URLs, sitemap and robots setup, metadata, structured data, internal links, alt text, Search Console, and live hosting behavior.
- Added privacy guardrails for public examples, screenshots, infrastructure values, and credentials.
- Added explicit `noindex`, Googlebot meta tag, and `X-Robots-Tag` checks.
