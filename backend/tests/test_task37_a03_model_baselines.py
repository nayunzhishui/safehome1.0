import importlib
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
CONTENT = ROOT / "content"


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
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "a03.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    monkeypatch.setenv("OFFLINE_BENCHMARK_ENABLED", "1")
    monkeypatch.setenv("OFFLINE_EXTERNAL_INGEST_ENABLED", "0")
    monkeypatch.setenv("OFFLINE_PRODUCTION_REPLACEMENT_ALLOWED", "0")
    return importlib.import_module("app").app


def _headers(app):
    with app.app_context():
        database = importlib.import_module("database")
        auth_utils = importlib.import_module("routes.auth_utils")
        with database.get_connection() as conn:
            now = database.now_iso()
            conn.execute(
                "INSERT INTO users (id, nickname, role, source, status, created_at, updated_at) "
                "VALUES ('researcher-a', 'researcher-a', 'researcher', 'test', 'active', ?, ?)",
                (now, now),
            )
            conn.commit()
        return {
            "Authorization": "Bearer "
            + auth_utils.generate_auth_token(
                {"id": "researcher-a", "role": "researcher"}
            )
        }


def test_candidate_registry_is_transparent_and_pretrained_candidate_stays_gated(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    response = app.test_client().get(
        "/api/research/benchmarks/model-candidates", headers=_headers(app)
    )
    data = response.get_json()["data"]
    assert response.status_code == 200
    assert data["random_seed"] == 37
    assert data["split_policy"]["same_group_cross_split_allowed"] is False
    assert [item["kind"] for item in data["candidates"]] == [
        "rule_lexicon",
        "linear_calibrated",
        "chinese_pretrained",
    ]
    pretrained = data["candidates"][2]
    assert pretrained["execution_status"] == "blocked_artifact_and_rights_review"
    assert pretrained["production_eligible"] is False
    assert data["probability_display_policy"] == "not_clinical_confidence"


def test_candidate_comparison_is_reproducible_and_reports_required_metrics(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    first = client.post("/api/research/benchmarks/runs/affect", headers=headers)
    second = client.post("/api/research/benchmarks/runs/affect", headers=headers)
    first_metrics = first.get_json()["data"]["metrics"]
    second_metrics = second.get_json()["data"]["metrics"]
    assert first.status_code == 200
    assert first_metrics["experiment_digest"] == second_metrics["experiment_digest"]
    assert first_metrics["split_counts"]["train"] > 0
    assert first_metrics["split_counts"]["validation"] > 0
    assert first_metrics["split_counts"]["test"] > 0
    assert first_metrics["human_gold_used"] is False
    assert first_metrics["probability_is_clinical_confidence"] is False
    assert first_metrics["production_replacement_allowed"] is False
    evaluated = [
        item for item in first_metrics["candidates"] if item["evaluated"] is True
    ]
    assert len(evaluated) == 2
    for item in evaluated:
        metrics = item["metrics"]
        assert {
            "macro_f1",
            "per_class_recall",
            "rare_cue_recall",
            "expected_calibration_error",
            "coverage_rate",
            "abstention_rate",
        }.issubset(metrics)
        assert metrics["coverage_rate"] + metrics["abstention_rate"] == 1.0
    blocked = [
        item for item in first_metrics["candidates"] if item["evaluated"] is False
    ]
    assert blocked == [
        {
            "candidate_id": "zh_pretrained_candidate_v1",
            "evaluated": False,
            "status": "blocked_artifact_and_rights_review",
            "block_reasons": [
                "model_artifact_not_admitted",
                "license_evidence_not_archived",
            ],
        }
    ]


def test_low_information_and_conflicting_inputs_abstain_for_human_review():
    sys.path.insert(0, str(BACKEND))
    module = importlib.import_module("services.affect_model_benchmark_service")
    registry = json.loads(
        (CONTENT / "affect_model_candidate_registry.json").read_text(encoding="utf-8")
    )
    terms = json.loads(
        (ROOT / "analysis" / "text_analysis" / "dictionaries" / "emotion_terms.json").read_text(
            encoding="utf-8"
        )
    )
    term_map = {}
    for item in terms["terms"]:
        term_map.setdefault(item["category"], []).append(item["word"])
    assert module.triage_text("嗯", term_map, registry)["reason"] == "text_too_short"
    assert (
        module.triage_text("今天讨论了课程安排", term_map, registry)["reason"]
        == "out_of_domain_no_emotion_cue"
    )
    conflict = module.triage_text("我既生气又难过", term_map, registry)
    assert conflict == {
        "label": "unknown",
        "needs_human_review": True,
        "reason": "conflicting_emotion_cues",
    }


def test_synthetic_split_is_group_safe_and_not_collapsed_to_train():
    sys.path.insert(0, str(BACKEND))
    module = importlib.import_module("services.affect_model_benchmark_service")
    payload = json.loads(
        (CONTENT / "synthetic_affect_benchmark_240.json").read_text(encoding="utf-8")
    )
    partitions = [module.synthetic_case_partition(item) for item in payload["cases"]]
    counts = {}
    by_group = {}
    for group_hash, split_name in partitions:
        counts[split_name] = counts.get(split_name, 0) + 1
        by_group.setdefault(group_hash, set()).add(split_name)
    assert set(counts) == {"train", "validation", "test"}
    assert all(len(splits) == 1 for splits in by_group.values())
    assert len(by_group) == 240


def test_split_migration_can_apply_verify_and_restore_snapshot(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    client.post(
        "/api/research/benchmarks/cases/syn-affect-001/annotations",
        json={
            "emotion_labels": ["anxiety"],
            "intensity": 2,
            "polarity_status": "affirmed",
            "valence": -0.5,
            "arousal": 0.6,
            "context": "synthetic",
            "reflex_node": "emotion",
            "rationale": "直接表达了担心。",
        },
        headers=headers,
    )
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            conn.execute(
                "UPDATE offline_benchmark_annotations SET group_hash = 'legacy', data_split = 'train'"
            )
            conn.execute(
                "DELETE FROM offline_annotation_group_splits WHERE dataset_card_id = ?",
                ("safehome_synthetic_affect_240_v1",),
            )
            conn.execute(
                "INSERT INTO offline_annotation_group_splits "
                "(id, dataset_card_id, group_hash, split_name, split_policy_version, created_at) "
                "VALUES ('legacy', ?, 'legacy', 'train', 'group-hash-70-15-15-v1', ?)",
                ("safehome_synthetic_affect_240_v1", database.now_iso()),
            )
            conn.commit()
        migration = importlib.import_module(
            "scripts.migrate_task37_a03_model_baselines"
        )
        snapshot_path = tmp_path / "split-snapshot.json"
        applied = migration.apply(snapshot_path)
        assert applied["ok"] is True
        assert set(applied["split_counts"]) == {"train", "validation", "test"}
        restored = migration.rollback(snapshot_path)
        assert restored["restored_annotation_count"] == 1
        with database.get_connection() as conn:
            row = conn.execute(
                "SELECT group_hash, data_split FROM offline_benchmark_annotations"
            ).fetchone()
        assert (row["group_hash"], row["data_split"]) == ("legacy", "train")
