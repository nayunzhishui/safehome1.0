from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis.profiling.build_task12_relationship_dataset import (  # noqa: E402
    ITEM_COLUMNS,
    build_item_mapping,
    calculate_dimensions,
)


def test_build_item_mapping_covers_all_abbreviations_and_excludes_open_text_from_clustering():
    original_headers = [f"meta-{index}" for index in range(10)] + [f"原题-{index}" for index in range(69)]
    all_data_headers = [f"data-meta-{index}" for index in range(11)] + ITEM_COLUMNS

    mapping = build_item_mapping(original_headers, all_data_headers)

    assert len(mapping) == 69
    assert mapping[0]["abbreviation"] == "Q1"
    assert mapping[0]["original_prompt"] == "原题-0"
    assert mapping[-1]["abbreviation"].startswith("@12")
    assert mapping[-1]["used_for_clustering"] is False
    assert sum(1 for item in mapping if item["used_for_clustering"]) == 67


def test_calculate_dimensions_uses_task12_frozen_formulas():
    row = {name: 1.0 for name in ITEM_COLUMNS}
    for name in [f"a{i}" for i in range(1, 6)] + [f"b{i}" for i in range(1, 6)]:
        row[name] = 2.0
    for name in [f"SN{i}" for i in range(1, 5)]:
        row[name] = 3.0
    for name in [f"PBC{i}" for i in range(1, 7)]:
        row[name] = 4.0
    for name in [f"BI{i}" for i in range(1, 7)]:
        row[name] = 5.0
    for name in [f"RAP{i}" for i in range(1, 6)]:
        row[name] = 2.0

    dimensions = calculate_dimensions(pd.DataFrame([row])).iloc[0]

    assert dimensions["PROM"] == 1.0
    assert dimensions["PREV"] == 1.0
    assert dimensions["RFD"] == 0.0
    assert dimensions["EMS_M"] == 1.0
    assert dimensions["EMS_SUM"] == 18.0
    assert dimensions["REL_SCHEMA"] == 1.0
    assert dimensions["BENEFIT"] == 4.0
    assert dimensions["REJ_THREAT"] == 4.0
    assert dimensions["AUTH_THREAT"] == 4.0
    assert dimensions["AUTH_PROTECT"] == 3.0
    assert dimensions["THREAT"] == 4.0
    assert dimensions["SN"] == 3.0
    assert dimensions["PBC"] == 4.0
    assert dimensions["BI"] == 5.0
    assert dimensions["RAP"] == 2.0
