"""Legacy CLI for the family topology audit; no longer exports hashed nodes."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEXT_ANALYSIS_DIR = PROJECT_ROOT / "analysis" / "text_analysis"
if str(TEXT_ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(TEXT_ANALYSIS_DIR))

from analyze_text_sources import DEFAULT_DB  # noqa: E402
from build_family_topology_audit import build_topology_summary, collect_edges  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="兼容入口：原社会网络原型已明确为家庭关系拓扑审计。")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs" / "text_analysis")
    parser.add_argument("--minimum-group-size", type=int, default=5)
    args = parser.parse_args()
    secret = os.environ.get("SAFEHOME_ANALYSIS_HMAC_KEY", "")
    if not secret:
        raise SystemExit("请通过 SAFEHOME_ANALYSIS_HMAC_KEY 提供运行级 HMAC 密钥。")
    payload = build_topology_summary(
        collect_edges(args.db),
        secret=secret.encode("utf-8"),
        minimum_group_size=max(2, args.minimum_group_size),
    )
    payload["legacy_entrypoint"] = "analysis/profiling/social_network_prototype.py"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "family_topology_audit_summary.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
