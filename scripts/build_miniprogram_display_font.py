"""Build the miniprogram display-font subsets (Noto Serif SC, SIL OFL 1.1).

The serif face is only used for closed sets of text: greetings, tab and page
titles, scale/course/program titles, profile names, numbers and content quotes.
User-written text keeps the system serif so a line never mixes two faces.

Usage: python scripts/build_miniprogram_display_font.py --source <NotoSerifSC-VF.ttf>
Writes apps/miniprogram/utils/display-font-data.js (base64 woff2 per weight).
"""

from __future__ import annotations

import argparse
import base64
import glob
import io
import json
import re
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
MINI = ROOT / "apps" / "miniprogram"
OUTPUT = MINI / "utils" / "display-font-data.js"

ASCII = "".join(chr(code) for code in range(0x20, 0x7F))
PUNCTUATION = "（）·“”‘’…、，。：；？！—–／《》「」〈〉"

# Fixed serif strings in page templates and page scripts (UIproduct3 Figma page 619:6).
STATIC_MEDIUM = [
    "早上好", "上午好", "中午好", "下午好", "晚上好", "夜深了",
    "训练", "课程", "我的", "安心陪伴",
    "先设置一个新密码", "创建账号", "从一件具体小事开始", "先接住这次感受", "先照顾好安全",
    "我想弄清楚的问题", "先了解边界", "我的议题", "最近一次事件", "例外与资源", "资料与共享",
    "提交前摘要", "反馈核对", "一个小行动与回看", "线上探索", "关系探索阶段性报告",
    "先知道这个工具能做什么", "安心陪伴隐私政策", "年龄与监护人保护设置", "把问题缩小到下一步",
    "关系隐喻互动绘画", "如果……会怎样", "先找现实帮助", "先把人连接上", "关于那条记录的回看信",
    "月日周一二三四五六日已记类条次份天个分", "本周复盘", "我的成长", "情绪记录",
    "起点测评", "阶段性报告", "阶段性反馈", "连续记录", "从已审核内容里找答案",
    "安心陪伴用户服务协议", "支持性工具，不替代现实帮助", "关系健康初筛报告", "阶段性报告正在人工复核",
    "自助整理", "待",
]
STATIC_REGULAR = ["原话", "0123456789"]


def _chars(values) -> set[str]:
    return {char for value in values for char in str(value or "")}


def medium_text() -> str:
    worksheets = json.loads((CONTENT / "assessment_worksheets.json").read_text(encoding="utf-8"))["worksheets"]
    programs = json.loads((CONTENT / "programs.json").read_text(encoding="utf-8"))["programs"]
    courses = json.loads((CONTENT / "courses.json").read_text(encoding="utf-8"))["courses"]
    names = []
    for path in sorted(glob.glob(str(CONTENT / "profiles" / "*.json"))):
        profile = json.loads(Path(path).read_text(encoding="utf-8"))
        names.extend(cluster.get("display_name") for cluster in profile.get("clusters") or [])
    review = (MINI / "utils" / "supportiveReview.js").read_text(encoding="utf-8")
    step_block = re.search(r"const STEP_TITLES = \{(.*?)\};", review, re.S)
    step_titles = re.findall(r':\s*"([^"]+)"', step_block.group(1)) if step_block else []
    values = STATIC_MEDIUM + step_titles + [item.get("display_title") for item in worksheets]
    values += [item.get("title") for item in programs] + [item.get("title") for item in courses] + names
    return "".join(sorted(_chars(values) | _chars([ASCII, PUNCTUATION])))


def regular_text() -> str:
    cards = json.loads((CONTENT / "training_cards.json").read_text(encoding="utf-8"))["cards"]
    courses = json.loads((CONTENT / "courses.json").read_text(encoding="utf-8"))["courses"]
    programs = json.loads((CONTENT / "programs.json").read_text(encoding="utf-8"))["programs"]
    values = STATIC_REGULAR + [card.get("example_phrase") for card in cards]
    values += [course.get("core_concept") for course in courses if isinstance(course.get("core_concept"), str)]
    for program in programs:
        values.extend(session.get("writing_prompt") for session in program.get("sessions") or [])
    guide = json.loads((CONTENT / "supportive_review_guide.json").read_text(encoding="utf-8"))
    values.append((guide.get("letter") or {}).get("closing"))
    hot_topics = (MINI / "pages" / "hot-topics" / "index.js").read_text(encoding="utf-8")
    values += re.findall(r'supportiveResponse:\s*"([^"]+)"', hot_topics)
    return "".join(sorted(_chars(values) | _chars([ASCII, PUNCTUATION])))


def subset_base64(source: Path, weight: int, text: str) -> tuple[str, int, int]:
    font = instancer.instantiateVariableFont(TTFont(source), {"wght": weight}, inplace=False)
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = ["kern"]
    options.name_IDs = [0, 1, 2, 3, 4, 6, 13, 14]
    options.notdef_outline = True
    options.hinting = False
    options.desubroutinize = True
    subsetter = subset.Subsetter(options)
    subsetter.populate(text=text)
    subsetter.subset(font)
    font.flavor = "woff2"
    font.recalcTimestamp = False  # keep the source timestamp so rebuilding the same text gives the same bytes
    buffer = io.BytesIO()
    font.save(buffer)
    data = buffer.getvalue()
    return base64.b64encode(data).decode("ascii"), len(data), font["maxp"].numGlyphs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path, help="NotoSerifSC-VF.ttf (variable, SIL OFL 1.1)")
    args = parser.parse_args()
    medium, medium_size, medium_glyphs = subset_base64(args.source, 500, medium_text())
    regular, regular_size, regular_glyphs = subset_base64(args.source, 400, regular_text())
    # Package uploads do not accept font files, so the subsets travel as base64 in a JS module.
    OUTPUT.write_text(
        "// Generated by scripts/build_miniprogram_display_font.py — do not edit by hand.\n"
        "// Noto Serif SC subsets (SIL Open Font License 1.1), woff2, base64.\n"
        "// The two data lines are public font bytes, not credentials; they carry detect-secrets'\n"
        "// inline allowlist marker because any long base64 string reads as a possible key.\n"
        f"module.exports = {{\n  medium: \"{medium}\", // pragma: allowlist secret\n"
        f"  regular: \"{regular}\", // pragma: allowlist secret\n}};\n",
        encoding="utf-8",
    )
    print(f"medium: {medium_glyphs} glyphs, {medium_size} bytes; regular: {regular_glyphs} glyphs, {regular_size} bytes")
    print(f"wrote {OUTPUT.relative_to(ROOT)} ({OUTPUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
