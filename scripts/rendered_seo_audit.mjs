#!/usr/bin/env node
/*
 * Optional rendered SEO audit helper.
 *
 * This script needs Playwright in the caller's environment. The core static
 * helper stays dependency-free; this one is for JavaScript-heavy pages where
 * source HTML is not enough evidence.
 */

const USER_AGENT =
  "CodexSEOAuditRendered/1.0 (+https://github.com/tojileon/seo-publish-readiness-skill)";

const DESKTOP_VIEWPORT = { width: 1366, height: 900 };
const MOBILE_VIEWPORT = { width: 390, height: 844 };

function parseArgs(argv) {
  const args = {
    url: null,
    format: "markdown",
    timeoutMs: 30000,
    waitMs: 0,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--format") {
      args.format = argv[++index];
    } else if (value === "--timeout-ms") {
      args.timeoutMs = Number(argv[++index]);
    } else if (value === "--wait-ms") {
      args.waitMs = Number(argv[++index]);
    } else if (value === "--help" || value === "-h") {
      args.help = true;
    } else if (!args.url) {
      args.url = value;
    } else {
      throw new Error(`Unexpected argument: ${value}`);
    }
  }

  if (args.format !== "markdown" && args.format !== "json") {
    throw new Error("--format must be markdown or json");
  }
  if (!Number.isFinite(args.timeoutMs) || args.timeoutMs < 1000) {
    throw new Error("--timeout-ms must be a number at least 1000");
  }
  if (!Number.isFinite(args.waitMs) || args.waitMs < 0) {
    throw new Error("--wait-ms must be a non-negative number");
  }
  return args;
}

function usage() {
  return `Usage: node scripts/rendered_seo_audit.mjs <url> [--format markdown|json] [--timeout-ms 30000] [--wait-ms 0]

Compares source HTML, rendered desktop DOM, and rendered mobile DOM for key SEO
signals. Requires Playwright to be installed in the current environment.`;
}

function assertAbsoluteHttpUrl(rawUrl) {
  let parsed;
  try {
    parsed = new URL(rawUrl);
  } catch {
    throw new Error("url must be an absolute http(s) URL");
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error("url must be an absolute http(s) URL");
  }
  return parsed.href;
}

async function loadPlaywright() {
  try {
    return await import("playwright");
  } catch {
    throw new Error(
      "Playwright is not installed. Install it in the active environment, then run this helper again.",
    );
  }
}

function valuesDiffer(first, second) {
  return JSON.stringify(first ?? null) !== JSON.stringify(second ?? null);
}

function buildComparison(source, desktop, mobile) {
  const checks = [
    ["title", "Title differs"],
    ["meta_description", "Meta description differs"],
    ["canonical", "Canonical differs"],
    ["robots_meta", "Robots meta differs"],
    ["viewport", "Viewport differs"],
    ["h1s", "H1 set differs"],
    ["json_ld_types", "JSON-LD types differ"],
    ["hreflang_links", "hreflang links differ"],
  ];

  const warnings = [];
  for (const [field, label] of checks) {
    if (valuesDiffer(source[field], desktop[field])) {
      warnings.push(`${label} between source HTML and rendered desktop DOM.`);
    }
    if (valuesDiffer(desktop[field], mobile[field])) {
      warnings.push(`${label} between rendered desktop and rendered mobile DOM.`);
    }
  }

  if (desktop.body_text_length < 200) {
    warnings.push("Rendered desktop body text is very short; verify the page has useful visible content.");
  }
  if (mobile.body_text_length < Math.min(200, desktop.body_text_length * 0.5)) {
    warnings.push("Rendered mobile body text is much shorter than desktop; verify mobile-first content parity.");
  }
  if (mobile.same_origin_links < Math.min(3, desktop.same_origin_links)) {
    warnings.push("Rendered mobile exposes fewer same-origin links than desktop; verify crawlable mobile navigation.");
  }
  if (desktop.images_missing_alt || mobile.images_missing_alt) {
    warnings.push("Rendered DOM has images without alt text.");
  }

  return warnings;
}

async function extractSignals(page, baseUrl, surface) {
  return await page.evaluate(
    ({ baseUrl: currentBaseUrl, surface: currentSurface }) => {
      const clean = (value) => (value || "").replace(/\s+/g, " ").trim();
      const resolveUrl = (value) => {
        if (!value) return null;
        try {
          return new URL(value, currentBaseUrl).href.split("#")[0];
        } catch {
          return value;
        }
      };
      const metaContent = (name) => {
        const exact = document.querySelector(`meta[name="${name}"]`);
        return exact ? clean(exact.getAttribute("content")) || null : null;
      };

      const robotsMeta = Array.from(document.querySelectorAll("meta"))
        .filter((meta) => {
          const name = (meta.getAttribute("name") || "").toLowerCase();
          return name === "robots" || name === "googlebot";
        })
        .map((meta) => {
          const name = (meta.getAttribute("name") || "").toLowerCase();
          return `${name}: ${clean(meta.getAttribute("content"))}`;
        })
        .filter(Boolean)
        .join(", ");

      const openGraph = {};
      for (const meta of Array.from(document.querySelectorAll("meta[property^='og:']"))) {
        const key = meta.getAttribute("property");
        const value = clean(meta.getAttribute("content"));
        if (key && value) openGraph[key] = value;
      }

      const twitter = {};
      for (const meta of Array.from(document.querySelectorAll("meta"))) {
        const name = meta.getAttribute("name") || meta.getAttribute("property") || "";
        if (name.toLowerCase().startsWith("twitter:")) {
          const value = clean(meta.getAttribute("content"));
          if (value) twitter[name] = value;
        }
      }

      const jsonLdTypes = new Set();
      let jsonLdInvalid = 0;
      const collectTypes = (value) => {
        if (Array.isArray(value)) {
          for (const item of value) collectTypes(item);
          return;
        }
        if (!value || typeof value !== "object") return;
        const typeValue = value["@type"];
        if (typeof typeValue === "string") jsonLdTypes.add(typeValue);
        if (Array.isArray(typeValue)) {
          for (const item of typeValue) {
            if (typeof item === "string") jsonLdTypes.add(item);
          }
        }
        for (const child of Object.values(value)) collectTypes(child);
      };

      const jsonLdBlocks = Array.from(document.querySelectorAll('script[type^="application/ld+json"]'));
      for (const block of jsonLdBlocks) {
        try {
          collectTypes(JSON.parse(block.textContent || ""));
        } catch {
          jsonLdInvalid += 1;
        }
      }

      const currentOrigin = new URL(currentBaseUrl).origin;
      const anchors = Array.from(document.querySelectorAll("a[href]"))
        .map((anchor) => resolveUrl(anchor.getAttribute("href")))
        .filter(Boolean);
      const sameOriginLinks = anchors.filter((href) => {
        try {
          return new URL(href).origin === currentOrigin;
        } catch {
          return false;
        }
      });

      const images = Array.from(document.querySelectorAll("img"));

      return {
        surface: currentSurface,
        url: currentBaseUrl,
        title: clean(document.title) || null,
        meta_description: metaContent("description"),
        robots_meta: robotsMeta || null,
        canonical: resolveUrl(document.querySelector('link[rel~="canonical"]')?.getAttribute("href")),
        viewport: metaContent("viewport"),
        open_graph_count: Object.keys(openGraph).length,
        twitter_count: Object.keys(twitter).length,
        json_ld_blocks: jsonLdBlocks.length,
        json_ld_invalid: jsonLdInvalid,
        json_ld_types: Array.from(jsonLdTypes).sort(),
        hreflang_links: Array.from(document.querySelectorAll('link[rel~="alternate"][hreflang]'))
          .map((link) => ({
            hreflang: link.getAttribute("hreflang") || "",
            href: resolveUrl(link.getAttribute("href")),
          }))
          .sort((first, second) => `${first.hreflang}:${first.href}`.localeCompare(`${second.hreflang}:${second.href}`)),
        h1s: Array.from(document.querySelectorAll("h1")).map((h1) => clean(h1.textContent)).filter(Boolean),
        body_text_length: clean(document.body?.innerText || "").length,
        same_origin_links: new Set(sameOriginLinks).size,
        images_total: images.length,
        images_missing_alt: images.filter((image) => !clean(image.getAttribute("alt"))).length,
      };
    },
    { baseUrl, surface },
  );
}

async function auditSurface(browser, url, viewport, surface, timeoutMs, waitMs) {
  const context = await browser.newContext({
    viewport,
    userAgent: USER_AGENT,
  });
  const page = await context.newPage();
  page.setDefaultTimeout(timeoutMs);
  page.setDefaultNavigationTimeout(timeoutMs);
  const response = await page.goto(url, { waitUntil: "networkidle", timeout: timeoutMs });
  if (waitMs) {
    await page.waitForTimeout(waitMs);
  }
  const finalUrl = page.url();
  const rendered = await extractSignals(page, finalUrl, surface);
  const sourceHtml = response ? await response.text() : "";
  await context.close();
  return {
    status: response ? response.status() : null,
    final_url: finalUrl,
    rendered,
    source_html: sourceHtml,
  };
}

async function auditSource(browser, sourceHtml, url) {
  const context = await browser.newContext({ viewport: DESKTOP_VIEWPORT, userAgent: USER_AGENT });
  const page = await context.newPage();
  await page.setContent(sourceHtml || "<!doctype html><html><head></head><body></body></html>", {
    waitUntil: "domcontentloaded",
  });
  const source = await extractSignals(page, url, "source");
  await context.close();
  return source;
}

async function audit(url, timeoutMs, waitMs) {
  const { chromium } = await loadPlaywright();
  const browser = await chromium.launch({ headless: true });
  try {
    const desktopResult = await auditSurface(browser, url, DESKTOP_VIEWPORT, "desktop", timeoutMs, waitMs);
    const mobileResult = await auditSurface(browser, url, MOBILE_VIEWPORT, "mobile", timeoutMs, waitMs);
    const source = await auditSource(browser, desktopResult.source_html, url);
    const warnings = buildComparison(source, desktopResult.rendered, mobileResult.rendered);
    return {
      url,
      desktop_status: desktopResult.status,
      desktop_final_url: desktopResult.final_url,
      mobile_status: mobileResult.status,
      mobile_final_url: mobileResult.final_url,
      source,
      desktop: desktopResult.rendered,
      mobile: mobileResult.rendered,
      warnings,
    };
  } finally {
    await browser.close();
  }
}

function renderMarkdown(report) {
  const lines = [];
  lines.push(`# Rendered SEO Audit: ${report.url}`);
  lines.push("");
  lines.push("## Status");
  lines.push(`- desktop: \`${report.desktop_status}\` at ${report.desktop_final_url}`);
  lines.push(`- mobile: \`${report.mobile_status}\` at ${report.mobile_final_url}`);
  lines.push("");
  lines.push("## Signals");
  for (const surface of [report.source, report.desktop, report.mobile]) {
    lines.push(`### ${surface.surface}`);
    lines.push(`- title: ${surface.title || "missing"}`);
    lines.push(`- meta description: ${surface.meta_description || "missing"}`);
    lines.push(`- canonical: ${surface.canonical || "missing"}`);
    lines.push(`- robots meta: ${surface.robots_meta || "none"}`);
    lines.push(`- viewport: ${surface.viewport || "missing"}`);
    lines.push(`- H1 count: ${surface.h1s.length}`);
    lines.push(`- body text length: ${surface.body_text_length}`);
    lines.push(`- same-origin links: ${surface.same_origin_links}`);
    lines.push(`- JSON-LD blocks: ${surface.json_ld_blocks} (types: ${surface.json_ld_types.join(", ") || "none"}, invalid: ${surface.json_ld_invalid})`);
    lines.push(`- hreflang links: ${surface.hreflang_links.length}`);
    lines.push(`- Open Graph tags: ${surface.open_graph_count}`);
    lines.push(`- Twitter card tags: ${surface.twitter_count}`);
    lines.push(`- images missing alt: ${surface.images_missing_alt} / ${surface.images_total}`);
    lines.push("");
  }
  lines.push("## Warnings");
  if (report.warnings.length) {
    for (const warning of report.warnings) lines.push(`- ${warning}`);
  } else {
    lines.push("- none");
  }
  return `${lines.join("\n")}\n`;
}

async function main() {
  let args;
  try {
    args = parseArgs(process.argv.slice(2));
    if (args.help) {
      console.log(usage());
      return 0;
    }
    if (!args.url) {
      throw new Error("missing url");
    }
    const url = assertAbsoluteHttpUrl(args.url);
    const report = await audit(url, args.timeoutMs, args.waitMs);
    if (args.format === "json") {
      console.log(JSON.stringify(report, null, 2));
    } else {
      process.stdout.write(renderMarkdown(report));
    }
    return 0;
  } catch (error) {
    console.error(error.message);
    if (!args?.help) console.error(usage());
    return 2;
  }
}

main().then((code) => {
  process.exitCode = code;
});
