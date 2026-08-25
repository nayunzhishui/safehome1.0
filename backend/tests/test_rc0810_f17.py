import hashlib
import importlib
import json
import shutil
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
CONTENT_ROOT = ROOT / "content"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    content_dir = tmp_path / "content"
    shutil.copytree(CONTENT_ROOT, content_dir)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "f17.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    monkeypatch.setenv("CONTENT_GOVERNANCE_PUBLISH_ENABLED", "1")
    return importlib.import_module("app").app, content_dir


def _approved_version(app, suffix: str, *, payload_id="emotion_naming", title=None):
    with app.app_context():
        database = importlib.import_module("database")
        service = importlib.import_module("services.content_governance_service")
        version_id = f"cgv-f17-{suffix}"
        payload = {
            "id": payload_id,
            "title": title or f"不可变内容 {suffix}",
            "purpose": "帮助识别感受，不作诊断。",
            "steps": ["停一下", "说出一个感受"],
            "enabled": True,
        }
        metadata = {
            "source": "项目自研",
            "source_version": suffix,
            "copyright_status": "owned",
            "age_scope": "12岁以上及照护者",
            "audience": "student,parent",
            "change_summary": f"F17 {suffix}",
        }
        now = database.now_iso()
        with database.get_connection() as conn:
            conn.execute(
                """INSERT INTO content_governance_versions
                (id, content_type, item_id, version, payload_json, payload_hash,
                 metadata_json, status, created_by, created_at, updated_at)
                VALUES (?, 'training_card', 'emotion_naming', ?, ?, ?, ?, 'approved', 'content-author', ?, ?)""",
                (version_id, suffix, database.json_dumps(payload), service._hash(payload), database.json_dumps(metadata), now, now),
            )
            for discipline, reviewer in (("research", "r1"), ("psychology", "r2"), ("ethics", "r3"), ("content", "r4")):
                conn.execute(
                    """INSERT INTO content_governance_reviews
                    (id, version_id, discipline, decision, reviewer_id, reviewer_role, evidence_path, created_at)
                    VALUES (?, ?, ?, 'approved', ?, 'reviewer', ?, ?)""",
                    (f"review-{suffix}-{discipline}", version_id, discipline, reviewer, f"evidence/{discipline}.md", now),
                )
            conn.commit()
        return service, database, version_id


def _publish(service, version_id):
    return service.publish_version(
        {"id": "content-owner", "role": "admin"},
        version_id,
        {
            "confirm_publish": True,
            "expected_hash": service.get_version(version_id)["payload_hash"],
            "dependency_impact_confirmed": True,
            "release_reason": "F17 合成发布",
        },
    )


def test_f17_migrations_and_policy_freeze_immutable_storage_contract(tmp_path, monkeypatch):
    app, _ = _fresh_app(tmp_path, monkeypatch)
    with app.app_context():
        database = importlib.import_module("database")
        migrations = importlib.import_module("services.schema_migration_service")
        with database.get_connection() as conn:
            tables = {row["name"] for row in database.list_database_tables(conn)}
            assert {"content_release_artifacts", "content_active_artifacts"} <= tables
            versions = [migration.version for migration in migrations.MIGRATIONS]
            assert versions.index("2026_08_25_072") == versions.index("2026_08_25_071") + 1
    policy = json.loads((ROOT / "config/rc0810/content_artifact_policy.json").read_text(encoding="utf-8"))
    assert policy["container_filesystem"] == "read_only"
    assert policy["production_gate_eligible"] is False


def test_publish_persists_full_immutable_artifact_without_writing_container(tmp_path, monkeypatch):
    app, content_dir = _fresh_app(tmp_path, monkeypatch)
    source_before = (content_dir / "training_cards.json").read_bytes()
    service, database, version_id = _approved_version(app, "v2")
    with app.app_context():
        release = _publish(service, version_id)
        active = database.load_content_json("training_cards.json")
        assert next(item for item in active["cards"] if item["id"] == "emotion_naming")["title"] == "不可变内容 v2"
        assert release["package"]["reviewers"]
        assert release["package"]["artifact_hash"] == release["artifact_hash"]
    assert (content_dir / "training_cards.json").read_bytes() == source_before


def test_two_connections_and_cache_restart_read_same_active_pointer(tmp_path, monkeypatch):
    app, _ = _fresh_app(tmp_path, monkeypatch)
    service, database, version_id = _approved_version(app, "restart")
    with app.app_context():
        release = _publish(service, version_id)
        with database.get_connection() as first, database.get_connection() as second:
            one = first.execute("SELECT artifact_id, generation FROM content_active_artifacts WHERE filename = 'training_cards.json'").fetchone()
            two = second.execute("SELECT artifact_id, generation FROM content_active_artifacts WHERE filename = 'training_cards.json'").fetchone()
            assert dict(one) == dict(two) == {"artifact_id": release["artifact_id"], "generation": 1}
        database.clear_content_artifact_cache()
        assert database.load_content_json("training_cards.json")["cards"]


def test_compare_and_swap_rejects_stale_concurrent_pointer(tmp_path, monkeypatch):
    app, _ = _fresh_app(tmp_path, monkeypatch)
    service, database, version_id = _approved_version(app, "cas")
    with app.app_context():
        _publish(service, version_id)
        _, _, stale_version_id = _approved_version(app, "cas-stale")
        stale_version = service.get_version(stale_version_id)
        stale_document = service._build_artifact_document(
            stale_version["content_type"], stale_version["item_id"], stale_version["payload"]
        )
        _, _, winning_version_id = _approved_version(app, "cas-winner")
        winner = _publish(service, winning_version_id)
        monkeypatch.setattr(service, "_build_artifact_document", lambda *args: stale_document)
        with pytest.raises(service.GovernanceError, match="active") as error:
            _publish(service, stale_version_id)
        assert error.value.code == "content_release_conflict"
        with database.get_connection() as conn:
            pointer = conn.execute("SELECT artifact_id FROM content_active_artifacts WHERE filename = 'training_cards.json'").fetchone()
            assert pointer["artifact_id"] == winner["artifact_id"]


def test_artifact_store_failure_leaves_active_pointer_unchanged(tmp_path, monkeypatch):
    app, _ = _fresh_app(tmp_path, monkeypatch)
    service, database, first_id = _approved_version(app, "stable")
    with app.app_context():
        first = _publish(service, first_id)
        _, _, second_id = _approved_version(app, "failure")
        monkeypatch.setattr(service, "_store_artifact", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("synthetic object store failure")))
        with pytest.raises(RuntimeError, match="object store failure"):
            _publish(service, second_id)
        with database.get_connection() as conn:
            pointer = conn.execute("SELECT artifact_id FROM content_active_artifacts WHERE filename = 'training_cards.json'").fetchone()
            assert pointer["artifact_id"] == first["artifact_id"]


def test_cache_key_tracks_new_artifact_hash_instead_of_stale_payload(tmp_path, monkeypatch):
    app, _ = _fresh_app(tmp_path, monkeypatch)
    service, database, first_id = _approved_version(app, "cache-a")
    with app.app_context():
        _publish(service, first_id)
        first = database.load_content_json("training_cards.json")
        _, _, second_id = _approved_version(app, "cache-b")
        _publish(service, second_id)
        second = database.load_content_json("training_cards.json")
        assert first != second
        assert next(item for item in second["cards"] if item["id"] == "emotion_naming")["title"] == "不可变内容 cache-b"


def test_restore_switches_only_to_verified_old_artifact(tmp_path, monkeypatch):
    app, _ = _fresh_app(tmp_path, monkeypatch)
    service, database, first_id = _approved_version(app, "old")
    with app.app_context():
        first = _publish(service, first_id)
        _, _, second_id = _approved_version(app, "new")
        _publish(service, second_id)
        restored = service.change_release_state({"id": "content-owner", "role": "admin"}, first["release_id"], "restore", {"confirm_action": True, "reason": "合成回滚"})
        assert restored["artifact_id"] == first["artifact_id"]
        active = database.load_content_json("training_cards.json")
        assert next(item for item in active["cards"] if item["id"] == "emotion_naming")["title"] == "不可变内容 old"


def test_hash_tamper_fails_closed_and_never_falls_back_to_container(tmp_path, monkeypatch):
    app, _ = _fresh_app(tmp_path, monkeypatch)
    service, database, version_id = _approved_version(app, "tamper")
    with app.app_context():
        release = _publish(service, version_id)
        with database.get_connection() as conn:
            conn.execute("UPDATE content_release_artifacts SET payload_text = '{}' WHERE id = ?", (release["artifact_id"],))
            conn.commit()
        database.clear_content_artifact_cache()
        with pytest.raises(database.ContentArtifactIntegrityError):
            database.load_content_json("training_cards.json")


def test_invalid_item_reference_is_rejected_before_active_switch(tmp_path, monkeypatch):
    app, _ = _fresh_app(tmp_path, monkeypatch)
    service, database, stable_id = _approved_version(app, "valid")
    with app.app_context():
        stable = _publish(service, stable_id)
        _, _, invalid_id = _approved_version(app, "invalid", payload_id="different-card")
        with pytest.raises(service.GovernanceError) as error:
            _publish(service, invalid_id)
        assert error.value.code == "content_reference_invalid"
        with database.get_connection() as conn:
            pointer = conn.execute("SELECT artifact_id FROM content_active_artifacts WHERE filename = 'training_cards.json'").fetchone()
            assert pointer["artifact_id"] == stable["artifact_id"]
