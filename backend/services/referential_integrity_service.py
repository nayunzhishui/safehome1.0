"""Cross-provider referential-integrity checks for high-value SafeHome links.

The current schema historically relied heavily on application-level ``*_id``
relationships. This module adds a single auditable source of truth for the most
important relationships without performing destructive table rebuilds.
"""

from __future__ import annotations

from typing import Any


RELATIONSHIPS = (
    ("emotion_diaries.user_id", "emotion_diaries", "user_id", "users", "id", False),
    ("assessment_results.user_id", "assessment_results", "user_id", "users", "id", False),
    ("consent_records.user_id", "consent_records", "user_id", "users", "id", False),
    ("family_links.parent_user_id", "family_links", "parent_user_id", "users", "id", False),
    ("family_links.student_user_id", "family_links", "student_user_id", "users", "id", True),
    ("risk_review_records.user_id", "risk_review_records", "user_id", "users", "id", False),
    (
        "relationship_pilot_enrollments.user_id",
        "relationship_pilot_enrollments",
        "user_id",
        "users",
        "id",
        False,
    ),
    (
        "research_delivery_workflows.enrollment_id",
        "research_delivery_workflows",
        "enrollment_id",
        "relationship_pilot_enrollments",
        "id",
        False,
    ),
)

_ALLOWED_REFERENCES = {
    (source_table, source_column, target_table, target_column)
    for _, source_table, source_column, target_table, target_column, _ in RELATIONSHIPS
}


def _count_orphans(conn, source_table: str, source_column: str, target_table: str, target_column: str, nullable: bool) -> int:
    null_clause = f"s.{source_column} IS NOT NULL AND " if nullable else ""
    row = conn.execute(
        f"""
        SELECT COUNT(*) AS count
        FROM {source_table} s
        WHERE {null_clause}NOT EXISTS (
            SELECT 1 FROM {target_table} t
            WHERE t.{target_column} = s.{source_column}
        )
        """
    ).fetchone()
    return int(row["count"] or 0)


def audit_referential_integrity(conn) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    total_orphans = 0
    for name, source_table, source_column, target_table, target_column, nullable in RELATIONSHIPS:
        count = _count_orphans(conn, source_table, source_column, target_table, target_column, nullable)
        total_orphans += count
        checks.append(
            {
                "relationship": name,
                "target": f"{target_table}.{target_column}",
                "nullable": nullable,
                "orphan_count": count,
                "ok": count == 0,
            }
        )
    return {
        "ok": total_orphans == 0,
        "total_orphans": total_orphans,
        "checks": checks,
        "boundary_notice": "只报告孤儿关系数量，不输出参与者原始心理文本或直接身份信息。",
    }


def assert_reference_exists(
    conn,
    *,
    source_table: str,
    source_column: str,
    target_table: str,
    target_column: str,
    value: object,
    allow_none: bool = False,
) -> None:
    key = (source_table, source_column, target_table, target_column)
    if key not in _ALLOWED_REFERENCES:
        raise ValueError("未注册的关系完整性检查")
    if value is None and allow_none:
        return
    if value in (None, ""):
        raise ValueError(f"{source_table}.{source_column} 不能为空")
    row = conn.execute(
        f"SELECT 1 FROM {target_table} WHERE {target_column} = ? LIMIT 1",
        (value,),
    ).fetchone()
    if row is None:
        raise ValueError(f"{source_table}.{source_column} 引用了不存在的 {target_table}.{target_column}")
