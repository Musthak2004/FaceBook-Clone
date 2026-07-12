// ─── FaceClone — 3D Feed Interactions ───
// Design system: "The Archive" (see DESIGN.md §5 — 3D Depth System)
// VanillaTilt card tilt, IntersectionObserver parallax, AJAX load-more,
// MutationObserver for dynamic content, Safari/touch detection.

(function() {
    'use strict';

    var FEED_SELECTOR     = '.news-feed';
    var CARD_SELECTOR     = '.post-card';
    var LOAD_MORE_BTN     = '#load-more-btn';
    var LOAD_MORE_URL     = '/posts/api/posts/';
    var LOAD_MORE_CONTAINER = '#load-more-container';

    // Toast dismiss duration in milliseconds
    var TOAST_DURATION = 4000;

    // VanillaTilt configuration matching the design spec
    var TILT_CONFIG = {
        max: 8,
        speed: 400,
        scale: 1.02,
        glare: true,
        'max-glare': 0.15,
        transition: true,
        easing: 'cubic-bezier(0.03, 0.98, 0.52, 0.99)',
    };

    // ─── Feature detection ───

    var isTouchDevice = function() {
        return 'ontouchstart' in window ||
            navigator.maxTouchPoints > 0;
    };

    var isSafari = function() {
        var ua = navigator.userAgent.toLowerCase();
        return ua.indexOf('safari') > -1 &&
               ua.indexOf('chrome') === -1 &&
               ua.indexOf('chromium') === -1;
    };

    var prefersReducedMotion = function() {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    };

    // Add .safari class to html so depth.css can apply fallback
    if (isSafari()) {
        document.documentElement.classList.add('safari');
    }

    // ─── VanillaTilt initialization ───

    function initTilt(container) {
        if (prefersReducedMotion()) return;
        if (isTouchDevice()) return; // CSS float animation instead
        if (isSafari()) return; // CSS-only subtle transform instead
        if (typeof VanillaTilt === 'undefined') return;

        var cards = container.querySelectorAll(CARD_SELECTOR);
        cards.forEach(function(card) {
            try {
                // Only init if not already initialized
                if (!card.hasAttribute('data-tilt')) {
                    VanillaTilt.init(card, TILT_CONFIG);
                }
            } catch (e) {
                // One bad card shouldn't break the rest
                console.warn('Tilt init failed for card', card.id, e);
            }
        });
    }

    // ─── IntersectionObserver parallax ───

    function initParallax(container) {
        if (prefersReducedMotion()) return;
        if (typeof IntersectionObserver === 'undefined') return;

        var cards = container.querySelectorAll(CARD_SELECTOR);
        if (!cards.length) return;

        var observer = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                var card = entry.target;
                if (entry.isIntersecting) {
                    // Vary depth based on how far the card is from viewport center
                    // Cards near the top get negative depth (-1), center gets 0, bottom gets positive
                    var rect = entry.boundingClientRect;
                    var viewportCenter = window.innerHeight / 2;
                    var cardCenter = rect.top + rect.height / 2;
                    var offset = (cardCenter - viewportCenter) / window.innerHeight;

                    // Map offset (-1 to 1) to depth (-1, 0, 1, 2, 3)
                    var depth = Math.round((offset + 1) * 2) - 1;
                    depth = Math.max(-1, Math.min(3, depth));
                    card.setAttribute('data-depth', depth);
                } else {
                    card.removeAttribute('data-depth');
                }
            });
        }, {
            threshold: [0, 0.25, 0.5, 0.75, 1.0],
            rootMargin: '50px 0px',
        });

        cards.forEach(function(card) {
            observer.observe(card);
        });
    }

    // ─── MutationObserver for dynamic content ───

    function observeFeed(container) {
        var feedContainer = container || document.querySelector(FEED_SELECTOR);
        if (!feedContainer) return;

        var observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) {
                        // Check if the new node is a card or contains cards
                        if (node.matches && node.matches(CARD_SELECTOR)) {
                            initTiltForNode(node);
                            observeParallaxForNode(node);
                        } else if (node.querySelectorAll) {
                            var nestedCards = node.querySelectorAll(CARD_SELECTOR);
                            nestedCards.forEach(function(card) {
                                initTiltForNode(card);
                                observeParallaxForNode(card);
                            });
                        }
                    }
                });
            });
        });

        observer.observe(feedContainer, {
            childList: true,
            subtree: true,
        });
    }

    // Wrappers for single-card init with try-catch
    function initTiltForNode(card) {
        try {
            if (prefersReducedMotion()) return;
            if (isTouchDevice()) return;
            if (isSafari()) return;
            if (typeof VanillaTilt !== 'undefined' && !card.hasAttribute('data-tilt')) {
                VanillaTilt.init(card, TILT_CONFIG);
            }
        } catch (e) {
            console.warn('Tilt init failed for dynamic card', card.id, e);
        }
    }

    function observeParallaxForNode(card) {
        if (typeof IntersectionObserver === 'undefined') return;
        try {
            if (prefersReducedMotion()) return;
            var observer = new IntersectionObserver(function(entries) {
                entries.forEach(function(entry) {
                    if (entry.isIntersecting) {
                        entry.target.setAttribute('data-depth', '1');
                    } else {
                        entry.target.removeAttribute('data-depth');
                    }
                });
            }, { threshold: 0.3 });
            observer.observe(card);
        } catch (e) {
            // silently skip
        }
    }

    // ─── AJAX Load-more ───

    function setupLoadMore() {
        var btn = document.querySelector(LOAD_MORE_BTN);
        if (!btn) return;

        var loading = false;
        var offset = 0;
        var url = btn.getAttribute('data-load-more-url') || LOAD_MORE_URL;

        btn.addEventListener('click', function() {
            if (loading) return;

            loading = true;
            btn.disabled = true;
            btn.innerHTML = '<span class="load-more-spinner"></span> Loading...';

            fetch(url + '?offset=' + offset, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
            .then(function(r) {
                if (!r.ok) throw new Error('Network response was ' + r.status);
                return r.json();
            })
            .then(function(data) {
                if (data.error) throw new Error(data.error);

                var feed = document.querySelector(FEED_SELECTOR);
                if (!feed) return;

                // Insert new cards
                if (data.html && data.html.length > 0) {
                    var temp = document.createElement('div');
                    temp.innerHTML = data.html;
                    var cards = temp.querySelectorAll(CARD_SELECTOR);
                    cards.forEach(function(card) {
                        feed.appendChild(card);
                    });

                    offset = data.next_offset || offset + cards.length;

                    // Hide button when no more posts
                    if (data.has_more === false || cards.length === 0) {
                        var container = document.querySelector(LOAD_MORE_CONTAINER);
                        if (container) container.classList.add('load-more-hidden');
                    }
                } else {
                    // No more posts
                    var container = document.querySelector(LOAD_MORE_CONTAINER);
                    if (container) container.classList.add('load-more-hidden');
                }

                btn.disabled = false;
                btn.innerHTML = 'View more posts';
                loading = false;
            })
            .catch(function(err) {
                btn.disabled = false;
                btn.innerHTML = 'View more posts';
                loading = false;

                // Show error toast
                showErrorToast('Could not load more posts. Check your connection.');
            });
        });
    }

    function showErrorToast(message) {
        var existing = document.querySelector('.toast-error');
        if (existing) existing.remove();

        var toast = document.createElement('div');
        toast.className = 'toast-error';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(function() {
            if (toast.parentNode) toast.parentNode.removeChild(toast);
        }, TOAST_DURATION);
    }

    // ─── Dark mode persistence ───

    function persistTheme(name) {
        try {
            localStorage.setItem('fc-theme', name);
        } catch (e) {
            // Safari private browsing throws — non-critical
        }
    }

    function setupThemeToggle() {
        var saved;
        try {
            saved = localStorage.getItem('fc-theme');
        } catch (e) {
            // Safari private browsing — read fails silently
        }

        if (saved === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else if (saved === 'light') {
            document.documentElement.setAttribute('data-theme', 'light');
        } else {
            // Respect OS preference
            if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
                document.documentElement.setAttribute('data-theme', 'dark');
                persistTheme('dark');
            }
        }

        // Listen for theme toggle clicks
        document.addEventListener('click', function(e) {
            var toggle = e.target.closest('[data-theme-toggle]');
            if (toggle) {
                var html = document.documentElement;
                var current = html.getAttribute('data-theme') || 'light';
                var next = current === 'dark' ? 'light' : 'dark';
                html.setAttribute('data-theme', next);
                persistTheme(next);
            }
        });
    }

    // ─── Init ───

    document.addEventListener('DOMContentLoaded', function() {
        setupThemeToggle();

        var feed = document.querySelector(FEED_SELECTOR);
        if (!feed) return;

        // Initial tilt + parallax for server-rendered cards
        initTilt(feed);
        initParallax(feed);

        // Observe for dynamic additions (AJAX load-more)
        observeFeed(feed);

        // AJAX load-more button handler
        setupLoadMore();
    });

})();
