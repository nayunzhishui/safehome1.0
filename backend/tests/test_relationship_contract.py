import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _generator():
    path = ROOT / "backend" / "scripts" / "generate_relationship_contract_types.py"
    spec = importlib.util.spec_from_file_location("relationship_contract_generator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_relationship_contract_schema_has_required_domain_types():
    schema = json.loads((ROOT / "shared" / "contracts" / "relationship-pilot.schema.json").read_text(encoding="utf-8"))
    assert {
        "RelationshipPilotEnrollment",
        "RelationshipPilotTask",
        "RelationshipScreeningReport",
        "RelationshipGrowth",
        "HypothesisFeedback",
    } <= set(schema["$defs"])


def test_relationship_contract_generated_types_are_up_to_date():
    module = _generator()
    generated = (ROOT / "shared" / "types" / "relationship-pilot.generated.ts").read_text(encoding="utf-8")
    assert generated == module.generate()
