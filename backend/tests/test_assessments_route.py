import importlib
import json
import os
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
# The owner-approved formal release (2026-10-08) only appended this marker to each worksheet's source_version.
RELEASE_SUFFIX = "-release-20261008"


def _review_worksheet(worksheet_id):
    payload = json.loads((PROJECT_ROOT / "content" / "assessment_worksheets.json").read_text(encoding="utf-8"))
    return next(item for item in payload["worksheets"] if item["id"] == worksheet_id)


def _worksheet_importer():
    import importlib.util

    sys.path.insert(0, str(BACKEND_ROOT))
    spec = importlib.util.spec_from_file_location("review_worksheet_import", BACKEND_ROOT / "scripts/import_worksheets_to_db.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("worksheet_id", ["study_engagement_uwes_s_17", "self_compassion_scs_cn"])
def test_worksheet_import_uses_source_scoring_over_stale_metadata(worksheet_id):
    from copy import deepcopy

    importer = _worksheet_importer()
    from routes.assessments import _db_row_to_worksheet
    from services.assessment_execution_service import execute_assessment

    worksheet = deepcopy(_review_worksheet(worksheet_id))
    worksheet["_meta"]["total_score_method"] = "sum"
    worksheet["derived_dimensions"] = []
    worksheet["_meta"]["derived_dimensions"] = [{"key": "OLD"}]
    restored = _db_row_to_worksheet(importer.worksheet_to_row(worksheet, "synthetic"))
    assert restored["_meta"]["total_score_method"] == worksheet["total_score_method"]
    assert restored["_meta"]["derived_dimensions"] == []
    answers = [{"question_id": q["id"], "value": q["options"][0]["value"]} for q in worksheet["questions"]]
    assert execute_assessment(restored, answers).total_score == execute_assessment(worksheet, answers).total_score


def test_worksheet_import_refuses_production_before_any_database_call(monkeypatch):
    importer = _worksheet_importer()
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setattr(importer, "init_db", lambda: pytest.fail("production initialization reached"))
    monkeypatch.setattr(importer, "get_connection", lambda: pytest.fail("production connection reached"))
    with pytest.raises(RuntimeError, match="生产"):
        importer.import_worksheets()


def test_worksheet_import_plan_reads_only_selected_definitions():
    importer = _worksheet_importer()
    worksheet = _review_worksheet("study_engagement_uwes_s_17")
    row = importer.worksheet_to_row(worksheet, "synthetic")
    row["instructions"] = "合成旧说明"

    class DefinitionConnection:
        calls = 0

        def execute(self, sql, params):
            assert sql.strip().startswith("SELECT") and "assessment_worksheets" in sql
            assert params == (worksheet["id"],)
            self.calls += 1
            return self

        def fetchone(self):
            return row

    conn = DefinitionConnection()
    assert importer.plan_worksheet_sync(conn, [worksheet], [worksheet["id"], worksheet["id"]]) == [
        {"id": worksheet["id"], "action": "updated", "changed_fields": ["instructions"]}
    ]
    with pytest.raises(ValueError, match="unknown"):
        importer.plan_worksheet_sync(conn, [worksheet], ["missing"])
    assert conn.calls == 1


def test_worksheet_import_plan_does_not_create_missing_sqlite_file(tmp_path, monkeypatch):
    import sqlite3

    importer = _worksheet_importer()
    missing = tmp_path / "missing-parent" / "definitions.sqlite3"
    monkeypatch.setattr(importer.Config, "DATABASE_PATH", missing)
    monkeypatch.setattr(importer, "is_mysql_enabled", lambda: False)
    monkeypatch.setattr(importer, "load_content_json", lambda filename: {"worksheets": [{"id": "synthetic"}]})
    monkeypatch.setattr(importer, "init_db", lambda: pytest.fail("preview initialized database"))
    monkeypatch.setattr(sys, "argv", ["import_worksheets_to_db.py", "--plan", "--worksheet-id", "synthetic"])
    with pytest.raises(sqlite3.OperationalError):
        importer.main()
    assert not missing.exists()
    assert not missing.parent.exists()


@pytest.mark.parametrize("raw,expected", [(0, 0), (4, 32)])
def test_author_afqy8_coding_order_and_bounds(tmp_path, raw, expected):
    _fresh_app(tmp_path)
    from services.assessment_execution_service import execute_assessment

    worksheet = _review_worksheet("afq_y8_avoidance_fusion")
    assert [q["id"] for q in worksheet["questions"]][-2:] == ["AFQY08", "AFQY07"]
    answers = [{"question_id": q["id"], "value": str(raw)} for q in worksheet["questions"]]
    assert execute_assessment(worksheet, answers).total_score == expected


def test_author_uwes_mean_is_weighted_by_items_and_legacy_snapshot_is_preserved(tmp_path):
    from copy import deepcopy

    _fresh_app(tmp_path)
    from services.assessment_execution_service import execute_assessment

    worksheet = _review_worksheet("study_engagement_uwes_s_17")
    answers = [{"question_id": q["id"], "value": "6" if q["dimension"] == "UWES_VIGOR" else "0"} for q in worksheet["questions"]]
    result = execute_assessment(worksheet, answers)
    assert result.total_score == 2.12  # 6 * 6 / 17; not the unweighted mean of three dimensions.
    assert {d["key"]: d["score"] for d in result.scores["dimensions"]} == {"UWES_VIGOR": 6, "UWES_DEDICATION": 0, "UWES_ABSORPTION": 0}
    assert [q["id"] for q in worksheet["questions"]] == ["UWES06", "UWES11", "UWES13", "UWES02", "UWES09", "UWES12", "UWES08", "UWES01", "UWES17", "UWES10", "UWES16", "UWES04", "UWES07", "UWES14", "UWES05", "UWES15", "UWES03"]
    legacy = deepcopy(worksheet)
    legacy["dimension_score_method"] = "sum"
    legacy["total_score_method"] = "sum"
    for q in legacy["questions"]:
        q["options"] = [{"value": str(i), "score": i, "label": str(i)} for i in range(1, 8)]
    old_answers = [{"question_id": q["id"], "value": "1"} for q in legacy["questions"]]
    assert execute_assessment(legacy, old_answers).total_score == 17


@pytest.mark.parametrize("worksheet_id,expected_count", [("rfq8_reflective_functioning", 6), ("big_five_tipi_10", 2)])
def test_custom_mean_dimensions_report_actual_item_count(tmp_path, worksheet_id, expected_count):
    _fresh_app(tmp_path)
    from services.assessment_execution_service import execute_assessment

    worksheet = _review_worksheet(worksheet_id)
    result = execute_assessment(worksheet, [{"question_id": q["id"], "value": "1"} for q in worksheet["questions"]])
    assert all(d["item_count"] == expected_count for d in result.scores["dimensions"])


@pytest.mark.parametrize("worksheet_id,effective,expected", [
    ("cfi2_cognitive_flexibility", 1, 12),
    ("cfi2_cognitive_flexibility", 6, 72),
    ("emotional_intelligence_eis_33", 1, 33),
    ("emotional_intelligence_eis_33", 5, 165),
])
def test_author_total_scales_use_correct_reverse_bounds(tmp_path, worksheet_id, effective, expected):
    _fresh_app(tmp_path)
    from services.assessment_execution_service import execute_assessment

    worksheet = _review_worksheet(worksheet_id)
    upper = 6 if worksheet_id == "cfi2_cognitive_flexibility" else 5
    answers = [{"question_id": q["id"], "value": str(upper + 1 - effective if q.get("reverse_scored") else effective)} for q in worksheet["questions"]]
    result = execute_assessment(worksheet, answers)
    assert result.total_score == expected
    assert len(result.scores["dimensions"]) == 1
    assert result.scores["dimensions"][0]["score"] == expected
    assert result.scores["dimensions"][0]["item_count"] == len(answers)


@pytest.mark.parametrize("negative_raw,expected", [(5, 1), (1, 5)])
def test_scs_reversed_subscales_explicitly_describe_score_direction(tmp_path, negative_raw, expected):
    _fresh_app(tmp_path)
    from services.assessment_execution_service import execute_assessment

    worksheet = _review_worksheet("self_compassion_scs_cn")
    answers = [
        {"question_id": question["id"], "value": str(negative_raw if question.get("reverse_scored") else expected)}
        for question in worksheet["questions"]
    ]
    result = execute_assessment(worksheet, answers)
    dimensions = {item["key"]: item for item in result.scores["dimensions"]}
    assert dimensions["SCS_SJ"]["label"] == "较少自我批评"
    assert dimensions["SCS_ISO"]["label"] == "较少孤立感"
    assert dimensions["SCS_OVER"]["label"] == "较少被情绪卷入"
    for key in ["SCS_SJ", "SCS_ISO", "SCS_OVER", "SCS_TOTAL"]:
        assert dimensions[key]["score"] == expected
    assert result.total_score is None
    assert all(answer["score"] == negative_raw for answer in result.answers if answer["question_id"] == "SCS01")


def test_review_corrections_survive_rebuilding_from_drafts():
    from backend.scripts.build_worksheets import build_worksheet_from_scale

    drafts = json.loads((PROJECT_ROOT / "content" / "scale_item_drafts.json").read_text(encoding="utf-8"))["drafts"]
    scales = json.loads((PROJECT_ROOT / "content" / "scales_catalog.json").read_text(encoding="utf-8"))["scales"]
    catalog = {item["id"]: item for item in scales}
    aliases = {"emotion_regulation_erq_gross": "emotion_regulation_erq"}
    for scale_id in ["emotion_regulation_erq_gross", "parent_reflective_functioning_prfq", "self_compassion_scs_cn", "mindful_attention_awareness_maas", "acceptance_action_aaq2", "academic_buoyancy_4", "emotional_resilience_11", "emotional_intelligence_eis_33", "cfi2_cognitive_flexibility", "study_engagement_uwes_s_17", "afq_y8_avoidance_fusion"]:
        draft = next(item for item in drafts if item["scale_id"] == scale_id)
        worksheet = _review_worksheet(aliases.get(scale_id, scale_id))
        rebuilt = build_worksheet_from_scale(catalog[scale_id], draft)
        for field in ["instructions", "total_score_method", "dimension_score_method"]:
            assert rebuilt[field] == worksheet[field], (scale_id, field)
        assert rebuilt["source_version"] + RELEASE_SUFFIX == worksheet["source_version"], scale_id
        assert rebuilt["_meta"]["total_score_method"] == worksheet["total_score_method"]
        assert rebuilt["dimensions"] == worksheet["dimensions"]
        assert rebuilt["questions"] == worksheet["questions"]


def test_public_worksheet_regeneration_keeps_time_window_and_ecs_example():
    from backend.scripts.update_task18_assessments import public_worksheets

    for generated in public_worksheets():
        if generated["id"] not in {"who5_wellbeing", "cognitive_curiosity_student"}:
            continue
        current = _review_worksheet(generated["id"])
        assert generated["instructions"] == current["instructions"]
        assert generated["questions"] == current["questions"]
        assert generated["source_version"] + RELEASE_SUFFIX == current["source_version"]


def test_reviewed_guidance_and_eis_typo_reach_assessment_api(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    markers = {
        "who5_wellbeing": "过去两周",
        "cognitive_curiosity_student": "平时",
        "mindful_attention_awareness_maas": "日常体验",
        "acceptance_action_aaq2": "不设固定三个月",
        "academic_buoyancy_4": "最近半年",
        "self_compassion_scs_cn": "通常",
        "emotional_resilience_11": "日常生活",
    }
    for worksheet_id, marker in markers.items():
        response = client.get(f"/api/assessments/{worksheet_id}")
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert marker in data["instructions"], worksheet_id
        assert data["source_version"] == _review_worksheet(worksheet_id)["source_version"]
    eis = client.get("/api/assessments/emotional_intelligence_eis_33").get_json()["data"]
    assert "克服它们的时候" in eis["questions"][1]["prompt"]
    assert "克服它们你" not in eis["questions"][1]["prompt"]


def test_new_erq_policy_preserves_original_snapshot_scoring(tmp_path):
    from copy import deepcopy

    _fresh_app(tmp_path)
    from database import json_dumps
    from services.assessment_execution_service import replay_assessment_snapshot
    from services.psychological_content_governance_service import build_assessment_snapshot, payload_hash

    legacy = deepcopy(_review_worksheet("emotion_regulation_erq"))
    legacy["total_score_method"] = "sum"
    legacy["_meta"]["total_score_method"] = "sum"
    legacy["source_version"] = "test-original-erq-version"
    snapshot = build_assessment_snapshot(legacy, result_summary="历史合成测试")
    answers = [{"question_id": question["id"], "value": "2"} for question in legacy["questions"]]
    replay = replay_assessment_snapshot({
        "content_snapshot_json": json_dumps(snapshot),
        "content_snapshot_hash": payload_hash(snapshot),
        "answers_json": json_dumps(answers),
    })
    assert replay["snapshot_valid"] is True
    assert replay["total_score"] == 20
    assert replay["worksheet_version"] == "test-original-erq-version"


def test_version_conflict_notices_reach_saved_result_summary(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "version-review-synthetic")
    for worksheet_id, marker in [
        ("afq_y8_avoidance_fusion", "本版0—4计分结果不与旧版记录直接比较"),
        ("emotional_resilience_11", "描述“难以恢复”的题目已按反向计分"),
    ]:
        worksheet = _review_worksheet(worksheet_id)
        response = client.post(
            "/api/assessment-results",
            headers={"Authorization": f"Bearer {token}"},
            json={"worksheet_id": worksheet_id, "answers": [
                {"question_id": question["id"], "value": question["options"][0]["value"]}
                for question in worksheet["questions"]
            ]},
        )
        assert response.status_code == 201
        data = response.get_json()["data"]
        assert marker in data["result_summary"]
        assert data["worksheet_version"] == worksheet["source_version"]


def test_all_worksheet_scores_survive_database_metadata_roundtrip(tmp_path, monkeypatch):
    from copy import deepcopy

    app = _fresh_app(tmp_path)
    import database
    from services.assessment_execution_service import execute_assessment

    original = json.loads((PROJECT_ROOT / "content" / "assessment_worksheets.json").read_text(encoding="utf-8"))
    payload = deepcopy(original)
    # Reproduce the stale/missing metadata present in the review baseline.
    for worksheet in payload["worksheets"]:
        if worksheet["id"] in {"mindful_attention_awareness_maas", "attribution_style_student_36", "hplp_c_health_promoting_lifestyle", "student_profile_v1"}:
            worksheet["_meta"] = {"total_score_method": "sum", "derived_dimensions": []}
    original_loader = database.load_content_json
    monkeypatch.setattr(database, "load_content_json", lambda name: payload if name == "assessment_worksheets.json" else original_loader(name))
    with app.app_context():
        with database.get_connection() as conn:
            database.sync_assessment_worksheets(conn)
            conn.commit()
    client = app.test_client()
    for worksheet in original["worksheets"]:
        response = client.get(f"/api/assessments/{worksheet['id']}")
        assert response.status_code == 200
        database_worksheet = response.get_json()["data"]
        answers = [
            {"question_id": question["id"], "value": question["options"][0]["value"] if question.get("options") else "合成观察"}
            for question in worksheet["questions"]
        ]
        file_result = execute_assessment(worksheet, answers)
        database_result = execute_assessment(database_worksheet, answers)
        assert database_result.scores == file_result.scores, worksheet["id"]
        assert database_result.total_score == file_result.total_score, worksheet["id"]


def _fresh_app(tmp_path):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    os.environ["DATABASE_PATH"] = str(tmp_path / "safehome-test.sqlite3")
    os.environ["CONTENT_DIR"] = str(PROJECT_ROOT / "content")
    module = importlib.import_module("app")
    return module.app


def _wechat_login(client, code: str):
    response = client.post("/api/auth/wechat-login", json={"code": code, "nickname": code})
    assert response.status_code == 200
    data = response.get_json()["data"]
    return data["user"]["id"], data["token"]


def _student_profile_answers(value: str = "1", free_text: str | None = None):
    answers = [
        {"question_id": question_id, "value": value}
        for question_id in ["test_anxiety", "iu_score", "fear_score", "self_compassion"]
    ]
    if free_text is not None:
        answers.append({"question_id": "free_text", "value": free_text})
    return answers


def test_legacy_self_built_assessment_is_removed_from_api(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "legacy-self-built")

    detail_response = client.get("/api/assessments/worksheet_3_1_anxiety")
    assert detail_response.status_code == 404

    submit_response = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worksheet_id": "worksheet_3_1_anxiety",
            "answers": [{"question_id": "q1", "prompt": "测试题", "value": "1", "score": 1}],
        },
    )

    assert submit_response.status_code == 404
    body = submit_response.get_json()
    assert body["ok"] is False
    assert body["error"]["code"] == "not_found"

    from database import get_connection

    with get_connection() as conn:
        saved_count = conn.execute(
            "SELECT COUNT(*) FROM assessment_results WHERE worksheet_id = ?",
            ("worksheet_3_1_anxiety",),
        ).fetchone()[0]

    assert saved_count == 0


def test_production_governance_gate_only_opens_approved_scales_and_allows_reviewer_preview(tmp_path):
    app = _fresh_app(tmp_path)
    app.config["CONTENT_GOVERNANCE_ENFORCED"] = True
    client = app.test_client()

    public_before = client.get("/api/assessments")
    assert public_before.status_code == 200
    visible_before = {item["id"] for item in public_before.get_json()["data"]["items"]}
    assert "student_profile_v1" in visible_before
    assert "big_five_bfi_60" in visible_before

    from database import get_connection

    with get_connection() as conn:
        conn.execute(
            "UPDATE assessment_worksheets SET review_status = 'pending_review' WHERE id = ?",
            ("big_five_bfi_60",),
        )
        conn.commit()

    public_after = client.get("/api/assessments")
    visible_ids = {item["id"] for item in public_after.get_json()["data"]["items"]}
    assert "student_profile_v1" in visible_ids
    assert "big_five_bfi_60" not in visible_ids

    hidden_detail = client.get("/api/assessments/big_five_bfi_60")
    assert hidden_detail.status_code == 404

    preview_detail = client.get(
        "/api/assessments/big_five_bfi_60?include_unapproved=true",
        headers={"X-Admin-Token": "safehome-local-admin-token"},
    )
    assert preview_detail.status_code == 200
    assert preview_detail.get_json()["data"]["review_status"] == "pending_review"


def test_production_governance_gate_rejects_submission_to_unapproved_scale(tmp_path):
    app = _fresh_app(tmp_path)
    app.config["CONTENT_GOVERNANCE_ENFORCED"] = True
    client = app.test_client()
    _user_id, token = _wechat_login(client, "governance-submit")

    from database import get_connection

    with get_connection() as conn:
        conn.execute(
            "UPDATE assessment_worksheets SET review_status = 'pending_review' WHERE id = ?",
            ("big_five_bfi_60",),
        )
        conn.commit()

    response = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={"worksheet_id": "big_five_bfi_60", "answers": []},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "assessment_not_enabled"


def test_legacy_assessment_results_are_hidden_from_user_history(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    user_id, token = _wechat_login(client, "history-filter-check")

    active_response = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worksheet_id": "student_profile_v1",
            "answers": _student_profile_answers("2"),
        },
    )
    assert active_response.status_code == 201

    from database import get_connection, json_dumps, now_iso

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO assessment_results (
                id, user_id, worksheet_id, worksheet_title, category,
                answers_json, scores_json, total_score, result_summary, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy_assessment_result",
                user_id,
                "worksheet_3_1_anxiety",
                "工作表3.1：总体焦虑水平及干扰程度量表",
                "量表类",
                json_dumps([]),
                json_dumps({}),
                None,
                "旧版自建工作表记录",
                now_iso(),
            ),
        )
        conn.commit()

    list_response = client.get(
        f"/api/assessment-results?user_id={user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 200
    items = list_response.get_json()["data"]["items"]
    assert [item["worksheet_id"] for item in items] == ["student_profile_v1"]


def test_enabled_student_profile_assessment_result_still_saves(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "student-enabled-check")

    response = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worksheet_id": "student_profile_v1",
            "answers": _student_profile_answers("3"),
        },
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["worksheet_id"] == "student_profile_v1"
    assert data["total_score"] is None
    assert {item["key"]: item["score"] for item in data["scores"]["dimensions"]} == {
        "test_anxiety": 3,
        "uncertainty_intolerance": 3,
        "pressure_alert": 3,
        "self_support": 3,
    }


def test_assessment_submission_rejects_unknown_question_id(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "assessment-unknown-question")

    response = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worksheet_id": "student_profile_v1",
            "answers": [{"question_id": "unknown", "value": "1", "score": 1}],
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "unknown_question_id"


def test_assessment_submission_rejects_duplicate_question_id(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "assessment-duplicate-question")
    answer = {"question_id": "test_anxiety", "value": "2"}

    response = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={"worksheet_id": "student_profile_v1", "answers": [answer, answer]},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "duplicate_question_id"


def test_assessment_submission_rejects_value_outside_question_options(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "assessment-invalid-option")

    response = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worksheet_id": "student_profile_v1",
            "answers": [{"question_id": "test_anxiety", "value": "99"}],
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_option_value"


def test_assessment_submission_rejects_missing_required_questions(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "assessment-missing-required")

    response = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worksheet_id": "emotion_regulation_erq",
            "answers": [{"question_id": "ERQ01", "value": "4"}],
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "missing_required_answers"


def test_assessment_submission_ignores_client_score_and_recalculates_from_options(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "assessment-server-score")
    answers = [
        {"question_id": f"ERQ{i:02d}", "value": "4", "score": 99}
        for i in range(1, 11)
    ]

    response = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={"worksheet_id": "emotion_regulation_erq", "answers": answers},
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["total_score"] is None
    dimensions = {item["key"]: item["score"] for item in data["scores"]["dimensions"]}
    assert dimensions == {"ERQ_CR": 24, "ERQ_ES": 16}
    assert {answer["score"] for answer in data["answers"]} == {4}


def test_assessment_detail_includes_training_recommendation_rules(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    response = client.get("/api/assessments/student_profile_v1")

    assert response.status_code == 200
    data = response.get_json()["data"]
    rules = data["training_recommendation_rules"]
    assert len(rules) == 1
    assert rules[0]["rule_id"] == "student_profile_pressure_alert_basic_support"
    assert len(rules[0]["recommended_card_ids"]) <= 3


def test_erq_appears_in_assessment_list(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    response = client.get("/api/assessments")
    assert response.status_code == 200
    items = response.get_json()["data"]["items"]
    ids = [item["id"] for item in items]
    assert "emotion_regulation_erq" in ids


def test_confirmed_pilot_expansion_appears_and_accepts_submission(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "pilot-expansion-check")
    pilot_ids = {
        "acceptance_action_aaq2",
        "academic_buoyancy_4",
        "afq_y8_avoidance_fusion",
        "cfi2_cognitive_flexibility",
    }

    list_response = client.get("/api/assessments")
    assert list_response.status_code == 200
    visible_ids = {item["id"] for item in list_response.get_json()["data"]["items"]}
    assert pilot_ids.issubset(visible_ids)
    assert "fmi_12_mindfulness" in visible_ids
    assert "swls_life_satisfaction" in visible_ids

    for worksheet_id in pilot_ids:
        detail_response = client.get(f"/api/assessments/{worksheet_id}")
        assert detail_response.status_code == 200
        worksheet = detail_response.get_json()["data"]
        assert worksheet["enabled_for_user"] is True
        assert worksheet["review_status"] == "production_approved"
        answers = [
            {
                "question_id": question["id"],
                "prompt": question["prompt"],
                "value": question["options"][0]["value"],
                "score": question["options"][0]["score"],
            }
            for question in worksheet["questions"]
        ]
        submit_response = client.post(
            "/api/assessment-results",
            headers={"Authorization": f"Bearer {token}"},
            json={"worksheet_id": worksheet_id, "answers": answers},
        )
        assert submit_response.status_code == 201


def test_erq_detail_exposes_dimensions(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    response = client.get("/api/assessments/emotion_regulation_erq")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["enabled_for_user"] is True
    assert len(data["questions"]) == 10
    dimension_codes = {dimension["code"] for dimension in data["dimensions"]}
    assert dimension_codes == {"ERQ_CR", "ERQ_ES"}


def test_erq_submission_scores_each_dimension_separately(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "erq-dimension-check")

    # 认知重评 6 题各填 5 分，表达抑制 4 题各填 2 分
    cr_items = ["ERQ01", "ERQ03", "ERQ05", "ERQ07", "ERQ08", "ERQ10"]
    es_items = ["ERQ02", "ERQ04", "ERQ06", "ERQ09"]
    answers = [
        {"question_id": item, "prompt": item, "value": "5", "score": 5} for item in cr_items
    ] + [
        {"question_id": item, "prompt": item, "value": "2", "score": 2} for item in es_items
    ]

    response = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worksheet_id": "emotion_regulation_erq",
            "answers": answers,
        },
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["total_score"] is None
    assert data["scores"]["total_score"] is None
    dimensions = {item["key"]: item for item in data["scores"]["dimensions"]}
    assert dimensions["ERQ_CR"]["score"] == 30
    assert dimensions["ERQ_CR"]["item_count"] == 6
    assert dimensions["ERQ_ES"]["score"] == 8
    assert dimensions["ERQ_ES"]["item_count"] == 4


def test_prfq_appears_in_assessment_list(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    response = client.get("/api/assessments")
    assert response.status_code == 200
    ids = [item["id"] for item in response.get_json()["data"]["items"]]
    assert "parent_reflective_functioning_prfq" in ids


def test_prfq_submission_uses_reverse_scoring_and_dimension_mean(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "prfq-reverse-check")

    # 全部 18 题都填 6 分。PRFQ11、PRFQ18 为反向题（7 点量表翻转为 8-6=2）。
    all_items = [f"PRFQ{i:02d}" for i in range(1, 19)]
    answers = [
        {"question_id": item, "prompt": item, "value": "6", "score": 6} for item in all_items
    ]

    response = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worksheet_id": "parent_reflective_functioning_prfq",
            "answers": answers,
        },
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    dimensions = {item["key"]: item for item in data["scores"]["dimensions"]}

    # 均值计分
    assert data["total_score"] is None
    assert data["scores"]["total_score"] is None
    assert dimensions["PRFQ_PM"]["score_method"] == "mean"
    # PM 无反向题：6 题均为 6 分，均值 6.0
    assert dimensions["PRFQ_PM"]["score"] == 6.0
    # CM 含反向题 PRFQ11（8-6=2）：(6*5 + 2)/6 = 5.33
    assert dimensions["PRFQ_CM"]["score"] == 5.33
    # IC 含反向题 PRFQ18（8-6=2）：(6*5 + 2)/6 = 5.33
    assert dimensions["PRFQ_IC"]["score"] == 5.33

    # answer 里仍保留用户实际选择的原始分（审计用），未被反向值覆盖
    saved_answers = {item["question_id"]: item for item in data["answers"]}
    assert saved_answers["PRFQ11"]["score"] == 6
    assert saved_answers["PRFQ18"]["score"] == 6


def test_declarative_relationship_scoring_supports_products_and_no_total(tmp_path):
    _fresh_app(tmp_path)
    from services.assessment_execution_service import execute_assessment

    options = [{"value": str(value), "score": value} for value in range(1, 6)]
    worksheet = {
        "dimension_score_method": "mean",
        "total_score_method": "none",
        "questions": [
            {"id": item_id, "dimension": dimension, "options": options}
            for item_id, dimension in [
                ("a1", "BENEFIT"),
                ("b1", "BENEFIT"),
                ("a2", "BENEFIT"),
                ("b2", "BENEFIT"),
                ("a4", "REJ_THREAT"),
                ("b4", "REJ_THREAT"),
                ("a5", "AUTH_PROTECT"),
                ("b5", "AUTH_PROTECT"),
            ]
        ],
        "dimensions": [
            {
                "code": "BENEFIT",
                "label": "获益信念",
                "calculation": {
                    "type": "mean_of_products",
                    "pairs": [["a1", "b1"], ["a2", "b2"]],
                },
            },
            {
                "code": "REJ_THREAT",
                "label": "拒绝威胁",
                "calculation": {"type": "product", "items": ["a4", "b4"]},
            },
            {
                "code": "AUTH_PROTECT",
                "label": "权威保护",
                "calculation": {
                    "type": "mean_terms",
                    "terms": [
                        {"item": "a5", "reverse_min": 1, "reverse_max": 5},
                        {"item": "b5"},
                    ],
                },
            },
        ],
        "derived_dimensions": [
            {
                "code": "THREAT",
                "label": "威胁信念",
                "calculation": {"type": "mean_dimensions", "dimensions": ["REJ_THREAT"]},
            }
        ],
    }
    raw = {"a1": 2, "b1": 3, "a2": 4, "b2": 5, "a4": 3, "b4": 4, "a5": 2, "b5": 5}
    answers = [{"question_id": key, "value": str(value)} for key, value in raw.items()]

    execution = execute_assessment(worksheet, answers)
    scores, total = execution.scores, execution.total_score

    dimensions = {item["key"]: item for item in scores["dimensions"]}
    assert dimensions["BENEFIT"]["score"] == 13
    assert dimensions["REJ_THREAT"]["score"] == 12
    assert dimensions["AUTH_PROTECT"]["score"] == 4.5
    assert dimensions["THREAT"]["score"] == 12
    assert scores["total_score"] is None
    assert total is None


@pytest.mark.parametrize(
    ("worksheet_id", "question_count"),
    [
        ("regulatory_focus_relationship_18", 18),
        ("micro_ysq_relationship_18", 18),
        ("relationship_initiation_intention_action", 31),
    ],
)
def test_task12_relationship_assessments_are_available_and_save(tmp_path, worksheet_id, question_count):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    from database import get_connection

    with get_connection() as conn:
        conn.execute(
            "UPDATE assessment_worksheets SET enabled_for_user = 1, review_status = 'pilot_approved' WHERE id = ?",
            (worksheet_id,),
        )
        conn.commit()
    _user_id, token = _wechat_login(client, f"task12-{worksheet_id}")

    detail = client.get(f"/api/assessments/{worksheet_id}")
    assert detail.status_code == 200
    worksheet = detail.get_json()["data"]
    assert len(worksheet["questions"]) == question_count
    assert "不构成诊断" in worksheet["result_disclaimer"]
    if worksheet_id == "regulatory_focus_relationship_18":
        assert [option["score"] for option in worksheet["questions"][0]["options"]] == list(range(1, 10))

    answers = [
        {
            "question_id": question["id"],
            "prompt": question["prompt"],
            "value": question["options"][0]["value"],
        }
        for question in worksheet["questions"]
    ]
    saved = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={"worksheet_id": worksheet_id, "answers": answers},
    )

    assert saved.status_code == 201
    data = saved.get_json()["data"]
    assert data["worksheet_id"] == worksheet_id
    assert data["total_score"] is None
    assert data["scores"]["dimensions"]


def test_profile_feature_can_transform_worksheet_range_to_training_range(tmp_path):
    _fresh_app(tmp_path)
    from services.assessment_profile_service import _feature_value

    feature = {
        "feature_id": "Q1",
        "worksheet_question_id": "Q1",
        "input_transform": {
            "type": "linear_range",
            "input_min": 1,
            "input_max": 9,
            "output_min": 1,
            "output_max": 5,
        },
    }
    answers = {"Q1": {"question_id": "Q1", "value": "9", "score": 9}}
    questions = {"Q1": {"id": "Q1", "options": [{"value": str(i), "score": i} for i in range(1, 10)]}}

    value, missing = _feature_value(feature, answers, questions)

    assert missing is False
    assert value == 5

    middle, missing = _feature_value(feature, {"Q1": {"question_id": "Q1", "value": "5", "score": 5}}, questions)
    assert missing is False
    assert middle == 3


def test_task12_three_scales_return_aggregate_profile_positions(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    from database import get_connection

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE assessment_worksheets
            SET enabled_for_user = 1, review_status = 'pilot_approved'
            WHERE id IN (?, ?, ?)
            """,
            (
                "regulatory_focus_relationship_18",
                "micro_ysq_relationship_18",
                "relationship_initiation_intention_action",
            ),
        )
        conn.commit()
    user_id, token = _wechat_login(client, "task12-profile-chain")

    for worksheet_id in [
        "regulatory_focus_relationship_18",
        "micro_ysq_relationship_18",
        "relationship_initiation_intention_action",
    ]:
        detail = client.get(f"/api/assessments/{worksheet_id}").get_json()["data"]
        answers = []
        for question in detail["questions"]:
            option = question["options"][len(question["options"]) // 2]
            answers.append({"question_id": question["id"], "prompt": question["prompt"], "value": option["value"]})
        saved = client.post(
            "/api/assessment-results",
            headers={"Authorization": f"Bearer {token}"},
            json={"worksheet_id": worksheet_id, "answers": answers},
        )
        assert saved.status_code == 201
        result_id = saved.get_json()["data"]["id"]

        response = client.get(
            f"/api/assessment-results/{result_id}/profile-position?user_id={user_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["available"] is True
        assert data["model_id"].startswith("task12_")
        assert data["feature_summary"]["data_quality"] == "complete"
        assert data["radar_support"]["dimensions"]
        assert data["suggested_assessment_questions"]
        assert "training_points" not in json.dumps(data, ensure_ascii=False)


def test_assessment_list_filters_by_audience_and_search(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    student_response = client.get("/api/assessments?audience_class=student")
    assert student_response.status_code == 200
    student_ids = [item["id"] for item in student_response.get_json()["data"]["items"]]
    assert "student_profile_v1" in student_ids
    assert "emotional_resilience_11" in student_ids
    assert "study_engagement_uwes_s_17" in student_ids
    assert "self_compassion_scs_cn" not in student_ids

    search_response = client.get("/api/assessments?q=%E8%87%AA%E6%88%91%E5%85%B3%E6%80%80")
    assert search_response.status_code == 200
    search_ids = [item["id"] for item in search_response.get_json()["data"]["items"]]
    assert search_ids == ["self_compassion_scs_cn"]


def test_assessment_text_answer_high_risk_creates_review_and_blocks_cards(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    user_id, token = _wechat_login(client, "assessment-risk-check")

    response = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worksheet_id": "student_profile_v1",
            "answers": _student_profile_answers(free_text="我最近不想活"),
        },
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["scores"]["risk"]["risk_level"] == "high"
    assert data["recommended_card_ids"] == []
    assert data["risk"]["requires_review"] is True

    from database import get_connection

    with get_connection() as conn:
        saved_count = conn.execute(
            "SELECT COUNT(*) FROM risk_review_records WHERE user_id = ? AND source_type = ?",
            (user_id, "assessment_result"),
        ).fetchone()[0]

    assert saved_count == 1


def test_assessment_profile_position_returns_cluster_for_modeled_scale(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    user_id, token = _wechat_login(client, "profile-position-check")

    answers = [
        {"question_id": f"ERES{i:02d}", "prompt": f"ERES{i:02d}", "value": "4", "score": 4}
        for i in range(1, 12)
    ]
    submit_response = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worksheet_id": "emotional_resilience_11",
            "answers": answers,
        },
    )
    assert submit_response.status_code == 201
    result_id = submit_response.get_json()["data"]["id"]

    response = client.get(
        f"/api/assessment-results/{result_id}/profile-position?user_id={user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["available"] is True
    assert data["worksheet_id"] == "emotional_resilience_11"
    assert data["position"]["profile_name"] is None
    assert data["position"]["pc1"] is not None
    assert data["feature_summary"]["answered_features"] == 11
    assert len(data["feature_profile"]) == 11
    assert data["feature_profile"][0]["z_score"] is not None
    assert "不构成诊断" in data["boundary_notice"]
    assert data["interpretation"]["status"] in {"usable", "low_confidence", "outlier"}
    assert data["position"]["can_use_interpretation"] is False
    assert data["suggested_assessment_questions"] == []
    assert data["recommended_project_tasks"] == []
    assert "不做明确画像" in data["explanation"]

    from database import get_connection

    with get_connection() as conn:
        row = conn.execute(
            "SELECT profile_model_id, profile_cluster_id, profile_pc1, profile_pc2, profile_confidence FROM assessment_results WHERE id = ?",
            (result_id,),
        ).fetchone()
    assert row["profile_model_id"]
    assert row["profile_cluster_id"] != ""
    assert row["profile_pc1"] is not None
    assert row["profile_pc2"] is not None
    assert row["profile_confidence"] is not None


def test_modeled_assessment_rejects_out_of_range_values_before_profile_position(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    user_id, token = _wechat_login(client, "profile-position-outlier")

    answers = [
        {"question_id": f"ERES{i:02d}", "prompt": f"ERES{i:02d}", "value": "99", "score": 99}
        for i in range(1, 12)
    ]
    submit_response = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worksheet_id": "emotional_resilience_11",
            "answers": answers,
        },
    )
    assert submit_response.status_code == 400
    assert submit_response.get_json()["error"]["code"] == "invalid_option_value"


def test_assessment_profile_position_is_optional_for_unmodeled_scale(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    user_id, token = _wechat_login(client, "profile-position-unavailable")

    answers = [
        {"question_id": f"ERQ{i:02d}", "value": "4"}
        for i in range(1, 11)
    ]
    submit_response = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worksheet_id": "emotion_regulation_erq",
            "answers": answers,
        },
    )
    assert submit_response.status_code == 201
    result_id = submit_response.get_json()["data"]["id"]

    response = client.get(
        f"/api/assessment-results/{result_id}/profile-position?user_id={user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["available"] is False
    assert "暂未接入" in data["reason"]


def test_participant_can_read_own_structured_affect_and_interaction_analysis(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "participant-exploratory-analysis")

    answers = [{"question_id": f"ERQ{i:02d}", "value": "4"} for i in range(1, 11)]
    saved_result = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={"worksheet_id": "emotion_regulation_erq", "answers": answers},
    )
    assert saved_result.status_code == 201
    result_id = saved_result.get_json()["data"]["id"]

    records = [
        ("亲子沟通", "着急", 7),
        ("亲子沟通", "着急", 5),
        ("作业拖延", "担心", 6),
        ("作业拖延", "担心", 4),
        ("亲子沟通", "担心", 3),
    ]
    for index, (scene, emotion, intensity) in enumerate(records):
        saved_diary = client.post(
            "/api/diaries",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "scene": scene,
                "event_description": f"PRIVATE_DIARY_TEXT_{index}",
                "parent_emotion": emotion,
                "parent_emotion_intensity": intensity,
                "raw_text": f"PRIVATE_RAW_TEXT_{index}",
            },
        )
        assert saved_diary.status_code == 201

    response = client.get(
        f"/api/assessment-results/{result_id}/exploratory-analysis",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["availability"] == "available"
    assert data["record_count"] == 5
    assert data["affect"]["items"][0]["label"] == "担心"
    assert data["affect"]["record_count"] == 5
    assert data["affect"]["category_count"] == 2
    assert data["affect"]["overall_average_intensity"] == 5.0
    assert data["affect"]["intensity_range"] == {"minimum": 3, "maximum": 7}
    assert data["affect"]["most_frequent_labels"] == ["担心"]
    assert "5 条记录" in data["affect"]["summary_text"]
    assert data["interaction_network"]["edges"][0]["support"] == 2
    network_summary = data["interaction_network"]["summary"]
    assert network_summary["node_count"] == 4
    assert network_summary["edge_count"] == 2
    assert network_summary["supported_record_count"] == 4
    assert network_summary["record_coverage_rate"] == 0.8
    assert network_summary["suppressed_pair_count"] == 1
    assert "4/5" in network_summary["summary_text"]
    assert data["raw_text_included"] is False
    assert data["other_participant_data_included"] is False
    assert "PRIVATE_" not in json.dumps(data, ensure_ascii=False)


def test_participant_analysis_waits_for_minimum_record_count(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "participant-analysis-minimum")
    saved_result = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worksheet_id": "emotion_regulation_erq",
            "answers": [{"question_id": f"ERQ{i:02d}", "value": "4"} for i in range(1, 11)],
        },
    )
    assert saved_result.status_code == 201
    result_id = saved_result.get_json()["data"]["id"]
    for index in range(4):
        response = client.post(
            "/api/diaries",
            headers={"Authorization": f"Bearer {token}"},
            json={"scene": "亲子沟通", "event_description": f"记录{index}", "parent_emotion": "担心"},
        )
        assert response.status_code == 201

    response = client.get(
        f"/api/assessment-results/{result_id}/exploratory-analysis",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["availability"] == "insufficient"
    assert data["record_count"] == 4
    assert data["affect"]["items"] == []
    assert data["interaction_network"]["edges"] == []


def test_participant_analysis_requires_five_usable_structured_records(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    user_id, token = _wechat_login(client, "participant-analysis-usable-minimum")
    saved_result = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worksheet_id": "emotion_regulation_erq",
            "answers": [{"question_id": f"ERQ{i:02d}", "value": "4"} for i in range(1, 11)],
        },
    )
    result_id = saved_result.get_json()["data"]["id"]
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            now = database.now_iso()
            for index in range(5):
                conn.execute(
                    """
                    INSERT INTO emotion_diaries
                    (id, user_id, scene, event_description, parent_emotion,
                     parent_emotion_intensity, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, 5, ?, ?)
                    """,
                    (f"legacy-empty-{index}", user_id, "", "历史记录", "", now, now),
                )
            conn.commit()

    response = client.get(
        f"/api/assessment-results/{result_id}/exploratory-analysis",
        headers={"Authorization": f"Bearer {token}"},
    )

    data = response.get_json()["data"]
    assert response.status_code == 200
    assert data["availability"] == "insufficient"
    assert data["record_count"] == 5
    assert data["usable_record_count"] == 0
    assert data["excluded_record_count"] == 5
    assert "可用于汇总" in data["reason"]


def test_participant_analysis_is_withheld_after_high_risk_feedback(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    user_id, token = _wechat_login(client, "participant-analysis-high-risk")
    saved_result = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worksheet_id": "emotion_regulation_erq",
            "answers": [{"question_id": f"ERQ{i:02d}", "value": "4"} for i in range(1, 11)],
        },
    )
    assert saved_result.status_code == 201
    result_id = saved_result.get_json()["data"]["id"]
    for index in range(5):
        response = client.post(
            "/api/diaries",
            headers={"Authorization": f"Bearer {token}"},
            json={"scene": "亲子沟通", "event_description": f"记录{index}", "parent_emotion": "担心"},
        )
        assert response.status_code == 201
    high_risk = client.post(
        "/api/feedback/generate",
        json={"user_id": user_id, "event_description": "我不想活了", "automatic_thought": "撑不下去了"},
    )
    assert high_risk.status_code == 201
    assert high_risk.get_json()["data"]["risk_level"] == "high"
    feedback_id = high_risk.get_json()["data"]["id"]

    response = client.get(
        f"/api/assessment-results/{result_id}/exploratory-analysis",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["availability"] == "withheld"
    assert data["record_count"] == 5
    assert data["human_review_required"] is True
    assert data["affect"]["items"] == []
    assert data["interaction_network"]["edges"] == []

    reviews = client.get(
        "/api/risk-review?status=pending",
        headers={"X-Admin-Token": "safehome-local-admin-token"},
    ).get_json()["data"]["items"]
    review = next(item for item in reviews if item["source_id"] == feedback_id)
    closed = client.post(
        f"/api/risk-review/{review['id']}/review",
        headers={"X-Admin-Token": "safehome-local-admin-token"},
        json={
            "review_status": "closed",
            "review_note": "已由人工完成复核。",
            "action_taken": "已完成现实支持确认。",
            "closed_reason": "本次人工关注已处理完成。",
        },
    )
    assert closed.status_code == 200

    available = client.get(
        f"/api/assessment-results/{result_id}/exploratory-analysis",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert available.status_code == 200
    assert available.get_json()["data"]["availability"] == "available"


def test_student_result_does_not_receive_stage_two_exploratory_analysis(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    registered = client.post(
        "/api/auth/register",
        json={
            "username": "stage-two-student",
            "password": "Password123!",
            "nickname": "学生",
            "role": "student",
        },
    )
    assert registered.status_code == 201
    token = registered.get_json()["data"]["token"]
    saved_result = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={"worksheet_id": "student_profile_v1", "answers": _student_profile_answers()},
    )
    assert saved_result.status_code == 201

    response = client.get(
        f"/api/assessment-results/{saved_result.get_json()['data']['id']}/exploratory-analysis",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["availability"] == "ineligible"
    assert data["affect"]["items"] == []
    assert data["interaction_network"]["edges"] == []


def test_assessment_result_reads_tolerate_mysql_dict_rows(tmp_path, monkeypatch):
    """pymysql DictCursor rows are plain dicts; positional row[0] returned 500 in production."""
    import sqlite3

    app = _fresh_app(tmp_path)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "participant-mysql-dict-rows")
    headers = {"Authorization": f"Bearer {token}"}
    answers = [{"question_id": f"ERQ{i:02d}", "value": "4"} for i in range(1, 11)]
    saved = client.post(
        "/api/assessment-results",
        headers=headers,
        json={"worksheet_id": "emotion_regulation_erq", "answers": answers},
    )
    assert saved.status_code == 201
    result_id = saved.get_json()["data"]["id"]
    monkeypatch.setattr(
        sqlite3,
        "Row",
        lambda cursor, row: {column[0]: row[index] for index, column in enumerate(cursor.description)},
    )

    listed = client.get("/api/assessment-results", headers=headers)
    assert listed.status_code == 200
    assert listed.get_json()["data"]["total"] == 1
    analysis = client.get(f"/api/assessment-results/{result_id}/exploratory-analysis", headers=headers)
    assert analysis.status_code == 200
    assert analysis.get_json()["data"]["record_count"] == 0


def _exploratory(client, token, result_id):
    response = client.get(
        f"/api/assessment-results/{result_id}/exploratory-analysis",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    return response.get_json()["data"]


def _erq_result(client, token):
    saved = client.post(
        "/api/assessment-results",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worksheet_id": "emotion_regulation_erq",
            "answers": [{"question_id": f"ERQ{i:02d}", "value": "4"} for i in range(1, 11)],
        },
    )
    assert saved.status_code == 201
    return saved.get_json()["data"]["id"]


def test_participant_analysis_withheld_until_high_risk_diary_review_closes(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "participant-analysis-diary-risk")
    headers = {"Authorization": f"Bearer {token}"}
    admin = {"X-Admin-Token": "safehome-local-admin-token"}
    result_id = _erq_result(client, token)
    for index in range(5):
        response = client.post(
            "/api/diaries",
            headers=headers,
            json={"scene": "亲子沟通", "event_description": f"记录{index}", "parent_emotion": "担心"},
        )
        assert response.status_code == 201
    risky = client.post(
        "/api/diaries",
        headers=headers,
        json={"scene": "睡前冲突", "event_description": "孩子说他不想活了。", "parent_emotion": "担心"},
    )
    assert risky.status_code == 201
    diary_id = risky.get_json()["data"]["id"]
    assert client.post("/api/feedback/generate", headers=headers, json={"diary_id": diary_id}).status_code == 201

    assert _exploratory(client, token, result_id)["availability"] == "withheld"

    reviews = client.get("/api/risk-review", headers=admin).get_json()["data"]["items"]
    review = next(item for item in reviews if item["source_type"] == "diary" and item["source_id"] == diary_id)
    closed = client.post(
        f"/api/risk-review/{review['id']}/review",
        headers=admin,
        json={
            "review_status": "closed",
            "review_note": "已由人工完成复核。",
            "action_taken": "已完成现实支持确认。",
            "closed_reason": "本次人工关注已处理完成。",
        },
    )
    assert closed.status_code == 200

    assert _exploratory(client, token, result_id)["availability"] == "available"


def test_participant_analysis_reports_scene_share_parent_child_pairs_and_trend(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()
    _user_id, token = _wechat_login(client, "participant-analysis-pairs")
    headers = {"Authorization": f"Bearer {token}"}
    result_id = _erq_result(client, token)
    records = [
        ("作业拖延", "生气", 8, "烦躁"),
        ("作业拖延", "生气", 6, "烦躁"),
        ("作业拖延", "着急", 5, "委屈"),
        ("睡前冲突", "着急", 4, "不确定"),
        ("睡前冲突", "着急", 3, "委屈"),
        ("手机使用", "担心", 4, "烦躁"),
    ]
    for scene, emotion, intensity, child in records:
        response = client.post(
            "/api/diaries",
            headers=headers,
            json={
                "scene": scene,
                "event_description": "一次普通的冲突记录",
                "parent_emotion": emotion,
                "parent_emotion_intensity": intensity,
                "child_emotion": child,
                "child_emotion_intensity": 5,
            },
        )
        assert response.status_code == 201

    data = _exploratory(client, token, result_id)

    assert data["availability"] == "available"
    edge = next(
        item for item in data["interaction_network"]["edges"]
        if item["scene"] == "作业拖延" and item["emotion"] == "生气"
    )
    assert (edge["support"], edge["share_in_scene"], edge["share_overall"]) == (2, 0.67, 0.33)
    assert (edge["lift"], edge["average_intensity"]) == (2.0, 7.0)
    parent_child = data["parent_child"]
    assert parent_child["paired_record_count"] == 5
    assert parent_child["causal_interpretation_allowed"] is False
    first = parent_child["pairs"][0]
    assert (first["parent_emotion"], first["child_emotion"], first["support"]) == ("生气", "烦躁", 2)
    assert first["average_parent_intensity"] == 7.0
    trend = data["affect"]["trend"]
    assert (trend["available"], trend["recent_count"], trend["earlier_count"]) == (True, 3, 3)
