from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (PROJECT_ROOT / path).read_text(encoding="utf-8")


def test_miniprogram_privacy_center_exposes_status_submit_cancel_and_appeal():
    js = _read("apps/miniprogram/pages/settings-detail/index.js")
    wxml = _read("apps/miniprogram/pages/settings-detail/index.wxml")
    api = _read("apps/miniprogram/services/api.js")

    assert "loadPrivacyRequests" in js
    assert "submitPrivacyDeleteRequest" in js
    assert "cancelPrivacyRequest" in js
    assert "appealPrivacyRequest" in js
    assert "我的删除申请" in wxml
    assert "privacyDeleteMyData" in api
    assert "Idempotency-Key" in api
    assert "/appeal" in api


def test_web_privacy_workspace_is_role_scoped_and_does_not_fake_completion():
    main = _read("apps/web/src/main.tsx")
    page = _read("apps/web/src/pages/PrivacyRequestsManagement.tsx")

    assert 'href: "/privacy-requests"' in main
    assert 'roles: ["admin", "supervisor"]' in main
    assert "领取并开始核对" in page
    assert "记录为未执行" in page
    assert "删除/匿名化执行器" in page
    assert "生成范围预览" in page
    assert "执行 Dry-run" in page
    assert "批准当前范围" in page
    assert "正式执行" in page
    assert 'transition("mark_completed")' not in page


def test_shared_privacy_contract_covers_review_scope_and_actions():
    constants = _read("shared/constants/api.ts")
    types = _read("shared/types/api.ts")

    assert "privacyAdminRequests" in constants
    assert "PrivacyHandlingScope" in types
    assert "PrivacyReviewDetail" in types
    assert "PrivacyRequestAction" in types
    assert "PrivacyScopePreview" in types
    assert "PrivacyExecutionResult" in types
