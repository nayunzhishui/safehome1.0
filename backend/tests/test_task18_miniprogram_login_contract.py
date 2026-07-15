from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_login_page_keeps_three_independent_login_paths():
    js = (ROOT / "apps/miniprogram/pages/login/index.js").read_text(encoding="utf-8")
    wxml = (ROOT / "apps/miniprogram/pages/login/index.wxml").read_text(encoding="utf-8")

    assert 'bindtap="submitWechatLogin"' in wxml
    assert 'open-type="getPhoneNumber"' in wxml
    assert 'bindgetphonenumber="handlePhoneLogin"' in wxml
    assert 'bindtap="submitLogin"' in wxml
    assert "wx.login({" in js
    assert "api.wechatLogin({ code: loginResult.code })" in js
    assert "api.phoneLogin({ code })" in js
    assert "api.login({ username, password })" in js


def test_login_page_probes_capabilities_without_disabling_account_login():
    js = (ROOT / "apps/miniprogram/pages/login/index.js").read_text(encoding="utf-8")
    wxml = (ROOT / "apps/miniprogram/pages/login/index.wxml").read_text(encoding="utf-8")

    assert "api.getAuthCapabilities()" in js
    assert "capabilityMessage" in wxml
    assert 'disabled="{{loading || wechatLoading || phoneLoading}}"' in wxml
