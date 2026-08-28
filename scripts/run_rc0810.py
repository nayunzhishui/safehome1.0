"""SafeHome RC0810 machine registry and recoverable execution harness.

The public interface is the nine CLI commands documented in the RC0810 plan.
Runtime state and complete command evidence stay under ``.codex_tmp/rc0810``;
the repository only keeps the registry, implementation, tests and redacted
hash summaries.  This module never resets a worktree or deploys production.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator


ROOT = Path(os.environ.get("RC0810_REPO_ROOT", Path(__file__).resolve().parents[1])).resolve()
REGISTRY_PATH = Path(
    os.environ.get(
        "RC0810_REGISTRY_PATH",
        ROOT / "content" / "rc0810_release_candidate_registry.json",
    )
).resolve()
RUNTIME_ROOT = Path(
    os.environ.get("RC0810_RUNTIME_ROOT", ROOT / ".codex_tmp" / "rc0810")
).resolve()
REGISTRY_SCHEMA = "safehome.rc0810.registry.v1"
STATE_SCHEMA = "safehome.rc0810.run-state.v1"
POINTER_SCHEMA = "safehome.rc0810.active-run.v1"
PRODUCTION_REVIEW_WAVES = [
    {
        "id": "A",
        "execution_units": ["RC0810-F10-B", "RC0810-F11", "RC0810-F12-B"],
        "freeze_unit": "RC0810-F12-B",
        "base_checkpoint": {
            "status": "review_pass",
            "commit": "39e76225d873c2aaac2731974fa1f63853a6f9be",
            "execution_units": [
                "RC0810-F10-A", "RC0810-F12-A", "RC0810-F07",
                "RC0810-F08", "RC0810-F09",
            ],
            "production_gate_eligible": False,
        },
    },
    {
        "id": "B",
        "execution_units": [
            "RC0810-F13", "RC0810-F15", "RC0810-F16", "RC0810-F17",
            "RC0810-F18", "RC0810-F19", "RC0810-F14-B", "RC0810-F20",
            "RC0810-F21",
        ],
        "freeze_unit": "RC0810-F21",
        "base_checkpoint": {
            "status": "review_pass",
            "commit": "4a17b9faf9187a5d414f92e84ff7b08e60802d49",
            "execution_units": ["RC0810-F14-A"],
            "production_gate_eligible": False,
            "evidence_binding": {
                "task": "RC0810-F14-A",
                "review_packet_path": "config/rc0810/f14a_review_packet_checkpoint.json",
                "review_packet_sha256": "67225a4361dc342f5aba89e26ed7583d00a93f4e19dc0d2f7b3f9683b4f21147",
                "decision_path": "config/rc0810/f14a_review_decision_checkpoint.json",
                "decision_sha256": "13cf65d6fd83c658016c02fe9580b7db9302d7302b2a1c88dc250ea635d0eeba",
            },
        },
    },
    {
        "id": "C",
        "execution_units": [
            "RC0810-F22-B", "RC0810-F23", "RC0810-F24", "RC0810-F25-B",
            "RC0810-F26",
        ],
        "freeze_unit": "RC0810-F26",
        "base_checkpoint": {
            "status": "review_pass",
            "commit": "aee4f55badfb3b0928e55b245ce7070d642bd29e",
            "execution_units": ["RC0810-F22-A", "RC0810-F25-A"],
            "production_gate_eligible": False,
            "legacy_phase_bindings": [
                {
                    "task": "RC0810-F22-A",
                    "commit": "e0fb7fd0bcde3e6ea6e485ec978d9663152831f9",
                    "baseline_path": "docs/02_专项进度与验收/rc0810_f22a_security_baseline.json",
                    "baseline_sha256": "3a45e934d068aee44ed5d50548681ce1ae73743f4da88020fb271be450676886",
                    "documented_review_decision_sha256": "7d1f0a9cb8870618d33f654984afa13ffc52b2f554b3710f9664c3b51fce2faa",
                },
                {
                    "task": "RC0810-F25-A",
                    "commit": "aee4f55badfb3b0928e55b245ce7070d642bd29e",
                    "baseline_path": "docs/02_专项进度与验收/rc0810_f25a_platform_baseline.json",
                    "baseline_sha256": "ebc72ad5f79bb59acec1c7146880f3452c25fdc92896b435da56f1b1d3ab8044",
                    "documented_review_decision_sha256": "4919cdfc4142b6926c56c5f3df297674e41ed363ad284e4fe85a06b86f88808c",
                },
            ],
        },
    },
]


class HarnessError(ValueError):
    """Raised when a registry, state transition or evidence is unsafe."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json(payload: Any) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_bytes(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
    os.replace(temporary, path)


@contextmanager
def state_lock(timeout_seconds: float = 5.0) -> Iterator[None]:
    """Use an exclusive lock file without maintaining a second state truth."""

    import time

    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    lock_path = RUNTIME_ROOT / "state.lock"
    deadline = time.monotonic() + timeout_seconds
    descriptor: int | None = None
    while descriptor is None:
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise HarnessError("状态锁超时；拒绝并发覆盖运行状态。")
            time.sleep(0.05)
    try:
        os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
        yield
    finally:
        os.close(descriptor)
        lock_path.unlink(missing_ok=True)


def task_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {task["id"]: task for task in registry["tasks"]}


def unit_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {unit["id"]: unit for unit in registry["execution_units"]}


def review_wave_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {wave["id"]: wave for wave in registry.get("review_waves", [])}


def _wave_for_unit(registry: dict[str, Any], task_id: str) -> dict[str, Any] | None:
    return next(
        (
            wave
            for wave in registry.get("review_waves", [])
            if task_id in wave["execution_units"]
        ),
        None,
    )


def _previous_waves(registry: dict[str, Any], wave_id: str) -> list[dict[str, Any]]:
    waves = registry.get("review_waves", [])
    position = next(index for index, wave in enumerate(waves) if wave["id"] == wave_id)
    return waves[:position]


def _load_reviewer_replacement_binding(
    registry: dict[str, Any],
    state: dict[str, Any],
    wave_id: str,
    review_root: Path,
) -> dict[str, Any] | None:
    """Load a canonical replacement record before the wave packet is frozen."""

    fixed_reviewer = state.get("fixed_wave_reviewer_id")
    if not fixed_reviewer:
        return None
    replacement_path = (
        review_root / f"wave-{wave_id}-reviewer-replacement.json"
    ).resolve()
    if not replacement_path.is_file():
        return None
    try:
        replacement_record = json.loads(
            replacement_path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise HarnessError("reviewer替换证据不是有效JSON。") from exc
    if replacement_record.get("replacement_reviewer_id") == fixed_reviewer:
        return None
    previous_waves = _previous_waves(registry, wave_id)
    previous_review = (
        state.get("wave_checkpoints", {})
        .get(previous_waves[-1]["id"], {})
        .get("review", {})
        if previous_waves
        else {}
    )
    checkpoint = replacement_record.get("previous_reviewer_checkpoint", {})
    replacement_reviewer = replacement_record.get("replacement_reviewer_id")
    recovery_attempts = replacement_record.get("recovery_attempts")
    if (
        replacement_record.get("schema")
        != "safehome.rc0810.reviewer_replacement.v1"
        or replacement_record.get("wave") != wave_id
        or replacement_record.get("previous_reviewer_id") != fixed_reviewer
        or not isinstance(replacement_reviewer, str)
        or not replacement_reviewer.strip()
        or replacement_reviewer == fixed_reviewer
        or replacement_record.get("replacement_reason")
        != "previous_reviewer_ended_and_cannot_be_recovered"
        or not isinstance(recovery_attempts, list)
        or not recovery_attempts
        or not all(isinstance(item, str) and item.strip() for item in recovery_attempts)
        or checkpoint.get("decision_evidence_sha256")
        != previous_review.get("decision_evidence_sha256")
    ):
        raise HarnessError("reviewer替换证据未绑定旧reviewer或最后有效checkpoint。")
    return {
        "evidence_path": str(replacement_path),
        "evidence_sha256": sha256_bytes(replacement_path.read_bytes()),
        "previous_reviewer_id": fixed_reviewer,
        "replacement_reviewer_id": replacement_reviewer,
        "previous_reviewer_checkpoint": {
            "decision_evidence_sha256": checkpoint.get(
                "decision_evidence_sha256"
            )
        },
    }


def topological_order(registry: dict[str, Any]) -> list[str]:
    units = unit_map(registry)
    declared = registry.get("execution_order")
    if declared != [unit["id"] for unit in registry.get("execution_units", [])]:
        raise HarnessError("执行顺序与分阶段执行单元不一致。")
    remaining = set(units)
    complete: set[str] = set()
    result: list[str] = []
    while remaining:
        selected = next(
            (
                task_id
                for task_id in declared
                if task_id in remaining
                and set(units[task_id]["dependencies"]).issubset(complete)
            ),
            None,
        )
        if selected is None:
            raise HarnessError("任务依赖存在循环或无法满足。")
        result.append(selected)
        complete.add(selected)
        remaining.remove(selected)
    return result


def _legacy_phase_checkpoint_is_valid(
    wave: dict[str, Any], checkpoint: dict[str, Any]
) -> bool:
    if (
        wave.get("id") != "C"
        or checkpoint != PRODUCTION_REVIEW_WAVES[2]["base_checkpoint"]
    ):
        return False
    checkpoint_commit = checkpoint["commit"]
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", checkpoint_commit, "HEAD"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    ).returncode != 0:
        return False
    for binding in checkpoint["legacy_phase_bindings"]:
        baseline_path = (ROOT / binding["baseline_path"]).resolve()
        if not _path_within(baseline_path, ROOT) or not baseline_path.is_file():
            return False
        try:
            baseline_bytes = _historical_checkpoint_evidence_bytes(baseline_path)
            if sha256_bytes(baseline_bytes) != binding["baseline_sha256"]:
                return False
            baseline = json.loads(baseline_bytes.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return False
        if (
            baseline.get("phase") != binding["task"].removeprefix("RC0810-")
            or baseline.get("production_gate_eligible") is not False
        ):
            return False
        commit = binding["commit"]
        if subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, checkpoint_commit],
            cwd=ROOT,
            capture_output=True,
            check=False,
        ).returncode != 0 or subprocess.run(
            ["git", "diff", "--quiet", commit, "--", binding["baseline_path"]],
            cwd=ROOT,
            capture_output=True,
            check=False,
        ).returncode != 0:
            return False
    return True


def _validate_command(command: dict[str, Any], policy: dict[str, Any]) -> None:
    argv = command.get("argv")
    if not isinstance(argv, list) or not argv or not all(
        isinstance(item, str) and item for item in argv
    ):
        raise HarnessError("验收命令必须使用非空argv数组。")
    if command.get("shell") is not False:
        raise HarnessError("验收命令必须显式shell=false。")
    if Path(argv[0]).name.lower() not in {
        item.lower() for item in policy["allowed_executables"]
    }:
        raise HarnessError(f"命令执行器未获允许：{argv[0]}")
    executable = Path(argv[0]).name.lower()
    if executable == "python":
        if len(argv) >= 2 and argv[1] == "-m":
            if len(argv) < 3 or argv[2] != "pytest":
                raise HarnessError("Python -m仅允许执行pytest验收。")
        elif len(argv) < 2 or not argv[1].endswith(".py"):
            raise HarnessError("Python验收仅允许仓库脚本或pytest模块。")
        if "-c" in argv:
            raise HarnessError("验收命令禁止Python -c动态代码。")
    joined = " ".join(argv).lower()
    if any(term.lower() in joined for term in policy["forbidden_terms"]):
        raise HarnessError("验收命令包含禁止操作。")
    timeout = command.get("timeout_seconds")
    if not isinstance(timeout, int) or not 0 < timeout <= policy["max_timeout_seconds"]:
        raise HarnessError("验收命令timeout无效。")
    cwd = Path(command.get("cwd", "."))
    if cwd.is_absolute() or ".." in cwd.parts:
        raise HarnessError("验收命令cwd必须是仓库内相对路径。")


def validate_registry(registry: dict[str, Any]) -> None:
    if registry.get("schema") != REGISTRY_SCHEMA:
        raise HarnessError("rc0810注册表schema不兼容。")
    tasks = registry.get("tasks")
    if not isinstance(tasks, list) or [task.get("id") for task in tasks] != [
        f"RC0810-F{index:02d}" for index in range(27)
    ]:
        raise HarnessError("注册表必须连续包含27个父任务。")
    subtasks = [subtask for task in tasks for subtask in task.get("subtasks", [])]
    if len(subtasks) != 225 or len({item.get("id") for item in subtasks}) != 225:
        raise HarnessError("注册表必须包含225个唯一二级工单。")
    tasks_by_id = task_map(registry)
    units_by_id = unit_map(registry)
    if set(units_by_id) != set(registry.get("execution_order", [])):
        raise HarnessError("执行单元必须唯一且完整登记。")
    for unit in units_by_id.values():
        if unit.get("task") not in tasks_by_id:
            raise HarnessError("执行单元引用未知父任务。")
        parent_task = tasks_by_id[unit["task"]]
        if not set(unit.get("dependencies", [])).issubset(units_by_id):
            raise HarnessError("执行单元依赖不存在。")
        declared_subtasks = unit.get("subtasks")
        if declared_subtasks is not None:
            task_subtasks = {item["id"] for item in parent_task.get("subtasks", [])}
            if (
                not isinstance(declared_subtasks, list)
                or not declared_subtasks
                or len(declared_subtasks) != len(set(declared_subtasks))
                or not set(declared_subtasks).issubset(task_subtasks)
            ):
                raise HarnessError("分阶段执行单元的二级工单映射无效。")
        unit_allowed = unit.get("allowed_files")
        if unit_allowed is not None and (
            not isinstance(unit_allowed, list)
            or not unit_allowed
            or any(
                not _path_allowed(path, parent_task["allowed_files"])
                for path in unit_allowed
            )
        ):
            raise HarnessError("分阶段执行单元的允许范围必须收窄于父任务。")
        inherited_shared = unit.get("inherited_shared_files", [])
        if not set(inherited_shared).issubset(set(unit_allowed or [])):
            raise HarnessError("分阶段共享文件必须属于该执行单元允许范围。")
        unit_budget = unit.get("change_budget")
        if unit_budget is not None and (
            unit_budget.get("expected_files", 0) <= 0
            or unit_budget.get("pause_when_actual_exceeds_percent") != 50
        ):
            raise HarnessError("分阶段change budget无效。")
    claim_classes = set(registry.get("claim_classes", {}))
    required_claim_classes = {
        "current_code_fact",
        "external_rule",
        "project_decision",
        "recommendation",
        "todo",
    }
    if claim_classes != required_claim_classes:
        raise HarnessError("事实、规则、决策、建议和待办分类不完整。")
    for claim in registry.get("claim_register", []):
        if claim.get("class") not in claim_classes or not claim.get("stale_if"):
            raise HarnessError("claim登记缺少有效分类或失效条件。")

    risk_model = registry.get("risk_priority_model", {})
    weights = risk_model.get("weights", {})
    score_min, score_max = risk_model.get("score_range", [None, None])
    forced_p0 = set(risk_model.get("forced_p0_categories", []))
    for risk in registry.get("risk_register", []):
        scores = risk.get("scores", {})
        if set(scores) != set(weights) or any(
            not isinstance(score, int) or not score_min <= score <= score_max
            for score in scores.values()
        ):
            raise HarnessError("风险登记的维度或分值无效。")
        computed = sum(weights[name] * scores[name] for name in weights)
        if risk.get("computed") != computed:
            raise HarnessError("风险加权分值与登记值不一致。")
        if risk.get("category") in forced_p0 and risk.get("priority") != "P0":
            raise HarnessError("强制P0风险不得降级。")
    for task in tasks:
        if not set(task["dependencies"]).issubset(tasks_by_id):
            raise HarnessError(f"{task['id']}依赖不存在。")
        budget = task.get("change_budget", {})
        if set(budget.get("allowed_modules", [])) != set(task.get("allowed_files", [])):
            raise HarnessError(f"{task['id']}的allowed scope与change budget不一致。")
        if set(budget.get("forbidden_modules", [])) != set(
            task.get("forbidden_files", [])
        ):
            raise HarnessError(f"{task['id']}的forbidden scope与change budget不一致。")
        if budget.get("expected_migrations", 0) > 0 and "backend/migrations/**" not in task[
            "allowed_files"
        ]:
            raise HarnessError(f"{task['id']}预计产生迁移但未显式允许迁移目录。")
        if budget.get("actual_delta_baseline") != "task_start_snapshot":
            raise HarnessError("change budget必须以任务启动快照为实际差异基线。")
        if budget.get("pause_when_actual_exceeds_percent") != 50:
            raise HarnessError("change budget超限阈值必须为50%。")
        for command in task.get("acceptance_commands", []):
            _validate_command(command, registry["command_policy"])
        for gate in task.get("external_gates", []):
            if gate.get("automation_may_approve") is not False or gate.get(
                "status"
            ) not in {"pending_external", "blocked_external"}:
                raise HarnessError("人工或平台门禁不得由自动化预置通过。")
    if tasks_by_id["RC0810-F00"]["dependencies"]:
        raise HarnessError("F00必须是无依赖根任务。")
    expected_early = [
        "RC0810-F00",
        "RC0810-F10-A",
        "RC0810-F12-A",
        "RC0810-F14-A",
        "RC0810-F22-A",
        "RC0810-F25-A",
    ]
    if registry["execution_order"][:6] != expected_early:
        raise HarnessError("早期失败基线波次必须紧跟F00执行。")
    if topological_order(registry) != registry["execution_order"]:
        raise HarnessError("依赖拓扑与冻结顺序不一致。")
    waves = registry.get("review_waves")
    if not isinstance(waves, list) or [wave.get("id") for wave in waves] != [
        "A",
        "B",
        "C",
    ]:
        raise HarnessError("审查波次必须按A/B/C唯一登记。")
    wave_units = [unit_id for wave in waves for unit_id in wave.get("execution_units", [])]
    if (
        len(wave_units) != len(set(wave_units))
        or not set(wave_units).issubset(units_by_id)
        or any(
            not wave.get("execution_units")
            or wave.get("freeze_unit") != wave["execution_units"][-1]
            for wave in waves
        )
    ):
        raise HarnessError("审查波次执行单元或冻结点无效。")
    positions = [registry["execution_order"].index(unit_id) for unit_id in wave_units]
    if positions != sorted(positions):
        raise HarnessError("审查波次必须服从冻结执行顺序。")
    for wave in waves:
        checkpoint = wave.get("base_checkpoint")
        if checkpoint is None:
            continue
        inherited = checkpoint.get("execution_units")
        first_position = registry["execution_order"].index(wave["execution_units"][0])
        if (
            checkpoint.get("status") != "review_pass"
            or checkpoint.get("production_gate_eligible") is not False
            or not isinstance(checkpoint.get("commit"), str)
            or len(checkpoint["commit"]) != 40
            or not isinstance(inherited, list)
            or not inherited
            or len(inherited) != len(set(inherited))
            or not set(inherited).issubset(units_by_id)
            or any(
                registry["execution_order"].index(unit_id) >= first_position
                for unit_id in inherited
            )
        ):
            raise HarnessError("波次历史review-pass checkpoint无效。")
        legacy_checkpoint = (
            wave.get("id") == "A"
            and checkpoint == PRODUCTION_REVIEW_WAVES[0]["base_checkpoint"]
        ) or _legacy_phase_checkpoint_is_valid(wave, checkpoint)
        if not legacy_checkpoint and not _historical_checkpoint_evidence_is_valid(
            registry, checkpoint
        ):
            raise HarnessError("波次历史review-pass checkpoint缺少有效独立复审证据。")
    if "review_pending_wave" not in set(
        registry.get("state_machine", {}).get("statuses", [])
    ) or "review_pending_wave" not in set(
        registry.get("subtask_record_schema", {}).get("statuses", [])
    ):
        raise HarnessError("Harness未注册review_pending_wave状态。")
    review_policy = registry.get("independent_review_policy", {})
    if (
        review_policy.get("fixed_reviewer_across_waves") is not True
        or review_policy.get("wave_decision_only_at_freeze") is not True
    ):
        raise HarnessError("固定reviewer与波次冻结门禁必须失败关闭。")
    mapping = registry.get("pr_mapping", {})
    if mapping.get("task_to_pr") != {
        task["id"]: task["pr_ids"] for task in tasks
    }:
        raise HarnessError("task_to_pr映射与任务登记不一致。")
    for pr_id, mapped_tasks in mapping.get("pr_to_tasks", {}).items():
        for task_id in mapped_tasks:
            if pr_id not in tasks_by_id[task_id]["pr_ids"]:
                raise HarnessError("pr_to_tasks反向映射不一致。")
    for task in tasks:
        for pr_id in task["pr_ids"]:
            if task["id"] not in mapping.get("pr_to_tasks", {}).get(pr_id, []):
                raise HarnessError("PR编号缺少反向任务映射。")


def load_registry() -> dict[str, Any]:
    try:
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HarnessError("rc0810注册表缺失或不是有效JSON。") from exc
    validate_registry(registry)
    return registry


def pointer_path() -> Path:
    return RUNTIME_ROOT / "state.json"


def _read_pointer() -> dict[str, Any] | None:
    path = pointer_path()
    if not path.exists():
        return None
    try:
        pointer = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HarnessError("活动运行指针损坏；拒绝猜测恢复点。") from exc
    if pointer.get("schema") != POINTER_SCHEMA:
        raise HarnessError("活动运行指针schema不兼容。")
    return pointer


def _state_path_from_pointer(pointer: dict[str, Any]) -> Path:
    run_id = pointer.get("run_id")
    if not isinstance(run_id, str) or not run_id or Path(run_id).name != run_id:
        raise HarnessError("活动run_id无效。")
    path = RUNTIME_ROOT / run_id / "state.json"
    expected = pointer.get("state_sha256")
    if not path.is_file() or sha256_bytes(path.read_bytes()) != expected:
        raise HarnessError("运行状态缺失或哈希不匹配。")
    return path


def read_state() -> dict[str, Any] | None:
    pointer = _read_pointer()
    if pointer is None:
        return None
    path = _state_path_from_pointer(pointer)
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HarnessError("运行状态损坏；拒绝继续。") from exc
    if state.get("schema") != STATE_SCHEMA or state.get("run_id") != pointer["run_id"]:
        raise HarnessError("运行状态schema或run_id不一致。")
    return state


def write_state(state: dict[str, Any]) -> None:
    run_id = state["run_id"]
    path = RUNTIME_ROOT / run_id / "state.json"
    atomic_write_json(path, state)
    pointer = {
        "schema": POINTER_SCHEMA,
        "run_id": run_id,
        "state_path": f"{run_id}/state.json",
        "state_sha256": sha256_bytes(path.read_bytes()),
        "updated_at": utc_now(),
    }
    atomic_write_json(pointer_path(), pointer)


def _new_subtask_record(
    item: dict[str, Any], task: dict[str, Any], allowed_scope: list[str]
) -> dict[str, Any]:
    return {
        "id": item["id"],
        "status": "pending",
        "input_baseline": None,
        "allowed_scope": allowed_scope,
        "actual_modified_files": [],
        "commands": [],
        "started_at": None,
        "finished_at": None,
        "exit_codes": [],
        "test_count": 0,
        "failure_summary": None,
        "source_tree": None,
        "dirty_diff_sha256": None,
        "evidence_dir": None,
        "rollback_point": task["rollback"],
        "review_decision": None,
    }


def _run_git(*args: str, env: dict[str, str] | None = None) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise HarnessError(f"Git只读快照失败：git {' '.join(args)}")
    return completed.stdout


def _git_text(*args: str) -> str:
    return _run_git(*args).decode("utf-8", errors="replace").strip()


def _committed_diff_files(base_commit: str | None, head_commit: str) -> list[str]:
    if not base_commit or base_commit == head_commit:
        return []
    raw = _run_git(
        "-c",
        "core.quotepath=false",
        "diff",
        "--name-only",
        "-z",
        f"{base_commit}..{head_commit}",
    )
    return sorted(_nul_paths(raw))


def _nul_paths(value: bytes) -> list[str]:
    return sorted(
        item.decode("utf-8", errors="replace")
        for item in value.split(b"\0")
        if item
    )


def _manifest_from_index(value: bytes) -> dict[str, str]:
    manifest: dict[str, str] = {}
    for item in value.split(b"\0"):
        if not item:
            continue
        metadata, separator, raw_path = item.partition(b"\t")
        if not separator:
            raise HarnessError("Git源码清单格式异常。")
        parts = metadata.decode("ascii", errors="strict").split()
        if len(parts) != 3:
            raise HarnessError("Git源码清单元数据异常。")
        manifest[raw_path.decode("utf-8", errors="replace")] = parts[1]
    return manifest


def _manifest_from_tree(tree: str) -> dict[str, str]:
    manifest: dict[str, str] = {}
    inventory = _run_git("-c", "core.quotepath=false", "ls-tree", "-r", "-z", tree)
    for item in inventory.split(b"\0"):
        if not item:
            continue
        metadata, separator, raw_path = item.partition(b"\t")
        parts = metadata.decode("ascii", errors="strict").split()
        if not separator or len(parts) != 3 or parts[1] != "blob":
            raise HarnessError("Git tree源码清单格式异常。")
        manifest[raw_path.decode("utf-8", errors="replace")] = parts[2]
    return manifest


def collect_git_snapshot(registry: dict[str, Any]) -> dict[str, Any]:
    """Bind HEAD and the actual dirty source tree without touching the real index."""

    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    temporary_root = Path(tempfile.mkdtemp(prefix="snapshot-", dir=RUNTIME_ROOT))
    temporary_index = temporary_root / "index"
    git_index = Path(_git_text("rev-parse", "--git-path", "index"))
    if not git_index.is_absolute():
        git_index = ROOT / git_index
    shutil.copy2(git_index, temporary_index)
    temporary_env = os.environ.copy()
    temporary_env["GIT_INDEX_FILE"] = str(temporary_index)
    try:
        completed = subprocess.run(
            ["git", "add", "-A", "--", "."],
            cwd=ROOT,
            env=temporary_env,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise HarnessError("临时索引无法冻结当前源码树。")
        source_tree = _run_git("write-tree", env=temporary_env).decode("ascii").strip()
        inventory = _run_git(
            "-c", "core.quotepath=false", "ls-files", "-s", "-z", env=temporary_env
        )
    finally:
        temporary_index.unlink(missing_ok=True)
        try:
            temporary_root.rmdir()
        except OSError:
            pass

    status = _run_git(
        "-c", "core.quotepath=false", "status", "--porcelain=v1", "-z",
    )
    staged = _run_git(
        "-c", "core.quotepath=false", "diff", "--cached", "--name-only", "-z"
    )
    unstaged = _run_git(
        "-c", "core.quotepath=false", "diff", "--name-only", "-z"
    )
    untracked_paths = _nul_paths(
        _run_git(
            "-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard", "-z"
        )
    )
    dirty_hasher = hashlib.sha256()
    dirty_hasher.update(_run_git("diff", "--binary", "HEAD"))
    for relative in untracked_paths:
        dirty_hasher.update(relative.encode("utf-8"))
        dirty_hasher.update(b"\0")
        path = ROOT / relative
        if path.is_file():
            dirty_hasher.update(path.read_bytes())
        else:
            dirty_hasher.update(b"<missing>")

    head = _git_text("rev-parse", "HEAD")
    head_tree = _git_text("rev-parse", "HEAD^{tree}")
    submodule_status = (
        _git_text("submodule", "status").splitlines()
        if (ROOT / ".gitmodules").is_file()
        else []
    )
    dirty = bool(status)
    manifest = _manifest_from_index(inventory)
    return {
        "schema": "safehome.rc0810.snapshot.v1",
        "captured_at": utc_now(),
        "git": {
            "head": head,
            "head_tree": head_tree,
            "origin_main_local": _git_text("rev-parse", "origin/main"),
            "branch": _git_text("branch", "--show-current"),
            "submodule_status": submodule_status,
            "dirty": dirty,
            "head_verified": not dirty and source_tree == head_tree,
            "verification_subject": "dirty_source_tree" if dirty else "head",
            "source_tree": source_tree,
            "source_manifest_sha256": sha256_bytes(inventory),
            "source_manifest": manifest,
            "dirty_diff_sha256": dirty_hasher.hexdigest(),
            "dirty_diff_algorithm": "sha256(git_diff_binary_HEAD || sorted(untracked_path_nul_file_bytes))",
            "status_sha256": sha256_bytes(status),
            "status_entries": len([item for item in status.split(b"\0") if item]),
            "staged_paths": _nul_paths(staged),
            "unstaged_paths": _nul_paths(unstaged),
            "untracked_paths": untracked_paths,
        },
        "baseline": registry["frozen_baseline"],
        "safety": {
            "destructive_git_command_executed": False,
            "production_mutation_executed": False,
            "secret_values_recorded": False,
        },
    }


def _acknowledge_concurrent_overlay(
    task_state: dict[str, Any],
    current_snapshot: dict[str, Any],
    inherited_paths: list[str],
    reason: str,
    allowed_files: list[str],
    inherited_shared_files: list[str],
) -> list[dict[str, Any]]:
    start = task_state.get("start_snapshot")
    if start is None:
        raise HarnessError("任务尚未冻结启动快照，不能登记并行继承改动。")
    if not reason.strip():
        raise HarnessError("登记并行继承改动必须提供reason。")
    manifest = start["source_manifest"]
    current_manifest = current_snapshot["git"]["source_manifest"]
    records: list[dict[str, Any]] = []
    for raw_path in inherited_paths:
        relative = Path(raw_path).as_posix()
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or relative in {"", "."}:
            raise HarnessError("并行继承路径必须是仓库内相对文件路径。")
        if _path_allowed(relative, allowed_files) and relative not in set(
            inherited_shared_files
        ):
            raise HarnessError(f"任务专属文件不得登记为并行继承：{relative}")
        before = manifest.get(relative)
        after = current_manifest.get(relative)
        if before == after:
            raise HarnessError(f"并行继承路径没有启动后变化：{relative}")
        if after is None:
            manifest.pop(relative, None)
        else:
            manifest[relative] = after
        records.append(
            {
                "path": relative,
                "start_blob": before,
                "inherited_blob": after,
                "reason": reason.strip(),
                "recorded_at": utc_now(),
            }
        )
    task_state.setdefault("concurrent_inherited_overlays", []).extend(records)
    task_state["concurrent_inherited_overlay_sha256"] = sha256_bytes(
        canonical_json(task_state["concurrent_inherited_overlays"])
    )
    return records


def snapshot_command(
    registry: dict[str, Any],
    inherited_paths: list[str] | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    with state_lock():
        state = read_state()
        if state is None:
            raise HarnessError("尚无活动run；请先start。")
        snapshot = collect_git_snapshot(registry)
        run_dir = RUNTIME_ROOT / state["run_id"]
        snapshot_path = run_dir / "snapshots" / f"snapshot-{uuid.uuid4().hex}.json"
        atomic_write_json(snapshot_path, snapshot)
        snapshot_hash = sha256_bytes(snapshot_path.read_bytes())
        current_item = next(
            (
                (task_id, record)
                for task_id, record in state["tasks"].items()
                if record.get("status") in {"in_progress", "fixing"}
            ),
            None,
        )
        current = current_item[1] if current_item is not None else None
        if current is not None and current.get("start_snapshot") is None:
            current["start_snapshot"] = {
                "path": str(snapshot_path),
                "sha256": snapshot_hash,
                "source_tree": snapshot["git"]["source_tree"],
                "source_manifest": snapshot["git"]["source_manifest"],
                "dirty_diff_sha256": snapshot["git"]["dirty_diff_sha256"],
            }
        inherited_records: list[dict[str, Any]] = []
        if inherited_paths:
            if current is None:
                raise HarnessError("没有进行中的任务可登记并行继承改动。")
            active_unit = unit_map(registry)[current_item[0]]
            active_task = task_map(registry)[active_unit["task"]]
            inherited_records = _acknowledge_concurrent_overlay(
                current,
                snapshot,
                inherited_paths,
                reason or "",
                active_unit.get("allowed_files", active_task["allowed_files"]),
                active_unit.get("inherited_shared_files", []),
            )
        state["latest_snapshot"] = {
            "path": str(snapshot_path),
            "sha256": snapshot_hash,
        }
        state["updated_at"] = utc_now()
        write_state(state)
    snapshot["snapshot_path"] = str(snapshot_path)
    snapshot["snapshot_sha256"] = snapshot_hash
    snapshot["concurrent_inherited_overlays"] = inherited_records
    return snapshot


def _resolve_command_argv(command: dict[str, Any]) -> list[str]:
    argv = list(command["argv"])
    if Path(argv[0]).name.lower() == "python":
        argv[0] = sys.executable
    if len(argv) >= 2 and argv[1].endswith(".py"):
        script = (ROOT / argv[1]).resolve()
        try:
            script.relative_to(ROOT)
        except ValueError as exc:
            raise HarnessError("Python脚本必须位于仓库内。") from exc
        if not script.is_file():
            raise HarnessError(f"验收脚本不存在：{argv[1]}")
        argv[1] = str(script)
    return argv


def _output_summary(value: bytes) -> dict[str, int]:
    return {
        "bytes": len(value),
        "lines": value.count(b"\n") + (1 if value and not value.endswith(b"\n") else 0),
        "content_recorded": 0,
    }


def _node_version() -> str | None:
    try:
        completed = subprocess.run(
            ["node", "--version"], capture_output=True, check=False, timeout=5
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.decode("ascii", errors="replace").strip()


def _validate_evidence_chain(state: dict[str, Any]) -> None:
    previous: str | None = None
    for item in state.get("evidence_chain", []):
        path = Path(item["path"])
        if not path.is_file() or sha256_bytes(path.read_bytes()) != item["file_sha256"]:
            raise HarnessError("命令证据文件缺失或被篡改。")
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise HarnessError("命令证据不是有效JSON。") from exc
        recorded_hash = record.pop("record_sha256", None)
        if recorded_hash != sha256_bytes(canonical_json(record)):
            raise HarnessError("命令证据记录哈希不匹配。")
        if record.get("previous_evidence_sha256") != previous:
            raise HarnessError("命令证据链断裂。")
        previous = item["file_sha256"]


def _task_delta(start: dict[str, Any], current: dict[str, Any]) -> list[str]:
    before = start.get("source_manifest", {})
    after = current["git"]["source_manifest"]
    return sorted(
        path for path in set(before) | set(after) if before.get(path) != after.get(path)
    )


def _unit_subtask_ids(unit: dict[str, Any], task: dict[str, Any]) -> list[str]:
    declared = unit.get("subtasks")
    if declared is not None:
        return list(declared)
    return [item["id"] for item in task["subtasks"]]


def _path_allowed(path: str, allowed_files: list[str]) -> bool:
    return path in allowed_files or any(
        allowed.endswith("/**") and path.startswith(allowed[:-3] + "/")
        for allowed in allowed_files
    )


def _path_forbidden(path: str, patterns: list[str], expected_migrations: int) -> bool:
    for declared in patterns:
        pattern = declared
        if declared.endswith(" when expected_migrations=0"):
            if expected_migrations != 0:
                continue
            pattern = declared.removesuffix(" when expected_migrations=0")
        if fnmatch.fnmatchcase(path, pattern):
            return True
    return False


def verify_task(registry: dict[str, Any], task_id: str) -> tuple[int, dict[str, Any]]:
    unit = unit_map(registry).get(task_id)
    if unit is None:
        raise HarnessError(f"未知任务：{task_id}")
    task = task_map(registry)[unit["task"]]
    with state_lock():
        state = read_state()
        if state is None or task_id not in state["tasks"]:
            raise HarnessError(f"{task_id}尚未start。")
        _validate_evidence_chain(state)
        task_state = state["tasks"][task_id]
        if task_state["status"] not in {"in_progress", "fixing"}:
            raise HarnessError(f"{task_id}当前状态不能verify。")
        current_registry_sha256 = sha256_bytes(REGISTRY_PATH.read_bytes())
        if current_registry_sha256 != state.get("registry_sha256"):
            frozen_current_registry = (
                task_state.get("start_registry_sha256")
                == current_registry_sha256
                and task_state.get("start_task_contract_sha256")
                == _task_contract_sha256(task, unit)
            )
            previous_registry = _previous_registry_snapshot(state)
            if frozen_current_registry:
                if not (
                    _registry_transition_is_scoped(previous_registry, registry, task_id)
                    or _registry_transition_is_wave_harness_upgrade(
                        previous_registry, registry
                    )
                ):
                    raise HarnessError("注册表变化超出当前任务；拒绝verify采用。")
                state.setdefault("registry_history", []).append(state["registry_sha256"])
                state["registry_sha256"] = current_registry_sha256
                state["registry_snapshot"] = registry
            else:
                if not (
                    _registry_transition_is_scoped(previous_registry, registry, task_id)
                    or _registry_transition_is_wave_harness_upgrade(
                        previous_registry, registry
                    )
                ):
                    raise HarnessError("任务启动后全局注册表合同发生变化；拒绝verify执行。")
                if not _verification_commands_unchanged(
                    previous_registry, registry, task_id
                ):
                    raise HarnessError("任务启动后验收命令发生变化；拒绝verify执行。")
        current_snapshot = collect_git_snapshot(registry)
        if task_state.get("start_snapshot") is None:
            task_state["start_snapshot"] = {
                "source_tree": current_snapshot["git"]["source_tree"],
                "source_manifest": current_snapshot["git"]["source_manifest"],
                "dirty_diff_sha256": current_snapshot["git"]["dirty_diff_sha256"],
            }
        delta = _task_delta(task_state["start_snapshot"], current_snapshot)
        registry_history = state.get("registry_history", [])
        if (
            registry_history
            and task_state.get("start_registry_sha256") != registry_history[-1]
        ):
            try:
                registry_relative = REGISTRY_PATH.relative_to(ROOT).as_posix()
            except ValueError:
                registry_relative = ""
            if registry_relative and registry_relative not in delta:
                delta = sorted([*delta, registry_relative])
        allowed_files = unit.get("allowed_files", task["allowed_files"])
        disallowed = [
            path
            for path in delta
            if not _path_allowed(path, allowed_files)
        ]
        if disallowed:
            raise HarnessError(f"任务实际差异超出允许范围：{disallowed}")
        expected_migrations = task["change_budget"]["expected_migrations"]
        forbidden = [
            path
            for path in delta
            if _path_forbidden(path, task["forbidden_files"], expected_migrations)
        ]
        if forbidden:
            raise HarnessError(f"任务实际差异命中禁止范围：{forbidden}")
        migration_delta = [
            path for path in delta if path.startswith("backend/migrations/")
        ]
        if len(migration_delta) > expected_migrations:
            raise HarnessError("任务实际迁移数超过change budget。")
        expected = unit.get("change_budget", task["change_budget"])["expected_files"]
        if len(delta) > expected * 1.5:
            raise HarnessError("任务实际文件数超过change budget 50%；必须暂停回填并拆分。")

        outcomes: list[dict[str, Any]] = []
        ok = True
        active_subtasks = _unit_subtask_ids(unit, task)
        task_state["active_subtasks"] = active_subtasks
        for subtask_id in active_subtasks:
            subtask = task_state["subtasks"][subtask_id]
            subtask["status"] = "running"
            subtask["input_baseline"] = {
                "source_tree": task_state["start_snapshot"]["source_tree"],
                "dirty_diff_sha256": task_state["start_snapshot"]["dirty_diff_sha256"],
            }
            subtask["actual_modified_files"] = delta
            subtask["started_at"] = utc_now()
        for index, command in enumerate(task["acceptance_commands"], start=1):
            _validate_command(command, registry["command_policy"])
            argv = _resolve_command_argv(command)
            cwd = (ROOT / command["cwd"]).resolve()
            try:
                cwd.relative_to(ROOT)
            except ValueError as exc:
                raise HarnessError("命令cwd超出仓库。") from exc
            started_at = utc_now()
            timed_out = False
            try:
                completed = subprocess.run(
                    argv,
                    cwd=cwd,
                    capture_output=True,
                    check=False,
                    shell=False,
                    timeout=command["timeout_seconds"],
                )
                stdout = completed.stdout
                stderr = completed.stderr
                exit_code = completed.returncode
            except subprocess.TimeoutExpired as exc:
                timed_out = True
                stdout = exc.stdout or b""
                stderr = exc.stderr or b""
                exit_code = 124
            previous = (
                state["evidence_chain"][-1]["file_sha256"]
                if state["evidence_chain"]
                else None
            )
            finished_at = utc_now()
            evidence = {
                "schema": "safehome.rc0810.command-evidence.v1",
                "task": task_id,
                "owner": state.get("operator_id", "runner"),
                "reviewer": None,
                "valid_until": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                "stale_if": registry["evidence_policy"]["invalidation"]["triggers"],
                "commit": current_snapshot["git"]["head"],
                "head_tree": current_snapshot["git"]["head_tree"],
                "source_tree": current_snapshot["git"]["source_tree"],
                "source_manifest_sha256": current_snapshot["git"]["source_manifest_sha256"],
                "dirty_diff_sha256": current_snapshot["git"]["dirty_diff_sha256"],
                "head_verified": current_snapshot["git"]["head_verified"],
                "registry_sha256": sha256_bytes(REGISTRY_PATH.read_bytes()),
                "argv": command["argv"],
                "cwd": command["cwd"],
                "started_at": started_at,
                "finished_at": finished_at,
                "timezone": "UTC",
                "timeout_seconds": command["timeout_seconds"],
                "timed_out": timed_out,
                "exit_code": exit_code,
                "stdout_summary": _output_summary(stdout),
                "stdout_sha256": sha256_bytes(stdout),
                "stderr_summary": _output_summary(stderr),
                "stderr_sha256": sha256_bytes(stderr),
                "python_version": platform.python_version(),
                "node_version": _node_version(),
                "os": platform.platform(),
                "previous_evidence_sha256": previous,
            }
            evidence["record_sha256"] = sha256_bytes(canonical_json(evidence))
            evidence_path = (
                RUNTIME_ROOT
                / state["run_id"]
                / "evidence"
                / task_id
                / f"command-{index:03d}-{uuid.uuid4().hex[:8]}.json"
            )
            atomic_write_json(evidence_path, evidence)
            file_hash = sha256_bytes(evidence_path.read_bytes())
            chain_item = {"path": str(evidence_path), "file_sha256": file_hash}
            state["evidence_chain"].append(chain_item)
            outcomes.append(
                {
                    "evidence": chain_item,
                    "exit_code": exit_code,
                    "timed_out": timed_out,
                    "argv": command["argv"],
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "test_count": command.get("expected_test_count", 1),
                }
            )
            if exit_code != 0:
                ok = False
                break
        task_state["actual_modified_files"] = delta
        task_state["outcomes"] = outcomes
        task_state["status"] = "implemented" if ok else "in_progress"
        for subtask_id in active_subtasks:
            subtask = task_state["subtasks"][subtask_id]
            subtask["status"] = "running" if ok else "review_failed"
            subtask["finished_at"] = utc_now()
            subtask["commands"] = [outcome["argv"] for outcome in outcomes]
            subtask["exit_codes"] = [outcome["exit_code"] for outcome in outcomes]
            subtask["test_count"] = sum(outcome["test_count"] for outcome in outcomes)
            subtask["failure_summary"] = None if ok else "acceptance_command_failed"
            subtask["source_tree"] = current_snapshot["git"]["source_tree"]
            subtask["dirty_diff_sha256"] = current_snapshot["git"]["dirty_diff_sha256"]
            subtask["evidence_dir"] = str(
                RUNTIME_ROOT / state["run_id"] / "evidence" / task_id
            )
        task_state["evidence_status"] = "current" if ok else "failed"
        state["updated_at"] = utc_now()
        write_state(state)
    return (0 if ok else 1), {
        "run_id": state["run_id"],
        "task": task_id,
        "status": task_state["status"],
        "head_verified": current_snapshot["git"]["head_verified"],
        "source_tree": current_snapshot["git"]["source_tree"],
        "dirty_diff_sha256": current_snapshot["git"]["dirty_diff_sha256"],
        "outcomes": outcomes,
    }


def review_task(
    registry: dict[str, Any],
    task_id: str,
    *,
    decision: str | None,
    reviewer_id: str | None,
    decision_evidence: str | None,
    pending_wave: bool = False,
) -> dict[str, Any]:
    with state_lock():
        state = read_state()
        if state is None or task_id not in state["tasks"]:
            raise HarnessError(f"{task_id}尚未start。")
        _validate_evidence_chain(state)
        task_state = state["tasks"][task_id]
        wave = _wave_for_unit(registry, task_id)
        if pending_wave and wave is None:
            raise HarnessError("该任务不属于A/B/C审查波次。")
        if pending_wave and any((decision, reviewer_id, decision_evidence)):
            raise HarnessError("主审checkpoint不得携带独立review decision。")
        if wave is not None and not pending_wave:
            raise HarnessError("波次任务不得使用单任务独立review decision。")
        run_dir = RUNTIME_ROOT / state["run_id"]
        packet_path = run_dir / "reviews" / f"{task_id}.json"
        if decision is None:
            unit = unit_map(registry)[task_id]
            task = task_map(registry)[unit["task"]]
            current_snapshot = collect_git_snapshot(registry)
            if task_state.get("evidence_status") != "current" or not task_state.get("outcomes"):
                raise HarnessError("测试证据缺失或已失效；必须重新verify。")
            latest_evidence_path = Path(
                task_state["outcomes"][-1]["evidence"]["path"]
            )
            latest_evidence = json.loads(latest_evidence_path.read_text(encoding="utf-8"))
            if (
                latest_evidence.get("source_tree") != current_snapshot["git"]["source_tree"]
                or latest_evidence.get("dirty_diff_sha256")
                != current_snapshot["git"]["dirty_diff_sha256"]
                or latest_evidence.get("registry_sha256")
                != sha256_bytes(REGISTRY_PATH.read_bytes())
            ):
                task_state["evidence_status"] = "stale"
                task_state["status"] = "stale"
                state["updated_at"] = utc_now()
                write_state(state)
                raise HarnessError("源码、差异或注册表已变化；旧测试证据不得进入审查。")
            if task_state["status"] != "implemented":
                raise HarnessError("只有implemented任务可生成独立审查包。")
            current_contract_sha256 = _task_contract_sha256(task, unit)
            start_contract_sha256 = task_state.get("start_task_contract_sha256")
            if start_contract_sha256 != current_contract_sha256:
                raise HarnessError("任务合同在start后发生漂移；必须重新冻结范围并重验。")
            if task_state.get("start_registry_sha256") != sha256_bytes(
                REGISTRY_PATH.read_bytes()
            ):
                raise HarnessError("任务注册表在start后发生漂移；必须重新冻结范围并重验。")
            delta = _task_delta(task_state["start_snapshot"], current_snapshot)
            registry_history = state.get("registry_history", [])
            if (
                registry_history
                and task_state.get("start_registry_sha256") != registry_history[-1]
            ):
                try:
                    registry_relative = REGISTRY_PATH.relative_to(ROOT).as_posix()
                except ValueError:
                    registry_relative = ""
                if registry_relative and registry_relative not in delta:
                    delta = sorted([*delta, registry_relative])
            packet = {
                "schema": "safehome.rc0810.review-packet.v1",
                "task": task_id,
                "base_commit": current_snapshot["git"]["head"],
                "source_tree": current_snapshot["git"]["source_tree"],
                "dirty_diff_sha256": current_snapshot["git"]["dirty_diff_sha256"],
                "registry_sha256": sha256_bytes(REGISTRY_PATH.read_bytes()),
                "task_contract_sha256": current_contract_sha256,
                "initial_task_contract_sha256": task_state.get(
                    "initial_task_contract_sha256"
                ),
                "start_task_contract_sha256": start_contract_sha256,
                "current_task_contract_sha256": current_contract_sha256,
                "start_registry_sha256": task_state.get("start_registry_sha256"),
                "actual_modified_files": delta,
                "concurrent_inherited_overlays": task_state.get(
                    "concurrent_inherited_overlays", []
                ),
                "active_subtasks": task_state.get("active_subtasks", []),
                "test_evidence": task_state.get("outcomes", []),
                "rollback": task_state["subtasks"][next(iter(task_state["subtasks"]))]["rollback_point"],
                "created_at": utc_now(),
                "review_decision": None,
                "challenge_nonce": uuid.uuid4().hex,
            }
            if pending_wave:
                checkpoint = {
                    "task": task_id,
                    "wave": wave["id"],
                    "status": "review_pending_wave",
                    "commit": current_snapshot["git"]["head"],
                    "source_tree": current_snapshot["git"]["source_tree"],
                    "dirty_diff_sha256": current_snapshot["git"]["dirty_diff_sha256"],
                    "actual_modified_files": delta,
                    "test_evidence": task_state.get("outcomes", []),
                    "recorded_at": utc_now(),
                    "independent_review_pass": False,
                }
                task_state["status"] = "review_pending_wave"
                task_state["main_review_checkpoint"] = checkpoint
                task_state["review_packet"] = None
                task_state["review"] = None
                for subtask_id in task_state.get("active_subtasks", []):
                    task_state["subtasks"][subtask_id]["status"] = (
                        "review_pending_wave"
                    )
                waves = state.setdefault("wave_checkpoints", {})
                declared_base = wave.get("base_checkpoint")
                base_commit = (
                    declared_base["commit"]
                    if isinstance(declared_base, dict)
                    else task_state["start_snapshot"].get("commit")
                )
                base_source_tree = (
                    _run_git("rev-parse", f"{base_commit}^{{tree}}")
                    .decode("ascii")
                    .strip()
                    if base_commit
                    else task_state["start_snapshot"]["source_tree"]
                )
                wave_state = waves.setdefault(
                    wave["id"],
                    {
                        "status": "in_progress",
                        "base_checkpoint": declared_base
                        or state.get("last_review_pass_checkpoint")
                        or state.get("last_verified_checkpoint"),
                        "base_commit": base_commit,
                        "base_source_tree": base_source_tree,
                        "pending_tasks": [],
                    },
                )
                wave_state["status"] = "review_pending_wave"
                wave_state["latest_task"] = task_id
                wave_state["updated_at"] = utc_now()
                if task_id not in wave_state["pending_tasks"]:
                    wave_state["pending_tasks"].append(task_id)
                state["last_progress_checkpoint"] = (
                    f"{task_id}:review_pending_wave"
                )
                state["updated_at"] = utc_now()
                write_state(state)
                return {
                    "task": task_id,
                    "status": "review_pending_wave",
                    "wave": wave["id"],
                    "independent_review_pass": False,
                }
            atomic_write_json(packet_path, packet)
            packet_hash = sha256_bytes(packet_path.read_bytes())
            task_state["status"] = "reviewing"
            task_state["review_packet"] = {
                "path": str(packet_path),
                "sha256": packet_hash,
            }
            state["updated_at"] = utc_now()
            write_state(state)
            return {
                "task": task_id,
                "status": "reviewing",
                "review_decision": None,
                "review_packet_path": str(packet_path),
                "review_packet_sha256": packet_hash,
            }
        if task_state["status"] != "reviewing":
            raise HarnessError("任务未处于reviewing状态。")
        if decision not in {"pass", "fix_required", "blocked_external"}:
            raise HarnessError("审查结论必须为pass/fix_required/blocked_external。")
        if not reviewer_id or reviewer_id.lower() in {
            "runner",
            "automation",
            "self",
            task_id.lower(),
            str(state.get("operator_id", "runner")).lower(),
        }:
            raise HarnessError("审查结论必须来自独立reviewer。")
        packet = task_state["review_packet"]
        path = Path(packet["path"])
        if not path.is_file() or sha256_bytes(path.read_bytes()) != packet["sha256"]:
            raise HarnessError("审查包缺失或被篡改。")
        packet_record = json.loads(path.read_text(encoding="utf-8"))
        current_snapshot = collect_git_snapshot(registry)
        if (
            packet_record.get("source_tree")
            != current_snapshot["git"]["source_tree"]
            or packet_record.get("dirty_diff_sha256")
            != current_snapshot["git"]["dirty_diff_sha256"]
            or packet_record.get("registry_sha256")
            != sha256_bytes(REGISTRY_PATH.read_bytes())
        ):
            task_state["evidence_status"] = "stale"
            task_state["status"] = "stale"
            state["updated_at"] = utc_now()
            write_state(state)
            raise HarnessError("源码、差异或注册表已变化；旧审查结论不得验收。")
        if not decision_evidence:
            raise HarnessError("独立审查必须提供decision evidence文件。")
        decision_path = Path(decision_evidence).resolve()
        review_root = (run_dir / "reviews").resolve()
        if not _path_within(decision_path, review_root) or not decision_path.is_file():
            raise HarnessError("decision evidence必须位于当前run的reviews目录。")
        try:
            decision_record = json.loads(decision_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise HarnessError("decision evidence不是有效JSON。") from exc
        if decision_record.get("schema") != "safehome.rc0810.review-decision.v1":
            raise HarnessError("decision evidence schema不兼容。")
        if (
            decision_record.get("review_packet_sha256") != packet["sha256"]
            or decision_record.get("challenge_nonce")
            != packet_record.get("challenge_nonce")
            or decision_record.get("decision") != decision
            or decision_record.get("reviewer_id") != reviewer_id
            or decision_record.get("reviewer_kind")
            not in registry["independent_review_policy"]["allowed_reviewer_kinds"]
        ):
            raise HarnessError("decision evidence与审查包、结论或reviewer不一致。")
        try:
            valid_until = datetime.fromisoformat(decision_record["valid_until"])
        except (KeyError, TypeError, ValueError) as exc:
            raise HarnessError("decision evidence缺少有效期限。") from exc
        if valid_until.tzinfo is None or valid_until <= datetime.now(timezone.utc):
            raise HarnessError("decision evidence已过期或缺少时区。")
        if not isinstance(decision_record.get("findings"), list):
            raise HarnessError("decision evidence必须包含findings数组。")
        decision_hash = sha256_bytes(decision_path.read_bytes())
        status_by_decision = {
            "pass": "verified",
            "fix_required": "review_failed",
            "blocked_external": "blocked_external",
        }
        task_state["status"] = status_by_decision[decision]
        task_state["review"] = {
            "decision": decision,
            "reviewer_id": reviewer_id,
            "reviewer_kind": decision_record["reviewer_kind"],
            "packet_sha256": packet["sha256"],
            "decision_evidence_path": str(decision_path),
            "decision_evidence_sha256": decision_hash,
            "valid_until": decision_record["valid_until"],
            "recorded_at": utc_now(),
        }
        if decision == "pass":
            state["last_verified_checkpoint"] = f"{task_id}:verified"
            state["last_review_pass_checkpoint"] = f"{task_id}:verified"
            state["last_progress_checkpoint"] = f"{task_id}:verified"
            unit = unit_map(registry)[task_id]
            for subtask_id in task_state.get("active_subtasks", []):
                subtask = task_state["subtasks"][subtask_id]
                shared_across_phases = sum(
                    subtask_id in candidate.get("subtasks", [])
                    for candidate in registry["execution_units"]
                    if candidate["task"] == unit["task"]
                ) > 1
                subtask["status"] = (
                    f"{unit['phase']}_verified" if shared_across_phases else "verified"
                )
                subtask["review_decision"] = "pass"
        state["updated_at"] = utc_now()
        write_state(state)
    return {"task": task_id, "status": task_state["status"], "decision": decision}


def review_wave(
    registry: dict[str, Any],
    wave_id: str,
    *,
    decision: str | None,
    reviewer_id: str | None,
    decision_evidence: str | None,
) -> dict[str, Any]:
    wave = review_wave_map(registry).get(wave_id)
    if wave is None:
        raise HarnessError(f"未知审查波次：{wave_id}")
    with state_lock():
        state = read_state()
        if state is None:
            raise HarnessError("尚无活动run。")
        _validate_evidence_chain(state)
        if not _previous_wave_reviews_complete(registry, state, wave_id):
            raise HarnessError("前一审查波次尚未review pass。")
        task_records = {
            task_id: state["tasks"].get(task_id)
            for task_id in wave["execution_units"]
        }
        if any(
            record is None or record.get("status") != "review_pending_wave"
            for record in task_records.values()
        ):
            raise HarnessError("波次冻结点尚未齐备review_pending_wave任务。")
        run_dir = RUNTIME_ROOT / state["run_id"]
        wave_state = state.get("wave_checkpoints", {}).get(wave_id)
        if not isinstance(wave_state, dict):
            raise HarnessError("波次checkpoint缺失。")
        packet_path = run_dir / "reviews" / f"wave-{wave_id}.json"
        if decision is None:
            if wave_state.get("status") == "reviewing":
                raise HarnessError("波次已处于reviewing状态。")
            current_snapshot = collect_git_snapshot(registry)
            freeze_record = task_records[wave["freeze_unit"]]
            freeze_checkpoint = freeze_record["main_review_checkpoint"]
            latest_evidence_path = Path(
                freeze_checkpoint["test_evidence"][-1]["evidence"]["path"]
            )
            latest_evidence = json.loads(
                latest_evidence_path.read_text(encoding="utf-8")
            )
            if (
                freeze_checkpoint.get("source_tree")
                != current_snapshot["git"]["source_tree"]
                or latest_evidence.get("registry_sha256")
                != sha256_bytes(REGISTRY_PATH.read_bytes())
            ):
                freeze_record["previous_status"] = freeze_record["status"]
                freeze_record["status"] = "stale"
                freeze_record["evidence_status"] = "stale"
                wave_state["status"] = "stale"
                state["updated_at"] = utc_now()
                write_state(state)
                raise HarnessError("波次冻结点源码或注册表已变化；checkpoint测试证据已失效。")
            actual_modified_files = sorted(
                set(
                    _committed_diff_files(
                        wave_state.get("base_commit"), current_snapshot["git"]["head"]
                    )
                )
                | {
                    path
                    for record in task_records.values()
                    for path in record["main_review_checkpoint"]["actual_modified_files"]
                }
            )
            modified_files_bytes = json.dumps(
                actual_modified_files,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
            review_root = (run_dir / "reviews").resolve()
            replacement_binding = _load_reviewer_replacement_binding(
                registry, state, wave_id, review_root
            )
            packet = {
                "schema": "safehome.rc0810.review-packet.v1",
                "task": f"WAVE-{wave_id}",
                "wave": wave_id,
                "base_checkpoint": wave_state.get("base_checkpoint"),
                "base_source_tree": wave_state.get("base_source_tree"),
                "base_commit": wave_state.get("base_commit"),
                "head_commit": current_snapshot["git"]["head"],
                "source_tree": current_snapshot["git"]["source_tree"],
                "dirty_diff_sha256": current_snapshot["git"]["dirty_diff_sha256"],
                "registry_sha256": sha256_bytes(REGISTRY_PATH.read_bytes()),
                "execution_units": wave["execution_units"],
                "freeze_unit": wave["freeze_unit"],
                "actual_modified_files": actual_modified_files,
                "actual_modified_files_sha256": sha256_bytes(modified_files_bytes),
                "test_evidence": [
                    outcome
                    for record in task_records.values()
                    for outcome in record["main_review_checkpoint"]["test_evidence"]
                ],
                "created_at": utc_now(),
                "review_decision": None,
                "challenge_nonce": uuid.uuid4().hex,
            }
            if replacement_binding is not None:
                packet["reviewer_replacement"] = replacement_binding
            atomic_write_json(packet_path, packet)
            packet_hash = sha256_bytes(packet_path.read_bytes())
            wave_state["status"] = "reviewing"
            wave_state["review_packet"] = {
                "path": str(packet_path),
                "sha256": packet_hash,
            }
            if replacement_binding is None:
                wave_state.pop("reviewer_replacement_binding", None)
            else:
                wave_state["reviewer_replacement_binding"] = replacement_binding
            state["last_progress_checkpoint"] = f"wave:{wave_id}:reviewing"
            state["updated_at"] = utc_now()
            write_state(state)
            return {
                "wave": wave_id,
                "status": "reviewing",
                "review_decision": None,
                "review_packet_path": str(packet_path),
                "review_packet_sha256": packet_hash,
            }

        if wave_state.get("status") != "reviewing":
            raise HarnessError("波次未处于reviewing状态。")
        if decision not in {"pass", "fix_required", "blocked_external"}:
            raise HarnessError("审查结论必须为pass/fix_required/blocked_external。")
        if not reviewer_id or reviewer_id.lower() in {
            "runner",
            "automation",
            "self",
            str(state.get("operator_id", "runner")).lower(),
        }:
            raise HarnessError("审查结论必须来自独立reviewer。")
        fixed_reviewer = state.get("fixed_wave_reviewer_id")
        packet = wave_state["review_packet"]
        path = Path(packet["path"])
        if not path.is_file() or sha256_bytes(path.read_bytes()) != packet["sha256"]:
            raise HarnessError("波次审查包缺失或被篡改。")
        packet_record = json.loads(path.read_text(encoding="utf-8"))
        current_snapshot = collect_git_snapshot(registry)
        if (
            packet_record.get("source_tree") != current_snapshot["git"]["source_tree"]
            or packet_record.get("dirty_diff_sha256")
            != current_snapshot["git"]["dirty_diff_sha256"]
            or packet_record.get("registry_sha256")
            != sha256_bytes(REGISTRY_PATH.read_bytes())
        ):
            wave_state["status"] = "stale"
            for record in task_records.values():
                record["status"] = "stale"
                record["evidence_status"] = "stale"
            state["updated_at"] = utc_now()
            write_state(state)
            raise HarnessError("源码、差异或注册表已变化；旧波次结论不得验收。")
        if not decision_evidence:
            raise HarnessError("独立审查必须提供decision evidence文件。")
        decision_path = Path(decision_evidence).resolve()
        review_root = (run_dir / "reviews").resolve()
        if not _path_within(decision_path, review_root) or not decision_path.is_file():
            raise HarnessError("decision evidence必须位于当前run的reviews目录。")
        try:
            decision_record = json.loads(decision_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise HarnessError("decision evidence不是有效JSON。") from exc
        if decision_record.get("schema") != "safehome.rc0810.review-decision.v1":
            raise HarnessError("decision evidence schema不兼容。")
        if (
            decision_record.get("review_packet_sha256") != packet["sha256"]
            or decision_record.get("challenge_nonce")
            != packet_record.get("challenge_nonce")
            or decision_record.get("decision") != decision
            or decision_record.get("reviewer_id") != reviewer_id
            or decision_record.get("reviewer_kind")
            not in registry["independent_review_policy"]["allowed_reviewer_kinds"]
        ):
            raise HarnessError("decision evidence与波次包、结论或reviewer不一致。")
        try:
            valid_until = datetime.fromisoformat(decision_record["valid_until"])
        except (KeyError, TypeError, ValueError) as exc:
            raise HarnessError("decision evidence缺少有效期限。") from exc
        if valid_until.tzinfo is None or valid_until <= datetime.now(timezone.utc):
            raise HarnessError("decision evidence已过期或缺少时区。")
        if not isinstance(decision_record.get("findings"), list):
            raise HarnessError("decision evidence必须包含findings数组。")

        replacement_metadata = None
        if fixed_reviewer and reviewer_id != fixed_reviewer:
            if "reviewer_replacement" in decision_record:
                raise HarnessError("decision evidence不得自报reviewer替换路径或哈希。")
            replacement = packet_record.get("reviewer_replacement")
            state_replacement = wave_state.get("reviewer_replacement_binding")
            if (
                not isinstance(replacement, dict)
                or replacement != state_replacement
                or replacement.get("previous_reviewer_id") != fixed_reviewer
                or replacement.get("replacement_reviewer_id") != reviewer_id
            ):
                raise HarnessError("reviewer替换证据未在波次冻结包与状态中预绑定。")
            current_replacement = _load_reviewer_replacement_binding(
                registry, state, wave_id, review_root
            )
            if current_replacement != replacement:
                raise HarnessError("reviewer替换证据在波次冻结后新增或变化。")
            replacement_metadata = {
                "previous_reviewer_id": fixed_reviewer,
                "evidence_path": replacement["evidence_path"],
                "evidence_sha256": replacement["evidence_sha256"],
                "reason": "previous_reviewer_ended_and_cannot_be_recovered",
            }

        state["fixed_wave_reviewer_id"] = reviewer_id
        decision_hash = sha256_bytes(decision_path.read_bytes())
        status_by_decision = {
            "pass": "review_pass",
            "fix_required": "review_failed",
            "blocked_external": "blocked_external",
        }
        wave_state["status"] = status_by_decision[decision]
        wave_state["review"] = {
            "decision": decision,
            "reviewer_id": reviewer_id,
            "reviewer_kind": decision_record["reviewer_kind"],
            "packet_sha256": packet["sha256"],
            "decision_evidence_path": str(decision_path),
            "decision_evidence_sha256": decision_hash,
            "valid_until": decision_record["valid_until"],
            "recorded_at": utc_now(),
        }
        if replacement_metadata is not None:
            wave_state["review"]["reviewer_replacement"] = replacement_metadata
        if decision == "pass":
            for task_id, record in task_records.items():
                record["status"] = "verified"
                record["review"] = {**wave_state["review"], "wave": wave_id}
                for subtask_id in record.get("active_subtasks", []):
                    record["subtasks"][subtask_id]["status"] = "verified"
                    record["subtasks"][subtask_id]["review_decision"] = "pass"
            checkpoint = f"{wave['freeze_unit']}:verified"
            state["last_verified_checkpoint"] = checkpoint
            state["last_review_pass_checkpoint"] = checkpoint
            state["last_progress_checkpoint"] = checkpoint
        else:
            state["last_progress_checkpoint"] = (
                f"wave:{wave_id}:{status_by_decision[decision]}"
            )
        state["updated_at"] = utc_now()
        write_state(state)
    return {
        "wave": wave_id,
        "status": status_by_decision[decision],
        "decision": decision,
    }


def resume_command(registry: dict[str, Any]) -> dict[str, Any]:
    with state_lock():
        state = read_state()
        if state is None:
            raise HarnessError("没有可恢复的run。")
        _validate_evidence_chain(state)
        progress = state.get("last_progress_checkpoint")
        if progress and not progress.startswith("wave:"):
            task_id, _, status = progress.partition(":")
            record = state["tasks"].get(task_id)
            if record and status == "review_pending_wave":
                checkpoint = record.get("main_review_checkpoint", {})
                current_snapshot = collect_git_snapshot(registry)
                if checkpoint.get("source_tree") != current_snapshot["git"]["source_tree"]:
                    record["previous_status"] = record["status"]
                    record["status"] = "stale"
                    record["evidence_status"] = "stale"
                    state["updated_at"] = utc_now()
                    write_state(state)
                    raise HarnessError("checkpoint源码已变化；旧测试证据已失效。")
            if record and record.get("status") == status and status in {
                "in_progress",
                "fixing",
                "review_pending_wave",
                "review_failed",
                "stale",
            }:
                return {
                    "run_id": state["run_id"],
                    "resume_from": progress,
                    "replayed_commands": 0,
                }
        if progress and progress.startswith("wave:"):
            return {
                "run_id": state["run_id"],
                "resume_from": progress,
                "replayed_commands": 0,
            }
        checkpoint = state.get("last_review_pass_checkpoint") or state.get(
            "last_verified_checkpoint"
        )
        return {
            "run_id": state["run_id"],
            "resume_from": checkpoint or "no_active_task",
            "replayed_commands": 0,
        }


def next_command(registry: dict[str, Any]) -> dict[str, Any]:
    state = read_state()
    task_states = {} if state is None else state["tasks"]
    terminal = {
        "verified",
        "committed",
        "pushed",
        "engineering_complete",
        "review_pending_wave",
    }

    def record_is_complete(record: dict[str, Any]) -> bool:
        return record.get("status") in terminal or (
            record.get("status") == "stale"
            and isinstance(record.get("review"), dict)
            and record["review"].get("decision") == "pass"
        )

    completed = {
        task_id
        for task_id, record in task_states.items()
        if record_is_complete(record)
    }
    for wave in registry.get("review_waves", []):
        completed.update(_active_wave_base_checkpoint_units(registry, state, wave))
    pending_dependencies = list(completed)
    units = unit_map(registry)
    while pending_dependencies:
        completed_unit = pending_dependencies.pop()
        for dependency in units.get(completed_unit, {}).get("dependencies", []):
            if dependency not in completed:
                completed.add(dependency)
                pending_dependencies.append(dependency)
    for unit in registry["execution_units"]:
        task_id = unit["id"]
        current = task_states.get(task_id)
        if current is None and task_id in completed:
            continue
        if current is not None and not record_is_complete(current):
            return {"task": task_id, "status": current["status"], "ready": False}
        dependencies_ready = set(unit["dependencies"]).issubset(completed)
        if current is None and dependencies_ready:
            wave = _wave_for_unit(registry, task_id)
            if (
                wave is not None
                and state is not None
                and not _previous_wave_reviews_complete(registry, state, wave["id"])
            ):
                blocked_wave = _previous_waves(registry, wave["id"])[-1]["id"]
                return {
                    "task": None,
                    "status": "wave_review_required",
                    "wave": blocked_wave,
                    "ready": False,
                }
            return {"task": task_id, "status": "planned", "ready": True}
    return {"task": None, "status": "complete", "ready": False}


def _recursive_dependents(
    registry: dict[str, Any], roots: set[str]
) -> list[str]:
    stale = set(roots)
    while True:
        before = len(stale)
        for task in registry["tasks"]:
            dependencies = set(task["dependencies"])
            dependencies.update(
                item.split(":", 1)[0] for item in task.get("phase_dependencies", [])
            )
            if dependencies & stale:
                stale.add(task["id"])
        if len(stale) == before:
            break
    return [task["id"] for task in registry["tasks"] if task["id"] in stale]


def _recursive_unit_dependents(
    registry: dict[str, Any], roots: set[str]
) -> list[str]:
    stale = set(roots)
    while True:
        before = len(stale)
        for unit in registry["execution_units"]:
            if set(unit["dependencies"]) & stale:
                stale.add(unit["id"])
        if len(stale) == before:
            break
    return [unit_id for unit_id in registry["execution_order"] if unit_id in stale]


def _latest_nonterminal_unit(
    registry: dict[str, Any], state: dict[str, Any], checkpoint_task_id: str | None
) -> str | None:
    nonterminal_statuses = {
        "in_progress",
        "fixing",
        "implemented",
        "reviewing",
        "review_failed",
        "review_pending_wave",
        "stale",
    }
    execution_positions = {
        unit_id: index for index, unit_id in enumerate(registry["execution_order"])
    }
    checkpoint_position = execution_positions.get(checkpoint_task_id or "", -1)
    return next(
        (
            unit_id
            for unit_id in reversed(registry["execution_order"])
            if unit_id in state["tasks"]
            and execution_positions[unit_id] >= checkpoint_position
            and state["tasks"][unit_id].get("status") in nonterminal_statuses
        ),
        None,
    )


def report_command(registry: dict[str, Any]) -> dict[str, Any]:
    with state_lock():
        state = read_state()
        if state is None:
            raise HarnessError("没有可报告的run。")
        _validate_evidence_chain(state)
        stale_tasks: list[str] = []
        current_registry_hash = sha256_bytes(REGISTRY_PATH.read_bytes())
        roots: set[str] = set()
        stale_reason: list[str] = []
        if current_registry_hash != state["registry_sha256"]:
            roots.update(
                _registry_change_roots(
                    state.get("registry_snapshot"), registry, state["tasks"]
                )
            )
            stale_reason.append("registry_changed")
        current_snapshot = collect_git_snapshot(registry)
        checkpoint = state.get("last_verified_checkpoint")
        checkpoint_task_id = checkpoint.split(":", 1)[0] if checkpoint else None
        active_task_id = _latest_nonterminal_unit(
            registry, state, checkpoint_task_id
        )
        source_anchor_id = active_task_id or checkpoint_task_id
        source_anchor = state["tasks"].get(source_anchor_id or "")
        if (
            source_anchor is not None
            and not source_anchor.get("outcomes")
            and checkpoint_task_id is not None
        ):
            source_anchor_id = checkpoint_task_id
            source_anchor = state["tasks"].get(checkpoint_task_id)
        if source_anchor and source_anchor.get("outcomes"):
            bound_source_tree = source_anchor["subtasks"][
                next(iter(source_anchor["subtasks"]))
            ].get("source_tree")
            if bound_source_tree != current_snapshot["git"]["source_tree"]:
                roots.add(source_anchor_id)
        if roots and "registry_changed" not in stale_reason:
            stale_reason.append("source_tree_changed")
        stale_units: list[str] = []
        if roots:
            stale_units = _recursive_unit_dependents(registry, roots)
            stale_parent_ids = {
                unit_map(registry)[unit_id]["task"] for unit_id in stale_units
            }
            stale_tasks = [
                task["id"] for task in registry["tasks"] if task["id"] in stale_parent_ids
            ]
            state["stale_tasks"] = {
                task_id: {
                    "status": "stale",
                    "reason": "+".join(stale_reason),
                    "detected_at": utc_now(),
                    "retest_required": True,
                }
                for task_id in stale_tasks
            }
            for unit_id in stale_units:
                if unit_id not in state["tasks"]:
                    continue
                state["tasks"][unit_id]["evidence_status"] = "stale"
                if state["tasks"][unit_id].get("status") != "stale":
                    state["tasks"][unit_id]["previous_status"] = state["tasks"][unit_id][
                        "status"
                    ]
                state["tasks"][unit_id]["status"] = "stale"
        stale_unit_set = set(stale_units)
        restored_any = False
        for unit_id, record in state["tasks"].items():
            if unit_id in stale_unit_set or record.get("status") != "stale":
                continue
            restored_status = _restorable_status(record)
            if restored_status is not None:
                record["status"] = restored_status
                record["evidence_status"] = "current"
                restored_any = True
        if roots or restored_any:
            state["updated_at"] = utc_now()
            write_state(state)
        report = {
            "schema": "safehome.rc0810.report.v1",
            "run_id": state["run_id"],
            "registry_sha256": current_registry_hash,
            "generated_at": utc_now(),
            "tasks": {
                task_id: {
                    "status": record["status"],
                    "actual_modified_files": record.get("actual_modified_files", []),
                    "review": record.get("review"),
                }
                for task_id, record in state["tasks"].items()
            },
            "next_task": next(
                (
                    task["id"]
                    for task in registry["tasks"]
                    if task["id"] not in state["tasks"]
                ),
                None,
            ),
            "production_release_approved": False,
            "external_gate_auto_approved": False,
            "review_waves": state.get("wave_checkpoints", {}),
            "stale_tasks": stale_tasks,
        }
        report_path = RUNTIME_ROOT / state["run_id"] / "report.json"
        atomic_write_json(report_path, report)
    report["report_path"] = str(report_path)
    report["report_sha256"] = sha256_bytes(report_path.read_bytes())
    return report


def _path_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def package_check(registry: dict[str, Any], artifact: str) -> dict[str, Any]:
    manifest_path = Path(artifact).resolve()
    if not (
        _path_within(manifest_path, RUNTIME_ROOT)
        or _path_within(manifest_path, ROOT)
    ):
        raise HarnessError("package manifest必须位于仓库或rc0810运行目录内。")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HarnessError("package manifest缺失或不是有效JSON。") from exc
    if manifest.get("schema") != "safehome.rc0810.package.v1":
        raise HarnessError("package manifest schema不兼容。")
    if manifest.get("built_from") not in {"git_archive", "staging"}:
        raise HarnessError("制品必须来自git archive或隔离staging。")
    if manifest.get("worktree_source_used") is not False:
        raise HarnessError("拒绝以工作区替代正式制品来源。")
    if manifest.get("complete_file_set") is not True:
        raise HarnessError("制品清单必须声明并证明完整文件集。")
    profile = registry.get("artifact_profiles", {}).get(manifest.get("profile_id"))
    if profile is None or profile.get("artifact_kind") != manifest.get("artifact_kind"):
        raise HarnessError("制品必须引用注册表中的受信artifact profile。")
    attestation = manifest.get("source_attestation", {})
    if (
        attestation.get("source_tree") != manifest.get("source_tree")
        or attestation.get("source_kind") != profile.get("source_kind")
    ):
        raise HarnessError("制品缺少可信且匹配的来源证明。")
    current = collect_git_snapshot(registry)
    bindings = {
        "commit": current["git"]["head"],
        "head_tree": current["git"]["head_tree"],
        "source_tree": current["git"]["source_tree"],
        "dirty_diff_sha256": current["git"]["dirty_diff_sha256"],
    }
    mismatched = [key for key, value in bindings.items() if manifest.get(key) != value]
    if mismatched:
        raise HarnessError(f"制品来源绑定不一致：{mismatched}")
    if manifest.get("artifact_kind") == "production_rc" and current["git"]["dirty"]:
        raise HarnessError("production RC不得从脏源码树生成。")
    if (
        manifest.get("artifact_kind") == "production_rc"
        and (
            attestation.get("source_kind") != "git_archive"
            or manifest.get("source_tree") != manifest.get("head_tree")
        )
    ):
        raise HarnessError("production RC必须来自同一HEAD的git archive。")
    root = Path(manifest.get("artifact_root", "")).resolve()
    if (
        not root.is_dir()
        or root == RUNTIME_ROOT
        or not _path_within(root, RUNTIME_ROOT)
        or _path_within(root, ROOT) and not _path_within(root, RUNTIME_ROOT)
    ):
        raise HarnessError("artifact_root必须是rc0810运行目录内的独立staging目录。")
    source_manifest = _manifest_from_tree(manifest["source_tree"])
    expected_paths = set(profile.get("expected_files", []))
    if not expected_paths or not expected_paths.issubset(source_manifest):
        raise HarnessError("artifact profile预期文件不在绑定源码树中。")
    expected_hashes = {
        relative: sha256_bytes(_run_git("cat-file", "blob", source_manifest[relative]))
        for relative in expected_paths
    }
    checked: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in manifest.get("files", []):
        relative = item.get("path")
        if not isinstance(relative, str) or not relative or relative in seen:
            raise HarnessError("制品文件路径缺失或重复。")
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise HarnessError("制品文件路径包含穿越。")
        target = (root / relative_path).resolve()
        if not _path_within(target, root) or target.is_symlink() or not target.is_file():
            raise HarnessError("制品文件不存在、越界或使用符号链接。")
        actual = sha256_bytes(target.read_bytes())
        if item.get("sha256") != actual or expected_hashes.get(relative) != actual:
            raise HarnessError(f"制品文件哈希不匹配：{relative}")
        seen.add(relative)
        checked.append({"path": relative, "sha256": actual})
    if not checked:
        raise HarnessError("制品文件清单不能为空。")
    actual_files: set[str] = set()
    for target in root.rglob("*"):
        if target.is_symlink():
            raise HarnessError("隔离制品目录禁止符号链接。")
        if target.is_file():
            actual_files.add(target.relative_to(root).as_posix())
    if actual_files != seen or seen != expected_paths:
        raise HarnessError("制品文件集与受信profile或完整manifest不一致。")
    return {
        "schema": "safehome.rc0810.package-check.v1",
        "status": "passed",
        "artifact_kind": manifest["artifact_kind"],
        "manifest_sha256": sha256_bytes(manifest_path.read_bytes()),
        "files_checked": len(checked),
        "source_tree": manifest["source_tree"],
        "production_release_approved": False,
    }


def _f00_start_snapshot(registry: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    frozen = registry["frozen_baseline"]
    frozen_manifest = _manifest_from_tree(frozen["source_tree"])
    current_snapshot = collect_git_snapshot(registry)
    current_manifest = current_snapshot["git"]["source_manifest"]
    shared_files = set(task.get("inherited_shared_files", []))
    inherited_overlay: dict[str, str | None] = {}
    effective_manifest = dict(frozen_manifest)
    for path in set(frozen_manifest) | set(current_manifest):
        if _path_allowed(path, task["allowed_files"]) and path not in shared_files:
            continue
        before = frozen_manifest.get(path)
        after = current_manifest.get(path)
        if before == after:
            continue
        inherited_overlay[path] = after
        if after is None:
            effective_manifest.pop(path, None)
        else:
            effective_manifest[path] = after
    return {
        "commit": frozen["head"],
        "source_tree": frozen["source_tree"],
        "source_manifest": effective_manifest,
        "dirty_diff_sha256": frozen["dirty_diff"]["sha256"],
        "binding": "frozen_preflight_plus_task_start_inherited_overlay",
        "concurrent_inherited_overlay": inherited_overlay,
        "concurrent_inherited_overlay_sha256": sha256_bytes(
            canonical_json(inherited_overlay)
        ),
    }


def _standard_start_snapshot(registry: dict[str, Any]) -> dict[str, Any]:
    snapshot = collect_git_snapshot(registry)
    return {
        "commit": snapshot["git"]["head"],
        "source_tree": snapshot["git"]["source_tree"],
        "source_manifest": snapshot["git"]["source_manifest"],
        "dirty_diff_sha256": snapshot["git"]["dirty_diff_sha256"],
        "binding": "task_start_worktree",
    }


def _wave_review_start_snapshot(
    state: dict[str, Any], wave: dict[str, Any]
) -> dict[str, Any]:
    """Recover the immutable reviewed tree for runs opened by the old Fix Loop."""

    wave_state = state.get("wave_checkpoints", {}).get(wave["id"], {})
    review = wave_state.get("review", {})
    packet_path = RUNTIME_ROOT / state["run_id"] / "reviews" / f"wave-{wave['id']}.json"
    expected_hash = review.get("packet_sha256")
    if not packet_path.is_file() or not expected_hash:
        raise HarnessError("Fix Loop缺少原波次审查包，拒绝猜测重开基线。")
    if sha256_bytes(packet_path.read_bytes()) != expected_hash:
        raise HarnessError("Fix Loop原波次审查包哈希不匹配。")
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    source_tree = packet.get("source_tree")
    if not isinstance(source_tree, str) or not source_tree:
        raise HarnessError("Fix Loop原波次审查包缺少源码树。")
    return {
        "commit": packet.get("head_commit"),
        "source_tree": source_tree,
        "source_manifest": _manifest_from_tree(source_tree),
        "dirty_diff_sha256": packet.get("dirty_diff_sha256"),
        "binding": "wave_review_packet_legacy_fix_recovery",
        "review_packet_sha256": expected_hash,
    }


def _task_contract_sha256(task: dict[str, Any], unit: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json({"task": task, "execution_unit": unit}))


def _registry_transition_is_wave_harness_upgrade(
    previous: dict[str, Any], current: dict[str, Any]
) -> bool:
    if previous.get("review_waves") is not None:
        return False
    if (
        current.get("version") != "2026-08-24.wave-review-v1"
        or current.get("review_waves") != PRODUCTION_REVIEW_WAVES
    ):
        return False
    allowed = {
        "version",
        "state_machine",
        "subtask_record_schema",
        "independent_review_policy",
        "review_waves",
        "tasks",
    }
    if {
        key: value for key, value in previous.items() if key not in allowed
    } != {key: value for key, value in current.items() if key not in allowed}:
        return False
    previous_tasks = json.loads(json.dumps(previous["tasks"]))
    current_tasks = json.loads(json.dumps(current["tasks"]))
    previous_f00 = next(task for task in previous_tasks if task["id"] == "RC0810-F00")
    current_f00 = next(task for task in current_tasks if task["id"] == "RC0810-F00")
    expected_f00_commands = json.loads(
        json.dumps(previous_f00["acceptance_commands"])
    )
    if len(expected_f00_commands) != 1:
        return False
    expected_f00_commands[0]["timeout_seconds"] = 360
    expected_f00_commands[0]["expected_test_count"] = 13
    if current_f00["acceptance_commands"] != expected_f00_commands:
        return False
    current_f00["acceptance_commands"] = previous_f00["acceptance_commands"]
    return current_tasks == previous_tasks


def _registry_transition_is_declared_checkpoint_resume(
    previous: dict[str, Any],
    current: dict[str, Any],
    wave: dict[str, Any] | None,
    task_id: str,
) -> bool:
    if wave is None or not isinstance(wave.get("base_checkpoint"), dict):
        return False
    checkpoint = wave["base_checkpoint"]
    legacy_checkpoint = (
        wave.get("id") == "A"
        and checkpoint == PRODUCTION_REVIEW_WAVES[0]["base_checkpoint"]
    )
    if legacy_checkpoint:
        try:
            relative = "content/rc0810_release_candidate_registry.json"
            raw = _run_git("show", f"{checkpoint['commit']}:{relative}")
            checkpoint_registry = json.loads(raw.decode("utf-8"))
        except (HarnessError, KeyError, UnicodeDecodeError, json.JSONDecodeError):
            return False
        candidate = json.loads(json.dumps(current))
        checkpoint_tasks = task_map(checkpoint_registry)
        candidate_tasks = task_map(candidate)
        for unit_id in wave.get("execution_units", []):
            unit = unit_map(candidate).get(unit_id)
            if unit is None:
                return False
            parent_id = unit.get("task")
            if parent_id not in checkpoint_tasks or parent_id not in candidate_tasks:
                return False
            candidate_tasks[parent_id].clear()
            candidate_tasks[parent_id].update(
                json.loads(json.dumps(checkpoint_tasks[parent_id]))
            )
        if _registry_transition_is_wave_harness_upgrade(
            checkpoint_registry, candidate
        ):
            return True
        if {
            key: value for key, value in previous.items() if key != "tasks"
        } != {key: value for key, value in current.items() if key != "tasks"}:
            return False
        previous_tasks = task_map(previous)
        current_tasks = task_map(current)
        changed_tasks = {
            task_id
            for task_id in set(previous_tasks) | set(current_tasks)
            if previous_tasks.get(task_id) != current_tasks.get(task_id)
        }
        checkpoint_parent_tasks = {
            unit_map(current)[unit_id]["task"]
            for unit_id in checkpoint.get("execution_units", [])
            if unit_id in unit_map(current)
        }
        return bool(changed_tasks) and changed_tasks <= checkpoint_parent_tasks and all(
            current_tasks.get(parent_id) == checkpoint_tasks.get(parent_id)
            for parent_id in changed_tasks
        )
    if not _legacy_phase_checkpoint_is_valid(
        wave, checkpoint
    ) and not _historical_checkpoint_evidence_is_valid(current, checkpoint):
        return False
    candidate = json.loads(json.dumps(current))
    candidate_wave = review_wave_map(candidate).get(wave["id"])
    previous_wave = review_wave_map(previous).get(wave["id"])
    if candidate_wave is None or previous_wave is None:
        return False
    if "base_checkpoint" in previous_wave:
        candidate_wave["base_checkpoint"] = json.loads(
            json.dumps(previous_wave["base_checkpoint"])
        )
    else:
        candidate_wave.pop("base_checkpoint", None)
    return _registry_transition_is_scoped(previous, candidate, task_id)


def _registry_transition_is_scoped(
    previous: dict[str, Any], current: dict[str, Any], task_id: str
) -> bool:
    current_unit = unit_map(current).get(task_id)
    previous_unit = unit_map(previous).get(task_id)
    if current_unit is None or previous_unit is None:
        return False
    parent_id = current_unit.get("task")
    if parent_id != previous_unit.get("task"):
        return False
    ignored = {"version", "tasks", "execution_units"}
    if {
        key: value for key, value in previous.items() if key not in ignored
    } != {key: value for key, value in current.items() if key not in ignored}:
        return False
    if {
        item["id"]: item for item in previous["tasks"] if item["id"] != parent_id
    } != {item["id"]: item for item in current["tasks"] if item["id"] != parent_id}:
        return False
    return {
        item["id"]: item
        for item in previous["execution_units"]
        if item["id"] != task_id
    } == {
        item["id"]: item
        for item in current["execution_units"]
        if item["id"] != task_id
    }


def _registry_change_roots(
    previous: dict[str, Any] | None,
    current: dict[str, Any],
    task_records: dict[str, Any],
) -> set[str]:
    if isinstance(previous, dict):
        scoped = {
            unit_id
            for unit_id in task_records
            if _registry_transition_is_scoped(previous, current, unit_id)
        }
        if len(scoped) == 1:
            return scoped
    return {
        unit_id
        for unit_id, record in task_records.items()
        if record.get("outcomes")
    }


def _restorable_status(record: dict[str, Any]) -> str | None:
    previous_status = record.get("previous_status")
    checkpoint = record.get("main_review_checkpoint") or {}
    if (
        previous_status == "review_pending_wave"
        and checkpoint.get("status") == "review_pending_wave"
    ):
        return previous_status
    if (
        previous_status in {"verified", "committed", "pushed", "engineering_complete"}
        and record.get("review", {}).get("decision") == "pass"
    ):
        return previous_status
    return None


def _registry_transition_is_wave_fix_scoped(
    previous: dict[str, Any], current: dict[str, Any], wave: dict[str, Any] | None
) -> bool:
    if wave is None:
        return False
    unit_ids = set(wave.get("execution_units", []))
    parent_ids = {
        unit.get("task")
        for unit in current.get("execution_units", [])
        if unit.get("id") in unit_ids
    }
    if None in parent_ids or not parent_ids:
        return False
    ignored = {"version", "tasks", "execution_units"}
    if {
        key: value for key, value in previous.items() if key not in ignored
    } != {key: value for key, value in current.items() if key not in ignored}:
        return False
    if {
        item["id"]: item for item in previous["tasks"] if item["id"] not in parent_ids
    } != {
        item["id"]: item for item in current["tasks"] if item["id"] not in parent_ids
    }:
        return False
    return {
        item["id"]: item
        for item in previous["execution_units"]
        if item["id"] not in unit_ids
    } == {
        item["id"]: item
        for item in current["execution_units"]
        if item["id"] not in unit_ids
    }


def _previous_wave_reviews_complete(
    registry: dict[str, Any], state: dict[str, Any], wave_id: str
) -> bool:
    checkpoints = state.get("wave_checkpoints", {})
    return all(
        checkpoints.get(wave["id"], {}).get("status") == "review_pass"
        for wave in _previous_waves(registry, wave_id)
    )


def _wave_base_checkpoint_units(wave: dict[str, Any] | None) -> set[str]:
    if wave is None:
        return set()
    checkpoint = wave.get("base_checkpoint")
    if not isinstance(checkpoint, dict):
        return set()
    commit = checkpoint["commit"]
    exists = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if exists.returncode != 0 or ancestor.returncode != 0:
        raise HarnessError("历史review-pass checkpoint不是当前HEAD的有效祖先。")
    return set(checkpoint["execution_units"])


def _active_wave_base_checkpoint_units(
    registry: dict[str, Any], state: dict[str, Any] | None, wave: dict[str, Any] | None
) -> set[str]:
    """Activate historical units only after the run has actually reached that wave."""
    if wave is None or state is None:
        return set()
    previous_waves = _previous_waves(registry, wave["id"])
    if previous_waves:
        if not _previous_wave_reviews_complete(registry, state, wave["id"]):
            return set()
    elif not any(
        unit_id in state.get("tasks", {}) for unit_id in wave.get("execution_units", [])
    ) and state.get("wave_checkpoints", {}).get(wave["id"], {}).get("status") != "review_pass":
        return set()
    return _wave_base_checkpoint_units(wave)


def _historical_checkpoint_evidence_is_valid(
    registry: dict[str, Any], checkpoint: dict[str, Any]
) -> bool:
    binding = checkpoint.get("evidence_binding")
    if not isinstance(binding, dict):
        return False
    required = {
        "task",
        "review_packet_path",
        "review_packet_sha256",
        "decision_path",
        "decision_sha256",
    }
    if not required.issubset(binding):
        return False
    task_id = binding.get("task")
    if task_id not in checkpoint.get("execution_units", []):
        return False
    try:
        packet_path = (ROOT / binding["review_packet_path"]).resolve()
        decision_path = (ROOT / binding["decision_path"]).resolve()
        packet_bytes = _historical_checkpoint_evidence_bytes(packet_path)
        decision_bytes = _historical_checkpoint_evidence_bytes(decision_path)
        if (
            sha256_bytes(packet_bytes) != binding["review_packet_sha256"]
            or sha256_bytes(decision_bytes) != binding["decision_sha256"]
        ):
            return False
        packet = json.loads(packet_bytes.decode("utf-8"))
        decision = json.loads(decision_bytes.decode("utf-8"))
        commit_tree = _run_git("rev-parse", f"{checkpoint['commit']}^{{tree}}")
        commit_tree_text = commit_tree.decode("ascii").strip()
    except (
        HarnessError,
        KeyError,
        OSError,
        TypeError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ):
        return False
    allowed_kinds = set(
        registry.get("independent_review_policy", {}).get(
            "allowed_reviewer_kinds", []
        )
    )
    return bool(
        packet.get("schema") == "safehome.rc0810.review-packet.v1"
        and packet.get("task") == task_id
        and packet.get("source_tree") == commit_tree_text
        and decision.get("schema") == "safehome.rc0810.review-decision.v1"
        and decision.get("decision") == "pass"
        and decision.get("reviewer_kind") in allowed_kinds
        and decision.get("reviewer_id")
        and decision.get("review_packet_sha256")
        == binding["review_packet_sha256"]
        and decision.get("challenge_nonce") == packet.get("challenge_nonce")
        and isinstance(decision.get("findings"), list)
        and not decision["findings"]
    )


def _historical_checkpoint_evidence_bytes(path: Path) -> bytes:
    if not path.is_file():
        raise OSError(f"historical review evidence is missing: {path}")
    if not _path_within(path, ROOT):
        return path.read_bytes()
    relative = path.relative_to(ROOT).as_posix()
    clean = subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", relative],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if clean.returncode != 0:
        raise OSError(f"historical review evidence is modified: {relative}")
    return _run_git("show", f"HEAD:{relative}")


def _verification_commands_unchanged(
    previous: dict[str, Any], current: dict[str, Any], task_id: str
) -> bool:
    previous_unit = unit_map(previous).get(task_id)
    current_unit = unit_map(current).get(task_id)
    if previous_unit is None or current_unit is None:
        return False
    previous_task = task_map(previous).get(previous_unit.get("task"))
    current_task = task_map(current).get(current_unit.get("task"))
    if previous_task is None or current_task is None:
        return False
    return previous_task.get("acceptance_commands") == current_task.get(
        "acceptance_commands"
    )


def _previous_registry_snapshot(state: dict[str, Any]) -> dict[str, Any]:
    snapshot = state.get("registry_snapshot")
    if isinstance(snapshot, dict):
        return snapshot
    try:
        relative = REGISTRY_PATH.relative_to(ROOT).as_posix()
    except ValueError as exc:
        raise HarnessError("缺少上一版注册表快照，不能验证合同演进。") from exc
    raw = _run_git("show", f"HEAD:{relative}")
    checkpoint = str(state.get("last_verified_checkpoint") or "").split(":", 1)[0]
    checkpoint_record = state.get("tasks", {}).get(checkpoint, {})
    if checkpoint_record.get("review", {}).get("decision") != "pass":
        raise HarnessError("上一版注册表缺少独立通过检查点；拒绝由HEAD恢复。")
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HarnessError("上一版注册表快照无效。") from exc


def start_task(registry: dict[str, Any], task_id: str) -> dict[str, Any]:
    unit = unit_map(registry).get(task_id)
    if unit is None:
        raise HarnessError(f"未知任务：{task_id}")
    task = task_map(registry)[unit["task"]]
    with state_lock():
        state = read_state()
        if state is None:
            state = {
                "schema": STATE_SCHEMA,
                "run_id": os.environ.get("RC0810_RUN_ID", f"run-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:8]}"),
                "registry_sha256": sha256_bytes(REGISTRY_PATH.read_bytes()),
                "operator_id": os.environ.get("RC0810_OPERATOR_ID", "runner"),
                "created_at": utc_now(),
                "updated_at": utc_now(),
                "registry_snapshot": registry,
                "tasks": {},
                "evidence_chain": [],
                "last_verified_checkpoint": None,
            }
        wave = _wave_for_unit(registry, task_id)
        if (
            wave is not None
            and not _previous_wave_reviews_complete(registry, state, wave["id"])
        ):
            raise HarnessError("前一审查波次尚未review pass；拒绝跨波次启动。")
        completed = {
            key
            for key, record in state["tasks"].items()
            if record.get("status")
            in {
                "verified",
                "committed",
                "pushed",
                "engineering_complete",
                "review_pending_wave",
            }
            or (
                record.get("status") == "stale"
                and isinstance(record.get("review"), dict)
                and record["review"].get("decision") == "pass"
            )
        }
        completed.update(_wave_base_checkpoint_units(wave))
        unmet = sorted(set(unit["dependencies"]) - completed)
        if unmet:
            raise HarnessError(f"{task_id}存在未完成依赖：{unmet}")
        existing = state["tasks"].get(task_id)
        if existing:
            previous_status = existing.get("status")
            legacy_fixing_recovery = (
                previous_status == "fixing"
                and existing.get("start_snapshot", {}).get("binding")
                not in {
                    "fix_iteration_start_worktree",
                    "wave_review_packet_legacy_fix_recovery",
                }
            )
            reopen_pending = (
                previous_status == "review_pending_wave"
                and wave is not None
                and (
                    state.get("wave_checkpoints", {})
                    .get(wave["id"], {})
                    .get("review", {})
                    .get("decision")
                    == "fix_required"
                )
            )
            if previous_status == "fixing" and not legacy_fixing_recovery:
                raise HarnessError(f"{task_id}已处于Fix Loop，拒绝重置迭代基线。")
            if previous_status not in {"review_failed", "fixing", "stale"} and not reopen_pending:
                raise HarnessError(f"{task_id}已启动，拒绝重复执行。")
            if legacy_fixing_recovery:
                if wave is None:
                    raise HarnessError("旧Fix Loop缺少波次信息，拒绝猜测重开基线。")
                fix_start = _wave_review_start_snapshot(state, wave)
            else:
                fix_start = _standard_start_snapshot(registry)
                fix_start["binding"] = "fix_iteration_start_worktree"
            existing.setdefault("iteration_history", []).append(
                {
                    "status": existing["status"],
                    "outcomes": existing.get("outcomes", []),
                    "review": existing.get("review"),
                    "closed_at": utc_now(),
                }
            )
            existing["status"] = "fixing"
            existing["review_packet"] = None
            existing["review"] = None
            existing["outcomes"] = []
            existing["evidence_status"] = "pending_retest"
            if wave is not None:
                wave_state = state.get("wave_checkpoints", {}).get(wave["id"])
                if wave_state is not None:
                    wave_state["status"] = "in_progress"
                    wave_state["review_packet"] = None
                state["last_progress_checkpoint"] = f"{task_id}:fixing"
            contract_hash = _task_contract_sha256(task, unit)
            existing.setdefault("initial_task_contract_sha256", contract_hash)
            existing["start_task_contract_sha256"] = contract_hash
            existing["start_registry_sha256"] = sha256_bytes(REGISTRY_PATH.read_bytes())
            existing["iteration_started_at"] = utc_now()
            existing["start_snapshot"] = fix_start
            allowed_scope = unit.get("allowed_files", task["allowed_files"])
            for subtask_id in _unit_subtask_ids(unit, task):
                existing["subtasks"][subtask_id]["allowed_scope"] = allowed_scope
            current_registry_sha256 = sha256_bytes(REGISTRY_PATH.read_bytes())
            if current_registry_sha256 != state.get("registry_sha256"):
                previous_registry = _previous_registry_snapshot(state)
                wave_fix_scoped = (
                    wave is not None
                    and isinstance(state.get("wave_checkpoints", {}).get(wave["id"]), dict)
                    and state["wave_checkpoints"][wave["id"]]
                    .get("review", {})
                    .get("decision")
                    == "fix_required"
                    and _registry_transition_is_wave_fix_scoped(
                        previous_registry, registry, wave
                    )
                )
                if not (
                    _registry_transition_is_scoped(previous_registry, registry, task_id)
                    or wave_fix_scoped
                    or _registry_transition_is_wave_harness_upgrade(
                        previous_registry, registry
                    )
                ):
                    raise HarnessError(
                        "注册表变化超出当前执行单元；拒绝Fix Loop采用。"
                    )
                state.setdefault("registry_history", []).append(
                    state["registry_sha256"]
                )
                state["registry_sha256"] = current_registry_sha256
            state["registry_snapshot"] = registry
            state["updated_at"] = utc_now()
            write_state(state)
            return {"run_id": state["run_id"], "task": task_id, "status": "fixing"}
        current_registry_sha256 = sha256_bytes(REGISTRY_PATH.read_bytes())
        if current_registry_sha256 != state.get("registry_sha256"):
            previous_registry = _previous_registry_snapshot(state)
            if not (
                _registry_transition_is_scoped(previous_registry, registry, task_id)
                or _registry_transition_is_wave_harness_upgrade(
                    previous_registry, registry
                )
                or _registry_transition_is_declared_checkpoint_resume(
                    previous_registry, registry, wave, task_id
                )
            ):
                raise HarnessError("注册表变化超出当前新执行单元；必须先独立冻结。")
            state.setdefault("registry_history", []).append(state["registry_sha256"])
            state["registry_sha256"] = current_registry_sha256
            state["registry_snapshot"] = registry
        frozen_start = (
            _f00_start_snapshot(registry, task)
            if task_id == "RC0810-F00"
            else _standard_start_snapshot(registry)
        )
        state["tasks"][task_id] = {
            "status": "in_progress",
            "started_at": utc_now(),
            "start_snapshot": frozen_start,
            "initial_task_contract_sha256": _task_contract_sha256(task, unit),
            "start_task_contract_sha256": _task_contract_sha256(task, unit),
            "start_registry_sha256": sha256_bytes(REGISTRY_PATH.read_bytes()),
            "iteration_started_at": utc_now(),
            "active_subtasks": _unit_subtask_ids(unit, task),
            "subtasks": {
                item["id"]: _new_subtask_record(
                    item, task, unit.get("allowed_files", task["allowed_files"])
                )
                for item in task["subtasks"]
            },
        }
        if wave is not None:
            state["last_progress_checkpoint"] = f"{task_id}:in_progress"
        state["updated_at"] = utc_now()
        write_state(state)
    return {"run_id": state["run_id"], "task": task_id, "status": "in_progress"}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SafeHome RC0810可恢复执行器")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan")
    sub.add_parser("next")
    for name in ("start", "verify"):
        command = sub.add_parser(name)
        command.add_argument("task")
    review = sub.add_parser("review")
    review.add_argument("task", nargs="?")
    review.add_argument("--pending-wave", action="store_true")
    review.add_argument("--wave", choices=("A", "B", "C"))
    review.add_argument(
        "--decision", choices=("pass", "fix_required", "blocked_external")
    )
    review.add_argument("--reviewer-id")
    review.add_argument("--decision-evidence")
    sub.add_parser("resume")
    sub.add_parser("report")
    snapshot = sub.add_parser("snapshot")
    snapshot.add_argument("--inherit", action="append", default=[])
    snapshot.add_argument("--reason")
    package = sub.add_parser("package-check")
    package.add_argument("artifact")
    return parser


def main() -> int:
    try:
        args = _parser().parse_args()
        registry = load_registry()
        if args.command == "plan":
            print(
                json.dumps(
                    {
                        "schema": REGISTRY_SCHEMA,
                        "version": registry["version"],
                        "task_count": len(registry["tasks"]),
                        "subtask_count": sum(
                            len(task["subtasks"]) for task in registry["tasks"]
                        ),
                        "execution_order": topological_order(registry),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        if args.command == "next":
            print(json.dumps(next_command(registry), ensure_ascii=False, indent=2))
            return 0
        if args.command == "start":
            print(json.dumps(start_task(registry, args.task.upper()), ensure_ascii=False, indent=2))
            return 0
        if args.command == "snapshot":
            print(
                json.dumps(
                    snapshot_command(registry, args.inherit, args.reason),
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        if args.command == "verify":
            exit_code, payload = verify_task(registry, args.task.upper())
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return exit_code
        if args.command == "review":
            if args.wave:
                if args.task or args.pending_wave:
                    raise HarnessError("波次审查不能同时指定task或--pending-wave。")
                payload = review_wave(
                    registry,
                    args.wave,
                    decision=args.decision,
                    reviewer_id=args.reviewer_id,
                    decision_evidence=args.decision_evidence,
                )
            else:
                if not args.task:
                    raise HarnessError("单任务审查必须指定task。")
                payload = review_task(
                    registry,
                    args.task.upper(),
                    decision=args.decision,
                    reviewer_id=args.reviewer_id,
                    decision_evidence=args.decision_evidence,
                    pending_wave=args.pending_wave,
                )
            print(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        if args.command == "resume":
            print(json.dumps(resume_command(registry), ensure_ascii=False, indent=2))
            return 0
        if args.command == "report":
            print(json.dumps(report_command(registry), ensure_ascii=False, indent=2))
            return 0
        if args.command == "package-check":
            print(
                json.dumps(
                    package_check(registry, args.artifact),
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        raise HarnessError(f"{args.command}尚未实现。")
    except HarnessError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
