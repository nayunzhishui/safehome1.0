import importlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch, content_dir=None):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "showcase.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir or ROOT / "content"))
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("ALLOW_PRODUCTION_SQLITE", "1")
    monkeypatch.setenv("SECRET_KEY", "showcase-test-secret-key-that-is-long-enough")
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "showcase-admin-token")
    return importlib.import_module("app").app


def test_showcase_opens_programs_and_training_cards_in_production(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    status = client.get("/api/showcase-access")
    programs = client.get("/api/programs")
    cards = client.get("/api/cards")

    assert status.status_code == 200
    assert status.get_json()["data"]["enabled"] is True
    assert len(programs.get_json()["data"]["items"]) == 3
    assert programs.get_json()["data"]["availability"]["status"] == "showcase_open"
    assert len(cards.get_json()["data"]["items"]) == 42


def test_close_script_restores_all_showcase_gates(tmp_path, monkeypatch):
    module_path = ROOT / "scripts" / "set_showcase_access.py"
    spec = importlib.util.spec_from_file_location("set_showcase_access", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    module.TARGET = tmp_path / "showcase_access.json"

    payload = module.set_mode(False)
    saved = json.loads(module.TARGET.read_text(encoding="utf-8"))

    assert payload["enabled"] is False
    assert saved["read_only_role_bypass"] is False
    assert saved["open_programs"] is False
    assert saved["open_training_cards"] is False
    assert saved["open_courses"] is False


def test_assessment_result_has_direct_owner_scoped_endpoint(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    register = client.post(
        "/api/auth/register",
        json={"username": "showcase-parent", "password": "StrongPass123!", "role": "parent", "nickname": "展示家长"},
    )
    token = register.get_json()["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}
    worksheet = client.get("/api/assessments/emotion_regulation_erq").get_json()["data"]
    answers = [{"question_id": item["id"], "value": item["options"][0]["value"]} for item in worksheet["questions"]]
    created = client.post(
        "/api/assessment-results",
        headers=headers,
        json={"worksheet_id": worksheet["id"], "answers": answers},
    )
    result_id = created.get_json()["data"]["id"]

    direct = client.get(f"/api/assessment-results/{result_id}", headers=headers)

    assert direct.status_code == 200
    assert direct.get_json()["data"]["id"] == result_id
    assert direct.get_json()["data"]["worksheet_id"] == worksheet["id"]


def test_miniprogram_result_page_uses_direct_result_and_auxiliary_fallbacks():
    page = (ROOT / "apps/miniprogram/pages/assessment-result/index.js").read_text(encoding="utf-8")
    assert "api.getAssessmentResult(this.data.resultId)" in page
    assert "api.getAssessment(this.data.worksheetId).catch(() => null)" in page
    assert "api.listAssessmentResults({ limit: 20 })" not in page
