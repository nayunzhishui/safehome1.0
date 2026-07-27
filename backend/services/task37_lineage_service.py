"""Metadata-only lineage and privacy lifecycle module for Task 37."""

from __future__ import annotations

import hashlib
import hmac
from collections import deque
from typing import Any

from config import Config
from database import get_connection, json_dumps, json_loads, new_id, now_iso, row_to_dict


class LineageError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _subject_hash(subject_ref: str) -> str:
    secret = str(Config.PRIVACY_TOMBSTONE_SECRET).encode("utf-8")
    return hmac.new(secret, subject_ref.encode("utf-8"), hashlib.sha256).hexdigest()


def register_dataset(metadata: dict[str, Any]) -> dict[str, Any]:
    forbidden = {"raw_text", "model_input", "phone", "email", "wechat_openid"}
    if forbidden & set(metadata):
        raise LineageError("raw_sensitive_data_forbidden", "数据集注册表只允许元数据，不得写入原始高敏内容")
    required = {
        "id",
        "dataset_key",
        "version",
        "data_class",
        "storage_layer",
        "source_kind",
        "rights_status",
        "purpose",
    }
    missing = [field for field in required if not metadata.get(field)]
    if missing:
        raise LineageError("required_field_missing", f"缺少字段：{','.join(sorted(missing))}")
    allowed = required | {"retention_until", "metadata"}
    unknown = set(metadata) - allowed
    if unknown:
        raise LineageError("unknown_fields", f"未知字段：{','.join(sorted(unknown))}")
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO computation_datasets
            (id, dataset_key, version, data_class, storage_layer, source_kind, rights_status,
             purpose, retention_until, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                metadata["id"],
                metadata["dataset_key"],
                metadata["version"],
                metadata["data_class"],
                metadata["storage_layer"],
                metadata["source_kind"],
                metadata["rights_status"],
                metadata["purpose"],
                metadata.get("retention_until"),
                json_dumps(metadata.get("metadata") or {}),
                timestamp,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM computation_datasets WHERE id = ?", (metadata["id"],)).fetchone()
    item = row_to_dict(row)
    item["metadata"] = json_loads(item.pop("metadata_json"), {})
    item["raw_text_stored"] = False
    return item


def record_authorization(dataset_id: str, authorization: dict[str, Any]) -> dict[str, Any]:
    required = {"subject_ref", "consent_type", "consent_version", "status"}
    if any(not authorization.get(field) for field in required):
        raise LineageError("authorization_incomplete", "授权快照字段不完整")
    item_id = new_id("computation_auth")
    timestamp = now_iso()
    subject_hash = _subject_hash(str(authorization["subject_ref"]))
    with get_connection() as conn:
        if not conn.execute("SELECT 1 FROM computation_datasets WHERE id = ?", (dataset_id,)).fetchone():
            raise LineageError("dataset_not_found", "数据集不存在")
        conn.execute(
            """INSERT INTO computation_authorization_snapshots
            (id, dataset_id, subject_hash, consent_type, consent_version, status, captured_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                item_id,
                dataset_id,
                subject_hash,
                authorization["consent_type"],
                authorization["consent_version"],
                authorization["status"],
                timestamp,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM computation_authorization_snapshots WHERE id = ?", (item_id,)).fetchone()
    return row_to_dict(row)


def add_lineage(
    parent_type: str,
    parent_id: str,
    child_type: str,
    child_id: str,
    transform_version: str,
    purpose: str,
) -> dict[str, Any]:
    values = [parent_type, parent_id, child_type, child_id, transform_version, purpose]
    if any(not str(value).strip() for value in values):
        raise LineageError("lineage_incomplete", "血缘边字段不完整")
    edge_id = new_id("lineage")
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO computation_lineage_edges
            (id, parent_resource_type, parent_resource_id, child_resource_type, child_resource_id,
             transform_version, purpose, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (*([edge_id] + values), now_iso()),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM computation_lineage_edges WHERE id = ?", (edge_id,)).fetchone()
    return row_to_dict(row)


def trace_descendants(root_type: str, root_id: str) -> list[dict[str, str]]:
    queue = deque([(root_type, root_id)])
    visited = {(root_type, root_id)}
    result: list[dict[str, str]] = []
    with get_connection() as conn:
        while queue:
            parent_type, parent_id = queue.popleft()
            rows = conn.execute(
                """SELECT child_resource_type, child_resource_id
                FROM computation_lineage_edges
                WHERE parent_resource_type = ? AND parent_resource_id = ?
                ORDER BY created_at, id""",
                (parent_type, parent_id),
            ).fetchall()
            for row in rows:
                key = (str(row["child_resource_type"]), str(row["child_resource_id"]))
                if key in visited:
                    continue
                visited.add(key)
                result.append({"resource_type": key[0], "resource_id": key[1]})
                queue.append(key)
    return result


def create_legal_hold(scope_type: str, scope_id: str, reason_code: str, expires_at: str | None = None) -> dict[str, Any]:
    hold_id = new_id("legal_hold")
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO computation_legal_holds
            (id, scope_type, scope_id, reason_code, expires_at, released_at, created_at)
            VALUES (?, ?, ?, ?, ?, NULL, ?)""",
            (hold_id, scope_type, scope_id, reason_code, expires_at, now_iso()),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM computation_legal_holds WHERE id = ?", (hold_id,)).fetchone()
    return row_to_dict(row)


def record_withdrawal(subject_ref: str, root_type: str, root_id: str, reason_code: str) -> dict[str, Any]:
    descendants = trace_descendants(root_type, root_id)
    affected = [{"resource_type": root_type, "resource_id": root_id}, *descendants]
    with get_connection() as conn:
        hold = conn.execute(
            """SELECT 1 FROM computation_legal_holds
            WHERE scope_type = ? AND scope_id = ? AND released_at IS NULL LIMIT 1""",
            (root_type, root_id),
        ).fetchone()
        tombstone_id = new_id("computation_tombstone")
        conn.execute(
            """INSERT INTO computation_deletion_tombstones
            (id, subject_hash, root_resource_type, root_resource_id, reason_code,
             affected_resources_json, blocked_by_legal_hold, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                tombstone_id,
                _subject_hash(subject_ref),
                root_type,
                root_id,
                reason_code,
                json_dumps(affected),
                1 if hold else 0,
                now_iso(),
            ),
        )
        conn.commit()
    return {
        "tombstone_id": tombstone_id,
        "affected_count": len(affected),
        "blocked_by_legal_hold": bool(hold),
        "tombstone_recorded": True,
        "raw_subject_stored": False,
    }
