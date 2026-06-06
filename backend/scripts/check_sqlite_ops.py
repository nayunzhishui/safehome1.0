"""Read-only SQLite operations checklist for deployment preparation."""

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "backend" / "safehome.sqlite3"
BACKUP_SCRIPT = PROJECT_ROOT / "backend" / "scripts" / "backup_sqlite.py"
RESTORE_SCRIPT = PROJECT_ROOT / "backend" / "scripts" / "restore_sqlite.py"
GITIGNORE = PROJECT_ROOT / ".gitignore"


def _database_path() -> Path:
    return Path(os.environ.get("DATABASE_PATH", DEFAULT_DATABASE_PATH)).resolve()


def _nearest_existing_parent(path: Path) -> Path | None:
    current = path.parent
    while current != current.parent:
        if current.exists():
            return current
        current = current.parent
    return current if current.exists() else None


def _is_temp_path(path: Path) -> bool:
    lowered = str(path).lower()
    temp_markers = ["\\temp\\", "\\tmp\\", "/tmp/", "/temp/"]
    return any(marker in lowered for marker in temp_markers)


def _gitignore_contains_backups() -> bool:
    if not GITIGNORE.exists():
        return False
    lines = [line.strip() for line in GITIGNORE.read_text(encoding="utf-8").splitlines()]
    return "backups/" in lines or "backups" in lines


def check() -> tuple[list[str], list[str], list[str]]:
    ok: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []

    database_path = _database_path()
    if os.environ.get("DATABASE_PATH"):
        ok.append(f"DATABASE_PATH 已配置：{database_path}")
    else:
        warnings.append(f"DATABASE_PATH 未显式配置，将使用默认路径：{database_path}")

    if database_path.parent.exists():
        ok.append(f"DATABASE_PATH 父目录存在：{database_path.parent}")
    else:
        nearest = _nearest_existing_parent(database_path)
        if nearest and os.access(nearest, os.W_OK):
            warnings.append(f"DATABASE_PATH 父目录尚不存在，但上级目录可写：{nearest}")
        else:
            errors.append(f"DATABASE_PATH 父目录不存在且未确认可创建：{database_path.parent}")

    if _is_temp_path(database_path):
        warnings.append(f"DATABASE_PATH 位于明显临时目录，试用/生产环境不建议使用：{database_path}")
    else:
        ok.append("DATABASE_PATH 未位于明显临时目录")

    if _gitignore_contains_backups():
        ok.append("backups/ 已加入 .gitignore")
    else:
        errors.append("backups/ 未加入 .gitignore")

    if BACKUP_SCRIPT.exists():
        ok.append("backup_sqlite.py 存在")
    else:
        errors.append("backup_sqlite.py 不存在")

    if RESTORE_SCRIPT.exists():
        ok.append("restore_sqlite.py 存在")
        restore_text = RESTORE_SCRIPT.read_text(encoding="utf-8")
        if "before_restore" in restore_text and "copy2(target, before_restore)" in restore_text:
            ok.append("restore_sqlite.py 包含恢复前备份逻辑")
        else:
            errors.append("restore_sqlite.py 未检测到恢复前备份逻辑")
    else:
        errors.append("restore_sqlite.py 不存在")

    return ok, warnings, errors


def main() -> int:
    ok, warnings, errors = check()
    for item in ok:
        print(f"ok: {item}")
    for item in warnings:
        print(f"warning: {item}")
    for item in errors:
        print(f"error: {item}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
