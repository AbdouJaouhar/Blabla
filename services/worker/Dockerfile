FROM python:3.11-slim

# System deps (optional: psycopg2 needs them)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (cached layers)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker code
COPY app/worker .

# Default command (Celery worker)
CMD ["celery", "-A", "worker_app.celery", "worker", "--loglevel=INFO"]
