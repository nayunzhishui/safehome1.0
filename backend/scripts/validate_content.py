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

    for filename, payload in [
        ("training_cards.json", training_cards),
        ("feedback_rules.json", feedback_rules),
        ("risk_keywords.json", risk_keywords),
        ("student_profile_rules.json", student_profile_rules),
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
