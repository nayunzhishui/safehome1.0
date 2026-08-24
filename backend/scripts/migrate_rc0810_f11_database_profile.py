"""Validate the F11 synthetic migration manifest; never mutates a database."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from services.database_profile_service import validate_synthetic_migration_fixture  # noqa: E402


DEFAULT_FIXTURE = BACKEND / "tests" / "fixtures" / "rc0810_f11_synthetic_migration.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    args = parser.parse_args()
    path = Path(args.fixture)
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_synthetic_migration_fixture(payload)
    result = {
        "schema": "safehome.rc0810.f11-migration-verification.v1",
        "fixture": path.name,
        "data_class": payload.get("data_class"),
        "records_compared": len(payload.get("before", [])),
        "ok": not errors and payload.get("data_class") == "synthetic_only",
        "errors": errors,
        "database_mutated": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
