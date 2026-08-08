/* Loaded synchronously in <head> so the correct theme is painted
   on the very first frame (no flash of wrong theme). */
(function () {
  var stored = null;
  try { stored = localStorage.getItem('dispatch-theme'); } catch (e) { /* private mode */ }
  var theme = stored || (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  document.documentElement.setAttribute('data-theme', theme);
})();
