from __future__ import annotations

from datetime import datetime, timezone

from database import (
    get_connection,
    json_dumps,
    json_loads,
    load_content_json,
    new_id,
    now_iso,
    row_to_dict,
    rows_to_dicts,
    write_audit_log,
)
from services.therapeutic_assessment_service import (
    FORMAL_ROLES,
    REVIEW_ROLES,
    TherapeuticAssessmentError,
    _idempotency,
)


LEVEL_RANK = {"T1": 1, "T2": 2, "T3": 3}


def _policy() -> dict:
    return load_content_json("therapeutic_assessment_competency_policy.json")


def _parse_time(value: object, field: str) -> str:
    text = str(value or "").strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TherapeuticAssessmentError("validation_error", f"{field}必须是ISO时间。") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def _present(row: dict) -> dict:
    item = dict(row)
    item["scope"] = json_loads(item.pop("scope_json", None), {})
    item["effective"] = (
        item.get("status") == "active"
        and str(item.get("starts_at") or "") <= now_iso()
        and str(item.get("expires_at") or "") > now_iso()
    )
    return item


def _normalize_scope(conn, scope: object) -> dict:
    if not isinstance(scope, dict):
        raise TherapeuticAssessmentError("validation_error", "授权范围必须是对象。")
    normalized: dict[str, object] = {}
    for field in ("case_ids", "complexity_scopes", "readiness_levels"):
        value = scope.get(field)
        if value is None:
            continue
        if not isinstance(value, list) or not value:
            raise TherapeuticAssessmentError("validation_error", f"{field}必须是非空数组。")
        items = [str(item or "").strip() for item in value]
        if any(not item for item in items):
            raise TherapeuticAssessmentError("validation_error", f"{field}不能包含空值。")
        normalized[field] = list(dict.fromkeys(items))
    if not normalized:
        raise TherapeuticAssessmentError("validation_error", "授权必须明确case、复杂度或准备度范围。")
    case_ids = normalized.get("case_ids", [])
    if case_ids:
        snapshots: dict[str, dict[str, str]] = {}
        for case_id in case_ids:
            row = conn.execute(
                """
                SELECT id, complexity_scope, readiness_level
                FROM therapeutic_assessment_cases
                WHERE id = ?
                """,
                (case_id,),
            ).fetchone()
            if row is None:
                raise TherapeuticAssessmentError("validation_error", f"授权范围中的case不存在：{case_id}", 422)
            snapshots[str(case_id)] = {
                "complexity_scope": str(row["complexity_scope"]),
                "readiness_level": str(row["readiness_level"]),
            }
        normalized["case_scope_snapshots"] = snapshots
    return normalized


def create_authorization(
    actor: dict,
    payload: dict,
    idempotency_key: str,
) -> tuple[dict, int]:
    key = _idempotency(idempotency_key)
    if str(actor.get("role") or "") not in REVIEW_ROLES:
        raise TherapeuticAssessmentError("forbidden", "只有督导或管理员可以授予任务授权。", 403)
    user_id = str(payload.get("user_id") or "").strip()
    level = str(payload.get("competency_level") or "").upper()
    task_code = str(payload.get("task_code") or "").strip()
    supervisor_id = str(payload.get("supervisor_user_id") or "").strip()
    evidence_ref = str(payload.get("evidence_ref") or "").strip()
    scope = payload.get("scope")
    starts_at = _parse_time(payload.get("starts_at") or now_iso(), "starts_at")
    expires_at = _parse_time(payload.get("expires_at"), "expires_at")
    policy = _policy()
    if level not in LEVEL_RANK or task_code not in policy["minimum_level"]:
        raise TherapeuticAssessmentError("validation_error", "胜任力级别或任务代码无效。")
    if LEVEL_RANK[level] < LEVEL_RANK[policy["minimum_level"][task_code]]:
        raise TherapeuticAssessmentError("insufficient_competency", "该级别不能承担所选任务。", 422)
    if not user_id or not supervisor_id or not evidence_ref or expires_at <= starts_at:
        raise TherapeuticAssessmentError("validation_error", "授权对象、督导、证据和有效期必须完整。")
    with get_connection() as conn:
        replay = conn.execute(
            """
            SELECT a.* FROM therapeutic_assessment_authorization_events e
            JOIN therapeutic_assessment_authorizations a ON a.id = e.authorization_id
            WHERE e.actor_id = ? AND e.idempotency_key = ?
            """,
            (str(actor["id"]), key),
        ).fetchone()
        if replay is not None:
            return _present(row_to_dict(replay)), 200
        target = conn.execute("SELECT role, status FROM users WHERE id = ?", (user_id,)).fetchone()
        supervisor = conn.execute("SELECT role, status FROM users WHERE id = ?", (supervisor_id,)).fetchone()
        if target is None or str(target["role"]) not in FORMAL_ROLES or str(target["status"]) != "active":
            raise TherapeuticAssessmentError("validation_error", "授权对象必须是有效研究角色。", 422)
        if supervisor is None or str(supervisor["role"]) not in REVIEW_ROLES or str(supervisor["status"]) != "active":
            raise TherapeuticAssessmentError("validation_error", "督导者必须是有效督导或管理员。", 422)
        normalized_scope = _normalize_scope(conn, scope)
        authorization_id = new_id("ta_authz")
        timestamp = now_iso()
        conn.execute(
            """
            INSERT INTO therapeutic_assessment_authorizations (
                id, user_id, competency_level, task_code, scope_json,
                supervisor_user_id, evidence_ref, starts_at, expires_at,
                status, version, granted_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', 1, ?, ?, ?)
            """,
            (
                authorization_id,
                user_id,
                level,
                task_code,
                json_dumps(normalized_scope),
                supervisor_id,
                evidence_ref,
                starts_at,
                expires_at,
                str(actor["id"]),
                timestamp,
                timestamp,
            ),
        )
        conn.execute(
            """
            INSERT INTO therapeutic_assessment_authorization_events (
                id, authorization_id, actor_id, action, before_version,
                after_version, reason, idempotency_key, created_at
            ) VALUES (?, ?, ?, 'granted', NULL, 1, ?, ?, ?)
            """,
            (new_id("ta_authz_evt"), authorization_id, str(actor["id"]), evidence_ref, key, timestamp),
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_authorization_granted",
            str(actor["id"]),
            "therapeutic_assessment_authorization",
            authorization_id,
            {"user_id": user_id, "competency_level": level, "task_code": task_code},
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM therapeutic_assessment_authorizations WHERE id = ?",
            (authorization_id,),
        ).fetchone()
        return _present(row_to_dict(row)), 201


def revoke_authorization(
    actor: dict,
    authorization_id: str,
    payload: dict,
    idempotency_key: str,
) -> dict:
    key = _idempotency(idempotency_key)
    if str(actor.get("role") or "") not in REVIEW_ROLES:
        raise TherapeuticAssessmentError("forbidden", "只有督导或管理员可以撤销任务授权。", 403)
    reason = str(payload.get("reason") or "").strip()
    expected = payload.get("expected_version")
    if not reason or not isinstance(expected, int):
        raise TherapeuticAssessmentError("validation_error", "撤销原因和expected_version不能为空。")
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM therapeutic_assessment_authorizations WHERE id = ?",
            (authorization_id,),
        ).fetchone()
        if row is None:
            raise TherapeuticAssessmentError("not_found", "没有找到该任务授权。", 404)
        item = row_to_dict(row)
        replay = conn.execute(
            "SELECT 1 FROM therapeutic_assessment_authorization_events WHERE actor_id = ? AND idempotency_key = ?",
            (str(actor["id"]), key),
        ).fetchone()
        if replay:
            return _present(item)
        if item["status"] != "active":
            raise TherapeuticAssessmentError("invalid_state", "该授权已不处于有效状态。", 409)
        if int(item["version"]) != expected:
            raise TherapeuticAssessmentError("version_conflict", "授权已变化，请重新读取。", 409)
        timestamp = now_iso()
        cursor = conn.execute(
            """
            UPDATE therapeutic_assessment_authorizations
            SET status = 'revoked', version = version + 1, revoked_by = ?,
                revoked_at = ?, revocation_reason = ?, updated_at = ?
            WHERE id = ? AND version = ?
            """,
            (str(actor["id"]), timestamp, reason, timestamp, authorization_id, expected),
        )
        if cursor.rowcount != 1:
            raise TherapeuticAssessmentError("version_conflict", "授权已变化，请重新读取。", 409)
        conn.execute(
            """
            INSERT INTO therapeutic_assessment_authorization_events (
                id, authorization_id, actor_id, action, before_version,
                after_version, reason, idempotency_key, created_at
            ) VALUES (?, ?, ?, 'revoked', ?, ?, ?, ?, ?)
            """,
            (new_id("ta_authz_evt"), authorization_id, str(actor["id"]), expected, expected + 1, reason, key, timestamp),
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_authorization_revoked",
            str(actor["id"]),
            "therapeutic_assessment_authorization",
            authorization_id,
            {"reason": reason},
        )
        conn.commit()
        return _present(
            row_to_dict(
                conn.execute(
                    "SELECT * FROM therapeutic_assessment_authorizations WHERE id = ?",
                    (authorization_id,),
                ).fetchone()
            )
        )


def list_authorizations(actor: dict, params: dict) -> dict:
    requested_user = str(params.get("user_id") or "").strip()
    role = str(actor.get("role") or "")
    if requested_user and requested_user != str(actor["id"]) and role not in REVIEW_ROLES:
        raise TherapeuticAssessmentError("forbidden", "只能查看自己的任务授权。", 403)
    user_id = requested_user or str(actor["id"])
    with get_connection() as conn:
        rows = rows_to_dicts(
            conn.execute(
                "SELECT * FROM therapeutic_assessment_authorizations WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        )
        write_audit_log(
            conn,
            "therapeutic_assessment_authorizations_viewed",
            str(actor["id"]),
            "user",
            user_id,
            {"count": len(rows)},
        )
        conn.commit()
    return {
        "items": [_present(row) for row in rows],
        "count": len(rows),
        "default_decision": "deny",
        "temporary_showcase_bypass_counts": False,
    }


def _scope_matches(scope: dict, case: dict) -> bool:
    case_ids = {str(item) for item in scope.get("case_ids") or []}
    complexities = {str(item) for item in scope.get("complexity_scopes") or []}
    readiness = {str(item) for item in scope.get("readiness_levels") or []}
    snapshots = scope.get("case_scope_snapshots")
    if isinstance(snapshots, dict) and str(case["id"]) in snapshots:
        snapshot = snapshots[str(case["id"])]
        if not isinstance(snapshot, dict) or (
            str(snapshot.get("complexity_scope") or "") != str(case["complexity_scope"])
            or str(snapshot.get("readiness_level") or "") != str(case["readiness_level"])
        ):
            return False
    return (
        (not case_ids or str(case["id"]) in case_ids)
        and (not complexities or str(case["complexity_scope"]) in complexities)
        and (not readiness or str(case["readiness_level"]) in readiness)
    )


def assert_task_authorized(conn, actor: dict, case: dict, task_code: str) -> dict:
    policy = _policy()
    required_level = policy["minimum_level"].get(task_code)
    if not required_level:
        raise TherapeuticAssessmentError("validation_error", "未知的胜任力任务代码。")
    user = conn.execute(
        "SELECT role, status FROM users WHERE id = ?",
        (str(actor["id"]),),
    ).fetchone()
    if user is None or str(user["status"]) != "active" or str(user["role"]) not in FORMAL_ROLES:
        raise TherapeuticAssessmentError(
            "competency_authorization_required",
            "当前账号已离岗、停用或不再属于正式研究角色，需要重新核验。",
            403,
        )
    timestamp = now_iso()
    rows = rows_to_dicts(
        conn.execute(
            """
            SELECT * FROM therapeutic_assessment_authorizations
            WHERE user_id = ? AND task_code = ? AND status = 'active'
              AND starts_at <= ? AND expires_at > ?
            ORDER BY competency_level DESC, expires_at DESC
            """,
            (str(actor["id"]), task_code, timestamp, timestamp),
        ).fetchall()
    )
    for row in rows:
        if LEVEL_RANK.get(str(row["competency_level"]), 0) < LEVEL_RANK[required_level]:
            continue
        if str(row["competency_level"]) == "T2" and (
            str(case["complexity_scope"]) not in set(policy["low_risk_scope"]["complexity_scopes"])
            or str(case["readiness_level"]) not in set(policy["low_risk_scope"]["readiness_levels"])
        ):
            continue
        scope = json_loads(row.get("scope_json"), {})
        if _scope_matches(scope, case):
            return _present(row)
    raise TherapeuticAssessmentError(
        "competency_authorization_required",
        "当前账号没有这项任务的有效授权，或授权范围/有效期不匹配。",
        403,
    )


def require_reauthorization_after_major_event(
    conn,
    case: dict,
    event_id: str,
    actor_id: str,
) -> int:
    timestamp = now_iso()
    rows = rows_to_dicts(
        conn.execute(
            """
            SELECT * FROM therapeutic_assessment_authorizations
            WHERE status = 'active' AND starts_at <= ? AND expires_at > ?
            """,
            (timestamp, timestamp),
        ).fetchall()
    )
    affected = [
        row for row in rows
        if _scope_matches(json_loads(row.get("scope_json"), {}), case)
    ]
    for row in affected:
        before = int(row["version"])
        conn.execute(
            """
            UPDATE therapeutic_assessment_authorizations
            SET status = 'review_required', version = version + 1,
                status_reason = 'major_incident_recheck',
                updated_at = ?
            WHERE id = ? AND version = ?
            """,
            (timestamp, row["id"], before),
        )
        conn.execute(
            """
            INSERT INTO therapeutic_assessment_authorization_events (
                id, authorization_id, actor_id, action, before_version,
                after_version, reason, idempotency_key, created_at
            ) VALUES (?, ?, ?, 'review_required', ?, ?, ?, ?, ?)
            """,
            (
                new_id("ta_authz_evt"),
                row["id"],
                actor_id,
                before,
                before + 1,
                f"major_incident:{event_id}",
                f"major-incident:{event_id}:{row['id']}",
                timestamp,
            ),
        )
    return len(affected)


def effective_authorization(actor: dict, params: dict) -> dict:
    case_id = str(params.get("case_id") or "").strip()
    task_code = str(params.get("task_code") or "").strip()
    if not case_id or not task_code:
        raise TherapeuticAssessmentError("validation_error", "case_id和task_code不能为空。")
    with get_connection() as conn:
        case = conn.execute(
            "SELECT * FROM therapeutic_assessment_cases WHERE id = ?",
            (case_id,),
        ).fetchone()
        if case is None:
            raise TherapeuticAssessmentError("not_found", "没有找到协作记录。", 404)
        try:
            authorization = assert_task_authorized(conn, actor, row_to_dict(case), task_code)
        except TherapeuticAssessmentError as exc:
            if exc.code != "competency_authorization_required":
                raise
            return {"authorized": False, "task_code": task_code, "reason": exc.message}
        return {
            "authorized": True,
            "task_code": task_code,
            "authorization_id": authorization["id"],
            "competency_level": authorization["competency_level"],
            "expires_at": authorization["expires_at"],
        }
