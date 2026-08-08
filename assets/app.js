/* THE DISPATCH — theme toggle, client-side search & tag filtering.
   No inline handlers (strict CSP: script-src 'self'). */
(function () {
  'use strict';

  /* ---------- theme toggle ---------- */
  var toggle = document.getElementById('theme-toggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try { localStorage.setItem('dispatch-theme', next); } catch (e) { /* ignore */ }
    });
  }

  /* ---------- archive search + tag filter ---------- */
  var list = document.getElementById('archive');
  if (!list) return;

  var input = document.getElementById('search');
  var noResults = document.getElementById('no-results');
  var countEl = document.getElementById('entry-count');
  var entries = Array.prototype.slice.call(list.querySelectorAll('.entry'));
  var activeTag = null;

  function haystack(entry) {
    return (entry.getAttribute('data-title') + ' ' +
            entry.getAttribute('data-tags') + ' ' +
            (entry.getAttribute('data-excerpt') || '')).toLowerCase();
  }

  function applyFilter() {
    var q = input ? input.value.trim().toLowerCase() : '';
    var visible = 0;
    entries.forEach(function (entry) {
      var tags = (entry.getAttribute('data-tags') || '').toLowerCase().split('|');
      var tagOk = !activeTag || tags.indexOf(activeTag) !== -1;
      var qOk = !q || haystack(entry).indexOf(q) !== -1;
      var show = tagOk && qOk;
      entry.style.display = show ? '' : 'none';
      if (show) visible++;
    });
    if (noResults) noResults.style.display = visible === 0 ? 'block' : 'none';
    if (countEl) countEl.textContent = String(visible).padStart(2, '0');
  }

  if (input) input.addEventListener('input', applyFilter);

  document.querySelectorAll('[data-tag-filter]').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      var t = btn.getAttribute('data-tag-filter').toLowerCase();
      activeTag = (activeTag === t) ? null : t;
      document.querySelectorAll('[data-tag-filter]').forEach(function (b) {
        b.classList.toggle('active', activeTag !== null && b.getAttribute('data-tag-filter').toLowerCase() === activeTag);
      });
      applyFilter();
    });
  });
})();
