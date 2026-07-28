"""Five-gate, human-decision-only AI assistance for Task38-F16."""

from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path

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
from services.therapeutic_assessment_service import (
    TherapeuticAssessmentError,
    _assert_researcher,
    _case_row,
    _event,
    _idempotency,
)


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "content" / "therapeutic_assessment_ai_assist_policy.json"
SOURCE_FIELDS = {"assessment_question", "working_question"}
DECISIONS = {"accepted", "modified", "rejected", "none_fit"}
BLOCKED_LANGUAGE = {
    "诊断",
    "患有",
    "人格障碍",
    "一定是",
    "肯定会",
    "治疗有效",
    "你应该",
}


@lru_cache(maxsize=1)
def policy() -> dict:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if (
        payload.get("schema") != "safehome.therapeutic-assessment.ai-assist.v1"
        or payload.get("auto_publish") is not False
        or payload.get("may_clear_safety_signal") is not False
        or payload.get("may_claim_human_review") is not False
    ):
        raise RuntimeError("治疗性评估AI辅助政策无效")
    return payload


def public_policy() -> dict:
    payload = policy()
    return {
        key: payload[key]
        for key in (
            "schema",
            "version",
            "allowed_tasks",
            "human_only_tasks",
            "five_gates",
            "auto_publish",
            "may_clear_safety_signal",
            "may_create_hypothesis_h",
            "may_claim_human_review",
            "provider_mode",
            "grounding_note",
            "boundary_notice",
        )
    }


def _source_text(case: dict, source_field: str) -> str:
    if source_field not in SOURCE_FIELDS:
        raise TherapeuticAssessmentError(
            "source_not_allowed",
            "AI候选只能使用当前记录中已授权的问题原话。",
            422,
        )
    text = str(case.get(source_field) or "").strip()
    if not text:
        raise TherapeuticAssessmentError("minimum_input_missing", "当前字段没有可整理的原话。", 422)
    if len(text) > 1200:
        raise TherapeuticAssessmentError("minimum_input_exceeded", "输入超过最小必要范围。", 422)
    return text


def _assert_case_scope(case: dict) -> None:
    required = policy()["allowed_case_scope"]
    actual = {
        "risk_level": str(case.get("risk_level") or ""),
        "safety_state": str(case.get("safety_state") or ""),
        "complexity_scope": str(case.get("complexity_scope") or ""),
    }
    if actual != required:
        raise TherapeuticAssessmentError(
            "ai_assist_scope_blocked",
            "该记录需要真人专属处理，AI候选已按默认拒绝。",
            409,
            {"required_scope": required, "actual_scope": actual},
        )


def _normalize_formatting(text: str) -> str:
    value = re.sub(r"[ \t]+", " ", text)
    value = re.sub(r"\n{3,}", "\n\n", value).strip()
    if value and value[-1] not in "。！？?":
        value += "。"
    return value


def _candidate_payload(task_type: str, text: str, case: dict) -> list[dict]:
    if task_type == "formatting":
        return [
            {"text": _normalize_formatting(text), "kind": "format_only"},
            {"text": text.strip(), "kind": "keep_original"},
        ]
    if task_type == "deidentification_reminder":
        signals = []
        if re.search(r"\b1[3-9]\d{9}\b", text):
            signals.append("可能包含手机号")
        if re.search(r"[\w.+-]+@[\w.-]+\.\w+", text):
            signals.append("可能包含邮箱")
        if re.search(r"\b\d{15,18}[0-9Xx]\b", text):
            signals.append("可能包含证件号")
        return [
            {
                "text": "；".join(signals) if signals else "未发现常见直接标识符，仍需人工逐字核对。",
                "kind": "reminder_only",
            }
        ]
    if task_type == "timeline_sort":
        fragments = [item.strip() for item in re.split(r"[。；\n]+", text) if item.strip()]
        return [
            {"text": " → ".join(fragments), "kind": "source_order"},
            {"text": text, "kind": "keep_original"},
        ]
    if task_type == "question_candidates":
        return [
            {
                "text": "在这次经历里，你最希望我们先共同理解哪一个片段？",
                "kind": "focus",
            },
            {
                "text": "停下来前后，你分别注意到了哪些想法、感受或行动？",
                "kind": "sequence",
            },
        ]
    if task_type == "missing_field_prompt":
        missing = [
            label
            for field, label in (
                ("working_question", "尚未共同确认工作问题"),
                ("assigned_researcher_id", "尚未分配研究者"),
            )
            if not str(case.get(field) or "").strip()
        ]
        return [
            {
                "text": "；".join(missing) if missing else "当前基础字段未发现空缺，仍需人工核对。",
                "kind": "missing_field_prompt",
            }
        ]
    return [
        {
            "text": "回看这次经历，哪些部分与你的体验相符，哪些部分需要修改？",
            "kind": "review",
        },
        {
            "text": "如果只选择一个低压力、可退出的小步骤，你愿意先尝试什么？",
            "kind": "next_step",
        },
    ]


def _five_gate_results(actor: dict, case: dict, source_field: str, text: str, candidates: list[dict]) -> dict:
    language_ok = not any(
        blocked in str(item.get("text") or "")
        for item in candidates
        for blocked in BLOCKED_LANGUAGE
    )
    results = {
        "minimum_input": bool(text) and len(text) <= 1200,
        "permission": str(actor.get("role") or "") in set(policy()["enabled_roles"]),
        "source": source_field in SOURCE_FIELDS
        and (
            ("question" if source_field in {"assessment_question", "working_question"} else source_field)
            in set(json_loads(case.get("shared_scope_json"), []))
        ),
        "language": language_ok,
        "responsibility": policy()["auto_publish"] is False,
    }
    if not all(results.values()):
        raise TherapeuticAssessmentError(
            "ai_assist_gate_blocked",
            "AI候选未通过全部五道门，已保留原话并停止。",
            409,
            {"five_gate_results": results},
        )
    return results


def _present(item: dict, case: dict) -> dict:
    result = dict(item)
    result["candidates"] = json_loads(result.pop("candidate_payload_json", None), [])
    result["five_gate_results"] = json_loads(result.pop("five_gate_results_json", None), {})
    result["original_text"] = str(case.get(result["source_field"]) or "")
    result["auto_publish"] = False
    result["may_clear_safety_signal"] = False
    result["human_review_completed"] = False
    result["boundary_notice"] = policy()["boundary_notice"]
    return result


def create_candidates(
    actor: dict,
    case_id: str,
    payload: dict,
    idempotency_key: str,
) -> tuple[dict, int]:
    key = _idempotency(idempotency_key)
    task_type = str(payload.get("task_type") or "")
    if task_type in set(policy()["human_only_tasks"]):
        raise TherapeuticAssessmentError(
            "human_only_task",
            "该任务属于真人专属范围，AI不能生成候选。",
            409,
        )
    if task_type not in set(policy()["allowed_tasks"]):
        raise TherapeuticAssessmentError("validation_error", "不支持的AI辅助任务。", 422)
    source_field = str(payload.get("source_field") or "")
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        _assert_researcher(actor, case)
        existing = conn.execute(
            "SELECT * FROM therapeutic_assessment_ai_assist_candidates "
            "WHERE created_by = ? AND idempotency_key = ?",
            (str(actor["id"]), key),
        ).fetchone()
        if existing:
            return _present(row_to_dict(existing), case), 200
        expected = int(payload.get("expected_case_version") or 0)
        if expected != int(case["version"]):
            raise TherapeuticAssessmentError("version_conflict", "记录已更新，请刷新后重试。", 409)
        _assert_case_scope(case)
        text = _source_text(case, source_field)
        candidates = _candidate_payload(task_type, text, case)
        gate_results = _five_gate_results(actor, case, source_field, text, candidates)
        timestamp = now_iso()
        candidate_id = new_id("ta_ai_candidate")
        conn.execute(
            """INSERT INTO therapeutic_assessment_ai_assist_candidates
            (id, case_id, task_type, source_field, original_text_sha256,
             candidate_payload_json, five_gate_results_json, provider_mode,
             status, version, created_by, idempotency_key, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending_human_decision', 1, ?, ?, ?, ?)""",
            (
                candidate_id,
                case_id,
                task_type,
                source_field,
                hashlib.sha256(text.encode("utf-8")).hexdigest(),
                json_dumps(candidates),
                json_dumps(gate_results),
                policy()["provider_mode"],
                str(actor["id"]),
                key,
                timestamp,
                timestamp,
            ),
        )
        _event(
            conn,
            case_id,
            actor,
            "ai_assist_candidates_created",
            key,
            int(case["version"]),
            int(case["version"]),
            {
                "candidate_id": candidate_id,
                "task_type": task_type,
                "five_gate_results": gate_results,
                "auto_publish": False,
            },
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_ai_assist_candidates_created",
            str(actor["id"]),
            "therapeutic_assessment_case",
            case_id,
            {
                "candidate_id": candidate_id,
                "task_type": task_type,
                "original_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "auto_publish": False,
            },
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM therapeutic_assessment_ai_assist_candidates WHERE id = ?",
            (candidate_id,),
        ).fetchone()
    return _present(row_to_dict(row), case), 201


def list_candidates(actor: dict, case_id: str) -> dict:
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        _assert_researcher(actor, case)
        rows = rows_to_dicts(
            conn.execute(
                "SELECT * FROM therapeutic_assessment_ai_assist_candidates "
                "WHERE case_id = ? ORDER BY created_at DESC",
                (case_id,),
            ).fetchall()
        )
    return {"items": [_present(item, case) for item in rows], "count": len(rows)}


def decide_candidate(
    actor: dict,
    candidate_id: str,
    payload: dict,
    idempotency_key: str,
) -> dict:
    key = _idempotency(idempotency_key)
    decision = str(payload.get("decision") or "")
    if decision not in DECISIONS:
        raise TherapeuticAssessmentError("validation_error", "不支持的人工决定。", 422)
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM therapeutic_assessment_ai_assist_candidates WHERE id = ?",
            (candidate_id,),
        ).fetchone()
        if row is None:
            raise TherapeuticAssessmentError("not_found", "没有找到该AI候选。", 404)
        item = row_to_dict(row)
        case = _case_row(conn, item["case_id"])
        _assert_researcher(actor, case)
        replay = conn.execute(
            "SELECT * FROM therapeutic_assessment_events WHERE actor_id = ? AND idempotency_key = ?",
            (str(actor["id"]), key),
        ).fetchone()
        if replay:
            return _present(item, case)
        expected = int(payload.get("expected_version") or 0)
        if expected != int(item["version"]):
            raise TherapeuticAssessmentError("version_conflict", "候选已更新，请刷新后重试。", 409)
        selected_index = payload.get("selected_candidate_index")
        candidates = json_loads(item["candidate_payload_json"], [])
        if decision in {"accepted", "modified"}:
            if not isinstance(selected_index, int) or selected_index < 0 or selected_index >= len(candidates):
                raise TherapeuticAssessmentError("validation_error", "请选择一个候选。", 422)
        reviewer_text = ""
        if decision == "accepted":
            reviewer_text = str(candidates[selected_index]["text"])
        elif decision == "modified":
            reviewer_text = str(payload.get("modified_text") or "").strip()
            if not reviewer_text or len(reviewer_text) > 1500:
                raise TherapeuticAssessmentError("validation_error", "修改内容不能为空且不能超过1500字。", 422)
            if any(value in reviewer_text for value in BLOCKED_LANGUAGE):
                raise TherapeuticAssessmentError("language_blocked", "修改内容包含诊断或保证式表达。", 422)
        timestamp = now_iso()
        next_version = int(item["version"]) + 1
        conn.execute(
            """UPDATE therapeutic_assessment_ai_assist_candidates
            SET status = ?, selected_candidate_index = ?, reviewer_text = ?,
                reviewed_by = ?, version = ?, updated_at = ?
            WHERE id = ?""",
            (
                decision,
                selected_index if isinstance(selected_index, int) else None,
                reviewer_text or None,
                str(actor["id"]),
                next_version,
                timestamp,
                candidate_id,
            ),
        )
        _event(
            conn,
            case["id"],
            actor,
            "ai_assist_candidate_decided",
            key,
            int(item["version"]),
            next_version,
            {
                "candidate_id": candidate_id,
                "decision": decision,
                "auto_publish": False,
                "human_review_completed": False,
            },
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_ai_assist_candidate_decided",
            str(actor["id"]),
            "therapeutic_assessment_ai_candidate",
            candidate_id,
            {"decision": decision, "auto_publish": False},
        )
        conn.commit()
        updated = row_to_dict(
            conn.execute(
                "SELECT * FROM therapeutic_assessment_ai_assist_candidates WHERE id = ?",
                (candidate_id,),
            ).fetchone()
        )
    return _present(updated, case)
