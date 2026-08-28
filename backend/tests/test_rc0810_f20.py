import hashlib
import importlib
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _fresh_app(tmp_path, monkeypatch):
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    content_dir = tmp_path / "content"
    shutil.copytree(ROOT / "content", content_dir)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "f20.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    return importlib.import_module("app").app, content_dir


def _login(client, code="f20-parent"):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code})
    assert response.status_code == 200
    return response.get_json()["data"]["token"]


def _answers(value="2"):
    return [
        {"question_id": question_id, "value": value}
        for question_id in ["test_anxiety", "iu_score", "fear_score", "self_compassion"]
    ]


def test_governed_payload_descriptors_bind_version_and_hash():
    service = importlib.import_module("services.psychological_content_governance_service")
    content = json.loads((ROOT / "content" / "assessment_worksheets.json").read_text(encoding="utf-8"))
    worksheet = content["worksheets"][0]

    descriptor = service.describe_payload(
        "worksheet", worksheet["id"], worksheet, worksheet["source_version"]
    )

    expected = hashlib.sha256(
        json.dumps(worksheet, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    assert descriptor == {
        "content_type": "worksheet",
        "item_id": worksheet["id"],
        "version": worksheet["source_version"],
        "payload_hash": expected,
        "hash_algorithm": "sha256",
    }


def test_production_manifest_fails_closed_without_explicit_rights_approval():
    service = importlib.import_module("services.psychological_content_governance_service")
    audit = service.build_content_audit(ROOT)

    assert audit["production_manifest"]["worksheet_ids"] == []
    assert audit["production_manifest"]["status"] == "blocked_external"
    assert audit["external_gates"] == {
        "psychology_reviewer": "pending_external",
        "content_rights_owner": "pending_external",
    }
    assert audit["scale_rights_and_use"]
    assert all(item["production_eligible"] is False for item in audit["scale_rights_and_use"])
    assert all("copyright_status" in item for item in audit["scale_rights_and_use"])


def test_missing_scale_or_scoring_fields_cannot_enter_production():
    service = importlib.import_module("services.psychological_content_governance_service")
    worksheet = {
        "id": "unsafe",
        "source_file": "unknown",
        "source_version": "v1",
        "questions": [],
        "scoring": "",
        "boundary_notice": "",
        "result_disclaimer": "",
    }
    rights = {"copyright_status": "owned", "production_approval": "approved"}

    result = service.production_eligibility(worksheet, rights)

    assert result["eligible"] is False
    assert set(result["blockers"]) >= {
        "questions_missing",
        "scoring_missing",
        "boundary_notice_missing",
        "result_disclaimer_missing",
    }


def test_dual_track_and_participant_copy_audits_have_no_unapproved_findings():
    service = importlib.import_module("services.psychological_content_governance_service")
    audit = service.build_content_audit(ROOT)

    assert audit["dual_track_audit"]["hardcoded_payload_matches"] == []
    assert audit["copy_audit"]["participant_findings"] == []
    assert audit["legacy_content_tracks"] == [
        {
            "endpoint": "/api/profile",
            "source": "readfeedback/student_scales.json",
            "status": "validation_only_legacy_track",
            "production_enabled": False,
            "replacement": "POST /api/assessment-results with governed assessment_worksheets artifact",
        }
    ]
    assert audit["terminology"]["participant"] == ["支持性测评", "协作式了解", "阶段性观察"]
    assert audit["terminology"]["internal"] == ["治疗性评估"]


def test_submission_saves_exact_snapshot_and_history_replays_original_payload(tmp_path, monkeypatch):
    app, _content_dir = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    token = _login(client)
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": "f20-snapshot-replay",
    }
    payload = {"worksheet_id": "student_profile_v1", "answers": _answers("2")}

    created = client.post(
        "/api/assessment-results",
        headers=headers,
        json=payload,
    )
    assert created.status_code == 201
    created_data = created.get_json()["data"]
    result_id = created_data["id"]

    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            row = conn.execute(
                "SELECT content_snapshot_json, content_snapshot_hash, worksheet_payload_hash, "
                "worksheet_version, interpretation_version FROM assessment_results WHERE id = ?",
                (result_id,),
            ).fetchone()
            snapshot = json.loads(row["content_snapshot_json"])
            original_prompt = snapshot["worksheet_payload"]["questions"][0]["prompt"]
            worksheet_row = conn.execute(
                "SELECT questions_json FROM assessment_worksheets WHERE id = 'student_profile_v1'"
            ).fetchone()
            current_questions = json.loads(worksheet_row["questions_json"])
            current_questions[0]["prompt"] = "新版本题目，不得改变旧结果"
            conn.execute(
                "UPDATE assessment_worksheets SET questions_json = ?, source_version = ? WHERE id = ?",
                (json.dumps(current_questions, ensure_ascii=False), "future-v2", "student_profile_v1"),
            )
            conn.execute(
                "UPDATE core_idempotency_records SET response_json = NULL, response_status = NULL "
                "WHERE idempotency_key = ?",
                ("f20-snapshot-replay",),
            )
            conn.commit()

    detail = client.get(f"/api/assessment-results/{result_id}", headers=headers)
    assert detail.status_code == 200
    data = detail.get_json()["data"]
    assert data["content_snapshot"]["worksheet_payload"]["questions"][0]["prompt"] == original_prompt
    assert data["historical_replay"]["snapshot_valid"] is True
    assert data["historical_replay"]["scores"] == data["scores"]
    assert data["worksheet_version"] != "future-v2"
    assert data["worksheet_payload_hash"] == data["content_snapshot"]["worksheet"]["payload_hash"]
    replay = client.post("/api/assessment-results", headers=headers, json=payload)

    assert replay.status_code == 200
    replay_data = replay.get_json()["data"]
    assert replay_data["idempotency_replayed"] is True
    assert replay_data["content_snapshot"]["worksheet_payload"]["questions"][0]["prompt"] == original_prompt
    assert replay_data["worksheet_version"] == data["worksheet_version"]
    assert replay_data["scores"] == data["scores"]
    assert replay_data["recommended_card_ids"] == created_data["recommended_card_ids"]


def test_production_routes_use_empty_human_owned_allowlist(tmp_path, monkeypatch):
    app, _content_dir = _fresh_app(tmp_path, monkeypatch)
    app.config.update(APP_ENV="production", CONTENT_GOVERNANCE_ENFORCED=True)
    client = app.test_client()

    listing = client.get("/api/assessments")
    legacy_profile = client.get("/api/student-assessment")
    legacy_profile_write = client.post("/api/profile", json={})

    assert listing.status_code == 200
    assert listing.get_json()["data"]["items"] == []
    assert legacy_profile.status_code == 409
    assert legacy_profile.get_json()["error"]["code"] == "assessment_not_in_production_manifest"
    assert legacy_profile_write.status_code == 409
    assert legacy_profile_write.get_json()["error"]["code"] == "assessment_not_in_production_manifest"


def test_tampered_historical_snapshot_is_not_replayed():
    service = importlib.import_module("services.psychological_content_governance_service")
    snapshot = {
        "schema_version": "safehome.assessment-content-snapshot.v1",
        "worksheet_payload": {"id": "w1", "questions": []},
    }

    result = service.verify_snapshot(snapshot, "0" * 64)

    assert result == {"valid": False, "reason": "snapshot_hash_mismatch"}


def test_f20_additive_migration_and_database_head_are_registered():
    migration_source = (BACKEND / "services" / "schema_migration_service.py").read_text(encoding="utf-8")
    model_source = (BACKEND / "models.py").read_text(encoding="utf-8")
    profile = json.loads((ROOT / "config" / "rc0810" / "database_profiles.json").read_text(encoding="utf-8"))

    assert "2026_08_25_076" in migration_source
    for field in (
        "content_snapshot_json",
        "content_snapshot_hash",
        "worksheet_payload_hash",
        "worksheet_version",
        "interpretation_version",
    ):
        assert field in migration_source
        assert field in model_source
    assert profile["profiles"]["production"]["explicit_migration_head"] == "2026_08_26_078"
    assert profile["profiles"]["production"]["approved_migration_head"] == "2026_08_24_063+2026_08_26_078"


def test_global_content_validator_includes_f20_governance_contract():
    validator = importlib.import_module("scripts.validate_content")

    assert validator.validate_psychological_content_governance(ROOT / "content") == []
