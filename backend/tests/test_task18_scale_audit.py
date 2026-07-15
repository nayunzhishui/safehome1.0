import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "audit_task18_scales.py"
SPEC = importlib.util.spec_from_file_location("audit_task18_scales", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def assert_pilot_approved(worksheet, catalog_item):
    assert worksheet["enabled_for_user"] is True
    assert worksheet["review_status"] == "pilot_approved"
    assert catalog_item["enabled"] is True
    assert catalog_item["review_status"] == "pilot_approved"
    assert worksheet["approval"]["scope"] == "pilot_release"


def test_task18_scale_audit_detects_known_screenshot_content_failures():
    payload = MODULE.audit()
    issues = {(row["worksheet_id"], row["location"], row["message"]) for row in payload["issues"]}



def test_task18_ghq12_matches_local_source_and_stays_governed():
    worksheets = MODULE._load(MODULE.WORKSHEETS_PATH)["worksheets"]
    catalog = MODULE._load(MODULE.CATALOG_PATH)["scales"]
    worksheet = next(item for item in worksheets if item["id"] == "ghq12_general_health")
    catalog_item = next(item for item in catalog if item["id"] == "ghq12_general_health")

    assert worksheet["questions"][-1]["prompt"] == "总的来看，感到适度的愉快吗？"
    assert worksheet["instructions"].startswith("请根据从两三周前到现在")
    assert worksheet["dimensions"][0]["reverse_item_codes"] == [
        "GHQ01",
        "GHQ03",
        "GHQ04",
        "GHQ07",
        "GHQ08",
        "GHQ12",
    ]
    assert_pilot_approved(worksheet, catalog_item)


def test_task18_tipi_matches_official_english_source_and_stays_governed():
    worksheets = MODULE._load(MODULE.WORKSHEETS_PATH)["worksheets"]
    catalog = MODULE._load(MODULE.CATALOG_PATH)["scales"]
    worksheet = next(item for item in worksheets if item["id"] == "big_five_tipi_10")
    catalog_item = next(item for item in catalog if item["id"] == "big_five_tipi_10")

    assert worksheet["questions"][-1]["prompt"] == "传统的、缺乏创造性的。"
    assert "成对特征" in worksheet["instructions"]
    assert "最近两周" not in worksheet["instructions"]
    assert [dimension["code"] for dimension in worksheet["dimensions"]] == [
        "EXTRAVERSION",
        "AGREEABLENESS",
        "CONSCIENTIOUSNESS",
        "EMOTIONAL_STABILITY",
        "OPENNESS",
    ]
    assert_pilot_approved(worksheet, catalog_item)


def test_task18_psss_uses_psss_items_instead_of_ssrs_items():
    worksheets = MODULE._load(MODULE.WORKSHEETS_PATH)["worksheets"]
    catalog = MODULE._load(MODULE.CATALOG_PATH)["scales"]
    worksheet = next(item for item in worksheets if item["id"] == "perceived_social_support_psss")
    catalog_item = next(item for item in catalog if item["id"] == "perceived_social_support_psss")
    prompts = [question["prompt"] for question in worksheet["questions"]]

    assert prompts[0] == "在我遇到问题时，有些人（领导、亲戚、同事）会出现在我的身旁。"
    assert prompts[-1] == "我能与朋友们讨论自己的难题。"
    assert not any("您有多少关系密切" in prompt for prompt in prompts)
    assert [dimension["item_ids"] for dimension in worksheet["dimensions"]] == [
        ["PSSS01", "PSSS02", "PSSS05", "PSSS10"],
        ["PSSS03", "PSSS04", "PSSS08", "PSSS11"],
        ["PSSS06", "PSSS07", "PSSS09", "PSSS12"],
    ]
    assert_pilot_approved(worksheet, catalog_item)


def test_task18_fmi12_matches_local_pdf_and_stays_governed():
    worksheets = MODULE._load(MODULE.WORKSHEETS_PATH)["worksheets"]
    catalog = MODULE._load(MODULE.CATALOG_PATH)["scales"]
    worksheet = next(item for item in worksheets if item["id"] == "fmi_12_mindfulness")
    catalog_item = next(item for item in catalog if item["id"] == "fmi_12_mindfulness")

    assert worksheet["questions"][0]["prompt"] == "我对当前的体验是开放的。"
    assert worksheet["questions"][1]["prompt"] == "无论吃饭、做饭、洗衣服或者说话时，我都会感受我的身体。"
    assert "最近一周内（包括今天）" in worksheet["instructions"]
    assert worksheet["dimensions"][0]["item_ids"] == [f"FMI{i:02d}" for i in range(1, 13)]
    assert_pilot_approved(worksheet, catalog_item)


def test_task18_self_compassion_matches_local_pdf_and_stays_governed():
    worksheets = MODULE._load(MODULE.WORKSHEETS_PATH)["worksheets"]
    catalog = MODULE._load(MODULE.CATALOG_PATH)["scales"]
    worksheet = next(item for item in worksheets if item["id"] == "self_compassion_scs_cn")
    catalog_item = next(item for item in catalog if item["id"] == "self_compassion_scs_cn")

    assert worksheet["questions"][2]["prompt"] == "遇到困难时，我会把困难看成是生活的一部分，是每个人都会经历的。"
    assert worksheet["dimension_score_method"] == "mean"
    assert worksheet["total_score_method"] == "none"
    assert worksheet["derived_dimensions"][0]["calculation"]["type"] == "mean_dimensions"
    assert_pilot_approved(worksheet, catalog_item)


def test_task18_swls_matches_local_docx_and_stays_governed():
    worksheets = MODULE._load(MODULE.WORKSHEETS_PATH)["worksheets"]
    catalog = MODULE._load(MODULE.CATALOG_PATH)["scales"]
    worksheet = next(item for item in worksheets if item["id"] == "swls_life_satisfaction")
    catalog_item = next(item for item in catalog if item["id"] == "swls_life_satisfaction")

    assert [question["prompt"] for question in worksheet["questions"]] == [
        "大多数情况下，我的生活接近理想状态。",
        "我的生活状态很好。",
        "我对自己的生活感到满意。",
        "到目前为止，我已经得到了我认为生活中最重要的事物。",
        "如果我可以再活一次，我不想改变任何事情。",
    ]
    assert [option["label"] for option in worksheet["questions"][0]["options"]] == [
        "1 强烈反对",
        "2 不同意",
        "3 基本不同意",
        "4 中立",
        "5 基本同意",
        "6 同意",
        "7 非常同意",
    ]
    assert_pilot_approved(worksheet, catalog_item)


def test_task18_attribution_restores_cause_inputs_and_dimension_specific_options():
    worksheets = MODULE._load(MODULE.WORKSHEETS_PATH)["worksheets"]
    catalog = MODULE._load(MODULE.CATALOG_PATH)["scales"]
    worksheet = next(item for item in worksheets if item["id"] == "attribution_style_student_36")
    catalog_item = next(item for item in catalog if item["id"] == "attribution_style_student_36")

    assert len(worksheet["questions"]) == 48
    assert worksheet["questions"][0]["id"] == "ASQ_CAUSE01"
    assert worksheet["questions"][0]["type"] == "textarea"
    assert worksheet["questions"][1]["options"][0]["label"] == "1 完全由于他人或客观因素"
    assert worksheet["questions"][1]["options"][-1]["label"] == "7 完全由于自己"
    assert worksheet["questions"][2]["options"][0]["label"] == "1 完全不会再存在"
    assert worksheet["questions"][3]["options"][-1]["label"] == "7 影响生活所有方面"
    assert worksheet["dimension_score_method"] == "mean"
    assert worksheet["total_score_method"] == "none"
    assert_pilot_approved(worksheet, catalog_item)


def test_task18_micro_ysq_exposes_all_item_level_supportive_dimensions():
    worksheets = MODULE._load(MODULE.WORKSHEETS_PATH)["worksheets"]
    catalog = MODULE._load(MODULE.CATALOG_PATH)["scales"]
    worksheet = next(item for item in worksheets if item["id"] == "micro_ysq_relationship_18")
    catalog_item = next(item for item in catalog if item["id"] == "micro_ysq_relationship_18")

    assert len(worksheet["dimensions"]) == 18
    assert [dimension["code"] for dimension in worksheet["dimensions"]] == [f"YSQ_THEME{i:02d}" for i in range(1, 19)]
    assert worksheet["dimensions"][0]["label"] == "被理解与关心担心"
    assert worksheet["dimensions"][-1]["label"] == "冲突回避与屈从"
    assert [question["dimension"] for question in worksheet["questions"]] == [f"YSQ_THEME{i:02d}" for i in range(1, 19)]
    assert_pilot_approved(worksheet, catalog_item)


def test_task18_bfi60_repairs_truncated_item_and_disables_total_score():
    worksheets = MODULE._load(MODULE.WORKSHEETS_PATH)["worksheets"]
    catalog = MODULE._load(MODULE.CATALOG_PATH)["scales"]
    worksheet = next(item for item in worksheets if item["id"] == "big_five_bfi_60")
    catalog_item = next(item for item in catalog if item["id"] == "big_five_bfi_60")

    assert worksheet["questions"][-1]["prompt"] == "我要花很多时间才能安顿下来工作。"
    assert worksheet["total_score_method"] == "none"
    assert len(worksheet["dimensions"]) == 5
    assert_pilot_approved(worksheet, catalog_item)


def test_task18_scale_audit_has_no_remaining_content_or_governance_issue():
    payload = MODULE.audit()
    assert payload["issues"] == []
    assert payload["affected_count"] == 0
