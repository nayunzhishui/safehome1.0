"""Flask application entrypoint for the SafeHome MVP backend."""

from flask import Flask, jsonify

from config import Config
from database import init_db
from routes.admin import bp as admin_bp
from routes.cards import bp as cards_bp
from routes.checkins import bp as checkins_bp
from routes.diaries import bp as diaries_bp
from routes.feedback import bp as feedback_bp
from routes.goals import bp as goals_bp
from routes.reports import bp as reports_bp
from routes.supervision import bp as supervision_bp


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)
    init_db()

    app.register_blueprint(goals_bp)
    app.register_blueprint(diaries_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(cards_bp)
    app.register_blueprint(checkins_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(supervision_bp)
    app.register_blueprint(admin_bp)

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        return response

    @app.get("/healthz")
    def healthz():
        return jsonify({"ok": True, "service": "safehome-backend"})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
