# ==== BUILD STAGE ====
FROM python:3.10-slim AS builder

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements_minimal.txt .
RUN pip install --user --no-cache-dir -r requirements_minimal.txt

# ==== RUNTIME STAGE ====
FROM python:3.10-slim

WORKDIR /app
ENV BASE_PATH=/app
ENV ULTRA_LOW_MEMORY=true
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* && \
    find /usr/local -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

COPY --from=builder /root/.local /root/.local

COPY config /app/config/
COPY operator /app/operator/
COPY sitecustomize.py /app/

RUN mkdir -p /app/logs /app/data/runtime

ENV PATH=/root/.local/bin:$PATH

CMD ["python", "/app/operator/backend/uvicorn_entry.py"]

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -fsS http://localhost:8011/health || exit 1
