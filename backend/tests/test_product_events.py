import importlib
import json
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_app(tmp_path):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    os.environ["APP_ENV"] = "development"
    os.environ["DATABASE_PATH"] = str(tmp_path / "safehome-test.sqlite3")
    os.environ["CONTENT_DIR"] = str(PROJECT_ROOT / "content")
    return importlib.import_module("app").app


def _student_headers(client):
    response = client.post(
        "/api/auth/register",
        json={"username": "event-student", "password": "password123", "role": "student"},
    )
    token = response.get_json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


def test_product_event_records_only_allowlisted_metadata(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    headers = _student_headers(client)

    response = client.post(
        "/api/product-events",
        headers=headers,
        json={
            "event_name": "relationship_entry_clicked",
            "metadata": {"action": "drawing", "stage": "exploration", "source": "primary_action"},
        },
    )

    assert response.status_code == 202
    database = importlib.import_module("database")
    with database.get_connection() as conn:
        row = conn.execute(
            "SELECT action, metadata_json FROM audit_logs WHERE action = ?",
            ("product_event_relationship_entry_clicked",),
        ).fetchone()
    metadata = json.loads(row["metadata_json"])
    assert metadata == {"action": "drawing", "source": "primary_action", "stage": "exploration"}


def test_product_event_rejects_sensitive_or_free_text_metadata(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    headers = _student_headers(client)

    unknown_field = client.post(
        "/api/product-events",
        headers=headers,
        json={"event_name": "relationship_task_save_failed", "metadata": {"raw_text": "一段敏感原文"}},
    )
    free_text = client.post(
        "/api/product-events",
        headers=headers,
        json={"event_name": "relationship_entry_clicked", "metadata": {"action": "一段自由文本"}},
    )

    assert unknown_field.status_code == 400
    assert free_text.status_code == 400


def test_product_event_requires_signed_login(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    response = client.post(
        "/api/product-events",
        json={"event_name": "relationship_report_downloaded", "metadata": {}},
    )

    assert response.status_code == 401


def test_product_event_rejects_non_object_payload(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    headers = _student_headers(client)

    response = client.post("/api/product-events", headers=headers, json=["relationship_entry_clicked"])

    assert response.status_code == 400
