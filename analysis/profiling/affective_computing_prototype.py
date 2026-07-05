"""Offline affective-computing prototype for SafeHome aggregated exports.

This script is intentionally offline-only. It writes desensitized aggregate
counts and never exports diary raw text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = PROJECT_ROOT / "backend" / "safehome.sqlite3"
DEFAULT_OUTPUT_DIR = Path(r"D:\codex\workspace\safehome1.0其他内容\画像系统设计_Claude_20260628\07_情感计算与SNA雏形_20260701")

POSITIVE_TERMS = ["平静", "放松", "安心", "稳定", "理解", "感谢", "开心", "舒服", "轻松"]
NEGATIVE_TERMS = ["着急", "生气", "担心", "失望", "烦", "难过", "紧张", "委屈", "害怕", "崩溃"]
AROUSAL_TERMS = ["冲突", "吵", "喊", "急", "发火", "哭", "失控", "压力", "考试", "拖延"]


def hash_id(value: str) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12]


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
    return bool(row)


def score_text(text: str) -> dict:
    positive = sum(text.count(term) for term in POSITIVE_TERMS)
    negative = sum(text.count(term) for term in NEGATIVE_TERMS)
    arousal = sum(text.count(term) for term in AROUSAL_TERMS)
    return {"positive_terms": positive, "negative_terms": negative, "arousal_terms": arousal, "valence": positive - negative}


def date_key(value: str | None) -> str:
    if not value:
        return "unknown"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return value[:10]


def collect_rows(db_path: Path) -> list[dict]:
    if not db_path.exists():
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows: list[dict] = []
    if table_exists(conn, "emotion_diaries"):
        for row in conn.execute(
            """
            SELECT user_id, created_at, scene, event_description, parent_emotion,
                   automatic_thought, body_sensation, behavior, raw_text
            FROM emotion_diaries
            """
        ):
            text = " ".join(str(row[key] or "") for key in row.keys() if key not in {"user_id", "created_at"})
            rows.append({"source": "emotion_diary", "user_id": row["user_id"], "created_at": row["created_at"], "text": text})
    if table_exists(conn, "emotion_thermometer"):
        for row in conn.execute("SELECT user_id, created_at, intensity_level, brief_text FROM emotion_thermometer"):
            text = f"{row['brief_text'] or ''}"
            rows.append(
                {
                    "source": "emotion_thermometer",
                    "user_id": row["user_id"],
                    "created_at": row["created_at"],
                    "text": text,
                    "intensity_level": row["intensity_level"],
                }
            )
    conn.close()
    return rows


def build_summary(rows: list[dict]) -> dict:
    by_user_day: dict[tuple[str, str], dict] = defaultdict(
        lambda: {
            "record_count": 0,
            "positive_terms": 0,
            "negative_terms": 0,
            "arousal_terms": 0,
            "valence": 0,
            "thermometer_count": 0,
            "thermometer_sum": 0,
        }
    )
    source_counts = Counter()
    for row in rows:
        key = (hash_id(row["user_id"]), date_key(row.get("created_at")))
        scores = score_text(row.get("text", ""))
        bucket = by_user_day[key]
        bucket["record_count"] += 1
        for field, value in scores.items():
            bucket[field] += value
        if row.get("source") == "emotion_thermometer":
            bucket["thermometer_count"] += 1
            bucket["thermometer_sum"] += int(row.get("intensity_level") or 0)
        source_counts[row.get("source", "unknown")] += 1

    aggregates = []
    for (user_hash, day), values in sorted(by_user_day.items()):
        thermometer_count = values.pop("thermometer_count")
        thermometer_sum = values.pop("thermometer_sum")
        values["thermometer_avg"] = round(thermometer_sum / thermometer_count, 2) if thermometer_count else None
        aggregates.append({"user_hash": user_hash, "date": day, **values})

    return {
        "schema_version": "2026-07-01-affective-prototype-v1",
        "privacy_note": "仅输出脱敏聚合指标，不包含原始日记文本、联系方式或可识别身份信息。",
        "source_counts": dict(source_counts),
        "aggregates": aggregates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    payload = build_summary(collect_rows(args.db))
    output_path = args.output_dir / "情感计算脱敏汇总.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
