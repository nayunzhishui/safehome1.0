import importlib.util
import json
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "backend" / "scripts" / "build_task12_relationship_content.py"


def _module():
    spec = importlib.util.spec_from_file_location("build_task12_relationship_content", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def test_builds_three_relationship_scale_drafts_and_training_rules(tmp_path):
    module = _module()
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    for filename in ["scale_item_drafts.json", "scales_catalog.json", "assessment_training_map.json"]:
        shutil.copy(PROJECT_ROOT / "content" / filename, content_dir / filename)

    result = module.build_content(
        content_dir,
        PROJECT_ROOT / "outputs" / "task12_relationship_profiles" / "item_mapping_preview.csv",
    )

    assert result == {"draft_count": 3, "catalog_count": 3, "rule_count": 3}
    drafts = json.loads((content_dir / "scale_item_drafts.json").read_text(encoding="utf-8"))["drafts"]
    by_id = {item["scale_id"]: item for item in drafts}
    assert len(by_id["regulatory_focus_relationship_18"]["items"]) == 18
    assert len(by_id["micro_ysq_relationship_18"]["items"]) == 18
    relationship = by_id["relationship_initiation_intention_action"]
    assert len(relationship["items"]) == 31
    assert not {"@11", "@12"} & {item["item_code"] for item in relationship["items"]}
    assert relationship["total_score_method"] == "none"
    benefit = next(item for item in relationship["dimensions"] if item["code"] == "BENEFIT")
    assert benefit["calculation"]["type"] == "mean_of_products"

    rules = json.loads((content_dir / "assessment_training_map.json").read_text(encoding="utf-8"))["rules"]
    task12_rules = [item for item in rules if item["rule_id"].startswith("task12_")]
    assert len(task12_rules) == 3
    assert all(len(item["recommended_card_ids"]) <= 3 for item in task12_rules)
