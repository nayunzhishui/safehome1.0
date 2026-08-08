"""Static guard for API query boundaries and sensitive route patterns."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROUTES_DIR = ROOT / "backend" / "routes"
SNAPSHOT_PATH = ROOT / "shared" / "contracts" / "api-boundary-audit.json"
AUTH_MARKERS = (
    "require_login(",
    "require_role(",
    "require_user_id(",
    "resolve_user_id_for_query(",
    "resolve_actor_user_id(",
    "require_admin_or_owner(",
    "require_admin_token(",
    "resolve_privacy_owner(",
    "_resolve_message_user_id(",
    "_actor(",
    "_researcher(",
    "_privacy_reviewer(",
)


def _is_route(node: ast.FunctionDef) -> bool:
    return any(
        isinstance(decorator, ast.Call)
        and isinstance(decorator.func, ast.Attribute)
        and decorator.func.attr in {"get", "post", "put", "patch", "delete", "route"}
        for decorator in node.decorator_list
    )


def _line(source_lines: list[str], node: ast.AST) -> str:
    return "\n".join(source_lines[node.lineno - 1 : getattr(node, "end_lineno", node.lineno)])


def _has_query_in_loop(node: ast.FunctionDef) -> bool:
    for child in ast.walk(node):
        if isinstance(child, (ast.For, ast.While)) and any(
            isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr == "execute"
            for call in ast.walk(child)
        ):
            return True
    return False


def build_snapshot() -> dict:
    findings = []
    for path in sorted(ROUTES_DIR.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        lines = source.splitlines()
        tree = ast.parse(source, filename=str(path))
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef) or not _is_route(node):
                continue
            body = _line(lines, node)
            location = f"backend/routes/{path.name}:{node.lineno}"
            if "request.args.get(\"user_id\")" in body or "request.args.get('user_id')" in body:
                if not any(marker in body for marker in AUTH_MARKERS):
                    findings.append({"severity": "blocker", "rule": "cross_user_parameter_without_visible_guard", "location": location, "handler": node.name})
            if _has_query_in_loop(node):
                findings.append({"severity": "warning", "rule": "possible_n_plus_one", "location": location, "handler": node.name})
            if "SELECT *" in body:
                findings.append({"severity": "warning", "rule": "select_star_in_http_adapter", "location": location, "handler": node.name})
            if any(isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute) and decorator.func.attr == "get" for decorator in node.decorator_list):
                if ".fetchall()" in body and "SELECT" in body and "LIMIT" not in body and "COUNT(" not in body:
                    findings.append({"severity": "warning", "rule": "possible_unbounded_list", "location": location, "handler": node.name})
    counts = {"blocker": 0, "warning": 0}
    for finding in findings:
        counts[finding["severity"]] += 1
    return {
        "schema": "safehome.api-boundary-audit.v1",
        "rules": ["cross_user_parameter_without_visible_guard", "possible_n_plus_one", "select_star_in_http_adapter", "possible_unbounded_list"],
        "counts": counts,
        "quality_boundary": "Static findings are engineering review signals, not participant or researcher quality scores.",
        "findings": findings,
    }


def _without_line_number(location: str) -> str:
    path, separator, line = str(location or "").rpartition(":")
    return path if separator and line.isdigit() else str(location or "")


def _semantic_snapshot(snapshot: dict) -> dict:
    normalized = json.loads(json.dumps(snapshot))
    for finding in normalized.get("findings", []):
        finding["location"] = _without_line_number(finding.get("location", ""))
    return normalized


def snapshots_semantically_equal(saved: dict, current: dict) -> bool:
    return _semantic_snapshot(saved) == _semantic_snapshot(current)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    snapshot = build_snapshot()
    rendered = json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
    if snapshot["counts"]["blocker"]:
        print(f"API boundary audit blockers: {snapshot['counts']['blocker']}")
        return 1
    if args.check:
        if not SNAPSHOT_PATH.exists():
            print("API boundary audit drift: regenerate shared/contracts/api-boundary-audit.json")
            return 1
        try:
            saved = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            print("API boundary audit drift: regenerate shared/contracts/api-boundary-audit.json")
            return 1
        if not snapshots_semantically_equal(saved, snapshot):
            print("API boundary audit drift: regenerate shared/contracts/api-boundary-audit.json")
            return 1
        if saved != snapshot:
            print("API boundary audit note: source line numbers moved; semantic findings are unchanged")
        print(f"API boundary audit passed: {snapshot['counts']['warning']} review warnings, 0 blockers")
        return 0
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(rendered, encoding="utf-8")
    print(f"generated {SNAPSHOT_PATH.relative_to(ROOT)}: {snapshot['counts']['warning']} warnings, 0 blockers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
