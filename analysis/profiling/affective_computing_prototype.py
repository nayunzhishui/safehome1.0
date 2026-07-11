"""Legacy CLI for affective computing; delegates to analysis/text_analysis."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEXT_ANALYSIS_DIR = PROJECT_ROOT / "analysis" / "text_analysis"
if str(TEXT_ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(TEXT_ANALYSIS_DIR))

from analyze_text_sources import DEFAULT_DB, _iter_text_records, open_readonly_sqlite  # noqa: E402
from build_text_features import build_feature_summary  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="兼容入口：离线情感计算现由 analysis/text_analysis 统一实现。")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs" / "text_analysis")
    parser.add_argument("--minimum-support", type=int, default=5)
    args = parser.parse_args()
    with open_readonly_sqlite(args.db) as conn:
        records = list(_iter_text_records(conn, None, None))
    payload = build_feature_summary(records, max(1, args.minimum_support))
    payload["legacy_entrypoint"] = "analysis/profiling/affective_computing_prototype.py"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "text_features_summary.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
