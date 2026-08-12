from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_rc0810_miniprogram.py"
CONTRACT = ROOT / "config" / "rc0810" / "miniprogram_cloud_targets.json"
BASELINE = ROOT / "docs" / "02_专项进度与验收" / "rc0810_f04_cloud_target_baseline.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def inspect() -> dict:
    contract = read_json(CONTRACT)
    errors: list[str] = []
    profiles = contract.get("profiles", {})
    if set(profiles) != {"development", "validation", "production"}:
        errors.append("profiles_incomplete")
    production = profiles.get("production", {})
    if production.get("runtime_overrides") is not False:
        errors.append("production_runtime_overrides_enabled")
    if production.get("transport") != "cloud-container":
        errors.append("production_transport_not_cloud_container")
    if contract.get("production_release_approved") is not False:
        errors.append("production_release_must_remain_pending")

    packages: dict[str, dict] = {}
    with tempfile.TemporaryDirectory(prefix="rc0810-f04-") as temp:
        for profile in ("production", "validation"):
            output = Path(temp) / profile
            completed = subprocess.run(
                [sys.executable, str(BUILDER), "--profile", profile, "--output", str(output), "--copy-source"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            if completed.returncode:
                errors.append(f"{profile}_build_failed")
                continue
            source = (output / "services" / "cloudConfig.js").read_text(encoding="utf-8")
            audit = read_json(output / "rc0810-cloud-target-audit.json")
            packages[profile] = {
                "target_locked": audit["target_locked"],
                "runtime_overrides_present": audit["runtime_overrides_present"],
                "production_gate_eligible": audit["production_gate_eligible"],
            }
            if profile == "production":
                forbidden = ["getExtConfigSync", "getStorageSync", "setStorageSync", "local-http", "saveCloudConfig"]
                if any(token in source for token in forbidden) or not audit["target_locked"]:
                    errors.append("production_package_switchable")
            elif "getExtConfigSync" not in source or "saveCloudConfig" not in source:
                errors.append("validation_controlled_override_missing")

    return {
        "schema": "safehome.rc0810.f04-cloud-target-baseline.v1",
        "status": "valid" if not errors else "invalid",
        "profiles": sorted(profiles),
        "production_release_approved": contract.get("production_release_approved"),
        "packages": packages,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-baseline", action="store_true")
    args = parser.parse_args()
    current = inspect()
    if args.write_baseline:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    elif not BASELINE.is_file() or read_json(BASELINE) != current:
        current["errors"] = [*current["errors"], "baseline_mismatch"]
        current["status"] = "invalid"
    print(json.dumps(current, ensure_ascii=False, indent=2))
    return 0 if current["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
