# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile
# Traffic Intelligence Service — UrbanFlow
# ─────────────────────────────────────────────────────────────────────────────
# Build context: traffic-intelligence-service/
# WORKDIR inside container: /app
# model.pkl saves to: /app/ml_model/model.pkl
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# Prevents Python from writing .pyc files and buffers stdout/stderr
# so logs appear immediately in docker logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies needed by psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer caching — only reruns if requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app/ ./app/
COPY tests/ ./tests/

# Copy the seed script (run manually via docker exec, not at container start)
COPY datasets/seed_traffic_data.py ./datasets/seed_traffic_data.py

# Create the ml_model directory — model.pkl will be written here at runtime
RUN mkdir -p /app/ml_model

# Expose the port this service runs on
EXPOSE 8002

# Health check — Docker will hit this every 30s to confirm the service is alive
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health')"

# Start the service
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]