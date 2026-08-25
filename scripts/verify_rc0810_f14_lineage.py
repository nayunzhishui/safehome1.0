"""Validate the RC0810-F14-B privacy-lineage rescan without mutating data."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "config" / "rc0810" / "privacy_lineage.schema.json"
CATALOG_PATH = ROOT / "config" / "rc0810" / "privacy_lineage_catalog.json"
TABLE_RE = re.compile(
    r"CREATE\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+[`\"']?([A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE,
)
TABLE_BLOCK_RE = re.compile(
    r"CREATE\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+[`\"']?"
    r"([A-Za-z_][A-Za-z0-9_]*)[`\"']?\s*\((.*?)\)\s*(?:\"\"\"|''')",
    re.IGNORECASE | re.DOTALL,
)
ENDPOINT_RE = re.compile(
    r"https://([A-Za-z0-9.-]+)(/[A-Za-z0-9._~!$&'()*+,;=:@%/-]*)?",
    re.IGNORECASE,
)
OUTBOUND_MARKERS = ("urlopen(", "urllib.request.urlopen(", "HTTPSConnection(")
SENSITIVE_VALUE_RE = re.compile(
    r"(?i)(?:bearer\s+[a-z0-9._-]{8,}|sk-[a-z0-9_-]{8,}|"
    r"(?:secret|token|password|api[_-]?key)=[^&\s\"']{6,})"
)
NON_COLUMN_PREFIXES = {"primary", "unique", "foreign", "constraint", "check"}
PHASE_B_REQUIRED_ASSETS = {
    "content_release_artifacts",
    "content_active_artifacts",
    "research_source_objects",
    "research_execution_manifests",
    "ai_capability_decisions",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_sha256(paths: list[Path]) -> str:
    manifest = {
        path.relative_to(ROOT).as_posix(): sha256_file(path)
        for path in sorted(paths)
    }
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def current_source_bindings(models_path: Path | None = None) -> dict[str, str]:
    models = models_path or ROOT / "backend" / "models.py"
    return {
        "models_sha256": sha256_file(models),
        "migration_manifest_sha256": manifest_sha256(
            list((ROOT / "backend" / "scripts").glob("migrate_*.py"))
        ),
        "route_manifest_sha256": manifest_sha256(
            list((ROOT / "backend" / "routes").glob("*.py"))
        ),
        "service_manifest_sha256": manifest_sha256(
            list((ROOT / "backend" / "services").glob("*.py"))
        ),
    }


def source_paths(models_path: Path | None = None) -> list[Path]:
    return [
        models_path or ROOT / "backend" / "models.py",
        *(ROOT / "backend" / "scripts").glob("migrate_*.py"),
        ROOT / "backend" / "services" / "schema_migration_service.py",
    ]


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def discover_tables(models_path: Path | None = None) -> dict[str, list[str]]:
    discovered: dict[str, list[str]] = {}
    for path in source_paths(models_path):
        text = path.read_text(encoding="utf-8")
        relative = _display_path(path)
        for table_name in TABLE_RE.findall(text):
            discovered.setdefault(table_name, []).append(relative)
    return {name: sorted(set(paths)) for name, paths in sorted(discovered.items())}


def discover_columns(models_path: Path | None = None) -> dict[str, list[str]]:
    columns: dict[str, set[str]] = {}
    for path in source_paths(models_path):
        text = path.read_text(encoding="utf-8")
        for table_name, body in TABLE_BLOCK_RE.findall(text):
            for raw_line in re.split(r"[,\n]", body):
                line = raw_line.strip()
                if not line:
                    continue
                token = line.split()[0].strip("`\"'[]").lower()
                if token in NON_COLUMN_PREFIXES or not re.fullmatch(
                    r"[a-z_][a-z0-9_]*", token
                ):
                    continue
                columns.setdefault(table_name, set()).add(token)
    return {name: sorted(values) for name, values in columns.items()}


def access_paths(table_names: set[str]) -> dict[str, list[str]]:
    result = {name: [] for name in table_names}
    code_paths = [
        *(ROOT / "backend" / "routes").glob("*.py"),
        *(ROOT / "backend" / "services").glob("*.py"),
    ]
    for path in code_paths:
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT).as_posix()
        identifiers = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text))
        for table_name in table_names & identifiers:
            result[table_name].append(relative)
    return {name: sorted(paths) for name, paths in result.items()}


def _subject_keys(columns: list[str]) -> list[str]:
    exact = {
        "user_id",
        "parent_id",
        "student_id",
        "participant_id",
        "subject_id",
        "subject_hash",
        "anonymous_id",
        "wechat_openid",
        "phone_hash",
    }
    return sorted(
        column
        for column in columns
        if column in exact
        or column.endswith("_user_id")
        or ("participant" in column and column.endswith("_id"))
    )


def _actor_keys(columns: list[str]) -> list[str]:
    exact = {
        "actor_id",
        "reviewer_id",
        "handled_by",
        "created_by",
        "updated_by",
        "approved_by",
        "researcher_id",
        "admin_id",
        "supervisor_id",
    }
    return sorted(column for column in columns if column in exact)


def generated_external_processors() -> list[dict[str, Any]]:
    code_paths = [
        *(ROOT / "backend" / "routes").glob("*.py"),
        *(ROOT / "backend" / "services").glob("*.py"),
    ]
    endpoint_sources: dict[str, set[str]] = {}
    dynamic_sources: set[str] = set()
    for path in code_paths:
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT).as_posix()
        endpoints = {
            f"https://{host.lower()}{path or '/'}"
            for host, path in ENDPOINT_RE.findall(text)
        }
        for endpoint in endpoints:
            endpoint_sources.setdefault(endpoint, set()).add(relative)
        if any(marker in text for marker in OUTBOUND_MARKERS) and not endpoints:
            dynamic_sources.add(relative)

    entries: list[tuple[str, str, str, list[str]]] = []
    for endpoint, paths in sorted(endpoint_sources.items()):
        entries.append((f"endpoint:{endpoint}", "fixed_endpoint", endpoint, sorted(paths)))
    for path in sorted(dynamic_sources):
        entries.append((f"dynamic:{path}", "dynamic_endpoint", "pending_runtime_value", [path]))
    return [
        {
            "processor_id": processor_id,
            "endpoint_kind": endpoint_kind,
            "endpoint": endpoint,
            "source_files": paths,
            "fields": "pending_privacy_owner_confirmation",
            "purpose": "pending_privacy_owner_confirmation",
            "necessity": "pending_privacy_owner_confirmation",
            "sensitivity": "pending_privacy_owner_confirmation",
            "retention": "pending_privacy_owner_confirmation",
            "processor_role": "pending_privacy_owner_confirmation",
            "export_capability": "pending_privacy_owner_confirmation",
            "deletion_capability": "pending_privacy_owner_confirmation",
            "privacy_notice_status": "pending_external",
            "review_status": "pending_external",
        }
        for processor_id, endpoint_kind, endpoint, paths in entries
    ]


def generated_assets(models_path: Path | None = None) -> list[dict[str, Any]]:
    tables = discover_tables(models_path)
    columns_by_table = discover_columns(models_path)
    accesses = access_paths(set(tables))
    return [
        {
            "asset_id": f"table:{table_name}",
            "table_name": table_name,
            "schema_sources": paths,
            "columns_sha256": hashlib.sha256(
                "\n".join(columns_by_table.get(table_name, [])).encode("utf-8")
            ).hexdigest(),
            "subject_keys": _subject_keys(columns_by_table.get(table_name, [])),
            "actor_keys": _actor_keys(columns_by_table.get(table_name, [])),
            "relationship_keys": sorted(
                column
                for column in columns_by_table.get(table_name, [])
                if column != "id"
                and column.endswith("_id")
                and column not in _subject_keys(columns_by_table.get(table_name, []))
                and column not in _actor_keys(columns_by_table.get(table_name, []))
            ),
            "access_paths": accesses[table_name],
            "collection_purpose": "pending_privacy_owner_confirmation",
            "retention_policy": "pending_privacy_owner_confirmation",
            "export_policy": "pending_privacy_owner_confirmation",
            "deletion_policy": "pending_privacy_owner_confirmation",
            "anonymization_policy": "pending_privacy_owner_confirmation",
            "tombstone_policy": (
                "native_minimal_tombstone"
                if "tombstone" in table_name or "deletion_verification" in table_name
                else "pending_privacy_owner_confirmation"
            ),
            "external_processor_ids": [],
            "review_status": "pending_external",
        }
        for table_name, paths in tables.items()
    ]


def refresh_catalog(catalog_path: Path = CATALOG_PATH) -> None:
    catalog = load_json(catalog_path)
    catalog["schema"] = "safehome.rc0810.privacy-lineage.v2"
    catalog["version"] = "2026-08-25.f14b"
    catalog["phase"] = "phase_b_rescan"
    catalog["assets"] = generated_assets()
    catalog["external_processors"] = generated_external_processors()
    catalog["source_bindings"] = current_source_bindings()
    catalog_path.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def validate_catalog(
    catalog_path: Path = CATALOG_PATH, models_path: Path | None = None
) -> dict[str, Any]:
    schema = load_json(SCHEMA_PATH)
    catalog = load_json(catalog_path)
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(catalog)]
    scanned = set(discover_tables(models_path))
    registered = {
        item.get("table_name")
        for item in catalog.get("assets", [])
        if isinstance(item, dict) and isinstance(item.get("table_name"), str)
    }
    asset_id_counts = Counter(
        item.get("asset_id")
        for item in catalog.get("assets", [])
        if isinstance(item, dict) and isinstance(item.get("asset_id"), str)
    )
    duplicate_asset_ids = sorted(
        asset_id for asset_id, count in asset_id_counts.items() if count > 1
    )
    missing = sorted(scanned - registered)
    extra = sorted(registered - scanned)
    if missing:
        errors.append(f"unregistered_tables:{','.join(missing)}")
    if extra:
        errors.append(f"unknown_catalog_tables:{','.join(extra)}")
    if duplicate_asset_ids:
        errors.append("duplicate_asset_ids")
    phase_b_required_assets = set(
        catalog.get("phase_b_evidence", {}).get("required_assets", [])
    )
    phase_b_required_assets_current = (
        phase_b_required_assets == PHASE_B_REQUIRED_ASSETS
        and PHASE_B_REQUIRED_ASSETS <= registered
    )
    if phase_b_required_assets_current:
        asset_by_table = {
            item.get("table_name"): item
            for item in catalog.get("assets", [])
            if isinstance(item, dict)
        }
        phase_b_required_assets_current = all(
            asset_by_table[name].get("access_paths")
            for name in PHASE_B_REQUIRED_ASSETS
        ) and "actor_id" in asset_by_table["ai_capability_decisions"].get(
            "actor_keys", []
        )
    if not phase_b_required_assets_current:
        errors.append("phase_b_required_assets_stale")
    asset_catalog_matches = catalog.get("assets") == generated_assets(models_path)
    if not asset_catalog_matches:
        errors.append("asset_catalog_mismatch")
    source_bindings_current = catalog.get("source_bindings") == current_source_bindings(
        models_path
    )
    if not source_bindings_current:
        errors.append("source_bindings_stale")
    processor_catalog_matches = (
        catalog.get("external_processors") == generated_external_processors()
    )
    if not processor_catalog_matches:
        errors.append("external_processor_catalog_mismatch")
    sensitive_value_scan_passed = not SENSITIVE_VALUE_RE.search(
        json.dumps(catalog, ensure_ascii=False)
    )
    if not sensitive_value_scan_passed:
        errors.append("sensitive_value_detected")
    pending_asset_reviews = sum(
        item.get("review_status") == "pending_external"
        for item in catalog.get("assets", [])
        if isinstance(item, dict)
    )
    pending_processor_reviews = sum(
        item.get("review_status") == "pending_external"
        for item in catalog.get("external_processors", [])
        if isinstance(item, dict)
    )
    confirmed_privacy_reviews = sum(
        item.get("review_status") == "approved"
        for item in [
            *catalog.get("assets", []),
            *catalog.get("external_processors", []),
        ]
        if isinstance(item, dict)
    )
    owner_pending = catalog.get("privacy_owner", {}).get("status") != "approved"
    return {
        "valid": not errors,
        "status": "phase_b_ready" if not errors else "invalid",
        "privacy_owner_status": catalog.get("privacy_owner", {}).get("status"),
        "release_gate_eligible": False,
        "asset_count": len(registered),
        "processor_count": len(catalog.get("external_processors", [])),
        "scanned_table_count": len(scanned),
        "unregistered_tables": missing,
        "unknown_catalog_tables": extra,
        "duplicate_asset_ids": duplicate_asset_ids,
        "phase_b_required_assets_current": phase_b_required_assets_current,
        "asset_catalog_matches": asset_catalog_matches,
        "source_bindings_current": source_bindings_current,
        "processor_catalog_matches": processor_catalog_matches,
        "sensitive_value_scan_passed": sensitive_value_scan_passed,
        "pending_asset_reviews": pending_asset_reviews,
        "pending_processor_reviews": pending_processor_reviews,
        "confirmed_privacy_reviews": confirmed_privacy_reviews,
        "privacy_gap_count": pending_asset_reviews
        + pending_processor_reviews
        + int(owner_pending),
        "errors": errors,
    }


def run_self_checks() -> dict[str, bool]:
    source_catalog = load_json(CATALOG_PATH)
    with tempfile.TemporaryDirectory(prefix="rc0810-f14-self-check-") as directory:
        root = Path(directory)

        tampered = copy.deepcopy(source_catalog)
        tampered["assets"][0]["columns_sha256"] = "0" * 64
        tampered_path = root / "tampered.json"
        tampered_path.write_text(json.dumps(tampered), encoding="utf-8")
        tampered_result = validate_catalog(tampered_path)

        processor_removed = copy.deepcopy(source_catalog)
        processor_removed["external_processors"] = processor_removed[
            "external_processors"
        ][1:]
        processor_path = root / "processor-removed.json"
        processor_path.write_text(json.dumps(processor_removed), encoding="utf-8")
        processor_result = validate_catalog(processor_path)

        secret = copy.deepcopy(source_catalog)
        secret["external_processors"][0]["endpoint"] += "?secret=self-check-value"
        secret_path = root / "secret.json"
        secret_path.write_text(json.dumps(secret), encoding="utf-8")
        secret_result = validate_catalog(secret_path)

        models_path = root / "models.py"
        models_path.write_text(
            (ROOT / "backend" / "models.py").read_text(encoding="utf-8")
            + "\n'''CREATE TABLE IF NOT EXISTS rc0810_unregistered_self_check "
            "(id TEXT PRIMARY KEY, participant_user_id TEXT)'''\n",
            encoding="utf-8",
        )
        unregistered_result = validate_catalog(CATALOG_PATH, models_path)

    return {
        "embedded_secret_rejected": (
            not secret_result["valid"]
            and "sensitive_value_detected" in secret_result["errors"]
        ),
        "processor_removal_rejected": (
            not processor_result["valid"]
            and "external_processor_catalog_mismatch" in processor_result["errors"]
        ),
        "tampered_asset_rejected": (
            not tampered_result["valid"]
            and "asset_catalog_mismatch" in tampered_result["errors"]
        ),
        "unregistered_table_rejected": (
            not unregistered_result["valid"]
            and "rc0810_unregistered_self_check"
            in unregistered_result["unregistered_tables"]
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--refresh-catalog", action="store_true")
    parser.add_argument("--models", type=Path)
    args = parser.parse_args()
    if args.refresh_catalog:
        refresh_catalog(args.catalog)
    result = validate_catalog(args.catalog, args.models)
    if args.self_check and result["valid"]:
        result["self_checks"] = run_self_checks()
        if all(result["self_checks"].values()):
            result["status"] = "self_check_passed"
        else:
            result["valid"] = False
            result["status"] = "invalid"
            result["errors"].append("self_check_failed")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
