"""O/P/H/U evidence ledger with human-only hypothesis controls."""

from __future__ import annotations

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
    REVIEW_ROLES,
    TherapeuticAssessmentError,
    _assert_participant,
    _assert_read,
    _assert_researcher,
    _case_row,
    _idempotency,
)


KINDS = {"O", "P", "H", "U"}
ORIGINS = {"human", "ai", "system"}
UNCERTAINTY_TYPES = {"missing", "conflict", "permission_denied", "unconfirmed"}
RECOGNITION = {"unconfirmed", "recognized", "partly_recognized", "not_recognized"}
JSON_FIELDS = (
    "visibility_scope",
    "exceptions",
    "supporting_evidence",
    "counter_evidence",
    "alternative_explanations",
    "falsification_criteria",
)


def _text(payload: dict, name: str, limit: int = 2000, required: bool = True) -> str:
    value = str(payload.get(name) or "").strip()
    if required and not value:
        raise TherapeuticAssessmentError("validation_error", f"{name}不能为空。")
    if len(value) > limit:
        raise TherapeuticAssessmentError("validation_error", f"{name}不能超过{limit}字。")
    return value


def _list(payload: dict, name: str, required: bool = False) -> list:
    value = payload.get(name, [])
    if not isinstance(value, list) or (required and not value):
        raise TherapeuticAssessmentError("validation_error", f"{name}必须是非空列表。" if required else f"{name}必须是列表。")
    if len(value) > 50:
        raise TherapeuticAssessmentError("validation_error", f"{name}条目过多。")
    return value


def _validate(actor: dict, payload: dict) -> dict:
    kind = str(payload.get("kind") or "").upper()
    if kind not in KINDS:
        raise TherapeuticAssessmentError("validation_error", "kind必须为O、P、H或U。")
    origin = str(payload.get("source_origin") or "human")
    if origin not in ORIGINS:
        raise TherapeuticAssessmentError("validation_error", "不支持的证据来源类型。")
    role = str(actor.get("role") or "")
    if role in {"parent", "student"} and kind not in {"O", "U"}:
        raise TherapeuticAssessmentError("forbidden", "参与者可以补充观察或未知项，模式和假设由人工共同整理。", 403)
    if role not in {"parent", "student"}:
        if role not in {"researcher", "supervisor", "admin"}:
            raise TherapeuticAssessmentError("forbidden", "当前角色不能写入证据账本。", 403)
    if kind == "H" and origin != "human":
        raise TherapeuticAssessmentError("human_hypothesis_required", "AI或系统不能创建或升级人工假设。", 409)

    content = _text(payload, "content")
    visibility = _list(payload, "visibility_scope", True)
    if not set(visibility).issubset({"participant", "research_team", "supervisor"}):
        raise TherapeuticAssessmentError("validation_error", "visibility_scope包含未知范围。")
    normalized = {
        "kind": kind,
        "content": content,
        "source_origin": origin,
        "source_ref": _text(payload, "source_ref", 500, False),
        "provider_id": _text(payload, "provider_id", 128, False),
        "observed_at": _text(payload, "observed_at", 64, False),
        "context": _text(payload, "context", 1000, False),
        "method_limitations": _text(payload, "method_limitations", 1000, False)
        or "仅适用于当前已授权资料与时间范围，不代表完整解释或诊断结论。",
        "visibility_scope": visibility,
        "applicability_scope": _text(payload, "applicability_scope", 1000, False),
        "question_link": _text(payload, "question_link", 500, False),
        "exceptions": _list(payload, "exceptions"),
        "time_window": _text(payload, "time_window", 200, False),
        "supporting_evidence": _list(payload, "supporting_evidence"),
        "counter_evidence": _list(payload, "counter_evidence"),
        "alternative_explanations": _list(payload, "alternative_explanations"),
        "falsification_criteria": _list(payload, "falsification_criteria"),
        "protective_function": _text(payload, "protective_function", 1000, False),
        "cost": _text(payload, "cost", 1000, False),
        "participant_recognition": str(payload.get("participant_recognition") or ""),
        "uncertainty_type": str(payload.get("uncertainty_type") or ""),
    }
    if kind == "O" and not all(normalized[name] for name in ("source_ref", "provider_id", "observed_at", "context")):
        raise TherapeuticAssessmentError("validation_error", "观察必须包含来源、提供者、时间和情境。")
    if kind == "P":
        if not normalized["applicability_scope"] or not normalized["time_window"] or not normalized["exceptions"]:
            raise TherapeuticAssessmentError("validation_error", "模式候选必须说明适用范围、例外和时间窗。")
        refs = {
            str(item.get("ref") or "")
            for item in normalized["supporting_evidence"]
            if isinstance(item, dict) and item.get("ref")
        }
        if len(refs) < 2:
            raise TherapeuticAssessmentError("validation_error", "模式候选至少需要两个不同事件或来源。")
    if kind == "H":
        required_texts = ("protective_function", "cost")
        required_lists = ("supporting_evidence", "counter_evidence", "alternative_explanations", "falsification_criteria")
        if not normalized["question_link"] or not all(normalized[name] for name in required_texts):
            raise TherapeuticAssessmentError("validation_error", "人工假设必须关联问题并说明保护功能和代价。")
        if not all(normalized[name] for name in required_lists):
            raise TherapeuticAssessmentError("validation_error", "人工假设必须包含依据、反证、替代解释和推翻条件。")
        if normalized["participant_recognition"] not in RECOGNITION:
            raise TherapeuticAssessmentError("validation_error", "参与者识别状态无效。")
    if kind == "U" and normalized["uncertainty_type"] not in UNCERTAINTY_TYPES:
        raise TherapeuticAssessmentError("validation_error", "未知项必须说明缺失、冲突、权限不足或未确认。")
    return normalized


def _present(row: dict) -> dict:
    item = dict(row)
    for field in JSON_FIELDS:
        item[field] = json_loads(item.pop(f"{field}_json", None), [])
    return item


def create_evidence(actor: dict, case_id: str, payload: dict, idempotency_key: str) -> tuple[dict, int]:
    key = _idempotency(idempotency_key)
    data = _validate(actor, payload)
    timestamp = now_iso()
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        if str(actor.get("role") or "") in {"parent", "student"}:
            _assert_participant(actor, case)
        else:
            _assert_researcher(actor, case)
            from services.therapeutic_assessment_competency_service import (
                assert_task_authorized,
            )

            task_code = {
                "O": "evidence_organize",
                "U": "evidence_organize",
                "P": "evidence_pattern",
                "H": "formal_assessment",
            }[data["kind"]]
            assert_task_authorized(conn, actor, case, task_code)
        existing = conn.execute(
            "SELECT * FROM therapeutic_assessment_evidence_items WHERE author_id = ? AND idempotency_key = ?",
            (str(actor["id"]), key),
        ).fetchone()
        if existing is not None:
            if str(existing["case_id"]) != case_id:
                raise TherapeuticAssessmentError("idempotency_conflict", "该提交标识已用于其它记录。", 409)
            return _present(row_to_dict(existing)), 200
        item_id = new_id("ta_evidence")
        review_status = "draft" if data["kind"] == "H" else "candidate" if data["kind"] == "P" else "recorded"
        conn.execute(
            """
            INSERT INTO therapeutic_assessment_evidence_items (
                id, case_id, kind, content, source_origin, source_ref, provider_id,
                observed_at, context, method_limitations, visibility_scope_json, applicability_scope,
                question_link, exceptions_json, time_window, supporting_evidence_json,
                counter_evidence_json, alternative_explanations_json,
                falsification_criteria_json, protective_function, cost,
                participant_recognition, uncertainty_type, author_id, review_status,
                version, idempotency_key, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
            """,
            (
                item_id, case_id, data["kind"], data["content"], data["source_origin"],
                data["source_ref"], data["provider_id"], data["observed_at"], data["context"],
                data["method_limitations"], json_dumps(data["visibility_scope"]), data["applicability_scope"],
                data["question_link"], json_dumps(data["exceptions"]), data["time_window"],
                json_dumps(data["supporting_evidence"]), json_dumps(data["counter_evidence"]),
                json_dumps(data["alternative_explanations"]), json_dumps(data["falsification_criteria"]),
                data["protective_function"], data["cost"], data["participant_recognition"],
                data["uncertainty_type"], str(actor["id"]), review_status, key, timestamp, timestamp,
            ),
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_evidence_created",
            str(actor["id"]),
            "therapeutic_assessment_case",
            case_id,
            {"evidence_id": item_id, "kind": data["kind"], "source_origin": data["source_origin"]},
        )
        conn.commit()
        row = conn.execute("SELECT * FROM therapeutic_assessment_evidence_items WHERE id = ?", (item_id,)).fetchone()
        return _present(row_to_dict(row)), 201


def create_action_followup(
    actor: dict,
    action_id: str,
    payload: dict,
    idempotency_key: str,
) -> tuple[dict, int]:
    """将一次行动后的新观察或未知项写回证据账本。"""
    kind = str(payload.get("kind") or "O").upper()
    if kind not in {"O", "U"}:
        raise TherapeuticAssessmentError(
            "validation_error",
            "行动随访只记录新的观察或仍待了解的部分。",
            422,
        )
    with get_connection() as conn:
        action = conn.execute(
            "SELECT * FROM therapeutic_assessment_actions WHERE id = ?",
            (action_id,),
        ).fetchone()
        if action is None:
            raise TherapeuticAssessmentError("not_found", "没有找到该行动记录。", 404)
        action_item = row_to_dict(action)
        case = _case_row(conn, str(action_item["case_id"]))
        if str(actor.get("role") or "") in {"parent", "student"}:
            _assert_participant(actor, case)
            if str(action_item["participant_user_id"]) != str(actor["id"]):
                raise TherapeuticAssessmentError("forbidden", "只能随访自己的行动记录。", 403)
        else:
            _assert_researcher(actor, case)

    evidence_payload = dict(payload)
    evidence_payload.update(
        {
            "kind": kind,
            "source_origin": "human",
            "source_ref": f"therapeutic-action:{action_id}",
            "provider_id": str(actor["id"]),
            "context": str(payload.get("context") or "参与者对一次自选小行动的后续记录"),
            "visibility_scope": payload.get("visibility_scope")
            or ["participant", "research_team"],
            "method_limitations": str(
                payload.get("method_limitations")
                or "这是一次行动后的新线索；是否完成、完成次数或主观变化均不代表疗效。"
            ),
        }
    )
    if kind == "U" and not evidence_payload.get("uncertainty_type"):
        evidence_payload["uncertainty_type"] = "unconfirmed"
    return create_evidence(actor, str(action_item["case_id"]), evidence_payload, idempotency_key)


def list_evidence(actor: dict, case_id: str) -> dict:
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        _assert_read(actor, case)
        rows = rows_to_dicts(
            conn.execute(
                "SELECT * FROM therapeutic_assessment_evidence_items WHERE case_id = ? ORDER BY created_at, id",
                (case_id,),
            ).fetchall()
        )
        items = [_present(row) for row in rows]
        if str(actor.get("role") or "") in {"parent", "student"}:
            items = [
                item for item in items
                if "participant" in item["visibility_scope"]
                and (item["kind"] != "H" or item["review_status"] in {"human_reviewed", "participant_checked"})
            ]
        write_audit_log(
            conn,
            "therapeutic_assessment_evidence_viewed",
            str(actor["id"]),
            "therapeutic_assessment_case",
            case_id,
            {"count": len(items)},
        )
        conn.commit()
        return {"items": items, "count": len(items)}


def review_hypothesis(actor: dict, evidence_id: str, payload: dict, idempotency_key: str) -> dict:
    key = _idempotency(idempotency_key)
    if str(actor.get("role") or "") not in REVIEW_ROLES:
        raise TherapeuticAssessmentError("forbidden", "人工假设需要督导或管理员复核。", 403)
    decision = str(payload.get("decision") or "")
    expected = payload.get("expected_version")
    if decision not in {"approved", "changes_requested"} or not isinstance(expected, int):
        raise TherapeuticAssessmentError("validation_error", "需要有效decision和expected_version。")
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM therapeutic_assessment_evidence_items WHERE id = ?", (evidence_id,)).fetchone()
        if row is None:
            raise TherapeuticAssessmentError("not_found", "没有找到该证据项。", 404)
        item = row_to_dict(row)
        if item["kind"] != "H":
            raise TherapeuticAssessmentError("validation_error", "只有H项进入人工假设复核。")
        case = _case_row(conn, str(item["case_id"]))
        _assert_researcher(actor, case)
        from services.therapeutic_assessment_competency_service import (
            assert_task_authorized,
        )

        assert_task_authorized(conn, actor, case, "formal_assessment")
        if int(item["version"]) != expected:
            raise TherapeuticAssessmentError("version_conflict", "证据项已更新，请刷新后重试。", 409)
        status = "human_reviewed" if decision == "approved" else "changes_requested"
        timestamp = now_iso()
        cursor = conn.execute(
            """
            UPDATE therapeutic_assessment_evidence_items
            SET review_status = ?, reviewed_by = ?, reviewed_at = ?,
                version = version + 1, updated_at = ?
            WHERE id = ? AND version = ?
            """,
            (status, str(actor["id"]), timestamp, timestamp, evidence_id, expected),
        )
        if cursor.rowcount != 1:
            raise TherapeuticAssessmentError("version_conflict", "证据项已更新，请刷新后重试。", 409)
        write_audit_log(
            conn,
            "therapeutic_assessment_hypothesis_reviewed",
            str(actor["id"]),
            "therapeutic_assessment_evidence",
            evidence_id,
            {"decision": decision, "idempotency_key_recorded": bool(key)},
        )
        conn.commit()
        return _present(row_to_dict(conn.execute("SELECT * FROM therapeutic_assessment_evidence_items WHERE id = ?", (evidence_id,)).fetchone()))
