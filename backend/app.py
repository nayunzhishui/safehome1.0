"""Flask application entrypoint for the SafeHome MVP backend."""

import json
import logging
from logging.config import dictConfig
import os

from flask import Flask, jsonify, request
from flask.json.provider import DefaultJSONProvider
from werkzeug.exceptions import HTTPException

from config import Config
from database import check_database_health, init_db
from routes.admin import bp as admin_bp
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
from routes.family import bp as family_bp
from routes.goals import bp as goals_bp
from routes.messages import bp as messages_bp
from routes.parent_assessments import bp as parent_assessments_bp
from routes.privacy import bp as privacy_bp
from routes.profile import bp as profile_bp
from routes.progress_summary import bp as progress_summary_bp
from routes.risk_review import bp as risk_review_bp
from routes.programs import bp as programs_bp
from routes.reports import bp as reports_bp
from routes.supervision import bp as supervision_bp
from routes.text_analysis import bp as text_analysis_bp
from routes.training_plan import bp as training_plan_bp


SERVICE_VERSION = "safehome-2026-06-04"
REQUIRED_CONTENT_FILES = [
    "training_cards.json",
    "feedback_rules.json",
    "risk_keywords.json",
    "programs.json",
    "courses.json",
    "readfeedback/student_profile_model.json",
]
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


class SafeHomeJSONProvider(DefaultJSONProvider):
    ensure_ascii = False

    def dumps(self, obj, **kwargs) -> str:
        kwargs.setdefault("default", self.default)
        kwargs.setdefault("ensure_ascii", self.ensure_ascii)
        kwargs.setdefault("sort_keys", self.sort_keys)
        return json.dumps(obj, **kwargs)


def check_content_health(content_dir) -> dict:
    missing_files = [filename for filename in REQUIRED_CONTENT_FILES if not (content_dir / filename).exists()]
    return {
        "ok": not missing_files,
        "content_dir": str(content_dir),
        "required_files_ok": not missing_files,
        "missing_files": missing_files,
    }


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
    app.register_blueprint(goals_bp)
    app.register_blueprint(diaries_bp)
    app.register_blueprint(emotion_thermometer_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(family_bp)
    app.register_blueprint(messages_bp)
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
    app.register_blueprint(risk_review_bp)
    app.register_blueprint(programs_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(supervision_bp)
    app.register_blueprint(text_analysis_bp)
    app.register_blueprint(training_plan_bp)
    app.register_blueprint(admin_bp)

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")
        if origin in app.config.get("ALLOWED_ORIGINS", []):
            response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Admin-Token, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
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
            return jsonify({"ok": False, "error": {"code": code, "message": message}}), status

        app.logger.exception("unhandled_exception method=%s path=%s", request.method, request.path)
        return jsonify({"ok": False, "error": {"code": "internal_error", "message": "服务暂时没有响应，请稍后再试。"}}), 500

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
    }


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5050"))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
