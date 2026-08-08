FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production
ENV CONTENT_DIR=/app/content
ENV DATABASE_PATH=/app/data/safehome.sqlite3
ENV RAG_V2_ENABLED=1
ENV MAX_REQUEST_BODY_BYTES=1048576

# All implemented product/API surfaces are enabled for the explicitly requested
# CloudBase validation deployment. Authentication, capability checks and object
# scope remain enforced by the application. Destructive data ingestion, model
# replacement and production fault injection remain disabled.
ENV PRODUCTION_FEATURES_UNLOCKED=1 \
    CONTENT_GOVERNANCE_ENFORCED=1 \
    CONTENT_GOVERNANCE_PUBLISH_ENABLED=1 \
    PRIVACY_EXECUTION_ENABLED=1 \
    PRIVACY_RETENTION_POLICY_APPROVED=1 \
    PRIVACY_PRODUCTION_EXECUTION_ENABLED=1 \
    RESEARCH_OPERATIONS_WRITE_ENABLED=1 \
    THERAPEUTIC_ASSESSMENT_LIFECYCLE_ENABLED=1 \
    AI_QA_ENABLED=1 \
    AI_QA_SANDBOX_ENABLED=1 \
    AI_QA_PROVIDER=deepseek \
    AI_QA_REAL_PROVIDER_ENABLED=1 \
    OFFLINE_BENCHMARK_ENABLED=1 \
    RESEARCH_METHODOLOGY_WORKBENCH_ENABLED=1 \
    RESEARCH_METHODOLOGY_FORMAL_FREEZE_ALLOWED=1 \
    RESEARCH_OUTCOME_ANALYSIS_ALLOWED=1 \
    RESEARCH_ANALYSIS_JOB_EXECUTION_ENABLED=1 \
    SECURITY_SCAN_EXECUTION_ENABLED=1 \
    RELIABILITY_WORKBENCH_ENABLED=1 \
    RELIABILITY_JOB_EXECUTION_ENABLED=1 \
    RELIABILITY_GRADUAL_RELEASE_ENABLED=1 \
    RELIABILITY_PRODUCTION_SLO_FROZEN=1 \
    UX_GOVERNANCE_WORKBENCH_ENABLED=1 \
    OPERATIONS_GOVERNANCE_WORKBENCH_ENABLED=1 \
    OPERATIONS_LOCAL_RELEASE_ENABLED=1 \
    OPERATIONS_PRODUCTION_RELEASE_ENABLED=1 \
    OFFLINE_EXTERNAL_INGEST_ENABLED=0 \
    OFFLINE_PRODUCTION_REPLACEMENT_ALLOWED=0 \
    RELIABILITY_FAULT_INJECTION_ENABLED=0

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
