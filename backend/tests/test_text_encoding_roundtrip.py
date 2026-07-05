import importlib
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_app_and_database(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "test-secret-token")
    app_module = importlib.import_module("app")
    database = importlib.import_module("database")
    return app_module.app, database


def test_diary_text_roundtrip_preserves_chinese_english_digits_punctuation_and_emoji(tmp_path, monkeypatch):
    app, database = _fresh_app_and_database(tmp_path, monkeypatch)
    client = app.test_client()
    mixed_text = "今天孩子说 homework 还没写完，家长提醒 2 次；先停一下，再一起看🙂。"

    create_response = client.post(
        "/api/diaries",
        json={
            "user_id": "encoding-user",
            "scene": "作业沟通",
            "event_description": mixed_text,
            "parent_emotion": "着急",
            "parent_emotion_intensity": 6,
            "child_emotion": "烦躁",
            "child_emotion_intensity": 5,
            "raw_text": mixed_text,
        },
    )

    assert create_response.status_code == 201
    created = create_response.get_json()["data"]
    assert created["event_description"] == mixed_text
    assert created["raw_text"] == mixed_text

    with database.get_connection() as conn:
        row = conn.execute("SELECT * FROM emotion_diaries WHERE id = ?", (created["id"],)).fetchone()

    assert row["event_description"] == mixed_text
    assert row["raw_text"] == mixed_text

    list_response = client.get("/api/diaries?user_id=encoding-user")

    assert list_response.status_code == 200
    items = list_response.get_json()["data"]["items"]
    assert items[0]["event_description"] == mixed_text
    assert items[0]["raw_text"] == mixed_text
