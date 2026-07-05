#!/bin/bash
# ============================================================
# Entrypoint — Run migrations, then start Daphne ASGI server
# ============================================================
set -e

echo "→ Running migrations..."
python manage.py migrate --noinput

echo "→ Starting Daphne (ASGI) on port ${PORT:-8000}..."
exec daphne -b 0.0.0.0 -p "${PORT:-8000}" social_network.asgi:application
