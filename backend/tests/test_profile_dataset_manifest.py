import importlib.util
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _builder():
    path = ROOT / "analysis" / "profiling" / "build_dataset_manifest.py"
    spec = importlib.util.spec_from_file_location("profile_dataset_manifest", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_profile_dataset_manifest_is_deterministic_and_covers_models():
    builder = _builder()

    first = builder.build_manifest(ROOT)
    second = builder.build_manifest(ROOT)

    assert first == second
    assert first["model_count"] == len(builder.model_paths(ROOT))
    assert first["model_count"] >= 12
    assert all(item["sample_count"] for item in first["models"])
    assert all(item["feature_count"] for item in first["models"])
    assert all(re.fullmatch(r"[0-9a-f]{64}", item["source_hash"]) for item in first["models"])
    assert all(re.fullmatch(r"[0-9a-f]{64}", item["artifact_hash"]) for item in first["models"])
    assert all(re.fullmatch(r"[A-Za-z0-9_.-]+", item["model_id"]) for item in first["models"])


def test_profile_dataset_manifest_contains_no_private_paths_or_row_data():
    builder = _builder()
    manifest = builder.build_manifest(ROOT)
    text = json.dumps(manifest, ensure_ascii=False, sort_keys=True)

    assert not re.search(r"[A-Za-z]:[\\/]", text)
    assert "training_points" not in text
    assert "research_dir" not in text
    assert "source_dataset" not in text
    assert '"participant_id":' not in text
    assert '"user_id":' not in text
    assert all(item["contains_row_level_points"] is False for item in manifest["models"])
    assert manifest["privacy"]["row_level_data_included"] is False
