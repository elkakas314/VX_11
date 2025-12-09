FROM python:3.11-slim
WORKDIR /app
COPY operator/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY operator/backend backend/
EXPOSE 8011
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "uvicorn", "backend.main_simple:app", "--host", "0.0.0.0", "--port", "8011"]
