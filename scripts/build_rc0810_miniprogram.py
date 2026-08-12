from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "apps" / "miniprogram"
DEFAULT_POLICY = ROOT / "config" / "rc0810" / "miniprogram_page_policy.json"
ROUTE_RE = re.compile(r"[\"'`](/pages/[a-z0-9-]+/index)(?:\?[^\"'`]*)?[\"'`]", re.I)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_policy(app: dict, policy: dict) -> dict[str, str]:
    pages = app.get("pages", [])
    records = policy.get("pages", [])
    mapping = {item.get("page"): item.get("classification") for item in records}
    if len(mapping) != len(records):
        raise ValueError("duplicate page classification")
    missing = sorted(set(pages) - set(mapping))
    extra = sorted(set(mapping) - set(pages))
    if missing or extra:
        raise ValueError(f"unclassified or unknown pages: missing={missing}, extra={extra}")
    allowed = set(policy.get("classifications", []))
    invalid = sorted(page for page, kind in mapping.items() if kind not in allowed)
    if invalid:
        raise ValueError(f"invalid page classifications: {invalid}")
    return mapping


def copy_source(output: Path, excluded: set[str]) -> None:
    for source in SOURCE.rglob("*"):
        if not source.is_file():
            continue
        relative = source.relative_to(SOURCE).as_posix()
        page_stem = relative.rsplit(".", 1)[0]
        if page_stem in excluded:
            continue
        if relative in {"project.private.config.json", "project.config.json", "app.json"}:
            continue
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def strip_named_methods(path: Path, names: list[str]) -> None:
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    for name in names:
        match = re.search(rf"\n\s*{re.escape(name)}\s*\([^)]*\)\s*\{{", text)
        if not match:
            raise ValueError(f"cannot strip production-only method {name} from {path.as_posix()}")
        depth = 1
        index = match.end()
        quote = None
        escaped = False
        while index < len(text) and depth:
            char = text[index]
            if quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
            elif char in {"'", '"', "`"}:
                quote = char
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            index += 1
        if depth:
            raise ValueError(f"unterminated method {name} in {path.as_posix()}")
        if index < len(text) and text[index] == ",":
            index += 1
        text = text[: match.start()] + text[index:]
    path.write_text(text, encoding="utf-8")


def strip_template_handlers(path: Path, names: list[str]) -> None:
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    for name in names:
        pattern = re.compile(
            rf"\s*<(view|button)\b[^>]*bindtap=[\"']{re.escape(name)}[\"'][^>]*>.*?</\1>",
            re.S,
        )
        text, count = pattern.subn("", text)
        if count != 1:
            raise ValueError(f"cannot strip production-only template handler {name} from {path.as_posix()}")
    path.write_text(text, encoding="utf-8")


def build_reachability(output: Path, included: list[str], journey: list[str]) -> dict:
    nodes = set(included)
    edges = []
    unresolved = []
    for path in output.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".js", ".wxml"}:
            continue
        source = path.relative_to(output).as_posix()
        for route in sorted(set(ROUTE_RE.findall(path.read_text(encoding="utf-8", errors="ignore")))):
            target = route.removeprefix("/")
            edges.append({"source": source, "target": target})
            if target not in nodes:
                unresolved.append({"source": source, "target": target})
    graph = {
        "schema": "safehome.rc0810.miniprogram-reachability.v1",
        "nodes": included,
        "edges": edges,
        "participant_journey_pages": journey,
        "unresolved_routes": unresolved,
    }
    write_json(output / "rc0810-page-reachability.json", graph)
    return graph


def scan_internal_routes(output: Path, internal: set[str]) -> list[dict]:
    findings = []
    for path in output.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".js", ".json", ".wxml", ".wxss"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for route in sorted(set(ROUTE_RE.findall(text))):
            normalized = route.removeprefix("/")
            if normalized in internal:
                findings.append({"file": path.relative_to(output).as_posix(), "route": route})
    return findings


def build(profile: str, output: Path, policy_path: Path, should_copy: bool) -> dict:
    app = read_json(SOURCE / "app.json")
    policy = read_json(policy_path)
    mapping = validate_policy(app, policy)
    internal = {page for page, kind in mapping.items() if kind != "participant"}
    included = list(app["pages"]) if profile == "validation" else [page for page in app["pages"] if page not in internal]
    manifest = dict(app)
    manifest["pages"] = included
    tab_pages = {item["pagePath"] for item in manifest.get("tabBar", {}).get("list", [])}
    if not tab_pages <= set(included):
        raise ValueError("tabBar references excluded page")
    artifact_root = (ROOT / ".codex_tmp" / "rc0810").resolve()
    system_temp_root = Path(tempfile.gettempdir()).resolve()
    allowed_parent = next(
        (
            parent
            for parent in (artifact_root, system_temp_root)
            if output != parent and parent in output.parents
        ),
        None,
    )
    if allowed_parent is None:
        raise ValueError("output must be a child of .codex_tmp/rc0810 or the system temp directory")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "app.json", manifest)
    write_json(output / "rc0810-environment.json", {
        "schema": "safehome.rc0810.miniprogram-environment.v1",
        "profile": profile,
        "watermark": "VALIDATION · 非正式环境" if profile == "validation" else None,
    })
    if should_copy:
        copy_source(output, set() if profile == "validation" else internal)
        if profile == "production":
            for relative, methods in policy.get("production_route_rewrites", {}).items():
                strip_named_methods(output / relative, methods)
            for relative, handlers in policy.get("production_template_handlers", {}).items():
                strip_template_handlers(output / relative, handlers)
    internal_routes = [] if not should_copy or profile == "validation" else scan_internal_routes(output, internal)
    journey = policy.get("participant_journey_pages", [])
    unreachable = sorted(set(journey) - set(included))
    graph = build_reachability(output, included, journey)
    audit = {
        "schema": "safehome.rc0810.miniprogram-package-audit.v1",
        "profile": profile,
        "source_manifest_sha256": file_hash(SOURCE / "app.json"),
        "policy_sha256": file_hash(policy_path),
        "page_count": len(included),
        "excluded_pages": sorted(internal) if profile == "production" else [],
        "unreachable_participant_pages": unreachable,
        "internal_route_references": internal_routes,
        "journey_gate_passed": not unreachable and not internal_routes and not graph["unresolved_routes"],
        "production_gate_eligible": profile == "production" and not unreachable and not internal_routes and not graph["unresolved_routes"],
    }
    write_json(output / "rc0810-package-audit.json", audit)
    if profile == "production" and should_copy and internal_routes:
        raise ValueError(f"production package references internal routes: {internal_routes}")
    return audit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True, choices=["production", "validation"])
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--policy", default=DEFAULT_POLICY, type=Path)
    parser.add_argument("--copy-source", action="store_true")
    args = parser.parse_args()
    try:
        audit = build(args.profile, args.output.resolve(), args.policy.resolve(), args.copy_source)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
