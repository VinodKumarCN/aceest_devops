# ---------- Build stage ----------
FROM python:3.11-slim AS base

# Keep Python output unbuffered so logs appear immediately in Docker
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies in a separate layer so Docker can cache them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Application stage ----------
COPY . .

# Initialise the SQLite database on startup via the app's own init_db()
# The app calls init_db() when __main__ runs, so no extra step is needed.

EXPOSE 5000

# Run as a non-root user for better security
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

CMD ["python", "app.py"]
