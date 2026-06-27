"""Flask application entrypoint for the SafeHome MVP backend."""

import json
import os

from flask import Flask, jsonify, request
from flask.json.provider import DefaultJSONProvider

from config import Config
from database import check_database_health, init_db
from routes.admin import bp as admin_bp
from routes.assessments import bp as assessments_bp
from routes.auth import bp as auth_bp
from routes.cards import bp as cards_bp
from routes.checkins import bp as checkins_bp
from routes.consent import bp as consent_bp
from routes.content_review import bp as content_review_bp
from routes.diaries import bp as diaries_bp
from routes.feedback import bp as feedback_bp
from routes.family import bp as family_bp
from routes.goals import bp as goals_bp
from routes.parent_assessments import bp as parent_assessments_bp
from routes.privacy import bp as privacy_bp
from routes.profile import bp as profile_bp
from routes.risk_review import bp as risk_review_bp
from routes.reports import bp as reports_bp
from routes.supervision import bp as supervision_bp


SERVICE_VERSION = "safehome-2026-06-04"
REQUIRED_CONTENT_FILES = [
    "training_cards.json",
    "feedback_rules.json",
    "risk_keywords.json",
    "readfeedback/student_profile_model.json",
]


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


def create_app(config_class: type[Config] = Config) -> Flask:
    config_class.validate()
    app = Flask(__name__)
    app.json = SafeHomeJSONProvider(app)
    app.config.from_object(config_class)
    app.config.pop("JSON_AS_ASCII", None)
    init_db()

    app.register_blueprint(auth_bp)
    app.register_blueprint(goals_bp)
    app.register_blueprint(diaries_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(family_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(parent_assessments_bp)
    app.register_blueprint(assessments_bp)
    app.register_blueprint(cards_bp)
    app.register_blueprint(checkins_bp)
    app.register_blueprint(consent_bp)
    app.register_blueprint(content_review_bp)
    app.register_blueprint(privacy_bp)
    app.register_blueprint(risk_review_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(supervision_bp)
    app.register_blueprint(admin_bp)

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")
        if origin in app.config.get("ALLOWED_ORIGINS", []):
            response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Admin-Token, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        return response

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
        database = check_database_health()
        content = check_content_health(app.config["CONTENT_DIR"])
        return jsonify(
            {
                "ok": bool(database.get("ok") and content.get("ok")),
                "service": "safehome-backend",
                "env": app.config.get("APP_ENV"),
                "version": SERVICE_VERSION,
                "database": database,
                "content": content,
            }
        )

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5050"))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
