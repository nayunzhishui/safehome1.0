"""Generate the deterministic T32 reliability and release registry."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "content" / "reliability_release_registry.json"


def _journey(journey_id: str, label: str, paths: list[str]) -> dict:
    return {
        "journey_id": journey_id,
        "label": label,
        "paths": paths,
        "metrics": [
            "success_rate", "latency_p50_ms", "latency_p95_ms", "error_rate",
            "server_error_rate", "retry_rate", "recovery_rate", "server_error_count",
            "gateway_502_count", "auth_401_count", "forbidden_403_count",
        ],
        "production_target": None,
        "target_status": "pending_test_cloud_observation",
    }


def build_registry() -> dict:
    return {
        "version": "2026-07-22-t36-f09-observability-v1",
        "status": "engineering_controls_ready_external_release_gates_pending",
        "journeys": [
            _journey("authentication", "登录", ["/api/auth/login", "/api/auth/wechat-login", "/api/auth/phone-login"]),
            _journey("diary_submission", "记录提交", ["/api/diaries"]),
            _journey("feedback_generation", "反馈生成", ["/api/feedback/generate"]),
            _journey("training_plan", "训练计划", ["/api/training-plan", "/api/journey/today"]),
            _journey("messages", "消息", ["/api/messages", "/api/notifications"]),
            _journey("training_history", "训练记录", ["/api/checkins"]),
            _journey("researcher_dashboard", "研究者仪表盘", ["/api/relationship-pilot/researcher/dashboard", "/api/research/access"]),
            _journey("research_queue", "研究队列", ["/api/research/work-items", "/api/research/queues"]),
            _journey("ai_sandbox", "AI合成沙盒", ["/api/ai-qa"]),
        ],
        "trace_fields": ["request_id", "actor_scope", "module", "journey", "outcome", "error_code", "status_code", "latency_ms", "retry_count", "recovered"],
        "sensitive_fields_forbidden": ["authorization", "cookie", "password", "token", "phone", "openid", "request_body", "response_body", "participant_text", "stack_trace"],
        "job_adapters": [
            {"job_type": "notification_delivery", "source_table": "notification_deliveries", "lease": True, "idempotency": True, "backoff": "exponential_60s_cap_3600s", "dead_letter": True, "manual_recovery": True},
            {"job_type": "privacy_execution", "source_table": "privacy_request_executions", "lease": True, "idempotency": True, "backoff": "manual_after_transaction_failure", "dead_letter": True, "manual_recovery": True},
            {"job_type": "ai_evaluation", "source_table": "ai_qa_evaluation_runs", "lease": True, "idempotency": True, "backoff": "exponential_60s_cap_3600s", "dead_letter": True, "manual_recovery": True},
            {"job_type": "offline_benchmark", "source_table": "offline_benchmark_runs", "lease": True, "idempotency": True, "backoff": "manual_after_artifact_check", "dead_letter": True, "manual_recovery": True},
            {"job_type": "affective_computation", "source_table": "reliable_jobs", "lease": True, "idempotency": True, "backoff": "exponential_60s_cap_3600s", "dead_letter": True, "manual_recovery": True},
            {"job_type": "social_network_analysis", "source_table": "reliable_jobs", "lease": True, "idempotency": True, "backoff": "exponential_60s_cap_3600s", "dead_letter": True, "manual_recovery": True},
            {"job_type": "participant_ai_qa", "source_table": "reliable_jobs", "lease": True, "idempotency": True, "backoff": "exponential_60s_cap_3600s", "dead_letter": True, "manual_recovery": True},
        ],
        "feature_flags": [
            {"name": "participant_journey", "default_enabled": True, "role_scope": ["parent", "student"], "rollback_default": True},
            {"name": "training_feedback_adaptive_ranking", "default_enabled": True, "role_scope": ["parent", "student"], "rollback_default": False},
            {"name": "research_operations_write", "default_enabled": False, "role_scope": ["researcher", "supervisor", "admin"], "rollback_default": False},
            {"name": "content_governance_publish", "default_enabled": False, "role_scope": ["admin"], "rollback_default": False},
            {"name": "ai_qa_sandbox", "default_enabled": False, "role_scope": ["researcher", "supervisor", "admin"], "rollback_default": False},
            {"name": "offline_benchmark", "default_enabled": False, "role_scope": ["researcher", "supervisor", "admin"], "rollback_default": False},
            {"name": "affective_computing", "default_enabled": False, "role_scope": ["researcher", "supervisor", "admin"], "rollback_default": False},
            {"name": "social_network_analysis", "default_enabled": False, "role_scope": ["researcher", "supervisor", "admin"], "rollback_default": False},
            {"name": "participant_ai_qa", "default_enabled": False, "role_scope": ["parent", "student", "researcher", "supervisor", "admin"], "rollback_default": False},
        ],
        "fault_scenarios": [
            {"scenario": "content_missing", "expected": "readiness_blocked_and_recoverable_message"},
            {"scenario": "database_timeout", "expected": "transaction_rollback_and_retryable_error"},
            {"scenario": "provider_failure", "expected": "backoff_or_safe_degradation"},
            {"scenario": "token_invalidated", "expected": "401_and_relogin_path"},
            {"scenario": "duplicate_message", "expected": "idempotent_single_delivery"},
            {"scenario": "artifact_corrupted", "expected": "hash_rejection_and_runtime_block"},
        ],
        "production_slo": {"status": "pending_test_cloud_observation", "observation_days": None, "thresholds": None, "local_results_acceptable_as_production_commitment": False},
        "alerts": [
            {"level": "P0", "meaning": "safety/privacy/data integrity or total outage", "human_owner": "pending"},
            {"level": "P1", "meaning": "critical journey degradation without immediate safety impact", "human_owner": "pending"},
            {"level": "P2", "meaning": "partial degradation or recoverable backlog", "human_owner": "pending"},
        ],
        "external_gates": ["test_cloud_observation", "cloudbase_gateway_trace", "mysql_backup_restore", "wechat_devtools", "android_ios_real_device", "on_call_owner", "security_privacy_ethics_review", "production_release_approval"],
        "production_release": {"approved": False, "automatic_signature_allowed": False, "temporary_showcase_exception_accepted": False},
    }


def canonical(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = canonical(build_registry())
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != rendered:
            print("reliability registry drift")
            return 1
        print(f"reliability registry check passed: sha256={hashlib.sha256(rendered.encode()).hexdigest()[:16]}")
        return 0
    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"generated {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
