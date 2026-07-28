import importlib
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
CONTENT = ROOT / "content"
COMMIT = "b" * 40


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
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "a06.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    monkeypatch.setenv("OFFLINE_BENCHMARK_ENABLED", "1")
    return importlib.import_module("app").app


def _headers(app):
    specs = [
        ("admin-a", "admin"),
        ("supervisor-a", "supervisor"),
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


def _model(client, headers):
    return client.post(
        "/api/research/benchmarks/model-versions",
        json={"code_commit": COMMIT},
        headers=headers["admin-a"],
    ).get_json()["data"]


def test_monitor_covers_drift_fairness_missingness_abstention_and_overturn(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    model = _model(client, headers)
    baseline = client.post(
        "/api/research/benchmarks/monitoring/drills",
        json={"scenario": "baseline", "model_version_id": model["id"]},
        headers=headers["supervisor-a"],
    ).get_json()["data"]
    assert baseline["gate_status"] == "green"
    expected = {
        "mean_input_length_delta",
        "label_distribution_jsd",
        "colloquial_style_rate_delta",
        "missing_rate",
        "abstention_rate",
        "maximum_subgroup_error_gap",
        "human_overturn_rate",
        "provider_exception_rate",
    }
    assert expected == set(baseline["metrics"])
    assert baseline["triggers"] == []
    assert "个体心理" in baseline["boundary_notice"]


def test_red_synthetic_drift_and_exception_trigger_full_stop(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    model = _model(client, headers)
    for scenario in ("abstention_spike", "subgroup_error_gap", "provider_exception"):
        response = client.post(
            "/api/research/benchmarks/monitoring/drills",
            json={"scenario": scenario, "model_version_id": model["id"]},
            headers=headers["supervisor-a"],
        )
        data = response.get_json()["data"]
        assert response.status_code == 200
        assert data["gate_status"] == "red_stopped"
        assert data["runtime_control"]["mode"] == "off"
        assert data["triggers"][0]["level"] == "red"


def test_model_threshold_degrade_and_disable_actions_are_versioned(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    model = _model(client, headers)
    actions = [
        (
            "model_rollback",
            {"model_version_id": model["id"], "reason": "恢复已登记模型版本"},
            "shadow",
        ),
        (
            "threshold_rollback",
            {
                "model_version_id": model["id"],
                "threshold_hash": model["threshold_hash"],
                "reason": "恢复已登记阈值版本",
            },
            "shadow",
        ),
        ("readonly_degrade", {"reason": "降级为只读人工复核"}, "readonly_degraded"),
        ("full_disable", {"reason": "完整关闭模型执行"}, "off"),
    ]
    versions = []
    for action, payload, mode in actions:
        response = client.post(
            f"/api/research/benchmarks/runtime-actions/{action}",
            json=payload,
            headers=headers["admin-a"],
        )
        assert response.status_code == 200
        control = response.get_json()["data"]
        assert control["mode"] == mode
        versions.append(control["version"])
    assert versions == sorted(set(versions))
    invalid = client.post(
        "/api/research/benchmarks/runtime-actions/threshold_rollback",
        json={
            "model_version_id": model["id"],
            "threshold_hash": "0" * 64,
            "reason": "不能选择未登记阈值",
        },
        headers=headers["admin-a"],
    )
    assert invalid.status_code == 400
    assert invalid.get_json()["error"]["code"] == "threshold_not_registered"


def test_model_stop_does_not_break_record_feedback_or_training_cards(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    client.post(
        "/api/research/benchmarks/runtime-actions/full_disable",
        json={"reason": "验证核心链路保持独立"},
        headers=headers["admin-a"],
    )
    diary = client.post(
        "/api/diaries",
        headers=headers["participant-a"],
        json={
            "scene": "沟通",
            "event_description": "今天尝试先停一下再沟通",
            "parent_emotion": "担心",
        },
    )
    feedback = client.post(
        "/api/feedback/generate",
        headers=headers["participant-a"],
        json={
            "event_description": "孩子写作业拖延，我有些着急",
            "scene": "作业拖延",
            "parent_emotion": "着急",
            "automatic_thought": "他可能还没有准备好开始",
            "behavior": "先停一下再询问",
        },
    )
    cards = client.get("/api/cards/recommend")
    assert diary.status_code == 201
    assert feedback.status_code == 201
    assert cards.status_code == 200
    assert cards.get_json()["data"]["items"]


def test_monitoring_is_role_restricted_and_never_accepts_real_payload(
    tmp_path, monkeypatch
):
    app = _app(tmp_path, monkeypatch)
    headers = _headers(app)
    client = app.test_client()
    assert (
        client.get(
            "/api/research/benchmarks/monitoring",
            headers=headers["participant-a"],
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/research/benchmarks/monitoring/drills",
            json={"scenario": "baseline"},
            headers=headers["researcher-a"],
        ).status_code
        == 403
    )
