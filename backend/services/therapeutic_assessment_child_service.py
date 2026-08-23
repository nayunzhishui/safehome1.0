"""Separated guardian/child safeguards for Task38-F14."""

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
    REVIEW_ROLES,
    TherapeuticAssessmentError,
    _assert_read,
    _assert_researcher,
    _case_row,
    _event,
    _idempotency,
)


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "content" / "therapeutic_assessment_child_policy.json"
GUARDIAN_ACTIONS = {"guardian_consent": "active", "guardian_withdraw": "withdrawn"}
CHILD_ACTIONS = {
    "child_assent": "assented",
    "child_refuse": "refused",
    "child_withdraw": "withdrawn",
}


@lru_cache(maxsize=1)
def policy() -> dict:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if (
        payload.get("schema")
        != "safehome.therapeutic-assessment.child-safeguards.v1"
        or payload.get("entry_enabled") is not False
        or payload.get("production_release_approved") is not False
    ):
        raise RuntimeError("未成年人保护政策无效")
    return payload


def public_policy() -> dict:
    payload = policy()
    return {
        "schema": payload["schema"],
        "version": payload["version"],
        "entry_enabled": False,
        "production_release_approved": False,
        "guardian_consent_does_not_override_child_refusal": True,
        "required_external_gates": list(payload["required_external_gates"]),
        "source_domains": list(payload["source_domains"]),
        "child_rights": list(payload["child_rights"]),
        "parent_position": payload["parent_position"],
        "temporary_showcase_counts_as_permission": False,
        "boundary_notice": payload["boundary_notice"],
    }


def _row(conn, case_id: str) -> dict:
    row = conn.execute(
        "SELECT * FROM therapeutic_assessment_child_safeguards WHERE case_id = ?",
        (case_id,),
    ).fetchone()
    if row is None:
        raise TherapeuticAssessmentError(
            "not_found",
            "尚未建立该记录的未成年人保护范围。",
            404,
        )
    return row_to_dict(row)


def _visible(conn, actor: dict, case: dict, safeguard: dict) -> bool:
    actor_id = str(actor["id"])
    if actor_id in {
        str(safeguard["guardian_user_id"]),
        str(safeguard["child_user_id"]),
    }:
        return True
    try:
        _assert_read(conn, actor, case)
    except TherapeuticAssessmentError:
        return False
    return True


def _assert_visible(conn, actor: dict, case: dict, safeguard: dict) -> None:
    if not _visible(conn, actor, case, safeguard):
        raise TherapeuticAssessmentError(
            "not_found",
            "没有找到可访问的未成年人保护记录。",
            404,
        )


def _source_permissions() -> dict:
    default = dict(policy()["default_source_permission"])
    return {name: dict(default) for name in policy()["source_domains"]}


def _status(item: dict) -> str:
    if item["child_assent_status"] in {"refused", "withdrawn"}:
        return "blocked_child_refusal"
    if item["guardian_consent_status"] != "active" or item["child_assent_status"] != "assented":
        return "blocked_pending_child_safeguards"
    if not all(
        str(item.get(name) or "").strip()
        for name in ("t3_evidence_ref", "ethics_evidence_ref", "pilot_evidence_ref")
    ):
        return "blocked_external_gates"
    return "specialist_review_ready"


def _present(item: dict, actor: dict) -> dict:
    result = dict(item)
    result["source_permissions"] = json_loads(
        result.pop("source_permissions_json"), {}
    )
    result["entry_enabled"] = False
    result["production_release_approved"] = False
    result["temporary_showcase_counts_as_permission"] = False
    result["child_private_material_auto_shared"] = False
    result["boundary_notice"] = policy()["boundary_notice"]
    if str(actor.get("role") or "") not in FORMAL_ROLES:
        for name in ("t3_evidence_ref", "ethics_evidence_ref", "pilot_evidence_ref"):
            result.pop(name, None)
    return result


def initialize(
    actor: dict,
    case_id: str,
    payload: dict,
    idempotency_key: str,
) -> tuple[dict, int]:
    if str(actor.get("role") or "") not in REVIEW_ROLES:
        raise TherapeuticAssessmentError(
            "forbidden",
            "未成年人保护范围只能由督导或管理员建立。",
            403,
        )
    key = _idempotency(idempotency_key)
    guardian_id = str(payload.get("guardian_user_id") or "").strip()
    child_id = str(payload.get("child_user_id") or "").strip()
    expected = payload.get("expected_case_version")
    if not guardian_id or not child_id or not isinstance(expected, int):
        raise TherapeuticAssessmentError("validation_error", "监护人、儿童和case版本不能为空。")
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        _assert_researcher(conn, actor, case)
        existing = conn.execute(
            """SELECT * FROM therapeutic_assessment_child_safeguards
            WHERE created_by = ? AND idempotency_key = ?""",
            (str(actor["id"]), key),
        ).fetchone()
        if existing is not None:
            item = row_to_dict(existing)
            if item["case_id"] != case_id:
                raise TherapeuticAssessmentError(
                    "idempotency_conflict",
                    "该幂等键已用于其它记录。",
                    409,
                )
            return _present(item, actor), 200
        if conn.execute(
            "SELECT 1 FROM therapeutic_assessment_child_safeguards WHERE case_id = ?",
            (case_id,),
        ).fetchone():
            raise TherapeuticAssessmentError(
                "already_exists",
                "该记录已经建立未成年人保护范围。",
                409,
            )
        if int(case["version"]) != expected:
            raise TherapeuticAssessmentError(
                "version_conflict",
                "记录已更新，请刷新后重试。",
                409,
            )
        if case["complexity_scope"] != "child":
            raise TherapeuticAssessmentError(
                "scope_mismatch",
                "只有未成年人/亲子范围可建立该保护记录。",
                409,
            )
        guardian = conn.execute(
            "SELECT role, status FROM users WHERE id = ?",
            (guardian_id,),
        ).fetchone()
        child = conn.execute(
            "SELECT role, status FROM users WHERE id = ?",
            (child_id,),
        ).fetchone()
        if (
            guardian is None
            or guardian["role"] != "parent"
            or guardian["status"] != "active"
            or child is None
            or child["role"] != "student"
            or child["status"] != "active"
            or child_id != str(case["participant_user_id"])
        ):
            raise TherapeuticAssessmentError(
                "validation_error",
                "监护人、儿童账号或对象范围无效。",
            )
        timestamp = now_iso()
        safeguard_id = new_id("ta_child")
        conn.execute(
            """INSERT INTO therapeutic_assessment_child_safeguards
            (id, case_id, guardian_user_id, child_user_id, source_permissions_json,
             status, policy_version, version, created_by, last_actor_id,
             idempotency_key, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'blocked_pending_child_safeguards', ?, 1,
                    ?, ?, ?, ?, ?)""",
            (
                safeguard_id,
                case_id,
                guardian_id,
                child_id,
                json_dumps(_source_permissions()),
                policy()["version"],
                str(actor["id"]),
                str(actor["id"]),
                key,
                timestamp,
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_child_safeguards_initialized",
            str(actor["id"]),
            "therapeutic_assessment_case",
            case_id,
            {"policy_version": policy()["version"]},
        )
        conn.commit()
        return _present(_row(conn, case_id), actor), 201


def update_decision(
    actor: dict,
    case_id: str,
    payload: dict,
    idempotency_key: str,
) -> dict:
    key = _idempotency(idempotency_key)
    action = str(payload.get("action") or "")
    expected = payload.get("expected_version")
    if not isinstance(expected, int):
        raise TherapeuticAssessmentError("validation_error", "expected_version无效。")
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        item = _row(conn, case_id)
        _assert_visible(conn, actor, case, item)
        replay = conn.execute(
            """SELECT 1 FROM therapeutic_assessment_events
            WHERE actor_id = ? AND idempotency_key = ? AND case_id = ?""",
            (str(actor["id"]), key, case_id),
        ).fetchone()
        if replay:
            return _present(item, actor)
        if int(item["version"]) != expected:
            raise TherapeuticAssessmentError(
                "version_conflict",
                "保护记录已更新，请刷新后重试。",
                409,
            )
        actor_id = str(actor["id"])
        updates: dict[str, str] = {}
        if action in GUARDIAN_ACTIONS:
            if actor_id != str(item["guardian_user_id"]):
                raise TherapeuticAssessmentError(
                    "forbidden",
                    "儿童账号不能代替监护人作出同意。",
                    403,
                )
            updates["guardian_consent_status"] = GUARDIAN_ACTIONS[action]
        elif action in CHILD_ACTIONS:
            if actor_id != str(item["child_user_id"]):
                raise TherapeuticAssessmentError(
                    "forbidden",
                    "监护人不能代替儿童同意或拒绝。",
                    403,
                )
            updates["child_assent_status"] = CHILD_ACTIONS[action]
        else:
            raise TherapeuticAssessmentError("validation_error", "不支持的决定动作。")
        candidate = {**item, **updates}
        status = _status(candidate)
        timestamp = now_iso()
        column = next(iter(updates))
        value = updates[column]
        cursor = conn.execute(
            f"""UPDATE therapeutic_assessment_child_safeguards
            SET {column} = ?, status = ?, version = version + 1,
                last_actor_id = ?, updated_at = ?
            WHERE case_id = ? AND version = ?""",
            (value, status, actor_id, timestamp, case_id, expected),
        )
        if cursor.rowcount != 1:
            raise TherapeuticAssessmentError(
                "version_conflict",
                "保护记录已更新，请刷新后重试。",
                409,
            )
        _event(
            conn,
            case_id,
            actor,
            f"child_safeguard_{action}",
            key,
            expected,
            expected + 1,
            {"status": status},
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_child_decision_updated",
            actor_id,
            "therapeutic_assessment_case",
            case_id,
            {"action": action, "status": status},
        )
        conn.commit()
        return _present(_row(conn, case_id), actor)


def update_gates(
    actor: dict,
    case_id: str,
    payload: dict,
    idempotency_key: str,
) -> dict:
    if str(actor.get("role") or "") not in REVIEW_ROLES:
        raise TherapeuticAssessmentError(
            "forbidden",
            "外部门禁只能由督导或管理员登记。",
            403,
        )
    key = _idempotency(idempotency_key)
    expected = payload.get("expected_version")
    refs = {
        name: str(payload.get(name) or "").strip()[:500]
        for name in ("t3_evidence_ref", "ethics_evidence_ref", "pilot_evidence_ref")
    }
    if not isinstance(expected, int) or not all(refs.values()):
        raise TherapeuticAssessmentError("validation_error", "T3、伦理、试点证据和版本不能为空。")
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        _assert_researcher(conn, actor, case)
        item = _row(conn, case_id)
        replay = conn.execute(
            """SELECT 1 FROM therapeutic_assessment_events
            WHERE actor_id = ? AND idempotency_key = ? AND case_id = ?""",
            (str(actor["id"]), key, case_id),
        ).fetchone()
        if replay:
            return _present(item, actor)
        if int(item["version"]) != expected:
            raise TherapeuticAssessmentError(
                "version_conflict",
                "保护记录已更新，请刷新后重试。",
                409,
            )
        candidate = {**item, **refs}
        status = _status(candidate)
        timestamp = now_iso()
        conn.execute(
            """UPDATE therapeutic_assessment_child_safeguards
            SET t3_evidence_ref = ?, ethics_evidence_ref = ?, pilot_evidence_ref = ?,
                status = ?, version = version + 1, last_actor_id = ?, updated_at = ?
            WHERE case_id = ? AND version = ?""",
            (
                refs["t3_evidence_ref"],
                refs["ethics_evidence_ref"],
                refs["pilot_evidence_ref"],
                status,
                str(actor["id"]),
                timestamp,
                case_id,
                expected,
            ),
        )
        _event(
            conn,
            case_id,
            actor,
            "child_safeguard_gates_recorded",
            key,
            expected,
            expected + 1,
            {"status": status, "evidence_refs_recorded": True},
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_child_gates_recorded",
            str(actor["id"]),
            "therapeutic_assessment_case",
            case_id,
            {"status": status, "evidence_refs_recorded": True},
        )
        conn.commit()
        return _present(_row(conn, case_id), actor)


def get_safeguard(actor: dict, case_id: str) -> dict:
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        item = _row(conn, case_id)
        _assert_visible(conn, actor, case, item)
        write_audit_log(
            conn,
            "therapeutic_assessment_child_safeguards_viewed",
            str(actor["id"]),
            "therapeutic_assessment_case",
            case_id,
            {"status": item["status"]},
        )
        conn.commit()
        return _present(item, actor)
