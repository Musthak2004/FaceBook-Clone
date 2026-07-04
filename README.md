# SocialNet — Facebook Clone

A full-stack social networking application built with Django 4.2 LTS, following the patterns from "Django for Beginners" by William S. Vincent.

## Tech Stack

- **Backend**: Python 3.10+, Django 4.2 LTS
- **Database**: SQLite (development), MySQL (production-ready configuration)
- **Frontend**: HTML, CSS (vanilla), JavaScript (vanilla)
- **Templates**: Django Template Language

## Features

- **Authentication**: Sign up, login, logout, password change/reset
- **User Profiles**: Custom profiles with pictures, bio, education, work
- **Posts**: Create, edit, delete with image uploads and visibility settings
- **Feed**: Paginated home feed showing friend posts
- **Reactions**: Like/unlike with multiple reaction types
- **Comments**: Comment and reply on posts
- **Friend System**: Send, accept, reject friend requests
- **Notifications**: Real-time notifications for likes, comments, friend requests
- **Messaging**: Private conversations with real-time polling
- **Search**: Search users and posts
- **Admin Dashboard**: Stats, user management, post moderation, report handling

## Project Structure

```
social_network/
├── accounts/       # Custom user model, auth, profiles
├── core/           # Homepage feed, context processors
├── posts/          # Post CRUD, feed, images
├── comments/       # Comments & replies
├── reactions/      # Like/unlike system
├── friendships/    # Friend requests & management
├── notifications/  # Notification system
├── messaging/      # Private chat
├── search/         # User & post search
├── dashboard/      # Admin dashboard
├── templates/      # Project-level templates
└── static/         # CSS, JS, images
```

## Quick Start

```bash
# Clone and enter directory
git clone <repo-url> && cd social_network

# Create virtual environment
python -m venv .venv && source .venv/bin/activate  # Linux/Mac
python -m venv .venv && .venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

## Environment Variables

Set in `.env` (see `.env` template):

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `django-insecure-...` | Django secret key |
| `DEBUG` | `True` | Debug mode |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost` | Allowed hosts |
| `EMAIL_BACKEND` | `console.EmailBackend` | Email backend |

## License

MIT
