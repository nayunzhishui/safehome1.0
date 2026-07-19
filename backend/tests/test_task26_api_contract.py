import importlib.util
import inspect
import json
import re
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
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "task26.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    return __import__("app").app


def _login(client, code="task26-user"):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code})
    token = response.get_json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


def _load_script(name: str):
    path = PROJECT_ROOT / "backend" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_contract_inventory_and_generated_artifacts_match_flask(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    builder = _load_script("build_api_contract")
    contract = builder.build_contract(app)
    stored = json.loads(builder.CONTRACT_PATH.read_text(encoding="utf-8"))

    assert contract == stored
    assert len(contract["endpoints"]) >= 130
    assert len({item["operation_id"] for item in contract["endpoints"]}) == len(contract["endpoints"])
    assert builder.generated_files(contract)[builder.TS_PATH] == builder.TS_PATH.read_text(encoding="utf-8")
    assert builder.generated_files(contract)[builder.MINIPROGRAM_PATH] == builder.MINIPROGRAM_PATH.read_text(encoding="utf-8")
    assert builder.generated_files(contract)[builder.DOC_PATH] == builder.DOC_PATH.read_text(encoding="utf-8")


def test_every_operation_declares_access_scope_error_request_id_and_compatibility_metadata():
    contract = json.loads((PROJECT_ROOT / "shared" / "contracts" / "api-contract.json").read_text(encoding="utf-8"))
    for item in contract["endpoints"]:
        assert item["access"]["roles"]
        assert item["object_scope"]
        assert item["response"]["request_id"] is True
        assert item["error_envelope"]["error"] == {"code": "string", "message": "string"}
        assert item["deprecation"]["status"] in {"active", "deprecated"}
        pagination = item["request"]["pagination"]
        if pagination:
            assert pagination["response"] == ["items", "page", "page_size", "total", "has_more"]
            assert pagination["max_page_size"] == 100


def test_compatibility_snapshot_has_no_breaking_change():
    checker = _load_script("check_api_compatibility")
    baseline = json.loads(checker.BASELINE_PATH.read_text(encoding="utf-8"))
    current = json.loads(checker.CURRENT_PATH.read_text(encoding="utf-8"))
    assert checker.compatibility_errors(baseline, current) == []


def test_boundary_scan_has_no_blocker_and_snapshot_is_current():
    audit = _load_script("audit_api_boundaries")
    snapshot = audit.build_snapshot()
    stored = json.loads(audit.SNAPSHOT_PATH.read_text(encoding="utf-8"))
    assert snapshot == stored
    assert snapshot["counts"]["blocker"] == 0


def test_standard_success_and_error_envelopes_include_request_id(tmp_path, monkeypatch):
    client = _fresh_app(tmp_path, monkeypatch).test_client()
    success = client.get("/api/auth/capabilities", headers={"X-Request-ID": "task26-success-001"})
    missing = client.get("/api/not-a-real-endpoint", headers={"X-Request-ID": "task26-error-001"})

    assert success.status_code == 200
    assert success.get_json()["request_id"] == "task26-success-001"
    assert success.headers["X-Request-ID"] == "task26-success-001"
    assert missing.status_code == 404
    assert missing.get_json() == {
        "ok": False,
        "error": {"code": "not_found", "message": "没有找到对应接口。"},
        "request_id": "task26-error-001",
    }


def test_legacy_limit_parameter_remains_compatible_for_messages(tmp_path, monkeypatch):
    client = _fresh_app(tmp_path, monkeypatch).test_client()
    response = client.get("/api/messages?limit=1", headers=_login(client))
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["page"] == 1 and data["page_size"] == 1
    assert response.headers["Deprecation"] == "true"
    assert "31 Oct 2026" in response.headers["Sunset"]
    contract = json.loads((PROJECT_ROOT / "shared" / "contracts" / "api-contract.json").read_text(encoding="utf-8"))
    operation = next(item for item in contract["endpoints"] if item["path"] == "/api/messages" and item["method"] == "GET")
    assert operation["request"]["pagination"]["deprecated_aliases"][0]["replacement"] == "page_size"


def test_sensitive_http_adapters_delegate_to_deep_services(tmp_path, monkeypatch):
    _fresh_app(tmp_path, monkeypatch)
    import routes.messages as messages_route
    import routes.privacy as privacy_route
    import routes.research_workspace as research_route
    import routes.relationship_pilot_routes as relationship_route

    assert "conn.execute" not in inspect.getsource(messages_route.list_messages)
    assert "conn.execute" not in inspect.getsource(messages_route.send_researcher_message)
    assert "conn.execute" not in inspect.getsource(privacy_route.consent_status)
    assert "conn.execute" not in inspect.getsource(privacy_route.export_my_data)
    assert "conn.execute" not in inspect.getsource(research_route.get_research_queue)
    relationship_source = inspect.getsource(relationship_route)
    for service_name in ["relationship_enrollment_service", "relationship_report_service", "relationship_growth_service"]:
        assert service_name in relationship_source


def test_shared_web_and_miniprogram_endpoint_literals_are_registered():
    contract = json.loads((PROJECT_ROOT / "shared" / "contracts" / "api-contract.json").read_text(encoding="utf-8"))

    def normalized(path: str) -> str:
        path = re.sub(r"<(?:(?:int|string|path|uuid):)?[^>]+>", ":*", path)
        return re.sub(r":[A-Za-z_][A-Za-z0-9_]*", ":*", path)

    contract_paths = {normalized(item["path"]) for item in contract["endpoints"]}
    sources = [
        PROJECT_ROOT / "shared" / "constants" / "api.ts",
        PROJECT_ROOT / "apps" / "web" / "src" / "services" / "safehomeApi.ts",
        PROJECT_ROOT / "apps" / "miniprogram" / "services" / "api.js",
    ]
    for source_path in sources:
        literals = set(re.findall(r"[\"'`](/api/[A-Za-z0-9_:/<>.-]+)[\"'`]", source_path.read_text(encoding="utf-8")))
        for literal in literals:
            candidate = normalized(literal)
            assert candidate in contract_paths or any(path.startswith(candidate + "/") for path in contract_paths), f"unregistered endpoint literal {literal} in {source_path}"
