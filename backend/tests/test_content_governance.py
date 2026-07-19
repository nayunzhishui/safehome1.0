import importlib
import json
import shutil
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
CONTENT_ROOT = PROJECT_ROOT / "content"
ADMIN_HEADERS = {"X-Admin-Token": "safehome-local-admin-token"}


def _fresh_app(tmp_path, monkeypatch, *, publish_enabled=True):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    content_dir = tmp_path / "content"
    shutil.copytree(CONTENT_ROOT, content_dir)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    monkeypatch.setenv("CONTENT_GOVERNANCE_PUBLISH_ENABLED", "1" if publish_enabled else "0")
    module = importlib.import_module("app")
    return module.app, content_dir


def _draft_payload(version="v2"):
    return {
        "content_type": "training_card",
        "item_id": "emotion_naming",
        "version": version,
        "payload": {
            "id": "emotion_naming",
            "title": "给情绪一个名字",
            "purpose": "帮助识别当下感受，不作诊断。",
            "steps": ["停一下", "选一个接近的情绪词"],
            "enabled": True,
        },
        "metadata": {
            "source": "项目自研",
            "source_version": "source-v2",
            "copyright_status": "owned",
            "age_scope": "12岁以上及照护者",
            "audience": "student,parent",
            "change_summary": "精简步骤并保持非诊断边界",
        },
    }


def _review_headers(app):
    actors = [
        ("research-reviewer", "researcher"),
        ("psychology-reviewer", "supervisor"),
        ("ethics-reviewer", "supervisor"),
        ("content-reviewer", "admin"),
    ]
    with app.app_context():
        database = importlib.import_module("database")
        auth_utils = importlib.import_module("routes.auth_utils")
        with database.get_connection() as conn:
            now = database.now_iso()
            for actor_id, role in actors:
                conn.execute("INSERT INTO users (id, nickname, role, source, status, created_at, updated_at) VALUES (?, ?, ?, 'test', 'active', ?, ?)", (actor_id, actor_id, role, now, now))
            conn.commit()
        return {actor_id: {"Authorization": f"Bearer {auth_utils.generate_auth_token({'id': actor_id, 'role': role})}"} for actor_id, role in actors}


def _approve_all(app, client, version_id):
    headers = _review_headers(app)
    assignments = {
        "research": "research-reviewer",
        "psychology": "psychology-reviewer",
        "ethics": "ethics-reviewer",
        "content": "content-reviewer",
    }
    for discipline, actor_id in assignments.items():
        response = client.post(
            f"/api/content-review/versions/{version_id}/reviews",
            json={"discipline": discipline, "decision": "approved", "evidence_path": f"evidence/{discipline}.md"},
            headers=headers[actor_id],
        )
        assert response.status_code == 200
    return response.get_json()["data"]


def test_inventory_registration_never_auto_approves(tmp_path, monkeypatch):
    app, _ = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.post("/api/content-review/inventory/register", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.get_json()["data"]["auto_approved"] is False

    versions = client.get("/api/content-review/versions?content_type=training_card&item_id=emotion_naming", headers=ADMIN_HEADERS)
    item = versions.get_json()["data"]["items"][0]
    assert item["status"] == "registered"
    assert item["metadata"]["governance_status"] != "approved"


def test_draft_requires_complete_source_copyright_and_age_metadata(tmp_path, monkeypatch):
    app, _ = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    payload = _draft_payload()
    payload["metadata"].pop("copyright_status")

    response = client.post("/api/content-review/versions", json=payload, headers=ADMIN_HEADERS)

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "content_metadata_incomplete"
    assert "copyright_status" in response.get_json()["error"]["details"]["missing_fields"]


def test_full_review_publish_pause_and_restore_keep_immutable_hash(tmp_path, monkeypatch):
    app, content_dir = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    created = client.post("/api/content-review/versions", json=_draft_payload(), headers=ADMIN_HEADERS).get_json()["data"]
    version_id = created["id"]

    submitted = client.post(f"/api/content-review/versions/{version_id}/submit", headers=ADMIN_HEADERS)
    assert submitted.status_code == 200
    approved = _approve_all(app, client, version_id)
    assert approved["status"] == "approved"

    publish = client.post(
        f"/api/content-review/versions/{version_id}/publish",
        json={"confirm_publish": True, "expected_hash": created["payload_hash"], "dependency_impact_confirmed": True, "release_reason": "合成验收发布"},
        headers=ADMIN_HEADERS,
    )
    assert publish.status_code == 200
    release = publish.get_json()["data"]
    assert release["package"]["payload_hash"] == created["payload_hash"]
    descriptor = client.get("/api/content-review/active/training_card/emotion_naming").get_json()["data"]
    assert descriptor["release_id"] == release["release_id"]
    assert descriptor["payload_hash"] == created["payload_hash"]
    active = json.loads((content_dir / "training_cards.json").read_text(encoding="utf-8"))
    assert next(card for card in active["cards"] if card["id"] == "emotion_naming")["title"] == "给情绪一个名字"

    paused = client.post(
        f"/api/content-review/releases/{release['release_id']}/pause",
        json={"confirm_action": True, "dependency_impact_confirmed": True},
        headers=ADMIN_HEADERS,
    )
    assert paused.status_code == 200
    inactive = json.loads((content_dir / "training_cards.json").read_text(encoding="utf-8"))
    assert next(card for card in inactive["cards"] if card["id"] == "emotion_naming")["enabled"] is False

    restored = client.post(
        f"/api/content-review/releases/{release['release_id']}/restore",
        json={"confirm_action": True},
        headers=ADMIN_HEADERS,
    )
    assert restored.status_code == 200
    assert restored.get_json()["data"]["restored"] is True
    detail = client.get(f"/api/content-review/versions/{version_id}", headers=ADMIN_HEADERS).get_json()["data"]
    assert detail["payload_hash"] == created["payload_hash"]


def test_publish_is_independently_gated_by_environment_confirmation_and_hash(tmp_path, monkeypatch):
    app, _ = _fresh_app(tmp_path, monkeypatch, publish_enabled=False)
    client = app.test_client()
    created = client.post("/api/content-review/versions", json=_draft_payload(), headers=ADMIN_HEADERS).get_json()["data"]
    version_id = created["id"]
    client.post(f"/api/content-review/versions/{version_id}/submit", headers=ADMIN_HEADERS)
    _approve_all(app, client, version_id)

    response = client.post(
        f"/api/content-review/versions/{version_id}/publish",
        json={"confirm_publish": True, "expected_hash": created["payload_hash"]},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "content_publish_disabled"


def test_atomic_publish_restores_content_file_when_database_switch_fails(tmp_path, monkeypatch):
    app, content_dir = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    created = client.post("/api/content-review/versions", json=_draft_payload(), headers=ADMIN_HEADERS).get_json()["data"]
    client.post(f"/api/content-review/versions/{created['id']}/submit", headers=ADMIN_HEADERS)
    _approve_all(app, client, created["id"])
    before = (content_dir / "training_cards.json").read_bytes()

    with app.app_context():
        service = importlib.import_module("services.content_governance_service")
        original_get_connection = service.get_connection
        calls = {"count": 0}

        def failing_get_connection():
            calls["count"] += 1
            if calls["count"] == 3:
                raise RuntimeError("synthetic database switch failure")
            return original_get_connection()

        monkeypatch.setattr(service, "get_connection", failing_get_connection)
        with pytest.raises(RuntimeError, match="synthetic database switch failure"):
            service.publish_version({"id": "admin-token", "role": "admin"}, created["id"], {"confirm_publish": True, "expected_hash": created["payload_hash"], "dependency_impact_confirmed": True, "release_reason": "恢复测试"})

    assert (content_dir / "training_cards.json").read_bytes() == before


def test_release_lock_rejects_concurrent_switch_without_changing_content(tmp_path, monkeypatch):
    app, content_dir = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    created = client.post("/api/content-review/versions", json=_draft_payload(), headers=ADMIN_HEADERS).get_json()["data"]
    client.post(f"/api/content-review/versions/{created['id']}/submit", headers=ADMIN_HEADERS)
    _approve_all(app, client, created["id"])
    before = (content_dir / "training_cards.json").read_bytes()
    lock_path = content_dir / ".content-governance.lock"
    lock_path.write_text("synthetic active release", encoding="utf-8")
    try:
        with app.app_context():
            service = importlib.import_module("services.content_governance_service")
            with pytest.raises(service.GovernanceError) as error:
                service.publish_version({"id": "admin-token", "role": "admin"}, created["id"], {"confirm_publish": True, "expected_hash": created["payload_hash"], "dependency_impact_confirmed": True, "release_reason": "并发测试"})
            assert error.value.code == "content_release_in_progress"
    finally:
        lock_path.unlink(missing_ok=True)
    assert (content_dir / "training_cards.json").read_bytes() == before


def test_research_role_cannot_sign_ethics_review(tmp_path, monkeypatch):
    app, _ = _fresh_app(tmp_path, monkeypatch)
    with app.app_context():
        database = importlib.import_module("database")
        auth_utils = importlib.import_module("routes.auth_utils")
        with database.get_connection() as conn:
            now = database.now_iso()
            conn.execute("INSERT INTO users (id, nickname, role, source, status, created_at, updated_at) VALUES ('researcher-1', '研究者', 'researcher', 'test', 'active', ?, ?)", (now, now))
            conn.commit()
        token = auth_utils.generate_auth_token({"id": "researcher-1", "role": "researcher"})
    client = app.test_client()
    created = client.post("/api/content-review/versions", json=_draft_payload(), headers=ADMIN_HEADERS).get_json()["data"]
    client.post(f"/api/content-review/versions/{created['id']}/submit", headers=ADMIN_HEADERS)

    response = client.post(
        f"/api/content-review/versions/{created['id']}/reviews",
        json={"discipline": "ethics", "decision": "approved", "evidence_path": "evidence/ethics.md"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "review_discipline_forbidden"


def test_one_reviewer_cannot_approve_multiple_disciplines(tmp_path, monkeypatch):
    app, _ = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    created = client.post("/api/content-review/versions", json=_draft_payload(), headers=ADMIN_HEADERS).get_json()["data"]
    client.post(f"/api/content-review/versions/{created['id']}/submit", headers=ADMIN_HEADERS)
    first = client.post(f"/api/content-review/versions/{created['id']}/reviews", json={"discipline": "research", "decision": "approved", "evidence_path": "evidence/research.md"}, headers=ADMIN_HEADERS)
    second = client.post(f"/api/content-review/versions/{created['id']}/reviews", json={"discipline": "psychology", "decision": "approved", "evidence_path": "evidence/psychology.md"}, headers=ADMIN_HEADERS)

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.get_json()["error"]["code"] == "reviewer_independence_required"


def test_dependency_scan_and_synthetic_replay_cover_high_risk_block(tmp_path, monkeypatch):
    app, _ = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    created = client.post("/api/content-review/versions", json=_draft_payload(), headers=ADMIN_HEADERS).get_json()["data"]
    detail = client.get(f"/api/content-review/versions/{created['id']}", headers=ADMIN_HEADERS).get_json()["data"]
    assert "impacts" in detail["dependency_impact"]

    response = client.post(
        "/api/content-review/replay",
        json={"cases": [{"case_id": "high-risk", "text": "我想自杀", "expected": {"risk_level": "high", "auto_feedback_allowed": False, "recommendation_allowed": False, "boundary_notice_present": True}}]},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    result = response.get_json()["data"]
    assert result["summary"] == {"total": 1, "passed": 1, "failed": 0}
    assert result["evidence_level"] == "synthetic_only"


def test_enforced_governance_blocks_legacy_direct_json_update(tmp_path, monkeypatch):
    app, _ = _fresh_app(tmp_path, monkeypatch)
    app.config["CONTENT_GOVERNANCE_ENFORCED"] = True
    client = app.test_client()

    response = client.post(
        "/api/content-review/update",
        json={"content_type": "training_card", "item_id": "emotion_naming", "review_status": "reviewed"},
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "legacy_content_update_disabled"
