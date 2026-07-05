"""Validate content JSON files against lightweight local schema files."""

import argparse
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
REVIEW_STATUSES = {"draft", "pending_review", "reviewed", "trial_enabled", "enabled", "disabled", "pilot_draft"}
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
    ]:
        if payload:
            errors.extend(validate_forbidden_terms(filename, payload))

    if not training_cards or not feedback_rules or not risk_keywords:
        return errors

    card_ids = {card.get("id") for card in training_cards.get("cards", []) if isinstance(card, dict)}
    errors.extend(validate_assessment_worksheets(assessment_worksheets))
    errors.extend(validate_scales_catalog_boundaries(scales_catalog))
    errors.extend(validate_profile_models(content_dir, assessment_worksheets, card_ids))
    for card in training_cards.get("cards", []):
        if not isinstance(card, dict):
            continue
        card_id = card.get("id", "unknown")
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
        errors.extend(validate_programs(programs, card_ids))

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


def validate_programs(payload: dict, card_ids: set[str]) -> list[str]:
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
        for card_id in program.get("recommended_card_ids", []):
            if card_id not in card_ids:
                errors.append(f"programs.json.programs[{program_id}].recommended_card_ids 包含不存在的训练卡：{card_id}")
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
