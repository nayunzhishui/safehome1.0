import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "build_rc0810_miniprogram.py"
POLICY = ROOT / "config" / "rc0810" / "miniprogram_page_policy.json"


def run_builder(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_f02_policy_classifies_every_registered_page():
    app = json.loads((ROOT / "apps" / "miniprogram" / "app.json").read_text(encoding="utf-8"))
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    classified = {item["page"] for item in policy["pages"]}

    assert classified == set(app["pages"])
    assert len(classified) == len(app["pages"])


def test_f02_production_manifest_excludes_internal_pages_and_keeps_participant_tabs(tmp_path):
    result = run_builder("--profile", "production", "--output", str(tmp_path))
    assert result.returncode == 0, result.stderr
    manifest = json.loads((tmp_path / "app.json").read_text(encoding="utf-8"))

    assert "pages/integration-test/index" not in manifest["pages"]
    assert "pages/debug/index" not in manifest["pages"]
    assert "pages/researcher-dashboard/index" not in manifest["pages"]
    assert "pages/therapeutic-assessment-quality/index" not in manifest["pages"]
    assert {item["pagePath"] for item in manifest["tabBar"]["list"]} <= set(manifest["pages"])


def test_f02_validation_manifest_keeps_internal_pages_and_has_watermark(tmp_path):
    result = run_builder("--profile", "validation", "--output", str(tmp_path))
    assert result.returncode == 0, result.stderr
    manifest = json.loads((tmp_path / "app.json").read_text(encoding="utf-8"))

    assert "pages/integration-test/index" in manifest["pages"]
    assert "pages/debug/index" in manifest["pages"]
    assert (tmp_path / "rc0810-environment.json").read_text(encoding="utf-8")
    assert json.loads((tmp_path / "rc0810-environment.json").read_text(encoding="utf-8"))["watermark"] == "VALIDATION · 非正式环境"


def test_f02_production_replaces_previous_validation_output(tmp_path):
    validation = run_builder("--profile", "validation", "--output", str(tmp_path), "--copy-source")
    assert validation.returncode == 0, validation.stderr
    assert (tmp_path / "pages" / "integration-test" / "index.js").is_file()

    production = run_builder("--profile", "production", "--output", str(tmp_path), "--copy-source")
    assert production.returncode == 0, production.stderr
    assert not (tmp_path / "pages" / "integration-test" / "index.js").exists()


def test_f02_builder_rejects_repository_directories_without_deleting_them():
    protected = ROOT / "docs"
    marker = protected / "01_当前执行入口" / "0810bug修改计划.md"
    before = marker.read_bytes()

    result = run_builder("--profile", "production", "--output", str(protected), "--copy-source")

    assert result.returncode != 0
    assert "system temp directory" in result.stderr
    assert marker.read_bytes() == before


def test_f02_production_package_contains_no_internal_page_files_or_routes(tmp_path):
    result = run_builder("--profile", "production", "--output", str(tmp_path), "--copy-source")
    assert result.returncode == 0, result.stderr
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    internal = {item["page"] for item in policy["pages"] if item["classification"] != "participant"}
    files = [path for path in tmp_path.rglob("*") if path.is_file()]
    relative = {path.relative_to(tmp_path).as_posix() for path in files}
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in files)

    for page in internal:
        assert not any(name.startswith(f"{page}.") for name in relative)
        assert f"/{page}" not in text
    for method in ["openIntegrationTest", "goResearcher", "openQualityRecord"]:
        assert method not in text


def test_f02_unclassified_page_fails_closed(tmp_path):
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    policy["pages"] = policy["pages"][:-1]
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(policy, ensure_ascii=False), encoding="utf-8")

    result = run_builder("--profile", "production", "--output", str(tmp_path / "out"), "--policy", str(policy_path))
    assert result.returncode != 0
    assert "unclassified" in result.stderr.lower()


def test_f02_participant_journey_pages_remain_reachable(tmp_path):
    result = run_builder("--profile", "production", "--output", str(tmp_path))
    assert result.returncode == 0, result.stderr
    audit = json.loads((tmp_path / "rc0810-package-audit.json").read_text(encoding="utf-8"))

    assert audit["journey_gate_passed"] is True
    assert audit["unreachable_participant_pages"] == []
    assert audit["internal_route_references"] == []
    graph = json.loads((tmp_path / "rc0810-page-reachability.json").read_text(encoding="utf-8"))
    assert set(graph["participant_journey_pages"]) <= set(graph["nodes"])
    assert graph["unresolved_routes"] == []


def test_f02_accessibility_contract_covers_real_engineering_checks():
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    assert policy["accessibility_gate"] == {
        "min_width_px": 320,
        "text_scale_percent": 200,
        "min_touch_target_px": 44,
        "states": ["loading", "empty", "error", "offline"],
        "manual_external": ["wechat_ios", "wechat_android", "screen_reader"],
    }


def test_f02_source_internal_pages_are_preserved():
    for page in [
        "pages/integration-test/index",
        "pages/debug/index",
        "pages/researcher-dashboard/index",
        "pages/therapeutic-assessment-quality/index",
    ]:
        assert (ROOT / "apps" / "miniprogram" / f"{page}.js").is_file()
