FROM mcr.microsoft.com/azurelinux/base/python:3.12@sha256:722b6224c23b3f21f5268e2073f80c0f396bc626e3193b6dbf66e40d89478f03 AS builder

WORKDIR /build

COPY backend/requirements.txt /build/requirements.txt
RUN python3 -m pip install --no-cache-dir --target /opt/python -r /build/requirements.txt \
    && PYTHONPATH=/opt/python python3 -m pip check \
    && find /opt/python -type d -name __pycache__ -prune -exec rm -rf {} + \
    && mkdir -p /runtime-data \
    && chown 65532:65532 /runtime-data

FROM mcr.microsoft.com/azurelinux/distroless/python:3.12-nonroot@sha256:d921452dba64944bf959f22450bb3740f5b2fff4a59faa64bd6b8eaf4c57b5b8

WORKDIR /app

COPY --from=builder /opt/python /opt/python

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production
ENV HOME=/app
ENV PATH=/opt/python/bin:/usr/bin
ENV PYTHONPATH=/opt/python
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
COPY --from=builder --chown=65532:65532 /runtime-data /app/data

WORKDIR /app/backend

USER nonroot

ENTRYPOINT ["/usr/bin/python3", "/app/verify_rc0810_f03_images.py", "--entrypoint", "--profile", "production", "--"]
CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]
