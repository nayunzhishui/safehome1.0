"""Prepare and control SafeHome external research access without auto-approving gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config/task36_external_access.example.json"
DEFAULT_STATE = ROOT / ".codex_tmp/task36_external_access_state.json"
GATE_SCHEMA = "safehome.external_access_gate.v1"


def _resolve_project_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def _load_config(config_path: Path) -> dict:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("schema") != "safehome.external_access.v1":
        raise ValueError("外部访问配置格式不兼容")
    host = str(config.get("local_proxy", {}).get("host") or "")
    port = int(config.get("local_proxy", {}).get("port") or 0)
    if host not in {"127.0.0.1", "::1", "localhost"}:
        raise ValueError("本地代理只能监听loopback")
    if port in {5050, 5173} or not 1024 <= port <= 65535:
        raise ValueError("必须使用独立的非特权代理端口，不能直接公开Flask或Vite")
    origins = config.get("allowed_origins") or []
    if not origins or "*" in origins or any(not str(origin).startswith("https://") for origin in origins):
        raise ValueError("ALLOWED_ORIGINS必须是确切HTTPS地址且禁止通配符")
    public_host = str(config.get("public_host") or "")
    if public_host not in origins:
        raise ValueError("public_host必须出现在ALLOWED_ORIGINS")
    mode = str(config.get("tunnel", {}).get("mode") or "")
    if mode not in {"named", "quick"}:
        raise ValueError("tunnel.mode只能是named或quick")
    scope = str(config.get("public_data_scope") or "")
    if mode == "quick" and scope not in {"synthetic_only", "deidentified_only"}:
        raise ValueError("Quick Tunnel只允许合成或完全脱敏数据")
    if config.get("access", {}).get("default_policy") != "deny":
        raise ValueError("外部身份门禁必须默认拒绝")
    web_root = _resolve_project_path(str(config.get("web_root") or ""))
    if not (web_root / "index.html").is_file():
        raise ValueError("Web生产构建不存在，请先执行apps/web npm run build")
    return config


def prepare(config_path: Path, *, dry_run: bool = True, state_path: Path = DEFAULT_STATE) -> dict:
    config = _load_config(config_path)
    return {
        "schema": "safehome.external_access_prepare.v1",
        "status": "prepared_dry_run" if dry_run else "prepared",
        "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "web_root_ready": True,
        "loopback_only": True,
        "cors_wildcard": False,
        "public_data_scope": config["public_data_scope"],
        "external_gate_approved": False,
        "processes_started": 0,
        "public_access_started": False,
        "state_written": False,
        "state_path": str(state_path),
    }


def _load_gate(gate_receipt: Path | None, config: dict) -> dict:
    if gate_receipt is None or not gate_receipt.is_file():
        raise PermissionError("缺少负责人、隐私和安全人工门禁receipt，禁止启动外部访问")
    gate = json.loads(gate_receipt.read_text(encoding="utf-8"))
    if gate.get("schema") != GATE_SCHEMA or gate.get("approved") is not True:
        raise PermissionError("人工门禁receipt未批准")
    expires_at = datetime.fromisoformat(str(gate.get("expires_at") or ""))
    if expires_at.tzinfo is None or expires_at.astimezone(timezone.utc) <= datetime.now(timezone.utc):
        raise PermissionError("人工门禁receipt已过期")
    if gate.get("public_host") != config.get("public_host"):
        raise PermissionError("人工门禁域名与配置不一致")
    if gate.get("data_scope") != config.get("public_data_scope"):
        raise PermissionError("人工门禁数据范围与配置不一致")
    if not all(gate.get(key) for key in ("owner_approved", "privacy_approved", "security_approved")):
        raise PermissionError("人工门禁签署不完整")
    return gate


def _proxy_command(config: dict) -> list[str]:
    proxy = config["local_proxy"]
    return [
        sys.executable,
        str(ROOT / "scripts/researcher_access_proxy.py"),
        "--listen-host",
        str(proxy["host"]),
        "--port",
        str(proxy["port"]),
        "--web-root",
        str(_resolve_project_path(config["web_root"])),
        "--api-base-url",
        str(config["api_base_url"]),
        "--max-request-bytes",
        str(proxy.get("max_request_bytes") or 1048576),
    ]


def start_local(
    config_path: Path, *, state_path: Path = DEFAULT_STATE
) -> dict:
    """Start only the loopback proxy for build/login verification.

    This command never starts a public tunnel and therefore cannot be presented
    as external-access approval.
    """

    config = _load_config(config_path)
    log_dir = _resolve_project_path(config["runtime"]["log_dir"])
    log_dir.mkdir(parents=True, exist_ok=True)
    proxy_log = (log_dir / "proxy-local.log").open("ab")
    proxy_process = subprocess.Popen(
        _proxy_command(config),
        cwd=ROOT,
        stdout=proxy_log,
        stderr=subprocess.STDOUT,
    )
    state = {
        "schema": "safehome.external_access_state.v1",
        "mode": "local_verification",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "public_host": None,
        "data_scope": "local_only",
        "gate_receipt_sha256": None,
        "gate_expires_at": None,
        "proxy_pid": proxy_process.pid,
        "tunnel_pid": 0,
        "public_access_started": False,
    }
    state_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = state_path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, state_path)
    return {
        "status": "local_started",
        "local_url": (
            f"http://{config['local_proxy']['host']}:"
            f"{config['local_proxy']['port']}"
        ),
        "public_access_started": False,
        "state_path": str(state_path),
    }


def start(config_path: Path, *, gate_receipt: Path | None, state_path: Path = DEFAULT_STATE) -> dict:
    config = _load_config(config_path)
    if config.get("enabled") is not True:
        raise PermissionError("配置enabled=false，禁止启动外部访问")
    gate = _load_gate(gate_receipt, config)
    proxy = config["local_proxy"]
    log_dir = _resolve_project_path(config["runtime"]["log_dir"])
    log_dir.mkdir(parents=True, exist_ok=True)
    proxy_log = (log_dir / "proxy.log").open("ab")
    tunnel_log = (log_dir / "tunnel.log").open("ab")
    proxy_command = _proxy_command(config)
    tunnel = config["tunnel"]
    tunnel_binary = str(tunnel.get("binary") or "cloudflared")
    if shutil.which(tunnel_binary) is None:
        raise FileNotFoundError("没有找到cloudflared可执行文件，禁止启动")
    if tunnel["mode"] == "named":
        tunnel_config_path = _resolve_project_path(tunnel["config_path"])
        if not tunnel_config_path.is_file():
            raise FileNotFoundError("命名Tunnel本地配置不存在")
        tunnel_config_text = tunnel_config_path.read_text(encoding="utf-8")
        if "<" in tunnel_config_text or "PROTECTED_CREDENTIAL_FILE" in tunnel_config_text:
            raise ValueError("命名Tunnel配置仍包含占位符")
        tunnel_command = [
            tunnel_binary,
            "--config", str(tunnel_config_path),
            "tunnel", "run",
        ]
    else:
        tunnel_command = [
            tunnel_binary,
            "tunnel", "--url", f"http://127.0.0.1:{proxy['port']}",
        ]
    proxy_process = subprocess.Popen(proxy_command, cwd=ROOT, stdout=proxy_log, stderr=subprocess.STDOUT)
    try:
        tunnel_process = subprocess.Popen(tunnel_command, cwd=ROOT, stdout=tunnel_log, stderr=subprocess.STDOUT)
    except Exception:
        proxy_process.terminate()
        raise
    state = {
        "schema": "safehome.external_access_state.v1",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "public_host": config["public_host"],
        "data_scope": config["public_data_scope"],
        "gate_receipt_sha256": hashlib.sha256(gate_receipt.read_bytes()).hexdigest(),
        "gate_expires_at": gate["expires_at"],
        "proxy_pid": proxy_process.pid,
        "tunnel_pid": tunnel_process.pid,
        "public_access_started": True,
    }
    state_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = state_path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, state_path)
    return {"status": "started", "public_host": config["public_host"], "state_path": str(state_path)}


def verify(config_path: Path) -> dict:
    config = _load_config(config_path)
    proxy = config["local_proxy"]
    base_url = f"http://{proxy['host']}:{proxy['port']}"
    outcomes = []
    for path in ("/healthz", "/readyz", "/login"):
        try:
            with urlopen(Request(base_url + path, method="GET"), timeout=5) as response:
                outcomes.append({"path": path, "status": response.status})
        except OSError as exc:
            outcomes.append({"path": path, "status": 0, "error": type(exc).__name__})
    return {"status": "verified" if all(item["status"] == 200 for item in outcomes) else "not_ready", "outcomes": outcomes}


def stop(state_path: Path = DEFAULT_STATE) -> dict:
    if not state_path.is_file():
        return {"status": "already_stopped", "processes_stopped": 0}
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("schema") != "safehome.external_access_state.v1":
        raise ValueError("运行状态格式不兼容，拒绝终止未知进程")
    stopped = 0
    for key in ("tunnel_pid", "proxy_pid"):
        pid = int(state.get(key) or 0)
        if pid > 0:
            try:
                os.kill(pid, signal.SIGTERM)
                stopped += 1
            except ProcessLookupError:
                pass
    state_path.unlink(missing_ok=True)
    return {"status": "stopped", "processes_stopped": stopped}


def status(state_path: Path = DEFAULT_STATE) -> dict:
    if not state_path.is_file():
        return {"status": "stopped", "public_access_started": False}
    state = json.loads(state_path.read_text(encoding="utf-8"))
    return {
        "status": "state_present",
        "public_access_started": bool(state.get("public_access_started")),
        "mode": state.get("mode", "public_tunnel"),
        "public_host": state.get("public_host"),
        "data_scope": state.get("data_scope"),
        "gate_expires_at": state.get("gate_expires_at"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="SafeHome controlled external access lifecycle")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("prepare", "verify", "start-local"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    start_parser.add_argument("--gate-receipt", type=Path, required=True)
    for command in ("stop", "status"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare(args.config, dry_run=True)
    elif args.command == "start":
        result = start(args.config, gate_receipt=args.gate_receipt)
    elif args.command == "start-local":
        result = start_local(args.config)
    elif args.command == "verify":
        result = verify(args.config)
    elif args.command == "stop":
        result = stop(args.state)
    else:
        result = status(args.state)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
