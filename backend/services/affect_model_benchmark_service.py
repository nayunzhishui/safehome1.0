"""Reproducible affect candidate comparison for synthetic engineering evidence."""

from __future__ import annotations

import hashlib
import json


SPLIT_DOMAIN = "safehome-annotation-group-v2:synthetic-case"


class AffectModelDependencyError(RuntimeError):
    """Raised when the declared offline model dependency is absent."""


def synthetic_case_partition(case: dict) -> tuple[str, str]:
    case_id = str(case["id"])
    group_hash = hashlib.sha256(f"{SPLIT_DOMAIN}:{case_id}".encode("utf-8")).hexdigest()
    bucket = int(group_hash[:8], 16) % 100
    split_name = "train" if bucket < 70 else "validation" if bucket < 85 else "test"
    return group_hash, split_name


def triage_text(text: str, terms: dict[str, list[str]], registry: dict) -> dict:
    value = str(text or "").strip()
    minimum_length = int(registry["abstention_policy"]["minimum_text_length"])
    if len(value) < minimum_length:
        reason = "text_too_short"
    else:
        matched = {
            label
            for label, words in terms.items()
            if label != "crisis_expression" and any(word in value for word in words)
        }
        if not matched:
            reason = "out_of_domain_no_emotion_cue"
        elif len(matched) > 1:
            reason = "conflicting_emotion_cues"
        else:
            return {
                "label": next(iter(matched)),
                "needs_human_review": False,
                "reason": None,
            }
    return {"label": "unknown", "needs_human_review": True, "reason": reason}


def _metric_bundle(
    gold: list[str],
    predicted: list[str],
    confidences: list[float],
    labels: list[str],
    rare_labels: list[str],
    subgroups: list[str],
) -> dict:
    try:
        from sklearn.metrics import f1_score, recall_score
    except ImportError as exc:
        raise AffectModelDependencyError(
            "scikit-learn is required by T37-A03; install backend/requirements.txt"
        ) from exc

    recalls = recall_score(gold, predicted, labels=labels, average=None, zero_division=0)
    per_class = {
        label: round(float(value), 4) for label, value in zip(labels, recalls)
    }
    rare_values = [per_class[label] for label in rare_labels if label in per_class]
    covered = sum(label != "unknown" for label in predicted)
    sample_count = len(gold)
    ece = 0.0
    if sample_count:
        for lower in (index / 10 for index in range(10)):
            upper = lower + 0.1
            indexes = [
                index
                for index, confidence in enumerate(confidences)
                if lower <= confidence < upper or (upper == 1.0 and confidence == 1.0)
            ]
            if indexes:
                accuracy = sum(predicted[index] == gold[index] for index in indexes) / len(
                    indexes
                )
                mean_confidence = sum(confidences[index] for index in indexes) / len(
                    indexes
                )
                ece += len(indexes) / sample_count * abs(accuracy - mean_confidence)
    coverage = covered / sample_count if sample_count else 0.0
    confusion_labels = labels + ["unknown"]
    confusion = {
        gold_label: {predicted_label: 0 for predicted_label in confusion_labels}
        for gold_label in labels
    }
    subgroup_counts: dict[str, list[int]] = {}
    for gold_label, predicted_label, subgroup in zip(gold, predicted, subgroups):
        confusion[gold_label][predicted_label] += 1
        bucket = subgroup_counts.setdefault(subgroup, [0, 0, 0])
        bucket[0] += int(gold_label == predicted_label)
        bucket[1] += 1
        bucket[2] += int(predicted_label != "unknown")
    return {
        "sample_count": sample_count,
        "macro_f1": round(
            float(
                f1_score(
                    gold,
                    predicted,
                    labels=labels,
                    average="macro",
                    zero_division=0,
                )
            ),
            4,
        ),
        "per_class_recall": per_class,
        "rare_cue_recall": round(sum(rare_values) / len(rare_values), 4)
        if rare_values
        else None,
        "expected_calibration_error": round(ece, 4),
        "coverage_rate": round(coverage, 4),
        "abstention_rate": round(1 - coverage, 4),
        "unknown_count": sample_count - covered,
        "confusion_matrix": confusion,
        "subgroups": {
            name: {
                "correct": values[0],
                "total": values[1],
                "accuracy": round(values[0] / values[1], 4),
                "coverage_rate": round(values[2] / values[1], 4),
            }
            for name, values in sorted(subgroup_counts.items())
        },
    }


def _rule_predictions(
    cases: list[dict], terms: dict[str, list[str]], registry: dict
) -> tuple[list[str], list[float]]:
    predicted: list[str] = []
    confidences: list[float] = []
    for case in cases:
        triage = triage_text(case["text"], terms, registry)
        predicted.append(triage["label"])
        confidences.append(0.0 if triage["needs_human_review"] else 0.85)
    return predicted, confidences


def _linear_predictions(
    train_cases: list[dict],
    validation_cases: list[dict],
    test_cases: list[dict],
    terms: dict[str, list[str]],
    registry: dict,
) -> tuple[list[str], list[float], float]:
    try:
        import numpy as np
        from sklearn.calibration import CalibratedClassifierCV
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
    except ImportError as exc:
        raise AffectModelDependencyError(
            "scikit-learn is required by T37-A03; install backend/requirements.txt"
        ) from exc

    seed = int(registry["random_seed"])
    pipeline = Pipeline(
        [
            (
                "features",
                TfidfVectorizer(
                    analyzer="char",
                    ngram_range=(1, 3),
                    min_df=1,
                    lowercase=False,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=1000,
                    random_state=seed,
                ),
            ),
        ]
    )
    model = CalibratedClassifierCV(pipeline, method="sigmoid", cv=3)
    model.fit(
        [case["text"] for case in train_cases],
        np.asarray([case["generator_label"] for case in train_cases]),
    )
    validation_probabilities = model.predict_proba(
        [case["text"] for case in validation_cases]
    )
    classes = list(model.classes_)
    validation_gold = [case["generator_label"] for case in validation_cases]
    threshold_scores: list[tuple[float, float, float]] = []
    from sklearn.metrics import f1_score

    for candidate_threshold in registry["abstention_policy"][
        "linear_threshold_candidates"
    ]:
        threshold = float(candidate_threshold)
        validation_predictions: list[str] = []
        for case, values in zip(validation_cases, validation_probabilities):
            triage = triage_text(case["text"], terms, registry)
            best_index = int(values.argmax())
            confidence = float(values[best_index])
            validation_predictions.append(
                "unknown"
                if triage["needs_human_review"] or confidence < threshold
                else classes[best_index]
            )
        macro_f1 = float(
            f1_score(
                validation_gold,
                validation_predictions,
                labels=classes,
                average="macro",
                zero_division=0,
            )
        )
        coverage = sum(label != "unknown" for label in validation_predictions) / len(
            validation_predictions
        )
        threshold_scores.append((macro_f1, coverage, threshold))
    threshold = max(
        threshold_scores,
        key=lambda item: (item[0], item[1], -item[2]),
    )[2]
    probabilities = model.predict_proba([case["text"] for case in test_cases])
    predicted: list[str] = []
    confidences: list[float] = []
    for case, values in zip(test_cases, probabilities):
        triage = triage_text(case["text"], terms, registry)
        best_index = int(values.argmax())
        confidence = float(values[best_index])
        if triage["needs_human_review"] or confidence < threshold:
            predicted.append("unknown")
        else:
            predicted.append(classes[best_index])
        confidences.append(confidence)
    return predicted, confidences, threshold


def compare_affect_candidates(
    cases: list[dict], terms: dict[str, list[str]], registry: dict
) -> dict:
    partitions: dict[str, list[dict]] = {
        "train": [],
        "validation": [],
        "test": [],
    }
    for case in cases:
        _, split_name = synthetic_case_partition(case)
        partitions[split_name].append(case)
    if any(not partitions[name] for name in partitions):
        raise ValueError("synthetic grouped split must contain train, validation and test")

    test_cases = partitions["test"]
    labels = sorted({str(case["generator_label"]) for case in cases})
    gold = [str(case["generator_label"]) for case in test_cases]
    subgroups = [str(case["subgroup"]) for case in test_cases]
    rule_predicted, rule_confidences = _rule_predictions(test_cases, terms, registry)
    linear_predicted, linear_confidences, linear_threshold = _linear_predictions(
        partitions["train"], partitions["validation"], test_cases, terms, registry
    )
    candidate_results = [
        {
            "candidate_id": "rule_lexicon_72_v1",
            "evaluated": True,
            "status": "synthetic_engineering_only",
            "metrics": _metric_bundle(
                gold,
                rule_predicted,
                rule_confidences,
                labels,
                registry["rare_cue_labels"],
                subgroups,
            ),
        },
        {
            "candidate_id": "char_tfidf_logreg_platt_v1",
            "evaluated": True,
            "status": "synthetic_engineering_only",
            "decision_threshold": linear_threshold,
            "metrics": _metric_bundle(
                gold,
                linear_predicted,
                linear_confidences,
                labels,
                registry["rare_cue_labels"],
                subgroups,
            ),
        },
    ]
    for candidate in registry["candidates"]:
        if candidate["kind"] == "chinese_pretrained":
            candidate_results.append(
                {
                    "candidate_id": candidate["id"],
                    "evaluated": False,
                    "status": candidate["execution_status"],
                    "block_reasons": candidate["block_reasons"],
                }
            )
    digest_payload = {
        "registry_version": registry["version"],
        "case_ids": [case["id"] for case in cases],
        "split_counts": {name: len(items) for name, items in partitions.items()},
        "candidates": candidate_results,
    }
    experiment_digest = hashlib.sha256(
        json.dumps(
            digest_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    selected = max(
        (item for item in candidate_results if item["evaluated"]),
        key=lambda item: (
            item["metrics"]["macro_f1"],
            item["metrics"]["coverage_rate"],
            item["candidate_id"],
        ),
    )
    return {
        "sample_count": len(cases),
        "split_counts": {name: len(items) for name, items in partitions.items()},
        "experiment_digest": experiment_digest,
        "registry_version": registry["version"],
        "feature_version": registry["feature_contract"]["version"],
        "random_seed": registry["random_seed"],
        "human_gold_used": False,
        "probability_is_clinical_confidence": False,
        "production_replacement_allowed": False,
        "candidates": candidate_results,
        "selected_for_engineering_review": selected["candidate_id"],
        "model_card": registry["model_card"],
        "coverage_rate": selected["metrics"]["coverage_rate"],
        "macro_f1_against_generator_seed": selected["metrics"]["macro_f1"],
        "calibration_error": selected["metrics"]["expected_calibration_error"],
        "confusion_matrix": selected["metrics"]["confusion_matrix"],
        "subgroups": selected["metrics"]["subgroups"],
        "failed_cases": [],
        "limitations": registry["model_card"]["known_limitations"],
    }
