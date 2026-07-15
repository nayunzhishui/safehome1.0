import json
from pathlib import Path

from services.assessment_execution_service import execute_assessment


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load(name: str) -> dict:
    return json.loads((PROJECT_ROOT / "content" / name).read_text(encoding="utf-8"))


def worksheets_by_id() -> dict[str, dict]:
    return {item["id"]: item for item in load("assessment_worksheets.json")["worksheets"]}


def submit_first_options(worksheet: dict):
    answers = [
        {"question_id": question["id"], "value": question["options"][0]["value"]}
        for question in worksheet["questions"]
    ]
    return execute_assessment(worksheet, answers)


def dimension_scores(result) -> dict[str, float]:
    return {row["key"]: row["score"] for row in result.scores.get("dimensions", [])}


def test_task18_opening_states_and_question_ids_are_consistent():
    worksheets = worksheets_by_id()
    catalog = {item["id"]: item for item in load("scales_catalog.json")["scales"]}
    opened = {
        "parental_burnout_pba": 23,
        "rsca_adolescent_resilience": 27,
        "regulatory_focus_general_18": 18,
        "rfq8_reflective_functioning": 8,
        "who5_wellbeing": 5,
        "cognitive_curiosity_student": 10,
    }
    for worksheet_id, count in opened.items():
        worksheet = worksheets[worksheet_id]
        question_ids = [question["id"] for question in worksheet["questions"]]
        assert worksheet["enabled_for_user"] is True
        if worksheet_id in catalog:
            assert catalog[worksheet_id]["enabled"] is True
        assert len(question_ids) == count
        assert len(question_ids) == len(set(question_ids))

    for worksheet_id, worksheet in worksheets.items():
        assert worksheet["enabled_for_user"] is True
        assert worksheet["review_status"] == "pilot_approved"
        if worksheet_id in catalog:
            assert catalog[worksheet_id]["enabled"] is True

    # These entries have project-owner approval but still lack an executable worksheet.
    for worksheet_id in {"sleep_isi_psqi", "parental_autonomy_support", "family_cohesion_adaptability"}:
        assert worksheet_id not in worksheets
        assert catalog[worksheet_id]["enabled"] is False
        assert catalog[worksheet_id]["approval_status"] == "project_owner_approved_waiting_technical_chain"


def test_task18_scoring_rules_cover_opened_scales():
    worksheets = worksheets_by_id()

    pba = submit_first_options(worksheets["parental_burnout_pba"])
    assert pba.total_score == 0
    assert dimension_scores(pba) == {"EXHAUSTION": 0, "CONTRAST": 0, "SATURATION": 0, "DISTANCING": 0}

    rsca = submit_first_options(worksheets["rsca_adolescent_resilience"])
    assert rsca.total_score == 75
    assert dimension_scores(rsca) == {
        "GOAL_FOCUS": 5,
        "EMOTION_CONTROL": 26,
        "POSITIVE_COGNITION": 4,
        "FAMILY_SUPPORT": 18,
        "INTERPERSONAL_ASSISTANCE": 22,
    }

    regulatory = submit_first_options(worksheets["regulatory_focus_general_18"])
    assert regulatory.total_score is None
    assert dimension_scores(regulatory) == {"PROMOTION": 1, "PREVENTION": 1}

    rfq8 = submit_first_options(worksheets["rfq8_reflective_functioning"])
    assert rfq8.total_score is None
    assert dimension_scores(rfq8) == {"RFQC": 3, "RFQU": 0.5}

    who5 = submit_first_options(worksheets["who5_wellbeing"])
    assert who5.total_score == 25
    assert dimension_scores(who5) == {"WELLBEING": 25}

    ecs = submit_first_options(worksheets["cognitive_curiosity_student"])
    assert ecs.total_score == 10
    assert dimension_scores(ecs) == {"INTEREST": 6, "DEPRIVATION": 4}

    tipi = submit_first_options(worksheets["big_five_tipi_10"])
    assert tipi.total_score is None
    assert dimension_scores(tipi) == {
        "EXTRAVERSION": 4,
        "AGREEABLENESS": 4,
        "CONSCIENTIOUSNESS": 4,
        "EMOTIONAL_STABILITY": 4,
        "OPENNESS": 4,
    }

    scs = submit_first_options(worksheets["self_compassion_scs_cn"])
    assert scs.total_score is None
    assert dimension_scores(scs) == {
        "SCS_SK": 1,
        "SCS_SJ": 5,
        "SCS_CH": 1,
        "SCS_ISO": 5,
        "SCS_MIND": 1,
        "SCS_OVER": 5,
        "SCS_TOTAL": 3,
    }

    micro_ysq = submit_first_options(worksheets["micro_ysq_relationship_18"])
    assert micro_ysq.total_score is None
    assert dimension_scores(micro_ysq) == {f"YSQ_THEME{i:02d}": 1 for i in range(1, 19)}

    bfi = submit_first_options(worksheets["big_five_bfi_60"])
    assert bfi.total_score is None
    assert len(dimension_scores(bfi)) == 5


def test_task18_training_rules_exist_for_supportive_scales_not_tipi():
    rules = load("assessment_training_map.json")["rules"]
    worksheet_ids = {
        rule.get("trigger_condition", {}).get("worksheet_id")
        for rule in rules
        if rule.get("rule_id", "").startswith("task18_")
    }
    assert worksheet_ids == {
        "parental_burnout_pba",
        "rsca_adolescent_resilience",
        "regulatory_focus_general_18",
        "rfq8_reflective_functioning",
        "who5_wellbeing",
        "cognitive_curiosity_student",
    }
    assert "big_five_tipi_10" not in worksheet_ids
