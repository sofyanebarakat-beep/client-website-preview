#!/usr/bin/env python3
"""Small, dependency-free SEO regression check for the static export."""

from pathlib import Path
import html
import json
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_PAGES = [
    ROOT / "index.html",
    ROOT / "about-us.html",
    ROOT / "service.html",
    ROOT / "blog.html",
    ROOT / "faq.html",
    ROOT / "contact-two.html",
    ROOT / "inquiry-form.html",
    ROOT / "portfolio-one.html",
    *sorted((ROOT / "service-detail").glob("*.html")),
    *sorted((ROOT / "project").glob("*.html")),
    *sorted((ROOT / "blog-post").glob("*.html")),
]


def count(pattern, source):
    return len(re.findall(pattern, source, flags=re.I | re.S))


errors = []
for page in PUBLIC_PAGES:
    source = page.read_text(encoding="utf-8")
    for label, pattern in {
        "title": r"<title>.*?</title>",
        "description": r'<meta[^>]+name="description"',
        "canonical": r'<link[^>]+rel="canonical"',
        "H1": r"<h1(?:\s|>)",
    }.items():
        found = count(pattern, source)
        if found != 1:
            errors.append(f"{page.relative_to(ROOT)}: expected 1 {label}, found {found}")
    if re.search(r'(?:href|src)="https://flampt\.webflow\.io', source):
        errors.append(f"{page.relative_to(ROOT)}: contains a Webflow demo-domain link")
    name = page.relative_to(ROOT)
    title = html.unescape((re.search(r"<title>(.*?)</title>", source, re.S) or [None, ""])[1])
    if len(title) > 62:
        errors.append(f"{name}: title is {len(title)} chars (max 62, Google truncates)")
    desc = re.search(r'<meta content="([^"]*)" name="description"', source)
    if desc and len(html.unescape(desc.group(1))) > 160:
        errors.append(f"{name}: meta description is {len(html.unescape(desc.group(1)))} chars (max 160)")
    if re.search(r'<meta content="[^"]*cdn\.prod\.website-files\.com[^"]*" (?:property="og:image"|name="twitter:image")', source):
        errors.append(f"{name}: social image is a template stock photo hosted on the Webflow CDN")
    if re.search(r'<a [^>]*href="https://(?:www\.)?(?:radianttemplates\.com|webflow\.com)[^"]*"(?![^>]*nofollow)', source):
        errors.append(f"{name}: dofollow link to the template vendor")
    if re.search(r'<img [^>]*\salt="[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+"', source):
        errors.append(f"{name}: image alt text is a template file name (use a description, or alt=\"\" if decorative)")
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', source, re.S):
        try:
            data = json.loads(block)
        except ValueError:
            errors.append(f"{name}: invalid JSON-LD")
            continue
        for node in data.get("@graph", [data]):
            if node.get("@type") == "WebSite" and not str(node.get("url", "")).startswith("https://"):
                errors.append(f"{name}: WebSite JSON-LD url must be absolute")
            if node.get("@type") == "LocalBusiness":
                for key in ("telephone", "address", "url", "image", "sameAs"):
                    if key not in node:
                        errors.append(f"{name}: LocalBusiness JSON-LD is missing {key}")

for page in (ROOT / "service-detail").glob("*.html"):
    source = page.read_text(encoding="utf-8")
    hero = re.search(r'<img[^>]+class="rt-hero-background-image"[^>]*>', source)
    if not hero or '/assets/images/services/' not in hero.group(0) or 'alt="' not in hero.group(0):
        errors.append(f"{page.relative_to(ROOT)}: service hero is not a local crawlable image")

try:
    ET.parse(ROOT / "sitemap.xml")
except ET.ParseError as exc:
    errors.append(f"sitemap.xml: {exc}")

if errors:
    print("SEO audit failed:")
    print("\n".join(f"- {error}" for error in errors))
    sys.exit(1)

print(f"SEO audit passed for {len(PUBLIC_PAGES)} public pages.")
