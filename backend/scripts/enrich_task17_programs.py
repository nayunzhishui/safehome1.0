"""Idempotently add Task 17 pilot protocol governance fields."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROGRAMS_PATH = PROJECT_ROOT / "content" / "programs.json"

COMMON = {
    "protocol_version": "2026.07-task17-v1",
    "pause_criteria": ["用户主动选择暂停", "练习中不适明显增加", "出现需要人工核对的风险或安全线索"],
    "exit_criteria": ["用户随时主动退出", "现实安全无法保证", "研究负责人依据已批准方案决定停止"],
    "minimum_dose": {"planned_sessions": 3, "minimum_completed_sessions": 2, "session_interval_days": "1至3天"},
    "completion_definition": "完成至少2节练习、留下每节完成状态，并完成一次阶段复盘；仅浏览页面不计完成。",
    "adverse_response_plan": "记录练习前后0至10分不适、负面体验和暂停原因；高风险或现实安全线索停止普通建议并进入人工复核。",
    "protocol_deviation_rule": "记录跳过、延迟、内容调整和研究者调整原因；不覆盖原版本，不把偏离样本自动写成疗效证据。",
    "recommendation_sources": ["program_default", "user_choice", "researcher_adjusted"],
    "approval": {
        "research": {"status": "pending", "reviewer": "", "reviewed_at": "", "evidence_path": ""},
        "psychology": {"status": "pending", "reviewer": "", "reviewed_at": "", "evidence_path": ""},
        "ethics": {"status": "pending", "reviewer": "", "reviewed_at": "", "evidence_path": ""},
    },
}

PROGRAM_SPECIFIC = {
    "self_compassion_exam_anxiety": {
        "inclusion_criteria": ["用户自主选择参加考试压力支持性练习", "能够阅读并完成短时书写", "当前能够保持基本安全"],
        "exclusion_criteria": ["需要立即危机干预或医疗处理", "书写会明显增加无法承受的不适", "无法理解知情说明或不能自主同意"],
        "neutral_alternative": "用户可跳过负性经历书写，改为记录一次普通学习任务和一个中性支持动作。",
        "primary_process_outcome": "自我支持练习完成与主观帮助度",
        "secondary_outcomes": ["压力线索具体化", "情绪调节练习体验"],
        "safety_gate": "每节允许跳过、改用中性主题或暂停；不要求披露高强度经历。",
    },
    "self_compassion_relationship_growth": {
        "inclusion_criteria": ["用户自主选择关系成长自我观察", "练习可由个人独立完成", "当前关系情境具备基本现实安全"],
        "exclusion_criteria": ["存在暴力、胁迫、跟踪、威胁、明显恐惧或报复风险", "练习可能迫使用户向伴侣披露内容", "需要立即现实保护或危机支持"],
        "primary_process_outcome": "安全前提下的个人表达与边界练习",
        "secondary_outcomes": ["关系事件觉察", "行动意愿与实际尝试"],
        "safety_gate": "命中暴力、胁迫、跟踪、威胁、恐惧或报复线索时停止共同沟通和修复建议，优先现实支持与人工复核。",
        "interpretation_boundary": "关系绘画、隐喻和句子补全只作为用户自述与访谈线索，不自动解释潜意识、关系类型或关系成败。",
    },
    "academic_pressure_sleep_health": {
        "inclusion_criteria": ["用户自主选择学习压力与睡眠习惯支持性练习", "愿意记录低风险作息和学习收尾行为", "当前不存在需要立即医学处理的明显异常"],
        "exclusion_criteria": ["持续严重睡眠困难并伴明显日间功能受损", "疑似呼吸暂停、急性躯体问题或其他需医疗评估情形", "需要立即危机干预或医疗处理"],
        "primary_process_outcome": "学习任务收尾与低风险睡前行为记录",
        "secondary_outcomes": ["学业压力应对", "主观睡眠健康行为线索"],
        "safety_gate": "当前不开放睡眠限制、刺激控制或医学解释；明显健康风险提示咨询合格医疗专业人员。",
        "clinical_boundary": "项目名称固定为睡眠健康促进，不称为CBT-I、失眠治疗或医疗方案；ISI/PSQI未审核前不输出筛查结论。",
    },
}


def main() -> int:
    payload = json.loads(PROGRAMS_PATH.read_text(encoding="utf-8"))
    if payload.get("version") == "2026-07-01-t8-programs-v1":
        payload["version"] = "2026.07-task17-program-protocol-v1"
    for program in payload.get("programs", []):
        for key, value in json.loads(json.dumps(COMMON, ensure_ascii=False)).items():
            program.setdefault(key, value)
        for key, value in PROGRAM_SPECIFIC[program["id"]].items():
            program.setdefault(key, value)
        measurement = program.get("measurement_plan") or {}
        measurement.setdefault("secondary_outcomes", program.get("secondary_outcomes", []))
        measurement.setdefault("measurement_windows", {
            "baseline": "首次练习前7天内",
            "practice": "每节练习完成或跳过时",
            "post": "最后一节后7天内",
            "follow_up": "项目结束后14至28天，是否执行由研究负责人确认",
        })
        measurement.setdefault("missing_data_rule", "保留缺失和退出原因，不用自动填补冒充真实回答；统计处理由冻结分析方案决定。")
        if not any(point.get("key") == "follow_up" for point in measurement.get("measurement_points", [])):
            measurement.setdefault("measurement_points", []).append(
                {"key": "follow_up", "label": "后续回看", "description": "项目结束14至28天后进行可选回看；时间窗和指标仍需研究负责人确认。"}
            )
        program["measurement_plan"] = measurement
        for session in program.get("sessions", []):
            session.setdefault("completion_criteria", "完成至少一个核心步骤，并提交完成、跳过或暂停状态。")
            session.setdefault("stop_rule", "不适明显增加、无法保持基本安全或出现现实风险时停止练习并寻求现实支持。")
    PROGRAMS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Task 17 program protocols enriched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
