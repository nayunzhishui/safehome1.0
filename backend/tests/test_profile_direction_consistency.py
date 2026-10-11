import json
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from services import assessment_profile_service as profile_service  # noqa: E402


WORKSHEETS = {
    item["id"]: item
    for item in json.loads((PROJECT_ROOT / "content" / "assessment_worksheets.json").read_text(encoding="utf-8"))["worksheets"]
}


def _clean(text):
    return re.sub(r"^\d+\.", "", str(text or "")).strip().rstrip("。")


def _name_groups(name):
    rest = name.split("：", 1)[1]
    if rest.endswith("较低"):
        high, low = rest[:-2].split("较高，", 1) if "较高，" in rest else ("", rest[:-2])
    else:
        high, low = rest[:-2], ""
    return [item for item in high.split("、") if item], [item for item in low.split("、") if item]


def _connectable_models():
    return [model for model in profile_service._load_models() if profile_service.model_is_connectable(model)]


def test_profile_names_describe_items_in_the_direction_of_their_wording():
    checked = 0
    for model in _connectable_models():
        questions = {item["id"]: item for item in WORKSHEETS[model.get("worksheet_id") or model["scale_id"]]["questions"]}
        by_text = {}
        for feature in model["features"]:
            question = questions[feature["worksheet_question_id"]]
            for text in (feature.get("label"), question["prompt"]):
                by_text[_clean(text)] = feature
        for cluster in model["clusters"]:
            if not str(cluster.get("profile_name") or "").startswith("画像"):
                continue
            high, low = _name_groups(cluster["profile_name"])
            for items, sign in ((high, 1), (low, -1)):
                for item in items:
                    feature = by_text.get(_clean(item))
                    if feature is None or feature["feature_id"] not in (cluster.get("center_z") or {}):
                        continue
                    wording_z = cluster["center_z"][feature["feature_id"]] * (-1 if feature.get("reverse_scored") else 1)
                    assert wording_z * sign > 0, (model["standard_scale_name"], cluster["cluster_id"], item)
                    checked += 1
    assert checked > 20


def test_rsca_reverse_items_are_reversed_before_matching():
    model = next(model for model in _connectable_models() if model.get("worksheet_id") == "rsca_adolescent_resilience")
    worksheet = WORKSHEETS["rsca_adolescent_resilience"]
    reverse_ids = {item["id"] for item in worksheet["questions"] if item.get("reverse_scored")}
    assert {feature["worksheet_question_id"] for feature in model["features"] if feature.get("reverse_scored")} == reverse_ids & {
        feature["worksheet_question_id"] for feature in model["features"]
    }

    def position(forward, reverse, monkeypatch_model=model):
        answers = [
            {"question_id": item["id"], "value": reverse if item["id"] in reverse_ids else forward, "score": reverse if item["id"] in reverse_ids else forward}
            for item in worksheet["questions"]
        ]
        original = profile_service._choose_model
        profile_service._choose_model = lambda _worksheet, requested_model_id=None: monkeypatch_model
        try:
            return profile_service.build_assessment_profile_position({"answers": answers}, worksheet)
        finally:
            profile_service._choose_model = original

    higher = position(forward=4, reverse=2)
    lower = position(forward=2, reverse=4)
    assert higher["position"]["can_use_interpretation"] is True
    assert lower["position"]["can_use_interpretation"] is True
    assert higher["position"]["display_name"] == "支持联结较可用的阶段性位置"
    assert lower["position"]["display_name"] == "较多独立应对的阶段性位置"
    reversed_rows = [row for row in higher["feature_profile"] if row["reverse_scored"]]
    assert len(reversed_rows) == 12
    # An answer of 2 on a 1-5 reversed item enters the model as 4.
    assert all(row["model_input_score"] == 4.0 for row in reversed_rows)
    assert sum(row["z_score"] for row in reversed_rows) > 0
