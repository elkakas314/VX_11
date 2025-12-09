FROM python:3.10-slim

WORKDIR /app
ENV BASE_PATH=/app

RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*

COPY requirements_minimal.txt .
RUN pip install --no-cache-dir -r requirements_minimal.txt
RUN apt-get clean && rm -rf /var/lib/apt/lists/* && find /usr/local -type d -name "__pycache__" -exec rm -rf {} +

COPY . /app

RUN mkdir -p /app/logs /app/data /app/models /app/sandbox

# MODULE DISABLED IN VX11 v6.4 — DO NOT START
ENV ULTRA_LOW_MEMORY=true
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "uvicorn", "manifestator.main:app", "--host", "0.0.0.0", "--port", "8005"]
