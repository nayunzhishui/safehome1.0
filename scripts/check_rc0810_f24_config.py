"""Generate/check the F24 inventory of direct environment reads."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
INVENTORY = ROOT / "config" / "rc0810" / "config_read_inventory.json"

EXPLICIT_PROFILES = {
    "backend/config.py": "flask_config_source",
    "backend/app.py": "application_boot_profile",
    "backend/gunicorn.conf.py": "gunicorn_server_profile",
    "backend/services/agent_runtime_service.py": "agent_runtime_profile",
    "backend/services/ai_qa_provider.py": "ai_provider_profile",
    "backend/services/build_fingerprint_service.py": "build_identity_profile",
    "backend/services/embedding_service.py": "embedding_provider_profile",
    "backend/services/family_binding_service.py": "binding_security_profile",
    "backend/services/mysql_pool_runtime.py": "mysql_infrastructure_profile",
    "backend/services/rag_v2_service.py": "rag_infrastructure_profile",
    "backend/services/redis_service.py": "redis_infrastructure_profile",
    "backend/services/research_execution_manifest_service.py": "research_build_profile",
    "backend/services/runtime_bootstrap.py": "pre_app_infrastructure_profile",
}


def _source_sha256(path: Path) -> str:
    raw = path.read_bytes()
    normalized = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(normalized).hexdigest()


def _environment_name(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return "<dynamic>"


def _reads(path: Path) -> list[dict]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    found: list[dict] = []
    for node in ast.walk(tree):
        name = None
        access = None
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            owner = node.func.value
            if isinstance(owner, ast.Attribute) and isinstance(owner.value, ast.Name) and owner.value.id == "os" and owner.attr == "environ" and node.func.attr == "get":
                name = _environment_name(node.args[0]) if node.args else "<dynamic>"
                access = "os.environ.get"
            elif isinstance(owner, ast.Name) and owner.id == "os" and node.func.attr == "getenv":
                name = _environment_name(node.args[0]) if node.args else "<dynamic>"
                access = "os.getenv"
        elif isinstance(node, ast.Subscript):
            owner = node.value
            if isinstance(owner, ast.Attribute) and isinstance(owner.value, ast.Name) and owner.value.id == "os" and owner.attr == "environ":
                name = _environment_name(node.slice)
                access = "os.environ[]"
        if access:
            found.append({"line": int(node.lineno), "name": name, "access": access})
    return sorted(found, key=lambda item: (item["line"], item["name"], item["access"]))


def build_inventory() -> dict:
    reads = []
    unclassified = []
    for path in sorted(BACKEND.rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        if "/tests/" in f"/{relative}/" or relative.startswith("backend/tests/"):
            continue
        items = _reads(path)
        if not items:
            continue
        profile = "cli_profile" if relative.startswith("backend/scripts/") else EXPLICIT_PROFILES.get(relative)
        source_hash = _source_sha256(path)
        record = {"file": relative, "profile": profile, "source_sha256": source_hash, "reads": items}
        reads.append(record)
        if profile is None:
            unclassified.append(relative)
    return {
        "schema": "safehome.rc0810.config-read-inventory.v1",
        "policy": "Runtime routes read current_app/Config; direct environment access is confined to registered startup, provider, build or CLI profiles.",
        "reads": reads,
        "unclassified_reads": sorted(unclassified),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    current = build_inventory()
    if current["unclassified_reads"]:
        print("unclassified config reads: " + ", ".join(current["unclassified_reads"]))
        return 1
    rendered = json.dumps(current, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        INVENTORY.parent.mkdir(parents=True, exist_ok=True)
        INVENTORY.write_text(rendered, encoding="utf-8")
        print(f"generated {INVENTORY.relative_to(ROOT).as_posix()}")
        return 0
    if not INVENTORY.exists() or INVENTORY.read_text(encoding="utf-8") != rendered:
        print("config read inventory drift; run with --write")
        return 1
    print(f"config inventory check passed: {sum(len(item['reads']) for item in current['reads'])} reads")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
