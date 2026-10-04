"""Family binding code generation and redemption rules."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from database import row_to_dict
from services.request_rate_limit_service import increment_db_limit


BIND_CODE_DIGITS = 10
BIND_CODE_VERSION = 1
UNAVAILABLE_MESSAGE = "绑定码无效或已不可使用，请向家长获取新码。"
RATE_LIMIT_MESSAGE = "请求过于频繁，请稍后再试。"
RATE_LIMIT_WINDOW_SECONDS = 15 * 60
RATE_LIMITS = {"account": 10, "device": 15, "ip": 30, "code": 5}


@dataclass(frozen=True)
class FamilyBindingError(Exception):
    code: str
    message: str
    status: int
    persist: bool = False


def generate_bind_code() -> str:
    return f"{secrets.randbelow(10**BIND_CODE_DIGITS):0{BIND_CODE_DIGITS}d}"


def hash_bind_code(bind_code: str, *, version: int = BIND_CODE_VERSION) -> str:
    pepper = (
        os.environ.get("FAMILY_BIND_CODE_PEPPER")
        or os.environ.get("SECRET_KEY")
        or "safehome-local-dev-secret"
    )
    message = f"family-bind:v{version}:{bind_code}".encode("utf-8")
    return hmac.new(pepper.encode("utf-8"), message, hashlib.sha256).hexdigest()


def redact_bind_code(bind_code: str) -> str:
    return f"redacted:{bind_code[-4:]}"


def _dimension_hash(dimension: str, value: str) -> str:
    return hash_bind_code(f"{dimension}:{value}")


def _window_key(timestamp: str) -> str:
    current = datetime.fromisoformat(timestamp)
    minute = current.minute - (current.minute % 15)
    return current.replace(minute=minute, second=0, microsecond=0).isoformat()


def _increment_db_limit(
    conn,
    *,
    dimension: str,
    dimension_hash: str,
    timestamp: str,
) -> int:
    return increment_db_limit(conn, dimension=dimension, dimension_hash=dimension_hash,
                              window_key=_window_key(timestamp), timestamp=timestamp)


def enforce_redemption_rate_limits(
    conn,
    *,
    actor_id: str,
    device_id: str,
    ip_address: str,
    bind_code: str,
    timestamp: str,
) -> None:
    values = {
        "account": actor_id,
        "device": device_id or f"actor:{actor_id}",
        "ip": ip_address or "unknown",
        "code": bind_code,
    }
    blocked = False
    try:
        for dimension, value in values.items():
            count = _increment_db_limit(
                conn, dimension=dimension, dimension_hash=_dimension_hash(dimension, value),
                timestamp=timestamp,
            )
            blocked = blocked or count > RATE_LIMITS[dimension]
    except Exception as exc:
        conn.rollback()
        raise FamilyBindingError(
            "family_binding_rate_limit_unavailable", "绑定保护暂时不可用，请稍后再试。", 503
        ) from exc

    if blocked:
        code_hash = hash_bind_code(bind_code)
        locked_until = (
            datetime.fromisoformat(timestamp) + timedelta(seconds=RATE_LIMIT_WINDOW_SECONDS)
        ).isoformat()
        conn.execute(
            """
            UPDATE family_links
            SET status = 'locked', locked_until = ?, lock_reason = 'rate_limit',
                updated_at = ?, version = version + 1
            WHERE bind_code_hash = ? AND status = 'pending'
            """,
            (locked_until, timestamp, code_hash),
        )
        raise FamilyBindingError("family_binding_rate_limited", RATE_LIMIT_MESSAGE, 429, persist=True)


def redeem_pending_link(conn, *, bind_code: str, student_user_id: str, timestamp: str) -> dict:
    if len(bind_code) != BIND_CODE_DIGITS or not bind_code.isdigit():
        raise FamilyBindingError(
            "bind_code_unavailable", UNAVAILABLE_MESSAGE, 400, persist=True
        )
    code_hash = hash_bind_code(bind_code)
    row = conn.execute(
        "SELECT * FROM family_links WHERE bind_code_hash = ? ORDER BY created_at DESC LIMIT 1",
        (code_hash,),
    ).fetchone()
    if (
        row is not None
        and row["status"] == "locked"
        and row["locked_until"]
        and datetime.fromisoformat(row["locked_until"]) <= datetime.fromisoformat(timestamp)
    ):
        conn.execute(
            """
            UPDATE family_links
            SET status = 'pending', locked_until = NULL, lock_reason = NULL,
                updated_at = ?, version = version + 1
            WHERE id = ? AND status = 'locked' AND version = ?
            """,
            (timestamp, row["id"], row["version"]),
        )
        row = conn.execute("SELECT * FROM family_links WHERE id = ?", (row["id"],)).fetchone()
    if row is None or row["status"] != "pending":
        raise FamilyBindingError(
            "bind_code_unavailable", UNAVAILABLE_MESSAGE, 400, persist=True
        )
    if row["expires_at"] and datetime.fromisoformat(row["expires_at"]) <= datetime.fromisoformat(timestamp):
        conn.execute(
            """
            UPDATE family_links
            SET status = 'expired', updated_at = ?, version = version + 1
            WHERE id = ? AND status = 'pending' AND version = ?
            """,
            (timestamp, row["id"], row["version"]),
        )
        raise FamilyBindingError("bind_code_unavailable", UNAVAILABLE_MESSAGE, 400, persist=True)
    result = conn.execute(
        """
        UPDATE family_links
        SET student_user_id = ?, status = 'consumed',
            attempt_count = attempt_count + 1, last_attempt_at = ?,
            confirmed_at = ?, updated_at = ?, version = version + 1
        WHERE id = ? AND status = 'pending' AND version = ?
          AND (expires_at IS NULL OR expires_at > ?)
          AND (locked_until IS NULL OR locked_until <= ?)
        """,
        (
            student_user_id,
            timestamp,
            timestamp,
            timestamp,
            row["id"],
            row["version"],
            timestamp,
            timestamp,
        ),
    )
    if result.rowcount != 1:
        raise FamilyBindingError(
            "bind_code_unavailable", UNAVAILABLE_MESSAGE, 400, persist=True
        )
    return row_to_dict(
        conn.execute("SELECT * FROM family_links WHERE id = ?", (row["id"],)).fetchone()
    )
