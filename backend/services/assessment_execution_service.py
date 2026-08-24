"""Validate and score one assessment submission through a single interface."""

from dataclasses import dataclass

from database import ensure_user, get_connection, json_dumps, new_id, now_iso, row_to_dict
from services.assessment_profile_position_store import backfill_profile_position
from services.assessment_profile_service import ProfilePositionUnavailable, build_assessment_profile_position
from services.idempotency_service import (
    IdempotencyConflictError,
    canonical_request_hash,
    public_idempotent_resource,
    record_side_effect,
    reserve_idempotency,
    store_idempotency_response,
)
from services.participant_safeguard_service import ParticipantSafeguardError, assert_participant_capability
from services.risk_review_service import create_risk_review_record, should_create_risk_review
from services.risk_service import check_text_risk
from services.training_recommendation_service import evaluate_training_rules, flatten_card_ids


class AssessmentSubmissionError(ValueError):
    """A client-visible assessment answer validation failure."""

    def __init__(self, code: str, message: str, status: int = 400, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details or {}


@dataclass(frozen=True)
class AssessmentExecutionResult:
    answers: list[dict]
    scores: dict
    total_score: int | float | None
    text_values: list[str]


def submit_assessment(
    worksheet: dict,
    submitted_answers: list[dict],
    *,
    user_id: str,
    nickname: str | None = None,
    result_summary: str | None = None,
    client_submission_id: str | None = None,
) -> dict:
    """Validate, score, risk-check, save, profile, and recommend in one module."""

    try:
        minor_safeguards = assert_participant_capability(user_id, "assessment")
    except ParticipantSafeguardError as exc:
        raise AssessmentSubmissionError(exc.code, exc.message, exc.status, exc.details) from exc

    execution = execute_assessment(worksheet, submitted_answers)
    answers = execution.answers
    scores = execution.scores
    score_provenance = build_score_provenance(worksheet, answers, scores)
    risk_result = check_text_risk(execution.text_values, source="assessment") if execution.text_values else None
    if risk_result:
        scores["risk"] = {
            "risk_level": risk_result.get("risk_level"),
            "safety_route": risk_result.get("safety_route"),
            "requires_review": risk_result.get("requires_review"),
            "allow_recommended_training_cards": risk_result.get("allow_recommended_training_cards"),
        }

    result_id = new_id("assessment")
    summary = result_summary or worksheet.get("result_disclaimer") or "本次内容已保存。结果仅用于自我观察和练习记录，不构成诊断。"
    if risk_result and not risk_result.get("allow_auto_feedback", True):
        summary = risk_result.get("safe_response") or summary
    request_hash = canonical_request_hash(
        actor_id=user_id,
        endpoint="POST /api/assessment-results",
        version="v1",
        payload={
            "worksheet_id": worksheet["id"],
            "answers": answers,
            "result_summary": summary,
        },
    ) if client_submission_id else None
    training_rules = evaluate_training_rules(
        worksheet["id"],
        scores,
        worksheet=worksheet,
        risk_result=risk_result,
        user_id=user_id,
    )
    recommended_card_ids = flatten_card_ids(training_rules) or worksheet.get("recommended_card_ids", [])
    if risk_result and not risk_result.get("allow_recommended_training_cards", True):
        recommended_card_ids = []
        training_rules = []

    replayed = False
    with get_connection() as conn:
        ensure_user(conn, user_id, nickname)
        reservation = None
        if client_submission_id:
            try:
                reservation = reserve_idempotency(
                    conn,
                    actor_id=user_id,
                    endpoint="POST /api/assessment-results",
                    idempotency_key=client_submission_id,
                    request_hash=request_hash,
                    resource_type="assessment_result",
                    resource_id=result_id,
                )
            except IdempotencyConflictError as exc:
                raise AssessmentSubmissionError(
                    "idempotency_conflict",
                    "该提交标识已用于另一份测评记录。",
                    409,
                ) from exc
            if not reservation.created:
                if reservation.response is not None:
                    result = public_idempotent_resource(reservation.response)
                    result["idempotency_replayed"] = True
                    return result
                row = conn.execute(
                    "SELECT * FROM assessment_results WHERE id = ? AND user_id = ?",
                    (reservation.resource_id, user_id),
                ).fetchone()
                if row is None:
                    raise AssessmentSubmissionError(
                        "idempotency_state_conflict",
                        "原提交结果不可用。",
                        409,
                    )
                replayed = True
        if not replayed:
            conn.execute(
                """
                INSERT INTO assessment_results (
                    id, user_id, worksheet_id, worksheet_title, category,
                    answers_json, scores_json, scoring_version, raw_scale_json,
                    raw_scores_json, transformed_scores_json, transformation_version,
                    total_score, result_summary, client_submission_id, request_hash, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result_id,
                    user_id,
                    worksheet["id"],
                    worksheet.get("display_title") or worksheet.get("source_title") or worksheet["id"],
                    worksheet.get("category"),
                    json_dumps(answers),
                    json_dumps(scores),
                    score_provenance["scoring_version"],
                    json_dumps(score_provenance["raw_scale"]),
                    json_dumps(score_provenance["raw_scores"]),
                    json_dumps(score_provenance["transformed_scores"]),
                    score_provenance["transformation_version"],
                    execution.total_score,
                    summary,
                    client_submission_id,
                    request_hash,
                    now_iso(),
                ),
            )
            if reservation is None or record_side_effect(
                conn,
                idempotency_record_id=reservation.id,
                effect_type="risk_task",
                effect_key="assessment_risk_review",
                status="committed" if should_create_risk_review(risk_result) else "not_required",
                metadata={"resource_id": result_id},
            ):
                create_risk_review_record(conn, user_id, "assessment_result", result_id, risk_result)
            row = conn.execute("SELECT * FROM assessment_results WHERE id = ?", (result_id,)).fetchone()
            result_row = row_to_dict(row)
            if result_row:
                result_row["answers"] = answers
                try:
                    position = build_assessment_profile_position(result_row, worksheet)
                    backfill_profile_position(conn, result_id, position)
                    if reservation is not None:
                        record_side_effect(
                            conn,
                            idempotency_record_id=reservation.id,
                            effect_type="profile_position",
                            effect_key="assessment_profile_position",
                            status="committed",
                            metadata={"resource_id": result_id},
                        )
                    row = conn.execute("SELECT * FROM assessment_results WHERE id = ?", (result_id,)).fetchone()
                except ProfilePositionUnavailable:
                    if reservation is not None:
                        record_side_effect(
                            conn,
                            idempotency_record_id=reservation.id,
                            effect_type="profile_position",
                            effect_key="assessment_profile_position",
                            status="not_available",
                            metadata={"resource_id": result_id},
                        )
            if reservation is not None:
                record_side_effect(
                    conn,
                    idempotency_record_id=reservation.id,
                    effect_type="recommendation",
                    effect_key="assessment_training_recommendation",
                    status="computed",
                    metadata={"resource_id": result_id, "card_count": len(recommended_card_ids)},
                )

        result = public_idempotent_resource(row_to_dict(row))
        result["answers"] = answers
        result["scores"] = scores
        result["raw_scale"] = score_provenance["raw_scale"]
        result["raw_scores"] = score_provenance["raw_scores"]
        result["transformed_scores"] = score_provenance["transformed_scores"]
        result["scoring_version"] = score_provenance["scoring_version"]
        result["transformation_version"] = score_provenance["transformation_version"]
        result["score_reporting_notice"] = score_provenance["reporting_notice"]
        result["recommended_card_ids"] = recommended_card_ids
        result["training_recommendation_rules"] = training_rules
        result["risk"] = risk_result
        result["minor_safeguards"] = minor_safeguards
        result["boundary_notice"] = worksheet.get("boundary_notice")
        result["result_disclaimer"] = worksheet.get("result_disclaimer")
        result["idempotency_replayed"] = replayed
        if reservation is not None and reservation.created:
            store_idempotency_response(
                conn,
                idempotency_record_id=reservation.id,
                response=result,
                response_status=201,
            )
        conn.commit()
        return result


def execute_assessment(worksheet: dict, submitted_answers: list[dict]) -> AssessmentExecutionResult:
    """Return canonical answers and server-calculated scores for a worksheet."""

    if not isinstance(submitted_answers, list):
        raise AssessmentSubmissionError("invalid_answers", "answers 必须是数组")

    questions = worksheet.get("questions") or []
    question_map = {question.get("id"): question for question in questions if question.get("id")}
    seen: set[str] = set()
    answers: list[dict] = []

    for submitted in submitted_answers:
        if not isinstance(submitted, dict):
            raise AssessmentSubmissionError("invalid_answer", "每一项回答都必须是对象")
        question_id = submitted.get("question_id")
        if not isinstance(question_id, str):
            raise AssessmentSubmissionError("unknown_question_id", f"题号不存在：{question_id}")
        if question_id not in question_map:
            raise AssessmentSubmissionError("unknown_question_id", f"题号不存在：{question_id}")
        if question_id in seen:
            raise AssessmentSubmissionError("duplicate_question_id", f"题号重复：{question_id}")
        seen.add(question_id)

        question = question_map[question_id]
        value = submitted.get("value")
        options = question.get("options") or []
        canonical = {
            "question_id": question_id,
            "prompt": question.get("prompt") or submitted.get("prompt"),
        }
        if options:
            option = next(
                (candidate for candidate in options if str(candidate.get("value")) == str(value)),
                None,
            )
            if option is None:
                raise AssessmentSubmissionError("invalid_option_value", f"题目 {question_id} 的选项无效")
            canonical["value"] = option.get("value")
            score = option.get("score")
            if isinstance(score, (int, float)) and not isinstance(score, bool):
                canonical["score"] = score
        else:
            if question.get("required") and not str(value or "").strip():
                raise AssessmentSubmissionError("missing_required_answers", f"必答题未填写：{question_id}")
            canonical["value"] = value
        answers.append(canonical)

    missing_ids = [
        question["id"]
        for question in questions
        if question.get("required") and question.get("id") not in seen
    ]
    if missing_ids:
        raise AssessmentSubmissionError(
            "missing_required_answers",
            f"缺少必答题：{', '.join(missing_ids)}",
        )

    scores, total_score = score_answers(worksheet, answers)
    text_values = [
        str(answer.get("value", "")).strip()
        for answer in answers
        if str(answer.get("value", "")).strip() and "score" not in answer
    ]
    return AssessmentExecutionResult(answers, scores, total_score, text_values)


def score_answers(worksheet: dict, answers: list[dict]) -> tuple[dict, int | float | None]:
    question_map = {question.get("id"): question for question in worksheet.get("questions", [])}
    score_method = worksheet.get("dimension_score_method", "sum")
    total_score_method = worksheet.get("total_score_method") or (worksheet.get("_meta") or {}).get("total_score_method", "sum")
    total: int | float = 0
    has_score = False
    dimension_totals: dict[str, dict] = {}
    item_scores: dict[str, int | float] = {}

    for answer in answers:
        question = question_map.get(answer.get("question_id"))
        score = answer.get("score")
        if isinstance(score, (int, float)) and not isinstance(score, bool):
            effective = _effective_score(question, score)
            item_scores[answer.get("question_id")] = effective
            total += effective
            has_score = True
            dimension = question.get("dimension") if question else None
            if dimension:
                bucket = dimension_totals.setdefault(dimension, {"score": 0, "item_count": 0})
                bucket["score"] += effective
                bucket["item_count"] += 1

    dimension_labels = _dimension_labels(worksheet)
    dimension_specs = {
        item.get("code") or item.get("key"): item
        for item in worksheet.get("dimensions", [])
        if isinstance(item, dict) and (item.get("code") or item.get("key"))
    }
    dimensions = []
    dimension_scores: dict[str, int | float] = {}
    ordered_dimension_codes = list(dimension_specs) or list(dimension_totals)
    for dimension in ordered_dimension_codes:
        bucket = dimension_totals.get(dimension, {"score": 0, "item_count": 0})
        item_count = bucket["item_count"]
        calculation = dimension_specs.get(dimension, {}).get("calculation")
        calculated = _calculate_dimension(calculation, item_scores, dimension_scores)
        if calculated is not None:
            value = calculated
            calculation_method = calculation.get("type", score_method)
        elif score_method == "mean" and item_count:
            value = round(bucket["score"] / item_count, 2)
            calculation_method = score_method
        else:
            value = bucket["score"]
            calculation_method = score_method
        dimension_scores[dimension] = value
        dimensions.append(
            {
                "key": dimension,
                "label": dimension_labels.get(dimension, dimension),
                "score": value,
                "item_count": item_count,
                "score_method": calculation_method,
            }
        )

    derived_dimensions = worksheet.get("derived_dimensions") or (worksheet.get("_meta") or {}).get("derived_dimensions", [])
    for spec in derived_dimensions:
        if not isinstance(spec, dict) or not spec.get("code"):
            continue
        calculation = spec.get("calculation") or {}
        value = _calculate_dimension(calculation, item_scores, dimension_scores)
        if value is None:
            continue
        dimension_scores[spec["code"]] = value
        dimensions.append(
            {
                "key": spec["code"],
                "label": spec.get("label", spec["code"]),
                "score": value,
                "item_count": len(calculation.get("dimensions", [])),
                "score_method": calculation.get("type", "derived"),
            }
        )

    persisted_total = total if has_score and total_score_method != "none" else None
    scores: dict = {"total_score": persisted_total}
    if dimensions:
        scores["dimensions"] = dimensions
    return scores, persisted_total


def build_score_provenance(worksheet: dict, answers: list[dict], scores: dict | None = None) -> dict:
    """Keep worksheet-scale scores distinct from model-compatibility transforms."""

    questions = {item.get("id"): item for item in worksheet.get("questions", [])}
    raw_items = {
        str(answer.get("question_id")): answer.get("score")
        for answer in answers
        if isinstance(answer.get("score"), (int, float)) and not isinstance(answer.get("score"), bool)
    }
    bounds = []
    for question in questions.values():
        option_bounds = _option_score_bounds(question)
        if option_bounds:
            bounds.append(option_bounds)
    unique_bounds = sorted({(float(low), float(high)) for low, high in bounds})
    raw_scale = {
        "ranges": [{"min": low, "max": high} for low, high in unique_bounds],
        "mixed_scales": len(unique_bounds) > 1,
        "worksheet_id": worksheet.get("id"),
    }
    raw_scores = {
        "item_scores": raw_items,
        "dimensions": (scores or {}).get("dimensions", []),
        "total_score": (scores or {}).get("total_score"),
        "score_space": "worksheet_raw",
    }
    transformed_scores: dict = {}
    transformation_version = None
    reporting_notice = "当前结果按问卷原始量尺保存；没有模型兼容转换。"
    if worksheet.get("id") == "regulatory_focus_relationship_18":
        transformation_version = "linear_9_to_5_v1"
        transformed_answers = []
        transformed_items = {}
        for answer in answers:
            copied = dict(answer)
            score = answer.get("score")
            if isinstance(score, (int, float)) and not isinstance(score, bool):
                transformed = round(1 + (float(score) - 1) * 4 / 8, 4)
                copied["score"] = transformed
                transformed_items[str(answer.get("question_id"))] = transformed
            transformed_answers.append(copied)
        model_scores, _ = score_answers(worksheet, transformed_answers)
        transformed_scores = {
            "item_scores": transformed_items,
            "dimensions": model_scores.get("dimensions", []),
            "total_score": model_scores.get("total_score"),
            "score_space": "model_input_1_to_5",
            "formula": "1 + (raw - 1) * 4 / 8",
            "input_range": {"min": 1, "max": 9},
            "output_range": {"min": 1, "max": 5},
        }
        reporting_notice = "九点原分与五点模型输入已分字段保存；报告必须标明量尺，不得混写。"
    return {
        "scoring_version": f"{worksheet.get('source_version') or 'unversioned'}::worksheet_server_score_v1",
        "raw_scale": raw_scale,
        "raw_scores": raw_scores,
        "transformed_scores": transformed_scores,
        "transformation_version": transformation_version,
        "reporting_notice": reporting_notice,
    }


def _option_score_bounds(question: dict) -> tuple[int | float, int | float] | None:
    scores = [
        option.get("score")
        for option in question.get("options", [])
        if isinstance(option.get("score"), (int, float)) and not isinstance(option.get("score"), bool)
    ]
    return (min(scores), max(scores)) if scores else None


def _effective_score(question: dict | None, score: int | float) -> int | float:
    if question and question.get("reverse_scored"):
        bounds = _option_score_bounds(question)
        if bounds:
            low, high = bounds
            return low + high - score
    return score


def _rounded(value: float) -> int | float:
    rounded = round(value, 2)
    return int(rounded) if rounded.is_integer() else rounded


def _calculate_dimension(calculation: dict | None, item_scores: dict, dimension_scores: dict) -> int | float | None:
    if not calculation:
        return None
    calculation_type = calculation.get("type")
    if calculation_type == "product":
        values = [item_scores.get(item) for item in calculation.get("items", [])]
        if not values or any(value is None for value in values):
            return None
        product = 1
        for value in values:
            product *= value
        return _rounded(float(product))
    if calculation_type == "mean_of_products":
        products = []
        for pair in calculation.get("pairs", []):
            values = [item_scores.get(item) for item in pair]
            if values and all(value is not None for value in values):
                product = 1
                for value in values:
                    product *= value
                products.append(product)
        return _rounded(sum(products) / len(products)) if products else None
    if calculation_type == "mean_terms":
        values = []
        for term in calculation.get("terms", []):
            value = item_scores.get(term.get("item"))
            if value is None:
                continue
            if term.get("reverse_min") is not None and term.get("reverse_max") is not None:
                value = term["reverse_min"] + term["reverse_max"] - value
            values.append(value)
        return _rounded(sum(values) / len(values)) if values else None
    if calculation_type == "mapped_mean_terms":
        values = []
        for term in calculation.get("terms", []):
            value = item_scores.get(term.get("item"))
            mapped = (term.get("map") or {}).get(str(value))
            if isinstance(mapped, (int, float)) and not isinstance(mapped, bool):
                values.append(mapped)
        return _rounded(sum(values) / len(values)) if values else None
    if calculation_type == "mean_dimensions":
        values = [dimension_scores.get(code) for code in calculation.get("dimensions", [])]
        values = [value for value in values if value is not None]
        return _rounded(sum(values) / len(values)) if values else None
    return None


def _dimension_labels(worksheet: dict) -> dict[str, str]:
    labels: dict[str, str] = {}
    for dimension in worksheet.get("dimensions", []) or []:
        if isinstance(dimension, dict):
            code = dimension.get("code") or dimension.get("key")
            label = dimension.get("label")
            if code and label:
                labels[code] = label
    return labels
