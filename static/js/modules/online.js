/* ============================================================
   Online Status module — Heartbeat ping + indicator refresh
   ============================================================ */

import { getCookie } from './utils.js';

export function initHeartbeat() {
  var userId = document.body.getAttribute('data-user-id');
  if (!userId) return;

  function ping() {
    fetch('/accounts/heartbeat/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.status === 'ok') {
          // Update online dots for friends
          var onlineIds = data.online_friends || [];
          document.querySelectorAll('[data-user-id]').forEach(function (el) {
            var uid = parseInt(el.getAttribute('data-user-id'), 10);
            var dot = el.querySelector('.online-dot');
            if (!dot) return;
            if (onlineIds.includes(uid)) {
              dot.classList.remove('offline');
            } else {
              dot.classList.add('offline');
            }
          });
        }
      })
      .catch(function () { /* ignore network errors */ });
  }

  // Ping every 2 minutes
  ping();
  setInterval(ping, 120000);
}
