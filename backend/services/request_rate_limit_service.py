"""Shared request protection using the existing database counter table."""

from contextlib import closing
from datetime import datetime, timezone
import time

from database import get_connection, new_id


def increment_db_limit(conn, *, dimension, dimension_hash, window_key, timestamp):
    params = (new_id('request_limit'), dimension, dimension_hash, window_key,
              timestamp, timestamp, timestamp)
    if getattr(conn, 'provider', 'sqlite') == 'mysql':
        update = '''ON DUPLICATE KEY UPDATE attempt_count = attempt_count + 1,
            last_attempt_at = VALUES(last_attempt_at), updated_at = VALUES(updated_at)'''
    else:
        update = '''ON CONFLICT(dimension, dimension_hash, window_key) DO UPDATE SET
            attempt_count = family_bind_rate_limits.attempt_count + 1,
            last_attempt_at = excluded.last_attempt_at, updated_at = excluded.updated_at'''
    conn.execute('''INSERT INTO family_bind_rate_limits
        (id, dimension, dimension_hash, window_key, attempt_count,
         last_attempt_at, created_at, updated_at)
        VALUES (?, ?, ?, ?, 1, ?, ?, ?) ''' + update, params)
    row = conn.execute('''SELECT attempt_count FROM family_bind_rate_limits
        WHERE dimension = ? AND dimension_hash = ? AND window_key = ?''',
        (dimension, dimension_hash, window_key)).fetchone()
    return int(row['attempt_count'])


def rate_limit(key, *, limit, window_seconds):
    """Count in a separate committed transaction; database failure blocks requests.

    Callers pass a namespaced, already hashed identity, never a raw IP or token.
    Later requests clean runtime windows older than one day; family binding
    keeps its own ledger.
    """
    dimension, digest = key.split(':', 1)
    limit, window_seconds = max(1, int(limit)), max(1, int(window_seconds))
    now = int(time.time())
    start = now // window_seconds * window_seconds
    timestamp = datetime.fromtimestamp(now, timezone.utc).isoformat()
    window_key = datetime.fromtimestamp(start, timezone.utc).isoformat()
    cutoff = datetime.fromtimestamp(now - 86400, timezone.utc).isoformat()
    decision = {'available': False, 'allowed': False, 'limit': limit,
                'remaining': 0, 'retry_after': max(1, start + window_seconds - now),
                'reason': 'database_unavailable'}
    try:
        with closing(get_connection()) as conn:
            try:
                # The existing unique key serializes competing workers' updates.
                count = increment_db_limit(conn, dimension=dimension,
                    dimension_hash=digest, window_key=window_key, timestamp=timestamp)
                conn.execute('''DELETE FROM family_bind_rate_limits
                    WHERE dimension = ? AND window_key < ?''', (dimension, cutoff))
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        decision.update(available=True, allowed=count <= limit,
                        remaining=max(0, limit - count),
                        reason='allowed' if count <= limit else 'rate_limited')
    except Exception:
        pass
    return decision
