import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROGRAMS = {
    item["id"]: item
    for item in json.loads((PROJECT_ROOT / "content" / "programs.json").read_text(encoding="utf-8"))["programs"]
}


def test_every_session_is_a_complete_text_practice():
    for program in PROGRAMS.values():
        assert program["summary"] and program["safety_note"]
        assert program["protocol_version"] == "2026.10-text-v2"
        for session in program["sessions"]:
            for field in ("intro", "example", "writing_prompt", "closing"):
                assert session[field].strip(), (program["id"], session["session_no"], field)
            # Bare labels such as "写事实" now carry an explanation after the original wording.
            assert all(len(step) > 8 for step in session["steps"]), (program["id"], session["session_no"])
            assert len(session["reflection_questions"]) >= 2


def test_original_wording_is_kept_while_enriching():
    exam_steps = PROGRAMS["self_compassion_exam_anxiety"]["sessions"][1]["steps"]
    assert [step.split("：", 1)[0] for step in exam_steps] == ["写事实", "写预测", "写评价", "补一个更灵活的解释"]
    assert PROGRAMS["self_compassion_exam_anxiety"]["sessions"][0]["writing_prompt"] == "当我想到这次考试或作业时，我最先担心的是……我可以先对自己说……"
    assert PROGRAMS["self_compassion_relationship_growth"]["interpretation_boundary"].startswith("关系绘画")
    review = PROGRAMS["self_compassion_relationship_growth"]["sessions"][2]["reflection_questions"]
    assert review[:2] == ["这段回应中最稳定自己的部分是什么？", "是否需要现实支持或人工反馈？"]


def test_each_program_cites_its_evidence():
    for program in PROGRAMS.values():
        evidence = program["evidence_basis"]
        assert len(evidence) >= 3
        assert all(item["practice"] and item["finding"] and item["citation"] for item in evidence)
    sleep = PROGRAMS["academic_pressure_sleep_health"]["evidence_basis"]
    assert any("教基厅函〔2021〕11号" in item["citation"] for item in sleep)
    exam = PROGRAMS["self_compassion_exam_anxiety"]["evidence_basis"]
    assert any("10.1126/science.1199427" in item["url"] for item in exam)


def test_new_participant_text_avoids_safety_screening_keywords():
    risk = json.loads((PROJECT_ROOT / "content" / "risk_keywords.json").read_text(encoding="utf-8"))
    keywords = [keyword for category in risk["categories"] for keyword in category["keywords"]]
    for program in PROGRAMS.values():
        texts = [program["summary"], program["safety_note"], *[item["finding"] for item in program["evidence_basis"]]]
        for session in program["sessions"]:
            texts += [session["intro"], session["example"], session["writing_prompt"], session["closing"]]
        hits = [keyword for keyword in keywords for text in texts if keyword in text]
        assert not hits, (program["id"], hits)
