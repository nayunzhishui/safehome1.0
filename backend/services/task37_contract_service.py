"""Versioned computation contracts for Task 37."""

from __future__ import annotations

import json
from typing import Any

from config import PROJECT_ROOT


PATH = PROJECT_ROOT / "content" / "task37_computation_contract.json"


class ContractError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def registry() -> dict[str, Any]:
    try:
        return json.loads(PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError("registry_unavailable", "计算契约注册表不可用") from exc


def validate_new_record(record: dict[str, Any]) -> dict[str, Any]:
    rules = registry()
    if record.get("contract_version") != rules["contract_version"]:
        raise ContractError("unsupported_version", "新写入必须使用当前计算契约版本")
    allowed = set(rules["required_input_fields"])
    unknown = set(record) - allowed
    if unknown:
        raise ContractError("unknown_fields", f"存在未知字段：{','.join(sorted(unknown))}")
    missing = [field for field in rules["required_input_fields"] if record.get(field) in (None, "")]
    if missing:
        raise ContractError("required_field_missing", f"缺少字段：{','.join(missing)}")
    if record["entity_type"] not in rules["entities"]:
        raise ContractError("entity_type_unknown", "未知计算对象类型")
    if record["purpose"] not in rules["allowed_purposes"]:
        raise ContractError("purpose_unknown", "未知数据用途")
    if record["subject_scope"] not in rules["allowed_subject_scopes"]:
        raise ContractError("subject_scope_unknown", "未知对象范围")
    if record["de_identification"] not in rules["allowed_de_identification"]:
        raise ContractError("de_identification_unknown", "未知去标识状态")
    window = record["time_window"]
    if not isinstance(window, dict) or not window.get("start") or not window.get("end"):
        raise ContractError("time_window_invalid", "时间窗必须包含start和end")
    if not isinstance(record["payload"], dict):
        raise ContractError("payload_invalid", "payload必须是对象")
    return {**record, "legacy": False, "read_only": False}


def read_record(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("contract_version") == registry()["contract_version"]:
        return validate_new_record(record)
    return {**record, "contract_version": "legacy", "legacy": True, "read_only": True}


def public_status() -> dict[str, Any]:
    rules = registry()
    return {
        "contract_version": rules["contract_version"],
        "entity_types": list(rules["entities"]),
        "required_input_fields": rules["required_input_fields"],
        "governed_output_fields": list(rules["governed_output_fields"]),
        "legacy_readable": rules["legacy_policy"]["readable"],
        "writes_enabled": rules["writes_enabled"],
        "boundary_notice": rules["boundary_notice"],
    }
