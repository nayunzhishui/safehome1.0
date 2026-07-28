import importlib
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
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "a02.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    monkeypatch.setenv("OFFLINE_BENCHMARK_ENABLED", "1")
    monkeypatch.setenv("OFFLINE_EXTERNAL_INGEST_ENABLED", "0")
    monkeypatch.setenv("OFFLINE_PRODUCTION_REPLACEMENT_ALLOWED", "0")
    return importlib.import_module("app").app


def _headers(app):
    specs = [
        ("annotator-a", "researcher"),
        ("annotator-b", "researcher"),
        ("supervisor-a", "supervisor"),
        ("admin-a", "admin"),
    ]
    with app.app_context():
        database = importlib.import_module("database")
        auth_utils = importlib.import_module("routes.auth_utils")
        with database.get_connection() as conn:
            now = database.now_iso()
            for actor_id, role in specs:
                conn.execute(
                    "INSERT INTO users (id, nickname, role, source, status, created_at, updated_at) VALUES (?, ?, ?, 'test', 'active', ?, ?)",
                    (actor_id, actor_id, role, now, now),
                )
            conn.commit()
        return {
            actor_id: {
                "Authorization": f"Bearer {auth_utils.generate_auth_token({'id': actor_id, 'role': role})}"
            }
            for actor_id, role in specs
        }


def _annotation(labels, intensity=2, polarity="affirmed"):
    return {
        "emotion_labels": labels,
        "intensity": intensity,
        "polarity_status": polarity,
        "valence": -0.5,
        "arousal": 0.6,
        "context": "synthetic",
        "reflex_node": "emotion",
        "evidence_excerpt": "",
        "rationale": "按手册中的直接情绪表达进行标注。",
    }


def test_schema_042_adds_adjudication_and_group_split_tables(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            tables = {row["name"] for row in database.list_database_tables(conn)}
            columns = {
                row["name"]
                for row in database.list_database_columns(
                    conn, "offline_benchmark_annotations"
                )
            }
        assert {
            "offline_annotation_adjudications",
            "offline_annotation_group_splits",
        }.issubset(tables)
        assert {
            "emotion_labels_json",
            "intensity",
            "polarity_status",
            "group_hash",
            "data_split",
        }.issubset(columns)
        assert database.CURRENT_SCHEMA_VERSION >= "2026_07_28_042"


def test_governance_exposes_minimum_fields_and_keeps_real_data_closed(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    data = app.test_client().get(
        "/api/research/benchmarks/annotation-governance",
        headers=headers["annotator-a"],
    ).get_json()["data"]
    assert data["active_data_class"] == "synthetic"
    assert data["real_data_gate"]["allowed"] is False
    assert data["deidentification"]["raw_group_key_persisted"] is False
    assert {"wechat_openid", "phone", "email"}.issubset(data["identity_fields_hidden"])


def test_multilabel_annotation_is_blind_and_cross_round_self_duplication_is_blocked(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    payload = _annotation(["calm", "anxiety"])
    first = client.post(
        "/api/research/benchmarks/cases/syn-affect-002/annotations",
        json=payload,
        headers=headers["annotator-a"],
    )
    duplicate_round = client.post(
        "/api/research/benchmarks/cases/syn-affect-002/annotations",
        json={**payload, "blind_round": "round_2"},
        headers=headers["annotator-a"],
    )
    data = first.get_json()["data"]
    assert data["labels"] == ["calm", "anxiety"]
    assert data["peer_annotation_visible"] is False
    assert "group_hash" not in data
    assert duplicate_round.status_code == 409


def test_conflict_requires_independent_adjudicator_and_preserves_originals(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    case_id = "syn-affect-001"
    client.post(
        f"/api/research/benchmarks/cases/{case_id}/annotations",
        json=_annotation(["anxiety"], 2),
        headers=headers["annotator-a"],
    )
    client.post(
        f"/api/research/benchmarks/cases/{case_id}/annotations",
        json=_annotation(["fear"], 4),
        headers=headers["annotator-b"],
    )
    forbidden = client.get(
        "/api/research/benchmarks/adjudication-queue",
        headers=headers["annotator-a"],
    )
    queue = client.get(
        "/api/research/benchmarks/adjudication-queue",
        headers=headers["supervisor-a"],
    ).get_json()["data"]
    assert forbidden.status_code == 403
    assert queue["total"] == 1
    assert queue["items"][0]["annotator_identity_included"] is False
    adjudicated = client.post(
        f"/api/research/benchmarks/cases/{case_id}/adjudications",
        json={
            **_annotation(["anxiety"], 3),
            "rationale": "两份标注均有部分依据，按未来担忧线索裁决。",
            "manual_clause": "标签边界：anxiety",
        },
        headers=headers["supervisor-a"],
    )
    assert adjudicated.status_code == 200
    assert adjudicated.get_json()["data"]["original_annotations_preserved"] is True
    assert client.get(
        "/api/research/benchmarks/adjudication-queue",
        headers=headers["supervisor-a"],
    ).get_json()["data"]["total"] == 0


def test_grouped_split_prevents_same_group_crossing_sets(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    for case_id in ("syn-affect-001", "syn-affect-001"):
        client.post(
            f"/api/research/benchmarks/cases/{case_id}/annotations",
            json=_annotation(["anxiety"]),
            headers=headers["annotator-a"],
        )
    report = client.get(
        "/api/research/benchmarks/split-report",
        headers=headers["supervisor-a"],
    ).get_json()["data"]
    assert report["passed"] is True
    assert report["cross_split_group_leakage"] == []
    assert report["group_key_persisted"] is False
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT data_split FROM offline_benchmark_annotations WHERE case_id = ?",
                ("syn-affect-001",),
            ).fetchall()
    assert len(rows) == 1


def test_agreement_report_includes_distribution_missing_conflicts_and_limitations(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    client.post(
        "/api/research/benchmarks/cases/syn-affect-001/annotations",
        json=_annotation(["anxiety"]),
        headers=headers["annotator-a"],
    )
    client.post(
        "/api/research/benchmarks/cases/syn-affect-001/annotations",
        json=_annotation(["fear"]),
        headers=headers["annotator-b"],
    )
    data = client.get(
        "/api/research/benchmarks/agreement", headers=headers["supervisor-a"]
    ).get_json()["data"]
    assert data["label_distribution"] == {"anxiety": 1, "fear": 1}
    assert data["missing_annotation_slots"] == 478
    assert data["pending_adjudication_cases"] == 1
    assert data["limitations"]
    assert data["human_gold_released"] is False
