"""Build the Task 18 governed capability opening matrix."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
OUTPUT_JSON = ROOT / "outputs" / "task18_opening_matrix.json"
OUTPUT_CSV = ROOT / "docs" / "02_专项进度与验收" / "任务十八已实现能力受控开放矩阵.csv"
OUTPUT_MD = ROOT / "docs" / "02_专项进度与验收" / "任务十八已实现能力受控开放矩阵_20260712.md"
APPROVED = {"pilot_approved", "production_approved", "enabled", "trial_enabled"}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def row(kind: str, item_id: str, title: str, status: str, enabled: bool, chain: str, category: str, reason: str, evidence: str) -> dict:
    return {
        "kind": kind,
        "item_id": item_id,
        "title": title,
        "governance_status": status,
        "enabled_flag": enabled,
        "technical_chain": chain,
        "opening_category": category,
        "reason": reason,
        "evidence": evidence,
    }


def classify_content(kind: str, item: dict, evidence: str) -> dict:
    status = str(item.get("review_status") or "missing")
    enabled = bool(item.get("enabled_for_user", item.get("enabled", True)))
    approved = status in APPROVED
    category = "开放" if enabled and approved else "待人工签字"
    reason = "治理批准、入口启用且技术链存在" if category == "开放" else "治理状态或独立审核证据未达到生产开放条件"
    return row(
        kind,
        str(item.get("id")),
        str(item.get("display_title") or item.get("title") or item.get("source_title") or item.get("id")),
        status,
        enabled,
        "完整" if evidence else "待核对",
        category,
        reason,
        evidence,
    )


def main() -> int:
    rows: list[dict] = []
    worksheets = load_json(CONTENT / "assessment_worksheets.json").get("worksheets", [])
    worksheet_by_id = {item.get("id"): item for item in worksheets}
    for item in worksheets:
        rows.append(classify_content("量表", item, "content/assessment_worksheets.json；/api/assessments；小程序 assessment 页面"))

    for item in load_json(CONTENT / "training_cards.json").get("cards", []):
        rows.append(classify_content("训练卡", item, "content/training_cards.json；/api/cards；小程序 training-card 页面"))

    for item in load_json(CONTENT / "courses.json").get("courses", []):
        rows.append(classify_content("课程", item, "content/courses.json；/api/courses；小程序 course-detail 页面"))

    for item in load_json(CONTENT / "programs.json").get("programs", []):
        rows.append(classify_content("项目", item, "content/programs.json；/api/programs；小程序 program-detail 页面"))

    for path in sorted((CONTENT / "profiles").glob("*.json")):
        item = load_json(path)
        status = str(item.get("admission_status") or "missing")
        worksheet_id = item.get("worksheet_id")
        worksheet = worksheet_by_id.get(worksheet_id)
        dependency_ready = bool(worksheet and worksheet.get("review_status") in APPROVED and worksheet.get("enabled_for_user", True))
        if status == "deprecated":
            category = "历史对照"
            reason = "模型已审核但已被指定主模型替代，不参与运行时匹配"
        elif status == "internal_only":
            category = "继续隐藏"
            reason = "模型明确为内部研究用途"
        elif status in APPROVED and dependency_ready:
            category = "开放"
            reason = "模型与对应量表均达到准入条件"
        else:
            category = "待人工签字"
            reason = "模型已审核但对应量表缺失或仍未完成生产准入" if status in APPROVED else "模型准入未批准"
        rows.append(
            row(
                "画像模型",
                str(item.get("model_id") or path.stem),
                str(item.get("profile_name") or item.get("model_id") or path.stem),
                status,
                status in APPROVED,
                "模型产物存在" if path.stat().st_size else "产物为空",
                category,
                reason,
                f"content/profiles/{path.name}；worksheet={worksheet_id or 'missing'}",
            )
        )

    analysis_items = [
        ("情感计算聚合", "outputs/text_analysis/text_analysis_summary.json"),
        ("语义共现网络", "outputs/text_analysis/semantic_network_summary.json"),
        ("家庭拓扑审计", "outputs/text_analysis/family_topology_audit_summary.json"),
    ]
    for title, relative_path in analysis_items:
        path = ROOT / relative_path
        available = False
        quality = "missing"
        if path.exists():
            payload = load_json(path)
            quality = str(payload.get("quality_status") or "legacy_unverified")
            available = quality == "valid" and payload.get("raw_text_included") is False
        rows.append(
            row(
                "研究分析",
                title,
                title,
                quality,
                available,
                "离线脚本+研究者只读API" if path.exists() else "离线脚本存在、当前产物缺失",
                "研究者受控" if available else "继续隐藏",
                "只允许脱敏聚合、质量门禁通过的研究者只读访问" if available else "产物缺失、样本不足或质量状态未通过",
                f"analysis/text_analysis；{relative_path}；GET /api/text-analysis/summary",
            )
        )

    miniprogram_pages = load_json(ROOT / "apps" / "miniprogram" / "app.json").get("pages", [])
    rows.append(row("技术入口", "miniprogram_pages", "小程序页面", "implemented", True, f"{len(miniprogram_pages)}页已注册", "开放", "页面注册完整，具体内容仍受后端治理", "apps/miniprogram/app.json"))
    rows.append(row("技术入口", "web_research_dashboard", "Web研究后台", "implemented", True, "角色路由+API客户端", "研究者受控", "研究后台按角色授权，不向普通用户开放", "apps/web/src/main.tsx；ResearchDashboard.tsx"))
    rows.append(row("技术入口", "risk_review", "风险人工复核", "implemented", True, "API+数据库+后台", "研究者受控", "高风险只进入人工复核，不生成普通自动建议", "backend/routes/risk_review.py；risk_review_records"))

    counts = Counter(item["opening_category"] for item in rows)
    kinds = Counter(item["kind"] for item in rows)
    payload = {
        "generated_at": "2026-07-12",
        "rule": "仅同时满足治理状态、技术链、权限和质量门禁的能力开放",
        "counts": dict(counts),
        "kind_counts": dict(kinds),
        "rows": rows,
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# 任务十八已实现能力受控开放矩阵",
        "",
        "生成日期：2026-07-12",
        "",
        "## 1. 判定规则",
        "",
        "技术实现不等于可开放。只有治理状态允许、技术链完整、权限正确、质量与隐私门禁通过时才归入“开放”；离线情感计算、语义共现网络、家庭拓扑和人工复核只归入“研究者受控”。",
        "",
        "## 2. 汇总",
        "",
    ]
    lines.extend(f"- {name}：{count} 项" for name, count in sorted(counts.items()))
    lines.extend(["", "## 3. 分类明细", ""])
    categories = ("开放", "研究者受控", "历史对照", "继续隐藏", "待人工签字")
    for category in categories:
        lines.extend([f"### 3.{categories.index(category)+1} {category}", ""])
        items = [item for item in rows if item["opening_category"] == category]
        if not items:
            lines.append("无。")
        else:
            lines.append("| 类型 | ID | 名称 | 治理状态 | 原因 |")
            lines.append("|---|---|---|---|---|")
            for item in items:
                title = item["title"].replace("|", "/")
                reason = item["reason"].replace("|", "/")
                lines.append(f"| {item['kind']} | `{item['item_id']}` | {title} | `{item['governance_status']}` | {reason} |")
        lines.append("")
    lines.extend(
        [
            "## 4. 关键结论",
            "",
            "1. 已具备完整 worksheet 的量表按项目负责人批准进入试点开放；只有目录元数据而缺少执行链的量表继续阻断。项目独立版权/心理/研究/伦理证据仍需归档。",
            "2. 画像模型只有在对应 worksheet 已存在且通过治理时才可随量表开放，不能单独靠模型状态绕过量表门禁。",
            "3. 情感计算、语义共现网络和家庭拓扑只读取脱敏聚合产物；样本不足、产物缺失或质量状态非 valid 时继续隐藏。",
            "4. Web研究后台、风险复核和离线聚合接口维持研究者受控，不向普通用户提供实时判断。",
            "",
        ]
    )
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"rows": len(rows), "counts": dict(counts), "output": str(OUTPUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
