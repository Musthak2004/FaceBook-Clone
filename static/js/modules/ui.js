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

export function initMobileNav() {
  var toggle = document.querySelector('.mobile-nav-toggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      document.querySelector('.nav-links').classList.toggle('show');
    });
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
