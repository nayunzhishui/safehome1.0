"""Build the task 18 screenshot map and governed-release baseline."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
SCREENSHOTS = Path(r"D:\codex\workspace\safehome1.0其他内容\文档图片\改错用图第二")
JSON_OUTPUT = ROOT / "outputs" / "task18_baseline.json"
MD_OUTPUT = ROOT / "docs" / "02_专项进度与验收" / "任务十八基线审计与截图映射_20260711.md"


SCREENSHOT_MAP = {
    "0d75a2c282336fecca694889a4f8dfb.jpg": ("量表填写", "量表题项与统一选项模板核查"),
    "150502d79077d466c3b2d8e1a3171c4.jpg": ("登录", "手机号授权取消后未恢复可用登录"),
    "15d33b91d7a8dc980d80ae9f1a7d51a.jpg": ("项目测试", "项目列表为空"),
    "2d9b4689b67ca8d2544bc9f50200ce7.jpg": ("量表填写", "长量表题项、选项和排版核查"),
    "3115c8c18ebaf7bcf9117251d899562.jpg": ("个性化训练方案", "节奏组件与训练卡重复、位置不稳定"),
    "39c5f3295d1f4ed84222e3e3d1f5b3b.jpg": ("TIPI", "专属指导语与题项核查"),
    "3b655ea0a2a78e4347c98659cdc96d6.jpg": ("登录", "账号密码表单与研究者账号不明确"),
    "3c87f578acda4c4c45a48ae879451e8.jpg": ("即时反馈", "主要情绪、触发点、互动线索和练习位置为占位内容"),
    "3d4c79e692a39e3634373c9685c2674.jpg": ("聚类画像", "散点、图例和雷达标签重叠"),
    "45acb27e398add63114ce22ece35ab3.jpg": ("关系成长仪表盘", "本周记录和关键事件保存链路"),
    "6cedf3f8a0f21620f019a12d920aa08.jpg": ("领悟社会支持", "题目语义与选项模板不匹配"),
    "6ec966db5fee92bff71a0433db45fc6.jpg": ("登录", "微信登录返回暂不可用"),
    "721d3488bae79130b3336d15df3ab61.jpg": ("FMI-12", "题项混入文献和计分说明"),
    "7265611031431fa10510e7a24d4c984.jpg": ("关系成长仪表盘", "保存后加载失败、时间轴未更新"),
    "a8aec34230bbbd970af96d4eb774d23.jpg": ("本周复盘", "多量表维度聚合与内部编码显示"),
    "aec8f43747d33162a106e2244a9b055.jpg": ("一般健康问卷", "第12题混入整段计分说明"),
    "dc5a59eda839226d12980c5fcc6d443.jpg": ("情绪温度计", "补充观察数值被滑轨遮挡"),
    "dcd1c9581568a21d9eff8c44b0ecc65.jpg": ("关系主动性画像", "散点和雷达重叠、训练推荐核查"),
    "e26edbd323714eb1d3bf93107d811d9.jpg": ("生活满意度", "题项混入英文标题和作答说明"),
    "edef811b8d838678888a5cf83840380.jpg": ("自我关怀", "题项混入反向计分说明"),
    "ff0f187f3e853d695fa575c80384a81.jpg": ("登录", "手机号授权取消后只剩账号注册路径"),
}


REQUIREMENTS = [
    "微信、手机号和账号密码登录",
    "研究者正式账号与受控凭据",
    "关系成长本周记录和时间轴",
    "情绪温度计视觉与提交",
    "情绪事件即时反馈数据绑定",
    "全量量表指导语、题项、选项、计分和维度",
    "聚类画像和结果图表",
    "完整测评记录",
    "推荐去重和独立训练记录",
    "暑期试点包",
    "本周多量表多维度汇总",
    "已实现能力受控开放",
]


def load(name: str) -> dict:
    return json.loads((CONTENT / name).read_text(encoding="utf-8"))


def status_counts(items: list[dict], key: str = "review_status") -> dict[str, int]:
    return dict(sorted(Counter(str(item.get(key) or "missing") for item in items).items()))


def audit() -> dict:
    screenshots = sorted(path.name for path in SCREENSHOTS.glob("*.jpg")) if SCREENSHOTS.exists() else []
    worksheets = load("assessment_worksheets.json").get("worksheets", [])
    catalog = load("scales_catalog.json").get("scales", [])
    cards = load("training_cards.json").get("cards", [])
    courses = load("courses.json").get("courses", [])
    programs = load("programs.json").get("programs", [])

    profile_models = []
    for path in sorted((CONTENT / "profiles").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        profile_models.append(
            {
                "file": path.name,
                "model_id": payload.get("model_id") or payload.get("id"),
                "admission_status": payload.get("admission_status") or "missing",
                "interpretation_approval_status": payload.get("interpretation_approval_status") or "missing",
            }
        )

    governed_worksheet_statuses = {"approved", "pilot_ready", "pilot_approved", "production_approved", "enabled", "trial_enabled"}
    worksheet_governance_conflicts = [
        {
            "id": item.get("id"),
            "review_status": item.get("review_status"),
            "source_file": item.get("source_file"),
        }
        for item in worksheets
        if item.get("enabled_for_user") is True and item.get("review_status") not in governed_worksheet_statuses
    ]

    program_release_ready = [
        item.get("id")
        for item in programs
        if item.get("enabled") is True and item.get("review_status") in {"pilot_approved", "production_approved"}
    ]

    return {
        "generated_at": "2026-07-11",
        "screenshot_evidence": {
            "directory": str(SCREENSHOTS),
            "expected_count": len(SCREENSHOT_MAP),
            "actual_count": len(screenshots),
            "missing": sorted(set(SCREENSHOT_MAP) - set(screenshots)),
            "unmapped": sorted(set(screenshots) - set(SCREENSHOT_MAP)),
            "items": [
                {
                    "file": name,
                    "page": SCREENSHOT_MAP[name][0],
                    "finding": SCREENSHOT_MAP[name][1],
                }
                for name in sorted(SCREENSHOT_MAP)
            ],
        },
        "requirements": [{"number": index, "name": name, "status": "planned"} for index, name in enumerate(REQUIREMENTS, 1)],
        "inventory": {
            "miniprogram_pages": len(list((ROOT / "apps" / "miniprogram" / "pages").glob("*/index.js"))),
            "worksheets": {
                "total": len(worksheets),
                "enabled_for_user": sum(item.get("enabled_for_user") is True for item in worksheets),
                "review_statuses": status_counts(worksheets),
                "governance_conflicts": worksheet_governance_conflicts,
            },
            "scale_catalog": {
                "total": len(catalog),
                "enabled": sum(item.get("enabled") is True for item in catalog),
                "review_statuses": status_counts(catalog),
            },
            "training_cards": {
                "total": len(cards),
                "enabled": sum(item.get("enabled", True) is True for item in cards),
                "review_statuses": status_counts(cards),
            },
            "courses": {
                "total": len(courses),
                "enabled": sum(item.get("enabled", True) is True for item in courses),
                "review_statuses": status_counts(courses),
            },
            "programs": {
                "total": len(programs),
                "enabled": sum(item.get("enabled") is True for item in programs),
                "review_statuses": status_counts(programs),
                "release_ready_ids": program_release_ready,
            },
            "profile_models": {
                "total": len(profile_models),
                "admission_statuses": dict(sorted(Counter(item["admission_status"] for item in profile_models).items())),
                "items": profile_models,
            },
        },
        "existing_task18_changes": {
            "script": "backend/scripts/update_task18_assessments.py",
            "test": "backend/tests/test_task18_scale_opening.py",
            "content_files": [
                "content/assessment_worksheets.json",
                "content/scale_item_drafts.json",
                "content/scales_catalog.json",
                "content/assessment_training_map.json",
            ],
            "assessment_service": "backend/services/assessment_execution_service.py",
            "review_note": "这些改动将若干 pilot_review_required 量表设为用户可见，与任务十八受控开放边界存在冲突，必须在 T18-06 逐份来源核对后决定是否保留开放。",
        },
        "release_policy": {
            "open": "治理状态允许、技术链路完整、权限与边界完整、自动测试通过",
            "researcher_only": "研究后台脱敏只读能力或已批准受控工具",
            "keep_hidden": "版权/题项/计分未确认、高风险工具、未批准项目、未经验证的实时判断",
        },
    }


def render_markdown(payload: dict) -> str:
    inventory = payload["inventory"]
    lines = [
        "# 任务十八基线审计与截图映射",
        "",
        "生成日期：2026-07-11",
        "",
        "## 1. 审计结论",
        "",
        f"- 截图：{payload['screenshot_evidence']['actual_count']} / {payload['screenshot_evidence']['expected_count']} 张已映射。",
        f"- 小程序页面：{inventory['miniprogram_pages']} 个。",
        f"- 用户 worksheet：{inventory['worksheets']['total']} 份，其中当前 enabled_for_user={inventory['worksheets']['enabled_for_user']}。",
        f"- 训练卡：{inventory['training_cards']['total']} 张；课程：{inventory['courses']['total']} 门；项目：{inventory['programs']['total']} 个。",
        f"- 当前满足项目正式开放状态的 ID：{', '.join(inventory['programs']['release_ready_ids']) or '无'}。",
        f"- 已启用但治理状态不足的 worksheet：{len(inventory['worksheets']['governance_conflicts'])} 份，必须在 T18-06 逐份复核。",
        "",
        "## 2. 截图映射",
        "",
        "| 文件 | 页面 | 事实问题 |",
        "|---|---|---|",
    ]
    for row in payload["screenshot_evidence"]["items"]:
        lines.append(f"| `{row['file']}` | {row['page']} | {row['finding']} |")

    lines.extend([
        "",
        "## 3. 十二项需求覆盖",
        "",
        "| 编号 | 需求 | 初始状态 |",
        "|---|---|---|",
    ])
    for row in payload["requirements"]:
        lines.append(f"| {row['number']} | {row['name']} | {row['status']} |")

    lines.extend([
        "",
        "## 4. 内容开放状态",
        "",
        "| 内容 | 总数 | 已启用 | 状态分布 |",
        "|---|---:|---:|---|",
        f"| worksheet | {inventory['worksheets']['total']} | {inventory['worksheets']['enabled_for_user']} | `{json.dumps(inventory['worksheets']['review_statuses'], ensure_ascii=False)}` |",
        f"| 量表目录 | {inventory['scale_catalog']['total']} | {inventory['scale_catalog']['enabled']} | `{json.dumps(inventory['scale_catalog']['review_statuses'], ensure_ascii=False)}` |",
        f"| 训练卡 | {inventory['training_cards']['total']} | {inventory['training_cards']['enabled']} | `{json.dumps(inventory['training_cards']['review_statuses'], ensure_ascii=False)}` |",
        f"| 课程 | {inventory['courses']['total']} | {inventory['courses']['enabled']} | `{json.dumps(inventory['courses']['review_statuses'], ensure_ascii=False)}` |",
        f"| 项目 | {inventory['programs']['total']} | {inventory['programs']['enabled']} | `{json.dumps(inventory['programs']['review_statuses'], ensure_ascii=False)}` |",
        "",
        "### 已启用但治理状态不足的 worksheet",
        "",
    ])
    conflicts = inventory["worksheets"]["governance_conflicts"]
    if conflicts:
        lines.extend(f"- `{row['id']}`：`{row['review_status']}`" for row in conflicts)
    else:
        lines.append("- 无。")

    lines.extend([
        "",
        "## 5. 既有任务十八改动审查",
        "",
        f"- {payload['existing_task18_changes']['review_note']}",
        "- 现有脚本、测试、content 和计分服务改动保留在工作区，后续按来源证据逐项验收，不整体回退。",
        "",
        "## 6. 开放规则",
        "",
        f"- 直接开放：{payload['release_policy']['open']}。",
        f"- 研究者受控：{payload['release_policy']['researcher_only']}。",
        f"- 继续隐藏：{payload['release_policy']['keep_hidden']}。",
        "",
        "## 7. 下一步",
        "",
        "T18-00 基线证据完成后进入 T18-01。先建立登录失败的后端和小程序状态测试，再修复微信、手机号和账号密码登录。",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    payload = audit()
    JSON_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    MD_OUTPUT.write_text(render_markdown(payload), encoding="utf-8")
    print(f"json={JSON_OUTPUT}")
    print(f"markdown={MD_OUTPUT}")
    print(f"screenshots={payload['screenshot_evidence']['actual_count']}")
    print(f"worksheet_conflicts={len(payload['inventory']['worksheets']['governance_conflicts'])}")


if __name__ == "__main__":
    main()
