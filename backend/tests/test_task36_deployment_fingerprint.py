import importlib
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _clear_modules():
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)


def _fresh_app(tmp_path, monkeypatch, *, build_info=None, content_dir=None):
    tmp_path.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(BACKEND))
    _clear_modules()
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task36-f09.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir or ROOT / "content"))
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("ALLOW_PRODUCTION_SQLITE", "1")
    monkeypatch.setenv("SECRET_KEY", "task36-f09-test-secret-key-that-is-long-enough")
    monkeypatch.setenv("ADMIN_EXPORT_TOKEN", "task36-f09-admin-token")
    if build_info is not None:
        build_path = tmp_path / "build_info.json"
        build_path.write_text(json.dumps(build_info, ensure_ascii=False), encoding="utf-8")
        monkeypatch.setenv("BUILD_INFO_PATH", str(build_path))
    else:
        monkeypatch.delenv("BUILD_INFO_PATH", raising=False)
    return importlib.import_module("app").app


def _build_info(content_dir=None):
    sys.path.insert(0, str(BACKEND))
    from services.build_fingerprint_service import generate_build_info

    return generate_build_info(
        ROOT,
        commit_sha="abcdef1234567890",
        build_time="2026-07-22T12:00:00+00:00",
        content_dir=content_dir or ROOT / "content",
    )


def test_healthz_exposes_safe_build_identity_and_response_headers(tmp_path, monkeypatch):
    info = _build_info()
    app = _fresh_app(tmp_path, monkeypatch, build_info=info)
    response = app.test_client().get("/healthz", headers={"X-Request-ID": "f09-health-001"})
    body = response.get_json()

    assert response.status_code == 200
    assert body["build"]["commit_sha"] == "abcdef1234567890"
    assert body["build"]["build_time"] == "2026-07-22T12:00:00+00:00"
    assert len(body["build"]["api_contract_hash"]) == 64
    assert len(body["build"]["content_manifest_hash"]) == 64
    assert body["build"]["schema_expected"]["version"] == "2026_07_27_038"
    assert response.headers["X-SafeHome-Build-ID"] == body["build"]["build_id"]
    assert response.headers["X-SafeHome-Service-Version"] == body["version"]
    serialized = response.get_data(as_text=True)
    assert str(ROOT) not in serialized
    assert "task36-f09-admin-token" not in serialized


def test_production_readiness_accepts_matching_packaged_fingerprint(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, build_info=_build_info())
    response = app.test_client().get("/readyz")
    deployment = response.get_json()["deployment"]

    assert response.status_code == 200
    assert deployment["ok"] is True
    assert deployment["diagnosis"] == "consistent"
    assert deployment["api_contract_matches"] is True
    assert deployment["content_manifest_matches"] is True
    assert deployment["schema_matches"] is True


def test_production_readiness_distinguishes_contract_content_and_schema_drift(tmp_path, monkeypatch):
    contract_info = {**_build_info(), "api_contract_hash": "0" * 64}
    contract_app = _fresh_app(tmp_path / "contract", monkeypatch, build_info=contract_info)
    contract = contract_app.test_client().get("/readyz")
    assert contract.status_code == 503
    assert contract.get_json()["deployment"]["diagnosis"] == "backend_contract_mismatch"

    content_dir = tmp_path / "content-copy"
    shutil.copytree(ROOT / "content", content_dir)
    content_info = _build_info(content_dir)
    cards_path = content_dir / "training_cards.json"
    cards = json.loads(cards_path.read_text(encoding="utf-8"))
    cards["version"] = f"{cards.get('version', 'unknown')}-drift"
    cards_path.write_text(json.dumps(cards, ensure_ascii=False), encoding="utf-8")
    content_app = _fresh_app(tmp_path / "content", monkeypatch, build_info=content_info, content_dir=content_dir)
    content = content_app.test_client().get("/readyz")
    assert content.status_code == 503
    assert content.get_json()["deployment"]["diagnosis"] == "content_manifest_mismatch"

    schema_app = _fresh_app(tmp_path / "schema", monkeypatch, build_info=_build_info())
    with schema_app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            conn.execute("DELETE FROM schema_migrations WHERE version = ?", (database.CURRENT_SCHEMA_VERSION,))
            conn.commit()
    schema = schema_app.test_client().get("/readyz")
    assert schema.status_code == 503
    assert schema.get_json()["deployment"]["diagnosis"] == "database_schema_mismatch"


def test_journey_snapshot_reports_auth_gateway_permission_and_server_failures(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch, build_info=_build_info())
    client = app.test_client()
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token

        with get_connection() as conn:
            timestamp = now_iso()
            conn.execute(
                "INSERT INTO users (id, nickname, role, status, created_at, updated_at) VALUES ('f09-researcher', 'F09', 'researcher', 'active', ?, ?)",
                (timestamp, timestamp),
            )
            conn.commit()
        headers = {"Authorization": f"Bearer {generate_auth_token({'id': 'f09-researcher', 'role': 'researcher'})}"}

    for path, status in [
        ("/api/auth/login", 401),
        ("/api/messages", 502),
        ("/api/checkins", 500),
        ("/api/relationship-pilot/researcher/dashboard", 403),
    ]:
        with app.app_context():
            from services.reliability_service import record_request_event

            record_request_event(
                request_id=f"f09-{status}-{path.rsplit('/', 1)[-1]}",
                method="GET",
                path=path,
                actor_scope="researcher",
                status_code=status,
                latency_ms=125.5,
                error_code=f"synthetic_{status}",
            )
    response = client.post(
        "/api/reliability/slo-snapshots",
        headers=headers,
        json={"environment": "local_synthetic", "window_minutes": 60},
    )
    metrics = response.get_json()["data"]["metrics"]

    assert response.status_code == 200
    assert metrics["authentication"]["auth_401_count"] >= 1
    assert metrics["messages"]["gateway_502_count"] >= 1
    assert metrics["training_history"]["server_error_count"] >= 1
    assert metrics["researcher_dashboard"]["forbidden_403_count"] >= 1
    assert metrics["researcher_dashboard"]["latency_p95_ms"] >= 0


def test_dual_client_error_contract_keeps_only_copyable_transport_metadata():
    mini_api = (ROOT / "apps" / "miniprogram" / "services" / "api.js").read_text(encoding="utf-8")
    mini_diagnostics = (ROOT / "apps" / "miniprogram" / "utils" / "errorDiagnostics.js").read_text(encoding="utf-8")
    web_api = (ROOT / "apps" / "web" / "src" / "services" / "safehomeApi.ts").read_text(encoding="utf-8")

    for marker in ("requestId", "clientVersion", "serviceVersion", "buildId", "occurredAt"):
        assert marker in mini_api or marker in mini_diagnostics
        assert marker in web_api
    forbidden = ("auth_token", "password", "payload", "正文")
    copy_function = mini_diagnostics.split("function buildErrorDiagnosticText", 1)[1]
    assert all(item not in copy_function for item in forbidden)
