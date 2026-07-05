"""Suggest and write profile-cluster to training-card mappings.

This script is deterministic and conservative: it does not infer diagnoses. It
only maps aggregate profile clusters to existing support practice cards so a
human reviewer can accept or revise the suggestions.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROFILES_DIR = ROOT / "content" / "profiles"
CARDS_PATH = ROOT / "content" / "training_cards.json"
OUTPUT_PATH = ROOT / "docs" / "10Claude协作" / "画像簇训练卡映射建议.md"


CARD_MAP = {
    "parent_reflective_functioning_prfq": [
        "prfq_pm_awareness",
        "prfq_cm_tolerance",
        "prfq_ic_curiosity",
    ],
    "emotion_regulation_erq": [
        "erq_reappraisal_parent",
        "erq_suppression_release",
        "parent_body_grounding",
    ],
    "self_compassion_scs_cn": [
        "scs_self_kindness",
        "scs_common_humanity",
        "scs_mindful_moment",
    ],
    "rsca_adolescent_resilience": [
        "rsca_emotion_regulation",
        "rsca_positive_cognition",
        "exam_micro_start",
    ],
    "emotional_resilience_11": [
        "rsca_emotion_regulation",
        "rsca_positive_cognition",
        "body_scan_before_study",
    ],
}

DEFAULT_STUDENT_CARDS = ["auto_thought_rewrite", "exam_micro_start", "body_scan_before_study"]
DEFAULT_PARENT_CARDS = ["validation_before_advice", "one_open_question", "parent_body_grounding"]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def available_card_ids() -> set[str]:
    return {card["id"] for card in load_json(CARDS_PATH).get("cards", [])}


def choose_cards(model: dict, cluster: dict, card_ids: set[str]) -> tuple[list[str], str]:
    worksheet_id = model.get("worksheet_id") or model.get("scale_id") or ""
    candidates = list(CARD_MAP.get(worksheet_id, []))
    if not candidates:
        name_blob = " ".join(
            str(value)
            for value in [
                model.get("standard_scale_name"),
                model.get("model_id"),
                model.get("group_id"),
                cluster.get("profile_name"),
                cluster.get("display_name"),
            ]
            if value
        ).lower()
        candidates = DEFAULT_PARENT_CARDS if "parent" in name_blob or "父母" in name_blob or "家长" in name_blob else DEFAULT_STUDENT_CARDS

    center_z = cluster.get("center_z") or {}
    if isinstance(center_z, dict) and center_z:
        low_features = sorted(center_z, key=lambda key: float(center_z.get(key) or 0))[:3]
    else:
        low_features = list((cluster.get("mean_scores") or {}).keys())[:3]

    selected = [card_id for card_id in candidates if card_id in card_ids][:2]
    if len(selected) < 2:
        for card_id in DEFAULT_STUDENT_CARDS + DEFAULT_PARENT_CARDS:
            if card_id in card_ids and card_id not in selected:
                selected.append(card_id)
            if len(selected) >= 2:
                break
    reason = f"根据该簇相对偏低或需支持的题项线索（{', '.join(low_features[:3]) or '模型轮廓'}）生成，供人工审核。"
    return selected[:2], reason


def main() -> None:
    card_ids = available_card_ids()
    lines = [
        "# 画像簇训练卡映射建议",
        "",
        "生成说明：本文件由 `analysis/profiling/suggest_cluster_card_map.py` 生成。建议只用于人工审核训练卡映射，不构成诊断、筛查或治疗方案。",
        "",
    ]
    updated_files = 0
    for path in sorted(PROFILES_DIR.glob("*.json")):
        model = load_json(path)
        clusters = model.get("clusters", [])
        if not isinstance(clusters, list):
            continue
        lines.append(f"## {model.get('standard_scale_name') or model.get('worksheet_id') or path.stem}")
        lines.append("")
        changed = False
        for cluster in clusters:
            if not isinstance(cluster, dict):
                continue
            cards, reason = choose_cards(model, cluster, card_ids)
            cluster["recommended_card_ids"] = cards
            cluster["card_reason"] = reason
            changed = True
            display_name = cluster.get("display_name") or cluster.get("profile_name") or cluster.get("cluster_id")
            lines.append(f"- 簇 {cluster.get('cluster_id')}（{display_name}）：`{', '.join(cards)}`")
            lines.append(f"  - 建议理由：{reason}")
        lines.append("")
        if changed:
            write_json(path, model)
            updated_files += 1
    OUTPUT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"updated_profile_files={updated_files}")
    print(f"review_doc={OUTPUT_PATH}")


if __name__ == "__main__":
    main()
