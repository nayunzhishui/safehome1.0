import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PRODUCTION = ROOT / "Dockerfile"
VALIDATION = ROOT / "deploy" / "Dockerfile.validation"
POLICY = ROOT / "config" / "rc0810" / "container_profiles.json"
VERIFY = ROOT / "deploy" / "verify_rc0810_f03_images.py"


def test_f03_production_image_is_fail_closed():
    text = PRODUCTION.read_text(encoding="utf-8")
    assert text.splitlines()[0] == (
        "FROM python:3.11-slim@sha256:"
        "1042b61448fef4ba92d16a8c7eb4996d027568ce64792a7877fd88511e0af7c6"
    )
    assert "openssl=3.5.7-1~deb13u2" in text
    assert "pip uninstall --yes setuptools" in text
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
    assert 'runtime_environment = "testing"' in text
    assert '"--entrypoint", "python"' in text
    assert "image entrypoint guard failed" in text
    assert '"ALLOW_PRODUCTION_SQLITE=1"' not in text
    assert "health contract mismatch" in text
