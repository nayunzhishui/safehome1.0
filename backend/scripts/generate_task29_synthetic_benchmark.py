"""Generate the deterministic 240-case synthetic affect benchmark (no real text)."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "content" / "synthetic_affect_benchmark_240.json"

LABELS = {
    "anxiety": (["担心", "焦虑", "紧张"], -0.7, 0.75),
    "fear": (["害怕", "恐惧"], -0.9, 0.9),
    "anger": (["生气", "愤怒"], -0.8, 0.9),
    "irritation": (["烦", "烦躁"], -0.6, 0.7),
    "sadness": (["难过", "失望", "沮丧"], -0.8, 0.35),
    "helplessness": (["无力"], -0.8, 0.25),
    "guilt": (["内疚"], -0.7, 0.4),
    "shame": (["羞愧"], -0.8, 0.5),
    "calm": (["平静", "放松", "安心"], 0.8, 0.2),
    "positive": (["开心", "高兴", "期待"], 0.8, 0.6),
}
SCENES = ["讨论安排时", "收到消息后", "准备出门前", "完成练习后", "回想今天时", "计划明天时"]
SUBGROUPS = ["brief_direct", "with_context", "with_degree", "with_contrast"]


def build_cases() -> list[dict]:
    cases: list[dict] = []
    index = 0
    for label, (terms, valence, arousal) in LABELS.items():
        for round_index in range(24):
            term = terms[round_index % len(terms)]
            scene = SCENES[round_index % len(SCENES)]
            subgroup = SUBGROUPS[round_index % len(SUBGROUPS)]
            if subgroup == "brief_direct":
                text = f"我感到{term}。"
            elif subgroup == "with_context":
                text = f"{scene}，我注意到自己有些{term}。"
            elif subgroup == "with_degree":
                text = f"{scene}，这种{term}的感觉比较明显。"
            else:
                text = f"{scene}，一开始有点{term}，不过我先停下来观察。"
            index += 1
            cases.append({
                "id": f"syn-affect-{index:03d}",
                "text": text,
                "generator_label": label,
                "valence": valence,
                "arousal": arousal,
                "context": "synthetic_daily_reflection",
                "reflex_node": "emotion",
                "subgroup": subgroup,
                "synthetic": True,
            })
    return cases


def payload() -> dict:
    cases = build_cases()
    case_hash = hashlib.sha256(json.dumps(cases, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return {
        "version": "2026-07-20-t29-synthetic-affect-v1",
        "contains_real_data": False,
        "case_count": len(cases),
        "generator_label_is_human_gold": False,
        "case_hash": case_hash,
        "cases": cases,
        "boundary_notice": "全部句子由固定模板生成；生成标签仅用于工程回归，不代替双人盲标金标准。",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = json.dumps(payload(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != rendered:
            raise SystemExit("synthetic benchmark artifact drift detected")
        print("synthetic benchmark artifact check passed: 240 cases")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"generated {args.output} with 240 synthetic cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
