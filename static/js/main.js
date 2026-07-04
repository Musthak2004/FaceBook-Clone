/* ============================================================
   Main JavaScript — Navigation, Dropdowns, Modals, Utils
   ============================================================ */

// DOM Ready
document.addEventListener('DOMContentLoaded', function () {
  initDropdowns();
  initModals();
  initMobileNav();
  initNotificationPolling();
});

/* ---- Dropdowns ---- */
function initDropdowns() {
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

/* ---- Modals ---- */
function initModals() {
  document.querySelectorAll('[data-modal-target]').forEach(function (trigger) {
    trigger.addEventListener('click', function () {
      var modalId = this.getAttribute('data-modal-target');
      var modal = document.getElementById(modalId);
      if (modal) openModal(modal);
    });
  });

  document.querySelectorAll('.modal-close, .modal-overlay').forEach(function (el) {
    el.addEventListener('click', function (e) {
      /* Only close when clicking the overlay BACKGROUND itself,
         not when clicks bubble up from child elements (form fields, etc.). */
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

function openModal(modal) {
  modal.classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function closeModal(modal) {
  modal.classList.add('hidden');
  document.body.style.overflow = '';
}

/* ---- Mobile Nav Toggle ---- */
function initMobileNav() {
  var toggle = document.querySelector('.mobile-nav-toggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      document.querySelector('.nav-links').classList.toggle('show');
    });
  }
}

/* ---- Notification Polling ---- */
function initNotificationPolling() {
  var badge = document.querySelector('.notification-badge');
  if (!badge) return;

  function pollNotifications() {
    var url = badge.getAttribute('data-poll-url') || '/notifications/';
    fetch(url + '?count=1')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var count = data.unread_count || 0;
        if (count > 0) {
          badge.textContent = count > 99 ? '99+' : count;
          badge.classList.remove('hidden');
        } else {
          badge.classList.add('hidden');
        }
      })
      .catch(function () { /* Silently fail */ });
  }

  // Poll every 30 seconds
  setInterval(pollNotifications, 30000);
}

/* ---- Utility Functions ---- */
function getCookie(name) {
  var value = '; ' + document.cookie;
  var parts = value.split('; ' + name + '=');
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

function csrfSafeMethod(method) {
  return /^(GET|HEAD|OPTIONS|TRACE)$/.test(method);
}

function setupAjax() {
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

// Show toast notification
function showToast(message) {
  var toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(function () { toast.remove(); }, 3000);
}

// Format relative time
function timeAgo(dateString) {
  var now = new Date();
  var date = new Date(dateString);
  var seconds = Math.floor((now - date) / 1000);

  if (seconds < 60) return 'just now';
  var minutes = Math.floor(seconds / 60);
  if (minutes < 60) return minutes + 'm';
  var hours = Math.floor(minutes / 60);
  if (hours < 24) return hours + 'h';
  var days = Math.floor(hours / 24);
  if (days < 7) return days + 'd';
  return date.toLocaleDateString();
}
