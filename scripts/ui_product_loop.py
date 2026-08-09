"""SafeHome 小程序 UIproduct 可恢复逐页 Loop 与 Harness。

本脚本只读取业务代码并写入 design/ui-product 与功能真值表自动证据区。
它不调用后端、不修改 API，也不替代 ImageGen、Figma 和真机人工审查。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MINI = ROOT / "apps" / "miniprogram"
APP_JSON = MINI / "app.json"
API_JS = MINI / "services" / "api.js"
TRUTH_TABLE = ROOT / "design" / "function-truth-table.md"
WORK_DIR = ROOT / "design" / "ui-product"
FACTS_JSON = WORK_DIR / "page-facts.json"
REGISTRY_JSON = WORK_DIR / "registry.json"
AUTO_BEGIN = "<!-- UI_PRODUCT_AUTO_FACTS:BEGIN -->"
AUTO_END = "<!-- UI_PRODUCT_AUTO_FACTS:END -->"
REQUIRED_BRANCH = "UIproduct"

STAGES = [
    "truth",
    "freeze",
    "imagegen",
    "image_review",
    "figma",
    "figma_review",
    "implementation",
    "loop_visual",
    "loop_ui",
    "loop_ux",
    "loop_states",
    "loop_device",
    "harness_visual",
    "harness_component",
    "harness_ux",
    "harness_engineering",
    "done",
]

ALLOWED_CHANGED_PREFIXES = (
    "AGENTS.md",
    "apps/miniprogram/",
    "design/",
    "docs/",
    "scripts/",
)
FORBIDDEN_CHANGED_PREFIXES = (
    "backend/",
    "content/",
    "shared/",
)


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def sha256_files(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(str(path.relative_to(ROOT)).replace("\\", "/").encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def load_app() -> dict[str, Any]:
    return json.loads(read_text(APP_JSON))


def page_paths(route: str) -> dict[str, Path]:
    base = MINI / route
    return {suffix: base.with_suffix(f".{suffix}") for suffix in ("wxml", "wxss", "js", "json")}


def line_number(source: str, offset: int) -> int:
    return source.count("\n", 0, offset) + 1


def clean_text(value: str) -> str:
    value = re.sub(r"<!--.*?-->", " ", value, flags=re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"{{.*?}}", " ", value, flags=re.S)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def parse_api_service() -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    source = read_text(API_JS)
    endpoints = {
        match.group(1): match.group(2)
        for match in re.finditer(r'^\s{2}([A-Za-z_$][\w$]*):\s*"([^"]+)"', source, re.M)
    }
    starts = list(
        re.finditer(
            r"^\s{2,4}(?:async\s+)?([A-Za-z_$][\w$]*)\s*\(([^)]*)\)\s*\{",
            source,
            re.M,
        )
    )
    methods: dict[str, dict[str, Any]] = {}
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(source)
        block = source[match.start():end]
        endpoint_keys = unique(re.findall(r"API_ENDPOINTS\.([A-Za-z_$][\w$]*)", block))
        paths = [endpoints[key] for key in endpoint_keys if key in endpoints]
        http_match = re.search(r'method:\s*"([A-Z]+)"', block)
        methods[match.group(1)] = {
            "parameters": re.sub(r"\s+", " ", match.group(2)).strip(),
            "http_method": http_match.group(1) if http_match else "GET",
            "endpoint_keys": endpoint_keys,
            "endpoint_templates": paths,
            "line": line_number(source, match.start()),
        }
    return endpoints, methods


def extract_visible_text(wxml: str) -> list[str]:
    values: list[str] = []
    for match in re.finditer(r">([^<>]+)<", wxml):
        value = clean_text(match.group(1))
        if value and re.search(r"[\u4e00-\u9fff]", value):
            values.append(value)
    return unique(values)[:24]


def extract_events(wxml: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    tag_pattern = re.compile(r"<([\w-]+)\b([^>]*)>", re.S)
    event_pattern = re.compile(
        r'(capture-)?(bind|catch)(?::)?([A-Za-z][\w-]*)\s*=\s*["\']([^"\']+)["\']'
    )
    for tag_match in tag_pattern.finditer(wxml):
        attrs = tag_match.group(2)
        for event_match in event_pattern.finditer(attrs):
            handler = event_match.group(4).strip()
            data_attrs = {
                key: value
                for key, value in re.findall(r'data-([\w-]+)\s*=\s*["\']([^"\']*)["\']', attrs)
            }
            label_match = re.search(r'aria-label\s*=\s*["\']([^"\']+)["\']', attrs)
            tail = wxml[tag_match.end(): tag_match.end() + 260]
            label = label_match.group(1) if label_match else clean_text(tail.split("</", 1)[0])
            events.append(
                {
                    "event": f"{event_match.group(2)}{event_match.group(3)}",
                    "handler": handler,
                    "tag": tag_match.group(1),
                    "label": label[:80],
                    "data": data_attrs,
                    "line": line_number(wxml, tag_match.start()),
                }
            )
    return events


def extract_page_methods(js: str) -> list[str]:
    return unique(
        re.findall(
            r"^\s{2,6}(?:async\s+)?([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{",
            js,
            re.M,
        )
    )


def extract_api_calls(js: str, api_methods: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    pattern = re.compile(r"(?<![\w$])(?:api|this\.api)\.([A-Za-z_$][\w$]*)\s*\(")
    for match in pattern.finditer(js):
        name = match.group(1)
        spec = api_methods.get(name)
        calls.append(
            {
                "method": name,
                "line": line_number(js, match.start()),
                "resolved": spec is not None,
                "http_method": spec["http_method"] if spec else "UNKNOWN",
                "endpoint_templates": spec["endpoint_templates"] if spec else [],
            }
        )
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    for call in calls:
        key = (call["method"], call["line"])
        if key not in seen:
            seen.add(key)
            deduped.append(call)
    return deduped


def extract_navigations(js: str, wxml: str) -> list[dict[str, Any]]:
    navigations: list[dict[str, Any]] = []
    js_pattern = re.compile(
        r"wx\.(navigateTo|redirectTo|switchTab|reLaunch)\s*\(\s*\{.*?url\s*:\s*([`\"'])(.*?)\2",
        re.S,
    )
    for match in js_pattern.finditer(js):
        captured = match.group(3)
        raw = captured.split("${", 1)[0] + ":dynamic" if "${" in captured else captured
        navigations.append(
            {
                "type": match.group(1),
                "target": raw,
                "line": line_number(js, match.start()),
                "source": "js",
            }
        )
    for match in re.finditer(r'<navigator\b[^>]*\burl=["\']([^"\']+)["\']', wxml, re.S):
        navigations.append(
            {
                "type": "navigator",
                "target": re.sub(r"{{.*?}}", ":param", match.group(1)),
                "line": line_number(wxml, match.start()),
                "source": "wxml",
            }
        )
    return navigations


def extract_storage(js: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    pattern = re.compile(
        r"wx\.(getStorageSync|setStorageSync|removeStorageSync)\s*\(\s*([A-Za-z_$][\w$]*|[\"'][^\"']+[\"'])"
    )
    for match in pattern.finditer(js):
        items.append(
            {
                "operation": match.group(1),
                "key": match.group(2).strip("\"'"),
                "line": line_number(js, match.start()),
            }
        )
    return items


def extract_state(wxml: str, js: str) -> dict[str, list[str]]:
    bindings = unique(
        [match.split(".", 1)[0] for match in re.findall(r"{{\s*([A-Za-z_$][\w$]*(?:\.[\w$]+)?)", wxml)]
    )
    branches = unique(
        [match.split(".", 1)[0] for match in re.findall(r'wx:(?:if|elif)\s*=\s*["\']{{\s*!?([A-Za-z_$][\w$]*(?:\.[\w$]+)?)', wxml)]
    )
    set_data: list[str] = []
    for match in re.finditer(r"this\.setData\s*\(\s*\{(.*?)\}\s*\)", js, re.S):
        body = match.group(1)
        set_data.extend(re.findall(r"(?:^|,)\s*([A-Za-z_$][\w$]*(?:\[[^]]+\])?(?:\.[\w$]+)?)\s*:", body))
        set_data.extend(re.findall(r"(?:^|,)\s*([A-Za-z_$][\w$]*)\s*(?=,|$)", body))
    return {"bindings": bindings, "branches": branches, "set_data": unique(set_data)}


def route_base(target: str) -> str:
    value = target.split("?", 1)[0].lstrip("/")
    return value


def likely_backend_files(endpoint_templates: list[str]) -> list[str]:
    if not endpoint_templates:
        return []
    tokens: set[str] = set()
    for template in endpoint_templates:
        for token in template.split("/"):
            token = token.strip().replace("-", "_")
            if token and token not in {"api", ":id", "id"} and not token.startswith(":"):
                tokens.add(token)
    found: list[str] = []
    for path in (ROOT / "backend").rglob("*.py"):
        relative = str(path.relative_to(ROOT)).replace("\\", "/")
        haystack = path.name.replace("-", "_") + " " + read_text(path)[:8000].replace("-", "_")
        if any(token in haystack for token in tokens):
            found.append(relative)
        if len(found) >= 8:
            break
    return found


def local_js_dependencies(entry: Path) -> list[Path]:
    """递归收集页面直接使用的本地 JS 工厂/工具，避免把共享处理器误报为缺失。"""
    found: list[Path] = []
    visited: set[Path] = set()

    def visit(path: Path, depth: int) -> None:
        if depth > 3 or path in visited or not path.exists():
            return
        visited.add(path)
        source = read_text(path)
        for match in re.finditer(r"require\(\s*[\"']([^\"']+)[\"']\s*\)", source):
            ref = match.group(1)
            if not ref.startswith("."):
                continue
            target = (path.parent / ref).resolve()
            candidates = [target, target.with_suffix(".js"), target / "index.js"]
            dependency = next((candidate for candidate in candidates if candidate.is_file()), None)
            if dependency is None or ROOT not in dependency.parents:
                continue
            if dependency not in found:
                found.append(dependency)
            visit(dependency, depth + 1)

    visit(entry, 0)
    return found


def build_facts() -> dict[str, Any]:
    app = load_app()
    routes: list[str] = app["pages"]
    _, api_methods = parse_api_service()
    all_sources: dict[str, str] = {}
    for route in routes:
        paths = page_paths(route)
        all_sources[route] = "\n".join(read_text(path) for path in paths.values() if path.exists())

    pages: list[dict[str, Any]] = []
    for index, route in enumerate(routes, start=1):
        paths = page_paths(route)
        missing = [suffix for suffix in ("wxml", "js", "json") if not paths[suffix].exists()]
        wxml = read_text(paths["wxml"]) if paths["wxml"].exists() else ""
        dependencies = local_js_dependencies(paths["js"]) if paths["js"].exists() else []
        js = "\n".join(
            [read_text(paths["js"])] + [read_text(dependency) for dependency in dependencies]
        ) if paths["js"].exists() else ""
        config = json.loads(read_text(paths["json"])) if paths["json"].exists() else {}
        events = extract_events(wxml)
        methods = extract_page_methods(js)
        method_set = set(methods)
        unresolved_events = unique(
            [
                event["handler"]
                for event in events
                if re.fullmatch(r"[A-Za-z_$][\w$]*", event["handler"])
                and event["handler"] not in method_set
            ]
        )
        api_calls = extract_api_calls(js, api_methods)
        unresolved_api = unique([call["method"] for call in api_calls if not call["resolved"]])
        navigations = extract_navigations(js, wxml)
        invalid_navigation: list[str] = []
        for navigation in navigations:
            target = route_base(navigation["target"])
            if target and ":param" not in target and ":dynamic" not in target and target.startswith("pages/") and target not in routes:
                invalid_navigation.append(target)
        upstream = []
        needle = f"/{route}"
        for source_route, source in all_sources.items():
            if source_route != route and (needle in source or route in source):
                upstream.append(source_route)
        components = config.get("usingComponents") or {}
        source_files = [path for path in paths.values() if path.exists()] + dependencies
        endpoint_templates = unique(
            [template for call in api_calls for template in call["endpoint_templates"]]
        )
        pages.append(
            {
                "index": index,
                "route": route,
                "title": config.get("navigationBarTitleText") or app.get("window", {}).get("navigationBarTitleText", ""),
                "source_files": [str(path.relative_to(ROOT)).replace("\\", "/") for path in source_files],
                "source_hash": sha256_files(source_files) if source_files else "",
                "missing_files": missing,
                "visible_text": extract_visible_text(wxml),
                "events": events,
                "page_methods": methods,
                "unresolved_event_handlers": unresolved_events,
                "api_calls": api_calls,
                "unresolved_api_methods": unresolved_api,
                "endpoint_templates": endpoint_templates,
                "backend_evidence": likely_backend_files(endpoint_templates),
                "navigations": navigations,
                "invalid_navigation_targets": unique(invalid_navigation),
                "upstream_pages": upstream,
                "components": components,
                "storage": extract_storage(js),
                "state": extract_state(wxml, js),
                "review_status": "blocked" if missing or unresolved_events or unresolved_api or invalid_navigation else "auto_evidence_complete",
            }
        )
    return {
        "schema_version": 1,
        "generated_at": now_iso(),
        "branch": run_git("branch", "--show-current"),
        "main_sha": run_git("rev-parse", "main"),
        "app_page_count": len(routes),
        "pages": pages,
    }


def md_cell(value: Any) -> str:
    if value in (None, "", [], {}):
        return "—"
    if isinstance(value, list):
        value = "、".join(str(item) for item in value)
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_auto_markdown(facts: dict[str, Any]) -> str:
    lines = [
        AUTO_BEGIN,
        "",
        "## 全页面自动代码证据（UIproduct Harness）",
        "",
        f"生成时间：`{facts['generated_at']}`  ",
        f"分支：`{facts['branch']}`  ",
        f"页面数：`{facts['app_page_count']}`",
        "",
        "本节由 `scripts/ui_product_loop.py audit-truth` 从当前代码生成，覆盖 WXML 事件、JS 处理器、API 客户端方法、接口模板、路由、本地存储、页面状态、组件和上下游入口。自动证据是逐页人工冻结的底稿；任何未解析项都会阻断 ImageGen。",
        "",
    ]
    for page in facts["pages"]:
        lines.extend(
            [
                f"### {page['index']:02d}：{page['title']} `{page['route']}`",
                "",
                f"- 真值状态：`{page['review_status']}`",
                f"- 源码指纹：`{page['source_hash']}`",
                f"- 核对文件：{md_cell([f'`{item}`' for item in page['source_files']])}",
                f"- 上游页面：{md_cell([f'`{item}`' for item in page['upstream_pages']])}",
                f"- 页面组件：{md_cell([f'`{key}` → `{value}`' for key, value in page['components'].items()])}",
                f"- 主要可见内容：{md_cell(page['visible_text'])}",
                "",
                "#### 交互与用户任务证据",
                "",
                "| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |",
                "|---:|---|---|---|---|",
            ]
        )
        if page["events"]:
            for event in page["events"]:
                lines.append(
                    f"| {event['line']} | {md_cell(event['label'])} | `{event['event']}` | `{event['handler']}` | {md_cell(event['data'])} |"
                )
        else:
            lines.append("| — | 只读或生命周期驱动页面 | — | — | — |")
        lines.extend(
            [
                "",
                "#### 接口真值",
                "",
                "| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |",
                "|---:|---|---|---|---|",
            ]
        )
        if page["api_calls"]:
            for call in page["api_calls"]:
                lines.append(
                    f"| {call['line']} | `{call['method']}` | `{call['http_method']}` | {md_cell([f'`{item}`' for item in call['endpoint_templates']])} | {md_cell([f'`{item}`' for item in page['backend_evidence']])} |"
                )
        else:
            lines.append("| — | 无直接 API 调用 | — | — | 页面由本地状态或路由驱动 |")
        navigation_evidence = [
            f"`{item['type']}` → `{item['target']}`（{item['source']}:{item['line']}）"
            for item in page["navigations"]
        ]
        storage_evidence = [
            f"`{item['operation']}` `{item['key']}`（JS:{item['line']}）"
            for item in page["storage"]
        ]
        lines.extend(
            [
                "",
                "#### 路由、本地状态与页面状态",
                "",
                f"- 下游路由：{md_cell(navigation_evidence)}",
                f"- 本地存储：{md_cell(storage_evidence)}",
                f"- WXML 数据绑定：{md_cell([f'`{item}`' for item in page['state']['bindings']])}",
                f"- 条件状态：{md_cell([f'`{item}`' for item in page['state']['branches']])}",
                f"- `setData` 状态：{md_cell([f'`{item}`' for item in page['state']['set_data']])}",
                f"- 未解析事件：{md_cell(page['unresolved_event_handlers'])}",
                f"- 未解析 API：{md_cell(page['unresolved_api_methods'])}",
                f"- 无效目标路由：{md_cell(page['invalid_navigation_targets'])}",
                "",
                "#### 设计与实现边界",
                "",
                "- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。",
                "- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。",
                "- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。",
                "",
            ]
        )
    lines.extend([AUTO_END, ""])
    return "\n".join(lines)


def update_truth_table(facts: dict[str, Any]) -> None:
    current = read_text(TRUTH_TABLE)
    current = re.sub(r"更新时间：\d{4}-\d{2}-\d{2}", "更新时间：2026-08-10", current, count=1)
    for page in facts["pages"]:
        route = re.escape(page["route"])
        status = (
            "自动代码证据已核对；逐页冻结前复核"
            if page["review_status"] == "auto_evidence_complete"
            else "代码事实存在阻断"
        )
        current = re.sub(
            rf"(\| `{route}` \| [^|]+ \| )[^|]+( \|)",
            rf"\g<1>{status}\g<2>",
            current,
            count=1,
        )
    auto = render_auto_markdown(facts)
    if AUTO_BEGIN in current and AUTO_END in current:
        prefix = current.split(AUTO_BEGIN, 1)[0].rstrip()
        suffix = current.split(AUTO_END, 1)[1].lstrip("\n")
        updated = prefix + "\n\n" + auto + suffix
    else:
        updated = current.rstrip() + "\n\n" + auto
    write_text(TRUTH_TABLE, updated)


def init_registry(facts: dict[str, Any]) -> dict[str, Any]:
    existing: dict[str, Any] = {}
    if REGISTRY_JSON.exists():
        existing = json.loads(read_text(REGISTRY_JSON))
    old_pages = {page["route"]: page for page in existing.get("pages", [])}
    pages = []
    for page in facts["pages"]:
        old = old_pages.get(page["route"], {})
        evidence = old.get("evidence", {})
        stage = old.get("stage", "truth_pending")
        if page["review_status"] == "auto_evidence_complete" and stage == "truth_pending":
            stage = "truth_auto_complete"
        pages.append(
            {
                "index": page["index"],
                "route": page["route"],
                "title": page["title"],
                "source_hash": page["source_hash"],
                "stage": stage,
                "evidence": evidence,
                "updated_at": old.get("updated_at", facts["generated_at"]),
            }
        )
    registry = {
        "schema_version": 1,
        "branch": REQUIRED_BRANCH,
        "main_sha_at_start": existing.get("main_sha_at_start", facts["main_sha"]),
        "visual_direction": "A_编辑手帐",
        "workflow": STAGES,
        "active_route": existing.get("active_route", pages[0]["route"] if pages else None),
        "updated_at": facts["generated_at"],
        "pages": pages,
    }
    write_text(REGISTRY_JSON, json.dumps(registry, ensure_ascii=False, indent=2) + "\n")
    return registry


def audit_truth() -> None:
    assert_branch()
    facts = build_facts()
    write_text(FACTS_JSON, json.dumps(facts, ensure_ascii=False, indent=2) + "\n")
    update_truth_table(facts)
    init_registry(facts)
    blocked = [page for page in facts["pages"] if page["review_status"] != "auto_evidence_complete"]
    print(f"已生成 {facts['app_page_count']} 页代码证据；阻断页 {len(blocked)}。")
    for page in blocked:
        print(
            f"- {page['route']}: missing={page['missing_files']} "
            f"events={page['unresolved_event_handlers']} api={page['unresolved_api_methods']} "
            f"routes={page['invalid_navigation_targets']}"
        )


def assert_branch() -> None:
    branch = run_git("branch", "--show-current")
    if branch != REQUIRED_BRANCH:
        raise SystemExit(f"UIproduct Harness 阻断：当前分支是 {branch!r}，必须是 {REQUIRED_BRANCH!r}。")


def check_scope() -> list[str]:
    assert_branch()
    changed = unique(
        run_git("diff", "--name-only", "main").splitlines()
        + run_git("diff", "--name-only").splitlines()
        + run_git("ls-files", "--others", "--exclude-standard").splitlines()
    )
    failures: list[str] = []
    for path in changed:
        normalized = path.replace("\\", "/")
        if normalized.startswith(FORBIDDEN_CHANGED_PREFIXES):
            failures.append(f"禁止范围发生改动：{normalized}")
        elif not normalized.startswith(ALLOWED_CHANGED_PREFIXES):
            failures.append(f"未授权范围发生改动：{normalized}")
    return failures


def check_truth() -> None:
    assert_branch()
    if not FACTS_JSON.exists() or not REGISTRY_JSON.exists():
        raise SystemExit("UIproduct Harness 阻断：请先运行 audit-truth。")
    facts = json.loads(read_text(FACTS_JSON))
    current = build_facts()
    failures = check_scope()
    if facts["app_page_count"] != current["app_page_count"]:
        failures.append("app.json 页面数量已变化，请重新运行 audit-truth。")
    saved = {page["route"]: page for page in facts["pages"]}
    current_map = {page["route"]: page for page in current["pages"]}
    if set(saved) != set(current_map):
        failures.append("功能真值表与 app.json 页面集合不一致。")
    for route, page in current_map.items():
        if page["review_status"] != "auto_evidence_complete":
            failures.append(f"{route} 存在未解析代码事实。")
        if route in saved and saved[route]["source_hash"] != page["source_hash"]:
            failures.append(f"{route} 源码已变化，必须更新真值表。")
    truth = read_text(TRUTH_TABLE)
    for route in current_map:
        if f"`{route}`" not in truth:
            failures.append(f"功能真值表遗漏页面：{route}")
    if failures:
        raise SystemExit("UIproduct 真值 Harness 失败：\n- " + "\n- ".join(failures))
    print(f"UIproduct 真值 Harness 通过：{len(current_map)} 页已登记且代码事实无未解析项。")


def load_registry() -> dict[str, Any]:
    if not REGISTRY_JSON.exists():
        raise SystemExit("请先运行 audit-truth 初始化机器注册表。")
    return json.loads(read_text(REGISTRY_JSON))


def resolve_evidence(value: str) -> str:
    if value.startswith(("http://", "https://", "figma://")):
        return value
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        raise SystemExit(f"证据不存在：{path}")
    return str(path.resolve()).replace("\\", "/")


def record_stage(route: str, stage: str, evidence: list[str], note: str) -> None:
    assert_branch()
    if stage not in STAGES:
        raise SystemExit(f"未知阶段：{stage}")
    registry = load_registry()
    page = next((item for item in registry["pages"] if item["route"] == route), None)
    if page is None:
        raise SystemExit(f"页面未登记：{route}")
    completed = [name for name in STAGES if name in page.get("evidence", {})]
    expected = STAGES[len(completed)] if len(completed) < len(STAGES) else "done"
    if stage != expected and stage not in page.get("evidence", {}):
        raise SystemExit(f"阶段顺序阻断：{route} 下一阶段应为 {expected}，不能记录 {stage}。")
    resolved = [resolve_evidence(item) for item in evidence]
    if stage != "done" and not resolved:
        raise SystemExit(f"阶段 {stage} 必须提供证据文件或 Figma 链接。")
    page.setdefault("evidence", {})[stage] = {
        "items": resolved,
        "note": note,
        "recorded_at": now_iso(),
    }
    page["stage"] = "complete" if stage == "done" else f"{stage}_complete"
    page["updated_at"] = now_iso()
    if stage == "done":
        remaining = [item for item in registry["pages"] if item["stage"] != "complete"]
        registry["active_route"] = remaining[0]["route"] if remaining else None
    else:
        registry["active_route"] = route
    registry["updated_at"] = now_iso()
    write_text(REGISTRY_JSON, json.dumps(registry, ensure_ascii=False, indent=2) + "\n")
    print(f"已记录 {route} / {stage}。")


def status() -> None:
    assert_branch()
    registry = load_registry()
    counts: dict[str, int] = {}
    for page in registry["pages"]:
        counts[page["stage"]] = counts.get(page["stage"], 0) + 1
    print(f"分支：{run_git('branch', '--show-current')}")
    print(f"main 起点：{registry['main_sha_at_start']}")
    print(f"视觉方向：{registry['visual_direction']}")
    print(f"当前页面：{registry['active_route']}")
    for key in sorted(counts):
        print(f"- {key}: {counts[key]}")


def harness() -> None:
    check_truth()
    failures = check_scope()
    main_sha = run_git("rev-parse", "main")
    registry = load_registry()
    if main_sha != registry["main_sha_at_start"]:
        failures.append("main 分支指针已变化；停止 UI 自动流程并人工核对。")
    diff_check = subprocess.run(
        ["git", "diff", "--check"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8"
    )
    if diff_check.returncode != 0:
        failures.append("git diff --check 未通过。")
    if failures:
        raise SystemExit("UIproduct 工程 Harness 失败：\n- " + "\n- ".join(failures))
    print("UIproduct 工程 Harness 通过：分支、范围、main 指针、真值覆盖和 diff 格式均合格。")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("audit-truth", help="扫描全部页面并更新真值证据与注册表")
    sub.add_parser("check-truth", help="检查页面覆盖、解析完整性与源码漂移")
    sub.add_parser("status", help="显示可恢复逐页状态")
    sub.add_parser("harness", help="执行分支、范围、真值与工程门禁")
    record = sub.add_parser("record", help="按顺序记录一页的阶段证据")
    record.add_argument("--page", required=True)
    record.add_argument("--stage", required=True, choices=STAGES)
    record.add_argument("--evidence", action="append", default=[])
    record.add_argument("--note", default="")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "audit-truth":
        audit_truth()
    elif args.command == "check-truth":
        check_truth()
    elif args.command == "status":
        status()
    elif args.command == "harness":
        harness()
    elif args.command == "record":
        record_stage(args.page, args.stage, args.evidence, args.note)
    else:
        raise SystemExit(f"未知命令：{args.command}")


if __name__ == "__main__":
    main()
