"""Build and verify the machine-readable public API contract.

The Flask route map remains the endpoint inventory source.  This script adds
stable access, pagination, idempotency, error and compatibility metadata, then
derives the shared TypeScript registry, mini-program registry and Markdown
reference from the same JSON contract.
"""

from __future__ import annotations

import argparse
import inspect
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
CONTRACT_PATH = ROOT / "shared" / "contracts" / "api-contract.json"
TS_PATH = ROOT / "shared" / "types" / "api-contract.generated.ts"
MINIPROGRAM_PATH = ROOT / "apps" / "miniprogram" / "services" / "api-contract.generated.js"
DOC_PATH = ROOT / "docs" / "03_技术真相" / "API机器契约.md"
CONTRACT_VERSION = "2026-07-21.2"
ALL_AUTHENTICATED_ROLES = ["parent", "student", "researcher", "supervisor", "admin"]


def _source(view_func) -> str:
    try:
        return inspect.getsource(view_func)
    except (OSError, TypeError):
        return ""


def _access_for(path: str, method: str, module: str, source: str) -> dict[str, Any]:
    if path.startswith("/api/therapeutic-assessment"):
        task_authorization = None
        if "/quality/reviews" in path:
            roles = ["supervisor", "admin"]
            task_authorization = "quality_review"
        elif path.endswith("/impact-analysis"):
            roles = ["supervisor", "admin"]
            task_authorization = "quality_incident_analysis"
        elif "/quality/incidents/" in path and path.endswith("/resolve"):
            roles = ["supervisor", "admin"]
            task_authorization = "quality_incident_resolution"
        elif (
            "/feedback-versions/" in path and (path.endswith("/review") or path.endswith("/send"))
        ) or ("/evidence/" in path and path.endswith("/review")):
            roles = ["supervisor", "admin"]
        elif path.endswith("/readiness") or path.endswith("/assign"):
            roles = ["supervisor", "admin"]
        elif path.endswith("/feedback-versions"):
            roles = ["researcher", "supervisor", "admin"]
        else:
            roles = ALL_AUTHENTICATED_ROLES
        access = {
            "mode": "role",
            "roles": roles,
            "legacy_admin_token": True,
            "showcase_read_bypass": False,
        }
        if task_authorization:
            access["task_authorization"] = task_authorization
        return access
    if path.startswith("/api/research/analysis"):
        roles = ["researcher", "supervisor", "admin"]
        if path.endswith("/execute-synthetic") or path.endswith("/claim") or path.endswith("/complete") or path.endswith("/fail") or path.endswith("/recover") or path.endswith("/suspend") or method == "DELETE":
            roles = ["admin"]
        return {"mode": "role", "roles": roles, "legacy_admin_token": True, "showcase_read_bypass": method == "GET"}
    if path.startswith("/api/operations-governance"):
        if path == "/api/operations-governance/public-status":
            return {"mode": "public", "roles": ["public"], "legacy_admin_token": False, "showcase_read_bypass": False}
        if path == "/api/operations-governance/evidence-packages" or path.endswith("/postmortem"):
            return {"mode": "role", "roles": ["supervisor", "admin"], "legacy_admin_token": True, "showcase_read_bypass": False}
        if path.endswith("/release") or path == "/api/operations-governance/packages/<package_id>/<action>" or path == "/api/operations-governance/runtime/rollback" or "/notifications/" in path:
            return {"mode": "role", "roles": ["admin"], "legacy_admin_token": True, "showcase_read_bypass": False}
        return {"mode": "role", "roles": ["researcher", "supervisor", "admin"], "legacy_admin_token": True, "showcase_read_bypass": False}
    if path == "/api/ux-governance/public-status":
        return {"mode": "public", "roles": ["public"], "legacy_admin_token": False, "showcase_read_bypass": False}
    if path.startswith("/api/ux-governance"):
        if path == "/api/ux-governance/audits":
            roles = ["admin"]
        elif path == "/api/ux-governance/evidence-packages":
            roles = ["supervisor", "admin"]
        else:
            roles = ["researcher", "supervisor", "admin"]
        return {"mode": "role", "roles": roles, "legacy_admin_token": True, "showcase_read_bypass": False}
    if path == "/api/reliability/public-status":
        return {"mode": "public", "roles": ["public"], "legacy_admin_token": False, "showcase_read_bypass": False}
    if path.startswith("/api/reliability"):
        if path == "/api/reliability/evidence-packages":
            roles = ["supervisor", "admin"]
        elif method in {"POST", "PATCH"} and path not in {"/api/reliability/slo-snapshots"}:
            roles = ["admin"]
        else:
            roles = ["researcher", "supervisor", "admin"]
        return {"mode": "role", "roles": roles, "legacy_admin_token": True, "showcase_read_bypass": False}
    if path == "/api/security/public-status":
        return {"mode": "public", "roles": ["public"], "legacy_admin_token": False, "showcase_read_bypass": False}
    if path.startswith("/api/security"):
        roles = ["admin"] if path != "/api/security/workbench" else ["researcher", "supervisor", "admin"]
        return {"mode": "role", "roles": roles, "legacy_admin_token": True, "showcase_read_bypass": False}
    if path == "/api/auth/admin-create-account":
        return {"mode": "admin", "roles": ["admin"], "legacy_admin_token": True, "showcase_read_bypass": False}
    if path == "/api/research/methodology/public-status":
        return {"mode": "public", "roles": ["public"], "legacy_admin_token": False, "showcase_read_bypass": False}
    if path.startswith("/api/research/methodology"):
        if path in {"/api/research/methodology/versions/sync", "/api/research/methodology/disable"}:
            return {"mode": "role", "roles": ["admin"], "legacy_admin_token": True, "showcase_read_bypass": False}
        if path == "/api/research/methodology/evidence-packages":
            return {"mode": "role", "roles": ["supervisor", "admin"], "legacy_admin_token": True, "showcase_read_bypass": False}
        return {"mode": "role", "roles": ["researcher", "supervisor", "admin"], "legacy_admin_token": True, "showcase_read_bypass": False}
    if path.startswith("/api/research/benchmarks"):
        if path in {"/api/research/benchmarks/dataset-cards/sync", "/api/research/benchmarks/disable"}:
            return {"mode": "role", "roles": ["admin"], "legacy_admin_token": True, "showcase_read_bypass": False}
        if path == "/api/research/benchmarks/agreement" or path.endswith("/reviews"):
            return {"mode": "role", "roles": ["supervisor", "admin"], "legacy_admin_token": True, "showcase_read_bypass": False}
        return {"mode": "role", "roles": ["researcher", "supervisor", "admin"], "legacy_admin_token": True, "showcase_read_bypass": False}
    if path.startswith("/api/ai-qa/"):
        if path == "/api/ai-qa/config":
            return {"mode": "public", "roles": ["public"], "legacy_admin_token": False, "showcase_read_bypass": False}
        if path == "/api/ai-qa/kill-switch":
            return {"mode": "role", "roles": ["admin"], "legacy_admin_token": True, "showcase_read_bypass": False}
        if path.endswith("/reviews"):
            return {"mode": "role", "roles": ["supervisor", "admin"], "legacy_admin_token": True, "showcase_read_bypass": False}
        if path in {"/api/ai-qa/evaluation/run", "/api/ai-qa/review/evidence"}:
            return {"mode": "role", "roles": ["researcher", "supervisor", "admin"], "legacy_admin_token": True, "showcase_read_bypass": False}
        return {"mode": "role", "roles": ["researcher", "admin"], "legacy_admin_token": True, "showcase_read_bypass": False}
    if module.endswith("routes.admin"):
        return {"mode": "admin", "roles": ["admin"], "legacy_admin_token": True, "showcase_read_bypass": False}
    if path.startswith("/api/research/"):
        roles = ["researcher", "supervisor", "admin"]
        return {"mode": "role", "roles": roles, "legacy_admin_token": True, "showcase_read_bypass": False}
    if path.startswith("/api/privacy/admin/"):
        return {"mode": "role", "roles": ["supervisor", "admin"], "legacy_admin_token": True, "showcase_read_bypass": False}
    if path == "/api/messages" and method == "POST":
        return {"mode": "role", "roles": ["researcher", "supervisor", "admin"], "legacy_admin_token": True, "showcase_read_bypass": False}
    if path.startswith("/api/research/access"):
        if (path == "/api/research/access/assignments" and method == "POST") or method == "PATCH":
            roles = ["admin"]
        elif path.endswith("/claim"):
            roles = ["researcher"]
        elif path.endswith("/capabilities"):
            roles = ALL_AUTHENTICATED_ROLES
        else:
            roles = ["researcher", "supervisor", "admin"]
        return {"mode": "role", "roles": roles, "legacy_admin_token": True, "showcase_read_bypass": False}
    if path.startswith("/api/profile-results/") or path.startswith("/api/parent-assessments/"):
        return {"mode": "owner_or_authorized", "roles": ALL_AUTHENTICATED_ROLES, "legacy_admin_token": True, "showcase_read_bypass": False}
    if path.startswith("/api/relationship-pilot/researcher/") or any(
        token in path for token in ["/confirm", "/send", "/notes"]
    ) and path.startswith("/api/relationship-pilot/"):
        return {"mode": "role", "roles": ["researcher", "supervisor", "admin"], "legacy_admin_token": True, "showcase_read_bypass": method == "GET"}
    role_call = re.search(r"require_role\((.*?)\)", source, flags=re.DOTALL)
    if role_call:
        roles = re.findall(r"['\"](parent|student|researcher|supervisor|admin)['\"]", role_call.group(1))
        return {"mode": "role", "roles": roles or ALL_AUTHENTICATED_ROLES, "legacy_admin_token": "allow_legacy_admin=True" in role_call.group(1), "showcase_read_bypass": False}
    if "_researcher(" in source:
        return {"mode": "role", "roles": ["researcher", "supervisor", "admin"], "legacy_admin_token": True, "showcase_read_bypass": method == "GET"}
    if "require_login(" in source or "_actor()" in source:
        return {"mode": "authenticated", "roles": ALL_AUTHENTICATED_ROLES, "legacy_admin_token": True, "showcase_read_bypass": method == "GET" and path.startswith("/api/relationship-pilot/")}
    if any(token in source for token in ["require_user_id(", "resolve_actor_user_id(", "resolve_user_id_for_query(", "require_admin_or_owner(", "resolve_privacy_owner(", "_resolve_message_user_id("]):
        return {"mode": "owner_or_authorized", "roles": ALL_AUTHENTICATED_ROLES, "legacy_admin_token": True, "showcase_read_bypass": False}
    if "require_admin_token(" in source:
        return {"mode": "admin", "roles": ["admin"], "legacy_admin_token": True, "showcase_read_bypass": False}
    if path.startswith("/health") or path == "/readyz" or path.startswith("/api/auth/"):
        return {"mode": "public", "roles": ["public"], "legacy_admin_token": False, "showcase_read_bypass": False}
    return {"mode": "public", "roles": ["public"], "legacy_admin_token": False, "showcase_read_bypass": False}


def _object_scope(path: str, access: dict[str, Any], source: str) -> str:
    if path == "/api/therapeutic-assessment/quality/runtime":
        return "authenticated_quality_queue_counts_and_pause_state_no_participant_text"
    if "/api/therapeutic-assessment/quality/reviews" in path:
        return "task_authorized_case_scoped_quality_review_with_version_and_independence_gates"
    if "/api/therapeutic-assessment/quality/incidents" in path:
        return "participant_owned_assigned_or_task_authorized_quality_incident_history"
    if path.endswith("/quality-incidents"):
        return "participant_owned_or_authorized_case_quality_incident_append_only"
    if path == "/api/operations-governance/public-status":
        return "non_sensitive_operations_gate_status_only"
    if path.startswith("/api/operations-governance"):
        return "internal_immutable_artifact_metadata_aggregate_metrics_and_incident_evidence_refs_no_participant_text"
    if path == "/api/ux-governance/public-status":
        return "non_sensitive_ux_gate_status_only"
    if path.startswith("/api/ux-governance"):
        return "internal_page_inventory_and_redacted_machine_evidence_no_participant_text"
    if path == "/api/reliability/public-status":
        return "non_sensitive_reliability_gate_status_only"
    if path.startswith("/api/reliability"):
        return "internal_redacted_reliability_metadata_no_participant_payload"
    if path == "/api/security/public-status":
        return "non_sensitive_security_gate_status_only"
    if path.startswith("/api/security/accounts/"):
        return "admin_only_account_state_without_credentials"
    if path.startswith("/api/security"):
        return "internal_redacted_security_evidence_no_secret_values"
    if path == "/api/research/methodology/public-status":
        return "non_sensitive_gate_status_only"
    if path.startswith("/api/research/methodology"):
        return "internal_pre_freeze_structure_and_synthetic_evidence_no_outcome_rows"
    if path.startswith("/api/research/benchmarks"):
        return "internal_offline_synthetic_or_metadata_only_runs_creator_scoped_for_researcher"
    if path.startswith("/api/ai-qa/sessions") or path.startswith("/api/ai-qa/messages"):
        return "own_synthetic_research_sessions_only"
    if path.startswith("/api/ai-qa/") and access["mode"] != "public":
        return "internal_synthetic_evidence_role_scoped"
    if path.startswith("/api/research/"):
        return "assigned_participants_for_researcher_full_for_supervisor_admin"
    if path.startswith("/api/privacy/admin/"):
        return "full_for_supervisor_admin"
    if path.startswith("/api/privacy/"):
        return "self"
    if path.startswith("/api/messages"):
        return "self_for_participant_assigned_participant_for_researcher_full_for_supervisor_admin"
    if path.startswith("/api/relationship-pilot/"):
        return "self_or_assigned_participant_or_supervisor_admin"
    if any(token in source for token in ["resolve_actor_user_id", "resolve_user_id_for_query", "require_admin_or_owner"]):
        return "self_or_authorized_role"
    if access["mode"] == "public":
        return "not_applicable_or_development_legacy"
    return "role_scoped"


def _pagination(source: str) -> dict[str, Any] | None:
    if not ("page_size" in source and "page" in source):
        return None
    aliases = []
    if "limit" in source:
        aliases.append({"name": "limit", "replacement": "page_size", "remove_after": "2026-10-31"})
    return {"page": "page", "page_size": "page_size", "max_page_size": 100, "response": ["items", "page", "page_size", "total", "has_more"], "deprecated_aliases": aliases}


def _idempotency(path: str, method: str, source: str) -> dict[str, Any]:
    supported = "Idempotency-Key" in source or "idempotency_key" in source
    required = supported and (path.endswith("/actions") or path.endswith("/execute"))
    return {"supported": supported, "required": required, "header": "Idempotency-Key" if supported else None, "max_length": 120 if supported else None}


def _request_contract(path: str, method: str, source: str) -> dict[str, Any]:
    query_parameters = sorted(set(re.findall(r"request\.args\.get\(\s*['\"]([^'\"]+)['\"]", source)))
    body_fields = set(re.findall(r"payload\.get\(\s*['\"]([^'\"]+)['\"]", source))
    body_fields.update(re.findall(r"payload\[\s*['\"]([^'\"]+)['\"]\s*\]", source))
    headers = sorted(set(re.findall(r"request\.headers\.get\(\s*['\"]([^'\"]+)['\"]", source)))
    ai_body_fields = {
        ("/api/ai-qa/sessions", "POST"): ["synthetic_data", "research_use_allowed"],
        ("/api/ai-qa/sessions/<session_id>/messages", "POST"): ["text", "synthetic_data", "fake_mode", "tools"],
        ("/api/ai-qa/messages/<message_id>/feedback", "POST"): ["evaluation", "note", "research_use_allowed"],
        ("/api/ai-qa/evaluation/<run_id>/reviews", "POST"): ["decision", "evidence_path", "note"],
        ("/api/ai-qa/kill-switch", "POST"): ["killed", "reason"],
    }
    body_fields.update(ai_body_fields.get((path, method), []))
    benchmark_body_fields = {
        ("/api/research/benchmarks/cases/<case_id>/annotations", "POST"): ["emotion_label", "valence", "arousal", "context", "reflex_node", "uncertain", "blind_round"],
        ("/api/research/benchmarks/runs/<run_id>/reviews", "POST"): ["decision", "evidence_path", "notes"],
        ("/api/research/benchmarks/disable", "POST"): ["reason"],
    }
    body_fields.update(benchmark_body_fields.get((path, method), []))
    methodology_body_fields = {
        ("/api/research/methodology/checks/run", "POST"): ["version_id"],
        ("/api/research/methodology/simulations/run", "POST"): ["version_id"],
        ("/api/research/methodology/evidence-packages", "POST"): ["version_id"],
        ("/api/research/methodology/disable", "POST"): ["reason"],
    }
    body_fields.update(methodology_body_fields.get((path, method), []))
    security_body_fields = {
        ("/api/security/accounts/<user_id>/status", "PATCH"): ["status", "reason_code", "expected_auth_epoch"],
    }
    body_fields.update(security_body_fields.get((path, method), []))
    reliability_body_fields = {
        ("/api/reliability/slo-snapshots", "POST"): ["environment", "window_minutes"],
        ("/api/reliability/jobs", "POST"): ["job_type", "source_type", "source_id", "idempotency_key", "max_attempts"],
        ("/api/reliability/jobs/<job_id>/claim", "POST"): ["lease_seconds", "force_due"],
        ("/api/reliability/jobs/<job_id>/fail", "POST"): ["error_code"],
        ("/api/reliability/jobs/<job_id>/recover", "POST"): ["reason_code"],
        ("/api/reliability/feature-flags/<flag_name>", "PATCH"): ["enabled", "role_scope", "rollout_percent", "reason_code"],
        ("/api/reliability/feature-flags/<flag_name>/rollback", "POST"): ["target_version", "reason_code"],
        ("/api/reliability/drills", "POST"): ["scenario"],
    }
    body_fields.update(reliability_body_fields.get((path, method), []))
    ux_body_fields = {
        ("/api/ux-governance/audits", "POST"): ["environment", "platform", "viewport", "results"],
    }
    body_fields.update(ux_body_fields.get((path, method), []))
    operations_body_fields = {
        ("/api/operations-governance/packages", "POST"): ["package_version", "previous_package_id", "risk_level", "target_environment"],
        ("/api/operations-governance/packages/<package_id>/reviews", "POST"): ["decision", "evidence_ref", "note"],
        ("/api/operations-governance/packages/<package_id>/approvals", "POST"): ["domain", "decision", "evidence_ref", "note"],
        ("/api/operations-governance/packages/<package_id>/release", "POST"): ["confirmation"],
        ("/api/operations-governance/packages/<package_id>/<action>", "POST"): ["reason_code"],
        ("/api/operations-governance/runtime/rollback", "POST"): ["target_package_id", "reason_code"],
        ("/api/operations-governance/monitoring/snapshots", "POST"): ["window_days", "environment"],
        ("/api/operations-governance/incidents", "POST"): ["capability_id", "package_id", "incident_type", "severity", "evidence_refs", "summary_code"],
        ("/api/operations-governance/incidents/<incident_id>/postmortem", "POST"): ["root_cause_code", "corrective_actions", "evidence_refs"],
        ("/api/operations-governance/incidents/<incident_id>/notifications/<notification_id>/<action>", "POST"): ["error_code"],
    }
    body_fields.update(operations_body_fields.get((path, method), []))
    return {
        "content_type": "application/json" if method in {"POST", "PUT", "PATCH"} else None,
        "path_parameters": sorted(re.findall(r"<(?:(?:int|string|path|uuid):)?([^>]+)>", path)),
        "query_parameters": query_parameters,
        "body_fields": sorted(body_fields),
        "headers": headers,
        "pagination": _pagination(source),
        "idempotency": _idempotency(path, method, source),
    }


def _error_codes(path: str, source: str, access: dict[str, Any]) -> list[str]:
    codes = set(re.findall(r"fail\(\s*['\"]([a-z0-9_]+)['\"]", source))
    if access["mode"] != "public":
        codes.update(["unauthorized", "forbidden"])
    if path.startswith("/api/ai-qa/"):
        codes.update(["ai_qa_sandbox_disabled", "ai_qa_killed", "validation_error"])
        if "/sessions" in path or "/messages" in path:
            codes.update(["not_found", "synthetic_data_required", "research_use_not_authorized", "ai_qa_rate_limited", "ai_qa_budget_exhausted", "ai_qa_tools_forbidden"])
        if path == "/api/ai-qa/kill-switch":
            codes.add("human_gate_required")
    if path.startswith("/api/research/benchmarks"):
        codes.update(["offline_benchmark_disabled", "offline_benchmark_killed", "benchmark_content_invalid"])
        if "/cases" in path:
            codes.update(["case_not_found", "annotation_label_invalid", "annotation_value_invalid", "annotation_value_out_of_range"])
        if "/runs/" in path:
            codes.update(["run_not_found", "review_invalid"])
    if path.startswith("/api/research/methodology"):
        codes.update([
            "methodology_content_invalid",
            "methodology_workbench_disabled",
            "methodology_workbench_killed",
            "methodology_version_missing",
            "methodology_version_immutable",
            "methodology_evidence_incomplete",
            "methodology_evidence_failed",
            "disable_reason_invalid",
        ])
    if path.startswith("/api/security"):
        codes.update(["security_scan_disabled", "state_conflict", "self_disable_forbidden", "not_found", "validation_error"])
    if path.startswith("/api/reliability"):
        codes.update(["reliability_workbench_disabled", "reliability_job_execution_disabled", "job_state_conflict", "job_lease_conflict", "job_not_due", "not_found", "validation_error"])
    codes.update(["internal_error", "http_error"])
    return sorted(codes)


def _enum_refs(path: str) -> list[str]:
    refs = []
    mapping = [
        ("/privacy/", "privacy_request_status"),
        ("/research/work-items", "research_work_item_status"),
        ("/risk-review", "risk_level"),
        ("/assessment", "assessment_status"),
        ("/messages", "message_status"),
        ("/supervision", "supervision_status"),
        ("/relationship-pilot", "relationship_pilot_status"),
        ("/ai-qa/", "ai_qa_route"),
        ("/research/benchmarks", "offline_benchmark_status"),
        ("/research/methodology", "research_methodology_status"),
        ("/security", "security_control_status"),
        ("/reliability", "reliability_control_status"),
    ]
    for token, ref in mapping:
        if token in path:
            refs.append(ref)
    return refs


def build_contract(flask_app) -> dict[str, Any]:
    endpoints = []
    for rule in sorted(flask_app.url_map.iter_rules(), key=lambda item: (item.rule, sorted(item.methods))):
        if rule.endpoint == "static":
            continue
        view_func = flask_app.view_functions[rule.endpoint]
        source = _source(view_func)
        module = str(getattr(view_func, "__module__", ""))
        for method in sorted(set(rule.methods) - {"HEAD", "OPTIONS"}):
            path = str(rule.rule)
            access = _access_for(path, method, module, source)
            pagination = _pagination(source)
            endpoints.append(
                {
                    "operation_id": f"{rule.endpoint}.{method.lower()}",
                    "method": method,
                    "path": path,
                    "handler": rule.endpoint,
                    "module": module,
                    "access": access,
                    "object_scope": _object_scope(path, access, source),
                    "request": _request_contract(path, method, source),
                    "response": {
                        "envelope": "health" if path.startswith("/health") or path == "/readyz" else ("standard_or_download" if "download" in source and "Response(" in source else "standard"),
                        "request_id": True,
                        "data_contract": f"{module}.{getattr(view_func, '__name__', rule.endpoint)}.data",
                    },
                    "error_envelope": {"ok": False, "error": {"code": "string", "message": "string"}, "request_id": "string"},
                    "error_codes": _error_codes(path, source, access),
                    "enum_refs": _enum_refs(path),
                    "deprecation": {"status": "active", "remove_after": None, "replacement": None},
                }
            )
    return {
        "schema": "safehome.api-contract.v1",
        "version": CONTRACT_VERSION,
        "base_path": "/api",
        "compatibility_policy": {
            "additive_fields_allowed": True,
            "deprecated_parameter_notice_days": 90,
            "error_envelope": "standard",
            "request_id_header": "X-Request-ID",
            "rollback": "restore_previous_contract_snapshot_and_module_adapter_without_changing_public_urls",
        },
        "endpoints": endpoints,
    }


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def render_typescript(contract: dict[str, Any]) -> str:
    payload = json.dumps(contract["endpoints"], ensure_ascii=False, indent=2)
    return "// Generated by backend/scripts/build_api_contract.py. Do not edit.\n" f"export const GENERATED_API_CONTRACT_VERSION = {json.dumps(contract['version'])} as const;\n" f"export const GENERATED_API_ENDPOINTS = {payload} as const;\n" "export type GeneratedApiOperationId = (typeof GENERATED_API_ENDPOINTS)[number]['operation_id'];\n"


def render_miniprogram(contract: dict[str, Any]) -> str:
    payload = json.dumps(contract["endpoints"], ensure_ascii=False, indent=2)
    return "// Generated by backend/scripts/build_api_contract.py. Do not edit.\n" f"const GENERATED_API_CONTRACT_VERSION = {json.dumps(contract['version'])};\n" f"const GENERATED_API_ENDPOINTS = {payload};\n\n" "module.exports = { GENERATED_API_CONTRACT_VERSION, GENERATED_API_ENDPOINTS };\n"


def render_markdown(contract: dict[str, Any]) -> str:
    lines = [
        "# API机器契约",
        "",
        f"契约版本：`{contract['version']}`。本文件由`backend/scripts/build_api_contract.py`生成，请勿手工编辑。",
        "",
        "统一成功包络为`{ok:true,data,request_id}`，统一错误包络为`{ok:false,error:{code,message},request_id}`；下载接口除外，但响应头仍含`X-Request-ID`。",
        "",
        "| 方法 | 路径 | 权限 | 对象范围 | 分页 | 幂等 | 状态 |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in contract["endpoints"]:
        roles = ",".join(item["access"]["roles"])
        pagination = "page/page_size" if item["request"]["pagination"] else "—"
        idem = "required" if item["request"]["idempotency"]["required"] else ("supported" if item["request"]["idempotency"]["supported"] else "—")
        lines.append(f"| {item['method']} | `{item['path']}` | {item['access']['mode']}:{roles} | {item['object_scope']} | {pagination} | {idem} | {item['deprecation']['status']} |")
    lines.extend(["", "## 兼容与回滚", "", "旧参数在契约标记的期限内继续可用；CI会比较Flask路由、shared、小程序注册表和本文件。回滚时恢复上一提交的契约快照与对应模块适配器，公开URL保持不变。", ""])
    return "\n".join(lines)


def generated_files(contract: dict[str, Any]) -> dict[Path, str]:
    return {
        CONTRACT_PATH: _json_text(contract),
        TS_PATH: render_typescript(contract),
        MINIPROGRAM_PATH: render_miniprogram(contract),
        DOC_PATH: render_markdown(contract),
    }


def _load_runtime_app():
    # Windows can briefly retain the SQLite handle after importing the Flask
    # module; the generated artifacts are independent from this disposable DB.
    temp_dir = tempfile.TemporaryDirectory(prefix="safehome-api-contract-", ignore_cleanup_errors=True)
    os.environ["APP_ENV"] = "development"
    os.environ["DATABASE_PATH"] = str(Path(temp_dir.name) / "contract.sqlite3")
    os.environ["CONTENT_DIR"] = str(ROOT / "content")
    sys.path.insert(0, str(BACKEND_ROOT))
    from app import app

    return app, temp_dir


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated artifacts differ")
    args = parser.parse_args()
    flask_app, temp_dir = _load_runtime_app()
    try:
        files = generated_files(build_contract(flask_app))
        if args.check:
            stale = [str(path.relative_to(ROOT)) for path, expected in files.items() if not path.exists() or path.read_text(encoding="utf-8") != expected]
            if stale:
                print("API contract drift: " + ", ".join(stale))
                return 1
            print(f"API contract check passed: {len(files)} artifacts")
            return 0
        for path, content in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            print(f"generated {path.relative_to(ROOT)}")
        return 0
    finally:
        temp_dir.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
