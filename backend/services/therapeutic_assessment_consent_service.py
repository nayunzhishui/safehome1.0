"""Per-item data control and dynamic consent for collaborative assessment."""
from __future__ import annotations
from datetime import datetime, timezone
from database import get_connection, json_dumps, json_loads, new_id, now_iso, row_to_dict, write_audit_log
from services.therapeutic_assessment_service import TherapeuticAssessmentError, _assert_participant, _case_row, _idempotency

VISIBILITIES = {"private", "professionals", "confirmed_shared_feedback"}
PURPOSES = {"collaborative_assessment", "human_review", "shared_feedback"}
PREVIEW = "你有一项协作资料状态更新，请进入小程序查看。"
CREATE_FIELDS = {"subject_user_id", "involved_user_ids", "content_ref", "content_sha256", "purpose", "visibility", "allowed_viewer_ids", "expires_at"}

def _parse_time(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TherapeuticAssessmentError("validation_error", "expires_at格式无效。") from exc

def _present(row: dict, include_ref: bool = True) -> dict:
    item = dict(row)
    item["involved_user_ids"] = json_loads(item.pop("involved_user_ids_json", None), [])
    item["allowed_viewer_ids"] = json_loads(item.pop("allowed_viewer_ids_json", None), [])
    item["retained_under_legal_hold"] = bool(item.get("legal_hold_reason"))
    item["notification_preview"] = PREVIEW
    if not include_ref:
        item.pop("content_ref", None)
        item.pop("content_sha256", None)
    return item

def _expired(item: dict) -> bool:
    return _parse_time(str(item["expires_at"])).astimezone(timezone.utc) <= datetime.now(timezone.utc)

def _confirmed_shared(conn, item: dict) -> bool:
    required = {str(item["subject_user_id"]), *json_loads(item.get("involved_user_ids_json"), [])}
    approved = {
        str(row["actor_id"])
        for row in conn.execute(
            "SELECT actor_id FROM therapeutic_assessment_data_consents WHERE data_item_id = ? AND action = 'approve'",
            (item["id"],),
        ).fetchall()
    }
    return required.issubset(approved)

def _can_read(conn, actor: dict, item: dict) -> bool:
    actor_id = str(actor["id"])
    if actor_id in {str(item["controller_user_id"]), str(item["provider_user_id"])}:
        return True
    visibility = str(item["visibility"])
    allowed = set(json_loads(item.get("allowed_viewer_ids_json"), []))
    if visibility == "professionals":
        return actor_id in allowed and str(actor.get("role") or "") in {"researcher", "supervisor", "admin"}
    if visibility == "confirmed_shared_feedback":
        return actor_id in allowed and _confirmed_shared(conn, item)
    return False

def create_data_item(actor: dict, case_id: str, payload: dict, idempotency_key: str) -> tuple[dict, int]:
    key = _idempotency(idempotency_key)
    unknown = set(payload) - CREATE_FIELDS
    if unknown:
        raise TherapeuticAssessmentError("validation_error", "资料包含未支持字段。", details={"unknown_fields": sorted(unknown)})
    role = str(actor.get("role") or "")
    if role not in {"parent", "student"}:
        raise TherapeuticAssessmentError("forbidden", "多方资料由参与者本人控制。", 403)
    subject = str(payload.get("subject_user_id") or "")
    involved = payload.get("involved_user_ids", [])
    viewers = payload.get("allowed_viewer_ids", [])
    visibility = str(payload.get("visibility") or "")
    purpose = str(payload.get("purpose") or "")
    content_ref = str(payload.get("content_ref") or "").strip()
    digest = str(payload.get("content_sha256") or "").lower()
    expires = str(payload.get("expires_at") or "")
    if not subject or not isinstance(involved, list) or not isinstance(viewers, list):
        raise TherapeuticAssessmentError("validation_error", "资料主体、涉及者和查看者格式无效。")
    if visibility not in VISIBILITIES or purpose not in PURPOSES:
        raise TherapeuticAssessmentError("validation_error", "资料用途或可见范围无效。")
    if not content_ref or len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise TherapeuticAssessmentError("validation_error", "资料引用或摘要无效。")
    _parse_time(expires)
    timestamp = now_iso()
    with get_connection() as conn:
        case = _case_row(conn, case_id)
        _assert_participant(actor, case)
        existing = conn.execute(
            "SELECT * FROM therapeutic_assessment_data_items WHERE provider_user_id = ? AND idempotency_key = ?",
            (str(actor["id"]), key),
        ).fetchone()
        if existing:
            return _present(row_to_dict(existing)), 200
        item_id = new_id("ta_data")
        status = "active" if subject == str(actor["id"]) else "pending_subject_consent"
        conn.execute(
            """INSERT INTO therapeutic_assessment_data_items
            (id, case_id, subject_user_id, provider_user_id, involved_user_ids_json, controller_user_id,
             visibility, allowed_viewer_ids_json, purpose, expires_at, status, content_ref, content_sha256,
             version, idempotency_key, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)""",
            (item_id, case_id, subject, str(actor["id"]), json_dumps(involved), subject, visibility,
             json_dumps(viewers), purpose, expires, status, content_ref, digest, key, timestamp, timestamp),
        )
        if subject == str(actor["id"]):
            conn.execute(
                """INSERT INTO therapeutic_assessment_data_consents
                (id, data_item_id, actor_id, action, visibility, allowed_viewer_ids_json, purpose,
                 expires_at, consent_version, idempotency_key, created_at)
                VALUES (?, ?, ?, 'approve', ?, ?, ?, ?, 1, ?, ?)""",
                (new_id("ta_consent"), item_id, subject, visibility, json_dumps(viewers), purpose, expires, key, timestamp),
            )
        write_audit_log(conn, "therapeutic_assessment_data_item_created", str(actor["id"]), "therapeutic_assessment_data_item", item_id, {"visibility": visibility, "purpose": purpose, "status": status})
        conn.commit()
        return _present(row_to_dict(conn.execute("SELECT * FROM therapeutic_assessment_data_items WHERE id = ?", (item_id,)).fetchone())), 201

def get_data_item(actor: dict, item_id: str) -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM therapeutic_assessment_data_items WHERE id = ?", (item_id,)).fetchone()
        if row is None:
            raise TherapeuticAssessmentError("not_found", "没有找到该资料。", 404)
        item = row_to_dict(row)
        if item["status"] == "withdrawn":
            raise TherapeuticAssessmentError("forbidden", "该资料授权已撤回。", 403)
        if _expired(item):
            raise TherapeuticAssessmentError("expired", "该资料授权已过期。", 410)
        if not _can_read(conn, actor, item):
            raise TherapeuticAssessmentError("forbidden", "该资料未向当前账号共享。", 403)
        write_audit_log(conn, "therapeutic_assessment_data_item_viewed", str(actor["id"]), "therapeutic_assessment_data_item", item_id, {"visibility": item["visibility"]})
        conn.commit()
        return _present(item)

def update_consent(actor: dict, item_id: str, payload: dict, idempotency_key: str) -> dict:
    key = _idempotency(idempotency_key)
    action = str(payload.get("action") or "")
    expected = payload.get("expected_version")
    if action not in {"approve", "modify", "withdraw"} or not isinstance(expected, int):
        raise TherapeuticAssessmentError("validation_error", "需要有效action和expected_version。")
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM therapeutic_assessment_data_items WHERE id = ?", (item_id,)).fetchone()
        if row is None:
            raise TherapeuticAssessmentError("not_found", "没有找到该资料。", 404)
        item = row_to_dict(row)
        actor_id = str(actor["id"])
        involved = {str(item["subject_user_id"]), *json_loads(item["involved_user_ids_json"], [])}
        if actor_id not in involved:
            raise TherapeuticAssessmentError("forbidden", "只有资料主体或涉及者可以更新同意。", 403)
        replay = conn.execute(
            """SELECT data_item_id, action FROM therapeutic_assessment_data_consents
            WHERE actor_id = ? AND idempotency_key = ?""",
            (actor_id, key),
        ).fetchone()
        if replay is not None:
            if str(replay["data_item_id"]) != item_id or str(replay["action"]) != action:
                raise TherapeuticAssessmentError("idempotency_conflict", "幂等键已用于不同的同意操作。", 409)
            return _present(item)
        if int(item["version"]) != expected:
            raise TherapeuticAssessmentError("version_conflict", "资料已更新，请刷新后重试。", 409)
        visibility = str(payload.get("visibility") or item["visibility"])
        viewers = payload.get("allowed_viewer_ids", json_loads(item["allowed_viewer_ids_json"], []))
        expires = str(payload.get("expires_at") or item["expires_at"])
        if visibility not in VISIBILITIES or not isinstance(viewers, list):
            raise TherapeuticAssessmentError("validation_error", "可见范围或查看者无效。")
        _parse_time(expires)
        status = "withdrawn" if action == "withdraw" else "active"
        legal_hold = str(payload.get("legal_hold_reason") or "").strip()[:500] if action == "withdraw" else item.get("legal_hold_reason")
        timestamp = now_iso()
        conn.execute(
            """UPDATE therapeutic_assessment_data_items SET visibility = ?, allowed_viewer_ids_json = ?,
            expires_at = ?, status = ?, legal_hold_reason = ?, withdrawn_at = ?,
            consent_version = consent_version + 1, version = version + 1, updated_at = ?
            WHERE id = ? AND version = ?""",
            (visibility, json_dumps(viewers), expires, status, legal_hold,
             timestamp if action == "withdraw" else item.get("withdrawn_at"), timestamp, item_id, expected),
        )
        conn.execute(
            """INSERT INTO therapeutic_assessment_data_consents
            (id, data_item_id, actor_id, action, visibility, allowed_viewer_ids_json, purpose,
             expires_at, consent_version, idempotency_key, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (new_id("ta_consent"), item_id, actor_id, action, visibility, json_dumps(viewers),
             item["purpose"], expires, int(item["consent_version"]) + 1, key, timestamp),
        )
        write_audit_log(conn, "therapeutic_assessment_data_consent_updated", actor_id, "therapeutic_assessment_data_item", item_id, {"action": action, "visibility": visibility})
        conn.commit()
        return _present(row_to_dict(conn.execute("SELECT * FROM therapeutic_assessment_data_items WHERE id = ?", (item_id,)).fetchone()))
