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


if __name__ == "__main__":
    unittest.main()
