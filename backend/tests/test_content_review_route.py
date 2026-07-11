import importlib
import json
import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
CONTENT_ROOT = PROJECT_ROOT / "content"
ADMIN_HEADERS = {"X-Admin-Token": "safehome-local-admin-token"}


def _copy_content(target: Path) -> None:
    shutil.copytree(CONTENT_ROOT, target)


def _fresh_app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    content_dir = tmp_path / "content"
    _copy_content(content_dir)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    module = importlib.import_module("app")
    return module.app, content_dir


def test_content_review_update_requires_admin_token(tmp_path, monkeypatch):
    app, _ = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.post(
        "/api/content-review/update",
        json={"content_type": "training_card", "item_id": "emotion_naming", "review_status": "reviewed"},
    )

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "unauthorized"


def test_content_review_update_review_status_writes_local_content(tmp_path, monkeypatch):
    app, content_dir = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.post(
        "/api/content-review/update",
        json={"content_type": "training_card", "item_id": "emotion_naming", "review_status": "reviewed", "enabled_for_user": False},
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    body = response.get_json()["data"]
    assert body["review_status"] == "reviewed"
    assert body["enabled_for_user"] is False

    cards = json.loads((content_dir / "training_cards.json").read_text(encoding="utf-8"))
    card = next(item for item in cards["cards"] if item["id"] == "emotion_naming")
    assert card["review_status"] == "reviewed"
    assert card["enabled"] is False
    assert card["enabled_for_user"] is False


def test_content_review_update_blocks_enable_true_without_manual_confirmation(tmp_path, monkeypatch):
    app, content_dir = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    before = json.loads((content_dir / "scales_catalog.json").read_text(encoding="utf-8"))
    response = client.post(
        "/api/content-review/update",
        json={"content_type": "scale", "item_id": "parent_reflective_functioning_prfq", "enabled_for_user": True},
        headers=ADMIN_HEADERS,
    )
    after = json.loads((content_dir / "scales_catalog.json").read_text(encoding="utf-8"))

    assert response.status_code == 409
    body = response.get_json()
    assert body["error"]["code"] == "manual_confirmation_required"
    assert after == before


def test_program_cannot_be_approved_without_three_signed_reviews(tmp_path, monkeypatch):
    app, _content_dir = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.post(
        "/api/content-review/update",
        json={"content_type": "program", "item_id": "self_compassion_exam_anxiety", "review_status": "pilot_approved"},
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "program_approval_incomplete"


def test_program_cannot_skip_governed_state_transition(tmp_path, monkeypatch):
    app, _content_dir = _fresh_app(tmp_path, monkeypatch)
    client = app.test_client()

    response = client.post(
        "/api/content-review/update",
        json={"content_type": "program", "item_id": "self_compassion_exam_anxiety", "review_status": "completed"},
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "invalid_program_transition"
