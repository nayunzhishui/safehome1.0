"""Fail-closed database profile checks without exposing connection details."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT_PATH = ROOT / "config" / "rc0810" / "database_profiles.json"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_SYNTHETIC_CATEGORIES = {
    "new_user",
    "legacy_user",
    "locked_user",
    "disabled_user",
    "historical_assessment",
    "training_checkin",
    "message",
    "research_task",
    "therapeutic_assessment",
}


def load_database_profiles(path: str | Path | None = None) -> dict[str, Any]:
    contract_path = Path(path or DEFAULT_CONTRACT_PATH)
    payload = json.loads(contract_path.read_text(encoding="utf-8"))
    if payload.get("schema") != "safehome.rc0810.database-profiles.v1":
        raise RuntimeError("数据库 profile 合同版本无效")
    return payload


def host_sha256(host: str) -> str:
    normalized = str(host or "").strip().lower().rstrip(".")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def startup_profile_errors(settings: Any, contract: dict[str, Any] | None = None) -> list[str]:
    payload = contract or load_database_profiles(getattr(settings, "DB_PROFILE_CONTRACT_PATH", None))
    env = str(getattr(settings, "APP_ENV", "development") or "development").lower()
    profile = payload.get("profiles", {}).get(env)
    if not isinstance(profile, dict):
        return ["database_profile_unknown_environment"]

    provider = str(getattr(settings, "DB_PROVIDER", "") or "").lower()
    errors: list[str] = []
    if provider not in set(profile.get("providers", [])):
        errors.append("database_provider_not_allowed")
    if str(getattr(settings, "DATABASE_DATA_WATERMARK", "")) != profile.get("data_watermark"):
        errors.append("database_data_watermark_mismatch")

    if env == "validation" and provider == "sqlite" and not bool(
        getattr(settings, "DATABASE_PATH_EXPLICIT", False)
    ):
        errors.append("validation_sqlite_path_not_explicit")

    if env != "production":
        return errors

    if bool(getattr(settings, "ALLOW_PRODUCTION_SQLITE", False)):
        errors.append("production_sqlite_override_forbidden")
    required = {
        "DB_PROFILE_APPROVAL_ID": getattr(settings, "DB_PROFILE_APPROVAL_ID", ""),
        "DB_APPROVED_HOST_SHA256": getattr(settings, "DB_APPROVED_HOST_SHA256", ""),
        "DB_APPROVED_DATABASE": getattr(settings, "DB_APPROVED_DATABASE", ""),
        "DB_APPROVED_MIGRATION_HEAD": getattr(settings, "DB_APPROVED_MIGRATION_HEAD", ""),
    }
    if any(not str(value or "").strip() for value in required.values()):
        errors.append("production_database_approval_missing")
        return errors

    approved_host = str(required["DB_APPROVED_HOST_SHA256"]).lower()
    if not SHA256_PATTERN.fullmatch(approved_host) or approved_host != host_sha256(
        str(getattr(settings, "MYSQL_HOST", ""))
    ):
        errors.append("production_database_host_not_approved")
    if str(required["DB_APPROVED_DATABASE"]) != str(getattr(settings, "MYSQL_DATABASE", "")):
        errors.append("production_database_name_not_approved")
    if int(getattr(settings, "DB_APPROVED_PORT", 0) or 0) != int(
        getattr(settings, "MYSQL_PORT", 0) or 0
    ):
        errors.append("production_database_port_not_approved")
    if str(required["DB_APPROVED_MIGRATION_HEAD"]) != str(profile.get("approved_migration_head")):
        errors.append("production_database_migration_head_not_approved")
    return errors


def granted_privileges(grant_rows: Iterable[Any]) -> set[str]:
    privileges: set[str] = set()
    for row in grant_rows:
        if isinstance(row, dict):
            text = " ".join(str(value) for value in row.values())
        else:
            text = str(row[0] if isinstance(row, (tuple, list)) and row else row)
        upper = text.upper()
        if "ALL PRIVILEGES" in upper:
            return {"ALL PRIVILEGES"}
        match = re.search(r"\bGRANT\s+(.+?)\s+ON\s+", upper)
        if match:
            privileges.update(item.strip() for item in match.group(1).split(","))
    return privileges


def runtime_profile_errors(settings: Any, facts: dict[str, Any], contract: dict[str, Any] | None = None) -> list[str]:
    payload = contract or load_database_profiles(getattr(settings, "DB_PROFILE_CONTRACT_PATH", None))
    errors = startup_profile_errors(settings, payload)
    env = str(getattr(settings, "APP_ENV", "development") or "development").lower()
    if env != "production":
        return errors
    profile = payload["profiles"]["production"]
    if facts.get("database_name") != str(getattr(settings, "DB_APPROVED_DATABASE", "")):
        errors.append("connected_database_not_approved")
    if facts.get("legacy_schema_version") != profile.get("legacy_schema_version"):
        errors.append("legacy_schema_version_mismatch")
    if facts.get("explicit_migration_head") != profile.get("explicit_migration_head"):
        errors.append("explicit_migration_head_mismatch")
    if facts.get("server_read_only") is True:
        errors.append("database_server_read_only")
    privileges = set(facts.get("privileges", set()))
    required = set(profile.get("required_runtime_privileges", []))
    if "ALL PRIVILEGES" not in privileges and not required.issubset(privileges):
        errors.append("database_runtime_privileges_insufficient")
    return errors


def public_database_fingerprint(settings: Any, facts: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider": str(getattr(settings, "DB_PROVIDER", "")),
        "environment": str(getattr(settings, "APP_ENV", "")),
        "schema_version": facts.get("legacy_schema_version"),
        "migration_head": facts.get("explicit_migration_head"),
        "host_sha256": host_sha256(str(getattr(settings, "MYSQL_HOST", "")))
        if str(getattr(settings, "DB_PROVIDER", "")) == "mysql"
        else None,
        "data_watermark": str(getattr(settings, "DATABASE_DATA_WATERMARK", "")),
    }


def validate_synthetic_migration_fixture(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema") != "safehome.rc0810.database-migration-fixture.v1":
        errors.append("fixture_schema_invalid")
    before = payload.get("before") if isinstance(payload.get("before"), list) else []
    after = payload.get("after") if isinstance(payload.get("after"), list) else []
    before_categories = {str(item.get("category")) for item in before if isinstance(item, dict)}
    if before_categories != REQUIRED_SYNTHETIC_CATEGORIES:
        errors.append("fixture_categories_incomplete")
    if any(set(item) != {"category", "id", "owner_id", "count", "status", "version"} for item in before + after):
        errors.append("fixture_fields_invalid")
    before_map = {str(item.get("category")): item for item in before}
    after_map = {str(item.get("category")): item for item in after}
    if before_map != after_map:
        errors.append("migration_manifest_mismatch")
    return errors
