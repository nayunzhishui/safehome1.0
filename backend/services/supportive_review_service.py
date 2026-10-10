"""Participant-owned L0 supportive self-review (自助整理).

A self-help adaptation of collaborative/therapeutic assessment ideas: the
participant's own question and best guess, one concrete episode, exceptions,
chosen questionnaires with extended-inquiry notes, a letter organised from the
participant's own words plus the questionnaires' fixed wording, one small
experiment and a follow-up.

No staff workflow reads these records.  They live in the shared ``records``
table (``module_type = 'supportive_review'``, ``export_allowed = 0``), so
research exports never include them and production needs no schema change.
The letter never interprets free text: it only quotes the participant and the
rule wording that was already shown on each questionnaire result.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from database import (
    get_connection,
    json_dumps,
    json_loads,
    load_content_json,
    new_id,
    now_iso,
    row_to_dict,
    write_audit_log,
)
from services.card_service import list_cards
from services.idempotency_service import (
    IdempotencyConflictError,
    IdempotencyValidationError,
    canonical_request_hash,
    reserve_idempotency,
)
from services.risk_review_service import create_risk_review_record, should_create_risk_review
from services.risk_service import check_text_risk


MODULE_TYPE = "supportive_review"
RECORD_SCHEMA = "safehome.supportive-review.v1"
GUIDE_FILE = "supportive_review_guide.json"
CREATE_ENDPOINT = "POST /api/supportive-review/reviews"
PARTICIPANT_ROLES = {"parent", "student"}
STEP_ORDER = ("question", "guess", "episode", "exceptions", "scales", "inquiry", "letter", "experiment", "followup")
SECTIONS = ("question", "guess", "episode", "exceptions", "scales", "inquiry", "letter_checks", "experiment", "followup")
RISK_RANK = {"low": 0, "medium": 1, "high": 2}
FIT_VALUES = {"like", "partly", "not_like", "need_time"}
MAX_REVIEWS_PER_USER = 50
MAX_LINKED_RESULTS = 3
NOTE_MAX_LENGTH = 300
# Dates shown to participants follow mainland China local time (no DST).
LOCAL_TZ = timezone(timedelta(hours=8))
# Rules whose wording describes practice rather than the result itself.
NON_DESCRIPTIVE_RULE_PREFIXES = ("task12_", "student_profile_")
BOUNDARY_NOTICE = "自助整理只用于自我了解，不构成诊断、专业评估或治疗建议；遇到紧急情况请使用紧急求助资源。"


class SupportiveReviewError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400, details: dict | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details or {}


def _guide() -> dict:
    return load_content_json(GUIDE_FILE)


def _step(step_id: str) -> dict:
    return next((step for step in _guide().get("steps", []) if step.get("id") == step_id), {})


def _field_limits(step_id: str) -> dict[str, int]:
    return {
        str(field["key"]): int(field.get("max_length") or NOTE_MAX_LENGTH)
        for field in _step(step_id).get("fields", [])
        if isinstance(field, dict) and field.get("key")
    }


def _topics() -> dict[str, dict]:
    return {str(topic.get("id")): topic for topic in _guide().get("topics", []) if topic.get("id")}


def _assert_participant(actor: dict) -> None:
    if str(actor.get("role") or "") not in PARTICIPANT_ROLES:
        raise SupportiveReviewError("forbidden", "自助整理只能由参与者本人使用。", 403)


def _text(value, field: str, limit: int, *, required: bool = False) -> str:
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise SupportiveReviewError("validation_error", "填写内容格式不正确。", 400, {"field": field})
    value = value.strip()
    if required and not value:
        raise SupportiveReviewError("validation_error", "这一项需要填写。", 400, {"field": field})
    if len(value) > limit:
        raise SupportiveReviewError("validation_error", f"这一项最多 {limit} 个字。", 400, {"field": field, "max_length": limit})
    return value


def _choice(value, field: str, allowed: set[str], *, required: bool = False) -> str:
    value = "" if value is None else str(value)
    if not value and not required:
        return ""
    if value not in allowed:
        raise SupportiveReviewError("validation_error", "请从给出的选项中选择。", 400, {"field": field})
    return value


def _date_value(value, field: str) -> str:
    if value in (None, ""):
        return ""
    try:
        return date.fromisoformat(str(value)).isoformat()
    except ValueError as exc:
        raise SupportiveReviewError("validation_error", "日期格式不正确。", 400, {"field": field}) from exc


def _local_date(timestamp: str | None) -> str:
    if not timestamp:
        return ""
    try:
        parsed = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
    except ValueError:
        return str(timestamp)[:10]
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(LOCAL_TZ).date().isoformat()


def _today() -> date:
    return datetime.now(LOCAL_TZ).date()


def _row(conn, actor: dict, review_id: str) -> dict:
    row = conn.execute(
        "SELECT * FROM records WHERE id = ? AND user_id = ? AND module_type = ?",
        (str(review_id), str(actor["id"]), MODULE_TYPE),
    ).fetchone()
    if row is None:
        raise SupportiveReviewError("not_found", "没有找到这次整理。", 404)
    return row_to_dict(row)


def _data(row: dict) -> dict:
    data = json_loads(row.get("data_json"), {})
    return data if isinstance(data, dict) else {}


def _save(conn, row_id: str, data: dict) -> None:
    timestamp = now_iso()
    data["updated_at"] = timestamp
    conn.execute(
        "UPDATE records SET data_json = ?, updated_at = ? WHERE id = ? AND module_type = ?",
        (json_dumps(data), timestamp, row_id, MODULE_TYPE),
    )


def _linked_results(conn, user_id: str, result_ids: list[str]) -> list[dict]:
    if not result_ids:
        return []
    placeholders = ", ".join("?" for _ in result_ids)
    rows = conn.execute(
        f"""
        SELECT id, worksheet_id, worksheet_title, scores_json, result_summary,
               content_snapshot_json, created_at
        FROM assessment_results
        WHERE user_id = ? AND id IN ({placeholders})
        """,
        (user_id, *result_ids),
    ).fetchall()
    by_id = {str(row["id"]): row_to_dict(row) for row in rows}
    return [by_id[result_id] for result_id in result_ids if result_id in by_id]


def _result_risk(result: dict) -> str:
    scores = json_loads(result.get("scores_json"), {}) or {}
    level = str((scores.get("risk") or {}).get("risk_level") or "low")
    return level if level in RISK_RANK else "low"


def _participant_texts(data: dict) -> list[str]:
    texts = [
        data.get("question"),
        data.get("question_history"),
        data.get("guess"),
        data.get("hoped_change"),
        *((data.get("episode") or {}).get(key) for key in ("situation", "body_feeling", "thought", "action", "after")),
        *((data.get("exceptions") or {}).get(key) for key in ("exception", "resources")),
        *(value for item in (data.get("inquiry") or {}).values() for value in (item or {}).values()),
        *((item or {}).get("note") for item in (data.get("letter_checks") or {}).values()),
        *((data.get("experiment") or {}).get(key) for key in ("own_idea", "obstacle", "plan_b", "stop_condition")),
        *((data.get("followup") or {}).get(key) for key in ("noticed", "learned")),
    ]
    return [str(text) for text in texts if isinstance(text, str) and text.strip()]


def _apply_text_risk(conn, actor: dict, review_id: str, data: dict) -> None:
    texts = _participant_texts(data)
    risk = check_text_risk(texts, source="supportive_review") if texts else None
    level = str((risk or {}).get("risk_level") or "low")
    data["text_risk_level"] = level if level in RISK_RANK else "low"
    data["safety_route"] = str((risk or {}).get("safety_route") or "standard")
    data["safe_response"] = (risk or {}).get("safe_response") if level != "low" else None
    reviewed_rank = RISK_RANK.get(str(data.get("risk_review_level") or ""), -1)
    if risk and should_create_risk_review(risk) and RISK_RANK.get(level, 0) > reviewed_rank:
        create_risk_review_record(conn, str(actor["id"]), "supportive_review", review_id, risk)
        data["risk_review_level"] = level


def _effective_risk(data: dict, results: list[dict]) -> str:
    levels = [str(data.get("text_risk_level") or "low"), *(_result_risk(result) for result in results)]
    return max(levels, key=lambda level: RISK_RANK.get(level, 0))


def _risk_payload(level: str, data: dict) -> dict:
    letter = _guide().get("letter", {})
    message = None
    if level == "high":
        message = letter.get("high_risk_note")
    elif level == "medium":
        message = data.get("safe_response") or letter.get("medium_note")
    return {"level": level, "message": message, "show_emergency_resources": level in {"medium", "high"}}


def _next_step(data: dict) -> str:
    done = set(data.get("steps_done") or [])
    for step_id in STEP_ORDER:
        if step_id == "inquiry" and not data.get("linked_result_ids"):
            continue
        if step_id not in done:
            return step_id
    return "done"


def _followup_due_on(data: dict) -> str:
    experiment = data.get("experiment") or {}
    if not experiment.get("own_idea") or (data.get("followup") or {}).get("completed_at"):
        return ""
    days = int((_guide().get("experiment") or {}).get("followup_days") or 7)
    start = experiment.get("planned_date") or _local_date(experiment.get("saved_at"))
    try:
        return (date.fromisoformat(start) + timedelta(days=days)).isoformat()
    except ValueError:
        return ""


def _status(data: dict, due_on: str) -> str:
    if (data.get("followup") or {}).get("completed_at"):
        return "completed"
    if due_on and date.fromisoformat(due_on) <= _today():
        return "followup_due"
    return "in_progress"


def _summary(row: dict, data: dict) -> dict:
    topic = _topics().get(str(data.get("topic_id") or ""), {})
    due_on = _followup_due_on(data)
    return {
        "id": row["id"],
        "version": int(data.get("version") or 1),
        "question": data.get("question") or "",
        "topic_id": data.get("topic_id") or "",
        "topic_title": topic.get("title") or "",
        "next_step": _next_step(data),
        "status": _status(data, due_on),
        "followup_due_on": due_on,
        "risk_level": str(data.get("text_risk_level") or "low"),
        "created_on": _local_date(row.get("created_at")),
        "updated_on": _local_date(row.get("updated_at")),
    }


def _rule_clues(result: dict) -> list[dict]:
    snapshot = json_loads(result.get("content_snapshot_json"), {}) or {}
    rules = ((snapshot.get("recommendation") or {}).get("rules")) or []
    scores = json_loads(result.get("scores_json"), {}) or {}
    labels = {str(item.get("key")): str(item.get("label") or item.get("key")) for item in scores.get("dimensions", []) if isinstance(item, dict)}
    clues = []
    for rule in rules:
        if not isinstance(rule, dict) or not rule.get("rule_id"):
            continue
        if str(rule["rule_id"]).startswith(NON_DESCRIPTIVE_RULE_PREFIXES):
            continue
        reason = str(rule.get("reason") or "").strip()
        sentence = reason.split("。")[0].strip()
        if not sentence:
            continue
        dimension = str((rule.get("trigger_condition") or {}).get("dimension") or "")
        clues.append({
            "rule_id": str(rule["rule_id"]),
            "label": labels.get(dimension, "整体") if dimension and dimension != "TOTAL" else "整体",
            "text": sentence + "。",
        })
    return clues


def _score_line(result: dict) -> str:
    scores = json_loads(result.get("scores_json"), {}) or {}
    parts = [
        f"{item.get('label') or item.get('key')} {item.get('score')}"
        for item in scores.get("dimensions", [])
        if isinstance(item, dict) and item.get("score") is not None
    ]
    if not parts and scores.get("total_score") is not None:
        parts = [f"总分 {scores['total_score']}"]
    return "；".join(parts[:6])


def _quote(value: str, limit: int = 40) -> str:
    value = " ".join(str(value or "").split())
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _episode_text(episode: dict) -> str:
    parts = []
    if episode.get("situation"):
        parts.append(f"{episode['situation']}。")
    if episode.get("body_feeling"):
        parts.append(f"当时：{episode['body_feeling']}。")
    if episode.get("thought"):
        parts.append(f"脑子里想到“{episode['thought']}”。")
    if episode.get("action"):
        parts.append(f"你做的是：{episode['action']}。")
    if episode.get("after"):
        parts.append(f"之后：{episode['after']}。")
    if episode.get("intensity") is not None:
        parts.append(f"难受程度 {episode['intensity']}/10。")
    return "".join(parts).replace("。。", "。")


def build_letter(data: dict, results: list[dict], risk_level: str) -> dict:
    letter = _guide().get("letter", {})
    sections_config = letter.get("sections", {})
    templates = letter.get("templates", {})
    question = str(data.get("question") or "")
    payload = {
        "title": str(letter.get("title_template") or "{question}").replace("{question}", _quote(question, 30)),
        "opening": letter.get("opening"),
        "check_options": letter.get("check_options", []),
        "sections": [],
        "closing": letter.get("closing"),
        "safety_only": risk_level == "high",
    }
    if risk_level == "high":
        payload["sections"].append({"id": "safety", "title": "先照顾好安全", "items": [{"id": "safety_note", "kind": "note", "text": letter.get("high_risk_note")}]})
        return payload

    own_words = []
    for key, label in (("question", "你想弄清楚"), ("guess", "你的猜测"), ("hoped_change", "你希望的变化")):
        if data.get(key):
            own_words.append({"id": key, "kind": "quote", "label": label, "text": data[key]})
    episode_text = _episode_text(data.get("episode") or {})
    if episode_text:
        own_words.append({"id": "episode", "kind": "quote", "label": "你记录的一次经历", "text": episode_text})
    resources = (data.get("exceptions") or {}).get("resources")
    if resources:
        own_words.append({"id": "resources", "kind": "quote", "label": "曾经帮到你的", "text": resources})
    payload["sections"].append({"id": "your_words", "level": 1, "title": sections_config.get("your_words", {}).get("title"), "items": own_words})

    clues = []
    first_label = ""
    for result in results:
        title = str(result.get("worksheet_title") or "问卷")
        result_clues = _rule_clues(result)
        if result_clues:
            for clue in result_clues:
                first_label = first_label or (clue["label"] if clue["label"] != "整体" else title)
                clues.append({
                    "id": f"result:{result['id']}:rule:{clue['rule_id']}",
                    "kind": "clue",
                    "label": f"{title} · {clue['label']}",
                    "text": clue["text"],
                    "checkable": True,
                })
        else:
            line = _score_line(result)
            if line:
                clues.append({
                    "id": f"result:{result['id']}:scores",
                    "kind": "fact",
                    "label": f"{title} · {_local_date(result.get('created_at'))}",
                    "text": f"这次作答的得分：{line}。",
                    "checkable": False,
                })
    if clues:
        payload["sections"].append({
            "id": "scale_clues",
            "level": 2,
            "title": sections_config.get("scale_clues", {}).get("title"),
            "intro": sections_config.get("scale_clues", {}).get("intro"),
            "items": clues,
        })

    connections = []
    if data.get("guess") and clues:
        connections.append({"id": "connection:guess", "kind": "prompt", "text": templates.get("connection_guess", "").replace("{guess}", _quote(data["guess"]))})
    thought = (data.get("episode") or {}).get("thought")
    if thought and first_label:
        connections.append({
            "id": "connection:thought",
            "kind": "prompt",
            "text": templates.get("connection_thought", "").replace("{thought}", _quote(thought)).replace("{label}", first_label),
        })
    exception = (data.get("exceptions") or {}).get("exception")
    if exception:
        connections.append({"id": "connection:exception", "kind": "prompt", "text": templates.get("connection_exception", "").replace("{exception}", _quote(exception))})
    for result in results:
        stood_out = ((data.get("inquiry") or {}).get(str(result["id"])) or {}).get("stood_out")
        if stood_out:
            connections.append({
                "id": f"connection:inquiry:{result['id']}",
                "kind": "prompt",
                "text": templates.get("connection_inquiry", "")
                .replace("{title}", str(result.get("worksheet_title") or "问卷"))
                .replace("{stood_out}", _quote(stood_out)),
            })
    if connections:
        payload["sections"].append({"id": "connections", "level": 2, "title": sections_config.get("connections", {}).get("title"), "items": connections})

    if risk_level == "low":
        angles = sections_config.get("other_angles", {})
        payload["sections"].append({
            "id": "other_angles",
            "level": 3,
            "collapsed": True,
            "title": angles.get("title"),
            "intro": angles.get("intro"),
            "items": [{"id": f"angle:{item['id']}", "kind": "prompt", "text": item["text"]} for item in angles.get("prompts", [])],
        })
    else:
        payload["sections"].append({"id": "support", "title": "照顾好自己", "items": [{"id": "medium_note", "kind": "note", "text": letter.get("medium_note")}]})
    payload["sections"].append({"id": "next", "title": sections_config.get("next", {}).get("title"), "items": [{"id": "next_text", "kind": "note", "text": sections_config.get("next", {}).get("text")}]})
    return payload


def _letter_item_ids(letter: dict) -> dict[str, str]:
    return {
        item["id"]: item.get("kind", "")
        for section in letter.get("sections", [])
        for item in section.get("items", [])
        if item.get("kind") in {"clue", "prompt"}
    }


def _card_options(data: dict, results: list[dict], risk_level: str) -> list[dict]:
    if risk_level == "high":
        return []
    visible = {card["id"]: card for card in list_cards() if card.get("id")}
    limit = int((_guide().get("experiment") or {}).get("max_card_options") or 3)
    ordered: list[str] = []
    for result in results:
        snapshot = json_loads(result.get("content_snapshot_json"), {}) or {}
        for card_id in ((snapshot.get("recommendation") or {}).get("card_ids")) or []:
            if card_id in visible and card_id not in ordered:
                ordered.append(card_id)
    if not ordered:
        topic = _topics().get(str(data.get("topic_id") or ""), {})
        for worksheet_id in topic.get("worksheet_ids", []):
            for card_id, card in visible.items():
                targets = {target.get("worksheet_id") for target in card.get("scale_targets", []) if isinstance(target, dict)}
                if worksheet_id in targets and card_id not in ordered:
                    ordered.append(card_id)
    return [
        {
            "id": card_id,
            "title": visible[card_id].get("user_facing_title") or visible[card_id].get("title"),
            "purpose": visible[card_id].get("purpose") or "",
            "duration_minutes": visible[card_id].get("duration_minutes"),
        }
        for card_id in ordered[:limit]
    ]


def _present(row: dict, data: dict, results: list[dict], *, detail: bool) -> dict:
    risk_level = _effective_risk(data, results)
    payload = _summary(row, data)
    payload.update({
        "question_history": data.get("question_history") or "",
        "guess": data.get("guess") or "",
        "hoped_change": data.get("hoped_change") or "",
        "episode": data.get("episode") or {},
        "exceptions": data.get("exceptions") or {},
        "linked_results": [
            {
                "id": result["id"],
                "worksheet_id": result.get("worksheet_id"),
                "worksheet_title": result.get("worksheet_title"),
                "created_on": _local_date(result.get("created_at")),
                "risk_level": _result_risk(result),
            }
            for result in results
        ],
        "inquiry": data.get("inquiry") or {},
        "letter_checks": data.get("letter_checks") or {},
        "experiment": data.get("experiment") or {},
        "followup": data.get("followup") or {},
        "steps_done": data.get("steps_done") or [],
        "risk": _risk_payload(risk_level, data),
        "boundary_notice": BOUNDARY_NOTICE,
    })
    if detail:
        payload["letter"] = build_letter(data, results, risk_level)
        payload["card_options"] = _card_options(data, results, risk_level)
    return payload


def guide_payload() -> dict:
    guide = _guide()
    return {
        "version": guide.get("version"),
        "display_name": guide.get("display_name"),
        "service_level": guide.get("service_level"),
        "boundary": guide.get("boundary", {}),
        "question_guide": guide.get("question_guide", {}),
        "topics": [
            {key: topic.get(key) for key in ("id", "title", "hint", "worksheet_ids", "examples")}
            for topic in guide.get("topics", [])
        ],
        "steps": guide.get("steps", []),
        "check_options": (guide.get("letter") or {}).get("check_options", []),
        "followup_days": (guide.get("experiment") or {}).get("followup_days"),
    }


def list_reviews(actor: dict) -> dict:
    _assert_participant(actor)
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM records WHERE user_id = ? AND module_type = ? ORDER BY updated_at DESC LIMIT ?",
            (str(actor["id"]), MODULE_TYPE, MAX_REVIEWS_PER_USER),
        ).fetchall()
    items = [_summary(row_to_dict(row), _data(row_to_dict(row))) for row in rows]
    return {"items": items, "count": len(items), "boundary_notice": BOUNDARY_NOTICE}


def create_review(actor: dict, payload: dict, idempotency_key: str) -> tuple[dict, int]:
    _assert_participant(actor)
    limits = _field_limits("question")
    question = _text(payload.get("question"), "question", limits.get("question", 200), required=True)
    history = _text(payload.get("question_history"), "question_history", limits.get("question_history", 300))
    topic_id = str(payload.get("topic_id") or "")
    if topic_id and topic_id not in _topics():
        raise SupportiveReviewError("validation_error", "请从列出的主题中选择。", 400, {"field": "topic_id"})
    try:
        request_hash = canonical_request_hash(
            actor_id=str(actor["id"]),
            endpoint=CREATE_ENDPOINT,
            version="v1",
            payload={"question": question, "question_history": history, "topic_id": topic_id},
        )
    except IdempotencyValidationError as exc:
        raise SupportiveReviewError(exc.code, exc.message, 400) from exc
    review_id = new_id("support_review")
    timestamp = now_iso()
    with get_connection() as conn:
        try:
            reservation = reserve_idempotency(
                conn,
                actor_id=str(actor["id"]),
                endpoint=CREATE_ENDPOINT,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                resource_type="supportive_review",
                resource_id=review_id,
            )
        except IdempotencyValidationError as exc:
            raise SupportiveReviewError(exc.code, exc.message, 400) from exc
        except IdempotencyConflictError as exc:
            raise SupportiveReviewError("idempotency_conflict", str(exc), 409) from exc
        if not reservation.created:
            row = _row(conn, actor, reservation.resource_id)
            data = _data(row)
            return _present(row, data, _linked_results(conn, str(actor["id"]), data.get("linked_result_ids") or []), detail=True), 200
        count = conn.execute(
            "SELECT COUNT(*) AS count FROM records WHERE user_id = ? AND module_type = ?",
            (str(actor["id"]), MODULE_TYPE),
        ).fetchone()["count"]
        if count >= MAX_REVIEWS_PER_USER:
            raise SupportiveReviewError("review_limit_reached", "整理记录已达上限，请先删除不再需要的记录。", 409)
        data = {
            "schema": RECORD_SCHEMA,
            "guide_version": _guide().get("version"),
            "version": 1,
            "topic_id": topic_id,
            "question": question,
            "question_history": history,
            "steps_done": ["question"],
            "linked_result_ids": [],
            "created_at": timestamp,
        }
        _apply_text_risk(conn, actor, review_id, data)
        data["updated_at"] = timestamp
        conn.execute(
            """
            INSERT INTO records (id, user_id, module_type, source_id, data_json, created_at, updated_at, export_allowed)
            VALUES (?, ?, ?, NULL, ?, ?, ?, 0)
            """,
            (review_id, str(actor["id"]), MODULE_TYPE, json_dumps(data), timestamp, timestamp),
        )
        write_audit_log(conn, "supportive_review_created", str(actor["id"]), "supportive_review", review_id, {"topic_id": topic_id, "risk_level": data["text_risk_level"]})
        conn.commit()
        row = _row(conn, actor, review_id)
        return _present(row, _data(row), [], detail=True), 201


def get_review(actor: dict, review_id: str) -> dict:
    _assert_participant(actor)
    with get_connection() as conn:
        row = _row(conn, actor, review_id)
        data = _data(row)
        results = _linked_results(conn, str(actor["id"]), data.get("linked_result_ids") or [])
    return _present(row, data, results, detail=True)


def _update_question(data: dict, body: dict) -> None:
    limits = _field_limits("question")
    data["question"] = _text(body.get("question"), "question", limits.get("question", 200), required=True)
    data["question_history"] = _text(body.get("question_history"), "question_history", limits.get("question_history", 300))
    topic_id = str(body.get("topic_id") or "")
    if topic_id and topic_id not in _topics():
        raise SupportiveReviewError("validation_error", "请从列出的主题中选择。", 400, {"field": "topic_id"})
    data["topic_id"] = topic_id


def _update_fields(data: dict, body: dict, step_id: str, keys: tuple[str, ...]) -> dict:
    limits = _field_limits(step_id)
    return {key: _text(body.get(key), key, limits.get(key, NOTE_MAX_LENGTH)) for key in keys}


def _update_episode(data: dict, body: dict) -> None:
    episode = _update_fields(data, body, "episode", ("situation", "body_feeling", "thought", "action", "after"))
    intensity = body.get("intensity")
    if intensity in (None, ""):
        episode["intensity"] = None
    else:
        if isinstance(intensity, bool) or not isinstance(intensity, (int, float)) or not 0 <= intensity <= 10:
            raise SupportiveReviewError("validation_error", "难受程度请在 0 到 10 之间选择。", 400, {"field": "intensity"})
        episode["intensity"] = int(intensity)
    data["episode"] = episode


def _update_scales(conn, actor: dict, data: dict, body: dict) -> None:
    result_ids = body.get("result_ids")
    if not isinstance(result_ids, list) or len(result_ids) > MAX_LINKED_RESULTS:
        raise SupportiveReviewError("validation_error", f"最多加入 {MAX_LINKED_RESULTS} 份问卷结果。", 400, {"field": "result_ids"})
    unique_ids = list(dict.fromkeys(str(item) for item in result_ids if str(item or "").strip()))
    found = _linked_results(conn, str(actor["id"]), unique_ids)
    if len(found) != len(unique_ids):
        raise SupportiveReviewError("not_found", "有问卷结果不存在或不属于你。", 404, {"field": "result_ids"})
    data["linked_result_ids"] = unique_ids
    inquiry = data.get("inquiry") or {}
    data["inquiry"] = {key: value for key, value in inquiry.items() if key in unique_ids}


def _update_inquiry(data: dict, body: dict) -> None:
    linked = set(data.get("linked_result_ids") or [])
    entries = body.get("entries")
    if not isinstance(entries, dict):
        raise SupportiveReviewError("validation_error", "回看内容格式不正确。", 400, {"field": "entries"})
    inquiry = {}
    for result_id, entry in entries.items():
        if result_id not in linked:
            raise SupportiveReviewError("validation_error", "只能回看已加入这次整理的问卷。", 400, {"field": "entries"})
        if not isinstance(entry, dict):
            raise SupportiveReviewError("validation_error", "回看内容格式不正确。", 400, {"field": "entries"})
        inquiry[result_id] = _update_fields(data, entry, "inquiry", ("stood_out", "fit"))
    data["inquiry"] = inquiry


def _update_letter_checks(data: dict, body: dict, results: list[dict]) -> None:
    checks = body.get("checks")
    if not isinstance(checks, dict):
        raise SupportiveReviewError("validation_error", "核对内容格式不正确。", 400, {"field": "checks"})
    letter = build_letter(data, results, _effective_risk(data, results))
    known = _letter_item_ids(letter)
    saved = {}
    for item_id, entry in checks.items():
        if item_id not in known:
            continue
        if not isinstance(entry, dict):
            raise SupportiveReviewError("validation_error", "核对内容格式不正确。", 400, {"field": "checks"})
        item = {"note": _text(entry.get("note"), "note", NOTE_MAX_LENGTH)}
        if known[item_id] == "clue":
            item["fit"] = _choice(entry.get("fit"), "fit", FIT_VALUES)
        if item.get("fit") or item["note"]:
            saved[item_id] = item
    data["letter_checks"] = saved


def _update_experiment(data: dict, body: dict, card_options: list[dict]) -> None:
    limits = _field_limits("experiment")
    card_id = str(body.get("card_id") or "")
    if card_id and card_id not in {card["id"] for card in card_options}:
        raise SupportiveReviewError("validation_error", "请从列出的练习中选择。", 400, {"field": "card_id"})
    data["experiment"] = {
        "own_idea": _text(body.get("own_idea"), "own_idea", limits.get("own_idea", 200), required=True),
        "obstacle": _text(body.get("obstacle"), "obstacle", limits.get("obstacle", 200)),
        "plan_b": _text(body.get("plan_b"), "plan_b", limits.get("plan_b", 200)),
        "stop_condition": _text(body.get("stop_condition"), "stop_condition", limits.get("stop_condition", 200), required=True),
        "card_id": card_id,
        "planned_date": _date_value(body.get("planned_date"), "planned_date"),
        "saved_at": now_iso(),
    }


def _update_followup(data: dict, body: dict) -> None:
    if not (data.get("experiment") or {}).get("own_idea"):
        raise SupportiveReviewError("experiment_required", "请先写下一个想试试的小实验。", 409)
    choices = _step("followup").get("choices", {})
    limits = _field_limits("followup")
    data["followup"] = {
        "question_now": _choice(body.get("question_now"), "question_now", {item["value"] for item in choices.get("question_now", [])}, required=True),
        "next": _choice(body.get("next"), "next", {item["value"] for item in choices.get("next", [])}, required=True),
        "noticed": _text(body.get("noticed"), "noticed", limits.get("noticed", 300)),
        "learned": _text(body.get("learned"), "learned", limits.get("learned", 300)),
        "completed_at": now_iso(),
    }


def update_review(actor: dict, review_id: str, payload: dict) -> dict:
    _assert_participant(actor)
    section = str(payload.get("section") or "")
    if section not in SECTIONS:
        raise SupportiveReviewError("validation_error", "不支持的整理步骤。", 400, {"field": "section"})
    body = payload.get("data")
    if not isinstance(body, dict):
        raise SupportiveReviewError("validation_error", "填写内容格式不正确。", 400, {"field": "data"})
    with get_connection() as conn:
        row = _row(conn, actor, review_id)
        data = _data(row)
        current_version = int(data.get("version") or 1)
        expected = payload.get("expected_version")
        if isinstance(expected, bool) or not isinstance(expected, int) or expected != current_version:
            raise SupportiveReviewError("version_conflict", "这次整理已在别处更新，请刷新后再保存。", 409, {"current_version": current_version})
        results = _linked_results(conn, str(actor["id"]), data.get("linked_result_ids") or [])
        if section == "question":
            _update_question(data, body)
        elif section == "guess":
            data.update(_update_fields(data, body, "guess", ("guess", "hoped_change")))
        elif section == "episode":
            _update_episode(data, body)
        elif section == "exceptions":
            data["exceptions"] = _update_fields(data, body, "exceptions", ("exception", "resources"))
        elif section == "scales":
            _update_scales(conn, actor, data, body)
        elif section == "inquiry":
            _update_inquiry(data, body)
        elif section == "letter_checks":
            _update_letter_checks(data, body, results)
        elif section == "experiment":
            _update_experiment(data, body, _card_options(data, results, _effective_risk(data, results)))
        elif section == "followup":
            _update_followup(data, body)
        step_id = "letter" if section == "letter_checks" else section
        steps_done = list(data.get("steps_done") or [])
        if step_id not in steps_done:
            steps_done.append(step_id)
        data["steps_done"] = steps_done
        data["version"] = current_version + 1
        _apply_text_risk(conn, actor, row["id"], data)
        _save(conn, row["id"], data)
        write_audit_log(conn, "supportive_review_updated", str(actor["id"]), "supportive_review", row["id"], {"section": section, "version": data["version"], "risk_level": data["text_risk_level"]})
        conn.commit()
        row = _row(conn, actor, review_id)
        data = _data(row)
        results = _linked_results(conn, str(actor["id"]), data.get("linked_result_ids") or [])
    return _present(row, data, results, detail=True)


def delete_review(actor: dict, review_id: str) -> dict:
    _assert_participant(actor)
    with get_connection() as conn:
        row = _row(conn, actor, review_id)
        conn.execute("DELETE FROM records WHERE id = ? AND user_id = ? AND module_type = ?", (row["id"], str(actor["id"]), MODULE_TYPE))
        write_audit_log(conn, "supportive_review_deleted", str(actor["id"]), "supportive_review", row["id"], {})
        conn.commit()
    return {"id": row["id"], "deleted": True}
