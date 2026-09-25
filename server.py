#!/usr/bin/env python3
"""
Static server for this Webflow export.

The exported pages link to each other without the ".html" extension
(e.g. /home-two, /about-us, /blog-post/xxx). Python's plain
`http.server` can't find those, so every click gives a 404.

This server maps clean URLs to the real files:
    /                -> index.html
    /home-two        -> home-two.html
    /project/foo     -> project/foo.html
    /dir/            -> dir/index.html (falls back to dir.html)
Unknown paths return the styled 404.html page with a 404 status.

Run:  python3 server.py         (defaults to port 8000)
      python3 server.py 9000
"""

import os
import sys
import posixpath
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote, urlsplit

ROOT = os.path.dirname(os.path.abspath(__file__))
HOME_PAGE = "index.html"
NOT_FOUND_PAGE = "404.html"

# Public, descriptive routes mapped to the original Webflow export files.
ROUTE_ALIASES = {
    "garde-corps-nice": "service-detail/complete-roof-replacement.html",
    "portails-sur-mesure-nice": "service-detail/professional-roof-installation.html",
    "portes-metalliques-nice": "service-detail/storm-damage-repair.html",
    "clotures-fer-forge-nice": "service-detail/roof-inspection-maintenance.html",
    "pergolas-marquises-nice": "service-detail/metal-roofing-systems.html",
    "rampes-escalier-nice": "service-detail/reliable-roof-repair.html",
    "realisations": "portfolio-one.html",
    "contact": "contact-two.html",
    "devis": "inquiry-form.html",
    "realisations/ouvrage-metallique-commercial-nice": "project/commercial-roof-renovation.html",
    "realisations/garde-corps-terrasse-panoramique": "project/harbor-point-commercial-roofing.html",
    "realisations/escalier-metallique-sur-mesure": "project/luxury-modern-villa-roofing.html",
    "realisations/cloture-sur-mesure-nice": "project/maple-ridge-roof-replacement.html",
    "realisations/garde-corps-acier-design": "project/metal-roof-installation.html",
    "realisations/portail-moderne-sur-mesure": "project/modern-villa-roof-solution.html",
    "realisations/structure-metallique-commerciale": "project/oakwood-commercial-flat-roof.html",
    "realisations/portail-coulissant-motorise": "project/professional-metal-roof-fitting.html",
    "realisations/ouvrage-metallique-residentiel": "project/residential-roof-installation.html",
    "realisations/rambarde-balcon-sur-mesure": "project/silver-crest-roof-renewal.html",
    "conseils/avantages-ferronnerie-sur-mesure": "blog-post/benefits-of-professional-roof-installation-for-long-term-protection.html",
    "conseils/erreurs-projet-ferronnerie": "blog-post/common-roofing-mistakes-homeowners-should-avoid-during-installation-projects.html",
    "conseils/entretien-ferronnerie": "blog-post/essential-roof-maintenance-tips-every-homeowner-should-know-to-protect.html",
    "conseils/choisir-materiau-ferronnerie": "blog-post/how-to-choose-the-right-roofing-material-for-your-home-today.html",
    "conseils/reperer-defauts-ferronnerie": "blog-post/how-to-spot-roof-damage-early-and-prevent-costly-issues-before-its-too-late.html",
    "conseils/climat-durabilite-ferronnerie": "blog-post/how-weather-conditions-affect-the-lifespan-of-your-roof-and-durability.html",
    "conseils/checklist-entretien-ferronnerie": "blog-post/seasonal-roof-maintenance-checklist-for-homeowners-to-protect-your-home-year-round.html",
    "conseils/meilleurs-materiaux-ferronnerie": "blog-post/top-5-roofing-materials-for-durability-style-and-ultimate-home-protection.html",
    "conseils/quand-reparer-ferronnerie": "blog-post/top-signs-your-roof-needs-immediate-repair-before-major-damage.html",
    "conseils/normes-garde-corps-hauteur-ecartement-resistance": "blog-post/normes-garde-corps-hauteur-ecartement-resistance.html",
    "conseils/remplissage-garde-corps-barreaux-cables-tole-verre": "blog-post/remplissage-garde-corps-barreaux-cables-tole-verre.html",
    "conseils/garde-corps-terrasse-balcon-escalier-differences": "blog-post/garde-corps-terrasse-balcon-escalier-differences.html",
}

# Legacy/template and previously published URLs permanently redirect here.
PERMANENT_REDIRECTS = {
    "/service-detail/complete-roof-replacement": "/garde-corps-nice/",
    "/service-detail/complete-roof-replacement.html": "/garde-corps-nice/",
    "/service-detail/professional-roof-installation": "/portails-sur-mesure-nice/",
    "/service-detail/professional-roof-installation.html": "/portails-sur-mesure-nice/",
    "/service-detail/storm-damage-repair": "/portes-metalliques-nice/",
    "/service-detail/storm-damage-repair.html": "/portes-metalliques-nice/",
    "/service-detail/roof-inspection-maintenance": "/clotures-fer-forge-nice/",
    "/service-detail/roof-inspection-maintenance.html": "/clotures-fer-forge-nice/",
    "/service-detail/metal-roofing-systems": "/pergolas-marquises-nice/",
    "/service-detail/metal-roofing-systems.html": "/pergolas-marquises-nice/",
    "/service-detail/reliable-roof-repair": "/rampes-escalier-nice/",
    "/service-detail/reliable-roof-repair.html": "/rampes-escalier-nice/",
    "/projects": "/realisations/",
    "/projects/": "/realisations/",
    "/pergolas-marquise": "/pergolas-marquises-nice/",
    "/pergolas-marquise/": "/pergolas-marquises-nice/",
    "/rampes-descalier": "/rampes-escalier-nice/",
    "/rampes-descalier/": "/rampes-escalier-nice/",
    "/home-one": "/",
    "/home-one.html": "/",
    "/home-two": "/",
    "/home-two.html": "/",
    "/home-three": "/",
    "/home-three.html": "/",
    "/portfolio-one": "/realisations/",
    "/portfolio-one.html": "/realisations/",
    "/portfolio-two": "/realisations/",
    "/portfolio-two.html": "/realisations/",
    "/portfolio-three": "/realisations/",
    "/portfolio-three.html": "/realisations/",
    "/contact-one": "/contact/",
    "/contact-one.html": "/contact/",
    "/contact-two": "/contact/",
    "/contact-two.html": "/contact/",
    "/contact-three": "/contact/",
    "/contact-three.html": "/contact/",
    "/inquiry-form": "/devis/",
    "/inquiry-form.html": "/devis/",
    "/project/commercial-roof-renovation.html": "/realisations/ouvrage-metallique-commercial-nice/",
    "/project/harbor-point-commercial-roofing.html": "/realisations/garde-corps-terrasse-panoramique/",
    "/project/luxury-modern-villa-roofing.html": "/realisations/escalier-metallique-sur-mesure/",
    "/project/maple-ridge-roof-replacement.html": "/realisations/cloture-sur-mesure-nice/",
    "/project/metal-roof-installation.html": "/realisations/garde-corps-acier-design/",
    "/project/modern-villa-roof-solution.html": "/realisations/portail-moderne-sur-mesure/",
    "/project/oakwood-commercial-flat-roof.html": "/realisations/structure-metallique-commerciale/",
    "/project/professional-metal-roof-fitting.html": "/realisations/portail-coulissant-motorise/",
    "/project/residential-roof-installation.html": "/realisations/ouvrage-metallique-residentiel/",
    "/project/silver-crest-roof-renewal.html": "/realisations/rambarde-balcon-sur-mesure/",
    "/blog-post/benefits-of-professional-roof-installation-for-long-term-protection.html": "/conseils/avantages-ferronnerie-sur-mesure/",
    "/blog-post/common-roofing-mistakes-homeowners-should-avoid-during-installation-projects.html": "/conseils/erreurs-projet-ferronnerie/",
    "/blog-post/essential-roof-maintenance-tips-every-homeowner-should-know-to-protect.html": "/conseils/entretien-ferronnerie/",
    "/blog-post/how-to-choose-the-right-roofing-material-for-your-home-today.html": "/conseils/choisir-materiau-ferronnerie/",
    "/blog-post/how-to-spot-roof-damage-early-and-prevent-costly-issues-before-its-too-late.html": "/conseils/reperer-defauts-ferronnerie/",
    "/blog-post/how-weather-conditions-affect-the-lifespan-of-your-roof-and-durability.html": "/conseils/climat-durabilite-ferronnerie/",
    "/blog-post/seasonal-roof-maintenance-checklist-for-homeowners-to-protect-your-home-year-round.html": "/conseils/checklist-entretien-ferronnerie/",
    "/blog-post/top-5-roofing-materials-for-durability-style-and-ultimate-home-protection.html": "/conseils/meilleurs-materiaux-ferronnerie/",
    "/blog-post/top-signs-your-roof-needs-immediate-repair-before-major-damage.html": "/conseils/quand-reparer-ferronnerie/",
    "/blog-post/normes-garde-corps-hauteur-ecartement-resistance.html": "/conseils/normes-garde-corps-hauteur-ecartement-resistance/",
    "/blog-post/remplissage-garde-corps-barreaux-cables-tole-verre.html": "/conseils/remplissage-garde-corps-barreaux-cables-tole-verre/",
    "/blog-post/garde-corps-terrasse-balcon-escalier-differences.html": "/conseils/garde-corps-terrasse-balcon-escalier-differences/",
}


class CleanURLHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Strip query string / fragment, decode %xx escapes.
        path = urlsplit(path).path
        path = unquote(path, errors="surrogatepass")
        path = posixpath.normpath(path)

        rel = path.lstrip("/")
        full = os.path.join(ROOT, rel)

        # "/" -> home page
        if rel in ("", "."):
            return os.path.join(ROOT, HOME_PAGE)

        # Language folders (/en/, /it/) mirror the French clean URLs.
        lang, _, lang_rest = rel.partition("/")
        if lang in ("en", "it"):
            lang_key = lang_rest.rstrip("/")
            if not lang_key:
                return os.path.join(ROOT, lang, HOME_PAGE)
            lang_alias = ROUTE_ALIASES.get(lang_key)
            if lang_alias:
                return os.path.join(ROOT, lang, lang_alias)

        alias = ROUTE_ALIASES.get(rel.rstrip("/"))
        if alias:
            return os.path.join(ROOT, alias)

        # Exact file (styles, scripts, images, *.html typed in full).
        if os.path.isfile(full):
            return full

        # Directory -> index.html, else <dir>.html
        if os.path.isdir(full):
            index = os.path.join(full, "index.html")
            if os.path.isfile(index):
                return index
            if os.path.isfile(full.rstrip("/") + ".html"):
                return full.rstrip("/") + ".html"

        # Clean URL -> add .html
        if not os.path.splitext(full)[1] and os.path.isfile(full + ".html"):
            return full + ".html"

        # Pages served at a clean URL (e.g. /realisations/) sit one or two levels
        # deeper than their real file, so their relative links (assets/..., ../about-us.html)
        # resolve to /realisations/assets/... Retry with leading segments stripped.
        parts = [p for p in rel.split("/") if p]
        for i in range(1, len(parts)):
            tail = "/".join(parts[i:])
            candidate = os.path.join(ROOT, tail)
            if os.path.isfile(candidate):
                return candidate
            alias_tail = ROUTE_ALIASES.get(tail.rstrip("/"))
            if alias_tail:
                return os.path.join(ROOT, alias_tail)
            if not os.path.splitext(candidate)[1] and os.path.isfile(candidate + ".html"):
                return candidate + ".html"

        # Nothing matched: hand back the 404 page path (status set in send_head).
        return os.path.join(ROOT, lang if lang in ("en", "it") else "", NOT_FOUND_PAGE)

    def send_head(self):
        requested_path = urlsplit(self.path).path
        redirect_target = PERMANENT_REDIRECTS.get(requested_path)
        if redirect_target:
            self.send_response(301)
            self.send_header("Location", redirect_target)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return None

        translated = self.translate_path(self.path)
        if os.path.basename(translated) == NOT_FOUND_PAGE and not self._asked_for_404():
            self.send_response(404)
            try:
                with open(translated, "rb") as f:
                    body = f.read()
            except OSError:
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", "13")
                self.end_headers()
                return None
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            import io
            return io.BytesIO(body)
        return super().send_head()

    def _asked_for_404(self):
        p = urlsplit(self.path).path.rstrip("/")
        return p in ("/404", "/404.html", "/en/404", "/en/404.html", "/it/404", "/it/404.html")

    def end_headers(self):
        if urlsplit(self.path).path == "/output/pdf/guide-de-marque-ferronnerie-du-rouret.pdf":
            self.send_header(
                "Content-Disposition",
                'attachment; filename="guide-de-marque-ferronnerie-du-rouret.pdf"',
            )
        if self.path.startswith("/assets/"):
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        else:
            self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        super().end_headers()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    os.chdir(ROOT)
    httpd = HTTPServer(("0.0.0.0", port), CleanURLHandler)
    print(f"Serving {ROOT}")
    print(f"  http://localhost:{port}/")
    print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
