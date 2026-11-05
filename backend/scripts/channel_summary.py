"""A3 渠道汇总：各渠道的人数和 7 日留存，只输出汇总数，不输出个人记录。

生产上由负责人自己运行：
    python backend/scripts/channel_summary.py --since 2026-11-01 --exclude <排除名单文件>
排除名单（访谈和测试账号，每行一个 user_id）由负责人保管，不放进仓库。
见 docs/11_商业化开发/开发框架.md 第 2 节。
"""

from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="渠道汇总（只出汇总数）")
    parser.add_argument("--since", required=True, help="起始日期 YYYY-MM-DD（北京时间）")
    parser.add_argument("--exclude", help="排除名单文件，每行一个 user_id")
    parser.parse_args()
    # TODO(A3-后端): 读 audit_logs 里 action = product_event_app_entry 的记录，按 metadata.channel 汇总
    raise NotImplementedError("A3-后端")


if __name__ == "__main__":
    raise SystemExit(main())
