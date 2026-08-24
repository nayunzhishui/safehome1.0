"""Execute F11 migrations against a disposable synthetic SQLite database."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from services.database_profile_service import validate_synthetic_migration_fixture  # noqa: E402


DEFAULT_FIXTURE = BACKEND / "tests" / "fixtures" / "rc0810_f11_synthetic_migration.json"
NOW = "2026-08-24T00:00:00+00:00"


def _row_ids(record: dict) -> list[str]:
    return [
        record["id"],
        *[f'{record["id"]}_{index:02d}' for index in range(2, record["count"] + 1)],
    ]


def _seed(conn, records: list[dict]) -> None:
    by_category = {item["category"]: item for item in records}
    for category in ("new_user", "legacy_user", "locked_user", "disabled_user"):
        item = by_category[category]
        conn.execute(
            """
            INSERT INTO users (
                id, nickname, role, source, username, status, auth_epoch,
                created_at, updated_at
            ) VALUES (?, ?, 'parent', 'synthetic_f11', ?, ?, ?, ?, ?)
            """,
            (item["id"], category, item["id"], item["status"], item["version"], NOW, NOW),
        )

    item = by_category["historical_assessment"]
    for record_id in _row_ids(item):
        conn.execute(
            """
            INSERT INTO assessment_results (
                id, user_id, worksheet_id, worksheet_title, category, answers_json,
                scores_json, scoring_version, result_summary, created_at
            ) VALUES (?, ?, 'synthetic_f11', 'Synthetic F11', 'synthetic',
                      '{}', '{}', ?, 'completed', ?)
            """,
            (record_id, item["owner_id"], str(item["version"]), NOW),
        )

    item = by_category["training_checkin"]
    for record_id in _row_ids(item):
        conn.execute(
            """
            INSERT INTO checkins (id, user_id, card_id, completed, reflection, created_at)
            VALUES (?, ?, 'synthetic_f11', 1, 'synthetic', ?)
            """,
            (record_id, item["owner_id"], NOW),
        )

    item = by_category["message"]
    for record_id in _row_ids(item):
        conn.execute(
            """
            INSERT INTO messages (
                id, user_id, message_type, title, source_type, source_id,
                delivery_version, status, created_at
            ) VALUES (?, ?, 'synthetic', 'Synthetic F11', 'synthetic_f11', ?, ?, ?, ?)
            """,
            (record_id, item["owner_id"], record_id, item["version"], item["status"], NOW),
        )

    item = by_category["research_task"]
    conn.execute(
        """
        INSERT INTO research_work_items (
            id, queue_type, source_type, source_id, user_id, status,
            version, created_at, updated_at
        ) VALUES (?, 'synthetic', 'synthetic_f11', ?, ?, ?, ?, ?, ?)
        """,
        (item["id"], item["id"], item["owner_id"], item["status"], item["version"], NOW, NOW),
    )

    item = by_category["therapeutic_assessment"]
    conn.execute(
        """
        INSERT INTO therapeutic_assessment_cases (
            id, participant_user_id, assessment_question, question_candidates_json,
            question_quality_json, question_status, candidate_decision, question_version,
            shared_scope_json, consent_status, status, risk_level, version, created_by,
            created_at, updated_at
        ) VALUES (?, ?, 'Synthetic F11?', '[]', '{}', 'submitted', 'unreviewed', 1,
                  '[]', 'synthetic', ?, 'low', ?, 'synthetic_f11', ?, ?)
        """,
        (item["id"], item["owner_id"], item["status"], item["version"], NOW, NOW),
    )
    conn.commit()


def _snapshot(conn, records: list[dict]) -> list[dict]:
    by_category = {item["category"]: item for item in records}
    result: list[dict] = []
    for category in ("new_user", "legacy_user", "locked_user", "disabled_user"):
        expected = by_category[category]
        row = conn.execute(
            "SELECT id, status, auth_epoch AS version FROM users WHERE id = ?",
            (expected["id"],),
        ).fetchone()
        result.append({
            "category": category,
            "id": row["id"],
            "owner_id": row["id"],
            "count": 1,
            "status": row["status"],
            "version": int(row["version"]),
        })

    rows = conn.execute(
        """
        SELECT id, user_id, scoring_version FROM assessment_results
        WHERE worksheet_id = 'synthetic_f11' ORDER BY id
        """
    ).fetchall()
    result.append({
        "category": "historical_assessment",
        "id": rows[0]["id"],
        "owner_id": rows[0]["user_id"],
        "count": len(rows),
        "status": "completed",
        "version": int(rows[0]["scoring_version"]),
    })

    expected = by_category["training_checkin"]
    rows = conn.execute(
        """
        SELECT id, user_id, completed FROM checkins
        WHERE card_id = 'synthetic_f11' ORDER BY id
        """
    ).fetchall()
    result.append({
        "category": "training_checkin",
        "id": rows[0]["id"],
        "owner_id": rows[0]["user_id"],
        "count": len(rows),
        "status": "completed" if rows[0]["completed"] else "incomplete",
        "version": expected["version"],
    })

    rows = conn.execute(
        """
        SELECT id, user_id, status, delivery_version FROM messages
        WHERE source_type = 'synthetic_f11' ORDER BY id
        """
    ).fetchall()
    result.append({
        "category": "message",
        "id": rows[0]["id"],
        "owner_id": rows[0]["user_id"],
        "count": len(rows),
        "status": rows[0]["status"],
        "version": int(rows[0]["delivery_version"]),
    })

    row = conn.execute(
        """
        SELECT id, user_id, status, version FROM research_work_items
        WHERE source_type = 'synthetic_f11'
        """
    ).fetchone()
    result.append({
        "category": "research_task",
        "id": row["id"],
        "owner_id": row["user_id"],
        "count": 1,
        "status": row["status"],
        "version": int(row["version"]),
    })

    row = conn.execute(
        """
        SELECT id, participant_user_id, status, version
        FROM therapeutic_assessment_cases WHERE id = ?
        """,
        (by_category["therapeutic_assessment"]["id"],),
    ).fetchone()
    result.append({
        "category": "therapeutic_assessment",
        "id": row["id"],
        "owner_id": row["participant_user_id"],
        "count": 1,
        "status": row["status"],
        "version": int(row["version"]),
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    args = parser.parse_args()
    path = Path(args.fixture)
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_synthetic_migration_fixture(payload)
    if payload.get("data_class") != "synthetic_only":
        errors.append("fixture_data_class_invalid")

    applied: list[str] = []
    before: list[dict] = []
    after: list[dict] = []
    database_path: Path | None = None
    with tempfile.TemporaryDirectory(prefix="safehome-rc0810-f11-") as temp_dir:
        database_path = Path(temp_dir) / "synthetic.sqlite3"
        os.environ.update({
            "APP_ENV": "validation",
            "DB_PROVIDER": "sqlite",
            "DATABASE_PATH": str(database_path),
            "DATABASE_DATA_WATERMARK": "synthetic_validation_only",
            "CONTENT_DIR": str(ROOT / "content"),
        })
        if not errors:
            import database
            from services.schema_migration_service import MIGRATIONS, apply_pending_schema_migrations

            conn = database.get_connection()
            try:
                for statement in database.SCHEMA_SQL:
                    conn.execute(statement)
                database.ensure_schema_columns(conn)
                for statement in database.INDEX_SQL:
                    database.create_index(conn, statement)
                database.record_schema_migration(conn)
                conn.commit()
                _seed(conn, payload["records"])
                before = _snapshot(conn, payload["records"])
                applied = apply_pending_schema_migrations(conn)
                conn.commit()
                after = _snapshot(conn, payload["records"])
                ledger = [
                    row["version"]
                    for row in conn.execute(
                        "SELECT version FROM explicit_schema_migrations ORDER BY version"
                    ).fetchall()
                ]
                expected_versions = [item.version for item in MIGRATIONS]
                if applied != expected_versions or ledger != expected_versions:
                    errors.append("pending_migrations_not_fully_applied")
                if before != payload["records"] or after != before:
                    errors.append("migration_data_invariants_changed")
            finally:
                conn.close()

    result = {
        "schema": "safehome.rc0810.f11-migration-verification.v2",
        "fixture": path.name,
        "data_class": payload.get("data_class"),
        "records_compared": len(before),
        "before_after_equal": bool(before) and before == after,
        "applied_migrations": applied,
        "synthetic_database_mutated": bool(applied),
        "production_database_mutated": False,
        "database_deleted_after_verification": bool(database_path) and not database_path.exists(),
        "ok": not errors,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
