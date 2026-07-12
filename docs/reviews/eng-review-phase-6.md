# Engineering Review: Phase 6 — 3D Depth UI

**Reviewed:** 2026-07-12  
**Commits:** 3 commits ahead of origin/main (Phase 6 3D Depth UI implementation)  
**Diff:** 17 files, 1393 insertions, 205 deletions  
**Reviewer:** Claude Code via /review

---

## Review Checklist Results

### CRITICAL Categories

| Category | Verdict | Notes |
|---|---|---|
| SQL Safety | ✅ Clean | All ORM, no raw SQL, no string interpolation |
| Race Conditions | ✅ Clean | Load-more has `loading` flag guard; like toggle is idempotent |
| LLM Trust Boundary | ✅ Clean | Django template auto-escaping on all user content |
| Shell Injection | ✅ Clean | No subprocess or shell calls |
| Enum Completeness | ⚠️ 2 issues | Both auto-fixed (see below) |

### INFORMATIONAL Categories

| Category | Verdict | Notes |
|---|---|---|
| Async/Sync Mixing | ✅ Clean | All synchronous |
| Column/Field Safety | ✅ Clean | No schema changes |
| Dead Code | ✅ Clean | No dead code found |
| LLM Prompt Issues | ✅ Clean | No LLM prompts in diff |
| Completeness Gaps | ✅ Clean | All state transitions covered |
| Time Windows | ✅ Clean | No time-dependent logic |
| Type Coercion | ✅ Clean | Python types are consistent |
| View/Frontend | ✅ Clean | Progressive enhancement chain correct (`.no-js` → `@supports` → Safari → touch) |
| CI/CD | ⚠️ N/A | No CI changes needed |

---

## Findings (ranked)

### 1. N+1 Query in PostFeedAPIView (AUTO-FIXED)
**File:** `posts/views.py` / `posts/models.py` / `templates/includes/post_card.html`

`like_count`, `comment_count`, and `has_images` are `@property` methods that call `.count()` / `.exists()` — each issues a separate SQL query per post. With `BATCH_SIZE=10`, this added ~30 extra queries per load-more request despite `prefetch_related('likes')` (`.count()` ignores the prefetch cache).

**Fix applied:**
- Added `Count('likes')` and `Count('comments')` annotations to the API queryset
- Updated model properties to return annotated values when available (`hasattr`)
- Changed template from `{% if post.has_images %}` to `{% if post.images.all %}` (uses prefetch cache)
- Dropped unnecessary `prefetch_related('likes')` from the API view

**Impact:** Reduces queries per load-more from ~36 to ~8.

### 2. ValueError on Non-Numeric Offset (AUTO-FIXED)
**File:** `posts/views.py:122`

`int(request.GET.get("offset", 0))` raises `ValueError` → 500 error if a client sends `?offset=abc`.

**Fix applied:** Wrapped in try/except, returns `HttpResponseBadRequest` (400).

### 3. localStorage Throw in Safari Private Browsing (AUTO-FIXED)
**File:** `static/js/feed-3d.js:266,278`

`localStorage.setItem()` throws in Safari private browsing mode. Dark-mode theme persistence would fail silently, and an uncaught throw could break the click event handler.

**Fix applied:** Extracted `persistTheme()` helper wrapping `setItem` in try/catch. Wrapped `getItem` in try/catch as well.

### 4. Missing IntersectionObserver Feature Detection (AUTO-FIXED)
**File:** `static/js/feed-3d.js:79,157`

`new IntersectionObserver(...)` throws in browsers that don't support it (IE11, older Android WebView). Parallax is progressive enhancement — the rest of the JS should work without it.

**Fix applied:** Added `typeof IntersectionObserver === 'undefined'` guards in both `initParallax` and `observeParallaxForNode`.

### 5. TODOS.md Staleness — Marked P1 Complete (FIXED)
**File:** `TODOS.md`

All 15 Phase 6 P1 tasks (T1–T15) were fully implemented but listed as unchecked `[ ]`.

**Fix applied:** Marked all as `[x]` and updated section header to include "— COMPLETE".

### 6. Per-Card Observer Design Tradeoff (ASK — no change needed)
**File:** `static/js/feed-3d.js:154-169`

`observeParallaxForNode` creates one `IntersectionObserver` per dynamically loaded card (with fixed `data-depth="1"`), while `initParallax` uses a single observer for all initial cards (computing ranged -1 to 3 based on viewport position). This is a conscious tradeoff: dynamically loaded cards appear at the bottom of the scroll, so a constant depth of 1 is reasonable. Not a bug — worth noting for maintainers.

---

## Specialist Summary

| Specialist | Status |
|---|---|
| **Testing** (always-on) | ✅ 4 new API tests covering load-more states, plus all 188 suite tests pass |
| **Maintainability** (always-on) | ✅ Clean DRY extraction of `post_card.html` include from both `home.html` and `post_list.html` |
| **Performance** | ⚠️ N+1 query issue found and fixed; CSS `will-change` + `translateZ` properly scoped |

---

## Quality Score: **8.5/10**

Deducted points for N+1 query (preventable with annotation), missing error handling on user-facing input, and missing polyfill guard. All four mechanical issues from the review were auto-fixed. **QA found and fixed one additional issue:** the AJAX load-more URL pointed at `/api/posts/` instead of the actual route `/posts/api/posts/`, causing a 404 on "View more posts" clicks. No unaddressed CRITICAL findings remain.

**Post-review QA commit:** `c22cc29` — `fix: correct AJAX load-more URL`
