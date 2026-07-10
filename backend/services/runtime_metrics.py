"""Process-local operational counters that never store request or user content."""

from __future__ import annotations

from collections import Counter
from threading import Lock


_lock = Lock()
_counters: Counter[str] = Counter()


def record_response(status_code: int) -> None:
    with _lock:
        _counters["api_responses_total"] += 1
        if int(status_code) >= 400:
            _counters["api_errors_total"] += 1
        if int(status_code) >= 500:
            _counters["api_server_errors_total"] += 1


def record_operation_failure(operation: str) -> None:
    safe_operations = {
        "create_report": "report_generation_failures_total",
        "send_report": "message_send_failures_total",
    }
    counter = safe_operations.get(operation)
    if not counter:
        return
    with _lock:
        _counters[counter] += 1


def snapshot() -> dict:
    with _lock:
        values = dict(_counters)
    total = int(values.get("api_responses_total", 0))
    errors = int(values.get("api_errors_total", 0))
    server_errors = int(values.get("api_server_errors_total", 0))
    return {
        "api_responses_total": total,
        "api_errors_total": errors,
        "api_server_errors_total": server_errors,
        "api_error_rate": round(errors / total, 4) if total else 0.0,
        "api_server_error_rate": round(server_errors / total, 4) if total else 0.0,
        "report_generation_failures_total": int(values.get("report_generation_failures_total", 0)),
        "message_send_failures_total": int(values.get("message_send_failures_total", 0)),
        "privacy": "只记录聚合计数，不记录请求正文、绘画、句子或开放叙事。",
    }


def reset_for_tests() -> None:
    with _lock:
        _counters.clear()
