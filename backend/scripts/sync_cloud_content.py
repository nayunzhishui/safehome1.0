"""Operator client for the admin content sync (training cards and assessment worksheets).

Usage (from the repository root, after the new package is deployed):
    python backend/scripts/sync_cloud_content.py plan
    python backend/scripts/sync_cloud_content.py apply --plan-hash <hash printed by plan>
    python backend/scripts/sync_cloud_content.py restore --backup <backup file written by plan>

The admin session token is read from --session (default: the git-ignored
.codex_tmp/claude-20261007/secret/admin-session.json written by save_admin_session.py).
The token is never printed.  `plan` writes the full backup of the current database rows
(blank content definitions only) next to the session folder and prints IDs and field
names, never the definitions themselves.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SESSION = ROOT / ".codex_tmp" / "claude-20261007" / "secret" / "admin-session.json"
DEFAULT_BACKUP_DIR = ROOT / ".codex_tmp" / "content-sync"


def _session(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"没有找到管理员会话文件：{path}。请先运行 save_admin_session.py。")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("role") != "admin" or not data.get("token") or not data.get("base_url"):
        raise SystemExit("管理员会话文件不完整，请重新运行 save_admin_session.py。")
    return data


def _call(session: dict, method: str, path: str, payload: dict | None = None) -> tuple[int, dict | None]:
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {session['token']}",
        "X-Request-ID": str(uuid.uuid4()),
    }
    body = None
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(session["base_url"].rstrip("/") + path, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=120) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode("utf-8"))
        except Exception:
            return exc.code, None
    except URLError as exc:
        raise SystemExit(f"网络连接失败：{type(exc).__name__}")


def _require_ok(status: int, payload: dict | None, action: str) -> dict:
    if status != 200 or not payload or not payload.get("ok", True):
        error = (payload or {}).get("error") or {}
        raise SystemExit(f"{action}没有成功：HTTP {status} {error.get('code') or ''} {error.get('message') or ''}".strip())
    return payload.get("data") or {}


def _print_tables(tables: dict) -> None:
    for table, summary in tables.items():
        print(f"[{table}] 新增 {len(summary['create'])}，更新 {len(summary['update'])}，未变 {summary['unchanged']}，库中多出 {len(summary['unknown_in_db'])}")
        if summary["create"]:
            print("  新增：", ", ".join(summary["create"]))
        for item in summary["update"]:
            print(f"  更新：{item['id']} -> {', '.join(item['fields'])}")
        if summary["unknown_in_db"]:
            print("  库中多出（不会删除）：", ", ".join(summary["unknown_in_db"]))


def plan(session: dict, backup_dir: Path) -> None:
    data = _require_ok(*_call(session, "GET", "/api/admin/content-sync/plan"), "读取同步计划")
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"content-backup-{stamp}.json"
    backup_path.write_text(
        json.dumps({"backup": data["backup"], "backup_hash": data["backup_hash"], "plan_hash": data["plan_hash"]}, ensure_ascii=False),
        encoding="utf-8",
    )
    print("内容版本：", json.dumps(data.get("content_versions"), ensure_ascii=False))
    _print_tables(data["tables"])
    print("已一致：" if data["in_sync"] else "需要同步：", "是" if data["in_sync"] else "否")
    print("备份文件：", backup_path)
    print("plan_hash：", data["plan_hash"])


def apply(session: dict, plan_hash: str) -> None:
    data = _require_ok(*_call(session, "POST", "/api/admin/content-sync/apply", {"plan_hash": plan_hash}), "执行同步")
    print("同步前：")
    _print_tables(data["before"])
    print("同步后：")
    _print_tables(data["after"])
    check = _require_ok(*_call(session, "GET", "/api/admin/content-sync/plan"), "复核同步结果")
    print("复核：数据库与已发布内容一致" if check["in_sync"] else "复核：仍有差异，请停止并检查")
    listing = _require_ok(*_call(session, "GET", "/api/assessments"), "读取用户端问卷列表")
    print("用户端可见问卷数量：", len(listing.get("items") or []))
    cards = _require_ok(*_call(session, "GET", "/api/cards"), "读取用户端训练卡列表")
    print("用户端可见训练卡数量：", len(cards.get("items") or []))


def restore(session: dict, backup_path: Path) -> None:
    saved = json.loads(backup_path.read_text(encoding="utf-8"))
    data = _require_ok(
        *_call(session, "POST", "/api/admin/content-sync/restore", {"backup": saved["backup"], "confirm": "restore"}),
        "恢复备份",
    )
    print("已恢复行数：", json.dumps(data["rows"], ensure_ascii=False))
    print("已移除（备份之后新增）：", json.dumps(data["removed_ids"], ensure_ascii=False))
    _print_tables(data["plan_after_restore"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--session", type=Path, default=DEFAULT_SESSION)
    sub = parser.add_subparsers(dest="command", required=True)
    plan_parser = sub.add_parser("plan")
    plan_parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR)
    apply_parser = sub.add_parser("apply")
    apply_parser.add_argument("--plan-hash", required=True)
    restore_parser = sub.add_parser("restore")
    restore_parser.add_argument("--backup", type=Path, required=True)
    args = parser.parse_args()
    session = _session(args.session)
    if args.command == "plan":
        plan(session, args.backup_dir)
    elif args.command == "apply":
        apply(session, args.plan_hash)
    else:
        restore(session, args.backup)
    return 0


if __name__ == "__main__":
    sys.exit(main())
