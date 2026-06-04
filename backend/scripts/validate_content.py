"""Validate content JSON files against lightweight local schema files."""

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTENT_DIR = PROJECT_ROOT / "content"
DEFAULT_SCHEMA_DIR = DEFAULT_CONTENT_DIR / "schemas"


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
