"""Participant-owned question wording, candidates and quality rubric."""

from __future__ import annotations

from database import get_connection, json_dumps, now_iso, write_audit_log
from services.therapeutic_assessment_service import (
    TherapeuticAssessmentError,
    _assert_participant,
    _case_row,
    _idempotency,
    _present_case,
    _event,
)


ACTIONS = {"generate_candidates", "revise", "select_candidate", "none_fit", "pause", "delete", "submit"}
BEST_GUESS_NOTICE = "最好猜测不是结论，可以随新资料修订或删除。"


def _quality(question: str) -> dict:
    text = question.strip()
    blame_terms = ("都是你", "都怪", "就是他", "就是她", "我太差", "我没用")
    absolute_terms = ("一定", "肯定", "永远", "从来都")
    return {
        "personal_concern": bool(text),
        "explorable": any(term in text for term in ("想", "理解", "探索", "观察", "发生")),
        "non_blame": not any(term in text for term in blame_terms),
        "evidence_responsive": len(text) >= 8,
        "allows_uncertainty": any(term in text for term in ("可能", "也许", "不确定", "暂时")) or not any(term in text for term in absolute_terms),
    }


def update_question(actor: dict, case_id: str, payload: dict, idempotency_key: str) -> dict:
    key = _idempotency(idempotency_key)
    action = str(payload.get("action") or "")
    expected = payload.get("expected_version")
    if action not in ACTIONS or not isinstance(expected, int):
        raise TherapeuticAssessmentError("validation_error", "需要有效action和expected_version。")
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        _assert_participant(actor, case)
        existing = conn.execute(
            "SELECT action FROM therapeutic_assessment_events WHERE actor_id = ? AND idempotency_key = ?",
            (str(actor["id"]), key),
        ).fetchone()
        if existing is not None:
            if str(existing["action"]) != f"question:{action}":
                raise TherapeuticAssessmentError("idempotency_conflict", "该提交标识已用于其它操作。", 409)
            return _present_case(conn, case, actor)
        before = int(case["version"])
        if expected != before:
            raise TherapeuticAssessmentError("version_conflict", "记录已更新，请刷新后重试。", 409)

        working = str(case.get("working_question") or case["assessment_question"])
        candidates = []
        candidate_decision = str(case.get("candidate_decision") or "unreviewed")
        status = str(case.get("question_status") or "submitted")
        best_guess = str(case.get("best_guess") or "")
        if action == "generate_candidates":
            candidates = [
                {"id": "candidate-1", "text": "在这次具体情境里，我最想理解自己什么？", "source": "system_prompt"},
                {"id": "candidate-2", "text": "我想先观察哪些变化、例外或可尝试的小一步？", "source": "system_prompt"},
            ]
            candidate_decision = "unreviewed"
        elif action == "revise":
            working = str(payload.get("working_question") or "").strip()
            if not working or len(working) > 1000:
                raise TherapeuticAssessmentError("validation_error", "改写问题不能为空且不能超过1000字。")
            best_guess = str(payload.get("best_guess") or "").strip()[:1000]
            status = "draft"
            candidate_decision = "participant_revised"
        elif action == "select_candidate":
            candidate_id = str(payload.get("candidate_id") or "")
            saved = __import__("json").loads(str(case.get("question_candidates_json") or "[]"))
            selected = next((item for item in saved if item.get("id") == candidate_id), None)
            if selected is None:
                raise TherapeuticAssessmentError("validation_error", "没有找到所选候选。")
            working = str(selected["text"])
            candidates = saved
            candidate_decision = candidate_id
            status = "draft"
        elif action == "none_fit":
            candidates = __import__("json").loads(str(case.get("question_candidates_json") or "[]"))
            candidate_decision = "none_fit"
        elif action == "pause":
            status = "paused"
        elif action == "delete":
            working = ""
            best_guess = ""
            candidates = []
            candidate_decision = "deleted"
            status = "deleted"
        elif action == "submit":
            proposed = str(payload.get("working_question") or working).strip()
            if status == "submitted" and proposed == working:
                raise TherapeuticAssessmentError("no_explicit_change", "未修改或未作明确选择不算确认。", 409)
            if not proposed:
                raise TherapeuticAssessmentError("validation_error", "提交问题不能为空。")
            working = proposed
            status = "submitted"

        if action not in {"generate_candidates", "select_candidate", "none_fit", "delete"}:
            candidates = __import__("json").loads(str(case.get("question_candidates_json") or "[]"))
        quality = _quality(working) if working else {}
        timestamp = now_iso()
        cursor = conn.execute(
            """
            UPDATE therapeutic_assessment_cases
            SET working_question = ?, question_candidates_json = ?, question_quality_json = ?,
                best_guess = ?, question_status = ?, candidate_decision = ?,
                question_version = question_version + 1, version = version + 1, updated_at = ?
            WHERE id = ? AND version = ?
            """,
            (
                working, json_dumps(candidates), json_dumps(quality), best_guess, status,
                candidate_decision, timestamp, case_id, before,
            ),
        )
        if cursor.rowcount != 1:
            raise TherapeuticAssessmentError("version_conflict", "记录已更新，请刷新后重试。", 409)
        _event(
            conn, case_id, actor, f"question:{action}", key, before, before + 1,
            {"question_status": status, "candidate_decision": candidate_decision, "best_guess_present": bool(best_guess)},
        )
        write_audit_log(
            conn, "therapeutic_assessment_question_updated", str(actor["id"]),
            "therapeutic_assessment_case", case_id,
            {"action": action, "before_version": before, "after_version": before + 1},
        )
        conn.commit()
        result = _present_case(conn, _case_row(conn, case_id), actor)
        result["best_guess_notice"] = BEST_GUESS_NOTICE
        return result
