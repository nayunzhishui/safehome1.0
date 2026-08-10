#!/usr/bin/env python3
"""Fail-closed validator for RC0810-F12 WeChat RC evidence."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "config" / "rc0810" / "wechat_external_evidence.schema.json"
CATALOG_PATH = ROOT / "config" / "rc0810" / "wechat_external_evidence_catalog.json"
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_rsa_pkcs1_v15_sha256(
    payload: bytes, signature_base64: str, modulus_hex: str, exponent: int
) -> bool:
    try:
        signature = base64.b64decode(signature_base64, validate=True)
        modulus = int(modulus_hex, 16)
    except (ValueError, TypeError):
        return False
    size = (modulus.bit_length() + 7) // 8
    if len(signature) != size or size < 64:
        return False
    encoded = pow(int.from_bytes(signature, "big"), exponent, modulus).to_bytes(size, "big")
    digest_info = bytes.fromhex("3031300d060960864801650304020105000420") + hashlib.sha256(
        payload
    ).digest()
    padding_length = size - len(digest_info) - 3
    expected = b"\x00\x01" + b"\xff" * padding_length + b"\x00" + digest_info
    return padding_length >= 8 and encoded == expected


def validate_definitions(schema: dict, catalog: dict) -> list[str]:
    errors: list[str] = []
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        errors.append(f"evidence schema is invalid: {exc.message}")
    if schema.get("$id") != "safehome.rc0810.wechat-external-evidence.v1":
        errors.append("schema id is not the frozen v1 identifier")
    if catalog.get("phase") != "definition_only":
        errors.append("catalog must remain definition_only during F12-A")
    if catalog.get("release_gate_eligible") is not False:
        errors.append("F12-A definitions cannot be release-gate eligible")
    class_ids = [item.get("id") for item in catalog.get("evidence_classes", [])]
    if class_ids != [f"E{index:02d}" for index in range(1, 11)]:
        errors.append("catalog must define E01 through E10 in order")
    for evidence_class in catalog.get("evidence_classes", []):
        if not evidence_class.get("owner") or not evidence_class.get("reviewer"):
            errors.append(f"{evidence_class.get('id')} must define owner and reviewer")
        if evidence_class.get("owner") == evidence_class.get("reviewer"):
            errors.append(f"{evidence_class.get('id')} owner and reviewer must be independent")
        if evidence_class.get("machine_actor_id") != "rc0810-evidence-validator":
            errors.append(f"{evidence_class.get('id')} must bind the registered machine actor")
        if evidence_class.get("max_state") not in {
            "human_verified",
            "platform_approved",
        }:
            errors.append(f"{evidence_class.get('id')} must freeze a maximum state")
        if not isinstance(evidence_class.get("validity_days"), int) or evidence_class.get(
            "validity_days", 0
        ) <= 0:
            errors.append(f"{evidence_class.get('id')} must define positive validity_days")
        if not evidence_class.get("invalidation_dependencies"):
            errors.append(f"{evidence_class.get('id')} must define invalidation dependencies")
    state_machine = catalog.get("state_machine", {})
    if state_machine.get("states") != [
        "machine_pass",
        "evidence_ready",
        "human_verified",
        "platform_approved",
    ]:
        errors.append("catalog state machine is not the frozen four-state sequence")
    if state_machine.get("automation_max_state") != "evidence_ready":
        errors.append("automation must not approve human or platform states")
    scenario_ids = {item.get("id") for item in catalog.get("scenarios", [])}
    if scenario_ids != {
        "health_ready_auth",
        "wechat_login",
        "phone_login",
        "message_flow",
        "foreground_background",
        "cold_start",
    }:
        errors.append("catalog must define the six frozen WeChat RC scenarios")
    for scenario in catalog.get("scenarios", []):
        if not scenario.get("steps") or any(
            not step.get("id") or not step.get("expected")
            for step in scenario.get("steps", [])
        ):
            errors.append(f"scenario {scenario.get('id')} must freeze ordered step expectations")
    matrix_platforms = {
        item.get("platform")
        for item in catalog.get("device_matrix", {}).get("required_slots", [])
    }
    if matrix_platforms != {"iOS", "Android"}:
        errors.append("device matrix must require iOS and Android real-device slots")
    if catalog.get("external_gates") != {
        "wechat_platform_operator": "pending_external",
        "device_operator": "pending_external",
    }:
        errors.append("F12-A external gates must remain pending_external")
    dependency_owners: dict[str, set[str]] = {}
    for evidence_class in catalog.get("evidence_classes", []):
        for dependency in evidence_class.get("invalidation_dependencies", []):
            dependency_owners.setdefault(dependency, set()).add(evidence_class.get("id"))
    propagation = catalog.get("invalidation_propagation", {})
    if set(propagation) != set(dependency_owners):
        errors.append("invalidation propagation keys must equal all E01-E10 dependencies")
    known_class_ids = set(class_ids)
    for dependency, owners in dependency_owners.items():
        closure = set(propagation.get(dependency, []))
        if not closure or not owners.issubset(closure) or not closure.issubset(known_class_ids):
            errors.append(f"invalidation propagation closure is invalid for {dependency}")
    attestation_contract = catalog.get("attestation_contract", {})
    if attestation_contract.get("schema") != "safehome.rc0810.external-attestation.v1":
        errors.append("catalog must freeze the external attestation contract")
    identity_policy = catalog.get("trusted_identity_policy", {})
    if (
        identity_policy.get("status") != "pending_external"
        or identity_policy.get("signature_algorithm") != "rsa_pkcs1_v1_5_sha256"
        or identity_policy.get("identities") != {}
    ):
        errors.append("F12-A trusted identity registry must remain empty and pending_external")
    return errors


def parse_timestamp(value: Any, field: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str):
        errors.append(f"{field} must be an ISO-8601 timestamp with timezone")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{field} must be an ISO-8601 timestamp with timezone")
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        errors.append(f"{field} must include timezone")
        return None
    return parsed


def require_fields(value: Any, fields: list[str], field: str, errors: list[str]) -> dict:
    if not isinstance(value, dict):
        errors.append(f"{field} must be an object")
        return {}
    for name in fields:
        if value.get(name) in (None, ""):
            errors.append(f"{field}.{name} is required")
    return value


def resolve_real_artifact(
    artifact_root: Path | None,
    relative_path: Any,
    field: str,
    errors: list[str],
) -> Path | None:
    if artifact_root is None:
        errors.append("real evidence requires --artifact-root")
        return None
    if not isinstance(relative_path, str):
        return None
    root = artifact_root.resolve()
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        errors.append(f"{field} escapes artifact root")
        return None
    if not candidate.is_file():
        errors.append(f"{field} does not exist under artifact root")
        return None
    return candidate


def transition_sha256(transition: dict[str, Any]) -> str:
    return canonical_sha256(transition)


def validate_evidence(
    evidence: dict,
    schema: dict,
    catalog: dict,
    expected_commit: str,
    expected_source_tree: str,
    expected_package_sha256: str,
    artifact_root: Path | None,
    current_dependencies: dict[str, str],
    current_dependencies_sha256: str | None,
    global_artifact_hashes: set[str],
) -> tuple[list[str], set[str]]:
    errors: list[str] = []
    invalidated_classes: set[str] = set()
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for violation in sorted(validator.iter_errors(evidence), key=lambda item: list(item.path)):
        path = ".".join(str(part) for part in violation.absolute_path) or "root"
        errors.append(f"schema violation at {path}: {violation.message}")
    required_top = [
        "schema",
        "evidence_id",
        "evidence_class",
        "status",
        "synthetic",
        "scenario_id",
        "device_slot_id",
        "test_account_role",
        "binding",
        "dependency_snapshot",
        "dependency_snapshot_source",
        "environment",
        "operator",
        "artifacts",
        "steps",
        "transitions",
        "validity",
    ]
    for field in required_top:
        if field not in evidence:
            errors.append(f"{field} is required")
    if evidence.get("schema") != "safehome.rc0810.wechat-external-evidence.v1":
        errors.append("schema must be safehome.rc0810.wechat-external-evidence.v1")
    classes = {
        item.get("id"): item for item in catalog.get("evidence_classes", [])
    }
    evidence_class = classes.get(evidence.get("evidence_class"))
    if evidence_class is None:
        errors.append("evidence_class must be one of E01 through E10")
        evidence_class = {}

    states = catalog.get("state_machine", {}).get("states", [])
    status = evidence.get("status")
    if status not in states:
        errors.append("status is not in the frozen state machine")
    synthetic = evidence.get("synthetic")
    if not isinstance(synthetic, bool):
        errors.append("synthetic must be boolean")
    if synthetic is True and status != catalog.get("state_machine", {}).get("synthetic_max_state"):
        errors.append("synthetic evidence cannot exceed machine_pass")
    if status in states and evidence_class.get("max_state") in states:
        if states.index(status) > states.index(evidence_class["max_state"]):
            errors.append("status exceeds the maximum state for this evidence class")

    scenarios = {item.get("id"): item for item in catalog.get("scenarios", [])}
    scenario = scenarios.get(evidence.get("scenario_id"))
    if scenario is None:
        errors.append("scenario_id is not defined in the frozen catalog")
        scenario = {}
    slots = {
        item.get("id"): item
        for item in catalog.get("device_matrix", {}).get("required_slots", [])
    }
    slot = slots.get(evidence.get("device_slot_id"))
    if slot is None:
        errors.append("device_slot_id is not defined in the frozen device matrix")
        slot = {}
    test_account_role = evidence.get("test_account_role")
    allowed_roles = catalog.get("account_role_policy", {}).get(
        evidence.get("scenario_id"), []
    )
    if test_account_role not in allowed_roles:
        errors.append("test_account_role is not allowed for the frozen scenario")

    binding = require_fields(
        evidence.get("binding"),
        catalog.get("binding_requirements", []),
        "binding",
        errors,
    )
    if not SHA1_RE.fullmatch(str(binding.get("commit", ""))):
        errors.append("binding.commit must be a lowercase 40-character Git object id")
    if not SHA1_RE.fullmatch(str(binding.get("source_tree", ""))):
        errors.append("binding.source_tree must be a lowercase 40-character Git tree id")
    if not SHA256_RE.fullmatch(str(binding.get("package_sha256", ""))):
        errors.append("binding.package_sha256 must be a lowercase SHA-256")
    if binding.get("commit") != expected_commit:
        errors.append("binding.commit does not match expected commit")
    if binding.get("source_tree") != expected_source_tree:
        errors.append("binding.source_tree does not match expected source tree")
    if binding.get("package_sha256") != expected_package_sha256:
        errors.append("binding.package_sha256 does not match expected package")

    environment = require_fields(
        evidence.get("environment"),
        catalog.get("environment_requirements", []),
        "environment",
        errors,
    )
    if slot and environment.get("platform") != slot.get("platform"):
        errors.append("environment.platform does not match device_slot_id")

    dependency_snapshot = evidence.get("dependency_snapshot")
    if not isinstance(dependency_snapshot, dict):
        errors.append("dependency_snapshot must be an object")
        dependency_snapshot = {}
    expected_dependency_names = set(evidence_class.get("invalidation_dependencies", []))
    if set(dependency_snapshot) != expected_dependency_names:
        errors.append("dependency_snapshot keys do not match the evidence class contract")
    dependency_source = require_fields(
        evidence.get("dependency_snapshot_source"),
        ["kind", "sha256"],
        "dependency_snapshot_source",
        errors,
    )
    if synthetic is True:
        if dependency_source.get("kind") != "synthetic_fixture":
            errors.append("synthetic evidence must use a synthetic dependency snapshot")
        if dependency_source.get("path") is not None:
            errors.append("synthetic dependency snapshot path must be null")
        if dependency_source.get("sha256") != canonical_sha256(dependency_snapshot):
            errors.append("synthetic dependency snapshot hash does not match values")
    else:
        if dependency_source.get("kind") != "rc_manifest":
            errors.append("real evidence must use an RC manifest dependency snapshot")
        if not dependency_source.get("path"):
            errors.append("real dependency snapshot source path is required")
        if current_dependencies_sha256 is None:
            errors.append("real evidence requires a current dependency snapshot file")
        elif dependency_source.get("sha256") != current_dependencies_sha256:
            errors.append("dependency snapshot source hash does not match current RC manifest")
    derived_dependencies = {
        "commit": binding.get("commit"),
        "source_tree": binding.get("source_tree"),
        "package_sha256": binding.get("package_sha256"),
        "appid_fingerprint": binding.get("appid_fingerprint"),
        "cloudbase_env_id": binding.get("cloudbase_env_id"),
        "cloudbase_service": binding.get("cloudbase_service"),
        "device_model": environment.get("device_model"),
        "os_version": environment.get("os_version"),
        "wechat_version": environment.get("wechat_version"),
    }
    for dependency in expected_dependency_names:
        expected_value = current_dependencies.get(dependency, derived_dependencies.get(dependency))
        if expected_value is None and synthetic is not True:
            errors.append(f"current dependency value is required for {dependency}")
            continue
        if dependency_snapshot.get(dependency) != expected_value:
            errors.append(f"dependency_snapshot.{dependency} is stale")
            invalidated_classes.update(
                catalog.get("invalidation_propagation", {}).get(
                    dependency, [evidence.get("evidence_class")]
                )
            )
    operator = require_fields(
        evidence.get("operator"), ["id", "role", "observed_at"], "operator", errors
    )
    operator_time = parse_timestamp(
        operator.get("observed_at"), "operator.observed_at", errors
    )
    if operator.get("role") != evidence_class.get("owner"):
        errors.append("operator.role does not match the evidence class owner")

    steps = evidence.get("steps")
    step_start_times: list[datetime] = []
    step_finish_times: list[datetime] = []
    if not isinstance(steps, list) or not steps:
        errors.append("steps must contain at least one executed step")
    else:
        for index, step in enumerate(steps):
            value = require_fields(
                step,
                ["id", "expected", "result", "started_at", "finished_at", "request_id"],
                f"steps[{index}]",
                errors,
            )
            started = parse_timestamp(value.get("started_at"), f"steps[{index}].started_at", errors)
            finished = parse_timestamp(value.get("finished_at"), f"steps[{index}].finished_at", errors)
            if started is not None:
                step_start_times.append(started)
            if finished is not None:
                step_finish_times.append(finished)
            if started is not None and finished is not None and finished < started:
                errors.append(f"steps[{index}] finishes before it starts")
            if (
                started is not None
                and index > 0
                and len(step_finish_times) >= index
                and started < step_finish_times[index - 1]
            ):
                errors.append(f"steps[{index}] starts before the previous step finishes")
        expected_steps = scenario.get("steps", [])
        if [step.get("id") for step in steps] != [step.get("id") for step in expected_steps]:
            errors.append("steps do not match the frozen scenario order")
        elif [step.get("expected") for step in steps] != [
            step.get("expected") for step in expected_steps
        ]:
            errors.append("step expectations do not match the frozen scenario")

    artifacts = evidence.get("artifacts")
    artifact_hashes: set[str] = set()
    artifact_capture_times: list[datetime] = []
    step_request_ids = {
        step.get("request_id") for step in steps if isinstance(step, dict)
    } if isinstance(steps, list) else set()
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("artifacts must contain at least one context-bound artifact")
    else:
        for index, artifact in enumerate(artifacts):
            value = require_fields(
                artifact,
                ["kind", *catalog.get("artifact_requirements", [])],
                f"artifacts[{index}]",
                errors,
            )
            digest = str(value.get("sha256", ""))
            if not SHA256_RE.fullmatch(digest):
                errors.append(f"artifacts[{index}].sha256 must be a lowercase SHA-256")
            elif digest in artifact_hashes:
                errors.append(f"artifacts[{index}].sha256 duplicates another artifact")
            elif digest in global_artifact_hashes:
                errors.append(f"artifacts[{index}].sha256 duplicates another evidence file")
            artifact_hashes.add(digest)
            global_artifact_hashes.add(digest)
            if value.get("package_sha256") != binding.get("package_sha256"):
                errors.append(f"artifacts[{index}].package_sha256 does not match binding")
            if value.get("request_id") not in step_request_ids:
                errors.append(f"artifacts[{index}].request_id does not map to an executed step")
            if value.get("account_role") != test_account_role:
                errors.append(f"artifacts[{index}].account_role does not match test_account_role")
            if synthetic is True:
                if not str(value.get("path", "")).startswith(
                    ".codex_tmp/rc0810/synthetic/"
                ):
                    errors.append(f"artifacts[{index}].path is outside the synthetic root")
            else:
                resolved = resolve_real_artifact(
                    artifact_root,
                    value.get("path"),
                    f"artifacts[{index}].path",
                    errors,
                )
                if resolved is not None and file_sha256(resolved) != digest:
                    errors.append(f"artifacts[{index}].sha256 does not match file content")
            captured = parse_timestamp(
                value.get("captured_at"), f"artifacts[{index}].captured_at", errors
            )
            if captured is not None:
                artifact_capture_times.append(captured)
            if (
                captured is not None
                and step_start_times
                and step_finish_times
                and not (min(step_start_times) <= captured <= max(step_finish_times))
            ):
                errors.append(f"artifacts[{index}].captured_at is outside the step timeline")

    transitions = evidence.get("transitions")
    expected_states = states[: states.index(status) + 1] if status in states else []
    if not isinstance(transitions, list):
        errors.append("transitions must be an array")
        transitions = []
    if [item.get("state") for item in transitions if isinstance(item, dict)] != expected_states:
        errors.append("transitions must contain every state in order without skipping")
    core = {key: value for key, value in evidence.items() if key != "transitions"}
    core_sha256 = canonical_sha256(core)
    previous_transition: dict[str, Any] | None = None
    event_times = [*step_finish_times, *artifact_capture_times]
    previous_time = max(event_times) if event_times else None
    transition_times: list[datetime] = []
    nonces: set[str] = set()
    for index, transition in enumerate(transitions):
        value = require_fields(
            transition,
            [
                "state",
                "evidence_core_sha256",
                "challenge_nonce",
                "actor_id",
                "identity_source",
                "transitioned_at",
            ],
            f"transitions[{index}]",
            errors,
        )
        if value.get("evidence_core_sha256") != core_sha256:
            errors.append(f"transitions[{index}].evidence_core_sha256 does not match evidence")
        expected_previous = (
            transition_sha256(previous_transition) if previous_transition is not None else None
        )
        if value.get("previous_transition_sha256") != expected_previous:
            errors.append(f"transitions[{index}] is not bound to the previous transition")
        nonce = value.get("challenge_nonce")
        if nonce in nonces:
            errors.append(f"transitions[{index}].challenge_nonce is reused")
        nonces.add(nonce)
        transitioned_at = parse_timestamp(
            value.get("transitioned_at"), f"transitions[{index}].transitioned_at", errors
        )
        if transitioned_at is not None and previous_time is not None and transitioned_at <= previous_time:
            errors.append(f"transitions[{index}] is not later than evidence or prior state")
        if transitioned_at is not None:
            previous_time = transitioned_at
            transition_times.append(transitioned_at)

        transition_state = value.get("state")
        if transition_state in {"machine_pass", "evidence_ready"}:
            expected_actor = evidence_class.get("machine_actor_id")
            expected_identity = "machine_registry"
        elif transition_state == "human_verified":
            expected_actor = evidence_class.get("reviewer")
            expected_identity = "reviewer_registry"
        else:
            expected_actor = evidence_class.get("platform_approver")
            expected_identity = "external_gate_registry"
        if value.get("actor_id") != expected_actor:
            errors.append(f"transitions[{index}].actor_id does not match the registered role")
        if value.get("identity_source") != expected_identity:
            errors.append(f"transitions[{index}].identity_source does not match the state")

        needs_attestation = transition_state in {"human_verified", "platform_approved"}
        if needs_attestation:
            if not value.get("attestation_path"):
                errors.append(f"transitions[{index}].attestation_path is required")
            if not SHA256_RE.fullmatch(str(value.get("attestation_sha256", ""))):
                errors.append(f"transitions[{index}].attestation_sha256 is required")
            resolved = resolve_real_artifact(
                artifact_root,
                value.get("attestation_path"),
                f"transitions[{index}].attestation_path",
                errors,
            )
            attestation_sha256 = str(value.get("attestation_sha256", ""))
            if resolved is not None and file_sha256(resolved) != attestation_sha256:
                errors.append(f"transitions[{index}].attestation_sha256 does not match file")
            if resolved is not None:
                try:
                    attestation = json.loads(resolved.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    errors.append(f"transitions[{index}] attestation is not valid JSON: {exc}")
                    attestation = {}
                contract = catalog.get("attestation_contract", {})
                for field in contract.get("required_fields", []):
                    if attestation.get(field) in (None, ""):
                        errors.append(f"transitions[{index}] attestation.{field} is required")
                expected_attestation = {
                    "schema": contract.get("schema"),
                    "state": transition_state,
                    "actor_id": value.get("actor_id"),
                    "identity_source": value.get("identity_source"),
                    "challenge_nonce": value.get("challenge_nonce"),
                    "evidence_core_sha256": value.get("evidence_core_sha256"),
                    "previous_transition_sha256": value.get("previous_transition_sha256"),
                    "issued_at": value.get("transitioned_at"),
                    "verification_method": (
                        contract.get("human_verification_method")
                        if transition_state == "human_verified"
                        else contract.get("platform_verification_method")
                    ),
                }
                for field, expected_value in expected_attestation.items():
                    if attestation.get(field) != expected_value:
                        errors.append(
                            f"transitions[{index}] attestation.{field} does not match transition"
                        )
                if attestation.get("package_sha256") != binding.get("package_sha256"):
                    errors.append(
                        f"transitions[{index}] attestation.package_sha256 does not match evidence"
                    )
                if attestation.get("appid_fingerprint") != binding.get("appid_fingerprint"):
                    errors.append(
                        f"transitions[{index}] attestation.appid_fingerprint does not match evidence"
                    )
                identity = catalog.get("trusted_identity_policy", {}).get(
                    "identities", {}
                ).get(value.get("actor_id"))
                if not isinstance(identity, dict):
                    errors.append(
                        f"transitions[{index}].actor_id is not a registered trusted identity"
                    )
                else:
                    if identity.get("identity_source") != value.get("identity_source"):
                        errors.append(f"transitions[{index}] trusted identity source mismatch")
                    if identity.get("issuer") != attestation.get("issuer"):
                        errors.append(f"transitions[{index}] attestation issuer is not trusted")
                    if transition_state not in identity.get("allowed_states", []):
                        errors.append(f"transitions[{index}] trusted identity cannot sign this state")
                    signed_payload = {
                        key: item
                        for key, item in attestation.items()
                        if key != "signature_base64"
                    }
                    try:
                        exponent = int(identity.get("exponent", 0))
                    except (TypeError, ValueError):
                        exponent = 0
                    if not verify_rsa_pkcs1_v15_sha256(
                        json.dumps(
                            signed_payload,
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        ).encode("utf-8"),
                        str(attestation.get("signature_base64", "")),
                        str(identity.get("modulus_hex", "")),
                        exponent,
                    ):
                        errors.append(f"transitions[{index}] attestation signature is invalid")
        elif value.get("attestation_path") is not None or value.get("attestation_sha256") is not None:
            errors.append(f"transitions[{index}] machine state must not self-attach approval")
        previous_transition = value

    if status in {"human_verified", "platform_approved"} and not evidence.get(
        "human_conclusion"
    ):
        errors.append("human_conclusion is required for human_verified or platform_approved")

    validity = require_fields(
        evidence.get("validity"), ["valid_from", "valid_until"], "validity", errors
    )
    valid_from = parse_timestamp(validity.get("valid_from"), "validity.valid_from", errors)
    valid_until = parse_timestamp(validity.get("valid_until"), "validity.valid_until", errors)
    if valid_from is not None and valid_until is not None and valid_until <= valid_from:
        errors.append("validity.valid_until must be after validity.valid_from")
    execution_window = [*step_start_times, *step_finish_times, *artifact_capture_times]
    if operator_time is not None and execution_window:
        if not (min(execution_window) <= operator_time <= max(execution_window)):
            errors.append("operator.observed_at is outside the execution and capture window")
    if operator_time is not None and transition_times and operator_time >= transition_times[0]:
        errors.append("operator.observed_at must be earlier than the machine transition")
    timeline = [*execution_window, *transition_times]
    if operator_time is not None:
        timeline.append(operator_time)
    if valid_from is not None and valid_until is not None:
        if any(moment < valid_from or moment > valid_until for moment in timeline):
            errors.append("evidence event or transition is outside the validity window")
    validity_days = evidence_class.get("validity_days")
    if (
        valid_from is not None
        and valid_until is not None
        and isinstance(validity_days, int)
        and (valid_until - valid_from).total_seconds() > validity_days * 86400
    ):
        errors.append("validity.valid_until exceeds catalog validity_days")
    if valid_until is not None and valid_until <= datetime.now(timezone.utc):
        errors.append("evidence has expired")
    if validity.get("invalidated_at") is not None or validity.get("invalidation_reasons"):
        errors.append("evidence has been invalidated")
    return errors, invalidated_classes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, action="append")
    parser.add_argument("--expected-commit")
    parser.add_argument("--expected-source-tree")
    parser.add_argument("--expected-package-sha256")
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--current-dependencies", type=Path)
    parser.add_argument("--require-bundle-coverage", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    errors = validate_definitions(schema, catalog)
    if args.self_check:
        for relative in [
            "scripts/run_rc0810.py",
            "scripts/verify_rc0810_f12_evidence.py",
            "backend/tests/test_rc0810_harness.py",
            "backend/tests/test_rc0810_f12.py",
        ]:
            try:
                source = (ROOT / relative).read_text(encoding="utf-8")
                compile(source, relative, "exec")
            except (OSError, SyntaxError) as exc:
                errors.append(f"Python compile failed for {relative}: {exc}")
        result = {
            "valid": not errors,
            "status": "self_check_passed" if not errors else "self_check_failed",
            "release_gate_eligible": False,
            "errors": errors,
        }
        print(json.dumps(result, ensure_ascii=False))
        return 0 if not errors else 1

    if args.evidence is not None:
        expected = [args.expected_commit, args.expected_source_tree, args.expected_package_sha256]
        evidences: list[dict[str, Any]] = []
        invalidated_classes: set[str] = set()
        global_artifact_hashes: set[str] = set()
        current_dependencies = {}
        current_dependencies_sha256: str | None = None
        if args.current_dependencies is not None:
            dependency_bytes = args.current_dependencies.read_bytes()
            current_dependencies_sha256 = hashlib.sha256(dependency_bytes).hexdigest()
            dependency_manifest = json.loads(dependency_bytes.decode("utf-8"))
            if dependency_manifest.get("schema") != "safehome.rc0810.current-dependencies.v1":
                errors.append("current dependency snapshot schema is invalid")
            if dependency_manifest.get("commit") != args.expected_commit:
                errors.append("current dependency snapshot commit does not match expected")
            if dependency_manifest.get("source_tree") != args.expected_source_tree:
                errors.append("current dependency snapshot source tree does not match expected")
            if dependency_manifest.get("package_sha256") != args.expected_package_sha256:
                errors.append("current dependency snapshot package does not match expected")
            current_dependencies = dependency_manifest.get("values", {})
            if not isinstance(current_dependencies, dict):
                errors.append("current dependency snapshot values must be an object")
                current_dependencies = {}
        if any(value is None for value in expected):
            errors.append("evidence validation requires all expected binding arguments")
        else:
            for evidence_path in args.evidence:
                try:
                    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    errors.append(f"cannot read evidence {evidence_path}: {exc}")
                    continue
                evidences.append(evidence)
                evidence_errors, propagated = validate_evidence(
                    evidence,
                    schema,
                    catalog,
                    args.expected_commit,
                    args.expected_source_tree,
                    args.expected_package_sha256,
                    args.artifact_root,
                    current_dependencies,
                    current_dependencies_sha256,
                    global_artifact_hashes,
                )
                errors.extend(evidence_errors)
                invalidated_classes.update(propagated)

        required_scenarios = {item["id"] for item in catalog.get("scenarios", [])}
        required_slots = {
            item["id"]
            for item in catalog.get("device_matrix", {}).get("required_slots", [])
        }
        e07_coverage = {
            (item.get("scenario_id"), item.get("device_slot_id"))
            for item in evidences
            if item.get("evidence_class") == "E07"
        }
        missing_device_coverage = {
            (scenario, slot)
            for scenario in required_scenarios
            for slot in required_slots
        } - e07_coverage
        requires_coverage = args.require_bundle_coverage or any(
            item.get("evidence_class") == "E07"
            and item.get("status") in {"evidence_ready", "human_verified", "platform_approved"}
            for item in evidences
        )
        if requires_coverage and missing_device_coverage:
            errors.append("E07 bundle is missing required scenario and device-slot coverage")
        if args.require_bundle_coverage:
            present_classes = {item.get("evidence_class") for item in evidences}
            required_classes = {
                item.get("id") for item in catalog.get("evidence_classes", [])
            }
            if present_classes != required_classes:
                errors.append("bundle must contain E01 through E10")

        single = evidences[0] if len(evidences) == 1 else {}
        result = {
            "valid": not errors,
            "status": (
                single.get("status", "bundle_machine_pass")
                if not errors
                else "evidence_invalid"
            ),
            "synthetic": all(item.get("synthetic") is True for item in evidences),
            "release_gate_eligible": False,
            "external_gates": catalog.get("external_gates", {}),
            "invalidated_evidence_classes": sorted(invalidated_classes),
            "current_dependency_snapshot_sha256": current_dependencies_sha256,
            "errors": errors,
        }
        print(json.dumps(result, ensure_ascii=False))
        return 0 if not errors else 1

    result = {
        "valid": not errors,
        "status": "definition_ready" if not errors else "definition_invalid",
        "release_gate_eligible": False,
        "external_gates": catalog.get("external_gates", {}),
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
