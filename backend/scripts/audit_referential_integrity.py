"""Read-only referential-integrity audit for SafeHome SQLite/MySQL schemas."""

from __future__ import annotations

import json

from database import get_connection, init_db
from services.referential_integrity_service import audit_referential_integrity


def main() -> int:
    init_db()
    with get_connection() as conn:
        result = audit_referential_integrity(conn)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
