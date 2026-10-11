import copy
import importlib
import json
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
MINIPROGRAM_ROOT = PROJECT_ROOT / "apps" / "miniprogram"
ADMIN_TOKEN = "task18-program-admin-token"


def _fresh_app(tmp_path, monkeypatch, app_env="validation"):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("DATABASE_DATA_WATERMARK", "synthetic_validation_only")
    monkeypatch.setenv("LEGACY_ADMIN_TOKEN_ENABLED", "1")
    monkeypatch.setenv("SECRET_KEY", "task18-program-production-secret-key")
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", ADMIN_TOKEN)
    if app_env == "production":
        monkeypatch.setenv("LEGACY_ADMIN_TOKEN_ENABLED", "1")
    return importlib.import_module("app").app


def test_validation_showcase_opens_all_programs_without_marking_them_approved(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.get("/api/programs")

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data["items"]) == 3
    assert data["availability"]["approved_count"] == 0
    assert data["availability"]["pending_review_count"] == 3
    assert data["availability"]["status"] == "showcase_open"
    assert data["availability"]["showcase_mode"] is True
    assert all(item["showcase_open"] is True for item in data["items"])
    assert client.get("/api/programs/self_compassion_exam_anxiety").status_code == 200


def _participant_headers(app, user_id="task18-program-parent"):
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token

        timestamp = now_iso()
        with get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (id, nickname, role, status, created_at, updated_at) VALUES (?, ?, 'parent', 'active', ?, ?)",
                (user_id, user_id, timestamp, timestamp),
            )
            conn.commit()
        token = generate_auth_token({"id": user_id, "role": "parent"})
    return {"Authorization": f"Bearer {token}"}


def test_production_opens_owner_released_programs_and_keeps_drafts_closed(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    app.config.update(APP_ENV="production")
    client = app.test_client()
    headers = _participant_headers(app)
    entry = {"session_no": 1, "reflection": "今天先写下一点感受。", "recommendation_source": "user_choice"}

    listing = client.get("/api/programs")
    detail = client.get("/api/programs/self_compassion_exam_anxiety")
    created = client.post("/api/programs/self_compassion_exam_anxiety/entries", json=entry, headers=headers)

    assert listing.status_code == 200
    data = listing.get_json()["data"]
    assert len(data["items"]) == 3
    assert all(item["preview_only"] is False and item["showcase_open"] is False for item in data["items"])
    assert data["availability"]["status"] == "available"
    assert data["availability"]["approved_count"] == 0
    assert data["availability"]["released_count"] == 3
    assert data["availability"]["pending_review_count"] == 3
    assert "负责人" in data["availability"]["message"]
    assert detail.status_code == 200
    assert all(item["status"] == "pending" for item in detail.get_json()["data"]["program"]["approval"].values())
    assert created.status_code == 201

    programs_route = sys.modules["routes.programs"]
    with app.app_context():
        draft = copy.deepcopy(programs_route._load_programs_payload())
    draft["programs"][0]["review_status"] = "pilot_draft"
    monkeypatch.setattr(programs_route, "_load_programs_payload", lambda: draft)
    blocked = client.post("/api/programs/self_compassion_exam_anxiety/entries", json=entry, headers=headers)

    assert len(client.get("/api/programs").get_json()["data"]["items"]) == 2
    assert client.get("/api/programs/self_compassion_exam_anxiety").status_code == 404
    assert blocked.status_code == 409
    assert blocked.get_json()["error"]["code"] == "program_not_approved"


def test_reviewer_can_preview_drafts_but_preview_does_not_approve_them(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    headers = {"X-Admin-Token": ADMIN_TOKEN}

    listing = client.get("/api/programs?include_drafts=true", headers=headers)
    detail = client.get(
        "/api/programs/self_compassion_exam_anxiety?include_drafts=true",
        headers=headers,
    )

    assert listing.status_code == 200
    list_data = listing.get_json()["data"]
    assert len(list_data["items"]) == 3
    assert list_data["availability"]["preview_mode"] is True
    assert all(item["preview_only"] is False for item in list_data["items"])
    assert all(item["review_status"] == "production_approved" for item in list_data["items"])
    assert detail.status_code == 200
    assert detail.get_json()["data"]["program"]["review_status"] == "production_approved"
    assert detail.get_json()["data"]["preview_mode"] is True


def test_draft_preview_requires_reviewer_role(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.get("/api/programs?include_drafts=true")

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "unauthorized"


def test_miniprogram_shows_truthful_pending_state_and_reviewer_preview():
    page_js = (MINIPROGRAM_ROOT / "pages" / "program-list" / "index.js").read_text(encoding="utf-8")
    page_wxml = (MINIPROGRAM_ROOT / "pages" / "program-list" / "index.wxml").read_text(encoding="utf-8")
    detail_js = (MINIPROGRAM_ROOT / "pages" / "program-detail" / "index.js").read_text(encoding="utf-8")
    detail_wxml = (MINIPROGRAM_ROOT / "pages" / "program-detail" / "index.wxml").read_text(encoding="utf-8")
    api_js = (MINIPROGRAM_ROOT / "services" / "api.js").read_text(encoding="utf-8")

    assert "include_drafts: true" in page_js
    assert "pending_review_count" in page_wxml
    assert "待三方审核" in page_wxml
    assert "preview=1" in page_js
    assert "include_drafts: true" in detail_js
    assert 'wx:if="{{!previewMode}}" class="submit-block"' in detail_wxml
    assert "研究者只读预览" in detail_wxml
    assert "Boolean(params.include_drafts)" in api_js
