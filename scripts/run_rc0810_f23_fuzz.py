"""Build deterministic RC0810-F23 fuzz cases from the frozen API contract."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "shared" / "contracts" / "api-contract.json"
DEFAULT_CORPUS = ROOT / "config" / "rc0810" / "f23_fuzz_seed_corpus.json"


class FuzzContractError(ValueError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise FuzzContractError(f"{path} must contain a JSON object")
    return payload


def _deep_value(depth: int) -> dict[str, Any]:
    if depth < 1 or depth > 32:
        raise FuzzContractError("deep_nested depth must be between 1 and 32")
    value: dict[str, Any] = {"leaf": "f23"}
    for index in range(depth):
        value = {f"level_{depth - index}": value}
    return value


def _resolved_value(spec: dict[str, Any]) -> Any:
    kind = spec.get("value_kind")
    if kind == "deep_nested":
        return _deep_value(int(spec.get("depth") or 0))
    if kind == "repeat":
        character = str(spec.get("character") or "")
        count = int(spec.get("count") or 0)
        if len(character) != 1 or count < 1 or count > 20_000:
            raise FuzzContractError("repeat requires one character and count 1..20000")
        return character * count
    if "value" not in spec:
        raise FuzzContractError(f"case {spec.get('case_id')} has no value")
    return copy.deepcopy(spec["value"])


def _field_set(endpoint: dict[str, Any]) -> set[str]:
    request = endpoint.get("request") or {}
    fields = request.get("body_fields") or []
    fields += request.get("query_parameters") or []
    return {str(field) for field in fields}


def build_cases(contract_path: Path = DEFAULT_CONTRACT, corpus_path: Path = DEFAULT_CORPUS) -> list[dict[str, Any]]:
    contract = _read_json(Path(contract_path))
    corpus = _read_json(Path(corpus_path))
    if corpus.get("schema") != "safehome.rc0810.f23-fuzz-corpus.v1":
        raise FuzzContractError("unsupported F23 corpus schema")
    endpoints = {
        str(item.get("operation_id")): item
        for item in contract.get("endpoints") or []
        if isinstance(item, dict) and item.get("operation_id")
    }
    built: list[dict[str, Any]] = []
    seen: set[str] = set()
    for target in corpus.get("targets") or []:
        operation_id = str(target.get("operation_id") or "")
        endpoint = endpoints.get(operation_id)
        if endpoint is None:
            raise FuzzContractError(f"operation missing from API contract: {operation_id}")
        allowed_fields = _field_set(endpoint)
        base = copy.deepcopy(target.get("base") or {})
        for spec in target.get("cases") or []:
            case_id = str(spec.get("case_id") or "")
            if not case_id or case_id in seen:
                raise FuzzContractError(f"duplicate or empty case_id: {case_id}")
            seen.add(case_id)
            field = str(spec.get("field") or "")
            operator = str(spec.get("operator") or "")
            if operator != "add_unknown" and field not in allowed_fields:
                raise FuzzContractError(
                    f"{case_id} field {field!r} is not declared by {operation_id}"
                )
            value = copy.deepcopy(base)
            if operator == "missing_field":
                value.pop(field, None)
            elif operator in {"replace", "add_unknown"}:
                value[field] = _resolved_value(spec)
            else:
                raise FuzzContractError(f"unsupported operator for {case_id}: {operator}")
            built.append(
                {
                    "case_id": case_id,
                    "operation_id": operation_id,
                    "method": endpoint.get("method"),
                    "path": endpoint.get("path"),
                    "operator": operator,
                    "field": field,
                    "input": value,
                    "seed": int(corpus.get("seed") or 0),
                }
            )
    max_cases = int(corpus.get("max_cases") or 0)
    if not built or len(built) > max_cases:
        raise FuzzContractError("F23 corpus is empty or exceeds max_cases")
    return sorted(built, key=lambda item: item["case_id"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = {
        "schema": "safehome.rc0810.f23-fuzz-cases.v1",
        "cases": build_cases(args.contract, args.corpus),
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
