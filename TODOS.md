# TODOS — Deferred work for Facebook Clone

## Deployment (P2, ~3-5h CC)
- [ ] Deploy to production (live URL) — post-feature-complete effort
- [ ] Set up real SMTP email provider (SendGrid, Mailgun, etc.)
- [ ] Docker Compose + PostgreSQL migration for production
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Write README with demo credentials and architecture
- [ ] Configure real Redis for Channels layer (switch from InMemoryChannelLayer)
- [ ] Set up Sentry error monitoring

## Feature enhancements (P3)
- [ ] Google Maps embed on event location pages
- [ ] Event reminders (via notification system)
- [ ] Event start/end range (currently start-time only baseline)
- [ ] Private groups with join requests and moderation roles
- [ ] Group invites feature
- [ ] Calendar export (.ics) for events
- [ ] Story reactions (quick emoji)
- [ ] Story view tracking (who viewed each story)
- [ ] User blocking / muting (trust & safety phase)
- [ ] Server-side rate limiting for typing indicators (currently client-side only)

## Notification target rendering contract (P3)
- [ ] Notification list template needs dispatch logic per GFK target type (Post → post link, Comment → comment link/context, Friendship → profile link). New notification target types require template updates to render correctly.
- [ ] Notification mention preferences (duplicate `email_mentions` / `push_mentions` fields)

## Design system & 3D UI (P1)
- [x] Run /design-consultation — established DESIGN.md with "The Archive" direction (warm charcoal + brass, Satoshi/Instrument Serif/JetBrains Mono, 4px spacing scale, shadow system, z-depth presets)
- [ ] T1: Extract shared post-card include template from home.html and post_list.html (DRY)
- [ ] T2: CSS foundation — .no-js gating, transition defaults, will-change, @supports guards
- [ ] T3: Add VanillaTilt.js v1.8.0 vendor library to static/vendor/
- [ ] T4: Create depth.css — card tilt, glass navbar, avatar translateZ, parallax, dark mode
- [ ] T5: Create feed-3d.js — VanillaTilt init, MutationObserver, IntersectionObserver, touch/Safari detection
- [ ] T6: Blue-tinted glass navbar — backdrop-filter: blur(12px), rgba(24,119,242,0.75)
- [ ] T7: Safari CSS-only fallback (no VanillaTilt JS on Safari)
- [ ] T8: AJAX load-more JSON endpoint (GET /api/posts/?offset=N) + full states (loading, error, exhausted)
- [ ] T9: Avatar placeholder initials with translateZ(20px)
- [ ] T10: Keyboard tilt (:focus-within + :focus-visible outline)
- [ ] T11: Touch device CSS float animation + 44px tap targets
- [ ] T12: Typography integration — Satoshi via Fontshare, Instrument Serif + JetBrains Mono via Google Fonts
- [ ] T13: Login page depth — glass form card, logo translateZ
- [ ] T14: Overlay z-stack — modals/dropdowns outside perspective container
- [ ] T15: Performance test — 60fps scroll, backdrop-filter <5% frame drops, FPS meter check

## Architecture hardening (P3)
- [ ] Move file cleanup from `post_delete` signals to storage-aware handler for remote storage (S3)
- [ ] Add story expiry scheduler cron job for production
- [ ] Notification mention preferences (duplicate `email_mentions` / `push_mentions` fields)
- [ ] Structured logging / metrics
- [ ] Input validation (file types, sizes, MIME checks) for all upload endpoints
