"""Consent-aware, idempotent WeChat subscription notification service."""

import json
from datetime import date, datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import current_app

from database import get_connection, json_loads, new_id, now_iso, row_to_dict, rows_to_dicts
from services.training_schedule_service import assignment_schedule, current_local_day


CHANNEL = "wechat_subscribe"
TRAINING_DUE = "training_due"
ALLOWED_DECISIONS = {"accept": "accepted", "reject": "rejected", "ban": "banned"}
_TOKEN_CACHE = {"appid": "", "value": "", "expires_at": 0.0}

REAUTHORIZATION_ERROR_CODES = {"43101", "user_refuse", "subscription_refused"}
TEMPLATE_ERROR_CODES = {"40037", "template_invalid", "subscription_fields_invalid", "subscription_fields_missing"}
PERMANENT_ERROR_CODES = {"40003", "invalid_openid", "invalid_recipient"}


def classify_notification_error(error_code: str) -> str:
    code = str(error_code or "").strip().lower()
    if code in REAUTHORIZATION_ERROR_CODES:
        return "reauthorization_required"
    if code in TEMPLATE_ERROR_CODES:
        return "template_error"
    if code in PERMANENT_ERROR_CODES:
        return "permanent_failure"
    return "retryable"


def _next_retry_at(attempt_count: int) -> str:
    delay_minutes = min(5 * (2 ** max(attempt_count - 1, 0)), 24 * 60)
    return (datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)).isoformat()


class NotificationError(RuntimeError):
    def __init__(self, code: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


def _config(name: str, default=None):
    return current_app.config.get(name, default)


def subscription_capability() -> dict:
    template_id = str(_config("WECHAT_TRAINING_DUE_TEMPLATE_ID", "") or "").strip()
    mode = str(_config("WECHAT_SUBSCRIBE_MODE", "once") or "once")
    return {
        "available": bool(template_id),
        "notification_type": TRAINING_DUE,
        "template_id": template_id or None,
        "subscription_mode": mode,
        "send_enabled": bool(_config("WECHAT_SUBSCRIBE_SEND_ENABLED", False)),
        "prompt_timing": "after_cadence_saved",
        "notice": "微信提醒需要单独授权；拒绝或关闭不会影响训练卡使用。",
    }


def get_preference(user_id: str) -> dict | None:
    template_id = str(_config("WECHAT_TRAINING_DUE_TEMPLATE_ID", "") or "").strip()
    if not template_id:
        return None
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, channel, notification_type, template_id, subscription_mode,
                   consent_status, consented_at, last_prompted_at, revoked_at, updated_at
            FROM notification_preferences
            WHERE user_id = ? AND channel = ? AND notification_type = ? AND template_id = ?
            LIMIT 1
            """,
            (user_id, CHANNEL, TRAINING_DUE, template_id),
        ).fetchone()
    return row_to_dict(row)


def record_consent(user_id: str, template_id: str, decision: str, source: str = "miniprogram") -> dict:
    configured_id = str(_config("WECHAT_TRAINING_DUE_TEMPLATE_ID", "") or "").strip()
    if not configured_id:
        raise NotificationError("subscription_template_unavailable", "订阅消息模板尚未配置", 503)
    if template_id != configured_id:
        raise NotificationError("subscription_template_mismatch", "订阅消息模板与当前配置不一致", 400)
    status = ALLOWED_DECISIONS.get(str(decision or "").strip().lower())
    if not status:
        raise NotificationError("invalid_subscription_decision", "授权结果不在允许范围内", 400)
    timestamp = now_iso()
    preference_id = new_id("notify_pref")
    mode = str(_config("WECHAT_SUBSCRIBE_MODE", "once") or "once")
    consented_at = timestamp if status == "accepted" else None
    revoked_at = timestamp if status in {"rejected", "banned"} else None
    with get_connection() as conn:
        existing = conn.execute(
            """
            SELECT id FROM notification_preferences
            WHERE user_id = ? AND channel = ? AND notification_type = ? AND template_id = ?
            LIMIT 1
            """,
            (user_id, CHANNEL, TRAINING_DUE, template_id),
        ).fetchone()
        if existing:
            preference_id = existing["id"]
            conn.execute(
                """
                UPDATE notification_preferences
                SET subscription_mode = ?, consent_status = ?, consent_source = ?, consented_at = ?,
                    last_prompted_at = ?, revoked_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (mode, status, source, consented_at, timestamp, revoked_at, timestamp, preference_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO notification_preferences (
                    id, user_id, channel, notification_type, template_id, subscription_mode,
                    consent_status, consent_source, consented_at, last_prompted_at, revoked_at,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    preference_id, user_id, CHANNEL, TRAINING_DUE, template_id, mode,
                    status, source, consented_at, timestamp, revoked_at, timestamp, timestamp,
                ),
            )
        from database import write_audit_log

        write_audit_log(
            conn,
            action="wechat_subscription_consent_recorded",
            actor_id=user_id,
            target_type="notification_preference",
            target_id=preference_id,
            metadata={"decision": status, "notification_type": TRAINING_DUE, "subscription_mode": mode},
        )
        conn.commit()
    return get_preference(user_id) or {}


def _latest_assignments_and_checkins() -> list[dict]:
    template_id = str(_config("WECHAT_TRAINING_DUE_TEMPLATE_ID", "") or "").strip()
    if not template_id:
        return []
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT r.id, r.user_id, r.data_json, r.updated_at, u.wechat_openid,
                   p.id AS preference_id, p.template_id, p.subscription_mode, p.consent_status,
                   (SELECT MAX(c.created_at) FROM checkins c
                    WHERE c.user_id = r.user_id AND c.completed = 1) AS latest_completed_at
            FROM records r
            JOIN users u ON u.id = r.user_id AND u.status = 'active'
            JOIN notification_preferences p ON p.user_id = r.user_id
                AND p.channel = ? AND p.notification_type = ?
            WHERE r.module_type = 'training_plan_assignment'
              AND r.source_id = 'current'
              AND p.consent_status = 'accepted'
              AND p.template_id = ?
            ORDER BY r.updated_at DESC
            """,
            (CHANNEL, TRAINING_DUE, template_id),
        ).fetchall()
    return rows_to_dicts(rows)


def due_candidates(run_day: date | None = None) -> list[dict]:
    current_day = run_day or current_local_day()
    candidates = []
    seen_users = set()
    for row in _latest_assignments_and_checkins():
        user_id = row["user_id"]
        if user_id in seen_users:
            continue
        seen_users.add(user_id)
        assignment = json_loads(row.get("data_json"), {})
        schedule = assignment_schedule(assignment, row.get("latest_completed_at"), today=current_day)
        if not schedule or not schedule.get("is_due_today") or not row.get("wechat_openid"):
            continue
        schedule_key = current_day.isoformat()
        candidates.append(
            {
                "user_id": user_id,
                "openid": row["wechat_openid"],
                "preference_id": row["preference_id"],
                "template_id": row["template_id"],
                "subscription_mode": row["subscription_mode"],
                "schedule_key": schedule_key,
                "idempotency_key": f"{TRAINING_DUE}:{user_id}:{schedule_key}:{row['template_id']}",
                "scheduled_for": schedule.get("next_practice_date") or schedule_key,
            }
        )
    return candidates


def _template_data() -> dict:
    raw = str(_config("WECHAT_TRAINING_DUE_TEMPLATE_FIELDS", "") or "").strip()
    try:
        mapping = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise NotificationError("subscription_fields_invalid", "订阅模板字段配置不是有效 JSON", 503) from exc
    if not isinstance(mapping, dict) or not mapping:
        raise NotificationError("subscription_fields_missing", "订阅模板字段尚未配置", 503)
    values = {
        "title": "今天可以练一次",
        "time": current_local_day().isoformat(),
        "note": "选一张最容易完成的训练卡即可",
    }
    data = {}
    for keyword, semantic in mapping.items():
        if semantic not in values:
            raise NotificationError("subscription_fields_invalid", "订阅模板字段包含未知语义", 503)
        data[str(keyword)] = {"value": values[semantic]}
    return data


def _wechat_json(url: str, payload: dict | None = None) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    request = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST" if body else "GET")
    try:
        with urlopen(request, timeout=8) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise NotificationError("wechat_service_unavailable", "微信通知服务暂时没有响应", 502) from exc


def _access_token() -> str:
    import time

    appid = str(_config("WECHAT_APPID", "") or "")
    if (
        _TOKEN_CACHE["appid"] == appid
        and _TOKEN_CACHE["value"]
        and time.time() < float(_TOKEN_CACHE["expires_at"])
    ):
        return str(_TOKEN_CACHE["value"])
    secret = str(_config("WECHAT_SECRET", "") or "")
    result = _wechat_json(
        "https://api.weixin.qq.com/cgi-bin/token?" + urlencode({"grant_type": "client_credential", "appid": appid, "secret": secret})
    )
    token = str(result.get("access_token") or "")
    if not token:
        raise NotificationError("wechat_access_token_failed", "微信通知凭证获取失败", 502)
    _TOKEN_CACHE.update({"appid": appid, "value": token, "expires_at": time.time() + max(int(result.get("expires_in") or 7200) - 300, 60)})
    return token


def send_wechat_subscription(candidate: dict) -> dict:
    token = _access_token()
    return _wechat_json(
        "https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token=" + token,
        {
            "touser": candidate["openid"],
            "template_id": candidate["template_id"],
            "page": str(_config("WECHAT_TRAINING_DUE_PAGE", "pages/personalized-plan/index")),
            "miniprogram_state": "formal" if str(_config("APP_ENV", "development")).lower() == "production" else "trial",
            "lang": "zh_CN",
            "data": _template_data(),
        },
    )


def run_due_notifications(*, dry_run: bool = True, run_day: date | None = None) -> dict:
    candidates = due_candidates(run_day)
    if dry_run:
        return {"dry_run": True, "candidate_count": len(candidates), "sent": 0, "skipped_duplicate": 0, "failed": 0, "deferred": 0, "dead_lettered": 0, "requires_action": 0}
    if not bool(_config("WECHAT_SUBSCRIBE_SEND_ENABLED", False)):
        raise NotificationError("subscription_send_disabled", "微信订阅消息真实发送开关尚未开启", 503)
    sent = skipped = failed = deferred = dead_lettered = requires_action = 0
    for candidate in candidates:
        timestamp = now_iso()
        with get_connection() as conn:
            existing = conn.execute(
                """
                SELECT id, status, attempt_count, retry_category, next_attempt_at,
                       max_attempts, dead_lettered_at, error_code
                FROM notification_deliveries WHERE idempotency_key = ? LIMIT 1
                """,
                (candidate["idempotency_key"],),
            ).fetchone()
            if existing:
                if existing["status"] != "failed":
                    skipped += 1
                    continue
                category = str(existing["retry_category"] or classify_notification_error(str(existing["error_code"] or "")))
                if category != "retryable":
                    requires_action += 1
                    continue
                max_attempts = int(existing["max_attempts"] or 3)
                if existing["dead_lettered_at"] or int(existing["attempt_count"] or 0) >= max_attempts:
                    if not existing["dead_lettered_at"]:
                        conn.execute(
                            "UPDATE notification_deliveries SET dead_lettered_at = ?, next_attempt_at = NULL, updated_at = ? WHERE id = ?",
                            (timestamp, timestamp, existing["id"]),
                        )
                        conn.commit()
                    dead_lettered += 1
                    continue
                if existing["next_attempt_at"] and str(existing["next_attempt_at"]) > timestamp:
                    deferred += 1
                    continue
                delivery_id = existing["id"]
                conn.execute(
                    """
                    UPDATE notification_deliveries
                    SET status = 'sending', attempt_count = attempt_count + 1,
                        last_attempt_at = ?, error_code = NULL, error_message = NULL, updated_at = ?
                    WHERE id = ?
                    """,
                    (timestamp, timestamp, delivery_id),
                )
            else:
                delivery_id = new_id("notify_delivery")
                conn.execute(
                    """
                    INSERT INTO notification_deliveries (
                        id, user_id, preference_id, notification_type, template_id, schedule_key,
                        idempotency_key, status, attempt_count, scheduled_for, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'sending', 1, ?, ?, ?)
                    """,
                    (
                        delivery_id, candidate["user_id"], candidate["preference_id"], TRAINING_DUE,
                        candidate["template_id"], candidate["schedule_key"], candidate["idempotency_key"],
                        candidate["scheduled_for"], timestamp, timestamp,
                    ),
                )
            conn.commit()
        try:
            result = send_wechat_subscription(candidate)
            errcode = int(result.get("errcode") or 0)
            if errcode != 0:
                raise NotificationError(str(errcode), str(result.get("errmsg") or "微信发送失败"), 502)
            with get_connection() as conn:
                conn.execute(
                    """
                    UPDATE notification_deliveries
                    SET status = 'sent', sent_at = ?, provider_message_id = ?, error_code = NULL,
                        error_message = NULL, retry_category = NULL, next_attempt_at = NULL,
                        dead_lettered_at = NULL, updated_at = ?
                    WHERE id = ?
                    """,
                    (now_iso(), str(result.get("msgid") or "") or None, now_iso(), delivery_id),
                )
                if candidate["subscription_mode"] == "once":
                    conn.execute(
                        "UPDATE notification_preferences SET consent_status = 'consumed', updated_at = ? WHERE id = ?",
                        (now_iso(), candidate["preference_id"]),
                    )
                conn.commit()
            sent += 1
        except NotificationError as exc:
            with get_connection() as conn:
                delivery = conn.execute(
                    "SELECT attempt_count, max_attempts FROM notification_deliveries WHERE id = ?",
                    (delivery_id,),
                ).fetchone()
                attempt_count = int(delivery["attempt_count"] or 1)
                max_attempts = int(delivery["max_attempts"] or 3)
                category = classify_notification_error(exc.code)
                exhausted = category == "retryable" and attempt_count >= max_attempts
                conn.execute(
                    """
                    UPDATE notification_deliveries
                    SET status = 'failed', error_code = ?, error_message = ?, retry_category = ?,
                        next_attempt_at = ?, dead_lettered_at = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        exc.code,
                        str(exc)[:200],
                        category,
                        _next_retry_at(attempt_count) if category == "retryable" and not exhausted else None,
                        now_iso() if exhausted else None,
                        now_iso(),
                        delivery_id,
                    ),
                )
                if category == "reauthorization_required":
                    conn.execute(
                        "UPDATE notification_preferences SET consent_status = 'rejected', revoked_at = ?, updated_at = ? WHERE id = ?",
                        (now_iso(), now_iso(), candidate["preference_id"]),
                    )
                conn.commit()
            failed += 1
    return {
        "dry_run": False,
        "candidate_count": len(candidates),
        "sent": sent,
        "skipped_duplicate": skipped,
        "failed": failed,
        "deferred": deferred,
        "dead_lettered": dead_lettered,
        "requires_action": requires_action,
    }
