# =============================================================================
# UrbanFlow — API Gateway Dockerfile
# =============================================================================
# Multi-stage build keeps the final image lean:
#   builder — installs dependencies into a virtual environment
#   runtime — copies only the venv and app code, no build tools
# =============================================================================

# --- Stage 1: builder ---
FROM python:3.11-slim AS builder

WORKDIR /app

# Install dependencies into a venv so we can copy just the venv to runtime.
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


# --- Stage 2: runtime ---
FROM python:3.11-slim AS runtime

# Non-root user for security — never run application code as root.
RUN addgroup --system urbanflow && adduser --system --ingroup urbanflow urbanflow

WORKDIR /app

# Copy the pre-built venv from the builder stage.
COPY --from=builder /opt/venv /opt/venv

# Copy application source.
COPY app/ ./app/
COPY tests/ ./tests/


RUN chown -R urbanflow:urbanflow /app/tests


# Set the venv on PATH so python and uvicorn resolve from it.
ENV PATH="/opt/venv/bin:$PATH"

# Run as the non-root user.
USER urbanflow

EXPOSE 8000

# uvicorn with a single worker.
# For production on the VPS, increase --workers to match CPU core count.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]