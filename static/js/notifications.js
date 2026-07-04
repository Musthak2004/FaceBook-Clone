/* ============================================================
   Notifications JavaScript — Dropdown, Mark Read, Polling
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {
  initNotificationDropdown();
  initMarkRead();
  initMarkAllRead();
});

/* ---- Notification Dropdown Toggle ---- */
function initNotificationDropdown() {
  var toggle = document.querySelector('.notification-toggle');
  var dropdown = document.querySelector('.notification-dropdown');

  if (!toggle || !dropdown) return;

  toggle.addEventListener('click', function (e) {
    e.stopPropagation();
    e.preventDefault();

    dropdown.classList.toggle('show');

    // Fetch notifications
    if (dropdown.classList.contains('show')) {
      fetchNotifications();
    }
  });

  // Close on outside click
  document.addEventListener('click', function (e) {
    if (!dropdown.contains(e.target) && !toggle.contains(e.target)) {
      dropdown.classList.remove('show');
    }
  });
}

/* ---- Fetch Notifications (AJAX) ---- */
function fetchNotifications() {
  var list = document.querySelector('.notification-dropdown-list');
  if (!list) return;

  fetch('/notifications/?format=json', {
    headers: { 'X-Requested-With': 'XMLHttpRequest' },
  })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (data.html) {
        list.innerHTML = data.html;
      }
    })
    .catch(function () { /* Silently fail */ });
}

/* ---- Mark Single Notification as Read ---- */
function initMarkRead() {
  document.addEventListener('click', function (e) {
    var item = e.target.closest('.notification-item');
    if (!item) return;

    var notificationId = item.getAttribute('data-notification-id');
    if (!notificationId) return;

    var isUnread = item.classList.contains('unread');
    if (isUnread) {
      var csrfToken = getCookie('csrftoken');

      fetch('/notifications/read/' + notificationId + '/', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken },
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.read) {
            item.classList.remove('unread');
            var dot = item.querySelector('.unread-dot');
            if (dot) dot.remove();
            updateBadgeCount(-1);
          }
        })
        .catch(function () { /* Silently fail */ });
    }

    // Navigate to notification link if has one
    var link = item.getAttribute('data-href');
    if (link) {
      window.location.href = link;
    }
  });
}

/* ---- Mark All as Read ---- */
function initMarkAllRead() {
  var markAllBtn = document.querySelector('.mark-all-read');
  if (!markAllBtn) return;

  markAllBtn.addEventListener('click', function () {
    var csrfToken = getCookie('csrftoken');

    fetch('/notifications/read-all/', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken },
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.read_all) {
          document.querySelectorAll('.notification-item.unread').forEach(function (item) {
            item.classList.remove('unread');
            var dot = item.querySelector('.unread-dot');
            if (dot) dot.remove();
          });
          var badge = document.querySelector('.notification-badge');
          if (badge) badge.classList.add('hidden');
        }
      })
      .catch(function () { /* Silently fail */ });
  });
}

/* ---- Update Badge Count ---- */
function updateBadgeCount(delta) {
  var badge = document.querySelector('.notification-badge');
  if (!badge) return;

  var count = parseInt(badge.textContent) || 0;
  count += delta;

  if (count > 0) {
    badge.textContent = count;
    badge.classList.remove('hidden');
  } else {
    badge.classList.add('hidden');
  }
}
