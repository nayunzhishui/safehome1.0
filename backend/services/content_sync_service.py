"""Plan, apply and restore the database copies of deployed content.

Production never initializes or syncs content at startup.  After a release that
changes `training_cards.json` or `assessment_worksheets.json`, a named admin runs:

1. plan    – read-only diff of both tables plus a full backup of the current rows;
2. apply   – the same upserts `init_db` uses, only if the plan hash still matches;
3. restore – write a previously returned backup back, if the release is rolled back.

Rows hold blank content definitions only (no answers or user records).
"""

from __future__ import annotations

import hashlib
import json

from database import (
    ASSESSMENT_WORKSHEET_COLUMNS,
    TRAINING_CARD_COLUMNS,
    _connection_provider,
    assessment_worksheet_row,
    get_connection,
    load_content_json,
    row_to_dict,
    sync_assessment_worksheets,
    sync_training_cards,
    training_card_row,
    write_audit_log,
)

TABLE_COLUMNS = {
    "training_cards": TRAINING_CARD_COLUMNS,
    "assessment_worksheets": ASSESSMENT_WORKSHEET_COLUMNS,
}
UNCOMPARED_COLUMNS = {"created_at", "updated_at"}


class ContentSyncError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def _canonical_hash(value) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _comparable(value) -> str:
    return "" if value is None else str(value)


def _content_rows() -> dict[str, dict[str, dict]]:
    cards_payload = load_content_json("training_cards.json")
    card_version = cards_payload.get("version", "unknown")
    cards = {
        card["id"]: training_card_row(card, card_version, "content")
        for card in cards_payload.get("cards", [])
        if isinstance(card, dict) and card.get("id")
    }
    worksheets = {
        worksheet["id"]: assessment_worksheet_row(worksheet, "content")
        for worksheet in load_content_json("assessment_worksheets.json").get("worksheets", [])
        if isinstance(worksheet, dict) and worksheet.get("id")
    }
    return {"training_cards": cards, "assessment_worksheets": worksheets}


def _database_rows(conn, table: str) -> dict[str, dict]:
    rows = conn.execute(f"SELECT * FROM {table}").fetchall()  # table comes from TABLE_COLUMNS only
    return {str(item["id"]): item for item in (row_to_dict(row) for row in rows) if item and item.get("id")}


def build_plan(conn) -> dict:
    content = _content_rows()
    tables: dict[str, dict] = {}
    backup: dict[str, list[dict]] = {}
    for table, columns in TABLE_COLUMNS.items():
        stored = _database_rows(conn, table)
        expected = content[table]
        create = sorted(set(expected) - set(stored))
        unknown = sorted(set(stored) - set(expected))
        update = []
        for item_id in sorted(set(expected) & set(stored)):
            fields = [
                column
                for column in columns
                if column not in UNCOMPARED_COLUMNS
                and _comparable(stored[item_id].get(column)) != _comparable(expected[item_id].get(column))
            ]
            if fields:
                update.append({"id": item_id, "fields": fields})
        tables[table] = {
            "create": create,
            "update": update,
            "unknown_in_db": unknown,
            "unchanged": len(expected) - len(create) - len(update),
        }
        backup[table] = [{column: stored[item_id].get(column) for column in columns} for item_id in sorted(stored)]
    backup_hash = _canonical_hash(backup)
    return {
        "tables": tables,
        "in_sync": all(not item["create"] and not item["update"] for item in tables.values()),
        "backup": backup,
        "backup_hash": backup_hash,
        "plan_hash": _canonical_hash({"tables": tables, "backup_hash": backup_hash}),
        "content_versions": {
            "training_cards": load_content_json("training_cards.json").get("version"),
            "assessment_worksheets": load_content_json("assessment_worksheets.json").get("version"),
        },
        "boundary": "只比较和写入空白内容定义（训练卡、量表题本），不读取答卷或用户记录。",
    }


def plan_content_sync() -> dict:
    with get_connection() as conn:
        return build_plan(conn)


def apply_content_sync(actor: dict, plan_hash: str) -> dict:
    plan_hash = str(plan_hash or "").strip()
    if not plan_hash:
        raise ContentSyncError("plan_hash_required", "请先读取同步计划，并提交计划中的 plan_hash。")
    with get_connection() as conn:
        before = build_plan(conn)
        if before["plan_hash"] != plan_hash:
            raise ContentSyncError("plan_changed", "数据库或内容在读取计划后发生了变化，请重新读取计划再确认。", 409)
        sync_training_cards(conn)
        sync_assessment_worksheets(conn)
        after = build_plan(conn)
        write_audit_log(
            conn,
            action="content_sync_applied",
            actor_id=actor["id"],
            target_type="content_sync",
            target_id="training_cards+assessment_worksheets",
            metadata={
                "plan_hash": plan_hash,
                "backup_hash": before["backup_hash"],
                "content_versions": before["content_versions"],
                "before": {table: {key: (len(value) if isinstance(value, list) else value) for key, value in item.items()} for table, item in before["tables"].items()},
                "in_sync_after": after["in_sync"],
            },
        )
        conn.commit()
    return {"applied": True, "before": before["tables"], "after": after["tables"], "in_sync": after["in_sync"]}


def _validated_backup(backup) -> dict[str, list[dict]]:
    if not isinstance(backup, dict) or set(backup) != set(TABLE_COLUMNS):
        raise ContentSyncError("invalid_backup", "备份必须同时包含 training_cards 和 assessment_worksheets。")
    validated = {}
    for table, columns in TABLE_COLUMNS.items():
        rows = backup.get(table)
        if not isinstance(rows, list) or not rows:
            raise ContentSyncError("invalid_backup", f"备份中的 {table} 为空或格式不正确。")
        cleaned = []
        for row in rows:
            if not isinstance(row, dict) or set(row) != set(columns) or not row.get("id"):
                raise ContentSyncError("invalid_backup", f"备份中的 {table} 行字段与表结构不一致。")
            if any(isinstance(value, (dict, list)) for value in row.values()):
                raise ContentSyncError("invalid_backup", f"备份中的 {table} 行字段必须是原始列值。")
            cleaned.append(row)
        validated[table] = cleaned
    return validated


def _upsert(conn, table: str, columns: tuple[str, ...], row: dict) -> None:
    column_sql = ", ".join(columns)
    placeholders = ", ".join("?" for _ in columns)
    update_columns = [column for column in columns if column != "id"]
    params = [row[column] for column in columns]
    if _connection_provider(conn) == "mysql":
        updates = ", ".join(f"{column}=VALUES({column})" for column in update_columns)
        conn.execute(f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {updates}", params)
    else:
        updates = ", ".join(f"{column}=excluded.{column}" for column in update_columns)
        conn.execute(f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders}) ON CONFLICT(id) DO UPDATE SET {updates}", params)


def restore_content_backup(actor: dict, backup, confirm: str) -> dict:
    if confirm != "restore":
        raise ContentSyncError("confirmation_required", "恢复会覆盖当前内容定义，请在请求中写明 confirm=restore。")
    validated = _validated_backup(backup)
    removed: dict[str, list[str]] = {}
    with get_connection() as conn:
        for table, rows in validated.items():
            for row in rows:
                _upsert(conn, table, TABLE_COLUMNS[table], row)
            # Rows created after the backup (for example cards added by the release) are
            # removed so the previous package's startup check sees exactly its own content.
            keep = {str(row["id"]) for row in rows}
            removed[table] = sorted(set(_database_rows(conn, table)) - keep)
            for item_id in removed[table]:
                conn.execute(f"DELETE FROM {table} WHERE id = ?", (item_id,))
        after = build_plan(conn)
        write_audit_log(
            conn,
            action="content_sync_restored",
            actor_id=actor["id"],
            target_type="content_sync",
            target_id="training_cards+assessment_worksheets",
            metadata={
                "restored_backup_hash": _canonical_hash(validated),
                "rows": {table: len(rows) for table, rows in validated.items()},
                "removed_ids": removed,
            },
        )
        conn.commit()
    return {
        "restored": True,
        "rows": {table: len(rows) for table, rows in validated.items()},
        "removed_ids": removed,
        "plan_after_restore": after["tables"],
    }
