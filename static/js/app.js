/* ============================================================
   SocialNet — Main application entry point (ES module)
   Initializes all UI components on DOM ready.
   ============================================================ */

import { initDropdowns, initModals, initMobileNav, initAjaxForms } from './modules/ui.js';
import { initNotifications } from './modules/notifications.js';
import { initFeed } from './modules/feed.js';
import { initMessaging } from './modules/messaging.js';
import { initSearch } from './modules/search.js';
import { initUpload } from './modules/upload.js';
import { initPostGalleries } from './modules/gallery.js';
import { initStories } from './modules/stories.js';

document.addEventListener('DOMContentLoaded', function () {
  // Global UI
  initDropdowns();
  initModals();
  initMobileNav();
  initAjaxForms();

  // Feature modules (each checks for its own DOM elements)
  initNotifications();
  initFeed();
  initMessaging();
  initSearch();
  initUpload();
  initPostGalleries();
  initStories();
});
