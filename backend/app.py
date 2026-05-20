"""Flask application entrypoint for the SafeHome MVP skeleton.

This file intentionally exposes only a minimal app factory and health check.
Business routes will be implemented in later tasks.
"""

from flask import Flask, jsonify

from config import Config


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    @app.get("/healthz")
    def healthz():
        return jsonify({"ok": True, "service": "safehome-backend"})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
