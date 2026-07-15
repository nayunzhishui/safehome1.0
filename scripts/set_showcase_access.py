"""Open or close the reversible SafeHome showcase access switch."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "content" / "showcase_access.json"


def set_mode(enabled: bool) -> dict:
    payload = {
        "version": "2026.07-showcase-v1",
        "enabled": enabled,
        "read_only_role_bypass": enabled,
        "open_programs": enabled,
        "allow_program_participation": enabled,
        "open_training_cards": enabled,
        "open_courses": enabled,
        "notice": (
            "临时展示模式已开启：登录用户可查看跨角色内容并参加项目试点；高风险阻断、数据归属和后台管理写权限保持不变。"
            if enabled
            else "展示模式已关闭：恢复正式角色、项目审核和训练卡发布门禁。"
        ),
        "updated_at": date.today().isoformat(),
    }
    temporary = TARGET.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(TARGET)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("open", "close"))
    args = parser.parse_args()
    payload = set_mode(args.mode == "open")
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
