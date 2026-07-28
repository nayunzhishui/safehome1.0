import importlib
import json
import shutil
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
CONTENT = ROOT / "content"


def _app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    content_dir = tmp_path / "content"
    shutil.copytree(CONTENT, content_dir)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "b03.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    return importlib.import_module("app").app, content_dir


def _actors(app):
    specs = [
        ("researcher-b03", "researcher"),
        ("supervisor-b03", "supervisor"),
        ("parent-b03", "parent"),
    ]
    with app.app_context():
        database = importlib.import_module("database")
        auth_utils = importlib.import_module("routes.auth_utils")
        with database.get_connection() as conn:
            now = database.now_iso()
            for actor_id, role in specs:
                conn.execute(
                    """
                    INSERT INTO users (
                        id, nickname, role, source, status, created_at, updated_at
                    ) VALUES (?, ?, ?, 'test', 'active', ?, ?)
                    """,
                    (actor_id, actor_id, role, now, now),
                )
            conn.commit()
        actors = {
            actor_id: {"id": actor_id, "role": role}
            for actor_id, role in specs
        }
        headers = {
            actor_id: {
                "Authorization": "Bearer "
                + auth_utils.generate_auth_token(
                    {"id": actor_id, "role": role}
                )
            }
            for actor_id, role in specs
        }
    return actors, headers


def _context(actor, **overrides):
    value = {
        "permission_granted": True,
        "consent_active": True,
        "recipient_matches_scope": True,
        "source_authorized": True,
        "language_checked": True,
        "responsible_role": actor["role"],
        "publisher_id": actor["id"],
        "author_id": actor["id"],
        "reviewer_id": "",
        "human_reviewed": False,
        "risk_level": "low",
        "high_risk_reviewed": False,
        "ordinary_training_path": False,
        "multi_party": False,
    }
    value.update(overrides)
    return value


def _evaluate(conn, service, actor, key, *, content="请在方便时查看。", sources=None, context=None):
    return service.evaluate_candidate(
        conn,
        actor,
        channel="researcher_message",
        subject_type="relationship_pilot_enrollment",
        subject_id=f"enrollment-{key}",
        recipient_user_id="parent-b03",
        content={"title": "提醒", "body": content},
        source_refs=(
            sources
            if sources is not None
            else [f"relationship_pilot_enrollment:enrollment-{key}"]
        ),
        idempotency_key=key,
        context=context or _context(actor),
    )


def test_each_gate_blocks_explains_and_can_recover(tmp_path, monkeypatch):
    app, _ = _app(tmp_path, monkeypatch)
    actors, _ = _actors(app)
    researcher = actors["researcher-b03"]
    supervisor = actors["supervisor-b03"]
    with app.app_context():
        database = importlib.import_module("database")
        service = importlib.import_module("services.publication_gate_service")
        cases = [
            ("minimum_input", {"content": ""}),
            (
                "permission",
                {"context": _context(researcher, permission_granted=False)},
            ),
            ("source", {"sources": []}),
            ("language", {"content": "你就是控制型人格。"}),
            (
                "responsibility",
                {"context": _context(researcher, publisher_id="other")},
            ),
        ]
        blocked = []
        with database.get_connection() as conn:
            for index, (gate_name, changes) in enumerate(cases):
                candidate = _evaluate(
                    conn,
                    service,
                    researcher,
                    f"gate-{index}",
                    **changes,
                )
                assert candidate["status"] == "blocked"
                assert candidate["blocked_gate"] == gate_name
                assert candidate["reason_code"]
                blocked.append(candidate)
            conn.commit()

        for index, candidate in enumerate(blocked):
            recovered = service.recover_candidate(
                supervisor,
                candidate["id"],
                {
                    "expected_version": 1,
                    "content": {"title": "提醒", "body": "请在方便时查看。"},
                    "source_refs": [
                        f"relationship_pilot_enrollment:enrollment-gate-{index}"
                    ],
                    "context": _context(
                        supervisor,
                        author_id="researcher-b03",
                    ),
                },
                f"recover-{index}",
            )
            assert recovered["status"] == "approved"
            assert recovered["blocked_gate"] is None
            assert recovered["version"] == 2

        with pytest.raises(service.PublicationGateError) as stale:
            service.recover_candidate(
                supervisor,
                blocked[0]["id"],
                {
                    "expected_version": 1,
                    "context": _context(supervisor),
                },
                "recover-stale",
            )
        assert stale.value.code == "publication_version_conflict"

        withdrawn = service.withdraw_candidate(
            supervisor,
            blocked[0]["id"],
            {"expected_version": 2, "reason": "测试撤回"},
            "withdraw-0",
        )
        assert withdrawn["status"] == "withdrawn"
        assert withdrawn["version"] == 3


def test_high_risk_multi_party_ai_and_showcase_flags_cannot_bypass(tmp_path, monkeypatch):
    app, _ = _app(tmp_path, monkeypatch)
    actors, _ = _actors(app)
    researcher = actors["researcher-b03"]
    parent = actors["parent-b03"]
    with app.app_context():
        database = importlib.import_module("database")
        service = importlib.import_module("services.publication_gate_service")
        with database.get_connection() as conn:
            showcase = _evaluate(
                conn,
                service,
                researcher,
                "showcase-bypass",
                context=_context(
                    researcher,
                    permission_granted=False,
                    temporary_showcase_bypass=True,
                ),
            )
            high_risk = _evaluate(
                conn,
                service,
                researcher,
                "high-risk",
                context=_context(
                    researcher,
                    risk_level="high",
                    ordinary_training_path=True,
                ),
            )
            multi_party = _evaluate(
                conn,
                service,
                researcher,
                "multi-party",
                context=_context(researcher, multi_party=True),
            )
            ai_candidate = service.evaluate_candidate(
                conn,
                parent,
                channel="ai_candidate",
                subject_type="ai_qa_session",
                subject_id="session-b03",
                recipient_user_id=parent["id"],
                content="这里是一条带来源的支持性候选。",
                source_refs=["content_governance_version:v1"],
                idempotency_key="ai-bypass",
                context={
                    **_context(
                        parent,
                        responsible_role="ai_safety_pipeline",
                        author_id="provider:fake",
                    ),
                    "safety_checked": False,
                    "formal_feedback_write_allowed": False,
                    "rules_or_ai_bypass": True,
                },
            )
            conn.commit()
        assert showcase["blocked_gate"] == "permission"
        assert high_risk["blocked_gate"] == "responsibility"
        assert multi_party["blocked_gate"] == "responsibility"
        assert ai_candidate["blocked_gate"] == "responsibility"


def test_approved_candidate_is_idempotent_publishable_and_audited(tmp_path, monkeypatch):
    app, _ = _app(tmp_path, monkeypatch)
    actors, headers = _actors(app)
    researcher = actors["researcher-b03"]
    with app.app_context():
        database = importlib.import_module("database")
        service = importlib.import_module("services.publication_gate_service")
        with database.get_connection() as conn:
            first = _evaluate(conn, service, researcher, "publish-once")
            replay = _evaluate(conn, service, researcher, "publish-once")
            assert first["id"] == replay["id"]
            service.assert_candidate_approved(first)
            published = service.mark_published(conn, first["id"], researcher)
            repeated = service.mark_published(conn, first["id"], researcher)
            conn.commit()
            gate_count = conn.execute(
                "SELECT COUNT(*) AS count FROM publication_gate_checks WHERE candidate_id = ?",
                (first["id"],),
            ).fetchone()["count"]
            actions = {
                row["action"]
                for row in conn.execute(
                    "SELECT action FROM audit_logs WHERE target_id = ?",
                    (first["id"],),
                ).fetchall()
            }
        assert published["status"] == "published"
        assert repeated["version"] == published["version"]
        assert gate_count == 5
        assert {"publication_gate_approved"} <= actions

    client = app.test_client()
    visible = client.get(
        "/api/therapeutic-assessment/publication-candidates",
        headers=headers["researcher-b03"],
    )
    forbidden = client.get(
        "/api/therapeutic-assessment/publication-candidates",
        headers=headers["parent-b03"],
    )
    assert visible.status_code == 200
    assert visible.get_json()["data"]["count"] == 1
    assert forbidden.status_code == 403


def test_policy_and_schema_are_fail_closed(tmp_path, monkeypatch):
    app, content_dir = _app(tmp_path, monkeypatch)
    _actors(app)
    policy = json.loads(
        (content_dir / "publication_gate_policy.json").read_text(encoding="utf-8")
    )
    assert set(policy["five_gates"]) == {
        "minimum_input",
        "permission",
        "source",
        "language",
        "responsibility",
    }
    assert policy["temporary_showcase_bypass_changes_write_permission"] is False
    assert policy["rules_or_ai_can_bypass_server_gate"] is False
    assert policy["production_release_approved"] is False
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            tables = {
                row["name"]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
        assert {
            "publication_candidates",
            "publication_gate_checks",
            "publication_candidate_events",
        } <= tables
        assert database.CURRENT_SCHEMA_VERSION == "2026_07_28_049"
