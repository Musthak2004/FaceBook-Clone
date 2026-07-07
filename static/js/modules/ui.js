/* ============================================================
   UI utilities — Dropdowns, Modals, Mobile Nav
   ============================================================ */

import { getCookie } from './utils.js';

export function initDropdowns() {
  document.querySelectorAll('.dropdown-toggle').forEach(function (toggle) {
    toggle.addEventListener('click', function (e) {
      e.stopPropagation();
      var dropdown = this.closest('.dropdown');
      var menu = dropdown.querySelector('.dropdown-menu');

      // Close all other dropdowns
      document.querySelectorAll('.dropdown-menu.show').forEach(function (m) {
        if (m !== menu) m.classList.remove('show');
      });

      menu.classList.toggle('show');
    });
  });

  // Close dropdowns on outside click
  document.addEventListener('click', function () {
    document.querySelectorAll('.dropdown-menu.show').forEach(function (menu) {
      menu.classList.remove('show');
    });
  });
}

export function openModal(modal) {
  modal.classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

export function closeModal(modal) {
  modal.classList.add('hidden');
  document.body.style.overflow = '';
}

export function initModals() {
  document.querySelectorAll('[data-modal-target]').forEach(function (trigger) {
    trigger.addEventListener('click', function () {
      var modalId = this.getAttribute('data-modal-target');
      var modal = document.getElementById(modalId);
      if (modal) openModal(modal);
    });
  });

  document.querySelectorAll('.modal-close, .modal-overlay').forEach(function (el) {
    el.addEventListener('click', function (e) {
      if (this.classList.contains('modal-overlay') && e.target !== this) return;
      var modal = this.closest('.modal-overlay');
      if (modal) closeModal(modal);
    });
  });

  // Close modal on Escape key
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay').forEach(function (modal) {
        closeModal(modal);
      });
    }
  });
}

// Mobile nav is now handled by base.html inline script (uses #mobile-menu-toggle, #mobile-nav-menu, #mobile-backdrop)
export function initMobileNav() {
  // no-op — kept for import compatibility
}

export function initTheme() {
  var toggle = document.getElementById('theme-toggle');
  if (!toggle) return;

  var current = localStorage.getItem('theme') || 'light';
  applyTheme(current);

  toggle.addEventListener('click', function () {
    var next = document.documentElement.getAttribute('data-theme') === 'dark'
      ? 'light'
      : 'dark';
    applyTheme(next);
    localStorage.setItem('theme', next);
  });
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  // Set Tailwind dark class
  if (theme === 'dark') {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
  var toggle = document.getElementById('theme-toggle');
  if (toggle) {
    toggle.innerHTML = theme === 'dark'
      ? '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>'
      : '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>';
  }
}

export function initAjaxForms() {
  var csrftoken = getCookie('csrftoken');
  document.addEventListener('click', function (e) {
    var form = e.target.closest('form[data-ajax]');
    if (form) {
      e.preventDefault();
      var formData = new FormData(form);
      fetch(form.action, {
        method: form.method || 'POST',
        body: formData,
        headers: { 'X-CSRFToken': csrftoken }
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          var event = new CustomEvent('ajax:response', { detail: data, bubbles: true });
          form.dispatchEvent(event);
        })
        .catch(function (err) { console.error('AJAX error:', err); });
    }
  });
}
