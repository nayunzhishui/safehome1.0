import hashlib
import json
import subprocess
import sys
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "content" / "rc0810_release_candidate_registry.json"
SCHEMA_PATH = ROOT / "config" / "rc0810" / "wechat_external_evidence.schema.json"
CATALOG_PATH = ROOT / "config" / "rc0810" / "wechat_external_evidence_catalog.json"
VERIFY_PATH = ROOT / "scripts" / "verify_rc0810_f12_evidence.py"
FIXTURE_START = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=1)


def _fixture_time(*, seconds: int = 0, days: int = 0) -> str:
    return (FIXTURE_START + timedelta(seconds=seconds, days=days)).isoformat()


def _transition_sha256(transition: dict) -> str:
    return hashlib.sha256(
        json.dumps(
            transition, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def _rebind_transitions(evidence: dict) -> None:
    core = {key: value for key, value in evidence.items() if key != "transitions"}
    core_sha256 = hashlib.sha256(
        json.dumps(core, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
    previous = None
    for transition in evidence["transitions"]:
        transition["evidence_core_sha256"] = core_sha256
        transition["previous_transition_sha256"] = (
            _transition_sha256(previous) if previous is not None else None
        )
        previous = transition


def _append_transition(
    evidence: dict,
    state: str,
    actor_id: str,
    identity_source: str,
    transitioned_at: str,
) -> None:
    evidence["transitions"].append(
        {
            "state": state,
            "previous_transition_sha256": None,
            "evidence_core_sha256": "0" * 64,
            "challenge_nonce": f"{len(evidence['transitions']) + 1:x}" * 32,
            "actor_id": actor_id,
            "identity_source": identity_source,
            "transitioned_at": transitioned_at,
            "attestation_path": f"attestations/{state}.json" if state in {"human_verified", "platform_approved"} else None,
            "attestation_sha256": "f" * 64 if state in {"human_verified", "platform_approved"} else None,
        }
    )
    _rebind_transitions(evidence)


def _valid_synthetic_evidence() -> dict:
    evidence = {
        "schema": "safehome.rc0810.wechat-external-evidence.v1",
        "evidence_id": "synthetic-e07-001",
        "evidence_class": "E07",
        "status": "machine_pass",
        "synthetic": True,
        "scenario_id": "cold_start",
        "device_slot_id": "ios_supported",
        "test_account_role": "parent",
        "binding": {
            "commit": "b" * 40,
            "source_tree": "c" * 40,
            "package_sha256": "a" * 64,
            "appid_fingerprint": "sha256:" + "d" * 64,
            "cloudbase_env_id": "synthetic-env",
            "cloudbase_service": "synthetic-service",
        },
        "dependency_snapshot": {
            "package_sha256": "a" * 64,
            "device_model": "synthetic-device",
            "os_version": "synthetic-os",
            "wechat_version": "synthetic-wechat",
        },
        "dependency_snapshot_source": {
            "kind": "synthetic_fixture",
            "path": None,
            "sha256": "0" * 64,
        },
        "environment": {
            "platform": "iOS",
            "base_library_version": "3.7.10",
            "devtools_version": "1.06.2504010",
            "device_model": "synthetic-device",
            "os_version": "synthetic-os",
            "wechat_version": "synthetic-wechat",
        },
        "operator": {
            "id": "synthetic-automation",
            "role": "device_operator",
            "observed_at": _fixture_time(seconds=9),
        },
        "artifacts": [
            {
                "kind": "screenshot",
                "path": ".codex_tmp/rc0810/synthetic/e07.png",
                "sha256": "e" * 64,
                "captured_at": _fixture_time(seconds=5),
                "package_sha256": "a" * 64,
                "request_id": "synthetic-request-001",
                "account_role": "parent",
            }
        ],
        "steps": [
            {
                "id": "terminate",
                "expected": "previous process is terminated",
                "result": "synthetic fixture passed",
                "started_at": _fixture_time(),
                "finished_at": _fixture_time(seconds=2),
                "request_id": "synthetic-request-001",
            },
            {
                "id": "cold_launch",
                "expected": "bound package cold launches",
                "result": "synthetic fixture passed",
                "started_at": _fixture_time(seconds=3),
                "finished_at": _fixture_time(seconds=7),
                "request_id": "synthetic-request-001",
            },
            {
                "id": "open_home",
                "expected": "initial home state is stable",
                "result": "synthetic fixture passed",
                "started_at": _fixture_time(seconds=8),
                "finished_at": _fixture_time(seconds=10),
                "request_id": "synthetic-request-001",
            },
        ],
        "human_conclusion": None,
        "validity": {
            "valid_from": _fixture_time(),
            "valid_until": _fixture_time(days=6),
            "invalidated_at": None,
            "invalidation_reasons": [],
        },
    }
    evidence["dependency_snapshot_source"]["sha256"] = hashlib.sha256(
        json.dumps(
            evidence["dependency_snapshot"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    core_sha256 = hashlib.sha256(
        json.dumps(
            evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    evidence["transitions"] = [
        {
            "state": "machine_pass",
            "previous_transition_sha256": None,
            "evidence_core_sha256": core_sha256,
            "challenge_nonce": "1" * 32,
            "actor_id": "rc0810-evidence-validator",
            "identity_source": "machine_registry",
            "transitioned_at": _fixture_time(seconds=12),
            "attestation_path": None,
            "attestation_sha256": None,
        }
    ]
    return evidence


def test_f12a_registry_freezes_definition_only_scope():
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    units = {unit["id"]: unit for unit in registry["execution_units"]}
    unit = units["RC0810-F12-A"]

    assert unit["subtasks"] == [f"F12.{index}" for index in range(1, 9)]
    assert unit["phase"] == "phase_a"
    assert len(unit["allowed_files"]) == 12
    assert unit["change_budget"]["expected_files"] == 12
    assert SCHEMA_PATH.is_file()
    assert CATALOG_PATH.is_file()
    assert VERIFY_PATH.is_file()


def test_f12a_catalog_covers_e01_to_e10_and_non_automatic_approval():
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))

    assert catalog["phase"] == "definition_only"
    assert catalog["release_gate_eligible"] is False
    assert catalog["state_machine"]["states"] == [
        "machine_pass",
        "evidence_ready",
        "human_verified",
        "platform_approved",
    ]
    assert catalog["state_machine"]["automation_max_state"] == "evidence_ready"
    assert [item["id"] for item in catalog["evidence_classes"]] == [
        f"E{index:02d}" for index in range(1, 11)
    ]
    for item in catalog["evidence_classes"]:
        assert item["owner"]
        assert item["reviewer"]
        assert item["validity_days"] > 0
        assert item["invalidation_dependencies"]

    dependency_owners = {}
    for item in catalog["evidence_classes"]:
        for dependency in item["invalidation_dependencies"]:
            dependency_owners.setdefault(dependency, set()).add(item["id"])
    assert len(dependency_owners) == 26
    assert set(catalog["invalidation_propagation"]) == set(dependency_owners)
    for dependency, owners in dependency_owners.items():
        assert owners.issubset(catalog["invalidation_propagation"][dependency])

    scenario_ids = {item["id"] for item in catalog["scenarios"]}
    assert scenario_ids == {
        "health_ready_auth",
        "wechat_login",
        "phone_login",
        "message_flow",
        "foreground_background",
        "cold_start",
    }
    assert catalog["device_matrix"]["required_dimensions"] == [
        "device_model",
        "os_version",
        "wechat_version",
        "base_library_version",
        "account_role",
        "package_sha256",
    ]
    assert {slot["platform"] for slot in catalog["device_matrix"]["required_slots"]} == {
        "iOS",
        "Android",
    }
    assert catalog["recovery_policy"]["package_change"] == "invalidate_and_retest"
    assert catalog["recovery_policy"]["device_replacement"] == "invalidate_device_evidence"


def test_f12a_schema_requires_rc_device_artifact_and_signature_context():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    assert schema["additionalProperties"] is False
    assert {"test_account_role", "dependency_snapshot_source", "transitions"}.issubset(
        schema["required"]
    )
    binding = schema["properties"]["binding"]
    assert set(binding["required"]) == {
        "commit",
        "source_tree",
        "package_sha256",
        "appid_fingerprint",
        "cloudbase_env_id",
        "cloudbase_service",
    }
    environment = schema["properties"]["environment"]
    assert set(environment["required"]) == {
        "platform",
        "base_library_version",
        "devtools_version",
        "device_model",
        "os_version",
        "wechat_version",
    }
    artifact = schema["properties"]["artifacts"]["items"]
    assert set(artifact["required"]) >= {
        "sha256",
        "captured_at",
        "package_sha256",
        "request_id",
        "account_role",
    }
    transition = schema["properties"]["transitions"]["items"]
    assert set(transition["required"]) >= {
        "state",
        "previous_transition_sha256",
        "evidence_core_sha256",
        "challenge_nonce",
        "actor_id",
        "identity_source",
        "transitioned_at",
    }


def test_f12a_definition_validator_is_no_go_without_external_evidence():
    completed = subprocess.run(
        [sys.executable, str(VERIFY_PATH)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["valid"] is True
    assert result["status"] == "definition_ready"
    assert result["release_gate_eligible"] is False
    assert result["external_gates"] == {
        "wechat_platform_operator": "pending_external",
        "device_operator": "pending_external",
    }
    assert result["errors"] == []


def test_f12a_synthetic_machine_evidence_is_valid_but_never_release_ready(tmp_path):
    evidence_path = tmp_path / "synthetic-evidence.json"
    evidence_path.write_text(
        json.dumps(_valid_synthetic_evidence(), ensure_ascii=False),
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(VERIFY_PATH),
            "--evidence",
            str(evidence_path),
            "--expected-commit",
            "b" * 40,
            "--expected-source-tree",
            "c" * 40,
            "--expected-package-sha256",
            "a" * 64,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["valid"] is True
    assert result["status"] == "machine_pass"
    assert result["synthetic"] is True
    assert result["release_gate_eligible"] is False
    assert result["errors"] == []


@pytest.mark.parametrize(
    ("case", "expected_error"),
    [
        ("missing_device", "environment.device_model is required"),
        ("package_mismatch", "does not match binding"),
        ("non_expected_package", "does not match expected package"),
        ("duplicate_artifact", "duplicates another artifact"),
        ("timeline_mismatch", "outside the step timeline"),
        ("contextless_screenshot", "request_id is required"),
        ("orphan_request_id", "does not map to an executed step"),
        ("scenario_step_drift", "step expectations do not match"),
        ("device_slot_mismatch", "does not match device_slot_id"),
        ("stale_dependency", "dependency_snapshot.device_model is stale"),
        ("excessive_validity", "exceeds catalog validity_days"),
        ("early_transition", "is not later than evidence or prior state"),
        ("future_operator", "operator.observed_at is outside"),
        ("account_role_mismatch", "does not match test_account_role"),
        ("transition_outside_validity", "outside the validity window"),
        ("automated_human_signature", "actor_id does not match the registered role"),
        ("missing_human_conclusion", "human_conclusion is required"),
        ("automated_platform_signature", "actor_id does not match the registered role"),
        ("expired", "evidence has expired"),
        ("invalidated", "evidence has been invalidated"),
        ("unexpected_approval_field", "schema violation"),
    ],
)
def test_f12a_validator_rejects_forged_or_stale_evidence(tmp_path, case, expected_error):
    evidence = deepcopy(_valid_synthetic_evidence())
    if case == "missing_device":
        evidence["environment"].pop("device_model")
    elif case == "package_mismatch":
        evidence["artifacts"][0]["package_sha256"] = "f" * 64
    elif case == "non_expected_package":
        evidence["binding"]["package_sha256"] = "f" * 64
        evidence["artifacts"][0]["package_sha256"] = "f" * 64
    elif case == "duplicate_artifact":
        evidence["artifacts"].append(deepcopy(evidence["artifacts"][0]))
    elif case == "timeline_mismatch":
        evidence["artifacts"][0]["captured_at"] = _fixture_time(seconds=3600)
    elif case == "contextless_screenshot":
        evidence["artifacts"][0].pop("request_id")
    elif case == "orphan_request_id":
        evidence["artifacts"][0]["request_id"] = "orphan-request"
    elif case == "scenario_step_drift":
        evidence["steps"][1]["expected"] = "caller supplied expectation"
    elif case == "device_slot_mismatch":
        evidence["environment"]["platform"] = "Android"
    elif case == "stale_dependency":
        evidence["dependency_snapshot"]["device_model"] = "old-device"
    elif case == "excessive_validity":
        evidence["validity"]["valid_until"] = _fixture_time(days=8)
    elif case == "early_transition":
        evidence["transitions"][0]["transitioned_at"] = _fixture_time(seconds=-1)
    elif case == "future_operator":
        evidence["operator"]["observed_at"] = "2030-08-10T10:00:09+08:00"
    elif case == "account_role_mismatch":
        evidence["artifacts"][0]["account_role"] = "arbitrary-role"
    elif case == "transition_outside_validity":
        evidence["transitions"][0]["transitioned_at"] = _fixture_time(days=8)
    elif case == "automated_human_signature":
        evidence["synthetic"] = False
        evidence["status"] = "human_verified"
        evidence["human_conclusion"] = "independent human conclusion"
        _append_transition(
            evidence,
            "evidence_ready",
            "rc0810-evidence-validator",
            "machine_registry",
            _fixture_time(seconds=13),
        )
        _append_transition(
            evidence,
            "human_verified",
            "forged-human",
            "reviewer_registry",
            _fixture_time(seconds=14),
        )
    elif case == "missing_human_conclusion":
        evidence["synthetic"] = False
        evidence["status"] = "human_verified"
        _append_transition(
            evidence,
            "evidence_ready",
            "rc0810-evidence-validator",
            "machine_registry",
            _fixture_time(seconds=13),
        )
        _append_transition(
            evidence,
            "human_verified",
            "independent_device_reviewer",
            "reviewer_registry",
            _fixture_time(seconds=14),
        )
    elif case == "automated_platform_signature":
        evidence["synthetic"] = False
        evidence["status"] = "platform_approved"
        evidence["human_conclusion"] = "independent human conclusion"
        _append_transition(
            evidence,
            "evidence_ready",
            "rc0810-evidence-validator",
            "machine_registry",
            _fixture_time(seconds=13),
        )
        _append_transition(
            evidence,
            "human_verified",
            "independent_device_reviewer",
            "reviewer_registry",
            _fixture_time(seconds=14),
        )
        _append_transition(
            evidence,
            "platform_approved",
            "forged-platform",
            "external_gate_registry",
            _fixture_time(seconds=15),
        )
    elif case == "invalidated":
        evidence["validity"]["invalidated_at"] = _fixture_time(seconds=15)
        evidence["validity"]["invalidation_reasons"] = ["package_changed"]
    elif case == "expired":
        evidence["validity"]["valid_until"] = _fixture_time(seconds=-3600)
    elif case == "unexpected_approval_field":
        evidence["automatic_platform_approval"] = True

    _rebind_transitions(evidence)

    evidence_path = tmp_path / f"{case}.json"
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            str(VERIFY_PATH),
            "--evidence",
            str(evidence_path),
            "--expected-commit",
            "b" * 40,
            "--expected-source-tree",
            "c" * 40,
            "--expected-package-sha256",
            "a" * 64,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    result = json.loads(completed.stdout)
    assert result["valid"] is False
    assert result["status"] == "evidence_invalid"
    assert result["release_gate_eligible"] is False
    assert any(expected_error in error for error in result["errors"]), result["errors"]


def test_f12a_real_artifact_is_root_bound_rehashed_and_context_mapped(tmp_path):
    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()
    artifact = artifact_root / "capture.png"
    artifact.write_bytes(b"synthetic bytes representing a real-artifact contract test")

    evidence = _valid_synthetic_evidence()
    evidence["synthetic"] = False
    evidence["artifacts"][0]["path"] = "capture.png"
    evidence["artifacts"][0]["sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
    dependency_manifest = {
        "schema": "safehome.rc0810.current-dependencies.v1",
        "commit": "b" * 40,
        "source_tree": "c" * 40,
        "package_sha256": "a" * 64,
        "values": deepcopy(evidence["dependency_snapshot"]),
    }
    dependencies_path = tmp_path / "current-dependencies.json"
    dependencies_path.write_text(json.dumps(dependency_manifest), encoding="utf-8")
    evidence["dependency_snapshot_source"] = {
        "kind": "rc_manifest",
        "path": "current-dependencies.json",
        "sha256": hashlib.sha256(dependencies_path.read_bytes()).hexdigest(),
    }
    _rebind_transitions(evidence)
    evidence_path = tmp_path / "real-machine-evidence.json"
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")

    command = [
        sys.executable,
        str(VERIFY_PATH),
        "--evidence",
        str(evidence_path),
        "--artifact-root",
        str(artifact_root),
        "--current-dependencies",
        str(dependencies_path),
        "--expected-commit",
        "b" * 40,
        "--expected-source-tree",
        "c" * 40,
        "--expected-package-sha256",
        "a" * 64,
    ]
    valid = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    assert valid.returncode == 0, valid.stdout
    assert json.loads(valid.stdout)["release_gate_eligible"] is False

    dependency_manifest["values"]["device_model"] = "changed-device"
    dependencies_path.write_text(json.dumps(dependency_manifest), encoding="utf-8")
    stale_source = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True, check=False
    )
    assert stale_source.returncode == 1
    assert any(
        "source hash does not match current RC manifest" in error
        for error in json.loads(stale_source.stdout)["errors"]
    )
    dependencies_path.write_text(
        json.dumps(
            {
                **dependency_manifest,
                "values": deepcopy(evidence["dependency_snapshot"]),
            }
        ),
        encoding="utf-8",
    )

    artifact.unlink()
    missing = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    assert missing.returncode == 1
    assert any(
        "does not exist under artifact root" in error
        for error in json.loads(missing.stdout)["errors"]
    )


def test_f12a_bundle_rejects_duplicate_artifacts_and_incomplete_device_coverage(tmp_path):
    first = _valid_synthetic_evidence()
    second = deepcopy(first)
    second["evidence_id"] = "synthetic-e07-002"
    second["artifacts"][0]["path"] = ".codex_tmp/rc0810/synthetic/e07-copy.png"
    _rebind_transitions(second)
    paths = []
    for index, evidence in enumerate((first, second), start=1):
        path = tmp_path / f"evidence-{index}.json"
        path.write_text(json.dumps(evidence), encoding="utf-8")
        paths.extend(["--evidence", str(path)])
    completed = subprocess.run(
        [
            sys.executable,
            str(VERIFY_PATH),
            *paths,
            "--require-bundle-coverage",
            "--expected-commit",
            "b" * 40,
            "--expected-source-tree",
            "c" * 40,
            "--expected-package-sha256",
            "a" * 64,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    errors = json.loads(completed.stdout)["errors"]
    assert any("duplicates another evidence file" in error for error in errors)
    assert any("missing required scenario and device-slot coverage" in error for error in errors)
    assert any("bundle must contain E01 through E10" in error for error in errors)


def test_f12a_dependency_drift_reports_recursive_invalidation_targets(tmp_path):
    evidence = _valid_synthetic_evidence()
    evidence["dependency_snapshot"]["package_sha256"] = "f" * 64
    _rebind_transitions(evidence)
    evidence_path = tmp_path / "stale-package.json"
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            str(VERIFY_PATH),
            "--evidence",
            str(evidence_path),
            "--expected-commit",
            "b" * 40,
            "--expected-source-tree",
            "c" * 40,
            "--expected-package-sha256",
            "a" * 64,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    result = json.loads(completed.stdout)
    assert result["invalidated_evidence_classes"] == ["E01", "E06", "E07", "E08", "E10"]


def test_f12a_human_transition_requires_trusted_identity_and_non_null_attestation(tmp_path):
    artifact_root = tmp_path / "artifacts"
    (artifact_root / "attestations").mkdir(parents=True)
    capture = artifact_root / "capture.png"
    capture.write_bytes(b"capture")

    evidence = _valid_synthetic_evidence()
    evidence["synthetic"] = False
    evidence["evidence_class"] = "E06"
    evidence["status"] = "human_verified"
    evidence["human_conclusion"] = "independent QA review completed"
    evidence["dependency_snapshot"] = {
        "commit": "b" * 40,
        "source_tree": "c" * 40,
        "package_sha256": "a" * 64,
        "test_plan_hash": "test-plan-v1",
    }
    evidence["operator"]["role"] = "qa_owner"
    evidence["artifacts"][0]["path"] = "capture.png"
    evidence["artifacts"][0]["sha256"] = hashlib.sha256(capture.read_bytes()).hexdigest()
    dependency_manifest = {
        "schema": "safehome.rc0810.current-dependencies.v1",
        "commit": "b" * 40,
        "source_tree": "c" * 40,
        "package_sha256": "a" * 64,
        "values": deepcopy(evidence["dependency_snapshot"]),
    }
    dependencies_path = tmp_path / "current-dependencies.json"
    dependencies_path.write_text(json.dumps(dependency_manifest), encoding="utf-8")
    evidence["dependency_snapshot_source"] = {
        "kind": "rc_manifest",
        "path": "current-dependencies.json",
        "sha256": hashlib.sha256(dependencies_path.read_bytes()).hexdigest(),
    }
    _append_transition(
        evidence,
        "evidence_ready",
        "rc0810-evidence-validator",
        "machine_registry",
        _fixture_time(seconds=13),
    )
    _append_transition(
        evidence,
        "human_verified",
        "independent_qa_reviewer",
        "reviewer_registry",
        _fixture_time(seconds=14),
    )
    human = evidence["transitions"][-1]
    attestation = {
        "schema": "safehome.rc0810.external-attestation.v1",
        "state": human["state"],
        "actor_id": human["actor_id"],
        "identity_source": human["identity_source"],
        "challenge_nonce": human["challenge_nonce"],
        "evidence_core_sha256": human["evidence_core_sha256"],
        "previous_transition_sha256": human["previous_transition_sha256"],
        "issued_at": human["transitioned_at"],
        "verification_method": "detached_human_decision",
        "source_reference": "independent-review-fixture",
        "issuer": "self-reported-untrusted-issuer",
        "review_id": "review-fixture-001",
        "package_sha256": "a" * 64,
        "appid_fingerprint": "sha256:" + "d" * 64,
        "signature_base64": "Zm9yZ2Vk",
    }
    attestation_path = artifact_root / human["attestation_path"]
    attestation_path.write_text(json.dumps(attestation), encoding="utf-8")
    human["attestation_sha256"] = hashlib.sha256(attestation_path.read_bytes()).hexdigest()

    evidence_path = tmp_path / "human-evidence.json"
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
    command = [
        sys.executable,
        str(VERIFY_PATH),
        "--evidence",
        str(evidence_path),
        "--artifact-root",
        str(artifact_root),
        "--current-dependencies",
        str(dependencies_path),
        "--expected-commit",
        "b" * 40,
        "--expected-source-tree",
        "c" * 40,
        "--expected-package-sha256",
        "a" * 64,
    ]
    forged = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    assert forged.returncode == 1
    assert any(
        "actor_id is not a registered trusted identity" in error
        for error in json.loads(forged.stdout)["errors"]
    )

    human["attestation_path"] = None
    human["attestation_sha256"] = None
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
    missing = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    missing_errors = json.loads(missing.stdout)["errors"]
    assert any("attestation_path is required" in error for error in missing_errors)
    assert any("attestation_sha256 is required" in error for error in missing_errors)
