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
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET
from collections import deque
from dataclasses import asdict, dataclass, field
from html.parser import HTMLParser
from typing import Iterable


USER_AGENT_NAME = "CodexSEOAudit"
USER_AGENT = f"{USER_AGENT_NAME}/1.1 (+https://github.com/tojileon/seo-publish-readiness-skill)"


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
    robots_txt_allowed: dict[str, bool | None]
    canonical: str | None
    viewport: str | None
    open_graph: dict[str, str]
    twitter: dict[str, str]
    json_ld_blocks: int
    json_ld_invalid: int
    json_ld_types: list[str]
    hreflang_links: list[dict[str, str]]
    h1s: list[str]
    images_total: int
    images_missing_alt: int
    same_origin_links: list[str]
    same_origin_assets: list[str]
    scripts_total: int
    app_root_signals: list[str]
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
        self.viewport: str | None = None
        self.open_graph: dict[str, str] = {}
        self.twitter: dict[str, str] = {}
        self.json_ld_blocks: list[str] = []
        self.in_json_ld = False
        self.current_json_ld: list[str] = []
        self.hreflang_links: list[dict[str, str]] = []
        self.images_total = 0
        self.images_missing_alt = 0
        self.links: list[str] = []
        self.assets: list[str] = []
        self.scripts_total = 0
        self.app_root_signals: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {k.lower(): (v or "") for k, v in attrs}
        tag = tag.lower()
        self.capture_app_root_signal(tag, attrs_dict)

        if tag == "title":
            self.in_title = True
            return

        if tag == "h1":
            self.in_h1 = True
            self.current_h1 = []
            return

        if tag == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            content = clean_text(attrs_dict.get("content", ""))
            if name == "description" and content:
                self.meta_description = content
            if name == "viewport" and content:
                self.viewport = content
            if name in {"robots", "googlebot"} and content:
                previous = f"{self.robots_meta}, " if self.robots_meta else ""
                self.robots_meta = f"{previous}{name}: {content}"
            if prop.startswith("og:") and content:
                self.open_graph[prop] = content
            if (name.startswith("twitter:") or prop.startswith("twitter:")) and content:
                self.twitter[name or prop] = content
            return

        if tag == "link":
            rel = attrs_dict.get("rel", "").lower()
            href = attrs_dict.get("href", "")
            if "canonical" in rel.split() and href:
                self.canonical = normalize_url(urllib.parse.urljoin(self.base_url, href))
            if "alternate" in rel.split() and attrs_dict.get("hreflang") and href:
                self.hreflang_links.append(
                    {
                        "hreflang": attrs_dict["hreflang"],
                        "href": normalize_url(urllib.parse.urljoin(self.base_url, href)),
                    }
                )
            if href and self.is_asset_url(href):
                self.assets.append(normalize_url(urllib.parse.urljoin(self.base_url, href)))
            return

        if tag == "img":
            self.images_total += 1
            src = attrs_dict.get("src", "")
            if src:
                self.assets.append(normalize_url(urllib.parse.urljoin(self.base_url, src)))
            if "alt" not in attrs_dict or not attrs_dict.get("alt", "").strip():
                self.images_missing_alt += 1
            return

        if tag == "script":
            self.scripts_total += 1
            script_type = attrs_dict.get("type", "").lower()
            script_id = attrs_dict.get("id", "").lower()
            src = attrs_dict.get("src", "")
            if src:
                asset_url = normalize_url(urllib.parse.urljoin(self.base_url, src))
                self.assets.append(asset_url)
                self.capture_script_signal(asset_url)
            if script_type.startswith("application/ld+json"):
                self.in_json_ld = True
                self.current_json_ld = []
            if script_id == "__next_data__":
                self.add_app_signal("Next.js data script")
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
        if self.in_json_ld:
            self.current_json_ld.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self.in_title = False
        if tag == "h1":
            self.in_h1 = False
            h1 = clean_text(" ".join(self.current_h1))
            if h1:
                self.h1s.append(h1)
        if tag == "script" and self.in_json_ld:
            self.in_json_ld = False
            value = clean_text(" ".join(self.current_json_ld))
            if value:
                self.json_ld_blocks.append(value)

    @property
    def title(self) -> str | None:
        value = clean_text(" ".join(self.title_parts))
        return value or None

    @staticmethod
    def is_asset_url(url: str) -> bool:
        path = urllib.parse.urlparse(url).path.lower()
        return path.endswith(
            (
                ".css",
                ".js",
                ".mjs",
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".webp",
                ".svg",
                ".ico",
                ".avif",
                ".woff",
                ".woff2",
            )
        )

    def capture_app_root_signal(self, tag: str, attrs: dict[str, str]) -> None:
        element_id = attrs.get("id", "").lower()
        classes = attrs.get("class", "").lower()
        if element_id in {"root", "app", "__next", "svelte"}:
            self.add_app_signal(f"app root #{element_id}")
        if "data-reactroot" in attrs:
            self.add_app_signal("React root attribute")
        if "ng-app" in attrs:
            self.add_app_signal("Angular app attribute")
        if tag == "div" and "app" in classes.split():
            self.add_app_signal("generic app container class")

    def capture_script_signal(self, url: str) -> None:
        path = urllib.parse.urlparse(url).path.lower()
        if "/_next/" in path:
            self.add_app_signal("Next.js asset")
        if "/_nuxt/" in path:
            self.add_app_signal("Nuxt asset")
        if "/assets/index-" in path:
            self.add_app_signal("bundled app asset")

    def add_app_signal(self, value: str) -> None:
        if value not in self.app_root_signals:
            self.app_root_signals.append(value)


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


def local_xml_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def extract_json_ld_types(blocks: list[str]) -> tuple[list[str], int]:
    types: set[str] = set()
    invalid = 0

    def collect(value: object) -> None:
        if isinstance(value, dict):
            type_value = value.get("@type")
            if isinstance(type_value, str):
                types.add(type_value)
            elif isinstance(type_value, list):
                types.update(item for item in type_value if isinstance(item, str))
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for item in value:
                collect(item)

    for block in blocks:
        try:
            collect(json.loads(block))
        except json.JSONDecodeError:
            invalid += 1
    return sorted(types), invalid


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


def parse_sitemap(xml_body: str) -> tuple[str, list[str]]:
    if not xml_body.strip():
        return "empty", []
    try:
        root = ET.fromstring(xml_body)
    except ET.ParseError:
        return "invalid", []
    kind = local_xml_name(root.tag)
    urls: list[str] = []
    for loc in root.iter():
        if local_xml_name(loc.tag) == "loc" and loc.text:
            urls.append(normalize_url(loc.text.strip()))
    return kind, urls


def parse_sitemap_urls(xml_body: str) -> list[str]:
    _kind, urls = parse_sitemap(xml_body)
    return urls


def discover_from_robots(robots_body: str) -> list[str]:
    urls: list[str] = []
    for line in robots_body.splitlines():
        if line.lower().startswith("sitemap:"):
            urls.append(normalize_url(line.split(":", 1)[1].strip()))
    return urls


def robots_permissions(
    robots_body: str,
    robots_status: int | None,
    url: str,
) -> dict[str, bool | None]:
    if robots_status is None or robots_status == 429 or robots_status >= 500:
        return {USER_AGENT_NAME: None, "Googlebot": None}
    if 400 <= robots_status < 500:
        return {USER_AGENT_NAME: True, "Googlebot": True}

    parser = urllib.robotparser.RobotFileParser()
    parser.parse(robots_body.splitlines())
    return {
        USER_AGENT_NAME: parser.can_fetch(USER_AGENT_NAME, url),
        "Googlebot": parser.can_fetch("Googlebot", url),
    }


def collect_sitemap_pages(
    sitemap_urls: list[str],
    root_url: str,
    timeout: float,
    max_pages: int,
    max_sitemaps: int = 20,
    max_depth: int = 3,
) -> tuple[list[dict], list[str]]:
    reports: list[dict] = []
    page_urls: list[str] = []
    seen_sitemaps: set[str] = set()
    queue: deque[tuple[str, int]] = deque((url, 0) for url in sitemap_urls)

    while queue and len(seen_sitemaps) < max_sitemaps and len(page_urls) < max_pages * 3:
        sitemap_url, depth = queue.popleft()
        sitemap_url = normalize_url(sitemap_url)
        if sitemap_url in seen_sitemaps:
            continue
        if not same_origin(sitemap_url, root_url):
            reports.append({"url": sitemap_url, "skipped": "cross-origin sitemap"})
            continue
        seen_sitemaps.add(sitemap_url)

        result = fetch(sitemap_url, timeout)
        kind, locs = parse_sitemap(result.body)
        same_origin_locs = [url for url in locs if same_origin(url, root_url)]
        report = {
            "url": sitemap_url,
            "status": result.status,
            "content_type": result.headers.get("content-type", ""),
            "type": kind,
            "loc_count": len(locs),
            "same_origin_loc_count": len(same_origin_locs),
            "cross_origin_loc_count": len(locs) - len(same_origin_locs),
            "fetch_error": result.error,
        }

        if kind == "sitemapindex":
            child_sitemaps = same_origin_locs
            report["child_sitemap_count"] = len(child_sitemaps)
            if depth >= max_depth:
                report["skipped_children"] = len(child_sitemaps)
            else:
                for child in child_sitemaps:
                    if child not in seen_sitemaps:
                        queue.append((child, depth + 1))
        elif kind == "urlset":
            report["page_loc_count"] = len(same_origin_locs)
            page_urls.extend(same_origin_locs[: max_pages * 3 - len(page_urls)])

        reports.append(report)

    return reports, page_urls[: max_pages * 3]


def missing_url_result(url: str, timeout: float) -> dict:
    result = fetch(url, timeout)
    warning = None
    if result.status not in {404, 410}:
        warning = f"Expected missing URL to return 404 or 410, got {result.status}."
    return {
        "url": url,
        "status": result.status,
        "warning": warning,
        "fetch_error": result.error,
    }


def analyze_page(
    url: str,
    root_url: str,
    timeout: float,
    robots_body: str,
    robots_status: int | None,
) -> PageReport:
    result = fetch(url, timeout)
    content_type = result.headers.get("content-type", "")
    parser = SEOHTMLParser(result.final_url)
    if "html" in content_type.lower() and result.body:
        parser.feed(result.body)
    json_ld_types, json_ld_invalid = extract_json_ld_types(parser.json_ld_blocks)

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
    assets = sorted({asset for asset in parser.assets if same_origin(asset, root_url)})
    report = PageReport(
        url=url,
        final_url=result.final_url,
        status=result.status,
        content_type=content_type,
        title=parser.title,
        meta_description=parser.meta_description,
        robots_meta=parser.robots_meta,
        x_robots_tag=result.headers.get("x-robots-tag"),
        robots_txt_allowed=robots_permissions(robots_body, robots_status, result.final_url),
        canonical=parser.canonical,
        viewport=parser.viewport,
        open_graph=parser.open_graph,
        twitter=parser.twitter,
        json_ld_blocks=len(parser.json_ld_blocks),
        json_ld_invalid=json_ld_invalid,
        json_ld_types=json_ld_types,
        hreflang_links=parser.hreflang_links,
        h1s=parser.h1s,
        images_total=parser.images_total,
        images_missing_alt=parser.images_missing_alt,
        same_origin_links=links,
        same_origin_assets=assets,
        scripts_total=parser.scripts_total,
        app_root_signals=parser.app_root_signals,
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
    for agent, allowed in report.robots_txt_allowed.items():
        if allowed is False:
            report.warnings.append(f"robots.txt disallows this URL for {agent}.")
        elif allowed is None:
            report.warnings.append(f"robots.txt permission for {agent} could not be verified.")

    if not report.title:
        report.warnings.append("Missing title element.")
    if not report.meta_description:
        report.warnings.append("Missing meta description.")
    if not report.viewport:
        report.warnings.append("Missing viewport meta tag; mobile rendering should be checked manually.")
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
    if not report.open_graph:
        report.warnings.append("Missing Open Graph metadata.")
    if not report.twitter:
        report.warnings.append("Missing Twitter card metadata.")
    if report.json_ld_invalid:
        report.warnings.append(f"{report.json_ld_invalid} JSON-LD block(s) could not be parsed.")
    if report.app_root_signals:
        report.warnings.append(
            "Page has JavaScript app signals; compare source HTML with rendered desktop and mobile DOM."
        )


def audit(root_url: str, max_pages: int, timeout: float, delay: float) -> dict:
    root_url = normalize_url(root_url)
    site_origin = origin(root_url)
    robots_url = urllib.parse.urljoin(site_origin, "/robots.txt")
    default_sitemap_url = urllib.parse.urljoin(site_origin, "/sitemap.xml")

    robots = fetch(robots_url, timeout)
    sitemap_urls = discover_from_robots(robots.body)
    if default_sitemap_url not in sitemap_urls:
        sitemap_urls.append(default_sitemap_url)

    discovered_urls: list[str] = [root_url]
    sitemap_reports, sitemap_page_urls = collect_sitemap_pages(sitemap_urls, root_url, timeout, max_pages)
    discovered_urls.extend(sitemap_page_urls)

    pages: list[PageReport] = []
    seen: set[str] = set()
    queue: deque[str] = deque(discovered_urls)

    while queue and len(pages) < max_pages:
        url = normalize_url(queue.popleft())
        if url in seen or not same_origin(url, root_url):
            continue
        seen.add(url)
        page = analyze_page(url, root_url, timeout, robots.body, robots.status)
        pages.append(page)
        for link in page.same_origin_links:
            if link not in seen and len(seen) + len(queue) < max_pages * 3:
                queue.append(link)
        if delay:
            time.sleep(delay)

    missing_stamp = int(time.time())
    missing_html_url = urllib.parse.urljoin(site_origin, f"/codex-seo-audit-missing-{missing_stamp}.html")
    missing_asset_url = urllib.parse.urljoin(site_origin, f"/assets/codex-seo-audit-missing-{missing_stamp}.png")

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
        "missing_url_check": missing_url_result(missing_html_url, timeout),
        "missing_asset_check": missing_url_result(missing_asset_url, timeout),
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
            detail = f"{sitemap['same_origin_loc_count']} / {sitemap['loc_count']} same-origin locs"
            if sitemap.get("type") == "sitemapindex":
                detail = f"{sitemap.get('child_sitemap_count', 0)} child sitemap(s), {detail}"
            if sitemap.get("type") == "urlset":
                detail = f"{sitemap.get('page_loc_count', 0)} page locs, {detail}"
            if sitemap.get("cross_origin_loc_count"):
                detail = f"{detail}, {sitemap['cross_origin_loc_count']} cross-origin loc(s) skipped"
            lines.append(f"- sitemap: `{sitemap['status']}` {sitemap['url']} ({sitemap.get('type')}; {detail})")
    missing = report["missing_url_check"]
    lines.append(f"- missing URL check: `{missing['status']}` at {missing['url']}")
    if missing["warning"]:
        lines.append(f"  - Warning: {missing['warning']}")
    missing_asset = report["missing_asset_check"]
    lines.append(f"- missing asset check: `{missing_asset['status']}` at {missing_asset['url']}")
    if missing_asset["warning"]:
        lines.append(f"  - Warning: {missing_asset['warning']}")

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
        lines.append(f"- robots.txt allowed: {page['robots_txt_allowed']}")
        lines.append(f"- viewport: {page['viewport'] or 'missing'}")
        lines.append(f"- Open Graph tags: {len(page['open_graph'])}")
        lines.append(f"- Twitter card tags: {len(page['twitter'])}")
        lines.append(
            f"- JSON-LD blocks: {page['json_ld_blocks']} "
            f"(types: {', '.join(page['json_ld_types']) if page['json_ld_types'] else 'none'}, "
            f"invalid: {page['json_ld_invalid']})"
        )
        lines.append(f"- hreflang links: {len(page['hreflang_links'])}")
        lines.append(f"- H1 count: {len(page['h1s'])}")
        lines.append(f"- images missing alt: {page['images_missing_alt']} / {page['images_total']}")
        lines.append(f"- same-origin HTML links found: {len(page['same_origin_links'])}")
        lines.append(f"- same-origin assets found: {len(page['same_origin_assets'])}")
        lines.append(f"- script tags: {page['scripts_total']}")
        if page["app_root_signals"]:
            lines.append(f"- JavaScript app signals: {', '.join(page['app_root_signals'])}")
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
