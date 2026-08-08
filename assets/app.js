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

/* ---------- scroll reveal — mirrors the anmolbakshi.com dossier ---------- */
(function () {
  'use strict';
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce || !('IntersectionObserver' in window)) return;

  document.querySelectorAll('.hero h1, .post-head h1').forEach(function (el) {
    el.classList.add('reveal-title');
  });
  ['.hero-kicker', '.hero-lede', '.hero-sub',
   '.ticker', '.controls', '.archive-meta',
   '.post-kicker', '.post-head .standfirst', '.post-byline',
   '.article', '.fig-rule', '.post-nav'
  ].forEach(function (sel) {
    document.querySelectorAll(sel).forEach(function (el) { el.classList.add('reveal'); });
  });
  var archive = document.getElementById('archive');
  if (archive) archive.classList.add('reveal-stagger');

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
    });
  }, { threshold: 0.01, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('.reveal, .reveal-title, .reveal-stagger').forEach(function (el) {
    io.observe(el);
  });

  /* Above-the-fold masthead/hero: fade in immediately on load. */
  requestAnimationFrame(function () {
    document.querySelectorAll('.hero .reveal-title, .hero .reveal, .ticker.reveal').forEach(function (el, i) {
      setTimeout(function () { el.classList.add('is-in'); }, 60 + i * 70);
    });
  });

  /* Safety net: never leave content hidden if the observer misfires. */
  setTimeout(function () {
    document.querySelectorAll('.reveal, .reveal-title, .reveal-stagger').forEach(function (el) {
      el.classList.add('is-in');
    });
  }, 1500);
})();
