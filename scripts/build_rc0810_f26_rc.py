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


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "docs" / "02_专项进度与验收" / "rc0810_f26_final_rc.json"
DEFAULT_MARKDOWN = ROOT / "docs" / "02_专项进度与验收" / "rc0810_f26_final_rc.md"
REGISTRY_PATH = ROOT / "content" / "rc0810_release_candidate_registry.json"
FINAL_POLICY_PATH = ROOT / "content" / "task37_38_final_acceptance_policy.json"
F22_REPORT_PATH = ROOT / "docs" / "02_专项进度与验收" / "rc0810_f22b_security_gate.json"
F25_REPORT_PATH = ROOT / "docs" / "02_专项进度与验收" / "rc0810_f25b_evidence.json"
ARTIFACT_ROOT = ROOT / ".codex_tmp" / "rc0810" / "f26"
WAVE_C_BASE_COMMIT = "908603e1"
WAVE_B_PACKET_SHA256 = "2b7c5c249bc80023c094a0a818f203364989d4ea408f59253ef48153c48c6e21"
WAVE_B_DECISION_SHA256 = "a24af5a4fb5f713af91c13767ea6b460cf4dea1a3e44544b6ec0b09df3a37feb"
BACKEND_SOURCE_PATHS = (
    "Dockerfile",
    ".dockerignore",
    "backend",
    "content",
    "shared",
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
        manifest = {
            "schema": "safehome.rc0810.f26-miniprogram-manifest.v1",
            "source_commit": commit,
            "source_tree": _git_text("rev-parse", f"{commit}^{{tree}}"),
            "release_input_sha256": built["manifest"]["release_input_sha256"],
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


def _required_ci(policy: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": item["id"],
            "title": item["title"],
            "required": item["required"] is True,
            "status": "not_run_user_waiver",
            "evidence": None,
            "release_effect": "blocking",
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
    return errors


def build_report(
    report_path: Path = DEFAULT_REPORT,
    *,
    markdown_path: Path = DEFAULT_MARKDOWN,
    commit: str | None = None,
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
    report = {
        "schema": "safehome.rc0810.f26-final-rc.v1",
        "phase": "F26",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_status": "review_pending_wave",
        "engineering_materials_status": "evidence_ready_no_go",
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
            "backend_image": {
                "status": "missing_blocking",
                "digest": None,
                "reason": "docker_daemon_unavailable_and_current_image_not_built",
            },
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
        "required_ci": _required_ci(final_policy),
        "security_evidence": {
            "path": F22_REPORT_PATH.relative_to(ROOT).as_posix(),
            "source_tree": f22.get("source_tree"),
            "candidate_source_tree": source_tree,
            "current_status": "current" if f22.get("source_tree") == source_tree else "stale",
            "historical_status": f22.get("status"),
            "sbom_status": "inventory_generated_but_current_vulnerability_scan_not_run",
            "production_gate_eligible": False,
        },
        "platform_evidence": {
            "path": F25_REPORT_PATH.relative_to(ROOT).as_posix(),
            "source_commit": f25.get("artifact_source", {}).get("commit"),
            "historical_engineering_status": f25.get("engineering_status"),
            "production_approved": False,
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
            "reviewed_head": None,
            "packet_path": None,
            "packet_sha256": None,
            "decision_artifact": None,
            "prior_wave_b_packet_sha256": WAVE_B_PACKET_SHA256,
            "prior_wave_b_decision_sha256": WAVE_B_DECISION_SHA256,
        },
        "release_decision": {
            "recommendation": "NO_GO",
            "production_gate_eligible": False,
            "automatic_release_performed": False,
            "blocking_reasons": [
                "required_ci_not_run_by_user_direction",
                "current_security_scan_missing_and_f22_evidence_stale",
                "backend_image_and_digest_missing",
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
            "F22-B security report is bound to an older source tree and is historical only.",
            "F25-B has eight external blockers and no platform or human approval.",
            "Required CI/Harness/regression was not run at F26 by explicit user direction.",
            "No current backend image, image digest, container scan or production migration evidence exists.",
        ],
        "subtasks": [
            {"id": "F26.1", "status": "evidence_ready"},
            {"id": "F26.2", "status": "blocked_user_waiver"},
            {"id": "F26.3", "status": "partial_backend_image_missing"},
            {"id": "F26.4", "status": "partial_image_and_security_missing"},
            {"id": "F26.5", "status": "partial_structural_scan_only"},
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
    blockers = "\n".join(f"- {item}" for item in report["release_decision"]["blocking_reasons"])
    gates = "\n".join(
        f"- {name}: {item['status']}（approved={str(item['approved']).lower()}）"
        for name, item in report["four_go"].items()
    )
    return f"""# RC0810-F26 最终 RC 收口与发布建议

结论：**NO-GO**。本报告完成工程材料收口，不代表 RC 已形成、平台已批准、已发布或已稳定运行。

## 候选基线

- commit：`{candidate['source_commit']}`
- tree：`{candidate['source_tree']}`
- 打包方式：隔离 Git archive；未从脏工作区直接打包
- production 小程序 ZIP：`{report['artifacts']['miniprogram_zip']['sha256']}`
- 后端镜像：缺失，未伪造 digest

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

波次 C 先由固定 reviewer 独立审查累计 diff 与本证据包。之后仍须补齐 required CI、当前安全扫描、正式后端镜像、微信平台与真机证据、四方签署和候选观察，才能重新判定 GO。
"""


def _review_decision_errors(review: dict[str, Any], decision_artifact: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    path_value = decision_artifact.get("path")
    if not isinstance(path_value, str) or not path_value.startswith("docs/02_专项进度与验收/"):
        return ["review_decision_path_invalid"]
    path = ROOT / path_value
    if not path.is_file() or _sha256(path.read_bytes()) != decision_artifact.get("sha256"):
        return ["review_decision_artifact_invalid"]
    decision = _read_json(path)
    if decision.get("schema") != "safehome.rc0810.wave-c-review-decision.v1":
        errors.append("review_decision_schema_invalid")
    if decision.get("reviewer_id") != "sartre_replacement" or decision.get("decision") != "pass":
        errors.append("review_decision_not_independent_pass")
    if decision.get("reviewed_base") != review.get("base_commit"):
        errors.append("review_base_mismatch")
    if decision.get("reviewed_head") != review.get("reviewed_head"):
        errors.append("review_head_mismatch")
    if decision.get("packet_sha256") != review.get("packet_sha256"):
        errors.append("review_packet_mismatch")
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
    if any(item.get("required") is not True or item.get("status") != "not_run_user_waiver" for item in required_ci):
        errors.append("required_ci_must_remain_unverified")
    security = report.get("security_evidence", {})
    if security.get("source_tree") == candidate.get("source_tree") or security.get("current_status") != "stale":
        errors.append("stale_security_evidence_promoted")
    image = report.get("artifacts", {}).get("backend_image", {})
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
    if review.get("reviewer_id") != "sartre_replacement":
        errors.append("fixed_reviewer_mismatch")
    if review.get("status") == "review_pass":
        artifact = review.get("decision_artifact")
        if not isinstance(artifact, dict):
            errors.append("review_pass_without_decision_artifact")
        else:
            errors.extend(_review_decision_errors(review, artifact))
    elif review.get("status") != "review_pending_wave":
        errors.append("wave_c_review_status_invalid")
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


def apply_review_decision(report_path: Path, decision_path: Path, markdown_path: Path) -> dict[str, Any]:
    report = _read_json(report_path)
    decision = _read_json(decision_path)
    review = report["wave_c_review"]
    review.update({
        "status": "review_pass" if decision.get("decision") == "pass" else "review_failed",
        "reviewed_head": decision.get("reviewed_head"),
        "packet_path": decision.get("packet_path"),
        "packet_sha256": decision.get("packet_sha256"),
        "decision_artifact": {
            "path": decision_path.relative_to(ROOT).as_posix(),
            "sha256": _sha256(decision_path.read_bytes()),
        },
    })
    report["task_status"] = "complete_no_go" if review["status"] == "review_pass" else "fix_required"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--source-commit")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--apply-review-decision", type=Path)
    args = parser.parse_args()
    if args.write_report:
        build_report(args.report, markdown_path=args.markdown, commit=args.source_commit)
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
