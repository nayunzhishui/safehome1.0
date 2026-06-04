"""Restore the configured SQLite database from a backup file."""

import argparse
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "backend" / "safehome.sqlite3"


def database_path() -> Path:
    return Path(os.environ.get("DATABASE_PATH", DEFAULT_DATABASE_PATH)).resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Restore SafeHome SQLite database from a backup file.")
    parser.add_argument("backup_path", help="Path to the backup SQLite file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    backup = Path(args.backup_path).resolve()
    target = database_path()

    if not backup.exists():
        print(f"备份文件不存在：{backup}", file=sys.stderr)
        return 1

    if target.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        before_restore = target.with_name(f"{target.name}.before_restore_{timestamp}")
        shutil.copy2(target, before_restore)
        print(f"已保存恢复前数据库：{before_restore}")

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup, target)
    print(f"SQLite 恢复完成：{target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
