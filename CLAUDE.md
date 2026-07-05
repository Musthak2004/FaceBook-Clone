# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run development server
python manage.py runserver

# Run all tests
python manage.py test

# Run tests for a specific app
python manage.py test accounts
python manage.py test posts
python manage.py test friendships

# Run a single test class or method
python manage.py test friendships.tests.FriendshipTestCase
python manage.py test friendships.tests.FriendshipTestCase.test_are_friends

# Apply migrations
python manage.py migrate

# Create new migrations
python manage.py makemigrations

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Activate virtual environment (Windows)
.venv\Scripts\activate

# Activate virtual environment (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create a new Django app
python manage.py startapp <app_name>
```

## Architecture

### Overview

A Django 4.2 LTS social network (Facebook clone) with vanilla frontend. Uses SQLite for development (MySQL ready for production).

### Apps (9 local apps)

All apps under `social_network/`:

| App | Model(s) | Purpose |
|-----|----------|---------|
| `accounts` | `CustomUser` (extends AbstractUser) | User auth, profiles, settings |
| `core` | — | Homepage feed, context processors |
| `posts` | `Post`, `PostImage`, `SavedPost` | Post CRUD, image uploads, visibility |
| `comments` | `Comment` (self-referential via `parent` for replies) | Comment/reply system |
| `reactions` | `Reaction` | Like/unlike with 7 reaction types |
| `friendships` | `Friendship` | Friend requests, accept/reject/block |
| `notifications` | `Notification` | Notification system driven by signals |
| `messaging` | `Conversation`, `Message` | Private 1-on-1 messaging |
| `search` | — | User + post search |
| `dashboard` | `Report` | Admin dashboard (staff-only) |

### Custom User Model

`accounts.CustomUser` extends `AbstractUser` with: profile_picture, cover_photo, bio, date_of_birth, education, work, location, website, is_private, friends (M2M through Friendship). Set as `AUTH_USER_MODEL` in settings.

### Friendship Model

Unidirectional with `from_user` / `to_user` fields and status (`pending` / `accepted` / `rejected` / `blocked`). Friendship is established when two reciprocal status=accepted records exist. Helper classmethods: `are_friends()`, `get_friends()`, `get_mutual_friends()`, `friend_status()`.

### Notifications

Driven by Django signals (`notifications/signals.py`) on `post_save` for Friendship, Reaction, and Comment. Types: friend_request, friend_accept, like, comment, reply. Global context processor `social_network.context_processors.notification_count` provides `unread_notifications_count` to all templates.

### Messaging

1-on-1 conversations only. Messages polled via JS (3-second interval). No WebSocket — uses AJAX polling pattern.

### Frontend

- **Templates**: Django template language, all extend `templates/base.html`
- **CSS**: Vanilla CSS with CSS custom properties (design token system in `static/css/base.css` vars): 11 CSS files total (base, components, auth, feed, profile, messaging, notifications, search, dashboard, responsive)
- **JS**: Vanilla JS (no framework). `main.js` (dropdowns, modals, notification polling), `feed.js` (like/save/comment AJAX, infinite scroll, post modal), `messaging.js` (chat polling, send)
- Infinite scroll via IntersectionObserver on `.infinite-scroll-sentinel`
- CSRF token read from cookie via `getCookie('csrftoken')` utility

### URL Structure

| Prefix | App |
|--------|-----|
| `/` | core (home feed) |
| `/accounts/` | Auth + accounts |
| `/posts/` | posts |
| `/comments/` | comments |
| `/reactions/` | reactions |
| `/friends/` | friendships |
| `/notifications/` | notifications |
| `/messages/` | messaging |
| `/search/` | search |
| `/dashboard/` | dashboard (staff-only) |
| `/admin/` | Django admin |

### Key Patterns

- **Views**: CBVs (Class-Based Views) throughout — CreateView, DetailView, UpdateView, DeleteView, ListView, TemplateView, and plain View for AJAX endpoints
- **Auth mixins**: `LoginRequiredMixin` on authenticated views; `UserPassesTestMixin` for ownership checks (post author, comment author); custom `StaffRequiredMixin` for dashboard
- **AJAX endpoints**: Return `JsonResponse`. Used for like/unlike, save/unsave, comment CRUD, friend requests, messaging
- **Post visibility**: Three tiers — public, friends, friends-only, only_me. Feed filters posts based on friendship status
- **Pagination**: Built-in Django `ListView` pagination (`paginate_by`), enhanced with infinite scroll on feed

### Settings

Configuration via `python-decouple` (.env file):
- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `TIME_ZONE`, `EMAIL_*`
- Default email backend: console (prints to terminal)
- `EMAIL_BACKEND= django.core.mail.backends.smtp.EmailBackend` for production with Gmail SMTP

### Gaps / Notes

- Tests exist only as stubs (`accounts/tests.py`, `posts/tests.py`, etc. — minimal content)
- No WebSockets (messaging and notifications use polling)
- No REST API framework
- No CI/CD configuration
- `.venv` in project root (already set up)
- `media/` directory for user uploads (not tracked in git)
