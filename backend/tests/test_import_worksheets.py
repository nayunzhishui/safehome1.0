import importlib
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_backend(tmp_path):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services.") or name.startswith("scripts."):
            sys.modules.pop(name, None)
    os.environ["DATABASE_PATH"] = str(tmp_path / "safehome-test.sqlite3")
    os.environ["CONTENT_DIR"] = str(PROJECT_ROOT / "content")
    app_module = importlib.import_module("app")
    return app_module.app


def test_import_worksheets_to_db_is_idempotent_and_preserves_core_items(tmp_path):
    _fresh_backend(tmp_path)
    importer = importlib.import_module("scripts.import_worksheets_to_db")
    first = importer.import_worksheets()
    second = importer.import_worksheets()

    assert first["created"] + first["updated"] + first["skipped"] > 0
    assert second["created"] == 0

    from database import get_connection, json_loads

    with get_connection() as conn:
        student = conn.execute("SELECT * FROM assessment_worksheets WHERE id = ?", ("student_profile_v1",)).fetchone()
        prfq = conn.execute("SELECT * FROM assessment_worksheets WHERE id = ?", ("parent_reflective_functioning_prfq",)).fetchone()

    assert student is not None
    assert student["category"] == "学生画像"
    assert prfq is not None
    assert prfq["dimension_score_method"] == "mean"
    questions = json_loads(prfq["questions_json"], [])
    assert len(questions) == 18
    reverse_ids = {item["id"] for item in questions if item.get("reverse_scored")}
    assert {"PRFQ11", "PRFQ18"}.issubset(reverse_ids)
