import importlib
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
ADMIN_HEADERS = {"X-Admin-Token": "safehome-local-admin-token"}
PRIVATE_TEXT = "这是一段只属于参与者的私密原文"


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(PROJECT_ROOT / "content"))
    return importlib.import_module("app").app


def _participant(client, code, *, consent=True, diaries=()):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code})
    assert response.status_code == 200
    data = response.get_json()["data"]
    headers = {"Authorization": f"Bearer {data['token']}"}
    if consent:
        granted = client.post("/api/consent", headers=headers, json={"consent_type": "anonymous_research", "agreed": True})
        assert granted.status_code in {200, 201}
    for scene, emotion, intensity in diaries:
        saved = client.post(
            "/api/diaries",
            headers=headers,
            json={
                "scene": scene,
                "event_description": PRIVATE_TEXT,
                "parent_emotion": emotion,
                "parent_emotion_intensity": intensity,
                "child_emotion": "委屈" if emotion == "着急" else "",
            },
        )
        assert saved.status_code == 201
    return data["user"]["id"], headers


def _insights(client, window=None):
    url = "/api/research/group-insights" + (f"?window_days={window}" if window is not None else "")
    response = client.get(url, headers=ADMIN_HEADERS)
    assert response.status_code == 200
    return response.get_json()["data"]


def test_group_insights_require_a_research_role(tmp_path, monkeypatch):
    client = _fresh_app(tmp_path, monkeypatch).test_client()
    assert client.get("/api/research/group-insights").status_code == 401
    _, headers = _participant(client, "group-insight-parent")
    assert client.get("/api/research/group-insights", headers=headers).status_code == 403


def test_group_insights_stay_hidden_below_ten_consented_participants(tmp_path, monkeypatch):
    client = _fresh_app(tmp_path, monkeypatch).test_client()
    for index in range(9):
        _participant(client, f"group-small-{index}", diaries=[("亲子沟通", "着急", 6)])
    for index in range(4):
        _participant(client, f"group-no-consent-{index}", consent=False, diaries=[("亲子沟通", "着急", 6)])

    data = _insights(client)
    assert data["availability"] == "suppressed"
    assert data["participant_count"] is None
    assert data["participant_count_band"] == "少于 10 人"
    assert "affect" not in data and "network" not in data
    assert data["window_days"] == 90


def test_group_insights_aggregate_consented_adults_without_raw_text_or_small_cells(tmp_path, monkeypatch):
    client = _fresh_app(tmp_path, monkeypatch).test_client()
    user_ids = []
    for index in range(12):
        user_id, _ = _participant(
            client,
            f"group-insight-{index}",
            diaries=[("亲子沟通", "着急", 7), ("作业拖延", "担心", 4)],
        )
        user_ids.append(user_id)
    # Two people record a rare emotion: below the three-person cell threshold.
    for index in range(2):
        _participant(client, f"group-rare-{index}", diaries=[("睡前", "无奈", 5)])
    # Withdrawn and never-consented people are left out entirely.
    withdrawn_id, headers = _participant(client, "group-withdrawn", diaries=[("亲子沟通", "生气", 9)])
    latest = client.get("/api/consent", headers=headers).get_json()["data"]
    latest_items = latest["items"] if isinstance(latest, dict) else latest
    latest_id = next(item["id"] for item in latest_items if item["consent_type"] == "anonymous_research")
    withdrawn = client.post(
        "/api/consent",
        headers=headers,
        json={"consent_type": "anonymous_research", "agreed": False, "expected_latest_id": latest_id},
    )
    assert withdrawn.status_code in {200, 201}
    _participant(client, "group-no-consent", consent=False, diaries=[("亲子沟通", "生气", 9)] * 3)

    data = _insights(client, window=30)
    text = json.dumps(data, ensure_ascii=False)
    assert data["availability"] == "available"
    assert data["window_days"] == 30
    assert data["participant_count"] == 14
    assert data["usable_record_count"] == 26
    assert PRIVATE_TEXT not in text
    assert all(user_id not in text for user_id in [*user_ids, withdrawn_id])
    assert "生气" not in text and "无奈" not in text
    assert data["raw_text_included"] is False and data["individual_results_included"] is False

    affect = data["affect"]
    emotions = {item["label"]: item for item in affect["emotions"]}
    assert set(emotions) == {"着急", "担心"}
    assert emotions["着急"]["participant_count"] == 12
    assert affect["emotion_hidden"]["hidden_category_count"] == 1
    assert affect["emotion_hidden"]["hidden_record_count"] == 2
    assert {item["key"] for item in affect["intensity_bands"]} == {"low", "middle", "high"}
    assert affect["weekly_trend"]["items"] and affect["weekly_trend"]["items"][0]["participant_count"] == 14
    pair = affect["parent_child"]["pairs"][0]
    assert (pair["parent_emotion"], pair["child_emotion"], pair["participant_count"]) == ("着急", "委屈", 12)

    links = {(item["scene"], item["emotion"]) for item in data["network"]["scene_emotion"]["links"]}
    assert links == {("亲子沟通", "着急"), ("作业拖延", "担心")}
    network = data["network"]["emotion_cooccurrence"]
    assert network["node_count"] == 2 and network["edge_count"] == 1
    assert network["density"] == 1.0
    assert network["strongest_links"] == [{"emotion_a": "担心", "emotion_b": "着急", "participant_count": 12}]
    assert network["individual_metrics"] is False
    assert network["persistence"]["link_count"] == 1


def test_group_insights_fall_back_to_ninety_days_for_unknown_windows(tmp_path, monkeypatch):
    client = _fresh_app(tmp_path, monkeypatch).test_client()
    assert _insights(client, window=7)["window_days"] == 90
    assert _insights(client, window="abc")["window_days"] == 90
    assert _insights(client, window=365)["window_options"] == [30, 90, 180, 365]


def test_growth_overview_shows_emotion_clues_without_taking_a_scale(tmp_path, monkeypatch):
    client = _fresh_app(tmp_path, monkeypatch).test_client()
    _, headers = _participant(
        client,
        "growth-emotion-parent",
        consent=False,
        diaries=[("亲子沟通", "着急", 6)] * 3 + [("作业拖延", "担心", 4)] * 2,
    )
    overview = client.get("/api/growth/overview", headers=headers)
    assert overview.status_code == 200
    insights = overview.get_json()["data"]["emotion_insights"]
    assert insights["availability"] == "available"
    assert insights["other_participant_data_included"] is False
    assert PRIVATE_TEXT not in json.dumps(insights, ensure_ascii=False)
