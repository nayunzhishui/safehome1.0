FROM python:3.11-slim@sha256:1042b61448fef4ba92d16a8c7eb4996d027568ce64792a7877fd88511e0af7c6

WORKDIR /app

RUN apt-get -o Acquire::Retries=3 update \
    && apt-get -o Acquire::Retries=3 install --yes --no-install-recommends \
        libssl3t64=3.5.7-1~deb13u2 \
        openssl=3.5.7-1~deb13u2 \
        openssl-provider-legacy=3.5.7-1~deb13u2 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt \
    && pip uninstall --yes setuptools \
    && pip check

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production
ENV HOME=/app
ENV CONTENT_DIR=/app/content
ENV MAX_REQUEST_BODY_BYTES=1048576

# The production image is deliberately fail-closed. Database credentials,
# application secrets and approved production capabilities are injected only
# by the deployment platform at runtime.
ENV PRODUCTION_FEATURES_UNLOCKED=0 \
    CONTENT_GOVERNANCE_PUBLISH_ENABLED=0 \
    PRIVACY_EXECUTION_ENABLED=0 \
    PRIVACY_PRODUCTION_EXECUTION_ENABLED=0 \
    RESEARCH_OPERATIONS_WRITE_ENABLED=0 \
    AI_QA_ENABLED=0 \
    AI_QA_SANDBOX_ENABLED=0 \
    AI_QA_REAL_PROVIDER_ENABLED=0 \
    OFFLINE_EXTERNAL_INGEST_ENABLED=0 \
    OFFLINE_PRODUCTION_REPLACEMENT_ALLOWED=0 \
    RELIABILITY_FAULT_INJECTION_ENABLED=0 \
    OPERATIONS_PRODUCTION_RELEASE_ENABLED=0

COPY backend /app/backend
COPY content /app/content
COPY shared /app/shared
COPY config/rc0810/database_profiles.json /app/config/rc0810/database_profiles.json
COPY deploy/verify_rc0810_f03_images.py /app/verify_rc0810_f03_images.py

RUN addgroup --system safehome \
    && adduser --system --ingroup safehome safehome \
    && mkdir -p /app/data \
    && chown -R safehome:safehome /app/data

WORKDIR /app/backend

USER safehome

ENTRYPOINT ["python", "/app/verify_rc0810_f03_images.py", "--entrypoint", "--profile", "production", "--"]
CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]
