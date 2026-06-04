"""Create a timestamped backup of the configured SQLite database."""

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "backend" / "safehome.sqlite3"
BACKUP_DIR = PROJECT_ROOT / "backups"


def database_path() -> Path:
    return Path(os.environ.get("DATABASE_PATH", DEFAULT_DATABASE_PATH)).resolve()


def main() -> int:
    source = database_path()
    if not source.exists():
        print(f"数据库文件不存在：{source}", file=sys.stderr)
        return 1

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = BACKUP_DIR / f"safehome_{timestamp}.sqlite3"
    shutil.copy2(source, target)
    print(f"SQLite 备份完成：{target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
