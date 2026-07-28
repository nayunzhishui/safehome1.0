"""Human review workbench for internal AI answer candidates."""

from __future__ import annotations

import hashlib
import json
import re
from difflib import SequenceMatcher
from typing import Any

from database import (
    get_connection,
    json_dumps,
    json_loads,
    new_id,
    now_iso,
    row_to_dict,
    rows_to_dicts,
    write_audit_log,
)
from services.ai_qa_output_gate_service import (
    BLAME_TERMS,
    CONCLUSION_TERMS,
    DIAGNOSTIC_TERMS,
    GUARANTEE_TERMS,
    RISK_CONCLUSION_TERMS,
)
from services.therapeutic_assessment_competency_service import LEVEL_RANK
from services.therapeutic_assessment_service import FORMAL_ROLES


DECISIONS = {"adopt", "modify", "reject", "none_match"}
STATUS_BY_DECISION = {
    "adopt": "adopted",
    "modify": "modified",
    "reject": "rejected",
    "none_match": "none_match",
}
LANGUAGE_TERMS = (
    *DIAGNOSTIC_TERMS,
    *GUARANTEE_TERMS,
    *BLAME_TERMS,
    *RISK_CONCLUSION_TERMS,
    *CONCLUSION_TERMS,
)


class AiQaReviewError(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        status: int = 400,
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.details = details or {}


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _require_role(actor: dict) -> None:
    if str(actor.get("role") or "") not in FORMAL_ROLES:
        raise AiQaReviewError("forbidden", "仅研究工作角色可访问AI审阅工作台。", 403)


def _requirement(scope: dict) -> tuple[str, str, str]:
    if str(scope.get("risk_level") or "low") == "high":
        return "feedback_review", "T3", "high_risk"
    if scope.get("involves_minor") is True:
        return "minor_or_family", "T3", "minor_or_family"
    if scope.get("multi_party") is True:
        return "couple_or_multi_person", "T3", "couple_or_multi_person"
    if scope.get("mechanism_explanation") is True:
        return "formal_assessment", "T3", "mechanism_explanation"
    return "feedback_draft", "T2", "individual_adult_low_risk"


def _diff(candidate: str, final: str | None) -> dict:
    if final is None:
        return {"changed": False, "similarity": None}
    return {
        "changed": candidate != final,
        "similarity": round(SequenceMatcher(None, candidate, final).ratio(), 4),
    }


def _present(row: dict) -> dict:
    item = dict(row)
    item["citations"] = json_loads(item.pop("citations_json", None), [])
    item["gate_violations"] = json_loads(
        item.pop("gate_violations_json", None),
        [],
    )
    item["scope"] = json_loads(item.pop("scope_json", None), {})
    item["formal_feedback_written"] = bool(
        item.get("formal_feedback_written")
    )
    item["diff"] = _diff(item["candidate_text"], item.get("final_text"))
    return item


def create_review_case(
    conn,
    *,
    message_id: str,
    session_id: str,
    subject_type: str,
    subject_id: str,
    recipient_user_id: str,
    draft_author_id: str,
    candidate_text: str,
    citations: list[dict],
    gate_violations: list[str],
    scope: dict,
    publication_candidate_id: str | None,
) -> dict:
    existing = conn.execute(
        "SELECT * FROM ai_qa_review_cases WHERE message_id = ?",
        (message_id,),
    ).fetchone()
    if existing is not None:
        item = _present(row_to_dict(existing))
        if item["candidate_sha256"] != _sha(candidate_text):
            raise AiQaReviewError(
                "review_case_message_conflict",
                "该AI消息已绑定不同候选内容。",
                409,
            )
        return item
    required_task, required_level, _complexity = _requirement(scope)
    timestamp = now_iso()
    case_id = new_id("aiqrc")
    source_snapshot = [
        {
            key: citation.get(key)
            for key in (
                "content_type",
                "content_id",
                "version_id",
                "content_version",
                "release_id",
                "payload_hash",
                "source_ref",
                "source_version",
            )
        }
        for citation in citations
    ]
    conn.execute(
        """
        INSERT INTO ai_qa_review_cases (
            id, message_id, session_id, subject_type, subject_id,
            recipient_user_id, draft_author_id, publication_candidate_id,
            candidate_text, candidate_sha256, citations_json,
            gate_violations_json, scope_json, source_snapshot_hash,
            required_task_code, required_competency, status,
            formal_feedback_written, version, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            'pending_review', 0, 1, ?, ?)
        """,
        (
            case_id,
            message_id,
            session_id,
            subject_type,
            subject_id,
            recipient_user_id,
            draft_author_id,
            publication_candidate_id,
            candidate_text,
            _sha(candidate_text),
            json_dumps(citations),
            json_dumps(gate_violations),
            json_dumps(scope),
            _sha(source_snapshot),
            required_task,
            required_level,
            timestamp,
            timestamp,
        ),
    )
    row = conn.execute(
        "SELECT * FROM ai_qa_review_cases WHERE id = ?",
        (case_id,),
    ).fetchone()
    return _present(row_to_dict(row))


def list_review_cases(actor: dict, params: dict) -> dict:
    _require_role(actor)
    status = str(params.get("status") or "").strip()
    task_code = str(params.get("required_task_code") or "").strip()
    clauses: list[str] = []
    values: list[str] = []
    if status:
        clauses.append("status = ?")
        values.append(status)
    if task_code:
        clauses.append("required_task_code = ?")
        values.append(task_code)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM ai_qa_review_cases
            {where}
            ORDER BY updated_at DESC
            LIMIT 200
            """,  # nosec B608: where is assembled only from fixed clauses
            values,
        ).fetchall()
        write_audit_log(
            conn,
            "ai_qa_review_cases_viewed",
            str(actor["id"]),
            "ai_qa_review_case",
            "list",
            {"status": status or None, "required_task_code": task_code or None},
        )
        conn.commit()
    return {"items": [_present(item) for item in rows_to_dicts(rows)]}


def get_review_case(actor: dict, case_id: str) -> dict:
    _require_role(actor)
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM ai_qa_review_cases WHERE id = ?",
            (case_id,),
        ).fetchone()
        if row is None:
            raise AiQaReviewError("not_found", "AI审阅任务不存在。", 404)
        write_audit_log(
            conn,
            "ai_qa_review_case_viewed",
            str(actor["id"]),
            "ai_qa_review_case",
            case_id,
            {"candidate_text_logged": False},
        )
        conn.commit()
    return _present(row_to_dict(row))


def _has_authorization(conn, actor_id: str, case: dict) -> bool:
    rows = conn.execute(
        """
        SELECT competency_level, scope_json
        FROM therapeutic_assessment_authorizations
        WHERE user_id = ? AND task_code = ? AND status = 'active'
          AND starts_at <= ? AND expires_at > ?
        """,
        (
            actor_id,
            case["required_task_code"],
            now_iso(),
            now_iso(),
        ),
    ).fetchall()
    _task, _level, required_complexity = _requirement(case["scope"])
    for row in rows:
        level = str(row["competency_level"])
        scope = json_loads(row["scope_json"], {})
        complexities = set(scope.get("complexity_scopes") or [])
        if (
            LEVEL_RANK.get(level, 0)
            >= LEVEL_RANK.get(case["required_competency"], 99)
            and required_complexity in complexities
        ):
            return True
    return False


def _validate_final_text(final_text: str, citations: list[dict]) -> None:
    if not final_text or len(final_text) > 3000:
        raise AiQaReviewError(
            "review_final_text_invalid",
            "修改后的候选内容必须为1至3000字。",
            422,
        )
    if any(term.lower() in final_text.lower() for term in LANGUAGE_TERMS):
        raise AiQaReviewError(
            "review_language_boundary_failed",
            "修改后的候选内容未通过非诊断语言边界。",
            422,
        )
    refs = {int(value) for value in re.findall(r"\[S(\d+)\]", final_text)}
    if not refs or any(index < 1 or index > len(citations) for index in refs):
        raise AiQaReviewError(
            "review_source_reference_invalid",
            "修改后的候选内容必须引用当前已批准来源。",
            422,
        )


def decide_review_case(
    actor: dict,
    case_id: str,
    payload: dict,
    idempotency_key: str,
) -> dict:
    _require_role(actor)
    allowed_fields = {"decision", "expected_version", "final_text", "rationale"}
    unknown = sorted(set(payload) - allowed_fields)
    if unknown:
        raise AiQaReviewError(
            "review_payload_fields_invalid",
            "审阅请求包含不允许的字段。",
            422,
            {"fields": unknown},
        )
    key = str(idempotency_key or "").strip()[:128]
    if not key:
        raise AiQaReviewError(
            "idempotency_key_required",
            "审阅决定需要Idempotency-Key。",
            422,
        )
    decision = str(payload.get("decision") or "").strip()
    expected = payload.get("expected_version")
    rationale = str(payload.get("rationale") or "").strip()
    final_text = str(payload.get("final_text") or "").strip() or None
    if decision not in DECISIONS or not isinstance(expected, int):
        raise AiQaReviewError(
            "review_decision_invalid",
            "审阅决定或expected_version无效。",
            422,
        )
    if decision in {"modify", "reject", "none_match"} and not rationale:
        raise AiQaReviewError(
            "review_rationale_required",
            "修改、拒绝或无匹配时必须填写理由。",
            422,
        )
    request_hash = _sha(
        {
            "case_id": case_id,
            "decision": decision,
            "expected_version": expected,
            "final_text": final_text,
            "rationale": rationale,
        }
    )
    with get_connection() as conn:
        replay = conn.execute(
            """
            SELECT request_sha256, review_case_id
            FROM ai_qa_review_actions
            WHERE actor_id = ? AND idempotency_key = ?
            """,
            (str(actor["id"]), key),
        ).fetchone()
        if replay is not None:
            if (
                str(replay["request_sha256"]) != request_hash
                or str(replay["review_case_id"]) != case_id
            ):
                raise AiQaReviewError(
                    "review_idempotency_conflict",
                    "该幂等键已用于其他审阅请求。",
                    409,
                )
            row = conn.execute(
                "SELECT * FROM ai_qa_review_cases WHERE id = ?",
                (case_id,),
            ).fetchone()
            return _present(row_to_dict(row))
        row = conn.execute(
            "SELECT * FROM ai_qa_review_cases WHERE id = ?",
            (case_id,),
        ).fetchone()
        if row is None:
            raise AiQaReviewError("not_found", "AI审阅任务不存在。", 404)
        case = _present(row_to_dict(row))
        if int(case["version"]) != expected:
            raise AiQaReviewError(
                "review_version_conflict",
                "AI候选已变化，请重新读取。",
                409,
            )
        if case["status"] != "pending_review":
            raise AiQaReviewError(
                "review_state_conflict",
                "该AI候选已完成审阅。",
                409,
            )
        if str(case["draft_author_id"]) == str(actor["id"]):
            raise AiQaReviewError(
                "reviewer_separation_required",
                "起草人与审阅人必须分离。",
                409,
            )
        if not _has_authorization(conn, str(actor["id"]), case):
            raise AiQaReviewError(
                "review_authorization_required",
                "当前账号缺少该对象范围的有效任务授权。",
                403,
                {
                    "required_task_code": case["required_task_code"],
                    "required_competency": case["required_competency"],
                },
            )
        if decision == "adopt":
            resolved_text = case["candidate_text"]
        elif decision == "modify":
            resolved_text = final_text
            _validate_final_text(resolved_text or "", case["citations"])
            if resolved_text == case["candidate_text"]:
                raise AiQaReviewError(
                    "review_modification_required",
                    "选择修改时，内容必须与原候选不同。",
                    422,
                )
        else:
            resolved_text = None
        timestamp = now_iso()
        status = STATUS_BY_DECISION[decision]
        cursor = conn.execute(
            """
            UPDATE ai_qa_review_cases
            SET status = ?, final_text = ?, final_sha256 = ?, reviewed_by = ?,
                reviewed_at = ?, version = version + 1, updated_at = ?
            WHERE id = ? AND version = ? AND status = 'pending_review'
            """,
            (
                status,
                resolved_text,
                _sha(resolved_text) if resolved_text else None,
                str(actor["id"]),
                timestamp,
                timestamp,
                case_id,
                expected,
            ),
        )
        if cursor.rowcount != 1:
            raise AiQaReviewError(
                "review_version_conflict",
                "AI候选已变化，请重新读取。",
                409,
            )
        diff = _diff(case["candidate_text"], resolved_text)
        conn.execute(
            """
            INSERT INTO ai_qa_review_actions (
                id, review_case_id, actor_id, decision, before_version,
                after_version, candidate_sha256, final_sha256, diff_json,
                rationale, request_sha256, idempotency_key, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id("aiqra"),
                case_id,
                str(actor["id"]),
                decision,
                expected,
                expected + 1,
                case["candidate_sha256"],
                _sha(resolved_text) if resolved_text else None,
                json_dumps(diff),
                rationale,
                request_hash,
                key,
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "ai_qa_review_decided",
            str(actor["id"]),
            "ai_qa_review_case",
            case_id,
            {
                "decision": decision,
                "before_version": expected,
                "after_version": expected + 1,
                "formal_feedback_written": False,
                "candidate_text_logged": False,
            },
        )
        conn.commit()
        result = conn.execute(
            "SELECT * FROM ai_qa_review_cases WHERE id = ?",
            (case_id,),
        ).fetchone()
    return _present(row_to_dict(result))
