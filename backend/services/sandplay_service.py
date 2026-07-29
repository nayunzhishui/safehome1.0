"""Sandplay-style expression task helpers migrated from ReadFeedback."""

from __future__ import annotations

from typing import Any

from services.content_loader import load_sandplay_tasks


class SandplayInputError(ValueError):
    """Raised when a submitted sandplay scene is invalid."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("；".join(errors))
        self.errors = errors


def validate_sandplay_scene(scene: dict[str, Any]) -> None:
    payload = load_sandplay_tasks()
    allowed_types = {symbol.get("type") for symbol in payload.get("symbols", [])}
    errors: list[str] = []
    symbols = scene.get("symbols") if isinstance(scene, dict) else None
    if not isinstance(symbols, list):
        raise SandplayInputError(["沙盘场景格式无效。"])
    if not 1 <= len(symbols) <= 12:
        errors.append("请放入 1-12 个象征物。")
    for item in symbols:
        if not isinstance(item, dict):
            errors.append("象征物格式无效。")
            continue
        if item.get("type") not in allowed_types:
            errors.append("包含未支持的象征物。")
        try:
            x = float(item.get("x"))
            y = float(item.get("y"))
        except (TypeError, ValueError):
            errors.append("象征物位置无效。")
            continue
        if not 0 <= x <= 100 or not 0 <= y <= 100:
            errors.append("象征物位置超出沙盘范围。")
    if errors:
        raise SandplayInputError(errors[:3])


def summarize_sandplay_scene(scene: dict[str, Any]) -> dict[str, Any]:
    payload = load_sandplay_tasks()
    symbol_lookup = {symbol.get("type"): symbol for symbol in payload.get("symbols", [])}
    counts: dict[str, int] = {}
    xs: list[float] = []
    ys: list[float] = []
    for item in scene.get("symbols", []):
        meta = symbol_lookup.get(item.get("type"), {})
        category = str(meta.get("category", "other"))
        counts[category] = counts.get(category, 0) + 1
        xs.append(float(item.get("x", 50)))
        ys.append(float(item.get("y", 50)))

    spread = 0.0
    if len(xs) > 1:
        mean_x = sum(xs) / len(xs)
        mean_y = sum(ys) / len(ys)
        spread = sum(((xs[index] - mean_x) ** 2 + (ys[index] - mean_y) ** 2) ** 0.5 for index in range(len(xs))) / len(xs)

    resource_count = counts.get("resource", 0)
    stress_count = counts.get("stress", 0)
    observation = "资源象征和压力象征可以作为下一轮访谈线索。"
    if stress_count > resource_count:
        observation = "压力象征多于资源象征，下一轮可优先寻找支持、例外经验和可行动的小步骤。"
    elif resource_count > stress_count:
        observation = "资源象征较明显，下一轮可追踪这些资源在真实情境中是否能被调用。"

    return {
        "symbol_count": len(scene.get("symbols", [])),
        "stress_count": stress_count,
        "resource_count": resource_count,
        "category_counts": counts,
        "spatial_spread": round(spread, 1),
        "observation": observation,
        "note": "此摘要只作为表达和访谈线索，不用于诊断。",
    }
