#!/usr/bin/env python3
"""
Generate the organised blog (French sources) — run automatically by build_i18n.py.

  * blog.html: featured article, search, category filters with counts, cards with
    category tags and reading time.
  * blog-post/*.html: breadcrumb, category links + reading time, header image,
    "À lire aussi" related articles chosen by shared categories.

To add an article: create its page in blog-post/, then add an entry to ARTICLES
below (categories + image source). Everything else is computed.
"""

import html
import os
import re
import json

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CATEGORIES = [
    ("portail", "Portail"),
    ("cloture", "Clôture"),
    ("garde-corps", "Garde-corps"),
    ("pergola", "Pergola"),
    ("marquise", "Marquise"),
    ("grille-defense", "Grille de défense"),
    ("escalier-rambarde", "Escalier & rambarde"),
    ("meuble", "Meuble"),
]
LABEL = dict(CATEGORIES)

# slug (file name without .html) -> categories (main one first), image source, image base name
ARTICLES = [
    ("essential-roof-maintenance-tips-every-homeowner-should-know-to-protect",
     ["portail", "cloture", "garde-corps", "grille-defense"], "assets/images/blog/entretien-ferronnerie.webp", "entretien-ferronnerie-exterieure"),
    ("how-to-spot-roof-damage-early-and-prevent-costly-issues-before-its-too-late",
     ["portail", "cloture", "grille-defense"], "assets/images/blog/corrosion-portail.webp", "corrosion-portail-fer"),
    ("top-5-roofing-materials-for-durability-style-and-ultimate-home-protection",
     ["portail", "garde-corps", "escalier-rambarde", "meuble"], "assets/images/blog/finitions-fer-forge.webp", "finitions-ferronnerie-art"),
    ("top-signs-your-roof-needs-immediate-repair-before-major-damage",
     ["portail", "cloture"], "assets/images/hero-blacksmith-sparks.jpg", "portail-a-restaurer-meulage"),
    ("how-to-choose-the-right-roofing-material-for-your-home-today",
     ["portail", "cloture", "garde-corps", "pergola", "marquise", "meuble"], "assets/images/atelier-ferronnier-soudure.jpg", "choisir-metal-ferronnerie"),
    ("benefits-of-professional-roof-installation-for-long-term-protection",
     ["portail", "garde-corps", "escalier-rambarde", "pergola"], "assets/images/features/travail-atelier-photo.webp", "avantages-ferronnerie-artisan"),
    ("seasonal-roof-maintenance-checklist-for-homeowners-to-protect-your-home-year-round",
     ["portail", "cloture", "garde-corps", "grille-defense", "pergola", "marquise"], "assets/images/features/securite-chantier-photo.webp", "calendrier-entretien-ferronnerie"),
    ("how-weather-conditions-affect-the-lifespan-of-your-roof-and-durability",
     ["portail", "cloture", "garde-corps", "pergola", "marquise"], "assets/images/features/portail-france-photo.webp", "air-marin-durabilite-ferronnerie"),
    ("common-roofing-mistakes-homeowners-should-avoid-during-installation-projects",
     ["garde-corps", "escalier-rambarde"], "assets/images/pose-garde-corps-fer-forge.jpg", "erreurs-pose-garde-corps"),
]
FEATURED = "how-to-choose-the-right-roofing-material-for-your-home-today"
BANNER_SRC = "assets/images/hero-blacksmith-sparks.jpg"
BANNER_BASE = "assets/images/blog/banner-atelier-ferronnerie"
BANNER_ALT = "Travail du métal à la meuleuse, avec des étincelles"


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


def write(path, text):
    with open(os.path.join(ROOT, path), "w", encoding="utf-8") as f:
        f.write(text)


def crop_save(src, out, w, h, quality=78):
    if os.path.exists(os.path.join(ROOT, out)):
        return
    im = Image.open(os.path.join(ROOT, src)).convert("RGB")
    sw, sh = im.size
    target = w / h
    if sw / sh > target:
        nw = int(sh * target)
        im = im.crop(((sw - nw) // 2, 0, (sw - nw) // 2 + nw, sh))
    else:
        nh = int(sw / target)
        im = im.crop((0, (sh - nh) // 2, sw, (sh - nh) // 2 + nh))
    im = im.resize((w, h), Image.LANCZOS)
    im.save(os.path.join(ROOT, out), "WEBP", quality=quality, method=6)


def ensure_images():
    for slug, cats, src, base in ARTICLES:
        crop_save(src, "assets/images/blog/%s-800.webp" % base, 800, 533)
        crop_save(src, "assets/images/blog/%s-1280.webp" % base, 1280, 776)
    crop_save(BANNER_SRC, BANNER_BASE + "-1920.webp", 1920, 800, 76)


def parse_post(slug):
    s = read("blog-post/%s.html" % slug)
    title = html.unescape(re.sub(r"<[^>]+>", "", re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S).group(1))).strip()
    date = re.search(r'rt-hero-publish-date.*?<div>([^<]+)</div>', s, re.S).group(1).strip()
    desc = html.unescape(re.search(r'<meta content="([^"]*)" name="description"', s).group(1))
    text = " ".join(re.sub(r"<[^>]+>", " ", m) for m in re.findall(r'<div class="(?:rt-tick-list )?w-richtext">(.*?)</div>\s*</div>', s, re.S))
    words = len(re.findall(r"\w+", html.unescape(text)))
    return {"title": title, "date": date, "desc": desc, "words": words, "minutes": max(2, round(words / 200 + 0.4))}


def esc(t):
    return html.escape(t, quote=True)


def chips(cats, prefix, limit=None, link=True):
    shown = cats if limit is None else cats[:limit]
    out = "".join(
        ('<a href="%sblog.html#%s">%s</a>' % (prefix, c, LABEL[c])) if link else "<span>%s</span>" % LABEL[c]
        for c in shown
    )
    if limit is not None and len(cats) > limit:
        out += '<span class="gh-more" aria-hidden="true">+%d</span>' % (len(cats) - limit)
    return out


def read_label(n):
    return "%d min de lecture" % n


def card(slug, cats, base, info, prefix):
    href = "%sblog-post/%s.html" % (prefix, slug)
    return (
        '<div class="rt-blog-collection-item w-dyn-item" role="listitem" data-cats="%s" data-slug="%s">'
        '<div class="w-layout-vflex rt-blog-card-item-one">'
        '<a class="rt-blog-card-image-wrapper rt-overflow-hidden rt-border-radius w-inline-block" href="%s">'
        '<img alt="%s" class="rt-blog-card-image" loading="lazy" decoding="async" src="%sassets/images/blog/%s-800.webp" width="800" height="533"/></a>'
        '<div class="gh-meta"><div class="rt-blog-publish-date">%s</div><div class="gh-read">%s</div></div>'
        '<div class="gh-cats">%s</div>'
        '<a class="rt-blog-title-wrapper w-inline-block" href="%s"><div class="rt-text-style-h5">%s</div></a>'
        '<div class="rt-blog-card-item-border-line"><div class="rt-blog-card-item-border-inner-line"></div></div>'
        "</div></div>"
        % (" ".join(cats), slug, href, esc(info["title"]), prefix, base, info["date"], read_label(info["minutes"]),
           chips(cats, prefix, 3, link=False), href, esc(info["title"]))
    )


LIST_CSS = """<style id="gh-blog-list-css">
.gh-toolbar{display:flex;flex-direction:column;align-items:center;gap:1.25rem;margin-top:1.75rem;width:100%}
.gh-search{position:relative;width:min(100%,32rem)}
.gh-search input{width:100%;height:3.1rem;padding:0 2.75rem 0 2.75rem;border:1px solid rgba(28,31,34,.25);border-radius:999px;background:#fff;font:inherit;font-size:1rem;color:#1C1F22}
.gh-search input:focus{outline:3px solid #F6B287;border-color:#D9672B}
.gh-search svg{position:absolute;left:1rem;top:50%;width:1.1rem;height:1.1rem;transform:translateY(-50%);color:#374151;pointer-events:none}
.gh-search button{position:absolute;right:.5rem;top:50%;transform:translateY(-50%);width:2.1rem;height:2.1rem;border:0;border-radius:50%;background:transparent;font-size:1.3rem;line-height:1;color:#374151;cursor:pointer}
.gh-search button[hidden]{display:none}
.gh-filter{display:flex;flex-wrap:wrap;justify-content:center;gap:.6rem}
.gh-chip{cursor:pointer;border:1px solid rgba(28,31,34,.25);background:#fff;color:#1C1F22;border-radius:999px;padding:.55rem 1rem;font:inherit;font-size:.95rem;font-weight:500;line-height:1.2;display:inline-flex;align-items:center;gap:.5rem;transition:background .2s,border-color .2s,color .2s,transform .2s}
.gh-chip .gh-n{font-size:.78rem;font-weight:600;min-width:1.4rem;padding:.15rem .4rem;border-radius:999px;background:#F3F6F7;color:#374151;text-align:center}
.gh-chip:hover{border-color:#D9672B;transform:translateY(-1px)}
.gh-chip.is-active{background:#D9672B;border-color:#D9672B;color:#fff}
.gh-chip.is-active .gh-n{background:rgba(255,255,255,.25);color:#fff}
.gh-chip:focus-visible,.gh-feature a:focus-visible{outline:3px solid #F6B287;outline-offset:2px}
.gh-count{margin:0;font-size:.95rem;color:#374151;text-align:center}
.gh-empty{text-align:center;padding:3rem 1rem;color:#374151;font-size:1.05rem}
.gh-empty[hidden]{display:none}
.gh-feature{display:grid;grid-template-columns:1.25fr 1fr;gap:2.5rem;align-items:center;margin:2.5rem 0 3rem;padding:1rem;border-radius:1.5rem;background:#F3F6F7}
.gh-feature[hidden]{display:none}
.gh-feature-img{display:block;overflow:hidden;border-radius:1rem}
.gh-feature-img img{display:block;width:100%;height:auto;transition:transform .6s ease}
.gh-feature:hover .gh-feature-img img{transform:scale(1.04)}
.gh-badge{display:inline-block;padding:.4rem .8rem;border-radius:999px;background:#D9672B;color:#fff;font-size:.8rem;font-weight:600;letter-spacing:.03em;text-transform:uppercase}
.gh-feature-body{display:flex;flex-direction:column;gap:1rem;align-items:flex-start;padding:1rem 1.25rem 1rem 0}
.gh-feature h3{margin:0;font-size:clamp(1.6rem,2.6vw,2.4rem);line-height:1.15;font-weight:500;letter-spacing:-.02em}
.gh-feature h3 a{color:inherit;text-decoration:none}
.gh-feature p{margin:0;color:#374151;line-height:1.6}
.gh-more-link{font-weight:600;color:#B9551F;text-decoration:none}
.gh-more-link:hover{text-decoration:underline}
.gh-meta{display:flex;align-items:center;gap:.75rem;flex-wrap:wrap}
.gh-read{font-size:.9rem;color:#374151}
.gh-read::before{content:"·";margin-right:.75rem}
.gh-cats{display:flex;flex-wrap:wrap;gap:.4rem;margin-top:.6rem}
.gh-cats span,.gh-cats a{font-size:.8rem;line-height:1;padding:.35rem .65rem;border-radius:999px;background:#F3F6F7;color:#374151;text-decoration:none}
.gh-feature .gh-cats span{background:#fff}
.gh-cats .gh-more{background:transparent;padding-left:.2rem}
.rt-blog-collection-item[hidden]{display:none!important}
@media (max-width:991px){.gh-feature{grid-template-columns:1fr;gap:1.25rem}.gh-feature-body{padding:0 .5rem .75rem}}
@media (max-width:767px){.gh-filter{justify-content:flex-start}}
</style>
"""

LIST_JS = """<script id="gh-blog-list-js">
(function(){var root=document.querySelector("[data-gh-blog]");if(!root)return;
var chips=root.querySelectorAll(".gh-chip"),items=root.querySelectorAll(".rt-blog-collection-item[data-cats]"),cnt=root.querySelector("[data-gh-count]"),
feat=root.querySelector(".gh-feature"),empty=root.querySelector(".gh-empty"),q=root.querySelector(".gh-search input"),clr=root.querySelector(".gh-search button");
var lang=(document.documentElement.getAttribute("lang")||"fr").slice(0,2);
var T={fr:["article","articles"],en:["article","articles"],it:["articolo","articoli"]}[lang]||["article","articles"];
function norm(s){return (s||"").toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g,"")}
var text=[];items.forEach(function(it){text.push(norm(it.textContent))});
var cat="all",query="",slug=feat?feat.getAttribute("data-slug"):null;
function apply(push){var n=0;
items.forEach(function(it,i){var okC=cat==="all"||(" "+it.getAttribute("data-cats")+" ").indexOf(" "+cat+" ")>-1;
var okQ=!query||query.split(" ").every(function(w){return text[i].indexOf(w)>-1});
var showFeat=feat&&cat==="all"&&!query&&it.getAttribute("data-slug")===slug;
var ok=okC&&okQ&&!showFeat;it.hidden=!ok;if(okC&&okQ)n++});
if(feat)feat.hidden=!(cat==="all"&&!query);
chips.forEach(function(c){var on=c.getAttribute("data-cat")===cat;c.classList.toggle("is-active",on);c.setAttribute("aria-pressed",on?"true":"false")});
if(clr)clr.hidden=!query;
if(cnt)cnt.textContent=n+" "+(n===1?T[0]:T[1]);
if(empty)empty.hidden=n>0;
if(push){try{history.replaceState(null,"",cat==="all"?location.pathname:"#"+cat)}catch(e){}}}
chips.forEach(function(c){c.addEventListener("click",function(){cat=c.getAttribute("data-cat");apply(true)})});
if(q){q.addEventListener("input",function(){query=norm(q.value).trim();apply(false)});
q.addEventListener("keydown",function(e){if(e.key==="Escape"&&q.value){q.value="";query="";apply(false)}})}
if(clr)clr.addEventListener("click",function(){q.value="";query="";apply(false);q.focus()});
function fromHash(){var h=decodeURIComponent((location.hash||"").slice(1));var ok=Array.prototype.some.call(chips,function(c){return c.getAttribute("data-cat")===h});cat=ok?h:"all";apply(false)}
window.addEventListener("hashchange",fromHash);fromHash();})();
</script>
"""


def listing():
    ensure_images()
    infos = {slug: parse_post(slug) for slug, *_ in ARTICLES}
    counts = {k: sum(1 for _, cats, *_ in ARTICLES if k in cats) for k, _ in CATEGORIES}
    fslug, fcats, _, fbase = next(a for a in ARTICLES if a[0] == FEATURED)
    fi = infos[fslug]
    fhref = "blog-post/%s.html" % fslug
    feature = (
        '<article class="gh-feature" data-slug="%s"><a class="gh-feature-img" href="%s" tabindex="-1" aria-hidden="true">'
        '<img alt="" src="assets/images/blog/%s-1280.webp" width="1280" height="776" decoding="async"/></a>'
        '<div class="gh-feature-body"><span class="gh-badge">À la une</span><div class="gh-cats">%s</div>'
        '<h3><a href="%s">%s</a></h3><p>%s</p><div class="gh-meta"><div class="rt-blog-publish-date">%s</div><div class="gh-read">%s</div></div>'
        '<a class="gh-more-link" href="%s">Lire l\'article →</a></div></article>'
        % (fslug, fhref, fbase, chips(fcats, "", 3, link=False), fhref, esc(fi["title"]), esc(fi["desc"]),
           fi["date"], read_label(fi["minutes"]), fhref)
    )
    bar = (
        '<div class="gh-toolbar"><div class="gh-search" role="search"><svg viewBox="0 0 20 20" aria-hidden="true" focusable="false">'
        '<circle cx="9" cy="9" r="6" fill="none" stroke="currentColor" stroke-width="2"/><path d="M14 14l4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
        '<input type="search" placeholder="Rechercher un article" aria-label="Rechercher un article" autocomplete="off"/>'
        '<button type="button" aria-label="Effacer la recherche" hidden>&times;</button></div>'
        '<div class="gh-filter" role="group" aria-label="Filtrer les articles par catégorie">'
        '<button type="button" class="gh-chip is-active" data-cat="all" aria-pressed="true">Tous<span class="gh-n">%d</span></button>%s</div>'
        '<p class="gh-count" role="status" aria-live="polite" data-gh-count></p></div>'
        % (len(ARTICLES), "".join(
            '<button type="button" class="gh-chip" data-cat="%s" aria-pressed="false">%s<span class="gh-n">%d</span></button>' % (k, v, counts[k])
            for k, v in CATEGORIES))
    )
    cards = "".join(card(slug, cats, base, infos[slug], "") for slug, cats, _, base in ARTICLES)
    inner = (
        '<div class="w-layout-blockcontainer rt-container w-container"><div class="w-layout-vflex rt-blog-card-main" data-gh-blog>'
        '<div class="w-layout-vflex rt-blog-card-top-content rt-text-center rt-top-content-gap">'
        '<div class="w-layout-hflex rt-hero-top-subtext rt-tag-box-gap-h2"><div class="rt-round rt-background-color-neon-lime rt-border-radius-full"></div>'
        '<div class="rt-text-style-h6 rt-font-weight-regular">Actualités</div></div>'
        '<h2 class="rt-gap-off">Conseils et actualités de l\'atelier</h2>%s</div>%s'
        '<div class="rt-blog-collection-listwrapper w-dyn-list"><div class="rt-blog-card-bottom-content-wrapper w-dyn-items" role="list">%s</div></div>'
        '<p class="gh-empty" hidden>Aucun article ne correspond à votre recherche.</p>'
        "</div></div>" % (bar, feature, cards)
    )
    s = read("blog.html")
    section = '<section class="rt-blog-card-section rt-border-radius-top-right-left"><!-- blog:list -->%s<!-- /blog:list --></section>' % inner
    s, n = re.subn(r'<section class="rt-blog-card-section[^"]*">.*?</section>', lambda m: section, s, count=1, flags=re.S)
    assert n == 1
    # replace the old filter assets and add the new ones
    s = re.sub(r'<style id="gh-filter-css">.*?</style>\n?', "", s, flags=re.S)
    s = re.sub(r'<style id="gh-blog-list-css">.*?</style>\n?', "", s, flags=re.S)
    s = re.sub(r'<script(?: id="gh-blog-list-js")?>\s*\(function\(\)\{var (?:bar=document\.querySelector\("\.gh-filter"\)|root=document\.querySelector\("\[data-gh-blog\]"\)).*?</script>\n?', "", s, flags=re.S)
    s = s.replace("</head>", LIST_CSS + "</head>", 1).replace("</body>", LIST_JS + "</body>", 1)
    # banner image: own ironwork photo instead of the template roofing photo
    banner = ('<img alt="%s" class="rt-hero-background-image w-variant-02f5dbb7-1f6e-1146-7e76-3a19f31af7f2" '
              'src="%s-1920.webp" width="1920" height="800" fetchpriority="high" decoding="async"/>' % (esc(BANNER_ALT), BANNER_BASE))
    s = re.sub(r'<img alt="[^"]*" class="rt-hero-background-image w-variant-02f5dbb7[^>]*/>', lambda m: banner, s, count=1)
    write("blog.html", s)


POST_CSS = """<style id="gh-post-css">
.gh-crumbs{display:flex;justify-content:center;align-items:center;gap:.5rem;margin:0 0 1.25rem;font-size:.95rem;color:#374151}
.gh-crumbs a{color:inherit;text-decoration:none}.gh-crumbs a:hover{text-decoration:underline}
.gh-postmeta{display:flex;flex-wrap:wrap;justify-content:center;align-items:center;gap:.6rem .9rem;margin:0 0 2rem}
.gh-postmeta .gh-cats{margin:0;justify-content:center}
.gh-postmeta .gh-cats a{background:#F3F6F7;transition:background .2s,color .2s}
.gh-postmeta .gh-cats a:hover{background:#D9672B;color:#fff}
.gh-postmeta .gh-read::before{margin-right:.6rem}
.gh-related-head{width:100%;display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:1rem}
.gh-cats span,.gh-cats a{font-size:.8rem;line-height:1;padding:.35rem .65rem;border-radius:999px;background:#F3F6F7;color:#374151;text-decoration:none}
.gh-cats{display:flex;flex-wrap:wrap;gap:.4rem;margin-top:.6rem}
.gh-cats .gh-more{background:transparent;padding-left:.2rem}
.gh-meta{display:flex;align-items:center;gap:.75rem;flex-wrap:wrap}
.gh-read{font-size:.9rem;color:#374151}
.gh-read::before{content:"·";margin-right:.75rem}
</style>
"""


def related_for(slug):
    me = next(a for a in ARTICLES if a[0] == slug)
    scored = []
    for order, (s2, cats, _, base) in enumerate(ARTICLES):
        if s2 == slug:
            continue
        scored.append((-len(set(cats) & set(me[1])), order, s2))
    return [x[2] for x in sorted(scored)[:3]]


def post(slug, cats, base, infos):
    info = infos[slug]
    path = "blog-post/%s.html" % slug
    s = read(path)
    s = re.sub(r"<!-- blog:crumbs -->.*?<!-- /blog:crumbs -->", "", s, flags=re.S)
    s = re.sub(r"<!-- blog:meta -->.*?<!-- /blog:meta -->", "", s, flags=re.S)
    crumbs = ('<!-- blog:crumbs --><nav class="gh-crumbs" aria-label="Fil d\'Ariane"><a href="../index.html">Accueil</a><span aria-hidden="true">›</span>'
              '<a href="../blog.html">Actualités</a></nav><!-- /blog:crumbs -->')
    meta = ('<!-- blog:meta --><div class="gh-postmeta"><div class="gh-cats">%s</div><div class="gh-read">%s</div></div><!-- /blog:meta -->'
            % (chips(cats, "../"), read_label(info["minutes"])))
    s = s.replace('<div class="w-layout-hflex rt-hero-publish-date', crumbs + '<div class="w-layout-hflex rt-hero-publish-date', 1)
    # header image: own ironwork photo
    hero = ('<div class="rt-hero-v1-image rt-overflow-hidden rt-border-radius"><img alt="%s" src="../assets/images/blog/%s-1280.webp" '
            'srcset="../assets/images/blog/%s-800.webp 800w, ../assets/images/blog/%s-1280.webp 1280w" sizes="(max-width: 1530px) 100vw, 1530px" '
            'width="1280" height="776" fetchpriority="high" decoding="async"/></div>' % (esc(info["title"]), base, base, base))
    s, n = re.subn(r'<div class="rt-hero-v1-image[^"]*"[^>]*>\s*<img[^>]*>\s*</div>', lambda m: meta + hero, s, count=1)
    assert n == 1, slug
    # related articles instead of a fixed "latest" list
    rel = related_for(slug)
    cards = "".join(card(r, next(a for a in ARTICLES if a[0] == r)[1], next(a for a in ARTICLES if a[0] == r)[3], infos[r], "../") for r in rel)
    section = ('<!-- blog:related --><section class="rt-recent-post-v1 rt-overflow-hidden"><div class="w-layout-blockcontainer rt-container w-container">'
               '<div class="w-layout-vflex rt-recent-post-main-v1"><div class="gh-related-head"><h2 class="rt-gap-off">À lire aussi</h2>'
               '<a class="gh-more-link" href="../blog.html">Tous les articles →</a></div>'
               '<div class="rt-blog-collection-listwrapper w-dyn-list"><div class="rt-blog-card-bottom-content-wrapper w-dyn-items" role="list">%s</div></div>'
               '</div></div></section><!-- /blog:related -->' % cards)
    s, n = re.subn(r'(?:<!-- blog:related -->)?<section class="rt-recent-post-v1[^"]*">.*?</section>(?:<!-- /blog:related -->)?', lambda m: section, s, count=1, flags=re.S)
    assert n == 1, slug
    s = re.sub(r'<style id="gh-post-css">.*?</style>\n?', "", s, flags=re.S)
    s = s.replace("</head>", POST_CSS + "</head>", 1)

    def art(m):
        j = json.loads(m.group(2))
        for nd in j.get("@graph", [j]):
            if isinstance(nd, dict) and nd.get("@type") == "Article":
                nd["articleSection"] = [LABEL[c] for c in cats]
                nd["wordCount"] = info["words"]
                nd["timeRequired"] = "PT%dM" % info["minutes"]
        return m.group(1) + json.dumps(j, ensure_ascii=False, separators=(", ", ": ")) + m.group(3)

    s = re.sub(r'(<script type="application/ld\+json">)(.*?)(</script>)', art, s, flags=re.S)
    write(path, s)


def main():
    ensure_images()
    infos = {slug: parse_post(slug) for slug, *_ in ARTICLES}
    listing()
    for slug, cats, _, base in ARTICLES:
        post(slug, cats, base, infos)
    return infos


if __name__ == "__main__":
    infos = main()
    print("Blog built: %d articles" % len(infos), {k[:18]: v["minutes"] for k, v in infos.items()})
