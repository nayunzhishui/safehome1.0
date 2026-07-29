import sqlite3
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from services.assessment_profile_position_store import (
    backfill_profile_position,
    profile_cluster_value,
)


def test_profile_position_store_normalizes_and_persists_position():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE assessment_results (
            id TEXT PRIMARY KEY,
            profile_model_id TEXT,
            profile_cluster_id INTEGER,
            profile_pc1 REAL,
            profile_pc2 REAL,
            profile_confidence REAL
        )
        """
    )
    conn.execute("INSERT INTO assessment_results (id) VALUES ('result-1')")

    backfill_profile_position(
        conn,
        "result-1",
        {
            "model_id": "model-1",
            "position": {
                "cluster_id": "3",
                "pc1": 1.2,
                "pc2": -0.4,
                "confidence": 0.82,
            },
        },
    )

    row = conn.execute(
        """
        SELECT profile_model_id, profile_cluster_id, profile_pc1,
               profile_pc2, profile_confidence
        FROM assessment_results WHERE id = 'result-1'
        """
    ).fetchone()
    assert row == ("model-1", 3, 1.2, -0.4, 0.82)
    assert profile_cluster_value({"cluster_id": ""}) is None
    assert profile_cluster_value({"cluster_id": "not-a-number"}) is None
