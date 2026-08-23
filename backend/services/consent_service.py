"""Immutable consent events and separate administrative annotations."""

from __future__ import annotations

import re

from database import new_id, now_iso, row_to_dict, write_audit_log


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ANNOTATION_TYPES = {"administrative_annotation", "error_correction"}
VERIFIED_PARTICIPANT_SOURCES = {"participant_self", "embedded_parent_assessment"}


class ConsentError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


def latest_consent_event(conn, subject_id: str, consent_type: str) -> dict | None:
    row = conn.execute(
        """
        SELECT * FROM consent_records
        WHERE COALESCE(subject_id, user_id) = ? AND consent_type = ?
        ORDER BY event_version DESC, created_at DESC, id DESC
        LIMIT 1
        """,
        (subject_id, consent_type),
    ).fetchone()
    return row_to_dict(row)


def is_verified_participant_event(event: dict | None, subject_id: str | None = None) -> bool:
    if not event:
        return False
    resolved_subject = str(event.get("subject_id") or "")
    return (
        bool(resolved_subject)
        and event.get("actor_id") == resolved_subject
        and event.get("source") in VERIFIED_PARTICIPANT_SOURCES
        and event.get("event_type") in {"self_agreed", "self_withdrawn"}
        and (subject_id is None or resolved_subject == subject_id)
    )


def _same_contract(
    latest: dict,
    *,
    actor_id: str,
    subject_id: str,
    source: str,
    agreed: bool,
    consent_version: str,
    purpose: str,
    processor: str,
    text_hash: str | None,
) -> bool:
    return (
        latest.get("actor_id") == actor_id
        and latest.get("subject_id") == subject_id
        and latest.get("source") == source
        and bool(latest.get("agreed")) == agreed
        and latest.get("consent_version") == consent_version
        and (latest.get("purpose") or latest.get("consent_type")) == purpose
        and (latest.get("processor") or "safehome") == processor
        and latest.get("text_hash") == text_hash
    )


def append_consent_event(
    conn,
    *,
    actor_id: str,
    subject_id: str,
    consent_type: str,
    consent_version: str,
    agreed: bool,
    purpose: str | None = None,
    processor: str = "safehome",
    text_hash: str | None = None,
    source: str,
    reason: str | None = None,
    evidence_ref: str | None = None,
    event_type: str | None = None,
    expected_latest_id: str | None = None,
    require_latest_guard: bool = False,
) -> tuple[dict, bool]:
    purpose = str(purpose or consent_type).strip()
    processor = str(processor or "safehome").strip()
    text_hash = str(text_hash).strip().lower() if text_hash else None
    if not consent_version or len(consent_version) > 120:
        raise ConsentError("validation_error", "consent_version 无效")
    if not purpose or len(purpose) > 120:
        raise ConsentError("validation_error", "purpose 无效")
    if not processor or len(processor) > 120:
        raise ConsentError("validation_error", "processor 无效")
    if text_hash and not SHA256_RE.fullmatch(text_hash):
        raise ConsentError("validation_error", "text_hash 必须是 SHA-256 十六进制值")

    latest = latest_consent_event(conn, subject_id, consent_type)
    if latest and _same_contract(
        latest,
        actor_id=actor_id,
        subject_id=subject_id,
        source=source,
        agreed=agreed,
        consent_version=consent_version,
        purpose=purpose,
        processor=processor,
        text_hash=text_hash,
    ):
        return latest, False
    if expected_latest_id and (not latest or latest.get("id") != expected_latest_id):
        raise ConsentError("consent_version_conflict", "同意状态已变化，请刷新后重试。", 409)
    if require_latest_guard and latest and not expected_latest_id:
        raise ConsentError("consent_version_conflict", "变更同意状态需要提供 expected_latest_id。", 409)

    timestamp = now_iso()
    record_id = new_id("consent")
    resolved_event_type = event_type or ("self_agreed" if agreed else "self_withdrawn")
    resolved_reason = str(reason or "").strip()[:300] or (None if agreed else "用户主动撤回")
    resolved_evidence = str(evidence_ref or "").strip()[:300] or None
    event_version = int(latest.get("event_version") or 0) + 1 if latest else 1
    try:
        conn.execute(
            """
            INSERT INTO consent_records (
                id, user_id, actor_id, subject_id, consent_type, consent_version,
                purpose, processor, text_hash, source, reason, evidence_ref,
                supersedes_id, event_type, event_version, agreed, agreed_at,
                revoked_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                subject_id,
                actor_id,
                subject_id,
                consent_type,
                consent_version,
                purpose,
                processor,
                text_hash,
                source,
                resolved_reason,
                resolved_evidence,
                latest.get("id") if latest else None,
                resolved_event_type,
                event_version,
                1 if agreed else 0,
                timestamp,
                None if agreed else timestamp,
                timestamp,
            ),
        )
    except Exception as exc:
        message = str(exc).lower()
        if "idx_consent_event_version" not in message and not (
            "consent_records.subject_id" in message
            and "consent_records.consent_type" in message
            and "consent_records.event_version" in message
        ):
            raise
        concurrent = latest_consent_event(conn, subject_id, consent_type)
        if concurrent and _same_contract(
            concurrent,
            actor_id=actor_id,
            subject_id=subject_id,
            source=source,
            agreed=agreed,
            consent_version=consent_version,
            purpose=purpose,
            processor=processor,
            text_hash=text_hash,
        ):
            return concurrent, False
        raise ConsentError(
            "consent_version_conflict", "同意状态已变化，请刷新后重试。", 409
        ) from exc
    write_audit_log(
        conn,
        action="consent_event_recorded",
        actor_id=actor_id,
        target_type="consent_record",
        target_id=record_id,
        metadata={
            "subject_id": subject_id,
            "consent_type": consent_type,
            "consent_version": consent_version,
            "purpose": purpose,
            "processor": processor,
            "event_type": resolved_event_type,
            "source": source,
            "supersedes_id": latest.get("id") if latest else None,
        },
    )
    row = conn.execute("SELECT * FROM consent_records WHERE id = ?", (record_id,)).fetchone()
    return row_to_dict(row), True


def has_active_consent(
    conn,
    subject_id: str,
    consent_type: str,
    *,
    consent_version: str,
    purpose: str,
    processor: str,
    require_verified_self: bool = True,
) -> bool:
    latest = latest_consent_event(conn, subject_id, consent_type)
    if not latest or not bool(latest.get("agreed")):
        return False
    if require_verified_self and (
        latest.get("source") != "participant_self"
        or latest.get("actor_id") != subject_id
        or latest.get("subject_id") != subject_id
    ):
        return False
    return (
        latest.get("consent_version") == consent_version
        and (latest.get("purpose") or latest.get("consent_type")) == purpose
        and (latest.get("processor") or "safehome") == processor
    )


def create_consent_annotation(
    conn,
    *,
    actor_id: str,
    consent_record_id: str,
    annotation_type: str,
    reason: str,
    evidence_ref: str,
    supersedes_id: str | None = None,
) -> dict:
    if annotation_type not in ANNOTATION_TYPES:
        raise ConsentError("validation_error", "annotation_type 不在支持范围内")
    reason = str(reason or "").strip()[:500]
    evidence_ref = str(evidence_ref or "").strip()[:300]
    if not reason or not evidence_ref:
        raise ConsentError("validation_error", "行政注释必须提供 reason 和 evidence_ref")
    consent = row_to_dict(
        conn.execute(
            "SELECT * FROM consent_records WHERE id = ?", (consent_record_id,)
        ).fetchone()
    )
    if not consent:
        raise ConsentError("not_found", "没有找到该同意事件。", 404)
    if supersedes_id:
        previous = row_to_dict(
            conn.execute(
                "SELECT * FROM consent_record_annotations WHERE id = ? AND consent_record_id = ?",
                (supersedes_id, consent_record_id),
            ).fetchone()
        )
        if not previous:
            raise ConsentError("annotation_version_conflict", "被替代的注释不存在。", 409)
    annotation_id = new_id("consent_annotation")
    timestamp = now_iso()
    subject_id = str(consent.get("subject_id") or consent.get("user_id"))
    conn.execute(
        """
        INSERT INTO consent_record_annotations (
            id, consent_record_id, actor_id, subject_id, annotation_type,
            reason, evidence_ref, supersedes_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            annotation_id,
            consent_record_id,
            actor_id,
            subject_id,
            annotation_type,
            reason,
            evidence_ref,
            supersedes_id,
            timestamp,
        ),
    )
    write_audit_log(
        conn,
        action="consent_annotation_created",
        actor_id=actor_id,
        target_type="consent_record_annotation",
        target_id=annotation_id,
        metadata={
            "subject_id": subject_id,
            "consent_record_id": consent_record_id,
            "annotation_type": annotation_type,
            "evidence_ref": evidence_ref,
            "supersedes_id": supersedes_id,
        },
    )
    return row_to_dict(
        conn.execute(
            "SELECT * FROM consent_record_annotations WHERE id = ?",
            (annotation_id,),
        ).fetchone()
    )
