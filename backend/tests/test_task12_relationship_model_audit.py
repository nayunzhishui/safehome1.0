import importlib.util
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "analysis" / "profiling" / "audit_task12_relationship_models.py"


def _module():
    spec = importlib.util.spec_from_file_location("audit_task12_relationship_models", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def test_task12_model_audit_is_aggregate_only_and_covers_serving_consistency():
    module = _module()
    result = module.audit_models(bootstrap_iterations=10)

    assert result["raw_text_included"] is False
    assert result["participant_rows_included"] is False
    assert len(result["models"]) == 3
    for model in result["models"]:
        assert model["n_cases"] == 425
        assert 0 <= model["online_euclidean_vs_gmm_agreement"] <= 1
        assert model["bootstrap_ari"]["iterations"] == 10
        assert "rows" not in json.dumps(model, ensure_ascii=False).lower()
