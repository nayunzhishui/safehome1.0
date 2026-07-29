"""Validate content JSON files against lightweight local schema files."""

import argparse
import hashlib
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTENT_DIR = PROJECT_ROOT / "content"
DEFAULT_SCHEMA_DIR = DEFAULT_CONTENT_DIR / "schemas"

FORBIDDEN_TERMS = [
    "人格障碍",
    "潜意识说明",
    "治疗保证",
    "保证改善",
    "立即治愈",
    "孩子异常",
    "你有病",
    "高危患者",
]

BOUNDARY_TERMS = ["不构成诊断", "不构成临床诊断", "不构成筛查", "非诊断", "不替代心理咨询", "不替代危机干预"]
HIGH_RISK_BLOCK_TERMS = ["高风险", "危机", "安全", "现实支持"]
REVIEW_STATUSES = {"draft", "pending_review", "reviewed", "trial_enabled", "enabled", "disabled", "pilot_draft", "pilot_approved", "paused", "completed"}
LEGACY_ASSESSMENT_ID_PREFIXES = ("worksheet_", "appendix_b_examples_")
SENSITIVE_SCALE_KEYWORDS = (
    "gad",
    "phq",
    "ces-d",
    "cesd",
    "dass",
    "isi",
    "psqi",
    "ghq",
    "epq",
    "bfi",
    "big five",
    "大五人格",
    "焦虑测评",
    "抑郁测评",
    "失眠量表",
    "睡眠质量",
    "anxiety_screening",
    "depression_screening",
    "sleep_health",
    "personality",
)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def is_empty(value) -> bool:
    return value is None or value == "" or value == []


def validate_required_fields(payload: dict, fields: list[str], label: str) -> list[str]:
    errors = []
    for field in fields:
        if field not in payload or is_empty(payload.get(field)):
            errors.append(f"{label}.{field} 缺失或为空")
    return errors


def validate_file(content_dir: Path, schema_path: Path) -> list[str]:
    schema = load_json(schema_path)
    content_file = schema.get("file")
    if not content_file:
        return [f"{schema_path.name}.file 缺失"]

    content_path = content_dir / content_file
    if not content_path.exists():
        return [f"{content_file} 文件不存在"]

    try:
        payload = load_json(content_path)
    except json.JSONDecodeError as exc:
        return [f"{content_file} JSON 解析失败：{exc}"]

    if not isinstance(payload, dict):
        return [f"{content_file} 根节点必须是 object"]

    errors = validate_required_fields(payload, schema.get("root_required", []), content_file)
    for list_schema in schema.get("lists", []):
        field = list_schema.get("field")
        items = payload.get(field)
        if not isinstance(items, list):
            errors.append(f"{content_file}.{field} 必须是数组")
            continue
        if not items:
            errors.append(f"{content_file}.{field} 不能为空")
            continue
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"{content_file}.{field}[{index}] 必须是 object")
                continue
            item_id = item.get("id", index)
            errors.extend(
                validate_required_fields(
                    item,
                    list_schema.get("item_required", []),
                    f"{content_file}.{field}[{item_id}]",
                )
            )
            for nested_field, minimum in list_schema.get("item_list_min_lengths", {}).items():
                value = item.get(nested_field)
                if not isinstance(value, list):
                    errors.append(f"{content_file}.{field}[{item_id}].{nested_field} 必须是数组")
                elif len(value) < int(minimum):
                    errors.append(f"{content_file}.{field}[{item_id}].{nested_field} 至少需要 {minimum} 项")
        seen_ids = set()
        for item in items:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            item_id = item["id"]
            if item_id in seen_ids:
                errors.append(f"{content_file}.{field}[{item_id}].id 重复")
            seen_ids.add(item_id)
    return errors


def iter_strings(value, path: str = ""):
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from iter_strings(item, f"{path}[{index}]")
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from iter_strings(item, f"{path}.{key}" if path else str(key))


def validate_forbidden_terms(filename: str, payload: dict) -> list[str]:
    errors = []
    for path, text in iter_strings(payload):
        for term in FORBIDDEN_TERMS:
            if term in text:
                errors.append(f"{filename}.{path} 含禁用语：{term}")
    return errors


def load_content_or_error(content_dir: Path, filename: str) -> tuple[dict | None, list[str]]:
    path = content_dir / filename
    if not path.exists():
        return None, [f"{filename} 文件不存在"]
    try:
        return load_json(path), []
    except json.JSONDecodeError as exc:
        return None, [f"{filename} JSON 解析失败：{exc}"]


def validate_cross_content_rules(content_dir: Path) -> list[str]:
    errors: list[str] = []
    training_cards, load_errors = load_content_or_error(content_dir, "training_cards.json")
    errors.extend(load_errors)
    feedback_rules, load_errors = load_content_or_error(content_dir, "feedback_rules.json")
    errors.extend(load_errors)
    risk_keywords, load_errors = load_content_or_error(content_dir, "risk_keywords.json")
    errors.extend(load_errors)
    student_profile_rules, load_errors = load_content_or_error(content_dir, "student_profile_rules.json")
    errors.extend(load_errors)
    scales_catalog, load_errors = load_content_or_error(content_dir, "scales_catalog.json")
    errors.extend(load_errors)
    assessment_worksheets, load_errors = load_content_or_error(content_dir, "assessment_worksheets.json")
    errors.extend(load_errors)
    scale_item_drafts, load_errors = load_content_or_error(content_dir, "scale_item_drafts.json")
    errors.extend(load_errors)
    assessment_training_map, load_errors = load_content_or_error(content_dir, "assessment_training_map.json")
    errors.extend(load_errors)
    diary_training_map, load_errors = load_content_or_error(content_dir, "diary_training_map.json")
    errors.extend(load_errors)
    programs, load_errors = load_content_or_error(content_dir, "programs.json")
    errors.extend(load_errors)
    governance_manifest, load_errors = load_content_or_error(content_dir, "content_governance_manifest.json")
    errors.extend(load_errors)
    replay_cases, load_errors = load_content_or_error(content_dir, "synthetic_content_replay_cases.json")
    errors.extend(load_errors)
    ai_qa_governance, load_errors = load_content_or_error(content_dir, "ai_qa_governance.json")
    errors.extend(load_errors)
    ai_qa_safety, load_errors = load_content_or_error(content_dir, "ai_qa_safety_responses.json")
    errors.extend(load_errors)
    ai_qa_suite, load_errors = load_content_or_error(content_dir, "ai_qa_synthetic_safety_suite.json")
    errors.extend(load_errors)

    for filename, payload in [
        ("training_cards.json", training_cards),
        ("feedback_rules.json", feedback_rules),
        ("risk_keywords.json", risk_keywords),
        ("student_profile_rules.json", student_profile_rules),
        ("scales_catalog.json", scales_catalog),
        ("assessment_worksheets.json", assessment_worksheets),
        ("scale_item_drafts.json", scale_item_drafts),
        ("assessment_training_map.json", assessment_training_map),
        ("diary_training_map.json", diary_training_map),
        ("programs.json", programs),
        ("content_governance_manifest.json", governance_manifest),
        ("synthetic_content_replay_cases.json", replay_cases),
        ("ai_qa_governance.json", ai_qa_governance),
        ("ai_qa_safety_responses.json", ai_qa_safety),
    ]:
        if payload:
            errors.extend(validate_forbidden_terms(filename, payload))

    if not training_cards or not feedback_rules or not risk_keywords:
        return errors

    if governance_manifest:
        required = {"filename", "content_types", "source", "source_version", "copyright_status", "age_scope", "audience", "change_summary", "governance_status"}
        for index, source in enumerate(governance_manifest.get("sources", [])):
            missing = sorted(required - set(source))
            if missing:
                errors.append(f"content_governance_manifest.json.sources[{index}] 缺少字段：{','.join(missing)}")
            filename = source.get("filename")
            if filename != "faq.json" and filename and not (content_dir / filename).exists():
                errors.append(f"content_governance_manifest.json.sources[{index}] 指向不存在文件：{filename}")
        if governance_manifest.get("import_policy") != "register_only_never_auto_approve":
            errors.append("content_governance_manifest.json.import_policy 必须禁止导入自动批准")

    if replay_cases:
        if replay_cases.get("contains_real_data") is not False:
            errors.append("synthetic_content_replay_cases.json 必须明确 contains_real_data=false")
        if not replay_cases.get("cases"):
            errors.append("synthetic_content_replay_cases.json.cases 不能为空")

    if ai_qa_governance:
        if ai_qa_governance.get("participant_feature_enabled") is not False:
            errors.append("ai_qa_governance.json.participant_feature_enabled 必须保持 false")
        if ai_qa_governance.get("status") != "blocked_human_review":
            errors.append("ai_qa_governance.json.status 必须为 blocked_human_review")
        decisions = ai_qa_governance.get("decisions") or {}
        required_decisions = {"service_name", "target_population", "allowed_scope", "provider", "data_retention_and_region", "human_on_call", "crisis_referral", "shutdown_owner"}
        missing_decisions = sorted(required_decisions - set(decisions))
        if missing_decisions:
            errors.append(f"ai_qa_governance.json.decisions 缺少：{','.join(missing_decisions)}")
        if any(not str(item.get("status", "")).endswith(("required", "review_required")) for item in decisions.values() if isinstance(item, dict)):
            errors.append("ai_qa_governance.json 未决事项不得伪装为已批准")

    if ai_qa_safety:
        routes = {item.get("route") for item in ai_qa_safety.get("responses", []) if isinstance(item, dict)}
        required_routes = {"risk_fixed", "blocked_scope", "blocked_privacy", "blocked_injection", "no_sources", "postcheck_degraded", "provider_degraded"}
        if ai_qa_safety.get("enabled_for_participants") is not False:
            errors.append("ai_qa_safety_responses.json.enabled_for_participants 必须保持 false")
        if ai_qa_safety.get("review_status") != "draft_requires_psychology_ethics_review":
            errors.append("ai_qa_safety_responses.json 必须保留心理与伦理审核门禁")
        if not required_routes <= routes:
            errors.append(f"ai_qa_safety_responses.json 缺少固定降级路由：{','.join(sorted(required_routes - routes))}")

    if ai_qa_suite:
        cases = ai_qa_suite.get("cases") or []
        thresholds = ai_qa_suite.get("thresholds") or {}
        categories = {item.get("category") for item in cases if isinstance(item, dict)}
        critical_categories = {"diagnosis", "treatment", "crisis", "violence", "abuse", "privacy", "injection", "tool_abuse", "postcheck", "reliability"}
        if ai_qa_suite.get("contains_real_data") is not False:
            errors.append("ai_qa_synthetic_safety_suite.json 必须明确 contains_real_data=false")
        if len(cases) < 20 or not critical_categories <= categories:
            errors.append("ai_qa_synthetic_safety_suite.json 必须覆盖不少于20例及全部关键安全类别")
        if thresholds.get("critical_failures_max") != 0 or thresholds.get("diagnostic_violations_max") != 0:
            errors.append("ai_qa_synthetic_safety_suite.json 关键失败和诊断违规阈值必须为0")
        if float(thresholds.get("citation_coverage_min", 0)) < 1:
            errors.append("ai_qa_synthetic_safety_suite.json 已回答内容引用覆盖阈值必须为100%")

    card_ids = {card.get("id") for card in training_cards.get("cards", []) if isinstance(card, dict)}
    errors.extend(validate_assessment_worksheets(assessment_worksheets))
    errors.extend(validate_scales_catalog_boundaries(scales_catalog))
    errors.extend(validate_profile_models(content_dir, assessment_worksheets, card_ids))
    for card in training_cards.get("cards", []):
        if not isinstance(card, dict):
            continue
        card_id = card.get("id", "unknown")
        tags = card.get("tags", [])
        if len(tags) != len(set(tags)):
            errors.append(f"training_cards.json.cards[{card_id}].tags 不得包含重复值")
        if "..." in json.dumps(card, ensure_ascii=False):
            errors.append(f"training_cards.json.cards[{card_id}] 包含残缺的三个英文句点文本")
        unsuitable_text = " ".join(str(item) for item in card.get("not_suitable_for", []))
        if not any(term in unsuitable_text for term in HIGH_RISK_BLOCK_TERMS):
            errors.append(f"training_cards.json.cards[{card_id}].not_suitable_for 缺少高风险/危机/安全/现实支持边界")

    for rule in feedback_rules.get("rules", []):
        if not isinstance(rule, dict):
            continue
        rule_id = rule.get("id", "unknown")
        for card_id in rule.get("recommended_card_ids", []):
            if card_id not in card_ids:
                errors.append(f"feedback_rules.json.rules[{rule_id}].recommended_card_ids 包含不存在的训练卡：{card_id}")
        if rule.get("risk_level") == "high" and rule.get("recommended_card_ids"):
            errors.append(f"feedback_rules.json.rules[{rule_id}] high 风险规则不得推荐普通训练卡")

    if assessment_training_map:
        errors.extend(
            validate_training_map_rules(
                "assessment_training_map.json",
                assessment_training_map,
                card_ids,
                expected_source_type="assessment",
                require_long_term=True,
            )
        )

    if diary_training_map:
        errors.extend(
            validate_training_map_rules(
                "diary_training_map.json",
                diary_training_map,
                card_ids,
                expected_source_type="diary",
                require_empty_long_term=True,
            )
        )

    if programs:
        worksheet_ids = {
            worksheet.get("id")
            for worksheet in (assessment_worksheets or {}).get("worksheets", [])
            if isinstance(worksheet, dict) and worksheet.get("id")
        }
        errors.extend(validate_programs(programs, card_ids, worksheet_ids))

    for rule in risk_keywords.get("handling_rules", []):
        if not isinstance(rule, dict):
            continue
        if rule.get("risk_level") == "high" and rule.get("allow_recommended_training_cards") is not False:
            errors.append("risk_keywords.json.handling_rules[high].allow_recommended_training_cards 必须为 false")

    feedback_boundary = feedback_rules.get("safety_notes") or feedback_rules.get("boundary_notice") or []
    if not isinstance(feedback_boundary, list):
        feedback_boundary = [str(feedback_boundary)]
    boundary_sources = {
        "feedback_rules.json": " ".join(str(item) for item in feedback_boundary),
        "risk_keywords.json": " ".join(str(item) for item in risk_keywords.get("safety_notes", [])),
    }
    if student_profile_rules:
        boundary_sources["student_profile_rules.json"] = " ".join(str(item) for item in student_profile_rules.get("safety_notes", []))
    for filename, text in boundary_sources.items():
        if not any(term in text for term in BOUNDARY_TERMS):
            errors.append(f"{filename} 风险边界文案需包含“不构成诊断”或“不替代心理咨询/危机干预”的同义表达")

    return errors


def validate_programs(payload: dict, card_ids: set[str], worksheet_ids: set[str]) -> list[str]:
    errors: list[str] = []
    root_boundary = str(payload.get("boundary_notice", ""))
    if not any(term in root_boundary for term in BOUNDARY_TERMS):
        errors.append("programs.json.boundary_notice 需包含非诊断或不替代边界")

    for program in payload.get("programs", []):
        if not isinstance(program, dict):
            continue
        program_id = program.get("id", "unknown")
        if program.get("review_status") not in REVIEW_STATUSES:
            errors.append(f"programs.json.programs[{program_id}].review_status 不在允许枚举中")
        boundary_text = str(program.get("boundary_notice", ""))
        if not any(term in boundary_text for term in BOUNDARY_TERMS):
            errors.append(f"programs.json.programs[{program_id}].boundary_notice 需包含非诊断或不替代边界")
        approval = program.get("approval") or {}
        approval_complete = all(
            isinstance(approval.get(role), dict)
            and approval[role].get("status") == "approved"
            and approval[role].get("reviewer")
            and approval[role].get("reviewed_at")
            and approval[role].get("evidence_path")
            for role in ("research", "psychology", "ethics")
        )
        if program.get("review_status") == "pilot_approved" and not approval_complete:
            errors.append(f"programs.json.programs[{program_id}] 三方签字不完整，不得标记 pilot_approved")
        if program.get("review_status") == "pilot_draft" and approval_complete:
            errors.append(f"programs.json.programs[{program_id}] 三方签字已完整，需由负责人明确决定是否迁移状态")
        for field in ["inclusion_criteria", "exclusion_criteria", "pause_criteria", "exit_criteria", "recommendation_sources"]:
            if not isinstance(program.get(field), list) or not program.get(field):
                errors.append(f"programs.json.programs[{program_id}].{field} 不能为空")
        for card_id in program.get("recommended_card_ids", []):
            if card_id not in card_ids:
                errors.append(f"programs.json.programs[{program_id}].recommended_card_ids 包含不存在的训练卡：{card_id}")
        measurement_plan = program.get("measurement_plan")
        if not isinstance(measurement_plan, dict):
            errors.append(f"programs.json.programs[{program_id}].measurement_plan 缺失或不是 object")
        else:
            if measurement_plan.get("status") not in {"draft_requires_research_review", "pilot_approved"}:
                errors.append(f"programs.json.programs[{program_id}].measurement_plan.status 不在允许枚举中")
            for field in ["baseline_worksheet_ids", "post_worksheet_ids"]:
                references = measurement_plan.get(field)
                if not isinstance(references, list) or not references:
                    errors.append(f"programs.json.programs[{program_id}].measurement_plan.{field} 不能为空")
                    continue
                for worksheet_id in references:
                    if worksheet_id not in worksheet_ids:
                        errors.append(
                            f"programs.json.programs[{program_id}].measurement_plan.{field} 包含不存在的 worksheet：{worksheet_id}"
                        )
            points = measurement_plan.get("measurement_points")
            if not isinstance(points, list) or len(points) < 2:
                errors.append(f"programs.json.programs[{program_id}].measurement_plan.measurement_points 至少需要 2 个时间点")
            elif any(not isinstance(point, dict) or is_empty(point.get("label")) or is_empty(point.get("description")) for point in points):
                errors.append(f"programs.json.programs[{program_id}].measurement_plan.measurement_points 缺少 label 或 description")
            if not isinstance(measurement_plan.get("primary_outcomes"), list) or not measurement_plan.get("primary_outcomes"):
                errors.append(f"programs.json.programs[{program_id}].measurement_plan.primary_outcomes 不能为空")
            if measurement_plan.get("status") != "pilot_approved" and not measurement_plan.get("manual_review_items"):
                errors.append(f"programs.json.programs[{program_id}].measurement_plan 草案必须列出 manual_review_items")
            measurement_boundary = str(measurement_plan.get("boundary_notice", ""))
            if not any(term in measurement_boundary for term in BOUNDARY_TERMS):
                errors.append(f"programs.json.programs[{program_id}].measurement_plan.boundary_notice 需包含非诊断或不替代边界")
        sessions = program.get("sessions", [])
        if not isinstance(sessions, list) or not sessions:
            errors.append(f"programs.json.programs[{program_id}].sessions 不能为空")
            continue
        first_session = sessions[0]
        for field in ["session_no", "title", "objective", "steps", "reflection_questions", "duration_minutes", "disclaimer"]:
            if is_empty(first_session.get(field)):
                errors.append(f"programs.json.programs[{program_id}].sessions[1].{field} 缺失或为空")
        for session in sessions:
            session_no = session.get("session_no", "unknown")
            disclaimer = str(session.get("disclaimer", ""))
            if not any(term in disclaimer for term in BOUNDARY_TERMS):
                errors.append(f"programs.json.programs[{program_id}].sessions[{session_no}].disclaimer 需包含非诊断或不替代边界")
            if not isinstance(session.get("steps"), list) or len(session.get("steps", [])) < 2:
                errors.append(f"programs.json.programs[{program_id}].sessions[{session_no}].steps 至少需要 2 项")
            if not isinstance(session.get("reflection_questions"), list) or len(session.get("reflection_questions", [])) < 2:
                errors.append(f"programs.json.programs[{program_id}].sessions[{session_no}].reflection_questions 至少需要 2 项")
    return errors


def validate_training_map_rules(
    filename: str,
    payload: dict,
    card_ids: set[str],
    *,
    expected_source_type: str,
    require_long_term: bool = False,
    require_empty_long_term: bool = False,
) -> list[str]:
    errors: list[str] = []
    for rule in payload.get("rules", []):
        if not isinstance(rule, dict):
            continue
        rule_id = rule.get("rule_id", "unknown")
        recommended_card_ids = rule.get("recommended_card_ids", [])
        condition = rule.get("trigger_condition", {})
        risk_condition = str(condition.get("risk_level", "")).lower() if isinstance(condition, dict) else ""

        if filename == "assessment_training_map.json":
            if rule.get("recommendation_mode") != "candidate_set":
                errors.append(f"{filename}.rules[{rule_id}].recommendation_mode 必须为 candidate_set")
            if rule.get("selection_policy") != "shared_choice":
                errors.append(f"{filename}.rules[{rule_id}].selection_policy 必须为 shared_choice")
            if rule.get("approval_status") != "draft_requires_psychology_review":
                errors.append(f"{filename}.rules[{rule_id}].approval_status 不得自动标记为已批准")
            if int(rule.get("max_candidates") or 0) not in {2, 3}:
                errors.append(f"{filename}.rules[{rule_id}].max_candidates 只允许 2 或 3")

        if len(recommended_card_ids) > 3:
            errors.append(f"{filename}.rules[{rule_id}].recommended_card_ids 不得超过 3 张训练卡")
        for card_id in recommended_card_ids:
            if card_id not in card_ids:
                errors.append(f"{filename}.rules[{rule_id}].recommended_card_ids 包含不存在的训练卡：{card_id}")
        for role in rule.get("card_roles", []):
            if not isinstance(role, dict):
                errors.append(f"{filename}.rules[{rule_id}].card_roles 必须是 object 数组")
                continue
            role_card_id = role.get("card_id")
            if role_card_id and role_card_id not in recommended_card_ids:
                errors.append(f"{filename}.rules[{rule_id}].card_roles 包含未推荐的训练卡：{role_card_id}")
        if rule.get("source_type") != expected_source_type:
            errors.append(f"{filename}.rules[{rule_id}].source_type 必须为 {expected_source_type}")
        if rule.get("review_status") not in REVIEW_STATUSES:
            errors.append(f"{filename}.rules[{rule_id}].review_status 不在允许枚举中")
        if "high" in risk_condition and recommended_card_ids:
            errors.append(f"{filename}.rules[{rule_id}] high 风险条件不得推荐普通训练卡")
        if not rule.get("reason"):
            errors.append(f"{filename}.rules[{rule_id}].reason 缺失")
        if not rule.get("today_suggestion"):
            errors.append(f"{filename}.rules[{rule_id}].today_suggestion 缺失")
        if not any(term in str(rule.get("not_suitable_when", "")) for term in HIGH_RISK_BLOCK_TERMS):
            errors.append(f"{filename}.rules[{rule_id}].not_suitable_when 缺少高风险/危机/安全/现实支持边界")
        if not any(
            term in str(rule.get("boundary_notice", ""))
            for term in ["不构成诊断", "不构成医学判断", "不构成治疗建议", "不构成治疗方案", "不替代"]
        ):
            errors.append(f"{filename}.rules[{rule_id}].boundary_notice 需包含非诊断或非治疗边界")
        if require_long_term and not rule.get("long_term_suggestion"):
            errors.append(f"{filename}.rules[{rule_id}].long_term_suggestion 缺失，测评推荐需要长期方向")
        if require_empty_long_term and rule.get("long_term_suggestion"):
            errors.append(f"{filename}.rules[{rule_id}].long_term_suggestion 应留空，情绪日记只生成今日建议")
    return errors


def validate_assessment_worksheets(payload: dict | None) -> list[str]:
    if not payload:
        return []

    errors: list[str] = []
    for worksheet in payload.get("worksheets", []):
        if not isinstance(worksheet, dict):
            continue
        worksheet_id = str(worksheet.get("id", ""))
        if worksheet_id.startswith(LEGACY_ASSESSMENT_ID_PREFIXES):
            errors.append(
                f"assessment_worksheets.json.worksheets[{worksheet_id}].id 属于已下线旧版自建工作表，不允许回流到用户端测评内容库"
            )
        if worksheet.get("enabled_for_user") is True:
            text = " ".join(
                str(worksheet.get(field, ""))
                for field in ["boundary_notice", "result_disclaimer", "instructions", "review_note"]
            )
            if not any(term in text for term in BOUNDARY_TERMS):
                errors.append(
                    f"assessment_worksheets.json.worksheets[{worksheet_id}] 已开放但缺少“不构成诊断/筛查”或“不替代”边界"
                )
        if is_sensitive_scale(worksheet):
            if worksheet.get("sensitive_category") in {None, "", "none", False}:
                errors.append(f"assessment_worksheets.json.worksheets[{worksheet_id}].sensitive_category 需标记敏感类别")
            text = " ".join(str(worksheet.get(field, "")) for field in ["boundary_notice", "result_disclaimer"])
            if not any(term in text for term in BOUNDARY_TERMS):
                errors.append(f"assessment_worksheets.json.worksheets[{worksheet_id}] 敏感语义内容缺少非诊断/非筛查边界")
    return errors


def is_sensitive_scale(scale: dict) -> bool:
    haystack = " ".join(
        [
            str(scale.get("id", "")),
            str(scale.get("display_name", "")),
            str(scale.get("theme", "")),
            str(scale.get("sensitive_category", "")),
            str(scale.get("source_folder", "")),
            " ".join(str(item) for item in scale.get("source_files", [])),
        ]
    ).lower()
    return any(keyword.lower() in haystack for keyword in SENSITIVE_SCALE_KEYWORDS)


def validate_scales_catalog_boundaries(payload: dict | None) -> list[str]:
    if not payload:
        return []

    errors: list[str] = []
    for scale in payload.get("scales", []):
        if not isinstance(scale, dict):
            continue
        scale_id = scale.get("id", "unknown")
        text = " ".join(
            str(scale.get(field, ""))
            for field in ["boundary_notice", "result_disclaimer", "notes", "not_open_reason", "exclusion_reason"]
        )
        if scale.get("enabled") is True and not any(term in text for term in BOUNDARY_TERMS):
            errors.append(f"scales_catalog.json.scales[{scale_id}] 已开放但缺少“不构成诊断/筛查”或“不替代”边界")
        if is_sensitive_scale(scale):
            if scale.get("sensitive_category") in {None, "", "none", False}:
                errors.append(f"scales_catalog.json.scales[{scale_id}].sensitive_category 需标记敏感类别")
            if not any(term in text for term in BOUNDARY_TERMS):
                errors.append(f"scales_catalog.json.scales[{scale_id}] 敏感语义量表缺少非诊断/非筛查边界")
    return errors


def _worksheet_question_ids(payload: dict | None) -> dict[str, set[str]]:
    worksheet_questions: dict[str, set[str]] = {}
    if not payload:
        return worksheet_questions
    for worksheet in payload.get("worksheets", []):
        if not isinstance(worksheet, dict) or not worksheet.get("id"):
            continue
        worksheet_questions[str(worksheet["id"])] = {
            str(question.get("id"))
            for question in worksheet.get("questions", [])
            if isinstance(question, dict) and question.get("id")
        }
    return worksheet_questions


def validate_profile_models(
    content_dir: Path,
    assessment_worksheets: dict | None = None,
    card_ids: set[str] | None = None,
) -> list[str]:
    profile_dir = content_dir / "profiles"
    if not profile_dir.exists():
        return []

    errors: list[str] = []
    if assessment_worksheets is None:
        assessment_worksheets, load_errors = load_content_or_error(content_dir, "assessment_worksheets.json")
        errors.extend(load_errors)
    if card_ids is None:
        training_cards, load_errors = load_content_or_error(content_dir, "training_cards.json")
        errors.extend(load_errors)
        card_ids = {
            card.get("id")
            for card in (training_cards or {}).get("cards", [])
            if isinstance(card, dict)
        }
    seen_model_ids: set[str] = set()
    worksheet_questions = _worksheet_question_ids(assessment_worksheets)
    known_card_ids = card_ids or set()
    for path in sorted(profile_dir.glob("*.json")):
        try:
            model = load_json(path)
        except json.JSONDecodeError as exc:
            errors.append(f"profiles/{path.name} JSON 解析失败：{exc}")
            continue
        if model.get("schema_version") != "2026.06-profile-model-v1":
            continue
        model_id = model.get("model_id") or path.stem
        if model_id in seen_model_ids:
            errors.append(f"profiles/{path.name}.model_id 重复：{model_id}")
        seen_model_ids.add(model_id)
        for field in ["model_id", "standard_scale_name", "scale_id", "n_cases", "n_features", "features", "clusters", "boundary_notice"]:
            if is_empty(model.get(field)):
                errors.append(f"profiles/{path.name}.{field} 缺失或为空")
        if not any(term in str(model.get("boundary_notice", "")) for term in BOUNDARY_TERMS):
            errors.append(f"profiles/{path.name}.boundary_notice 缺少非诊断/非筛查边界")
        if model.get("n_cases", 0) < 40:
            errors.append(f"profiles/{path.name}.n_cases 小于 40，不应作为聚类画像模型")
        if model.get("n_features", 0) < 2:
            errors.append(f"profiles/{path.name}.n_features 小于 2，不应作为聚类画像模型")
        manual_review_required = model.get("worksheet_link_status") == "manual_review_required"
        if manual_review_required and is_empty(model.get("worksheet_link_note")):
            errors.append(f"profiles/{path.name}.worksheet_link_note 缺失，人工复核模型必须说明不能自动接入的原因")

        worksheet_id = str(model.get("worksheet_id") or model.get("scale_id") or "")
        linked_question_ids = worksheet_questions.get(worksheet_id)
        if not manual_review_required:
            if not worksheet_id:
                errors.append(f"profiles/{path.name}.worksheet_id 或 scale_id 缺失，无法校验题项映射")
            elif linked_question_ids is None:
                errors.append(f"profiles/{path.name} 找不到对应 assessment_worksheets：{worksheet_id}")

        if not isinstance(model.get("features"), list) or not model["features"]:
            continue
        for index, feature in enumerate(model["features"]):
            if not isinstance(feature, dict):
                errors.append(f"profiles/{path.name}.features[{index}] 必须是 object")
                continue
            for field in ["feature_id", "worksheet_question_id", "mean", "std"]:
                if is_empty(feature.get(field)):
                    errors.append(f"profiles/{path.name}.features[{index}].{field} 缺失或为空")
            question_id = str(feature.get("worksheet_question_id") or "")
            if linked_question_ids is not None and not manual_review_required and question_id not in linked_question_ids:
                errors.append(
                    f"profiles/{path.name}.features[{index}].worksheet_question_id 未在 assessment_worksheets[{worksheet_id}].questions 中找到：{question_id}"
                )
        for index, cluster in enumerate(model.get("clusters", [])):
            if not isinstance(cluster, dict):
                errors.append(f"profiles/{path.name}.clusters[{index}] 必须是 object")
                continue
            for field in ["cluster_id", "profile_name", "n", "percent", "center_z", "pca_centroid", "supportive_explanation"]:
                if is_empty(cluster.get(field)):
                    errors.append(f"profiles/{path.name}.clusters[{index}].{field} 缺失或为空")
            if not any(term in str(cluster.get("supportive_explanation", "")) for term in ["不代表固定标签", "不构成诊断", "支持性"]):
                errors.append(f"profiles/{path.name}.clusters[{index}].supportive_explanation 缺少支持性非标签边界")
            for card_id in cluster.get("recommended_card_ids", []):
                if known_card_ids and card_id not in known_card_ids:
                    errors.append(f"profiles/{path.name}.clusters[{index}].recommended_card_ids 包含不存在的训练卡：{card_id}")
        serialized = json.dumps(model, ensure_ascii=False)
        if "anonymous_row_id" in serialized or "row_000" in serialized:
            errors.append(f"profiles/{path.name} 不应包含逐行匿名样本记录")
        errors.extend(validate_forbidden_terms(f"profiles/{path.name}", model))
    return errors


def validate_emotion_annotation_content(content_dir: Path) -> list[str]:
    errors: list[str] = []
    try:
        ontology = load_json(content_dir / "emotion_annotation_ontology.json")
        examples = load_json(content_dir / "emotion_annotation_examples.json")
        data_policy = load_json(content_dir / "offline_annotation_data_policy.json")
    except (OSError, json.JSONDecodeError) as exc:
        return [f"情绪标注体系不可读取：{exc}"]

    labels = ontology.get("emotion_labels", [])
    codes = [item.get("code") for item in labels]
    required_labels = {
        "anxiety",
        "fear",
        "anger",
        "irritation",
        "sadness",
        "helplessness",
        "guilt",
        "shame",
        "calm",
        "positive",
        "unknown",
    }
    if len(codes) != len(set(codes)) or not required_labels.issubset(set(codes)):
        errors.append("情绪标注体系标签必须唯一并包含全部基础标签和unknown")
    required_label_fields = {
        "code",
        "name",
        "include",
        "exclude",
        "prohibited_interpretations",
    }
    for item in labels:
        if required_label_fields - set(item):
            errors.append(f"情绪标签字段不完整：{item.get('code')}")
        if not item.get("include") or not item.get("exclude") or not item.get(
            "prohibited_interpretations"
        ):
            errors.append(f"情绪标签必须包含纳入、排除和禁用解释：{item.get('code')}")
    mode = ontology.get("annotation_mode", {})
    if mode.get("emotion") != "multi_label" or mode.get("maximum_emotion_labels") != 3:
        errors.append("情绪标注必须采用最多三个标签的多标签规则")
    if mode.get("polarity_status") != ["affirmed", "negated", "uncertain"]:
        errors.append("情绪标注必须区分肯定、否定和不确定")
    intensity = mode.get("intensity_scale", {})
    if intensity.get("min") != 0 or intensity.get("max") != 4 or len(
        intensity.get("anchors", {})
    ) != 5:
        errors.append("情绪强度必须定义0至4的五级锚点")
    safety_cues = ontology.get("safety_cues", [])
    if (
        len(safety_cues) != 1
        or safety_cues[0].get("code") != "crisis_expression"
        or safety_cues[0].get("is_emotion_label") is not False
        or "概率" not in str(safety_cues[0].get("rule", ""))
    ):
        errors.append("安全线索必须与情绪标签分离且不得输出危机概率")
    release = ontology.get("release_boundary", {})
    if (
        release.get("expert_review_required") is not True
        or release.get("automatic_expert_signoff_allowed") is not False
    ):
        errors.append("情绪标注体系必须等待真人专家审查且禁止自动专家签字")
    example_items = examples.get("examples", [])
    counterexamples = examples.get("counterexamples", [])
    if len(example_items) < 12 or len(counterexamples) < 8:
        errors.append("情绪标注体系至少需要12个边界样例和8个反例")
    valid_codes = set(codes)
    for item in example_items:
        if not set(item.get("labels", [])).issubset(valid_codes):
            errors.append(f"情绪标注样例含未登记标签：{item.get('id')}")
        if not 0 <= int(item.get("intensity", -1)) <= 4:
            errors.append(f"情绪标注样例强度越界：{item.get('id')}")
    adjudication = examples.get("adjudication", {})
    if adjudication.get("automatic_adjudication_allowed") is not False:
        errors.append("情绪标注分歧不得自动裁决")
    if data_policy.get("active_data_class") != "synthetic":
        errors.append("真实数据权利未核验前标注数据必须保持synthetic")
    if data_policy.get("real_data_gate", {}).get("allowed") is not False:
        errors.append("真实标注数据入口必须保持关闭")
    if data_policy.get("real_data_gate", {}).get("automatic_approval_allowed") is not False:
        errors.append("标注数据权利和伦理不得自动批准")
    hidden = set(data_policy.get("identity_fields_hidden", []))
    if not {"participant_user_id", "family_id", "wechat_openid", "phone", "email"}.issubset(hidden):
        errors.append("标注工具必须隐藏参与者、家庭和直接联系身份字段")
    split_policy = data_policy.get("split_policy", {})
    if (
        sum(int(split_policy.get(key, 0)) for key in ("train_percent", "validation_percent", "test_percent")) != 100
        or split_policy.get("same_group_cross_split_allowed") is not False
    ):
        errors.append("标注数据分组切分比例必须合计100且禁止同组跨集合")
    annotation_policy = data_policy.get("annotation_policy", {})
    if (
        int(annotation_policy.get("minimum_independent_annotators", 0)) < 2
        or annotation_policy.get("peer_answers_visible_before_submit") is not False
        or annotation_policy.get("model_prediction_visible_before_submit") is not False
        or annotation_policy.get("adjudicator_must_be_independent") is not True
    ):
        errors.append("标注流程必须双人独立、盲标且由独立第三人裁决")
    return errors


def validate_offline_benchmark_content(content_dir: Path) -> list[str]:
    errors: list[str] = []
    filenames = [
        "offline_benchmark_registry.json",
        "offline_benchmark_label_mapping.json",
        "offline_benchmark_annotation_manual.json",
        "synthetic_affect_benchmark_240.json",
        "affect_model_candidate_registry.json",
        "affect_shadow_execution_policy.json",
        "affect_monitoring_policy.json",
        "affect_release_gate_policy.json",
        "network_analysis_policy.json",
        "synthetic_group_network_suite.json",
    ]
    payloads = {}
    for filename in filenames:
        try:
            payloads[filename] = load_json(content_dir / filename)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{filename} 不可读取：{exc}")
    if errors:
        return errors
    registry = payloads["offline_benchmark_registry.json"]
    if registry.get("external_ingest_enabled") is not False or registry.get("production_replacement_allowed") is not False:
        errors.append("offline_benchmark_registry.json 外部摄取和生产替换必须默认关闭")
    seen = set()
    required = {"id", "name", "source_url", "source_version", "language", "platform", "population", "context", "license", "content_rights_status", "sensitivity", "allowed_uses", "prohibited_uses", "ingest_status", "deletion_method"}
    for card in registry.get("cards", []):
        missing = required - set(card)
        if missing:
            errors.append(f"offline_benchmark_registry.json.cards 缺少字段：{sorted(missing)}")
        if card.get("id") in seen:
            errors.append(f"offline_benchmark_registry.json.cards.id 重复：{card.get('id')}")
        seen.add(card.get("id"))
        if card.get("ingest_status", "").startswith("blocked_") and (card.get("local_path") or card.get("artifact_sha256")):
            errors.append(f"{card.get('id')} 权利阻断时不得登记本地工件或哈希")
        if card.get("ingest_status", "").startswith("blocked_") and card.get("allowed_uses") != ["metadata_review_only"]:
            errors.append(f"{card.get('id')} 权利阻断时只允许metadata_review_only")
    synthetic = payloads["synthetic_affect_benchmark_240.json"]
    cases = synthetic.get("cases", [])
    canonical = json.dumps(cases, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    import hashlib
    if synthetic.get("contains_real_data") is not False or len(cases) != 240 or synthetic.get("case_count") != 240:
        errors.append("synthetic_affect_benchmark_240.json 必须明确无真实数据且恰好240例")
    if hashlib.sha256(canonical).hexdigest() != synthetic.get("case_hash"):
        errors.append("synthetic_affect_benchmark_240.json.case_hash 不匹配")
    if synthetic.get("generator_label_is_human_gold") is not False:
        errors.append("synthetic_affect_benchmark_240.json 生成标签不得标为人工金标准")
    manual = payloads["offline_benchmark_annotation_manual.json"]
    if not 200 <= int(manual.get("target_case_count", 0)) <= 500 or int(manual.get("minimum_annotators", 0)) < 2:
        errors.append("offline_benchmark_annotation_manual.json 需200至500例且至少两名标注者")
    if manual.get("status") != "draft_human_annotation_pending":
        errors.append("offline_benchmark_annotation_manual.json 未经人工完成前必须保持draft_human_annotation_pending")
    thresholds = manual.get("agreement_thresholds", {})
    try:
        kappa_threshold = float(thresholds.get("emotion_cohen_kappa", -1))
        valence_gap_threshold = float(thresholds.get("maximum_mean_valence_gap", -1))
        arousal_gap_threshold = float(thresholds.get("maximum_mean_arousal_gap", -1))
        minimum_complete = int(thresholds.get("minimum_complete_cases", 0))
    except (TypeError, ValueError):
        errors.append("offline_benchmark_annotation_manual.json 一致性阈值必须为数值")
    else:
        if not 0 <= kappa_threshold <= 1:
            errors.append("offline_benchmark_annotation_manual.json 情绪kappa阈值必须在0至1")
        if not 0 <= valence_gap_threshold <= 2:
            errors.append("offline_benchmark_annotation_manual.json 效价平均差阈值必须在0至2")
        if not 0 <= arousal_gap_threshold <= 1:
            errors.append("offline_benchmark_annotation_manual.json 唤醒平均差阈值必须在0至1")
        if minimum_complete > int(manual.get("target_case_count", 0)):
            errors.append("offline_benchmark_annotation_manual.json 完整双标案例阈值不得超过目标案例数")
    mapping = payloads["offline_benchmark_label_mapping.json"]
    if "unmapped" not in mapping.get("project_labels", []):
        errors.append("offline_benchmark_label_mapping.json 必须保留unmapped")
    candidates = payloads["affect_model_candidate_registry.json"]
    kinds = [item.get("kind") for item in candidates.get("candidates", [])]
    if kinds != ["rule_lexicon", "linear_calibrated", "chinese_pretrained"]:
        errors.append("情感候选注册表必须依次登记规则、线性和中文预训练候选")
    if candidates.get("production_replacement_allowed") is not False:
        errors.append("情感候选注册表在人工金标准完成前不得允许生产替换")
    pretrained = next(
        (
            item
            for item in candidates.get("candidates", [])
            if item.get("kind") == "chinese_pretrained"
        ),
        {},
    )
    if pretrained.get("execution_status") != "blocked_artifact_and_rights_review":
        errors.append("中文预训练候选在模型制品和许可归档前必须保持阻断")
    if candidates.get("probability_display_policy") != "not_clinical_confidence":
        errors.append("模型分数不得显示为临床置信度")
    shadow_policy = payloads["affect_shadow_execution_policy.json"]
    if (
        shadow_policy.get("allowed_data_classes") != ["synthetic"]
        or shadow_policy.get("participant_effect_allowed") is not False
        or shadow_policy.get("feedback_write_allowed") is not False
        or shadow_policy.get("training_card_write_allowed") is not False
        or shadow_policy.get("raw_text_persistence_allowed") is not False
    ):
        errors.append("情感影子执行必须只读、仅合成且不得影响参与者反馈或训练卡")
    if shadow_policy.get("active_candidate_id") not in {
        item.get("id") for item in candidates.get("candidates", [])
    }:
        errors.append("情感影子执行的活动候选必须存在于模型注册表")
    if set(shadow_policy.get("drift_stop_conditions", [])) != {
        "model_registry_hash_changed",
        "lexicon_hash_changed",
        "threshold_hash_changed",
        "feature_version_changed",
        "dataset_hash_changed",
        "schema_version_changed",
        "code_commit_missing",
    }:
        errors.append("情感影子执行必须在模型、内容、数据、schema或commit漂移时停止")
    monitor_policy = payloads["affect_monitoring_policy.json"]
    required_monitor_metrics = {
        "mean_input_length_delta",
        "label_distribution_jsd",
        "colloquial_style_rate_delta",
        "missing_rate",
        "abstention_rate",
        "maximum_subgroup_error_gap",
        "human_overturn_rate",
        "provider_exception_rate",
    }
    if set(monitor_policy.get("metrics", {})) != required_monitor_metrics:
        errors.append("情感监测必须覆盖长度、标签、语言风格、缺失、弃答、逐组误差、人工推翻和异常")
    if any(
        float(item.get("yellow", -1)) >= float(item.get("red", -1))
        for item in monitor_policy.get("metrics", {}).values()
    ):
        errors.append("情感监测黄线必须低于红线")
    if (
        monitor_policy.get("participant_feedback_dependency") is not False
        or monitor_policy.get("training_card_dependency") is not False
        or monitor_policy.get("red_action") != "disable_model_runtime"
    ):
        errors.append("情感模型停机必须独立于参与者反馈和训练卡核心链路")
    release_policy = payloads["affect_release_gate_policy.json"]
    required_release_gates = {
        "data_rights_approval",
        "annotation_manual_and_double_annotation",
        "independent_test_and_local_validity",
        "abstention_review_and_rollback",
        "non_diagnostic_output_boundary",
        "test_cloud_shadow",
        "accountable_owner_approval",
    }
    if set(release_policy.get("gate_order", [])) != required_release_gates:
        errors.append("情感计算发布门禁必须覆盖权利、标注、效度、弃答复核回滚、输出边界、测试云和负责人")
    if (
        release_policy.get("runtime_activation_allowed") is not False
        or release_policy.get("temporary_showcase_privilege_counts_as_approval") is not False
        or release_policy.get("simulated_agent_counts_as_human_signoff") is not False
    ):
        errors.append("情感计算工程门禁不得激活运行、接受展示越权或模拟签字")
    network_policy = payloads["network_analysis_policy.json"]
    if any(
        network_policy.get(key) is not False
        for key in (
            "participant_visible",
            "individual_metrics_allowed",
            "training_model",
            "causal_inference_allowed",
            "family_quality_inference_allowed",
            "production_group_data_allowed",
        )
    ):
        errors.append("群体网络分析不得开启参与者展示、个体指标、训练、因果或生产真实数据")
    if set(network_policy.get("boundary_variants", [])) != {
        "approved_cohort",
        "observed_nodes",
        "active_nodes",
    }:
        errors.append("群体网络分析必须登记三类边界敏感性")
    network_fixture = payloads["synthetic_group_network_suite.json"]
    fixture_canonical = {
        "nodes": network_fixture.get("nodes", []),
        "windows": network_fixture.get("windows", []),
    }
    fixture_hash = hashlib.sha256(
        json.dumps(
            fixture_canonical,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    if (
        network_fixture.get("contains_real_data") is not False
        or network_fixture.get("data_class") != "synthetic"
        or fixture_hash != network_fixture.get("fixture_hash")
    ):
        errors.append("群体网络合成工件必须明确无真人数据且哈希一致")
    return errors


def validate_therapeutic_assessment_contract(content_dir: Path) -> list[str]:
    errors: list[str] = []
    filename = "therapeutic_assessment_production_contract.json"
    try:
        contract = load_json(content_dir / filename)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{filename} 不可读取：{exc}"]
    expected_sets = {
        "service_levels": {"L0", "L1", "L2", "L3"},
        "competency_levels": {"T1", "T2", "T3"},
        "evidence_kinds": {"O", "P", "H", "U"},
        "five_gates": {
            "minimum_input",
            "permission",
            "source",
            "language",
            "responsibility",
        },
        "separate_dimensions": {
            "service_level",
            "competency_level",
            "object_permission",
            "safety_state",
        },
    }
    for field, expected in expected_sets.items():
        if set(contract.get(field, [])) != expected:
            errors.append(f"{filename}.{field} 与权威契约不一致")
    if (
        contract.get("default_unknown_decision") != "deny"
        or contract.get("legacy_case_readable") is not True
        or contract.get("temporary_showcase_bypass_changes_formal_authorization") is not False
        or contract.get("production_release_approved") is not False
    ):
        errors.append(f"{filename} 必须默认拒绝未知值、兼容旧记录且禁止展示越权和自动发布")
    import hashlib

    source_contracts = contract.get("source_contracts", {})
    if not source_contracts:
        errors.append(f"{filename}.source_contracts 不能为空")
    for source_name, expected_hash in source_contracts.items():
        source_path = content_dir / source_name
        if not source_path.exists():
            errors.append(f"{filename} 指向不存在的来源契约：{source_name}")
            continue
        if hashlib.sha256(source_path.read_bytes()).hexdigest() != expected_hash:
            errors.append(f"{filename} 来源契约哈希漂移：{source_name}")
    queue_filename = "therapeutic_assessment_queue_policy.json"
    try:
        queue_policy = load_json(content_dir / queue_filename)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{queue_filename} 不可读取：{exc}")
        return errors
    required_queue_types = {"review", "information", "feedback", "risk", "supervision"}
    if set(queue_policy.get("queue_types", {})) != required_queue_types:
        errors.append(f"{queue_filename} 必须覆盖复核、补资料、反馈、风险和督导队列")
    if (
        queue_policy.get("temporary_showcase_bypass_changes_write_permission") is not False
        or queue_policy.get("automatic_role_downgrade_allowed") is not False
        or queue_policy.get("production_release_approved") is not False
    ):
        errors.append(f"{queue_filename} 不得接受展示越权、自动降级或自动发布")
    for queue_type, config in queue_policy.get("queue_types", {}).items():
        if (
            not config.get("task_code")
            or config.get("required_competency") not in {"T1", "T2", "T3"}
            or int(config.get("sla_hours", 0)) <= 0
        ):
            errors.append(f"{queue_filename}.{queue_type} 缺少任务、胜任力或SLA")
    publication_filename = "publication_gate_policy.json"
    try:
        publication_policy = load_json(content_dir / publication_filename)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{publication_filename} 不可读取：{exc}")
        return errors
    required_gates = {
        "minimum_input",
        "permission",
        "source",
        "language",
        "responsibility",
    }
    required_channels = {
        "therapeutic_feedback",
        "relationship_report",
        "researcher_message",
        "ai_candidate",
    }
    if set(publication_policy.get("five_gates", [])) != required_gates:
        errors.append(f"{publication_filename} 必须完整登记五道发布门")
    if set(publication_policy.get("channels", {})) != required_channels:
        errors.append(f"{publication_filename} 必须覆盖反馈、AI候选、报告和消息")
    if (
        publication_policy.get("unknown_decision") != "deny"
        or publication_policy.get("failure_mode") != "explain_and_hold"
        or publication_policy.get(
            "temporary_showcase_bypass_changes_write_permission"
        )
        is not False
        or publication_policy.get("rules_or_ai_can_bypass_server_gate") is not False
        or publication_policy.get("production_release_approved") is not False
    ):
        errors.append(f"{publication_filename} 必须失败关闭、可解释保留且禁止绕过")
    release_filename = "therapeutic_assessment_release_gate_policy.json"
    try:
        release_policy = load_json(content_dir / release_filename)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{release_filename} 不可读取：{exc}")
        return errors
    expected_release_gates = {
        "engineering_content",
        "human_evidence",
        "workforce_duty",
        "privacy_recovery",
        "infrastructure_release",
    }
    if set(release_policy.get("gate_order", [])) != expected_release_gates:
        errors.append(f"{release_filename} 必须完整登记五类生产证据门禁")
    if set(release_policy.get("engineering_tasks", [])) != {
        f"T38-F{index:02d}" for index in range(19)
    }:
        errors.append(f"{release_filename} 工程门必须覆盖T38-F00至F18")
    evidence_rules = release_policy.get("evidence_rules", {})
    if (
        evidence_rules.get("production_environment_only") is not True
        or evidence_rules.get("distinct_recorder_and_verifier") is not True
        or evidence_rules.get("artifact_sha256_required") is not True
        or evidence_rules.get("simulation_counts_as_approval") is not False
        or evidence_rules.get("automated_test_counts_as_human_evidence") is not False
        or release_policy.get("production_release_approved") is not False
        or release_policy.get("temporary_showcase_counts_as_permission") is not False
    ):
        errors.append(
            f"{release_filename} 必须限定生产证据、双人核验且禁止模拟签字、展示越权和自动发布"
        )
    adult_filename = "therapeutic_assessment_adult_launch_policy.json"
    try:
        adult_policy = load_json(content_dir / adult_filename)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{adult_filename} 不可读取：{exc}")
        return errors
    if (
        adult_policy.get("schema")
        != "safehome.therapeutic-assessment.adult-launch.v1"
        or adult_policy.get("allowed_levels") != ["L1", "L2"]
        or adult_policy.get("eligible_age_bands") != ["adult"]
        or adult_policy.get("allowed_data_scopes") != ["single_person"]
        or adult_policy.get("production_release_approved") is not False
        or adult_policy.get("temporary_showcase_counts_as_release") is not False
    ):
        errors.append(f"{adult_filename} 必须仅覆盖低风险成人单人L1/L2且不得自动发布")
    if not {
        "AIS",
        "FIS",
        "layer_3",
        "trauma_activation",
        "family_confrontation",
    }.issubset(set(adult_policy.get("excluded_methods", []))):
        errors.append(f"{adult_filename} 缺少高挑战方法排除项")
    if set(adult_policy.get("required_notices", [])) != {
        "waiting_time",
        "withdrawal",
        "privacy",
        "confidentiality_exceptions",
        "complaint_path",
    }:
        errors.append(f"{adult_filename} 必须完整说明等待、退出、隐私、保密例外和投诉")
    child_filename = "therapeutic_assessment_child_policy.json"
    try:
        child_policy = load_json(content_dir / child_filename)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{child_filename} 不可读取：{exc}")
        return errors
    if (
        child_policy.get("schema")
        != "safehome.therapeutic-assessment.child-safeguards.v1"
        or child_policy.get("entry_enabled") is not False
        or child_policy.get("production_release_approved") is not False
        or child_policy.get("guardian_consent_does_not_override_child_refusal")
        is not True
        or child_policy.get("temporary_showcase_counts_as_permission") is not False
    ):
        errors.append(f"{child_filename} 必须保持入口关闭、儿童拒绝优先且禁止展示旁路")
    if set(child_policy.get("source_domains", [])) != {
        "child",
        "guardian",
        "school",
        "professional",
    }:
        errors.append(f"{child_filename} 必须分开儿童、监护人、学校和专业来源")
    if set(child_policy.get("required_external_gates", [])) != {
        "t3_child_competency",
        "ethics_approval",
        "a0_a3_pilot_evidence",
    }:
        errors.append(f"{child_filename} 必须要求T3、伦理和A0-A3试点证据")
    multi_filename = "therapeutic_assessment_multi_party_policy.json"
    try:
        multi_policy = load_json(content_dir / multi_filename)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{multi_filename} 不可读取：{exc}")
        return errors
    if (
        multi_policy.get("schema")
        != "safehome.therapeutic-assessment.multi-party.v1"
        or multi_policy.get("entry_enabled") is not False
        or multi_policy.get("production_release_approved") is not False
        or multi_policy.get("individual_disclosure_joint_default") is not False
        or multi_policy.get("relationship_cycle_must_not_equalize_harm") is not True
        or multi_policy.get("temporary_showcase_counts_as_permission") is not False
    ):
        errors.append(f"{multi_filename} 必须默认关闭、个别资料不共享且不得平均伤害责任")
    if set(multi_policy.get("precheck_signals", [])) != {
        "fear",
        "coercive_control",
        "violence",
        "retaliation_risk",
        "custody_dispute",
        "shared_device_risk",
    }:
        errors.append(f"{multi_filename} 必须完整登记六类共同反馈前安全检查")
    ai_filename = "therapeutic_assessment_ai_assist_policy.json"
    try:
        ai_policy = load_json(content_dir / ai_filename)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{ai_filename} 不可读取：{exc}")
        return errors
    if (
        ai_policy.get("schema") != "safehome.therapeutic-assessment.ai-assist.v1"
        or ai_policy.get("auto_publish") is not False
        or ai_policy.get("may_clear_safety_signal") is not False
        or ai_policy.get("may_create_hypothesis_h") is not False
        or ai_policy.get("may_claim_human_review") is not False
    ):
        errors.append(f"{ai_filename} 必须禁止自动发布、解除安全信号、生成H或冒充真人审核")
    if set(ai_policy.get("five_gates", [])) != {
        "minimum_input",
        "permission",
        "source",
        "language",
        "responsibility",
    }:
        errors.append(f"{ai_filename} 必须完整登记五道门")
    if not {
        "hypothesis_h",
        "assessment_interpretation",
        "minor_feedback",
        "couple_feedback",
        "trauma_feedback",
        "violence_response",
        "self_harm_response",
        "applicability_decision",
        "referral",
        "safety_disposition",
    }.issubset(set(ai_policy.get("human_only_tasks", []))):
        errors.append(f"{ai_filename} 必须完整登记真人专属任务")
    return errors


def validate_therapeutic_method_library(content_dir: Path) -> list[str]:
    errors: list[str] = []
    filename = "therapeutic_assessment_method_library.json"
    try:
        payload = load_json(content_dir / filename)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{filename} 不可读取：{exc}"]
    governance = payload.get("governance") or {}
    if payload.get("schema") != "safehome.therapeutic-assessment.method-library.v1":
        errors.append(f"{filename} schema不兼容")
    if governance.get("required_independent_disciplines") != [
        "research",
        "psychology",
        "ethics",
        "content",
    ]:
        errors.append(f"{filename} 必须经过研究、心理、伦理和内容四专业独立审核")
    if (
        governance.get("automatic_release_allowed") is not False
        or int(governance.get("minimum_distinct_reviewers", 0)) < 2
    ):
        errors.append(f"{filename} 不得自动发布，且必须至少两名独立审核者")
    items = payload.get("items") or []
    ids = [str(item.get("id") or "") for item in items]
    if len(items) < 9 or len(ids) != len(set(ids)) or not all(ids):
        errors.append(f"{filename} 条目不足、缺少id或存在重复id")
    required_types = {
        "service_level_guidance",
        "assessment_question_rubric",
        "evidence_templates",
        "feedback_checklist",
        "written_letter_framework",
        "applicability_checklist",
        "stop_rules",
        "professional_interview_scaffold",
    }
    if not required_types.issubset(
        {str(item.get("artifact_type") or "") for item in items}
    ):
        errors.append(f"{filename} 缺少计划要求的方法制品")
    required_fields = {
        "source",
        "source_version",
        "version",
        "applicable_levels",
        "reviewers",
        "review_status",
        "valid_from",
        "expires_at",
        "disabled_scenarios",
        "access_tier",
        "ordinary_recommendation",
        "body",
    }
    for item in items:
        missing = sorted(required_fields - set(item))
        if missing:
            errors.append(
                f"{filename}:{item.get('id') or 'unknown'} 缺少字段：{','.join(missing)}"
            )
            continue
        if (
            not item.get("source")
            or not item.get("source_version")
            or not item.get("applicable_levels")
            or not isinstance(item.get("reviewers"), list)
            or not item.get("review_status")
            or not item.get("valid_from")
            or not item.get("expires_at")
            or not item.get("disabled_scenarios")
            or not item.get("body")
        ):
            errors.append(f"{filename}:{item.get('id')} 内容治理元数据不能为空")
        if str(item.get("expires_at")) <= str(item.get("valid_from")):
            errors.append(f"{filename}:{item.get('id')} 有效期不正确")
    controlled = {
        item.get("id"): item
        for item in items
        if item.get("id")
        in {"ais_professional_scaffold", "fis_professional_scaffold"}
    }
    if set(controlled) != {
        "ais_professional_scaffold",
        "fis_professional_scaffold",
    } or any(
        item.get("access_tier") != "t3_professional"
        or item.get("ordinary_recommendation") is not False
        for item in controlled.values()
    ):
        errors.append(f"{filename} AIS/FIS只能作为T3受控专业材料")
    return errors


def validate_therapeutic_research_protocol(content_dir: Path) -> list[str]:
    filename = "therapeutic_assessment_research_protocol.json"
    errors: list[str] = []
    try:
        payload = load_json(content_dir / filename)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{filename} 不可读取：{exc}"]
    if payload.get("schema") != "safehome.therapeutic-assessment.research-protocol.v1":
        errors.append(f"{filename} schema不兼容")
    groups = payload.get("metrics") or {}
    if not {"process", "implementation", "harm"}.issubset(groups):
        errors.append(f"{filename} 缺少过程、实施或伤害指标")
        return errors
    required = {
        "id",
        "priority",
        "denominator",
        "timepoint",
        "missing_data",
        "analysis_method",
    }
    all_metrics = [item for group in groups.values() for item in group]
    if not all(required.issubset(item) for item in all_metrics):
        errors.append(f"{filename} 指标缺少预先定义的分母、时间点、缺失或分析方法")
    ids = [str(item.get("id") or "") for item in all_metrics]
    if not all(ids) or len(ids) != len(set(ids)):
        errors.append(f"{filename} 指标id缺失或重复")
    if payload.get("symptom_scales", {}).get("role") != "exploratory_outcome_only":
        errors.append(f"{filename} 症状量表只能作为探索性结局")
    rules = payload.get("analysis_rules") or {}
    if rules.get("satisfaction_may_offset_serious_harm") is not False:
        errors.append(f"{filename} 不得用满意度抵消严重伤害事件")
    policy = payload.get("export_policy") or {}
    if (
        policy.get("default_deidentified") is not True
        or policy.get("minimum_necessary") is not True
        or policy.get("raw_text_in_default_export") is not False
        or not policy.get("allowed_purposes")
    ):
        errors.append(f"{filename} 研究导出必须默认脱敏、最小必要且用途受控")
    return errors


def validate_therapeutic_pilot_evidence(content_dir: Path) -> list[str]:
    filename = "therapeutic_assessment_pilot_evidence_registry.json"
    try:
        payload = load_json(content_dir / filename)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{filename} 不可读取：{exc}"]
    errors: list[str] = []
    if payload.get("schema") != "safehome.therapeutic-assessment.pilot-evidence.v1":
        errors.append(f"{filename} schema不兼容")
    stages = payload.get("stages") or []
    a0 = next((item for item in stages if item.get("id") == "A0"), None)
    if not a0 or len(a0.get("roles") or []) != 5:
        errors.append(f"{filename} A0必须覆盖五类专家职责")
    elif not all(item.get("questions") and item.get("evidence_refs") for item in a0["roles"]):
        errors.append(f"{filename} A0每类职责必须包含问题和证据索引")
    if a0 and (
        a0.get("simulated_role_may_sign") is not False
        or a0.get("automatic_test_may_sign") is not False
        or a0.get("production_release_approved") is not False
    ):
        errors.append(f"{filename} 模拟角色和自动测试不得计作真人签字")
    a1 = next((item for item in stages if item.get("id") == "A1"), None)
    if not a1 or len(a1.get("screen_prompts") or []) != 3 or len(a1.get("coverage_domains") or []) != 7:
        errors.append(f"{filename} A1必须包含逐屏三问和七类理解检查")
    elif (
        a1.get("usability_is_efficacy_research") is not False
        or a1.get("synthetic_interview_may_sign") is not False
        or a1.get("human_interviews_complete") is not False
    ):
        errors.append(f"{filename} A1不得把合成访谈或可用性测试当作真人疗效证据")
    a2 = next((item for item in stages if item.get("id") == "A2"), None)
    if not a2 or len(a2.get("sequence") or []) != 5:
        errors.append(f"{filename} A2必须按五步低风险人工原型顺序执行")
    elif (
        a2.get("system_may_generate_h") is not False
        or a2.get("system_may_publish_feedback") is not False
        or a2.get("case_supervision_required") is not True
        or a2.get("human_supervision_complete") is not False
    ):
        errors.append(f"{filename} A2必须逐例督导且系统不得生成H或发布反馈")
    a3 = next((item for item in stages if item.get("id") == "A3"), None)
    expected_a3_domains = {
        "workflow_state_machine",
        "permission_and_shared_scope",
        "reminders_and_privacy",
        "weak_network_and_recovery",
        "researcher_queue_and_workload",
        "cross_client_consistency",
        "participant_correction_withdrawal_complaint",
    }
    if not a3 or {item.get("id") for item in a3.get("verification_domains") or []} != expected_a3_domains:
        errors.append(f"{filename} A3必须覆盖七类形成性试点验证")
    elif (
        a3.get("real_device_required") is not True
        or a3.get("synthetic_or_automation_may_sign") is not False
        or a3.get("severe_issue_blocks_next_stage") is not True
        or a3.get("formative_pilot_complete") is not False
        or a3.get("human_entry_dependencies_complete") is not False
    ):
        errors.append(f"{filename} A3必须保留真人前置、真机和严重问题阻断")
    a4 = next((item for item in stages if item.get("id") == "A4"), None)
    expected_a4_metrics = {
        "completion_rate",
        "time_to_first_review",
        "revision_rate",
        "queue_load",
        "refusal_or_withdrawal",
        "negative_events",
        "severe_issues",
        "stop_count",
    }
    if not a4 or {item.get("id") for item in a4.get("metrics") or []} != expected_a4_metrics:
        errors.append(f"{filename} A4必须预定义八类安全实施可行性指标")
    elif (
        a4.get("purpose") != "safe_implementation_feasibility_only"
        or a4.get("efficacy_claim_allowed") is not False
        or a4.get("treatment_effect_estimation_allowed") is not False
        or a4.get("symptom_change_claim_allowed") is not False
        or a4.get("severe_issue_blocks_release") is not True
        or a4.get("feasibility_pilot_complete") is not False
    ):
        errors.append(f"{filename} A4不得宣称疗效且严重问题必须阻断发布")
    return errors


def validate_task37_release_execution(content_dir: Path) -> list[str]:
    filename = "task37_release_execution_registry.json"
    try:
        payload = load_json(content_dir / filename)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{filename} 不可读取：{exc}"]
    errors: list[str] = []
    if payload.get("schema") != "safehome.task37.release-execution.v1":
        errors.append(f"{filename} schema不兼容")
        return errors
    r01 = next((item for item in payload.get("stages") or [] if item.get("id") == "R01"), None)
    if not r01 or len(r01.get("probes") or []) < 4 or len(r01.get("worker_checks") or []) < 4:
        errors.append(f"{filename} R01缺少health/ready、worker或监控检查")
    elif (
        r01.get("local_automation_is_test_cloud_evidence") is not False
        or r01.get("test_cloud_execution_complete") is not False
        or r01.get("production_mutation_executed") is not False
        or r01.get("production_release_approved") is not False
        or (r01.get("read_only_fallback") or {}).get("production_promotion_allowed") is not False
    ):
        errors.append(f"{filename} R01不得把本地演练计为测试云或自动晋级生产")
    r02 = next((item for item in payload.get("stages") or [] if item.get("id") == "R02"), None)
    if not r02 or len(r02.get("ordered_steps") or []) < 10:
        errors.append(f"{filename} R02缺少生产迁移、备份、恢复或核验顺序")
    elif (
        r02.get("privacy_tombstone_required") is not True
        or r02.get("checksum_and_row_count_required") is not True
        or r02.get("command_generation_only") is not True
        or r02.get("production_migration_executed") is not False
        or r02.get("production_restore_executed") is not False
        or (r02.get("rollback_policy") or {}).get("drop_tables_automatically") is not False
        or (r02.get("rollback_policy") or {}).get("delete_audit_automatically") is not False
    ):
        errors.append(f"{filename} R02只能生成证据且不得自动破坏数据或审计")
    return errors


def validate_research_methodology_content(content_dir: Path) -> list[str]:
    errors: list[str] = []
    try:
        registry = load_json(content_dir / "research_methodology_registry.json")
        worksheets = load_json(content_dir / "assessment_worksheets.json")
    except (OSError, json.JSONDecodeError) as exc:
        return [f"research_methodology_registry.json 不可读取：{exc}"]

    if registry.get("status") != "draft_before_freeze":
        errors.append("research_methodology_registry.json 未经真人签字必须保持 draft_before_freeze")
    if any(registry.get(key) is not False for key in ("real_outcome_data_accessed", "formal_freeze_allowed", "confirmatory_analysis_allowed")):
        errors.append("研究方法注册表不得标记读取真实结果、正式冻结或允许验证性分析")
    worksheet_ids = {item.get("id") for item in worksheets.get("worksheets", [])}
    measures = registry.get("measures", [])
    measure_ids = {item.get("measure_id") for item in measures}
    if worksheet_ids != measure_ids or len(measures) != len(measure_ids):
        errors.append("研究方法注册表必须且只能登记全部测评工作表")
    nine_point = next((item for item in measures if item.get("measure_id") == "regulatory_focus_relationship_18"), {})
    separation = nine_point.get("score_separation", {})
    if separation.get("raw_scale") != {"min": 1, "max": 9, "field": "raw_scores_json"}:
        errors.append("九点量表必须把1至9原分保存在 raw_scores_json")
    if separation.get("model_input_scale") != {"min": 1, "max": 5, "field": "transformed_scores_json"}:
        errors.append("九点量表的1至5模型输入必须与原分分离")
    if separation.get("raw_values_preserved") is not True or separation.get("transformation_version") != "linear_9_to_5_v1":
        errors.append("九点量表必须保留原值并登记线性转换版本")
    for metric in registry.get("metrics", []):
        if not metric.get("denominator_event") or not metric.get("deduplication") or not metric.get("window"):
            errors.append(f"研究指标缺少分母、去重或时间窗：{metric.get('id')}")
    signatures = registry.get("signature_requirements", [])
    if not signatures or any(item.get("status") != "pending_human_signature" for item in signatures):
        errors.append("研究方法签字项只能保持 pending_human_signature")
    for standard in registry.get("reporting_standards", []):
        if not str(standard.get("official_url", "")).startswith("https://") or standard.get("accessed_on") != "2026-07-20":
            errors.append(f"报告规范缺少已核验来源或访问日期：{standard.get('id')}")
    if int(registry.get("generated_from", {}).get("outcome_rows_read", -1)) != 0:
        errors.append("研究方法注册表生成过程不得读取真实结果行")
    return errors


def validate_security_registry_content(content_dir: Path) -> list[str]:
    errors: list[str] = []
    try:
        registry = load_json(content_dir / "security_privacy_abuse_registry.json")
        contract = load_json(DEFAULT_SCHEMA_DIR.parent.parent / "shared" / "contracts" / "api-contract.json")
    except (OSError, json.JSONDecodeError) as exc:
        return [f"security_privacy_abuse_registry.json 不可读取：{exc}"]
    matrix = registry.get("authorization_matrix", [])
    endpoint_ids = {item.get("operation_id") for item in contract.get("endpoints", [])}
    matrix_ids = {item.get("operation_id") for item in matrix}
    if endpoint_ids != matrix_ids or len(matrix) != len(matrix_ids):
        errors.append("安全授权矩阵必须逐项覆盖当前机器API契约且不得重复")
    required = {"method", "path", "object_type", "action", "object_scope", "allowed_roles", "denied_roles", "idempotency"}
    allowed_actions = {"create", "read", "update", "send", "export", "delete"}
    for item in matrix:
        if required - set(item):
            errors.append(f"安全授权矩阵字段不完整：{item.get('operation_id')}")
        if item.get("action") not in allowed_actions:
            errors.append(f"安全授权矩阵动作无效：{item.get('operation_id')}")
    summary = registry.get("authorization_summary", {})
    if summary.get("formal_permission_acceptance_passed") is not False:
        errors.append("临时展示越权保留期间不得标记正式权限验收通过")
    showcase = registry.get("temporary_showcase_exception", {})
    if showcase.get("enabled") is not True or showcase.get("accepted_for_formal_permission_testing") is not False:
        errors.append("临时展示越权必须显式登记且不得用于正式权限验收")
    if len(registry.get("asset_inventory", [])) < 11:
        errors.append("安全资产清单未覆盖身份、测评、日记、消息、导出、离线、AI和备份")
    if len(registry.get("web_miniprogram_threats", [])) < 9 or len(registry.get("ai_threats", [])) < 8:
        errors.append("Web/小程序或AI威胁模型覆盖不足")
    if registry.get("identity_controls", {}).get("auth_epoch_rotation") is not True:
        errors.append("账号令牌轮换必须由服务端auth_epoch支持")
    return errors


def validate_reliability_registry_content(content_dir: Path) -> list[str]:
    errors: list[str] = []
    try:
        registry = load_json(content_dir / "reliability_release_registry.json")
    except (OSError, json.JSONDecodeError) as exc:
        return [f"reliability_release_registry.json 不可读取：{exc}"]
    if len(registry.get("journeys", [])) != 9:
        errors.append("可靠性注册表必须覆盖九条核心旅程")
    required_trace = {"request_id", "actor_scope", "module", "journey", "outcome", "error_code", "status_code", "latency_ms", "retry_count", "recovered"}
    if set(registry.get("trace_fields", [])) != required_trace:
        errors.append("可靠性追踪字段必须使用脱敏白名单")
    forbidden = {"authorization", "cookie", "password", "token", "request_body", "response_body", "participant_text"}
    if not forbidden.issubset(set(registry.get("sensitive_fields_forbidden", []))):
        errors.append("可靠性注册表未完整禁止秘密值和参与者正文")
    if not {"notification_delivery", "privacy_execution", "ai_evaluation", "offline_benchmark"}.issubset(
        {item.get("job_type") for item in registry.get("job_adapters", [])}
    ):
        errors.append("可靠任务适配器必须覆盖通知、隐私、AI评估和离线基准")
    if len(registry.get("fault_scenarios", [])) != 6:
        errors.append("可靠性固定合成故障场景必须为六类")
    if registry.get("production_slo", {}).get("status") != "pending_test_cloud_observation" or registry.get("production_slo", {}).get("thresholds") is not None:
        errors.append("没有测试云连续观察前不得冻结正式SLO阈值")
    release = registry.get("production_release", {})
    if release.get("approved") is not False or release.get("automatic_signature_allowed") is not False or release.get("temporary_showcase_exception_accepted") is not False:
        errors.append("可靠性注册表不得推断上线决定或接受临时展示越权")
    return errors


def validate_ux_experience_registry_content(content_dir: Path) -> list[str]:
    errors: list[str] = []
    try:
        registry = load_json(content_dir / "ux_experience_registry.json")
    except (OSError, json.JSONDecodeError) as exc:
        return [f"ux_experience_registry.json 不可读取：{exc}"]
    pages = registry.get("pages", [])
    try:
        miniprogram_pages = load_json(PROJECT_ROOT / "apps" / "miniprogram" / "app.json").get("pages", [])
    except (OSError, json.JSONDecodeError) as exc:
        return [f"小程序app.json不可读取：{exc}"]
    if {item.get("path") for item in pages if item.get("platform") == "miniprogram"} != set(miniprogram_pages):
        errors.append("体验注册表必须逐项覆盖当前小程序页面")
    if sum(item.get("platform") == "web" for item in pages) < 35:
        errors.append("体验注册表必须覆盖全部已知Web路由")
    required = {"platform", "path", "title", "workspace", "goal", "primary_action", "data_source", "states", "roles", "sensitivity", "owner", "draft_required"}
    for item in pages:
        missing = required - set(item)
        if missing:
            errors.append(f"体验页面 {item.get('path', '<unknown>')} 缺少字段：{', '.join(sorted(missing))}")
    if registry.get("participant_information_architecture") != ["记录", "练习", "了解自己", "人工支持"]:
        errors.append("参与者信息架构必须保持四个固定入口模型")
    if registry.get("researcher_information_architecture") != ["待处理", "参与者", "内容", "研究/导出", "系统状态"]:
        errors.append("研究者信息架构必须保持五个固定工作区")
    expected_gates = {"touch_target", "contrast", "focus_visible", "accessible_name", "heading_order", "form_association", "horizontal_overflow", "reduced_motion"}
    if set(registry.get("automated_gates", [])) != expected_gates:
        errors.append("体验自动门禁必须完整覆盖八项检查")
    if registry.get("home_layout_guard", {}).get("today_step_before") != "三步开始":
        errors.append("今天的一小步必须保持在三步开始之前")
    return errors


def validate_operations_governance_content(content_dir: Path) -> list[str]:
    errors: list[str] = []
    try:
        registry = load_json(content_dir / "operations_capability_registry.json")
        cards = load_json(content_dir / "operations_asset_cards.json")
        manifest = load_json(content_dir / "operations_release_manifest.json")
        contract = load_json(DEFAULT_SCHEMA_DIR.parent.parent / "shared" / "contracts" / "api-contract.json")
    except (OSError, json.JSONDecodeError) as exc:
        return [f"任务三十四运营治理制品不可读取：{exc}"]
    endpoint_ids = {item.get("operation_id") for item in contract.get("endpoints", [])}
    covered_ids = {operation_id for item in registry.get("capabilities", []) for operation_id in item.get("operation_ids", [])}
    if endpoint_ids != covered_ids:
        errors.append("运营能力注册表必须逐项覆盖当前机器API契约")
    capability_fields = {"intended_use", "owner", "dependencies", "data", "open_roles", "feature_flags", "version", "tests", "rollback", "governance_status"}
    for item in registry.get("capabilities", []):
        if capability_fields - set(item):
            errors.append(f"运营能力登记字段不完整：{item.get('id')}")
    if registry.get("production_release_approved") is not False:
        errors.append("运营能力注册表不得自动标记生产发布批准")
    if registry.get("temporary_showcase_exception", {}).get("formal_permission_acceptance") is not False:
        errors.append("临时展示越权不得用于正式权限验收")
    if registry.get("treatment_assessment", {}).get("real_participant_release_allowed") is not False:
        errors.append("治疗性评估真实参与者发布门禁必须保持关闭")
    card_fields = {"source", "license", "metrics", "bias", "failure_modes", "out_of_domain", "admission_criteria", "disable_criteria"}
    card_types = set()
    for item in cards.get("cards", []):
        card_types.add(item.get("card_type"))
        if card_fields - set(item):
            errors.append(f"运营数据/规则/模型卡字段不完整：{item.get('id')}")
    if not {"dataset", "rule", "model"}.issubset(card_types):
        errors.append("运营卡片必须同时覆盖数据集、规则和模型")
    required_artifact_types = {"content", "rule", "model", "dictionary", "prompt", "knowledge_index"}
    artifact_types = {item.get("artifact_type") for item in manifest.get("artifacts", [])}
    if not required_artifact_types.issubset(artifact_types):
        errors.append("运营发布包未覆盖内容、规则、模型、词典、提示和知识索引")
    for item in manifest.get("artifacts", []):
        relative = str(item.get("path") or "")
        target = content_dir / relative.removeprefix("content/")
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != item.get("sha256"):
            errors.append(f"运营发布制品哈希无效：{relative}")
    return errors


def validate_ai_continuous_quality_content(content_dir: Path) -> list[str]:
    errors: list[str] = []
    try:
        policy = load_json(content_dir / "ai_qa_continuous_quality_policy.json")
        suite = load_json(content_dir / "ai_qa_synthetic_safety_suite.json")
    except (OSError, json.JSONDecodeError) as exc:
        return [f"AI持续质量制品不可读取：{exc}"]
    if policy.get("schema_version") != "safehome.ai-qa-continuous-quality.v1":
        errors.append("AI持续质量策略版本不兼容")
    if policy.get("real_participant_text_allowed") is not False:
        errors.append("AI持续质量评测不得使用真实参与者文本")
    if suite.get("contains_real_data") is not False or suite.get(
        "data_origin"
    ) != "project_authored_synthetic_only":
        errors.append("AI持续质量评测集必须是项目编写的纯合成数据")
    cases = suite.get("cases", [])
    ids = [str(item.get("id") or "") for item in cases]
    if not cases or not all(ids) or len(ids) != len(set(ids)):
        errors.append("AI持续质量评测案例为空、缺少标识或存在重复")
    categories = {str(item.get("category") or "") for item in cases}
    if not set(policy.get("required_categories") or []).issubset(categories):
        errors.append("AI持续质量评测集未覆盖全部必需类别")
    if policy.get("critical_failure_blocks_release") is not True:
        errors.append("AI安全关键漏拦必须阻断发布")
    groups = policy.get("artifact_groups", {})
    for group in ("model_adapter", "prompt", "knowledge", "rules", "suite"):
        paths = groups.get(group)
        if not isinstance(paths, list) or not paths:
            errors.append(f"AI持续质量变更监测组缺失：{group}")
            continue
        for relative_path in paths:
            path = PROJECT_ROOT / str(relative_path)
            if not path.is_file():
                errors.append(f"AI持续质量变更监测制品不存在：{relative_path}")
    return errors


def validate_ai_runtime_policy_content(content_dir: Path) -> list[str]:
    errors: list[str] = []
    try:
        policy = load_json(content_dir / "ai_qa_runtime_policy.json")
    except (OSError, json.JSONDecodeError) as exc:
        return [f"AI运行控制策略不可读取：{exc}"]
    if policy.get("schema_version") != "safehome.ai-qa-runtime-policy.v1":
        errors.append("AI运行控制策略版本不兼容")
    expected_scopes = {"user", "role", "provider", "project"}
    for field in ("budgets_micros_per_day", "rate_limits_per_hour"):
        if set(policy.get(field) or {}) != expected_scopes:
            errors.append(f"AI运行控制策略范围不完整：{field}")
    circuit = policy.get("circuit_breaker", {})
    if (
        int(circuit.get("failure_threshold", 0)) < 1
        or int(circuit.get("cooldown_seconds", 0)) < 1
        or int(circuit.get("half_open_max_probes", 0)) != 1
    ):
        errors.append("AI熔断策略必须包含阈值、冷却和单探针半开")
    retention = policy.get("retention", {})
    if any(
        int(retention.get(key, 0)) < 1
        for key in (
            "session_text_days",
            "deidentified_derived_days",
            "provider_metadata_days",
            "audit_days",
        )
    ):
        errors.append("AI文本、衍生数据、供应商元数据和审计保留期必须分开")
    if policy.get("core_services_unaffected") != [
        "messages",
        "records",
        "human_feedback",
    ]:
        errors.append("AI故障不得影响消息、记录和人工反馈")
    if (
        policy.get("degradation", {}).get(
            "kill_switch_reactivation_via_api"
        )
        is not False
        or policy.get("production_release_approved") is not False
    ):
        errors.append("AI运行策略不得自动恢复kill switch或批准生产发布")
    return errors


def validate_ai_release_policy_content(content_dir: Path) -> list[str]:
    errors: list[str] = []
    try:
        policy = load_json(content_dir / "ai_qa_release_policy.json")
    except (OSError, json.JSONDecodeError) as exc:
        return [f"AI分阶段发布策略不可读取：{exc}"]
    if policy.get("schema_version") != "safehome.ai-qa-release-policy.v1":
        errors.append("AI分阶段发布策略版本不兼容")
    stages = policy.get("stages", [])
    expected_ids = [
        "local_fake",
        "synthetic_real_provider",
        "test_cloud_shadow",
        "researcher_read_only",
        "researcher_editable_candidate",
        "restricted_participant_evaluation",
    ]
    if [item.get("id") for item in stages] != expected_ids:
        errors.append("AI发布阶段缺失或顺序不正确")
    if [item.get("order") for item in stages] != list(range(6)):
        errors.append("AI发布阶段序号必须连续")
    required_triggers = {
        "missing_source",
        "unauthorized_access",
        "incorrect_publication",
        "provider_governance_breach",
        "kill_switch_unavailable",
    }
    if not required_triggers.issubset(
        set(policy.get("immediate_rollback_triggers") or [])
    ):
        errors.append("AI立即回退触发器不完整")
    if (
        policy.get("automatic_advance_allowed") is not False
        or policy.get("simulated_signoffs_counted") is not False
        or policy.get("participant_entry_enabled") is not False
        or policy.get("production_release_approved") is not False
    ):
        errors.append("AI发布策略不得自动晋级、模拟签字或批准参与者入口")
    return errors


def validate_content(content_dir: Path = DEFAULT_CONTENT_DIR, schema_dir: Path = DEFAULT_SCHEMA_DIR) -> list[str]:
    if not schema_dir.exists():
        return [f"schema 目录不存在：{schema_dir}"]

    errors: list[str] = []
    schema_paths = sorted(schema_dir.glob("*.schema.json"))
    if not schema_paths:
        return [f"schema 目录为空：{schema_dir}"]

    for schema_path in schema_paths:
        errors.extend(validate_file(content_dir, schema_path))
    errors.extend(validate_cross_content_rules(content_dir))
    errors.extend(validate_emotion_annotation_content(content_dir))
    errors.extend(validate_offline_benchmark_content(content_dir))
    errors.extend(validate_therapeutic_assessment_contract(content_dir))
    errors.extend(validate_therapeutic_method_library(content_dir))
    errors.extend(validate_therapeutic_research_protocol(content_dir))
    errors.extend(validate_therapeutic_pilot_evidence(content_dir))
    errors.extend(validate_task37_release_execution(content_dir))
    errors.extend(validate_research_methodology_content(content_dir))
    errors.extend(validate_security_registry_content(content_dir))
    errors.extend(validate_reliability_registry_content(content_dir))
    errors.extend(validate_ux_experience_registry_content(content_dir))
    errors.extend(validate_operations_governance_content(content_dir))
    errors.extend(validate_ai_continuous_quality_content(content_dir))
    errors.extend(validate_ai_runtime_policy_content(content_dir))
    errors.extend(validate_ai_release_policy_content(content_dir))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SafeHome content JSON files.")
    parser.add_argument("--content-dir", type=Path, default=DEFAULT_CONTENT_DIR)
    parser.add_argument("--schema-dir", type=Path, default=DEFAULT_SCHEMA_DIR)
    args = parser.parse_args()

    errors = validate_content(args.content_dir, args.schema_dir)
    if errors:
        print("内容校验失败：", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("内容校验通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
