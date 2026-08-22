"""Pre-publication delivery gate for participant-facing AI QA answers.

The core AI service may persist an answer candidate before a human review is
finished. This adapter prevents participant HTTP responses from exposing that
candidate until the linked review case is resolved. It also corrects review
scope metadata using the actual participant role instead of assuming an adult
low-risk subject.
"""

from __future__ import annotations

from copy import deepcopy

from database import get_connection, json_dumps, json_loads, row_to_dict, write_audit_log
from services.ai_qa_service import get_session as core_get_session
from services.ai_qa_service import send_message as core_send_message


PARTICIPANT_ROLES = {"parent", "student"}
PENDING_REVIEW_TEXT = "这条支持性回答正在完成人工复核，复核通过后会在本会话中显示。"
REJECTED_REVIEW_TEXT = "这条候选回答未通过人工复核，因此没有向你展示原候选内容。"


def _risk_rank(value: str | None) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(str(value or "").lower(), 0)


def _derived_risk(message: dict, existing_scope: dict) -> str:
    candidates = [str(existing_scope.get("risk_level") or "low")]
    safety = message.get("safety") if isinstance(message, dict) else {}
    if isinstance(safety, dict):
        for key in ("risk_level", "severity"):
            if safety.get(key):
                candidates.append(str(safety.get(key)))
        precheck = safety.get("precheck")
        if isinstance(precheck, dict) and precheck.get("severity"):
            candidates.append(str(precheck.get("severity")))
        postcheck = safety.get("postcheck")
        if isinstance(postcheck, dict) and postcheck.get("severity"):
            candidates.append(str(postcheck.get("severity")))
    return max(candidates, key=_risk_rank).lower()


def _requirement(scope: dict) -> tuple[str, str]:
    if str(scope.get("risk_level") or "low") == "high":
        return "feedback_review", "T3"
    if scope.get("involves_minor") is True:
        return "minor_or_family", "T3"
    if scope.get("multi_party") is True:
        return "couple_or_multi_person", "T3"
    if scope.get("mechanism_explanation") is True:
        return "formal_assessment", "T3"
    return "feedback_draft", "T2"


def _normalize_review_case(actor: dict, result: dict) -> dict | None:
    case_id = str(result.get("review_case_id") or "")
    message = result.get("message") if isinstance(result, dict) else None
    if not case_id or not isinstance(message, dict):
        return None

    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM ai_qa_review_cases WHERE id = ?",
            (case_id,),
        ).fetchone()
        if row is None:
            return None
        case = row_to_dict(row)
        if str(case.get("recipient_user_id") or "") != str(actor.get("id") or ""):
            return None
        if str(case.get("message_id") or "") != str(message.get("id") or ""):
            return None

        scope = json_loads(case.get("scope_json"), {})
        existing_scope = dict(scope) if isinstance(scope, dict) else {}
        role = str(actor.get("role") or "")
        involves_minor = role == "student"
        scope.update(
            {
                "object_scope": (
                    "individual_student_support"
                    if involves_minor
                    else "individual_parent_support"
                ),
                "risk_level": _derived_risk(message, existing_scope),
                # A student role is conservatively treated as involving a minor;
                # the current age model only distinguishes under-14 vs 14+, so
                # 14+ cannot be safely equated with legal adulthood.
                "involves_minor": involves_minor,
                "participant_role": role,
                "pre_publication_review_required": True,
            }
        )
        required_task, required_competency = _requirement(scope)
        conn.execute(
            """
            UPDATE ai_qa_review_cases
            SET scope_json = ?, required_task_code = ?, required_competency = ?,
                updated_at = updated_at
            WHERE id = ? AND status = 'pending_review'
            """,
            (json_dumps(scope), required_task, required_competency, case_id),
        )
        write_audit_log(
            conn,
            "ai_qa_participant_review_scope_normalized",
            str(actor["id"]),
            "ai_qa_review_case",
            case_id,
            {
                "participant_role": role,
                "involves_minor": involves_minor,
                "risk_level": scope["risk_level"],
                "required_task_code": required_task,
                "required_competency": required_competency,
                "candidate_delivered_before_review": False,
            },
        )
        conn.commit()
        updated = conn.execute(
            "SELECT * FROM ai_qa_review_cases WHERE id = ?",
            (case_id,),
        ).fetchone()
    return row_to_dict(updated)


def _delivery_view(message: dict, case: dict | None) -> dict:
    item = deepcopy(message)
    if case is None:
        # Fixed/scripted degradation responses are not review candidates and
        # remain immediately visible.
        item["delivery_status"] = "immediate_safe_response"
        return item

    status = str(case.get("status") or "pending_review")
    item["review_status"] = status
    if status == "pending_review":
        item["content"] = PENDING_REVIEW_TEXT
        item["citations"] = []
        item["model"] = {
            "human_verification_required": True,
            "candidate_withheld": True,
        }
        item["delivery_status"] = "pending_human_review"
    elif status in {"adopted", "modified"}:
        item["content"] = str(case.get("final_text") or "")
        item["delivery_status"] = "human_review_approved"
        if isinstance(item.get("model"), dict):
            item["model"]["human_verification_required"] = False
            item["model"]["human_verified"] = True
    elif status in {"rejected", "none_match"}:
        item["content"] = REJECTED_REVIEW_TEXT
        item["citations"] = []
        item["model"] = {"human_verified": True, "candidate_rejected": True}
        item["delivery_status"] = "human_review_rejected"
    else:
        item["content"] = PENDING_REVIEW_TEXT
        item["citations"] = []
        item["model"] = {"candidate_withheld": True}
        item["delivery_status"] = "pending_human_review"
    return item


def send_participant_delivery_message(actor: dict, session_id: str, payload: dict) -> dict:
    result = core_send_message(actor, session_id, payload)
    if str(actor.get("role") or "") not in PARTICIPANT_ROLES:
        return result
    case = _normalize_review_case(actor, result)
    if isinstance(result.get("message"), dict):
        result = dict(result)
        result["message"] = _delivery_view(result["message"], case)
        if case is not None:
            result["route"] = "pending_human_review" if case.get("status") == "pending_review" else result.get("route")
            result["human_escalation"] = True
            result["candidate_withheld"] = case.get("status") == "pending_review"
    return result


def get_participant_delivery_session(actor: dict, session_id: str) -> dict:
    session = core_get_session(actor, session_id)
    if str(actor.get("role") or "") not in PARTICIPANT_ROLES:
        return session

    messages = session.get("messages") if isinstance(session, dict) else None
    if not isinstance(messages, list) or not messages:
        return session

    message_ids = [
        str(item.get("id"))
        for item in messages
        if isinstance(item, dict) and item.get("role") == "assistant" and item.get("id")
    ]
    cases_by_message: dict[str, dict] = {}
    if message_ids:
        placeholders = ",".join("?" for _ in message_ids)
        with get_connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM ai_qa_review_cases WHERE message_id IN ({placeholders})",
                message_ids,
            ).fetchall()
            cases_by_message = {str(row["message_id"]): row_to_dict(row) for row in rows}

    result = dict(session)
    result["messages"] = [
        _delivery_view(item, cases_by_message.get(str(item.get("id"))))
        if isinstance(item, dict) and item.get("role") == "assistant"
        else item
        for item in messages
    ]
    return result
