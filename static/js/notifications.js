/* ============================================================
   Notifications JavaScript — WebSocket, Dropdown, Mark Read
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {
  initNotificationWebSocket();
  initNotificationDropdown();
  initMarkRead();
  initMarkAllRead();
});

/* ---- WebSocket Connection ---- */
let notificationSocket = null;

function initNotificationWebSocket() {
  var badge = document.querySelector('.notification-badge');
  if (!badge) return;

  var wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
  var wsUrl = wsScheme + '://' + window.location.host + '/ws/notifications/';

  function connect() {
    notificationSocket = new WebSocket(wsUrl);

    notificationSocket.onopen = function () {
      console.debug('Notification WebSocket connected');
    };

    notificationSocket.onmessage = function (e) {
      try {
        var data = JSON.parse(e.data);

        if (data.type === 'notification') {
          // Update badge
          updateBadge(data.unread_count);
          // Show a brief toast for real-time feedback
          showToast(data.message);
        } else if (data.type === 'unread_count') {
          updateBadge(data.count);
        }
      } catch (err) {
        console.error('Notification WS error:', err);
      }
    };

    notificationSocket.onclose = function () {
      console.debug('Notification WebSocket disconnected');
      // Fall back to polling if WS fails
      setTimeout(startPollingFallback, 5000);
    };

    notificationSocket.onerror = function () {
      notificationSocket.close();
    };
  }

  connect();
}

/* ---- Polling Fallback ---- */
let pollInterval = null;

function startPollingFallback() {
  if (pollInterval) return;
  var badge = document.querySelector('.notification-badge');
  if (!badge) return;

  function poll() {
    var url = badge.getAttribute('data-poll-url') || '/notifications/';
    fetch(url + '?count=1')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        updateBadge(data.unread_count || 0);
      })
      .catch(function () {});
  }

  pollInterval = setInterval(poll, 30000);
}

/* ---- Update Badge ---- */
function updateBadge(count) {
  var badge = document.querySelector('.notification-badge');
  if (!badge) return;

  if (count > 0) {
    badge.textContent = count > 99 ? '99+' : count;
    badge.classList.remove('hidden');
  } else {
    badge.classList.add('hidden');
  }
}

/* ---- Notification Dropdown Toggle ---- */
function initNotificationDropdown() {
  var toggle = document.querySelector('.notification-toggle');
  var dropdown = document.querySelector('.notification-dropdown');

  if (!toggle || !dropdown) return;

  toggle.addEventListener('click', function (e) {
    e.stopPropagation();
    e.preventDefault();

    dropdown.classList.toggle('show');

    if (dropdown.classList.contains('show')) {
      fetchNotifications();
    }
  });

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
    .catch(function () {});
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
            // Notify WebSocket
            if (notificationSocket && notificationSocket.readyState === WebSocket.OPEN) {
              notificationSocket.send(JSON.stringify({
                type: 'mark_read',
                notification_id: parseInt(notificationId),
              }));
            } else {
              updateBadgeDelta(-1);
            }
          }
        })
        .catch(function () {});
    }

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
          // Notify WebSocket
          if (notificationSocket && notificationSocket.readyState === WebSocket.OPEN) {
            notificationSocket.send(JSON.stringify({ type: 'mark_all_read' }));
          } else {
            var badge = document.querySelector('.notification-badge');
            if (badge) badge.classList.add('hidden');
          }
        }
      })
      .catch(function () {});
  });
}

/* ---- Delta update for fallback ---- */
function updateBadgeDelta(delta) {
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
