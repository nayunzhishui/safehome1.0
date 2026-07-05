import importlib
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _fresh_app(tmp_path):
    sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith("routes.") or name.startswith("services."):
            sys.modules.pop(name, None)
    os.environ["DATABASE_PATH"] = str(tmp_path / "safehome-test.sqlite3")
    os.environ["CONTENT_DIR"] = str(PROJECT_ROOT / "content")
    module = importlib.import_module("app")
    return module.app


def test_legacy_self_built_assessment_is_removed_from_api(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    detail_response = client.get("/api/assessments/worksheet_3_1_anxiety")
    assert detail_response.status_code == 404

    submit_response = client.post(
        "/api/assessment-results",
        json={
            "user_id": "parent-legacy-check",
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


def test_legacy_assessment_results_are_hidden_from_user_history(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    active_response = client.post(
        "/api/assessment-results",
        json={
            "user_id": "history-filter-check",
            "worksheet_id": "student_profile_v1",
            "answers": [{"question_id": "test_anxiety", "prompt": "测试题", "value": "2", "score": 2}],
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
                "history-filter-check",
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

    list_response = client.get("/api/assessment-results?user_id=history-filter-check")
    assert list_response.status_code == 200
    items = list_response.get_json()["data"]["items"]
    assert [item["worksheet_id"] for item in items] == ["student_profile_v1"]


def test_enabled_student_profile_assessment_result_still_saves(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    response = client.post(
        "/api/assessment-results",
        json={
            "user_id": "student-enabled-check",
            "worksheet_id": "student_profile_v1",
            "answers": [{"question_id": "test_anxiety", "prompt": "测试题", "value": "3", "score": 3}],
        },
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["worksheet_id"] == "student_profile_v1"
    assert data["total_score"] == 3


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
        json={
            "user_id": "erq-dimension-check",
            "worksheet_id": "emotion_regulation_erq",
            "answers": answers,
        },
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["total_score"] == 6 * 5 + 4 * 2
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

    # 全部 18 题都填 6 分。PRFQ11、PRFQ18 为反向题（7 点量表翻转为 8-6=2）。
    all_items = [f"PRFQ{i:02d}" for i in range(1, 19)]
    answers = [
        {"question_id": item, "prompt": item, "value": "6", "score": 6} for item in all_items
    ]

    response = client.post(
        "/api/assessment-results",
        json={
            "user_id": "prfq-reverse-check",
            "worksheet_id": "parent_reflective_functioning_prfq",
            "answers": answers,
        },
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    dimensions = {item["key"]: item for item in data["scores"]["dimensions"]}

    # 均值计分
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

    response = client.post(
        "/api/assessment-results",
        json={
            "user_id": "assessment-risk-check",
            "worksheet_id": "student_profile_v1",
            "answers": [{"question_id": "free_text", "prompt": "压力事件", "value": "我最近不想活"}],
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
            ("assessment-risk-check", "assessment_result"),
        ).fetchone()[0]

    assert saved_count == 1


def test_assessment_profile_position_returns_cluster_for_modeled_scale(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    answers = [
        {"question_id": f"ERES{i:02d}", "prompt": f"ERES{i:02d}", "value": "4", "score": 4}
        for i in range(1, 12)
    ]
    submit_response = client.post(
        "/api/assessment-results",
        json={
            "user_id": "profile-position-check",
            "worksheet_id": "emotional_resilience_11",
            "answers": answers,
        },
    )
    assert submit_response.status_code == 201
    result_id = submit_response.get_json()["data"]["id"]

    response = client.get(f"/api/assessment-results/{result_id}/profile-position?user_id=profile-position-check")

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["available"] is True
    assert data["worksheet_id"] == "emotional_resilience_11"
    assert data["position"]["profile_name"]
    assert data["position"]["pc1"] is not None
    assert data["feature_summary"]["answered_features"] == 11
    assert len(data["feature_profile"]) == 11
    assert data["feature_profile"][0]["z_score"] is not None
    assert "不构成诊断" in data["boundary_notice"]
    assert data["interpretation"]["status"] in {"usable", "low_confidence", "outlier"}
    assert data["position"]["can_use_interpretation"] is False
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


def test_assessment_profile_position_marks_outlier_without_strong_interpretation(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    answers = [
        {"question_id": f"ERES{i:02d}", "prompt": f"ERES{i:02d}", "value": "99", "score": 99}
        for i in range(1, 12)
    ]
    submit_response = client.post(
        "/api/assessment-results",
        json={
            "user_id": "profile-position-outlier",
            "worksheet_id": "emotional_resilience_11",
            "answers": answers,
        },
    )
    assert submit_response.status_code == 201
    result_id = submit_response.get_json()["data"]["id"]

    response = client.get(f"/api/assessment-results/{result_id}/profile-position?user_id=profile-position-outlier")

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["available"] is True
    assert data["interpretation"]["status"] == "outlier"
    assert data["interpretation"]["can_use_interpretation"] is False
    assert data["position"]["can_use_interpretation"] is False
    assert "不做明确画像解释" in data["explanation"]


def test_assessment_profile_position_is_optional_for_unmodeled_scale(tmp_path):
    app = _fresh_app(tmp_path)
    client = app.test_client()

    answers = [
        {"question_id": "ERQ01", "prompt": "ERQ01", "value": "4", "score": 4},
        {"question_id": "ERQ02", "prompt": "ERQ02", "value": "3", "score": 3},
    ]
    submit_response = client.post(
        "/api/assessment-results",
        json={
            "user_id": "profile-position-unavailable",
            "worksheet_id": "emotion_regulation_erq",
            "answers": answers,
        },
    )
    assert submit_response.status_code == 201
    result_id = submit_response.get_json()["data"]["id"]

    response = client.get(f"/api/assessment-results/{result_id}/profile-position?user_id=profile-position-unavailable")

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["available"] is False
    assert "暂未接入" in data["reason"]
