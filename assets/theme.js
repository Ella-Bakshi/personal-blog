/* Clickjacking guard: CSP frame-ancestors is ignored in a <meta> tag (GitHub Pages
   can't emit HTTP headers), so bust out of frames here as a fallback. Scoped to the
   production host so it never blanks legitimate dev/preview embeds. The real fix is the
   X-Frame-Options / frame-ancestors HTTP header in _headers on Cloudflare Pages / Netlify. */
(function () {
  try {
    if (location.hostname === 'blog.anmolbakshi.com' && window.top !== window.self) {
      window.top.location = window.self.location;
    }
  } catch (e) { document.documentElement.style.display = 'none'; }
})();

/* Loaded synchronously in <head> so the correct theme is painted
   on the very first frame (no flash of wrong theme). */
(function () {
  var stored = null;
  try { stored = localStorage.getItem('dispatch-theme'); } catch (e) { /* private mode */ }
  var theme = stored || (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  document.documentElement.setAttribute('data-theme', theme);
})();
