import importlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch, content_dir=None, app_env="validation"):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "showcase.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir or ROOT / "content"))
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("ALLOW_PRODUCTION_SQLITE", "1")
    monkeypatch.setenv("SECRET_KEY", "showcase-test-secret-key-that-is-long-enough")
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "showcase-admin-token")
    return importlib.import_module("app").app


def test_showcase_opens_programs_and_training_cards_in_validation(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    status = client.get("/api/showcase-access")
    programs = client.get("/api/programs")
    cards = client.get("/api/cards")

    assert status.status_code == 200
    assert status.get_json()["data"]["enabled"] is True
    assert len(programs.get_json()["data"]["items"]) == 3
    assert programs.get_json()["data"]["availability"]["status"] == "showcase_open"
    assert len(cards.get_json()["data"]["items"]) == 42


def test_close_script_restores_all_showcase_gates(tmp_path, monkeypatch):
    module_path = ROOT / "scripts" / "set_showcase_access.py"
    spec = importlib.util.spec_from_file_location("set_showcase_access", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    module.TARGET = tmp_path / "showcase_access.json"

    payload = module.set_mode(False)
    saved = json.loads(module.TARGET.read_text(encoding="utf-8"))

    assert payload["enabled"] is False
    assert saved["read_only_role_bypass"] is False
    assert saved["researcher_platform_full_access"] is False
    assert saved["open_programs"] is False
    assert saved["open_training_cards"] is False
    assert saved["open_courses"] is False


def test_assessment_result_has_direct_owner_scoped_endpoint(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    register = client.post(
        "/api/auth/register",
        json={"username": "showcase-parent", "password": "StrongPass123!", "role": "parent", "nickname": "展示家长"},
    )
    token = register.get_json()["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}
    worksheet = client.get("/api/assessments/emotion_regulation_erq").get_json()["data"]
    answers = [{"question_id": item["id"], "value": item["options"][0]["value"]} for item in worksheet["questions"]]
    created = client.post(
        "/api/assessment-results",
        headers=headers,
        json={"worksheet_id": worksheet["id"], "answers": answers},
    )
    result_id = created.get_json()["data"]["id"]

    direct = client.get(f"/api/assessment-results/{result_id}", headers=headers)

    assert direct.status_code == 200
    assert direct.get_json()["data"]["id"] == result_id
    assert direct.get_json()["data"]["worksheet_id"] == worksheet["id"]


def test_miniprogram_result_page_uses_direct_result_and_auxiliary_fallbacks():
    page = (ROOT / "apps/miniprogram/pages/assessment-result/index.js").read_text(encoding="utf-8")
    assert "api.getAssessmentResult(this.data.resultId)" in page
    assert "api.getAssessment(this.data.worksheetId).catch(() => null)" in page
    assert "api.listAssessmentResults({ limit: 20 })" not in page


def test_temporary_researcher_platform_full_access_allows_authenticated_parent_reads_and_writes(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    register = client.post(
        "/api/auth/register",
        json={"username": "showcase-test1", "password": "StrongPass123!", "role": "parent", "nickname": "Test1"},
    )
    token = register.get_json()["data"]["token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "X-SafeHome-Researcher-Workspace": "1",
    }
    wyd_register = client.post(
        "/api/auth/register",
        json={"username": "showcase-wyd", "password": "StrongPass123!", "role": "parent", "nickname": "wyd"},
    )
    wyd_data = wyd_register.get_json()["data"]
    wyd_headers = {"Authorization": f"Bearer {wyd_data['token']}"}
    wyd_user_id = wyd_data["user"]["id"]

    with app.app_context():
        from database import get_connection, now_iso

        with get_connection() as conn:
            timestamp = now_iso()
            conn.execute(
                """
                INSERT INTO relationship_pilot_enrollments (
                    id, user_id, assessment_result_id, worksheet_id, dimensions_json,
                    radar_features_json, profile_json, consent_scope, status,
                    review_status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, '[]', '[]', '{}', ?, 'enrolled', 'pending_review', ?, ?)
                """,
                (
                    "showcase-enrollment-wyd",
                    wyd_user_id,
                    "showcase-result-wyd",
                    "regulatory_focus_relationship_18",
                    "relationship_pilot_stage2_v1",
                    timestamp,
                    timestamp,
                ),
            )
            conn.commit()

    dashboard = client.get("/api/relationship-pilot/researcher/dashboard", headers=headers)
    note = client.post(
        "/api/relationship-pilot/enrollments/showcase-enrollment-wyd/notes",
        headers=headers,
        json={"note": "开发验证：普通账号临时使用研究者记录能力。"},
    )
    sent = client.post(
        "/api/messages",
        headers={**headers, "Idempotency-Key": "showcase-test1-to-wyd"},
        json={
            "enrollment_id": "showcase-enrollment-wyd",
            "title": "开发验证消息",
            "body": "这是一条用于验证临时研究者平台读写链路的消息。",
            "message_type": "researcher_message",
        },
    )
    received = client.get("/api/messages?page=1&page_size=50", headers=wyd_headers)

    assert dashboard.status_code == 200
    assert dashboard.get_json()["data"]["items"][0]["id"] == "showcase-enrollment-wyd"
    assert note.status_code == 201
    assert note.get_json()["data"]["note"] == "开发验证：普通账号临时使用研究者记录能力。"
    assert sent.status_code == 201
    assert received.status_code == 200
    assert received.get_json()["data"]["items"][0]["title"] == "开发验证消息"


def test_miniprogram_researcher_dashboard_labels_temporary_full_access():
    page_js = (ROOT / "apps/miniprogram/pages/researcher-dashboard/index.js").read_text(encoding="utf-8")
    page_wxml = (ROOT / "apps/miniprogram/pages/researcher-dashboard/index.wxml").read_text(encoding="utf-8")

    assert "researcher_platform_full_access" in page_js
    assert "开发全权限模式" in page_wxml
    assert "治疗性评估、AI、情感计算、网络分析、发布与生产门禁" in page_wxml


def test_temporary_full_access_covers_current_mobile_research_workspace(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    register = client.post(
        "/api/auth/register",
        json={"username": "workspace-parent", "password": "StrongPass123!", "role": "parent", "nickname": "普通测试账号"},
    )
    token = register.get_json()["data"]["token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "X-SafeHome-Researcher-Workspace": "1",
    }

    capabilities = client.get("/api/research/access/capabilities", headers=headers)
    operations = client.get("/api/research/operations", headers=headers)
    queues = client.get("/api/research/queues?queue=risk_review&page=1&page_size=20&status=active", headers=headers)
    participants = client.get("/api/research/participants?page=1&page_size=20", headers=headers)
    assessment_cases = client.get("/api/therapeutic-assessment/cases", headers=headers)
    assessment_runtime = client.get("/api/therapeutic-assessment/work-queue/runtime", headers=headers)

    assert capabilities.status_code == 200
    assert capabilities.get_json()["data"]["development_exception_active"] is True
    assert capabilities.get_json()["data"]["effective_role"] == "admin"
    assert operations.status_code == 200
    assert queues.status_code == 200
    assert participants.status_code == 200
    assert assessment_cases.status_code == 200
    assert assessment_runtime.status_code == 200


def test_miniprogram_maps_old_account_login_failures_to_actionable_messages():
    api_js = (ROOT / "apps/miniprogram/services/api.js").read_text(encoding="utf-8")

    assert 'invalid_credentials: "用户名或密码不正确，请重新输入。"' in api_js
    assert 'account_locked: "该账号因多次登录失败已暂时锁定，请稍后再试。"' in api_js
    assert 'account_inactive: "该账号当前不可用，请联系管理员核对账号状态。"' in api_js
    assert 'temporary_credential_expired: "该账号的临时密码已过期，请联系管理员重置密码。"' in api_js


def test_researcher_dashboard_contains_narrow_viewport_guards():
    wxss = (ROOT / "apps/miniprogram/pages/researcher-dashboard/index.wxss").read_text(encoding="utf-8")

    assert ".researcher-dashboard-page > *" in wxss
    assert "overflow-x: hidden;" in wxss
    assert ".error-actions button" in wxss
    assert "overflow-wrap: anywhere;" in wxss


def test_temporary_full_access_covers_all_research_platform_read_write_surfaces(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)

    research_operations = (
        ("POST", "/api/research/access/assignments"),
        ("POST", "/api/research/analysis/jobs"),
        ("POST", "/api/research/benchmarks/runs/affect"),
        ("POST", "/api/research/benchmarks/network/analyze"),
        ("POST", "/api/research/methodology/versions/sync"),
        ("GET", "/api/research/computation-contract/public-status"),
        ("POST", "/api/therapeutic-assessment/production-gate/evaluate"),
        ("PUT", "/api/therapeutic-assessment/cases/example/researcher-workbench/draft"),
        ("POST", "/api/ai-qa/release/transition"),
        ("POST", "/api/ai-qa/knowledge/rebuild"),
        ("GET", "/api/text-analysis/summary"),
        ("POST", "/api/relationship-pilot/enrollments/example/notes"),
        ("POST", "/api/operations-governance/packages/example/release"),
        ("PATCH", "/api/reliability/feature-flags/example"),
        ("POST", "/api/content-review/versions/example/publish"),
        ("PATCH", "/api/security/accounts/example/status"),
        ("POST", "/api/ux-governance/audits"),
        ("POST", "/api/risk-review/example/review"),
        ("POST", "/api/supervision/example/reply"),
    )
    base_actor = {"id": "ordinary-parent", "role": "parent", "source": "auth_token"}

    with app.app_context():
        from routes.auth_utils import elevate_actor_for_showcase_researcher_platform

        for method, path in research_operations:
            with app.test_request_context(
                path,
                method=method,
                headers={"X-SafeHome-Researcher-Workspace": "1"},
            ):
                elevated = elevate_actor_for_showcase_researcher_platform(base_actor)
            assert elevated["role"] == "admin", (method, path, elevated)
            assert elevated["original_role"] == "parent"
            assert elevated["showcase_full_access"] is True


def test_temporary_research_access_does_not_open_general_account_administration(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    base_actor = {"id": "ordinary-parent", "role": "parent", "source": "auth_token"}

    with app.app_context():
        from routes.auth_utils import elevate_actor_for_showcase_researcher_platform

        with app.test_request_context(
            "/api/auth/admin-create-account",
            method="POST",
            headers={"X-SafeHome-Researcher-Workspace": "1"},
        ):
            actor = elevate_actor_for_showcase_researcher_platform(base_actor)

    assert actor == base_actor


def test_temporary_full_access_reaches_representative_live_write_routes(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    register = client.post(
        "/api/auth/register",
        json={"username": "full-access-parent", "password": "StrongPass123!", "role": "parent"},
    )
    token = register.get_json()["data"]["token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "X-SafeHome-Researcher-Workspace": "1",
        "Idempotency-Key": "showcase-live-route-smoke",
    }
    operations = (
        ("POST", "/api/research/access/assignments"),
        ("POST", "/api/research/benchmarks/runs/affect"),
        ("POST", "/api/research/benchmarks/network/analyze"),
        ("POST", "/api/ai-qa/release/transition"),
        ("POST", "/api/therapeutic-assessment/production-gate/evaluate"),
        ("PATCH", "/api/security/accounts/example/status"),
    )

    for method, path in operations:
        response = client.open(path, method=method, headers=headers, json={})
        assert response.status_code != 403, (method, path, response.get_json())


def test_temporary_research_access_requires_explicit_workspace_request(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    base_actor = {"id": "ordinary-parent", "role": "parent", "source": "auth_token"}

    with app.app_context():
        from routes.auth_utils import elevate_actor_for_showcase_researcher_platform

        with app.test_request_context("/api/therapeutic-assessment/cases", method="POST"):
            actor = elevate_actor_for_showcase_researcher_platform(base_actor)

    assert actor == base_actor


def test_miniprogram_researcher_dashboard_marks_workspace_requests():
    page_js = (ROOT / "apps/miniprogram/pages/researcher-dashboard/index.js").read_text(encoding="utf-8")
    api_js = (ROOT / "apps/miniprogram/services/api.js").read_text(encoding="utf-8")

    assert 'defaultHeaders: { "X-SafeHome-Researcher-Workspace": "1" }' in page_js
    assert "...defaultHeaders" in api_js


def test_account_credential_tool_can_prepare_old_participant_rotation(tmp_path):
    module_path = ROOT / "backend/scripts/bootstrap_researcher.py"
    spec = importlib.util.spec_from_file_location("bootstrap_account", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    receipt_path = tmp_path / "test1-rotation.json"

    prepared = module.prepare(
        receipt_path,
        username="Test1",
        role="parent",
        nickname="Test1",
        target_environment="production",
        operation="rotate",
    )
    receipt = json.loads(prepared.read_text(encoding="utf-8"))

    assert receipt["username"] == "Test1"
    assert receipt["role"] == "parent"
    assert receipt["operation"] == "rotate"
    assert receipt["status"] == "pending_cloud_provision"
    assert len(receipt["password"]) >= 20


def test_old_participant_rotation_preserves_user_id_and_role(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    monkeypatch.setenv("LEGACY_ADMIN_TOKEN_ENABLED", "1")
    client = app.test_client()
    registered = client.post(
        "/api/auth/register",
        json={"username": "Test1-old", "password": "OldStrongPass123!", "role": "parent"},
    ).get_json()["data"]
    original_user_id = registered["user"]["id"]

    rotated = client.post(
        "/api/auth/admin-create-account",
        headers={"X-Admin-Token": "showcase-admin-token"},
        json={
            "username": "Test1-old",
            "password": "NewStrongPass456!",
            "role": "parent",
            "nickname": "Test1",
            "rotate_existing": True,
        },
    )
    login = client.post(
        "/api/auth/login",
        json={"username": "Test1-old", "password": "NewStrongPass456!"},
    )

    assert rotated.status_code == 200
    assert rotated.get_json()["data"]["credentials_rotated"] is True
    assert rotated.get_json()["data"]["user"]["id"] == original_user_id
    assert rotated.get_json()["data"]["user"]["role"] == "parent"
    assert login.status_code == 200
    assert login.get_json()["data"]["user"]["id"] == original_user_id
