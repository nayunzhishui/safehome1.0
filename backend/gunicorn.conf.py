"""Gunicorn runtime defaults for SafeHome.

The configuration keeps the application as a modular monolith.  Values are
controlled by environment variables so CloudBase can tune capacity without
rewriting the image.
"""

from __future__ import annotations

import multiprocessing
import os


def _int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except ValueError:
        value = default
    return max(minimum, min(value, maximum))


bind = f"0.0.0.0:{os.environ.get('PORT', '5050')}"
workers = _int("WEB_CONCURRENCY", 2, 1, max(2, multiprocessing.cpu_count() * 2 + 1))
worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "gthread")
threads = _int("WEB_THREADS", 4, 1, 32)
timeout = _int("GUNICORN_TIMEOUT_SECONDS", 30, 5, 180)
graceful_timeout = _int("GUNICORN_GRACEFUL_TIMEOUT_SECONDS", 30, 5, 180)
keepalive = _int("GUNICORN_KEEPALIVE_SECONDS", 5, 1, 30)
max_requests = _int("GUNICORN_MAX_REQUESTS", 1000, 100, 100000)
max_requests_jitter = _int("GUNICORN_MAX_REQUESTS_JITTER", 100, 0, 10000)
preload_app = False
capture_output = True
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info").lower()
forwarded_allow_ips = os.environ.get("FORWARDED_ALLOW_IPS", "127.0.0.1")

# /dev/shm avoids slow temporary-file heartbeat writes in containerized Linux.
if os.path.isdir("/dev/shm"):
    worker_tmp_dir = "/dev/shm"


def when_ready(server):
    server.log.info(
        "safehome gunicorn ready workers=%s threads=%s worker_class=%s timeout=%ss",
        workers,
        threads,
        worker_class,
        timeout,
    )
