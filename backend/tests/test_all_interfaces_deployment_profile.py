from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _env_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def test_cloudbase_all_interface_profile_opens_implemented_surfaces_without_destructive_automation():
    values = _env_values(ROOT / "config" / "production_features.enabled.example.env")
    enabled = {
        "PRODUCTION_FEATURES_UNLOCKED",
        "CONTENT_GOVERNANCE_ENFORCED",
        "CONTENT_GOVERNANCE_PUBLISH_ENABLED",
        "PRIVACY_EXECUTION_ENABLED",
        "PRIVACY_RETENTION_POLICY_APPROVED",
        "PRIVACY_PRODUCTION_EXECUTION_ENABLED",
        "RESEARCH_OPERATIONS_WRITE_ENABLED",
        "THERAPEUTIC_ASSESSMENT_LIFECYCLE_ENABLED",
        "OFFLINE_BENCHMARK_ENABLED",
        "RESEARCH_METHODOLOGY_WORKBENCH_ENABLED",
        "RESEARCH_METHODOLOGY_FORMAL_FREEZE_ALLOWED",
        "RESEARCH_OUTCOME_ANALYSIS_ALLOWED",
        "RESEARCH_ANALYSIS_JOB_EXECUTION_ENABLED",
        "SECURITY_SCAN_EXECUTION_ENABLED",
        "RELIABILITY_WORKBENCH_ENABLED",
        "RELIABILITY_JOB_EXECUTION_ENABLED",
        "RELIABILITY_GRADUAL_RELEASE_ENABLED",
        "RELIABILITY_PRODUCTION_SLO_FROZEN",
        "UX_GOVERNANCE_WORKBENCH_ENABLED",
        "OPERATIONS_GOVERNANCE_WORKBENCH_ENABLED",
        "OPERATIONS_LOCAL_RELEASE_ENABLED",
        "OPERATIONS_PRODUCTION_RELEASE_ENABLED",
        "WECHAT_SUBSCRIBE_SEND_ENABLED",
    }
    assert {name for name in enabled if values.get(name) != "1"} == set()
    assert values["AI_QA_ENABLED"] == "0"
    assert values["AI_QA_SANDBOX_ENABLED"] == "0"
    assert values["AI_QA_REAL_PROVIDER_ENABLED"] == "0"
    assert values["AI_QA_PROVIDER"] == "deepseek"
    assert values["TRUST_CLOUDBASE_IDENTITY_HEADERS"] == "0"
    assert values["OFFLINE_EXTERNAL_INGEST_ENABLED"] == "0"
    assert values["OFFLINE_PRODUCTION_REPLACEMENT_ALLOWED"] == "0"
    assert values["RELIABILITY_FAULT_INJECTION_ENABLED"] == "0"


def test_cloudbase_profile_contains_placeholders_instead_of_external_secrets():
    text = (ROOT / "config" / "production_features.enabled.example.env").read_text(
        encoding="utf-8"
    )
    assert "__FROM_CLOUDBASE_SECRET_STORE__" in text
    assert "DEEPSEEK_API_KEY=sk-" not in text
    assert "WECHAT_SECRET=" in text
    assert "WECHAT_SECRET=__FROM_CLOUDBASE_SECRET_STORE__" in text


def test_cloudbase_dockerfile_defaults_to_fail_closed_runtime_interfaces():
    text = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    for token in (
        "PRODUCTION_FEATURES_UNLOCKED=0",
        "AI_QA_ENABLED=0",
        "AI_QA_SANDBOX_ENABLED=0",
        "AI_QA_REAL_PROVIDER_ENABLED=0",
        "RESEARCH_OPERATIONS_WRITE_ENABLED=0",
        "OPERATIONS_PRODUCTION_RELEASE_ENABLED=0",
    ):
        assert token in text
    assert "RELIABILITY_FAULT_INJECTION_ENABLED=0" in text
    assert "OFFLINE_PRODUCTION_REPLACEMENT_ALLOWED=0" in text
    assert "ADMIN_EXPORT_TOKEN=" not in text
    assert "SECRET_KEY=" not in text
