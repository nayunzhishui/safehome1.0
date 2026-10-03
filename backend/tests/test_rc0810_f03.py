import json
import os
import subprocess
import sys
from pathlib import Path

import importlib.util
import pytest


ROOT = Path(__file__).resolve().parents[2]
PRODUCTION = ROOT / "Dockerfile"
VALIDATION = ROOT / "deploy" / "Dockerfile.validation"
POLICY = ROOT / "config" / "rc0810" / "container_profiles.json"
VERIFY = ROOT / "deploy" / "verify_rc0810_f03_images.py"


def test_f03_production_image_is_fail_closed():
    text = PRODUCTION.read_text(encoding="utf-8")
    assert "PRODUCTION_FEATURES_UNLOCKED=1" not in text
    assert "AI_QA_REAL_PROVIDER_ENABLED=1" not in text
    assert "OPERATIONS_PRODUCTION_RELEASE_ENABLED=1" not in text


def test_f03_validation_image_keeps_explicit_validation_capabilities():
    text = VALIDATION.read_text(encoding="utf-8")
    assert "APP_ENV=validation" in text
    assert "PRODUCTION_FEATURES_UNLOCKED=1" in text
    assert "AI_QA_SANDBOX_ENABLED=1" in text
    assert "THERAPEUTIC_ASSESSMENT_LIFECYCLE_ENABLED=1" in text
    assert "RESEARCH_METHODOLOGY_WORKBENCH_ENABLED=1" in text
    assert "RESEARCH_OUTCOME_ANALYSIS_ALLOWED=1" in text
    assert "RELIABILITY_FAULT_INJECTION_ENABLED=0" in text


def test_f03_images_do_not_embed_secret_values():
    text = PRODUCTION.read_text(encoding="utf-8") + VALIDATION.read_text(encoding="utf-8")
    for name in ["SECRET_KEY", "MYSQL_PASSWORD", "WECHAT_SECRET", "DEEPSEEK_API_KEY", "ADMIN_EXPORT_TOKEN"]:
        assert f"{name}=" not in text


def test_f03_profile_policy_matches_dockerfiles():
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    assert policy["production"]["dockerfile"] == "Dockerfile"
    assert policy["validation"]["dockerfile"] == "deploy/Dockerfile.validation"
    assert policy["production"]["production_gate_eligible"] is False


def test_f03_verifier_accepts_current_profiles():
    result = subprocess.run([sys.executable, str(VERIFY)], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["valid"] is True


def test_f03_verifier_rejects_production_unlock(tmp_path):
    bad = tmp_path / "Dockerfile"
    bad.write_text(PRODUCTION.read_text(encoding="utf-8") + "\nENV PRODUCTION_FEATURES_UNLOCKED=1\n", encoding="utf-8")
    result = subprocess.run([sys.executable, str(VERIFY), "--production", str(bad)], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode != 0
    assert "production" in result.stdout.lower()


def test_f03_both_profiles_use_same_application_entrypoint():
    production = PRODUCTION.read_text(encoding="utf-8")
    validation = VALIDATION.read_text(encoding="utf-8")
    command = 'CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]'
    assert command in production
    assert command in validation


def test_f03_database_and_provider_configuration_are_runtime_injected():
    production = PRODUCTION.read_text(encoding="utf-8")
    assert "MYSQL_HOST=" not in production
    assert "DATABASE_PATH=" not in production


def test_f03_images_package_database_profile_contract():
    copy_contract = (
        "COPY config/rc0810/database_profiles.json "
        "/app/config/rc0810/database_profiles.json"
    )
    assert copy_contract in PRODUCTION.read_text(encoding="utf-8")
    assert copy_contract in VALIDATION.read_text(encoding="utf-8")


def test_f03_production_runtime_override_is_rejected():
    execution_flags = [
        "AI_QA_ENABLED",
        "THERAPEUTIC_ASSESSMENT_LIFECYCLE_ENABLED",
        "OFFLINE_BENCHMARK_ENABLED",
        "RESEARCH_METHODOLOGY_FORMAL_FREEZE_ALLOWED",
        "RESEARCH_OUTCOME_ANALYSIS_ALLOWED",
        "RESEARCH_ANALYSIS_JOB_EXECUTION_ENABLED",
        "SECURITY_SCAN_EXECUTION_ENABLED",
        "RELIABILITY_JOB_EXECUTION_ENABLED",
        "RELIABILITY_GRADUAL_RELEASE_ENABLED",
        "OPERATIONS_LOCAL_RELEASE_ENABLED",
    ]
    for flag in execution_flags:
        environment = os.environ.copy()
        environment.update({"APP_ENV": "production", flag: "1"})
        result = subprocess.run(
            [
                sys.executable,
                str(VERIFY),
                "--entrypoint",
                "--profile",
                "production",
                "--",
                sys.executable,
                "-c",
                "print('must-not-run')",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=environment,
        )
        assert result.returncode == 78, flag
        assert f"runtime override rejected for {flag}" in result.stdout
        assert "must-not-run" not in result.stdout


def test_f03_validation_runtime_executes_allowed_command():
    environment = os.environ.copy()
    environment.update(
        {
            "APP_ENV": "validation",
            "PRODUCTION_FEATURES_UNLOCKED": "1",
            "PRIVACY_PRODUCTION_EXECUTION_ENABLED": "0",
            "AI_QA_REAL_PROVIDER_ENABLED": "0",
            "OFFLINE_PRODUCTION_REPLACEMENT_ALLOWED": "0",
            "RELIABILITY_FAULT_INJECTION_ENABLED": "0",
            "OPERATIONS_PRODUCTION_RELEASE_ENABLED": "0",
        }
    )
    result = subprocess.run(
        [
            sys.executable,
            str(VERIFY),
            "--entrypoint",
            "--profile",
            "validation",
            "--",
            sys.executable,
            "-c",
            "print('validation-ready')",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "validation-ready"


def test_f03_runtime_verifier_contract_is_exposed():
    text = VERIFY.read_text(encoding="utf-8")
    assert 'parser.add_argument("--runtime"' in text
    assert "production_override_exit" in text
    assert "image config/history" in text
    assert "route inventory mismatch" in text
    assert 'parser.add_argument("--build"' in text
    assert "backend/tests found in image filesystem" in text
    assert "local runtime artifacts found in image filesystem" in text
    assert "runtime capabilities disabled" in text
    assert "forbidden runtime capabilities enabled" in text


def test_runtime_policy_files_and_governance_texts_are_packaged():
    policies = ["operations_reliability_policy.json", "research_execution_manifest_policy.json", "database_recovery_policy.json"]
    for dockerfile in [PRODUCTION, VALIDATION]:
        text = dockerfile.read_text(encoding="utf-8")
        for filename in policies:
            assert f"config/rc0810/{filename}" in text
            assert (ROOT / "config/rc0810" / filename).is_file()
    ignore = (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
    for filename in ["consent.md", "privacy.md"]:
        exception = f"!content/{filename}"
        assert exception in ignore
        assert ignore.index(exception) > ignore.index("*.md")


@pytest.mark.parametrize("dockerfile", [PRODUCTION, VALIDATION])
def test_gunicorn_home_is_owned_runtime_directory(dockerfile):
    text = dockerfile.read_text(encoding="utf-8")
    assert "ENV HOME=/app/data" in text
    assert "mkdir -p /app/data" in text
    assert "safehome:safehome /app/data" in text
    assert "USER safehome" in text


@pytest.mark.parametrize("guard_rejected", [False, True])
def test_runtime_verifier_separates_production_guard_and_synthetic_app(monkeypatch, guard_rejected):
    spec = importlib.util.spec_from_file_location("f03_runtime_probe", VERIFY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    calls = []

    def fake_run(command, **_kwargs):
        calls.append(command)
        profile = "validation" if any("f03-validation" in str(part) for part in command) else "production"
        flags = {name: True for name in policy[profile].get("required_enabled_flags", [])}
        flags.update({name: False for name in policy[profile].get("required_disabled_flags", [])})
        if command[1:3] == ["image", "inspect"]:
            payload = [{"Id": "synthetic-image", "Config": {
                "Entrypoint": ["python", "/app/verify_rc0810_f03_images.py", "--entrypoint", "--profile", profile, "--"],
                "Cmd": policy["application_command"], "Env": [],
            }}]
        elif command[1] == "history":
            payload = None
        elif "must-not-run" in command[-1]:
            return subprocess.CompletedProcess(command, 78, "blocked", "")
        elif "tests_dir" in command[-1]:
            payload = {"tests_dir": False, "forbidden": []}
        elif "from config import Config" in command[-1]:
            assert "--entrypoint" not in command
            assert f"APP_ENV={profile}" in command
            assert "DB_PROVIDER=sqlite" not in command
            if profile == "production" and guard_rejected:
                return subprocess.CompletedProcess(command, 78, '{"valid":false}', "")
            payload = flags
        elif "from app import app" in command[-1]:
            assert "--entrypoint" in command
            assert "APP_ENV=testing" in command
            assert "DATABASE_DATA_WATERMARK=local_fake_only" in command
            assert "ALLOW_PRODUCTION_SQLITE=1" not in command
            payload = {"status_code": 200, "health": {"service": "safehome-backend"}, "routes": ["/healthz"]}
        else:
            raise AssertionError("unexpected probe")
        return subprocess.CompletedProcess(command, 0, "" if payload is None else json.dumps(payload), "")

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    result = module.verify_runtime_images()
    assert result["valid"] is (not guard_rejected), result["errors"]
    assert ("production: image entrypoint guard failed" in result["errors"]) is guard_rejected
    for profile in ("production", "validation"):
        assert result["images"][profile]["entrypoint_ready"] is (not guard_rejected or profile == "validation")
        assert result["images"][profile]["probe_environment"] == "testing"
    assert len([command for command in calls if "from app import app" in command[-1]]) == 2
