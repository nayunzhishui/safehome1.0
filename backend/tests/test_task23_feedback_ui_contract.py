from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def test_feedback_rating_component_uses_four_shared_non_diagnostic_choices():
    source = _read("apps/miniprogram/components/feedback-rating/index.js")
    wxml = _read("apps/miniprogram/components/feedback-rating/index.wxml")
    for value in ["matches", "partly_matches", "does_not_match", "uncomfortable"]:
        assert value in source
    for label in ["符合", "部分符合", "不符合", "让我不舒服"]:
        assert label in source
    assert "不会据此推断风险或诊断" in wxml
    assert 'aria-label="评价为{{item.label}}"' in wxml


def test_feedback_rating_is_available_in_all_required_participant_surfaces():
    surfaces = {
        "feedback-result": "instant_feedback",
        "relationship-report": "stage_report",
        "training-card": "training_recommendation",
        "message-detail": "message",
    }
    for page, source_type in surfaces.items():
        js = _read(f"apps/miniprogram/pages/{page}/index.js")
        wxml = _read(f"apps/miniprogram/pages/{page}/index.wxml")
        config = _read(f"apps/miniprogram/pages/{page}/index.json")
        assert "createFeedbackLedgerEntry" in js
        assert f' source_type: "{source_type}"' in js or f'source_type: "{source_type}"' in js
        assert "<feedback-rating" in wxml
        assert '"feedback-rating"' in config


def test_negative_training_evaluation_promotes_an_existing_alternative():
    source = _read("apps/miniprogram/pages/training-card/index.js")
    assert '["does_not_match", "uncomfortable"]' in source
    assert "cards.slice(1)" in source
    assert "isPrimary: index === 0" in source


def test_feedback_ledger_contract_is_shared_across_clients():
    shared = _read("shared/constants/api.ts")
    miniprogram = _read("apps/miniprogram/services/api.js")
    web = _read("apps/web/src/services/safehomeApi.ts")
    assert 'feedbackLedger: "/api/feedback-ledger"' in shared
    assert "createFeedbackLedgerEntry" in miniprogram
    assert "createFeedbackLedgerEntry" in web
    assert "getFeedbackLedgerSummary" in web
