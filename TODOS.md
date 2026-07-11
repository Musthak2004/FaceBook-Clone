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

## Architecture hardening (P3)
- [ ] Move file cleanup from `post_delete` signals to storage-aware handler for remote storage (S3)
- [ ] Add story expiry scheduler cron job for production
- [ ] Notification mention preferences (duplicate `email_mentions` / `push_mentions` fields)
- [ ] Structured logging / metrics
- [ ] Input validation (file types, sizes, MIME checks) for all upload endpoints
