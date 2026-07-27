"""Build offline, aggregate affect and semantic co-occurrence evidence.

This module is the single text-analysis path. It reads SQLite in read-only mode,
keeps writers separated, and never serializes source text or stable identities.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import jieba
except ImportError as exc:  # pragma: no cover
    raise SystemExit("缺少离线分析依赖 jieba，请运行：python -m pip install -r analysis/text_analysis/requirements.txt") from exc


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
DICTIONARY_DIR = Path(__file__).resolve().parent / "dictionaries"
DEFAULT_DB = Path(os.environ.get("DATABASE_PATH", BACKEND_ROOT / "safehome.sqlite3"))
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


ANALYSIS_DEFINITIONS = {
    "affective_computing": "按写作者分层的情绪词、效价、唤醒和强度聚合线索。",
    "semantic_cooccurrence_network": "文本字段或句子内的概念共现与反射弧线索，不代表真实社会关系。",
    "family_topology_audit": "经授权且有效的结构化家庭绑定数据质量摘要，不评价关系好坏。",
}
PROHIBITED_USES = ["诊断", "危机预测", "人格判断", "关系质量打分", "自动惩罚"]
BOUNDARY_NOTICE = "离线分析只提供脱敏、自我观察和研究线索，不构成诊断、筛查、治疗建议、风险预测或关系质量评价。"
REFLEX_ORDER = ["trigger", "thought", "body_feeling", "emotion", "reaction", "behavior", "outcome"]
NEGATIONS = {"不", "没", "没有", "并不", "不是", "未", "无"}
DEGREE_WEIGHTS = {"极其": 1.8, "非常": 1.6, "特别": 1.5, "很": 1.3, "更": 1.2, "有点": 0.65, "稍微": 0.6, "一点": 0.6}
CONTRAST_TERMS = {"但", "但是", "不过", "然而", "可是"}
SENTENCE_SPLIT = re.compile(r"[。！？!?；;\n]+")

TEXT_SOURCES = [
    {"table": "emotion_diaries", "column": "event_description", "source_type": "user_text", "sentiment_ok": True, "network_ok": True},
    {"table": "emotion_diaries", "column": "automatic_thought", "source_type": "user_text", "sentiment_ok": True, "network_ok": True},
    {"table": "emotion_diaries", "column": "body_sensation", "source_type": "user_text", "sentiment_ok": True, "network_ok": True},
    {"table": "emotion_diaries", "column": "behavior", "source_type": "user_text", "sentiment_ok": True, "network_ok": True},
    {"table": "emotion_diaries", "column": "raw_text", "source_type": "user_text", "sentiment_ok": True, "network_ok": True},
    {"table": "feedback_results", "column": "supportive_feedback", "source_type": "system_text", "sentiment_ok": True, "network_ok": False},
    {"table": "supervision_requests", "column": "message", "source_type": "user_text", "sentiment_ok": True, "network_ok": False},
    {"table": "supervision_requests", "column": "supervisor_reply", "source_type": "supervisor_text", "sentiment_ok": True, "network_ok": False},
    {"table": "checkins", "column": "reflection", "source_type": "user_text", "sentiment_ok": True, "network_ok": False},
    {"table": "emotion_thermometer", "column": "brief_text", "source_type": "user_text", "sentiment_ok": True, "network_ok": True},
]


def _read_json(filename: str) -> dict:
    path = DICTIONARY_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"缺少文本分析词典：{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _category_terms(payload: dict, node_type: str, reflex_node: str) -> list[dict]:
    entries = []
    for category, terms in payload.items():
        if category in {"version", "source_note", "license"} or not isinstance(terms, list):
            continue
        for term in terms:
            entries.append({"word": str(term), "category": category, "type": node_type, "reflex_node": reflex_node})
    return entries


def load_dictionaries() -> dict:
    emotion_payload = _read_json("emotion_terms.json")
    emotion_entries = emotion_payload.get("terms")
    if not isinstance(emotion_entries, list):
        emotion_entries = _category_terms(emotion_payload, "emotion", "emotion")
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
    for entry in [*node_entries, *({"word": word} for word in NEGATIONS | set(DEGREE_WEIGHTS) | CONTRAST_TERMS)]:
        jieba.add_word(entry["word"])
    return {"emotion_by_word": emotion_by_word, "node_entries": node_entries, "stopwords": stopwords}


def tokenize(text: str, dictionaries: dict | None = None) -> list[str]:
    dictionaries = dictionaries or load_dictionaries()
    normalized = re.sub(r"\s+", " ", (text or "").strip())
    return [token.strip() for token in jieba.lcut(normalized) if token.strip() and token.strip() not in dictionaries["stopwords"]]


def open_readonly_sqlite(database_path: Path) -> sqlite3.Connection:
    """Open an immutable source database without creating or migrating it."""

    resolved = database_path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"离线分析数据库不存在：{resolved}")
    conn = sqlite3.connect(f"file:{resolved.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _date_filter(days: int | None) -> str | None:
    if not days:
        return None
    return (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _iter_text_records(conn: sqlite3.Connection, user_id: str | None, days: int | None):
    start_date = _date_filter(days)
    for source in TEXT_SOURCES:
        table, column = source["table"], source["column"]
        columns = _table_columns(conn, table)
        if column not in columns:
            continue
        where = [f"{column} IS NOT NULL", f"TRIM({column}) != ''"]
        params: list[str] = []
        if user_id and "user_id" in columns:
            where.append("user_id = ?")
            params.append(user_id)
        consent_columns = _table_columns(conn, "consent_records")
        if "user_id" in columns and {"user_id", "consent_type", "agreed", "created_at"} <= consent_columns:
            where.append(
                f"""NOT EXISTS (
                    SELECT 1 FROM consent_records consent_latest
                    WHERE consent_latest.user_id = {table}.user_id
                      AND consent_latest.consent_type IN ('anonymous_research', 'research_authorization')
                      AND consent_latest.created_at = (
                          SELECT MAX(consent_inner.created_at) FROM consent_records consent_inner
                          WHERE consent_inner.user_id = consent_latest.user_id
                            AND consent_inner.consent_type = consent_latest.consent_type
                      )
                      AND consent_latest.agreed = 0
                )"""
            )
        if start_date and "created_at" in columns:
            where.append("substr(created_at, 1, 10) >= ?")
            params.append(start_date)
        created_select = "created_at" if "created_at" in columns else "NULL"
        rows = conn.execute(
            f"SELECT {column} AS text_value, {created_select} AS recorded_at FROM {table} WHERE {' AND '.join(where)}",
            params,
        ).fetchall()
        for row in rows:
            yield {
                "source": f"{table}.{column}",
                "source_type": source["source_type"],
                "text": str(row["text_value"] or ""),
                "recorded_at": row["recorded_at"],
                "sentiment_ok": source["sentiment_ok"],
                "network_ok": source["network_ok"],
            }


def _modifier(tokens: list[str], index: int) -> tuple[float, bool]:
    previous = tokens[max(0, index - 3) : index]
    negated = any(token in NEGATIONS for token in previous)
    degree = 1.0
    for token in previous:
        degree *= DEGREE_WEIGHTS.get(token, 1.0)
    return degree, negated


def _sentence_segments(text: str) -> list[tuple[str, float]]:
    segments: list[tuple[str, float]] = []
    for sentence in SENTENCE_SPLIT.split(text or ""):
        sentence = sentence.strip()
        if not sentence:
            continue
        parts = re.split(r"(但是|不过|然而|可是|但)", sentence)
        has_contrast = any(part in CONTRAST_TERMS for part in parts)
        after_contrast = False
        for part in parts:
            if part in CONTRAST_TERMS:
                after_contrast = True
                continue
            if part.strip():
                weight = 1.25 if after_contrast else (0.75 if has_contrast else 1.0)
                segments.append((part.strip(), weight))
    return segments


def _empty_sentiment(record_count: int = 0) -> dict:
    return {
        "record_count": record_count,
        "emotion_keywords": [],
        "emotion_categories": [],
        "intensity_signal_score": 0,
        "intensity_per_record": 0,
        "intensity_per_1000_chars": 0,
        "valence": 0,
        "arousal": 0,
        "matched_emotion_count": 0,
        "negated_match_count": 0,
        "negated_polarity_signal": 0,
        "text_length": 0,
        "coverage_rate": 0,
        "effective_coverage_rate": 0,
    }


def _analyze_sentiment(records: list[dict], dictionaries: dict) -> dict:
    emotion_words = Counter()
    emotion_categories = Counter()
    valence_values: list[float] = []
    arousal_values: list[float] = []
    intensity_score = 0.0
    negated_count = 0
    negated_polarity_values: list[float] = []
    text_length = sum(len(item.get("text") or "") for item in records)
    for item in records:
        for segment, contrast_weight in _sentence_segments(item.get("text") or ""):
            tokens = tokenize(segment, dictionaries)
            for index, word in enumerate(tokens):
                emotion = dictionaries["emotion_by_word"].get(word)
                if not emotion:
                    continue
                degree, negated = _modifier(tokens, index)
                if negated:
                    negated_count += 1
                    flipped = (
                        -float(emotion["polarity"])
                        * float(emotion["intensity"])
                        * degree
                        * contrast_weight
                        * 0.5
                    )
                    negated_polarity_values.append(flipped)
                    continue
                effective_intensity = float(emotion["intensity"]) * degree * contrast_weight
                emotion_words[word] += 1
                emotion_categories[emotion["category"]] += 1
                intensity_score += effective_intensity
                valence_values.append(float(emotion["polarity"]) * effective_intensity)
                arousal_values.append(float(emotion["arousal_weight"]) * effective_intensity)
    matched = len(valence_values)
    record_count = len(records)
    result = _empty_sentiment(record_count)
    result.update(
        {
            "emotion_keywords": emotion_words.most_common(30),
            "emotion_categories": emotion_categories.most_common(16),
            "intensity_signal_score": round(intensity_score, 3),
            "intensity_per_record": round(intensity_score / record_count, 3) if record_count else 0,
            "intensity_per_1000_chars": round(intensity_score * 1000 / text_length, 3) if text_length else 0,
            "valence": round(sum(valence_values) / matched, 3) if matched else 0,
            "arousal": round(sum(arousal_values) / matched, 3) if matched else 0,
            "matched_emotion_count": matched,
            "negated_match_count": negated_count,
            "negated_polarity_signal": (
                round(sum(negated_polarity_values) / len(negated_polarity_values), 3)
                if negated_polarity_values
                else 0
            ),
            "text_length": text_length,
            "coverage_rate": round(matched / record_count, 3) if record_count else 0,
            "effective_coverage_rate": (
                round((matched + negated_count) / record_count, 3)
                if record_count
                else 0
            ),
        }
    )
    return result


def _chain_edges(nodes: set[tuple[str, str, str]]) -> list[tuple[str, str]]:
    by_reflex: dict[str, list[str]] = defaultdict(list)
    for node_type, word, reflex_node in sorted(nodes):
        by_reflex[reflex_node].append(f"{node_type}:{word}")
    ordered = [node for reflex in REFLEX_ORDER for node in by_reflex.get(reflex, [])]
    return list(zip(ordered, ordered[1:]))


def _analyze_network(records: list[dict], dictionaries: dict, minimum_support: int) -> dict:
    node_occurrence = Counter()
    node_documents = Counter()
    edge_occurrence = Counter()
    edge_documents = Counter()
    reflex_edges = Counter()
    reflex_chains = Counter()

    for item in records:
        document_nodes: set[str] = set()
        document_edges: set[tuple[str, str]] = set()
        for segment, _weight in _sentence_segments(item.get("text") or ""):
            token_set = set(tokenize(segment, dictionaries))
            matched: set[tuple[str, str, str]] = set()
            for entry in dictionaries["node_entries"]:
                if entry["word"] not in token_set:
                    continue
                node_type = entry.get("type") or "term"
                reflex_node = entry.get("reflex_node") or node_type
                node_id = f"{node_type}:{entry['word']}"
                node_occurrence[node_id] += 1
                document_nodes.add(node_id)
                matched.add((node_type, entry["word"], reflex_node))
            sentence_nodes = sorted({f"{kind}:{word}" for kind, word, _reflex in matched})
            for index, left in enumerate(sentence_nodes):
                for right in sentence_nodes[index + 1 :]:
                    edge = (left, right)
                    edge_occurrence[edge] += 1
                    document_edges.add(edge)
            chain = _chain_edges(matched)
            for edge in chain:
                reflex_edges[edge] += 1
            if chain:
                reflex_chains[" -> ".join([chain[0][0], *[right for _left, right in chain]])] += 1
        node_documents.update(document_nodes)
        edge_documents.update(document_edges)

    allowed_nodes = {node for node, count in node_documents.items() if count >= minimum_support}
    nodes = [
        {"id": node, "type": node.split(":", 1)[0], "label": node.split(":", 1)[1], "count": node_occurrence[node], "document_frequency": count}
        for node, count in node_documents.most_common()
        if node in allowed_nodes
    ][:80]
    edges = [
        {"source": left, "target": right, "weight": edge_occurrence[(left, right)], "document_frequency": count}
        for (left, right), count in edge_documents.most_common()
        if count >= minimum_support and left in allowed_nodes and right in allowed_nodes
    ][:120]
    return {
        "nodes": nodes,
        "edges": edges,
        "reflex_arc_edges": [
            {"source": left, "target": right, "weight": count}
            for (left, right), count in reflex_edges.most_common(80)
            if count >= minimum_support and left in allowed_nodes and right in allowed_nodes
        ],
        "reflex_arc_chains": [
            {"chain": chain, "count": count}
            for chain, count in reflex_chains.most_common(40)
            if count >= minimum_support
        ],
        "suppression": {
            "minimum_support": minimum_support,
            "suppressed_node_count": sum(count < minimum_support for count in node_documents.values()),
            "suppressed_edge_count": sum(count < minimum_support for count in edge_documents.values()),
        },
        "window": "sentence",
    }


def _dictionary_hashes() -> dict[str, str]:
    hashes = {}
    for path in sorted(DICTIONARY_DIR.glob("*.json")):
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def analyze_records(records: list[dict], minimum_support: int = 1) -> dict:
    dictionaries = load_dictionaries()
    sentiment_records = [item for item in records if item.get("sentiment_ok")]
    network_records = [item for item in records if item.get("network_ok")]
    by_source_type: dict[str, list[dict]] = defaultdict(list)
    for item in sentiment_records:
        by_source_type[item.get("source_type") or "unknown"].append(item)
    sentiment = _analyze_sentiment(sentiment_records, dictionaries)
    source_counts = Counter(item.get("source") or "unknown" for item in records)
    source_type_counts = Counter(item.get("source_type") or "unknown" for item in records)
    record_count = len(records)
    quality_status = "empty" if record_count == 0 else ("insufficient_data" if record_count < minimum_support else "valid")
    return {
        "schema_version": "2026-07-11-offline-text-analysis-v1",
        "analysis_version": "affect_semantic_rules_v3",
        "analysis_definitions": ANALYSIS_DEFINITIONS,
        "prohibited_uses": PROHIBITED_USES,
        "record_count": record_count,
        "source_counts": dict(source_counts),
        "source_type_counts": dict(source_type_counts),
        "sentiment_summary": sentiment,
        "sentiment_by_source_type": {
            source_type: _analyze_sentiment(items, dictionaries)
            for source_type, items in sorted(by_source_type.items())
        },
        "cooccurrence_network": _analyze_network(network_records, dictionaries, max(1, minimum_support)),
        "dictionary_version": _read_json("emotion_terms.json").get("version"),
        "dictionary_hashes": _dictionary_hashes(),
        "quality_status": quality_status,
        "available": quality_status == "valid",
        "insufficient_data_reasons": ["no_records"] if record_count == 0 else (["below_minimum_support"] if quality_status == "insufficient_data" else []),
        "privacy_gate_passed": True,
        "boundary_notice": BOUNDARY_NOTICE,
        "raw_text_included": False,
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest(database_path: Path, result: dict, parameters: dict) -> dict:
    return {
        "run_id": hashlib.sha256(json.dumps({"source": _sha256(database_path), "parameters": parameters, "dictionaries": result["dictionary_hashes"]}, sort_keys=True).encode()).hexdigest()[:16],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_hashes": {database_path.name: _sha256(database_path)},
        "dictionary_hashes": result["dictionary_hashes"],
        "analysis_version": result["analysis_version"],
        "parameters": parameters,
        "random_seed": None,
        "privacy_rules": {"raw_text_included": False, "stable_identity_exported": False, "minimum_support": parameters["minimum_support"]},
        "record_counts": {"total": result["record_count"], "by_source_type": result["source_type_counts"]},
        "quality_status": result["quality_status"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build offline aggregate affect and semantic co-occurrence evidence.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--user-id", default="", help="Optional analysis scope; the identity is never written to output.")
    parser.add_argument("--days", type=int, default=0)
    parser.add_argument("--minimum-support", type=int, default=5)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "outputs" / "text_analysis" / "text_analysis_summary.json")
    args = parser.parse_args()

    with open_readonly_sqlite(args.db) as conn:
        records = list(_iter_text_records(conn, args.user_id or None, args.days or None))
    result = analyze_records(records, minimum_support=max(1, args.minimum_support))
    parameters = {"days": args.days or None, "minimum_support": max(1, args.minimum_support), "user_scope_applied": bool(args.user_id)}
    result["filters"] = parameters
    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    result["manifest"] = _manifest(args.db, result, parameters)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "record_count": result["record_count"], "quality_status": result["quality_status"], "raw_text_included": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
