"""Prepare and apply one-time account credentials without committing secrets."""

from __future__ import annotations

import argparse
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_USERNAME = "safehome_researcher_01"
DEFAULT_BASE_URL = "https://flask-gh3l-261352-9-1436233118.sh.run.tcloudbase.com"
ALLOWED_BOOTSTRAP_ROLES = {"parent", "student", "researcher", "supervisor", "admin"}
ALLOWED_TARGET_ENVIRONMENTS = {"local", "test_cloud", "production"}
ALLOWED_OPERATIONS = {"create", "rotate"}


def _read_receipt(receipt_path: Path) -> dict:
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("schema") != "safehome.one_time_credential.v1":
        raise ValueError("一次性凭据格式不兼容，请重新prepare。")
    try:
        expires_at = datetime.fromisoformat(str(receipt["expires_at"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("一次性凭据缺少有效过期时间。") from exc
    if expires_at.tzinfo is None:
        raise ValueError("一次性凭据过期时间必须包含时区。")
    if expires_at <= datetime.now(timezone.utc):
        raise ValueError("一次性凭据已过期，请重新prepare。")
    return receipt


def _validate_target_environment(receipt: dict, base_url: str) -> None:
    is_local = base_url.startswith("http://127.0.0.1") or base_url.startswith("http://localhost")
    target = receipt.get("target_environment")
    if is_local and target != "local":
        raise ValueError("非本地凭据不能应用到本地环境。")
    if not is_local and target == "local":
        raise ValueError("本地凭据不能应用到云端环境。")


def prepare(
    receipt_path: Path | None = None,
    *,
    username: str = DEFAULT_USERNAME,
    role: str = "researcher",
    nickname: str | None = None,
    target_environment: str = "local",
    operation: str = "create",
) -> Path:
    username = str(username or "").strip()
    role = str(role or "").strip()
    if len(username) < 3:
        raise ValueError("账号名至少需要3个字符。")
    if role not in ALLOWED_BOOTSTRAP_ROLES:
        raise ValueError("账号角色必须是parent、student、researcher、supervisor或admin。")
    if target_environment not in ALLOWED_TARGET_ENVIRONMENTS:
        raise ValueError("目标环境只能是local、test_cloud或production。")
    if operation not in ALLOWED_OPERATIONS:
        raise ValueError("凭据操作只能是create或rotate。")
    now = datetime.now(timezone.utc)
    timestamp = now.astimezone().strftime("%Y%m%d_%H%M%S")
    account_kind = role
    default_nicknames = {
        "parent": "安心陪伴参与者",
        "student": "安心陪伴参与者",
        "researcher": "安心陪伴研究者",
        "supervisor": "安心陪伴督导",
        "admin": "安心陪伴管理员",
    }
    target = receipt_path or ROOT / ".codex_tmp" / f"{account_kind}-account-{timestamp}.json"
    payload = {
        "schema": "safehome.one_time_credential.v1",
        "receipt_id": f"credential_receipt_{secrets.token_hex(12)}",
        "username": username,
        "password": secrets.token_urlsafe(20),
        "role": role,
        "nickname": nickname or default_nicknames[role],
        "target_environment": target_environment,
        "operation": operation,
        "status": "pending_cloud_provision",
        "created_at": now.isoformat(timespec="seconds"),
        "expires_at": (now + timedelta(hours=24)).isoformat(timespec="seconds"),
        "security_notice": "一次性凭据文件，不得提交 Git；首次登录必须修改密码。",
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def _apply_receipt(receipt_path: Path, base_url: str, admin_token: str, expected_operation: str) -> dict:
    if not admin_token:
        raise ValueError("缺少 ADMIN_EXPORT_TOKEN，不能创建或轮换云端账号。")
    receipt = _read_receipt(receipt_path)
    _validate_target_environment(receipt, base_url)
    if receipt.get("operation") != expected_operation:
        raise ValueError(f"当前命令只接受operation={expected_operation}的receipt。")
    role = str(receipt.get("role") or "researcher")
    default_nickname = "安心陪伴管理员" if role == "admin" else "安心陪伴研究者"
    request_payload = {
        "username": receipt["username"],
        "password": receipt["password"],
        "role": role,
        "nickname": receipt.get("nickname") or default_nickname,
        "rotate_existing": receipt.get("operation") == "rotate",
        "temporary_credential": True,
        "credential_receipt_id": receipt["receipt_id"],
        "credential_expires_at": receipt["expires_at"],
    }
    request = Request(
        f"{base_url.rstrip('/')}/api/auth/admin-create-account",
        data=json.dumps(request_payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Admin-Token": admin_token},
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"账号凭据操作失败：HTTP {exc.code}，请使用request_id查询服务端脱敏日志。") from exc
    except (URLError, OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"账号凭据操作失败：{type(exc).__name__}") from exc
    is_local = base_url.startswith("http://127.0.0.1") or base_url.startswith("http://localhost")
    receipt["status"] = "local_provisioned" if is_local else "cloud_provisioned"
    receipt["provisioned_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    receipt["user_id"] = result.get("data", {}).get("user", {}).get("id")
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def apply(receipt_path: Path, base_url: str, admin_token: str) -> dict:
    return _apply_receipt(receipt_path, base_url, admin_token, "create")


def rotate(receipt_path: Path, base_url: str, admin_token: str) -> dict:
    return _apply_receipt(receipt_path, base_url, admin_token, "rotate")


def _account_request(username: str, base_url: str, admin_token: str, *, action: str | None = None) -> dict:
    if not admin_token:
        raise ValueError("缺少 ADMIN_EXPORT_TOKEN，不能核验、解锁或撤销账号。")
    normalized = str(username or "").strip()
    if len(normalized) < 3:
        raise ValueError("账号名至少需要3个字符。")
    suffix = f"/{action}" if action else ""
    request = Request(
        f"{base_url.rstrip('/')}/api/auth/admin-accounts/{quote(normalized, safe='')}{suffix}",
        headers={"Accept": "application/json", "X-Admin-Token": admin_token},
        method="POST" if action else "GET",
    )
    try:
        with urlopen(request, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"账号{action or 'verify'}失败：HTTP {exc.code}，请使用request_id查询服务端脱敏日志。") from exc
    except (URLError, OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"账号{action or 'verify'}失败：{type(exc).__name__}") from exc
    return result.get("data") or {}


def verify(username: str, base_url: str, admin_token: str) -> dict:
    return _account_request(username, base_url, admin_token)


def unlock(username: str, base_url: str, admin_token: str) -> dict:
    return _account_request(username, base_url, admin_token, action="unlock")


def revoke(username: str, base_url: str, admin_token: str) -> dict:
    return _account_request(username, base_url, admin_token, action="revoke")


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--receipt", type=Path)
    prepare_parser.add_argument("--username", default=DEFAULT_USERNAME)
    prepare_parser.add_argument("--role", choices=sorted(ALLOWED_BOOTSTRAP_ROLES), default="researcher")
    prepare_parser.add_argument("--nickname")
    prepare_parser.add_argument("--target-environment", choices=sorted(ALLOWED_TARGET_ENVIRONMENTS), default="local")
    prepare_parser.add_argument("--operation", choices=sorted(ALLOWED_OPERATIONS), default="create")
    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("--receipt", type=Path, required=True)
    apply_parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    rotate_parser = subparsers.add_parser("rotate")
    rotate_parser.add_argument("--receipt", type=Path, required=True)
    rotate_parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    for command in ("verify", "unlock", "revoke"):
        account_parser = subparsers.add_parser(command)
        account_parser.add_argument("--username", default=DEFAULT_USERNAME)
        account_parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()

    if args.command == "prepare":
        path = prepare(
            args.receipt,
            username=args.username,
            role=args.role,
            nickname=args.nickname,
            target_environment=args.target_environment,
            operation=args.operation,
        )
        print(f"receipt={path}")
        print(f"username={args.username}")
        print("password=stored_in_receipt_only")
        return

    admin_token = os.environ.get("ADMIN_EXPORT_TOKEN", "")
    if args.command in {"apply", "rotate"}:
        result = apply(args.receipt, args.base_url, admin_token) if args.command == "apply" else rotate(
            args.receipt, args.base_url, admin_token
        )
        print(f"receipt={args.receipt}")
        print(f"username={result['data']['user']['username']}")
        print(f"role={result['data']['user']['role']}")
        print(f"created={result['data']['created']}")
        print(f"credentials_rotated={result['data'].get('credentials_rotated', False)}")
        return

    account_operations = {"verify": verify, "unlock": unlock, "revoke": revoke}
    result = account_operations[args.command](args.username, args.base_url, admin_token)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
