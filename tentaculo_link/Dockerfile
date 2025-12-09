FROM python:3.10-slim

WORKDIR /app
ENV BASE_PATH=/app

RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Dependencias mínimas para Tentáculo (sin IA pesada)
COPY requirements_tentaculo.txt .
RUN pip install --no-cache-dir -r requirements_tentaculo.txt
RUN apt-get clean && rm -rf /var/lib/apt/lists/* && find /usr/local -type d -name "__pycache__" -exec rm -rf {} +

COPY . /app

RUN mkdir -p /app/logs /app/data /app/models /app/sandbox
ENV ULTRA_LOW_MEMORY=true
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "uvicorn", "tentaculo_link.main_v7:app", "--host", "0.0.0.0", "--port", "8000"]

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

