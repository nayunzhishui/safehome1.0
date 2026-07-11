import importlib
import json
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_app(tmp_path):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    os.environ["DATABASE_PATH"] = str(tmp_path / "safehome-test.sqlite3")
    os.environ["CONTENT_DIR"] = str(PROJECT_ROOT / "content")
    os.environ.pop("APP_ENV", None)
    module = importlib.import_module("app")
    return module.app


def _wechat_login(client, code: str):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code})
    assert response.status_code == 200
    data = response.get_json()["data"]
    return data["user"]["id"], data["token"]


def test_admin_export_writes_audit_log_after_success(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    response = client.get("/api/admin/export?type=diaries", headers={"X-Admin-Token": "safehome-local-admin-token"})

    assert response.status_code == 200

    import database

    with database.get_connection() as conn:
        audit = conn.execute(
            """
            SELECT action, actor_id, target_type, target_id, metadata_json
            FROM audit_logs
            WHERE action = 'export_diaries'
            """
        ).fetchone()

    assert audit is not None
    assert audit["actor_id"] == "admin-token"
    assert audit["target_type"] == "export"
    assert audit["target_id"] == "diaries"
    metadata = json.loads(audit["metadata_json"])
    assert metadata["type"] == "diaries"
    assert metadata["row_count"] == 0
    assert metadata["limit"] == 1000
    assert metadata["row_count_before_limit"] == 0
    assert metadata["row_count_exported"] == 0


def test_unauthorized_admin_export_does_not_write_audit_log(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    response = client.get("/api/admin/export?type=diaries", headers={"X-Admin-Token": "wrong-token"})

    assert response.status_code == 401

    import database

    with database.get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) AS count FROM audit_logs").fetchone()["count"]

    assert count == 0


def test_admin_export_rejects_limit_over_max(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    response = client.get(
        "/api/admin/export?type=diaries&limit=5001",
        headers={"X-Admin-Token": "safehome-local-admin-token"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_export_limit"


def test_admin_export_limit_applies_and_audit_records_counts(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    for scene in ["作业拖延", "睡前冲突"]:
        create_response = client.post(
            "/api/goals",
            json={"user_id": "parent-export-limit", "scene": scene, "smart_goal": "先记录一次具体事件"},
        )
        assert create_response.status_code == 201

    response = client.get(
        "/api/admin/export?type=goals&limit=1",
        headers={"X-Admin-Token": "safehome-local-admin-token"},
    )

    assert response.status_code == 200
    csv_lines = [line for line in response.get_data(as_text=True).splitlines() if line.strip()]
    assert len(csv_lines) == 2

    import database

    with database.get_connection() as conn:
        audit = conn.execute(
            """
            SELECT metadata_json FROM audit_logs
            WHERE action = 'export_goals'
            ORDER BY created_at DESC
            LIMIT 1
            """
        ).fetchone()

    metadata = json.loads(audit["metadata_json"])
    assert metadata["limit"] == 1
    assert metadata["row_count_before_limit"] == 2
    assert metadata["row_count_exported"] == 1


def test_assessment_export_only_includes_active_assessment_ids(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    user_id, token = _wechat_login(client, "assessment-export-filter")

    active_response = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "user_id": user_id,
            "worksheet_id": "student_profile_v1",
            "answers": [
                {"question_id": question_id, "value": "2"}
                for question_id in ["test_anxiety", "iu_score", "fear_score", "self_compassion"]
            ],
        },
    )
    assert active_response.status_code == 201

    import database

    with database.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO assessment_results (
                id, user_id, worksheet_id, worksheet_title, category,
                answers_json, scores_json, total_score, result_summary, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy_export_assessment_result",
                user_id,
                "worksheet_3_1_anxiety",
                "工作表3.1：总体焦虑水平及干扰程度量表",
                "量表类",
                database.json_dumps([]),
                database.json_dumps({}),
                None,
                "旧版自建工作表记录",
                database.now_iso(),
            ),
        )
        conn.commit()

    response = client.get(
        "/api/admin/export?type=assessments",
        headers={"X-Admin-Token": "safehome-local-admin-token"},
    )

    assert response.status_code == 200
    csv_text = response.get_data(as_text=True)
    assert "student_profile_v1" in csv_text
    assert "worksheet_3_1_anxiety" not in csv_text
