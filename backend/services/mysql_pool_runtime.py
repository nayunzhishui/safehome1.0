"""Optional MySQL connection-pool adapter for SafeHome.

The legacy database module intentionally keeps its sqlite-compatible API.  This
module swaps only the MySQLConnection constructor before the Flask app imports
routes, so existing services keep calling ``database.get_connection()``.

The pool is process-local (one pool per Gunicorn worker) and never contains
application data beyond normal DB connections.
"""

from __future__ import annotations

import os
import threading
from typing import Any

from config import Config


_LOCK = threading.Lock()
_POOL = None
_INSTALL_STATE = {
    "installed": False,
    "enabled": False,
    "reason": "not_initialized",
}


def _bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(value, maximum))


def pool_settings() -> dict[str, Any]:
    max_connections = _int("MYSQL_POOL_MAX_CONNECTIONS", 7, 1, 64)
    max_cached = _int("MYSQL_POOL_MAX_CACHED", 5, 0, max_connections)
    min_cached = _int("MYSQL_POOL_MIN_CACHED", 1, 0, max_cached or 1)
    return {
        "enabled": _bool("MYSQL_POOL_ENABLED", default=Config.DB_PROVIDER == "mysql"),
        "min_cached": min_cached,
        "max_cached": max_cached,
        "max_connections": max_connections,
        "blocking": True,
        "connect_timeout_seconds": _int("MYSQL_CONNECT_TIMEOUT_SECONDS", 5, 1, 60),
        "read_timeout_seconds": _int("MYSQL_READ_TIMEOUT_SECONDS", 10, 1, 120),
        "write_timeout_seconds": _int("MYSQL_WRITE_TIMEOUT_SECONDS", 10, 1, 120),
        "ssl_ca_configured": bool(os.environ.get("MYSQL_SSL_CA", "").strip()),
        "ssl_verify_identity": _bool("MYSQL_SSL_VERIFY_IDENTITY", default=True),
    }


def _creator_kwargs() -> dict[str, Any]:
    import pymysql

    settings = pool_settings()
    kwargs: dict[str, Any] = {
        "host": Config.MYSQL_HOST,
        "port": Config.MYSQL_PORT,
        "user": Config.MYSQL_USER,
        "password": Config.MYSQL_PASSWORD,
        "database": Config.MYSQL_DATABASE,
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": False,
        "connect_timeout": settings["connect_timeout_seconds"],
        "read_timeout": settings["read_timeout_seconds"],
        "write_timeout": settings["write_timeout_seconds"],
    }
    ssl_ca = os.environ.get("MYSQL_SSL_CA", "").strip()
    if ssl_ca:
        kwargs.update(
            {
                "ssl_ca": ssl_ca,
                "ssl_verify_cert": True,
                "ssl_verify_identity": settings["ssl_verify_identity"],
            }
        )
    return kwargs


def _get_pool():
    global _POOL
    if _POOL is not None:
        return _POOL
    with _LOCK:
        if _POOL is not None:
            return _POOL
        try:
            import pymysql
            from dbutils.pooled_db import PooledDB
        except ImportError as exc:  # pragma: no cover - dependency smoke covers this in CI
            raise RuntimeError("MySQL连接池需要 PyMySQL 与 DBUtils") from exc
        settings = pool_settings()
        _POOL = PooledDB(
            creator=pymysql,
            mincached=settings["min_cached"],
            maxcached=settings["max_cached"],
            maxconnections=settings["max_connections"],
            blocking=True,
            maxusage=None,
            setsession=[],
            ping=1,
            **_creator_kwargs(),
        )
    return _POOL


class PooledMySQLConnection:
    """Drop-in adapter matching ``database.MySQLConnection``."""

    provider = "mysql"

    def __init__(self):
        self._connection = _get_pool().connection(shareable=False)

    def __enter__(self):
        self._connection.ping(reconnect=True)
        return self

    def __exit__(self, exc_type, exc, traceback):
        if exc_type is None:
            self.commit()
        else:
            try:
                self._connection.rollback()
            except Exception:
                pass
        self.close()
        return False

    def execute(self, sql: str, params=None):
        # Import lazily to avoid a database -> pool -> database import cycle.
        from database import _mysqlize_query

        self._connection.ping(reconnect=True)
        cursor = self._connection.cursor()
        cursor.execute(_mysqlize_query(sql), tuple(params or ()))
        return cursor

    def commit(self) -> None:
        self._connection.commit()

    def rollback(self) -> None:
        self._connection.rollback()

    def close(self) -> None:
        # DBUtils returns the physical connection to the process-local pool.
        self._connection.close()


def install_mysql_pool() -> dict[str, Any]:
    """Install the pool adapter before ``app`` imports route modules."""
    global _INSTALL_STATE
    if Config.DB_PROVIDER != "mysql":
        _INSTALL_STATE = {"installed": False, "enabled": False, "reason": "sqlite_provider"}
        return status()
    settings = pool_settings()
    if not settings["enabled"]:
        _INSTALL_STATE = {"installed": False, "enabled": False, "reason": "disabled_by_config"}
        return status()

    import database

    database.MySQLConnection = PooledMySQLConnection
    _INSTALL_STATE = {"installed": True, "enabled": True, "reason": "installed"}
    return status()


def status() -> dict[str, Any]:
    return {
        **_INSTALL_STATE,
        "provider": Config.DB_PROVIDER,
        "settings": pool_settings(),
        "pool_created": _POOL is not None,
    }
