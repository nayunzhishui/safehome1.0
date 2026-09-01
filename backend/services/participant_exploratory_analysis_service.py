"""Participant-visible descriptive analysis from structured self records only."""

from __future__ import annotations

from collections import Counter, defaultdict


MINIMUM_RECORDS = 5
MAXIMUM_RECORDS = 100


def _empty_affect(
    record_count: int = 0,
    usable_record_count: int = 0,
    excluded_record_count: int = 0,
) -> dict:
    return {
        "method": "self_recorded_emotion_labels",
        "record_count": record_count,
        "usable_record_count": usable_record_count,
        "excluded_record_count": excluded_record_count,
        "category_count": 0,
        "overall_average_intensity": None,
        "intensity_range": None,
        "most_frequent_labels": [],
        "items": [],
        "summary_text": "当前没有可汇总的结构化情绪标签。",
        "next_check_text": "继续记录具体情境、情绪名称和强度后再比较。",
    }


def build_participant_exploratory_analysis(conn, user_id: str) -> dict:
    """Return non-diagnostic affect and scene-emotion co-occurrence summaries."""

    user = conn.execute(
        "SELECT role FROM users WHERE id = ? AND COALESCE(status, 'active') != 'deleted'",
        (user_id,),
    ).fetchone()
    if user is None:
        raise KeyError(user_id)

    base = {
        "schema": "safehome.participant-exploratory-analysis.v1",
        "scope": "self_structured_diaries",
        "minimum_required": MINIMUM_RECORDS,
        "raw_text_included": False,
        "other_participant_data_included": False,
        "human_review_required": False,
        "boundary_notice": "这些内容只描述近期记录中的情绪与场景共现，不评价人格、关系质量，也不构成诊断或风险结论。",
    }
    if str(user["role"] or "") not in {"parent", "adult"}:
        return {
            **base,
            "availability": "ineligible",
            "record_count": 0,
            "reason": "第二阶段仅向已登录的成人参与者开放。",
            "affect": _empty_affect(),
            "interaction_network": _empty_network(),
        }

    record_count = min(
        int(conn.execute("SELECT COUNT(*) FROM emotion_diaries WHERE user_id = ?", (user_id,)).fetchone()[0]),
        MAXIMUM_RECORDS,
    )
    high_risk = conn.execute(
        """
        SELECT 1
        FROM feedback_results AS feedback
        WHERE feedback.user_id = ?
          AND feedback.risk_level = 'high'
          AND (
              NOT EXISTS (
                  SELECT 1
                  FROM risk_review_records AS review
                  WHERE review.source_type = 'feedback'
                    AND review.source_id = feedback.id
              )
              OR EXISTS (
                  SELECT 1
                  FROM risk_review_records AS review
                  WHERE review.source_type = 'feedback'
                    AND review.source_id = feedback.id
                    AND review.review_status <> 'closed'
              )
          )
        LIMIT 1
        """,
        (user_id,),
    ).fetchone()
    if high_risk is not None:
        return {
            **base,
            "availability": "withheld",
            "record_count": record_count,
            "reason": "近期记录包含需要优先人工关注的安全线索，探索性分析暂不展示。",
            "human_review_required": True,
            "affect": _empty_affect(record_count),
            "interaction_network": _empty_network(record_count),
        }

    rows = conn.execute(
        """
        SELECT scene, parent_emotion, parent_emotion_intensity
        FROM emotion_diaries
        WHERE user_id = ?
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        (user_id, MAXIMUM_RECORDS),
    ).fetchall()
    record_count = len(rows)
    usable_rows = []
    for row in rows:
        scene = str(row["scene"] or "").strip()
        emotion = str(row["parent_emotion"] or "").strip()
        try:
            intensity = int(row["parent_emotion_intensity"])
        except (TypeError, ValueError):
            continue
        if not scene or not emotion or not 0 <= intensity <= 10:
            continue
        usable_rows.append((scene, emotion, intensity))
    usable_record_count = len(usable_rows)
    excluded_record_count = record_count - usable_record_count
    if record_count < MINIMUM_RECORDS or usable_record_count < MINIMUM_RECORDS:
        reason = (
            f"至少需要 {MINIMUM_RECORDS} 条情绪记录后再生成近期线索。"
            if record_count < MINIMUM_RECORDS
            else f"当前只有 {usable_record_count} 条记录可用于汇总，至少需要 {MINIMUM_RECORDS} 条包含情境、情绪和有效强度的记录。"
        )
        return {
            **base,
            "availability": "insufficient",
            "record_count": record_count,
            "usable_record_count": usable_record_count,
            "excluded_record_count": excluded_record_count,
            "reason": reason,
            "affect": _empty_affect(record_count, usable_record_count, excluded_record_count),
            "interaction_network": _empty_network(record_count, usable_record_count, excluded_record_count),
        }

    emotion_counts: Counter[str] = Counter()
    emotion_intensities: defaultdict[str, list[int]] = defaultdict(list)
    scene_counts: Counter[str] = Counter()
    pair_counts: Counter[tuple[str, str]] = Counter()
    all_intensities: list[int] = []
    for scene, emotion, intensity in usable_rows:
        emotion_counts[emotion] += 1
        emotion_intensities[emotion].append(intensity)
        all_intensities.append(intensity)
        scene_counts[scene] += 1
        pair_counts[(scene, emotion)] += 1

    affect_items = [
        {
            "label": label,
            "count": count,
            "average_intensity": round(sum(emotion_intensities[label]) / len(emotion_intensities[label]), 1),
        }
        for label, count in sorted(emotion_counts.items(), key=lambda item: (-item[1], item[0]))[:8]
    ]
    highest_count = max(emotion_counts.values(), default=0)
    most_frequent_labels = sorted(
        label for label, count in emotion_counts.items() if count == highest_count
    )
    overall_average_intensity = round(sum(all_intensities) / len(all_intensities), 1)
    intensity_range = {"minimum": min(all_intensities), "maximum": max(all_intensities)}
    eligible_pairs = [
        (scene, emotion, support)
        for (scene, emotion), support in sorted(pair_counts.items(), key=lambda item: (-item[1], item[0][0], item[0][1]))
        if support >= 2
    ]
    supported_pairs = eligible_pairs[:12]
    scene_labels = sorted({scene for scene, _emotion, _support in supported_pairs})
    emotion_labels = sorted({emotion for _scene, emotion, _support in supported_pairs})
    scene_ids = {label: f"scene:{index}" for index, label in enumerate(scene_labels)}
    emotion_ids = {label: f"emotion:{index}" for index, label in enumerate(emotion_labels)}
    nodes = [
        {"id": scene_ids[label], "type": "scene", "label": label, "support": scene_counts[label]}
        for label in scene_labels
    ] + [
        {"id": emotion_ids[label], "type": "emotion", "label": label, "support": emotion_counts[label]}
        for label in emotion_labels
    ]
    edges = [
        {"source": scene_ids[scene], "target": emotion_ids[emotion], "scene": scene, "emotion": emotion, "support": support}
        for scene, emotion, support in supported_pairs
    ]
    supported_record_count = sum(support for _scene, _emotion, support in supported_pairs)
    suppressed_pair_count = sum(1 for support in pair_counts.values() if support < 2)
    omitted_supported_pair_count = max(0, len(eligible_pairs) - len(supported_pairs))
    record_coverage_rate = (
        round(supported_record_count / usable_record_count, 4)
        if usable_record_count
        else 0.0
    )

    return {
        **base,
        "availability": "available",
        "record_count": record_count,
        "usable_record_count": usable_record_count,
        "excluded_record_count": excluded_record_count,
        "affect": {
            "method": "self_recorded_emotion_labels",
            "record_count": record_count,
            "usable_record_count": usable_record_count,
            "excluded_record_count": excluded_record_count,
            "category_count": len(emotion_counts),
            "overall_average_intensity": overall_average_intensity,
            "intensity_range": intensity_range,
            "most_frequent_labels": most_frequent_labels,
            "items": affect_items,
            "summary_text": (
                f"{record_count} 条记录中有 {usable_record_count} 条可用于汇总，包含 {len(emotion_counts)} 类自填情绪；"
                f"整体平均强度 {overall_average_intensity}，范围 {intensity_range['minimum']}—{intensity_range['maximum']}。"
            ),
            "next_check_text": "后续只与本人使用同一记录方式的新记录比较，不自动解释好坏。",
        },
        "interaction_network": {
            "method": "scene_emotion_cooccurrence",
            "nodes": nodes,
            "edges": edges,
            "summary": {
                "record_count": record_count,
                "usable_record_count": usable_record_count,
                "excluded_record_count": excluded_record_count,
                "supported_record_count": supported_record_count,
                "record_coverage_rate": record_coverage_rate,
                "scene_count": len(scene_labels),
                "emotion_count": len(emotion_labels),
                "node_count": len(nodes),
                "edge_count": len(edges),
                "suppressed_pair_count": suppressed_pair_count,
                "omitted_supported_pair_count": omitted_supported_pair_count,
                "summary_text": (
                    f"展示 {len(edges)} 条场景—情绪共现线索，覆盖 {supported_record_count}/{usable_record_count} 条可用记录；"
                    f"{suppressed_pair_count} 个只出现 1 次的组合未展示。"
                ),
                "next_check_text": "继续记录后再看相同组合是否重复出现；不据此评价关系质量。",
            },
            "minimum_edge_support": 2,
            "individual_metrics": False,
            "relationship_quality_judgement": False,
        },
    }


def _empty_network(
    record_count: int = 0,
    usable_record_count: int = 0,
    excluded_record_count: int = 0,
) -> dict:
    return {
        "method": "scene_emotion_cooccurrence",
        "nodes": [],
        "edges": [],
        "summary": {
            "record_count": record_count,
            "usable_record_count": usable_record_count,
            "excluded_record_count": excluded_record_count,
            "supported_record_count": 0,
            "record_coverage_rate": 0.0,
            "scene_count": 0,
            "emotion_count": 0,
            "node_count": 0,
            "edge_count": 0,
            "suppressed_pair_count": 0,
            "omitted_supported_pair_count": 0,
            "summary_text": "当前没有达到最小支持度的场景—情绪共现线索。",
            "next_check_text": "继续记录后再看相同组合是否重复出现。",
        },
        "minimum_edge_support": 2,
        "individual_metrics": False,
        "relationship_quality_judgement": False,
    }
