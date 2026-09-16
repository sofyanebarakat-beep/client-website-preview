/*
 * Lightweight client-side language switcher for the (Webflow-exported) static site.
 *
 * - Languages: French (default / source), English, Italian.
 * - The page markup is authored in FRENCH; EN / IT come from window.SITE_TRANSLATIONS
 *   (see translations.js). Strings with no entry stay in French ("content later").
 * - The chosen language is saved in localStorage and applied on every page.
 * - A flag + code dropdown is injected into the navbar, right AFTER the "Devis gratuit" button.
 */
(function () {
  "use strict";

  var STORAGE_KEY = "siteLang";
  var SOURCE_LANG = "fr";
  var DEFAULT_LANG = "fr";

  /* Inline SVG flags – render identically on every OS (emoji flags don't show on Windows). */
  var FLAGS = {
    fr: '<svg viewBox="0 0 3 2" width="20" height="14" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><rect width="3" height="2" fill="#fff"/><rect width="1" height="2" fill="#002395"/><rect width="1" height="2" x="2" fill="#ED2939"/></svg>',
    en: '<svg viewBox="0 0 60 30" width="20" height="14" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><clipPath id="i18n-uk"><rect width="60" height="30"/></clipPath><g clip-path="url(#i18n-uk)"><rect width="60" height="30" fill="#012169"/><path d="M0,0 60,30M60,0 0,30" stroke="#fff" stroke-width="6"/><path d="M0,0 60,30M60,0 0,30" stroke="#C8102E" stroke-width="4"/><path d="M30,0 V30M0,15 H60" stroke="#fff" stroke-width="10"/><path d="M30,0 V30M0,15 H60" stroke="#C8102E" stroke-width="6"/></g></svg>',
    it: '<svg viewBox="0 0 3 2" width="20" height="14" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><rect width="3" height="2" fill="#fff"/><rect width="1" height="2" fill="#008C45"/><rect width="1" height="2" x="2" fill="#CD212A"/></svg>'
  };

  var LANGS = [
    { code: "fr", label: "Français", short: "FR" },
    { code: "en", label: "English", short: "EN" },
    { code: "it", label: "Italiano", short: "IT" }
  ];

  var DICT = window.SITE_TRANSLATIONS || {};

  /* Remember the original (English) value of every node we touch so we can
     switch back and forth without reloading the page. */
  var originals = new WeakMap();

  function getLang() {
    var v;
    try { v = localStorage.getItem(STORAGE_KEY); } catch (e) { v = null; }
    if (v && LANGS.some(function (l) { return l.code === v; })) return v;
    return DEFAULT_LANG;
  }

  function setLang(code) {
    try { localStorage.setItem(STORAGE_KEY, code); } catch (e) {}
  }

  function norm(s) {
    return s.replace(/\s+/g, " ").trim();
  }

  function translateString(key, lang) {
    if (lang === SOURCE_LANG) return null;      // French is the source language
    var entry = DICT[key];
    if (entry && entry[lang]) return entry[lang];
    return null;
  }

  /* ---- apply translation to a single text node ---- */
  function handleTextNode(node, lang) {
    var raw = originals.has(node) ? originals.get(node) : node.nodeValue;
    var key = norm(raw);
    if (!key) return;
    if (!originals.has(node)) originals.set(node, raw);

    var lead = raw.match(/^\s*/)[0];
    var trail = raw.match(/\s*$/)[0];
    var translated = translateString(key, lang);
    node.nodeValue = translated == null ? raw : (lead + translated + trail);
  }

  /* ---- apply translation to an attribute (placeholder / aria-label / value) ---- */
  function handleAttr(el, attr, lang) {
    var store = "__i18n_" + attr;
    var raw = el[store] != null ? el[store] : el.getAttribute(attr);
    if (raw == null) return;
    var key = norm(raw);
    if (!key) return;
    if (el[store] == null) el[store] = raw;
    var translated = translateString(key, lang);
    el.setAttribute(attr, translated == null ? raw : translated);
  }

  var SKIP_TAGS = { SCRIPT: 1, STYLE: 1, NOSCRIPT: 1, CODE: 1, PRE: 1 };
  var applying = false;

  function translateTree(root, lang) {
    if (!root) return;

    if (root.nodeType === 3) { handleTextNode(root, lang); return; }
    if (root.nodeType !== 1) return;
    if (SKIP_TAGS[root.tagName]) return;
    if (root.classList && root.classList.contains("lang-switch")) return;

    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        var p = n.parentNode;
        while (p && p.nodeType === 1) {
          if (SKIP_TAGS[p.tagName]) return NodeFilter.FILTER_REJECT;
          if (p.classList && p.classList.contains("lang-switch")) return NodeFilter.FILTER_REJECT;
          p = p.parentNode;
        }
        return n.nodeValue && n.nodeValue.trim()
          ? NodeFilter.FILTER_ACCEPT
          : NodeFilter.FILTER_REJECT;
      }
    });
    var textNodes = [];
    while (walker.nextNode()) textNodes.push(walker.currentNode);
    textNodes.forEach(function (n) { handleTextNode(n, lang); });

    var withPlaceholder = root.querySelectorAll("[placeholder]");
    for (var i = 0; i < withPlaceholder.length; i++) handleAttr(withPlaceholder[i], "placeholder", lang);

    var withAria = root.querySelectorAll("[aria-label]");
    for (var j = 0; j < withAria.length; j++) handleAttr(withAria[j], "aria-label", lang);

    var inputs = root.querySelectorAll('input[type="submit"], input[type="button"], input[type="reset"]');
    for (var k = 0; k < inputs.length; k++) handleAttr(inputs[k], "value", lang);
  }

  function applyLanguage(lang) {
    applying = true;
    document.documentElement.setAttribute("lang", lang);

    // <title>
    if (document.title) {
      var t = document.createTextNode(document.title);
      // reuse the text-node machinery on a detached node
      handleTextNode(t, lang);
      if (t.nodeValue !== document.title) document.title = t.nodeValue;
    }

    translateTree(document.body, lang);
    updateSwitchUI(lang);
    // let mutation events from our own writes settle
    setTimeout(function () { applying = false; }, 0);
  }

  /* ---------------- Switcher UI ---------------- */

  function injectStyles() {
    if (document.getElementById("lang-switch-styles")) return;
    var css =
      '.lang-switch{position:relative;display:inline-flex;align-items:center;font-family:inherit;margin-left:12px;z-index:900}' +
      '.lang-switch *{box-sizing:border-box}' +
      /* trigger: a plain circle, sized to roughly match the "Devis gratuit" button height,
         a touch larger for an easier tap target — flag only, no code / no caret */
      '.lang-switch__btn{display:inline-flex;align-items:center;justify-content:center;flex:0 0 auto;' +
      'cursor:pointer;border:1px solid rgba(0,0,0,.15);background:#fff;color:#111;border-radius:50%;' +
      'width:2.75rem;height:2.75rem;padding:0;transition:box-shadow .15s ease,border-color .15s ease}' +
      '.lang-switch__btn:hover{border-color:rgba(0,0,0,.35);box-shadow:0 2px 10px rgba(0,0,0,.12)}' +
      '.lang-switch__flag{display:inline-flex;line-height:0;border-radius:3px;overflow:hidden;' +
      'box-shadow:0 0 0 1px rgba(0,0,0,.12)}' +
      '.lang-switch__flag svg{display:block}' +
      /* trigger: the active flag fills the whole circular button edge-to-edge (cropped via
         preserveAspectRatio="slice"), no white padding / own border around it */
      '.lang-switch__btn .lang-switch__flag{width:100%;height:100%;border-radius:50%;box-shadow:none}' +
      '.lang-switch__btn .lang-switch__flag svg{width:100%;height:100%}' +
      '.lang-switch__menu{position:absolute;top:calc(100% + 8px);right:0;min-width:170px;background:#fff;color:#111;' +
      'border:1px solid rgba(0,0,0,.12);border-radius:12px;box-shadow:0 12px 30px rgba(0,0,0,.18);padding:6px;' +
      'display:none;flex-direction:column}' +
      '.lang-switch.is-open .lang-switch__menu{display:flex}' +
      '.lang-switch__item{display:flex;align-items:center;gap:10px;width:100%;background:none;border:0;cursor:pointer;' +
      'text-align:left;padding:10px 12px;border-radius:8px;font-size:14px;font-weight:600;color:#111}' +
      '.lang-switch__item:hover{background:rgba(0,0,0,.06)}' +
      '.lang-switch__item.is-active{background:rgba(0,0,0,.09)}' +
      '.lang-switch__check{margin-left:auto;font-size:13px;opacity:.7}' +
      /* desktop: compact the "Devis gratuit" CTA and keep the switch glued to it */
      '@media (min-width:992px){' +
      '.rt-navbar-button-wraper{display:flex;align-items:center;gap:8px}' +
      '.rt-navbar-button-wraper .lang-switch{margin-left:0}' +
      '.rt-navbar-button-wraper .rt-button{padding-left:1rem!important;padding-right:1rem!important}' +
      '.rt-navbar-button-wraper .rt-text-style-button{white-space:nowrap}}' +
      /* mobile: the theme hides the CTA wrapper; the switch is moved out (placeSwitch) */
      /* and pinned just left of the hamburger button */
      '@media (max-width:991px){.rt-navbar-wrapper-v4>.lang-switch{margin-left:auto;margin-right:6px}}' +
      /* hero CTAs: keep "Demander un devis" / "Voir nos réalisations" side by side */
      /* and each button's own text on a single line, even on small phones */
      '.rt-hero-button-wrapper{flex-direction:row!important;flex-wrap:wrap!important}' +
      '.rt-hero-button-wrapper>div{flex:0 0 auto!important}' +
      '.rt-hero-button-wrapper .rt-text-style-button{white-space:nowrap}';
    var style = document.createElement("style");
    style.id = "lang-switch-styles";
    style.textContent = css;
    document.head.appendChild(style);
  }

  var switchEls = [];

  function buildSwitch() {
    var current = getLang();
    var wrap = document.createElement("div");
    wrap.className = "lang-switch";

    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "lang-switch__btn";
    btn.setAttribute("aria-haspopup", "true");
    btn.setAttribute("aria-expanded", "false");
    // circle, flag only — the language name still reaches screen readers / hover via aria-label+title
    btn.innerHTML = '<span class="lang-switch__flag" data-flag></span>';

    var menu = document.createElement("div");
    menu.className = "lang-switch__menu";
    menu.setAttribute("role", "menu");

    LANGS.forEach(function (l) {
      var item = document.createElement("button");
      item.type = "button";
      item.className = "lang-switch__item" + (l.code === current ? " is-active" : "");
      item.setAttribute("role", "menuitem");
      item.dataset.code = l.code;
      item.innerHTML =
        '<span class="lang-switch__flag">' + FLAGS[l.code] + "</span>" +
        "<span>" + l.label + "</span>" +
        '<span class="lang-switch__check" aria-hidden="true">' + (l.code === current ? "✓" : "") + "</span>";
      item.addEventListener("click", function () {
        close(wrap, btn);
        if (l.code === getLang()) return;
        setLang(l.code);
        applyLanguage(l.code);
      });
      menu.appendChild(item);
    });

    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      var open = wrap.classList.toggle("is-open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });

    wrap.appendChild(btn);
    wrap.appendChild(menu);
    switchEls.push(wrap);
    return wrap;
  }

  function close(wrap, btn) {
    wrap.classList.remove("is-open");
    if (btn) btn.setAttribute("aria-expanded", "false");
  }

  function updateSwitchUI(lang) {
    var meta = LANGS.filter(function (l) { return l.code === lang; })[0] || LANGS[0];
    switchEls.forEach(function (wrap) {
      var f = wrap.querySelector("[data-flag]");
      if (f) f.innerHTML = FLAGS[meta.code] || "";
      var btn = wrap.querySelector(".lang-switch__btn");
      if (btn) {
        var label = "Langue : " + meta.label;
        btn.setAttribute("aria-label", label);
        btn.title = label;
      }
      var items = wrap.querySelectorAll(".lang-switch__item");
      for (var i = 0; i < items.length; i++) {
        var active = items[i].dataset.code === lang;
        items[i].classList.toggle("is-active", active);
        var chk = items[i].querySelector(".lang-switch__check");
        if (chk) chk.textContent = active ? "✓" : "";
      }
    });
  }

  var MOBILE_MQ = "(max-width:991px)";

  /* Desktop: switch lives INSIDE the CTA wrapper, glued to the "Devis gratuit"
     button. Mobile: the theme hides that wrapper, so move the switch out to sit
     just left of the hamburger button. */
  function placeSwitch(sw, ctaWrap) {
    var isMobile = window.matchMedia(MOBILE_MQ).matches;
    var hamburger = ctaWrap.parentNode.querySelector(".rt-mobile-list-button");
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
      // Fallback: fixed top-right corner
      var sw2 = buildSwitch();
      sw2.style.position = "fixed";
      sw2.style.top = "16px";
      sw2.style.right = "16px";
      sw2.style.zIndex = "9999";
      document.body.appendChild(sw2);
    }

    document.addEventListener("click", function () {
      switchEls.forEach(function (w) { close(w, w.querySelector(".lang-switch__btn")); });
    });
  }

  /* ---------------- Re-translate Webflow-injected / cloned content ---------------- */
  function observe() {
    if (!window.MutationObserver) return;
    var pending = null;
    var obs = new MutationObserver(function (muts) {
      if (applying) return;
      var lang = getLang();
      if (lang === SOURCE_LANG) return;
      for (var i = 0; i < muts.length; i++) {
        var added = muts[i].addedNodes;
        for (var j = 0; j < added.length; j++) {
          var n = added[j];
          if (n.nodeType === 1 || n.nodeType === 3) {
            if (n.nodeType === 1 && n.classList && n.classList.contains("lang-switch")) continue;
            (function (node) {
              if (pending) clearTimeout(pending);
              pending = setTimeout(function () {
                applying = true;
                translateTree(node, getLang());
                setTimeout(function () { applying = false; }, 0);
              }, 50);
            })(n);
          }
        }
      }
    });
    obs.observe(document.body, { childList: true, subtree: true });
  }

  /* ---------------- init ---------------- */
  function init() {
    if (window.__i18nInit) return;
    window.__i18nInit = true;
    injectStyles();
    mountSwitch();
    applyLanguage(getLang());
    observe();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
