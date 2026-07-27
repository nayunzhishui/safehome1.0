"""Fail-closed data-use authorization for Task 37.

This module validates machine-readable purpose and consent boundaries. It does
not decide ethics, professional suitability, or production release.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import PROJECT_ROOT


GOVERNANCE_PATH = PROJECT_ROOT / "content" / "task37_data_use_governance.json"


class DataUseDenied(ValueError):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}


def load_governance(path: Path | None = None) -> dict[str, Any]:
    target = path or GOVERNANCE_PATH
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DataUseDenied("governance_unavailable", "数据用途治理契约不可用") from exc
    if payload.get("schema_version") != "safehome.task37-data-use-governance.v1":
        raise DataUseDenied("governance_invalid", "数据用途治理契约版本无效")
    return payload


def _require_consent(request_data: dict[str, Any], purpose: str) -> str:
    consent = request_data.get("consent")
    if not isinstance(consent, dict) or consent.get("agreed") is not True or consent.get("revoked") is True:
        raise DataUseDenied("explicit_opt_in_required", "该数据用途需要当前有效的独立主动授权")
    if consent.get("purpose") != purpose:
        raise DataUseDenied("consent_purpose_mismatch", "授权用途与本次数据用途不一致")
    version = str(consent.get("version") or "").strip()
    if not version:
        raise DataUseDenied("consent_version_required", "授权记录缺少版本")
    return version


def _validate_source(governance: dict[str, Any], request_data: dict[str, Any], purpose: str) -> tuple[str, str | None]:
    source_kind = str(request_data.get("source_kind") or "").strip()
    source_rule = governance["source_rules"].get(source_kind)
    if source_rule is None:
        raise DataUseDenied("source_kind_unknown", "未知数据来源类型")

    if request_data.get("contains_identifiable_data") is True and purpose in {"model_training", "secondary_research"}:
        raise DataUseDenied("de_identification_required", "训练或二次研究不得使用可识别参与者数据")

    if source_rule.get("participant_data") is True:
        return "explicit_opt_in", _require_consent(request_data, purpose)

    approved_statuses = set(source_rule.get("approved_rights_statuses") or [])
    if request_data.get("rights_status") not in approved_statuses:
        raise DataUseDenied("source_rights_not_approved", "来源权利状态未批准")
    return "not_applicable_no_participant_data", None


def authorize_data_use(request_data: dict[str, Any]) -> dict[str, Any]:
    """Authorize one bounded computation request or fail closed."""

    governance = load_governance()
    domain = str(request_data.get("domain") or "").strip()
    purpose = str(request_data.get("purpose") or "").strip()
    domain_rule = governance["domains"].get(domain)
    if domain_rule is None:
        raise DataUseDenied("domain_unknown", "未知计算领域")
    purpose_rule = governance["data_purposes"].get(purpose)
    if purpose_rule is None:
        raise DataUseDenied("purpose_unknown", "未知数据用途")

    requested_use = str(request_data.get("requested_use") or "").strip()
    if requested_use and requested_use in set(domain_rule.get("prohibited_uses") or []):
        raise DataUseDenied(
            "prohibited_use",
            "请求用途属于禁止用途",
            {"domain": domain, "requested_use": requested_use},
        )

    consent_basis, consent_version = _validate_source(governance, request_data, purpose)
    return {
        "allowed": True,
        "domain": domain,
        "purpose": purpose,
        "requested_use": requested_use or None,
        "governance_version": governance["version"],
        "consent_basis": consent_basis,
        "consent_version": consent_version,
        "participant_visible_risk_conclusion": False,
        "automatic_crisis_action": False,
        "external_review_status": "pending_human_evidence",
    }
