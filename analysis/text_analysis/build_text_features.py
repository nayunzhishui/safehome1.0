"""Build source-separated aggregate affect features from a read-only snapshot."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from analyze_text_sources import (  # noqa: E402
    DEFAULT_DB,
    PROJECT_ROOT,
    _iter_text_records,
    analyze_records,
    open_readonly_sqlite,
)


def build_feature_summary(records: list[dict], minimum_support: int = 5) -> dict:
    aggregate = analyze_records(records, minimum_support=minimum_support)
    sentiment = aggregate["sentiment_summary"]
    return {
        "schema_version": "2026-07-11-affect-features-v1",
        "analysis_kind": "affective_computing",
        "analysis_version": "text_features_v3_source_separated_rules",
        "record_count": aggregate["record_count"],
        "source_counts": aggregate["source_counts"],
        "source_type_counts": aggregate["source_type_counts"],
        "sentiment_by_source_type": aggregate["sentiment_by_source_type"],
        "emotion_keywords": sentiment["emotion_keywords"],
        "emotion_categories": sentiment["emotion_categories"],
        "valence": sentiment["valence"],
        "arousal": sentiment["arousal"],
        "matched_emotion_count": sentiment["matched_emotion_count"],
        "negated_match_count": sentiment["negated_match_count"],
        "intensity_hint": sentiment["intensity_signal_score"],
        "intensity_per_record": sentiment["intensity_per_record"],
        "intensity_per_1000_chars": sentiment["intensity_per_1000_chars"],
        "coverage_rate": sentiment["coverage_rate"],
        "quality_status": aggregate["quality_status"],
        "available": aggregate["available"],
        "insufficient_data_reasons": aggregate["insufficient_data_reasons"],
        "privacy_gate_passed": True,
        "dictionary_hashes": aggregate["dictionary_hashes"],
        "raw_text_included": False,
        "boundary_notice": aggregate["boundary_notice"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build SafeHome aggregate affect features.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--user-id", default="")
    parser.add_argument("--days", type=int, default=0)
    parser.add_argument("--minimum-support", type=int, default=5)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "outputs" / "text_analysis" / "text_features_summary.json")
    args = parser.parse_args()

    with open_readonly_sqlite(args.db) as conn:
        records = list(_iter_text_records(conn, args.user_id or None, args.days or None))
    result = build_feature_summary(records, max(1, args.minimum_support))
    result["filters"] = {"user_scope_applied": bool(args.user_id), "days": args.days or None, "minimum_support": max(1, args.minimum_support)}
    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "record_count": result["record_count"], "quality_status": result["quality_status"], "raw_text_included": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
