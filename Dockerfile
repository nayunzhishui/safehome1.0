FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production
ENV CONTENT_DIR=/app/content
ENV DATABASE_PATH=/app/data/safehome.sqlite3

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY content /app/content
COPY shared /app/shared

RUN mkdir -p /app/data

WORKDIR /app/backend

CMD ["sh", "-c", "gunicorn -w ${WEB_CONCURRENCY:-2} -b 0.0.0.0:${PORT:-5050} app:app"]
