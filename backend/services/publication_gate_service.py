"""Server-side five-gate pipeline for participant-facing publications."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from flask import current_app

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


class PublicationGateError(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        status: int = 409,
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details or {}


def _policy() -> dict:
    path = current_app.config["CONTENT_DIR"] / "publication_gate_policy.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = [_text(item) for item in value]
        return "\n".join(part for part in parts if part)
    if isinstance(value, dict):
        parts = [_text(item) for item in value.values()]
        return "\n".join(part for part in parts if part)
    return ""


def _present(row: dict) -> dict:
    item = dict(row)
    for source, target, default in (
        ("content_json", "content", {}),
        ("source_refs_json", "source_refs", []),
        ("gate_summary_json", "gate_summary", {}),
        ("diff_json", "diff", {}),
    ):
        item[target] = json_loads(item.pop(source, None), default)
    item["multi_party"] = bool(item.get("multi_party"))
    return item


def _gate_results(
    actor: dict,
    channel_policy: dict,
    payload: dict,
    policy: dict,
) -> list[dict]:
    content_text = _text(payload.get("content"))
    source_refs = payload.get("source_refs")
    source_refs = source_refs if isinstance(source_refs, list) else []
    role = str(actor.get("role") or "")
    reviewer_id = str(payload.get("reviewer_id") or "").strip()
    author_id = str(payload.get("author_id") or "").strip()
    risk_level = str(payload.get("risk_level") or "low")
    multi_party = payload.get("multi_party") is True
    blocked_phrase = next(
        (phrase for phrase in policy["blocked_phrases"] if phrase in content_text),
        None,
    )
    human_review_required = bool(channel_policy.get("human_review_required"))
    if multi_party or risk_level == "high":
        human_review_required = True
    content_value = payload.get("content")
    channel = str(payload.get("channel") or "")
    if channel == "researcher_message":
        minimum_content_ok = (
            isinstance(content_value, dict)
            and bool(_text(content_value.get("title")))
            and bool(_text(content_value.get("body")))
        )
    elif channel == "therapeutic_feedback":
        minimum_content_ok = (
            isinstance(content_value, dict)
            and bool(_text(content_value.get("title")))
            and bool(_text(content_value.get("participant_content")))
            and bool(_text(content_value.get("next_step")))
        )
    else:
        minimum_content_ok = bool(content_text)

    checks = {
        "minimum_input": (
            minimum_content_ok
            and len(content_text) <= 12000
            and bool(str(payload.get("subject_type") or "").strip())
            and bool(str(payload.get("subject_id") or "").strip())
            and bool(str(payload.get("recipient_user_id") or "").strip())
        ),
        "permission": (
            payload.get("permission_granted") is True
            and payload.get("consent_active") is True
            and payload.get("recipient_matches_scope") is True
            and role in set(channel_policy.get("allowed_publisher_roles") or [])
        ),
        "source": (
            (bool(source_refs) or not channel_policy.get("source_required"))
            and payload.get("source_authorized") is True
        ),
        "language": payload.get("language_checked") is True and blocked_phrase is None,
        "responsibility": (
            bool(str(payload.get("responsible_role") or "").strip())
            and str(payload.get("publisher_id") or "") == str(actor.get("id") or "")
            and (
                not human_review_required
                or (
                    payload.get("human_reviewed") is True
                    and bool(reviewer_id)
                    and (not author_id or reviewer_id != author_id)
                )
            )
            and (
                risk_level != "high"
                or (
                    role in set(policy["high_risk"]["reviewer_roles"])
                    and payload.get("high_risk_reviewed") is True
                    and payload.get("ordinary_training_path") is not True
                )
            )
            and (
                not multi_party
                or (
                    payload.get("multi_party_authorized") is True
                    and payload.get("human_reviewed") is True
                )
            )
            and (
                payload.get("channel") != "ai_candidate"
                or (
                    payload.get("safety_checked") is True
                    and payload.get("formal_feedback_write_allowed") is False
                )
            )
        ),
    }
    reasons = {
        "minimum_input": "minimum_input_incomplete",
        "permission": "permission_or_scope_denied",
        "source": "source_missing_or_unauthorized",
        "language": (
            "language_boundary_failed" if blocked_phrase else "language_check_missing"
        ),
        "responsibility": "responsibility_chain_incomplete",
    }
    return [
        {
            "gate_name": gate,
            "decision": "passed" if checks[gate] else "blocked",
            "reason_code": None if checks[gate] else reasons[gate],
            "details": {
                "blocked_phrase": blocked_phrase if gate == "language" else None,
                "human_review_required": (
                    human_review_required if gate == "responsibility" else None
                ),
                "temporary_showcase_bypass_accepted": False,
            },
        }
        for gate in policy["five_gates"]
    ]


def _event(
    conn,
    candidate_id: str,
    actor: dict,
    action: str,
    idempotency_key: str,
    before_version: int | None,
    after_version: int | None,
    metadata: dict,
) -> None:
    conn.execute(
        """
        INSERT INTO publication_candidate_events (
            id, candidate_id, actor_id, action, before_version, after_version,
            metadata_json, idempotency_key, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            new_id("pge"),
            candidate_id,
            str(actor["id"]),
            action,
            before_version,
            after_version,
            json_dumps(metadata),
            idempotency_key,
            now_iso(),
        ),
    )


def evaluate_candidate(
    conn,
    actor: dict,
    *,
    channel: str,
    subject_type: str,
    subject_id: str,
    recipient_user_id: str,
    content: Any,
    source_refs: list,
    idempotency_key: str,
    context: dict,
) -> dict:
    policy = _policy()
    if channel not in policy["channels"]:
        raise PublicationGateError(
            "publication_channel_invalid",
            "发布渠道不受支持。",
            422,
        )
    if not idempotency_key or len(idempotency_key) > 160:
        raise PublicationGateError(
            "idempotency_key_required",
            "发布流水线需要有效幂等键。",
            422,
        )
    payload = {
        **context,
        "channel": channel,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "recipient_user_id": recipient_user_id,
        "content": content,
        "source_refs": source_refs,
    }
    content_hash = _sha(content)
    existing = conn.execute(
        """
        SELECT * FROM publication_candidates
        WHERE created_by = ? AND channel = ? AND idempotency_key = ?
        """,
        (str(actor["id"]), channel, idempotency_key),
    ).fetchone()
    if existing:
        item = row_to_dict(existing)
        if (
            item["content_sha256"] != content_hash
            or str(item["subject_id"]) != str(subject_id)
            or str(item["recipient_user_id"]) != str(recipient_user_id)
        ):
            raise PublicationGateError(
                "publication_idempotency_conflict",
                "该发布幂等键已用于其他内容。",
                409,
            )
        return _present(item)

    results = _gate_results(actor, policy["channels"][channel], payload, policy)
    blocked = next((item for item in results if item["decision"] == "blocked"), None)
    timestamp = now_iso()
    candidate_id = new_id("pub")
    previous_content = context.get("previous_content")
    diff = {
        "previous_sha256": (
            _sha(previous_content) if previous_content is not None else None
        ),
        "current_sha256": content_hash,
        "changed": (
            previous_content is not None and _sha(previous_content) != content_hash
        ),
    }
    conn.execute(
        """
        INSERT INTO publication_candidates (
            id, channel, subject_type, subject_id, recipient_user_id, author_id,
            reviewed_by, status, blocked_gate, reason_code, risk_level, multi_party,
            content_json, content_sha256, source_refs_json, gate_summary_json,
            diff_json, policy_version, version, idempotency_key, created_by,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
        """,
        (
            candidate_id,
            channel,
            subject_type,
            subject_id,
            recipient_user_id,
            str(context.get("author_id") or actor["id"]),
            str(context.get("reviewer_id") or "") or None,
            "blocked" if blocked else "approved",
            blocked["gate_name"] if blocked else None,
            blocked["reason_code"] if blocked else None,
            str(context.get("risk_level") or "low"),
            1 if context.get("multi_party") is True else 0,
            json_dumps(content),
            content_hash,
            json_dumps(source_refs),
            json_dumps(
                {item["gate_name"]: item["decision"] for item in results}
            ),
            json_dumps(diff),
            policy["version"],
            idempotency_key,
            str(actor["id"]),
            timestamp,
            timestamp,
        ),
    )
    for result in results:
        conn.execute(
            """
            INSERT INTO publication_gate_checks (
                id, candidate_id, attempt_no, gate_name, decision, reason_code,
                details_json, checked_by, checked_at
            ) VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id("pgc"),
                candidate_id,
                result["gate_name"],
                result["decision"],
                result["reason_code"],
                json_dumps(result["details"]),
                str(actor["id"]),
                timestamp,
            ),
        )
    _event(
        conn,
        candidate_id,
        actor,
        "publication_approved" if blocked is None else "publication_blocked",
        f"{idempotency_key}:gate",
        None,
        1,
        {"blocked_gate": blocked["gate_name"] if blocked else None},
    )
    write_audit_log(
        conn,
        "publication_gate_approved" if blocked is None else "publication_gate_blocked",
        str(actor["id"]),
        "publication_candidate",
        candidate_id,
        {
            "channel": channel,
            "subject_type": subject_type,
            "subject_id": subject_id,
            "blocked_gate": blocked["gate_name"] if blocked else None,
            "raw_content_logged": False,
        },
    )
    row = conn.execute(
        "SELECT * FROM publication_candidates WHERE id = ?",
        (candidate_id,),
    ).fetchone()
    return _present(row_to_dict(row))


def assert_candidate_approved(candidate: dict) -> None:
    if candidate.get("status") != "approved":
        raise PublicationGateError(
            "publication_gate_blocked",
            "内容未通过统一发布门，已保留为可恢复候选。",
            409,
            {
                "candidate_id": candidate.get("id"),
                "blocked_gate": candidate.get("blocked_gate"),
                "reason_code": candidate.get("reason_code"),
            },
        )


def mark_published(conn, candidate_id: str, actor: dict) -> dict:
    row = conn.execute(
        "SELECT * FROM publication_candidates WHERE id = ?",
        (candidate_id,),
    ).fetchone()
    if row is None:
        raise PublicationGateError(
            "publication_candidate_not_found",
            "没有找到发布候选。",
            404,
        )
    item = row_to_dict(row)
    if item["status"] == "published":
        return _present(item)
    if item["status"] != "approved":
        assert_candidate_approved(_present(item))
    before = int(item["version"])
    timestamp = now_iso()
    updated = conn.execute(
        """
        UPDATE publication_candidates
        SET status = 'published', published_by = ?, published_at = ?,
            version = version + 1, updated_at = ?
        WHERE id = ? AND version = ? AND status = 'approved'
        """,
        (str(actor["id"]), timestamp, timestamp, candidate_id, before),
    )
    if updated.rowcount != 1:
        raise PublicationGateError(
            "publication_version_conflict",
            "发布候选已变化，请重新读取。",
            409,
        )
    _event(
        conn,
        candidate_id,
        actor,
        "publication_published",
        f"publish:{candidate_id}:{before}",
        before,
        before + 1,
        {},
    )
    return _present(
        row_to_dict(
            conn.execute(
                "SELECT * FROM publication_candidates WHERE id = ?",
                (candidate_id,),
            ).fetchone()
        )
    )


def recover_candidate(
    actor: dict,
    candidate_id: str,
    payload: dict,
    idempotency_key: str,
) -> dict:
    if str(actor.get("role") or "") not in {"researcher", "supervisor", "admin"}:
        raise PublicationGateError(
            "forbidden",
            "只有正式研究角色可以恢复发布候选。",
            403,
        )
    expected = int(payload.get("expected_version", -1))
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM publication_candidates WHERE id = ?",
            (candidate_id,),
        ).fetchone()
        if row is None:
            raise PublicationGateError(
                "publication_candidate_not_found",
                "没有找到发布候选。",
                404,
            )
        current = row_to_dict(row)
        if int(current["version"]) != expected:
            raise PublicationGateError(
                "publication_version_conflict",
                "发布候选已变化，请重新读取。",
                409,
            )
        if current["status"] not in {"blocked", "approved"}:
            raise PublicationGateError(
                "publication_state_invalid",
                "当前状态不能恢复。",
                409,
            )
        content = payload.get(
            "content",
            json_loads(current["content_json"], {}),
        )
        source_refs = payload.get(
            "source_refs",
            json_loads(current["source_refs_json"], []),
        )
        context = dict(payload.get("context") or {})
        policy = _policy()
        results = _gate_results(
            actor,
            policy["channels"][current["channel"]],
            {
                **context,
                "channel": current["channel"],
                "subject_type": current["subject_type"],
                "subject_id": current["subject_id"],
                "recipient_user_id": current["recipient_user_id"],
                "content": content,
                "source_refs": source_refs,
            },
            policy,
        )
        blocked = next(
            (item for item in results if item["decision"] == "blocked"),
            None,
        )
        attempt = int(
            conn.execute(
                """
                SELECT COALESCE(MAX(attempt_no), 0) + 1 AS n
                FROM publication_gate_checks WHERE candidate_id = ?
                """,
                (candidate_id,),
            ).fetchone()["n"]
        )
        timestamp = now_iso()
        for result in results:
            conn.execute(
                """
                INSERT INTO publication_gate_checks (
                    id, candidate_id, attempt_no, gate_name, decision, reason_code,
                    details_json, checked_by, checked_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id("pgc"),
                    candidate_id,
                    attempt,
                    result["gate_name"],
                    result["decision"],
                    result["reason_code"],
                    json_dumps(result["details"]),
                    str(actor["id"]),
                    timestamp,
                ),
            )
        changed = conn.execute(
            """
            UPDATE publication_candidates
            SET status = ?, blocked_gate = ?, reason_code = ?, reviewed_by = ?,
                content_json = ?, content_sha256 = ?, source_refs_json = ?,
                gate_summary_json = ?, diff_json = ?, version = version + 1,
                updated_at = ?
            WHERE id = ? AND version = ?
            """,
            (
                "blocked" if blocked else "approved",
                blocked["gate_name"] if blocked else None,
                blocked["reason_code"] if blocked else None,
                str(context.get("reviewer_id") or "") or current.get("reviewed_by"),
                json_dumps(content),
                _sha(content),
                json_dumps(source_refs),
                json_dumps(
                    {item["gate_name"]: item["decision"] for item in results}
                ),
                json_dumps(
                    {
                        "previous_sha256": current["content_sha256"],
                        "current_sha256": _sha(content),
                        "changed": current["content_sha256"] != _sha(content),
                    }
                ),
                timestamp,
                candidate_id,
                expected,
            ),
        )
        if changed.rowcount != 1:
            raise PublicationGateError(
                "publication_version_conflict",
                "发布候选已变化，请重新读取。",
                409,
            )
        _event(
            conn,
            candidate_id,
            actor,
            "publication_recovered" if blocked is None else "publication_reblocked",
            idempotency_key,
            expected,
            expected + 1,
            {"blocked_gate": blocked["gate_name"] if blocked else None},
        )
        write_audit_log(
            conn,
            (
                "publication_candidate_recovered"
                if blocked is None
                else "publication_candidate_reblocked"
            ),
            str(actor["id"]),
            "publication_candidate",
            candidate_id,
            {"blocked_gate": blocked["gate_name"] if blocked else None},
        )
        conn.commit()
        return _present(
            row_to_dict(
                conn.execute(
                    "SELECT * FROM publication_candidates WHERE id = ?",
                    (candidate_id,),
                ).fetchone()
            )
        )


def withdraw_candidate(
    actor: dict,
    candidate_id: str,
    payload: dict,
    idempotency_key: str,
) -> dict:
    if str(actor.get("role") or "") not in {"supervisor", "admin"}:
        raise PublicationGateError(
            "forbidden",
            "只有督导或管理员可以撤回发布候选。",
            403,
        )
    reason = str(payload.get("reason") or "").strip()
    expected = int(payload.get("expected_version", -1))
    if not reason:
        raise PublicationGateError(
            "withdrawal_reason_required",
            "撤回需要说明原因。",
            422,
        )
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM publication_candidates WHERE id = ?",
            (candidate_id,),
        ).fetchone()
        if row is None:
            raise PublicationGateError(
                "publication_candidate_not_found",
                "没有找到发布候选。",
                404,
            )
        current = row_to_dict(row)
        if int(current["version"]) != expected:
            raise PublicationGateError(
                "publication_version_conflict",
                "发布候选已变化，请重新读取。",
                409,
            )
        timestamp = now_iso()
        changed = conn.execute(
            """
            UPDATE publication_candidates
            SET status = 'withdrawn', withdrawn_at = ?, withdrawal_reason = ?,
                version = version + 1, updated_at = ?
            WHERE id = ? AND version = ? AND status != 'withdrawn'
            """,
            (timestamp, reason[:1000], timestamp, candidate_id, expected),
        )
        if changed.rowcount != 1:
            raise PublicationGateError(
                "publication_state_invalid",
                "当前候选已撤回或不能撤回。",
                409,
            )
        _event(
            conn,
            candidate_id,
            actor,
            "publication_withdrawn",
            idempotency_key,
            expected,
            expected + 1,
            {"reason_present": True},
        )
        write_audit_log(
            conn,
            "publication_candidate_withdrawn",
            str(actor["id"]),
            "publication_candidate",
            candidate_id,
            {"reason_present": True},
        )
        conn.commit()
        return _present(
            row_to_dict(
                conn.execute(
                    "SELECT * FROM publication_candidates WHERE id = ?",
                    (candidate_id,),
                ).fetchone()
            )
        )


def list_candidates(
    actor: dict,
    *,
    status: str = "",
    channel: str = "",
    limit: int = 50,
) -> dict:
    role = str(actor.get("role") or "")
    if role not in {"researcher", "supervisor", "admin"}:
        raise PublicationGateError(
            "forbidden",
            "当前账号不能查看正式发布候选。",
            403,
        )
    where = ["1 = 1"]
    params: list[Any] = []
    if status:
        where.append("status = ?")
        params.append(status)
    if channel:
        where.append("channel = ?")
        params.append(channel)
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM publication_candidates
            WHERE {' AND '.join(where)}
            ORDER BY updated_at DESC LIMIT ?
            """,
            (*params, max(1, min(limit, 100))),
        ).fetchall()
    items = [_present(item) for item in rows_to_dicts(rows)]
    return {
        "items": items,
        "count": len(items),
        "production_release_approved": False,
    }
