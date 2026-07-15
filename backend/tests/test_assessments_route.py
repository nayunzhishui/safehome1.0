import importlib
import json
import os
import sys
from pathlib import Path

import pytest


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
    assert data["total_score"] == 12


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
    assert data["total_score"] == 40
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
        assert worksheet["review_status"] == "pilot_approved"
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
