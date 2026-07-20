"""Governed pre-freeze research methodology evidence; never reads outcome rows."""

from __future__ import annotations

import hashlib
import json
import math
import random

from flask import current_app

from database import get_connection, json_dumps, json_loads, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log


SIMULATION_VERSION = "t30-feasibility-sensitivity-v1"


class ResearchMethodologyError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.status = status
        self.details = details or {}


def _content_json(filename: str) -> dict:
    path = current_app.config["CONTENT_DIR"] / filename
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResearchMethodologyError("methodology_content_invalid", f"研究方法内容不可用：{filename}", 503) from exc


def _canonical_hash(payload: dict) -> str:
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(rendered).hexdigest()


def _control() -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT disabled, reason, changed_by, changed_at FROM research_methodology_runtime_control WHERE id = 'global'").fetchone()
    return dict(row) if row else {"disabled": 0, "reason": None, "changed_by": None, "changed_at": None}


def _require_enabled() -> None:
    if not current_app.config.get("RESEARCH_METHODOLOGY_WORKBENCH_ENABLED", False):
        raise ResearchMethodologyError("methodology_workbench_disabled", "研究方法工作台已关闭", 409)
    if int(_control().get("disabled") or 0):
        raise ResearchMethodologyError("methodology_workbench_killed", "研究方法工作台已停用", 503)


def get_public_status() -> dict:
    registry = _content_json("research_methodology_registry.json")
    control = _control()
    return {
        "status": registry["status"],
        "formal_freeze_recorded": False,
        "confirmatory_analysis_allowed": False,
        "real_outcome_data_accessed": False,
        "workbench_enabled": bool(current_app.config.get("RESEARCH_METHODOLOGY_WORKBENCH_ENABLED")) and not bool(control.get("disabled")),
        "boundary_notice": registry["boundary_notice"],
    }


def get_config() -> dict:
    registry = _content_json("research_methodology_registry.json")
    return {
        **get_public_status(),
        "registry_version": registry["version"],
        "measure_count": len(registry["measures"]),
        "product_line_count": len(registry["product_lines"]),
        "unresolved_blocker_count": len(registry["unresolved_blockers"]),
        "runtime_control": {"disabled": int(_control().get("disabled") or 0), "changed_at": _control().get("changed_at")},
    }


def get_registry() -> dict:
    return _content_json("research_methodology_registry.json")


def _decode_version(row) -> dict:
    item = row_to_dict(row)
    item["registry"] = json_loads(item.pop("registry_json"), {})
    return item


def sync_registry(actor: dict) -> dict:
    _require_enabled()
    registry = get_registry()
    registry_hash = _canonical_hash(registry)
    timestamp = now_iso()
    with get_connection() as conn:
        existing = conn.execute("SELECT * FROM research_methodology_versions WHERE version = ?", (registry["version"],)).fetchone()
        if existing:
            if existing["registry_hash"] != registry_hash:
                raise ResearchMethodologyError("methodology_version_immutable", "同一研究方法版本的哈希已变化，必须生成新版本", 409)
            return _decode_version(existing)
        version_id = new_id("rmv")
        conn.execute(
            """INSERT INTO research_methodology_versions
            (id, version, status, registry_json, registry_hash, formal_freeze_allowed, real_outcome_data_accessed, created_by, created_at)
            VALUES (?, ?, 'draft_before_freeze', ?, ?, 0, 0, ?, ?)""",
            (version_id, registry["version"], json_dumps(registry), registry_hash, actor["id"], timestamp),
        )
        write_audit_log(conn, "research_methodology_registry_synced", actor["id"], "research_methodology_version", version_id, {"registry_hash": registry_hash, "formal_freeze_allowed": False, "real_outcome_data_accessed": False})
        conn.commit()
        row = conn.execute("SELECT * FROM research_methodology_versions WHERE id = ?", (version_id,)).fetchone()
    return _decode_version(row)


def list_versions() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM research_methodology_versions ORDER BY created_at DESC").fetchall()
    return [_decode_version(row) for row in rows]


def _require_version(version_id: str | None = None) -> dict:
    with get_connection() as conn:
        if version_id:
            row = conn.execute("SELECT * FROM research_methodology_versions WHERE id = ?", (version_id,)).fetchone()
        else:
            row = conn.execute("SELECT * FROM research_methodology_versions ORDER BY created_at DESC LIMIT 1").fetchone()
    if not row:
        raise ResearchMethodologyError("methodology_version_missing", "请先由管理员同步研究方法注册表", 409)
    return _decode_version(row)


def _save_evidence_row(table: str, prefix: str, columns: list[str], values: list, actor: dict, action: str, version_id: str, audit: dict) -> str:
    evidence_id, timestamp = new_id(prefix), now_iso()
    placeholders = ", ".join("?" for _ in range(len(columns) + 3))
    names = ", ".join(["id", *columns, "created_by", "created_at"])
    with get_connection() as conn:
        conn.execute(f"INSERT INTO {table} ({names}) VALUES ({placeholders})", (evidence_id, *values, actor["id"], timestamp))
        write_audit_log(conn, action, actor["id"], table, evidence_id, {"version_id": version_id, **audit})
        conn.commit()
    return evidence_id


def run_machine_checks(actor: dict, version_id: str | None = None) -> dict:
    _require_enabled()
    version = _require_version(version_id)
    registry = version["registry"]
    worksheet_payload = _content_json("assessment_worksheets.json")
    worksheet_ids = {item["id"] for item in worksheet_payload.get("worksheets", [])}
    measure_ids = {item["measure_id"] for item in registry.get("measures", [])}
    nine_point = next((item for item in registry.get("measures", []) if item.get("measure_id") == "regulatory_focus_relationship_18"), {})
    separation = nine_point.get("score_separation") or {}
    hard_checks = {
        "all_worksheets_registered": worksheet_ids == measure_ids,
        "nine_point_raw_range_is_1_to_9": separation.get("raw_scale") == {"min": 1, "max": 9, "field": "raw_scores_json"},
        "five_point_model_input_separate": separation.get("model_input_scale") == {"min": 1, "max": 5, "field": "transformed_scores_json"},
        "nine_point_raw_values_preserved": separation.get("raw_values_preserved") is True,
        "product_lines_have_prohibited_interpretation": all(item.get("prohibited_interpretation") for item in registry.get("product_lines", [])),
        "metrics_have_denominator_and_dedup": all(item.get("denominator_event") and item.get("deduplication") for item in registry.get("metrics", [])),
        "between_within_separated": registry.get("longitudinal_plan", {}).get("between_within_separated") is True,
        "real_outcomes_not_accessed": registry.get("real_outcome_data_accessed") is False,
        "formal_freeze_not_auto_granted": registry.get("formal_freeze_allowed") is False,
        "confirmatory_analysis_blocked": registry.get("confirmatory_analysis_allowed") is False,
    }
    blockers = list(registry.get("unresolved_blockers", []))
    results = {
        "hard_checks": hard_checks,
        "hard_check_passed": all(hard_checks.values()),
        "worksheet_count": len(worksheet_ids),
        "measure_count": len(measure_ids),
        "unresolved_blockers": blockers,
        "formal_freeze_ready": False,
        "formal_freeze_recorded": False,
        "real_outcome_rows_read": 0,
        "status": "machine_structure_complete_human_freeze_pending" if all(hard_checks.values()) else "machine_structure_failed",
    }
    artifact_hash = _canonical_hash(results)
    check_id = _save_evidence_row(
        "research_methodology_checks", "rmc",
        ["version_id", "check_type", "status", "results_json", "artifact_hash"],
        [version["id"], "pre_freeze_machine_readiness", results["status"], json_dumps(results), artifact_hash],
        actor, "research_methodology_check_run", version["id"], {"status": results["status"], "real_outcome_rows_read": 0},
    )
    return {"id": check_id, "version_id": version["id"], "artifact_hash": artifact_hash, **results}


def _wilson_half_width(successes: int, total: int, z: float = 1.96) -> float:
    proportion = successes / total
    denominator = 1 + z * z / total
    radius = z * math.sqrt((proportion * (1 - proportion) + z * z / (4 * total)) / total) / denominator
    return round(radius, 4)


def _within_person_sensitivity(seed: int) -> dict:
    rng = random.Random(seed)
    estimates = []
    for _ in range(100):
        numerator = denominator = 0.0
        for _participant in range(40):
            intercept = rng.gauss(0, 1)
            xs, ys = [], []
            for wave in range(3):
                x = wave - 1
                y = intercept + 0.2 * x + rng.gauss(0, 0.6)
                xs.append(x); ys.append(y)
            mean_x, mean_y = sum(xs) / 3, sum(ys) / 3
            numerator += sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
            denominator += sum((x - mean_x) ** 2 for x in xs)
        estimates.append(numerator / denominator)
    mean_estimate = sum(estimates) / len(estimates)
    rmse = math.sqrt(sum((value - 0.2) ** 2 for value in estimates) / len(estimates))
    return {"true_within_slope": 0.2, "mean_recovered_slope": round(mean_estimate, 4), "rmse": round(rmse, 4), "participants": 40, "waves": 3, "replications": 100, "interpretation": "仅验证三波合成设计的估计可恢复性，不构成功效依据。"}


def _cluster_sensitivity(seed: int) -> dict:
    rng = random.Random(seed + 31)
    stabilities = []
    minimum_ratios = []
    for _ in range(100):
        values = [rng.gauss(-1.2, 0.35) for _ in range(40)] + [rng.gauss(1.2, 0.35) for _ in range(40)]
        baseline = [int(value >= 0) for value in values]
        perturbed = [int((value + rng.gauss(0, 0.12)) >= 0) for value in values]
        stabilities.append(sum(a == b for a, b in zip(baseline, perturbed)) / len(values))
        ratio = min(sum(baseline), len(baseline) - sum(baseline)) / len(baseline)
        minimum_ratios.append(ratio)
    return {"mean_assignment_stability": round(sum(stabilities) / len(stabilities), 4), "minimum_cluster_ratio": round(min(minimum_ratios), 4), "replications": 100, "perturbation_sd": 0.12, "interpretation": "只检查合成可分结构，不证明真实人群存在类别或发展轨迹。"}


def run_simulation(actor: dict, version_id: str | None = None) -> dict:
    _require_enabled()
    version = _require_version(version_id)
    seed = int(version["registry"].get("simulation_plan", {}).get("random_seed", 20260720))
    completion_precision = []
    for sample_size in (20, 40, 80):
        successes = round(sample_size * 0.7)
        completion_precision.append({"n": sample_size, "assumed_for_sensitivity_only": 0.7, "wilson_half_width": _wilson_half_width(successes, sample_size)})
    metrics = {
        "contains_real_data": False,
        "real_outcome_rows_read": 0,
        "confirmatory_power_claim": False,
        "completion_precision": completion_precision,
        "attrition_sensitivity": [{"attrition": rate, "starting_n": 80, "effective_n": round(80 * (1 - rate))} for rate in (0.0, 0.2, 0.4)],
        "longitudinal_identifiability": _within_person_sensitivity(seed),
        "cluster_stability": _cluster_sensitivity(seed),
        "unresolved_for_power": ["primary_estimand", "effect_size_or_precision_target", "primary_timepoint", "sample_size_basis"],
        "status": "engineering_feasibility_only_human_design_freeze_pending",
    }
    parameters = {"seed": seed, "simulation_version": SIMULATION_VERSION, "outcome_source": "synthetic_only"}
    artifact_hash = _canonical_hash({"parameters": parameters, "metrics": metrics})
    simulation_id = _save_evidence_row(
        "research_methodology_simulation_runs", "rms",
        ["version_id", "simulation_version", "parameters_json", "metrics_json", "artifact_hash", "contains_real_data", "confirmatory_power_claim", "status"],
        [version["id"], SIMULATION_VERSION, json_dumps(parameters), json_dumps(metrics), artifact_hash, 0, 0, metrics["status"]],
        actor, "research_methodology_simulation_run", version["id"], {"contains_real_data": False, "confirmatory_power_claim": False},
    )
    return {"id": simulation_id, "version_id": version["id"], "parameters": parameters, "metrics": metrics, "artifact_hash": artifact_hash, "status": metrics["status"]}


def create_evidence_package(actor: dict, version_id: str | None = None) -> dict:
    _require_enabled()
    version = _require_version(version_id)
    with get_connection() as conn:
        check = conn.execute("SELECT id, status, artifact_hash FROM research_methodology_checks WHERE version_id = ? ORDER BY created_at DESC LIMIT 1", (version["id"],)).fetchone()
        simulation = conn.execute("SELECT id, status, artifact_hash FROM research_methodology_simulation_runs WHERE version_id = ? ORDER BY created_at DESC LIMIT 1", (version["id"],)).fetchone()
    if not check or not simulation:
        raise ResearchMethodologyError("methodology_evidence_incomplete", "需先完成机器检查和合成仿真", 409)
    if check["status"] != "machine_structure_complete_human_freeze_pending" or simulation["status"] != "engineering_feasibility_only_human_design_freeze_pending":
        raise ResearchMethodologyError("methodology_evidence_failed", "机器检查或合成仿真尚未达到证据包条件", 409)
    package = {
        "registry_version": version["version"],
        "registry_hash": version["registry_hash"],
        "machine_check": dict(check),
        "synthetic_simulation": dict(simulation),
        "signature_placeholders": version["registry"].get("signature_requirements", []),
        "unresolved_blockers": version["registry"].get("unresolved_blockers", []),
        "status": "draft_for_human_signature",
        "formal_freeze_recorded": False,
        "confirmatory_analysis_allowed": False,
        "real_outcome_rows_read": 0,
        "boundary_notice": "本包只供真人核对和签字；系统不签字、不自动冻结、不解锁主要结果分析。",
    }
    artifact_hash = _canonical_hash(package)
    package_id = _save_evidence_row(
        "research_methodology_evidence_packages", "rmep",
        ["version_id", "package_json", "artifact_hash", "status", "formal_freeze_recorded"],
        [version["id"], json_dumps(package), artifact_hash, "draft_for_human_signature", 0],
        actor, "research_methodology_evidence_package_created", version["id"], {"formal_freeze_recorded": False, "real_outcome_rows_read": 0},
    )
    return {"id": package_id, "version_id": version["id"], "artifact_hash": artifact_hash, **package}


def list_evidence() -> dict:
    with get_connection() as conn:
        check_rows = rows_to_dicts(conn.execute("SELECT * FROM research_methodology_checks ORDER BY created_at DESC LIMIT 50").fetchall())
        simulation_rows = rows_to_dicts(conn.execute("SELECT * FROM research_methodology_simulation_runs ORDER BY created_at DESC LIMIT 50").fetchall())
        package_rows = rows_to_dicts(conn.execute("SELECT * FROM research_methodology_evidence_packages ORDER BY created_at DESC LIMIT 50").fetchall())
    for item in check_rows:
        item["results"] = json_loads(item.pop("results_json"), {})
    for item in simulation_rows:
        item["parameters"] = json_loads(item.pop("parameters_json"), {})
        item["metrics"] = json_loads(item.pop("metrics_json"), {})
    for item in package_rows:
        item["package"] = json_loads(item.pop("package_json"), {})
    return {"checks": check_rows, "simulations": simulation_rows, "packages": package_rows}


def disable_runtime(actor: dict, data: dict) -> dict:
    reason = str(data.get("reason") or "").strip()
    if len(reason) < 5 or len(reason) > 500:
        raise ResearchMethodologyError("disable_reason_invalid", "停用原因需为5至500字")
    timestamp = now_iso()
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM research_methodology_runtime_control WHERE id = 'global'").fetchone()
        if existing:
            conn.execute("UPDATE research_methodology_runtime_control SET disabled = 1, reason = ?, changed_by = ?, changed_at = ? WHERE id = 'global'", (reason, actor["id"], timestamp))
        else:
            conn.execute("INSERT INTO research_methodology_runtime_control (id, disabled, reason, changed_by, changed_at) VALUES ('global', 1, ?, ?, ?)", (reason, actor["id"], timestamp))
        write_audit_log(conn, "research_methodology_workbench_disabled", actor["id"], "research_methodology_runtime", "global", {"reason": reason, "formal_freeze_recorded": False})
        conn.commit()
    return {"disabled": True, "changed_at": timestamp}
