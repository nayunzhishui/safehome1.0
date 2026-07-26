"""Static contract audit for Task36 F16."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    model = text("backend/models.py")
    service = text("backend/services/therapeutic_assessment_service.py")
    routes = text("backend/routes/therapeutic_assessment.py")
    mini = text("apps/miniprogram/pages/therapeutic-assessment/index.wxml")
    web = text("apps/web/src/pages/TherapeuticAssessmentWorkbench.tsx")
    privacy = json.loads(text("content/privacy_retention_policy.json"))

    for table in (
        "therapeutic_assessment_cases",
        "therapeutic_assessment_feedback_versions",
        "therapeutic_assessment_actions",
        "therapeutic_assessment_events",
    ):
        assert table in model
    for marker in (
        "consent_required",
        "version_conflict",
        "readiness_gate",
        "external_gate_required",
        "human_review_required",
        "risk_review_required",
        "efficacy_score",
    ):
        assert marker in service
    assert "elevate_actor_for_showcase" not in routes
    assert "共同理解一次关系体验" in mini
    assert "AI 只能生成草稿" in web
    assert "therapeutic_assessment" in privacy["scope_labels"]
    assert "疗效分数" in mini and "诊断" in mini
    print("T36-F16 therapeutic-assessment audit: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
