# ── Stage 1: Build dependencies ──────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies for asyncpg and psycopg
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime image ──────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependency (libpq for asyncpg)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default: long polling mode
CMD ["python", "main.py"]
