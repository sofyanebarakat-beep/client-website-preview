/* Demo mode: block navigation so links, menu items and buttons never leave the current page. */
(function () {
  document.addEventListener(
    "click",
    function (e) {
      var link = e.target.closest("a[href]");
      if (!link) return;
      var href = link.getAttribute("href") || "";
      if (href.charAt(0) === "#" || href.indexOf("javascript:") === 0) return;
      e.preventDefault();
    },
    true
  );

  document.addEventListener(
    "submit",
    function (e) {
      e.preventDefault();
    },
    true
  );
})();
