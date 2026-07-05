# SocialNet — Facebook Clone

A full-featured social networking platform built with **Django 4.2 LTS**, inspired by Facebook. Features real-time messaging via WebSockets, user profiles with online status, posts with reactions/comments/shares, friend system with mutual connections, groups, events, 24-hour stories, business/organization pages, polling, saved collections, trending hashtags, a REST API, dark mode, and an admin dashboard.

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11, Django 4.2 LTS, Django REST Framework |
| **Database** | SQLite (development), PostgreSQL (production) |
| **Real-time** | Django Channels + WebSocket (Redis channel layer) |
| **Frontend** | Vanilla HTML, CSS (custom properties design system), JavaScript (ES modules) |
| **Templates** | Django Template Language with partials/inclusion |
| **CI/CD** | GitHub Actions (automated test suite on push/PR) |
| **Infrastructure** | Docker Compose (web + PostgreSQL + Redis), Daphne ASGI server |
| **File Storage** | Local filesystem (dev) / AWS S3 (production) |
| **Email** | SMTP (Gmail) / SendGrid |

## Features

### Core Social Features
- **User Profiles** — Custom avatars, cover photos, bio, education, work, location, privacy controls
- **Posts** — Rich text with #hashtags and @mentions, image uploads, visibility tiers (public / friends only / only me)
- **Reactions** — 7 reaction types (like, love, care, haha, wow, sad, angry)
- **Comments & Replies** — Nested threading on posts
- **Friend System** — Send, accept, reject, and block friend requests; mutual friends tracking
- **Feed** — Paginated home feed with infinite scroll, filtered by friendship status
- **Online Status** — Real-time online/offline indicators via heartbeat middleware

### Real-time Communication
- **WebSocket Messaging** — Direct messages over Django Channels with conversation-based groups
- **WebSocket Notifications** — Live push notifications for likes, comments, friend requests, shares
- **Fallback Polling** — Automatic 3-second AJAX polling fallback if WebSocket disconnects

### Community Features
- **Groups** — Create and join communities; role-based (admin/member); group-specific posts
- **Events** — Create events with date/location; RSVP with going/maybe/not-going status
- **Pages** — Business, organization, and public figure pages; users follow, admins post updates
- **Stories** — 24-hour disappearing photo stories with full-screen viewer

### Content & Discovery
- **Hashtags** — Automatic `#hashtag` parsing with dedicated trending page
- **Saved Collections** — Bookmark posts into named collections for later reference
- **Post Polls** — Create polls within posts; real-time percentage results after voting
- **Share** — Repost to timeline with optional commentary; share to Twitter, Facebook, LinkedIn, WhatsApp, email
- **Search** — Global search across users and posts
- **Trending** — Trending hashtags page

### Moderation & Safety
- **User Blocking** — Block users to prevent interaction
- **Content Reporting** — Report posts with reason categories (spam, harassment, hate speech, etc.)
- **Admin Dashboard** — Staff dashboard with stats, user management, post moderation, report handling

### Platform Features
- **Dark Mode** — CSS custom property toggling with `localStorage` persistence
- **Email Verification** — Signed token-based email verification on signup
- **Password Reset** — Email-based password reset flow
- **Accessibility** — ARIA roles/labels, skip-to-content link, semantic HTML, screen reader support
- **Notification Preferences** — Per-type toggle to control which notifications you receive
- **Loading States** — Skeleton screens with shimmer animation, button loading spinners, image fade-in

### API
- **REST API** — Django REST Framework with ModelViewSets for posts, comments, users, messages, groups, events
- **Authentication** — Session-based + Basic auth for API
- **Pagination** — 20 items per page

## Architecture

```
social_network/
├── accounts/         # Custom user model, profiles, auth, email verification
├── api/              # REST API serializers and viewsets
├── comments/         # Comment & reply system (self-referential FK)
├── core/             # Homepage feed, context processors
├── dashboard/        # Staff-only admin dashboard
├── events/           # Events with RSVP
├── friendships/      # Friend requests, accept/reject/block, mutual friends
├── groups/           # Community groups with role-based membership
├── messaging/        # Private chat with WebSocket + polling fallback
├── notifications/    # Signal-driven notifications, preferences, WebSocket push
├── pages/            # Business/organization pages with follow system
├── posts/            # Post CRUD, images, polls, hashtags, mentions, saved collections
├── reactions/        # 7-type reaction system
├── reports/          # Content moderation and reporting
├── search/           # Global user and post search
├── stories/          # 24-hour disappearing stories
├── static/           # CSS (11 files), JS (ES modules), images
└── templates/        # 60+ Django templates extending base.html
```

### Data Model (18 models across 14 apps)

| Model | App | Purpose |
|-------|-----|---------|
| `CustomUser` | accounts | Extended user with profile, online status, friends M2M |
| `Post`, `PostImage`, `Tag` | posts | Content posts, images, hashtag taxonomy |
| `Poll`, `PollOption`, `PollVote` | posts | Inline polls with percentage voting |
| `SavedCollection`, `SavedPost` | posts | Named bookmark collections |
| `Comment` | comments | Threaded comments (self-referential parent FK) |
| `Reaction` | reactions | Unique (user, post) reactions with 7 types |
| `Friendship` | friendships | Unidirectional with pending/accepted/blocked status |
| `Notification`, `NotificationPreference` | notifications | Signal-driven notifications with per-type toggles |
| `Conversation`, `Message` | messaging | 1-on-1 chat with read status |
| `Group`, `GroupMembership`, `GroupPost` | groups | Community groups with admin/member roles |
| `Event`, `Attendee` | events | Events with RSVP (going/maybe/not-going) |
| `Story` | stories | 24-hour auto-expiring stories |
| `Page`, `PageFollower`, `PagePost` | pages | Business/public figure pages |
| `Report` | reports | Generic content reporting |

### URL Structure

| Prefix | App | Purpose |
|--------|-----|---------|
| `/` | core | Home feed |
| `/accounts/` | accounts + auth | Login, signup, profile, password reset |
| `/posts/` | posts | Post CRUD, hashtags, polls, saves, shares |
| `/comments/` | comments | Comment CRUD |
| `/reactions/` | reactions | Like/unlike AJAX |
| `/friends/` | friendships | Friend requests, list |
| `/notifications/` | notifications | Notification list, preferences |
| `/messages/` | messaging | Private conversations |
| `/search/` | search | User + post search |
| `/groups/` | groups | Community groups |
| `/events/` | events | Events with RSVP |
| `/stories/` | stories | 24-hour stories |
| `/pages/` | pages | Business/organization pages |
| `/reports/` | reports | Content reporting |
| `/dashboard/` | dashboard | Staff admin panel |
| `/api/` | api | REST API endpoints |
| `/admin/` | Django admin | Admin interface |

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Setup

```bash
# Clone the repository
git clone <repo-url> && cd FaceBook-Clone

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate       # Linux/Mac
.venv\Scripts\activate          # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create a superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

Visit **http://127.0.0.1:8000** in your browser.

### Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `SECRET_KEY` | `django-insecure-...` | ✓ | Django secret key (change in production) |
| `DEBUG` | `False` | | Set to `True` for development |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | | Comma-separated allowed hosts |
| `DATABASE_URL` | `sqlite:///...` | | PostgreSQL URL for production |
| `REDIS_URL` | `redis://...` | | Redis URL for Channels layer |
| `EMAIL_HOST` | `smtp.gmail.com` | | SMTP server |
| `EMAIL_PORT` | `587` | | SMTP port |
| `EMAIL_HOST_USER` | | | SMTP username |
| `EMAIL_HOST_PASSWORD` | | | SMTP app password |
| `DEFAULT_FROM_EMAIL` | `noreply@socialnet.local` | | From address for emails |

## Running Tests

```bash
# Run all tests
python manage.py test

# Run tests for a specific app
python manage.py test accounts
python manage.py test posts
python manage.py test friendships

# Run a single test class
python manage.py test friendships.tests.FriendshipTestCase
```

The test suite runs automatically via **GitHub Actions** on every push or PR to `main`.

## Production Deployment with Docker

The project includes a complete Docker Compose stack for production.

```bash
# Set environment variables
cp .env.example .env
# Edit .env with your production values

# Build and start all services
docker compose up -d

# Create superuser
docker compose exec web python manage.py createsuperuser
```

The stack launches:
- **web** — Daphne ASGI server on port 8000
- **db** — PostgreSQL 16
- **redis** — Redis 7 (channels layer)

Media files and static files persist in Docker volumes.

### Production Configuration

For cloud deployment:

- **Static files**: Served via WhiteNoise or AWS S3 (`django-storages` + `boto3`)
- **Media files**: Stored on AWS S3 when `AWS_ACCESS_KEY_ID` is set
- **ASGI Server**: Daphne handles both HTTP and WebSocket traffic
- **Database**: PostgreSQL via `DATABASE_URL` environment variable

## Project Commands

```bash
python manage.py runserver          # Development server
python manage.py test               # Run all tests
python manage.py migrate            # Apply migrations
python manage.py makemigrations     # Create new migrations
python manage.py createsuperuser    # Create admin user
python manage.py collectstatic      # Collect static files
python manage.py shell              # Django shell
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `Django>=4.2,<5.0` | Web framework (LTS) |
| `djangorestframework>=3.14` | REST API |
| `channels>=4.0` | WebSocket support |
| `daphne>=4.0` | ASGI server |
| `channels_redis>=4.1` | Redis channel layer |
| `Pillow>=10.0` | Image processing |
| `dj-database-url>=2.0` | Database URL parsing |
| `python-decouple>=3.8` | Environment variable management |
| `django-ratelimit>=4.1` | Rate limiting |
| `django-debug-toolbar>=4.4` | Debug toolbar |
| `psycopg2-binary>=2.9` | PostgreSQL adapter |
| `django-storages[boto3]>=1.14` | AWS S3 storage |
| `sendgrid>=6.11` | Email delivery |
| `gunicorn>=22.0` | WSGI server |

## License

MIT

---

Built with Django 4.2 LTS following patterns from *"Django for Beginners"* by William S. Vincent.
