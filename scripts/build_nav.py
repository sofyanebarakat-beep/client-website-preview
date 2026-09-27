#!/usr/bin/env python3
"""
Write the main menu into every French page.

    Accueil · À propos · Nos prestations (submenu with every service)
    · Réalisations · Actualités

plus a tap-to-call button beside the mobile menu button.

The menu lives between <!-- nav:menu --> and <!-- /nav:menu --> inside
.rt-navbar-inner-menu-wrapper; edit SERVICES below and re-run:

    python3 scripts/build_nav.py && python3 scripts/build_i18n.py

Styles are in assets/css/nav.css. New French strings need an entry in
assets/i18n/translations.js for the EN / IT copies.
"""

import os
import re

from build_i18n import ROOT, FR_ONLY, depth_of, list_pages

START, END = "<!-- nav:menu -->", "<!-- /nav:menu -->"
CALL_START, CALL_END = "<!-- nav:call -->", "<!-- /nav:call -->"
PHONE, PHONE_LABEL = "+33769871108", "07 69 87 11 08"
CSS_LINK = '<link href="{p}assets/css/nav.css" rel="stylesheet"/>'
ICON = ("https://cdn.prod.website-files.com/69a196b4902215f53ac6be15/"
        "69a55bdd252f3181e36a4ed7_Vector%20(71).svg")

# (page, title, short description, thumbnail) — same order as the home page
SERVICES = [
    ("service-detail/complete-roof-replacement.html", "Garde-corps",
     "Balcons, terrasses et mezzanines",
     "assets/images/services/garde-corps-exterieur-fer-forge-nice-320.webp"),
    ("service-detail/professional-roof-installation.html", "Portails",
     "Battants, coulissants ou motorisés",
     "assets/images/services/portail-fer-forge-volutes-villa-nice-320.webp"),
    ("service-detail/storm-damage-repair.html", "Portes métalliques",
     "Portes d’entrée et de service en acier",
     "assets/images/services/porte-metallique-fer-forge-nice-480.webp"),
    ("service-detail/roof-inspection-maintenance.html", "Clôtures",
     "Clôtures en fer forgé et en métal",
     "assets/images/services/cloture-fer-forge-nice-360.webp"),
    ("service-detail/metal-roofing-systems.html", "Pergolas &amp; marquises",
     "Abris et auvents pour terrasses et entrées",
     "assets/images/services/pergola-adossee-verre-volutes-fer-forge-nice-320.webp"),
    ("service-detail/reliable-roof-repair.html", "Rampes d'escalier",
     "Intérieur et extérieur, sur mesure",
     "assets/images/services/rampe-escalier-fer-forge-volutes-noir-blanc-nice-320.webp"),
]


def section_of(page):
    if page == "index.html":
        return "home"
    if page == "about-us.html":
        return "about"
    if page == "service.html" or page.startswith("service-detail/"):
        return "services"
    if page.startswith(("portfolio-", "project/")):
        return "work"
    if page == "blog.html" or page.startswith("blog-post/"):
        return "news"
    return None


def top_link(href, label, active):
    cls = "rt-navigation-link-v1 rt-nav-top-link w-inline-block"
    cur = ""
    if active:
        cls += " rt-nav-active"
        cur = ' aria-current="page"'
    return '<a%s class="%s" href="%s">\n<div>%s</div>\n</a>' % (cur, cls, href, label)


def menu(page):
    p = "../" * depth_of(page)
    sec = section_of(page)
    items = []
    for href, title, desc, img in SERVICES:
        here = page == href
        items.append(
            '<a%s class="rt-service-link%s" href="%s%s">\n'
            '<img alt="" class="rt-service-thumb" height="56" loading="lazy" src="%s%s" width="56"/>\n'
            '<span class="rt-service-text">\n'
            '<span class="rt-service-title">%s</span>\n'
            '<span class="rt-service-desc">%s</span>\n'
            '</span>\n'
            '</a>' % (' aria-current="page"' if here else "", " rt-nav-active" if here else "",
                      p, href, p, img, title, desc)
        )
    return "\n".join([
        START,
        top_link(p + "index.html", "Accueil", sec == "home" and page == "index.html"),
        top_link(p + "about-us.html", "À propos", sec == "about"),
        '<div class="rt-navbar-dropdown-v1 rt-services-dropdown w-dropdown%s" data-delay="0" data-hover="true">'
        % (" rt-nav-active" if sec == "services" else ""),
        '<div class="rt-drop-down-toggle-v3 w-dropdown-toggle">',
        '<div class="rt-menu-font-v1">Nos prestations</div>',
        '<div class="w-layout-vflex rt-navbar-drop-down-icon-wrapper">',
        '<img alt="" class="rt-navbar-drop-down-icon" height="6" loading="lazy" src="%s" width="10"/>' % ICON,
        '</div>',
        '</div>',
        '<nav aria-label="Nos prestations" class="rt-navigation rt-services-menu w-dropdown-list">',
        '<div class="rt-services-menu-head">',
        '<span class="rt-services-menu-eyebrow">Nos prestations</span>',
        '<span class="rt-services-menu-sub">Fabriqué et posé sur mesure à Nice</span>',
        '</div>',
        '<div class="rt-services-grid">',
        "\n".join(items),
        '</div>',
        '<div class="rt-services-menu-foot">',
        '<a class="rt-services-all" href="%sservice.html">Voir toutes nos prestations →</a>' % p,
        '<a class="rt-services-cta" href="%sinquiry-form.html">Demander un devis gratuit</a>' % p,
        '</div>',
        '</nav>',
        '</div>',
        top_link(p + "portfolio-one.html", "Réalisations", sec == "work"),
        top_link(p + "blog.html", "Actualités", sec == "news"),
        END,
    ])


def call_button():
    return "\n".join([
        CALL_START,
        '<a aria-label="Appeler l’atelier au %s" class="rt-nav-call" href="tel:%s">' % (PHONE_LABEL, PHONE),
        '<svg aria-hidden="true" fill="none" height="20" stroke="currentColor" stroke-linecap="round" '
        'stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="20">'
        '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 '
        '19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 '
        '2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 '
        '2.81.7A2 2 0 0 1 22 16.92z"/></svg>',
        '</a>',
        CALL_END,
    ])


HAMBURGER = re.compile(r'<div class="rt-mobile-list-button w-nav-button"[^>]*>')
CALL_RE = re.compile(re.escape(CALL_START) + r".*?" + re.escape(CALL_END) + r"\n", re.S)

WRAPPER = '<div class="w-layout-hflex rt-navbar-inner-menu-wrapper">\n'
REGION = re.compile(
    re.escape(WRAPPER) + r"(?P<body>.*?)\n</div>\n(?=<div class=\"w-layout-vflex rt-nav-bottom-content\">)",
    re.S,
)


def main():
    changed = 0
    for page in list_pages():
        if page in FR_ONLY:
            continue
        path = os.path.join(ROOT, page)
        src = open(path, encoding="utf-8").read()
        m = REGION.search(src)
        if not m:
            continue
        doc = src[:m.start("body")] + menu(page) + src[m.end("body"):]
        doc = CALL_RE.sub("", doc)
        doc = HAMBURGER.sub(lambda h: call_button() + "\n" + h.group(0), doc, count=1)
        link = CSS_LINK.format(p="../" * depth_of(page))
        if "assets/css/nav.css" not in doc:
            anchor = "<!-- i18n:head -->" if "<!-- i18n:head -->" in doc else "</head>"
            doc = doc.replace(anchor, link + "\n" + anchor, 1)
        if doc != src:
            with open(path, "w", encoding="utf-8") as f:
                f.write(doc)
            changed += 1
    print("Menu written to %d French pages." % changed)


if __name__ == "__main__":
    main()
