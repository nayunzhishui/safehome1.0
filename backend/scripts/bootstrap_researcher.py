"""Prepare and apply a one-time researcher credential without committing secrets."""

from __future__ import annotations

import argparse
import json
import os
import secrets
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_USERNAME = "safehome_researcher_01"
DEFAULT_BASE_URL = "https://flask-gh3l-261352-9-1436233118.sh.run.tcloudbase.com"


def prepare(receipt_path: Path | None = None) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = receipt_path or ROOT / ".codex_tmp" / f"researcher-account-{timestamp}.json"
    payload = {
        "username": DEFAULT_USERNAME,
        "password": secrets.token_urlsafe(20),
        "role": "researcher",
        "nickname": "安心陪伴研究者",
        "status": "pending_cloud_provision",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "security_notice": "一次性凭据文件，不得提交 Git；首次登录后应轮换密码。",
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def apply(receipt_path: Path, base_url: str, admin_token: str) -> dict:
    if not admin_token:
        raise ValueError("缺少 ADMIN_EXPORT_TOKEN，不能创建或轮换云端账号。")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    role = str(receipt.get("role") or "researcher")
    default_nickname = "安心陪伴管理员" if role == "admin" else "安心陪伴研究者"
    request_payload = {
        "username": receipt["username"],
        "password": receipt["password"],
        "role": role,
        "nickname": receipt.get("nickname") or default_nickname,
        "rotate_existing": True,
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
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"云端创建账号失败：HTTP {exc.code} {body}") from exc
    except (URLError, OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"云端创建账号失败：{exc}") from exc
    is_local = base_url.startswith("http://127.0.0.1") or base_url.startswith("http://localhost")
    receipt["status"] = "local_provisioned" if is_local else "cloud_provisioned"
    receipt["provisioned_at"] = datetime.now().isoformat(timespec="seconds")
    receipt["user_id"] = result.get("data", {}).get("user", {}).get("id")
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--receipt", type=Path)
    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("--receipt", type=Path, required=True)
    apply_parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()

    if args.command == "prepare":
        path = prepare(args.receipt)
        print(f"receipt={path}")
        print(f"username={DEFAULT_USERNAME}")
        print("password=stored_in_receipt_only")
        return

    result = apply(args.receipt, args.base_url, os.environ.get("ADMIN_EXPORT_TOKEN", ""))
    print(f"receipt={args.receipt}")
    print(f"username={result['data']['user']['username']}")
    print(f"role={result['data']['user']['role']}")
    print(f"created={result['data']['created']}")


if __name__ == "__main__":
    main()
