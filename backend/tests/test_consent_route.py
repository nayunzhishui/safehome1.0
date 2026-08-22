import importlib
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch, app_env: str = "development"):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", app_env)
    if app_env == "production":
        monkeypatch.setenv("DB_PROVIDER", "sqlite")
        monkeypatch.setenv("ALLOW_PRODUCTION_SQLITE", "1")
        monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "production-test-token")
        monkeypatch.setenv("SECRET_KEY", "production-test-secret-key-32-chars")
    else:
        monkeypatch.delenv("DB_PROVIDER", raising=False)
        monkeypatch.delenv("ALLOW_PRODUCTION_SQLITE", raising=False)
        monkeypatch.delenv("ADMIN_EXPORT_TOKEN", raising=False)
        monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    module = importlib.import_module("app")
    return module.app


def test_create_and_list_consent_records(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    create_response = client.post(
        "/api/consent",
        json={
            "user_id": "parent-consent",
            "consent_type": "user_agreement",
            "consent_version": "2026.07-consent-v2",
            "agreed": True,
        },
    )

    assert create_response.status_code == 201
    created = create_response.get_json()["data"]
    assert created["user_id"] == "parent-consent"
    assert created["consent_type"] == "user_agreement"
    assert created["consent_version"] == "2026.07-consent-v2"
    assert created["agreed"] == 1
    assert created["revoked_at"] is None

    list_response = client.get("/api/consent?user_id=parent-consent")
    assert list_response.status_code == 200
    listed = list_response.get_json()["data"]
    assert listed["count"] == 1
    assert listed["items"][0]["id"] == created["id"]


def test_research_authorization_can_be_declined(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.post(
        "/api/consent",
        json={
            "user_id": "parent-consent",
            "consent_type": "research_authorization",
            "agreed": False,
        },
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["agreed"] == 0
    assert data["consent_version"] == "2026.07-consent-v2"
    assert data["revoked_at"]


def test_invalid_consent_type_is_rejected(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.post(
        "/api/consent",
        json={
            "user_id": "parent-consent",
            "consent_type": "clinical_diagnosis",
            "agreed": True,
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "validation_error"


def test_task37_data_purposes_have_separate_consent_records(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    for consent_type in (
        "service_data",
        "quality_evaluation",
        "model_training",
        "secondary_research",
    ):
        response = client.post(
            "/api/consent",
            json={
                "user_id": "participant-task37",
                "consent_type": consent_type,
                "consent_version": f"2026.07-{consent_type}-v1",
                "agreed": consent_type == "service_data",
            },
        )
        assert response.status_code == 201
        assert response.get_json()["data"]["consent_type"] == consent_type

    listed = client.get("/api/consent?user_id=participant-task37").get_json()["data"]
    assert {item["consent_type"] for item in listed["items"]} == {
        "service_data",
        "quality_evaluation",
        "model_training",
        "secondary_research",
    }


def test_production_consent_requires_authenticated_actor(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, app_env="production")
    client = app.test_client()

    response = client.post(
        "/api/consent",
        json={
            "consent_type": "privacy_policy",
            "agreed": True,
        },
    )

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "unauthorized"


def test_profile_records_consent_summary_and_exports_status(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    client.post(
        "/api/consent",
        json={"user_id": "student-consent", "consent_type": "research_authorization", "agreed": True},
    )
    profile_response = client.post(
        "/api/profile",
        json={
            "user_id": "student-consent",
            "scores": {
                "test_anxiety": 4.2,
                "iu_score": 4.1,
                "f_score": 2.8,
                "self_compassion": 2.7,
            },
            "free_text": "考试前会担心，但愿意先做一次情绪命名练习。",
        },
    )

    assert profile_response.status_code == 201
    created = profile_response.get_json()["data"]
    assert created["consent_summary"]["research_authorization"]["status"] == "agreed"

    detail_response = client.get(f"/api/profile-results/{created['student_profile_id']}?user_id=student-consent")
    assert detail_response.status_code == 200
    detail = detail_response.get_json()["data"]
    assert detail["report"]["consent_summary"]["research_authorization"]["status"] == "agreed"

    export_response = client.get(
        "/api/admin/export?type=profile&user_id=student-consent",
        headers={"X-Admin-Token": "safehome-local-admin-token"},
    )
    assert export_response.status_code == 200
    csv_text = export_response.get_data(as_text=True)
    assert "research_authorization_status" in csv_text
    assert "agreed" in csv_text


def _parent_answers() -> dict:
    content_path = PROJECT_ROOT / "content" / "readfeedback" / "parent_scales.json"
    payload = json.loads(content_path.read_text(encoding="utf-8"))
    return {
        item["item_code"]: "3"
        for scale in payload["scales"]
        for item in scale["items"]
    }


def test_parent_assessment_research_consent_syncs_consent_record_and_export(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.post(
        "/api/parent-assessments",
        json={
            "user_id": "parent-consent-assessment",
            "participant_code": "PCONSENT",
            "research_consent": True,
            "answers": _parent_answers(),
            "question_answers": {
                "q1": "comfort",
                "q2": "sometimes",
                "q3": "early",
                "q4": "balanced",
                "q5": "some",
                "q7": "clear",
                "q8": "pause",
            },
        },
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["research_consent"] == 1
    assert data["consent_summary"]["research_authorization"] == "agreed"

    consent_response = client.get("/api/consent?user_id=parent-consent-assessment")
    records = consent_response.get_json()["data"]["items"]
    assert any(item["consent_type"] == "research_authorization" and item["agreed"] == 1 for item in records)

    export_response = client.get(
        "/api/admin/export?type=parent_assessments&user_id=parent-consent-assessment",
        headers={"X-Admin-Token": "safehome-local-admin-token"},
    )
    assert export_response.status_code == 200
    csv_text = export_response.get_data(as_text=True)
    assert "research_consent_status" in csv_text
    assert "PCONSENT" in csv_text
