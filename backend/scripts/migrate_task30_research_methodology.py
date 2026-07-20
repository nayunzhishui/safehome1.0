"""Task 30 idempotent migration, score-provenance backfill, and rollback plan."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from database import (  # noqa: E402
    CURRENT_SCHEMA_VERSION,
    get_connection,
    init_db,
    json_dumps,
    json_loads,
    list_database_columns,
    list_database_tables,
    write_audit_log,
)
from services.assessment_execution_service import build_score_provenance  # noqa: E402


TABLES = (
    "research_methodology_versions",
    "research_methodology_checks",
    "research_methodology_simulation_runs",
    "research_methodology_evidence_packages",
    "research_methodology_runtime_control",
)
SCORE_COLUMNS = (
    "scoring_version",
    "raw_scale_json",
    "raw_scores_json",
    "transformed_scores_json",
    "transformation_version",
)


def _worksheets() -> dict[str, dict]:
    payload = json.loads((PROJECT_ROOT / "content" / "assessment_worksheets.json").read_text(encoding="utf-8"))
    return {item["id"]: item for item in payload.get("worksheets", [])}


def backfill_score_provenance() -> dict:
    worksheet_map = _worksheets()
    updated = skipped_unknown = already_present = 0
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT id, worksheet_id, answers_json, scores_json, scoring_version,
                      raw_scale_json, raw_scores_json, transformed_scores_json,
                      transformation_version
               FROM assessment_results ORDER BY created_at, id"""
        ).fetchall()
        for row in rows:
            worksheet = worksheet_map.get(row["worksheet_id"])
            if not worksheet:
                skipped_unknown += 1
                continue
            has_provenance = bool(row["scoring_version"]) and json_loads(row["raw_scores_json"], {}) not in ({}, None)
            if has_provenance:
                already_present += 1
                continue
            provenance = build_score_provenance(
                worksheet,
                json_loads(row["answers_json"], []),
                json_loads(row["scores_json"], {}),
            )
            conn.execute(
                """UPDATE assessment_results
                   SET scoring_version = ?, raw_scale_json = ?, raw_scores_json = ?,
                       transformed_scores_json = ?, transformation_version = ?
                   WHERE id = ?""",
                (
                    provenance["scoring_version"],
                    json_dumps(provenance["raw_scale"]),
                    json_dumps(provenance["raw_scores"]),
                    json_dumps(provenance["transformed_scores"]),
                    provenance["transformation_version"],
                    row["id"],
                ),
            )
            updated += 1
        if updated:
            write_audit_log(
                conn,
                "task30_score_provenance_backfilled",
                "system:migration",
                "assessment_results",
                "task30",
                {
                    "updated_count": updated,
                    "unknown_worksheet_count": skipped_unknown,
                    "raw_score_preserved": True,
                    "formal_freeze_recorded": False,
                    "outcome_rows_read": 0,
                },
            )
        conn.commit()
    return {"updated": updated, "already_present": already_present, "unknown_worksheet": skipped_unknown}


def audit() -> dict:
    with get_connection() as conn:
        existing = {row["name"] for row in list_database_tables(conn)}
        counts = {
            table: int(conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])
            if table in existing else None
            for table in TABLES
        }
        columns = {row["name"] for row in list_database_columns(conn, "assessment_results")}
        missing_score_columns = sorted(set(SCORE_COLUMNS) - columns)
        migration = conn.execute(
            "SELECT version, name, applied_at FROM schema_migrations WHERE version = ?",
            (CURRENT_SCHEMA_VERSION,),
        ).fetchone()
    return {
        "ok": all(table in existing for table in TABLES) and not missing_score_columns and migration is not None,
        "schema_version": CURRENT_SCHEMA_VERSION,
        "tables": counts,
        "missing_score_columns": missing_score_columns,
        "migration_recorded": dict(migration) if migration else None,
        "formal_freeze_recorded": False,
        "real_outcome_rows_read": 0,
    }


def rollback_plan() -> dict:
    return {
        "automatic_rollback_executed": False,
        "safe_rollback_steps": [
            "设置 RESEARCH_METHODOLOGY_WORKBENCH_ENABLED=0",
            "保持 RESEARCH_METHODOLOGY_FORMAL_FREEZE_ALLOWED=0 和 RESEARCH_OUTCOME_ANALYSIS_ALLOWED=0",
            "管理员调用只允许停用的运行控制",
            "隐藏 Web 研究方法工作台并取消方法学 API 路由注册",
            "保留研究方法版本、机器检查、合成仿真、证据包和审计记录只读",
            "保留 assessment_results 原分、转换分和版本字段，避免再次混写量尺",
        ],
        "destructive_step_requires_human_approval": True,
        "human_signature_inferred": False,
        "ethics_approval_inferred": False,
        "formal_freeze_inferred": False,
        "production_release_inferred": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--rollback-plan", action="store_true")
    args = parser.parse_args()
    backfill = None
    if args.apply:
        init_db()
        backfill = backfill_score_provenance()
    result = rollback_plan() if args.rollback_plan else audit()
    if backfill is not None:
        result["backfill"] = backfill
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if args.rollback_plan or result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
