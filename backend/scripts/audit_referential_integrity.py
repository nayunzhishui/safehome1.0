"""Read-only referential-integrity audit for SafeHome SQLite/MySQL schemas."""

from __future__ import annotations

import json
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from database import get_connection, init_db  # noqa: E402
from services.referential_integrity_service import audit_referential_integrity  # noqa: E402


def main() -> int:
    init_db()
    with get_connection() as conn:
        result = audit_referential_integrity(conn)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
