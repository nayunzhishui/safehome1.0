import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "scripts" / "build_rc0810_miniprogram.py"
POLICY = ROOT / "config" / "rc0810" / "miniprogram_cloud_targets.json"
SOURCE_CONFIG = ROOT / "apps" / "miniprogram" / "services" / "cloudConfig.js"


def run_builder(profile: str, output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(BUILDER),
            "--profile",
            profile,
            "--output",
            str(output),
            "--copy-source",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def run_cloud_config(module: Path, body: str, wx_value: dict | None = None) -> subprocess.CompletedProcess[str]:
    setup = wx_value or {}
    script = f"""
const state = {json.dumps(setup, ensure_ascii=False)};
global.wx = {{
  getExtConfigSync: () => state.extConfig || {{}},
  getStorageSync: (key) => (state.storage || {{}})[key],
  setStorageSync: (key, value) => {{ state.storage = state.storage || {{}}; state.storage[key] = value; }},
  removeStorageSync: (key) => {{ state.removed = state.removed || []; state.removed.push(key); if (state.storage) delete state.storage[key]; }},
}};
const cloud = require({json.dumps(str(module))});
{body}
"""
    return subprocess.run(
        ["node", "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_f04_contract_separates_three_profiles_and_keeps_release_pending():
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    profiles = policy["profiles"]

    assert set(profiles) == {"development", "validation", "production"}
    assert profiles["development"]["runtime_overrides"] is True
    assert profiles["validation"]["runtime_overrides"] is True
    assert profiles["production"]["runtime_overrides"] is False
    assert profiles["production"]["transport"] == "cloud-container"
    assert policy["production_release_approved"] is False


def test_f04_source_development_defaults_to_loopback_not_cloudbase():
    result = run_cloud_config(
        SOURCE_CONFIG,
        "console.log(JSON.stringify(cloud.getCloudConfig()));",
    )
    assert result.returncode == 0, result.stderr
    config = json.loads(result.stdout)
    assert config["profile"] == "development"
    assert config["transport"] == "local-http"
    assert config["localHttpBaseUrl"] == "http://127.0.0.1:5000"
    assert config["cloudEnvId"] == ""


def test_f04_development_accepts_loopback_override_but_rejects_remote_http():
    accepted = run_cloud_config(
        SOURCE_CONFIG,
        "console.log(JSON.stringify(cloud.getCloudConfig()));",
        {"storage": {"safehome_cloud_config": {"transport": "local-http", "localHttpBaseUrl": "http://localhost:5100"}}},
    )
    assert accepted.returncode == 0, accepted.stderr
    assert json.loads(accepted.stdout)["localHttpBaseUrl"] == "http://localhost:5100"

    rejected = run_cloud_config(
        SOURCE_CONFIG,
        "try { cloud.getCloudConfig(); } catch (error) { console.log(JSON.stringify({code:error.code,recoverable:error.recoverable})); }",
        {"storage": {"safehome_cloud_config": {"transport": "local-http", "localHttpBaseUrl": "http://example.com:5000"}}},
    )
    assert rejected.returncode == 0, rejected.stderr
    assert json.loads(rejected.stdout) == {"code": "cloud_config_invalid", "recoverable": True}

    cloud = run_cloud_config(
        SOURCE_CONFIG,
        "console.log(JSON.stringify(cloud.getCloudConfig({transport:'cloud-container',cloudEnvId:'prod-d3gl35otiaa7c8d24',containerService:'flask-gh3l'})));",
    )
    assert cloud.returncode == 0, cloud.stderr
    assert json.loads(cloud.stdout)["transport"] == "cloud-container"


def test_f04_validation_build_uses_explicit_controlled_cloud_target(tmp_path):
    result = run_builder("validation", tmp_path)
    assert result.returncode == 0, result.stderr
    module = tmp_path / "services" / "cloudConfig.js"
    policy = json.loads(POLICY.read_text(encoding="utf-8"))["profiles"]["validation"]
    target = policy["allowed_targets"][0]
    runtime = run_cloud_config(
        module,
        "console.log(JSON.stringify(cloud.getCloudConfig()));",
        {"extConfig": {"safehomeCloud": target}},
    )
    assert runtime.returncode == 0, runtime.stderr
    config = json.loads(runtime.stdout)
    assert config["profile"] == "validation"
    assert config["cloudEnvId"] == target["cloudEnvId"]
    assert config["containerService"] == target["containerService"]


def test_f04_validation_debug_page_can_switch_to_registered_cloud_target(tmp_path):
    result = run_builder("validation", tmp_path)
    assert result.returncode == 0, result.stderr
    script = f"""
let page = null; let saved = null;
global.wx = {{
  getExtConfigSync: () => ({{}}), getStorageSync: () => ({{}}),
  setStorageSync: (key, value) => {{ saved = value; }}, showToast: () => {{}},
}};
global.Page = (value) => {{ page = value; }};
const apiPath = {json.dumps(str(tmp_path / 'services' / 'api.js'))};
require.cache[require.resolve(apiPath)] = {{ exports: {{ createSafeHomeApi: () => ({{ getDebugConfig: () => saved }}) }} }};
require({json.dumps(str(tmp_path / 'pages' / 'debug' / 'index.js'))});
page.setData = () => {{}}; page.refreshApi = () => {{}}; page.useCloudBackend();
console.log(JSON.stringify(saved));
"""
    runtime = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False)
    assert runtime.returncode == 0, runtime.stderr
    saved = json.loads(runtime.stdout)
    assert saved["cloudEnvId"] == "prod-d3gl35otiaa7c8d24"
    assert saved["containerService"] == "flask-gh3l"


def test_f04_validation_rejects_unknown_environment_without_fallback(tmp_path):
    result = run_builder("validation", tmp_path)
    assert result.returncode == 0, result.stderr
    runtime = run_cloud_config(
        tmp_path / "services" / "cloudConfig.js",
        "try { cloud.getCloudConfig(); } catch (error) { console.log(JSON.stringify({code:error.code,message:error.userMessage,recoverable:error.recoverable})); }",
        {"extConfig": {"safehomeCloud": {"transport": "cloud-container", "cloudEnvId": "unknown-env", "containerService": "wrong-service"}}},
    )
    error = json.loads(runtime.stdout)
    assert error["code"] == "cloud_config_invalid"
    assert error["recoverable"] is True
    assert "配置" in error["message"]


def test_f04_production_package_ignores_storage_extconfig_and_call_options(tmp_path):
    result = run_builder("production", tmp_path)
    assert result.returncode == 0, result.stderr
    policy = json.loads(POLICY.read_text(encoding="utf-8"))["profiles"]["production"]
    runtime = run_cloud_config(
        tmp_path / "services" / "cloudConfig.js",
        "console.log(JSON.stringify(cloud.getCloudConfig({transport:'local-http',cloudEnvId:'evil',containerService:'evil'})));",
        {
            "extConfig": {"safehomeCloud": {"cloudEnvId": "evil-ext", "containerService": "evil"}},
            "storage": {"safehome_cloud_config": {"transport": "local-http", "localHttpBaseUrl": "http://127.0.0.1:5000"}},
        },
    )
    assert runtime.returncode == 0, runtime.stderr
    config = json.loads(runtime.stdout)
    assert config["profile"] == "production"
    assert config["cloudEnvId"] == policy["cloudEnvId"]
    assert config["containerService"] == policy["containerService"]
    assert config["transport"] == "cloud-container"


def test_f04_production_package_contains_no_runtime_switch_interface(tmp_path):
    result = run_builder("production", tmp_path)
    assert result.returncode == 0, result.stderr
    text = (tmp_path / "services" / "cloudConfig.js").read_text(encoding="utf-8")

    for forbidden in ["getExtConfigSync", "getStorageSync", "setStorageSync", "local-http", "http://", "saveCloudConfig"]:
        assert forbidden not in text


def test_f04_legacy_migration_only_removes_connection_key(tmp_path):
    result = run_builder("production", tmp_path)
    assert result.returncode == 0, result.stderr
    runtime = run_cloud_config(
        tmp_path / "services" / "cloudConfig.js",
        "cloud.migrateLegacyCloudConfig(); console.log(JSON.stringify(state));",
        {"storage": {"safehome_cloud_config": {"cloudEnvId": "old"}, "auth_token": "keep", "draft_diary": {"text": "keep"}, "task_progress": 3}},
    )
    state = json.loads(runtime.stdout)
    assert state["removed"] == ["safehome_cloud_config"]
    assert state["storage"] == {"auth_token": "keep", "draft_diary": {"text": "keep"}, "task_progress": 3}


def test_f04_cloud_target_audit_binds_package_and_stays_no_go(tmp_path):
    result = run_builder("production", tmp_path)
    assert result.returncode == 0, result.stderr
    audit = json.loads((tmp_path / "rc0810-cloud-target-audit.json").read_text(encoding="utf-8"))

    assert audit["profile"] == "production"
    assert audit["runtime_overrides_present"] is False
    assert audit["target_locked"] is True
    assert audit["production_release_approved"] is False
    assert audit["production_gate_eligible"] is False


def test_f04_app_launch_migrates_connection_key_before_reading_target():
    text = (ROOT / "apps" / "miniprogram" / "app.js").read_text(encoding="utf-8")
    migrate_at = text.index("migrateLegacyCloudConfig()")
    read_at = text.index("getCloudConfig()")

    assert migrate_at < read_at
    assert "cloudConfigError" in text


def test_f04_production_network_failure_is_recoverable_without_target_fallback(tmp_path):
    result = run_builder("production", tmp_path)
    assert result.returncode == 0, result.stderr
    script = f"""
let cloudCalls = 0; let httpCalls = 0;
global.wx = {{
  getStorageSync: () => '', removeStorageSync: () => {{}}, setStorageSync: () => {{}},
  request: () => {{ httpCalls += 1; }},
  cloud: {{ callContainer: (options) => {{ cloudCalls += 1; options.fail({{ errCode: 'DNS_FAIL' }}); }} }},
  getAccountInfoSync: () => ({{ miniProgram: {{ envVersion: 'release' }} }}),
}};
const api = require({json.dumps(str(tmp_path / 'services' / 'api.js'))}).createSafeHomeApi({{defaultUserId:'test-user'}});
api.healthz().catch((error) => console.log(JSON.stringify({{code:error.code,retryable:error.retryable,cloudCalls,httpCalls}})));
"""
    runtime = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False)
    assert runtime.returncode == 0, runtime.stderr
    outcome = json.loads(runtime.stdout.strip().splitlines()[-1])
    assert outcome == {"code": "DNS_FAIL", "retryable": True, "cloudCalls": 1, "httpCalls": 0}
