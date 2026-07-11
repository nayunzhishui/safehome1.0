"""Privacy center endpoints for consent withdrawal and data requests."""

from flask import Blueprint, current_app, request

from database import get_connection, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log
from routes.consent import DEFAULT_CONSENT_VERSION, get_latest_consent
from routes.auth_utils import AuthError, auth_error_response, get_current_actor
from routes.utils import fail, ok

bp = Blueprint("privacy", __name__, url_prefix="/api/privacy")

RESEARCH_CONSENT_TYPES = {"anonymous_research", "research_authorization"}


def resolve_privacy_owner(requested_user_id: str | None) -> tuple[str, dict]:
    user_id = str(requested_user_id or "").strip()
    actor = get_current_actor(allow_legacy_admin=False)
    if actor is not None:
        if user_id and actor["id"] != user_id:
            raise AuthError("只能操作自己的隐私数据", status=403)
        return str(actor["id"]), actor
    if str(current_app.config.get("APP_ENV", "development")).lower() == "production":
        raise AuthError("隐私中心需要先登录", status=401)
    if not user_id:
        raise ValueError("请提供匿名 user_id")
    return user_id, {"id": user_id, "role": "anonymous", "source": "anonymous_trial"}


def _latest_consent_status(conn, user_id: str, consent_type: str) -> dict:
    latest = get_latest_consent(conn, user_id, consent_type)
    return {
        "user_id": user_id,
        "consent_type": consent_type,
        "agreed": bool(latest and latest.get("agreed")),
        "consent_version": latest.get("consent_version") if latest else None,
        "agreed_at": latest.get("agreed_at") if latest and latest.get("agreed") else None,
        "revoked_at": latest.get("revoked_at") if latest else None,
        "created_at": latest.get("created_at") if latest else None,
    }


def revoked_research_user_ids(conn) -> set[str]:
    rows = conn.execute(
        """
        SELECT * FROM consent_records
        WHERE consent_type IN (?, ?)
        ORDER BY user_id ASC, consent_type ASC, created_at DESC
        """,
        ("anonymous_research", "research_authorization"),
    ).fetchall()
    latest_by_key: dict[tuple[str, str], dict] = {}
    for row in rows:
        item = row_to_dict(row)
        key = (item["user_id"], item["consent_type"])
        if key not in latest_by_key:
            latest_by_key[key] = item
    return {user_id for (user_id, _), item in latest_by_key.items() if not item.get("agreed")}


def research_revoked_filter(conn, column: str = "user_id") -> tuple[str, list[str]]:
    revoked_ids = sorted(revoked_research_user_ids(conn))
    if not revoked_ids:
        return "", []
    placeholders = ",".join("?" for _ in revoked_ids)
    return f"{column} NOT IN ({placeholders})", revoked_ids


@bp.get("/consent-status")
def consent_status():
    try:
        user_id, _actor = resolve_privacy_owner(request.args.get("user_id"))
    except AuthError as exc:
        return auth_error_response(exc)
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)

    with get_connection() as conn:
        items = [
            _latest_consent_status(conn, user_id, consent_type)
            for consent_type in ["user_agreement", "privacy_policy", "non_diagnostic_notice", "anonymous_research", "research_authorization"]
        ]
    return ok({"user_id": user_id, "items": items})


@bp.post("/revoke-consent")
def revoke_consent():
    payload = request.get_json(silent=True) or {}
    try:
        user_id, actor = resolve_privacy_owner(payload.get("user_id"))
    except AuthError as exc:
        return auth_error_response(exc)
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)

    consent_type = str(payload.get("consent_type") or "anonymous_research").strip()
    if consent_type not in RESEARCH_CONSENT_TYPES:
        return fail("validation_error", "当前仅支持撤回匿名研究授权", status=400)

    timestamp = now_iso()
    record_id = new_id("consent")
    reason = str(payload.get("reason") or "用户主动撤回").strip()[:300]
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO consent_records (
                id, user_id, consent_type, consent_version, agreed,
                agreed_at, revoked_at, created_at
            )
            VALUES (?, ?, ?, ?, 0, ?, ?, ?)
            """,
            (record_id, user_id, consent_type, payload.get("consent_version") or DEFAULT_CONSENT_VERSION, timestamp, timestamp, timestamp),
        )
        write_audit_log(
            conn,
            action="privacy_revoke_consent",
            actor_id=actor["id"],
            target_type="consent",
            target_id=consent_type,
            metadata={"route": "/api/privacy/revoke-consent", "reason_length": len(reason)},
        )
        conn.commit()

    return ok(
        {
            "user_id": user_id,
            "consent_type": consent_type,
            "agreed": False,
            "revoked_at": timestamp,
        }
    )


@bp.post("/delete-my-data")
def delete_my_data():
    payload = request.get_json(silent=True) or {}
    try:
        user_id, actor = resolve_privacy_owner(payload.get("user_id"))
    except AuthError as exc:
        return auth_error_response(exc)
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)

    timestamp = now_iso()
    request_id = new_id("privacy")
    reason = str(payload.get("reason") or "").strip()[:500]
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO privacy_requests (
                id, user_id, request_type, reason, status,
                handled_by, handled_note, created_at, updated_at
            )
            VALUES (?, ?, 'delete_my_data', ?, 'pending', NULL, NULL, ?, ?)
            """,
            (request_id, user_id, reason or None, timestamp, timestamp),
        )
        write_audit_log(
            conn,
            action="privacy_delete_request",
            actor_id=actor["id"],
            target_type="privacy_request",
            target_id=request_id,
            metadata={"route": "/api/privacy/delete-my-data", "reason_length": len(reason)},
        )
        conn.commit()
        row = conn.execute("SELECT * FROM privacy_requests WHERE id = ?", (request_id,)).fetchone()
    return ok(row_to_dict(row), status=201)


def _count_for_user(conn, table: str, user_id: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) AS count FROM {table} WHERE user_id = ?", (user_id,)).fetchone()
    return int(row["count"]) if row else 0


@bp.get("/export-my-data")
def export_my_data():
    try:
        user_id, _actor = resolve_privacy_owner(request.args.get("user_id"))
    except AuthError as exc:
        return auth_error_response(exc)
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)

    with get_connection() as conn:
        consent_items = [
            _latest_consent_status(conn, user_id, consent_type)
            for consent_type in ["user_agreement", "privacy_policy", "non_diagnostic_notice", "anonymous_research", "research_authorization"]
        ]
        privacy_rows = conn.execute(
            """
            SELECT id, request_type, status, created_at, updated_at
            FROM privacy_requests
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        ).fetchall()
        summary = {
            "user_id": user_id,
            "counts": {
                "goals": _count_for_user(conn, "goals", user_id),
                "diaries": _count_for_user(conn, "emotion_diaries", user_id),
                "feedback": _count_for_user(conn, "feedback_results", user_id),
                "checkins": _count_for_user(conn, "checkins", user_id),
                "profiles": _count_for_user(conn, "student_profiles", user_id),
                "parent_assessments": _count_for_user(conn, "parent_assessment_submissions", user_id),
                "supervision": _count_for_user(conn, "supervision_requests", user_id),
            },
            "consent_status": consent_items,
            "privacy_requests": rows_to_dicts(privacy_rows),
            "boundary_notice": "该摘要不包含自由文本原文、联系方式、后台审计 metadata 或风险处置私密备注。",
        }
    return ok(summary)
