"""Local, redacted Task 31 security configuration scanner.

This scanner never prints secret values and does not claim a network advisory scan.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAKID[A-Za-z0-9]{12,}\b"),
)
SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".json", ".yaml", ".yml"}


def _tracked_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True
    )
    return [root / name.decode("utf-8") for name in result.stdout.split(b"\0") if name]


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def run_scan(root: Path = ROOT) -> dict:
    tracked = _tracked_files(root)
    source_files = [
        path for path in tracked
        if path.suffix.lower() in SOURCE_SUFFIXES or path.name == "Dockerfile"
    ]
    secret_hits: list[str] = []
    for path in source_files:
        relative = path.relative_to(root).as_posix()
        if relative.startswith(("docs/", "content/", "backend/tests/", "apps/web/tests/")):
            continue
        text = _read(path)
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            secret_hits.append(relative)

    requirements = _read(root / "backend" / "requirements.txt").splitlines()
    dependencies = [line.strip() for line in requirements if line.strip() and not line.lstrip().startswith("#")]
    unpinned = [line for line in dependencies if "==" not in line]
    docker = _read(root / "Dockerfile")
    config = _read(root / "backend" / "config.py")
    app = _read(root / "backend" / "app.py")
    forbidden_artifacts = [
        path.relative_to(root).as_posix()
        for path in tracked
        if path.suffix.lower() in {".db", ".sqlite", ".sqlite3", ".pem", ".key"}
        or any(part in {"node_modules", "__pycache__", ".venv", "dist"} for part in path.parts)
    ]
    checks = [
        {"id": "tracked_secret_patterns", "status": "passed" if not secret_hits else "failed", "severity": "blocker", "count": len(secret_hits), "paths": secret_hits},
        {"id": "dependency_pins", "status": "passed" if not unpinned else "failed", "severity": "warning", "count": len(unpinned), "packages": unpinned},
        {"id": "container_non_root", "status": "passed" if "USER safehome" in docker else "failed", "severity": "blocker"},
        {"id": "cors_allowlist", "status": "passed" if "origin in app.config.get(\"ALLOWED_ORIGINS\"" in app else "failed", "severity": "blocker"},
        {"id": "production_default_secret_guards", "status": "passed" if "生产环境禁止使用默认 SECRET_KEY" in config and "生产环境禁止使用默认 ADMIN_EXPORT_TOKEN" in config else "failed", "severity": "blocker"},
        {"id": "api_security_headers", "status": "passed" if all(name in app for name in ("X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy", "Permissions-Policy")) else "failed", "severity": "blocker"},
        {"id": "tracked_runtime_artifacts", "status": "passed" if not forbidden_artifacts else "failed", "severity": "blocker", "count": len(forbidden_artifacts), "paths": forbidden_artifacts},
        {"id": "network_dependency_advisories", "status": "evidence_pending", "severity": "external_gate", "reason": "本地离线扫描不连接漏洞库，需CI或获批网络环境生成依赖告警证据。"},
    ]
    blockers = [item["id"] for item in checks if item["status"] == "failed" and item["severity"] == "blocker"]
    warnings = [item["id"] for item in checks if item["status"] in {"failed", "evidence_pending"} and item["severity"] != "blocker"]
    payload = {
        "schema": "safehome.task31.security_scan.v1",
        "mode": "local_static_redacted",
        "hard_checks_passed": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "checks": checks,
        "secret_values_returned": False,
        "production_approval_inferred": False,
    }
    payload["artifact_hash"] = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run_scan()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"security scan: blockers={len(result['blockers'])}; warnings={len(result['warnings'])}; hash={result['artifact_hash'][:16]}")
    return 0 if result["hard_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
