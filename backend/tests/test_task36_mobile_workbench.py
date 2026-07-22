import importlib
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
ADMIN_HEADERS = {"X-Admin-Token": "safehome-local-admin-token"}


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    return importlib.import_module("app").app


def _participant_with_diary(client, code: str, nickname: str) -> str:
    login = client.post("/api/auth/wechat-login", json={"code": code, "nickname": nickname})
    assert login.status_code == 200
    data = login.get_json()["data"]
    created = client.post(
        "/api/diaries",
        headers={"Authorization": f"Bearer {data['token']}"},
        json={
            "scene": "日常沟通",
            "event_description": "我停下来听完，再说自己的担心。",
            "parent_emotion": "着急",
        },
    )
    assert created.status_code == 201
    return data["user"]["id"]


def test_participant_matrix_supports_stable_search_and_pagination(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    first_id = _participant_with_diary(client, "mobile-workbench-a", "一位昵称很长但仍应保持单行可读的参与者甲")
    second_id = _participant_with_diary(client, "mobile-workbench-b", "参与者乙")

    first = client.get("/api/research/participants?page=1&page_size=1", headers=ADMIN_HEADERS)
    second = client.get("/api/research/participants?page=2&page_size=1", headers=ADMIN_HEADERS)
    assert first.status_code == 200
    assert second.status_code == 200
    first_data = first.get_json()["data"]
    second_data = second.get_json()["data"]
    assert first_data["total"] == 2
    assert first_data["count"] == 1
    assert first_data["page"] == 1
    assert first_data["page_size"] == 1
    assert first_data["has_more"] is True
    assert second_data["has_more"] is False
    assert {first_data["items"][0]["user_id"], second_data["items"][0]["user_id"]} == {first_id, second_id}

    search = client.get("/api/research/participants?q=%E5%BE%88%E9%95%BF&page=1&page_size=10", headers=ADMIN_HEADERS)
    assert search.status_code == 200
    assert search.get_json()["data"]["items"][0]["user_id"] == first_id


def test_participant_matrix_rejects_bad_pages_and_requires_auth(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    assert client.get("/api/research/participants?page=0&page_size=10", headers=ADMIN_HEADERS).status_code == 400
    assert client.get("/api/research/participants?page=1&page_size=101", headers=ADMIN_HEADERS).status_code == 400
    assert client.get("/api/research/participants?page=1&page_size=10").status_code == 401


def test_mobile_workbench_static_contract_covers_five_workspaces_and_recovery():
    page_root = PROJECT_ROOT / "apps" / "miniprogram" / "pages" / "researcher-dashboard"
    js = (page_root / "index.js").read_text(encoding="utf-8")
    wxml = (page_root / "index.wxml").read_text(encoding="utf-8")
    wxss = (page_root / "index.wxss").read_text(encoding="utf-8")
    page_json = (page_root / "index.json").read_text(encoding="utf-8")
    api_js = (PROJECT_ROOT / "apps" / "miniprogram" / "services" / "api.js").read_text(encoding="utf-8")

    for label in ("待处理", "参与者", "反馈与消息", "试点项目", "我的工作"):
        assert label in js
    assert "Promise.allSettled" in js
    assert "wx.onNetworkStatusChange" in js
    assert "setTimeout(() => this.loadParticipants(true), 350)" in js
    assert "wx.setStorageSync" in js and "wx.getStorageSync" in js
    assert "getResearchOperations" in api_js and "getResearchParticipants" in api_js
    assert "服务版本" not in wxml
    assert "请求编号" in wxml
    assert "min-height: 88rpx" in wxss
    assert "text-overflow: ellipsis" in wxss
    assert '"enablePullDownRefresh": true' in page_json


def test_shared_and_web_clients_expose_paginated_participant_contract():
    shared = (PROJECT_ROOT / "shared" / "types" / "api.ts").read_text(encoding="utf-8")
    web = (PROJECT_ROOT / "apps" / "web" / "src" / "services" / "safehomeApi.ts").read_text(encoding="utf-8")
    assert "interface ResearchParticipantPage" in shared
    assert "has_more: boolean" in shared
    assert "page_size?: number" in web
    assert "Promise<ResearchParticipantPage>" in web


def test_visual_audit_covers_required_viewports_large_text_and_overflow():
    source = (PROJECT_ROOT / "scripts" / "audit_task36_mobile_workbench.mjs").read_text(encoding="utf-8")
    assert "const VIEWPORTS = [360, 375, 430, 768]" in source
    assert '"large-text"' in source
    assert "scrollWidth" in source
    assert "box.height < 44" in source
    assert "participant-name" in source
