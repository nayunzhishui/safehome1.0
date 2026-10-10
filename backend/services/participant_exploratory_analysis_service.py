"""Participant-visible descriptive analysis from structured self records only."""

from __future__ import annotations

from collections import Counter, defaultdict


MINIMUM_RECORDS = 5
MAXIMUM_RECORDS = 100
MINIMUM_PAIR_SUPPORT = 2
TREND_MINIMUM_PER_HALF = 3
# Child-emotion answers that say the parent could not tell are not paired.
UNCERTAIN_CHILD_EMOTIONS = {"不确定", "说不清", "不知道"}


def _mean(values: list[int]) -> float | None:
    return round(sum(values) / len(values), 1) if values else None


def _intensity_trend(usable_rows: list[tuple]) -> dict:
    """Compare the newer half of the records with the older half (rows newest first)."""

    base = {"method": "recent_vs_earlier_halves", "minimum_required": 2 * TREND_MINIMUM_PER_HALF}
    if len(usable_rows) < 2 * TREND_MINIMUM_PER_HALF:
        return {
            **base,
            "available": False,
            "summary_text": f"至少需要 {2 * TREND_MINIMUM_PER_HALF} 条可用记录，才比较前后两段的强度。",
        }
    half = len(usable_rows) // 2
    recent = [row[2] for row in usable_rows[:half]]
    earlier = [row[2] for row in usable_rows[half:]]
    recent_average, earlier_average = _mean(recent), _mean(earlier)
    difference = round(recent_average - earlier_average, 1)
    if difference > 0:
        comparison = f"高于之前 {len(earlier)} 条的 {earlier_average}"
    elif difference < 0:
        comparison = f"低于之前 {len(earlier)} 条的 {earlier_average}"
    else:
        comparison = f"与之前 {len(earlier)} 条持平"
    return {
        **base,
        "available": True,
        "recent_count": len(recent),
        "earlier_count": len(earlier),
        "recent_average_intensity": recent_average,
        "earlier_average_intensity": earlier_average,
        "difference": difference,
        "summary_text": f"最近 {len(recent)} 条记录的平均强度为 {recent_average}，{comparison}。",
        "next_check_text": "强度会受场景和当天状态影响，这里只作自我回看，不代表好转或变差。",
    }


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
        "trend": _intensity_trend([]),
        "summary_text": "当前没有可汇总的结构化情绪标签。",
        "next_check_text": "继续记录具体情境、情绪名称和强度后再比较。",
    }


def _empty_parent_child(paired_record_count: int = 0) -> dict:
    return {
        "method": "parent_child_emotion_cooccurrence",
        "paired_record_count": paired_record_count,
        "minimum_pair_support": MINIMUM_PAIR_SUPPORT,
        "pairs": [],
        "suppressed_pair_count": 0,
        "summary_text": "当前没有可汇总的家长与孩子情绪组合。",
        "next_check_text": "这里只描述两种情绪在同一次记录里一起出现，不代表谁引起了谁。",
        "causal_interpretation_allowed": False,
    }


def _parent_child_pairs(usable_rows: list[tuple]) -> dict:
    paired = [
        (emotion, child_emotion, intensity, child_intensity)
        for _scene, emotion, intensity, child_emotion, child_intensity in usable_rows
        if child_emotion and child_emotion not in UNCERTAIN_CHILD_EMOTIONS
    ]
    if not paired:
        return _empty_parent_child()
    pair_counts: Counter[tuple[str, str]] = Counter()
    parent_counts: Counter[str] = Counter()
    parent_intensities: defaultdict[tuple[str, str], list[int]] = defaultdict(list)
    child_intensities: defaultdict[tuple[str, str], list[int]] = defaultdict(list)
    for emotion, child_emotion, intensity, child_intensity in paired:
        pair_counts[(emotion, child_emotion)] += 1
        parent_counts[emotion] += 1
        parent_intensities[(emotion, child_emotion)].append(intensity)
        if child_intensity is not None:
            child_intensities[(emotion, child_emotion)].append(child_intensity)
    supported = sorted(
        ((pair, support) for pair, support in pair_counts.items() if support >= MINIMUM_PAIR_SUPPORT),
        key=lambda item: (-item[1], item[0][0], item[0][1]),
    )[:8]
    pairs = [
        {
            "parent_emotion": emotion,
            "child_emotion": child_emotion,
            "support": support,
            "share_of_parent_emotion": round(support / parent_counts[emotion], 2),
            "average_parent_intensity": _mean(parent_intensities[(emotion, child_emotion)]),
            "average_child_intensity": _mean(child_intensities[(emotion, child_emotion)]),
        }
        for (emotion, child_emotion), support in supported
    ]
    result = _empty_parent_child(len(paired))
    result["pairs"] = pairs
    result["suppressed_pair_count"] = sum(1 for support in pair_counts.values() if support < MINIMUM_PAIR_SUPPORT)
    if pairs:
        top = pairs[0]
        result["summary_text"] = (
            f"{len(paired)} 条记录同时填写了孩子的情绪；重复出现至少 {MINIMUM_PAIR_SUPPORT} 次的组合有 {len(pairs)} 个，"
            f"最常见的是你“{top['parent_emotion']}”时孩子“{top['child_emotion']}”（{top['support']} 次）。"
        )
    else:
        result["summary_text"] = (
            f"{len(paired)} 条记录同时填写了孩子的情绪，暂时没有重复至少 {MINIMUM_PAIR_SUPPORT} 次的组合。"
        )
    return result


def _has_unresolved_high_risk(conn, user_id: str) -> bool:
    """Withhold the view while any high-risk diary or feedback review is still open.

    Diaries are screened when saved (review source ``diary``); feedback without a
    diary is reviewed under source ``feedback``. A high-risk feedback that has no
    review of either kind is treated as unresolved.
    """

    open_review = conn.execute(
        """
        SELECT 1
        FROM risk_review_records
        WHERE user_id = ?
          AND risk_level = 'high'
          AND source_type IN ('diary', 'feedback')
          AND review_status <> 'closed'
        LIMIT 1
        """,
        (user_id,),
    ).fetchone()
    if open_review is not None:
        return True
    unreviewed = conn.execute(
        """
        SELECT 1
        FROM feedback_results AS feedback
        WHERE feedback.user_id = ?
          AND feedback.risk_level = 'high'
          AND NOT EXISTS (
              SELECT 1
              FROM risk_review_records AS review
              WHERE (review.source_type = 'feedback' AND review.source_id = feedback.id)
                 OR (review.source_type = 'diary' AND review.source_id = feedback.diary_id)
          )
        LIMIT 1
        """,
        (user_id,),
    ).fetchone()
    return unreviewed is not None


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
            "parent_child": _empty_parent_child(),
        }

    record_count = min(
        int(conn.execute("SELECT COUNT(*) AS count FROM emotion_diaries WHERE user_id = ?", (user_id,)).fetchone()["count"]),
        MAXIMUM_RECORDS,
    )
    if _has_unresolved_high_risk(conn, user_id):
        return {
            **base,
            "availability": "withheld",
            "record_count": record_count,
            "reason": "近期记录包含需要优先人工关注的安全线索，探索性分析暂不展示。",
            "human_review_required": True,
            "affect": _empty_affect(record_count),
            "interaction_network": _empty_network(record_count),
            "parent_child": _empty_parent_child(),
        }

    rows = conn.execute(
        """
        SELECT scene, parent_emotion, parent_emotion_intensity, child_emotion, child_emotion_intensity
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
        child_emotion = str(row["child_emotion"] or "").strip()
        try:
            child_intensity = int(row["child_emotion_intensity"])
        except (TypeError, ValueError):
            child_intensity = None
        if child_intensity is not None and not 0 <= child_intensity <= 10:
            child_intensity = None
        usable_rows.append((scene, emotion, intensity, child_emotion, child_intensity))
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
            "parent_child": _empty_parent_child(),
        }

    emotion_counts: Counter[str] = Counter()
    emotion_intensities: defaultdict[str, list[int]] = defaultdict(list)
    scene_counts: Counter[str] = Counter()
    pair_counts: Counter[tuple[str, str]] = Counter()
    pair_intensities: defaultdict[tuple[str, str], list[int]] = defaultdict(list)
    all_intensities: list[int] = []
    for scene, emotion, intensity, _child_emotion, _child_intensity in usable_rows:
        emotion_counts[emotion] += 1
        emotion_intensities[emotion].append(intensity)
        all_intensities.append(intensity)
        scene_counts[scene] += 1
        pair_counts[(scene, emotion)] += 1
        pair_intensities[(scene, emotion)].append(intensity)

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
        if support >= MINIMUM_PAIR_SUPPORT
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
    edges = []
    for scene, emotion, support in supported_pairs:
        # share_in_scene: how often this emotion was recorded in this scene;
        # lift > 1 means it is recorded here more often than across all scenes.
        share_in_scene = support / scene_counts[scene]
        share_overall = emotion_counts[emotion] / usable_record_count
        edges.append(
            {
                "source": scene_ids[scene],
                "target": emotion_ids[emotion],
                "scene": scene,
                "emotion": emotion,
                "support": support,
                "share_in_scene": round(share_in_scene, 2),
                "share_overall": round(share_overall, 2),
                "lift": round(share_in_scene / share_overall, 2),
                "average_intensity": _mean(pair_intensities[(scene, emotion)]),
            }
        )
    supported_record_count = sum(support for _scene, _emotion, support in supported_pairs)
    suppressed_pair_count = sum(1 for support in pair_counts.values() if support < MINIMUM_PAIR_SUPPORT)
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
            "trend": _intensity_trend(usable_rows),
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
            "minimum_edge_support": MINIMUM_PAIR_SUPPORT,
            "individual_metrics": False,
            "relationship_quality_judgement": False,
        },
        "parent_child": _parent_child_pairs(usable_rows),
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
