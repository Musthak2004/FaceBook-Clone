/* ============================================================
   Shared utility functions
   ============================================================ */

/**
 * Read a cookie value by name.
 */
export function getCookie(name) {
  var value = '; ' + document.cookie;
  var parts = value.split('; ' + name + '=');
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

/**
 * Check if an HTTP method is safe (no CSRF token needed for these).
 */
export function csrfSafeMethod(method) {
  return /^(GET|HEAD|OPTIONS|TRACE)$/.test(method);
}

/**
 * Show a brief toast notification.
 */
export function showToast(message) {
  var toast = document.getElementById('toast-container');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast-container';
    toast.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);z-index:9999;display:flex;flex-direction:column;gap:10px;pointer-events:none;align-items:center;';
    document.body.appendChild(toast);
  }
  var el = document.createElement('div');
  el.className = 'toast-social';
  el.textContent = message;
  toast.appendChild(el);
  setTimeout(function () {
    el.classList.remove('show');
    setTimeout(function () { el.remove(); }, 300);
  }, 2800);
}

/**
 * Format a date as a human-friendly relative string.
 */
export function timeAgo(dateString) {
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

/**
 * Escape HTML entities (XSS-safe).
 */
export function escapeHtml(text) {
  var div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
