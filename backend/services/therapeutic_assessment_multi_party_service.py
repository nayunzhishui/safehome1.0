"""Multi-party consent and safety separation for Task38-F15."""

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
    _case_row,
    _event,
    _idempotency,
)


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "content" / "therapeutic_assessment_multi_party_policy.json"
CONSENT_DECISIONS = {"consent": "active", "refuse": "refused", "withdraw": "withdrawn"}


@lru_cache(maxsize=1)
def policy() -> dict:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if (
        payload.get("schema") != "safehome.therapeutic-assessment.multi-party.v1"
        or payload.get("entry_enabled") is not False
        or payload.get("production_release_approved") is not False
    ):
        raise RuntimeError("伴侣与多人保护政策无效")
    return payload


def public_policy() -> dict:
    payload = policy()
    return {
        "schema": payload["schema"],
        "version": payload["version"],
        "entry_enabled": False,
        "production_release_approved": False,
        "individual_disclosure_joint_default": False,
        "relationship_cycle_must_not_equalize_harm": True,
        "precheck_signals": list(payload["precheck_signals"]),
        "required_external_gates": list(payload["required_external_gates"]),
        "temporary_showcase_counts_as_permission": False,
        "boundary_notice": payload["boundary_notice"],
    }


def _row(conn, case_id: str) -> dict:
    row = conn.execute(
        "SELECT * FROM therapeutic_assessment_multi_party_safeguards WHERE case_id = ?",
        (case_id,),
    ).fetchone()
    if row is None:
        raise TherapeuticAssessmentError(
            "not_found",
            "尚未建立该记录的多人保护范围。",
            404,
        )
    return row_to_dict(row)


def _decode(item: dict) -> tuple[list[str], dict, dict]:
    return (
        json_loads(item["party_user_ids_json"], []),
        json_loads(item["party_consents_json"], {}),
        json_loads(item["screening_by_party_json"], {}),
    )


def _assert_visible(actor: dict, case: dict, item: dict) -> None:
    parties, _, _ = _decode(item)
    actor_id = str(actor["id"])
    role = str(actor.get("role") or "")
    if not (
        actor_id in parties
        or role in REVIEW_ROLES
        or (
            role == "researcher"
            and actor_id == str(case.get("assigned_researcher_id") or "")
        )
    ):
        raise TherapeuticAssessmentError(
            "forbidden",
            "当前账号没有该多人保护记录的对象范围权限。",
            403,
        )


def _has_signal(screenings: dict) -> bool:
    return any(any(bool(value) for value in values.values()) for values in screenings.values())


def _status(item: dict, consents: dict, screenings: dict) -> str:
    if _has_signal(screenings):
        return "separate_support_required"
    if any(value in {"refused", "withdrawn"} for value in consents.values()):
        return "blocked_party_refusal"
    if not consents or any(value != "active" for value in consents.values()):
        return "blocked_pending_multi_party"
    if set(screenings) != set(consents):
        return "blocked_pending_multi_party"
    if not all(
        str(item.get(name) or "").strip()
        for name in ("t3_evidence_ref", "ethics_evidence_ref", "pilot_evidence_ref")
    ):
        return "blocked_external_gates"
    return "specialist_review_ready"


def _present(item: dict, actor: dict) -> dict:
    result = dict(item)
    parties, consents, screenings = _decode(result)
    result.pop("party_user_ids_json", None)
    result.pop("party_consents_json", None)
    result.pop("screening_by_party_json", None)
    result["party_user_ids"] = parties
    result["party_consents"] = consents
    result["safety_signal_present"] = _has_signal(screenings)
    result["individual_disclosure_joint_default"] = False
    result["joint_feedback_allowed"] = (
        result["status"] == "specialist_review_ready"
        and not result["safety_signal_present"]
    )
    result["entry_enabled"] = False
    result["production_release_approved"] = False
    result["temporary_showcase_counts_as_permission"] = False
    result["boundary_notice"] = policy()["boundary_notice"]
    if str(actor.get("role") or "") in FORMAL_ROLES:
        result["screening_by_party"] = screenings
    else:
        result["your_screening_completed"] = str(actor["id"]) in screenings
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
            "多人保护范围只能由督导或管理员建立。",
            403,
        )
    key = _idempotency(idempotency_key)
    party_ids = payload.get("party_user_ids")
    expected = payload.get("expected_case_version")
    if (
        not isinstance(party_ids, list)
        or len(set(party_ids)) < 2
        or any(not isinstance(item, str) or not item.strip() for item in party_ids)
        or not isinstance(expected, int)
    ):
        raise TherapeuticAssessmentError("validation_error", "参与方列表或case版本无效。")
    party_ids = sorted(set(party_ids))
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        existing = conn.execute(
            """SELECT * FROM therapeutic_assessment_multi_party_safeguards
            WHERE created_by = ? AND idempotency_key = ?""",
            (str(actor["id"]), key),
        ).fetchone()
        if existing is not None:
            return _present(row_to_dict(existing), actor), 200
        if conn.execute(
            "SELECT 1 FROM therapeutic_assessment_multi_party_safeguards WHERE case_id = ?",
            (case_id,),
        ).fetchone():
            raise TherapeuticAssessmentError("already_exists", "该记录已建立多人保护范围。", 409)
        if (
            int(case["version"]) != expected
            or case["complexity_scope"] not in {"couple", "multi_person"}
            or str(case["participant_user_id"]) not in party_ids
        ):
            raise TherapeuticAssessmentError(
                "scope_mismatch",
                "case版本、多人范围或参与方不匹配。",
                409,
            )
        placeholders = ",".join("?" for _ in party_ids)
        users = conn.execute(
            f"SELECT id, role, status FROM users WHERE id IN ({placeholders})",
            tuple(party_ids),
        ).fetchall()
        if (
            len(users) != len(party_ids)
            or any(row["status"] != "active" or row["role"] not in {"parent", "student"} for row in users)
        ):
            raise TherapeuticAssessmentError("validation_error", "参与方账号无效。")
        timestamp = now_iso()
        safeguard_id = new_id("ta_multi")
        conn.execute(
            """INSERT INTO therapeutic_assessment_multi_party_safeguards
            (id, case_id, party_user_ids_json, party_consents_json,
             screening_by_party_json, individual_disclosure_joint_default,
             status, policy_version, version, created_by, last_actor_id,
             idempotency_key, created_at, updated_at)
            VALUES (?, ?, ?, ?, '{}', 0, 'blocked_pending_multi_party', ?, 1,
                    ?, ?, ?, ?, ?)""",
            (
                safeguard_id,
                case_id,
                json_dumps(party_ids),
                json_dumps({user_id: "pending" for user_id in party_ids}),
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
            "therapeutic_assessment_multi_party_initialized",
            str(actor["id"]),
            "therapeutic_assessment_case",
            case_id,
            {"party_count": len(party_ids), "joint_default": False},
        )
        conn.commit()
        return _present(_row(conn, case_id), actor), 201


def update_consent(
    actor: dict,
    case_id: str,
    payload: dict,
    idempotency_key: str,
) -> dict:
    key = _idempotency(idempotency_key)
    decision = str(payload.get("decision") or "")
    expected = payload.get("expected_version")
    if decision not in CONSENT_DECISIONS or not isinstance(expected, int):
        raise TherapeuticAssessmentError("validation_error", "决定或版本无效。")
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        item = _row(conn, case_id)
        _assert_visible(actor, case, item)
        parties, consents, screenings = _decode(item)
        actor_id = str(actor["id"])
        if actor_id not in parties:
            raise TherapeuticAssessmentError("forbidden", "只能处理自己的多人同意。", 403)
        if conn.execute(
            "SELECT 1 FROM therapeutic_assessment_events WHERE actor_id = ? AND idempotency_key = ?",
            (actor_id, key),
        ).fetchone():
            return _present(item, actor)
        if int(item["version"]) != expected:
            raise TherapeuticAssessmentError("version_conflict", "记录已更新，请刷新。", 409)
        consents[actor_id] = CONSENT_DECISIONS[decision]
        status = _status(item, consents, screenings)
        _update_json(conn, item, actor, key, consents, screenings, status, f"multi_party_{decision}")
        return _present(_row(conn, case_id), actor)


def update_safety_screen(
    actor: dict,
    case_id: str,
    payload: dict,
    idempotency_key: str,
) -> dict:
    key = _idempotency(idempotency_key)
    expected = payload.get("expected_version")
    signals = {}
    for name in policy()["precheck_signals"]:
        value = payload.get(name)
        if not isinstance(value, bool):
            raise TherapeuticAssessmentError("validation_error", "安全预检需要逐项明确选择。")
        signals[name] = value
    if not isinstance(expected, int):
        raise TherapeuticAssessmentError("validation_error", "expected_version无效。")
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        item = _row(conn, case_id)
        _assert_visible(actor, case, item)
        parties, consents, screenings = _decode(item)
        actor_id = str(actor["id"])
        if actor_id not in parties:
            raise TherapeuticAssessmentError("forbidden", "只能完成自己的安全预检。", 403)
        if conn.execute(
            "SELECT 1 FROM therapeutic_assessment_events WHERE actor_id = ? AND idempotency_key = ?",
            (actor_id, key),
        ).fetchone():
            return _present(item, actor)
        if int(item["version"]) != expected:
            raise TherapeuticAssessmentError("version_conflict", "记录已更新，请刷新。", 409)
        screenings[actor_id] = signals
        status = _status(item, consents, screenings)
        _update_json(conn, item, actor, key, consents, screenings, status, "multi_party_safety_screened")
        return _present(_row(conn, case_id), actor)


def _update_json(
    conn,
    item: dict,
    actor: dict,
    key: str,
    consents: dict,
    screenings: dict,
    status: str,
    action: str,
) -> None:
    before = int(item["version"])
    timestamp = now_iso()
    cursor = conn.execute(
        """UPDATE therapeutic_assessment_multi_party_safeguards
        SET party_consents_json = ?, screening_by_party_json = ?, status = ?,
            version = version + 1, last_actor_id = ?, updated_at = ?
        WHERE case_id = ? AND version = ?""",
        (
            json_dumps(consents),
            json_dumps(screenings),
            status,
            str(actor["id"]),
            timestamp,
            item["case_id"],
            before,
        ),
    )
    if cursor.rowcount != 1:
        raise TherapeuticAssessmentError("version_conflict", "记录已更新，请刷新。", 409)
    _event(
        conn,
        str(item["case_id"]),
        actor,
        action,
        key,
        before,
        before + 1,
        {"status": status, "joint_feedback_allowed": status == "specialist_review_ready"},
    )
    write_audit_log(
        conn,
        "therapeutic_assessment_multi_party_updated",
        str(actor["id"]),
        "therapeutic_assessment_case",
        str(item["case_id"]),
        {"action": action, "status": status},
    )
    conn.commit()


def update_gates(
    actor: dict,
    case_id: str,
    payload: dict,
    idempotency_key: str,
) -> dict:
    if str(actor.get("role") or "") not in REVIEW_ROLES:
        raise TherapeuticAssessmentError("forbidden", "多人外部门禁只能由督导或管理员登记。", 403)
    key = _idempotency(idempotency_key)
    expected = payload.get("expected_version")
    refs = {
        name: str(payload.get(name) or "").strip()[:500]
        for name in ("t3_evidence_ref", "ethics_evidence_ref", "pilot_evidence_ref")
    }
    if not isinstance(expected, int) or not all(refs.values()):
        raise TherapeuticAssessmentError("validation_error", "T3、伦理、试点证据和版本不能为空。")
    with get_connection() as conn:
        item = _row(conn, case_id)
        if int(item["version"]) != expected:
            raise TherapeuticAssessmentError("version_conflict", "记录已更新，请刷新。", 409)
        if conn.execute(
            "SELECT 1 FROM therapeutic_assessment_events WHERE actor_id = ? AND idempotency_key = ?",
            (str(actor["id"]), key),
        ).fetchone():
            return _present(item, actor)
        _, consents, screenings = _decode(item)
        candidate = {**item, **refs}
        status = _status(candidate, consents, screenings)
        timestamp = now_iso()
        conn.execute(
            """UPDATE therapeutic_assessment_multi_party_safeguards
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
        _event(conn, case_id, actor, "multi_party_gates_recorded", key, expected, expected + 1, {"status": status})
        write_audit_log(
            conn,
            "therapeutic_assessment_multi_party_gates_recorded",
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
        _assert_visible(actor, case, item)
        write_audit_log(
            conn,
            "therapeutic_assessment_multi_party_viewed",
            str(actor["id"]),
            "therapeutic_assessment_case",
            case_id,
            {"status": item["status"]},
        )
        conn.commit()
        return _present(item, actor)
