"""Canonical request hashing and database-backed idempotency helpers."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any


MAX_CANONICAL_BODY_BYTES = 64 * 1024
DEFAULT_IGNORED_FIELDS = frozenset({"client_submission_id", "nickname"})
SIDE_EFFECT_STATUSES = frozenset(
    {
        "pending",
        "committed",
        "computed",
        "not_required",
        "not_available",
        "externally_committed",
        "failed",
        "compensation_required",
        "compensated",
        "cancelled",
    }
)


class IdempotencyValidationError(ValueError):
    """A stable client-visible validation failure for idempotent writes."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def public_idempotent_resource(item: dict | None) -> dict | None:
    """Return an API-safe copy without the internal canonical request digest."""

    if item is None:
        return None
    public_item = dict(item)
    public_item.pop("request_hash", None)
    return public_item


class IdempotencyConflictError(ValueError):
    """The same actor/endpoint/key was already bound to another request."""

    code = "idempotency_conflict"


@dataclass(frozen=True)
class IdempotencyReservation:
    id: str
    created: bool
    actor_id: str
    endpoint: str
    idempotency_key: str
    request_hash: str
    resource_type: str
    resource_id: str
    response_status: int | None = None
    response: dict | None = None


def canonical_request_hash(
    *,
    actor_id: str,
    endpoint: str,
    version: str,
    payload: dict[str, Any],
    ignored_fields: set[str] | frozenset[str] = DEFAULT_IGNORED_FIELDS,
) -> str:
    """Hash one normalized request while binding its actor and API contract."""

    if not isinstance(payload, dict):
        raise IdempotencyValidationError(
            "invalid_idempotency_payload",
            "幂等请求内容必须是对象。",
        )
    normalized_payload = {
        key: _normalize(value, field_name=key)
        for key, value in payload.items()
        if key not in ignored_fields
    }
    canonical_body = _canonical_json(normalized_payload)
    if len(canonical_body.encode("utf-8")) > MAX_CANONICAL_BODY_BYTES:
        raise IdempotencyValidationError(
            "idempotency_payload_too_large",
            "幂等请求内容不能超过64 KiB。",
        )
    envelope = {
        "actor_id": str(actor_id),
        "endpoint": str(endpoint),
        "payload": normalized_payload,
        "version": str(version),
    }
    return hashlib.sha256(_canonical_json(envelope).encode("utf-8")).hexdigest()


def reserve_idempotency(
    conn,
    *,
    actor_id: str,
    endpoint: str,
    idempotency_key: str,
    request_hash: str,
    resource_type: str,
    resource_id: str,
) -> IdempotencyReservation:
    """Atomically reserve one key or replay the already committed winner."""

    key = str(idempotency_key or "").strip()
    if not key:
        raise IdempotencyValidationError("missing_idempotency_key", "提交标识不能为空。")
    if len(key) > 120:
        raise IdempotencyValidationError(
            "invalid_idempotency_key",
            "提交标识不能超过120个字符。",
        )
    record_id = f"idem_{uuid.uuid4().hex}"
    timestamp = _now_iso()
    try:
        conn.execute(
            """
            INSERT INTO core_idempotency_records (
                id, actor_id, endpoint, idempotency_key, request_hash,
                resource_type, resource_id, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'committed', ?, ?)
            """,
            (
                record_id,
                str(actor_id),
                str(endpoint),
                key,
                str(request_hash),
                str(resource_type),
                str(resource_id),
                timestamp,
                timestamp,
            ),
        )
        return IdempotencyReservation(
            record_id,
            True,
            str(actor_id),
            str(endpoint),
            key,
            str(request_hash),
            str(resource_type),
            str(resource_id),
            None,
            None,
        )
    except Exception as exc:
        if not _is_integrity_error(exc):
            raise
        existing = conn.execute(
            """
            SELECT * FROM core_idempotency_records
            WHERE actor_id = ? AND endpoint = ? AND idempotency_key = ?
            """,
            (str(actor_id), str(endpoint), key),
        ).fetchone()
        if existing is None:
            raise
        if str(existing["request_hash"]) != str(request_hash):
            raise IdempotencyConflictError("该提交标识已用于另一份请求。") from exc
        return IdempotencyReservation(
            str(existing["id"]),
            False,
            str(existing["actor_id"]),
            str(existing["endpoint"]),
            str(existing["idempotency_key"]),
            str(existing["request_hash"]),
            str(existing["resource_type"]),
            str(existing["resource_id"]),
            int(existing["response_status"]) if existing["response_status"] is not None else None,
            json.loads(existing["response_json"]) if existing["response_json"] else None,
        )


def store_idempotency_response(
    conn,
    *,
    idempotency_record_id: str,
    response: dict,
    response_status: int,
) -> None:
    conn.execute(
        """
        UPDATE core_idempotency_records
        SET response_json = ?, response_status = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            _canonical_json(response),
            int(response_status),
            _now_iso(),
            str(idempotency_record_id),
        ),
    )


def record_side_effect(
    conn,
    *,
    idempotency_record_id: str,
    effect_type: str,
    effect_key: str,
    status: str,
    external_reference: str | None = None,
    metadata: dict | None = None,
) -> bool:
    """Record one local or external effect once within the caller transaction."""

    _validate_side_effect_status(status)
    timestamp = _now_iso()
    try:
        conn.execute(
            """
            INSERT INTO core_side_effect_ledger (
                id, idempotency_record_id, effect_type, effect_key, status,
                external_reference, metadata_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"effect_{uuid.uuid4().hex}",
                str(idempotency_record_id),
                str(effect_type),
                str(effect_key),
                str(status),
                external_reference,
                _canonical_json(metadata or {}),
                timestamp,
                timestamp,
            ),
        )
        return True
    except Exception as exc:
        if not _is_integrity_error(exc):
            raise
        existing = conn.execute(
            """
            SELECT id FROM core_side_effect_ledger
            WHERE idempotency_record_id = ? AND effect_type = ? AND effect_key = ?
            """,
            (str(idempotency_record_id), str(effect_type), str(effect_key)),
        ).fetchone()
        if existing is None:
            raise
        return False


def update_side_effect_status(
    conn,
    *,
    idempotency_record_id: str,
    effect_type: str,
    effect_key: str,
    status: str,
    external_reference: str | None = None,
    metadata: dict | None = None,
) -> dict:
    """Update reconciliation state without pretending an external action vanished."""

    _validate_side_effect_status(status)
    row = conn.execute(
        """
        SELECT * FROM core_side_effect_ledger
        WHERE idempotency_record_id = ? AND effect_type = ? AND effect_key = ?
        """,
        (str(idempotency_record_id), str(effect_type), str(effect_key)),
    ).fetchone()
    if row is None:
        raise IdempotencyValidationError(
            "side_effect_not_found",
            "没有找到对应的副作用记录。",
        )
    current = str(row["status"])
    if current in {"externally_committed", "compensation_required"} and status not in {
        "externally_committed",
        "compensation_required",
        "compensated",
    }:
        raise IdempotencyValidationError(
            "external_side_effect_not_revertible",
            "外部动作已发生，只能登记补偿状态，不能标记为已回滚。",
        )
    if current == "compensated" and status != "compensated":
        raise IdempotencyValidationError(
            "side_effect_terminal_state",
            "已补偿的副作用状态不能回退。",
        )
    metadata_json = (
        _canonical_json(metadata)
        if metadata is not None
        else row["metadata_json"]
    )
    conn.execute(
        """
        UPDATE core_side_effect_ledger
        SET status = ?, external_reference = COALESCE(?, external_reference),
            metadata_json = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            status,
            external_reference,
            metadata_json,
            _now_iso(),
            row["id"],
        ),
    )
    updated = conn.execute(
        "SELECT * FROM core_side_effect_ledger WHERE id = ?",
        (row["id"],),
    ).fetchone()
    return dict(updated)


def _validate_side_effect_status(status: str) -> None:
    if status not in SIDE_EFFECT_STATUSES:
        raise IdempotencyValidationError(
            "invalid_side_effect_status",
            "副作用状态无效。",
        )


def _is_integrity_error(exc: Exception) -> bool:
    if isinstance(exc, sqlite3.IntegrityError):
        return True
    if exc.__class__.__name__ != "IntegrityError":
        return False
    args = getattr(exc, "args", ())
    return bool(args and args[0] in {1062, "1062"})


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _normalize(value: Any, *, field_name: str | None = None) -> Any:
    if isinstance(value, dict):
        return {
            key: _normalize(child, field_name=key)
            for key, child in sorted(value.items())
        }
    if isinstance(value, (list, tuple)):
        return [_normalize(child) for child in value]
    if isinstance(value, datetime):
        return _normalize_datetime(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str) and _is_time_field(field_name):
        return _normalize_time_string(value)
    return value


def _is_time_field(field_name: str | None) -> bool:
    if not field_name:
        return False
    return field_name in {"event_time", "start_date"} or field_name.endswith(
        ("_at", "_date")
    )


def _normalize_time_string(value: str) -> str:
    candidate = value.strip()
    if not candidate:
        return candidate
    if len(candidate) == 10:
        try:
            return date.fromisoformat(candidate).isoformat()
        except ValueError:
            return value
    try:
        parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError:
        return value
    return _normalize_datetime(parsed) if parsed.tzinfo is not None else parsed.isoformat()


def _normalize_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        return value.isoformat()
    normalized = value.astimezone(timezone.utc).isoformat()
    return normalized.replace("+00:00", "Z")
