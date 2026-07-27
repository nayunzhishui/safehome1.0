import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(("routes.", "services.")):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task38-f03.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def _seed(app):
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token

        now = now_iso()
        users = {"parent-f03": "parent", "researcher-f03": "researcher", "supervisor-f03": "supervisor"}
        with get_connection() as conn:
            for actor_id, role in users.items():
                conn.execute(
                    "INSERT INTO users (id, nickname, role, status, created_at, updated_at) VALUES (?, ?, ?, 'active', ?, ?)",
                    (actor_id, actor_id, role, now, now),
                )
            conn.commit()
        return {
            role: {"Authorization": f"Bearer {generate_auth_token({'id': actor_id, 'role': role})}"}
            for actor_id, role in users.items()
        }


def _case(client, headers):
    response = client.post(
        "/api/therapeutic-assessment/cases",
        headers={**headers["parent"], "Idempotency-Key": "f03-case"},
        json={"assessment_question": "我想理解一次沟通", "shared_scope": ["question"], "consent": True},
    )
    return response.get_json()["data"]


def _post(client, headers, case_id, payload, key):
    return client.post(
        f"/api/therapeutic-assessment/cases/{case_id}/evidence",
        headers={**headers, "Idempotency-Key": key},
        json=payload,
    )


def test_schema_032_adds_evidence_ledger(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    with app.app_context():
        from database import CURRENT_SCHEMA_NAME, CURRENT_SCHEMA_VERSION, get_connection

        with get_connection() as conn:
            tables = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "therapeutic_assessment_evidence_items" in tables
        assert CURRENT_SCHEMA_VERSION == "2026_07_27_032"
        assert CURRENT_SCHEMA_NAME == "therapeutic_assessment_evidence_ledger"


def test_observation_requires_source_context_and_visibility(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    invalid = _post(client, headers["parent"], case["id"], {"kind": "O", "content": "我停了一下"}, "f03-o-invalid")
    valid = _post(
        client,
        headers["parent"],
        case["id"],
        {
            "kind": "O",
            "content": "对话中我停顿了几秒",
            "source_ref": "diary:1",
            "provider_id": "parent-f03",
            "observed_at": "2026-07-27T10:00:00+08:00",
            "context": "一次具体对话",
            "visibility_scope": ["participant", "research_team"],
        },
        "f03-o-valid",
    )
    assert invalid.status_code == 400
    assert valid.status_code == 201
    assert valid.get_json()["data"]["kind"] == "O"


def test_pattern_requires_two_distinct_evidence_sources(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    payload = {
        "kind": "P",
        "content": "在两次类似场景中都出现停顿",
        "source_origin": "human",
        "applicability_scope": "相似对话",
        "exceptions": ["其它场景尚不清楚"],
        "time_window": "最近两周",
        "supporting_evidence": [
            {"ref": "diary:1", "source": "diary"},
            {"ref": "diary:2", "source": "diary"}
        ],
        "visibility_scope": ["research_team"],
    }
    response = _post(client, headers["supervisor"], case["id"], payload, "f03-p")
    assert response.status_code == 201


def test_ai_cannot_create_h_and_h_requires_counterevidence(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    base = {
        "kind": "H",
        "content": "这是一个待共同核对的人工假设",
        "question_link": case["id"],
        "supporting_evidence": [{"ref": "diary:1", "source": "diary"}],
        "counter_evidence": ["也有能够继续表达的时刻"],
        "alternative_explanations": ["当时可能只是疲劳"],
        "falsification_criteria": ["若其它相似对话并未出现则需修订"],
        "protective_function": "暂时降低冲突强度",
        "cost": "可能减少表达机会",
        "participant_recognition": "unconfirmed",
        "visibility_scope": ["research_team"],
    }
    ai = _post(client, headers["supervisor"], case["id"], {**base, "source_origin": "ai"}, "f03-h-ai")
    missing = _post(
        client,
        headers["supervisor"],
        case["id"],
        {**base, "source_origin": "human", "counter_evidence": []},
        "f03-h-missing",
    )
    valid = _post(client, headers["supervisor"], case["id"], {**base, "source_origin": "human"}, "f03-h-human")
    assert ai.status_code == 409
    assert missing.status_code == 400
    assert valid.status_code == 201
    assert valid.get_json()["data"]["review_status"] == "draft"
    evidence = valid.get_json()["data"]
    reviewed = client.post(
        f"/api/therapeutic-assessment/evidence/{evidence['id']}/review",
        headers={**headers["supervisor"], "Idempotency-Key": "f03-h-review"},
        json={"decision": "approved", "expected_version": evidence["version"]},
    )
    assert reviewed.status_code == 200
    assert reviewed.get_json()["data"]["review_status"] == "human_reviewed"


def test_participant_cannot_see_unreviewed_h(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    created = _post(
        client,
        headers["supervisor"],
        case["id"],
        {
            "kind": "H",
            "content": "内部人工假设草稿",
            "question_link": case["id"],
            "supporting_evidence": [{"ref": "diary:1", "source": "diary"}],
            "counter_evidence": ["存在不同表现"],
            "alternative_explanations": ["情境压力"],
            "falsification_criteria": ["新资料不支持时修订"],
            "protective_function": "减少压力",
            "cost": "降低表达",
            "participant_recognition": "unconfirmed",
            "source_origin": "human",
            "visibility_scope": ["participant", "research_team"],
        },
        "f03-hidden-h",
    )
    assert created.status_code == 201
    listed = client.get(f"/api/therapeutic-assessment/cases/{case['id']}/evidence", headers=headers["parent"])
    assert listed.status_code == 200
    assert listed.get_json()["data"]["items"] == []
