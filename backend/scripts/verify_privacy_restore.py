"""Read-only privacy tombstone verification for a restored SQLite backup."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import sqlite3
from pathlib import Path


USER_TABLES = (
    "goals", "emotion_diaries", "emotion_thermometer", "feedback_results", "checkins",
    "assessment_results", "student_profiles", "student_profile_followups", "student_sandplay_entries",
    "parent_assessment_submissions", "records", "consent_records", "risk_review_records", "weekly_reports",
    "supervision_requests", "messages", "notification_preferences", "notification_deliveries",
    "relationship_pilot_enrollments", "relationship_screening_reports", "relationship_pilot_tasks",
    "relationship_narratives", "relationship_longitudinal_entries", "relationship_hypothesis_feedback", "feedback_ledger",
    "therapeutic_assessment_cases", "therapeutic_assessment_actions",
)

TABLE_SCOPES = {
    "consent_records": "account_identity",
    "goals": "participant_records", "emotion_diaries": "participant_records", "emotion_thermometer": "participant_records",
    "assessment_results": "participant_records", "student_profiles": "participant_records", "student_profile_followups": "participant_records",
    "student_sandplay_entries": "participant_records", "parent_assessment_submissions": "participant_records", "risk_review_records": "participant_records",
    "feedback_results": "feedback_and_training", "feedback_ledger": "feedback_and_training", "checkins": "feedback_and_training",
    "weekly_reports": "feedback_and_training", "supervision_requests": "feedback_and_training",
    "messages": "messages_and_notifications", "notification_preferences": "messages_and_notifications", "notification_deliveries": "messages_and_notifications",
    "relationship_pilot_enrollments": "relationship_pilot", "relationship_screening_reports": "relationship_pilot",
    "relationship_pilot_tasks": "relationship_pilot", "relationship_narratives": "relationship_pilot",
    "relationship_longitudinal_entries": "relationship_pilot", "relationship_hypothesis_feedback": "relationship_pilot",
    "records": "research_outputs",
    "therapeutic_assessment_cases": "therapeutic_assessment",
    "therapeutic_assessment_actions": "therapeutic_assessment",
}


def verify(database_path: Path, secret: bytes) -> dict:
    if not secret:
        raise ValueError("必须提供与执行时一致的墓碑HMAC密钥")
    resolved = database_path.resolve()
    conn = sqlite3.connect(f"file:{resolved.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        tables = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        if "privacy_deletion_tombstones" not in tables:
            return {"ok": False, "reason": "tombstone_table_missing", "tombstone_count": 0, "violation_counts": {}}
        tombstones = conn.execute("SELECT subject_hash, replacement_user_id, scope_json FROM privacy_deletion_tombstones").fetchall()
        scopes_by_hash = {row["subject_hash"]: set(json.loads(row["scope_json"] or "[]")) for row in tombstones}
        violation_counts: dict[str, int] = {}
        if "users" in tables:
            rows = conn.execute("SELECT id, status FROM users").fetchall()
            violation_counts["users"] = sum(
                1 for row in rows
                if "account_identity" in scopes_by_hash.get(hmac.new(secret, str(row["id"]).encode(), hashlib.sha256).hexdigest(), set())
                and row["status"] != "deleted"
            )
        for table in USER_TABLES:
            if table not in tables:
                continue
            scope = TABLE_SCOPES.get(table)
            if not scope:
                continue
            user_column = "participant_user_id" if table in {"therapeutic_assessment_cases", "therapeutic_assessment_actions"} else "user_id"
            rows = conn.execute(f"SELECT DISTINCT {user_column} AS user_id FROM {table} WHERE {user_column} IS NOT NULL").fetchall()
            violation_counts[table] = sum(
                1 for row in rows
                if scope in scopes_by_hash.get(hmac.new(secret, str(row["user_id"]).encode(), hashlib.sha256).hexdigest(), set())
            )
        if "therapeutic_assessment_cases" in tables:
            for table in ("therapeutic_assessment_feedback_versions", "therapeutic_assessment_events"):
                if table not in tables:
                    continue
                rows = conn.execute(
                    f"""
                    SELECT DISTINCT c.participant_user_id AS user_id
                    FROM {table} d
                    JOIN therapeutic_assessment_cases c ON c.id = d.case_id
                    WHERE c.participant_user_id IS NOT NULL
                    """
                ).fetchall()
                violation_counts[table] = sum(
                    1 for row in rows
                    if "therapeutic_assessment" in scopes_by_hash.get(
                        hmac.new(secret, str(row["user_id"]).encode(), hashlib.sha256).hexdigest(),
                        set(),
                    )
                )
        violation_counts = {key: value for key, value in violation_counts.items() if value}
        return {
            "ok": not violation_counts,
            "reason": None if not violation_counts else "deleted_subject_reappeared_after_restore",
            "tombstone_count": len(tombstones),
            "violation_counts": violation_counts,
            "raw_identifiers_included": False,
        }
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="验证恢复后的SQLite备份没有让已删除主体重新出现")
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--secret", required=True, help="与PRIVACY_TOMBSTONE_SECRET一致；不会写入输出")
    args = parser.parse_args()
    result = verify(args.db, args.secret.encode("utf-8"))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
