/* ============================================================
   Loading States — Button states, global spinner, page loading
   ============================================================ */

/**
 * Add loading state to a button element.
 * Returns a cleanup function that restores the button.
 */
export function setButtonLoading(btn) {
  btn.classList.add('btn-loading');
  btn.disabled = true;
  return function () {
    btn.classList.remove('btn-loading');
    btn.disabled = false;
  };
}

/**
 * Show a full-page overlay spinner (for page transitions).
 * Returns a cleanup function to remove it.
 */
export function showPageSpinner() {
  var overlay = document.createElement('div');
  overlay.style.cssText =
    'position:fixed;top:0;left:0;right:0;bottom:0;' +
    'background:var(--bg-secondary);z-index:9999;' +
    'display:flex;align-items:center;justify-content:center;' +
    'opacity:0;transition:opacity 0.2s ease;';
  overlay.innerHTML = '<div class="spinner spinner-lg"></div>';
  document.body.appendChild(overlay);
  // Trigger fade-in
  requestAnimationFrame(function () {
    overlay.style.opacity = '1';
  });
  return function () {
    overlay.style.opacity = '0';
    setTimeout(function () { overlay.remove(); }, 250);
  };
}

/**
 * Set loading state on a form submit button.
 * Hooks a one-time event on form submit.
 */
export function initFormLoadingStates() {
  document.addEventListener('submit', function (e) {
    var form = e.target;
    if (form.getAttribute('data-no-loading') !== null) return;
    var submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
    if (submitBtn && !submitBtn.disabled) {
      setButtonLoading(submitBtn);
    }
  });
}
