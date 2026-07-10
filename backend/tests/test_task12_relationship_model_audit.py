import importlib.util
import json
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "analysis" / "profiling" / "audit_task12_relationship_models.py"


def _module():
    spec = importlib.util.spec_from_file_location("audit_task12_relationship_models", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def test_task12_model_audit_is_aggregate_only_and_covers_serving_consistency(tmp_path):
    module = _module()
    npz_path = tmp_path / "synthetic_item_matrices.npz"
    rng = np.random.default_rng(20260710)

    def four_groups(feature_count: int) -> np.ndarray:
        return np.vstack(
            [rng.normal(center, 0.2, (30, feature_count)) for center in (1.5, 2.5, 3.5, 4.5)]
        )

    regulatory_columns = [f"Q{index}" for index in range(1, 19)]
    micro_ysq_columns = [f"YSQ{index}" for index in range(1, 19)]
    relationship_columns = (
        [f"a{index}" for index in range(1, 6)]
        + [f"b{index}" for index in range(1, 6)]
        + [f"SN{index}" for index in range(1, 5)]
        + [f"PBC{index}" for index in range(1, 7)]
        + [f"BI{index}" for index in range(1, 7)]
        + [f"RAP{index}" for index in range(1, 6)]
    )
    np.savez_compressed(
        npz_path,
        regulatory_focus=four_groups(len(regulatory_columns)),
        regulatory_focus_columns=np.array(regulatory_columns),
        micro_ysq=four_groups(len(micro_ysq_columns)),
        micro_ysq_columns=np.array(micro_ysq_columns),
        relationship=four_groups(len(relationship_columns)),
        relationship_columns=np.array(relationship_columns),
    )

    result = module.audit_models(npz_path=npz_path, bootstrap_iterations=10)

    assert result["raw_text_included"] is False
    assert result["participant_rows_included"] is False
    assert len(result["models"]) == 3
    for model in result["models"]:
        assert model["n_cases"] == 120
        assert 0 <= model["online_euclidean_vs_gmm_agreement"] <= 1
        assert model["bootstrap_ari"]["iterations"] == 10
        assert "rows" not in json.dumps(model, ensure_ascii=False).lower()
