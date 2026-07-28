"""Synthetic drift, fairness and rollback drills for registered affect models."""

from __future__ import annotations

import hashlib
import json

from flask import current_app

from database import (
    get_connection,
    json_dumps,
    json_loads,
    new_id,
    now_iso,
    row_to_dict,
    write_audit_log,
)
from services.affect_shadow_service import AffectShadowError


SCENARIO_VALUES = {
    "baseline": {},
    "input_length_shift": {"mean_input_length_delta": 0.62},
    "label_distribution_shift": {"label_distribution_jsd": 0.31},
    "colloquial_style_shift": {"colloquial_style_rate_delta": 0.36},
    "missingness_spike": {"missing_rate": 0.34},
    "abstention_spike": {"abstention_rate": 0.57},
    "subgroup_error_gap": {"maximum_subgroup_error_gap": 0.29},
    "human_overturn_spike": {"human_overturn_rate": 0.39},
    "provider_exception": {"provider_exception_rate": 0.18},
}
BASELINE_METRICS = {
    "mean_input_length_delta": 0.04,
    "label_distribution_jsd": 0.03,
    "colloquial_style_rate_delta": 0.05,
    "missing_rate": 0.0,
    "abstention_rate": 0.11,
    "maximum_subgroup_error_gap": 0.06,
    "human_overturn_rate": 0.0,
    "provider_exception_rate": 0.0,
}
RUNTIME_ACTIONS = {
    "model_rollback",
    "threshold_rollback",
    "readonly_degrade",
    "full_disable",
}


def _policy() -> dict:
    path = current_app.config["CONTENT_DIR"] / "affect_monitoring_policy.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _decode_monitor(row) -> dict:
    item = row_to_dict(row)
    item["metrics"] = json_loads(item.pop("metrics_json"), {})
    item["triggers"] = json_loads(item.pop("triggers_json"), [])
    return item


def _current_control() -> dict:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM offline_model_runtime_controls WHERE id = 'global'"
        ).fetchone()
    if row:
        return row_to_dict(row)
    return {
        "id": "global",
        "mode": "shadow",
        "active_model_version_id": None,
        "active_threshold_hash": None,
        "version": 0,
        "reason": "initial_shadow_default",
        "changed_by": "system",
        "changed_at": None,
    }


def get_monitoring_status() -> dict:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM offline_model_monitor_runs ORDER BY created_at DESC LIMIT 20"
        ).fetchall()
    policy = _policy()
    return {
        "policy_version": policy["version"],
        "runtime_control": _current_control(),
        "recent_runs": [_decode_monitor(row) for row in rows],
        "participant_feedback_dependency": False,
        "training_card_dependency": False,
        "group_difference_interpretation": policy["group_difference_interpretation"],
        "boundary_notice": policy["boundary_notice"],
    }


def _set_control(
    actor: dict,
    *,
    mode: str,
    model_version_id: str | None,
    threshold_hash: str | None,
    reason: str,
) -> dict:
    current = _current_control()
    timestamp = now_iso()
    version = int(current["version"]) + 1
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO offline_model_runtime_controls "
            "(id, mode, active_model_version_id, active_threshold_hash, version, reason, changed_by, changed_at) "
            "VALUES ('global', ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET mode = excluded.mode, "
            "active_model_version_id = excluded.active_model_version_id, "
            "active_threshold_hash = excluded.active_threshold_hash, version = excluded.version, "
            "reason = excluded.reason, changed_by = excluded.changed_by, changed_at = excluded.changed_at",
            (
                mode,
                model_version_id,
                threshold_hash,
                version,
                reason,
                actor["id"],
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "offline_model_runtime_changed",
            actor["id"],
            "offline_model_runtime",
            "global",
            {
                "from_mode": current["mode"],
                "to_mode": mode,
                "version": version,
                "reason": reason,
                "participant_feedback_changed": False,
                "training_cards_changed": False,
            },
        )
        conn.commit()
    return _current_control()


def run_monitor_drill(actor: dict, scenario: str, model_version_id: str | None) -> dict:
    policy = _policy()
    if scenario not in SCENARIO_VALUES:
        raise AffectShadowError(
            "monitor_scenario_invalid", "未知的合成漂移或异常演练场景"
        )
    if model_version_id:
        with get_connection() as conn:
            exists = conn.execute(
                "SELECT id FROM offline_model_versions WHERE id = ?",
                (model_version_id,),
            ).fetchone()
        if not exists:
            raise AffectShadowError("model_version_not_found", "模型版本不存在", 404)
    metrics = {**BASELINE_METRICS, **SCENARIO_VALUES[scenario]}
    triggers = []
    gate_status = "green"
    for metric, value in metrics.items():
        thresholds = policy["metrics"][metric]
        if float(value) >= float(thresholds["red"]):
            level = "red"
            gate_status = "red_stopped"
        elif float(value) >= float(thresholds["yellow"]):
            level = "yellow"
            if gate_status == "green":
                gate_status = "yellow_review"
        else:
            continue
        triggers.append(
            {
                "metric": metric,
                "value": value,
                "level": level,
                "threshold": thresholds[level],
            }
        )
    timestamp = now_iso()
    run_id = new_id("omr")
    artifact_hash = hashlib.sha256(
        json_dumps(
            {
                "policy_version": policy["version"],
                "scenario": scenario,
                "model_version_id": model_version_id,
                "metrics": metrics,
                "triggers": triggers,
                "gate_status": gate_status,
            }
        ).encode("utf-8")
    ).hexdigest()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO offline_model_monitor_runs "
            "(id, scenario, model_version_id, metrics_json, triggers_json, gate_status, "
            "artifact_hash, contains_real_data, created_by, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)",
            (
                run_id,
                scenario,
                model_version_id,
                json_dumps(metrics),
                json_dumps(triggers),
                gate_status,
                artifact_hash,
                actor["id"],
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "offline_model_monitor_drill",
            actor["id"],
            "offline_model_monitor_run",
            run_id,
            {
                "scenario": scenario,
                "gate_status": gate_status,
                "contains_real_data": False,
            },
        )
        conn.commit()
    if gate_status == "red_stopped":
        _set_control(
            actor,
            mode="off",
            model_version_id=model_version_id,
            threshold_hash=None,
            reason=f"red_monitor_trigger:{scenario}",
        )
    elif gate_status == "yellow_review":
        _set_control(
            actor,
            mode="readonly_degraded",
            model_version_id=model_version_id,
            threshold_hash=None,
            reason=f"yellow_monitor_trigger:{scenario}",
        )
    with get_connection() as conn:
        saved = conn.execute(
            "SELECT * FROM offline_model_monitor_runs WHERE id = ?", (run_id,)
        ).fetchone()
    result = _decode_monitor(saved)
    result["runtime_control"] = _current_control()
    result["boundary_notice"] = policy["boundary_notice"]
    return result


def apply_runtime_action(actor: dict, action: str, data: dict) -> dict:
    if action not in RUNTIME_ACTIONS:
        raise AffectShadowError("runtime_action_invalid", "未知的模型回滚动作")
    reason = str(data.get("reason") or "").strip()
    if len(reason) < 5 or len(reason) > 300:
        raise AffectShadowError("runtime_reason_invalid", "回滚原因需为5至300字")
    current = _current_control()
    model_version_id = str(data.get("model_version_id") or "") or None
    threshold_hash = str(data.get("threshold_hash") or "") or None
    if action in {"model_rollback", "threshold_rollback"}:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id, threshold_hash FROM offline_model_versions WHERE id = ?",
                (model_version_id,),
            ).fetchone()
        if not row:
            raise AffectShadowError("model_version_not_found", "回滚目标模型不存在", 404)
        if action == "threshold_rollback":
            if threshold_hash != row["threshold_hash"]:
                raise AffectShadowError(
                    "threshold_not_registered", "阈值回滚只能选择已登记版本"
                )
        else:
            threshold_hash = row["threshold_hash"]
        mode = "shadow"
    elif action == "readonly_degrade":
        mode = "readonly_degraded"
        model_version_id = current.get("active_model_version_id")
        threshold_hash = current.get("active_threshold_hash")
    else:
        mode = "off"
        model_version_id = current.get("active_model_version_id")
        threshold_hash = current.get("active_threshold_hash")
    return _set_control(
        actor,
        mode=mode,
        model_version_id=model_version_id,
        threshold_hash=threshold_hash,
        reason=f"{action}:{reason}",
    )
