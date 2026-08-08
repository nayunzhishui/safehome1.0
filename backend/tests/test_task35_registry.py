import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_task35_registry_covers_f00_to_f15_without_claiming_production():
    registry = json.loads(
        (ROOT / "config" / "task35_registry.json").read_text(encoding="utf-8")
    )
    assert [item["id"] for item in registry["tasks"]] == [
        f"T35-F{index:02d}" for index in range(16)
    ]
    assert registry["production_replacement_allowed"] is False
    assert any("pending" in item["status"] for item in registry["tasks"])
    assert any(item["status"] == "not_started_by_gate" for item in registry["tasks"])


def test_task35_verifier_binds_frozen_artifact_hashes():
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_task35.py"), "verify"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)
    assert result["status"] == "passed"
    assert result["engineering_task_count"] == 16
    assert result["production_replacement_allowed"] is False
    assert result["external_download_started"] is False
