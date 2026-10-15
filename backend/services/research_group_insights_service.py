"""Group-level emotion summaries and emotion networks from consented adult diaries.

Researchers get aggregates only: no raw text, no participant identifiers and no
individual metrics. Groups smaller than ``MINIMUM_PARTICIPANTS`` return nothing,
and any category, link or week backed by fewer than the cell threshold is merged
away before the payload is built.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from statistics import median

from services.emotion_vocabulary_service import EmotionVocabulary, load_emotion_vocabulary
from services.group_network_analysis_service import (
    _adjacency,
    _average_clustering,
    _component_sizes,
    _degree_centralization,
)


WINDOW_OPTIONS = (30, 90, 180, 365)
DEFAULT_WINDOW_DAYS = 90
MINIMUM_PARTICIPANTS = 10
MINIMUM_CELL_PARTICIPANTS = 3
MINIMUM_WEEK_PARTICIPANTS = 5
MAX_LABELS = 10
MAX_LINKS = 12
MAX_PAIRS = 8
MAX_CENTRAL = 3
# Weeks are cut on Beijing time so they match what participants and staff see.
LOCAL_OFFSET = timedelta(hours=8)
UNCERTAIN_CHILD_EMOTIONS = {"不确定", "说不清", "不知道"}
INTENSITY_BANDS = (
    ("low", "较低（0–3）", 0, 3),
    ("middle", "中等（4–6）", 4, 6),
    ("high", "较高（7–10）", 7, 10),
)
BOUNDARY_NOTICE = (
    "群体层面的描述性统计：只含明确同意研究使用的成人参与者，不含原文和个人结果；"
    "共同出现不代表因果，不用于推断个人、评价家庭关系或诊断。"
)
CONSENT_RULE = "只纳入研究同意（研究用途或去标识化研究）最新为“同意”、且两类研究同意都没有撤回的家长或成人账号。"
# Latest research consent of either kind is "agreed", and neither kind is withdrawn.
CONSENTED_DIARY_OWNER = """
    EXISTS (
        SELECT 1 FROM consent_records granted
        WHERE granted.user_id = d.user_id
          AND granted.consent_type IN ('anonymous_research', 'research_authorization')
          AND granted.agreed = 1
          AND granted.created_at = (
              SELECT MAX(granted_latest.created_at) FROM consent_records granted_latest
              WHERE granted_latest.user_id = granted.user_id
                AND granted_latest.consent_type = granted.consent_type
          )
    )
    AND NOT EXISTS (
        SELECT 1 FROM consent_records withdrawn
        WHERE withdrawn.user_id = d.user_id
          AND withdrawn.consent_type IN ('anonymous_research', 'research_authorization')
          AND withdrawn.agreed = 0
          AND withdrawn.created_at = (
              SELECT MAX(withdrawn_latest.created_at) FROM consent_records withdrawn_latest
              WHERE withdrawn_latest.user_id = withdrawn.user_id
                AND withdrawn_latest.consent_type = withdrawn.consent_type
          )
    )
"""


def normalize_window(value) -> int:
    try:
        days = int(value)
    except (TypeError, ValueError):
        return DEFAULT_WINDOW_DAYS
    return days if days in WINDOW_OPTIONS else DEFAULT_WINDOW_DAYS


def _mean(values: list[int]) -> float | None:
    return round(sum(values) / len(values), 1) if values else None


def _parse_time(value) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _usable_record(row, vocabulary: EmotionVocabulary) -> dict | None:
    """Emotions are counted by category; the main (first) one carries the intensity."""

    scene = str(row["scene"] or "").strip()
    emotions = vocabulary.labels(row["parent_emotion"], "parent")
    emotion = emotions[0] if emotions else ""
    created_at = _parse_time(row["created_at"])
    try:
        intensity = int(row["parent_emotion_intensity"])
    except (TypeError, ValueError):
        return None
    if not scene or not emotion or created_at is None or not 0 <= intensity <= 10:
        return None
    child_emotion = vocabulary.primary_label(row["child_emotion"], "child")
    try:
        child_intensity = int(row["child_emotion_intensity"])
    except (TypeError, ValueError):
        child_intensity = None
    if child_intensity is not None and not 0 <= child_intensity <= 10:
        child_intensity = None
    return {
        "user": str(row["user_id"]),
        "scene": scene,
        "emotion": emotion,
        "emotions": emotions,
        "intensity": intensity,
        "child_emotion": "" if child_emotion in UNCERTAIN_CHILD_EMOTIONS else child_emotion,
        "child_intensity": child_intensity,
        "created_at": created_at,
    }


def _category_rows(records: list[dict], key: str, participant_total: int) -> tuple[list[dict], dict]:
    groups: defaultdict[str, list[dict]] = defaultdict(list)
    for record in records:
        groups[record[key]].append(record)
    rows: list[dict] = []
    hidden_categories = 0
    hidden_records = 0
    for label, items in groups.items():
        participants = len({item["user"] for item in items})
        if participants < MINIMUM_CELL_PARTICIPANTS:
            hidden_categories += 1
            hidden_records += len(items)
            continue
        rows.append(
            {
                "label": label,
                "record_count": len(items),
                "participant_count": participants,
                "record_share": round(len(items) / len(records), 3),
                "participant_share": round(participants / participant_total, 3),
                "average_intensity": _mean([item["intensity"] for item in items]),
            }
        )
    rows.sort(key=lambda item: (-item["participant_count"], -item["record_count"], item["label"]))
    return rows[:MAX_LABELS], {
        "hidden_category_count": hidden_categories,
        "hidden_record_count": hidden_records,
        "omitted_category_count": max(0, len(rows) - MAX_LABELS),
    }


def _intensity_bands(records: list[dict]) -> list[dict]:
    bands = []
    for key, label, low, high in INTENSITY_BANDS:
        count = sum(1 for item in records if low <= item["intensity"] <= high)
        bands.append({"key": key, "label": label, "record_count": count, "record_share": round(count / len(records), 3)})
    return bands


def _weekly_trend(records: list[dict]) -> dict:
    weeks: defaultdict[str, list[dict]] = defaultdict(list)
    for record in records:
        local_day = (record["created_at"] + LOCAL_OFFSET).date()
        week_start = local_day - timedelta(days=local_day.weekday())
        weeks[week_start.isoformat()].append(record)
    items = []
    suppressed = 0
    for week_start in sorted(weeks):
        week_records = weeks[week_start]
        participants = len({item["user"] for item in week_records})
        if participants < MINIMUM_WEEK_PARTICIPANTS:
            suppressed += 1
            continue
        items.append(
            {
                "week_start": week_start,
                "participant_count": participants,
                "record_count": len(week_records),
                "average_intensity": _mean([item["intensity"] for item in week_records]),
            }
        )
    return {
        "method": "beijing_calendar_weeks",
        "minimum_week_participants": MINIMUM_WEEK_PARTICIPANTS,
        "items": items,
        "suppressed_week_count": suppressed,
    }


def _parent_child_pairs(records: list[dict]) -> dict:
    paired = [item for item in records if item["child_emotion"]]
    groups: defaultdict[tuple[str, str], list[dict]] = defaultdict(list)
    parent_totals: Counter[str] = Counter()
    for item in paired:
        groups[(item["emotion"], item["child_emotion"])].append(item)
        parent_totals[item["emotion"]] += 1
    rows = []
    hidden = 0
    for (emotion, child_emotion), items in groups.items():
        participants = len({item["user"] for item in items})
        if participants < MINIMUM_CELL_PARTICIPANTS:
            hidden += 1
            continue
        child_values = [item["child_intensity"] for item in items if item["child_intensity"] is not None]
        rows.append(
            {
                "parent_emotion": emotion,
                "child_emotion": child_emotion,
                "record_count": len(items),
                "participant_count": participants,
                "share_of_parent_emotion": round(len(items) / parent_totals[emotion], 3),
                "average_parent_intensity": _mean([item["intensity"] for item in items]),
                "average_child_intensity": _mean(child_values),
            }
        )
    rows.sort(key=lambda item: (-item["participant_count"], -item["record_count"], item["parent_emotion"], item["child_emotion"]))
    return {
        "method": "parent_child_emotion_cooccurrence",
        "paired_record_count": len(paired),
        "pairs": rows[:MAX_PAIRS],
        "hidden_pair_count": hidden,
        "causal_interpretation_allowed": False,
    }


def _scene_emotion_links(records: list[dict]) -> dict:
    scene_totals = Counter(item["scene"] for item in records)
    emotion_totals = Counter(item["emotion"] for item in records)
    groups: defaultdict[tuple[str, str], list[dict]] = defaultdict(list)
    for item in records:
        groups[(item["scene"], item["emotion"])].append(item)
    links = []
    hidden = 0
    for (scene, emotion), items in groups.items():
        participants = len({item["user"] for item in items})
        if participants < MINIMUM_CELL_PARTICIPANTS:
            hidden += 1
            continue
        share_in_scene = len(items) / scene_totals[scene]
        share_overall = emotion_totals[emotion] / len(records)
        links.append(
            {
                "scene": scene,
                "emotion": emotion,
                "record_count": len(items),
                "participant_count": participants,
                "share_in_scene": round(share_in_scene, 3),
                "share_overall": round(share_overall, 3),
                "lift": round(share_in_scene / share_overall, 2),
                "average_intensity": _mean([item["intensity"] for item in items]),
            }
        )
    links.sort(key=lambda item: (-item["participant_count"], -item["lift"], item["scene"], item["emotion"]))
    return {
        "method": "scene_emotion_cooccurrence",
        "links": links[:MAX_LINKS],
        "hidden_link_count": hidden,
        "omitted_link_count": max(0, len(links) - MAX_LINKS),
    }


def _emotion_sets(records: list[dict]) -> dict[str, set[str]]:
    # Every chosen emotion category counts toward the participant's set, not only the main one.
    sets: defaultdict[str, set[str]] = defaultdict(set)
    for item in records:
        sets[item["user"]].update(item.get("emotions") or [item["emotion"]])
    return sets


def _pair_weights(emotion_sets: dict[str, set[str]], nodes: set[str]) -> Counter[tuple[str, str]]:
    weights: Counter[tuple[str, str]] = Counter()
    for emotions in emotion_sets.values():
        ordered = sorted(emotions & nodes)
        for index, first in enumerate(ordered):
            for second in ordered[index + 1:]:
                weights[(first, second)] += 1
    return weights


def _emotion_network(records: list[dict], window_start: datetime, window_days: int) -> dict:
    """Emotions are linked when the same participant recorded both within the window."""

    emotion_sets = _emotion_sets(records)
    node_support = Counter(emotion for emotions in emotion_sets.values() for emotion in emotions)
    nodes = {emotion for emotion, support in node_support.items() if support >= MINIMUM_CELL_PARTICIPANTS}
    weights = _pair_weights(emotion_sets, nodes)
    edges = [
        {"source": first, "target": second, "weight": weight}
        for (first, second), weight in weights.items()
        if weight >= MINIMUM_CELL_PARTICIPANTS
    ]
    edges.sort(key=lambda item: (-item["weight"], item["source"], item["target"]))
    node_count = len(nodes)
    edge_count = len(edges)
    graph = _adjacency(nodes, edges)
    strength = Counter()
    for edge in edges:
        strength[edge["source"]] += edge["weight"]
        strength[edge["target"]] += edge["weight"]
    central = [
        {"emotion": emotion, "linked_emotion_count": len(graph[emotion]), "link_strength": strength[emotion]}
        for emotion in sorted(nodes, key=lambda label: (-strength[label], -len(graph[label]), label))
        if strength[emotion]
    ][:MAX_CENTRAL]

    midpoint = window_start + timedelta(days=window_days / 2)
    earlier = _pair_weights(_emotion_sets([item for item in records if item["created_at"] < midpoint]), nodes)
    later = _pair_weights(_emotion_sets([item for item in records if item["created_at"] >= midpoint]), nodes)
    persistent = sum(1 for edge in edges if earlier[(edge["source"], edge["target"])] and later[(edge["source"], edge["target"])])

    return {
        "method": "participant_level_emotion_cooccurrence",
        "node_definition": "情绪名称；至少 3 位参与者在窗口内记录过。",
        "edge_definition": "同一参与者在窗口内记录过这两种情绪；至少 3 位参与者如此才显示。",
        "node_count": node_count,
        "edge_count": edge_count,
        "hidden_node_count": len(node_support) - node_count,
        "density": round(2 * edge_count / (node_count * (node_count - 1)), 3) if node_count > 1 else 0.0,
        "average_clustering": _average_clustering(graph) if node_count else 0.0,
        "degree_centralization": _degree_centralization(graph) if node_count else 0.0,
        "component_count": len(_component_sizes(nodes, edges, MINIMUM_CELL_PARTICIPANTS)) if node_count else 0,
        "central_emotions": central,
        "strongest_links": [
            {"emotion_a": edge["source"], "emotion_b": edge["target"], "participant_count": edge["weight"]}
            for edge in edges[:5]
        ],
        "persistence": {
            "method": "earlier_half_vs_later_half",
            "persistent_link_count": persistent,
            "link_count": edge_count,
            "persistence_rate": round(persistent / edge_count, 3) if edge_count else None,
        },
        "individual_metrics": False,
    }


def _summary_text(participants: int, usable: int, emotions: list[dict], network: dict, window_days: int) -> str:
    parts = [f"近 {window_days} 天，{participants} 位参与者留下 {usable} 条可汇总的情绪记录。"]
    if emotions:
        top = emotions[0]
        parts.append(f"最多人记录的情绪是“{top['label']}”（{top['participant_count']} 人）。")
    if network["strongest_links"]:
        link = network["strongest_links"][0]
        parts.append(f"最常被同一人一起记录的是“{link['emotion_a']}”和“{link['emotion_b']}”（{link['participant_count']} 人）。")
    return "".join(parts)


def build_group_insights(
    conn,
    *,
    window_days: int,
    scope_clause: str,
    scope_params: list,
    scope_label: str,
    now: datetime | None = None,
) -> dict:
    current = now or datetime.now(timezone.utc)
    window_days = normalize_window(window_days)
    window_start = current - timedelta(days=window_days)
    rows = conn.execute(
        f"""
        SELECT d.user_id, d.scene, d.parent_emotion, d.parent_emotion_intensity,
               d.child_emotion, d.child_emotion_intensity, d.created_at
        FROM emotion_diaries d
        JOIN users u ON u.id = d.user_id
        WHERE d.created_at >= ?
          AND u.role IN ('parent', 'adult')
          AND COALESCE(u.status, 'active') != 'deleted'
          AND ({CONSENTED_DIARY_OWNER})
          AND ({scope_clause})
        ORDER BY d.created_at ASC
        """,
        (window_start.isoformat(), *scope_params),
    ).fetchall()
    vocabulary = load_emotion_vocabulary()
    records = [record for record in (_usable_record(row, vocabulary) for row in rows) if record is not None]
    participants = len({record["user"] for record in records})
    base = {
        "schema": "safehome.research-group-insights.v1",
        "generated_at": current.isoformat(),
        "window_days": window_days,
        "window_options": list(WINDOW_OPTIONS),
        "scope": scope_label,
        "data_mode": "consented_production_diaries",
        "thresholds": {
            "minimum_participants": MINIMUM_PARTICIPANTS,
            "minimum_cell_participants": MINIMUM_CELL_PARTICIPANTS,
            "minimum_week_participants": MINIMUM_WEEK_PARTICIPANTS,
        },
        "consent_rule": CONSENT_RULE,
        "raw_text_included": False,
        "individual_results_included": False,
        "boundary_notice": BOUNDARY_NOTICE,
    }
    if participants < MINIMUM_PARTICIPANTS:
        return {
            **base,
            "availability": "suppressed",
            "participant_count": None,
            "participant_count_band": f"少于 {MINIMUM_PARTICIPANTS} 人",
            "reason": (
                f"近 {window_days} 天有可用记录、且同意研究使用的成人参与者少于 {MINIMUM_PARTICIPANTS} 人，"
                "为保护个人信息不展示群体结果。可以放宽时间范围，或等更多参与者同意后再看。"
            ),
        }

    intensities = [record["intensity"] for record in records]
    emotions, emotion_hidden = _category_rows(records, "emotion", participants)
    scenes, scene_hidden = _category_rows(records, "scene", participants)
    network = _emotion_network(records, window_start, window_days)
    return {
        **base,
        "availability": "available",
        "participant_count": participants,
        "participant_count_band": None,
        "record_count": len(rows),
        "usable_record_count": len(records),
        "excluded_record_count": len(rows) - len(records),
        "summary_text": _summary_text(participants, len(records), emotions, network, window_days),
        "affect": {
            "method": "self_recorded_emotion_labels",
            "average_intensity": _mean(intensities),
            "median_intensity": median(intensities),
            "intensity_bands": _intensity_bands(records),
            "emotions": emotions,
            "emotion_hidden": emotion_hidden,
            "scenes": scenes,
            "scene_hidden": scene_hidden,
            "weekly_trend": _weekly_trend(records),
            "parent_child": _parent_child_pairs(records),
        },
        "network": {
            "scene_emotion": _scene_emotion_links(records),
            "emotion_cooccurrence": network,
        },
    }
