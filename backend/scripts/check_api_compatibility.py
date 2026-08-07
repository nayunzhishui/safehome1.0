"""Replay the frozen API snapshot and reject breaking public changes."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CURRENT_PATH = ROOT / "shared" / "contracts" / "api-contract.json"
BASELINE_PATH = ROOT / "shared" / "contracts" / "api-contract.baseline.json"

# Reviewed security hardenings may make object scope narrower without changing
# method/path/response compatibility.  Keep the historical baseline and admit
# only exact old->new transitions here; all other scope drift remains blocking.
ACCEPTED_OBJECT_SCOPE_STRENGTHENING = {
    "consent.list_consent_records.get": ("role_scoped", "self_or_authorized_role"),
    "consent.create_consent_record.post": ("role_scoped", "self_or_authorized_role"),
}


def _index(contract: dict) -> dict[str, dict]:
    return {item["operation_id"]: item for item in contract.get("endpoints", [])}


def _accepted_scope_strengthening(operation_id: str, old_scope: object, new_scope: object) -> bool:
    expected = ACCEPTED_OBJECT_SCOPE_STRENGTHENING.get(operation_id)
    return expected == (old_scope, new_scope)


def compatibility_errors(baseline: dict, current: dict) -> list[str]:
    errors = []
    old_items = _index(baseline)
    new_items = _index(current)
    for operation_id, old in old_items.items():
        new = new_items.get(operation_id)
        if new is None:
            deprecation = old.get("deprecation") or {}
            remove_after = deprecation.get("remove_after")
            removable = deprecation.get("status") == "deprecated" and remove_after and remove_after <= date.today().isoformat()
            if not removable:
                errors.append(f"removed active endpoint: {operation_id}")
            continue
        for key in ["method", "path", "object_scope"]:
            if old.get(key) == new.get(key):
                continue
            if key == "object_scope" and _accepted_scope_strengthening(
                operation_id, old.get(key), new.get(key)
            ):
                continue
            errors.append(f"changed {key}: {operation_id}")
        old_roles = set((old.get("access") or {}).get("roles") or [])
        new_roles = set((new.get("access") or {}).get("roles") or [])
        if not new_roles.issubset(old_roles):
            errors.append(f"widened roles: {operation_id}")
        old_idem = ((old.get("request") or {}).get("idempotency") or {}).get("required")
        new_idem = ((new.get("request") or {}).get("idempotency") or {}).get("required")
        if old_idem and not new_idem:
            errors.append(f"relaxed required idempotency: {operation_id}")
        if (old.get("response") or {}).get("envelope") != (new.get("response") or {}).get("envelope"):
            errors.append(f"changed response envelope: {operation_id}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-baseline", action="store_true")
    args = parser.parse_args()
    if args.freeze_baseline:
        BASELINE_PATH.write_text(CURRENT_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"frozen {BASELINE_PATH.relative_to(ROOT)}")
        return 0
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    current = json.loads(CURRENT_PATH.read_text(encoding="utf-8"))
    errors = compatibility_errors(baseline, current)
    if errors:
        print("API compatibility errors:\n- " + "\n- ".join(errors))
        return 1
    print(
        f"API compatibility replay passed: {len(baseline.get('endpoints', []))} frozen operations; "
        f"{len(ACCEPTED_OBJECT_SCOPE_STRENGTHENING)} reviewed scope strengthenings"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
