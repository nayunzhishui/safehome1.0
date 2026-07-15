"""Apply the Task 19 nine-point relationship scale correction deterministically."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "content"
SCALE_ID = "regulatory_focus_relationship_18"
LIKERT = [
    {"value": 1, "label": "非常不同意"},
    {"value": 2, "label": "很不同意"},
    {"value": 3, "label": "不同意"},
    {"value": 4, "label": "比较不同意"},
    {"value": 5, "label": "不确定"},
    {"value": 6, "label": "比较同意"},
    {"value": 7, "label": "同意"},
    {"value": 8, "label": "很同意"},
    {"value": 9, "label": "非常同意"},
]
SCORING_NOTE = "数据1实测为1-5，新问卷为1-9，模型接入时必须按元数据换算"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _artifact_hash(model: dict) -> str:
    material = {key: value for key, value in model.items() if key != "artifact_hash"}
    canonical = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def apply() -> dict[str, int]:
    draft_path = CONTENT / "scale_item_drafts.json"
    draft_payload = _read(draft_path)
    draft = next(item for item in draft_payload["drafts"] if item.get("scale_id") == SCALE_ID)
    draft["likert"] = LIKERT
    for item in draft.get("items", []):
        item["likert"] = LIKERT
    draft["scoring_notes"] = [
        "PROM 与 PREV 分别取题项均值",
        "RFD=PROM-PREV 仅供研究画像定位",
        SCORING_NOTE,
    ]
    draft_payload["updated_at"] = "2026-07-15"
    _write(draft_path, draft_payload)

    worksheet_path = CONTENT / "assessment_worksheets.json"
    worksheet_payload = _read(worksheet_path)
    worksheet = next(item for item in worksheet_payload["worksheets"] if item.get("id") == SCALE_ID)
    options = [
        {"label": f"{item['value']} {item['label']}", "value": str(item["value"]), "score": item["value"]}
        for item in LIKERT
    ]
    for question in worksheet.get("questions", []):
        question["options"] = options
    worksheet["scoring"] = "PROM 与 PREV 分别取题项均值；RFD=PROM-PREV 仅供研究画像定位；当前问卷采用1-9计分，画像匹配前线性换算到既往1-5训练范围。"
    worksheet["source_version"] = "2026.07-regulatory_focus_relationship_18-nine-point"
    meta = worksheet.setdefault("_meta", {})
    meta["response_scale"] = {"min": 1, "max": 9, "points": 9}
    meta["profile_input_transform"] = {"type": "linear_range", "input_min": 1, "input_max": 9, "output_min": 1, "output_max": 5}
    worksheet_payload["updated_at"] = "2026-07-15"
    _write(worksheet_path, worksheet_payload)

    catalog_path = CONTENT / "scales_catalog.json"
    catalog_payload = _read(catalog_path)
    catalog = next(item for item in catalog_payload["scales"] if item.get("id") == SCALE_ID)
    catalog["notes"] = "任务十二本地研究试点内容；按项目负责人要求使用1-9计分；画像匹配前线性换算到既往1-5训练范围，不改写历史答卷。"
    catalog["response_scale"] = {"min": 1, "max": 9, "points": 9}
    catalog_payload["updated_at"] = "2026-07-15"
    _write(catalog_path, catalog_payload)

    model_path = CONTENT / "profiles" / "task12_regulatory_focus_relationship_18_profile_model.json"
    model = _read(model_path)
    for feature in model.get("features", []):
        transform = feature.setdefault("input_transform", {})
        transform.update({"type": "linear_range", "input_min": 1, "input_max": 9, "output_min": 1, "output_max": 5})
    model["worksheet_response_range"] = [1, 9]
    model["training_response_range"] = [1, 5]
    model["artifact_hash"] = _artifact_hash(model)
    _write(model_path, model)
    return {"draft_questions": len(draft.get("items", [])), "worksheet_questions": len(worksheet.get("questions", [])), "model_features": len(model.get("features", []))}


if __name__ == "__main__":
    print(json.dumps(apply(), ensure_ascii=False))
