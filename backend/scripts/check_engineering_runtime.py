"""Print a redacted preflight summary for SafeHome engineering/AI runtime."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from config import Config
from services.agent_runtime_service import public_policy
from services.embedding_service import public_status as embedding_status
from services.mysql_pool_runtime import pool_settings
from services.rag_v2_service import settings as rag_settings
from services.redis_service import settings as redis_settings
from services.schema_migration_service import migration_manifest


def _enabled(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def main() -> int:
    Config.validate()
    payload = {
        "app_env": Config.APP_ENV,
        "db_provider": Config.DB_PROVIDER,
        "mysql": {
            "configured": all([Config.MYSQL_HOST, Config.MYSQL_USER, Config.MYSQL_DATABASE]) if Config.DB_PROVIDER == "mysql" else False,
            "password_configured": bool(Config.MYSQL_PASSWORD) if Config.DB_PROVIDER == "mysql" else False,
            "pool": pool_settings(),
        },
        "redis": redis_settings(),
        "rag": {
            "v2_enabled": _enabled("RAG_V2_ENABLED", True),
            "retrieval": rag_settings(),
            "embedding": embedding_status(),
        },
        "agent": public_policy(),
        "migrations": migration_manifest(),
        "existing_ai_qa": {
            "enabled": bool(Config.AI_QA_ENABLED),
            "sandbox_enabled": bool(Config.AI_QA_SANDBOX_ENABLED),
            "provider": Config.AI_QA_PROVIDER,
            "real_provider_enabled": bool(Config.AI_QA_REAL_PROVIDER_ENABLED),
        },
        "proxy": {
            "trust_proxy_hops": int(os.environ.get("TRUST_PROXY_HOPS", "0") or 0),
            "forwarded_allow_ips_configured": bool(os.environ.get("FORWARDED_ALLOW_IPS", "").strip()),
        },
        "secrets": {
            "values_printed": False,
            "mysql_password_value_printed": False,
            "redis_url_value_printed": False,
            "embedding_api_key_value_printed": False,
        },
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
