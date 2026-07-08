"""Build aggregate text feature summary without exporting raw text."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from analyze_text_sources import PROJECT_ROOT, analyze_records, get_connection, init_db, _iter_text_records


def main() -> int:
    parser = argparse.ArgumentParser(description="Build SafeHome aggregate text features.")
    parser.add_argument("--user-id", default="")
    parser.add_argument("--days", type=int, default=0)
    parser.add_argument("--output", default=str(PROJECT_ROOT / "outputs" / "text_analysis" / "text_features_summary.json"))
    args = parser.parse_args()

    init_db()
    with get_connection() as conn:
        records = list(_iter_text_records(conn, args.user_id or None, args.days or None))
    aggregate = analyze_records(records)
    text_lengths = [len(item["text"]) for item in records]
    result = {
        "analysis_version": "text_features_v2_jieba_va",
        "record_count": aggregate["record_count"],
        "source_counts": aggregate["source_counts"],
        "source_type_counts": aggregate["source_type_counts"],
        "emotion_keywords": aggregate["sentiment_summary"]["emotion_keywords"],
        "emotion_categories": aggregate["sentiment_summary"]["emotion_categories"],
        "valence": aggregate["sentiment_summary"]["valence"],
        "arousal": aggregate["sentiment_summary"]["arousal"],
        "matched_emotion_count": aggregate["sentiment_summary"]["matched_emotion_count"],
        "intensity_hint": aggregate["sentiment_summary"]["intensity_signal_score"],
        "text_length": {
            "count": len(text_lengths),
            "avg": round(sum(text_lengths) / len(text_lengths), 2) if text_lengths else 0,
            "max": max(text_lengths) if text_lengths else 0,
        },
        "raw_text_included": False,
        "boundary_notice": aggregate["boundary_notice"],
        "filters": {"user_id": args.user_id or None, "days": args.days or None},
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output), "record_count": result["record_count"], "raw_text_included": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
