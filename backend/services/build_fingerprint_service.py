"""Safe build identity and deployment-consistency checks for task 36 F09."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from database import CURRENT_SCHEMA_NAME, CURRENT_SCHEMA_VERSION


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
DEFAULT_API_CONTRACT_PATH = ROOT / "shared" / "contracts" / "api-contract.json"
DEFAULT_BUILD_INFO_PATH = BACKEND / "build_info.json"
HASH_PATTERN_LENGTH = 64


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_hash(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def api_contract_hash(project_root: Path = ROOT) -> str:
    path = project_root / "shared" / "contracts" / "api-contract.json"
    return _sha256_file(path) if path.exists() else "missing"


def content_manifest_hash(content_dir: Path) -> str:
    entries = []
    ignored_names = {"__pycache__", ".pytest_cache", ".DS_Store"}
    for path in sorted(content_dir.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file() or any(part in ignored_names for part in path.parts):
            continue
        entries.append(
            {
                "path": path.relative_to(content_dir).as_posix(),
                "sha256": _sha256_file(path),
            }
        )
    return _canonical_hash(entries)


def generate_build_info(
    project_root: Path,
    *,
    commit_sha: str,
    build_time: str,
    content_dir: Path | None = None,
) -> dict:
    content_root = content_dir or project_root / "content"
    payload = {
        "schema": "safehome.build-fingerprint.v1",
        "commit_sha": str(commit_sha or "unknown")[:64],
        "build_time": str(build_time or "unknown")[:64],
        "api_contract_hash": api_contract_hash(project_root),
        "content_manifest_hash": content_manifest_hash(content_root),
    }
    payload["build_id"] = _canonical_hash(payload)[:20]
    return payload


def _valid_hash(value: object) -> bool:
    text = str(value or "")
    return len(text) == HASH_PATTERN_LENGTH and all(character in "0123456789abcdef" for character in text.lower())


def load_build_identity(content_dir: Path) -> dict:
    current_api_hash = api_contract_hash(ROOT)
    current_content_hash = content_manifest_hash(content_dir)
    configured_path = Path(os.environ.get("BUILD_INFO_PATH", DEFAULT_BUILD_INFO_PATH))
    configured = {}
    source = "local_unpacked"
    if configured_path.exists():
        try:
            candidate = json.loads(configured_path.read_text(encoding="utf-8-sig"))
            if isinstance(candidate, dict):
                configured = candidate
                source = "packaged_manifest"
        except (OSError, json.JSONDecodeError):
            source = "invalid_manifest"
    configured_api_hash = str(
        os.environ.get("BUILD_API_CONTRACT_HASH")
        or configured.get("api_contract_hash")
        or current_api_hash
    ).lower()
    configured_content_hash = str(
        os.environ.get("BUILD_CONTENT_MANIFEST_HASH")
        or configured.get("content_manifest_hash")
        or current_content_hash
    ).lower()
    commit_sha = str(os.environ.get("BUILD_COMMIT_SHA") or configured.get("commit_sha") or "local-unpacked")[:64]
    build_time = str(os.environ.get("BUILD_TIME_UTC") or configured.get("build_time") or "not-packaged")[:64]
    base = {
        "schema": "safehome.build-fingerprint.v1",
        "commit_sha": commit_sha,
        "build_time": build_time,
        "api_contract_hash": configured_api_hash,
        "content_manifest_hash": configured_content_hash,
    }
    build_id = str(configured.get("build_id") or _canonical_hash(base)[:20])[:32]
    manifest_valid = bool(
        source == "packaged_manifest"
        and configured.get("schema") == "safehome.build-fingerprint.v1"
        and _valid_hash(configured_api_hash)
        and _valid_hash(configured_content_hash)
        and commit_sha not in {"", "unknown", "local-unpacked"}
        and build_time not in {"", "unknown", "not-packaged"}
    )
    return {
        **base,
        "build_id": build_id,
        "source": source,
        "manifest_valid": manifest_valid,
        "current_api_contract_hash": current_api_hash,
        "current_content_manifest_hash": current_content_hash,
        "schema_expected": {
            "version": CURRENT_SCHEMA_VERSION,
            "name": CURRENT_SCHEMA_NAME,
        },
    }


def public_build_identity(identity: dict) -> dict:
    return {
        key: identity.get(key)
        for key in (
            "schema",
            "build_id",
            "commit_sha",
            "build_time",
            "api_contract_hash",
            "content_manifest_hash",
            "source",
            "manifest_valid",
            "schema_expected",
        )
    }


def deployment_consistency(identity: dict, database: dict, app_env: str) -> dict:
    api_matches = bool(
        _valid_hash(identity.get("api_contract_hash"))
        and identity.get("api_contract_hash") == identity.get("current_api_contract_hash")
    )
    content_matches = bool(
        _valid_hash(identity.get("content_manifest_hash"))
        and identity.get("content_manifest_hash") == identity.get("current_content_manifest_hash")
    )
    schema_matches = bool(database.get("schema_version_ok"))
    production = str(app_env or "").lower() == "production"
    manifest_required_and_missing = production and not identity.get("manifest_valid")
    if manifest_required_and_missing:
        diagnosis = "build_identity_missing_or_invalid"
    elif not api_matches:
        diagnosis = "backend_contract_mismatch"
    elif not content_matches:
        diagnosis = "content_manifest_mismatch"
    elif not schema_matches:
        diagnosis = "database_schema_mismatch"
    else:
        diagnosis = "consistent"
    return {
        "ok": diagnosis == "consistent",
        "diagnosis": diagnosis,
        "api_contract_matches": api_matches,
        "content_manifest_matches": content_matches,
        "schema_matches": schema_matches,
        "build_manifest_required": production,
        "build_manifest_valid": bool(identity.get("manifest_valid")),
        "boundary_notice": "指纹只用于区分部署版本，不表示人工、伦理、真机或生产发布已批准。",
    }
