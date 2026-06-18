import importlib.util
import pathlib
import sys
import unittest


SCRIPT_PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "static_seo_audit.py"
SPEC = importlib.util.spec_from_file_location("static_seo_audit", SCRIPT_PATH)
static_seo_audit = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = static_seo_audit
SPEC.loader.exec_module(static_seo_audit)


class StaticSeoAuditTests(unittest.TestCase):
    def test_parser_extracts_search_and_share_signals(self) -> None:
        html = """
        <!doctype html>
        <html>
          <head>
            <title>Test Product</title>
            <meta name="description" content="A useful product page.">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta property="og:title" content="Test Product">
            <meta property="og:url" content="/product">
            <meta name="twitter:card" content="summary_large_image">
            <link rel="canonical" href="/product">
            <link rel="alternate" hreflang="en-au" href="/au/product">
            <link rel="stylesheet" href="/assets/site.css">
            <script type="application/ld+json">
              {"@context":"https://schema.org","@type":"SoftwareApplication","name":"Test Product"}
            </script>
          </head>
          <body>
            <div id="root"></div>
            <h1>Test Product</h1>
            <img src="/assets/screenshot.png" alt="Product screenshot">
            <a href="/pricing">Pricing</a>
          </body>
        </html>
        """
        parser = static_seo_audit.SEOHTMLParser("https://example.com/product")
        parser.feed(html)
        json_ld_types, invalid = static_seo_audit.extract_json_ld_types(parser.json_ld_blocks)

        self.assertEqual(parser.title, "Test Product")
        self.assertEqual(parser.meta_description, "A useful product page.")
        self.assertEqual(parser.viewport, "width=device-width, initial-scale=1")
        self.assertEqual(parser.canonical, "https://example.com/product")
        self.assertEqual(parser.open_graph["og:title"], "Test Product")
        self.assertEqual(parser.twitter["twitter:card"], "summary_large_image")
        self.assertEqual(parser.hreflang_links[0]["href"], "https://example.com/au/product")
        self.assertEqual(json_ld_types, ["SoftwareApplication"])
        self.assertEqual(invalid, 0)
        self.assertIn("https://example.com/assets/site.css", parser.assets)
        self.assertIn("app root #root", parser.app_root_signals)

    def test_parse_sitemap_distinguishes_urlset_and_index(self) -> None:
        urlset = """
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>https://example.com/</loc></url>
          <url><loc>https://example.com/pricing</loc></url>
        </urlset>
        """
        sitemap_index = """
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <sitemap><loc>https://example.com/sitemap-pages.xml</loc></sitemap>
        </sitemapindex>
        """

        self.assertEqual(
            static_seo_audit.parse_sitemap(urlset),
            ("urlset", ["https://example.com/", "https://example.com/pricing"]),
        )
        self.assertEqual(
            static_seo_audit.parse_sitemap(sitemap_index),
            ("sitemapindex", ["https://example.com/sitemap-pages.xml"]),
        )

    def test_collect_sitemap_pages_recurses_same_origin_index(self) -> None:
        original_fetch = static_seo_audit.fetch

        def fake_fetch(url: str, _timeout: float):
            bodies = {
                "https://example.com/sitemap.xml": """
                  <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
                    <sitemap><loc>https://example.com/sitemap-pages.xml</loc></sitemap>
                    <sitemap><loc>https://cdn.example.com/sitemap.xml</loc></sitemap>
                  </sitemapindex>
                """,
                "https://example.com/sitemap-pages.xml": """
                  <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
                    <url><loc>https://example.com/</loc></url>
                    <url><loc>https://example.com/about</loc></url>
                  </urlset>
                """,
            }
            return static_seo_audit.FetchResult(
                url=url,
                final_url=url,
                status=200,
                headers={"content-type": "application/xml"},
                body=bodies[url],
            )

        static_seo_audit.fetch = fake_fetch
        try:
            reports, pages = static_seo_audit.collect_sitemap_pages(
                ["https://example.com/sitemap.xml"],
                "https://example.com/",
                timeout=1,
                max_pages=4,
            )
        finally:
            static_seo_audit.fetch = original_fetch

        self.assertEqual(pages, ["https://example.com/", "https://example.com/about"])
        self.assertEqual(reports[0]["type"], "sitemapindex")
        self.assertEqual(reports[0]["child_sitemap_count"], 1)
        self.assertEqual(reports[0]["cross_origin_loc_count"], 1)
        self.assertEqual(reports[1]["type"], "urlset")
        self.assertEqual(reports[1]["page_loc_count"], 2)

    def test_robots_permissions_respect_disallow_rules(self) -> None:
        body = """
        User-agent: Googlebot
        Disallow: /private

        User-agent: *
        Allow: /
        """
        permissions = static_seo_audit.robots_permissions(
            body,
            200,
            "https://example.com/private/report",
        )

        self.assertTrue(permissions["CodexSEOAudit"])
        self.assertFalse(permissions["Googlebot"])
        self.assertTrue(
            static_seo_audit.robots_permissions("", 404, "https://example.com/private/report")[
                "Googlebot"
            ]
        )


if __name__ == "__main__":
    unittest.main()
