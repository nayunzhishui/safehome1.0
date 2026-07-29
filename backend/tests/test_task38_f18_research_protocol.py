import importlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
PROTOCOL = ROOT / "content" / "therapeutic_assessment_research_protocol.json"


def _app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "f18.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def _seed(app):
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token

        now = now_iso()
        users = {
            "participant-f18": "parent",
            "researcher-f18": "researcher",
            "other-researcher-f18": "researcher",
            "admin-f18": "admin",
        }
        with get_connection() as conn:
            for user_id, role in users.items():
                conn.execute(
                    "INSERT INTO users (id, nickname, role, status, created_at, updated_at) "
                    "VALUES (?, ?, ?, 'active', ?, ?)",
                    (user_id, user_id, role, now, now),
                )
            conn.execute(
                """
                INSERT INTO therapeutic_assessment_cases
                (id, participant_user_id, assessment_question, shared_scope_json,
                 consent_status, status, risk_level, workflow_state, hypothesis_state,
                 safety_state, complexity_scope, readiness_level, assigned_researcher_id,
                 version, created_by, created_at, updated_at)
                VALUES ('case-f18', 'participant-f18', '不应进入导出的原始问题', '["question"]',
                        'active', 'open', 'low', 'participant_check', 'observations_only',
                        'low_risk', 'individual_adult_low_risk', 'L2', 'researcher-f18',
                        1, 'participant-f18', ?, ?)
                """,
                (now, now),
            )
            conn.execute(
                """
                INSERT INTO therapeutic_assessment_quality_incidents
                (id, case_id, reporter_user_id, source_type, category, description,
                 requested_resolution, status, idempotency_key, created_at, updated_at)
                VALUES ('incident-f18', 'case-f18', 'admin-f18', 'research_review',
                        'diagnostic_misunderstanding', '合成严重事件', '人工复核',
                        'reported', 'incident-f18-key', ?, ?)
                """,
                (now, now),
            )
            conn.commit()
        return {
            user_id: {
                "Authorization": f"Bearer {generate_auth_token({'id': user_id, 'role': role})}"
            }
            for user_id, role in users.items()
        }


def test_protocol_predefines_metrics_denominators_missingness_and_analysis():
    payload = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    assert payload["schema"] == "safehome.therapeutic-assessment.research-protocol.v1"
    assert payload["symptom_scales"]["role"] == "exploratory_outcome_only"
    assert payload["analysis_rules"]["satisfaction_may_offset_serious_harm"] is False
    metrics = payload["metrics"]
    assert {"process", "implementation", "harm"} <= set(metrics)
    required = {"id", "priority", "denominator", "timepoint", "missing_data", "analysis_method"}
    assert all(required <= set(item) for group in metrics.values() for item in group)
    assert any(item["id"] == "participant_question_retained" for item in metrics["process"])
    assert any(item["id"] == "risk_human_chain_failure" for item in metrics["harm"])


def test_protocol_and_export_are_formal_role_only_and_purpose_controlled(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    assert client.get(
        "/api/therapeutic-assessment/research-protocol",
        headers=headers["participant-f18"],
    ).status_code == 403
    protocol = client.get(
        "/api/therapeutic-assessment/research-protocol",
        headers=headers["researcher-f18"],
    )
    assert protocol.status_code == 200
    rejected = client.post(
        "/api/therapeutic-assessment/research-export/preview",
        json={"purpose": "marketing"},
        headers=headers["researcher-f18"],
    )
    assert rejected.status_code == 400


def test_research_export_is_minimal_deidentified_scoped_and_keeps_harm_separate(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    own = client.post(
        "/api/therapeutic-assessment/research-export/preview",
        json={"purpose": "protocol_analysis"},
        headers=headers["researcher-f18"],
    )
    assert own.status_code == 200
    data = own.get_json()["data"]
    assert data["count"] == 1
    row = data["rows"][0]
    assert row["case_key"].startswith("ta_")
    assert "case_id" not in row
    assert "participant_user_id" not in row
    assert "assessment_question" not in row
    assert "satisfaction" not in row
    assert row["serious_harm_open_count"] == 1
    assert data["harm_metrics_separate"] is True
    assert data["symptom_outcomes_role"] == "exploratory_outcome_only"

    other = client.post(
        "/api/therapeutic-assessment/research-export/preview",
        json={"purpose": "protocol_analysis"},
        headers=headers["other-researcher-f18"],
    )
    assert other.status_code == 200
    assert other.get_json()["data"]["count"] == 0


def test_shared_web_and_miniprogram_contracts_expose_controlled_protocol_only():
    shared = (ROOT / "shared" / "types" / "api.ts").read_text(encoding="utf-8")
    web_api = (
        ROOT / "apps" / "web" / "src" / "services" / "safehomeApi.ts"
    ).read_text(encoding="utf-8")
    mini_api = (
        ROOT / "apps" / "miniprogram" / "services" / "api.js"
    ).read_text(encoding="utf-8")
    assert "interface TherapeuticAssessmentResearchProtocol" in shared
    assert "previewTherapeuticAssessmentResearchExport" in web_api
    assert "previewTherapeuticAssessmentResearchExport" in mini_api
