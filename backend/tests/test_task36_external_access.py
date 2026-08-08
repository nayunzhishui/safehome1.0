import importlib.util
import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]


def _load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace(".", "_"), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_external_access_defaults_are_disabled_and_secret_free():
    config_path = ROOT / "config/task36_external_access.example.json"
    tunnel_path = ROOT / "config/cloudflared.safehome.example.yml"
    access_path = ROOT / "config/cloudflare-access-policy.example.json"
    gate_path = ROOT / "config/task36_external_access_gate.example.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    access = json.loads(access_path.read_text(encoding="utf-8"))
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    serialized = "".join(
        path.read_text(encoding="utf-8")
        for path in (config_path, tunnel_path, access_path, gate_path)
    )

    assert config["enabled"] is False
    assert config["public_data_scope"] == "synthetic_only"
    assert config["local_proxy"]["host"] == "127.0.0.1"
    assert config["local_proxy"]["port"] not in {5050, 5173}
    assert config["tunnel"]["mode"] == "named"
    assert access["default_action"] == "deny"
    assert access["allow"]["emails"] == ["<APPROVED_EMAIL>"]
    assert gate["approved"] is False
    assert "<TUNNEL_ID>" in serialized
    assert "<PROTECTED_CREDENTIAL_FILE>" in serialized
    for forbidden in ("token:", "password:", "WECHAT_SECRET", "ADMIN_EXPORT_TOKEN"):
        assert forbidden not in serialized


def test_prepare_dry_run_never_starts_process_or_writes_runtime_state(tmp_path):
    module = _load_script("manage_researcher_external_access.py")
    config = json.loads((ROOT / "config/task36_external_access.example.json").read_text(encoding="utf-8"))
    config["web_root"] = str(tmp_path / "dist")
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist/index.html").write_text("<html>safehome</html>", encoding="utf-8")
    config_path = tmp_path / "access.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    result = module.prepare(config_path, dry_run=True, state_path=tmp_path / "state.json")

    assert result["status"] == "prepared_dry_run"
    assert result["processes_started"] == 0
    assert result["public_access_started"] is False
    assert result["external_gate_approved"] is False
    assert not (tmp_path / "state.json").exists()


def test_wildcard_origin_public_bind_and_real_data_quick_tunnel_are_blocked(tmp_path):
    module = _load_script("manage_researcher_external_access.py")
    base = json.loads((ROOT / "config/task36_external_access.example.json").read_text(encoding="utf-8"))
    base["web_root"] = str(tmp_path / "dist")
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist/index.html").write_text("ok", encoding="utf-8")

    unsafe_configs = []
    wildcard = {**base, "allowed_origins": ["*"]}
    unsafe_configs.append(wildcard)
    public_bind = json.loads(json.dumps(base))
    public_bind["local_proxy"]["host"] = "0.0.0.0"
    unsafe_configs.append(public_bind)
    quick_real = json.loads(json.dumps(base))
    quick_real["tunnel"]["mode"] = "quick"
    quick_real["public_data_scope"] = "real_participant_data"
    unsafe_configs.append(quick_real)

    for index, payload in enumerate(unsafe_configs):
        path = tmp_path / f"unsafe-{index}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        try:
            module.prepare(path, dry_run=True, state_path=tmp_path / f"state-{index}.json")
        except ValueError:
            continue
        raise AssertionError("unsafe external access configuration must be blocked")


def test_start_requires_human_gate_receipt_before_process_creation(tmp_path, monkeypatch):
    module = _load_script("manage_researcher_external_access.py")
    config = json.loads((ROOT / "config/task36_external_access.example.json").read_text(encoding="utf-8"))
    config["enabled"] = True
    config["web_root"] = str(tmp_path / "dist")
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist/index.html").write_text("ok", encoding="utf-8")
    config_path = tmp_path / "enabled.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    called = []
    monkeypatch.setattr(module.subprocess, "Popen", lambda *args, **kwargs: called.append((args, kwargs)))

    try:
        module.start(config_path, gate_receipt=None, state_path=tmp_path / "state.json")
    except PermissionError as exc:
        assert "人工门禁" in str(exc)
    else:
        raise AssertionError("start must require an external human gate receipt")
    assert called == []


def test_same_origin_proxy_has_spa_fallback_api_allowlist_and_security_headers(tmp_path):
    module = _load_script("researcher_access_proxy.py")
    web_root = tmp_path / "dist"
    web_root.mkdir()
    (web_root / "index.html").write_text("index", encoding="utf-8")
    (web_root / "asset.js").write_text("asset", encoding="utf-8")

    assert module.is_proxy_path("/api/auth/login") is True
    assert module.is_proxy_path("/healthz") is True
    assert module.is_proxy_path("/readyz") is True
    assert module.is_proxy_path("/internal/file") is False
    assert module.resolve_static_path(web_root, "/asset.js") == web_root / "asset.js"
    assert module.resolve_static_path(web_root, "/dashboard") == web_root / "index.html"
    assert module.resolve_static_path(web_root, "/../secret") is None
    headers = module.security_headers()
    assert "default-src 'self'" in headers["Content-Security-Policy"]
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["Referrer-Policy"] == "no-referrer"


def test_manager_cli_exposes_only_controlled_lifecycle_commands():
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts/manage_researcher_external_access.py"), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    for command in ("prepare", "start-local", "start", "verify", "stop", "status"):
        assert command in completed.stdout


def test_local_start_never_starts_tunnel_or_claims_public_access(
    tmp_path, monkeypatch
):
    module = _load_script("manage_researcher_external_access.py")
    config = json.loads(
        (ROOT / "config/task36_external_access.example.json").read_text(
            encoding="utf-8"
        )
    )
    config["web_root"] = str(tmp_path / "dist")
    config["runtime"]["log_dir"] = str(tmp_path / "logs")
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist/index.html").write_text("ok", encoding="utf-8")
    config_path = tmp_path / "local.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    calls = []

    class Process:
        pid = 43210

    monkeypatch.setattr(
        module.subprocess,
        "Popen",
        lambda command, **kwargs: calls.append((command, kwargs)) or Process(),
    )
    state_path = tmp_path / "state.json"
    result = module.start_local(config_path, state_path=state_path)
    state = json.loads(state_path.read_text(encoding="utf-8"))

    assert result["status"] == "local_started"
    assert result["public_access_started"] is False
    assert state["mode"] == "local_verification"
    assert state["tunnel_pid"] == 0
    assert state["public_access_started"] is False
    assert len(calls) == 1
    assert "cloudflared" not in " ".join(str(item) for item in calls[0][0])


def test_proxy_serves_deep_link_and_forwards_only_allowlisted_headers(tmp_path):
    module = _load_script("researcher_access_proxy.py")
    captured = {}

    class UpstreamHandler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            captured.update({key.lower(): value for key, value in self.headers.items()})
            body = b'{"ok":true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            return

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
    upstream_thread = threading.Thread(target=upstream.serve_forever, daemon=True)
    upstream_thread.start()
    web_root = tmp_path / "dist"
    web_root.mkdir()
    (web_root / "index.html").write_text("<html>dashboard</html>", encoding="utf-8")

    class ProxyHandler(module.ResearchAccessHandler):
        pass

    ProxyHandler.web_root = web_root
    ProxyHandler.api_base_url = f"http://127.0.0.1:{upstream.server_port}"
    proxy = ThreadingHTTPServer(("127.0.0.1", 0), ProxyHandler)
    proxy_thread = threading.Thread(target=proxy.serve_forever, daemon=True)
    proxy_thread.start()
    try:
        with urlopen(f"http://127.0.0.1:{proxy.server_port}/dashboard", timeout=5) as response:
            assert response.status == 200
            assert b"dashboard" in response.read()
            assert response.headers["X-Frame-Options"] == "DENY"
        request = Request(
            f"http://127.0.0.1:{proxy.server_port}/healthz",
            headers={
                "Authorization": "Bearer local-test-token",
                "X-WX-OPENID": "must-not-forward",
                "CF-Access-Jwt-Assertion": "must-not-forward",
            },
        )
        with urlopen(request, timeout=5) as response:
            assert response.status == 200
            assert response.headers["X-Request-ID"]
        assert captured["authorization"] == "Bearer local-test-token"
        assert "x-wx-openid" not in captured
        assert "cf-access-jwt-assertion" not in captured
    finally:
        proxy.shutdown()
        upstream.shutdown()
