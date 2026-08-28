#!/usr/bin/env python3
"""Validate F03 container profiles and guard container startup."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "config" / "rc0810" / "container_profiles.json"
TRUE_VALUES = {"1", "true", "yes"}


def _docker_env(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    logical = text.replace("\\\r\n", " ").replace("\\\n", " ")
    for match in re.finditer(r"(?:^|\n)ENV\s+([^\n]+)", logical):
        for name, value in re.findall(r"([A-Z][A-Z0-9_]*)=([^\s]+)", match.group(1)):
            values[name] = value.strip()
    return values


def _is_enabled(value: str | None) -> bool:
    return str(value or "").strip().lower() in TRUE_VALUES


def validate_files(production: Path, validation: Path, policy_path: Path) -> dict:
    errors: list[str] = []
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        production_text = production.read_text(encoding="utf-8")
        validation_text = validation.read_text(encoding="utf-8")
    except (OSError, ValueError, KeyError) as exc:
        return {"valid": False, "errors": [f"profile_input_invalid: {exc}"]}

    texts = {"production": production_text, "validation": validation_text}
    envs = {name: _docker_env(text) for name, text in texts.items()}
    for profile in ("production", "validation"):
        contract = policy[profile]
        env = envs[profile]
        if env.get("APP_ENV") != contract["app_env"]:
            errors.append(f"{profile}: APP_ENV mismatch")
        for flag in contract.get("required_enabled_flags", []):
            if not _is_enabled(env.get(flag)):
                errors.append(f"{profile}: {flag} must be enabled")
        for flag in contract.get("required_disabled_flags", []):
            if _is_enabled(env.get(flag)):
                errors.append(f"{profile}: {flag} must be disabled")
        for secret in policy["secret_names"]:
            if re.search(rf"(?:^|\s){re.escape(secret)}=", texts[profile]):
                errors.append(f"{profile}: {secret} must be runtime injected")

    expected_cmd = "CMD " + json.dumps(policy["application_command"], ensure_ascii=False)
    for profile, text in texts.items():
        if expected_cmd not in text:
            errors.append(f"{profile}: application command mismatch")
        if f'--profile\", \"{profile}' not in text:
            errors.append(f"{profile}: immutable entrypoint profile missing")

    return {
        "schema": "safehome.rc0810.f03-verification.v1",
        "valid": not errors,
        "errors": errors,
        "profiles": {
            name: {
                "app_env": envs[name].get("APP_ENV"),
                "production_gate_eligible": bool(policy[name]["production_gate_eligible"]),
            }
            for name in ("production", "validation")
        },
    }


def guard_runtime(profile: str) -> list[str]:
    errors: list[str] = []
    expected_env = "production" if profile == "production" else "validation"
    if os.environ.get("APP_ENV") != expected_env:
        errors.append(f"{profile}: APP_ENV must remain {expected_env}")
    if profile == "production":
        for flag in (
            "PRODUCTION_FEATURES_UNLOCKED",
            "CONTENT_GOVERNANCE_PUBLISH_ENABLED",
            "PRIVACY_EXECUTION_ENABLED",
            "PRIVACY_PRODUCTION_EXECUTION_ENABLED",
            "RESEARCH_OPERATIONS_WRITE_ENABLED",
            "AI_QA_ENABLED",
            "AI_QA_SANDBOX_ENABLED",
            "AI_QA_REAL_PROVIDER_ENABLED",
            "THERAPEUTIC_ASSESSMENT_LIFECYCLE_ENABLED",
            "OFFLINE_BENCHMARK_ENABLED",
            "OFFLINE_EXTERNAL_INGEST_ENABLED",
            "OFFLINE_PRODUCTION_REPLACEMENT_ALLOWED",
            "RESEARCH_METHODOLOGY_FORMAL_FREEZE_ALLOWED",
            "RESEARCH_OUTCOME_ANALYSIS_ALLOWED",
            "RESEARCH_ANALYSIS_JOB_EXECUTION_ENABLED",
            "SECURITY_SCAN_EXECUTION_ENABLED",
            "RELIABILITY_JOB_EXECUTION_ENABLED",
            "RELIABILITY_FAULT_INJECTION_ENABLED",
            "RELIABILITY_GRADUAL_RELEASE_ENABLED",
            "OPERATIONS_LOCAL_RELEASE_ENABLED",
            "OPERATIONS_PRODUCTION_RELEASE_ENABLED",
        ):
            if _is_enabled(os.environ.get(flag)):
                errors.append(f"production: runtime override rejected for {flag}")
    elif profile == "validation":
        for flag in (
            "PRIVACY_PRODUCTION_EXECUTION_ENABLED",
            "AI_QA_REAL_PROVIDER_ENABLED",
            "OFFLINE_PRODUCTION_REPLACEMENT_ALLOWED",
            "RELIABILITY_FAULT_INJECTION_ENABLED",
            "OPERATIONS_PRODUCTION_RELEASE_ENABLED",
        ):
            if _is_enabled(os.environ.get(flag)):
                errors.append(f"validation: production-only override rejected for {flag}")
    else:
        errors.append(f"unknown profile: {profile}")
    return errors


def verify_runtime_images() -> dict:
    policy = json.loads(DEFAULT_POLICY.read_text(encoding="utf-8"))
    images = {
        "production": "safehome-rc0810-f03-production:local",
        "validation": "safehome-rc0810-f03-validation:local",
    }
    errors: list[str] = []
    inspected: dict[str, dict] = {}
    route_sets: dict[str, list[str]] = {}
    for profile, image in images.items():
        result = subprocess.run(
            ["docker", "image", "inspect", image], capture_output=True, text=True, encoding="utf-8"
        )
        if result.returncode != 0:
            errors.append(f"{profile}: image unavailable")
            continue
        data = json.loads(result.stdout)[0]
        config = data["Config"]
        inspected[profile] = {"image_id": data["Id"], "entrypoint": config["Entrypoint"], "cmd": config["Cmd"]}
        expected_profile = ["--profile", profile]
        joined = " ".join(config.get("Entrypoint") or [])
        if " ".join(expected_profile) not in joined:
            errors.append(f"{profile}: image entrypoint profile mismatch")

        history = subprocess.run(
            ["docker", "history", "--no-trunc", "--format", "{{.CreatedBy}}", image],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        config_text = "\n".join(config.get("Env") or [])
        scan_text = config_text + "\n" + history.stdout
        for secret in ("SECRET_KEY", "MYSQL_PASSWORD", "WECHAT_SECRET", "DEEPSEEK_API_KEY", "ADMIN_EXPORT_TOKEN"):
            if re.search(rf"(?:^|\s){re.escape(secret)}=", scan_text):
                errors.append(f"{profile}: {secret} found in image config/history")

        runtime_environment = "testing" if profile == "production" else "validation"
        environment = [
            "docker", "run", "--rm",
            "-e", f"APP_ENV={runtime_environment}",
            "-e", "DB_PROVIDER=sqlite",
            "-e", "DATABASE_PATH=/app/data/rc0810-runtime.sqlite3",
            "-e", "SECRET_KEY=rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr",
            "-e", "ADMIN_EXPORT_TOKEN=rc0810-runtime-test-token",
        ]
        if profile == "validation":
            environment += ["-e", "PRODUCTION_FEATURES_UNLOCKED=1"]
        required_flags = policy[profile].get("required_enabled_flags", [])
        disabled_flags = policy[profile].get("required_disabled_flags", [])
        runtime_flags = required_flags + disabled_flags
        probe = (
            "import json; from app import app; "
            "response=app.test_client().get('/healthz'); "
            "print(json.dumps({'status_code':response.status_code,'health':response.get_json(),"
            f"'capabilities':{{name:bool(app.config.get(name)) for name in {runtime_flags!r}}},"
            "'routes':sorted(str(rule) for rule in app.url_map.iter_rules())}))"
        )
        run = subprocess.run(
            environment + [image, "python", "-c", probe],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if run.returncode != 0:
            errors.append(f"{profile}: image entrypoint execution failed")
            continue
        try:
            probe_result = json.loads(run.stdout)
        except ValueError:
            errors.append(f"{profile}: runtime probe output invalid")
            continue
        route_sets[profile] = probe_result.get("routes", [])
        inspected[profile]["ready"] = probe_result.get("status_code") == 200
        inspected[profile]["probe_environment"] = runtime_environment
        inspected[profile]["health_service"] = (probe_result.get("health") or {}).get("service")
        inspected[profile]["route_count"] = len(route_sets[profile])
        inspected[profile]["enabled_capabilities"] = probe_result.get("capabilities", {})
        if not inspected[profile]["ready"] or inspected[profile]["health_service"] != "safehome-backend":
            errors.append(f"{profile}: health contract mismatch")
        missing_capabilities = [name for name in required_flags if not inspected[profile]["enabled_capabilities"].get(name)]
        if missing_capabilities:
            errors.append(f"{profile}: runtime capabilities disabled: {', '.join(missing_capabilities)}")
        enabled_forbidden = [name for name in disabled_flags if inspected[profile]["enabled_capabilities"].get(name)]
        if enabled_forbidden:
            errors.append(f"{profile}: forbidden runtime capabilities enabled: {', '.join(enabled_forbidden)}")

        filesystem_probe = (
            "import json; from pathlib import Path; root=Path('/app'); "
            "bad=[str(p) for pattern in ('*.sqlite','*.sqlite3','*.db','*.pyc') for p in root.rglob(pattern)]; "
            "bad += [str(p) for p in root.rglob('__pycache__')]; "
            "print(json.dumps({'tests_dir':(root/'backend/tests').exists(),'forbidden':bad}))"
        )
        filesystem = subprocess.run(
            ["docker", "run", "--rm", "--entrypoint", "python", image, "-c", filesystem_probe],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        try:
            filesystem_result = json.loads(filesystem.stdout)
        except ValueError:
            errors.append(f"{profile}: filesystem probe output invalid")
        else:
            inspected[profile]["filesystem_clean"] = not filesystem_result["tests_dir"] and not filesystem_result["forbidden"]
            if filesystem_result["tests_dir"]:
                errors.append(f"{profile}: backend/tests found in image filesystem")
            if filesystem_result["forbidden"]:
                errors.append(f"{profile}: local runtime artifacts found in image filesystem")

    if route_sets.get("production") != route_sets.get("validation"):
        errors.append("production/validation: route inventory mismatch")

    blocked = subprocess.run(
        [
            "docker", "run", "--rm", "-e", "APP_ENV=production", "-e", "AI_QA_ENABLED=1",
            images["production"], "python", "-c", "print('must-not-run')",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if blocked.returncode != 78 or "must-not-run" in blocked.stdout:
        errors.append("production: illegal runtime override was not rejected")

    return {
        "schema": "safehome.rc0810.f03-runtime-verification.v1",
        "valid": not errors,
        "errors": errors,
        "images": inspected,
        "production_override_exit": blocked.returncode,
    }


def build_image(profile: str) -> dict:
    dockerfile = "Dockerfile" if profile == "production" else "deploy/Dockerfile.validation"
    image = f"safehome-rc0810-f03-{profile}:local"
    result = subprocess.run(
        ["docker", "build", "--pull=false", "-t", image, "-f", dockerfile, "."], cwd=ROOT
    )
    return {"valid": result.returncode == 0, "profile": profile, "image": image, "exit_code": result.returncode}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--production", type=Path, default=ROOT / "Dockerfile")
    parser.add_argument("--validation", type=Path, default=ROOT / "deploy" / "Dockerfile.validation")
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--entrypoint", action="store_true")
    parser.add_argument("--runtime", action="store_true")
    parser.add_argument("--build", choices=("production", "validation"))
    parser.add_argument("--profile", choices=("production", "validation"))
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if args.build:
        result = build_image(args.build)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["valid"] else 1

    if args.runtime:
        result = verify_runtime_images()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["valid"] else 1

    if args.entrypoint:
        errors = guard_runtime(args.profile or "")
        if errors:
            print(json.dumps({"valid": False, "errors": errors}, ensure_ascii=False))
            return 78
        command = args.command[1:] if args.command[:1] == ["--"] else args.command
        if not command:
            print(json.dumps({"valid": False, "errors": ["application command missing"]}, ensure_ascii=False))
            return 78
        os.execvp(command[0], command)

    result = validate_files(args.production.resolve(), args.validation.resolve(), args.policy.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
