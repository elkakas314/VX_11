# ==== BUILD STAGE ====
FROM python:3.10-slim AS builder

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements_minimal.txt .
RUN pip install --user --no-cache-dir -r requirements_minimal.txt

# ==== RUNTIME STAGE ====
FROM python:3.10-slim

WORKDIR /app
ENV ULTRA_LOW_MEMORY=true
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY config /app/config/
COPY shubniggurath /app/shubniggurath/
COPY sitecustomize.py /app/

RUN mkdir -p /app/logs /app/data /app/models /app/sandbox /app/data/runtime

CMD ["python", "-m", "uvicorn", "shubniggurath.main:app", "--host", "0.0.0.0", "--port", "8007"]

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -fsS http://localhost:8007/health || exit 1

