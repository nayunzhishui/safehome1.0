"""Generate the machine-checkable T30 methodology registry without reading outcomes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTENT_ROOT = PROJECT_ROOT / "content"
DEFAULT_OUTPUT = CONTENT_ROOT / "research_methodology_registry.json"


PRODUCT_LINES = [
    {
        "id": "participant_journey",
        "design": "feasibility_observational_candidate",
        "primary_question": "参与者能否找到并完成唯一下一步，并在中断或错误后恢复？",
        "secondary_questions": ["哪些流程状态最常阻断下一步？", "转人工是否被正确触发并到达？"],
        "population": "eligible_consented_participants_pending_definition",
        "time_zero": "first_exposure_to_journey_card_pending_freeze",
        "followup_window": "single_session_and_followup_window_pending_freeze",
        "exposure": "journey_card_and_existing_entry_points",
        "primary_outcome": "unique_primary_outcome_pending_freeze",
        "candidate_estimands": ["completion_proportion", "median_time_to_completion", "recovery_proportion"],
        "comparator": "historical_or_concurrent_comparator_pending_freeze",
        "allowed_interpretation": "可用性、流程摩擦和错误恢复",
        "prohibited_interpretation": "完成更多等于心理改善或干预有效",
    },
    {
        "id": "training_recommendation",
        "design": "acceptability_feasibility_candidate",
        "primary_question": "参与者能否理解、选择、替换并完成推荐训练卡？",
        "secondary_questions": ["不适和跳过发生在哪个分母层级？", "替换后是否仍能完成低负担练习？"],
        "population": "low_risk_pilot_population_pending_freeze",
        "time_zero": "first_recommendation_impression",
        "followup_window": "recommendation_to_checkin_window_pending_freeze",
        "exposure": "governed_recommendation_and_alternative_card",
        "primary_outcome": "unique_primary_outcome_pending_freeze",
        "candidate_estimands": ["selection_per_impression", "completion_per_selection", "discomfort_per_impression"],
        "comparator": "recommendation_strategy_or_descriptive_reference_pending_freeze",
        "allowed_interpretation": "推荐可理解性、可接受性和流程负担",
        "prohibited_interpretation": "点击率、完成率或帮助度等于疗效",
    },
    {
        "id": "supportive_feedback",
        "design": "collaborative_feedback_observational_candidate",
        "primary_question": "参与者能否理解并纠正支持性反馈，且不适能否进入人工复核？",
        "secondary_questions": ["反馈版本修订是否保留历史？", "人工升级等待时间是否可接受？"],
        "population": "feedback_recipients_pending_definition",
        "time_zero": "first_feedback_view",
        "followup_window": "feedback_to_review_resolution_pending_freeze",
        "exposure": "versioned_supportive_feedback_with_four_option_correction",
        "primary_outcome": "unique_primary_outcome_pending_freeze",
        "candidate_estimands": ["correction_distribution", "review_resolution_time", "revision_proportion"],
        "comparator": "descriptive_reference_pending_freeze",
        "allowed_interpretation": "反馈的协作性、可纠正性和人工衔接",
        "prohibited_interpretation": "选择符合等于客观诊断正确",
    },
    {
        "id": "relationship_pilot",
        "design": "feasibility_longitudinal_candidate",
        "primary_question": "关系报告与阶段反馈能否被理解、共同核对并支持后续记录？",
        "secondary_questions": ["退出、撤回和未授权事件是否被正确处理？", "重复测量是否具有版本与时间可比性？"],
        "population": "relationship_pilot_participants_pending_freeze",
        "time_zero": "baseline_assessment_or_enrollment_pending_freeze",
        "followup_window": "primary_wave_and_interval_pending_freeze",
        "exposure": "researcher_confirmed_report_and_stage_feedback",
        "primary_outcome": "unique_primary_outcome_pending_freeze",
        "candidate_estimands": ["report_confirmation_proportion", "followup_completion", "within_person_descriptive_change"],
        "comparator": "within_person_or_control_condition_pending_freeze",
        "allowed_interpretation": "流程可行性、接受度和阶段性描述",
        "prohibited_interpretation": "无对照变化等于关系改善或因果效果",
    },
    {
        "id": "controlled_ai_qa",
        "design": "synthetic_preclinical_only",
        "primary_question": "固定合成集上是否能安全拒答并提供批准来源？",
        "secondary_questions": ["过度拒答、延迟和成本是否在候选门槛内？", "严重失败是否正确进入停用与人工复核？"],
        "population": "synthetic_cases_only",
        "time_zero": "evaluation_run_start",
        "followup_window": "single_offline_run",
        "exposure": "fake_provider_and_approved_knowledge",
        "primary_outcome": "severe_failure_count_zero_engineering_gate",
        "candidate_estimands": ["severe_failure_rate", "correct_refusal_rate", "source_coverage"],
        "comparator": "prompt_or_model_version_comparison_after_governance",
        "allowed_interpretation": "是否可申请进入下一内部评审门",
        "prohibited_interpretation": "离线准确率等于真实帮助、临床安全或治疗效果",
    },
]


METRICS = [
    {"id": "journey_completion", "family": "process", "numerator_event": "primary_action_completed", "denominator_event": "eligible_primary_action_exposed", "deduplication": "user_id+journey_date+action_id", "window": "same_journey_date", "exceptions": ["technical_failure", "withdrew_research_consent"], "interpretation": "流程完成比例"},
    {"id": "journey_recovery", "family": "process", "numerator_event": "action_completed_after_recovery", "denominator_event": "recoverable_interruption", "deduplication": "user_id+interruption_id", "window": "pending_freeze", "exceptions": ["safety_routed"], "interpretation": "中断恢复比例"},
    {"id": "feedback_discomfort", "family": "safety", "numerator_event": "evaluation_uncomfortable", "denominator_event": "feedback_seen", "deduplication": "user_id+source_id+content_version", "window": "first_active_evaluation", "exceptions": [], "interpretation": "不适信号，不等于风险诊断"},
    {"id": "human_escalation_delay", "family": "safety", "numerator_event": "resolved_escalations", "denominator_event": "escalations_created", "deduplication": "work_item_id", "window": "created_at_to_closed_at", "exceptions": ["participant_cancelled"], "interpretation": "人工衔接可靠性"},
    {"id": "card_selection", "family": "recommendation", "numerator_event": "card_selected", "denominator_event": "recommendation_impression", "deduplication": "user_id+recommendation_id+card_id", "window": "recommendation_version", "exceptions": [], "interpretation": "推荐被选择比例"},
    {"id": "card_completion", "family": "recommendation", "numerator_event": "checkin_completed", "denominator_event": "card_selected", "deduplication": "user_id+assignment_id+due_date", "window": "assignment_window", "exceptions": ["assignment_cancelled"], "interpretation": "选择后的练习完成比例"},
    {"id": "ai_severe_failure", "family": "ai_safety", "numerator_event": "severity_high_failure", "denominator_event": "synthetic_case_run", "deduplication": "evaluation_run_id+case_id", "window": "single_evaluation_run", "exceptions": [], "interpretation": "工程安全门，不等于现场安全"},
    {"id": "ai_source_coverage", "family": "ai_quality", "numerator_event": "answer_with_approved_source", "denominator_event": "answer_expected_case", "deduplication": "evaluation_run_id+case_id", "window": "single_evaluation_run", "exceptions": ["correct_refusal_expected"], "interpretation": "批准来源覆盖"},
]


def _numeric_options(question: dict) -> list[float]:
    values = []
    for option in question.get("options", []):
        score = option.get("score")
        if isinstance(score, (int, float)) and not isinstance(score, bool):
            values.append(float(score))
    return values


def _measure_entry(worksheet: dict) -> dict:
    questions = worksheet.get("questions", [])
    numeric = [_numeric_options(question) for question in questions]
    numeric = [values for values in numeric if values]
    ranges = sorted({(min(values), max(values), len(values)) for values in numeric})
    reverse_items = [question.get("id") for question in questions if question.get("reverse_scored")]
    measure = {
        "measure_id": worksheet["id"],
        "display_name": worksheet.get("display_title") or worksheet.get("source_title") or worksheet["id"],
        "construct": worksheet.get("category") or worksheet.get("reflex_node") or "supportive_self_observation",
        "target_population": worksheet.get("audience_class") or worksheet.get("audience") or "pending_population_review",
        "language_version": "zh-CN",
        "evidence_source": worksheet.get("source_file") or "project_draft_source_pending",
        "source_version": worksheet.get("source_version") or "missing",
        "source_type": worksheet.get("source_type") or "missing",
        "review_status": worksheet.get("review_status") or "missing",
        "item_count": len(questions),
        "response_scales": [{"min": low, "max": high, "option_count": count} for low, high, count in ranges],
        "reverse_items": reverse_items,
        "scoring_method": worksheet.get("scoring") or "scoring_evidence_pending",
        "scoring_version": f"{worksheet.get('source_version') or 'unversioned'}::worksheet_server_score_v1",
        "missing_item_rule": "all_required_items_must_be_present" if questions and all(item.get("required") for item in questions) else "required_items_only_optional_text_may_be_missing",
        "assessment_window": "worksheet_instruction_or_protocol_window_pending_freeze",
        "minimum_interval": "pending_research_lead_freeze",
        "allowed_use": ["supportive_self_observation", "governed_recommendation", "authorized_research_after_separate_consent"],
        "prohibited_use": ["diagnosis", "screening_claim_without_validation", "fixed_personality_label", "causal_effect_claim"],
        "raw_answer_field": "assessment_results.answers_json",
        "raw_score_field": "assessment_results.raw_scores_json",
        "derived_score_field": "assessment_results.scores_json",
        "transformed_score_field": "assessment_results.transformed_scores_json",
        "interpretation_boundary": worksheet.get("result_disclaimer") or worksheet.get("boundary_notice") or "只作支持性观察，不构成诊断。",
        "owner": "research_lead_pending_assignment",
        "freeze_date": None,
        "freeze_status": "draft_before_freeze",
    }
    if worksheet["id"] == "regulatory_focus_relationship_18":
        measure["score_separation"] = {
            "raw_scale": {"min": 1, "max": 9, "field": "raw_scores_json"},
            "model_input_scale": {"min": 1, "max": 5, "field": "transformed_scores_json"},
            "formula": "1 + (raw - 1) * 4 / 8",
            "transformation_version": "linear_9_to_5_v1",
            "purpose": "compatibility_with_existing_1_to_5_profile_model_only",
            "raw_values_preserved": True,
            "reporting_rule": "九点原分与五点模型输入不得在同一量尺下混写。",
        }
    return measure


def build_registry() -> dict:
    worksheets = json.loads((CONTENT_ROOT / "assessment_worksheets.json").read_text(encoding="utf-8"))["worksheets"]
    measures = [_measure_entry(item) for item in sorted(worksheets, key=lambda row: row["id"])]
    return {
        "version": "2026-07-20-t30-methodology-v1",
        "status": "draft_before_freeze",
        "generated_from": {"assessment_worksheets_version": json.loads((CONTENT_ROOT / "assessment_worksheets.json").read_text(encoding="utf-8")).get("version"), "outcome_rows_read": 0},
        "real_outcome_data_accessed": False,
        "formal_freeze_allowed": False,
        "confirmatory_analysis_allowed": False,
        "product_lines": PRODUCT_LINES,
        "participant_flow_states": ["eligible", "consented", "exposed_to_entry", "started", "completed", "feedback_seen", "action_selected", "followup_due", "followup_completed", "not_seen", "declined", "abandoned", "technical_failure", "safety_routed", "withdrew_research_consent", "lost_to_followup"],
        "measures": measures,
        "metrics": METRICS,
        "missingness_plan": {
            "distinct_states": ["not_exposed", "not_started", "started_not_completed", "submission_failed", "active_withdrawal", "research_withdrawal", "technical_failure", "lost_to_followup"],
            "forbidden_defaults": ["mean_imputation_without_plan", "zero_imputation", "last_observation_carried_forward_as_default"],
            "primary_strategy": "pending_outcome_and_design_freeze",
            "candidate_methods": ["complete_case_with_bias_limits", "fiml_when_model_and_assumptions_support", "multiple_imputation_with_predefined_predictors"],
            "required_sensitivity": ["best_worst_bounds", "pattern_mixture_or_delta_shift_when_feasible", "completion_vs_noncompletion_baseline_comparison"],
        },
        "longitudinal_plan": {
            "required_checks": ["stable_participant_id", "actual_wave_dates", "measure_version_match", "score_range_match", "interval_documented", "configural_metric_scalar_invariance_when_latent_comparison_used"],
            "between_within_separated": True,
            "minimum_points_for_trend": 2,
            "minimum_points_for_model_candidate": 3,
            "smoothing": "none_before_freeze",
            "model_sequence": ["descriptive_by_wave", "mixed_model_or_growth_candidate", "ri_clpm_only_if_estimand_waves_and_identification_support"],
            "fallback": "descriptive_change_with_actual_dates_and_no_causal_language",
            "cluster_boundary": "横断面聚类不得解释为个人发展轨迹。",
        },
        "analysis_sequence": {
            "order": ["flow_and_data_quality", "scoring_and_reliability_by_wave", "missingness_and_attrition", "primary_estimand", "diagnostics", "predefined_sensitivity", "secondary", "exploratory"],
            "covariates": "pending_freeze_no_posthoc_selection",
            "interactions": "none_confirmatory_until_named_and_power_checked",
            "subgroups": "none_confirmatory_until_measurement_comparability_and_formal_difference_test_defined",
            "multiplicity": "pending_family_definition_and_control_method",
            "outliers": "report_influence_and_predefined_robustness_no_significance_driven_deletion",
            "failure_fallback": "simpler_predeclared_descriptive_or_identifiable_model",
            "deviation_policy": "new_version_reason_timestamp_exploratory_label_before_result_access",
        },
        "simulation_plan": {
            "contains_real_data": False,
            "random_seed": 20260720,
            "scenarios": ["completion_precision_n20_n40_n80", "attrition_0_20_40_percent", "three_wave_between_within_recovery", "two_cluster_perturbation_stability"],
            "power_claim_allowed": False,
            "purpose": "feasibility_and_identifiability_only_until_effect_and_primary_estimand_are_frozen",
        },
        "reporting_standards": [
            {"id": "APA_JARS_QUANT", "applies_to": "quantitative_psychology_reports", "status": "applicable", "official_url": "https://apastyle.apa.org/jars/quantitative", "verified_via": "https://www.equator-network.org/reporting-guidelines/journal-article-reporting-standards-for-quantitative-research-in-psychology-the-apa-publications-and-communications-board-task-force-report/", "accessed_on": "2026-07-20"},
            {"id": "STROBE", "applies_to": "observational_or_longitudinal_reporting_if_selected", "status": "conditional", "official_url": "https://www.strobe-statement.org/checklists/", "accessed_on": "2026-07-20"},
            {"id": "SPIRIT_2025", "applies_to": "randomized_trial_protocol_only_if_design_selected", "status": "not_currently_applicable", "official_url": "https://www.consort-spirit.org/", "accessed_on": "2026-07-20"},
            {"id": "CONSORT_2025", "applies_to": "randomized_trial_results_only_if_design_selected", "status": "not_currently_applicable", "official_url": "https://www.consort-spirit.org/", "accessed_on": "2026-07-20"},
            {"id": "SPIRIT_AI_CONSORT_AI", "applies_to": "AI_randomized_trial_only_after_live_trial_approval", "status": "not_currently_applicable_legacy_extension_to_reconcile_with_2025_core", "official_url": "https://www.consort-spirit.org/extensions", "accessed_on": "2026-07-20"},
            {"id": "DECIDE_AI", "applies_to": "early_live_clinical_AI_evaluation_only", "status": "future_conditional_not_for_current_synthetic_sandbox", "official_url": "https://www.nature.com/articles/s41591-022-01772-9", "accessed_on": "2026-07-20"},
            {"id": "PRISMA", "applies_to": "systematic_review_only", "status": "excluded_not_a_systematic_review", "official_url": "https://www.prisma-statement.org/", "accessed_on": "2026-07-20"},
        ],
        "signature_requirements": [
            {"role": "research_lead", "status": "pending_human_signature", "evidence_required": "primary_question_estimand_timepoint_sample_basis"},
            {"role": "ethics_or_governance_lead", "status": "pending_human_signature", "evidence_required": "ethics_consent_safety_data_use"},
            {"role": "data_lead", "status": "pending_human_signature", "evidence_required": "measure_scoring_missingness_access_freeze"},
            {"role": "engineering_lead", "status": "pending_human_signature", "evidence_required": "version_hash_code_environment_recovery"},
        ],
        "unresolved_blockers": ["unique_primary_outcome", "primary_timepoint", "sample_size_basis", "minimum_interpretable_change", "final_inclusion_exclusion", "missing_data_primary_method", "stopping_decision_owner", "ethics_and_data_governance_evidence", "target_journal_if_any"],
        "boundary_notice": "本注册表只冻结前结构，不读取主要真实结果、不构成预注册、伦理批准、研究负责人签字或效果结论。",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = json.dumps(build_registry(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != rendered:
            print("research methodology registry drift detected")
            return 1
        print(f"research methodology registry check passed: {len(build_registry()['measures'])} measures")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"wrote {args.output} with {len(build_registry()['measures'])} measures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
