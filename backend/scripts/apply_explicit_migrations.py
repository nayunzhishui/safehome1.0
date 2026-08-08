"""Inspect or apply SafeHome explicit additive migrations.

Examples:
    python backend/scripts/apply_explicit_migrations.py --list
    python backend/scripts/apply_explicit_migrations.py --apply

This script never performs destructive rollback.  Rollback notes are printed so
an operator/Codex can review them before any manual reversal.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from database import get_connection  # noqa: E402
from services.schema_migration_service import apply_pending_schema_migrations, migration_manifest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true", help="Print migration manifest without changing DB")
    parser.add_argument("--apply", action="store_true", help="Apply pending migrations")
    args = parser.parse_args()

    manifest = migration_manifest()
    if args.list or not args.apply:
        print(json.dumps({"migrations": manifest}, ensure_ascii=False, indent=2))
        if not args.apply:
            return 0

    with get_connection() as conn:
        applied = apply_pending_schema_migrations(conn)
        conn.commit()
    print(json.dumps({"ok": True, "applied": applied, "manifest": manifest}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
