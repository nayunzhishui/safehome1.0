"""Explicit and auditable transfer of anonymous trial records to a formal account."""

from __future__ import annotations

import hashlib
import re

from database import json_dumps, json_loads, new_id, now_iso, row_to_dict, write_audit_log


ANONYMOUS_ID_PATTERN = re.compile(r"^(?:wx|web)_user_\d{10,16}_[0-9a-fA-F]{4,20}$")

# Only participant-owned rows are transferred. Review notes and audit logs remain
# immutable because their actor/reviewer identity has a different meaning.
USER_ID_TABLES = (
    ("goals", "目标"),
    ("emotion_diaries", "情绪日记"),
    ("emotion_thermometer", "情绪温度"),
    ("feedback_results", "支持性反馈"),
    ("checkins", "训练记录"),
    ("assessment_results", "支持性测评"),
    ("student_profiles", "阶段性画像"),
    ("student_profile_followups", "画像跟进"),
    ("student_sandplay_entries", "表达练习"),
    ("parent_assessment_submissions", "家长测评"),
    ("records", "项目记录"),
    ("consent_records", "知情记录"),
    ("risk_review_records", "人工关注记录"),
    ("weekly_reports", "周度复盘"),
    ("supervision_requests", "人工支持"),
    ("messages", "站内消息"),
    ("notification_preferences", "提醒授权"),
    ("notification_deliveries", "提醒发送记录"),
    ("privacy_requests", "隐私请求"),
    ("relationship_pilot_enrollments", "关系探索报名"),
    ("relationship_screening_reports", "阶段性报告"),
    ("relationship_pilot_tasks", "关系探索任务"),
    ("relationship_narratives", "关系叙事"),
    ("relationship_longitudinal_entries", "连续记录"),
    ("relationship_hypothesis_feedback", "报告回应"),
)


def is_supported_anonymous_id(value: str | None) -> bool:
    return bool(value and ANONYMOUS_ID_PATTERN.fullmatch(str(value).strip()))


def _research_anonymous_id(user_id: str) -> str:
    return f"anon_{hashlib.sha256(user_id.encode('utf-8')).hexdigest()[:12]}"


def count_claimable_records(conn, anonymous_id: str) -> dict[str, int]:
    counts = {
        table: int(conn.execute(f"SELECT COUNT(*) AS count FROM {table} WHERE user_id = ?", (anonymous_id,)).fetchone()["count"])
        for table, _label in USER_ID_TABLES
    }
    family_count = conn.execute(
        "SELECT COUNT(*) AS count FROM family_links WHERE parent_user_id = ? OR student_user_id = ?",
        (anonymous_id, anonymous_id),
    ).fetchone()["count"]
    counts["family_links"] = int(family_count)
    return counts


def summarized_counts(counts: dict[str, int]) -> list[dict]:
    labels = {table: label for table, label in USER_ID_TABLES}
    labels["family_links"] = "家庭关联"
    return [
        {"module": table, "label": labels[table], "count": int(count)}
        for table, count in counts.items()
        if int(count) > 0
    ]


def register_claim_candidate(conn, target_user_id: str, anonymous_id: str | None) -> dict | None:
    """Register a login-device candidate without moving any records."""

    if not is_supported_anonymous_id(anonymous_id) or anonymous_id == target_user_id:
        return None
    target = conn.execute("SELECT role, status FROM users WHERE id = ?", (target_user_id,)).fetchone()
    if target is None or target["role"] not in {"parent", "student", "user"} or target["status"] != "active":
        return None
    if conn.execute("SELECT id FROM users WHERE id = ?", (anonymous_id,)).fetchone() is None:
        return None

    counts = count_claimable_records(conn, anonymous_id)
    if sum(counts.values()) == 0:
        return None

    existing = conn.execute("SELECT * FROM data_claims WHERE anonymous_id = ?", (anonymous_id,)).fetchone()
    timestamp = now_iso()
    if existing is not None:
        item = row_to_dict(existing)
        if item["target_user_id"] != target_user_id:
            return None
        if item["status"] == "available":
            conn.execute(
                "UPDATE data_claims SET counts_json = ?, updated_at = ? WHERE id = ?",
                (json_dumps(counts), timestamp, item["id"]),
            )
        return item

    claim_id = new_id("claim")
    conn.execute(
        """
        INSERT INTO data_claims (
            id, anonymous_id, target_user_id, status, counts_json,
            claimed_at, created_at, updated_at
        ) VALUES (?, ?, ?, 'available', ?, NULL, ?, ?)
        """,
        (claim_id, anonymous_id, target_user_id, json_dumps(counts), timestamp, timestamp),
    )
    return {"id": claim_id, "target_user_id": target_user_id, "status": "available", "counts_json": json_dumps(counts)}


def claim_preview(conn, target_user_id: str) -> dict:
    row = conn.execute(
        """
        SELECT * FROM data_claims
        WHERE target_user_id = ? AND status = 'available'
        ORDER BY created_at ASC LIMIT 1
        """,
        (target_user_id,),
    ).fetchone()
    if row is None:
        return {
            "available": False,
            "claim_id": None,
            "total_records": 0,
            "modules": [],
            "boundary_notice": "当前没有待合并的本机试用记录。",
        }
    item = row_to_dict(row)
    counts = count_claimable_records(conn, item["anonymous_id"])
    conn.execute(
        "UPDATE data_claims SET counts_json = ?, updated_at = ? WHERE id = ?",
        (json_dumps(counts), now_iso(), item["id"]),
    )
    return {
        "available": sum(counts.values()) > 0,
        "claim_id": item["id"],
        "total_records": sum(counts.values()),
        "modules": summarized_counts(counts),
        "boundary_notice": "只显示记录数量，不展示试用期填写原文；需要你确认后才会合并。",
    }


def claim_records(conn, target_user_id: str, claim_id: str) -> dict:
    row = conn.execute(
        "SELECT * FROM data_claims WHERE id = ? AND target_user_id = ?",
        (claim_id, target_user_id),
    ).fetchone()
    if row is None:
        raise LookupError("没有找到可认领的试用记录")
    claim = row_to_dict(row)
    stored_counts = json_loads(claim.get("counts_json"), {})
    if claim["status"] == "claimed":
        return {
            "claim_id": claim_id,
            "status": "claimed",
            "total_records": sum(int(value) for value in stored_counts.values()),
            "modules": summarized_counts(stored_counts),
            "claimed_at": claim.get("claimed_at"),
            "already_completed": True,
        }
    if claim["status"] != "available":
        raise ValueError("该认领记录当前不可处理")

    anonymous_id = claim["anonymous_id"]
    counts = count_claimable_records(conn, anonymous_id)
    for table, _label in USER_ID_TABLES:
        conn.execute(f"UPDATE {table} SET user_id = ? WHERE user_id = ?", (target_user_id, anonymous_id))
    conn.execute(
        "UPDATE family_links SET parent_user_id = ? WHERE parent_user_id = ?",
        (target_user_id, anonymous_id),
    )
    conn.execute(
        "UPDATE family_links SET student_user_id = ? WHERE student_user_id = ?",
        (target_user_id, anonymous_id),
    )
    research_id = _research_anonymous_id(target_user_id)
    conn.execute("UPDATE student_profiles SET anonymous_id = ? WHERE user_id = ?", (research_id, target_user_id))
    conn.execute("UPDATE parent_assessment_submissions SET anonymous_id = ? WHERE user_id = ?", (research_id, target_user_id))

    timestamp = now_iso()
    conn.execute(
        "UPDATE data_claims SET status = 'claimed', counts_json = ?, claimed_at = ?, updated_at = ? WHERE id = ?",
        (json_dumps(counts), timestamp, timestamp, claim_id),
    )
    conn.execute(
        """
        UPDATE users SET status = 'merged', updated_at = ?
        WHERE id = ? AND username IS NULL AND wechat_openid IS NULL AND phone_hash IS NULL
        """,
        (timestamp, anonymous_id),
    )
    write_audit_log(
        conn,
        action="anonymous_data_claimed",
        actor_id=target_user_id,
        target_type="data_claim",
        target_id=claim_id,
        metadata={"record_count": sum(counts.values()), "module_counts": counts},
    )
    return {
        "claim_id": claim_id,
        "status": "claimed",
        "total_records": sum(counts.values()),
        "modules": summarized_counts(counts),
        "claimed_at": timestamp,
        "already_completed": False,
    }
