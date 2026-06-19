#!/usr/bin/env python3
"""Fetch PageSpeed Insights evidence for a public URL.

The helper uses only the Python standard library. PageSpeed Insights may accept
unauthenticated requests in some environments, but callers should pass --api-key
when quota blocks unauthenticated checks.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Iterable


API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
DEFAULT_CATEGORIES = ["performance", "accessibility", "best-practices", "seo"]


def absolute_http_url(value: str) -> str:
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise argparse.ArgumentTypeError("url must be an absolute http(s) URL")
    return value


def fetch_pagespeed(url: str, strategy: str, timeout: float, api_key: str | None) -> dict:
    query: list[tuple[str, str]] = [
        ("url", url),
        ("strategy", strategy),
        ("locale", "en"),
    ]
    query.extend(("category", category) for category in DEFAULT_CATEGORIES)
    if api_key:
        query.append(("key", api_key))

    request_url = f"{API_URL}?{urllib.parse.urlencode(query)}"
    request = urllib.request.Request(
        request_url,
        headers={"User-Agent": "CodexSEOAuditPageSpeed/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        message = body
        try:
            parsed = json.loads(body)
            message = parsed.get("error", {}).get("message") or body
        except json.JSONDecodeError:
            pass
        raise RuntimeError(f"PageSpeed API returned HTTP {exc.code}: {message}") from exc


def score(value: object) -> int | None:
    if isinstance(value, int | float):
        return round(float(value) * 100)
    return None


def metric_summary(metrics: dict) -> dict[str, dict[str, object]]:
    fields = {
        "largest_contentful_paint": "LARGEST_CONTENTFUL_PAINT_MS",
        "cumulative_layout_shift": "CUMULATIVE_LAYOUT_SHIFT_SCORE",
        "interaction_to_next_paint": "INTERACTION_TO_NEXT_PAINT",
        "first_contentful_paint": "FIRST_CONTENTFUL_PAINT_MS",
    }
    summary: dict[str, dict[str, object]] = {}
    for output_name, api_name in fields.items():
        metric = metrics.get(api_name)
        if isinstance(metric, dict):
            summary[output_name] = {
                "category": metric.get("category"),
                "percentile": metric.get("percentile"),
            }
    return summary


def summarize(data: dict, strategy: str) -> dict:
    lighthouse = data.get("lighthouseResult", {})
    categories = lighthouse.get("categories", {})
    audits = lighthouse.get("audits", {})
    loading_experience = data.get("loadingExperience", {})
    origin_experience = data.get("originLoadingExperience", {})

    return {
        "url": data.get("id"),
        "strategy": strategy,
        "final_url": lighthouse.get("finalDisplayedUrl") or lighthouse.get("finalUrl"),
        "fetch_time": lighthouse.get("fetchTime"),
        "scores": {
            name: score(category.get("score")) if isinstance(category, dict) else None
            for name, category in categories.items()
        },
        "field_data": {
            "page_overall_category": loading_experience.get("overall_category"),
            "page_metrics": metric_summary(loading_experience.get("metrics", {})),
            "origin_overall_category": origin_experience.get("overall_category"),
            "origin_metrics": metric_summary(origin_experience.get("metrics", {})),
        },
        "lab_metrics": {
            "largest_contentful_paint": audits.get("largest-contentful-paint", {}).get("displayValue"),
            "cumulative_layout_shift": audits.get("cumulative-layout-shift", {}).get("displayValue"),
            "total_blocking_time": audits.get("total-blocking-time", {}).get("displayValue"),
            "speed_index": audits.get("speed-index", {}).get("displayValue"),
        },
        "top_opportunities": top_opportunities(audits),
    }


def top_opportunities(audits: dict, limit: int = 5) -> list[dict[str, object]]:
    opportunities: list[dict[str, object]] = []
    for audit_id, audit in audits.items():
        if not isinstance(audit, dict):
            continue
        details = audit.get("details")
        if not isinstance(details, dict) or details.get("type") != "opportunity":
            continue
        savings = details.get("overallSavingsMs")
        if not isinstance(savings, int | float) or savings <= 0:
            continue
        opportunities.append(
            {
                "id": audit_id,
                "title": audit.get("title"),
                "display_value": audit.get("displayValue"),
                "overall_savings_ms": round(float(savings)),
            }
        )
    return sorted(opportunities, key=lambda item: item["overall_savings_ms"], reverse=True)[:limit]


def render_markdown(summary: dict) -> str:
    lines = [
        f"# PageSpeed Insights: {summary['url']}",
        "",
        f"- strategy: `{summary['strategy']}`",
        f"- final URL: {summary.get('final_url') or 'unknown'}",
        f"- fetch time: {summary.get('fetch_time') or 'unknown'}",
        "",
        "## Scores",
    ]
    for name in ["performance", "accessibility", "best-practices", "seo"]:
        lines.append(f"- {name}: {summary['scores'].get(name)}")

    lines.extend(["", "## Field Data"])
    field_data = summary["field_data"]
    lines.append(f"- page category: {field_data.get('page_overall_category') or 'unavailable'}")
    lines.append(f"- origin category: {field_data.get('origin_overall_category') or 'unavailable'}")
    for scope in ["page_metrics", "origin_metrics"]:
        metrics = field_data.get(scope) or {}
        lines.append(f"- {scope}:")
        if not metrics:
            lines.append("  - unavailable")
        for name, metric in metrics.items():
            lines.append(f"  - {name}: {metric.get('category')} at percentile {metric.get('percentile')}")

    lines.extend(["", "## Lab Metrics"])
    for name, value in summary["lab_metrics"].items():
        lines.append(f"- {name}: {value or 'unavailable'}")

    lines.extend(["", "## Top Opportunities"])
    if summary["top_opportunities"]:
        for item in summary["top_opportunities"]:
            lines.append(
                f"- {item['title']}: {item.get('display_value') or item['overall_savings_ms']}"
            )
    else:
        lines.append("- none reported")

    lines.append("")
    lines.append(
        "Note: PageSpeed Insights combines lab Lighthouse data with field data when available. "
        "Treat lab-only results as launch-readiness evidence, not a guaranteed ranking outcome."
    )
    return "\n".join(lines) + "\n"


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch PageSpeed Insights evidence for a public URL.")
    parser.add_argument("url", type=absolute_http_url)
    parser.add_argument("--strategy", choices={"mobile", "desktop"}, default="mobile")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--format", choices={"markdown", "json"}, default="markdown")
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        summary = summarize(fetch_pagespeed(args.url, args.strategy, args.timeout, args.api_key), args.strategy)
    except RuntimeError as exc:
        print(
            f"PageSpeed Insights unavailable: {exc}. "
            "If this is a quota error, retry with --api-key or use the PageSpeed Insights web UI.",
            file=sys.stderr,
        )
        return 2
    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(render_markdown(summary), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
