# ==== BUILD STAGE ====
FROM python:3.10-slim AS builder

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements_tentaculo.txt .
RUN pip install --user --no-cache-dir -r requirements_tentaculo.txt

# Optional: Install test dependencies if available
COPY requirements-test.txt .
RUN test -f requirements-test.txt && pip install --user --no-cache-dir -r requirements-test.txt || echo "Test requirements not found"

# ==== RUNTIME STAGE ====
FROM python:3.10-slim

WORKDIR /app
ENV BASE_PATH=/app
ENV ULTRA_LOW_MEMORY=true
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* && \
    find /usr/local -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Copy only Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy specific modules + minimal config (safer than copying entire tree)
COPY config/ /app/config/
COPY tentaculo_link/ /app/tentaculo_link/
COPY switch/ /app/switch/
COPY madre/ /app/madre/
COPY spawner/ /app/spawner/
COPY sitecustomize.py /app/
COPY py.typed /app/

# Create directories
RUN mkdir -p /app/logs /app/data /app/models /app/sandbox

# Add user local bin to PATH
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

CMD ["uvicorn", "tentaculo_link.main_v7:app", "--host", "0.0.0.0", "--port", "8000"]

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

