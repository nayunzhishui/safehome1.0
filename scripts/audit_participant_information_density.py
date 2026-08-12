"""Generate a read-only participant-page and function-preservation baseline.

The audit intentionally measures source-level exposure instead of claiming to
measure rendered cognitive load. Runtime screenshots remain a later UI-review
step. No product source file is changed by this script.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MINI = ROOT / "apps" / "miniprogram"
DEFAULT_POLICY = ROOT / "config" / "rc0810" / "miniprogram_page_policy.json"
DEFAULT_OUTPUT = ROOT / "artifacts" / "information-density"
DEFAULT_FUNCTION_OUTPUT = ROOT / "artifacts" / "convergence" / "function-baseline"

TAG_RE = re.compile(r"<[^>]+>", re.S)
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
MUSTACHE_RE = re.compile(r"{{.*?}}", re.S)
TEXT_RE = re.compile(r">([^<]+)<", re.S)
VISIBLE_ATTR_RE = re.compile(
    r"(?:title|subtitle|text|more-text|button-label|message|boundary-notice|placeholder)=[\"']([^\"']+)[\"']"
)
CLASS_RE = re.compile(r'class=["\']([^"\']+)["\']')
HANDLER_RE = re.compile(r"(?:bind|catch):?(?:tap|change|submit|confirm|input|retry|action|more)=[\"']([\w:-]+)[\"']")
API_RE = re.compile(r"\bapi\.([A-Za-z_$][\w$]*)\s*\(")
ROUTE_RE = re.compile(r"[\"'`](/pages/[a-z0-9-]+/index)(?:\?[^\"'`]*)?[\"'`]", re.I)
METHOD_RE = re.compile(r"^\s{2}([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{", re.M)
CONDITIONAL_RE = re.compile(r"\bwx:(if|elif|else)\b")

TERMS = (
    "modelId", "model_id", "clusterId", "cluster_id", "PCA", "feature",
    "算法", "模型", "样本", "聚类", "置信度", "匹配清晰度", "研究",
)
RISK_TERMS = ("风险", "危机", "自伤", "自杀", "伤害", "紧急", "人工支持")
BOUNDARY_TERMS = ("不构成诊断", "不做诊断", "不替代", "边界", "仅用于", "只作为")
RECOMMENDATION_TERMS = ("推荐", "建议", "可以先做", "下一步", "今天的一小步")
STATUS_TERMS = ("状态", "进度", "记录", "完成", "暂停", "失败", "正在", "暂无", "还没有")

HOME_FEATURES = [
    "消息中心", "情绪天气", "测一测", "情绪日记", "今天的一小步", "三步开始",
    "支持性反馈", "训练中心", "人工支持", "最近记录", "阶段性反馈", "联调测试入口（仅开发态）",
]
RESULT_FEATURES = [
    "测评名称与结果摘要", "风险状态提示", "阶段性画像/匹配清晰度", "画像相对位置图",
    "画像维度雷达图", "画像文字解释", "优势提示", "当前可做的小步骤", "可讨论问题",
    "后续项目任务线索", "量表维度位置", "维度雷达图", "维度分数与范围", "训练卡推荐",
    "进入可练习任务", "返回测一测", "非诊断边界说明",
]

HOME_BUTTONS = [
    {"label": "消息中心", "handler": "openMessages", "target": "/pages/messages/index"},
    {"label": "情绪天气/记录", "handler": "openThermometer", "target": "/pages/thermometer/index"},
    {"label": "测一测", "handler": "openCoreEntry", "target": "/pages/assessment/index"},
    {"label": "情绪日记", "handler": "openCoreEntry", "target": "/pages/diary-form/index"},
    {"label": "今天的一小步", "handler": "openTodayAction", "target": "服务端/本地草稿返回的受控目标"},
    {"label": "今天的一小步重试", "handler": "retryTodayJourney", "target": "原地重试"},
    {"label": "了解三步", "handler": "openGettingStarted", "target": "/pages/getting-started/index"},
    {"label": "三步：去记录", "handler": "openStartStep", "target": "/pages/diary-form/index"},
    {"label": "三步：了解反馈", "handler": "openStartStep", "target": "/pages/getting-started/index"},
    {"label": "三步：去练习", "handler": "openStartStep", "target": "/pages/training/index"},
    {"label": "支持性反馈", "handler": "openCoreEntry", "target": "/pages/diary-form/index（先提示需记录）"},
    {"label": "训练中心", "handler": "openCoreEntry", "target": "/pages/training/index"},
    {"label": "人工支持", "handler": "openCoreEntry", "target": "/pages/supervision/index"},
    {"label": "最近记录/查看全部/去记录", "handler": "openWeeklyReport/startDiary", "target": "/pages/weekly-report/index 或 /pages/diary-form/index"},
    {"label": "阶段性反馈/本周复盘", "handler": "openWeeklyReport", "target": "/pages/weekly-report/index"},
    {"label": "阶段性反馈空态：去测一测", "handler": "openAssessment", "target": "/pages/assessment/index"},
    {"label": "进入联调测试页（仅开发态）", "handler": "openIntegrationTest", "target": "/pages/integration-test/index"},
]

RESULT_BUTTONS = [
    {"label": "查看可练习任务", "handler": "openRecommendedCards", "target": "/pages/training-card/index 或 /pages/training/index"},
    {"label": "返回测一测", "handler": "backToAssessment", "target": "navigateBack(delta=2)"},
]

HOME_DATA_BLOCKS = [
    "顶部问候与消息状态", "情绪天气", "测一测/情绪日记核心入口", "今天的一小步",
    "三步开始", "更多支持入口", "最近记录", "阶段性反馈", "开发态联调入口",
]
RESULT_DATA_BLOCKS = [
    "测评名称与结果摘要", "风险提示", "阶段性画像位置", "画像图例与解释", "优势/小步骤",
    "讨论问题/项目任务线索", "学生支持性画像摘要", "量表维度位置与图表", "推荐训练卡",
    "结果操作区", "统一边界提示",
]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    return result.stdout.strip()


def literal_text_nodes(wxml: str) -> list[str]:
    clean = COMMENT_RE.sub("", wxml)
    nodes = []
    for raw in TEXT_RE.findall(clean):
        text = MUSTACHE_RE.sub("", raw)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            nodes.append(text)
    for raw in VISIBLE_ATTR_RE.findall(clean):
        text = MUSTACHE_RE.sub("", raw)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            nodes.append(text)
    return nodes


def count_class_units(wxml: str, tokens: tuple[str, ...]) -> int:
    count = 0
    for value in CLASS_RE.findall(wxml):
        static = MUSTACHE_RE.sub("", value)
        if any(token in class_name.lower() for class_name in static.split() for token in tokens):
            count += 1
    return count


def count_structural_units(wxml: str, suffixes: tuple[str, ...]) -> int:
    count = 0
    for value in CLASS_RE.findall(wxml):
        static = MUSTACHE_RE.sub("", value)
        class_names = [item for item in static.split() if "--" not in item]
        if any(class_name in suffixes or class_name.endswith(suffixes) for class_name in class_names):
            count += 1
    return count


def term_hits(source: str, terms: tuple[str, ...]) -> int:
    return sum(source.lower().count(term.lower()) for term in terms)


def page_metrics(page: str) -> dict:
    base = MINI / page
    wxml = read_text(base.with_suffix(".wxml"))
    js = read_text(base.with_suffix(".js"))
    wxss = read_text(base.with_suffix(".wxss"))
    config = read_text(base.with_suffix(".json"))
    nodes = literal_text_nodes(wxml)
    literal_text = "".join(nodes)
    handlers = HANDLER_RE.findall(wxml)
    buttons = len(re.findall(r"<button\b", wxml))
    tappable_views = len(re.findall(r"<(?:view|text|image)\b[^>]*(?:bindtap|catchtap)=", wxml))
    sections = count_structural_units(wxml, ("section", "-section"))
    cards = count_structural_units(wxml, ("card", "panel", "block", "strip", "-card", "-panel", "-block", "-strip"))
    custom_actions = len(re.findall(r"<[a-z][\w-]+\b[^>]*\bbind:(?:action|retry|more)=", wxml))
    action_count = buttons + tappable_views + len(re.findall(r"<navigator\b", wxml)) + custom_actions
    terminology = term_hits(literal_text, TERMS)
    repetition = sum(count - 1 for count in Counter(node for node in nodes if len(node) >= 4).values() if count > 1)
    decision_load = action_count + len(set(handlers)) + term_hits(wxml, RECOMMENDATION_TERMS)
    return {
        "page": page,
        "source_bytes": sum(len(text.encode("utf-8")) for text in (wxml, js, wxss, config)),
        "wxml_bytes": len(wxml.encode("utf-8")),
        "section_count": sections,
        "card_count": cards,
        "visible_literal_chars": len(literal_text),
        "text_node_count": len(nodes),
        "longest_text_node_chars": max((len(node) for node in nodes), default=0),
        "title_explanation_count": sum(1 for node in nodes if len(node) >= 8),
        "button_count": buttons,
        "tappable_view_count": tappable_views,
        "action_count": action_count,
        "unique_handler_count": len(set(handlers)),
        "chart_count": len(re.findall(r"<canvas\b|<ec-canvas\b", wxml)),
        "metric_count": count_class_units(wxml, ("metric", "score", "number", "value", "count")),
        "recommendation_hits": term_hits(wxml, RECOMMENDATION_TERMS),
        "risk_hits": term_hits(wxml, RISK_TERMS),
        "boundary_hits": term_hits(wxml, BOUNDARY_TERMS),
        "status_hits": term_hits(wxml, STATUS_TERMS),
        "terminology_burden": terminology,
        "repetition_count": repetition,
        "conditional_count": len(CONDITIONAL_RE.findall(wxml)),
        "decision_load": decision_load,
        "api_call_count": len(set(API_RE.findall(js))),
    }


def add_scores(rows: list[dict]) -> None:
    dimensions = {
        "text_density": ("visible_literal_chars", "text_node_count", "longest_text_node_chars"),
        "action_density": ("action_count", "unique_handler_count"),
        "visual_density": ("section_count", "card_count", "chart_count", "metric_count"),
        "terminology": ("terminology_burden",),
        "repetition": ("repetition_count", "boundary_hits"),
        "decision_load_score": ("decision_load", "conditional_count"),
    }
    maxima = {key: max((row[key] for row in rows), default=1) or 1 for keys in dimensions.values() for key in keys}
    for row in rows:
        scores = {}
        for label, keys in dimensions.items():
            scores[label] = round(100 * sum(row[key] / maxima[key] for key in keys) / len(keys), 1)
        row.update(scores)
        row["density_score"] = round(
            0.24 * scores["text_density"]
            + 0.20 * scores["action_density"]
            + 0.20 * scores["visual_density"]
            + 0.12 * scores["terminology"]
            + 0.08 * scores["repetition"]
            + 0.16 * scores["decision_load_score"],
            1,
        )


def handler_targets(js: str) -> list[str]:
    return sorted(set(ROUTE_RE.findall(js)))


def function_baseline(page: str, features: list[str], buttons: list[dict], captured_at: str = "") -> dict:
    base = MINI / page
    wxml = read_text(base.with_suffix(".wxml"))
    js = read_text(base.with_suffix(".js"))
    handlers = sorted(set(HANDLER_RE.findall(wxml)))
    api_calls = sorted(set(API_RE.findall(js)))
    classes = [MUSTACHE_RE.sub("", item) for item in CLASS_RE.findall(wxml)]
    detected_data_blocks = sorted({
        token for item in classes for token in item.split()
        if any(marker in token for marker in ("section", "card", "strip", "actions", "list", "head"))
    })
    has_loading = "loading" in wxml.lower() or "Loading" in js
    has_error = "error" in wxml.lower() or "Error" in js
    has_empty = "wx:else" in wxml or "暂无" in wxml or "还没有" in wxml or "没有找到" in wxml
    if page == "pages/home/index":
        data_blocks = HOME_DATA_BLOCKS
        error_states = ["今天的一小步错误与手动重试", "阶段性反馈错误/离线提示", "首页数据整体异常时的保守回退"]
        loading_states = ["今天的一小步卡片加载态", "情绪天气未就绪时显示联网后更新"]
        empty_states = ["最近记录空态并提供去记录", "阶段性反馈不足/不可用空态并保留测评和周报入口"]
    elif page == "pages/assessment-result/index":
        data_blocks = RESULT_DATA_BLOCKS
        error_states = ["结果读取失败或未找到共用错误区", "画像位置/量表/训练卡辅助请求失败时降级显示"]
        loading_states = ["整页正在读取结果"]
        empty_states = ["没有找到结果", "维度不足时不绘图并解释原因", "无推荐卡时保留训练中心回退"]
    else:
        data_blocks = detected_data_blocks
        error_states = ["页面/局部错误提示"] if has_error else []
        loading_states = ["页面/局部加载提示"] if has_loading else []
        empty_states = ["页面/局部空状态"] if has_empty else []
    return {
        "schema": "safehome.function-baseline.v1",
        "captured_at": captured_at,
        "captured_from": "current_worktree",
        "page": page,
        "routes": [f"/{page}"],
        "features": features,
        "buttons": buttons,
        "links": [{"handler": handler} for handler in handlers],
        "navigation_targets": handler_targets(js),
        "data_blocks": data_blocks,
        "api_calls": api_calls,
        "conditional_states": sorted(set(CONDITIONAL_RE.findall(wxml))),
        "error_states": error_states,
        "loading_states": loading_states,
        "empty_states": empty_states,
        "source_files": [str(base.with_suffix(suffix).relative_to(ROOT)).replace("\\", "/") for suffix in (".js", ".json", ".wxml", ".wxss")],
    }


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def git_baseline() -> dict:
    status = git("status", "--short").splitlines()
    return {
        "captured_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "branch": git("branch", "--show-current"),
        "head": git("rev-parse", "HEAD"),
        "recent_commits": git("log", "-10", "--oneline").splitlines(),
        "dirty": bool(status),
        "status_short": status,
        "diff_stat": git("diff", "--stat").splitlines(),
        "baseline_policy": "current_worktree; preserve and avoid all pre-existing modifications",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--function-output", type=Path, default=DEFAULT_FUNCTION_OUTPUT)
    args = parser.parse_args()

    policy = read_json(args.policy)
    participant_pages = [item["page"] for item in policy["pages"] if item["classification"] == "participant"]
    r00 = ROOT / "artifacts" / "convergence" / "R00-baseline"
    r00.mkdir(parents=True, exist_ok=True)
    git_path = r00 / "git-baseline.json"
    if not git_path.exists():
        git_path.write_text(json.dumps(git_baseline(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    captured_at = datetime.now().astimezone().isoformat(timespec="seconds")
    rows = [page_metrics(page) for page in participant_pages]
    add_scores(rows)
    rows.sort(key=lambda row: (-row["density_score"], row["page"]))
    for index, row in enumerate(rows, 1):
        row["rank"] = index

    args.output.mkdir(parents=True, exist_ok=True)
    args.function_output.mkdir(parents=True, exist_ok=True)
    columns = ["rank", "page", "density_score"] + [key for key in rows[0] if key not in {"rank", "page", "density_score"}]
    write_csv(args.output / "pages.csv", rows, columns)
    write_csv(args.output / "text-density.csv", rows, ["rank", "page", "text_density", "visible_literal_chars", "text_node_count", "longest_text_node_chars", "title_explanation_count"])
    write_csv(args.output / "action-density.csv", rows, ["rank", "page", "action_density", "button_count", "tappable_view_count", "action_count", "unique_handler_count", "decision_load", "decision_load_score"])

    duplicate_rows = []
    occurrences: defaultdict[str, set[str]] = defaultdict(set)
    for page in participant_pages:
        for node in literal_text_nodes(read_text((MINI / page).with_suffix(".wxml"))):
            if len(node) >= 8:
                occurrences[node].add(page)
    for text, pages in occurrences.items():
        if len(pages) > 1:
            duplicate_rows.append({"text": text, "page_count": len(pages), "pages": " | ".join(sorted(pages))})
    duplicate_rows.sort(key=lambda item: (-item["page_count"], -len(item["text"]), item["text"]))
    write_csv(args.output / "duplicate-copy.csv", duplicate_rows, ["text", "page_count", "pages"])

    terminology_rows = []
    long_rows = []
    for page in participant_pages:
        wxml = read_text((MINI / page).with_suffix(".wxml"))
        for term in TERMS:
            count = wxml.lower().count(term.lower())
            if count:
                terminology_rows.append({"page": page, "term": term, "count": count})
        for node in literal_text_nodes(wxml):
            if len(node) > 80:
                long_rows.append({"page": page, "chars": len(node), "text": node})
    terminology_rows.sort(key=lambda item: (-item["count"], item["page"], item["term"]))
    long_rows.sort(key=lambda item: (-item["chars"], item["page"]))
    write_csv(args.output / "terminology.csv", terminology_rows, ["page", "term", "count"])
    write_csv(args.output / "long-copy.csv", long_rows, ["page", "chars", "text"])

    summary = {
        "schema": "safehome.participant-information-density.v1",
        "captured_at": captured_at,
        "captured_from": "current_worktree",
        "participant_page_count": len(rows),
        "measurement_scope": "miniprogram pages classified as participant by config/rc0810/miniprogram_page_policy.json",
        "ranking_formula": {
            "text_density": 0.24,
            "action_density": 0.20,
            "visual_density": 0.20,
            "terminology": 0.12,
            "repetition": 0.08,
            "decision_load": 0.16,
        },
        "limitations": [
            "Static source audit; conditional branches are counted together and may not render simultaneously.",
            "Literal copy excludes runtime API content and mustache values.",
            "Scores rank audit priority only; they are not user-quality or clinical-safety scores.",
            "Runtime screenshots, device widths, scroll depth and assistive-technology checks remain pending for R02/R03.",
        ],
        "top_pages": [{key: row[key] for key in ("rank", "page", "density_score", "text_density", "action_density", "visual_density", "terminology", "repetition", "decision_load_score")} for row in rows[:15]],
    }
    (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.function_output / "home.before.json").write_text(json.dumps(function_baseline("pages/home/index", HOME_FEATURES, HOME_BUTTONS, captured_at), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.function_output / "assessment-result.before.json").write_text(json.dumps(function_baseline("pages/assessment-result/index", RESULT_FEATURES, RESULT_BUTTONS, captured_at), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Participant information-density baseline written: {len(rows)} pages; top={rows[0]['page']} ({rows[0]['density_score']})")


if __name__ == "__main__":
    main()
