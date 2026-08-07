import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_task18_opening_matrix_covers_all_governed_content():
    subprocess.run([sys.executable, str(ROOT / "scripts" / "audit_task18_opening.py")], cwd=ROOT, check=True)
    payload = json.loads((ROOT / "outputs" / "task18_opening_matrix.json").read_text(encoding="utf-8"))
    rows = payload["rows"]

    assert sum(1 for item in rows if item["kind"] == "量表") == 33
    assert sum(1 for item in rows if item["kind"] == "训练卡") == 42
    assert sum(1 for item in rows if item["kind"] == "课程") == 5
    assert sum(1 for item in rows if item["kind"] == "项目") == 3
    assert sum(1 for item in rows if item["kind"] == "画像模型") == 11
    assert all(item["opening_category"] != "开放" for item in rows if item["kind"] in {"课程", "项目"})
    assert all(item["opening_category"] in {"研究者受控", "继续隐藏"} for item in rows if item["kind"] == "研究分析")


def test_production_showcase_opens_cards_and_courses_without_changing_review_status(tmp_path, monkeypatch):
    sys.path.insert(0, str(ROOT / "backend"))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("ALLOW_PRODUCTION_SQLITE", "1")
    monkeypatch.setenv("SECRET_KEY", "task18-opening-production-secret")
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "task18-opening-admin")
    monkeypatch.setenv("LEGACY_ADMIN_TOKEN_ENABLED", "1")
    app = __import__("app").app
    client = app.test_client()

    assert len(client.get("/api/cards").get_json()["data"]["items"]) == 42
    assert len(client.get("/api/cards/recommend").get_json()["data"]["items"]) > 0
    courses = client.get("/api/courses").get_json()["data"]
    assert len(courses["items"]) == 5
    assert courses["pathways"]
    assert courses["pending_review_count"] == 5
    assert client.get("/api/courses/understand_child_emotion").status_code == 200

    headers = {"X-Admin-Token": "task18-opening-admin"}
    assert len(client.get("/api/cards?include_unapproved=true", headers=headers).get_json()["data"]["items"]) == 42
    assert len(client.get("/api/courses?include_unapproved=true", headers=headers).get_json()["data"]["items"]) == 5
