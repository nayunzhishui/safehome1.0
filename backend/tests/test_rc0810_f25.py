import json
import importlib.util
import subprocess
import sys
import copy
import hashlib
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / "scripts" / "verify_rc0810_f25_platform.py"
CONFIG = ROOT / "config" / "rc0810"
REGISTRY = ROOT / "content" / "rc0810_release_candidate_registry.json"
F25B_REPORT = ROOT / "docs" / "02_专项进度与验收" / "rc0810_f25b_evidence.json"
F25B_BUILDER = ROOT / "scripts" / "build_rc0810_f25b_evidence.py"


def run_verifier(*args: str):
    return subprocess.run(
        [sys.executable, str(VERIFIER), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def load_verifier_module():
    spec = importlib.util.spec_from_file_location("verify_rc0810_f25_platform", VERIFIER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_f25b_builder_module():
    spec = importlib.util.spec_from_file_location("build_rc0810_f25b_evidence", F25B_BUILDER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_f25a_source_binding_allows_later_evidence_only_commit(monkeypatch):
    module = load_verifier_module()
    recorded_head = "a" * 40
    recorded_tree = "b" * 40
    source_tree = "c" * 40
    diff_bytes = b"frozen evidence diff"
    baseline = {
        "head": recorded_head,
        "head_tree": recorded_tree,
        "source_tree": source_tree,
        "dirty_diff_sha256": module.sha256_bytes(diff_bytes),
        "source_manifest_sha256": "d" * 64,
    }
    current = {
        "head": "e" * 40,
        "head_tree": "f" * 40,
        "source_tree": source_tree,
        "dirty_diff_sha256": "0" * 64,
        "source_manifest_sha256": "d" * 64,
    }

    def fake_git(*args, **_kwargs):
        if args[:2] == ("merge-base", "--is-ancestor"):
            return b""
        if args[0] == "rev-parse":
            return f"{recorded_tree}\n".encode("ascii")
        if args[0] == "diff-tree":
            return diff_bytes
        raise AssertionError(args)

    monkeypatch.setattr(module, "git", fake_git)
    assert module.source_binding_errors(baseline, current) == []


def test_f25b_backend_context_hash_uses_tree_inventory(monkeypatch):
    module = load_f25b_builder_module()
    included = b"100644 blob deadbeef\tbackend/app.py"
    excluded = b"100644 blob feedface\tbackend/tests/test_app.py"
    inventory = included + b"\0" + excluded + b"\0"
    calls = []

    def fake_git_bytes(*args):
        calls.append(args)
        return inventory

    monkeypatch.setattr(module, "_git_bytes", fake_git_bytes)
    assert module._backend_context_sha256("a" * 40) == hashlib.sha256(included + b"\0").hexdigest()
    assert calls[0][:5] == ("-c", "core.quotepath=false", "ls-tree", "-r", "-z")


def test_package_content_manifest_ignores_zip_container_metadata(tmp_path):
    module = load_f25b_builder_module()
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.js").write_text("console.log('ok');\n", encoding="utf-8")
    (source / "RC0810_F25B_MANIFEST.json").write_text("metadata\n", encoding="utf-8")
    expected = module._content_manifest_sha256(source)

    archives = []
    for index, (system, compression) in enumerate(((0, zipfile.ZIP_DEFLATED), (3, zipfile.ZIP_STORED))):
        path = tmp_path / f"package-{index}.zip"
        with zipfile.ZipFile(path, "w") as archive:
            info = zipfile.ZipInfo("app.js", date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = system
            info.compress_type = compression
            info.external_attr = (0o100644 if index == 0 else 0o100755) << 16
            archive.writestr(info, (source / "app.js").read_bytes())
            archive.writestr(module.PACKAGE_MANIFEST_NAME, b"metadata\n")
        archives.append(path)

    with zipfile.ZipFile(archives[0]) as first, zipfile.ZipFile(archives[1]) as second:
        assert module._archive_content_manifest_sha256(first) == expected
        assert module._archive_content_manifest_sha256(second) == expected

    tampered = tmp_path / "tampered.zip"
    with zipfile.ZipFile(tampered, "w") as archive:
        archive.writestr("app.js", b"console.log('tampered');\n")
        archive.writestr(module.PACKAGE_MANIFEST_NAME, b"metadata\n")
    with zipfile.ZipFile(tampered) as archive:
        assert module._archive_content_manifest_sha256(archive) != expected


def test_registry_evidence_is_portable_but_raw_mode_still_fails_closed(monkeypatch):
    module = load_f25b_builder_module()
    report = json.loads(F25B_REPORT.read_text(encoding="utf-8"))
    commit = report["artifact_source"]["commit"]
    evidence = report["artifact_binding"]["backend_image"]["registry_evidence"]
    assert module.registry_evidence_errors(evidence, commit, require_raw=False) == []
    raw_paths = set(module._registry_evidence_paths(commit).values())
    original_is_file = module.Path.is_file
    monkeypatch.setattr(
        module.Path,
        "is_file",
        lambda path: False if path in raw_paths else original_is_file(path),
    )
    raw_errors = module.registry_evidence_errors(evidence, commit, require_raw=True)
    assert set(raw_errors) >= {
        "registry_file_missing:build_metadata",
        "registry_file_missing:container_scan",
        "registry_file_missing:image_sbom",
    }


def test_f25a_default_definition_is_ready_but_release_stays_no_go():
    completed = run_verifier()
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["valid"] is True
    assert payload["status"] == "definition_ready"
    assert payload["phase"] == "F25-A"
    assert payload["production_gate_eligible"] is False


def test_f25a_catalog_covers_all_fourteen_subtasks_and_schema_is_strict():
    catalog = json.loads((CONFIG / "wechat_platform_catalog.json").read_text(encoding="utf-8"))
    schema = json.loads((CONFIG / "wechat_platform_acceptance.schema.json").read_text(encoding="utf-8"))
    assert catalog["subtasks"] == [f"F25.{index}" for index in range(1, 15)]
    assert schema["additionalProperties"] is False
    assert schema["properties"]["production_gate_eligible"] == {"const": False}


def test_f25a_artifact_binding_is_empty_and_package_change_invalidates_evidence():
    catalog = json.loads((CONFIG / "wechat_platform_catalog.json").read_text(encoding="utf-8"))
    freeze = json.loads((CONFIG / "wechat_platform_review_freeze.json").read_text(encoding="utf-8"))
    binding = catalog["artifact_binding"]
    assert binding["status"] == "pending_external"
    assert all(binding[field] is None for field in (
        "miniprogram_package_sha256", "backend_image_digest", "cloudbase_config_sha256",
        "privacy_text_sha256", "base_library_version",
    ))
    assert set(freeze["invalidation_rules"]["package_or_image"]) >= {"artifact", "device", "journey", "materials", "platform"}


def test_f25a_platform_checklist_covers_appid_category_domains_privacy_and_filing():
    catalog = json.loads((CONFIG / "wechat_platform_catalog.json").read_text(encoding="utf-8"))
    checks = {item["id"]: item for item in catalog["platform_checks"]}
    assert set(checks) == {
        "appid_subject", "service_category", "interface_permissions", "legal_domains",
        "cloudbase_environment", "privacy_guideline", "filing_status", "qualification_materials",
    }
    assert all(item["status"] == "pending_external" for item in checks.values())
    assert all(item["owner"] for item in checks.values())


def test_f25a_account_matrix_includes_legacy_lock_and_multi_device_cases():
    catalog = json.loads((CONFIG / "wechat_platform_catalog.json").read_text(encoding="utf-8"))
    assert catalog["account_scenarios"] == [
        "wechat_one_tap_login", "phone_login", "account_login", "logout",
        "legacy_account", "locked_account", "multi_device_session",
    ]


def test_f25a_message_matrix_covers_denied_expired_duplicate_and_feedback_paths():
    catalog = json.loads((CONFIG / "wechat_platform_catalog.json").read_text(encoding="utf-8"))
    assert set(catalog["message_scenarios"]) == {
        "subscription_denied", "subscription_expired", "subscription_duplicate",
        "training_record", "historical_feedback", "researcher_feedback_message",
    }


def test_f25a_devtools_matrix_requires_compile_package_network_and_warnings():
    catalog = json.loads((CONFIG / "wechat_platform_catalog.json").read_text(encoding="utf-8"))
    assert catalog["devtools_checks"] == [
        "compile", "subpackages", "package_size", "network", "base_library", "page_warnings"
    ]


def test_f25a_device_matrix_has_ios_android_and_eight_lifecycle_scenarios():
    catalog = json.loads((CONFIG / "wechat_platform_catalog.json").read_text(encoding="utf-8"))
    slots = {item["platform"]: item for item in catalog["device_slots"]}
    assert set(slots) == {"ios", "android"}
    expected = {"cold_start", "warm_start", "foreground_background", "weak_network", "offline_recovery", "large_font", "keyboard", "safe_area"}
    assert all(set(item["scenarios"]) == expected for item in slots.values())
    assert all(item["device_id"] is None and item["operator_id"] is None for item in slots.values())


def test_f25a_journeys_cover_core_loop_and_closed_production_surfaces():
    catalog = json.loads((CONFIG / "wechat_platform_catalog.json").read_text(encoding="utf-8"))
    journeys = catalog["journeys"]
    assert journeys["participant_core"] == ["goal", "diary", "feedback", "training", "checkin", "weekly_report", "supervision"]
    assert set(journeys["production_negative"]) == {"internal_route_hidden", "temporary_privilege_disabled", "debug_entry_hidden"}
    assert journeys["status"] == "pending_external"


def test_f25a_review_materials_include_test_account_boundaries_and_recovery():
    catalog = json.loads((CONFIG / "wechat_platform_catalog.json").read_text(encoding="utf-8"))
    assert catalog["review_materials"] == [
        "review_notes", "test_account_guide", "feature_paths", "boundary_statement", "failure_recovery"
    ]


def test_f25a_evidence_contract_binds_owner_reviewer_validity_artifact_and_request():
    catalog = json.loads((CONFIG / "wechat_platform_catalog.json").read_text(encoding="utf-8"))
    contract = catalog["evidence_contract"]
    assert set(contract["required_fields"]) == {
        "owner", "reviewer", "captured_at", "valid_until", "invalidation_conditions", "artifact_sha256", "request_id"
    }
    assert contract["automation_max_state"] == "evidence_ready"
    assert contract["states"][-1] == "stale"


def test_f25a_capability_map_links_page_api_data_and_keeps_missing_platform_claims_blocking():
    mapping = json.loads((CONFIG / "wechat_platform_capability_map.json").read_text(encoding="utf-8"))
    app_pages = json.loads((ROOT / "apps/miniprogram/app.json").read_text(encoding="utf-8"))["pages"]
    inventory = mapping["registered_page_inventory"]
    assert [item["page"] for item in inventory] == app_pages
    assert len({item["page"] for item in inventory}) == len(app_pages) == 53
    assert {item["classification"] for item in inventory} <= set(mapping["allowed_page_classifications"])
    mapped_pages = {
        page
        for item in mapping["capabilities"]
        for page in item["pages"]
    }
    assert {item["page"] for item in inventory if item["classification"] == "public_mapped"} == mapped_pages
    assert all(
        item["classification"] == "public_mapped" or item["classification"].startswith("blocker_")
        for item in inventory
    )
    for item in mapping["capabilities"]:
        assert item["pages"] and item["apis"] and item["data_domains"]
        assert item["service_category"] is None
        assert item["qualification"] is None
        assert item["privacy_declaration"] is None
        assert item["status"] == "blocking_pending_external"
    assert mapping["unmapped_public_capability_policy"] == "block_or_hide_before_review"
    assert mapping["production_gate_eligible"] is False


def test_f25a_zero_context_review_forbids_oral_help_mutation_privilege_and_debugging():
    review = json.loads((CONFIG / "wechat_platform_zero_context_review.json").read_text(encoding="utf-8"))
    assert set(review["allowed_inputs"]) == {"submitted_materials", "test_account", "frozen_release_candidate"}
    assert set(review["forbidden_assistance"]) >= {"oral_supplement", "database_mutation", "temporary_privilege", "live_debugging"}
    assert review["reviewer_id"] is None
    assert review["status"] == "pending_external"
    assert review["automation_may_approve"] is False
    assert review["required_outcomes"] == [
        "login_without_help", "find_core_journey", "understand_non_diagnostic_boundary", "recover_from_failure"
    ]


def test_f25a_review_freeze_covers_contract_accounts_data_artifacts_target_privacy_and_library():
    freeze = json.loads((CONFIG / "wechat_platform_review_freeze.json").read_text(encoding="utf-8"))
    assert set(freeze["frozen_inputs"]) == {
        "backend_contract", "test_accounts", "test_data", "miniprogram_package",
        "backend_image", "cloudbase_target", "privacy_text", "base_library",
    }
    assert freeze["current_snapshot"] is None
    assert set(freeze["invalidation_rules"]) == {
        "package_or_image", "cloudbase_target", "privacy_text", "base_library", "test_account_or_data"
    }
    assert freeze["production_gate_eligible"] is False


def test_f25a_semantics_reject_release_flag_required_outcome_and_invalidation_drift():
    module = load_verifier_module()
    assert set(module.RELEASE_EVIDENCE_RELATIVES) == {
        "docs/02_专项进度与验收/rc0810_f22a_security_baseline.json",
        "docs/02_专项进度与验收/rc0810_f22b_security_gate.json",
        "docs/02_专项进度与验收/rc0810_f25a_platform_baseline.json",
        "docs/02_专项进度与验收/rc0810_f25a_platform_baseline_current.json",
        "docs/02_专项进度与验收/rc0810_f25b_evidence.json",
        "docs/02_专项进度与验收/rc0810_f26_final_rc.json",
        "docs/02_专项进度与验收/rc0810_f26_final_rc.md",
        "docs/02_专项进度与验收/rc0810_required_ci_evidence.json",
        "docs/02_专项进度与验收/rc0810_wave_c_review_packet.json",
        "docs/02_专项进度与验收/rc0810_wave_c_review_decision.json",
    }
    definitions = module.load_definitions()

    release_mutation = copy.deepcopy(definitions)
    release_mutation["capability"]["production_gate_eligible"] = True
    assert "capability_production_gate_must_remain_closed" in module.validate_semantics(release_mutation)

    outcome_mutation = copy.deepcopy(definitions)
    outcome_mutation["zero_context"]["required_outcomes"] = []
    assert "zero_context_required_outcomes_incomplete" in module.validate_semantics(outcome_mutation)

    invalidation_mutation = copy.deepcopy(definitions)
    invalidation_mutation["freeze"]["invalidation_rules"]["cloudbase_target"] = []
    assert "review_freeze_invalidation_targets_incomplete" in module.validate_semantics(invalidation_mutation)


def test_f25a_semantics_reject_duplicate_ids_unknown_states_and_unknown_fields():
    module = load_verifier_module()
    definitions = module.load_definitions()

    duplicate = copy.deepcopy(definitions)
    duplicate["catalog"]["platform_checks"].append(copy.deepcopy(duplicate["catalog"]["platform_checks"][0]))
    assert "platform_check_ids_must_be_unique" in module.validate_semantics(duplicate)

    unknown_state = copy.deepcopy(definitions)
    unknown_state["real_world"]["items"][0]["status"] = "machine_approved"
    assert "real_world_evidence_must_remain_pending" in module.validate_semantics(unknown_state)

    unknown_field = copy.deepcopy(definitions)
    unknown_field["zero_context"]["surprise"] = True
    assert any(error.startswith("zero_context_schema:") for error in module.validate_semantics(unknown_field))


def test_f25a_write_baseline_validates_before_atomic_replace(tmp_path):
    module = load_verifier_module()
    definitions = module.load_definitions()
    definitions["zero_context"]["required_outcomes"] = []
    target = tmp_path / "baseline.json"
    target.write_text('{"sentinel":"last-valid"}\n', encoding="utf-8")
    before = target.read_bytes()
    result = module.write_validated_baseline(target, definitions=definitions)
    assert result["valid"] is False
    assert target.read_bytes() == before


def test_f25a_raci_and_real_world_evidence_remain_unassigned_pending_and_human_only():
    raci = json.loads((CONFIG / "wechat_platform_raci.json").read_text(encoding="utf-8"))
    real_world = json.loads((CONFIG / "wechat_platform_real_world_evidence.json").read_text(encoding="utf-8"))
    assert len(raci["domains"]) == 8
    assert raci["assignments"] == []
    assert raci["automation_may_sign"] is False
    assert {item["id"] for item in real_world["items"]} == {
        "core_funnel", "failure_recovery", "user_understanding_interview", "human_processing_capacity"
    }
    assert all(item["owner"] is None and item["status"] == "pending_external" for item in real_world["items"])
    assert real_world["automation_may_approve"] is False


def test_f25a_self_check_and_registry_freeze_exact_sixteen_file_scope():
    completed = run_verifier("--self-check")
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["self_checks"] == {
        "source_drift_rejected": True,
        "definition_drift_rejected": True,
        "summary_drift_rejected": True,
        "release_flag_drift_rejected": True,
        "required_outcome_drift_rejected": True,
        "invalidation_target_drift_rejected": True,
        "duplicate_matrix_id_rejected": True,
        "unknown_state_rejected": True,
    }
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    unit = next(item for item in registry["execution_units"] if item["id"] == "RC0810-F25-A")
    task = next(item for item in registry["tasks"] if item["id"] == "RC0810-F25")
    assert len(unit["allowed_files"]) == 16
    assert unit["change_budget"]["expected_files"] == 16
    assert unit["subtasks"] == [f"F25.{index}" for index in range(1, 15)]
    assert [item["expected_test_count"] for item in task["acceptance_commands"]] == [23, 30, 1, 1, 1]


def test_f25b_packet_is_valid_but_release_stays_no_go():
    completed = subprocess.run(
        [
            sys.executable,
            str(F25B_BUILDER),
            "--report",
            str(F25B_REPORT),
            "--rebuild-missing",
            "--self-check",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["valid"] is True
    assert result["status"] == "self_check_passed"
    assert result["production_gate_eligible"] is False
    assert all(result["self_checks"].values())


def test_f25b_package_is_bound_and_excludes_internal_surfaces():
    report = json.loads(F25B_REPORT.read_text(encoding="utf-8"))
    package = ROOT / report["artifact_binding"]["miniprogram_package"]["path"]
    if not package.is_file():
        rebuilt = subprocess.run(
            [
                sys.executable,
                str(F25B_BUILDER),
                "--report",
                str(F25B_REPORT),
                "--rebuild-missing",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert rebuilt.returncode == 0, rebuilt.stderr
    with zipfile.ZipFile(package) as archive:
        names = set(archive.namelist())
        assert "project.private.config.json" not in names
        assert "pages/debug/index.js" not in names
        assert "pages/integration-test/index.js" not in names
        assert "pages/researcher-dashboard/index.js" not in names
        assert "pages/therapeutic-assessment-quality/index.js" not in names
        project = json.loads(archive.read("project.config.json"))
        assert project["setting"]["urlCheck"] is True
        assert project["condition"]["miniprogram"]["list"] == []


def test_f25b_external_results_remain_pending_and_blockers_are_complete():
    report = json.loads(F25B_REPORT.read_text(encoding="utf-8"))
    assert report["engineering_status"] == "evidence_ready"
    assert report["external_verification_complete"] is False
    assert report["release_recommendation"] == "NO_GO"
    assert report["artifact_binding"]["backend_image"]["image_digest"] is None
    assert report["artifact_binding"]["backend_image"]["status"] == "pending_external"
    assert {item["id"] for item in report["blockers"]} == {
        "F25-EXT-01", "F25-EXT-02", "F25-EXT-03", "F25-EXT-04",
        "F25-EXT-05", "F25-EXT-06", "F25-EXT-07", "F25-EXT-08",
    }
    assert [item["id"] for item in report["subtasks"]] == [
        f"F25.{number}" for number in range(1, 15)
    ]
    required_metadata = {
        "captured_at", "valid_until", "request_id", "invalidation_conditions"
    }
    for group in (
        report["platform_checks"], report["account_scenarios"],
        report["message_scenarios"], report["devtools"]["checks"],
        report["device_matrix"], report["real_world_evidence"],
    ):
        assert all(required_metadata <= set(item) for item in group)


def test_f25b_rejects_fabricated_device_verification(tmp_path):
    module_spec = importlib.util.spec_from_file_location("build_rc0810_f25b_evidence", F25B_BUILDER)
    module = importlib.util.module_from_spec(module_spec)
    assert module_spec.loader is not None
    module_spec.loader.exec_module(module)
    report = json.loads(F25B_REPORT.read_text(encoding="utf-8"))
    report["device_matrix"][0]["status"] = "human_verified"
    candidate = tmp_path / "fabricated.json"
    candidate.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
    result = module.validate_report(candidate)
    assert result["valid"] is False
    assert "external_evidence_must_remain_pending" in result["errors"]
