import importlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
REGISTRY = ROOT / "content" / "therapeutic_assessment_service_levels.json"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(("routes.", "services.")):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task38-f01.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def _seed(app):
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token

        now = now_iso()
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO users (id, nickname, role, status, created_at, updated_at) VALUES ('parent-f01', '参与者', 'parent', 'active', ?, ?)",
                (now, now),
            )
            conn.execute(
                """INSERT INTO therapeutic_assessment_cases
                   (id, participant_user_id, assessment_question, shared_scope_json, consent_status,
                    status, risk_level, complexity_scope, readiness_level, version, created_by,
                    created_at, updated_at)
                   VALUES ('case-f01', 'parent-f01', '我想理解最近的沟通', '["question"]', 'active',
                           'open', 'low', 'individual_adult_low_risk', 'L0', 1, 'parent-f01', ?, ?)""",
                (now, now),
            )
            conn.commit()
        return {"Authorization": f"Bearer {generate_auth_token({'id': 'parent-f01', 'role': 'parent'})}"}


def test_registry_has_four_levels_and_safe_public_names():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert payload["schema"] == "safehome.therapeutic-assessment.service-levels.v1"
    assert [item["id"] for item in payload["levels"]] == ["L0", "L1", "L2", "L3"]
    assert payload["default_level"] == "L0"
    assert payload["levels"][0]["display_name"] == "支持性评估准备"
    assert payload["levels"][2]["display_name"] == "协作式阶段性评估"
    assert payload["levels"][3]["formal_ta"] is True
    assert payload["levels"][0]["formal_ta"] is False
    assert payload["levels"][1]["formal_ta"] is False
    assert "AI治疗性评估" not in json.dumps(payload, ensure_ascii=False)


def test_service_level_endpoint_and_case_response_share_same_contract(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    levels = client.get("/api/therapeutic-assessment/service-levels", headers=headers)
    cases = client.get("/api/therapeutic-assessment/cases", headers=headers)
    assert levels.status_code == 200 and cases.status_code == 200
    level_payload = levels.get_json()["data"]
    case = cases.get_json()["data"]["items"][0]
    assert level_payload["current_default"]["id"] == "L0"
    assert case["service_level"]["id"] == case["readiness_level"] == "L0"
    assert case["service_level"]["display_name"] == "支持性评估准备"
    assert case["service_level"]["formal_ta"] is False
    assert level_payload["production_max_without_human_chain"] == "L0"


def test_web_miniprogram_and_shared_use_public_language_and_show_level():
    mini = (ROOT / "apps/miniprogram/pages/therapeutic-assessment/index.wxml").read_text(encoding="utf-8")
    web = (ROOT / "apps/web/src/pages/TherapeuticAssessmentWorkbench.tsx").read_text(encoding="utf-8")
    shared = (ROOT / "shared/types/api.ts").read_text(encoding="utf-8")
    assert 'aria-label="支持性评估"' in mini
    assert "{{activeCase.service_level.display_name}}" in mini
    assert "协作式评估工作台" in web
    assert "selected.service_level.display_name" in web
    assert '"L0" | "L1" | "L2" | "L3"' in shared
