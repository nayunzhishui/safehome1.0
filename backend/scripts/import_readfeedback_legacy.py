"""Import legacy ReadFeedback SQLite data into the SafeHome database.

This script reads the legacy database in read-only mode and writes deterministic
legacy_* IDs into the SafeHome database. It is safe to run multiple times.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))

from database import ensure_schema_columns, ensure_user, get_connection, json_dumps, now_iso, sync_training_cards  # noqa: E402
from models import SCHEMA_SQL  # noqa: E402


DEFAULT_SOURCE = Path(r"D:\桌面\Desktop\2026.5work\20260504夏老师文件\readfeedback\unified_assessment.sqlite3")
DEFAULT_TARGET = BACKEND_ROOT / "safehome.sqlite3"


def _loads(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _anonymous_id(user_id: str) -> str:
    digest = hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
    return f"anon_{digest}"


def _connect_legacy_readonly(path: Path) -> sqlite3.Connection:
    uri = f"file:{path.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (table,)).fetchone()
    return row is not None


def init_target_db(target_path: Path) -> None:
    with get_connection(target_path) as conn:
        for statement in SCHEMA_SQL:
            conn.execute(statement)
        ensure_schema_columns(conn)
        sync_training_cards(conn)
        conn.commit()


def import_parent_rows(source: sqlite3.Connection, target: sqlite3.Connection) -> int:
    if not _table_exists(source, "parent_submissions"):
        return 0
    rows = source.execute("SELECT * FROM parent_submissions ORDER BY id").fetchall()
    count = 0
    for row in rows:
        old_id = str(row["id"])
        submission_id = f"legacy_parent_{old_id}"
        user_id = f"legacy_parent_user_{row['participant_code'] or old_id}"
        created_at = row["created_at"] or now_iso()
        ensure_user(target, user_id, f"legacy parent {row['participant_code'] or old_id}")
        target.execute(
            """
            INSERT OR IGNORE INTO parent_assessment_submissions (
                id, user_id, anonymous_id, participant_code, research_consent,
                study_batch, source_channel, questionnaire_version, scoring_version,
                answers_json, scores_json, profile_key, report_json,
                started_at, completed_at, duration_seconds, quality_flags_json,
                legacy_source_id, legacy_source_table, export_allowed,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                submission_id,
                user_id,
                _anonymous_id(user_id),
                row["participant_code"],
                row["research_consent"],
                row["study_batch"],
                row["source_channel"],
                row["questionnaire_version"],
                row["scoring_version"],
                row["answers_json"],
                row["scores_json"],
                row["profile_key"],
                row["report_json"],
                row["started_at"],
                row["completed_at"],
                row["duration_seconds"],
                row["quality_flags_json"],
                old_id,
                "parent_submissions",
                row["research_consent"],
                created_at,
                created_at,
            ),
        )
        target.execute(
            """
            INSERT OR IGNORE INTO records (
                id, user_id, module_type, source_id, data_json,
                created_at, updated_at, export_allowed
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"legacy_record_parent_{old_id}",
                user_id,
                "parent_assessment",
                submission_id,
                json_dumps({"legacy_source_id": old_id, "profile_key": row["profile_key"]}),
                created_at,
                created_at,
                row["research_consent"],
            ),
        )
        count += 1
    return count


def import_parent_actions(source: sqlite3.Connection, target: sqlite3.Connection) -> int:
    if not _table_exists(source, "parent_report_actions"):
        return 0
    rows = source.execute("SELECT * FROM parent_report_actions ORDER BY id").fetchall()
    for row in rows:
        target.execute(
            """
            INSERT OR IGNORE INTO parent_report_actions (id, submission_id, action_key, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                f"legacy_parent_action_{row['id']}",
                f"legacy_parent_{row['submission_id']}",
                row["action_key"],
                row["created_at"],
            ),
        )
    return len(rows)


def import_student_rows(source: sqlite3.Connection, target: sqlite3.Connection) -> dict[int, str]:
    id_map: dict[int, str] = {}
    if not _table_exists(source, "student_submissions"):
        return id_map
    rows = source.execute("SELECT * FROM student_submissions ORDER BY id").fetchall()
    for row in rows:
        old_id = int(row["id"])
        participant = row["participant_code"] or str(old_id)
        user_id = f"legacy_student_user_{participant}"
        assessment_id = f"legacy_student_assessment_{old_id}"
        profile_id = f"legacy_student_profile_{old_id}"
        created_at = row["created_at"] or now_iso()
        scores = _loads(row["scores_json"], {})
        profile_result = _loads(row["profile_result_json"], {})
        report = _loads(row["report_json"], {})
        features = scores.get("features", {})
        dimensions = [
            {"key": "test_anxiety", "label": "考试压力反应", "level": "", "summary": str(features.get("test_anxiety", ""))},
            {"key": "iu_total", "label": "不确定性耐受", "level": "", "summary": str(features.get("iu_total", ""))},
            {"key": "self_compassion", "label": "自我支持资源", "level": "", "summary": str(features.get("self_compassion", ""))},
        ]
        ensure_user(target, user_id, f"legacy student {participant}")
        target.execute(
            """
            INSERT OR IGNORE INTO assessment_results (
                id, user_id, worksheet_id, worksheet_title, category,
                answers_json, scores_json, total_score, result_summary, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                assessment_id,
                user_id,
                "legacy_readfeedback_student_profile",
                "旧 ReadFeedback 学生画像测评",
                "学生画像",
                json_dumps({"answers": _loads(row["answers_json"], {}), "text_answers": _loads(row["text_answers_json"], {})}),
                row["scores_json"],
                None,
                report.get("summary") or profile_result.get("summary") or "旧 ReadFeedback 学生画像记录",
                created_at,
            ),
        )
        target.execute(
            """
            INSERT OR IGNORE INTO student_profiles (
                id, user_id, anonymous_id, assessment_result_id, round, source,
                scores_json, text_features_json, profile_code, profile_name,
                confidence, dimensions_json, recommended_task_ids_json,
                risk_level, requires_review, boundary_notice, rules_version,
                model_version, model_type, cluster_id, pc1, pc2, nearest_distance,
                second_distance, report_json, visuals_json,
                legacy_source_id, legacy_source_table, export_allowed,
                data_quality, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile_id,
                user_id,
                _anonymous_id(user_id),
                assessment_id,
                1,
                "legacy_readfeedback",
                row["scores_json"],
                json_dumps({"text_answers_present": bool(row["text_answers_json"])}),
                profile_result.get("profile_id") or profile_result.get("profile_code") or "legacy_profile",
                profile_result.get("profile_name") or report.get("role") or "旧学生画像",
                profile_result.get("confidence"),
                json_dumps(dimensions),
                json_dumps([]),
                "low",
                0,
                "旧数据导入，仅作历史研究记录；不构成诊断。",
                "legacy",
                "2026.05-student-profile-kmeans-v1",
                "readfeedback-kmeans-pca",
                profile_result.get("cluster_id"),
                profile_result.get("pc1"),
                profile_result.get("pc2"),
                profile_result.get("nearest_distance"),
                profile_result.get("second_distance"),
                row["report_json"],
                json_dumps({}),
                str(old_id),
                "student_submissions",
                row["research_consent"],
                "legacy_import",
                created_at,
                created_at,
            ),
        )
        target.execute(
            """
            INSERT OR IGNORE INTO records (
                id, user_id, module_type, source_id, data_json,
                created_at, updated_at, export_allowed
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"legacy_record_student_{old_id}",
                user_id,
                "student_profile",
                profile_id,
                json_dumps({"legacy_source_id": old_id, "profile_code": profile_result.get("profile_id")}),
                created_at,
                created_at,
                row["research_consent"],
            ),
        )
        id_map[old_id] = profile_id
    return id_map


def import_student_followups(source: sqlite3.Connection, target: sqlite3.Connection, id_map: dict[int, str]) -> int:
    if not _table_exists(source, "student_followups"):
        return 0
    rows = source.execute("SELECT * FROM student_followups ORDER BY id").fetchall()
    for row in rows:
        profile_id = id_map.get(int(row["submission_id"]))
        if not profile_id:
            continue
        user_row = target.execute("SELECT user_id FROM student_profiles WHERE id = ?", (profile_id,)).fetchone()
        user_id = user_row["user_id"] if user_row else "legacy_student_user_unknown"
        target.execute(
            """
            INSERT OR IGNORE INTO student_profile_followups (
                id, profile_id, user_id, round_no, fit, task_done,
                state_score, text, keywords_json, created_at, export_allowed
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"legacy_followup_{row['id']}",
                profile_id,
                user_id,
                row["round_no"],
                row["profile_fit"],
                row["task_done"],
                row["state_score"],
                row["reflection_text"],
                row["text_keywords"],
                row["created_at"],
                1,
            ),
        )
    return len(rows)


def import_student_sandplay(source: sqlite3.Connection, target: sqlite3.Connection, id_map: dict[int, str]) -> int:
    if not _table_exists(source, "student_sandplay_entries"):
        return 0
    rows = source.execute("SELECT * FROM student_sandplay_entries ORDER BY id").fetchall()
    for row in rows:
        profile_id = id_map.get(int(row["submission_id"]))
        if not profile_id:
            continue
        user_row = target.execute("SELECT user_id FROM student_profiles WHERE id = ?", (profile_id,)).fetchone()
        user_id = user_row["user_id"] if user_row else "legacy_student_user_unknown"
        target.execute(
            """
            INSERT OR IGNORE INTO student_sandplay_entries (
                id, profile_id, user_id, task_title, scene_json,
                reflection_text, summary_json, created_at, export_allowed
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"legacy_sandplay_{row['id']}",
                profile_id,
                user_id,
                f"旧沙盘表达第 {row['round_no']} 轮",
                row["scene_json"],
                row["reflection_text"],
                row["summary_json"],
                row["created_at"],
                1,
            ),
        )
    return len(rows)


def run_import(source_path: Path, target_path: Path) -> dict[str, int]:
    if not source_path.exists():
        raise FileNotFoundError(source_path)
    init_target_db(target_path)
    with _connect_legacy_readonly(source_path) as source, get_connection(target_path) as target:
        parent_count = import_parent_rows(source, target)
        parent_action_count = import_parent_actions(source, target)
        student_map = import_student_rows(source, target)
        followup_count = import_student_followups(source, target, student_map)
        sandplay_count = import_student_sandplay(source, target, student_map)
        target.commit()
    return {
        "parent_submissions": parent_count,
        "parent_report_actions": parent_action_count,
        "student_submissions": len(student_map),
        "student_followups": followup_count,
        "student_sandplay_entries": sandplay_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Import legacy ReadFeedback SQLite data into SafeHome.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    args = parser.parse_args()
    result = run_import(args.source, args.target)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
