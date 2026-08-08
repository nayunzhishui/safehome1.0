import json
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "apps" / "miniprogram" / "utils" / "assessment-dimension-visualization.js"
PAGE = ROOT / "apps" / "miniprogram" / "pages" / "assessment-result"


def _run_helper(dimensions, worksheet):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is required for the mini-program helper unit test")
    script = """
const helper = require(process.argv[1]);
const dimensions = JSON.parse(process.argv[2]);
const worksheet = JSON.parse(process.argv[3]);
process.stdout.write(JSON.stringify(helper.buildDimensionVisualization(dimensions, worksheet)));
"""
    completed = subprocess.run(
        [node, "-e", script, str(HELPER), json.dumps(dimensions), json.dumps(worksheet)],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(completed.stdout)


def _worksheet(dimension_count=3, low=1, high=7):
    definitions = []
    questions = []
    for index in range(dimension_count):
        code = f"D{index + 1}"
        item_ids = [f"{code}Q1", f"{code}Q2"]
        definitions.append({"code": code, "label": f"维度{index + 1}", "item_ids": item_ids})
        for item_id in item_ids:
            questions.append(
                {
                    "id": item_id,
                    "dimension": code,
                    "options": [
                        {"label": str(low), "score": low},
                        {"label": str(high), "score": high},
                    ],
                }
            )
    return {"dimensions": definitions, "questions": questions}


def test_dimension_radar_normalizes_mean_scores_and_labels_midpoint_safely():
    dimensions = [
        {"key": "D1", "label": "维度一", "score": 4, "scoreMethod": "mean"},
        {"key": "D2", "label": "维度二", "score": 7, "scoreMethod": "mean"},
        {"key": "D3", "label": "维度三", "score": 1, "scoreMethod": "mean"},
    ]
    output = _run_helper(dimensions, _worksheet())

    assert output["showRadar"] is True
    assert output["referenceLabel"] == "量尺中点"
    assert [row["positionPercent"] for row in output["dimensions"]] == [50, 100, 0]
    assert "不是常模" in output["chartNote"]


def test_dimension_radar_uses_each_sum_dimension_own_range():
    worksheet = _worksheet()
    dimensions = [
        {"key": "D1", "label": "维度一", "score": 8, "scoreMethod": "sum"},
        {"key": "D2", "label": "维度二", "score": 14, "scoreMethod": "sum"},
        {"key": "D3", "label": "维度三", "score": 2, "scoreMethod": "sum"},
    ]
    output = _run_helper(dimensions, worksheet)

    assert [row["rangeText"] for row in output["dimensions"]] == [
        "本维度量尺 2–14",
        "本维度量尺 2–14",
        "本维度量尺 2–14",
    ]
    assert [row["positionPercent"] for row in output["dimensions"]] == [50, 100, 0]


def test_more_than_eight_dimensions_falls_back_to_readable_cards():
    dimensions = [
        {"key": f"D{index + 1}", "label": f"维度{index + 1}", "score": 4, "scoreMethod": "mean"}
        for index in range(9)
    ]
    output = _run_helper(dimensions, _worksheet(dimension_count=9))

    assert output["showRadar"] is False
    assert output["radarFeatures"] == []
    assert "避免标签拥挤" in output["chartNote"]


def test_result_page_keeps_text_equivalent_and_non_diagnostic_wording():
    markup = (PAGE / "index.wxml").read_text(encoding="utf-8")
    script = (PAGE / "index.js").read_text(encoding="utf-8")

    assert 'canvas-id="dimensionRadarCanvas"' in markup
    assert "scaleVisualization.dimensions" in markup
    assert "量尺中点不是常模、目标值或好坏标准" in HELPER.read_text(encoding="utf-8")
    assert 'wx.createCanvasContext("dimensionRadarCanvas", this)' in script
