#!/usr/bin/env python3
"""Static, redacted engineering audit for Task36-F13."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _check(passed: bool, evidence: list[str]) -> dict:
    return {"passed": bool(passed), "evidence": evidence}


def build_report() -> dict:
    service = _read("backend/services/research_analysis_service.py")
    route = _read("backend/routes/research_analysis.py")
    models = _read("backend/models.py")
    migration = _read("backend/scripts/migrate_task36_research_analysis.py")
    shared = _read("shared/types/api.ts")
    web = _read("apps/web/src/pages/ResearchAnalysisWorkbench.tsx")
    mini = _read("apps/miniprogram/pages/researcher-dashboard/index.js")
    tests = _read("backend/tests/test_task36_research_analysis_jobs.py")
    checks = {
        "snapshot_reference_only": _check(
            "research_analysis_snapshot_links" in models
            and "raw_text_included" in service
            and "sensitive_payload_rejected" in service,
            ["backend/models.py", "backend/services/research_analysis_service.py"],
        ),
        "async_lifecycle": _check(
            all(value in service for value in ["queued", "running", "succeeded", "failed", "canceled", "expired", "suspended"])
            and all(value in route for value in ["/claim", "/complete", "/fail", "/recover", "/suspend"]),
            ["backend/services/research_analysis_service.py", "backend/routes/research_analysis.py"],
        ),
        "lease_backoff_dead_letter": _check(
            "lease_expires_at" in service
            and "backoff" in service
            and "dead_lettered_at" in service
            and "test_lease_backoff_dead_letter_recovery" in tests,
            ["backend/services/research_analysis_service.py", "backend/tests/test_task36_research_analysis_jobs.py"],
        ),
        "authorization_freeze_and_delete": _check(
            "_freeze_invalid_snapshot" in service
            and "research_authorization_invalid" in service
            and "derived_data_only" in service,
            ["backend/services/research_analysis_service.py"],
        ),
        "shadow_mode_cross_client": _check(
            "interface ResearchAnalysisJob" in shared
            and "研究者影子模式" in web
            and "loadAnalysisJobs" in mini,
            [
                "shared/types/api.ts",
                "apps/web/src/pages/ResearchAnalysisWorkbench.tsx",
                "apps/miniprogram/pages/researcher-dashboard/index.js",
            ],
        ),
        "migration_and_rollback": _check(
            "2026_07_25_028" in _read("backend/database.py")
            and "schema_preserved" in migration
            and "不自动DROP" in migration,
            ["backend/database.py", "backend/scripts/migrate_task36_research_analysis.py"],
        ),
    }
    passed = all(item["passed"] for item in checks.values())
    return {
        "schema": "safehome.task36.research_analysis_audit.v1",
        "task": "T36-F13",
        "status": "passed" if passed else "failed",
        "engineering_complete": passed,
        "release_approved": False,
        "production_mutations_executed": False,
        "temporary_showcase_bypass_counts_as_formal_permission_evidence": False,
        "checks": checks,
        "external_gates_pending": [
            "cloudbase_schema_migration_approval",
            "research_data_use_and_ethics_review",
            "model_or_dictionary_rights_review",
            "test_cloud_worker_observation",
            "human_researcher_sampling",
            "production_release_approval",
        ],
    }


def main() -> int:
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
