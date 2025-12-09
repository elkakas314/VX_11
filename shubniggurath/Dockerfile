FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements_minimal.txt .
RUN pip install --no-cache-dir -r requirements_minimal.txt
RUN apt-get clean && rm -rf /var/lib/apt/lists/* && find /usr/local -type d -name "__pycache__" -exec rm -rf {} +

# Copy source
COPY config config/
COPY shubniggurath shubniggurath/

# Create required dirs
RUN mkdir -p /app/logs /app/data /app/models /app/sandbox

# MODULE DISABLED IN VX11 v6.4 — DO NOT START
ENV ULTRA_LOW_MEMORY=true
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "uvicorn", "shubniggurath.main:app", "--host", "0.0.0.0", "--port", "8007"]
