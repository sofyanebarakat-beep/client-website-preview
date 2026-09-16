#!/usr/bin/env python3
"""Small, dependency-free SEO regression check for the static export."""

from pathlib import Path
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
