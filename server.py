#!/usr/bin/env python3
"""
Local preview server for the website (the repository root).

Every page is a folder with an index.html (/a-propos/, /garde-corps-nice/ ...),
exactly as GitHub Pages serves it:
    /                   -> index.html
    /a-propos/          -> a-propos/index.html
    /a-propos           -> 301 to /a-propos/
Old addresses (about-us.html, service-detail/..., project/...) redirect to the
new clean URLs. src/, archive/ and scripts/ are never served. Unknown paths
return the styled 404 page with a 404 status.

Run:  python3 server.py         (defaults to port 8000)
      python3 server.py 9000
"""

import io
import os
import posixpath
import sys
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote, urlsplit

ROOT = os.path.dirname(os.path.abspath(__file__))
NOT_FOUND_PAGE = "404.html"
PRIVATE_DIRS = ("src", "archive", "scripts", ".git")

# Old addresses of the site -> their clean URL (also applied under /en/ and /it/).
PERMANENT_REDIRECTS = {
    "/about-us": "/a-propos/",
    "/about-us.html": "/a-propos/",
    "/blog": "/conseils/",
    "/blog-post/benefits-of-professional-roof-installation-for-long-term-protection": "/conseils/avantages-ferronnerie-sur-mesure/",
    "/blog-post/benefits-of-professional-roof-installation-for-long-term-protection.html": "/conseils/avantages-ferronnerie-sur-mesure/",
    "/blog-post/cloture-fer-forge-sur-muret": "/conseils/cloture-fer-forge-sur-muret/",
    "/blog-post/cloture-fer-forge-sur-muret.html": "/conseils/cloture-fer-forge-sur-muret/",
    "/blog-post/cloture-pleine-ou-ajouree-choisir": "/conseils/cloture-pleine-ou-ajouree-choisir/",
    "/blog-post/cloture-pleine-ou-ajouree-choisir.html": "/conseils/cloture-pleine-ou-ajouree-choisir/",
    "/blog-post/common-roofing-mistakes-homeowners-should-avoid-during-installation-projects": "/conseils/erreurs-projet-ferronnerie/",
    "/blog-post/common-roofing-mistakes-homeowners-should-avoid-during-installation-projects.html": "/conseils/erreurs-projet-ferronnerie/",
    "/blog-post/couleur-finition-porte-metallique": "/conseils/couleur-finition-porte-metallique/",
    "/blog-post/couleur-finition-porte-metallique.html": "/conseils/couleur-finition-porte-metallique/",
    "/blog-post/dimensions-portail-sur-mesure": "/conseils/dimensions-portail-sur-mesure/",
    "/blog-post/dimensions-portail-sur-mesure.html": "/conseils/dimensions-portail-sur-mesure/",
    "/blog-post/entretien-garde-corps-exterieur-bord-de-mer": "/conseils/entretien-garde-corps-exterieur-bord-de-mer/",
    "/blog-post/entretien-garde-corps-exterieur-bord-de-mer.html": "/conseils/entretien-garde-corps-exterieur-bord-de-mer/",
    "/blog-post/essential-roof-maintenance-tips-every-homeowner-should-know-to-protect": "/conseils/entretien-ferronnerie/",
    "/blog-post/essential-roof-maintenance-tips-every-homeowner-should-know-to-protect.html": "/conseils/entretien-ferronnerie/",
    "/blog-post/garde-corps-fer-forge-style-maison": "/conseils/garde-corps-fer-forge-style-maison/",
    "/blog-post/garde-corps-fer-forge-style-maison.html": "/conseils/garde-corps-fer-forge-style-maison/",
    "/blog-post/garde-corps-terrasse-balcon-escalier-differences": "/conseils/garde-corps-terrasse-balcon-escalier-differences/",
    "/blog-post/garde-corps-terrasse-balcon-escalier-differences.html": "/conseils/garde-corps-terrasse-balcon-escalier-differences/",
    "/blog-post/garde-corps-verre-ou-metal-choisir": "/conseils/garde-corps-verre-ou-metal-choisir/",
    "/blog-post/garde-corps-verre-ou-metal-choisir.html": "/conseils/garde-corps-verre-ou-metal-choisir/",
    "/blog-post/hauteur-cloture-regles-urbanisme": "/conseils/hauteur-cloture-regles-urbanisme/",
    "/blog-post/hauteur-cloture-regles-urbanisme.html": "/conseils/hauteur-cloture-regles-urbanisme/",
    "/blog-post/hauteur-rampe-escalier-securite": "/conseils/hauteur-rampe-escalier-securite/",
    "/blog-post/hauteur-rampe-escalier-securite.html": "/conseils/hauteur-rampe-escalier-securite/",
    "/blog-post/how-to-choose-the-right-roofing-material-for-your-home-today": "/conseils/choisir-materiau-ferronnerie/",
    "/blog-post/how-to-choose-the-right-roofing-material-for-your-home-today.html": "/conseils/choisir-materiau-ferronnerie/",
    "/blog-post/how-to-spot-roof-damage-early-and-prevent-costly-issues-before-its-too-late": "/conseils/reperer-defauts-ferronnerie/",
    "/blog-post/how-to-spot-roof-damage-early-and-prevent-costly-issues-before-its-too-late.html": "/conseils/reperer-defauts-ferronnerie/",
    "/blog-post/how-weather-conditions-affect-the-lifespan-of-your-roof-and-durability": "/conseils/climat-durabilite-ferronnerie/",
    "/blog-post/how-weather-conditions-affect-the-lifespan-of-your-roof-and-durability.html": "/conseils/climat-durabilite-ferronnerie/",
    "/blog-post/marquise-verre-entree-maison": "/conseils/marquise-verre-entree-maison/",
    "/blog-post/marquise-verre-entree-maison.html": "/conseils/marquise-verre-entree-maison/",
    "/blog-post/motoriser-portail-fer-forge": "/conseils/motoriser-portail-fer-forge/",
    "/blog-post/motoriser-portail-fer-forge.html": "/conseils/motoriser-portail-fer-forge/",
    "/blog-post/normes-garde-corps-hauteur-ecartement-resistance": "/conseils/normes-garde-corps-hauteur-ecartement-resistance/",
    "/blog-post/normes-garde-corps-hauteur-ecartement-resistance.html": "/conseils/normes-garde-corps-hauteur-ecartement-resistance/",
    "/blog-post/pergola-adossee-ou-autoportee": "/conseils/pergola-adossee-ou-autoportee/",
    "/blog-post/pergola-adossee-ou-autoportee.html": "/conseils/pergola-adossee-ou-autoportee/",
    "/blog-post/portail-battant-ou-coulissant-choisir": "/conseils/portail-battant-ou-coulissant-choisir/",
    "/blog-post/portail-battant-ou-coulissant-choisir.html": "/conseils/portail-battant-ou-coulissant-choisir/",
    "/blog-post/porte-metallique-portillon-securiser-acces": "/conseils/porte-metallique-portillon-securiser-acces/",
    "/blog-post/porte-metallique-portillon-securiser-acces.html": "/conseils/porte-metallique-portillon-securiser-acces/",
    "/blog-post/portillon-metallique-choisir-serrure": "/conseils/portillon-metallique-choisir-serrure/",
    "/blog-post/portillon-metallique-choisir-serrure.html": "/conseils/portillon-metallique-choisir-serrure/",
    "/blog-post/rampe-escalier-exterieure-choisir": "/conseils/rampe-escalier-exterieure-choisir/",
    "/blog-post/rampe-escalier-exterieure-choisir.html": "/conseils/rampe-escalier-exterieure-choisir/",
    "/blog-post/rampe-escalier-interieure-style": "/conseils/rampe-escalier-interieure-style/",
    "/blog-post/rampe-escalier-interieure-style.html": "/conseils/rampe-escalier-interieure-style/",
    "/blog-post/remplissage-garde-corps-barreaux-cables-tole-verre": "/conseils/remplissage-garde-corps-barreaux-cables-tole-verre/",
    "/blog-post/remplissage-garde-corps-barreaux-cables-tole-verre.html": "/conseils/remplissage-garde-corps-barreaux-cables-tole-verre/",
    "/blog-post/seasonal-roof-maintenance-checklist-for-homeowners-to-protect-your-home-year-round": "/conseils/checklist-entretien-ferronnerie/",
    "/blog-post/seasonal-roof-maintenance-checklist-for-homeowners-to-protect-your-home-year-round.html": "/conseils/checklist-entretien-ferronnerie/",
    "/blog-post/toiture-pergola-metallique-choisir": "/conseils/toiture-pergola-metallique-choisir/",
    "/blog-post/toiture-pergola-metallique-choisir.html": "/conseils/toiture-pergola-metallique-choisir/",
    "/blog-post/top-5-roofing-materials-for-durability-style-and-ultimate-home-protection": "/conseils/meilleurs-materiaux-ferronnerie/",
    "/blog-post/top-5-roofing-materials-for-durability-style-and-ultimate-home-protection.html": "/conseils/meilleurs-materiaux-ferronnerie/",
    "/blog-post/top-signs-your-roof-needs-immediate-repair-before-major-damage": "/conseils/quand-reparer-ferronnerie/",
    "/blog-post/top-signs-your-roof-needs-immediate-repair-before-major-damage.html": "/conseils/quand-reparer-ferronnerie/",
    "/blog.html": "/conseils/",
    "/contact-one": "/contact/",
    "/contact-one.html": "/contact/",
    "/contact-three": "/contact/",
    "/contact-three.html": "/contact/",
    "/contact-two": "/contact/",
    "/contact-two.html": "/contact/",
    "/home-one": "/",
    "/home-one.html": "/",
    "/home-three": "/",
    "/home-three.html": "/",
    "/home-two": "/",
    "/home-two.html": "/",
    "/index.html": "/",
    "/inquiry-form": "/devis/",
    "/inquiry-form.html": "/devis/",
    "/pergolas-marquise": "/pergolas-marquises-nice/",
    "/pergolas-marquise/": "/pergolas-marquises-nice/",
    "/portfolio-one": "/realisations/",
    "/portfolio-one.html": "/realisations/",
    "/portfolio-three": "/realisations/",
    "/portfolio-three.html": "/realisations/",
    "/portfolio-two": "/realisations/",
    "/portfolio-two.html": "/realisations/",
    "/project/commercial-roof-renovation": "/realisations/ouvrage-metallique-commercial-nice/",
    "/project/commercial-roof-renovation.html": "/realisations/ouvrage-metallique-commercial-nice/",
    "/project/harbor-point-commercial-roofing": "/realisations/garde-corps-terrasse-panoramique/",
    "/project/harbor-point-commercial-roofing.html": "/realisations/garde-corps-terrasse-panoramique/",
    "/project/luxury-modern-villa-roofing": "/realisations/escalier-metallique-sur-mesure/",
    "/project/luxury-modern-villa-roofing.html": "/realisations/escalier-metallique-sur-mesure/",
    "/project/maple-ridge-roof-replacement": "/realisations/cloture-sur-mesure-nice/",
    "/project/maple-ridge-roof-replacement.html": "/realisations/cloture-sur-mesure-nice/",
    "/project/metal-roof-installation": "/realisations/garde-corps-acier-design/",
    "/project/metal-roof-installation.html": "/realisations/garde-corps-acier-design/",
    "/project/modern-villa-roof-solution": "/realisations/portail-moderne-sur-mesure/",
    "/project/modern-villa-roof-solution.html": "/realisations/portail-moderne-sur-mesure/",
    "/project/oakwood-commercial-flat-roof": "/realisations/structure-metallique-commerciale/",
    "/project/oakwood-commercial-flat-roof.html": "/realisations/structure-metallique-commerciale/",
    "/project/professional-metal-roof-fitting": "/realisations/portail-coulissant-motorise/",
    "/project/professional-metal-roof-fitting.html": "/realisations/portail-coulissant-motorise/",
    "/project/residential-roof-installation": "/realisations/ouvrage-metallique-residentiel/",
    "/project/residential-roof-installation.html": "/realisations/ouvrage-metallique-residentiel/",
    "/project/silver-crest-roof-renewal": "/realisations/rambarde-balcon-sur-mesure/",
    "/project/silver-crest-roof-renewal.html": "/realisations/rambarde-balcon-sur-mesure/",
    "/projects": "/realisations/",
    "/projects/": "/realisations/",
    "/rampes-descalier": "/rampes-escalier-nice/",
    "/rampes-descalier/": "/rampes-escalier-nice/",
    "/service": "/services/",
    "/service-detail/complete-roof-replacement": "/garde-corps-nice/",
    "/service-detail/complete-roof-replacement.html": "/garde-corps-nice/",
    "/service-detail/metal-roofing-systems": "/pergolas-marquises-nice/",
    "/service-detail/metal-roofing-systems.html": "/pergolas-marquises-nice/",
    "/service-detail/professional-roof-installation": "/portails-sur-mesure-nice/",
    "/service-detail/professional-roof-installation.html": "/portails-sur-mesure-nice/",
    "/service-detail/reliable-roof-repair": "/rampes-escalier-nice/",
    "/service-detail/reliable-roof-repair.html": "/rampes-escalier-nice/",
    "/service-detail/roof-inspection-maintenance": "/clotures-fer-forge-nice/",
    "/service-detail/roof-inspection-maintenance.html": "/clotures-fer-forge-nice/",
    "/service-detail/storm-damage-repair": "/portes-metalliques-nice/",
    "/service-detail/storm-damage-repair.html": "/portes-metalliques-nice/",
    "/service.html": "/services/",
}


class CleanURLHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        rel = posixpath.normpath(unquote(urlsplit(path).path, errors="surrogatepass")).lstrip("/")
        if rel in ("", "."):
            return os.path.join(ROOT, "index.html")
        if rel.split("/")[0] not in PRIVATE_DIRS:
            full = os.path.join(ROOT, rel)
            if os.path.isfile(full):
                return full
            if os.path.isfile(os.path.join(full, "index.html")):
                return os.path.join(full, "index.html")
        lang = rel.split("/")[0]
        return os.path.join(ROOT, lang if lang in ("en", "it") else "", NOT_FOUND_PAGE)

    def _redirect(self, target):
        self.send_response(301)
        self.send_header("Location", target)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def send_head(self):
        path = urlsplit(self.path).path
        for prefix in ("", "/en", "/it"):
            if prefix and not path.startswith(prefix + "/"):
                continue
            target = PERMANENT_REDIRECTS.get(path[len(prefix):])
            if target:
                self._redirect(prefix + target)
                return None

        # Folder URL without its trailing slash: redirect like GitHub Pages does,
        # so relative links on the page resolve against the folder.
        rel = unquote(path).lstrip("/")
        if rel and not path.endswith("/") and rel.split("/")[0] not in PRIVATE_DIRS \
                and os.path.isfile(os.path.join(ROOT, rel, "index.html")):
            self._redirect(path + "/")
            return None

        translated = self.translate_path(self.path)
        if os.path.basename(translated) == NOT_FOUND_PAGE and os.path.basename(path) != NOT_FOUND_PAGE:
            with open(translated, "rb") as f:
                body = f.read()
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            return io.BytesIO(body)
        return super().send_head()

    def end_headers(self):
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
    httpd = ThreadingHTTPServer(("0.0.0.0", port), CleanURLHandler)
    print(f"Serving {ROOT}")
    print(f"  http://localhost:{port}/")
    print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
