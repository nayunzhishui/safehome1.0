"""Machine audit for Task 37 P04 execution harness."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "content" / "task37_execution_harness.json"
SERVICE_PATH = ROOT / "backend" / "services" / "task37_harness_service.py"


def main() -> int:
    payload = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    service = SERVICE_PATH.read_text(encoding="utf-8")
    checks = {
        "seven_states": len(payload.get("job_states", [])) == 7,
        "independent_kill_switches": set(payload.get("kill_switches", []))
        == {"affective_computing", "social_network_analysis", "participant_ai_qa"},
        "required_metrics": {
            "throughput",
            "queue_duration_ms",
            "failure_rate",
            "coverage_rate",
            "abstention_rate",
            "cost_microunits",
            "human_backlog",
        }.issubset(payload.get("metrics", [])),
        "metadata_only_logging": payload.get("logging", {}).get("stores_raw_text") is False,
        "sensitive_rejection": "sensitive_payload_rejected" in service,
        "worker_hashing": "hashlib.sha256(worker_id.encode" in service,
        "production_disabled": payload.get("release", {}).get("production_execution_enabled") is False,
    }
    failed = sorted(key for key, value in checks.items() if not value)
    print(json.dumps({"task": "T37-P04", "checks": checks, "failed": failed}, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
