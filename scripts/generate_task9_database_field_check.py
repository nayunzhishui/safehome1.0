"""Generate Task 9 database field and relationship checklist."""

from __future__ import annotations

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
OUTPUT_PATH = PROJECT_ROOT / "docs" / "02_专项进度与验收" / "任务九数据库字段检查表_20260702.md"

CREATE_TABLE_RE = re.compile(r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*)\)", re.I | re.S)
FIELD_RE = re.compile(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s+(.+?)\s*$")
RELATION_HINTS = {
    "user_id": "users.id",
    "parent_user_id": "users.id",
    "student_user_id": "users.id",
    "goal_id": "goals.id",
    "diary_id": "emotion_diaries.id",
    "card_id": "training_cards.id",
    "worksheet_id": "assessment_worksheets.id",
    "assessment_result_id": "assessment_results.id",
    "profile_id": "student_profiles.id",
    "source_id": "source table by source_type",
    "target_id": "target table by target_type",
}


def load_schema_sql() -> list[str]:
    import sys

    sys.path.insert(0, str(BACKEND_ROOT))
    from models import SCHEMA_SQL  # pylint: disable=import-outside-toplevel

    return SCHEMA_SQL


def split_columns(body: str) -> list[str]:
    columns: list[str] = []
    current: list[str] = []
    depth = 0
    for char in body:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == "," and depth == 0:
            columns.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    if current:
        columns.append("".join(current).strip())
    return [column for column in columns if column and not column.upper().startswith(("FOREIGN KEY", "PRIMARY KEY ("))]


def parse_tables() -> list[dict]:
    tables = []
    for statement in load_schema_sql():
        match = CREATE_TABLE_RE.search(statement)
        if not match:
            continue
        table_name, body = match.groups()
        fields = []
        for column in split_columns(body):
            field_match = FIELD_RE.match(column)
            if not field_match:
                continue
            name, definition = field_match.groups()
            fields.append(
                {
                    "name": name,
                    "definition": " ".join(definition.split()),
                    "primary_key": "PRIMARY KEY" in definition.upper(),
                    "required": "NOT NULL" in definition.upper() or "PRIMARY KEY" in definition.upper(),
                    "relation": RELATION_HINTS.get(name, ""),
                }
            )
        tables.append({"name": table_name, "fields": fields})
    return tables


def render_markdown(tables: list[dict]) -> str:
    lines = [
        "# 任务九数据库字段检查表",
        "",
        "<!-- task9_database_field_check -->",
        "",
        "生成日期：2026-07-02",
        "",
        "来源：`backend/models.py` 的 `SCHEMA_SQL`。",
        "",
        "说明：本表用于任务九 T9-14/T9-15 审查。当前 schema 以服务层关联校验为主，未强制补加数据库外键，避免破坏既有 SQLite/MySQL 兼容数据和历史记录。",
        "",
        "## 汇总",
        "",
        f"- 表数量：{len(tables)}",
        f"- 字段数量：{sum(len(table['fields']) for table in tables)}",
        "",
        "## 字段明细",
        "",
    ]
    for table in tables:
        lines.extend(
            [
                f"### {table['name']}",
                "",
                "| 字段 | 定义 | 主键 | 必填 | 关联提示 |",
                "|---|---|---|---|---|",
            ]
        )
        for field in table["fields"]:
            lines.append(
                "| {name} | `{definition}` | {primary_key} | {required} | {relation} |".format(
                    name=field["name"],
                    definition=field["definition"].replace("|", "\\|"),
                    primary_key="是" if field["primary_key"] else "否",
                    required="是" if field["required"] else "否",
                    relation=field["relation"] or "",
                )
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    tables = parse_tables()
    OUTPUT_PATH.write_text(render_markdown(tables) + "\n", encoding="utf-8")
    print(OUTPUT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
