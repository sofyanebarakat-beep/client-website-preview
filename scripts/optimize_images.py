#!/usr/bin/env python3
"""
Optimise the images of the French source pages (src/) — run automatically by
build_i18n.py, safe to run again (it only fills in what is missing).

For every <img> with a local raster file:
  * JPG / PNG are converted to WebP (the page then points at the .webp),
  * width / height are added (no layout shift while the page loads),
  * images wider than 560 px get smaller WebP copies (<name>-w480.webp,
    -w800, -w1200, -w1600) and a srcset + sizes, so phones download a small file,
  * decoding="async" is added,
  * the page's hero image (first .rt-hero-background-image or active hero slide)
    loads first: fetchpriority="high" and never lazy.
JPG / PNG backgrounds in inline styles and video posters are switched to WebP too.
SVG icons are left alone.
"""

import os
import re

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")

RASTER = (".jpg", ".jpeg", ".png", ".webp", ".avif")
WIDTHS = (480, 800, 1200, 1600)
MIN_RESPONSIVE = 560          # narrower images are served as they are
MAX_WIDTH = 2400              # converted JPG / PNG are capped to this width
QUALITY = 78

FULL_WIDTH = re.compile(r'class="[^"]*(?:rt-hero-background-image|gh-slide-img|rt-cta-image|rt-banner)[^"]*"')
CARD = re.compile(r'class="[^"]*(?:rt-blog-image|rt-portfolio-image|gh-svc|rt-service-image|rt-team)[^"]*"')


def attr(tag, name):
    m = re.search(r'\s%s="([^"]*)"' % re.escape(name), tag)
    return m.group(1) if m else None


def set_attr(tag, name, value):
    if attr(tag, name) is not None:
        return re.sub(r'(\s%s=)"[^"]*"' % re.escape(name), r'\1"%s"' % value, tag, count=1)
    end = "/>" if tag.endswith("/>") else ">"
    return tag[: -len(end)] + ' %s="%s"%s' % (name, value, end)


def drop_attr(tag, name):
    return re.sub(r'\s%s="[^"]*"' % re.escape(name), "", tag)


def to_file(page, url):
    """Repository path of a src/ page's image URL, or None if it is not a local file."""
    if re.match(r"^(?:[a-z]+:|//|data:)", url, re.I):
        return None
    path = url.split("?")[0].split("#")[0]
    if path.startswith("/"):
        f = os.path.join(ROOT, path.lstrip("/"))
    else:
        f = os.path.normpath(os.path.join(ROOT, os.path.dirname(page), path))
    return f if os.path.isfile(f) else None


def sibling_url(url, new_name):
    return url.rsplit("/", 1)[0] + "/" + new_name if "/" in url else new_name


def webp_of(f):
    """WebP version of a JPG / PNG (created once), else the file itself."""
    base, ext = os.path.splitext(f)
    if ext.lower() not in (".jpg", ".jpeg", ".png"):
        return f
    out = base + ".webp"
    if not os.path.exists(out):
        im = Image.open(f)
        im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")
        if im.width > MAX_WIDTH:
            im = im.resize((MAX_WIDTH, round(im.height * MAX_WIDTH / im.width)), Image.LANCZOS)
        im.save(out, "WEBP", quality=QUALITY, method=6)
    return out


def variants(f, width):
    """Smaller WebP copies of f: [(file, width)], created once."""
    base = os.path.splitext(f)[0]
    out = []
    for w in WIDTHS:
        if w >= width * 0.9:
            break
        v = "%s-w%d.webp" % (base, w)
        if not os.path.exists(v):
            im = Image.open(f)
            im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")
            im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(v, "WEBP", quality=QUALITY, method=6)
        out.append((v, w))
    return out


def sizes_for(tag):
    if FULL_WIDTH.search(tag):
        return "100vw"
    if CARD.search(tag):
        return "(max-width: 767px) 100vw, (max-width: 991px) 50vw, 33vw"
    return "(max-width: 767px) 100vw, 50vw"


def optimise_img(tag, page):
    src = attr(tag, "src")
    f = to_file(page, src) if src else None
    if not f or not f.lower().endswith(RASTER):
        return tag
    w = webp_of(f)
    if w != f:
        src = sibling_url(src, os.path.basename(w))
        tag = set_attr(tag, "src", src)
        srcset = attr(tag, "srcset")
        if srcset:
            tag = set_attr(tag, "srcset", re.sub(r"\.(?:jpe?g|png)(?=\s|$|,)", ".webp", srcset, flags=re.I))
        f = w
    try:
        width, height = Image.open(f).size
    except OSError:
        return tag
    if attr(tag, "width") is None and attr(tag, "height") is None:
        tag = set_attr(tag, "width", str(width))
        tag = set_attr(tag, "height", str(height))
    if attr(tag, "srcset") is None and width > MIN_RESPONSIVE:
        vs = variants(f, width)
        if vs:
            cands = ["%s %dw" % (sibling_url(src, os.path.basename(v)), vw) for v, vw in vs]
            cands.append("%s %dw" % (src, width))
            tag = set_attr(tag, "srcset", ", ".join(cands))
            if attr(tag, "sizes") is None:
                tag = set_attr(tag, "sizes", sizes_for(tag))
    if attr(tag, "decoding") is None:
        tag = set_attr(tag, "decoding", "async")
    return tag


def optimise_page(page):
    path = os.path.join(SRC, page)
    doc = open(path, encoding="utf-8").read()
    out = re.sub(r"<img\b[^>]*>", lambda m: optimise_img(m.group(0), page), doc)

    # the hero image loads first
    hero = re.search(r'<img\b[^>]*class="[^"]*rt-hero-background-image[^"]*"[^>]*>', out) or \
        re.search(r'<div class="gh-slide is-active"[^>]*>(?:<picture[^>]*>(?:<source[^>]*>)*)?(<img\b[^>]*>)', out)
    if hero:
        tag = hero.group(1) if hero.re.groups else hero.group(0)
        new = set_attr(drop_attr(tag, "loading"), "fetchpriority", "high")
        if new != tag:
            out = out.replace(tag, new, 1)

    # JPG / PNG backgrounds and video posters -> WebP
    def swap(m):
        url = m.group(2)
        f = to_file(page, url)
        if not f or not f.lower().endswith((".jpg", ".jpeg", ".png")):
            return m.group(0)
        return m.group(1) + sibling_url(url, os.path.basename(webp_of(f))) + m.group(3)

    out = re.sub(r"""(url\(["']?)([^"')]+)(["']?\))""", swap, out)
    out = re.sub(r'(\s(?:poster|data-poster-url)=")([^"]+)(")', swap, out)

    if out != doc:
        with open(path, "w", encoding="utf-8") as f:
            f.write(out)
        return True
    return False


def main():
    changed = 0
    for dirpath, _, files in os.walk(SRC):
        for name in files:
            if name.endswith(".html"):
                page = os.path.relpath(os.path.join(dirpath, name), SRC).replace(os.sep, "/")
                changed += optimise_page(page)
    print("Images optimised in %d source pages." % changed)


if __name__ == "__main__":
    main()
