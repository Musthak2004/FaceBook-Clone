/* ============================================================
   Search module — Live Search, Search Tabs
   ============================================================ */

import { escapeHtml } from './utils.js';

export function initLiveSearch() {
  var searchInput = document.querySelector('.nav-search input[name="q"]');
  if (!searchInput) return;

  var searchTimeout;

  searchInput.addEventListener('input', function () {
    clearTimeout(searchTimeout);
    var query = this.value.trim();

    if (query.length < 2) {
      hideSearchResults();
      return;
    }

    searchTimeout = setTimeout(function () {
      performSearch(query);
    }, 300);
  });

  document.addEventListener('click', function (e) {
    var results = document.querySelector('.live-search-results');
    if (results && !e.target.closest('.nav-search')) {
      results.classList.add('hidden');
    }
  });
}

function performSearch(query) {
  fetch('/search/?q=' + encodeURIComponent(query) + '&format=json', {
    headers: { 'X-Requested-With': 'XMLHttpRequest' },
  })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      showSearchResults(data, query);
    })
    .catch(function () {});
}

function showSearchResults(data, query) {
  var container = document.querySelector('.live-search-results');
  if (!container) {
    container = document.createElement('div');
    container.className = 'live-search-results dropdown-menu show';
    container.style.cssText =
      'position:absolute;top:100%;left:0;right:0;z-index:200;' +
      'max-height:400px;overflow-y:auto;';
    document.querySelector('.nav-search').appendChild(container);
  }

  container.classList.remove('hidden');

  var html = '';

  if (data.users && data.users.length > 0) {
    html += '<div class="search-results-section">';
    html += '<div class="search-results-label">People</div>';
    data.users.forEach(function (user) {
      html +=
        '<a href="' + user.url + '" class="dropdown-item">' +
        '<img src="' + (user.avatar || '/static/images/default-avatar.png') + '" ' +
        'alt="" class="avatar avatar-sm">' +
        '<span>' + escapeHtml(user.username) + '</span>' +
        '</a>';
    });
    html += '</div>';
  }

  if (data.posts && data.posts.length > 0) {
    html += '<div class="search-results-section">';
    html += '<div class="search-results-label">Posts</div>';
    data.posts.forEach(function (post) {
      html +=
        '<a href="' + post.url + '" class="dropdown-item">' +
        '<span>' + escapeHtml(post.content.substring(0, 60)) + '</span>' +
        '</a>';
    });
    html += '</div>';
  }

  if (!html) {
    html =
      '<div class="dropdown-item" style="color:var(--text-muted)">' +
      'No results for "' + escapeHtml(query) + '"' +
      '</div>';
  }

  html +=
    '<div class="dropdown-divider"></div>' +
    '<a href="/search/?q=' + encodeURIComponent(query) + '" class="dropdown-item" ' +
    'style="justify-content:center;color:var(--primary);font-weight:600;">' +
    'See all results</a>';

  container.innerHTML = html;
}

function hideSearchResults() {
  var container = document.querySelector('.live-search-results');
  if (container) container.classList.add('hidden');
}

export function initSearchTabs() {
  var tabs = document.querySelectorAll('.search-tabs .tab');
  if (!tabs.length) return;

  tabs.forEach(function (tab) {
    tab.addEventListener('click', function () {
      var type = this.getAttribute('data-type');

      tabs.forEach(function (t) { t.classList.remove('active'); });
      this.classList.add('active');

      var typeInput = document.querySelector('input[name="type"]');
      if (typeInput) typeInput.value = type;

      var form = document.querySelector('.search-form');
      if (form) form.submit();
    });
  });
}

export function initSearch() {
  initLiveSearch();
  initSearchTabs();
}
