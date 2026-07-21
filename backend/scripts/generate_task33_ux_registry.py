"""Generate the Task 33 page/state coverage and UX governance registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP_JSON = ROOT / "apps" / "miniprogram" / "app.json"
OUTPUT = ROOT / "content" / "ux_experience_registry.json"


PAGE_LABELS = {
    "home": "首页", "login": "登录", "register": "注册", "messages": "消息中心",
    "message-detail": "消息详情", "emergency-guide": "安全支持说明", "emergency-resources": "现实支持资源",
    "getting-started": "三步开始", "thermometer": "情绪温度", "training": "训练中心",
    "training-history": "训练记录", "personalized-plan": "个性化训练方案", "program-list": "项目列表",
    "program-detail": "项目详情", "relationship-pilot": "关系探索试点", "relationship-report": "阶段性报告",
    "relationship-task": "关系探索任务", "relationship-growth": "关系成长记录", "growth-dashboard": "成长仪表盘",
    "relationship-narrative": "关系探索材料", "researcher-dashboard": "研究者仪表盘", "course": "课程",
    "course-detail": "课程详情", "profile": "我的", "settings-detail": "设置详情", "goal-setting": "目标设定",
    "diary-form": "情绪日记", "feedback-result": "支持性反馈", "assessment": "测一测",
    "assessment-history": "测评记录", "assessment-detail": "测评填写", "assessment-result": "测评结果",
    "hot-topics": "支持性案例", "task-detail": "训练任务", "training-card": "训练卡",
    "checkin": "练习打卡", "weekly-report": "本周复盘", "supervision": "人工支持",
    "debug": "调试", "integration-test": "联调测试",
}

MINI_GROUPS = {
    "记录": {"home", "thermometer", "diary-form", "goal-setting", "weekly-report"},
    "练习": {"getting-started", "training", "training-history", "personalized-plan", "task-detail", "training-card", "checkin", "course", "course-detail"},
    "了解自己": {"assessment", "assessment-history", "assessment-detail", "assessment-result", "feedback-result", "program-list", "program-detail", "relationship-pilot", "relationship-report", "relationship-task", "relationship-growth", "growth-dashboard", "relationship-narrative", "hot-topics"},
    "人工支持": {"messages", "message-detail", "supervision", "emergency-guide", "emergency-resources"},
    "账户与系统": {"login", "register", "profile", "settings-detail", "researcher-dashboard", "debug", "integration-test"},
}

WRITE_PAGES = {"login", "register", "thermometer", "goal-setting", "diary-form", "assessment-detail", "relationship-task", "relationship-growth", "checkin", "supervision", "program-detail"}
DRAFT_PAGES = {"goal-setting", "diary-form", "assessment-detail", "relationship-task", "relationship-growth", "checkin", "supervision", "program-detail"}
WEB_DRAFT_PATHS = {"/assessment", "/student/assessment", "/relationship-assessment"}
SENSITIVE_PAGES = {"messages", "message-detail", "thermometer", "assessment-history", "assessment-result", "feedback-result", "relationship-pilot", "relationship-report", "relationship-task", "relationship-growth", "growth-dashboard", "relationship-narrative", "weekly-report", "supervision", "researcher-dashboard"}
RESEARCHER_PAGES = {"researcher-dashboard", "debug", "integration-test"}


WEB_ROUTES = [
    ("/", "项目首页", "public", "公开入口", "low"),
    ("/about-study", "研究说明", "public", "阅读研究边界", "medium"),
    ("/login", "登录", "public", "登录", "medium"),
    ("/register", "注册", "public", "创建账号", "high"),
    ("/privacy", "隐私中心", "participant", "管理隐私申请", "high"),
    ("/assessment", "家长支持性测评", "participant", "填写测评", "high"),
    ("/assessment/report/:id", "家长测评报告", "participant", "查看支持性报告", "high"),
    ("/student", "学生入口", "participant", "了解测评", "medium"),
    ("/student/assessment", "学生支持性测评", "participant", "填写测评", "high"),
    ("/student/report/:id", "学生测评报告", "participant", "查看支持性报告", "high"),
    ("/relationship-assessment", "关系行动方式问卷", "participant", "填写九点问卷", "high"),
    ("/family", "家庭绑定", "participant", "管理家庭关联", "high"),
    ("/dashboard", "研究者总览", "待处理", "进入待处理事项", "high"),
    ("/diaries", "参与者与记录", "参与者", "查看记录", "high"),
    ("/feedback", "反馈审核", "待处理", "审核反馈", "high"),
    ("/supervision", "人工支持工作台", "待处理", "处置支持请求", "high"),
    ("/reviews", "人工复核", "待处理", "处理复核", "high"),
    ("/privacy-requests", "隐私申请", "待处理", "处理隐私申请", "high"),
    ("/goals", "目标管理", "参与者", "查看目标", "high"),
    ("/checkins", "练习记录", "参与者", "查看练习", "high"),
    ("/reports", "周度报告", "参与者", "查看报告", "high"),
    ("/profiles", "支持性画像", "参与者", "查看画像", "high"),
    ("/content/review", "内容审核总览", "内容", "查看审核状态", "medium"),
    ("/content/scales", "量表目录", "内容", "审核量表", "high"),
    ("/content/worksheets", "测评题库", "内容", "管理题库", "high"),
    ("/content/cards", "训练卡", "内容", "管理训练卡", "medium"),
    ("/content/rules", "反馈规则", "内容", "查看规则", "high"),
    ("/ai-sandbox", "AI合成沙盒", "研究/导出", "运行合成评测", "high"),
    ("/research/benchmarks", "离线算法基准", "研究/导出", "查看离线证据", "high"),
    ("/research/methodology", "研究方法冻结准备", "研究/导出", "生成冻结证据", "high"),
    ("/export", "数据导出", "研究/导出", "生成脱敏导出", "critical"),
    ("/security/privacy", "安全与隐私防护", "系统状态", "查看安全状态", "critical"),
    ("/reliability/release", "可靠性与发布证据", "系统状态", "查看可靠性证据", "critical"),
    ("/system/experience", "体验与无障碍", "系统状态", "查看体验门禁", "medium"),
    ("/integration-test", "联调测试", "系统状态", "运行本地联调", "high"),
]


def _group_for(page: str) -> str:
    return next((group for group, pages in MINI_GROUPS.items() if page in pages), "账户与系统")


def _mini_entry(path: str) -> dict:
    page = path.split("/")[1]
    role = "researcher" if page in RESEARCHER_PAGES else "participant"
    is_write = page in WRITE_PAGES
    return {
        "platform": "miniprogram",
        "path": path,
        "title": PAGE_LABELS.get(page, page),
        "workspace": _group_for(page),
        "goal": f"完成{PAGE_LABELS.get(page, page)}的单一主要任务",
        "primary_action": "保存并继续" if is_write else "查看或继续",
        "data_source": "local_draft_and_api" if is_write else "api_or_local_state",
        "states": ["loading", "empty", "error", "retry", "success", "permission_denied"],
        "roles": [role] if role == "researcher" else ["parent", "student"],
        "sensitivity": "high" if page in SENSITIVE_PAGES else "medium" if is_write else "low",
        "owner": "participant_experience" if role != "researcher" else "research_operations",
        "draft_required": page in DRAFT_PAGES,
    }


def build_registry() -> dict:
    app = json.loads(APP_JSON.read_text(encoding="utf-8"))
    mini_pages = [_mini_entry(path) for path in app["pages"]]
    web_pages = [
        {
            "platform": "web", "path": path, "title": title, "workspace": workspace,
            "goal": f"完成{title}的主要任务", "primary_action": action,
            "data_source": "local_draft_and_api" if path in WEB_DRAFT_PATHS else "safehome_api", "states": ["loading", "empty", "error", "retry", "success", "permission_denied"],
            "roles": ["public"] if workspace == "public" else (["parent", "student"] if workspace == "participant" else ["researcher", "supervisor", "admin"]),
            "sensitivity": sensitivity, "owner": "public_experience" if workspace == "public" else "research_operations",
            "draft_required": path in WEB_DRAFT_PATHS,
        }
        for path, title, workspace, action, sensitivity in WEB_ROUTES
    ]
    return {
        "version": "2026.07-task33-v1",
        "status": "engineering_complete_local_external_validation_pending",
        "participant_information_architecture": ["记录", "练习", "了解自己", "人工支持"],
        "researcher_information_architecture": ["待处理", "参与者", "内容", "研究/导出", "系统状态"],
        "home_layout_guard": {"preserve_existing_blocks": True, "today_step_after": "测一测/情绪日记", "today_step_before": "三步开始"},
        "design_tokens": {
            "color": ["canvas", "surface", "ink", "muted", "primary", "primary_deep", "warning", "danger", "line", "focus"],
            "type": ["display", "title", "body", "caption", "data"],
            "space": ["xs", "sm", "md", "lg", "xl"],
            "radius": ["sm", "md", "lg", "pill"],
            "patterns": ["primary_task", "state_panel", "feedback_evaluation", "sensitive_notice", "form", "table", "timeline", "chart"],
        },
        "automated_gates": ["touch_target", "contrast", "focus_visible", "accessible_name", "heading_order", "form_association", "horizontal_overflow", "reduced_motion"],
        "form_resilience": ["draft_timestamp", "save_status", "duplicate_submit_guard", "leave_prompt", "restore_entry", "slow_loading_state", "retry_without_reentry"],
        "pages": mini_pages + web_pages,
        "external_gates": [
            {"gate": "large_text", "status": "pending_human_device_evidence"},
            {"gate": "screen_reader", "status": "pending_human_device_evidence"},
            {"gate": "wechat_embedded_browser", "status": "pending_human_device_evidence"},
            {"gate": "android_ios", "status": "pending_human_device_evidence"},
            {"gate": "formative_cognitive_interviews", "status": "pending_human_research_evidence"},
        ],
        "boundary_notice": "自动检查只能发现部分体验问题，不能替代大字体、读屏、真机和真人认知访谈，也不构成发布批准。",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = json.dumps(build_registry(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != expected:
            raise SystemExit("Task 33 UX registry is stale; regenerate it")
        print("Task 33 UX registry check passed")
        return 0
    OUTPUT.write_text(expected, encoding="utf-8")
    print(f"wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
