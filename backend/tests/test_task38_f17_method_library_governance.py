import importlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
LIBRARY = ROOT / "content" / "therapeutic_assessment_method_library.json"


def _app(tmp_path, monkeypatch):
    sys.path.insert(0, str(BACKEND))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "f17.sqlite3"))
    monkeypatch.setenv("CONTENT_DIR", str(ROOT / "content"))
    return importlib.import_module("app").app


def _seed(app):
    users = {
        "participant-f17": "parent",
        "researcher-f17": "researcher",
        "supervisor-f17": "supervisor",
        "admin-f17": "admin",
    }
    with app.app_context():
        from database import get_connection, now_iso
        from routes.auth_utils import generate_auth_token

        now = now_iso()
        with get_connection() as conn:
            for user_id, role in users.items():
                conn.execute(
                    "INSERT INTO users (id, nickname, role, status, created_at, updated_at) "
                    "VALUES (?, ?, ?, 'active', ?, ?)",
                    (user_id, user_id, role, now, now),
                )
            conn.commit()
        return {
            user_id: {
                "Authorization": f"Bearer {generate_auth_token({'id': user_id, 'role': role})}"
            }
            for user_id, role in users.items()
        }


def test_library_covers_required_artifacts_and_metadata():
    payload = json.loads(LIBRARY.read_text(encoding="utf-8"))
    assert payload["schema"] == "safehome.therapeutic-assessment.method-library.v1"
    assert payload["governance"]["required_independent_disciplines"] == [
        "research",
        "psychology",
        "ethics",
        "content",
    ]
    assert payload["governance"]["automatic_release_allowed"] is False
    artifact_types = {item["artifact_type"] for item in payload["items"]}
    assert {
        "service_level_guidance",
        "assessment_question_rubric",
        "evidence_templates",
        "feedback_checklist",
        "written_letter_framework",
        "applicability_checklist",
        "stop_rules",
        "professional_interview_scaffold",
    } <= artifact_types
    required = {
        "source",
        "source_version",
        "version",
        "applicable_levels",
        "reviewers",
        "review_status",
        "valid_from",
        "expires_at",
        "disabled_scenarios",
        "access_tier",
        "ordinary_recommendation",
        "body",
    }
    assert all(required <= set(item) for item in payload["items"])


def test_ais_fis_are_professional_only_and_absent_from_ordinary_recommendations():
    payload = json.loads(LIBRARY.read_text(encoding="utf-8"))
    controlled = {
        item["id"]: item
        for item in payload["items"]
        if item["id"] in {"ais_professional_scaffold", "fis_professional_scaffold"}
    }
    assert set(controlled) == {"ais_professional_scaffold", "fis_professional_scaffold"}
    assert all(item["access_tier"] == "t3_professional" for item in controlled.values())
    assert all(item["ordinary_recommendation"] is False for item in controlled.values())
    ordinary_files = [
        ROOT / "content" / "assessment_training_map.json",
        ROOT / "content" / "diary_training_map.json",
        ROOT / "content" / "training_cards.json",
        ROOT / "content" / "programs.json",
    ]
    ordinary_text = "\n".join(path.read_text(encoding="utf-8") for path in ordinary_files)
    assert "ais_professional_scaffold" not in ordinary_text
    assert "fis_professional_scaffold" not in ordinary_text


def test_public_catalog_never_exposes_method_bodies(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    response = client.get(
        "/api/therapeutic-assessment/method-library",
        headers=headers["participant-f17"],
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["count"] >= 9
    assert all("body" not in item for item in data["items"])
    assert all("source" not in item for item in data["items"])
    assert data["automatic_release_allowed"] is False


def test_method_detail_requires_formal_role_and_professional_templates_require_supervision(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    headers = _seed(app)
    client = app.test_client()
    participant = client.get(
        "/api/therapeutic-assessment/method-library/assessment_question_rubric",
        headers=headers["participant-f17"],
    )
    assert participant.status_code == 403
    researcher = client.get(
        "/api/therapeutic-assessment/method-library/assessment_question_rubric",
        headers=headers["researcher-f17"],
    )
    assert researcher.status_code == 200
    assert "body" in researcher.get_json()["data"]
    controlled = client.get(
        "/api/therapeutic-assessment/method-library/ais_professional_scaffold",
        headers=headers["researcher-f17"],
    )
    assert controlled.status_code == 403
    supervisor = client.get(
        "/api/therapeutic-assessment/method-library/ais_professional_scaffold",
        headers=headers["supervisor-f17"],
    )
    assert supervisor.status_code == 200
    assert supervisor.get_json()["data"]["ordinary_recommendation"] is False


def test_method_library_is_registered_in_existing_four_discipline_governance(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    _seed(app)
    with app.app_context():
        from services.content_governance_service import (
            CONTENT_TARGETS,
            REQUIRED_DISCIPLINES,
            list_inventory,
        )

        assert CONTENT_TARGETS["therapeutic_method"] == (
            "therapeutic_assessment_method_library.json",
            "items",
            "id",
        )
        assert REQUIRED_DISCIPLINES == ("research", "psychology", "ethics", "content")
        inventory = [
            item
            for item in list_inventory()["items"]
            if item["content_type"] == "therapeutic_method"
        ]
        assert len(inventory) == 9
        assert all(item["governed_version"] is None for item in inventory)


def test_migration_plan_apply_verify_and_rollback(tmp_path):
    database_path = tmp_path / "f17-migration.sqlite3"
    script = BACKEND / "scripts" / "migrate_task38_f17_method_library.py"
    for action in ("plan", "apply", "verify", "rollback"):
        result = subprocess.run(
            [sys.executable, str(script), action, "--database-path", str(database_path)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr


def test_shared_web_and_miniprogram_use_the_same_catalog_contract():
    shared = (ROOT / "shared" / "types" / "api.ts").read_text(encoding="utf-8")
    web_api = (
        ROOT / "apps" / "web" / "src" / "services" / "safehomeApi.ts"
    ).read_text(encoding="utf-8")
    web_page = (
        ROOT / "apps" / "web" / "src" / "pages" / "TherapeuticAssessmentWorkbench.tsx"
    ).read_text(encoding="utf-8")
    mini_api = (
        ROOT / "apps" / "miniprogram" / "services" / "api.js"
    ).read_text(encoding="utf-8")
    mini_page = (
        ROOT / "apps" / "miniprogram" / "pages" / "therapeutic-assessment" / "index.js"
    ).read_text(encoding="utf-8")

    assert "interface TherapeuticAssessmentMethodCatalog" in shared
    assert "/method-library" in web_api
    assert "getTherapeuticAssessmentMethodLibrary" in web_page
    assert "/method-library" in mini_api
    assert "methodCatalog" in mini_page
