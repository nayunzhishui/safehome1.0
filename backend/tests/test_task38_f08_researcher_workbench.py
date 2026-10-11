import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(("routes.", "services.")):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "f08.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def _seed(app):
    roles = {
        "p-f08": "parent",
        "r-f08": "researcher",
        "r2-f08": "researcher",
        "s-f08": "supervisor",
    }
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token
        now = now_iso()
        with get_connection() as conn:
            for user_id, role in roles.items():
                conn.execute(
                    "INSERT INTO users (id, nickname, role, status, created_at, updated_at) VALUES (?, ?, ?, 'active', ?, ?)",
                    (user_id, user_id, role, now, now),
                )
            conn.execute(
                """
                INSERT INTO therapeutic_assessment_authorizations (
                    id, user_id, competency_level, task_code, scope_json,
                    supervisor_user_id, evidence_ref, starts_at, expires_at,
                    status, version, granted_by, created_at, updated_at
                ) VALUES ('auth-f08-workbench', 'r-f08', 'T1', 'workbench_draft', ?,
                    's-f08', 'test-evidence:f08', ?, '2099-01-01T00:00:00+00:00',
                    'active', 1, 's-f08', ?, ?)
                """,
                ('{"complexity_scopes":["individual_adult_low_risk"]}', now, now, now),
            )
            conn.execute(
                """
                INSERT INTO therapeutic_assessment_authorizations (
                    id, user_id, competency_level, task_code, scope_json,
                    supervisor_user_id, evidence_ref, starts_at, expires_at,
                    status, version, granted_by, created_at, updated_at
                ) VALUES ('auth-f08-evidence', 'r-f08', 'T1', 'evidence_organize', ?,
                    's-f08', 'test-evidence:f08-evidence', ?, '2099-01-01T00:00:00+00:00',
                    'active', 1, 's-f08', ?, ?)
                """,
                ('{"complexity_scopes":["individual_adult_low_risk"]}', now, now, now),
            )
            conn.commit()
        return {
            user_id: {"Authorization": f"Bearer {generate_auth_token({'id': user_id, 'role': role})}"}
            for user_id, role in roles.items()
        }


def _case(client, headers):
    created = client.post(
        "/api/therapeutic-assessment/cases",
        headers={**headers["p-f08"], "Idempotency-Key": "f08-case"},
        json={"assessment_question": "我想理解一次退开的沟通", "shared_scope": ["question"], "consent": True},
    )
    case = created.get_json()["data"]
    with client.application.app_context():
        from database import get_connection, now_iso

        timestamp = now_iso()
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO therapeutic_assessment_work_queue (
                id, case_id, queue_type, task_code, required_competency,
                priority, status, scope_snapshot_json, assigned_user_id,
                claimed_at, due_at, version, created_by, created_at, updated_at
                ) VALUES (?, ?, 'supervision', 'workbench_draft', 'T3',
                          'normal', 'claimed', '{}', 's-f08',
                          ?, '2099-01-01T00:00:00+00:00', 1, 's-f08', ?, ?)""",
                (f"queue-{case['id']}", case["id"], timestamp, timestamp, timestamp),
            )
            conn.commit()
    assigned = client.post(
        f"/api/therapeutic-assessment/cases/{case['id']}/assign",
        headers={**headers["s-f08"], "Idempotency-Key": "f08-assign"},
        json={"researcher_id": "r-f08"},
    )
    assert created.status_code == 201
    assert assigned.status_code == 200
    return assigned.get_json()["data"]


def _observation(client, headers, case_id, key="f08-o"):
    return client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/evidence",
        headers={**headers["r-f08"], "Idempotency-Key": key},
        json={
            "kind": "O",
            "content": "参与者在一次对话中停顿了几秒",
            "source_ref": f"diary:{key}",
            "provider_id": "p-f08",
            "observed_at": "2026-07-27T10:00:00+08:00",
            "context": "一次具体对话",
            "method_limitations": "单次自述，只说明当时情境。",
            "visibility_scope": ["participant", "research_team"],
        },
    )


def test_schema_037_adds_workbench_and_method_limitations(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    with app.app_context():
        from database import CURRENT_SCHEMA_NAME, CURRENT_SCHEMA_VERSION, get_connection
        with get_connection() as conn:
            tables = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(therapeutic_assessment_evidence_items)")}
        assert {
            "therapeutic_assessment_researcher_workbench_drafts",
            "therapeutic_assessment_researcher_workbench_draft_events",
        }.issubset(tables)
        assert "method_limitations" in columns
        assert CURRENT_SCHEMA_VERSION >= "2026_07_27_038"
        assert CURRENT_SCHEMA_NAME


def test_workbench_enforces_object_scope_and_audits_sensitive_read(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    assert _observation(client, headers, case["id"]).status_code == 201

    participant = client.get(
        f"/api/therapeutic-assessment/cases/{case['id']}/researcher-workbench",
        headers=headers["p-f08"],
    )
    other_researcher = client.get(
        f"/api/therapeutic-assessment/cases/{case['id']}/researcher-workbench",
        headers=headers["r2-f08"],
    )
    allowed = client.get(
        f"/api/therapeutic-assessment/cases/{case['id']}/researcher-workbench?kind=O&page_size=1",
        headers=headers["r-f08"],
    )
    assert participant.status_code == 403
    assert other_researcher.status_code == 403
    assert allowed.status_code == 200
    body = allowed.get_json()["data"]
    assert body["evidence_items"][0]["method_limitations"] == "单次自述，只说明当时情境。"
    with app.app_context():
        from database import get_connection
        with get_connection() as conn:
            audit = conn.execute(
                "SELECT metadata_json FROM audit_logs WHERE action = 'therapeutic_assessment_workbench_viewed'"
            ).fetchone()
        assert audit is not None


def test_workbench_summary_uses_full_authorized_case_not_current_filter(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    created = client.post(
        "/api/therapeutic-assessment/cases",
        headers={**headers["p-f08"], "Idempotency-Key": "f08-summary-case"},
        json={"assessment_question": "我想理解一次退开的沟通", "shared_scope": ["question"], "consent": True},
    )
    case = created.get_json()["data"]
    with app.app_context():
        from database import get_connection
        with get_connection() as conn:
            conn.execute(
                "UPDATE therapeutic_assessment_cases SET assigned_researcher_id = 'r-f08' WHERE id = ?",
                (case["id"],),
            )
            conn.commit()
    assert _observation(client, headers, case["id"], "f08-summary-o1").status_code == 201
    assert _observation(client, headers, case["id"], "f08-summary-o2").status_code == 201

    response = client.get(
        f"/api/therapeutic-assessment/cases/{case['id']}/researcher-workbench?kind=U&page_size=1",
        headers=headers["r-f08"],
    )
    body = response.get_json()["data"]
    assert response.status_code == 200
    assert body["evidence_items"] == []
    assert body["evidence_total"] == 0
    assert body["evidence_summary"]["item_count"] == 2
    assert body["evidence_summary"]["kind_counts"]["O"] == 2
    assert body["evidence_summary"]["source_count"] == 2


def test_miniprogram_surfaces_evidence_summary_for_both_roles():
    participant_js = (ROOT / "apps/miniprogram/pages/therapeutic-assessment/index.js").read_text(encoding="utf-8")
    participant_wxml = (ROOT / "apps/miniprogram/pages/therapeutic-assessment/index.wxml").read_text(encoding="utf-8")
    researcher_js = (ROOT / "apps/miniprogram/pages/researcher-dashboard/index.js").read_text(encoding="utf-8")
    researcher_wxml = (ROOT / "apps/miniprogram/pages/researcher-dashboard/index.wxml").read_text(encoding="utf-8")
    assert "evidenceSummary" in participant_js
    assert "evidenceSummary" in participant_wxml
    assert "evidence_summary" in researcher_js
    assert "evidence_summary" in researcher_wxml


def test_draft_is_recoverable_versioned_idempotent_and_separated(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    endpoint = f"/api/therapeutic-assessment/cases/{case['id']}/researcher-workbench/draft"
    payload = {
        "internal_notes": "仅供研究团队核对的内部备注",
        "participant_visible_draft": "这份理解可以和你一起核对，也可以不同意。",
        "filters": {"kind": "O", "visibility": "research_team"},
        "expected_version": 0,
    }
    first = client.put(endpoint, headers={**headers["r-f08"], "Idempotency-Key": "f08-draft-1"}, json=payload)
    replay = client.put(endpoint, headers={**headers["r-f08"], "Idempotency-Key": "f08-draft-1"}, json=payload)
    conflict = client.put(
        endpoint,
        headers={**headers["r-f08"], "Idempotency-Key": "f08-draft-2"},
        json={**payload, "expected_version": 0},
    )
    restored = client.get(
        f"/api/therapeutic-assessment/cases/{case['id']}/researcher-workbench",
        headers=headers["r-f08"],
    )
    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.get_json()["data"]["version"] == 1
    assert conflict.status_code == 409
    assert restored.get_json()["data"]["draft"]["internal_notes"] == payload["internal_notes"]
    assert restored.get_json()["data"]["draft"]["participant_visible_draft"] == payload["participant_visible_draft"]


def test_participant_case_never_exposes_internal_feedback_fields(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    with app.app_context():
        from database import get_connection, new_id, now_iso
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO therapeutic_assessment_feedback_versions (
                    id, case_id, version_no, author_id, source, status,
                    observations_json, evidence_json, alternatives_json, uncertainty,
                    next_step, human_discussion_json, participant_content, sent_at, created_at
                ) VALUES (?, ?, 1, 'r-f08', 'human', 'sent', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id("feedback"),
                    case["id"],
                    '["内部观察"]',
                    '["内部依据"]',
                    '["内部替代解释"]',
                    "内部不确定性",
                    "内部下一步",
                    '["内部讨论"]',
                    "参与者可以看到的文字",
                    now_iso(),
                    now_iso(),
                ),
            )
            conn.commit()
    detail = client.get(f"/api/therapeutic-assessment/cases/{case['id']}", headers=headers["p-f08"])
    version = detail.get_json()["data"]["feedback_versions"][0]
    assert detail.status_code == 200
    assert version["participant_content"] == "参与者可以看到的文字"
    assert not {"observations", "evidence", "alternatives", "human_discussion", "author_id", "uncertainty", "next_step"} & set(version)
