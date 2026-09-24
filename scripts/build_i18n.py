#!/usr/bin/env python3
"""
Build the multilingual site.

French pages in the repo are the SOURCE. This script

  * (re)writes each French page with hreflang / og:locale / language-switcher
    metadata and localisation attributes on forms,
  * generates a fully translated static copy of every page under /en/ and /it/
    using assets/i18n/translations.js as the dictionary,
  * regenerates sitemap.xml with hreflang alternates for the three languages.

Run after ANY edit to a French page or to translations.js:

    python3 scripts/build_i18n.py            # build
    python3 scripts/build_i18n.py --report   # also list text with no translation

The output is committed (GitHub Pages serves static files), so do not edit
files under en/ or it/ by hand: they are overwritten on every build.
"""

import html
import json
import os
import re
import shutil
import subprocess
import sys
from urllib.parse import urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://ferronnerie-rouret.com"
LANGS = ("fr", "en", "it")
GENERATED = ("en", "it")
OG_LOCALE = {"fr": "fr_FR", "en": "en_GB", "it": "it_IT"}
SKIP_DIRS = {"assets", "en", "it", "scripts", "output", "tmp", "node_modules", ".git"}
FR_ONLY = {"style-guide.html"}            # internal brand guide: French only
NON_PAGE_PREFIXES = ("output/", "sitemap.xml", "robots.txt", "style-guide.html")

HEAD_START, HEAD_END = "<!-- i18n:head -->", "<!-- /i18n:head -->"

TAG_RE = r"<(?:[^>\"']|\"[^\"]*\"|'[^']*')*>"
TOKEN = re.compile(
    r"(?P<comment><!--.*?-->)"
    r"|(?P<raw><(?P<rawtag>script|style)\b(?:[^>\"']|\"[^\"]*\"|'[^']*')*>.*?</(?P=rawtag)\s*>)"
    r"|(?P<tag>" + TAG_RE + r")"
    r"|(?P<text>[^<]+|<)",
    re.S | re.I,
)
ATTR = re.compile(
    r"(?P<pre>\s)(?P<name>alt|title|placeholder|aria-label|data-wait|content|value)="
    r"(?:\"(?P<dq>[^\"]*)\"|'(?P<sq>[^']*)')"
)
META_KEYS = {
    "description", "og:title", "og:description", "twitter:title", "twitter:description",
}


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def load_dictionary():
    js = os.path.join(ROOT, "assets", "i18n", "translations.js")
    out = subprocess.check_output(
        ["node", "-e",
         "global.window={};require(process.argv[1]);"
         "console.log(JSON.stringify(window.SITE_TRANSLATIONS))", js]
    )
    return json.loads(out)


def list_pages():
    pages = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for f in filenames:
            if f.endswith(".html"):
                pages.append(os.path.relpath(os.path.join(dirpath, f), ROOT).replace(os.sep, "/"))
    return sorted(pages)


class Translator:
    def __init__(self, dictionary, lang):
        self.d, self.lang, self.missing = dictionary, lang, set()

    def lookup(self, raw):
        key = norm(html.unescape(raw))
        if not key:
            return None
        entry = self.d.get(key)
        if entry and entry.get(self.lang):
            return entry[self.lang]
        if re.search(r"[A-Za-zÀ-ÿ]{3}", key):
            self.missing.add(key)
        return None

    def text(self, raw):
        tr = self.lookup(raw)
        if tr is None:
            return raw
        lead = re.match(r"\s*", raw).group(0)
        trail = re.search(r"\s*$", raw).group(0)
        return lead + html.escape(tr, quote=False) + trail

    def attr_value(self, raw):
        tr = self.lookup(raw)
        return raw if tr is None else html.escape(tr, quote=True)

    def json_ld(self, body):
        try:
            data = json.loads(body)
        except ValueError:
            return body

        def walk(o):
            if isinstance(o, str):
                entry = self.d.get(norm(o))
                return entry[self.lang] if entry and entry.get(self.lang) else o
            if isinstance(o, list):
                return [walk(x) for x in o]
            if isinstance(o, dict):
                return {k: walk(v) for k, v in o.items()}
            return o

        return json.dumps(walk(data), ensure_ascii=False, separators=(", ", ": "))


def tag_name(tag):
    m = re.match(r"<\s*([A-Za-z][A-Za-z0-9-]*)", tag)
    return m.group(1).lower() if m else ""


def attr_of(tag, name):
    m = re.search(r"\s" + re.escape(name) + r"=(?:\"([^\"]*)\"|'([^']*)')", tag)
    return (m.group(1) if m.group(1) is not None else m.group(2)) if m else None


def translate_tag(tag, tr):
    name = tag_name(tag)
    is_meta = name == "meta"
    meta_key = (attr_of(tag, "name") or attr_of(tag, "property") or "").lower() if is_meta else ""
    itype = (attr_of(tag, "type") or "").lower() if name == "input" else ""

    def repl(m):
        an = m.group("name")
        if an == "content" and not (is_meta and meta_key in META_KEYS):
            return m.group(0)
        if an == "value" and itype not in ("submit", "button", "reset"):
            return m.group(0)
        raw = m.group("dq") if m.group("dq") is not None else m.group("sq")
        return '%s%s="%s"' % (m.group("pre"), an, tr.attr_value(raw))

    return ATTR.sub(repl, tag)


def translate_document(src, tr):
    out = []
    for m in TOKEN.finditer(src):
        if m.group("comment"):
            out.append(m.group(0))
        elif m.group("raw"):
            raw = m.group(0)
            if m.group("rawtag").lower() == "script" and "ld+json" in raw[:200]:
                head, body, tail = re.match(r"(<script[^>]*>)(.*?)(</script\s*>)", raw, re.S | re.I).groups()
                raw = head + tr.json_ld(body) + tail
            out.append(raw)
        elif m.group("tag"):
            out.append(translate_tag(m.group(0), tr))
        else:
            out.append(tr.text(m.group(0)))
    return "".join(out)


# ---------------------------------------------------------------- paths / URLs

def depth_of(page):
    return page.count("/")


def canonical_path(base):
    m = re.search(r'<link[^>]*rel="canonical"[^>]*>', base)
    if not m:
        return None
    href = attr_of(m.group(0), "href")
    if not href or not href.startswith(SITE):
        return None
    return urlsplit(href).path or "/"


def lang_url(canon_path, lang):
    if lang == "fr":
        return SITE + canon_path
    return SITE + "/" + lang + canon_path


def rewrite_paths(src, page, pages_set, lang_dir_prefix):
    """Fix relative links inside a generated (/en, /it) copy: pages stay inside the
    language folder, everything else (assets, files) moves up one level."""
    page_dir = os.path.dirname(page)

    def fix_href(m):
        val = m.group(2)
        if re.match(r"^(?:[a-z][a-z0-9+.-]*:|//|#|/)", val, re.I):
            return m.group(0)
        target = os.path.normpath(os.path.join(page_dir, val.split("#")[0].split("?")[0])).replace(os.sep, "/")
        if target.startswith(NON_PAGE_PREFIXES) or (target.endswith(".html") and target not in pages_set):
            return '%s"../%s"' % (m.group(1), val)
        return m.group(0)

    def process(chunk):
        chunk = re.sub(r'(\shref=)"([^"]*)"', fix_href, chunk)
        return re.sub(
            r"(?P<pre>[\s\"',(])(?P<up>(?:\.\./)*)assets/",
            lambda m: m.group("pre") + m.group("up") + "../assets/",
            chunk,
        )

    out = []
    for m in TOKEN.finditer(src):
        if m.group("tag") or (m.group("raw") and m.group("rawtag").lower() == "style"):
            out.append(process(m.group(0)))
        elif m.group("raw"):
            # <script src="..."> : rewrite the opening tag only, never the script body
            head = re.match(TAG_RE, m.group(0)).group(0)
            out.append(process(head) + m.group(0)[len(head):])
        else:
            out.append(m.group(0))
    return "".join(out)


# ---------------------------------------------------------------- normalise FR

def normalise_base(src, page):
    """Strip everything this script adds so it can be re-added cleanly."""
    src = re.sub(re.escape(HEAD_START) + r".*?" + re.escape(HEAD_END) + r"\n?", "", src, flags=re.S)
    src = re.sub(r'<input type="hidden" name="Langue"[^>]*/>', "", src)
    src = re.sub(r'<style id="i18n-early">.*?</style><script>.*?</script>\n?', "", src, flags=re.S)
    src = re.sub(r'<script src="[^"]*assets/i18n/translations\.js"[^>]*>\s*</script>\s*', "", src)
    src = re.sub(r'\s*<meta content="[^"]*" property="og:locale(?::alternate)?"\s*/>', "", src)

    rel_assets = "../" * depth_of(page) + "assets/"

    def abs_assets(chunk):
        return re.sub(r"(?<=[(\"'\s,])/assets/", rel_assets, chunk)

    out = []
    for m in TOKEN.finditer(src):
        if m.group("tag") or (m.group("raw") and m.group("rawtag").lower() == "style"):
            out.append(abs_assets(m.group(0)))
        else:
            out.append(m.group(0))
    src = "".join(out)

    def field_attrs(m):
        tag = m.group(0)
        itype = (attr_of(tag, "type") or "").lower()
        name = attr_of(tag, "name") or ""
        add = []
        if itype == "tel":
            add += [("inputmode", "tel"), ("autocomplete", "tel")]
        elif itype == "email":
            add += [("autocomplete", "email")]
        elif name in ("Nom-complet", "Your-name"):
            add += [("autocomplete", "name")]
        for k, v in add:
            if attr_of(tag, k) is None:
                tag = tag[:-2] + ' %s="%s"/>' % (k, v) if tag.endswith("/>") else tag[:-1] + ' %s="%s">' % (k, v)
        return tag

    return re.sub(r"<input\b[^>]*>", field_attrs, src)


def head_block(page, lang, canon):
    depth = depth_of(page) + (1 if lang != "fr" else 0)
    lines = [
        HEAD_START,
        '<meta name="i18n-lang" content="%s"/>' % lang,
        '<meta name="i18n-path" content="%s"/>' % page,
        '<meta name="i18n-root" content="%s"/>' % ("../" * depth),
    ]
    if canon:
        for l in LANGS:
            lines.append('<link href="%s" hreflang="%s" rel="alternate"/>' % (lang_url(canon, l), l))
        lines.append('<link href="%s" hreflang="x-default" rel="alternate"/>' % lang_url(canon, "fr"))
        lines.append('<meta content="%s" property="og:locale"/>' % OG_LOCALE[lang])
        for l in LANGS:
            if l != lang:
                lines.append('<meta content="%s" property="og:locale:alternate"/>' % OG_LOCALE[l])
    lines.append(HEAD_END)
    return "\n".join(lines) + "\n"


def render(base, page, lang, dictionary, pages_set, translators):
    canon = canonical_path(base) if page not in FR_ONLY else None
    doc = base
    if lang != "fr":
        tr = translators[lang]
        doc = translate_document(doc, tr)
        doc = rewrite_paths(doc, page, pages_set, lang)
        doc = re.sub(r'(<html\b[^>]*\blang=")fr(")', r"\g<1>%s\g<2>" % lang, doc, count=1)
        if canon:
            url = lang_url(canon, lang)
            doc = re.sub(r'(<link[^>]*href=")[^"]*("[^>]*rel="canonical")', r"\g<1>%s\g<2>" % url, doc, count=1)
            doc = re.sub(r'(<meta content=")[^"]*(" property="og:url")', r"\g<1>%s\g<2>" % url, doc, count=1)
    # hidden field: tells the workshop which language the visitor used
    doc = re.sub(
        r"(<form\b[^>]*>)",
        lambda m: m.group(1) + '<input type="hidden" name="Langue" data-name="Langue" value="%s"/>' % lang,
        doc,
    )
    if page in FR_ONLY:
        return doc
    return doc.replace("</head>", head_block(page, lang, canon) + "</head>", 1)


# ---------------------------------------------------------------- sitemap

def build_sitemap(canon_by_page):
    path = os.path.join(ROOT, "sitemap.xml")
    s = open(path, encoding="utf-8").read()
    if "xmlns:xhtml" not in s:
        s = s.replace("<urlset ", '<urlset xmlns:xhtml="http://www.w3.org/1999/xhtml" ', 1)
    blocks = re.findall(r"  <url>.*?</url>\n", s, re.S)
    fr_blocks = [b for b in blocks if not re.search(r"<loc>%s/(?:en|it)/" % re.escape(SITE), b)]

    def alternates(canon):
        rows = ['    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>\n' % (l, lang_url(canon, l)) for l in LANGS]
        rows.append('    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>\n' % lang_url(canon, "fr"))
        return "".join(rows)

    known = set(canon_by_page.values())
    out_blocks = []
    for b in fr_blocks:
        b = re.sub(r"    <xhtml:link[^>]*/>\n", "", b)
        loc = re.search(r"<loc>(.*?)</loc>", b).group(1)
        canon = urlsplit(loc).path or "/"
        if canon in known:
            b = b.replace("  </url>", alternates(canon) + "  </url>")
        out_blocks.append(b)
        if canon in known:
            lastmod = re.search(r"<lastmod>.*?</lastmod>", b)
            for l in GENERATED:
                out_blocks.append(
                    "  <url>\n    <loc>%s</loc>\n%s%s  </url>\n"
                    % (lang_url(canon, l), ("    " + lastmod.group(0) + "\n") if lastmod else "", alternates(canon))
                )
    head = s[: s.index("  <url>")]
    open(path, "w", encoding="utf-8").write(head + "".join(out_blocks) + "</urlset>\n")


# ---------------------------------------------------------------- main

def main():
    report = "--report" in sys.argv
    dictionary = load_dictionary()
    pages = list_pages()
    pages_set = set(pages) - FR_ONLY
    translators = {l: Translator(dictionary, l) for l in GENERATED}

    for l in GENERATED:
        shutil.rmtree(os.path.join(ROOT, l), ignore_errors=True)

    canon_by_page = {}
    for page in pages:
        src = open(os.path.join(ROOT, page), encoding="utf-8").read()
        base = normalise_base(src, page)
        c = canonical_path(base)
        if c and page not in FR_ONLY:
            canon_by_page[page] = c
        for lang in LANGS:
            if lang != "fr" and page in FR_ONLY:
                continue
            doc = render(base, page, lang, dictionary, pages_set, translators)
            dest = os.path.join(ROOT, page if lang == "fr" else os.path.join(lang, page))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            if lang != "fr" or doc != src:
                with open(dest, "w", encoding="utf-8") as f:
                    f.write(doc)

    build_sitemap(canon_by_page)
    total = sum(1 for p in pages if p not in FR_ONLY) * len(GENERATED)
    print("Built %d pages (%d French sources, %d generated)." % (total, len(pages), total))
    if report:
        miss = sorted(translators["en"].missing)
        print("%d French strings without translation:" % len(miss))
        for k in miss:
            print("  -", k[:110])


if __name__ == "__main__":
    main()
