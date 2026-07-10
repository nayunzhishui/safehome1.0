"""Start an isolated local backend for Playwright end-to-end checks."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))
runtime_dir = Path(tempfile.mkdtemp(prefix="safehome-e2e-"))
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("DATABASE_PATH", str(runtime_dir / "safehome-e2e.sqlite3"))
os.environ.setdefault("CONTENT_DIR", str(ROOT / "content"))
os.environ.setdefault("ADMIN_EXPORT_TOKEN", "e2e-admin-token")
os.environ.setdefault("ALLOWED_ORIGINS", "http://127.0.0.1:5173")

from app import app  # noqa: E402
from database import get_connection, now_iso  # noqa: E402
from werkzeug.security import generate_password_hash  # noqa: E402


def seed_researcher() -> None:
    timestamp = now_iso()
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM users WHERE username = ?", ("e2e_researcher",)).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO users (id, nickname, role, source, username, password_hash, status, created_at, updated_at) VALUES (?, ?, 'researcher', 'e2e', ?, ?, 'active', ?, ?)",
                ("e2e_researcher", "E2E研究者", "e2e_researcher", generate_password_hash("e2e-password-123"), timestamp, timestamp),
            )
            conn.commit()


if __name__ == "__main__":
    seed_researcher()
    app.run(host="127.0.0.1", port=5050, debug=False, use_reloader=False)
