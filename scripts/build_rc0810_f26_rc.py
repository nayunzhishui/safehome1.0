"""Build and validate the RC0810-F26 release-candidate evidence.

This command packages an immutable Git commit in an isolated archive. It does
not run required CI, build a Docker image, approve external gates, migrate a
database, or release production. Missing evidence therefore remains NO-GO.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import build_rc0810_f25b_evidence as f25b
import run_rc0810_f22_scans as f22scan


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "docs" / "02_专项进度与验收" / "rc0810_f26_final_rc.json"
DEFAULT_MARKDOWN = ROOT / "docs" / "02_专项进度与验收" / "rc0810_f26_final_rc.md"
REGISTRY_PATH = ROOT / "content" / "rc0810_release_candidate_registry.json"
FINAL_POLICY_PATH = ROOT / "content" / "task37_38_final_acceptance_policy.json"
F22_REPORT_PATH = ROOT / "docs" / "02_专项进度与验收" / "rc0810_f22b_security_gate.json"
F25_REPORT_PATH = ROOT / "docs" / "02_专项进度与验收" / "rc0810_f25b_evidence.json"
ARTIFACT_ROOT = ROOT / ".codex_tmp" / "rc0810" / "f26"
RC0810_RUNTIME_ROOT = ROOT / ".codex_tmp" / "rc0810"
ACTIVE_STATE_POINTER = RC0810_RUNTIME_ROOT / "state.json"
WAVE_C_PACKET_NAME = "wave-C-f26.json"
WAVE_C_PACKET_ARCHIVE = ROOT / "docs" / "02_专项进度与验收" / "rc0810_wave_c_review_packet.json"
WAVE_C_BASE_COMMIT = "908603e1"
WAVE_C_PENDING_BLOCKER = "wave_c_independent_review_pending"
WAVE_B_PACKET_SHA256 = "2b7c5c249bc80023c094a0a818f203364989d4ea408f59253ef48153c48c6e21"
WAVE_B_DECISION_SHA256 = "a24af5a4fb5f713af91c13767ea6b460cf4dea1a3e44544b6ec0b09df3a37feb"
BACKEND_SOURCE_PATHS = (
    "Dockerfile",
    ".dockerignore",
    "backend",
    "content",
    "shared",
    "config/rc0810/database_profiles.json",
    "deploy/verify_rc0810_f03_images.py",
)
LOCK_PATTERNS = (
    re.compile(r"(^|/)requirements[^/]*\.txt$"),
    re.compile(r"(^|/)package-lock\.json$"),
    re.compile(r"(^|/)(npm-shrinkwrap\.json|pnpm-lock\.yaml|yarn\.lock|poetry\.lock|Pipfile\.lock)$"),
)
INTERNAL_MINIPROGRAM_FILES = {
    "project.private.config.json",
    "pages/debug/index.js",
    "pages/integration-test/index.js",
    "pages/researcher-dashboard/index.js",
    "pages/therapeutic-assessment-quality/index.js",
}


class RcEvidenceError(RuntimeError):
    pass


def _run(*argv: str) -> subprocess.CompletedProcess[bytes]:
    completed = subprocess.run(argv, cwd=ROOT, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RcEvidenceError(
            completed.stderr.decode("utf-8", errors="replace")
            or completed.stdout.decode("utf-8", errors="replace")
        )
    return completed


def _git_bytes(*args: str) -> bytes:
    return _run("git", *args).stdout


def _git_text(*args: str) -> str:
    return _git_bytes(*args).decode("utf-8", errors="strict").strip()


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256(payload)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_repository_path(path: Path) -> Path:
    return (ROOT / path).resolve() if not path.is_absolute() else path.resolve()


def _git_file(commit: str, path: str) -> bytes:
    return _git_bytes("show", f"{commit}:{path}")


def _write_bytes(path: Path, payload: bytes) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return {
        "status": "generated",
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": _sha256(payload),
        "size_bytes": len(payload),
    }


def _write_json_artifact(path: Path, value: Any) -> dict[str, Any]:
    payload = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return _write_bytes(path, payload)


def _build_miniprogram_package(commit: str, target: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="rc0810-f26-mini-") as directory:
        staging = Path(directory) / "f25b.zip"
        built = f25b.build_miniprogram_package(commit, staging)
        with zipfile.ZipFile(staging) as source:
            files = {
                name: source.read(name)
                for name in source.namelist()
                if name != "RC0810_F25B_MANIFEST.json"
            }
        content_manifest_sha256 = f25b._content_manifest_digest(files)
        manifest = {
            "schema": "safehome.rc0810.f26-miniprogram-manifest.v1",
            "source_commit": commit,
            "source_tree": _git_text("rev-parse", f"{commit}^{{tree}}"),
            "release_input_sha256": built["manifest"]["release_input_sha256"],
            "content_manifest_sha256": content_manifest_sha256,
            "profile": "production",
            "production_release_approved": False,
        }
        files["RC0810_F26_MANIFEST.json"] = (
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        ).encode("utf-8")
        target.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name in sorted(files):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, files[name])
    return {
        "status": "generated",
        "path": target.relative_to(ROOT).as_posix(),
        "sha256": _sha256(target.read_bytes()),
        "size_bytes": target.stat().st_size,
        "profile": "production",
        "static_journey_gate_passed": built["audit"]["journey_gate_passed"] is True,
        "release_input_sha256": manifest["release_input_sha256"],
        "content_manifest_sha256": content_manifest_sha256,
    }


def _dependency_inputs(commit: str) -> list[dict[str, Any]]:
    names = _git_text("ls-tree", "-r", "--name-only", commit).splitlines()
    return [
        {"path": path, "sha256": _sha256(_git_file(commit, path))}
        for path in names
        if any(pattern.search(path) for pattern in LOCK_PATTERNS)
    ]


def _requirement_components(commit: str, path: str) -> list[dict[str, str]]:
    components = []
    for raw in _git_file(commit, path).decode("utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        match = re.match(r"([A-Za-z0-9_.-]+)\s*(.*)", line)
        if match:
            components.append({"ecosystem": "pypi", "name": match.group(1), "constraint": match.group(2) or "unbounded", "source": path})
    return components


def _npm_components(commit: str, path: str) -> list[dict[str, str]]:
    lock = json.loads(_git_file(commit, path))
    root = lock.get("packages", {}).get("", {})
    requested = {**root.get("dependencies", {}), **root.get("devDependencies", {})}
    components = []
    for name, constraint in sorted(requested.items()):
        resolved = lock.get("packages", {}).get(f"node_modules/{name}", {}).get("version")
        components.append({
            "ecosystem": "npm",
            "name": name,
            "constraint": str(constraint),
            "resolved_version": str(resolved) if resolved else "unknown",
            "source": path,
        })
    return components


def _build_sbom(commit: str, source_tree: str, inputs: list[dict[str, Any]]) -> dict[str, Any]:
    components: list[dict[str, str]] = []
    for item in inputs:
        path = item["path"]
        if path.endswith("requirements.txt"):
            components.extend(_requirement_components(commit, path))
        elif path.endswith("package-lock.json"):
            components.extend(_npm_components(commit, path))
    return {
        "schema": "safehome.rc0810.source-sbom.v1",
        "source_commit": commit,
        "source_tree": source_tree,
        "status": "inventory_only_not_vulnerability_scan",
        "dependency_inputs": inputs,
        "components": components,
    }


def _migration_summary(commit: str) -> dict[str, Any]:
    path = "backend/services/schema_migration_service.py"
    payload = _git_file(commit, path)
    versions = re.findall(r'version="([0-9_]+)"', payload.decode("utf-8"))
    return {
        "head": versions[-1] if versions else None,
        "count": len(versions),
        "source_path": path,
        "source_sha256": _sha256(payload),
        "production_migration_executed": False,
        "rollback_executed": False,
        "rollback_plan": "deploy/rc0810_f11_database_rollback.md",
    }


def _tracked_hash_summary(commit: str, prefixes: tuple[str, ...]) -> dict[str, Any]:
    paths = [
        path for path in _git_text("ls-tree", "-r", "--name-only", commit).splitlines()
        if path.startswith(prefixes)
    ]
    files = {path: _sha256(_git_file(commit, path)) for path in paths}
    return {"file_count": len(files), "sha256": _canonical_sha256(files), "files": files}


def _pr_owner(pr_id: str) -> str:
    prefix = pr_id.split("-", 1)[0]
    if prefix in {"WX", "QA"}:
        return "platform_owner"
    if prefix == "PRIV":
        return "privacy_owner"
    if prefix in {"PSY", "CONTENT"}:
        return "professional_owner"
    if prefix in {"REL", "PR8"}:
        return "release_owner"
    return "engineering_owner"


def _pr8_matrix(registry: dict[str, Any]) -> list[dict[str, Any]]:
    mapped: dict[str, list[str]] = {}
    for task in registry["tasks"]:
        for pr_id in task["pr_ids"]:
            mapped.setdefault(pr_id, []).append(task["id"])
    result = []
    for pr_id, task_ids in sorted(mapped.items()):
        if "RC0810-F26" in task_ids:
            status = "blocked"
            action = "完成波次 C 独立审查、required CI、正式镜像和四方签署后重新判定。"
        elif "RC0810-F25" in task_ids:
            status = "blocked_external"
            action = "补齐微信平台、开发者工具、真机、账号、RACI 与真实世界证据。"
        else:
            status = "partial"
            action = "历史工程证据仅作参考；在当前 RC 上补跑 required CI/安全 Gate 后才能标记 resolved。"
        result.append({
            "pr_id": pr_id,
            "tasks": task_ids,
            "status": status,
            "owner": _pr_owner(pr_id),
            "next_action": action,
            "resolved_commit": None,
            "current_rc_evidence": None,
        })
    return result


def _required_ci(policy: dict[str, Any], local_ci_complete: bool = False) -> list[dict[str, Any]]:
    return [
        {
            "id": item["id"],
            "title": item["title"],
            "required": item["required"] is True,
            "status": "local_pass" if local_ci_complete else "not_run_user_waiver",
            "evidence": "local_required_ci_and_fix_loop" if local_ci_complete else None,
            "release_effect": "satisfied_locally" if local_ci_complete else "blocking",
        }
        for item in policy["automatic_acceptance_categories"]
    ]


def _release_drill() -> dict[str, Any]:
    return {
        "execution_status": "planned_not_executed",
        "production_mutation_authorized": False,
        "freeze_window": "候选提交、镜像、ZIP、配置、内容、账号和测试数据同时冻结。",
        "canary_scope": "仅负责人批准的测试账号和最小灰度对象；本任务不自动创建。",
        "observation_window": {
            "hours": 72,
            "owner_approved_alternative": None,
            "monitors": ["error_rate", "queue_backlog", "risk_sla", "messages", "ai_cost", "user_blocking"],
        },
        "automatic_stop_thresholds": [
            "health_or_readiness_failure",
            "risk_sla_breach",
            "unexpected_message_or_export",
            "migration_or_data_integrity_error",
            "material_user_blocking_regression",
        ],
        "manual_checkpoints": ["before_canary", "before_expansion", "before_general_release", "after_rollback"],
        "rollback_order": ["stop_traffic", "code", "database", "content", "data_reconciliation"],
        "rollback_notes": {
            "code": "恢复上一已批准镜像与小程序版本。",
            "database": "仅按已审查的兼容窗口和迁移回滚说明执行，不自动删列。",
            "content": "恢复上一已批准内容 artifact，并重算内容摘要。",
            "data_reconciliation": "核对新写入、队列、审计、消息、导出和风险任务。",
        },
    }


def _side_effect_ledger() -> list[dict[str, Any]]:
    return [
        {
            "domain": domain,
            "status": "planned_not_executed",
            "reconcile": reconcile,
            "compensation": compensation,
            "notification": notification,
        }
        for domain, reconcile, compensation, notification in (
            ("messages", "按请求 ID 和发送回执核对已发/待发/重复。", "停止队列并按业务规则补发或更正。", "必要时通知受影响用户与值守人。"),
            ("external_ai", "按审计 ID 核对请求、响应、成本和数据范围。", "停止新请求并隔离异常输出；外部调用不可撤销。", "通知 AI 与隐私负责人。"),
            ("exports", "按导出审计核对授权、文件和下载状态。", "撤销可撤销链接并登记不可撤销下载。", "通知数据与隐私负责人。"),
            ("risk_tasks", "按风险任务 ID 核对创建、确认、升级和关闭。", "补建、重新分派或人工接管遗漏任务。", "通知专业值守与安全负责人。"),
        )
    ]


def _artifact_errors(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    candidate = report.get("candidate", {})
    for name, artifact in report.get("artifacts", {}).items():
        if artifact.get("status") != "generated":
            continue
        relative = artifact.get("path")
        if not isinstance(relative, str) or not relative.startswith(".codex_tmp/rc0810/f26/"):
            errors.append(f"{name}_path_invalid")
            continue
        path = (ROOT / relative).resolve()
        if ROOT.resolve() not in path.parents or not path.is_file():
            errors.append(f"{name}_missing")
            continue
        if _sha256(path.read_bytes()) != artifact.get("sha256"):
            errors.append(f"{name}_sha256_mismatch")
    mini = report.get("artifacts", {}).get("miniprogram_zip", {})
    if mini.get("status") == "generated" and (ROOT / mini["path"]).is_file():
        with zipfile.ZipFile(ROOT / mini["path"]) as archive:
            names = set(archive.namelist())
            if names & INTERNAL_MINIPROGRAM_FILES:
                errors.append("miniprogram_contains_internal_surface")
            required = {"app.json", "project.config.json", "rc0810-package-audit.json", "RC0810_F26_MANIFEST.json"}
            if not required <= names:
                errors.append("miniprogram_manifest_or_contract_missing")
            else:
                project = json.loads(archive.read("project.config.json"))
                conditions = project.get("condition", {}).get("miniprogram", {}).get("list")
                if project.get("setting", {}).get("urlCheck") is not True or conditions != []:
                    errors.append("miniprogram_profile_not_frozen")
                mini_manifest = json.loads(archive.read("RC0810_F26_MANIFEST.json"))
                if mini_manifest.get("source_commit") != candidate.get("source_commit") or mini_manifest.get("source_tree") != candidate.get("source_tree"):
                    errors.append("miniprogram_candidate_binding_mismatch")
                content_manifest = f25b._archive_content_manifest_sha256(
                    archive, manifest_name="RC0810_F26_MANIFEST.json"
                )
                if (
                    mini.get("content_manifest_sha256") != content_manifest
                    or mini_manifest.get("content_manifest_sha256") != content_manifest
                ):
                    errors.append("miniprogram_content_manifest_mismatch")
                f25 = _read_json(F25_REPORT_PATH)
                f25_source = f25.get("artifact_source", {})
                f25_manifest = (
                    f25.get("artifact_binding", {})
                    .get("miniprogram_package", {})
                    .get("content_manifest_sha256")
                )
                if (
                    f25_source.get("commit") != candidate.get("source_commit")
                    or f25_manifest != content_manifest
                ):
                    errors.append("f25_f26_content_identity_mismatch")
    source_sbom = report.get("artifacts", {}).get("source_sbom", {})
    if source_sbom.get("status") == "generated" and (ROOT / source_sbom["path"]).is_file():
        sbom_value = _read_json(ROOT / source_sbom["path"])
        if sbom_value.get("source_commit") != candidate.get("source_commit") or sbom_value.get("source_tree") != candidate.get("source_tree"):
            errors.append("source_sbom_candidate_binding_mismatch")
    artifact_manifest = report.get("artifacts", {}).get("artifact_manifest", {})
    if artifact_manifest.get("status") == "generated" and (ROOT / artifact_manifest["path"]).is_file():
        manifest_value = _read_json(ROOT / artifact_manifest["path"])
        if manifest_value.get("source_commit") != candidate.get("source_commit") or manifest_value.get("source_tree") != candidate.get("source_tree"):
            errors.append("artifact_manifest_candidate_binding_mismatch")
    return errors


def build_report(
    report_path: Path = DEFAULT_REPORT,
    *,
    markdown_path: Path = DEFAULT_MARKDOWN,
    commit: str | None = None,
    local_ci_complete: bool = False,
    backend_image_id: str | None = None,
    backend_image_tag: str | None = None,
) -> dict[str, Any]:
    commit = _git_text("rev-parse", commit or "HEAD")
    source_tree = _git_text("rev-parse", f"{commit}^{{tree}}")
    branch = _git_text("rev-parse", "--abbrev-ref", "HEAD")
    origin_main = _git_text("rev-parse", "origin/main")
    workspace_dirty = bool(_git_text("status", "--porcelain"))
    artifact_dir = ARTIFACT_ROOT / commit
    source_tar = _write_bytes(artifact_dir / "safehome-source.tar", _git_bytes("archive", "--format=tar", commit))
    backend_tar = _write_bytes(
        artifact_dir / "safehome-backend-source.tar",
        _git_bytes("archive", "--format=tar", commit, "--", *BACKEND_SOURCE_PATHS),
    )
    miniprogram = _build_miniprogram_package(commit, artifact_dir / "safehome-miniprogram-production.zip")
    dependency_inputs = _dependency_inputs(commit)
    sbom = _build_sbom(commit, source_tree, dependency_inputs)
    sbom_artifact = _write_json_artifact(artifact_dir / "safehome-source-sbom.json", sbom)
    manifest_value = {
        "schema": "safehome.rc0810.f26-artifact-manifest.v1",
        "source_commit": commit,
        "source_tree": source_tree,
        "profile": "production",
        "production_release_approved": False,
        "artifacts": {
            "source_tar": source_tar,
            "backend_source_tar": backend_tar,
            "miniprogram_zip": miniprogram,
            "source_sbom": sbom_artifact,
        },
    }
    manifest = _write_json_artifact(artifact_dir / "RC0810_F26_ARTIFACT_MANIFEST.json", manifest_value)
    sums_payload = "".join(
        f"{item['sha256']}  {Path(item['path']).name}\n"
        for item in (source_tar, backend_tar, miniprogram, sbom_artifact, manifest)
    ).encode("utf-8")
    sums = _write_bytes(artifact_dir / "SHA256SUMS", sums_payload)

    registry = _read_json(REGISTRY_PATH)
    final_policy = _read_json(FINAL_POLICY_PATH)
    f22 = _read_json(F22_REPORT_PATH)
    f25 = _read_json(F25_REPORT_PATH)
    wave_base = _git_text("rev-parse", WAVE_C_BASE_COMMIT)
    local_evidence_mode = local_ci_complete and bool(backend_image_id and backend_image_tag)
    registry_evidence = f25b.load_registry_evidence(commit)
    if registry_evidence is None and f25.get("artifact_source", {}).get("commit") == commit:
        embedded_registry = (
            f25.get("artifact_binding", {})
            .get("backend_image", {})
            .get("registry_evidence")
        )
        if not f25b.registry_evidence_errors(embedded_registry, commit):
            registry_evidence = embedded_registry
    registry_evidence_mode = registry_evidence is not None
    current_security_tree = f22scan.security_source_snapshot()["source_tree"] if (local_evidence_mode or registry_evidence_mode) else None
    security_is_current = (local_evidence_mode or registry_evidence_mode) and f22.get("source_tree") == current_security_tree
    backend_image = (
        registry_evidence
        if registry_evidence_mode
        else
        {
            "status": "local_built_unpublished",
            "image_id": backend_image_id,
            "tag": backend_image_tag,
            "digest": None,
            "source_commit": commit,
            "reason": "registry_digest_and_attestation_pending",
        }
        if local_evidence_mode
        else {
            "status": "missing_blocking",
            "digest": None,
            "reason": "docker_daemon_unavailable_and_current_image_not_built",
        }
    )
    registry_raw_pending = bool(
        registry_evidence_mode
        and registry_evidence.get("raw_evidence_publication", {}).get("production_blocking")
    )
    report = {
        "schema": "safehome.rc0810.f26-final-rc.v1",
        "phase": "F26",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_status": "review_pending_wave",
        "engineering_materials_status": "evidence_ready_no_go",
        "evidence_mode": (
            "current_candidate_evidence_no_go"
            if registry_evidence_mode
            else "local_gates_complete_no_go" if local_evidence_mode else "historical_user_waiver"
        ),
        "candidate": {
            "source_commit": commit,
            "source_tree": source_tree,
            "branch": branch,
            "origin_main": origin_main,
            "origin_in_sync_at_generation": origin_main == commit,
            "workspace_dirty_observed": workspace_dirty,
            "packaging_mode": "isolated_git_archive",
            "direct_dirty_worktree_build_allowed": False,
        },
        "artifacts": {
            "source_tar": source_tar,
            "backend_source_tar": backend_tar,
            "miniprogram_zip": miniprogram,
            "source_sbom": {**sbom_artifact, "coverage": sbom["status"], "component_count": len(sbom["components"])},
            "artifact_manifest": manifest,
            "sha256sums": sums,
            "backend_image": backend_image,
        },
        "dependency_locks": {
            "inputs": dependency_inputs,
            "aggregate_sha256": _canonical_sha256(dependency_inputs),
        },
        "source_summaries": {
            "migration": _migration_summary(commit),
            "content_artifacts": _tracked_hash_summary(commit, ("content/content_governance_manifest.json", "content/offline_baseline_manifest.json", "content/operations_release_manifest.json")),
            "rc0810_config": _tracked_hash_summary(commit, ("config/rc0810/",)),
        },
        "required_ci": (
            [
                {
                    "id": item["id"],
                    "title": item["title"],
                    "required": item["required"] is True,
                    "status": "not_verified_for_candidate",
                    "evidence": None,
                    "release_effect": "blocking",
                }
                for item in final_policy["automatic_acceptance_categories"]
            ]
            if registry_evidence_mode
            else _required_ci(final_policy, local_evidence_mode)
        ),
        "required_ci_summary": (
            {
                "status": "local_only_not_official",
                "blocking_job": None,
                "high_vulnerabilities": None,
                "official_github_ci": "no_bound_success",
                "candidate_commit": commit,
                "evidence_scope": "candidate_commit_only",
            }
            if local_evidence_mode
            else {
                "status": "not_verified_for_candidate",
                "blocking_job": None,
                "high_vulnerabilities": None,
                "official_github_ci": "no_bound_success",
                "candidate_commit": commit,
                "evidence_scope": "candidate_commit_only",
            }
            if registry_evidence_mode
            else {"status": "not_run_user_waiver"}
        ),
        "security_evidence": {
            "path": F22_REPORT_PATH.relative_to(ROOT).as_posix(),
            "source_tree": f22.get("source_tree"),
            "candidate_source_tree": current_security_tree or source_tree,
            "current_status": "current" if security_is_current else "stale",
            "historical_status": f22.get("status"),
            "sbom_status": "current_scan_complete_no_go" if security_is_current else "inventory_generated_but_current_vulnerability_scan_not_run",
            "production_gate_eligible": False,
        },
        "platform_evidence": {
            "path": F25_REPORT_PATH.relative_to(ROOT).as_posix(),
            "source_commit": f25.get("artifact_source", {}).get("commit"),
            "historical_engineering_status": f25.get("engineering_status"),
            "production_approved": False,
            "miniprogram_content_manifest_sha256": f25.get("artifact_binding", {}).get("miniprogram_package", {}).get("content_manifest_sha256"),
            "external_blockers": f25.get("blockers", []),
        },
        "pr8_close_matrix": _pr8_matrix(registry),
        "release_drill": _release_drill(),
        "irreversible_side_effect_ledger": _side_effect_ledger(),
        "four_go": {
            "product": {"approved": False, "status": "pending_external", "owner": "product_owner"},
            "platform": {"approved": False, "status": "blocked_external", "owner": "platform_owner"},
            "engineering": {"approved": False, "status": "blocked_required_ci_image_security", "owner": "engineering_owner"},
            "professional": {"approved": False, "status": "pending_external", "owner": "professional_owner"},
        },
        "wave_c_review": {
            "status": "review_pending_wave",
            "reviewer_id": "sartre_replacement",
            "base_commit": wave_base,
            "packet_path": None,
            "packet_sha256": None,
            "packet_nonce": None,
            "packet_head": None,
            "packet_source_tree": None,
            "harness_binding": None,
            "decision_reviewed_head": None,
            "decision_artifact": None,
            "prior_wave_b_packet_sha256": WAVE_B_PACKET_SHA256,
            "prior_wave_b_decision_sha256": WAVE_B_DECISION_SHA256,
        },
        "release_decision": {
            "recommendation": "NO_GO",
            "production_gate_eligible": False,
            "automatic_release_performed": False,
            "blocking_reasons": [
                *( ["official_required_ci_not_verified_for_candidate", "image_security_findings_and_signed_attestation_pending"]
                   if registry_evidence_mode
                   else ["official_required_ci_not_verified_for_candidate", "backend_registry_digest_and_attestation_missing"]
                   if local_evidence_mode
                   else ["required_ci_not_run_by_user_direction", "current_security_scan_missing_and_f22_evidence_stale", "backend_image_and_digest_missing"] ),
                *(["registry_raw_evidence_actions_artifact_pending"] if registry_raw_pending else []),
                "wechat_platform_real_device_and_human_evidence_missing",
                "product_platform_engineering_professional_go_incomplete",
                "72h_candidate_observation_not_executed",
                "wave_c_independent_review_pending",
            ],
        },
        "phase_separation": {
            "engineering_materials_complete": True,
            "rc_formed": False,
            "platform_approved": False,
            "released": False,
            "stable_operation_verified": False,
        },
        "known_issues": [
            ("F22-B security report is current for the candidate but remains NO-GO." if security_is_current else "F22-B security report is bound to an older source tree and is historical only."),
            "F25-B has eight external blockers and no platform or human approval.",
            *( ["Official GitHub required CI has not been verified for this candidate.",
                "The GHCR digest and Trivy CycloneDX SBOM are bound; Critical/High image findings and signed-attestation verification remain blocking."]
               if registry_evidence_mode
               else ["Local required CI and fix loop completed, but npm audit still reports four High findings with no upstream fix.",
                "The backend image is local only; registry digest and supply-chain attestation remain missing."]
               if local_evidence_mode
               else ["Required CI/Harness/regression was not run at F26 by explicit user direction.",
                     "No current backend image, image digest, container scan or production migration evidence exists."] ),
        ],
        "subtasks": [
            {"id": "F26.1", "status": "evidence_ready"},
            {"id": "F26.2", "status": "blocked_official_ci_pending" if registry_evidence_mode else "local_complete_with_failure" if local_evidence_mode else "blocked_user_waiver"},
            {"id": "F26.3", "status": "registry_digest_bound_no_go" if registry_evidence_mode else "local_image_registry_digest_missing" if local_evidence_mode else "partial_backend_image_missing"},
            {"id": "F26.4", "status": "current_scan_no_go" if (registry_evidence_mode or local_evidence_mode) else "partial_image_and_security_missing"},
            {"id": "F26.5", "status": "current_scan_no_go" if (registry_evidence_mode or local_evidence_mode) else "partial_structural_scan_only"},
            {"id": "F26.6", "status": "evidence_ready"},
            {"id": "F26.7", "status": "evidence_ready_no_resolved_claims"},
            {"id": "F26.8", "status": "review_pending_wave"},
            {"id": "F26.9", "status": "complete_no_go"},
            {"id": "F26.10", "status": "planned_not_executed"},
            {"id": "F26.11", "status": "blocked_external"},
            {"id": "F26.12", "status": "pending_external"},
            {"id": "F26.13", "status": "planned_not_executed"},
            {"id": "F26.14", "status": "evidence_ready"},
        ],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    return report


def render_markdown(report: dict[str, Any]) -> str:
    candidate = report["candidate"]
    local_mode = report.get("evidence_mode") == "local_gates_complete_no_go"
    registry_mode = report.get("evidence_mode") == "current_candidate_evidence_no_go"
    image = report["artifacts"]["backend_image"]
    image_line = (
        f"`{image['immutable_ref']}`；Trivy CycloneDX SBOM 已绑定，扫描仍有 Critical/High 阻断，签名证明待外部核验"
        if registry_mode
        else f"本地已构建 `{image['tag']}` / `{image['image_id']}`；未伪造 registry digest"
        if local_mode
        else "缺失，未伪造 digest"
    )
    blockers = "\n".join(f"- {item}" for item in report["release_decision"]["blocking_reasons"])
    gates = "\n".join(
        f"- {name}: {item['status']}（approved={str(item['approved']).lower()}）"
        for name, item in report["four_go"].items()
    )
    if report["wave_c_review"]["status"] == "review_pass":
        next_action = (
            "波次 C 固定 reviewer 已审查通过工程实现与如实 NO-GO 结论。仍须完成 required CI、关闭镜像安全发现并核验签名证明、"
            "微信平台与真机证据、四方签署和候选观察，才能重新判定 GO。"
        )
    else:
        next_action = (
            "波次 C 先由固定 reviewer 独立审查累计 diff 与本证据包。之后仍须完成 required CI、关闭镜像安全发现并核验签名证明、"
            "微信平台与真机证据、四方签署和候选观察，才能重新判定 GO。"
        )
    return f"""# RC0810-F26 最终 RC 收口与发布建议

结论：**NO-GO**。本报告完成工程材料收口，不代表 RC 已形成、平台已批准、已发布或已稳定运行。

## 候选基线

- commit：`{candidate['source_commit']}`
- tree：`{candidate['source_tree']}`
- 打包方式：隔离 Git archive；未从脏工作区直接打包
- production 小程序 ZIP：`{report['artifacts']['miniprogram_zip']['sha256']}`
- 后端镜像：{image_line}

## 阻断原因

{blockers}

## 四方 GO

{gates}

## 阶段事实

- 工程材料完成：是
- RC 形成：否
- 平台审核通过：否
- 正式发布：否
- 稳定运行验证：否

## 发布演练

仅形成计划，未执行生产动作。候选观察窗口为 72 小时；回滚顺序为停止流量、代码、数据库、内容、数据核对。消息、外部 AI、导出和风险任务必须分别对账并执行补偿或通知。

## 下一动作

{next_action}
"""


def _complete_wave_c_review_state(report: dict[str, Any]) -> None:
    report["task_status"] = "complete_no_go"
    blockers = report["release_decision"]["blocking_reasons"]
    report["release_decision"]["blocking_reasons"] = [
        blocker for blocker in blockers if blocker != WAVE_C_PENDING_BLOCKER
    ]
    for subtask in report["subtasks"]:
        if subtask.get("id") == "F26.8":
            subtask["status"] = "review_pass"
            break


def _review_state_errors(report: dict[str, Any]) -> list[str]:
    status = report.get("wave_c_review", {}).get("status")
    blockers = report.get("release_decision", {}).get("blocking_reasons", [])
    pending_blocker = WAVE_C_PENDING_BLOCKER in blockers
    subtask_status = next(
        (item.get("status") for item in report.get("subtasks", []) if item.get("id") == "F26.8"),
        None,
    )
    errors: list[str] = []
    if status == "review_pass":
        if pending_blocker:
            errors.append("review_pass_with_pending_blocker")
        if subtask_status != "review_pass":
            errors.append("review_pass_with_pending_subtask")
        if report.get("task_status") != "complete_no_go":
            errors.append("review_pass_with_incomplete_task")
    elif status == "review_pending_wave":
        if not pending_blocker:
            errors.append("review_pending_without_pending_blocker")
        if subtask_status != "review_pending_wave":
            errors.append("review_pending_with_closed_subtask")
        if report.get("task_status") != "review_pending_wave":
            errors.append("review_pending_with_complete_task")
    return errors


def _active_harness_binding() -> tuple[dict[str, Any], dict[str, Any], Path]:
    pointer = _read_json(ACTIVE_STATE_POINTER)
    state_path_value = pointer.get("state_path")
    if not isinstance(state_path_value, str):
        raise RcEvidenceError("active Harness state_path missing")
    state_path = (RC0810_RUNTIME_ROOT / state_path_value).resolve()
    if RC0810_RUNTIME_ROOT.resolve() not in state_path.parents or not state_path.is_file():
        raise RcEvidenceError("active Harness state path invalid")
    state_payload = state_path.read_bytes()
    if _sha256(state_payload) != pointer.get("state_sha256"):
        raise RcEvidenceError("active Harness state hash mismatch")
    state = json.loads(state_payload)
    if state.get("run_id") != pointer.get("run_id"):
        raise RcEvidenceError("active Harness run mismatch")
    wave_b = state.get("wave_checkpoints", {}).get("B", {})
    review = wave_b.get("review", {})
    if (
        state.get("fixed_wave_reviewer_id") != "sartre_replacement"
        or wave_b.get("status") != "review_pass"
        or review.get("packet_sha256") != WAVE_B_PACKET_SHA256
        or review.get("decision_evidence_sha256") != WAVE_B_DECISION_SHA256
    ):
        raise RcEvidenceError("Harness fixed reviewer or wave-B checkpoint invalid")
    wave_c = state.get("wave_checkpoints", {}).get("C", {})
    if wave_c.get("status") == "review_pass":
        raise RcEvidenceError("Harness already claims an unbound wave-C review pass")
    return pointer, state, state_path


def _expected_wave_c_packet_path() -> tuple[Path, dict[str, Any], dict[str, Any], Path]:
    pointer, state, state_path = _active_harness_binding()
    packet_path = (
        RC0810_RUNTIME_ROOT / pointer["run_id"] / "reviews" / WAVE_C_PACKET_NAME
    ).resolve()
    return packet_path, pointer, state, state_path


def _packet_payload_errors(
    report: dict[str, Any],
    packet: dict[str, Any],
    *,
    actual_sha256: str,
    packet_path: Path,
    require_current_head: bool = False,
) -> list[str]:
    errors: list[str] = []
    review = report.get("wave_c_review", {})
    candidate = report.get("candidate", {})
    try:
        expected_path, pointer, _, state_path = _expected_wave_c_packet_path()
    except (OSError, json.JSONDecodeError, RcEvidenceError) as exc:
        return [f"harness_binding_invalid:{exc}"]
    if packet_path.resolve() != expected_path:
        errors.append("review_packet_path_not_active_wave_c")
    if packet.get("schema") != "safehome.rc0810.wave-review-packet.v2" or packet.get("wave") != "C":
        errors.append("review_packet_identity_invalid")
    nonce = packet.get("packet_nonce")
    if not isinstance(nonce, str) or len(nonce) < 16:
        errors.append("review_packet_nonce_invalid")
    if packet.get("reviewer_id") != "sartre_replacement":
        errors.append("review_packet_reviewer_invalid")
    if packet.get("base_checkpoint", {}).get("commit") != review.get("base_commit"):
        errors.append("review_packet_base_invalid")
    packet_head = packet.get("review_head", {}).get("commit")
    packet_tree = packet.get("review_head", {}).get("source_tree")
    if packet.get("release_candidate", {}).get("commit") != candidate.get("source_commit"):
        errors.append("review_packet_candidate_commit_invalid")
    if packet.get("release_candidate", {}).get("source_tree") != candidate.get("source_tree"):
        errors.append("review_packet_candidate_tree_invalid")
    try:
        if packet_tree != _git_text("rev-parse", f"{packet_head}^{{tree}}"):
            errors.append("review_packet_head_tree_invalid")
        _run("git", "merge-base", "--is-ancestor", review.get("base_commit"), packet_head)
        if require_current_head and packet_head != _git_text("rev-parse", "HEAD"):
            errors.append("review_packet_not_bound_to_current_head")
        elif not require_current_head:
            _run("git", "merge-base", "--is-ancestor", packet_head, "HEAD")
    except (RcEvidenceError, TypeError) as exc:
        errors.append(f"review_packet_git_binding_invalid:{exc}")
    bound = review.get("packet_sha256") is not None
    if bound:
        expected_relative = expected_path.relative_to(ROOT).as_posix()
        if review.get("packet_path") != expected_relative:
            errors.append("bound_review_packet_path_mismatch")
        if review.get("packet_sha256") != actual_sha256:
            errors.append("bound_review_packet_hash_mismatch")
        if review.get("packet_nonce") != nonce:
            errors.append("bound_review_packet_nonce_mismatch")
        if review.get("packet_head") != packet_head or review.get("packet_source_tree") != packet_tree:
            errors.append("bound_review_packet_head_mismatch")
        harness = review.get("harness_binding", {})
        if (
            harness.get("run_id") != pointer.get("run_id")
            or harness.get("state_path") != state_path.relative_to(ROOT).as_posix()
            or harness.get("state_sha256") != pointer.get("state_sha256")
            or harness.get("fixed_reviewer_id") != "sartre_replacement"
            or harness.get("last_review_pass_checkpoint") != "RC0810-F21:verified"
        ):
            errors.append("bound_harness_state_mismatch")
    return errors


def _bound_review_packet_errors(report: dict[str, Any]) -> list[str]:
    review = report.get("wave_c_review", {})
    path_value = review.get("packet_path")
    if not isinstance(path_value, str):
        return ["review_packet_not_prebound"]
    active_binding_error: Exception | None = None
    try:
        expected_path, _, _, _ = _expected_wave_c_packet_path()
    except (OSError, json.JSONDecodeError, RcEvidenceError) as exc:
        active_binding_error = exc
        run_id = review.get("harness_binding", {}).get("run_id")
        expected_path = (RC0810_RUNTIME_ROOT / str(run_id or "") / "reviews" / WAVE_C_PACKET_NAME).resolve()
    path = (ROOT / path_value).resolve()
    if path != expected_path:
        return ["review_packet_missing_or_self_reported_path"]
    if not path.is_file():
        archive_value = review.get("packet_archive_path")
        archive_path = (ROOT / str(archive_value or "")).resolve()
        if archive_path != WAVE_C_PACKET_ARCHIVE.resolve() or not archive_path.is_file():
            return ["review_packet_missing_or_self_reported_path"]
        archive_bytes = archive_path.read_bytes()
        archive_sha256 = _sha256(archive_bytes)
        if (
            archive_sha256 != review.get("packet_sha256")
            or archive_sha256 != review.get("packet_archive_sha256")
        ):
            return ["review_packet_archive_hash_mismatch"]
        try:
            packet = json.loads(archive_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return [f"review_packet_unreadable:{exc}"]
        harness = review.get("harness_binding", {})
        expected_runtime = (
            f".codex_tmp/rc0810/{harness.get('run_id')}/reviews/{WAVE_C_PACKET_NAME}"
        )
        errors: list[str] = []
        if path_value != expected_runtime:
            errors.append("bound_review_packet_path_mismatch")
        if packet.get("schema") != "safehome.rc0810.wave-review-packet.v2" or packet.get("wave") != "C":
            errors.append("review_packet_identity_invalid")
        if packet.get("reviewer_id") != "sartre_replacement":
            errors.append("review_packet_reviewer_invalid")
        if packet.get("base_checkpoint", {}).get("commit") != review.get("base_commit"):
            errors.append("review_packet_base_invalid")
        nonce = packet.get("packet_nonce")
        packet_head = packet.get("review_head", {}).get("commit")
        packet_tree = packet.get("review_head", {}).get("source_tree")
        candidate = report.get("candidate", {})
        if review.get("packet_nonce") != nonce:
            errors.append("bound_review_packet_nonce_mismatch")
        if review.get("packet_head") != packet_head or review.get("packet_source_tree") != packet_tree:
            errors.append("bound_review_packet_head_mismatch")
        if packet.get("release_candidate", {}).get("commit") != candidate.get("source_commit"):
            errors.append("review_packet_candidate_commit_invalid")
        if packet.get("release_candidate", {}).get("source_tree") != candidate.get("source_tree"):
            errors.append("review_packet_candidate_tree_invalid")
        if harness.get("fixed_reviewer_id") != "sartre_replacement":
            errors.append("bound_harness_state_mismatch")
        try:
            if packet_tree != _git_text("rev-parse", f"{packet_head}^{{tree}}"):
                errors.append("review_packet_head_tree_invalid")
            _run("git", "merge-base", "--is-ancestor", review.get("base_commit"), packet_head)
            _run("git", "merge-base", "--is-ancestor", packet_head, "HEAD")
        except (RcEvidenceError, TypeError) as exc:
            errors.append(f"review_packet_git_binding_invalid:{exc}")
        return errors
    if active_binding_error is not None:
        return [f"harness_binding_invalid:{active_binding_error}"]
    try:
        packet = _read_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"review_packet_unreadable:{exc}"]
    return _packet_payload_errors(
        report,
        packet,
        actual_sha256=_sha256(path.read_bytes()),
        packet_path=path,
    )


def _review_decision_errors(report: dict[str, Any], decision_artifact: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    review = report["wave_c_review"]
    errors.extend(_bound_review_packet_errors(report))
    path_value = decision_artifact.get("path")
    if path_value != "docs/02_专项进度与验收/rc0810_wave_c_review_decision.json":
        return ["review_decision_path_invalid"]
    path = ROOT / path_value
    if not path.is_file() or _sha256(path.read_bytes()) != decision_artifact.get("sha256"):
        return ["review_decision_artifact_invalid"]
    decision = _read_json(path)
    if decision.get("schema") != "safehome.rc0810.wave-c-review-decision.v1":
        errors.append("review_decision_schema_invalid")
    if decision.get("reviewer_id") != "sartre_replacement" or decision.get("decision") != "pass":
        errors.append("review_decision_not_independent_pass")
    if decision.get("reviewer_kind") != "separate_agent":
        errors.append("reviewer_kind_invalid")
    if decision.get("reviewed_base") != review.get("base_commit"):
        errors.append("review_base_mismatch")
    if decision.get("packet_path") != review.get("packet_path"):
        errors.append("review_packet_path_mismatch")
    if (
        decision.get("packet_sha256") != review.get("packet_sha256")
        or decision.get("packet_nonce") != review.get("packet_nonce")
        or decision.get("packet_head") != review.get("packet_head")
    ):
        errors.append("review_packet_mismatch")
    candidate = report["candidate"]
    if (
        decision.get("candidate_commit") != candidate.get("source_commit")
        or decision.get("candidate_source_tree") != candidate.get("source_tree")
    ):
        errors.append("review_candidate_mismatch")
    reviewed_head = decision.get("reviewed_head")
    if reviewed_head != review.get("decision_reviewed_head"):
        errors.append("review_decision_head_mismatch")
    try:
        _run("git", "merge-base", "--is-ancestor", reviewed_head, "HEAD")
    except (RcEvidenceError, TypeError) as exc:
        errors.append(f"review_decision_head_invalid:{exc}")
    if decision.get("production_recommendation") != "NO_GO":
        errors.append("review_decision_must_preserve_no_go")
    if not isinstance(decision.get("findings"), list):
        errors.append("review_findings_invalid")
    try:
        valid_until = datetime.fromisoformat(decision["valid_until"])
        if valid_until.tzinfo is None or valid_until <= datetime.now(timezone.utc):
            errors.append("review_decision_expired")
    except (KeyError, TypeError, ValueError):
        errors.append("review_decision_validity_invalid")
    return errors


def validate_report(report_path: Path = DEFAULT_REPORT) -> dict[str, Any]:
    try:
        report = _read_json(report_path)
    except (OSError, json.JSONDecodeError) as exc:
        return {"valid": False, "errors": [f"report_unreadable:{exc}"]}
    errors: list[str] = []
    if report.get("schema") != "safehome.rc0810.f26-final-rc.v1" or report.get("phase") != "F26":
        errors.append("report_identity_invalid")
    candidate = report.get("candidate", {})
    commit = candidate.get("source_commit")
    try:
        if not isinstance(commit, str) or len(commit) != 40:
            raise RcEvidenceError("candidate commit invalid")
        if candidate.get("source_tree") != _git_text("rev-parse", f"{commit}^{{tree}}"):
            errors.append("candidate_tree_mismatch")
        _run("git", "merge-base", "--is-ancestor", commit, "HEAD")
    except RcEvidenceError as exc:
        errors.append(f"candidate_binding_invalid:{exc}")
    if candidate.get("packaging_mode") != "isolated_git_archive" or candidate.get("direct_dirty_worktree_build_allowed") is not False:
        errors.append("dirty_build_policy_invalid")
    errors.extend(_artifact_errors(report))
    required_ci = report.get("required_ci", [])
    policy = _read_json(FINAL_POLICY_PATH)
    expected_ci = {item["id"] for item in policy["automatic_acceptance_categories"]}
    if {item.get("id") for item in required_ci} != expected_ci:
        errors.append("required_ci_catalog_incomplete")
    evidence_mode = report.get("evidence_mode", "historical_user_waiver")
    if evidence_mode == "current_candidate_evidence_no_go":
        if any(
            item.get("required") is not True
            or item.get("status") != "not_verified_for_candidate"
            or item.get("evidence") is not None
            or item.get("release_effect") != "blocking"
            for item in required_ci
        ):
            errors.append("official_required_ci_evidence_invalid")
        if report.get("required_ci_summary") != {
            "status": "not_verified_for_candidate",
            "blocking_job": None,
            "high_vulnerabilities": None,
            "official_github_ci": "no_bound_success",
            "candidate_commit": commit,
            "evidence_scope": "candidate_commit_only",
        }:
            errors.append("official_required_ci_summary_invalid")
    elif evidence_mode == "local_gates_complete_no_go":
        if any(
            item.get("required") is not True
            or item.get("status") != "local_pass"
            or item.get("evidence") != "local_required_ci_and_fix_loop"
            for item in required_ci
        ):
            errors.append("local_required_ci_evidence_invalid")
        if report.get("required_ci_summary") != {
            "status": "local_only_not_official",
            "blocking_job": None,
            "high_vulnerabilities": None,
            "official_github_ci": "no_bound_success",
            "candidate_commit": commit,
            "evidence_scope": "candidate_commit_only",
        }:
            errors.append("required_ci_failure_summary_invalid")
    elif evidence_mode == "historical_user_waiver":
        if any(item.get("required") is not True or item.get("status") != "not_run_user_waiver" for item in required_ci):
            errors.append("required_ci_must_remain_unverified")
    else:
        errors.append("evidence_mode_invalid")
    security = report.get("security_evidence", {})
    image = report.get("artifacts", {}).get("backend_image", {})
    if evidence_mode in {"current_candidate_evidence_no_go", "local_gates_complete_no_go"}:
        try:
            current_security_tree = f22scan.security_source_snapshot()["source_tree"]
        except (RuntimeError, OSError) as exc:
            errors.append(f"security_snapshot_unavailable:{exc}")
        else:
            if (
                security.get("source_tree") != current_security_tree
                or security.get("candidate_source_tree") != current_security_tree
                or security.get("current_status") != "current"
            ):
                errors.append("current_security_evidence_invalid")
        if evidence_mode == "current_candidate_evidence_no_go":
            errors.extend(f25b.registry_evidence_errors(image, commit))
        elif (
                image.get("status") != "local_built_unpublished"
                or not re.fullmatch(r"sha256:[0-9a-f]{64}", str(image.get("image_id") or ""))
                or not isinstance(image.get("tag"), str)
                or image.get("source_commit") != commit
                or image.get("digest") is not None
            ):
                errors.append("local_backend_image_evidence_invalid")
    else:
        if security.get("source_tree") == candidate.get("source_tree") or security.get("current_status") != "stale":
            errors.append("stale_security_evidence_promoted")
        if image.get("status") != "missing_blocking" or image.get("digest") is not None:
            errors.append("backend_image_fabricated")
    registry = _read_json(REGISTRY_PATH)
    expected_prs = {pr_id for task in registry["tasks"] for pr_id in task["pr_ids"]}
    matrix = report.get("pr8_close_matrix", [])
    if {item.get("pr_id") for item in matrix} != expected_prs:
        errors.append("pr8_close_matrix_incomplete")
    if any(item.get("status") not in {"partial", "blocked_external", "blocked"} or not item.get("owner") or not item.get("next_action") for item in matrix):
        errors.append("pr8_close_claim_invalid")
    drill = report.get("release_drill", {})
    if drill.get("execution_status") != "planned_not_executed" or drill.get("observation_window", {}).get("hours", 0) < 72:
        errors.append("release_drill_or_observation_invalid")
    side_effects = report.get("irreversible_side_effect_ledger", [])
    if {item.get("domain") for item in side_effects} != {"messages", "external_ai", "exports", "risk_tasks"} or any(item.get("status") != "planned_not_executed" for item in side_effects):
        errors.append("side_effect_ledger_invalid")
    four_go = report.get("four_go", {})
    if set(four_go) != {"product", "platform", "engineering", "professional"} or any(item.get("approved") is not False for item in four_go.values()):
        errors.append("four_go_must_remain_closed")
    decision = report.get("release_decision", {})
    if decision.get("recommendation") != "NO_GO" or decision.get("production_gate_eligible") is not False or decision.get("automatic_release_performed") is not False:
        errors.append("release_decision_must_be_no_go")
    review = report.get("wave_c_review", {})
    errors.extend(_review_state_errors(report))
    if review.get("reviewer_id") != "sartre_replacement":
        errors.append("fixed_reviewer_mismatch")
    if review.get("status") == "review_pass":
        artifact = review.get("decision_artifact")
        if not isinstance(artifact, dict):
            errors.append("review_pass_without_decision_artifact")
        else:
            errors.extend(_review_decision_errors(report, artifact))
    elif review.get("status") != "review_pending_wave":
        errors.append("wave_c_review_status_invalid")
    elif review.get("packet_sha256") is not None:
        errors.extend(_bound_review_packet_errors(report))
    phases = report.get("phase_separation", {})
    if phases != {
        "engineering_materials_complete": True,
        "rc_formed": False,
        "platform_approved": False,
        "released": False,
        "stable_operation_verified": False,
    }:
        errors.append("phase_separation_invalid")
    return {
        "valid": not errors,
        "phase": "F26",
        "status": "evidence_ready_no_go" if not errors else "invalid",
        "release_recommendation": "NO_GO",
        "errors": errors,
    }


def run_self_checks(report_path: Path = DEFAULT_REPORT) -> dict[str, bool]:
    original = _read_json(report_path)
    mutations: list[tuple[str, dict[str, Any]]] = []
    release = copy.deepcopy(original)
    release["release_decision"]["recommendation"] = "GO"
    mutations.append(("forged_release_go_rejected", release))
    ci = copy.deepcopy(original)
    ci["required_ci"][0]["status"] = "verified"
    mutations.append(("forged_required_ci_rejected", ci))
    review = copy.deepcopy(original)
    if review["wave_c_review"].get("status") == "review_pass":
        review["wave_c_review"]["decision_artifact"]["sha256"] = "0" * 64
    else:
        review["wave_c_review"]["status"] = "review_pass"
    mutations.append(("forged_review_pass_rejected", review))
    artifact = copy.deepcopy(original)
    artifact["artifacts"]["source_tar"]["sha256"] = "0" * 64
    mutations.append(("artifact_hash_drift_rejected", artifact))
    matrix = copy.deepcopy(original)
    matrix["pr8_close_matrix"].pop()
    mutations.append(("missing_pr8_item_rejected", matrix))
    observation = copy.deepcopy(original)
    observation["release_drill"]["observation_window"]["hours"] = 24
    mutations.append(("short_observation_window_rejected", observation))
    checks: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix="rc0810-f26-self-check-") as directory:
        for name, candidate in mutations:
            path = Path(directory) / f"{name}.json"
            path.write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")
            checks[name] = not validate_report(path)["valid"]
    return checks


def bind_review_packet(report_path: Path, packet_path: Path, markdown_path: Path) -> dict[str, Any]:
    report = _read_json(report_path)
    review = report["wave_c_review"]
    if review.get("status") != "review_pending_wave" or any(
        review.get(key) is not None
        for key in ("packet_path", "packet_sha256", "packet_nonce", "packet_head", "harness_binding")
    ):
        raise RcEvidenceError("wave-C review packet is already bound or review is not pending")
    expected_path, pointer, state, state_path = _expected_wave_c_packet_path()
    packet_path = packet_path.resolve()
    if packet_path != expected_path or not packet_path.is_file():
        raise RcEvidenceError("wave-C packet must use the fixed active-run path")
    packet = _read_json(packet_path)
    packet_sha256 = _sha256(packet_path.read_bytes())
    errors = _packet_payload_errors(
        report,
        packet,
        actual_sha256=packet_sha256,
        packet_path=packet_path,
        require_current_head=True,
    )
    if errors:
        raise RcEvidenceError(";".join(errors))
    review.update({
        "packet_path": packet_path.relative_to(ROOT).as_posix(),
        "packet_sha256": packet_sha256,
        "packet_nonce": packet["packet_nonce"],
        "packet_head": packet["review_head"]["commit"],
        "packet_source_tree": packet["review_head"]["source_tree"],
        "harness_binding": {
            "run_id": pointer["run_id"],
            "state_path": state_path.relative_to(ROOT).as_posix(),
            "state_sha256": pointer["state_sha256"],
            "fixed_reviewer_id": state["fixed_wave_reviewer_id"],
            "last_review_pass_checkpoint": state["last_review_pass_checkpoint"],
            "wave_b_packet_sha256": WAVE_B_PACKET_SHA256,
            "wave_b_decision_sha256": WAVE_B_DECISION_SHA256,
        },
    })
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    return report


def apply_review_decision(report_path: Path, decision_path: Path, markdown_path: Path) -> dict[str, Any]:
    report = _read_json(report_path)
    decision_path = _resolve_repository_path(decision_path)
    decision = _read_json(decision_path)
    review = report["wave_c_review"]
    if review.get("status") != "review_pending_wave" or review.get("packet_sha256") is None:
        raise RcEvidenceError("wave-C packet must be prebound before applying a decision")
    if decision.get("reviewed_head") != _git_text("rev-parse", "HEAD"):
        raise RcEvidenceError("review decision must bind the current pre-decision HEAD")
    review.update({
        "status": "review_pass" if decision.get("decision") == "pass" else "review_failed",
        "decision_reviewed_head": decision.get("reviewed_head"),
        "decision_artifact": {
            "path": decision_path.relative_to(ROOT).as_posix(),
            "sha256": _sha256(decision_path.read_bytes()),
        },
    })
    errors = _review_decision_errors(report, review["decision_artifact"])
    if errors:
        raise RcEvidenceError(";".join(errors))
    _complete_wave_c_review_state(report)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--source-commit")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--local-ci-complete", action="store_true")
    parser.add_argument("--backend-image-id")
    parser.add_argument("--backend-image-tag")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--bind-review-packet", type=Path)
    parser.add_argument("--apply-review-decision", type=Path)
    args = parser.parse_args()
    if args.write_report:
        build_report(
            args.report,
            markdown_path=args.markdown,
            commit=args.source_commit,
            local_ci_complete=args.local_ci_complete,
            backend_image_id=args.backend_image_id,
            backend_image_tag=args.backend_image_tag,
        )
    if args.bind_review_packet:
        bind_review_packet(args.report, args.bind_review_packet, args.markdown)
    if args.apply_review_decision:
        apply_review_decision(args.report, args.apply_review_decision, args.markdown)
    result = validate_report(args.report)
    if result["valid"] and args.self_check:
        result["self_checks"] = run_self_checks(args.report)
        result["valid"] = all(result["self_checks"].values())
        result["status"] = "self_check_passed" if result["valid"] else "invalid"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
