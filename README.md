# SEO Publish Readiness Skill

A Codex skill for practical SEO publish-readiness checks, Google indexing readiness, and static-site launch verification.

The skill is designed for product sites, app landing pages, documentation sites, and static marketing sites. It turns SEO requests into source-backed and live-site-backed findings instead of generic advice.

Current version: `0.3.2`. See [CHANGELOG.md](CHANGELOG.md) for release notes.

## Installation

Clone this repo into your Codex skills folder:

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/tojileon/seo-publish-readiness-skill.git ~/.codex/skills/seo-publish-readiness
```

Restart Codex or reload skills if your environment requires it.

## Quick Start

Ask Codex:

```text
Use $seo-publish-readiness to review https://example.com for Google SEO readiness.
```

For best results, provide both the repo path and the public URL. The skill is designed to compare source intent against live behavior.

## What It Covers

- Google crawlability and indexing basics
- Canonical URL strategy
- Sitemap and robots.txt checks
- Robots meta tags, Googlebot meta tags, and `X-Robots-Tag` checks
- Titles, descriptions, H1s, headings, image alt text, and internal links
- Search-intent expansion and page/content recommendations
- Structured data review
- Google Search Console verification steps
- Static hosting and CDN publish-readiness checks
- Focused landing pages for distinct search intent
- Safe public documentation that avoids private infrastructure values

## Example Prompts

```text
Use $seo-publish-readiness to review this static app website for Google SEO readiness.
```

```text
Use $seo-publish-readiness to check whether our sitemap, robots.txt, canonical URLs, and focused landing pages are ready before submitting to Google Search Console.
```

```text
Use $seo-publish-readiness to audit this product page and suggest the highest-impact SEO fixes.
```

```text
Use $seo-publish-readiness to find related search intents for this product site and decide which existing pages to improve versus which new pages to create.
```

## Expected Output

A good audit starts with evidence, not generic advice. Expect:

- Findings ordered by severity.
- Evidence from source files, live URLs, headers, rendered HTML, or Search Console when available.
- A compact Search Intent Map when content strategy, keyword/page fit, or new-page recommendations are in scope.
- Concrete fixes and exact verification steps.
- A final status: `DONE`, `DONE_WITH_CONCERNS`, `BLOCKED`, or `NEEDS_CONTEXT`.

## Validation

Run the Codex skill validator from any shell:

```bash
tmp=$(mktemp -d)
python3 -m pip install --quiet --target "$tmp" PyYAML &&
PYTHONPATH="$tmp" python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" ~/.codex/skills/seo-publish-readiness
rc=$?
rm -rf "$tmp"
test "$rc" -eq 0
```

Then run the behavior smoke matrix in [SMOKE_TEST.md](SMOKE_TEST.md). The validator only checks packaging; the smoke matrix checks the skill's crawl-safety, structured-data, Search Intent Map, and Search Console behavior.

## Before Public Release

Before changing this repo's visibility to public:

- Run the skill validator.
- Run the behavior smoke matrix.
- Smoke test it on at least one real static site or product page.
- Search for secrets, tokens, private infrastructure values, dashboard screenshots, and project-specific identifiers.
- Confirm the references point to official Google Search documentation without copying long passages.

## License

MIT
