import importlib
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    return importlib.import_module("app").app


def _login(client, code):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code})
    return response.get_json()["data"]["token"]


def test_general_growth_aggregates_owned_records_without_mixing_assessment_scales(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    token = _login(client, "growth-overview-user")
    headers = {"Authorization": f"Bearer {token}"}
    assert client.post(
        "/api/emotion-thermometer",
        headers=headers,
        json={"intensity_level": 6, "emotion_label": "有些着急"},
    ).status_code == 201
    assert client.post(
        "/api/diaries",
        headers=headers,
        json={"scene": "沟通", "event_description": "我先停了一下。", "parent_emotion": "着急"},
    ).status_code == 201

    response = client.get("/api/growth/overview", headers=headers)
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["summary"]["record_count"] == 1
    assert data["thermometer"][0]["intensity_level"] == 6
    assert data["timeline"][0]["type"] == "diary"
    assert "不同量尺分开" in data["boundary_notice"]


def test_general_growth_requires_login(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    assert client.get("/api/growth/overview").status_code == 401
