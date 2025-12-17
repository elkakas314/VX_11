# ==== BUILD STAGE ====
FROM python:3.11-slim AS builder

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY operator_backend/backend/requirements.txt ./requirements.txt
RUN pip install --user --no-cache-dir -r requirements.txt

# ==== RUNTIME STAGE ====
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV ULTRA_LOW_MEMORY=true

RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* && \
    find /usr/local -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Copy only Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy only necessary files
COPY config /app/config/
COPY operator_backend/backend /app/backend/

# Add user local bin to PATH
ENV PATH=/root/.local/bin:$PATH

EXPOSE 8011
CMD ["python", "-m", "uvicorn", "backend.main_v7:app", "--host", "0.0.0.0", "--port", "8011"]
