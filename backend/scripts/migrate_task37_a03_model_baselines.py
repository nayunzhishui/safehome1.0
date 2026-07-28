"""Rebuild synthetic annotation splits for the T37-A03 reproducible baseline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from config import Config
from database import get_connection, json_dumps, now_iso, rows_to_dicts
from services.affect_model_benchmark_service import synthetic_case_partition


DATASET_ID = "safehome_synthetic_affect_240_v1"
SPLIT_POLICY_VERSION = "synthetic-case-group-hash-70-15-15-v2"
CONFIRMATION = "APPLY_TASK37_A03_SYNTHETIC_SPLITS"


def _cases() -> list[dict]:
    path = Config.CONTENT_DIR / "synthetic_affect_benchmark_240.json"
    return json.loads(path.read_text(encoding="utf-8"))["cases"]


def snapshot(path: Path) -> dict:
    with get_connection() as conn:
        annotations = rows_to_dicts(
            conn.execute(
                "SELECT id, group_hash, data_split FROM offline_benchmark_annotations "
                "WHERE dataset_card_id = ? ORDER BY id",
                (DATASET_ID,),
            ).fetchall()
        )
        split_rows = rows_to_dicts(
            conn.execute(
                "SELECT * FROM offline_annotation_group_splits "
                "WHERE dataset_card_id = ? ORDER BY id",
                (DATASET_ID,),
            ).fetchall()
        )
    payload = {
        "dataset_id": DATASET_ID,
        "annotations": annotations,
        "group_splits": split_rows,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_dumps(payload), encoding="utf-8")
    return {"snapshot_path": str(path), "annotation_count": len(annotations)}


def apply(snapshot_path: Path) -> dict:
    snapshot_result = snapshot(snapshot_path)
    cases = {case["id"]: case for case in _cases()}
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM offline_annotation_group_splits WHERE dataset_card_id = ?",
            (DATASET_ID,),
        )
        for case in cases.values():
            group_hash, split_name = synthetic_case_partition(case)
            conn.execute(
                "INSERT INTO offline_annotation_group_splits "
                "(id, dataset_card_id, group_hash, split_name, split_policy_version, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    f"oas_{group_hash[:24]}",
                    DATASET_ID,
                    group_hash,
                    split_name,
                    SPLIT_POLICY_VERSION,
                    timestamp,
                ),
            )
        annotation_rows = conn.execute(
            "SELECT id, case_id FROM offline_benchmark_annotations WHERE dataset_card_id = ?",
            (DATASET_ID,),
        ).fetchall()
        for row in annotation_rows:
            case = cases.get(row["case_id"])
            if case is None:
                raise RuntimeError(f"annotation case missing from synthetic fixture: {row['case_id']}")
            group_hash, split_name = synthetic_case_partition(case)
            conn.execute(
                "UPDATE offline_benchmark_annotations SET group_hash = ?, data_split = ?, updated_at = ? "
                "WHERE id = ?",
                (group_hash, split_name, timestamp, row["id"]),
            )
        conn.commit()
    return {"action": "apply", **snapshot_result, **verify(), "production_mutation": False}


def verify() -> dict:
    expected = {case["id"]: synthetic_case_partition(case) for case in _cases()}
    split_counts: dict[str, int] = {}
    mismatches: list[str] = []
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT case_id, group_hash, data_split FROM offline_benchmark_annotations "
            "WHERE dataset_card_id = ?",
            (DATASET_ID,),
        ).fetchall()
        group_rows = conn.execute(
            "SELECT group_hash, split_name, split_policy_version "
            "FROM offline_annotation_group_splits WHERE dataset_card_id = ?",
            (DATASET_ID,),
        ).fetchall()
    for row in group_rows:
        split_counts[row["split_name"]] = split_counts.get(row["split_name"], 0) + 1
        if row["split_policy_version"] != SPLIT_POLICY_VERSION:
            mismatches.append(row["group_hash"])
    for row in rows:
        if expected.get(row["case_id"]) != (row["group_hash"], row["data_split"]):
            mismatches.append(row["case_id"])
    return {
        "ok": not mismatches
        and set(split_counts) == {"train", "validation", "test"}
        and sum(split_counts.values()) == 240,
        "split_counts": split_counts,
        "mismatches": sorted(set(mismatches)),
        "split_policy_version": SPLIT_POLICY_VERSION,
    }


def rollback(snapshot_path: Path) -> dict:
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if payload.get("dataset_id") != DATASET_ID:
        raise RuntimeError("snapshot dataset mismatch")
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM offline_annotation_group_splits WHERE dataset_card_id = ?",
            (DATASET_ID,),
        )
        for row in payload["group_splits"]:
            conn.execute(
                "INSERT INTO offline_annotation_group_splits "
                "(id, dataset_card_id, group_hash, split_name, split_policy_version, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    row["id"],
                    row["dataset_card_id"],
                    row["group_hash"],
                    row["split_name"],
                    row["split_policy_version"],
                    row["created_at"],
                ),
            )
        for row in payload["annotations"]:
            conn.execute(
                "UPDATE offline_benchmark_annotations SET group_hash = ?, data_split = ? WHERE id = ?",
                (row["group_hash"], row["data_split"], row["id"]),
            )
        conn.commit()
    return {
        "action": "rollback",
        "restored_annotation_count": len(payload["annotations"]),
        "restored_group_count": len(payload["group_splits"]),
        "production_mutation": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["plan", "apply", "verify", "rollback"])
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--allow-production", action="store_true")
    parser.add_argument("--confirmation", default="")
    args = parser.parse_args()
    production = str(Config.APP_ENV).lower() == "production"
    if args.action in {"apply", "rollback"} and args.snapshot is None:
        raise RuntimeError("apply/rollback requires --snapshot")
    if production and args.action in {"apply", "rollback"} and (
        not args.allow_production or args.confirmation != CONFIRMATION
    ):
        raise RuntimeError("生产数据迁移已阻断：需要备份恢复证据和精确确认短语")
    if args.action == "plan":
        result = {
            "action": "plan",
            "dataset_id": DATASET_ID,
            "split_policy_version": SPLIT_POLICY_VERSION,
            "requires_snapshot": True,
            "production_mutation": False,
        }
    elif args.action == "apply":
        result = apply(args.snapshot)
    elif args.action == "rollback":
        result = rollback(args.snapshot)
    else:
        result = {"action": "verify", **verify(), "production_mutation": False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
