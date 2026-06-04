"""Flask application entrypoint for the SafeHome MVP backend."""

import os

from flask import Flask, jsonify, request

from config import Config
from database import init_db
from routes.admin import bp as admin_bp
from routes.assessments import bp as assessments_bp
from routes.cards import bp as cards_bp
from routes.checkins import bp as checkins_bp
from routes.consent import bp as consent_bp
from routes.diaries import bp as diaries_bp
from routes.feedback import bp as feedback_bp
from routes.goals import bp as goals_bp
from routes.parent_assessments import bp as parent_assessments_bp
from routes.profile import bp as profile_bp
from routes.risk_review import bp as risk_review_bp
from routes.reports import bp as reports_bp
from routes.supervision import bp as supervision_bp


def create_app(config_class: type[Config] = Config) -> Flask:
    config_class.validate()
    app = Flask(__name__)
    app.config.from_object(config_class)
    init_db()

    app.register_blueprint(goals_bp)
    app.register_blueprint(diaries_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(parent_assessments_bp)
    app.register_blueprint(assessments_bp)
    app.register_blueprint(cards_bp)
    app.register_blueprint(checkins_bp)
    app.register_blueprint(consent_bp)
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
        return jsonify({"ok": True, "service": "safehome-backend"})

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5050"))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
