/*
 * Language switcher for the multilingual static site.
 *
 * Each language has its own pre-translated pages (/ = FR, /en/, /it/) built by
 * scripts/build_i18n.py, so switching is plain navigation to the same page in
 * the other language — no runtime translation, no reload flash.
 *
 * Page metadata (added by the build script):
 *   <meta name="i18n-lang"  content="fr|en|it">
 *   <meta name="i18n-path"  content="conseils/x/">        page path from the site root ("" on the home page)
 *   <meta name="i18n-root"  content="../">                relative path back to the site root
 */
(function () {
  "use strict";

  function meta(name) {
    var el = document.querySelector('meta[name="' + name + '"]');
    return el ? el.getAttribute("content") : null;
  }

  var CURRENT = meta("i18n-lang");
  var PAGE_PATH = meta("i18n-path");
  var ROOT = meta("i18n-root");
  if (!CURRENT || PAGE_PATH === null || ROOT === null) return;   // "" = language home

  var FLAGS = {
    fr: '<svg viewBox="0 0 3 2" width="22" height="15" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false"><rect width="3" height="2" fill="#fff"/><rect width="1" height="2" fill="#002395"/><rect width="1" height="2" x="2" fill="#ED2939"/></svg>',
    en: '<svg viewBox="0 0 60 30" width="22" height="15" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false"><clipPath id="i18n-uk"><rect width="60" height="30"/></clipPath><g clip-path="url(#i18n-uk)"><rect width="60" height="30" fill="#012169"/><path d="M0,0 60,30M60,0 0,30" stroke="#fff" stroke-width="6"/><path d="M0,0 60,30M60,0 0,30" stroke="#C8102E" stroke-width="4"/><path d="M30,0 V30M0,15 H60" stroke="#fff" stroke-width="10"/><path d="M30,0 V30M0,15 H60" stroke="#C8102E" stroke-width="6"/></g></svg>',
    it: '<svg viewBox="0 0 3 2" width="22" height="15" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false"><rect width="3" height="2" fill="#fff"/><rect width="1" height="2" fill="#008C45"/><rect width="1" height="2" x="2" fill="#CD212A"/></svg>'
  };

  var LANGS = [
    { code: "fr", label: "Français", short: "FR" },
    { code: "en", label: "English", short: "EN" },
    { code: "it", label: "Italiano", short: "IT" }
  ];

  var BUTTON_LABEL = {
    fr: function (l) { return "Choisir la langue (actuellement : " + l + ")"; },
    en: function (l) { return "Choose language (currently: " + l + ")"; },
    it: function (l) { return "Scegli la lingua (attualmente: " + l + ")"; }
  };
  var MENU_LABEL = { fr: "Langues du site", en: "Site languages", it: "Lingue del sito" };

  function urlFor(code) {
    return ROOT + (code === "fr" ? "" : code + "/") + PAGE_PATH;
  }

  function labelOf(code) {
    for (var i = 0; i < LANGS.length; i++) if (LANGS[i].code === code) return LANGS[i];
    return LANGS[0];
  }

  var switchEls = [];
  var uid = 0;

  function injectStyles() {
    if (document.getElementById("lang-switch-styles")) return;
    var css =
      '.lang-switch{position:relative;display:inline-flex;align-items:center;font-family:inherit;margin-left:12px;z-index:900}' +
      '.lang-switch *{box-sizing:border-box}' +
      '.lang-switch__btn{display:inline-flex;align-items:center;gap:8px;flex:0 0 auto;height:2.75rem;padding:0 .8rem 0 .7rem;' +
      'cursor:pointer;border:1px solid rgba(0,0,0,.15);background:#fff;color:#111;border-radius:999px;font:inherit;' +
      'font-size:14px;font-weight:700;letter-spacing:.02em;transition:box-shadow .15s ease,border-color .15s ease}' +
      '.lang-switch__btn:hover{border-color:rgba(0,0,0,.35);box-shadow:0 2px 10px rgba(0,0,0,.12)}' +
      '.lang-switch__btn:focus-visible,.lang-switch__item:focus-visible{outline:3px solid #D9672B;outline-offset:2px}' +
      '.lang-switch__flag{display:inline-flex;line-height:0;border-radius:3px;overflow:hidden;box-shadow:0 0 0 1px rgba(0,0,0,.14)}' +
      '.lang-switch__flag svg{display:block}' +
      '.lang-switch__caret{width:10px;height:10px;transition:transform .15s ease}' +
      '.lang-switch.is-open .lang-switch__caret{transform:rotate(180deg)}' +
      '.lang-switch__menu{position:absolute;top:calc(100% + 8px);right:0;min-width:190px;margin:0;list-style:none;background:#fff;color:#111;' +
      'border:1px solid rgba(0,0,0,.12);border-radius:12px;box-shadow:0 12px 30px rgba(0,0,0,.18);padding:6px;display:none;flex-direction:column}' +
      '.lang-switch.is-open .lang-switch__menu{display:flex}' +
      '.lang-switch__item{display:flex;align-items:center;gap:10px;width:100%;text-decoration:none;padding:10px 12px;border-radius:8px;' +
      'font-size:14px;font-weight:600;color:#111}' +
      '.lang-switch__item:hover{background:rgba(0,0,0,.06)}' +
      '.lang-switch__item[aria-current="true"]{background:rgba(0,0,0,.09)}' +
      '.lang-switch__code{margin-left:auto;font-size:12px;font-weight:700;opacity:.65;letter-spacing:.04em}' +
      '@media (min-width:992px){' +
      '.rt-navbar-button-wraper{display:flex;align-items:center;gap:8px}' +
      '.rt-navbar-button-wraper .lang-switch{margin-left:0}' +
      '.rt-navbar-button-wraper .rt-button{padding-left:1rem!important;padding-right:1rem!important}' +
      '.rt-navbar-button-wraper .rt-text-style-button{white-space:nowrap}}' +
      '@media (max-width:991px){.rt-navbar-wrapper-v4>.lang-switch{margin-left:auto;margin-right:6px}}' +
      '.rt-hero-button-wrapper{flex-direction:row!important;flex-wrap:wrap!important}' +
      '.rt-hero-button-wrapper>div{flex:0 0 auto!important}' +
      '.rt-hero-button-wrapper .rt-text-style-button{white-space:nowrap}';
    var style = document.createElement("style");
    style.id = "lang-switch-styles";
    style.textContent = css;
    document.head.appendChild(style);
  }

  function setOpen(wrap, open, focusTarget) {
    var btn = wrap.querySelector(".lang-switch__btn");
    wrap.classList.toggle("is-open", open);
    btn.setAttribute("aria-expanded", open ? "true" : "false");
    if (open && focusTarget) focusTarget.focus();
  }

  function buildSwitch() {
    var current = labelOf(CURRENT);
    var id = "lang-menu-" + (++uid);

    var wrap = document.createElement("div");
    wrap.className = "lang-switch";

    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "lang-switch__btn";
    btn.setAttribute("aria-haspopup", "true");
    btn.setAttribute("aria-expanded", "false");
    btn.setAttribute("aria-controls", id);
    btn.setAttribute("aria-label", BUTTON_LABEL[CURRENT](current.label));
    btn.innerHTML =
      '<span class="lang-switch__flag">' + FLAGS[current.code] + "</span>" +
      "<span>" + current.short + "</span>" +
      '<svg class="lang-switch__caret" viewBox="0 0 10 10" aria-hidden="true" focusable="false"><path d="M1 3l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';

    var menu = document.createElement("ul");
    menu.className = "lang-switch__menu";
    menu.id = id;
    menu.setAttribute("aria-label", MENU_LABEL[CURRENT]);

    var links = [];
    LANGS.forEach(function (l) {
      var li = document.createElement("li");
      var a = document.createElement("a");
      a.className = "lang-switch__item";
      a.href = urlFor(l.code);
      a.lang = l.code;
      a.setAttribute("hreflang", l.code);
      if (l.code === CURRENT) a.setAttribute("aria-current", "true");
      a.innerHTML =
        '<span class="lang-switch__flag">' + FLAGS[l.code] + "</span>" +
        "<span>" + l.label + "</span>" +
        '<span class="lang-switch__code" aria-hidden="true">' + l.short + "</span>";
      li.appendChild(a);
      menu.appendChild(li);
      links.push(a);
    });

    function currentIndex() {
      for (var i = 0; i < links.length; i++) if (links[i] === document.activeElement) return i;
      return -1;
    }

    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      var open = !wrap.classList.contains("is-open");
      setOpen(wrap, open, open ? links[LANGS.indexOf(current)] || links[0] : null);
    });

    btn.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        setOpen(wrap, true, e.key === "ArrowDown" ? links[0] : links[links.length - 1]);
      }
    });

    menu.addEventListener("keydown", function (e) {
      var i = currentIndex();
      if (e.key === "ArrowDown") { e.preventDefault(); links[(i + 1) % links.length].focus(); }
      else if (e.key === "ArrowUp") { e.preventDefault(); links[(i - 1 + links.length) % links.length].focus(); }
      else if (e.key === "Home") { e.preventDefault(); links[0].focus(); }
      else if (e.key === "End") { e.preventDefault(); links[links.length - 1].focus(); }
      else if (e.key === "Escape") { e.preventDefault(); setOpen(wrap, false); btn.focus(); }
      else if (e.key === "Tab") { setOpen(wrap, false); }
    });

    wrap.appendChild(btn);
    wrap.appendChild(menu);
    switchEls.push(wrap);
    return wrap;
  }

  var MOBILE_MQ = "(max-width:991px)";

  function placeSwitch(sw, ctaWrap) {
    var isMobile = window.matchMedia(MOBILE_MQ).matches;
    // mobile: switcher sits left of the tap-to-call button (if any), then the menu button
    var hamburger = ctaWrap.parentNode.querySelector(".rt-nav-call, .rt-mobile-list-button");
    if (isMobile && hamburger) {
      if (sw.parentNode !== ctaWrap.parentNode || sw.nextSibling !== hamburger) {
        ctaWrap.parentNode.insertBefore(sw, hamburger);
      }
    } else if (sw.parentNode !== ctaWrap) {
      ctaWrap.appendChild(sw);
    }
  }

  function mountSwitch() {
    var anchors = document.querySelectorAll(".rt-navbar-button-wraper");
    if (anchors.length) {
      for (var i = 0; i < anchors.length; i++) {
        var sw = buildSwitch();
        (function (sw, ctaWrap) {
          placeSwitch(sw, ctaWrap);
          var mq = window.matchMedia(MOBILE_MQ);
          var relay = function () { placeSwitch(sw, ctaWrap); };
          if (mq.addEventListener) mq.addEventListener("change", relay);
          else if (mq.addListener) mq.addListener(relay);
        })(sw, anchors[i]);
      }
    } else {
      var fallback = buildSwitch();
      fallback.style.position = "fixed";
      fallback.style.top = "16px";
      fallback.style.right = "16px";
      fallback.style.zIndex = "9999";
      document.body.appendChild(fallback);
    }

    document.addEventListener("click", function () {
      switchEls.forEach(function (w) { setOpen(w, false); });
    });
  }

  var ARTICLE_COPY = {
    fr: {
      subtitle: "Atelier de ferronnerie d'art à Nice",
      whatsapp: "WhatsApp +33 7 69 87 11 08",
      phone: "07 69 87 11 08",
      quote: "Demander un devis",
      whatsappLabel: "Contacter La Ferronnerie du Rouret sur WhatsApp",
      phoneLabel: "Appeler La Ferronnerie du Rouret au 07 69 87 11 08"
    },
    en: {
      subtitle: "Art metalwork workshop in Nice",
      whatsapp: "WhatsApp +33 7 69 87 11 08",
      phone: "+33 7 69 87 11 08",
      quote: "Request a quote",
      whatsappLabel: "Contact La Ferronnerie du Rouret on WhatsApp",
      phoneLabel: "Call La Ferronnerie du Rouret on +33 7 69 87 11 08"
    },
    it: {
      subtitle: "Laboratorio di lavorazione artistica del ferro a Nizza",
      whatsapp: "WhatsApp +33 7 69 87 11 08",
      phone: "+33 7 69 87 11 08",
      quote: "Richiedi un preventivo",
      whatsappLabel: "Contatta La Ferronnerie du Rouret su WhatsApp",
      phoneLabel: "Chiama La Ferronnerie du Rouret al +33 7 69 87 11 08"
    }
  };

  var WHATSAPP_COPY = {
    fr: {
      title: "Un projet de ferronnerie ?",
      message: "Échangez directement avec notre atelier sur WhatsApp.",
      action: "Écrire au +33 7 69 87 11 08",
      close: "Fermer la notification WhatsApp",
      preset: "Bonjour, je souhaite obtenir des informations pour mon projet de ferronnerie."
    },
    en: {
      title: "Planning a metalwork project?",
      message: "Chat directly with our workshop on WhatsApp.",
      action: "Message +33 7 69 87 11 08",
      close: "Close the WhatsApp notification",
      preset: "Hello, I would like more information about my metalwork project."
    },
    it: {
      title: "Hai un progetto di lavorazione del ferro?",
      message: "Parla direttamente con il nostro laboratorio su WhatsApp.",
      action: "Scrivi al +33 7 69 87 11 08",
      close: "Chiudi la notifica WhatsApp",
      preset: "Buongiorno, vorrei ricevere informazioni per il mio progetto di lavorazione del ferro."
    }
  };

  function mountWhatsAppNotice() {
    if (document.querySelector(".gh-whatsapp-notice")) return;

    var copy = WHATSAPP_COPY[CURRENT] || WHATSAPP_COPY.fr;
    var notice = document.createElement("aside");
    notice.className = "gh-whatsapp-notice";
    notice.setAttribute("role", "complementary");
    notice.setAttribute("aria-label", "WhatsApp");
    notice.innerHTML =
      '<button class="gh-whatsapp-notice__close" type="button" aria-label="' + copy.close + '">&times;</button>' +
      '<div class="gh-whatsapp-notice__icon" aria-hidden="true">WA</div>' +
      '<div class="gh-whatsapp-notice__content">' +
        '<strong class="gh-whatsapp-notice__title">' + copy.title + "</strong>" +
        '<span class="gh-whatsapp-notice__message">' + copy.message + "</span>" +
        '<a class="gh-whatsapp-notice__action" href="https://wa.me/33769871108?text=' + encodeURIComponent(copy.preset) + '" target="_blank" rel="noopener">' + copy.action + "</a>" +
      "</div>";

    notice.querySelector(".gh-whatsapp-notice__close").addEventListener("click", function () {
      notice.classList.remove("is-visible");
      window.setTimeout(function () { notice.remove(); }, 250);
    });

    document.body.appendChild(notice);
    window.setTimeout(function () {
      if (document.body.contains(notice)) notice.classList.add("is-visible");
    }, 5500);
  }

  function enhanceArticle() {
    if (PAGE_PATH.indexOf("conseils/") !== 0 || PAGE_PATH === "conseils/") return;

    document.body.classList.add("gh-article-page");

    var author = document.querySelector(".rt-more-details-author-inner");
    if (!author) return;

    var imageWrap = author.querySelector(".rt-more-details-author-image");
    var image = imageWrap ? imageWrap.querySelector("img") : null;
    if (image) {
      image.src = ROOT + "assets/images/logo-la-ferronnerie-du-rouret.svg";
      image.removeAttribute("srcset");
      image.removeAttribute("sizes");
      image.removeAttribute("data-w-id");
      image.removeAttribute("style");
      image.alt = "Logo de La Ferronnerie du Rouret";
      image.width = 120;
      image.height = 120;
      image.className = "gh-author-logo";
    }

    var details = author.querySelector(".rt-author-details-warpper");
    var copy = ARTICLE_COPY[CURRENT] || ARTICLE_COPY.fr;
    if (details) {
      var lines = details.children;
      if (lines[0]) lines[0].textContent = "La Ferronnerie du Rouret";
      if (lines[1]) lines[1].textContent = copy.subtitle;
    }

    if (!author.querySelector(".gh-author-cta")) {
      var actions = document.createElement("div");
      actions.className = "gh-author-cta";
      actions.innerHTML =
        '<a class="gh-author-action gh-author-action--whatsapp" href="https://wa.me/33769871108" target="_blank" rel="noopener" aria-label="' + copy.whatsappLabel + '">' + copy.whatsapp + "</a>" +
        '<a class="gh-author-action gh-author-action--phone" href="tel:+33769871108" aria-label="' + copy.phoneLabel + '">' + copy.phone + "</a>" +
        '<a class="gh-author-action gh-author-action--quote" href="' + ROOT + 'devis/">' + copy.quote + "</a>";
      author.appendChild(actions);
    }
  }

  function init() {
    if (window.__i18nInit) return;
    window.__i18nInit = true;
    injectStyles();
    mountSwitch();
    enhanceArticle();
    mountWhatsAppNotice();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
