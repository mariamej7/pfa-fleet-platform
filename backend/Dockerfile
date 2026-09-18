FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYSPARK_PYTHON=python3 \
    PYTHONPATH=/app/backend

RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt

RUN pip install --default-timeout=300 --retries=10 --no-cache-dir -r /app/backend/requirements.txt

COPY backend/app /app/backend/app
COPY pipeline /app/pipeline

WORKDIR /app/backend

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]