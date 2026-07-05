# ============================================================
# Dockerfile — Production build for SocialNet
# Uses Daphne ASGI server for Channels/WebSocket support
# ============================================================
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=social_network.settings \
    PYTHONPATH=/app

WORKDIR /app

# Install system deps needed for psycopg2 & Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev libjpeg-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create media & static directories
RUN mkdir -p /app/media /app/staticfiles

# Collect static files (safe even without a DB in production-like env)
RUN python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
