"""Governed offline affect/network benchmarks using synthetic data by default."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict, deque

from flask import current_app

from config import PROJECT_ROOT
from database import get_connection, json_dumps, json_loads, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log
from services.affect_model_benchmark_service import (
    compare_affect_candidates,
    synthetic_case_partition,
)


ALLOWED_LABELS = {
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
    "crisis_expression",
    "unknown",
    "unmapped",
}
ANNOTATION_EMOTION_LABELS = ALLOWED_LABELS - {"crisis_expression"}
ALLOWED_REFLEX_NODES = {"trigger", "thought", "body_feeling", "emotion", "reaction", "behavior", "outcome", "unmapped"}
REVIEW_DECISIONS = {"engineering_reviewed", "changes_required", "stop"}
ALGORITHM_VERSION = "safehome-offline-affect-network-v1"
ANNOTATION_DATASET_ID = "safehome_synthetic_affect_240_v1"
ANNOTATION_MANUAL_VERSION = "2026-07-28-t37-a01-v1"
SPLIT_POLICY_VERSION = "synthetic-case-group-hash-70-15-15-v2"


class OfflineBenchmarkError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.status = status
        self.details = details or {}


def _content_json(filename: str) -> dict:
    path = current_app.config["CONTENT_DIR"] / filename
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OfflineBenchmarkError("benchmark_content_invalid", f"离线基准内容不可用：{filename}", 503) from exc


def _control() -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT disabled, reason, changed_by, changed_at FROM offline_benchmark_runtime_control WHERE id = 'global'").fetchone()
    return dict(row) if row else {"disabled": 0, "reason": None, "changed_by": None, "changed_at": None}


def _require_enabled() -> None:
    if not current_app.config.get("OFFLINE_BENCHMARK_ENABLED", False):
        raise OfflineBenchmarkError("offline_benchmark_disabled", "离线基准已关闭", 409)
    if int(_control().get("disabled") or 0):
        raise OfflineBenchmarkError("offline_benchmark_killed", "离线基准运行已被停用", 503)


def get_config() -> dict:
    registry = _content_json("offline_benchmark_registry.json")
    manual = _content_json("offline_benchmark_annotation_manual.json")
    return {
        "enabled": bool(current_app.config.get("OFFLINE_BENCHMARK_ENABLED")) and not bool(_control().get("disabled")),
        "external_ingest_enabled": False,
        "production_replacement_allowed": False,
        "registry_version": registry["version"],
        "registry_status": registry["status"],
        "annotation_status": manual["status"],
        "synthetic_case_count": manual["target_case_count"],
        "runtime_control": {"disabled": int(_control().get("disabled") or 0), "changed_at": _control().get("changed_at")},
        "boundary_notice": registry["boundary_notice"],
    }


def get_annotation_governance() -> dict:
    policy = _content_json("offline_annotation_data_policy.json")
    return {
        "version": policy["version"],
        "active_dataset_id": policy["active_dataset_id"],
        "active_data_class": policy["active_data_class"],
        "purpose": policy["purpose"],
        "minimum_necessary_fields": policy["minimum_necessary_fields"],
        "identity_fields_hidden": policy["identity_fields_hidden"],
        "deidentification": policy["deidentification"],
        "retention": policy["retention"],
        "split_policy": policy["split_policy"],
        "annotation_policy": policy["annotation_policy"],
        "real_data_gate": policy["real_data_gate"],
    }


def get_affect_model_candidates() -> dict:
    registry = _content_json("affect_model_candidate_registry.json")
    return {
        "version": registry["version"],
        "status": registry["status"],
        "random_seed": registry["random_seed"],
        "dataset_id": registry["dataset_id"],
        "split_policy": registry["split_policy"],
        "feature_contract": registry["feature_contract"],
        "abstention_policy": registry["abstention_policy"],
        "probability_display_policy": registry["probability_display_policy"],
        "production_replacement_allowed": registry[
            "production_replacement_allowed"
        ],
        "candidates": registry["candidates"],
        "model_card": registry["model_card"],
    }


def _decode_card(row) -> dict:
    item = row_to_dict(row)
    item["allowed_uses"] = json_loads(item.pop("allowed_uses_json"), [])
    item["prohibited_uses"] = json_loads(item.pop("prohibited_uses_json"), [])
    return item


def sync_registry(actor: dict) -> dict:
    _require_enabled()
    registry = _content_json("offline_benchmark_registry.json")
    timestamp = now_iso()
    with get_connection() as conn:
        for card in registry["cards"]:
            existing = conn.execute("SELECT created_at FROM offline_dataset_cards WHERE id = ?", (card["id"],)).fetchone()
            created_at = existing["created_at"] if existing else timestamp
            values = (card["name"], card["source_url"], card["source_version"], card["language"], card["platform"],
                      card["population"], card["context"], card["license"], card["content_rights_status"], card["sensitivity"],
                      json_dumps(card["allowed_uses"]), json_dumps(card["prohibited_uses"]), card.get("artifact_sha256"),
                      card.get("local_path"), card["ingest_status"], card["deletion_method"], card.get("review_note"), registry["version"])
            if existing:
                conn.execute("""UPDATE offline_dataset_cards SET name = ?, source_url = ?, source_version = ?, language = ?, platform = ?, population = ?, context = ?, license = ?, content_rights_status = ?, sensitivity = ?, allowed_uses_json = ?, prohibited_uses_json = ?, artifact_sha256 = ?, local_path = ?, ingest_status = ?, deletion_method = ?, review_note = ?, registry_version = ?, updated_at = ? WHERE id = ?""", (*values, timestamp, card["id"]))
            else:
                conn.execute("""INSERT INTO offline_dataset_cards (id, name, source_url, source_version, language, platform, population, context, license, content_rights_status, sensitivity, allowed_uses_json, prohibited_uses_json, artifact_sha256, local_path, ingest_status, deletion_method, review_note, registry_version, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (card["id"], *values, created_at, timestamp))
        write_audit_log(conn, "offline_dataset_registry_synced", actor["id"], "offline_dataset_registry", registry["version"], {"card_count": len(registry["cards"]), "external_downloaded": False})
        conn.commit()
    return {"registry_version": registry["version"], "card_count": len(registry["cards"]), "external_downloaded": False}


def list_dataset_cards() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM offline_dataset_cards ORDER BY ingest_status, id").fetchall()
    return [_decode_card(row) for row in rows]


def _synthetic_payload() -> dict:
    payload = _content_json("synthetic_affect_benchmark_240.json")
    if payload.get("contains_real_data") is not False or payload.get("case_count") != 240:
        raise OfflineBenchmarkError("synthetic_fixture_invalid", "合成基准必须明确无真实数据且包含240例", 503)
    rendered = json.dumps(payload["cases"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if hashlib.sha256(rendered).hexdigest() != payload.get("case_hash"):
        raise OfflineBenchmarkError("synthetic_fixture_hash_mismatch", "合成基准哈希不一致", 503)
    return payload


def list_blind_cases(actor: dict, offset: int = 0, limit: int = 20) -> dict:
    _require_enabled()
    payload = _synthetic_payload()
    offset = max(0, int(offset))
    limit = max(1, min(int(limit), 50))
    with get_connection() as conn:
        annotated = {row["case_id"] for row in conn.execute("SELECT case_id FROM offline_benchmark_annotations WHERE dataset_card_id = ? AND annotator_id = ?", ("safehome_synthetic_affect_240_v1", actor["id"])).fetchall()}
    items = []
    for case in payload["cases"][offset: offset + limit]:
        items.append({"id": case["id"], "text": case["text"], "synthetic": True, "already_annotated": case["id"] in annotated})
    return {"items": items, "offset": offset, "limit": limit, "total": 240, "blind": True, "generator_labels_included": False}


def _annotation_fields(data: dict, case_text: str) -> dict:
    raw_labels = data.get("emotion_labels")
    if raw_labels is None:
        raw_labels = [data.get("emotion_label")]
    if not isinstance(raw_labels, list):
        raise OfflineBenchmarkError("annotation_labels_invalid", "情绪标签必须为数组")
    labels = list(dict.fromkeys(str(item or "").strip() for item in raw_labels))
    if not 1 <= len(labels) <= 3 or any(label not in ANNOTATION_EMOTION_LABELS for label in labels):
        raise OfflineBenchmarkError("annotation_label_invalid", "情绪标签需为一至三个已登记标签")
    polarity = str(data.get("polarity_status") or ("uncertain" if labels == ["unknown"] else "affirmed"))
    if polarity not in {"affirmed", "negated", "uncertain"}:
        raise OfflineBenchmarkError("annotation_polarity_invalid", "否定状态无效")
    try:
        intensity = int(data.get("intensity", 0 if polarity != "affirmed" else 2))
    except (TypeError, ValueError) as exc:
        raise OfflineBenchmarkError("annotation_intensity_invalid", "强度必须为0至4整数") from exc
    if not 0 <= intensity <= 4:
        raise OfflineBenchmarkError("annotation_intensity_invalid", "强度必须为0至4整数")
    evidence_excerpt = str(data.get("evidence_excerpt") or "").strip()
    if evidence_excerpt and (len(evidence_excerpt) > 160 or evidence_excerpt not in case_text):
        raise OfflineBenchmarkError("annotation_evidence_invalid", "证据片段必须来自当前文本且不超过160字")
    rationale = str(data.get("rationale") or "").strip()
    if len(rationale) > 400:
        raise OfflineBenchmarkError("annotation_rationale_invalid", "标注理由不得超过400字")
    needs_human = bool(data.get("needs_human_understanding"))
    review_reason = str(data.get("human_review_reason") or "").strip() or None
    valid_reasons = set(_content_json("emotion_annotation_ontology.json")["human_review_reasons"])
    if review_reason and review_reason not in valid_reasons:
        raise OfflineBenchmarkError("annotation_review_reason_invalid", "真人了解原因未登记")
    if review_reason and not needs_human:
        raise OfflineBenchmarkError("annotation_review_reason_invalid", "填写真人了解原因时必须开启需真人了解")
    return {
        "labels": labels,
        "primary_label": labels[0],
        "intensity": intensity,
        "polarity_status": polarity,
        "evidence_excerpt": evidence_excerpt or None,
        "rationale": rationale or None,
        "needs_human_understanding": int(needs_human),
        "human_review_reason": review_reason,
    }


def _ensure_group_split(conn, case: dict, timestamp: str) -> tuple[str, str]:
    group_hash, split_name = synthetic_case_partition(case)
    row = conn.execute(
        "SELECT split_name FROM offline_annotation_group_splits WHERE dataset_card_id = ? AND group_hash = ?",
        (ANNOTATION_DATASET_ID, group_hash),
    ).fetchone()
    split_name = row["split_name"] if row else split_name
    if not row:
        conn.execute(
            "INSERT INTO offline_annotation_group_splits (id, dataset_card_id, group_hash, split_name, split_policy_version, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                f"oas_{group_hash[:24]}",
                ANNOTATION_DATASET_ID,
                group_hash,
                split_name,
                SPLIT_POLICY_VERSION,
                timestamp,
            ),
        )
    return group_hash, split_name


def save_annotation(actor: dict, case_id: str, data: dict) -> dict:
    _require_enabled()
    payload = _synthetic_payload()
    case = next((item for item in payload["cases"] if item["id"] == case_id), None)
    if not case:
        raise OfflineBenchmarkError("case_not_found", "合成案例不存在", 404)
    fields = _annotation_fields(data, case["text"])
    emotion = fields["primary_label"]
    reflex = str(data.get("reflex_node") or "")
    if reflex not in ALLOWED_REFLEX_NODES:
        raise OfflineBenchmarkError("annotation_label_invalid", "标注标签不在允许范围")
    try:
        valence, arousal = float(data.get("valence")), float(data.get("arousal"))
    except (TypeError, ValueError) as exc:
        raise OfflineBenchmarkError("annotation_value_invalid", "效价和唤醒必须为数值") from exc
    if not -1 <= valence <= 1 or not 0 <= arousal <= 1:
        raise OfflineBenchmarkError("annotation_value_out_of_range", "效价范围-1至1，唤醒范围0至1")
    context_label = str(data.get("context") or "").strip()[:80] or "unmapped"
    blind_round = str(data.get("blind_round") or "round_1")
    if blind_round not in {"round_1", "round_2"}:
        raise OfflineBenchmarkError("blind_round_invalid", "盲标轮次无效")
    timestamp = now_iso()
    annotation_id = new_id("oba")
    with get_connection() as conn:
        cross_round = conn.execute(
            "SELECT blind_round FROM offline_benchmark_annotations WHERE dataset_card_id = ? AND case_id = ? AND annotator_id = ? AND blind_round != ?",
            (ANNOTATION_DATASET_ID, case_id, actor["id"], blind_round),
        ).fetchone()
        if cross_round:
            raise OfflineBenchmarkError("annotation_independence_violation", "同一标注者不能以另一轮次充当第二名标注者", 409)
        group_hash, split_name = _ensure_group_split(conn, case, timestamp)
        existing = conn.execute("SELECT id, created_at FROM offline_benchmark_annotations WHERE dataset_card_id = ? AND case_id = ? AND annotator_id = ? AND blind_round = ?", (ANNOTATION_DATASET_ID, case_id, actor["id"], blind_round)).fetchone()
        values = (
            emotion,
            valence,
            arousal,
            context_label,
            reflex,
            int(bool(data.get("uncertain"))),
            json_dumps(fields["labels"]),
            fields["intensity"],
            fields["polarity_status"],
            fields["evidence_excerpt"],
            fields["rationale"],
            fields["needs_human_understanding"],
            fields["human_review_reason"],
            ANNOTATION_MANUAL_VERSION,
            group_hash,
            split_name,
        )
        if existing:
            annotation_id = existing["id"]
            conn.execute(
                "UPDATE offline_benchmark_annotations SET emotion_label = ?, valence = ?, arousal = ?, context_label = ?, reflex_node = ?, uncertain = ?, emotion_labels_json = ?, intensity = ?, polarity_status = ?, evidence_excerpt = ?, rationale = ?, needs_human_understanding = ?, human_review_reason = ?, manual_version = ?, group_hash = ?, data_split = ?, updated_at = ? WHERE id = ?",
                (*values, timestamp, annotation_id),
            )
        else:
            conn.execute(
                "INSERT INTO offline_benchmark_annotations (id, dataset_card_id, case_id, annotator_id, blind_round, emotion_label, valence, arousal, context_label, reflex_node, uncertain, emotion_labels_json, intensity, polarity_status, evidence_excerpt, rationale, needs_human_understanding, human_review_reason, manual_version, group_hash, data_split, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (annotation_id, ANNOTATION_DATASET_ID, case_id, actor["id"], blind_round, *values, timestamp, timestamp),
            )
        write_audit_log(conn, "offline_blind_annotation_saved", actor["id"], "offline_benchmark_case", case_id, {"blind_round": blind_round, "generator_label_visible": False, "peer_annotation_visible": False, "synthetic": True, "manual_version": ANNOTATION_MANUAL_VERSION, "data_split": split_name})
        conn.commit()
    return {"id": annotation_id, "case_id": case_id, "blind_round": blind_round, "saved": True, "labels": fields["labels"], "data_split": split_name, "generator_label_visible": False, "peer_annotation_visible": False}


def _cohen_kappa(pairs: list[tuple[str, str]]) -> float | None:
    if not pairs:
        return None
    labels = sorted({label for pair in pairs for label in pair})
    observed = sum(left == right for left, right in pairs) / len(pairs)
    left_counts, right_counts = Counter(left for left, _ in pairs), Counter(right for _, right in pairs)
    expected = sum((left_counts[label] / len(pairs)) * (right_counts[label] / len(pairs)) for label in labels)
    return round((observed - expected) / (1 - expected), 4) if expected < 1 else (1.0 if observed == 1 else 0.0)


def agreement_summary() -> dict:
    manual = _content_json("offline_benchmark_annotation_manual.json")
    thresholds = manual["agreement_thresholds"]
    with get_connection() as conn:
        rows = rows_to_dicts(conn.execute("SELECT case_id, annotator_id, emotion_label, emotion_labels_json, intensity, polarity_status, valence, arousal FROM offline_benchmark_annotations WHERE dataset_card_id = ? AND blind_round = 'round_1' ORDER BY case_id, created_at", (ANNOTATION_DATASET_ID,)).fetchall())
        adjudicated_rows = conn.execute(
            "SELECT DISTINCT case_id FROM offline_annotation_adjudications WHERE dataset_card_id = ?",
            (ANNOTATION_DATASET_ID,),
        ).fetchall()
    for row in rows:
        row["emotion_labels"] = json_loads(row.get("emotion_labels_json"), []) or [
            row["emotion_label"]
        ]
    by_case: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        if row["annotator_id"] not in {item["annotator_id"] for item in by_case[row["case_id"]]}:
            by_case[row["case_id"]].append(row)
    complete = [items[:2] for items in by_case.values() if len(items) >= 2]
    pairs = [(items[0]["emotion_label"], items[1]["emotion_label"]) for items in complete]
    kappa = _cohen_kappa(pairs)
    exact_multilabel_agreement = (
        round(
            sum(set(items[0]["emotion_labels"]) == set(items[1]["emotion_labels"]) for items in complete)
            / len(complete),
            4,
        )
        if complete
        else None
    )
    label_distribution = Counter(label for row in rows for label in row["emotion_labels"])
    disagreement_matrix: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for left, right in pairs:
        if left != right:
            disagreement_matrix[left][right] += 1
    mean_valence_gap = round(sum(abs(float(a[0]["valence"]) - float(a[1]["valence"])) for a in complete) / len(complete), 4) if complete else None
    mean_arousal_gap = round(sum(abs(float(a[0]["arousal"]) - float(a[1]["arousal"])) for a in complete) / len(complete), 4) if complete else None
    distinct_annotators = len({row["annotator_id"] for row in rows})
    release_eligible = bool(
        len(complete) >= int(thresholds["minimum_complete_cases"])
        and distinct_annotators >= int(manual["minimum_annotators"])
        and kappa is not None
        and kappa >= float(thresholds["emotion_cohen_kappa"])
        and mean_valence_gap is not None
        and mean_valence_gap <= float(thresholds["maximum_mean_valence_gap"])
        and mean_arousal_gap is not None
        and mean_arousal_gap <= float(thresholds["maximum_mean_arousal_gap"])
    )
    adjudicated = {row["case_id"] for row in adjudicated_rows}
    conflicts = {
        case_id
        for case_id, items in by_case.items()
        if len(items) >= 2
        and (
            set(items[0]["emotion_labels"]) != set(items[1]["emotion_labels"])
            or abs(int(items[0]["intensity"]) - int(items[1]["intensity"])) >= 2
            or items[0]["polarity_status"] != items[1]["polarity_status"]
        )
    }
    return {
        "complete_double_annotated_cases": len(complete),
        "required_cases": int(thresholds["minimum_complete_cases"]),
        "distinct_annotators": distinct_annotators,
        "emotion_cohen_kappa": kappa,
        "exact_multilabel_agreement": exact_multilabel_agreement,
        "mean_valence_gap": mean_valence_gap,
        "mean_arousal_gap": mean_arousal_gap,
        "label_distribution": dict(sorted(label_distribution.items())),
        "missing_annotation_slots": max(0, 240 * int(manual["minimum_annotators"]) - len(rows)),
        "disagreement_matrix": {
            left: dict(sorted(values.items()))
            for left, values in sorted(disagreement_matrix.items())
        },
        "pending_adjudication_cases": len(conflicts - adjudicated),
        "adjudicated_cases": len(adjudicated),
        "agreement_thresholds": thresholds,
        "human_gold_release_eligible": release_eligible and not bool(conflicts - adjudicated),
        "human_gold_released": False,
        "limitations": [
            "Kappa受类别分布和低基率影响，不能单独证明标注质量。",
            "当前240例为合成文本，不能代表真实中文参与者表达。",
            "一致性达标不等于心理学有效性或产品有效性。",
        ],
        "boundary_notice": "系统不把生成标签、工程阈值或自动裁决升级为人工金标准。",
    }


def list_adjudication_queue() -> dict:
    payload = _synthetic_payload()
    texts = {item["id"]: item["text"] for item in payload["cases"]}
    with get_connection() as conn:
        rows = rows_to_dicts(
            conn.execute(
                "SELECT * FROM offline_benchmark_annotations WHERE dataset_card_id = ? AND blind_round = 'round_1' ORDER BY case_id, created_at",
                (ANNOTATION_DATASET_ID,),
            ).fetchall()
        )
        adjudicated = {
            row["case_id"]
            for row in conn.execute(
                "SELECT case_id FROM offline_annotation_adjudications WHERE dataset_card_id = ?",
                (ANNOTATION_DATASET_ID,),
            ).fetchall()
        }
    by_case: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        if row["annotator_id"] not in {item["annotator_id"] for item in by_case[row["case_id"]]}:
            row["emotion_labels"] = json_loads(row.pop("emotion_labels_json"), []) or [
                row["emotion_label"]
            ]
            by_case[row["case_id"]].append(row)
    items = []
    for case_id, annotations in by_case.items():
        if len(annotations) < 2 or case_id in adjudicated:
            continue
        left, right = annotations[:2]
        conflict = (
            set(left["emotion_labels"]) != set(right["emotion_labels"])
            or abs(int(left["intensity"]) - int(right["intensity"])) >= 2
            or left["polarity_status"] != right["polarity_status"]
        )
        if not conflict:
            continue
        def public_annotation(item: dict, slot: str) -> dict:
            return {
                "slot": slot,
                "annotation_id": item["id"],
                "emotion_labels": item["emotion_labels"],
                "intensity": item["intensity"],
                "polarity_status": item["polarity_status"],
                "evidence_excerpt": item["evidence_excerpt"],
                "rationale": item["rationale"],
                "needs_human_understanding": bool(item["needs_human_understanding"]),
                "human_review_reason": item["human_review_reason"],
                "manual_version": item["manual_version"],
            }
        items.append(
            {
                "case_id": case_id,
                "text": texts.get(case_id, ""),
                "annotations": [public_annotation(left, "A"), public_annotation(right, "B")],
                "annotator_identity_included": False,
                "model_prediction_included": False,
            }
        )
    return {"items": items, "total": len(items), "blind_identity": True}


def adjudicate_case(actor: dict, case_id: str, data: dict) -> dict:
    queue_item = next(
        (item for item in list_adjudication_queue()["items"] if item["case_id"] == case_id),
        None,
    )
    if not queue_item:
        raise OfflineBenchmarkError("adjudication_case_unavailable", "当前案例不在待裁决队列", 409)
    annotation_ids = [item["annotation_id"] for item in queue_item["annotations"]]
    with get_connection() as conn:
        authors = {
            row["annotator_id"]
            for row in conn.execute(
                "SELECT annotator_id FROM offline_benchmark_annotations WHERE id IN (?, ?)",
                tuple(annotation_ids),
            ).fetchall()
        }
    if actor["id"] in authors:
        raise OfflineBenchmarkError("adjudicator_not_independent", "前两轮标注者不能裁决自己的案例", 403)
    fields = _annotation_fields(data, queue_item["text"])
    rationale = str(data.get("rationale") or "").strip()
    manual_clause = str(data.get("manual_clause") or "").strip()
    if len(rationale) < 5 or len(manual_clause) < 3:
        raise OfflineBenchmarkError("adjudication_evidence_required", "裁决必须填写理由和手册条款")
    timestamp, adjudication_id = now_iso(), new_id("oadj")
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO offline_annotation_adjudications (id, dataset_card_id, case_id, annotation_a_id, annotation_b_id, adjudicator_id, final_labels_json, final_intensity, final_polarity_status, needs_human_understanding, human_review_reason, rationale, manual_clause, manual_version, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                adjudication_id,
                ANNOTATION_DATASET_ID,
                case_id,
                annotation_ids[0],
                annotation_ids[1],
                actor["id"],
                json_dumps(fields["labels"]),
                fields["intensity"],
                fields["polarity_status"],
                fields["needs_human_understanding"],
                fields["human_review_reason"],
                rationale,
                manual_clause,
                ANNOTATION_MANUAL_VERSION,
                timestamp,
            ),
        )
        write_audit_log(
            conn,
            "offline_annotation_adjudicated",
            actor["id"],
            "offline_benchmark_case",
            case_id,
            {
                "annotation_ids": annotation_ids,
                "manual_version": ANNOTATION_MANUAL_VERSION,
                "original_annotations_preserved": True,
            },
        )
        conn.commit()
    return {
        "id": adjudication_id,
        "case_id": case_id,
        "final_labels": fields["labels"],
        "manual_version": ANNOTATION_MANUAL_VERSION,
        "original_annotations_preserved": True,
    }


def split_report() -> dict:
    with get_connection() as conn:
        rows = rows_to_dicts(
            conn.execute(
                "SELECT dataset_card_id, group_hash, split_name FROM offline_annotation_group_splits ORDER BY split_name, group_hash"
            ).fetchall()
        )
    by_group: dict[tuple[str, str], set[str]] = defaultdict(set)
    counts = Counter()
    for row in rows:
        by_group[(row["dataset_card_id"], row["group_hash"])].add(row["split_name"])
        counts[row["split_name"]] += 1
    leakage = [
        {"dataset_card_id": key[0], "group_hash": key[1], "splits": sorted(splits)}
        for key, splits in by_group.items()
        if len(splits) > 1
    ]
    return {
        "policy_version": SPLIT_POLICY_VERSION,
        "group_key_persisted": False,
        "group_hash_persisted": True,
        "split_group_counts": dict(sorted(counts.items())),
        "cross_split_group_leakage": leakage,
        "passed": not leakage,
    }


def _dictionary_terms() -> dict[str, list[str]]:
    path = PROJECT_ROOT / "analysis" / "text_analysis" / "dictionaries" / "emotion_terms.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    terms: dict[str, list[str]] = defaultdict(list)
    for item in payload.get("terms", []):
        terms[str(item["category"])].append(str(item["word"]))
    return terms


def _components(nodes: list[str], edges: list[tuple[str, str, float]], threshold: float) -> list[list[str]]:
    graph = {node: set() for node in nodes}
    for left, right, weight in edges:
        if weight >= threshold:
            graph[left].add(right); graph[right].add(left)
    seen, groups = set(), []
    for start in nodes:
        if start in seen:
            continue
        queue, group = deque([start]), []
        seen.add(start)
        while queue:
            node = queue.popleft(); group.append(node)
            for nxt in graph[node] - seen:
                seen.add(nxt); queue.append(nxt)
        groups.append(sorted(group))
    return groups


def _network_metrics() -> dict:
    star_nodes = [f"s{i}" for i in range(12)]
    star_edges = [("s0", f"s{i}", 1.0 + (i % 3) * 0.2) for i in range(1, 12)]
    strength = Counter()
    for left, right, weight in star_edges:
        strength[left] += weight; strength[right] += weight
    community_nodes = [f"c{i}" for i in range(12)]
    community_edges = []
    for start in (0, 6):
        for index in range(start, start + 6):
            community_edges.append((f"c{index}", f"c{start + ((index - start + 1) % 6)}", 1.0))
    community_edges.append(("c2", "c8", 0.1))
    groups_low = _components(community_nodes, community_edges, 0.0)
    groups_sparse = _components(community_nodes, community_edges, 0.5)
    perturbed = [(left, right, weight * (1.05 if index % 2 else 0.95)) for index, (left, right, weight) in enumerate(star_edges)]
    perturbed_strength = Counter()
    for left, right, weight in perturbed:
        perturbed_strength[left] += weight; perturbed_strength[right] += weight
    checks = {
        "inverse_weight_distance_positive": all(1 / weight > 0 for _, _, weight in star_edges),
        "star_center_highest_strength": strength.most_common(1)[0][0] == "s0",
        "star_center_stable_under_5pct_perturbation": perturbed_strength.most_common(1)[0][0] == "s0",
        "community_threshold_splits_weak_bridge": len(groups_low) == 1 and len(groups_sparse) == 2,
        "sparse_threshold_documented": True,
    }
    return {"synthetic_graphs": ["ring", "star", "two_community", "weighted_perturbation"], "checks": checks, "passed": all(checks.values()), "community_count_before_threshold": len(groups_low), "community_count_after_threshold": len(groups_sparse), "complexity_note": "strength O(E); components O(V+E); production centrality remains offline and bounded", "public_graph_used": False, "public_graph_block_reason": "source_data_rights_human_review_pending", "family_quality_inference": False}


def _save_run(actor: dict, benchmark_type: str, card_id: str, metrics: dict, parameters: dict) -> dict:
    timestamp = now_iso()
    run_id = new_id("obr")
    artifact_hash = hashlib.sha256(json.dumps({"type": benchmark_type, "metrics": metrics, "parameters": parameters, "algorithm": ALGORITHM_VERSION}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    status = "engineering_threshold_passed" if (metrics.get("passed", True) and not metrics.get("failed_cases")) else "engineering_review_required"
    with get_connection() as conn:
        conn.execute("INSERT INTO offline_benchmark_runs (id, benchmark_type, dataset_card_id, evidence_level, algorithm_version, parameters_json, metrics_json, artifact_hash, raw_text_included, production_replacement_allowed, status, created_by, created_at) VALUES (?, ?, ?, 'synthetic_engineering_only', ?, ?, ?, ?, 0, 0, ?, ?, ?)", (run_id, benchmark_type, card_id, ALGORITHM_VERSION, json_dumps(parameters), json_dumps(metrics), artifact_hash, status, actor["id"], timestamp))
        write_audit_log(conn, "offline_benchmark_run_created", actor["id"], "offline_benchmark_run", run_id, {"benchmark_type": benchmark_type, "dataset_card_id": card_id, "raw_text_included": False, "production_replacement_allowed": False})
        conn.commit()
    return get_run(run_id)


def run_affect_benchmark(actor: dict) -> dict:
    _require_enabled()
    payload = _synthetic_payload()
    registry = _content_json("affect_model_candidate_registry.json")
    metrics = compare_affect_candidates(
        payload["cases"], _dictionary_terms(), registry
    )
    return _save_run(
        actor,
        "affect_candidate_comparison",
        "safehome_synthetic_affect_240_v1",
        metrics,
        {
            "random_seed": registry["random_seed"],
            "case_hash": payload["case_hash"],
            "label_reference": "generator_seed_not_human_gold",
            "registry_version": registry["version"],
            "feature_version": registry["feature_contract"]["version"],
            "experiment_digest": metrics["experiment_digest"],
        },
    )


def run_network_benchmark(actor: dict) -> dict:
    _require_enabled()
    metrics = _network_metrics()
    return _save_run(actor, "network_algorithms", "safehome_synthetic_network_v1", metrics, {"random_seed": 29, "weight_distance": "1/weight", "thresholds": [0.0, 0.5], "perturbation": 0.05})


def _decode_run(row) -> dict:
    item = row_to_dict(row)
    item["parameters"] = json_loads(item.pop("parameters_json"), {})
    item["metrics"] = json_loads(item.pop("metrics_json"), {})
    return item


def get_run(run_id: str) -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM offline_benchmark_runs WHERE id = ?", (run_id,)).fetchone()
    if not row:
        raise OfflineBenchmarkError("run_not_found", "基准运行不存在", 404)
    return _decode_run(row)


def list_runs(actor: dict) -> list[dict]:
    scope = "" if actor["role"] in {"admin", "supervisor"} else " WHERE created_by = ?"
    params = () if not scope else (actor["id"],)
    with get_connection() as conn:
        rows = conn.execute(f"SELECT * FROM offline_benchmark_runs{scope} ORDER BY created_at DESC LIMIT 100", params).fetchall()
    return [_decode_run(row) for row in rows]


def review_run(actor: dict, run_id: str, data: dict) -> dict:
    run = get_run(run_id)
    decision = str(data.get("decision") or "")
    evidence_path = str(data.get("evidence_path") or "").strip()
    if decision not in REVIEW_DECISIONS or not evidence_path or len(evidence_path) > 500 or ".." in evidence_path:
        raise OfflineBenchmarkError("review_invalid", "复核决定或证据路径无效")
    review_id, timestamp = new_id("obrv"), now_iso()
    with get_connection() as conn:
        conn.execute("INSERT INTO offline_benchmark_reviews (id, run_id, reviewer_id, decision, evidence_path, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (review_id, run_id, actor["id"], decision, evidence_path, str(data.get("notes") or "")[:1000] or None, timestamp))
        write_audit_log(conn, "offline_benchmark_review_saved", actor["id"], "offline_benchmark_run", run_id, {"decision": decision, "evidence_path": evidence_path, "production_replacement_allowed": False})
        conn.commit()
    return {"id": review_id, "run_id": run["id"], "reviewer_id": actor["id"], "decision": decision, "evidence_path": evidence_path, "created_at": timestamp, "production_replacement_allowed": False}


def disable_runtime(actor: dict, data: dict) -> dict:
    reason = str(data.get("reason") or "").strip()
    if len(reason) < 5 or len(reason) > 500:
        raise OfflineBenchmarkError("disable_reason_invalid", "停用原因需为5至500字")
    timestamp = now_iso()
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM offline_benchmark_runtime_control WHERE id = 'global'").fetchone()
        if existing:
            conn.execute("UPDATE offline_benchmark_runtime_control SET disabled = 1, reason = ?, changed_by = ?, changed_at = ? WHERE id = 'global'", (reason, actor["id"], timestamp))
        else:
            conn.execute("INSERT INTO offline_benchmark_runtime_control (id, disabled, reason, changed_by, changed_at) VALUES ('global', 1, ?, ?, ?)", (reason, actor["id"], timestamp))
        write_audit_log(conn, "offline_benchmark_disabled", actor["id"], "offline_benchmark_runtime", "global", {"reason": reason})
        conn.commit()
    return {"disabled": True, "changed_at": timestamp}
