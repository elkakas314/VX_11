# ==== BUILD STAGE ====
FROM python:3.11-slim AS builder

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements_minimal.txt .
RUN pip install --user --no-cache-dir -r requirements_minimal.txt

# ==== RUNTIME STAGE ====
FROM python:3.11-slim

WORKDIR /app
ENV ULTRA_LOW_MEMORY=true
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* && \
    find /usr/local -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Copy only Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy only necessary files
COPY config /app/config/
COPY shubniggurath /app/shubniggurath/

# Create required dirs
RUN mkdir -p /app/logs /app/data /app/models /app/sandbox

# Add user local bin to PATH
ENV PATH=/root/.local/bin:$PATH

# MODULE DISABLED IN VX11 v6.4 — DO NOT START
CMD ["python", "-m", "uvicorn", "shubniggurath.main:app", "--host", "0.0.0.0", "--port", "8007"]
