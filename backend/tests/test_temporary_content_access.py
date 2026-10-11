import importlib
from test_auth_route import _fresh_app, _register

def _client(tmp_path, monkeypatch):
    app = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()
    registered = _register(client, "temporary-content-review", "parent")
    token = registered.get_json()["data"]["token"]
    app.config.update(APP_ENV="production", CONTENT_GOVERNANCE_ENFORCED=True,
                      TEMPORARY_ASSESSMENTS_OPEN=True, TEMPORARY_TRAINING_CARDS_OPEN=True,
                      TEMPORARY_PROGRAMS_OPEN=True)
    return app, client, {"Authorization": "Bearer " + token}

def test_temporary_content_requires_real_login(tmp_path, monkeypatch):
    app, client, headers = _client(tmp_path, monkeypatch)
    for route in ["/api/assessments", "/api/cards", "/api/programs"]:
        assert client.get(route).get_json()["data"]["items"] == []
        assert client.get(route, headers={"X-Admin-Token": "not-auth"}).get_json()["data"]["items"] == []
        assert client.get(route, headers=headers).get_json()["data"]["items"]

def test_switches_are_independent_and_do_not_rewrite_approvals(tmp_path, monkeypatch):
    app, client, headers = _client(tmp_path, monkeypatch)
    for flag, route in [("TEMPORARY_ASSESSMENTS_OPEN", "/api/assessments"),
                        ("TEMPORARY_TRAINING_CARDS_OPEN", "/api/cards"),
                        ("TEMPORARY_PROGRAMS_OPEN", "/api/programs")]:
        app.config[flag] = False
        assert client.get(route, headers=headers).get_json()["data"]["items"] == []
        app.config[flag] = True
    data = client.get("/api/programs", headers=headers).get_json()["data"]
    assert data["availability"]["approved_count"] == 0
    assert data["availability"]["status"] == "temporary_open"
    assert all(x["review_status"] == "pilot_draft" and not x["preview_only"] for x in data["items"])

def test_temporary_off_stops_new_program_submission(tmp_path, monkeypatch):
    app, client, headers = _client(tmp_path, monkeypatch)
    app.config["TEMPORARY_PROGRAMS_OPEN"] = False
    response = client.post("/api/programs/self_compassion_exam_anxiety/entries", headers=headers,
                           json={"session_no": 1, "reflection": "synthetic"})
    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "program_not_approved"

def test_temporary_disclosures_and_legacy_profile_remain_separate(tmp_path, monkeypatch):
    app, client, headers = _client(tmp_path, monkeypatch)
    data = client.get("/api/assessments", headers=headers).get_json()["data"]
    assert "临时开放" in data["boundary_notice"]
    assert "student_profile_v1" not in {x["id"] for x in data["items"]}
    assert all("临时开放" in x["review_note"] for x in data["items"])
    cards = client.get("/api/cards", headers=headers).get_json()["data"]["items"]
    assert all("临时开放" in x["boundary_notice"] for x in cards)


def test_closed_training_blocks_new_writes_but_keeps_history_and_replay(tmp_path, monkeypatch):
    app, client, headers = _client(tmp_path, monkeypatch)
    payload = {"card_id": "emotion_naming", "reflection": "synthetic", "client_submission_id": "before-close"}
    created = client.post("/api/checkins", headers=headers, json=payload)
    assert created.status_code == 201
    app.config["TEMPORARY_TRAINING_CARDS_OPEN"] = False
    replay = client.post("/api/checkins", headers=headers, json=payload)
    assert replay.status_code == 200 and replay.get_json()["data"]["idempotency_replayed"]
    rejected = client.post("/api/checkins", headers=headers, json={**payload, "client_submission_id": "after-close"})
    assert rejected.status_code == 409
    assert rejected.get_json()["error"]["code"] == "card_not_available"
    assert client.get("/api/checkins", headers=headers).get_json()["data"]["total"] == 1
    database = importlib.import_module("database")
    with database.get_connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM core_idempotency_records WHERE idempotency_key = ?", ("after-close",)).fetchone()[0] == 0
    app.config["TEMPORARY_TRAINING_CARDS_OPEN"] = True
    assert client.post("/api/checkins", headers=headers, json={**payload, "client_submission_id": "after-close"}).status_code == 201


def test_temporary_training_does_not_enable_unknown_or_disabled_cards(tmp_path, monkeypatch):
    app, client, headers = _client(tmp_path, monkeypatch)
    service = importlib.import_module("services.card_service")
    monkeypatch.setattr(service, "load_content_json", lambda _: {"cards": [{"id": "disabled", "enabled": False}]})
    for card_id in ["missing", "disabled"]:
        response = client.post("/api/checkins", headers=headers, json={"card_id": card_id})
        assert response.status_code == 409
    assert client.get("/api/checkins", headers=headers).get_json()["data"]["total"] == 0
