"""B6 由内容盘点表生成内容地图初稿。

    python backend/scripts/build_content_map.py --inventory "D:/桌面/Desktop/2026.10work/内容库/00_现有内容盘点_内容地图初稿.csv"

盘点表在 Excel 里改，改完另存为 CSV（UTF-8）再运行，后端不为此加 openpyxl 依赖。
输出 content/content_map.json：已有条目保留人工补的标签，只补新增条目。
见 docs/11_商业化开发/开发框架.md 第 8 节。
"""

from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="由盘点表生成内容地图初稿")
    parser.add_argument("--inventory", required=True, help="盘点表导出的 CSV（UTF-8）")
    parser.add_argument("--dry-run", action="store_true", help="只打印差异，不写文件")
    parser.parse_args()
    # TODO(B6-后端): 读 CSV → 合并进 content/content_map.json → 调用 content_map_service.validate_references()
    raise NotImplementedError("B6-后端")


if __name__ == "__main__":
    raise SystemExit(main())
