"""Build user-facing assessment worksheets from scale drafts and catalog."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTENT_ROOT = PROJECT_ROOT / "content"

DEFAULT_BOUNDARY_NOTICE = "本内容只用于自我观察和练习参考，不构成诊断、筛查结论或人格标签。"
WORKSHEET_SCALE_ALIASES = {
    "emotion_regulation_erq": "emotion_regulation_erq_gross",
}
SCALE_WORKSHEET_ALIASES = {
    "emotion_regulation_erq_gross": "emotion_regulation_erq",
}
DEFAULT_RECOMMENDED_CARD_IDS = {
    "student": ["student_emotion_naming", "student_two_thoughts", "self_support_statement"],
    "parent": ["three_second_pause", "nonjudgmental_response", "parent_repair_question"],
    "adult": ["emotion_naming", "cognitive_flexibility", "self_support_statement"],
    "family": ["three_second_pause", "nonjudgmental_response", "parent_after_conflict_repair"],
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def option_rows(likert: list[dict]) -> list[dict]:
    return [
        {
            "label": f"{option.get('value')} {option.get('label')}",
            "value": str(option.get("value")),
            "score": option.get("value"),
        }
        for option in likert
    ]


def dimension_lookup(draft: dict) -> dict[str, dict]:
    lookup: dict[str, dict] = {}
    for dimension in draft.get("dimensions", []):
        code = dimension.get("code")
        if code:
            lookup[code] = dimension
    return lookup


def score_method_for(scale_id: str, draft: dict) -> str:
    if draft.get("dimension_score_method") in {"mean", "sum"}:
        return draft["dimension_score_method"]
    if scale_id in {"parent_reflective_functioning_prfq", "self_compassion_scs_cn"}:
        return "mean"
    if len(draft.get("dimensions", [])) > 1:
        return "sum"
    return "sum"


def build_scoring_text(draft: dict, scale: dict) -> str:
    notes = draft.get("scoring_notes", [])
    if notes:
        return "；".join(str(note).rstrip("。") for note in notes) + "。"
    return "按题项原始分保存，正式解释以人工复核后的计分规则为准。"


def recommended_card_ids_for(scale: dict, draft: dict) -> list[str]:
    explicit_ids = scale.get("recommended_card_ids") or draft.get("recommended_card_ids") or []
    if explicit_ids:
        return explicit_ids
    audience_class = scale.get("audience_class") or scale.get("audience") or draft.get("audience") or "adult"
    return DEFAULT_RECOMMENDED_CARD_IDS.get(audience_class, DEFAULT_RECOMMENDED_CARD_IDS["adult"])


def build_worksheet_from_scale(scale: dict, draft: dict, worksheet_id: str | None = None) -> dict:
    scale_id = scale["id"]
    target_id = worksheet_id or SCALE_WORKSHEET_ALIASES.get(scale_id, scale_id)
    questions = []
    for item in sorted(draft.get("items", []), key=lambda value: value.get("display_order", 0)):
        questions.append(
            {
                "id": item.get("item_code"),
                "prompt": item.get("text"),
                "type": "scale",
                "required": True,
                "dimension": item.get("dimension"),
                "reverse_scored": bool(item.get("reverse_scored", False)),
                "options": option_rows(item.get("likert") or draft.get("likert", [])),
            }
        )

    dimensions = []
    for dimension in draft.get("dimensions", []):
        code = dimension.get("code")
        if not code:
            continue
        dimension_row = {
                "code": code,
                "label": dimension.get("label", code),
                "item_ids": dimension.get("item_codes", []),
                "reverse_item_codes": dimension.get("reverse_item_codes", []),
                "description": dimension.get("note") or dimension.get("source_label") or "",
            }
        if dimension.get("calculation"):
            dimension_row["calculation"] = dimension["calculation"]
        dimensions.append(dimension_row)

    boundary_notice = scale.get("boundary_notice") or DEFAULT_BOUNDARY_NOTICE
    result_disclaimer = scale.get("result_disclaimer") or boundary_notice
    return {
        "id": target_id,
        "source_file": "；".join(draft.get("source_files", [])),
        "source_title": draft.get("display_name") or scale.get("display_name"),
        "display_title": scale.get("display_name") or draft.get("display_name"),
        "category": scale.get("category") or "成人自助",
        "audience": scale.get("audience"),
        "audience_class": scale.get("audience_class"),
        "reflex_node": scale.get("reflex_node"),
        "search_keywords": scale.get("search_keywords", []),
        "sensitive_category": scale.get("sensitive_category", "none"),
        "pages": 1,
        "instructions": (
            "请根据最近一段时间的真实情况填写。结果只用于自我观察、画像候选和练习参考，"
            "不用于诊断、筛查或评价人格。"
        ),
        "sections": [
            {
                "title": "填写说明",
                "content": draft.get("instructions")
                or "请按当前题项填写。没有标准答案，选择最接近你近期状态的一项即可。",
            }
        ],
        "questions": questions,
        "dimensions": dimensions,
        "derived_dimensions": draft.get("derived_dimensions", []),
        "dimension_score_method": score_method_for(scale["id"], draft),
        "total_score_method": draft.get("total_score_method", "sum"),
        "scoring": build_scoring_text(draft, scale),
        "recommended_card_ids": recommended_card_ids_for(scale, draft),
        "source_version": f"2026.06-{scale_id}-from-scale-draft",
        "source_type": scale.get("source_type", "authorized_resource"),
        "review_status": scale.get("review_status", "pilot_review_required"),
        "enabled_for_user": bool(scale.get("enabled", False)),
        "review_note": scale.get("notes") or "由量表草稿自动构建，正式大规模开放前仍需人工复核。",
        "boundary_notice": boundary_notice,
        "result_disclaimer": result_disclaimer,
        "profile_model_id": scale.get("profile_model_id"),
        "_meta": {
            "total_score_method": draft.get("total_score_method", "sum"),
            "derived_dimensions": draft.get("derived_dimensions", []),
        },
    }


def worksheet_index(worksheets: list[dict]) -> dict[str, int]:
    return {worksheet.get("id"): index for index, worksheet in enumerate(worksheets) if worksheet.get("id")}


def enrich_existing_worksheet(worksheet: dict, catalog_by_id: dict[str, dict]) -> dict:
    worksheet_id = worksheet.get("id")
    title = worksheet.get("display_title") or worksheet.get("source_title") or worksheet_id or "未命名测评"
    if worksheet_id == "student_profile_v1":
        worksheet.setdefault("audience", "student")
        worksheet.setdefault("audience_class", "student")
        worksheet.setdefault("reflex_node", "integrated_profile")
        worksheet.setdefault("search_keywords", ["学生画像", "压力反应", "支持资源", "测一测"])
        worksheet.setdefault("sensitive_category", "none")
        worksheet.setdefault("result_disclaimer", DEFAULT_BOUNDARY_NOTICE)
        worksheet.setdefault("boundary_notice", DEFAULT_BOUNDARY_NOTICE)
        worksheet.setdefault("source_file", "content/assessment_worksheets.json")
        worksheet.setdefault("scoring", "规则版学生支持性画像，仅用于支持性解释和练习推荐，不构成诊断或筛查。")
        worksheet.setdefault("recommended_card_ids", DEFAULT_RECOMMENDED_CARD_IDS["student"])
        worksheet.setdefault("source_version", "2026.06-student-profile-v1")
        worksheet.setdefault("source_type", "curated_content")
        return worksheet

    scale_id = WORKSHEET_SCALE_ALIASES.get(worksheet_id, worksheet_id)
    scale = catalog_by_id.get(scale_id)
    if not scale:
        worksheet.setdefault("audience_class", worksheet.get("audience") or "adult")
        worksheet.setdefault("reflex_node", "reflection")
        worksheet.setdefault("search_keywords", [title])
        worksheet.setdefault("sensitive_category", "none")
        worksheet.setdefault("result_disclaimer", worksheet.get("boundary_notice") or DEFAULT_BOUNDARY_NOTICE)
        worksheet.setdefault("boundary_notice", worksheet.get("boundary_notice") or DEFAULT_BOUNDARY_NOTICE)
        worksheet.setdefault("source_file", "content/assessment_worksheets.json")
        worksheet.setdefault("scoring", "保留的手工测评题项，正式解释以人工复核后的计分规则为准。")
        worksheet.setdefault("recommended_card_ids", DEFAULT_RECOMMENDED_CARD_IDS.get(worksheet.get("audience_class") or "adult", DEFAULT_RECOMMENDED_CARD_IDS["adult"]))
        worksheet.setdefault("source_version", f"2026.06-{worksheet_id}-manual-retained")
        worksheet.setdefault("source_type", "manual_retained")
        return worksheet

    worksheet.setdefault("audience", scale.get("audience"))
    worksheet.setdefault("audience_class", scale.get("audience_class") or scale.get("audience"))
    worksheet.setdefault("reflex_node", scale.get("reflex_node") or "reflection")
    worksheet.setdefault("search_keywords", scale.get("search_keywords", []))
    worksheet.setdefault("sensitive_category", scale.get("sensitive_category", "none"))
    worksheet.setdefault("result_disclaimer", scale.get("result_disclaimer") or DEFAULT_BOUNDARY_NOTICE)
    worksheet.setdefault("boundary_notice", scale.get("boundary_notice") or DEFAULT_BOUNDARY_NOTICE)
    worksheet.setdefault("source_file", "；".join(scale.get("source_files", [])) or "content/assessment_worksheets.json")
    worksheet.setdefault("scoring", scale.get("notes") or "保留的测评题项，正式解释以人工复核后的计分规则为准。")
    worksheet.setdefault("recommended_card_ids", scale.get("recommended_card_ids") or DEFAULT_RECOMMENDED_CARD_IDS.get(worksheet.get("audience_class") or "adult", DEFAULT_RECOMMENDED_CARD_IDS["adult"]))
    worksheet.setdefault("source_version", f"2026.06-{scale_id}-catalog-retained")
    worksheet.setdefault("source_type", scale.get("source_type") or "authorized_resource")
    return worksheet


def build_worksheets(content_dir: Path = CONTENT_ROOT) -> dict:
    worksheets_path = content_dir / "assessment_worksheets.json"
    worksheets_payload = load_json(worksheets_path)
    drafts_payload = load_json(content_dir / "scale_item_drafts.json")
    catalog_payload = load_json(content_dir / "scales_catalog.json")

    drafts = {draft.get("scale_id"): draft for draft in drafts_payload.get("drafts", []) if draft.get("scale_id")}
    catalog_by_id = {scale.get("id"): scale for scale in catalog_payload.get("scales", []) if scale.get("id")}
    worksheets = worksheets_payload.setdefault("worksheets", [])
    for worksheet in worksheets:
        enrich_existing_worksheet(worksheet, catalog_by_id)
    indexes = worksheet_index(worksheets)

    generated_ids: list[str] = []
    ordered_scale_ids = [
        scale.get("id")
        for scale in catalog_payload.get("scales", [])
        if scale.get("id") in drafts
    ]
    ordered_scale_ids.extend(scale_id for scale_id in drafts if scale_id not in ordered_scale_ids)

    for scale_id in ordered_scale_ids:
        if not scale_id:
            continue
        draft = drafts.get(scale_id)
        if not draft or not draft.get("items"):
            continue
        scale = catalog_by_id.get(scale_id) or {
            "id": scale_id,
            "display_name": draft.get("display_name") or scale_id,
            "audience": draft.get("audience") or "adult",
            "audience_class": draft.get("audience") or "adult",
            "category": "成人自助",
            "reflex_node": "reflection",
            "search_keywords": [draft.get("display_name") or scale_id],
            "sensitive_category": "none",
            "enabled": True,
            "review_status": "pilot_review_required",
        }
        worksheet_id = SCALE_WORKSHEET_ALIASES.get(scale_id, scale_id)
        worksheet = build_worksheet_from_scale(scale, draft, worksheet_id=worksheet_id)
        if worksheet_id in indexes:
            worksheets[indexes[worksheet_id]] = worksheet
        else:
            indexes[worksheet_id] = len(worksheets)
            worksheets.append(worksheet)
        generated_ids.append(scale_id)

    worksheets_payload["version"] = "2026.06-assessment-worksheets-scale-build-v1"
    worksheets_payload["updated_at"] = (
        catalog_payload.get("updated_at") or drafts_payload.get("updated_at") or worksheets_payload.get("updated_at")
    )
    worksheets_payload["boundary_notice"] = (
        "当前测一测内容来自项目内容库和已抽取量表草稿。所有结果只用于自我观察、阶段性画像候选和练习参考，"
        "不构成诊断、筛查结论或人格标签。敏感语义量表必须展示边界提示并保留人工复核。"
    )
    return {"payload": worksheets_payload, "generated_ids": generated_ids}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content-dir", default=str(CONTENT_ROOT))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    content_dir = Path(args.content_dir)
    result = build_worksheets(content_dir)
    if not args.dry_run:
        write_json(content_dir / "assessment_worksheets.json", result["payload"])
    print(json.dumps({"generated_ids": result["generated_ids"], "count": len(result["generated_ids"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
