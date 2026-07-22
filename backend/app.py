"""Flask application entrypoint for the SafeHome MVP backend."""

import json
import logging
from logging.config import dictConfig
import os
import re
import time
import uuid

from flask import Flask, g, jsonify, request
from flask.json.provider import DefaultJSONProvider
from werkzeug.exceptions import HTTPException

from config import Config
from database import check_database_health, get_connection, init_db
from routes.admin import bp as admin_bp
from routes.ai_qa import bp as ai_qa_bp
from routes.assessments import bp as assessments_bp
from routes.auth import bp as auth_bp
from routes.cards import bp as cards_bp
from routes.checkins import bp as checkins_bp
from routes.consent import bp as consent_bp
from routes.content_review import bp as content_review_bp
from routes.courses import bp as courses_bp
from routes.diaries import bp as diaries_bp
from routes.emotion_thermometer import bp as emotion_thermometer_bp
from routes.feedback import bp as feedback_bp
from routes.feedback_ledger import bp as feedback_ledger_bp
from routes.family import bp as family_bp
from routes.general_growth import bp as general_growth_bp
from routes.goals import bp as goals_bp
from routes.journey import bp as journey_bp
from routes.messages import bp as messages_bp
from routes.notifications import bp as notifications_bp
from routes.offline_benchmarks import bp as offline_benchmarks_bp
from routes.research_methodology import bp as research_methodology_bp
from routes.reliability import bp as reliability_bp
from routes.ux_governance import bp as ux_governance_bp
from routes.operations_governance import bp as operations_governance_bp
from routes.security_controls import bp as security_controls_bp
from routes.parent_assessments import bp as parent_assessments_bp
from routes.privacy import bp as privacy_bp
from routes.product_events import bp as product_events_bp
from routes.profile import bp as profile_bp
from routes.progress_summary import bp as progress_summary_bp
from routes.risk_review import bp as risk_review_bp
from routes.programs import bp as programs_bp
from routes.reports import bp as reports_bp
from routes.showcase_access import bp as showcase_access_bp
from routes.relationship_pilot_routes import bp as relationship_pilot_bp
from routes.research_workspace import bp as research_workspace_bp
from routes.supervision import bp as supervision_bp
from routes.text_analysis import bp as text_analysis_bp
from routes.training_plan import bp as training_plan_bp
from services.runtime_metrics import record_response, snapshot as runtime_metrics_snapshot
from services.reliability_service import record_request_event
from routes.auth_utils import AuthError, get_current_actor
from services.assessment_profile_service import model_artifact_hash_is_valid


SERVICE_VERSION = os.environ.get("SERVICE_VERSION", "safehome-2026-07-10-task12-login").strip() or "safehome-2026-07-10-task12-login"
REQUIRED_CONTENT_FILES = [
    "training_cards.json",
    "feedback_rules.json",
    "risk_keywords.json",
    "programs.json",
    "courses.json",
    "showcase_access.json",
    "privacy_retention_policy.json",
    "content_governance_manifest.json",
    "ai_qa_governance.json",
    "ai_qa_safety_responses.json",
    "ai_qa_synthetic_safety_suite.json",
    "offline_benchmark_registry.json",
    "offline_benchmark_label_mapping.json",
    "offline_benchmark_annotation_manual.json",
    "synthetic_affect_benchmark_240.json",
    "research_methodology_registry.json",
    "security_privacy_abuse_registry.json",
    "reliability_release_registry.json",
    "ux_experience_registry.json",
    "operations_capability_registry.json",
    "operations_asset_cards.json",
    "operations_knowledge_index.json",
    "operations_release_manifest.json",
    "readfeedback/student_profile_model.json",
]
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{8,64}$")
LEGACY_LIMIT_PATHS = {"/api/assessment-results", "/api/checkins", "/api/messages"}


class SafeHomeJSONProvider(DefaultJSONProvider):
    ensure_ascii = False

    def dumps(self, obj, **kwargs) -> str:
        kwargs.setdefault("default", self.default)
        kwargs.setdefault("ensure_ascii", self.ensure_ascii)
        kwargs.setdefault("sort_keys", self.sort_keys)
        return json.dumps(obj, **kwargs)


def check_content_health(content_dir) -> dict:
    missing_files = [filename for filename in REQUIRED_CONTENT_FILES if not (content_dir / filename).exists()]
    versions = {}
    for filename in ["assessment_worksheets.json", "scales_catalog.json", "training_cards.json"]:
        path = content_dir / filename
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            versions[filename] = payload.get("version") or payload.get("updated_at") or "unknown"
        except (OSError, json.JSONDecodeError):
            versions[filename] = "unreadable"
    model_versions = {}
    invalid_profile_artifacts = []
    ungoverned_profile_models = []
    profiles_dir = content_dir / "profiles"
    if profiles_dir.exists():
        for path in profiles_dir.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                if path.name.startswith("task12_"):
                    model_versions[path.stem] = payload.get("model_version") or payload.get("version") or payload.get("model_id") or "unknown"
                if payload.get("admission_status") not in {"internal_only", "pilot_approved", "production_approved", "deprecated"}:
                    ungoverned_profile_models.append(path.name)
                if not model_artifact_hash_is_valid(payload):
                    invalid_profile_artifacts.append(path.name)
            except (OSError, json.JSONDecodeError):
                if path.name.startswith("task12_"):
                    model_versions[path.stem] = "unreadable"
                invalid_profile_artifacts.append(path.name)
    models_ok = not invalid_profile_artifacts and not ungoverned_profile_models
    return {
        "ok": not missing_files and models_ok,
        "required_files_ok": not missing_files,
        "missing_files": missing_files,
        "content_versions": versions,
        "relationship_profile_model_versions": model_versions,
        "profile_models_ok": models_ok,
        "invalid_profile_artifacts": sorted(set(invalid_profile_artifacts)),
        "ungoverned_profile_models": sorted(set(ungoverned_profile_models)),
    }


def operational_backlog() -> dict:
    try:
        with get_connection() as conn:
            pending = conn.execute("SELECT COUNT(*) AS count FROM risk_review_records WHERE review_status IN ('pending', 'priority_review')").fetchone()
            high_priority = conn.execute("SELECT COUNT(*) AS count FROM risk_review_records WHERE review_status IN ('pending', 'priority_review') AND risk_level = 'high'").fetchone()
        return {"ok": True, "risk_review_pending": int(pending["count"]), "risk_review_high_priority": int(high_priority["count"])}
    except Exception:
        return {"ok": False, "risk_review_pending": None, "risk_review_high_priority": None}


def apply_config_overrides(config_class: type[Config], config_overrides: dict | None) -> None:
    if not config_overrides:
        return
    for key, value in config_overrides.items():
        if hasattr(config_class, key):
            setattr(config_class, key, value)


def configure_logging(app: Flask) -> None:
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        }
    }
    root_handlers = ["console"]
    log_file = os.environ.get("LOG_FILE", "").strip()
    if log_file:
        handlers["file"] = {
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": log_file,
            "encoding": "utf-8",
        }
        root_handlers.append("file")

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": LOG_FORMAT,
                }
            },
            "handlers": handlers,
            "root": {
                "level": level,
                "handlers": root_handlers,
            },
        }
    )
    app.logger.setLevel(level)


def create_app(
    config_class: type[Config] = Config,
    config_overrides: dict | None = None,
    init_database: bool = True,
) -> Flask:
    apply_config_overrides(config_class, config_overrides)
    config_class.validate()
    app = Flask(__name__)
    app.json = SafeHomeJSONProvider(app)
    app.config.from_object(config_class)
    if config_overrides:
        app.config.update(config_overrides)
    app.config.pop("JSON_AS_ASCII", None)
    configure_logging(app)
    if init_database:
        init_db()

    app.register_blueprint(auth_bp)
    app.register_blueprint(ai_qa_bp)
    app.register_blueprint(goals_bp)
    app.register_blueprint(journey_bp)
    app.register_blueprint(diaries_bp)
    app.register_blueprint(emotion_thermometer_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(feedback_ledger_bp)
    app.register_blueprint(family_bp)
    app.register_blueprint(general_growth_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(offline_benchmarks_bp)
    app.register_blueprint(research_methodology_bp)
    app.register_blueprint(reliability_bp)
    app.register_blueprint(ux_governance_bp)
    app.register_blueprint(operations_governance_bp)
    app.register_blueprint(security_controls_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(progress_summary_bp)
    app.register_blueprint(parent_assessments_bp)
    app.register_blueprint(assessments_bp)
    app.register_blueprint(cards_bp)
    app.register_blueprint(checkins_bp)
    app.register_blueprint(consent_bp)
    app.register_blueprint(content_review_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(privacy_bp)
    app.register_blueprint(product_events_bp)
    app.register_blueprint(risk_review_bp)
    app.register_blueprint(programs_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(showcase_access_bp)
    app.register_blueprint(relationship_pilot_bp)
    app.register_blueprint(research_workspace_bp)
    app.register_blueprint(supervision_bp)
    app.register_blueprint(text_analysis_bp)
    app.register_blueprint(training_plan_bp)
    app.register_blueprint(admin_bp)

    @app.before_request
    def begin_request_trace():
        incoming = str(request.headers.get("X-Request-ID") or "").strip()
        g.request_id = incoming if REQUEST_ID_PATTERN.fullmatch(incoming) else uuid.uuid4().hex
        g.request_started_at = time.perf_counter()

    @app.after_request
    def add_cors_headers(response):
        record_response(response.status_code)
        request_id = getattr(g, "request_id", uuid.uuid4().hex)
        duration_ms = round((time.perf_counter() - getattr(g, "request_started_at", time.perf_counter())) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        app.logger.info(
            "request_completed request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )
        actor_scope = "anonymous"
        try:
            actor = get_current_actor(allow_legacy_admin=True)
            actor_scope = str(actor.get("role") or "anonymous") if actor else "anonymous"
        except AuthError:
            pass
        error_code = None
        body = response.get_json(silent=True)
        if isinstance(body, dict) and isinstance(body.get("error"), dict):
            error_code = str(body["error"].get("code") or "") or None
        try:
            retry_count = max(0, min(int(request.headers.get("X-Retry-Count") or 0), 100))
        except (TypeError, ValueError):
            retry_count = 0
        record_request_event(
            request_id=request_id,
            method=request.method,
            path=request.path,
            actor_scope=actor_scope,
            status_code=response.status_code,
            latency_ms=duration_ms,
            error_code=error_code,
            retry_count=retry_count,
            recovered=str(request.headers.get("X-Recovered") or "").lower() in {"1", "true", "yes"},
        )
        origin = request.headers.get("Origin")
        if origin in app.config.get("ALLOWED_ORIGINS", []):
            response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Admin-Token, Authorization, Idempotency-Key, X-Request-ID, X-Retry-Count, X-Recovered"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if request.path.startswith("/api/"):
            response.headers.setdefault("Cache-Control", "no-store")
        if request.method == "GET" and request.path in LEGACY_LIMIT_PATHS and "limit" in request.args:
            response.headers["Deprecation"] = "true"
            response.headers["Sunset"] = "Sat, 31 Oct 2026 00:00:00 GMT"
            # CloudBase/Gunicorn rejects the former repository-relative Link
            # header as an invalid HTTP header and turns an otherwise valid
            # 200 response into a gateway 502. Keep the standard lifecycle
            # headers and publish migration guidance in the API contract.
        return response

    @app.errorhandler(Exception)
    def handle_exception(error):
        if isinstance(error, HTTPException):
            status = error.code or 500
            code = "not_found" if status == 404 else "http_error"
            message = "没有找到对应接口。" if status == 404 else "请求暂时没有完成，请稍后再试。"
            app.logger.warning(
                "http_exception code=%s status=%s method=%s path=%s",
                code,
                status,
                request.method,
                request.path,
            )
            return jsonify({"ok": False, "error": {"code": code, "message": message}, "request_id": getattr(g, "request_id", None)}), status

        app.logger.exception("unhandled_exception method=%s path=%s", request.method, request.path)
        return jsonify({"ok": False, "error": {"code": "internal_error", "message": "服务暂时没有响应，请稍后再试。"}, "request_id": getattr(g, "request_id", None)}), 500

    @app.get("/healthz")
    def healthz():
        return jsonify(
            {
                "ok": True,
                "service": "safehome-backend",
                "env": app.config.get("APP_ENV"),
                "version": SERVICE_VERSION,
            }
        )

    @app.get("/healthz/deep")
    def deep_healthz():
        return jsonify(build_readiness_payload(app))

    @app.get("/readyz")
    def readyz():
        payload = build_readiness_payload(app)
        return jsonify(payload), 200 if payload["ok"] else 503

    return app


def build_readiness_payload(app: Flask) -> dict:
    database = check_database_health()
    content = check_content_health(app.config["CONTENT_DIR"])
    return {
        "ok": bool(database.get("ok") and content.get("ok")),
        "service": "safehome-backend",
        "env": app.config.get("APP_ENV"),
        "version": SERVICE_VERSION,
        "database": database,
        "content": content,
        "runtime_metrics": runtime_metrics_snapshot(),
        "operational_backlog": operational_backlog(),
    }


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5050"))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
