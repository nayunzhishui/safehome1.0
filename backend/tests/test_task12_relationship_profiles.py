import importlib.util
import json
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "analysis" / "profiling" / "build_task12_relationship_profiles.py"


def _module():
    spec = importlib.util.spec_from_file_location("build_task12_relationship_profiles", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def test_method_comparison_is_reproducible_and_reports_required_metrics():
    module = _module()
    rng = np.random.default_rng(20260710)
    matrix = np.vstack([rng.normal(-1, 0.25, (60, 4)), rng.normal(1, 0.25, (60, 4))])

    first = module.compare_methods(matrix, k_values=range(2, 4), stability_seeds=(11, 23, 37))
    second = module.compare_methods(matrix, k_values=range(2, 4), stability_seeds=(11, 23, 37))

    assert first == second
    assert {row["method"] for row in first} == {"gaussian_mixture", "kmeans"}
    assert all({"k", "silhouette", "min_cluster_ratio", "stability", "readability"} <= row.keys() for row in first)
    assert all("bic" in row and "aic" in row for row in first if row["method"] == "gaussian_mixture")


def test_generated_models_do_not_contain_row_level_training_points(tmp_path):
    module = _module()
    output_dir = tmp_path / "profiles"
    report_path = tmp_path / "method-report.md"

    result = module.build_profiles(
        PROJECT_ROOT / "outputs" / "task12_relationship_profiles" / "private" / "item_matrices.npz",
        PROJECT_ROOT / "outputs" / "task12_relationship_profiles" / "item_mapping_preview.csv",
        output_dir,
        report_path,
        k_values=range(2, 3),
        stability_seeds=(11, 23),
    )

    assert result["model_count"] == 3
    for path in output_dir.glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert "training_points" not in payload
        assert payload["features"]
        assert payload["clusters"]
        assert payload["radar_support"]["dimensions"]
        assert all(cluster["suggested_assessment_questions"] for cluster in payload["clusters"])
