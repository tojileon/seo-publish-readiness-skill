import importlib.util
import pathlib
import sys
import unittest


SCRIPT_PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "pagespeed_insights.py"
SPEC = importlib.util.spec_from_file_location("pagespeed_insights", SCRIPT_PATH)
pagespeed_insights = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = pagespeed_insights
SPEC.loader.exec_module(pagespeed_insights)


class PageSpeedInsightsTests(unittest.TestCase):
    def test_summarize_extracts_scores_field_data_and_opportunities(self) -> None:
        data = {
            "id": "https://example.com/",
            "lighthouseResult": {
                "finalDisplayedUrl": "https://example.com/",
                "fetchTime": "2026-06-19T00:00:00Z",
                "categories": {
                    "performance": {"score": 0.92},
                    "accessibility": {"score": 1},
                    "best-practices": {"score": 0.88},
                    "seo": {"score": 0.95},
                },
                "audits": {
                    "largest-contentful-paint": {"displayValue": "1.2 s"},
                    "cumulative-layout-shift": {"displayValue": "0"},
                    "total-blocking-time": {"displayValue": "20 ms"},
                    "speed-index": {"displayValue": "1.5 s"},
                    "render-blocking-resources": {
                        "title": "Eliminate render-blocking resources",
                        "displayValue": "Potential savings of 300 ms",
                        "details": {"type": "opportunity", "overallSavingsMs": 300.2},
                    },
                },
            },
            "loadingExperience": {
                "overall_category": "FAST",
                "metrics": {
                    "LARGEST_CONTENTFUL_PAINT_MS": {
                        "category": "FAST",
                        "percentile": 1200,
                    }
                },
            },
            "originLoadingExperience": {
                "overall_category": "AVERAGE",
                "metrics": {
                    "INTERACTION_TO_NEXT_PAINT": {
                        "category": "AVERAGE",
                        "percentile": 240,
                    }
                },
            },
        }

        summary = pagespeed_insights.summarize(data, "mobile")

        self.assertEqual(summary["scores"]["performance"], 92)
        self.assertEqual(summary["scores"]["accessibility"], 100)
        self.assertEqual(summary["scores"]["best-practices"], 88)
        self.assertEqual(summary["scores"]["seo"], 95)
        self.assertEqual(summary["field_data"]["page_overall_category"], "FAST")
        self.assertEqual(
            summary["field_data"]["origin_metrics"]["interaction_to_next_paint"]["percentile"],
            240,
        )
        self.assertEqual(summary["top_opportunities"][0]["id"], "render-blocking-resources")


if __name__ == "__main__":
    unittest.main()
