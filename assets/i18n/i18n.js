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

  var PROJECT_COPY = {
    fr: {
      detailsTitle: "Le projet en un coup d'œil",
      need: "Besoin du client",
      solution: "Solution proposée",
      material: "Matériau",
      finish: "Finition",
      location: "Localisation",
      duration: "Délai",
      locationFallback: "Nice et Côte d'Azur",
      durationFallback: "Défini après l'étude technique du chantier",
      materialFallback: "Métal sélectionné selon les contraintes du projet",
      finishFallback: "Finition adaptée à l'usage et à l'environnement",
      galleryTitle: "Galerie du projet",
      galleryHint: "Sélectionnez une photo pour l'afficher en plein écran.",
      openImage: "Afficher cette photo en plein écran",
      closeGallery: "Fermer la galerie",
      previous: "Photo précédente",
      next: "Photo suivante",
      ctaTitle: "Vous souhaitez un projet similaire ?",
      ctaText: "Parlez directement de votre besoin avec notre atelier de ferronnerie.",
      whatsapp: "WhatsApp +33 7 69 87 11 08",
      phone: "Appeler le +33 7 69 87 11 08",
      quote: "Demander un devis",
      quick: "Réponse rapide sur WhatsApp",
      hours: "Atelier joignable du lundi au vendredi, de 8h à 18h",
      similar: "Réalisations similaires",
      beforeAfter: "Avant / Après",
      trustTitle: "Les engagements de l'atelier",
      preset: "Bonjour, je souhaite un projet similaire à cette réalisation : "
    },
    en: {
      detailsTitle: "Project at a glance",
      need: "Client requirement",
      solution: "Proposed solution",
      material: "Material",
      finish: "Finish",
      location: "Location",
      duration: "Lead time",
      locationFallback: "Nice and the French Riviera",
      durationFallback: "Confirmed after the technical site assessment",
      materialFallback: "Metal selected for the project's requirements",
      finishFallback: "Finish suited to the use and environment",
      galleryTitle: "Project gallery",
      galleryHint: "Select a photo to view it full screen.",
      openImage: "View this photo full screen",
      closeGallery: "Close gallery",
      previous: "Previous photo",
      next: "Next photo",
      ctaTitle: "Would you like a similar project?",
      ctaText: "Discuss your requirements directly with our metalwork workshop.",
      whatsapp: "WhatsApp +33 7 69 87 11 08",
      phone: "Call +33 7 69 87 11 08",
      quote: "Request a quote",
      quick: "Quick response on WhatsApp",
      hours: "Workshop available Monday to Friday, 8am–6pm",
      similar: "Similar projects",
      beforeAfter: "Before / After",
      trustTitle: "Our workshop commitments",
      preset: "Hello, I would like a project similar to this one: "
    },
    it: {
      detailsTitle: "Il progetto in breve",
      need: "Esigenza del cliente",
      solution: "Soluzione proposta",
      material: "Materiale",
      finish: "Finitura",
      location: "Località",
      duration: "Tempi",
      locationFallback: "Nizza e Costa Azzurra",
      durationFallback: "Definiti dopo lo studio tecnico del cantiere",
      materialFallback: "Metallo selezionato in base ai requisiti del progetto",
      finishFallback: "Finitura adatta all'uso e all'ambiente",
      galleryTitle: "Galleria del progetto",
      galleryHint: "Seleziona una foto per visualizzarla a schermo intero.",
      openImage: "Visualizza questa foto a schermo intero",
      closeGallery: "Chiudi la galleria",
      previous: "Foto precedente",
      next: "Foto successiva",
      ctaTitle: "Desideri un progetto simile?",
      ctaText: "Parla direttamente delle tue esigenze con il nostro laboratorio.",
      whatsapp: "WhatsApp +33 7 69 87 11 08",
      phone: "Chiama +33 7 69 87 11 08",
      quote: "Richiedi un preventivo",
      quick: "Risposta rapida su WhatsApp",
      hours: "Laboratorio disponibile dal lunedì al venerdì, 8:00–18:00",
      similar: "Progetti simili",
      beforeAfter: "Prima / Dopo",
      trustTitle: "Gli impegni del laboratorio",
      preset: "Buongiorno, vorrei un progetto simile a questa realizzazione: "
    }
  };

  function isProjectPage() {
    return PAGE_PATH.indexOf("realisations/") === 0 && PAGE_PATH !== "realisations/";
  }

  function projectTitle() {
    var heading = document.querySelector("h1");
    return heading ? heading.textContent.trim() : document.title.split("|")[0].trim();
  }

  function projectWhatsAppUrl(copy) {
    return "https://wa.me/33769871108?text=" + encodeURIComponent(copy.preset + projectTitle() + " — " + window.location.href);
  }

  function trackContactClicks() {
    document.addEventListener("click", function (event) {
      var link = event.target.closest ? event.target.closest("a") : null;
      if (!link) return;
      var href = link.getAttribute("href") || "";
      var method = null;
      if (href.indexOf("wa.me/33769871108") !== -1) method = "whatsapp";
      else if (href.indexOf("tel:+33769871108") === 0) method = "phone";
      else if (href.indexOf("devis/") !== -1) method = "quote";
      if (!method) return;
      var detail = { method: method, pagePath: PAGE_PATH, pageTitle: document.title };
      window.dataLayer = window.dataLayer || [];
      window.dataLayer.push({ event: "contact_click", contact_method: method, page_path: PAGE_PATH, page_title: document.title });
      try { window.dispatchEvent(new CustomEvent("contact_click", { detail: detail })); } catch (error) { /* Legacy browser: dataLayer remains available. */ }
    });
  }

  function mountWhatsAppNotice() {
    if (document.querySelector(".gh-whatsapp-notice")) return;

    try {
      if (window.sessionStorage.getItem("gh-whatsapp-notice-shown") === "1") return;
    } catch (error) { /* Storage can be unavailable in private browsing. */ }

    var copy = WHATSAPP_COPY[CURRENT] || WHATSAPP_COPY.fr;
    var projectCopy = PROJECT_COPY[CURRENT] || PROJECT_COPY.fr;
    var destination = isProjectPage() ? projectWhatsAppUrl(projectCopy) : "https://wa.me/33769871108?text=" + encodeURIComponent(copy.preset);
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
        '<a class="gh-whatsapp-notice__action" href="' + destination + '" target="_blank" rel="noopener">' + copy.action + "</a>" +
      "</div>";

    notice.querySelector(".gh-whatsapp-notice__close").addEventListener("click", function () {
      notice.classList.remove("is-visible");
      window.setTimeout(function () { notice.remove(); }, 250);
    });

    document.body.appendChild(notice);
    window.setTimeout(function () {
      if (document.body.contains(notice)) {
        notice.classList.add("is-visible");
        try { window.sessionStorage.setItem("gh-whatsapp-notice-shown", "1"); } catch (error) { /* Optional enhancement. */ }
      }
    }, 5500);
  }

  function findProjectImages() {
    var selectors = [".rt-hero-main-image-wrapper img", ".rt-feature-image-wrapper img"];
    var images = [];
    selectors.forEach(function (selector) {
      var image = document.querySelector(selector);
      if (image && image.getAttribute("src") && images.indexOf(image) === -1) images.push(image);
    });
    return images;
  }

  function mountProjectGallery(copy, anchor) {
    var images = findProjectImages();
    if (!images.length) return;

    var section = document.createElement("section");
    section.className = "gh-project-gallery";
    section.innerHTML = '<div class="rt-container w-container"><div class="gh-project-heading"><h2>' + copy.galleryTitle + '</h2><p>' + copy.galleryHint + '</p></div><div class="gh-project-gallery__grid"></div></div>';
    var grid = section.querySelector(".gh-project-gallery__grid");

    images.forEach(function (source, index) {
      source.decoding = "async";
      if (index > 0) source.loading = "lazy";
      var button = document.createElement("button");
      button.type = "button";
      button.className = "gh-project-gallery__item";
      button.setAttribute("aria-label", copy.openImage + " " + (index + 1));
      var clone = source.cloneNode(true);
      clone.removeAttribute("style");
      clone.removeAttribute("data-w-id");
      clone.loading = "lazy";
      button.appendChild(clone);
      button.addEventListener("click", function () { openLightbox(index); });
      grid.appendChild(button);
    });

    var lightbox = document.createElement("div");
    lightbox.className = "gh-lightbox";
    lightbox.setAttribute("role", "dialog");
    lightbox.setAttribute("aria-modal", "true");
    lightbox.setAttribute("aria-label", copy.galleryTitle);
    lightbox.innerHTML = '<button class="gh-lightbox__close" type="button" aria-label="' + copy.closeGallery + '">&times;</button><button class="gh-lightbox__nav gh-lightbox__nav--prev" type="button" aria-label="' + copy.previous + '">&#8249;</button><img class="gh-lightbox__image" alt=""><button class="gh-lightbox__nav gh-lightbox__nav--next" type="button" aria-label="' + copy.next + '">&#8250;</button><span class="gh-lightbox__count"></span>';
    document.body.appendChild(lightbox);
    var activeIndex = 0;
    var closeButton = lightbox.querySelector(".gh-lightbox__close");

    function showImage(index) {
      activeIndex = (index + images.length) % images.length;
      var source = images[activeIndex];
      var target = lightbox.querySelector(".gh-lightbox__image");
      target.src = source.currentSrc || source.src;
      target.alt = source.alt || projectTitle();
      lightbox.querySelector(".gh-lightbox__count").textContent = (activeIndex + 1) + " / " + images.length;
    }
    function openLightbox(index) {
      showImage(index);
      lightbox.classList.add("is-open");
      document.body.classList.add("gh-lightbox-open");
      closeButton.focus();
    }
    function closeLightbox() {
      lightbox.classList.remove("is-open");
      document.body.classList.remove("gh-lightbox-open");
    }
    closeButton.addEventListener("click", closeLightbox);
    lightbox.querySelector(".gh-lightbox__nav--prev").addEventListener("click", function () { showImage(activeIndex - 1); });
    lightbox.querySelector(".gh-lightbox__nav--next").addEventListener("click", function () { showImage(activeIndex + 1); });
    lightbox.addEventListener("click", function (event) { if (event.target === lightbox) closeLightbox(); });
    document.addEventListener("keydown", function (event) {
      if (!lightbox.classList.contains("is-open")) return;
      if (event.key === "Escape") closeLightbox();
      else if (event.key === "ArrowLeft") showImage(activeIndex - 1);
      else if (event.key === "ArrowRight") showImage(activeIndex + 1);
    });

    anchor.parentNode.insertBefore(section, anchor);

    var beforeAfterImages = images.filter(function (image) { return /avant|après|before|after|prima|dopo/i.test(image.alt || ""); });
    if (beforeAfterImages.length >= 2) {
      var beforeAfter = document.createElement("div");
      beforeAfter.className = "gh-before-after";
      beforeAfter.innerHTML = "<h3>" + copy.beforeAfter + "</h3>";
      beforeAfterImages.slice(0, 2).forEach(function (image) {
        var clone = image.cloneNode(true);
        clone.removeAttribute("style");
        clone.loading = "lazy";
        beforeAfter.appendChild(clone);
      });
      section.querySelector(".rt-container").appendChild(beforeAfter);
    }
  }

  function sentenceMatching(text, expression, fallback) {
    var sentences = text.split(/[.!?]+/);
    for (var i = 0; i < sentences.length; i++) {
      if (expression.test(sentences[i])) return sentences[i].trim();
    }
    return fallback;
  }

  function mountProjectSummary(copy, anchor) {
    var overview = document.querySelector(".rt-project-overview-wrapper-v1 .w-richtext");
    var paragraphs = overview ? overview.querySelectorAll("p") : [];
    var fullText = overview ? overview.textContent.replace(/\s+/g, " ").trim() : "";
    var description = document.querySelector('meta[name="description"]');
    var locationSource = (description ? description.content : "") + " " + fullText;
    var knownPlaces = ["Nice", "Antibes", "Cannes", "Mougins", "Monaco", "Saint-Paul-de-Vence", "Cagnes-sur-Mer", "Villefranche-sur-Mer"];
    var location = copy.locationFallback;
    for (var i = 0; i < knownPlaces.length; i++) if (locationSource.indexOf(knownPlaces[i]) !== -1) { location = knownPlaces[i]; break; }

    var values = [
      paragraphs[0] ? paragraphs[0].textContent.trim() : (description ? description.content : projectTitle()),
      paragraphs[1] ? paragraphs[1].textContent.trim() : fullText,
      sentenceMatching(fullText, /acier|aluminium|inox|fer|métal|metal/i, copy.materialFallback),
      sentenceMatching(fullText, /thermola|galvani|peinture|patine|finition|laqu/i, copy.finishFallback),
      location,
      copy.durationFallback
    ];
    var labels = [copy.need, copy.solution, copy.material, copy.finish, copy.location, copy.duration];
    var section = document.createElement("section");
    section.className = "gh-project-summary";
    section.innerHTML = '<div class="rt-container w-container"><h2>' + copy.detailsTitle + '</h2><div class="gh-project-summary__grid"></div></div>';
    var grid = section.querySelector(".gh-project-summary__grid");
    labels.forEach(function (label, index) {
      var card = document.createElement("div");
      card.className = "gh-project-summary__card";
      var strong = document.createElement("strong");
      var span = document.createElement("span");
      strong.textContent = label;
      span.textContent = values[index] || "—";
      card.appendChild(strong);
      card.appendChild(span);
      grid.appendChild(card);
    });
    var commitments = document.querySelectorAll(".rt-project-scope-wrapper li");
    if (commitments.length) {
      var trust = document.createElement("div");
      trust.className = "gh-project-trust";
      trust.innerHTML = "<h3>" + copy.trustTitle + "</h3><ul></ul>";
      var list = trust.querySelector("ul");
      for (var j = 0; j < commitments.length; j++) {
        var item = document.createElement("li");
        item.textContent = commitments[j].textContent.trim();
        list.appendChild(item);
      }
      section.querySelector(".rt-container").appendChild(trust);
    }
    anchor.parentNode.insertBefore(section, anchor);
  }

  function mountProjectCta(copy, anchor) {
    var section = document.createElement("section");
    section.className = "gh-project-cta";
    section.innerHTML = '<div class="rt-container w-container"><div class="gh-project-cta__inner"><div><span class="gh-project-cta__badge">' + copy.quick + '</span><h2>' + copy.ctaTitle + '</h2><p>' + copy.ctaText + '</p><small>' + copy.hours + '</small></div><div class="gh-project-cta__actions"><a class="gh-project-cta__button gh-project-cta__button--whatsapp" target="_blank" rel="noopener">' + copy.whatsapp + '</a><a class="gh-project-cta__button" href="tel:+33769871108">' + copy.phone + '</a><a class="gh-project-cta__button gh-project-cta__button--quote" href="' + ROOT + 'devis/">' + copy.quote + '</a></div></div></div>';
    section.querySelector(".gh-project-cta__button--whatsapp").href = projectWhatsAppUrl(copy);
    anchor.parentNode.insertBefore(section, anchor);
  }

  function mountProjectMobileBar(copy) {
    var bar = document.createElement("nav");
    bar.className = "gh-project-mobile-bar";
    bar.setAttribute("aria-label", copy.ctaTitle);
    bar.innerHTML = '<a href="tel:+33769871108">' + copy.phone.replace(/ \+33.*/, "") + '</a><a class="gh-project-mobile-bar__whatsapp" target="_blank" rel="noopener">WhatsApp</a><a href="' + ROOT + 'devis/">' + copy.quote + '</a>';
    bar.querySelector(".gh-project-mobile-bar__whatsapp").href = projectWhatsAppUrl(copy);
    document.body.appendChild(bar);
  }

  function enhanceProjectPage() {
    if (!isProjectPage()) return;
    document.body.classList.add("gh-project-page");
    var copy = PROJECT_COPY[CURRENT] || PROJECT_COPY.fr;
    var anchor = document.querySelector(".rt-recent-post-v2") || document.querySelector(".rt-footer-v1");
    if (!anchor) return;
    mountProjectSummary(copy, anchor);
    mountProjectGallery(copy, anchor);
    mountProjectCta(copy, anchor);
    mountProjectMobileBar(copy);

    var similarHeading = anchor.querySelector("h2");
    if (similarHeading) similarHeading.textContent = copy.similar;
    var currentLinks = anchor.querySelectorAll('a[aria-current="page"]');
    for (var i = 0; i < currentLinks.length; i++) {
      var card = currentLinks[i].closest ? currentLinks[i].closest(".rt-portfolio-content-v2") : null;
      if (card) card.style.display = "none";
    }
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
    enhanceProjectPage();
    trackContactClicks();
    mountWhatsAppNotice();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
