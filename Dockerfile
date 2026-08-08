FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production
ENV CONTENT_DIR=/app/content
ENV DATABASE_PATH=/app/data/safehome.sqlite3
ENV RAG_V2_ENABLED=1
ENV MAX_REQUEST_BODY_BYTES=1048576

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt \
    && pip check

COPY backend /app/backend
COPY content /app/content
COPY shared /app/shared

RUN addgroup --system safehome \
    && adduser --system --ingroup safehome safehome \
    && mkdir -p /app/data \
    && chown -R safehome:safehome /app/data

WORKDIR /app/backend

USER safehome

CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]
