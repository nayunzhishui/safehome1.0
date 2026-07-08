"""Offline text analysis for SafeHome research summaries.

The script only emits aggregate counts, affective scores and co-occurrence
edges. It never writes raw user text to the output file.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import jieba
except ImportError as exc:  # pragma: no cover - exercised by environment setup
    raise SystemExit("缺少离线分析依赖 jieba，请运行：python -m pip install -r analysis/text_analysis/requirements.txt") from exc


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
DICTIONARY_DIR = Path(__file__).resolve().parent / "dictionaries"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from database import get_connection, init_db, rows_to_dicts  # noqa: E402


TEXT_SOURCES = [
    {"table": "emotion_diaries", "column": "event_description", "source_type": "user_text", "sentiment_ok": True, "network_ok": True, "is_sensitive": True, "default_export": False, "desensitized": True},
    {"table": "emotion_diaries", "column": "automatic_thought", "source_type": "user_text", "sentiment_ok": True, "network_ok": True, "is_sensitive": True, "default_export": False, "desensitized": True},
    {"table": "emotion_diaries", "column": "behavior", "source_type": "user_text", "sentiment_ok": True, "network_ok": True, "is_sensitive": True, "default_export": False, "desensitized": True},
    {"table": "emotion_diaries", "column": "raw_text", "source_type": "user_text", "sentiment_ok": True, "network_ok": True, "is_sensitive": True, "default_export": False, "desensitized": True},
    {"table": "feedback_results", "column": "supportive_feedback", "source_type": "system_text", "sentiment_ok": True, "network_ok": False, "is_sensitive": False, "default_export": True, "desensitized": True},
    {"table": "supervision_requests", "column": "message", "source_type": "user_text", "sentiment_ok": True, "network_ok": False, "is_sensitive": True, "default_export": False, "desensitized": True},
    {"table": "supervision_requests", "column": "supervisor_reply", "source_type": "supervisor_text", "sentiment_ok": True, "network_ok": False, "is_sensitive": True, "default_export": False, "desensitized": True},
    {"table": "checkins", "column": "reflection", "source_type": "user_text", "sentiment_ok": True, "network_ok": False, "is_sensitive": True, "default_export": False, "desensitized": True},
    {"table": "emotion_thermometer", "column": "brief_text", "source_type": "user_text", "sentiment_ok": True, "network_ok": True, "is_sensitive": True, "default_export": False, "desensitized": True},
]

BOUNDARY_NOTICE = "文本分析仅输出脱敏聚合线索，用于研究和阶段性反馈参考，不构成诊断、筛查、治疗建议或风险预测。"
REFLEX_ORDER = ["trigger", "thought", "body_feeling", "emotion", "reaction", "behavior", "outcome"]


def _read_json(filename: str) -> dict:
    path = DICTIONARY_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"缺少文本分析词典：{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _category_terms(payload: dict, node_type: str, reflex_node: str) -> list[dict]:
    entries = []
    for category, terms in payload.items():
        if category in {"version", "source_note"}:
            continue
        if not isinstance(terms, list):
            continue
        for term in terms:
            entries.append({"word": str(term), "category": category, "type": node_type, "reflex_node": reflex_node})
    return entries


def load_dictionaries() -> dict:
    emotion_payload = _read_json("emotion_terms.json")
    emotion_entries = emotion_payload.get("terms")
    if not isinstance(emotion_entries, list):
        emotion_entries = [
            {"word": item["word"], "category": item["category"], "polarity": item.get("polarity", 0), "intensity": item.get("intensity", 1), "arousal_weight": item.get("arousal_weight", 0.5), "reflex_node": item.get("reflex_node", "emotion")}
            for item in _category_terms(emotion_payload, "emotion", "emotion")
        ]
    scene_entries = _category_terms(_read_json("scene_terms.json"), "scene", "trigger")
    person_entries = _category_terms(_read_json("person_terms.json"), "person", "trigger")
    behavior_entries = _category_terms(_read_json("behavior_terms.json"), "behavior", "behavior")
    stopwords = set(_read_json("stopwords.json").get("stopwords", []))

    emotion_by_word = {}
    node_entries = []
    for entry in emotion_entries:
        word = str(entry.get("word") or "").strip()
        if not word:
            continue
        normalized = {
            "word": word,
            "category": entry.get("category") or "emotion",
            "type": "emotion",
            "polarity": float(entry.get("polarity", 0)),
            "intensity": float(entry.get("intensity", 1)),
            "arousal_weight": float(entry.get("arousal_weight", 0.5)),
            "reflex_node": entry.get("reflex_node") or "emotion",
        }
        emotion_by_word[word] = normalized
        node_entries.append(normalized)
    node_entries.extend(scene_entries + person_entries + behavior_entries)
    for entry in node_entries:
        jieba.add_word(entry["word"])
    return {"emotion_by_word": emotion_by_word, "node_entries": node_entries, "stopwords": stopwords}


def tokenize(text: str, dictionaries: dict | None = None) -> list[str]:
    dictionaries = dictionaries or load_dictionaries()
    stopwords = dictionaries["stopwords"]
    tokens = []
    for token in jieba.lcut(text or ""):
        token = token.strip()
        if not token or token in stopwords:
            continue
        tokens.append(token)
    return tokens


def _date_filter(days: int | None) -> str | None:
    if not days:
        return None
    start = datetime.now(timezone.utc) - timedelta(days=days)
    return start.date().isoformat()


def _table_columns(conn, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row["name"] for row in rows}


def _iter_text_records(conn, user_id: str | None, days: int | None):
    start_date = _date_filter(days)
    for source in TEXT_SOURCES:
        table = source["table"]
        column = source["column"]
        try:
            columns = _table_columns(conn, table)
        except Exception:
            continue
        if column not in columns:
            continue
        where = [f"{column} IS NOT NULL", f"TRIM({column}) != ''"]
        params: list[str] = []
        if user_id and "user_id" in columns:
            where.append("user_id = ?")
            params.append(user_id)
        if start_date and "created_at" in columns:
            where.append("substr(created_at, 1, 10) >= ?")
            params.append(start_date)
        rows = conn.execute(
            f"""
            SELECT {column} AS text_value
            FROM {table}
            WHERE {' AND '.join(where)}
            """,
            params,
        ).fetchall()
        for row in rows_to_dicts(rows):
            yield {
                "source": f"{table}.{column}",
                "source_type": source["source_type"],
                "text": str(row.get("text_value") or ""),
                "sentiment_ok": source["sentiment_ok"],
                "network_ok": source["network_ok"],
            }


def _chain_edges(nodes: set[tuple[str, str, str]]) -> list[tuple[str, str]]:
    by_reflex = {}
    for node_type, word, reflex_node in nodes:
        if reflex_node not in by_reflex:
            by_reflex[reflex_node] = f"{node_type}:{word}"
    ordered = [node for node in REFLEX_ORDER if node in by_reflex]
    return [(ordered[index], ordered[index + 1]) for index in range(len(ordered) - 1)]


def analyze_records(records: list[dict]) -> dict:
    dictionaries = load_dictionaries()
    emotion_by_word = dictionaries["emotion_by_word"]
    node_entries = dictionaries["node_entries"]
    source_counts = Counter(item["source"] for item in records)
    source_type_counts = Counter(item["source_type"] for item in records)
    emotion_words = Counter()
    emotion_categories = Counter()
    nodes = Counter()
    edges = Counter()
    reflex_edges = Counter()
    reflex_chains = Counter()
    valence_values: list[float] = []
    arousal_values: list[float] = []
    intensity_score = 0.0

    for item in records:
        tokens = set(tokenize(item["text"], dictionaries))
        if item["sentiment_ok"]:
            for word in tokens:
                emotion = emotion_by_word.get(word)
                if not emotion:
                    continue
                emotion_words[word] += 1
                emotion_categories[emotion["category"]] += 1
                intensity = emotion["intensity"]
                intensity_score += intensity
                valence_values.append(emotion["polarity"] * intensity)
                arousal_values.append(emotion["arousal_weight"] * intensity)

        if item["network_ok"]:
            matched_nodes: set[tuple[str, str, str]] = set()
            for entry in node_entries:
                word = entry["word"]
                if word not in tokens:
                    continue
                node_type = entry.get("type") or "term"
                reflex_node = entry.get("reflex_node") or node_type
                key = f"{node_type}:{word}"
                nodes[key] += 1
                matched_nodes.add((node_type, word, reflex_node))
            sorted_nodes = sorted(matched_nodes)
            for index, left in enumerate(sorted_nodes):
                for right in sorted_nodes[index + 1 :]:
                    edge_key = (f"{left[0]}:{left[1]}", f"{right[0]}:{right[1]}")
                    edges[edge_key] += 1
            chain = _chain_edges(matched_nodes)
            for left_reflex, right_reflex in chain:
                reflex_edges[(left_reflex, right_reflex)] += 1
            if chain:
                reflex_chains[" -> ".join([chain[0][0], *[right for _left, right in chain]])] += 1

    record_count = len(records)
    mean_valence = round(sum(valence_values) / len(valence_values), 3) if valence_values else 0
    mean_arousal = round(sum(arousal_values) / len(arousal_values), 3) if arousal_values else 0
    return {
        "record_count": record_count,
        "source_counts": dict(source_counts),
        "source_type_counts": dict(source_type_counts),
        "sentiment_summary": {
            "emotion_keywords": emotion_words.most_common(30),
            "emotion_categories": emotion_categories.most_common(16),
            "intensity_signal_score": round(intensity_score, 2),
            "valence": mean_valence,
            "arousal": mean_arousal,
            "matched_emotion_count": len(valence_values),
        },
        "cooccurrence_network": {
            "nodes": [
                {"id": key, "type": key.split(":", 1)[0], "label": key.split(":", 1)[1], "count": count}
                for key, count in nodes.most_common(80)
            ],
            "edges": [
                {"source": source, "target": target, "weight": weight}
                for (source, target), weight in edges.most_common(120)
            ],
            "reflex_arc_edges": [
                {"source": source, "target": target, "weight": weight}
                for (source, target), weight in reflex_edges.most_common(80)
            ],
            "reflex_arc_chains": [
                {"chain": chain, "count": count}
                for chain, count in reflex_chains.most_common(40)
            ],
        },
        "dictionary_version": _read_json("emotion_terms.json").get("version"),
        "boundary_notice": BOUNDARY_NOTICE,
        "raw_text_included": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build aggregate text analysis without exporting raw text.")
    parser.add_argument("--user-id", default="", help="Optional user_id filter.")
    parser.add_argument("--days", type=int, default=0, help="Optional lookback days.")
    parser.add_argument("--output", default=str(PROJECT_ROOT / "outputs" / "text_analysis" / "text_analysis_summary.json"))
    args = parser.parse_args()

    init_db()
    with get_connection() as conn:
        records = list(_iter_text_records(conn, args.user_id or None, args.days or None))

    result = analyze_records(records)
    result["filters"] = {
        "user_id": args.user_id or None,
        "days": args.days or None,
    }
    result["generated_at"] = datetime.now(timezone.utc).isoformat()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output), "record_count": result["record_count"], "raw_text_included": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
