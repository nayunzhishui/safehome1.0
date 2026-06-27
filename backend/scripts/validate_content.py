"""Validate content JSON files against lightweight local schema files."""

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTENT_DIR = PROJECT_ROOT / "content"
DEFAULT_SCHEMA_DIR = DEFAULT_CONTENT_DIR / "schemas"

FORBIDDEN_TERMS = [
    "人格障碍",
    "潜意识说明",
    "治疗保证",
    "保证改善",
    "立即治愈",
    "孩子异常",
    "你有病",
    "高危患者",
]

BOUNDARY_TERMS = ["不构成诊断", "不构成临床诊断", "不替代心理咨询", "不替代危机干预"]
HIGH_RISK_BLOCK_TERMS = ["高风险", "危机", "安全", "现实支持"]
REVIEW_STATUSES = {"draft", "pending_review", "reviewed", "trial_enabled", "enabled", "disabled"}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def is_empty(value) -> bool:
    return value is None or value == "" or value == []


def validate_required_fields(payload: dict, fields: list[str], label: str) -> list[str]:
    errors = []
    for field in fields:
        if field not in payload or is_empty(payload.get(field)):
            errors.append(f"{label}.{field} 缺失或为空")
    return errors


def validate_file(content_dir: Path, schema_path: Path) -> list[str]:
    schema = load_json(schema_path)
    content_file = schema.get("file")
    if not content_file:
        return [f"{schema_path.name}.file 缺失"]

    content_path = content_dir / content_file
    if not content_path.exists():
        return [f"{content_file} 文件不存在"]

    try:
        payload = load_json(content_path)
    except json.JSONDecodeError as exc:
        return [f"{content_file} JSON 解析失败：{exc}"]

    if not isinstance(payload, dict):
        return [f"{content_file} 根节点必须是 object"]

    errors = validate_required_fields(payload, schema.get("root_required", []), content_file)
    for list_schema in schema.get("lists", []):
        field = list_schema.get("field")
        items = payload.get(field)
        if not isinstance(items, list):
            errors.append(f"{content_file}.{field} 必须是数组")
            continue
        if not items:
            errors.append(f"{content_file}.{field} 不能为空")
            continue
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"{content_file}.{field}[{index}] 必须是 object")
                continue
            item_id = item.get("id", index)
            errors.extend(
                validate_required_fields(
                    item,
                    list_schema.get("item_required", []),
                    f"{content_file}.{field}[{item_id}]",
                )
            )
            for nested_field, minimum in list_schema.get("item_list_min_lengths", {}).items():
                value = item.get(nested_field)
                if not isinstance(value, list):
                    errors.append(f"{content_file}.{field}[{item_id}].{nested_field} 必须是数组")
                elif len(value) < int(minimum):
                    errors.append(f"{content_file}.{field}[{item_id}].{nested_field} 至少需要 {minimum} 项")
        seen_ids = set()
        for item in items:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            item_id = item["id"]
            if item_id in seen_ids:
                errors.append(f"{content_file}.{field}[{item_id}].id 重复")
            seen_ids.add(item_id)
    return errors


def iter_strings(value, path: str = ""):
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from iter_strings(item, f"{path}[{index}]")
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from iter_strings(item, f"{path}.{key}" if path else str(key))


def validate_forbidden_terms(filename: str, payload: dict) -> list[str]:
    errors = []
    for path, text in iter_strings(payload):
        for term in FORBIDDEN_TERMS:
            if term in text:
                errors.append(f"{filename}.{path} 含禁用语：{term}")
    return errors


def load_content_or_error(content_dir: Path, filename: str) -> tuple[dict | None, list[str]]:
    path = content_dir / filename
    if not path.exists():
        return None, [f"{filename} 文件不存在"]
    try:
        return load_json(path), []
    except json.JSONDecodeError as exc:
        return None, [f"{filename} JSON 解析失败：{exc}"]


def validate_cross_content_rules(content_dir: Path) -> list[str]:
    errors: list[str] = []
    training_cards, load_errors = load_content_or_error(content_dir, "training_cards.json")
    errors.extend(load_errors)
    feedback_rules, load_errors = load_content_or_error(content_dir, "feedback_rules.json")
    errors.extend(load_errors)
    risk_keywords, load_errors = load_content_or_error(content_dir, "risk_keywords.json")
    errors.extend(load_errors)
    student_profile_rules, load_errors = load_content_or_error(content_dir, "student_profile_rules.json")
    errors.extend(load_errors)
    scales_catalog, load_errors = load_content_or_error(content_dir, "scales_catalog.json")
    errors.extend(load_errors)
    scale_item_drafts, load_errors = load_content_or_error(content_dir, "scale_item_drafts.json")
    errors.extend(load_errors)
    assessment_training_map, load_errors = load_content_or_error(content_dir, "assessment_training_map.json")
    errors.extend(load_errors)
    diary_training_map, load_errors = load_content_or_error(content_dir, "diary_training_map.json")
    errors.extend(load_errors)

    for filename, payload in [
        ("training_cards.json", training_cards),
        ("feedback_rules.json", feedback_rules),
        ("risk_keywords.json", risk_keywords),
        ("student_profile_rules.json", student_profile_rules),
        ("scales_catalog.json", scales_catalog),
        ("scale_item_drafts.json", scale_item_drafts),
        ("assessment_training_map.json", assessment_training_map),
        ("diary_training_map.json", diary_training_map),
    ]:
        if payload:
            errors.extend(validate_forbidden_terms(filename, payload))

    if not training_cards or not feedback_rules or not risk_keywords:
        return errors

    card_ids = {card.get("id") for card in training_cards.get("cards", []) if isinstance(card, dict)}
    for card in training_cards.get("cards", []):
        if not isinstance(card, dict):
            continue
        card_id = card.get("id", "unknown")
        unsuitable_text = " ".join(str(item) for item in card.get("not_suitable_for", []))
        if not any(term in unsuitable_text for term in HIGH_RISK_BLOCK_TERMS):
            errors.append(f"training_cards.json.cards[{card_id}].not_suitable_for 缺少高风险/危机/安全/现实支持边界")

    for rule in feedback_rules.get("rules", []):
        if not isinstance(rule, dict):
            continue
        rule_id = rule.get("id", "unknown")
        for card_id in rule.get("recommended_card_ids", []):
            if card_id not in card_ids:
                errors.append(f"feedback_rules.json.rules[{rule_id}].recommended_card_ids 包含不存在的训练卡：{card_id}")
        if rule.get("risk_level") == "high" and rule.get("recommended_card_ids"):
            errors.append(f"feedback_rules.json.rules[{rule_id}] high 风险规则不得推荐普通训练卡")

    if assessment_training_map:
        errors.extend(
            validate_training_map_rules(
                "assessment_training_map.json",
                assessment_training_map,
                card_ids,
                expected_source_type="assessment",
                require_long_term=True,
            )
        )

    if diary_training_map:
        errors.extend(
            validate_training_map_rules(
                "diary_training_map.json",
                diary_training_map,
                card_ids,
                expected_source_type="diary",
                require_empty_long_term=True,
            )
        )

    for rule in risk_keywords.get("handling_rules", []):
        if not isinstance(rule, dict):
            continue
        if rule.get("risk_level") == "high" and rule.get("allow_recommended_training_cards") is not False:
            errors.append("risk_keywords.json.handling_rules[high].allow_recommended_training_cards 必须为 false")

    feedback_boundary = feedback_rules.get("safety_notes") or feedback_rules.get("boundary_notice") or []
    if not isinstance(feedback_boundary, list):
        feedback_boundary = [str(feedback_boundary)]
    boundary_sources = {
        "feedback_rules.json": " ".join(str(item) for item in feedback_boundary),
        "risk_keywords.json": " ".join(str(item) for item in risk_keywords.get("safety_notes", [])),
    }
    if student_profile_rules:
        boundary_sources["student_profile_rules.json"] = " ".join(str(item) for item in student_profile_rules.get("safety_notes", []))
    for filename, text in boundary_sources.items():
        if not any(term in text for term in BOUNDARY_TERMS):
            errors.append(f"{filename} 风险边界文案需包含“不构成诊断”或“不替代心理咨询/危机干预”的同义表达")

    return errors


def validate_training_map_rules(
    filename: str,
    payload: dict,
    card_ids: set[str],
    *,
    expected_source_type: str,
    require_long_term: bool = False,
    require_empty_long_term: bool = False,
) -> list[str]:
    errors: list[str] = []
    for rule in payload.get("rules", []):
        if not isinstance(rule, dict):
            continue
        rule_id = rule.get("rule_id", "unknown")
        recommended_card_ids = rule.get("recommended_card_ids", [])
        condition = rule.get("trigger_condition", {})
        risk_condition = str(condition.get("risk_level", "")).lower() if isinstance(condition, dict) else ""

        if len(recommended_card_ids) > 3:
            errors.append(f"{filename}.rules[{rule_id}].recommended_card_ids 不得超过 3 张训练卡")
        for card_id in recommended_card_ids:
            if card_id not in card_ids:
                errors.append(f"{filename}.rules[{rule_id}].recommended_card_ids 包含不存在的训练卡：{card_id}")
        for role in rule.get("card_roles", []):
            if not isinstance(role, dict):
                errors.append(f"{filename}.rules[{rule_id}].card_roles 必须是 object 数组")
                continue
            role_card_id = role.get("card_id")
            if role_card_id and role_card_id not in recommended_card_ids:
                errors.append(f"{filename}.rules[{rule_id}].card_roles 包含未推荐的训练卡：{role_card_id}")
        if rule.get("source_type") != expected_source_type:
            errors.append(f"{filename}.rules[{rule_id}].source_type 必须为 {expected_source_type}")
        if rule.get("review_status") not in REVIEW_STATUSES:
            errors.append(f"{filename}.rules[{rule_id}].review_status 不在允许枚举中")
        if "high" in risk_condition and recommended_card_ids:
            errors.append(f"{filename}.rules[{rule_id}] high 风险条件不得推荐普通训练卡")
        if not rule.get("reason"):
            errors.append(f"{filename}.rules[{rule_id}].reason 缺失")
        if not rule.get("today_suggestion"):
            errors.append(f"{filename}.rules[{rule_id}].today_suggestion 缺失")
        if not any(term in str(rule.get("not_suitable_when", "")) for term in HIGH_RISK_BLOCK_TERMS):
            errors.append(f"{filename}.rules[{rule_id}].not_suitable_when 缺少高风险/危机/安全/现实支持边界")
        if not any(
            term in str(rule.get("boundary_notice", ""))
            for term in ["不构成诊断", "不构成医学判断", "不构成治疗建议", "不构成治疗方案", "不替代"]
        ):
            errors.append(f"{filename}.rules[{rule_id}].boundary_notice 需包含非诊断或非治疗边界")
        if require_long_term and not rule.get("long_term_suggestion"):
            errors.append(f"{filename}.rules[{rule_id}].long_term_suggestion 缺失，测评推荐需要长期方向")
        if require_empty_long_term and rule.get("long_term_suggestion"):
            errors.append(f"{filename}.rules[{rule_id}].long_term_suggestion 应留空，情绪日记只生成今日建议")
    return errors


def validate_content(content_dir: Path = DEFAULT_CONTENT_DIR, schema_dir: Path = DEFAULT_SCHEMA_DIR) -> list[str]:
    if not schema_dir.exists():
        return [f"schema 目录不存在：{schema_dir}"]

    errors: list[str] = []
    schema_paths = sorted(schema_dir.glob("*.schema.json"))
    if not schema_paths:
        return [f"schema 目录为空：{schema_dir}"]

    for schema_path in schema_paths:
        errors.extend(validate_file(content_dir, schema_path))
    errors.extend(validate_cross_content_rules(content_dir))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SafeHome content JSON files.")
    parser.add_argument("--content-dir", type=Path, default=DEFAULT_CONTENT_DIR)
    parser.add_argument("--schema-dir", type=Path, default=DEFAULT_SCHEMA_DIR)
    args = parser.parse_args()

    errors = validate_content(args.content_dir, args.schema_dir)
    if errors:
        print("内容校验失败：", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("内容校验通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
