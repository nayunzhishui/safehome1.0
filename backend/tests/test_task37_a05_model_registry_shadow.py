import importlib
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
CONTENT = ROOT / "content"
COMMIT = "a" * 40


def _app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    content_dir = tmp_path / "content"
    shutil.copytree(CONTENT, content_dir)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "a05.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    monkeypatch.setenv("OFFLINE_BENCHMARK_ENABLED", "1")
    monkeypatch.setenv("OFFLINE_EXTERNAL_INGEST_ENABLED", "0")
    monkeypatch.setenv("OFFLINE_PRODUCTION_REPLACEMENT_ALLOWED", "0")
    return importlib.import_module("app").app


def _headers(app):
    specs = [
        ("admin-a", "admin"),
        ("researcher-a", "researcher"),
        ("participant-a", "participant"),
    ]
    with app.app_context():
        database = importlib.import_module("database")
        auth_utils = importlib.import_module("routes.auth_utils")
        with database.get_connection() as conn:
            now = database.now_iso()
            for actor_id, role in specs:
                conn.execute(
                    "INSERT INTO users (id, nickname, role, source, status, created_at, updated_at) "
                    "VALUES (?, ?, ?, 'test', 'active', ?, ?)",
                    (actor_id, actor_id, role, now, now),
                )
            conn.commit()
        return {
            actor_id: {
                "Authorization": "Bearer "
                + auth_utils.generate_auth_token({"id": actor_id, "role": role})
            }
            for actor_id, role in specs
        }


def _register(client, headers):
    response = client.post(
        "/api/research/benchmarks/model-versions",
        json={"code_commit": COMMIT},
        headers=headers["admin-a"],
    )
    assert response.status_code == 200
    return response.get_json()["data"]


def test_registration_pins_all_assets_and_is_idempotent(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    first = _register(client, headers)
    second = _register(client, headers)
    assert first["id"] == second["id"]
    assert first["code_commit"] == COMMIT
    assert first["schema_version"] >= "2026_07_28_043"
    assert len(first["lexicon_hash"]) == 64
    assert len(first["threshold_hash"]) == 64
    assert len(first["dataset_hash"]) == 64
    assert len(first["asset_manifest_hash"]) == 64
    assert first["status"] == "registered_shadow_only"


def test_shadow_run_is_read_only_replayable_and_has_review_queue(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    model = _register(client, headers)
    created = client.post(
        "/api/research/benchmarks/shadow-runs",
        json={"model_version_id": model["id"]},
        headers=headers["researcher-a"],
    )
    run = created.get_json()["data"]
    replay = client.post(
        f"/api/research/benchmarks/shadow-runs/{run['id']}/replay",
        json={"model_version_id": model["id"]},
        headers=headers["researcher-a"],
    ).get_json()["data"]
    queue = client.get(
        "/api/research/benchmarks/shadow-review-queue",
        headers=headers["researcher-a"],
    ).get_json()["data"]
    assert created.status_code == 200
    assert run["raw_text_included"] == 0
    assert run["participant_effect_allowed"] == 0
    assert run["sample_count"] > 0
    assert 0 <= run["coverage_rate"] <= 1
    assert run["unknown_count"] == run["review_queue_count"]
    assert replay["id"] != run["id"] and replay["parent_run_id"] == run["id"]
    assert replay["artifact_hash"] != run["artifact_hash"]
    assert queue["raw_text_included"] is False
    assert all(item["case_id"].startswith("syn-affect-") for item in queue["items"])
    assert all("text" not in item for item in queue["items"])


def test_content_or_schema_drift_stops_shadow_execution(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    model = _register(client, headers)
    content_dir = Path(app.config["CONTENT_DIR"])
    registry_path = content_dir / "affect_model_candidate_registry.json"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    payload["abstention_policy"]["minimum_text_length"] += 1
    registry_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    blocked = client.post(
        "/api/research/benchmarks/shadow-runs",
        json={"model_version_id": model["id"]},
        headers=headers["researcher-a"],
    )
    assert blocked.status_code == 409
    assert blocked.get_json()["error"]["code"] == "shadow_asset_drift"
    assert "threshold_hash" in blocked.get_json()["error"]["details"]["drift_fields"]


def test_roles_and_raw_text_scope_are_enforced(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    forbidden_create = client.post(
        "/api/research/benchmarks/model-versions",
        json={"code_commit": COMMIT},
        headers=headers["researcher-a"],
    )
    forbidden_list = client.get(
        "/api/research/benchmarks/model-versions",
        headers=headers["participant-a"],
    )
    invalid_commit = client.post(
        "/api/research/benchmarks/model-versions",
        json={"code_commit": "latest"},
        headers=headers["admin-a"],
    )
    assert forbidden_create.status_code == 403
    assert forbidden_list.status_code == 403
    assert invalid_commit.status_code == 400
    assert invalid_commit.get_json()["error"]["code"] == "code_commit_required"


def test_researcher_interfaces_show_versions_metrics_limits_and_queue_without_participant_entry():
    web = (ROOT / "apps" / "web" / "src" / "pages" / "OfflineBenchmarkWorkbench.tsx").read_text(
        encoding="utf-8"
    )
    mini_js = (
        ROOT / "apps" / "miniprogram" / "pages" / "researcher-dashboard" / "index.js"
    ).read_text(encoding="utf-8")
    mini_view = (
        ROOT / "apps" / "miniprogram" / "pages" / "researcher-dashboard" / "index.wxml"
    ).read_text(encoding="utf-8")
    app_json = json.loads(
        (ROOT / "apps" / "miniprogram" / "app.json").read_text(encoding="utf-8")
    )
    assert "情感模型影子运行" in web
    assert "sample_count" in web and "coverage_rate" in web
    assert "unknown_count" in web and "limitations" in web
    assert "listOfflineModelReviewQueue" in web
    assert "listOfflineModelVersions" in mini_js
    assert "情感模型影子版本" in mini_view
    assert "不显示原文" in mini_view
    assert "pages/researcher-dashboard/index" in app_json["pages"]
    assert not any("affect-shadow" in page for page in app_json["pages"])
