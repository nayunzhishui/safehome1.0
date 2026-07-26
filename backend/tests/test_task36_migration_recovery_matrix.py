import json
import hashlib
import hmac
import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from scripts.task36_migration_recovery import exercise, mysql57_contract, production_command, rollback_plan
from scripts.verify_privacy_restore import verify as verify_privacy_restore


def test_f18_exercises_empty_legacy_repeat_partial_interrupt_and_restore(tmp_path):
    lab = tmp_path / "lab"
    result = exercise(lab)
    assert result["ok"] is True
    assert all(result["scenarios"].values())
    assert result["target_schema"]["version"] == "2026_07_26_029"
    assert len(result["backup_manifest"]["sha256"]) == 64
    assert len(result["backup_manifest"]["schema_hash"]) == 64
    assert result["backup_manifest"]["table_row_counts"] == result["restore_manifest"]["table_row_counts"]
    assert result["production_mutation_executed"] is False

    repeated = exercise(lab)
    assert repeated["ok"] is True
    assert all(repeated["scenarios"].values())


def test_f18_mysql57_contract_is_additive_and_index_safe():
    result = mysql57_contract()
    assert result["ok"] is True
    assert result["placeholder_conversion_ok"] is True
    assert result["invalid_text_defaults"] == []
    assert result["destructive_statements"] == []
    assert result["indexed_text_columns"] == []
    assert result["oversized_indexes"] == []


def test_f18_rollback_and_production_commands_do_not_mutate():
    rollback = rollback_plan()
    assert rollback["drop_tables"] is False
    assert rollback["delete_history"] is False
    assert rollback["delete_audit"] is False
    assert rollback["requires_human_approval"] is True
    assert rollback["steps"][-1] == "retain_additive_tables_versions_and_audit"

    for action in ("apply", "restore", "rollback"):
        generated = production_command(action)
        assert generated["command_generated_only"] is True
        assert generated["production_mutation_executed"] is False
        assert generated["requires_human_approval"] is True


def test_f18_machine_matrix_covers_required_slices():
    matrix = json.loads((ROOT / "config" / "task36_migration_matrix.json").read_text(encoding="utf-8"))
    assert set(matrix["covered_slices"]) == {"T36-F03", "T36-F12", "T36-F13", "T36-F16"}
    assert matrix["production_policy"] == {
        "automatic_apply": False,
        "automatic_restore": False,
        "automatic_rollback": False,
        "drop_tables": False,
        "delete_audit": False,
        "requires_human_approval": True,
    }


def test_f18_restored_backup_rechecks_therapeutic_assessment_tombstone(tmp_path):
    path = tmp_path / "restored-with-deleted-user.sqlite3"
    secret = b"synthetic-tombstone-secret"
    user_id = "deleted-participant-f18"
    subject_hash = hmac.new(secret, user_id.encode(), hashlib.sha256).hexdigest()
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE privacy_deletion_tombstones (subject_hash TEXT, replacement_user_id TEXT, scope_json TEXT)")
        conn.execute("CREATE TABLE therapeutic_assessment_cases (id TEXT PRIMARY KEY, participant_user_id TEXT)")
        conn.execute("CREATE TABLE therapeutic_assessment_actions (id TEXT PRIMARY KEY, participant_user_id TEXT)")
        conn.execute("CREATE TABLE therapeutic_assessment_feedback_versions (id TEXT PRIMARY KEY, case_id TEXT)")
        conn.execute("CREATE TABLE therapeutic_assessment_events (id TEXT PRIMARY KEY, case_id TEXT)")
        conn.execute("INSERT INTO privacy_deletion_tombstones VALUES (?, NULL, '[\"therapeutic_assessment\"]')", (subject_hash,))
        conn.execute("INSERT INTO therapeutic_assessment_cases VALUES ('case-f18', ?)", (user_id,))
        conn.execute("INSERT INTO therapeutic_assessment_actions VALUES ('action-f18', ?)", (user_id,))
        conn.execute("INSERT INTO therapeutic_assessment_feedback_versions VALUES ('feedback-f18', 'case-f18')")
        conn.execute("INSERT INTO therapeutic_assessment_events VALUES ('event-f18', 'case-f18')")
        conn.commit()
    blocked = verify_privacy_restore(path, secret)
    assert blocked["ok"] is False
    assert set(blocked["violation_counts"]) == {
        "therapeutic_assessment_cases",
        "therapeutic_assessment_actions",
        "therapeutic_assessment_feedback_versions",
        "therapeutic_assessment_events",
    }
