import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class SkillDocsTests(unittest.TestCase):
    def read(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_version_is_aligned(self) -> None:
        version = self.read("VERSION").strip()
        readme = self.read("README.md")
        changelog = self.read("CHANGELOG.md")

        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        self.assertIn(f"Current version: `{version}`", readme)
        self.assertIn(f"## {version} - ", changelog)

    def test_faqpage_guidance_matches_current_google_search_behavior(self) -> None:
        docs = "\n".join(
            self.read(path)
            for path in [
                "SKILL.md",
                "references/google-search-seo-guide.md",
                "references/search-intent-expansion.md",
                "SMOKE_TEST.md",
                "CHANGELOG.md",
            ]
        )

        stale_patterns = [
            r"well-known authoritative government or health sites",
            r"government or health authority",
            r"restricted FAQ rich-result eligibility",
            r"Google restricts FAQ rich-result visibility",
            r"Google narrowed FAQ rich-result visibility",
        ]
        for pattern in stale_patterns:
            self.assertIsNone(re.search(pattern, docs))

        self.assertIn("Google no longer shows FAQ rich results in Search", docs)
        self.assertIn("must not recommend `FAQPage` JSON-LD for Google rich-result visibility", docs)

    def test_rendered_and_pagespeed_helpers_are_documented(self) -> None:
        docs = "\n".join(
            self.read(path)
            for path in [
                "SKILL.md",
                "README.md",
                "references/advanced-seo-checks.md",
                "references/static-site-seo-checklist.md",
                "SMOKE_TEST.md",
                "CHANGELOG.md",
            ]
        )

        self.assertIn("scripts/rendered_seo_audit.mjs", docs)
        self.assertIn("source-vs-rendered", docs)
        self.assertIn("desktop-vs-mobile", docs)
        self.assertIn("scripts/pagespeed_insights.py", docs)
        self.assertIn("PageSpeed Insights", docs)

    def test_image_alt_guidance_distinguishes_informative_and_decorative_images(self) -> None:
        docs = "\n".join(
            self.read(path)
            for path in [
                "SKILL.md",
                "references/static-site-seo-checklist.md",
                "references/search-intent-expansion.md",
                "SMOKE_TEST.md",
            ]
        )

        self.assertIn("important product-proof images", docs)
        self.assertIn("decorative or duplicate", docs)
        self.assertIn("avoid screen-reader repetition", docs)


if __name__ == "__main__":
    unittest.main()
