#!/usr/bin/env python3
"""Small same-origin SEO launch audit for static/product sites.

The script intentionally uses only the Python standard library so a Codex agent
can run it without preparing a project environment.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import deque
from dataclasses import asdict, dataclass, field
from html.parser import HTMLParser
from typing import Iterable


USER_AGENT = "CodexSEOAudit/1.0 (+https://github.com/tojileon/seo-publish-readiness-skill)"


@dataclass
class FetchResult:
    url: str
    final_url: str
    status: int | None
    headers: dict[str, str]
    body: str
    error: str | None = None


@dataclass
class PageReport:
    url: str
    final_url: str
    status: int | None
    content_type: str
    title: str | None
    meta_description: str | None
    robots_meta: str | None
    x_robots_tag: str | None
    canonical: str | None
    h1s: list[str]
    images_total: int
    images_missing_alt: int
    same_origin_links: list[str]
    warnings: list[str] = field(default_factory=list)
    fetch_error: str | None = None


class SEOHTMLParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.title_parts: list[str] = []
        self.in_title = False
        self.in_h1 = False
        self.current_h1: list[str] = []
        self.h1s: list[str] = []
        self.meta_description: str | None = None
        self.robots_meta: str | None = None
        self.canonical: str | None = None
        self.images_total = 0
        self.images_missing_alt = 0
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {k.lower(): (v or "") for k, v in attrs}
        tag = tag.lower()

        if tag == "title":
            self.in_title = True
            return

        if tag == "h1":
            self.in_h1 = True
            self.current_h1 = []
            return

        if tag == "meta":
            name = attrs_dict.get("name", "").lower()
            content = clean_text(attrs_dict.get("content", ""))
            if name == "description" and content:
                self.meta_description = content
            if name in {"robots", "googlebot"} and content:
                previous = f"{self.robots_meta}, " if self.robots_meta else ""
                self.robots_meta = f"{previous}{name}: {content}"
            return

        if tag == "link":
            rel = attrs_dict.get("rel", "").lower()
            href = attrs_dict.get("href", "")
            if "canonical" in rel.split() and href:
                self.canonical = normalize_url(urllib.parse.urljoin(self.base_url, href))
            return

        if tag == "img":
            self.images_total += 1
            if "alt" not in attrs_dict or not attrs_dict.get("alt", "").strip():
                self.images_missing_alt += 1
            return

        if tag == "a":
            href = attrs_dict.get("href", "")
            if href:
                self.links.append(normalize_url(urllib.parse.urljoin(self.base_url, href)))

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self.in_h1:
            self.current_h1.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self.in_title = False
        if tag == "h1":
            self.in_h1 = False
            h1 = clean_text(" ".join(self.current_h1))
            if h1:
                self.h1s.append(h1)

    @property
    def title(self) -> str | None:
        value = clean_text(" ".join(self.title_parts))
        return value or None


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()


def normalize_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    parsed = parsed._replace(fragment="")
    return urllib.parse.urlunparse(parsed)


def origin(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def same_origin(url: str, root: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    root_parsed = urllib.parse.urlparse(root)
    return parsed.scheme in {"http", "https"} and parsed.netloc == root_parsed.netloc


def fetch(url: str, timeout: float) -> FetchResult:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            raw = response.read(2_000_000)
            charset = response.headers.get_content_charset() or "utf-8"
            body = raw.decode(charset, errors="replace")
            return FetchResult(
                url=url,
                final_url=response.geturl(),
                status=response.status,
                headers={k.lower(): v for k, v in response.headers.items()},
                body=body,
            )
    except urllib.error.HTTPError as exc:
        raw = exc.read(200_000)
        charset = exc.headers.get_content_charset() or "utf-8"
        return FetchResult(
            url=url,
            final_url=exc.geturl(),
            status=exc.code,
            headers={k.lower(): v for k, v in exc.headers.items()},
            body=raw.decode(charset, errors="replace"),
            error=f"HTTP {exc.code}",
        )
    except Exception as exc:  # noqa: BLE001 - surface network failures as audit evidence.
        return FetchResult(
            url=url,
            final_url=url,
            status=None,
            headers={},
            body="",
            error=f"{type(exc).__name__}: {exc}",
        )


def parse_sitemap_urls(xml_body: str) -> list[str]:
    if not xml_body.strip():
        return []
    try:
        root = ET.fromstring(xml_body)
    except ET.ParseError:
        return []
    urls: list[str] = []
    for loc in root.iter():
        if loc.tag.endswith("loc") and loc.text:
            urls.append(normalize_url(loc.text.strip()))
    return urls


def discover_from_robots(robots_body: str) -> list[str]:
    urls: list[str] = []
    for line in robots_body.splitlines():
        if line.lower().startswith("sitemap:"):
            urls.append(normalize_url(line.split(":", 1)[1].strip()))
    return urls


def analyze_page(url: str, root_url: str, timeout: float) -> PageReport:
    result = fetch(url, timeout)
    content_type = result.headers.get("content-type", "")
    parser = SEOHTMLParser(result.final_url)
    if "html" in content_type.lower() and result.body:
        parser.feed(result.body)

    links = sorted(
        {
            link
            for link in parser.links
            if same_origin(link, root_url)
            and not urllib.parse.urlparse(link).path.lower().endswith(
                (".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".css", ".js")
            )
        }
    )
    report = PageReport(
        url=url,
        final_url=result.final_url,
        status=result.status,
        content_type=content_type,
        title=parser.title,
        meta_description=parser.meta_description,
        robots_meta=parser.robots_meta,
        x_robots_tag=result.headers.get("x-robots-tag"),
        canonical=parser.canonical,
        h1s=parser.h1s,
        images_total=parser.images_total,
        images_missing_alt=parser.images_missing_alt,
        same_origin_links=links,
        fetch_error=result.error,
    )
    add_page_warnings(report, root_url)
    return report


def add_page_warnings(report: PageReport, root_url: str) -> None:
    if report.status is None:
        report.warnings.append("Fetch failed; page indexability could not be verified.")
    elif not 200 <= report.status < 300:
        report.warnings.append(f"Expected indexable page to return 2xx, got {report.status}.")

    if "html" not in report.content_type.lower():
        report.warnings.append(f"Expected HTML content type, got {report.content_type or 'missing header'}.")

    if report.final_url != report.url:
        report.warnings.append(f"Requested URL resolves to {report.final_url}; verify this redirect is intentional.")

    robots_signals = " ".join(filter(None, [report.robots_meta, report.x_robots_tag])).lower()
    if "noindex" in robots_signals:
        report.warnings.append("Page has a noindex directive.")
    if "nofollow" in robots_signals:
        report.warnings.append("Page has a nofollow directive.")

    if not report.title:
        report.warnings.append("Missing title element.")
    if not report.meta_description:
        report.warnings.append("Missing meta description.")
    if len(report.h1s) != 1:
        report.warnings.append(f"Expected exactly one H1, found {len(report.h1s)}.")
    if not report.canonical:
        report.warnings.append("Missing canonical URL.")
    elif not same_origin(report.canonical, root_url):
        report.warnings.append(f"Canonical points off-origin: {report.canonical}.")
    elif report.canonical != normalize_url(report.final_url):
        report.warnings.append(f"Canonical differs from final URL: {report.canonical}.")
    if report.images_missing_alt:
        report.warnings.append(f"{report.images_missing_alt} of {report.images_total} images lack alt text.")


def audit(root_url: str, max_pages: int, timeout: float, delay: float) -> dict:
    root_url = normalize_url(root_url)
    site_origin = origin(root_url)
    robots_url = urllib.parse.urljoin(site_origin, "/robots.txt")
    default_sitemap_url = urllib.parse.urljoin(site_origin, "/sitemap.xml")

    robots = fetch(robots_url, timeout)
    sitemap_urls = discover_from_robots(robots.body)
    if default_sitemap_url not in sitemap_urls:
        sitemap_urls.append(default_sitemap_url)

    sitemap_reports = []
    discovered_urls: list[str] = [root_url]
    for sitemap_url in sitemap_urls:
        if not same_origin(sitemap_url, root_url):
            sitemap_reports.append({"url": sitemap_url, "skipped": "cross-origin sitemap"})
            continue
        result = fetch(sitemap_url, timeout)
        locs = [url for url in parse_sitemap_urls(result.body) if same_origin(url, root_url)]
        sitemap_reports.append(
            {
                "url": sitemap_url,
                "status": result.status,
                "content_type": result.headers.get("content-type", ""),
                "loc_count": len(locs),
                "fetch_error": result.error,
            }
        )
        discovered_urls.extend(locs[:max_pages])

    pages: list[PageReport] = []
    seen: set[str] = set()
    queue: deque[str] = deque(discovered_urls)

    while queue and len(pages) < max_pages:
        url = normalize_url(queue.popleft())
        if url in seen or not same_origin(url, root_url):
            continue
        seen.add(url)
        page = analyze_page(url, root_url, timeout)
        pages.append(page)
        for link in page.same_origin_links:
            if link not in seen and len(seen) + len(queue) < max_pages * 3:
                queue.append(link)
        if delay:
            time.sleep(delay)

    missing_url = urllib.parse.urljoin(site_origin, f"/codex-seo-audit-missing-{int(time.time())}.html")
    missing = fetch(missing_url, timeout)
    missing_warning = None
    if missing.status not in {404, 410}:
        missing_warning = f"Expected missing URL to return 404 or 410, got {missing.status}."

    return {
        "root_url": root_url,
        "robots": {
            "url": robots_url,
            "status": robots.status,
            "content_type": robots.headers.get("content-type", ""),
            "sitemap_hints": discover_from_robots(robots.body),
            "fetch_error": robots.error,
        },
        "sitemaps": sitemap_reports,
        "pages": [asdict(page) for page in pages],
        "missing_url_check": {
            "url": missing_url,
            "status": missing.status,
            "warning": missing_warning,
            "fetch_error": missing.error,
        },
    }


def render_markdown(report: dict) -> str:
    lines: list[str] = []
    lines.append(f"# Static SEO Audit: {report['root_url']}")
    lines.append("")
    robots = report["robots"]
    lines.append("## Discovery")
    lines.append(f"- robots.txt: `{robots['status']}` at {robots['url']}")
    if robots["sitemap_hints"]:
        lines.append("- robots sitemap hints:")
        lines.extend(f"  - {url}" for url in robots["sitemap_hints"])
    else:
        lines.append("- robots sitemap hints: none found")
    for sitemap in report["sitemaps"]:
        if sitemap.get("skipped"):
            lines.append(f"- sitemap skipped: {sitemap['url']} ({sitemap['skipped']})")
        else:
            lines.append(
                f"- sitemap: `{sitemap['status']}` {sitemap['url']} "
                f"({sitemap['loc_count']} same-origin locs)"
            )
    missing = report["missing_url_check"]
    lines.append(f"- missing URL check: `{missing['status']}` at {missing['url']}")
    if missing["warning"]:
        lines.append(f"  - Warning: {missing['warning']}")

    lines.append("")
    lines.append("## Pages")
    for page in report["pages"]:
        lines.append(f"### {page['url']}")
        lines.append(f"- status: `{page['status']}`")
        lines.append(f"- final URL: {page['final_url']}")
        lines.append(f"- content type: `{page['content_type']}`")
        lines.append(f"- title: {page['title'] or 'missing'}")
        lines.append(f"- meta description: {page['meta_description'] or 'missing'}")
        lines.append(f"- canonical: {page['canonical'] or 'missing'}")
        lines.append(f"- robots meta: {page['robots_meta'] or 'none'}")
        lines.append(f"- X-Robots-Tag: {page['x_robots_tag'] or 'none'}")
        lines.append(f"- H1 count: {len(page['h1s'])}")
        lines.append(f"- images missing alt: {page['images_missing_alt']} / {page['images_total']}")
        lines.append(f"- same-origin HTML links found: {len(page['same_origin_links'])}")
        if page["warnings"]:
            lines.append("- warnings:")
            lines.extend(f"  - {warning}" for warning in page["warnings"])
        else:
            lines.append("- warnings: none")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
    return parsed


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a same-origin static SEO launch audit.")
    parser.add_argument("url", help="Root URL to audit, for example https://example.com/")
    parser.add_argument("--max-pages", type=positive_int, default=8, help="maximum HTML pages to inspect")
    parser.add_argument("--timeout", type=float, default=10.0, help="network timeout in seconds")
    parser.add_argument("--delay", type=float, default=0.0, help="delay between page fetches in seconds")
    parser.add_argument("--format", choices={"markdown", "json"}, default="markdown")
    args = parser.parse_args(list(argv) if argv is not None else None)

    root_url = args.url
    parsed = urllib.parse.urlparse(root_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        parser.error("url must be an absolute http(s) URL")

    report = audit(root_url, args.max_pages, args.timeout, args.delay)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_markdown(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
