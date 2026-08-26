"""Build and verify the RC0810-F25-B local evidence packet.

The packet freezes only reproducible repository evidence. WeChat console,
DevTools, real-device and human results remain external and are never promoted
by this script.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "docs" / "02_专项进度与验收" / "rc0810_f25b_evidence.json"
ARTIFACT_ROOT = ROOT / ".codex_tmp" / "rc0810" / "f25b"
RELEASE_INPUTS = (
    "apps/miniprogram/app.json",
    "apps/miniprogram/project.config.json",
    "apps/miniprogram/services/cloudConfig.js",
    "config/rc0810/miniprogram_cloud_targets.json",
    "config/rc0810/miniprogram_page_policy.json",
    "content/privacy.md",
)
BACKEND_CONTEXTS = ("Dockerfile", ".dockerignore", "backend", "content", "shared")
ACCOUNT_SCENARIOS = (
    "wechat_one_tap_login", "phone_login", "account_login", "logout",
    "legacy_account", "locked_account", "multi_device_session",
)
MESSAGE_SCENARIOS = (
    "subscription_denied", "subscription_expired", "subscription_duplicate",
    "training_record", "historical_feedback", "researcher_feedback_message",
)
DEVICE_SCENARIOS = (
    "cold_start", "warm_start", "foreground_background", "weak_network",
    "offline_recovery", "large_font", "keyboard", "safe_area",
)
PLATFORM_CHECKS = (
    "appid_subject", "service_category", "interface_permissions", "legal_domains",
    "cloudbase_environment", "privacy_guideline", "filing_status",
    "qualification_materials",
)
DEVTOOLS_CHECKS = (
    "compile", "subpackages", "package_size", "network", "base_library",
    "page_warnings",
)
RACI_DOMAINS = (
    "filing_and_category", "privacy", "psychology_content", "deployment",
    "database", "ai_supplier", "device_acceptance", "incident_response",
)
REAL_WORLD_ITEMS = (
    "core_funnel", "failure_recovery", "user_understanding_interview",
    "human_processing_capacity",
)
BLOCKER_IDS = {
    "F25-EXT-01", "F25-EXT-02", "F25-EXT-03", "F25-EXT-04",
    "F25-EXT-05", "F25-EXT-06", "F25-EXT-07", "F25-EXT-08",
}


class EvidenceError(RuntimeError):
    pass


def _run(*argv: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[bytes]:
    completed = subprocess.run(argv, cwd=cwd, capture_output=True, check=False)
    if completed.returncode != 0:
        raise EvidenceError(
            completed.stderr.decode("utf-8", errors="replace")
            or completed.stdout.decode("utf-8", errors="replace")
        )
    return completed


def _git_bytes(*args: str) -> bytes:
    return _run("git", *args).stdout


def _git_text(*args: str) -> str:
    return _git_bytes(*args).decode("utf-8", errors="strict").strip()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_sha256(value: Any) -> str:
    return _sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def _git_file(commit: str, relative: str) -> bytes:
    return _git_bytes("show", f"{commit}:{relative}")


def _release_input_snapshot(commit: str) -> dict[str, Any]:
    files = {path: _sha256(_git_file(commit, path)) for path in RELEASE_INPUTS}
    project = json.loads(_git_file(commit, "apps/miniprogram/project.config.json"))
    cloud = json.loads(_git_file(commit, "config/rc0810/miniprogram_cloud_targets.json"))
    production = cloud["profiles"]["production"]
    appid = str(project["appid"])
    return {
        "files": files,
        "release_input_sha256": _canonical_sha256(files),
        "appid_fingerprint": f"sha256:{_sha256(appid.encode('utf-8'))}",
        "base_library_version": str(project["libVersion"]),
        "cloudbase_env_id": str(production["cloudEnvId"]),
        "cloudbase_service": str(production["containerService"]),
        "privacy_text_sha256": files["content/privacy.md"],
        "cloudbase_config_sha256": files["config/rc0810/miniprogram_cloud_targets.json"],
    }


def _backend_context_sha256(commit: str) -> str:
    return _sha256(_git_bytes("archive", "--format=tar", commit, "--", *BACKEND_CONTEXTS))


def _safe_extract_tar(payload: bytes, destination: Path) -> None:
    destination = destination.resolve()
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:") as archive:
        for member in archive.getmembers():
            target = (destination / member.name).resolve()
            if destination not in target.parents and target != destination:
                raise EvidenceError(f"unsafe archive entry: {member.name}")
        archive.extractall(destination, filter="data")


def _write_deterministic_zip(source: Path, target: Path) -> str:
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(item for item in source.rglob("*") if item.is_file()):
            relative = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    return _sha256(target.read_bytes())


def _sanitize_project_config(raw: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(raw)
    result["condition"] = {"miniprogram": {"list": []}}
    if result.get("setting", {}).get("urlCheck") is not True:
        raise EvidenceError("production project.config.json must keep urlCheck=true")
    return result


def build_miniprogram_package(commit: str, target: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="rc0810-f25b-source-") as directory:
        checkout = Path(directory) / "source"
        checkout.mkdir()
        _safe_extract_tar(_git_bytes("archive", "--format=tar", commit), checkout)
        output = Path(directory) / "production-package"
        completed = subprocess.run(
            [
                sys.executable,
                str(checkout / "scripts" / "build_rc0810_miniprogram.py"),
                "--profile", "production",
                "--output", str(output),
                "--copy-source",
            ],
            cwd=checkout,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise EvidenceError(completed.stderr or completed.stdout)
        audit = json.loads(completed.stdout)
        project = json.loads(
            (checkout / "apps" / "miniprogram" / "project.config.json").read_text(encoding="utf-8")
        )
        (output / "project.config.json").write_text(
            json.dumps(_sanitize_project_config(project), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        manifest = {
            "schema": "safehome.rc0810.f25b-miniprogram-manifest.v1",
            "source_commit": commit,
            "source_tree": _git_text("rev-parse", f"{commit}^{{tree}}"),
            "release_input_sha256": _release_input_snapshot(commit)["release_input_sha256"],
            "package_audit_sha256": _sha256((output / "rc0810-package-audit.json").read_bytes()),
            "profile": "production",
            "production_release_approved": False,
        }
        (output / "RC0810_F25B_MANIFEST.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        package_sha256 = _write_deterministic_zip(output, target)
    return {"sha256": package_sha256, "audit": audit, "manifest": manifest}


def _probe_docker() -> dict[str, Any]:
    completed = subprocess.run(
        ["docker", "version", "--format", "{{json .}}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return {"status": "pending_external", "image_digest": None, "blocker": "docker_daemon_unavailable"}
    return {"status": "pending_external", "image_digest": None, "blocker": "backend_image_not_built_in_f25b"}


def _devtools_cli_status() -> dict[str, Any]:
    configured = os.environ.get("WECHAT_DEVTOOLS_CLI")
    candidates = [
        configured,
        r"C:\Program Files (x86)\Tencent\微信web开发者工具\cli.bat",
        r"C:\Program Files\Tencent\微信web开发者工具\cli.bat",
    ]
    found = next((str(Path(item)) for item in candidates if item and Path(item).is_file()), None)
    return {
        "status": "pending_external",
        "cli_detected": bool(found),
        "cli_path": found,
        "blocker": "devtools_execution_not_performed" if found else "wechat_devtools_cli_not_found",
    }


def _pending(items: tuple[str, ...], owner: str, reviewer: str) -> list[dict[str, Any]]:
    return [
        {
            "id": item,
            "status": "pending_external",
            "owner": owner,
            "reviewer": reviewer,
            "captured_at": None,
            "valid_until": None,
            "request_id": None,
            "invalidation_conditions": ["package_or_image", "cloudbase_target", "test_account_or_data"],
        }
        for item in items
    ]


def build_report(
    report_path: Path = DEFAULT_REPORT,
    *,
    commit: str | None = None,
    docker_probe: Callable[[], dict[str, Any]] = _probe_docker,
) -> dict[str, Any]:
    commit = _git_text("rev-parse", commit or "HEAD")
    source_tree = _git_text("rev-parse", f"{commit}^{{tree}}")
    snapshot = _release_input_snapshot(commit)
    artifact_directory = ARTIFACT_ROOT / commit
    package_path = artifact_directory / "safehome-miniprogram-production.zip"
    package = build_miniprogram_package(commit, package_path)
    docker = docker_probe()
    report = {
        "schema": "safehome.rc0810.f25b-evidence.v1",
        "phase": "F25-B",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "engineering_status": "evidence_ready",
        "external_verification_complete": False,
        "production_gate_eligible": False,
        "release_recommendation": "NO_GO",
        "artifact_source": {
            "commit": commit,
            "source_tree": source_tree,
            "release_input_sha256": snapshot["release_input_sha256"],
            "backend_build_context_sha256": _backend_context_sha256(commit),
            "files": snapshot["files"],
        },
        "artifact_binding": {
            "miniprogram_package": {
                "path": package_path.relative_to(ROOT).as_posix(),
                "sha256": package["sha256"],
                "status": "evidence_ready",
                "profile": "production",
                "static_journey_gate_passed": package["audit"]["journey_gate_passed"],
                "size_bytes": package_path.stat().st_size,
            },
            "backend_image": docker,
            "appid_fingerprint": snapshot["appid_fingerprint"],
            "cloudbase_env_id": snapshot["cloudbase_env_id"],
            "cloudbase_service": snapshot["cloudbase_service"],
            "cloudbase_config_sha256": snapshot["cloudbase_config_sha256"],
            "privacy_text_sha256": snapshot["privacy_text_sha256"],
            "base_library_version": snapshot["base_library_version"],
        },
        "platform_checks": _pending(PLATFORM_CHECKS, "wechat_platform_operator", "independent_platform_reviewer"),
        "account_scenarios": _pending(ACCOUNT_SCENARIOS, "account_test_operator", "independent_qa_reviewer"),
        "message_scenarios": _pending(MESSAGE_SCENARIOS, "message_test_operator", "independent_qa_reviewer"),
        "devtools": {
            **_devtools_cli_status(),
            "checks": _pending(DEVTOOLS_CHECKS, "wechat_devtools_operator", "independent_qa_reviewer"),
            "raw_log_path": None,
        },
        "device_matrix": [
            {
                "platform": platform,
                "device_id": None,
                "operator_id": None,
                "reviewer_id": None,
                "status": "pending_external",
                "scenarios": list(DEVICE_SCENARIOS),
                "evidence_paths": [],
                "captured_at": None,
                "valid_until": None,
                "request_id": None,
                "invalidation_conditions": ["package_or_image", "base_library", "device_replacement"],
            }
            for platform in ("iOS", "Android")
        ],
        "journeys": {
            "participant_core": ["goal", "diary", "feedback", "training", "checkin", "weekly_report", "supervision"],
            "production_negative": ["internal_route_hidden", "temporary_privilege_disabled", "debug_entry_hidden"],
            "static_package_status": "evidence_ready",
            "real_device_status": "pending_external",
        },
        "review_materials": {
            "status": "evidence_ready",
            "review_notes": "使用冻结 production 候选包；不得口头补充、临时提权、改库或现场调试。",
            "test_account_guide": "账号由授权负责人在仓库外提供；仅使用冻结角色与测试数据，不在仓库保存凭据。",
            "feature_paths": ["目标→记录→反馈→训练→打卡→周报→督导", "消息→历次反馈→研究者反馈"],
            "boundary_statement": "系统提供非诊断、支持性训练；高风险内容进入人工支持路径，不替代诊断或危机干预。",
            "failure_recovery": "失败时保留请求 ID，使用页面重试；不得切换未登记环境、放宽权限或修改数据库绕过。",
        },
        "zero_context_review": {
            "status": "pending_external",
            "reviewer_id": None,
            "captured_at": None,
            "valid_until": None,
            "request_id": None,
            "invalidation_conditions": ["package_or_image", "test_account_or_data", "submitted_materials"],
            "allowed_inputs": ["submitted_materials", "test_account", "frozen_release_candidate"],
            "forbidden_assistance": ["oral_supplement", "database_mutation", "temporary_privilege", "live_debugging", "out_of_band_instruction"],
        },
        "freeze_window": {
            "status": "evidence_ready",
            "frozen_inputs": ["backend_contract", "test_accounts", "test_data", "miniprogram_package", "backend_image", "cloudbase_target", "privacy_text", "base_library"],
            "invalidation_rules": {
                "package_or_image": ["artifact", "device", "journey", "materials", "platform"],
                "cloudbase_target": ["platform", "journey", "device"],
                "privacy_text": ["privacy", "materials", "platform"],
                "base_library": ["devtools", "device", "journey"],
                "test_account_or_data": ["zero_context", "journey", "messages"],
            },
        },
        "raci": [
            {"domain": domain, "responsible": None, "accountable": None, "consulted": None, "informed": None, "status": "pending_external"}
            for domain in RACI_DOMAINS
        ],
        "real_world_evidence": [
            {
                "id": item,
                "owner": None,
                "reviewer": "independent_pilot_reviewer",
                "status": "pending_external",
                "evidence_paths": [],
                "captured_at": None,
                "valid_until": None,
                "request_id": None,
                "invalidation_conditions": ["pilot_scope", "package_or_image", "measurement_definition"],
            }
            for item in REAL_WORLD_ITEMS
        ],
        "subtasks": [
            {"id": f"F25.{number}", "status": "evidence_ready" if number in {8, 9, 10, 12} else "blocked_external"}
            for number in range(1, 15)
        ],
        "blockers": [
            {"id": "F25-EXT-01", "scope": "backend_image", "status": "pending_external", "reason": docker["blocker"]},
            {"id": "F25-EXT-02", "scope": "wechat_platform", "status": "pending_external", "reason": "console_receipts_and_qualifications_missing"},
            {"id": "F25-EXT-03", "scope": "accounts_and_messages", "status": "pending_external", "reason": "real_accounts_and_request_logs_missing"},
            {"id": "F25-EXT-04", "scope": "devtools", "status": "pending_external", "reason": _devtools_cli_status()["blocker"]},
            {"id": "F25-EXT-05", "scope": "ios_android", "status": "pending_external", "reason": "real_device_evidence_missing"},
            {"id": "F25-EXT-06", "scope": "zero_context_review", "status": "pending_external", "reason": "independent_human_review_missing"},
            {"id": "F25-EXT-07", "scope": "raci", "status": "pending_external", "reason": "authorized_people_not_assigned"},
            {"id": "F25-EXT-08", "scope": "real_world", "status": "pending_external", "reason": "pilot_observation_and_capacity_evidence_missing"},
        ],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def _package_errors(report: dict[str, Any], *, rebuild_missing: bool) -> list[str]:
    errors: list[str] = []
    binding = report.get("artifact_binding", {}).get("miniprogram_package", {})
    relative = binding.get("path")
    if not isinstance(relative, str) or not relative.startswith(".codex_tmp/rc0810/f25b/"):
        return ["package_path_invalid"]
    package_path = (ROOT / relative).resolve()
    if ROOT.resolve() not in package_path.parents:
        return ["package_path_outside_workspace"]
    commit = report.get("artifact_source", {}).get("commit")
    if not package_path.is_file() and rebuild_missing and isinstance(commit, str):
        build_miniprogram_package(commit, package_path)
    if not package_path.is_file():
        return ["package_missing"]
    if _sha256(package_path.read_bytes()) != binding.get("sha256"):
        errors.append("package_sha256_mismatch")
        return errors
    with zipfile.ZipFile(package_path) as archive:
        names = set(archive.namelist())
        forbidden = {
            "project.private.config.json",
            "pages/debug/index.js",
            "pages/integration-test/index.js",
            "pages/researcher-dashboard/index.js",
            "pages/therapeutic-assessment-quality/index.js",
        }
        if names & forbidden:
            errors.append("production_package_contains_internal_surface")
        required = {"app.json", "project.config.json", "rc0810-package-audit.json", "RC0810_F25B_MANIFEST.json"}
        if not required <= names:
            errors.append("production_package_required_files_missing")
        else:
            project = json.loads(archive.read("project.config.json"))
            condition = project.get("condition", {}).get("miniprogram", {}).get("list", [])
            if project.get("setting", {}).get("urlCheck") is not True or condition != []:
                errors.append("production_project_config_not_frozen")
            audit = json.loads(archive.read("rc0810-package-audit.json"))
            if audit.get("profile") != "production" or audit.get("journey_gate_passed") is not True:
                errors.append("production_package_audit_failed")
    return errors


def validate_report(report_path: Path = DEFAULT_REPORT, *, rebuild_missing: bool = False) -> dict[str, Any]:
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"valid": False, "errors": [f"report_unreadable:{exc}"]}
    errors: list[str] = []
    if report.get("schema") != "safehome.rc0810.f25b-evidence.v1" or report.get("phase") != "F25-B":
        errors.append("report_identity_invalid")
    if report.get("engineering_status") != "evidence_ready":
        errors.append("engineering_status_invalid")
    if report.get("external_verification_complete") is not False or report.get("production_gate_eligible") is not False or report.get("release_recommendation") != "NO_GO":
        errors.append("production_gate_must_remain_closed")
    source = report.get("artifact_source", {})
    commit = source.get("commit")
    try:
        if not isinstance(commit, str) or len(commit) != 40:
            raise EvidenceError("commit invalid")
        _run("git", "merge-base", "--is-ancestor", commit, "HEAD")
        if source.get("source_tree") != _git_text("rev-parse", f"{commit}^{{tree}}"):
            errors.append("source_tree_mismatch")
        current = _release_input_snapshot("HEAD")
        if current["release_input_sha256"] != source.get("release_input_sha256") or current["files"] != source.get("files"):
            errors.append("release_input_drift")
        if _backend_context_sha256("HEAD") != source.get("backend_build_context_sha256"):
            errors.append("backend_context_drift")
    except (EvidenceError, KeyError, json.JSONDecodeError) as exc:
        errors.append(f"source_binding_invalid:{exc}")
    errors.extend(_package_errors(report, rebuild_missing=rebuild_missing))
    backend = report.get("artifact_binding", {}).get("backend_image", {})
    if backend.get("status") != "pending_external" or backend.get("image_digest") is not None:
        errors.append("backend_image_must_not_be_fabricated")
    external_groups = [
        report.get("platform_checks", []), report.get("account_scenarios", []),
        report.get("message_scenarios", []), report.get("raci", []),
        report.get("real_world_evidence", []), report.get("device_matrix", []),
    ]
    if any(item.get("status") != "pending_external" for group in external_groups for item in group):
        errors.append("external_evidence_must_remain_pending")
    if report.get("zero_context_review", {}).get("status") != "pending_external" or report.get("zero_context_review", {}).get("reviewer_id") is not None:
        errors.append("zero_context_review_must_remain_pending")
    if {item.get("id") for item in report.get("blockers", [])} != BLOCKER_IDS:
        errors.append("external_blocker_catalog_incomplete")
    if [item.get("id") for item in report.get("subtasks", [])] != [f"F25.{number}" for number in range(1, 15)]:
        errors.append("subtask_catalog_incomplete")
    return {
        "valid": not errors,
        "status": "evidence_ready_external_blockers" if not errors else "invalid",
        "phase": "F25-B",
        "production_gate_eligible": False,
        "errors": errors,
    }


def run_self_checks(report_path: Path = DEFAULT_REPORT) -> dict[str, bool]:
    original = json.loads(report_path.read_text(encoding="utf-8"))
    checks: dict[str, bool] = {}
    mutations = []
    release = copy.deepcopy(original)
    release["production_gate_eligible"] = True
    mutations.append(("release_gate_drift_rejected", release))
    image = copy.deepcopy(original)
    image["artifact_binding"]["backend_image"] = {"status": "human_verified", "image_digest": "sha256:" + "a" * 64, "blocker": None}
    mutations.append(("fabricated_image_rejected", image))
    human = copy.deepcopy(original)
    human["device_matrix"][0]["status"] = "human_verified"
    mutations.append(("fabricated_device_rejected", human))
    blockers = copy.deepcopy(original)
    blockers["blockers"].pop()
    mutations.append(("missing_blocker_rejected", blockers))
    source = copy.deepcopy(original)
    source["artifact_source"]["release_input_sha256"] = "0" * 64
    mutations.append(("release_input_drift_rejected", source))
    with tempfile.TemporaryDirectory(prefix="rc0810-f25b-self-check-") as directory:
        for name, candidate in mutations:
            path = Path(directory) / f"{name}.json"
            path.write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")
            checks[name] = not validate_report(path)["valid"]
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--source-commit")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--rebuild-missing", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.write_report:
        build_report(args.report, commit=args.source_commit)
    result = validate_report(args.report, rebuild_missing=args.rebuild_missing)
    if result["valid"] and args.self_check:
        result["self_checks"] = run_self_checks(args.report)
        result["valid"] = all(result["self_checks"].values())
        result["status"] = "self_check_passed" if result["valid"] else "invalid"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
