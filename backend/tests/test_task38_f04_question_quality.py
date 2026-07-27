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
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "f04.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def _seed(app):
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token
        now = now_iso()
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO users (id, nickname, role, status, created_at, updated_at) VALUES ('p-f04', 'p', 'parent', 'active', ?, ?)",
                (now, now),
            )
            conn.commit()
        return {"Authorization": f"Bearer {generate_auth_token({'id': 'p-f04', 'role': 'parent'})}"}


def _case(client, headers):
    result = client.post(
        "/api/therapeutic-assessment/cases",
        headers={**headers, "Idempotency-Key": "f04-case"},
        json={"assessment_question": "我想理解这次为什么会退开", "shared_scope": ["question"], "consent": True},
    )
    return result.get_json()["data"]


def _update(client, headers, case, payload, key):
    return client.patch(
        f"/api/therapeutic-assessment/cases/{case['id']}/question",
        headers={**headers, "Idempotency-Key": key},
        json={"expected_version": case["version"], **payload},
    )


def test_schema_033_and_original_question_is_immutable(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    revised = _update(client, headers, case, {"action": "revise", "working_question": "我想探索这次退开前发生了什么"}, "f04-revise")
    assert revised.status_code == 200
    data = revised.get_json()["data"]
    assert data["assessment_question"] == "我想理解这次为什么会退开"
    assert data["working_question"] == "我想探索这次退开前发生了什么"
    with app.app_context():
        from database import CURRENT_SCHEMA_VERSION
        assert CURRENT_SCHEMA_VERSION >= "2026_07_27_038"


def test_candidates_do_not_count_as_acceptance_and_none_fit_is_explicit(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    generated = _update(client, headers, case, {"action": "generate_candidates"}, "f04-generate")
    data = generated.get_json()["data"]
    assert len(data["question_candidates"]) == 2
    assert data["candidate_decision"] == "unreviewed"
    none_fit = _update(client, headers, data, {"action": "none_fit"}, "f04-none")
    assert none_fit.get_json()["data"]["candidate_decision"] == "none_fit"


def test_quality_rubric_and_best_guess_are_non_conclusive(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    revised = _update(
        client,
        headers,
        case,
        {
            "action": "revise",
            "working_question": "我想探索这次对话中自己退开前发生了什么，也允许暂时不确定",
            "best_guess": "也许当时压力较高",
        },
        "f04-quality",
    )
    data = revised.get_json()["data"]
    assert set(data["question_quality"]) == {
        "personal_concern", "explorable", "non_blame", "evidence_responsive", "allows_uncertainty"
    }
    assert data["best_guess_notice"] == "最好猜测不是结论，可以随新资料修订或删除。"


def test_pause_delete_and_noop_are_explicit(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    case = _case(client, headers)
    noop = _update(client, headers, case, {"action": "submit"}, "f04-noop")
    paused = _update(client, headers, case, {"action": "pause"}, "f04-pause")
    deleted = _update(client, headers, paused.get_json()["data"], {"action": "delete"}, "f04-delete")
    assert noop.status_code == 409
    assert paused.get_json()["data"]["question_status"] == "paused"
    assert deleted.get_json()["data"]["question_status"] == "deleted"
