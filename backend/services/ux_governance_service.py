"""Task 33 UX coverage, automated evidence and human-gate packaging."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from flask import current_app

from database import get_connection, json_dumps, json_loads, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "content" / "ux_experience_registry.json"
ALLOWED_ENVIRONMENTS = {"local_automated", "test_cloud_evidence_pending"}
ALLOWED_PLATFORMS = {"web", "miniprogram", "cross_platform"}
ALLOWED_CHECKS = {"touch_target", "contrast", "focus_visible", "accessible_name", "heading_order", "form_association", "horizontal_overflow", "reduced_motion"}
ALLOWED_STATUSES = {"passed", "failed", "manual_required", "not_run"}


class UXGovernanceError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400, details: dict | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.details = details or {}


def _registry() -> dict:
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UXGovernanceError("ux_registry_unavailable", "体验覆盖注册表暂时不可用。", 503) from exc


def _hash(payload: object) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _expand(row) -> dict:
    item = row_to_dict(row)
    for key in ("results_json", "package_json"):
        if key in item:
            item[key.removesuffix("_json")] = json_loads(item.pop(key), {})
    for key in ("contains_participant_text", "human_research_approved", "device_acceptance_approved", "release_approved"):
        if key in item:
            item[key] = bool(item[key])
    return item


def get_registry() -> dict:
    return _registry()


def get_public_status() -> dict:
    registry = _registry()
    return {
        "status": registry["status"],
        "registry_version": registry["version"],
        "miniprogram_page_count": sum(item["platform"] == "miniprogram" for item in registry["pages"]),
        "web_route_count": sum(item["platform"] == "web" for item in registry["pages"]),
        "automated_gate_count": len(registry["automated_gates"]),
        "human_device_acceptance_approved": False,
        "formative_research_approved": False,
        "release_approved": False,
        "boundary_notice": registry["boundary_notice"],
    }


def list_audits(limit: int = 100) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM ux_audit_runs ORDER BY created_at DESC LIMIT ?", (max(1, min(int(limit), 200)),)).fetchall()
    return [_expand(row) for row in rows]


def workbench() -> dict:
    if not current_app.config.get("UX_GOVERNANCE_WORKBENCH_ENABLED", False):
        raise UXGovernanceError("ux_workbench_disabled", "当前环境未开启体验治理工作台。", 503)
    registry = _registry()
    with get_connection() as conn:
        audits = rows_to_dicts(conn.execute("SELECT * FROM ux_audit_runs ORDER BY created_at DESC LIMIT 50").fetchall())
        packages = rows_to_dicts(conn.execute("SELECT * FROM ux_evidence_packages ORDER BY created_at DESC LIMIT 20").fetchall())
    return {
        "registry": registry,
        "audit_runs": [_expand(item) for item in audits],
        "evidence_packages": [_expand(item) for item in packages],
        "external_gates": registry["external_gates"],
        "human_device_acceptance_approved": False,
        "formative_research_approved": False,
        "release_approved": False,
    }


def create_audit_run(actor: dict, payload: dict) -> dict:
    unknown = set(payload) - {"environment", "platform", "viewport", "results"}
    if unknown:
        raise UXGovernanceError("validation_error", "体验审计只接受环境、平台、视口和固定检查结果。", details={"unknown_fields": sorted(unknown)})
    environment = str(payload.get("environment") or "local_automated")
    platform = str(payload.get("platform") or "cross_platform")
    viewport = str(payload.get("viewport") or "automated_matrix")[:80]
    results = payload.get("results")
    if environment not in ALLOWED_ENVIRONMENTS or platform not in ALLOWED_PLATFORMS or not isinstance(results, dict):
        raise UXGovernanceError("validation_error", "环境、平台或检查结果无效。")
    if set(results) != ALLOWED_CHECKS:
        raise UXGovernanceError("validation_error", "必须提交完整的八项固定体验检查。", details={"required_checks": sorted(ALLOWED_CHECKS)})
    normalized = {}
    for name, value in results.items():
        if not isinstance(value, dict) or set(value) - {"status", "checked", "issues", "artifact"}:
            raise UXGovernanceError("validation_error", f"{name} 检查结果字段无效。")
        status = str(value.get("status") or "not_run")
        checked = int(value.get("checked") or 0)
        issues = int(value.get("issues") or 0)
        artifact = str(value.get("artifact") or "")[:200]
        if status not in ALLOWED_STATUSES or checked < 0 or issues < 0:
            raise UXGovernanceError("validation_error", f"{name} 检查结果值无效。")
        normalized[name] = {"status": status, "checked": checked, "issues": issues, "artifact": artifact}
    overall = "failed" if any(item["status"] == "failed" or item["issues"] > 0 for item in normalized.values()) else "local_automated_passed_external_manual_pending"
    registry = _registry()
    audit_id = new_id("ux_audit")
    timestamp = now_iso()
    artifact_hash = _hash({"environment": environment, "platform": platform, "viewport": viewport, "results": normalized, "registry_version": registry["version"]})
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO ux_audit_runs
               (id, environment, platform, viewport, registry_version, results_json,
                artifact_hash, status, contains_participant_text, created_by, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)""",
            (audit_id, environment, platform, viewport, registry["version"], json_dumps(normalized), artifact_hash, overall, actor["id"], timestamp),
        )
        write_audit_log(conn, "ux_audit_recorded", actor["id"], "ux_audit_run", audit_id, {"environment": environment, "platform": platform, "status": overall, "contains_participant_text": False})
        conn.commit()
        row = conn.execute("SELECT * FROM ux_audit_runs WHERE id = ?", (audit_id,)).fetchone()
    return _expand(row)


def create_evidence_package(actor: dict) -> dict:
    registry = _registry()
    with get_connection() as conn:
        audit_count = int(conn.execute("SELECT COUNT(*) AS count FROM ux_audit_runs").fetchone()["count"])
        passed_count = int(conn.execute("SELECT COUNT(*) AS count FROM ux_audit_runs WHERE status = 'local_automated_passed_external_manual_pending'").fetchone()["count"])
        package = {
            "registry_version": registry["version"],
            "page_coverage": {"total": len(registry["pages"]), "miniprogram": sum(item["platform"] == "miniprogram" for item in registry["pages"]), "web": sum(item["platform"] == "web" for item in registry["pages"])},
            "automated_audits": {"total": audit_count, "passed": passed_count},
            "external_gates": registry["external_gates"],
            "human_research_approved": False,
            "device_acceptance_approved": False,
            "release_approved": False,
            "human_signatures": [],
        }
        package_id = new_id("ux_evidence")
        timestamp = now_iso()
        artifact_hash = _hash(package)
        conn.execute(
            """INSERT INTO ux_evidence_packages
               (id, status, package_json, artifact_hash, human_research_approved,
                device_acceptance_approved, release_approved, created_by, created_at)
               VALUES (?, 'draft_for_human_ux_review', ?, ?, 0, 0, 0, ?, ?)""",
            (package_id, json_dumps(package), artifact_hash, actor["id"], timestamp),
        )
        write_audit_log(conn, "ux_evidence_package_created", actor["id"], "ux_evidence_package", package_id, {"release_approved": False})
        conn.commit()
    return {"id": package_id, "status": "draft_for_human_ux_review", **package, "artifact_hash": artifact_hash, "created_at": timestamp}
