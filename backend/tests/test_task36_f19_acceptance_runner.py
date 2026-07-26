import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from run_task36_f19_acceptance import initial_evidence, validate_manifest, verify, write_evidence


def manifest():
    return json.loads((ROOT / "config" / "task36_acceptance_manifest.json").read_text(encoding="utf-8"))


def test_f19_manifest_covers_all_tasks_layers_and_safe_commands():
    payload = manifest()
    assert validate_manifest(payload) == []
    assert set(payload["required_tasks"]) == {f"T36-F{index:02d}" for index in range(20)}
    assert {item["category"] for item in payload["commands"]} == {
        "backend",
        "shared",
        "web",
        "miniprogram",
        "security",
        "fault_recovery",
    }
    assert all(item["required"] is True for item in payload["commands"])
    assert all(item["mutates_external_state"] is False for item in payload["external_observation_commands"])


def test_f19_evidence_never_approves_external_or_production_gates():
    evidence = initial_evidence(manifest())
    assert evidence["release_approved"] is False
    assert evidence["external_gates_executed"] is False
    assert evidence["production_mutations_executed"] is False
    assert evidence["wechat_secret_mutated"] is False
    assert evidence["public_tunnel_started"] is False
    assert all(item == {"id": item["id"], "status": "evidence_pending", "executed": False, "approved": False} for item in evidence["external_gates"])


def test_f19_verify_requires_all_commands_docs_and_registry(tmp_path):
    payload = manifest()
    evidence = initial_evidence(payload)
    evidence["status"] = "passed"
    evidence["results"] = [
        {
            "id": item["id"],
            "category": item["category"],
            "required": True,
            "passed": True,
            "output_text_stored": False,
        }
        for item in payload["commands"]
    ]
    evidence["results"].extend(
        [
            {"id": "documentation_paths", "category": "documentation", "required": True, "passed": True},
            {"id": "task36_registry_f00_f18", "category": "documentation", "required": True, "passed": True},
        ]
    )
    path = tmp_path / "evidence.json"
    write_evidence(path, evidence)
    assert verify(path)["ok"] is True
    evidence["results"][0]["passed"] = False
    write_evidence(path, evidence)
    assert verify(path)["ok"] is False


def test_f19_evidence_only_stores_output_hashes_not_text():
    source = (ROOT / "scripts" / "run_task36_f19_acceptance.py").read_text(encoding="utf-8")
    assert '"stdout_sha256"' in source and '"stderr_sha256"' in source
    assert '"output_text_stored": False' in source
    assert '"stdout_text"' not in source and '"stderr_text"' not in source
