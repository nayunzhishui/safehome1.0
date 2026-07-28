"""Low-risk adult L1/L2 first-release scope for Task38-F13."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from database import (
    get_connection,
    json_dumps,
    json_loads,
    new_id,
    now_iso,
    row_to_dict,
    write_audit_log,
)
from services.therapeutic_assessment_service import (
    FORMAL_ROLES,
    TherapeuticAssessmentError,
    _assert_read,
    _case_row,
    _idempotency,
)


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "content" / "therapeutic_assessment_adult_launch_policy.json"
AGE_BANDS = {"adult", "minor", "unknown"}
DATA_SCOPES = {"single_person", "multi_party", "unknown"}
URGENCY_LEVELS = {"non_urgent", "urgent", "unknown"}
DECISIONS = {
    "eligible_l1_l2",
    "human_review_required",
    "outside_first_release_scope",
}


@lru_cache(maxsize=1)
def policy() -> dict:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if payload.get("schema") != "safehome.therapeutic-assessment.adult-launch.v1":
        raise RuntimeError("低风险成人首发政策schema无效")
    if payload.get("production_release_approved") is not False:
        raise RuntimeError("低风险成人首发政策不能自动批准生产发布")
    return payload


def public_scope() -> dict:
    payload = policy()
    return {
        "schema": payload["schema"],
        "version": payload["version"],
        "allowed_levels": list(payload["allowed_levels"]),
        "eligible_age_bands": list(payload["eligible_age_bands"]),
        "allowed_data_scopes": list(payload["allowed_data_scopes"]),
        "allowed_urgency": list(payload["allowed_urgency"]),
        "allowed_concern_scopes": list(payload["allowed_concern_scopes"]),
        "excluded_methods": list(payload["excluded_methods"]),
        "required_notices": list(payload["required_notices"]),
        "notices": dict(payload["notices"]),
        "external_gates_required": bool(payload["external_gates_required"]),
        "production_release_approved": False,
        "temporary_showcase_counts_as_release": False,
        "boundary_notice": payload["boundary_notice"],
    }


def _string(payload: dict, name: str, allowed: set[str]) -> str:
    value = str(payload.get(name) or "").strip()
    if value not in allowed:
        raise TherapeuticAssessmentError(
            "validation_error",
            f"{name}不在允许范围内。",
        )
    return value


def _string_list(payload: dict, name: str) -> list[str]:
    value = payload.get(name)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise TherapeuticAssessmentError("validation_error", f"{name}必须是字符串列表。")
    return sorted({item.strip() for item in value if item.strip()})


def _decision(
    *,
    age_band: str,
    voluntary_participation: bool,
    data_scope: str,
    urgency: str,
    concern_scope: str,
    excluded_signals: list[str],
    acknowledged_notices: list[str],
) -> tuple[str, list[str], str]:
    payload = policy()
    hard_reasons: list[str] = []
    review_reasons: list[str] = []
    if age_band == "minor":
        hard_reasons.append("minor_or_unknown_age")
    elif age_band == "unknown":
        review_reasons.append("unknown_age")
    if voluntary_participation is not True:
        hard_reasons.append("not_voluntary")
    if data_scope == "multi_party":
        hard_reasons.append("multi_party_data")
    elif data_scope == "unknown":
        review_reasons.append("unknown_data_scope")
    if urgency == "urgent":
        hard_reasons.append("urgent_or_emergency")
    elif urgency == "unknown":
        review_reasons.append("unknown_urgency")
    if concern_scope not in payload["allowed_concern_scopes"]:
        hard_reasons.append("unsupported_concern_scope")
    if set(excluded_signals) & set(payload["excluded_signals"]):
        hard_reasons.append("excluded_safety_signal")
    if not set(payload["required_notices"]).issubset(set(acknowledged_notices)):
        review_reasons.append("missing_required_notices")
    if hard_reasons:
        return (
            "outside_first_release_scope",
            sorted(set(hard_reasons + review_reasons)),
            str(payload["outside_scope_route"]),
        )
    if review_reasons:
        return (
            "human_review_required",
            sorted(set(review_reasons)),
            "human_scope_review",
        )
    return "eligible_l1_l2", [], "continue_engineering_flow"


def _present(row: dict) -> dict:
    item = dict(row)
    item["voluntary_participation"] = bool(item["voluntary_participation"])
    item["excluded_signals"] = json_loads(item.pop("excluded_signals_json"), [])
    item["acknowledged_notices"] = json_loads(
        item.pop("acknowledged_notices_json"), []
    )
    item["reason_codes"] = json_loads(item.pop("reason_codes_json"), [])
    item["external_gates_required"] = True
    item["production_release_approved"] = False
    item["temporary_showcase_counts_as_release"] = False
    item["boundary_notice"] = policy()["boundary_notice"]
    return item


def record_screening(
    actor: dict,
    case_id: str,
    payload: dict,
    idempotency_key: str,
) -> tuple[dict, int]:
    key = _idempotency(idempotency_key)
    requested_level = str(payload.get("requested_level") or "").strip()
    if requested_level not in policy()["allowed_levels"]:
        raise TherapeuticAssessmentError(
            "validation_error",
            "首发筛查只接受L1或L2。",
        )
    age_band = _string(payload, "age_band", AGE_BANDS)
    data_scope = _string(payload, "data_scope", DATA_SCOPES)
    urgency = _string(payload, "urgency", URGENCY_LEVELS)
    concern_scope = str(payload.get("concern_scope") or "").strip()
    if not concern_scope or len(concern_scope) > 100:
        raise TherapeuticAssessmentError("validation_error", "concern_scope无效。")
    voluntary = payload.get("voluntary_participation")
    if not isinstance(voluntary, bool):
        raise TherapeuticAssessmentError(
            "validation_error",
            "voluntary_participation必须明确选择。",
        )
    excluded_signals = _string_list(payload, "excluded_signals")
    acknowledged_notices = _string_list(payload, "acknowledged_notices")
    unknown_signals = set(excluded_signals) - set(policy()["excluded_signals"])
    if unknown_signals:
        raise TherapeuticAssessmentError(
            "validation_error",
            "包含不支持的安全信号。",
        )
    expected_case_version = payload.get("expected_case_version")
    if not isinstance(expected_case_version, int) or expected_case_version < 1:
        raise TherapeuticAssessmentError(
            "validation_error",
            "expected_case_version无效。",
        )
    with get_connection() as conn:
        existing = conn.execute(
            """SELECT * FROM therapeutic_assessment_launch_screenings
            WHERE recorded_by = ? AND idempotency_key = ?""",
            (str(actor["id"]), key),
        ).fetchone()
        if existing is not None:
            item = row_to_dict(existing)
            if str(item["case_id"]) != case_id:
                raise TherapeuticAssessmentError(
                    "idempotency_conflict",
                    "该幂等键已用于其它协作记录。",
                    409,
                )
            return _present(item), 200
        case = _case_row(conn, case_id)
        _assert_read(actor, case)
        role = str(actor.get("role") or "")
        if (
            str(actor["id"]) != str(case["participant_user_id"])
            and role not in FORMAL_ROLES
        ):
            raise TherapeuticAssessmentError(
                "forbidden",
                "当前账号不能登记该记录的首发范围。",
                403,
            )
        if (
            case["status"] == "withdrawn"
            or case["consent_status"] == "withdrawn"
        ):
            raise TherapeuticAssessmentError(
                "withdrawn",
                "该协作已经撤回，不能继续首发筛查。",
                409,
            )
        if int(case["version"]) != expected_case_version:
            raise TherapeuticAssessmentError(
                "version_conflict",
                "记录已更新，请刷新后重试。",
                409,
            )
        decision, reason_codes, recommended_route = _decision(
            age_band=age_band,
            voluntary_participation=voluntary,
            data_scope=data_scope,
            urgency=urgency,
            concern_scope=concern_scope,
            excluded_signals=excluded_signals,
            acknowledged_notices=acknowledged_notices,
        )
        if decision not in DECISIONS:
            raise RuntimeError("首发范围决策无效")
        screening_id = new_id("ta_launch")
        timestamp = now_iso()
        conn.execute(
            """INSERT INTO therapeutic_assessment_launch_screenings
            (id, case_id, participant_user_id, requested_level, age_band,
             voluntary_participation, data_scope, urgency, concern_scope,
             excluded_signals_json, acknowledged_notices_json, decision,
             reason_codes_json, recommended_route, policy_version, case_version,
             recorded_by, version, idempotency_key, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)""",
            (
                screening_id,
                case_id,
                str(case["participant_user_id"]),
                requested_level,
                age_band,
                int(voluntary),
                data_scope,
                urgency,
                concern_scope,
                json_dumps(excluded_signals),
                json_dumps(acknowledged_notices),
                decision,
                json_dumps(reason_codes),
                recommended_route,
                str(policy()["version"]),
                expected_case_version,
                str(actor["id"]),
                key,
                timestamp,
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_launch_scope_recorded",
            str(actor["id"]),
            "therapeutic_assessment_case",
            case_id,
            {
                "decision": decision,
                "reason_codes": reason_codes,
                "requested_level": requested_level,
                "policy_version": policy()["version"],
            },
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM therapeutic_assessment_launch_screenings WHERE id = ?",
            (screening_id,),
        ).fetchone()
        return _present(row_to_dict(row)), 201


def latest_screening(actor: dict, case_id: str) -> dict:
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        _assert_read(actor, case)
        row = conn.execute(
            """SELECT * FROM therapeutic_assessment_launch_screenings
            WHERE case_id = ? ORDER BY created_at DESC LIMIT 1""",
            (case_id,),
        ).fetchone()
        write_audit_log(
            conn,
            "therapeutic_assessment_launch_scope_viewed",
            str(actor["id"]),
            "therapeutic_assessment_case",
            case_id,
            {"found": row is not None},
        )
        conn.commit()
        if row is None:
            return {
                "case_id": case_id,
                "decision": "screening_required",
                "external_gates_required": True,
                "production_release_approved": False,
                "temporary_showcase_counts_as_release": False,
                "boundary_notice": policy()["boundary_notice"],
            }
        return _present(row_to_dict(row))
