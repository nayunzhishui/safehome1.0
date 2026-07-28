import importlib
import json
import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
CONTENT_ROOT = PROJECT_ROOT / "content"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    content_dir = tmp_path / "content"
    shutil.copytree(CONTENT_ROOT, content_dir)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    monkeypatch.setenv("AI_QA_ENABLED", "0")
    monkeypatch.setenv("AI_QA_SANDBOX_ENABLED", "1")
    monkeypatch.setenv("AI_QA_PROVIDER", "fake")
    return importlib.import_module("app").app


def _headers(app, *, actor_id: str, role: str):
    with app.app_context():
        database = importlib.import_module("database")
        auth_utils = importlib.import_module("routes.auth_utils")
        with database.get_connection() as conn:
            now = database.now_iso()
            conn.execute(
                """
                INSERT INTO users
                (id, nickname, role, source, status, created_at, updated_at)
                VALUES (?, ?, ?, 'test', 'active', ?, ?)
                """,
                (actor_id, actor_id, role, now, now),
            )
            conn.commit()
        token = auth_utils.generate_auth_token({"id": actor_id, "role": role})
    return {"Authorization": f"Bearer {token}"}


def test_provider_registry_is_fail_closed_and_contains_only_public_evidence(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    headers = _headers(app, actor_id="researcher-c02", role="researcher")

    response = client.get("/api/ai-qa/providers", headers=headers)

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["policy_version"] == "2026.07-t37-c02-v1"
    assert data["status"] == "blocked_external_contract_evidence"
    assert data["selected_provider"] is None
    assert data["external_provider_enabled"] is False
    assert {item["id"] for item in data["candidates"]} == {"deepseek", "openai"}
    assert all(item["production_eligible"] is False for item in data["candidates"])
    assert data["outbound_policy"]["activated"] is False
    serialized = json.dumps(data, ensure_ascii=False).lower()
    assert "sk-" not in serialized
    assert "api_key_value" not in serialized


def test_parent_cannot_view_provider_contract_workbench(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    response = app.test_client().get(
        "/api/ai-qa/providers",
        headers=_headers(app, actor_id="parent-c02", role="parent"),
    )
    assert response.status_code == 403


def test_researcher_cannot_write_and_secret_like_metadata_is_rejected(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    payload = {
        "provider_id": "openai",
        "evidence_type": "service_contract",
        "artifact_ref": "evidence://contracts/service.pdf",
        "artifact_sha256": "b" * 64,
    }
    researcher = client.post(
        "/api/ai-qa/providers/evidence",
        json=payload,
        headers={
            **_headers(app, actor_id="researcher-c02-write", role="researcher"),
            "Idempotency-Key": "researcher-write",
        },
    )
    secret = client.post(
        "/api/ai-qa/providers/evidence",
        json={**payload, "artifact_ref": "sk-do-not-store"},
        headers={
            **_headers(app, actor_id="admin-c02-secret", role="admin"),
            "Idempotency-Key": "secret-write",
        },
    )
    assert researcher.status_code == 403
    assert secret.status_code == 422
    assert secret.get_json()["error"]["code"] == "secret_material_rejected"


def test_contract_evidence_requires_independent_verification_and_all_gates(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    admin_headers = _headers(app, actor_id="admin-c02", role="admin")
    supervisor_headers = _headers(
        app, actor_id="supervisor-c02", role="supervisor"
    )
    payload = {
        "provider_id": "deepseek",
        "evidence_type": "data_processing_agreement",
        "artifact_ref": "evidence://contracts/deepseek-dpa-redacted.pdf",
        "artifact_sha256": "a" * 64,
        "notes": "脱敏副本，仅登记证据元数据。",
    }

    created = client.post(
        "/api/ai-qa/providers/evidence",
        json=payload,
        headers={**admin_headers, "Idempotency-Key": "c02-evidence-1"},
    )
    replay = client.post(
        "/api/ai-qa/providers/evidence",
        json=payload,
        headers={**admin_headers, "Idempotency-Key": "c02-evidence-1"},
    )
    assert created.status_code == 201
    assert replay.status_code == 200
    item = created.get_json()["data"]
    assert item["status"] == "pending"
    assert item["qualifies_for_selection"] is False

    self_verify = client.post(
        f"/api/ai-qa/providers/evidence/{item['id']}/verify",
        json={"decision": "verified", "expected_version": 1},
        headers={**admin_headers, "Idempotency-Key": "c02-verify-self"},
    )
    assert self_verify.status_code == 409
    assert self_verify.get_json()["error"]["code"] == "independent_review_required"

    verified = client.post(
        f"/api/ai-qa/providers/evidence/{item['id']}/verify",
        json={"decision": "verified", "expected_version": 1},
        headers={**supervisor_headers, "Idempotency-Key": "c02-verify-independent"},
    )
    assert verified.status_code == 200
    assert verified.get_json()["data"]["status"] == "verified"
    assert verified.get_json()["data"]["qualifies_for_selection"] is True

    status = client.get("/api/ai-qa/providers", headers=admin_headers)
    data = status.get_json()["data"]
    deepseek = next(item for item in data["candidates"] if item["id"] == "deepseek")
    assert "data_processing_agreement" not in deepseek["missing_evidence"]
    assert deepseek["missing_evidence"]
    assert deepseek["production_eligible"] is False
    assert data["selected_provider"] is None


def test_provider_config_exposes_selection_summary_not_contract_details(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    data = app.test_client().get("/api/ai-qa/config").get_json()["data"]
    summary = data["provider_selection"]
    assert summary == {
        "policy_version": "2026.07-t37-c02-v1",
        "status": "blocked_external_contract_evidence",
        "selected_provider": None,
        "external_provider_enabled": False,
        "candidate_ids": ["deepseek", "openai"],
    }
    assert "official_sources" not in summary
    assert "secret_env_names" not in summary


def test_schema_051_adds_provider_evidence_table(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            tables = {
                row["name"]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            columns = {
                row["name"]
                for row in conn.execute(
                    "PRAGMA table_info(ai_provider_contract_evidence)"
                ).fetchall()
            }
    assert database.CURRENT_SCHEMA_VERSION == "2026_07_28_051"
    assert database.CURRENT_SCHEMA_NAME == "ai_provider_selection_evidence"
    assert "ai_provider_contract_evidence" in tables
    assert {
        "provider_id",
        "evidence_type",
        "artifact_ref",
        "artifact_sha256",
        "status",
        "recorded_by",
        "verified_by",
        "version",
        "idempotency_key",
    }.issubset(columns)
