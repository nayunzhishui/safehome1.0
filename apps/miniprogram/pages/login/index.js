const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

function normalizeRedirect(rawRedirect) {
  if (!rawRedirect) return "";
  const decoded = decodeURIComponent(rawRedirect);
  return decoded.startsWith("/pages/") ? decoded : "";
}

function navigateAfterAuth(redirectUrl) {
  if (redirectUrl) {
    wx.redirectTo({ url: redirectUrl });
    return;
  }
  wx.switchTab({ url: "/pages/home/index" });
}

Page({
  data: {
    username: "",
    password: "",
    redirectUrl: "",
    loading: false,
    status: "idle",
    message: "",
  },

  onLoad(options = {}) {
    this.setData({ redirectUrl: normalizeRedirect(options.redirect) });
  },

  onUsernameInput(event) {
    this.setData({ username: event.detail.value });
  },

  onPasswordInput(event) {
    this.setData({ password: event.detail.value });
  },

  submitLogin() {
    const username = this.data.username.trim();
    const password = this.data.password;
    if (!username || !password) {
      this.setData({ status: "error", message: "请填写用户名和密码" });
      return;
    }
    this.setData({ loading: true, status: "loading", message: "正在登录..." });
    api.login({ username, password })
      .then((result) => {
        const app = getApp();
        if (app && app.setAuthSession) {
          app.setAuthSession(result.token, result.user);
        }
        wx.showToast({ title: "已登录", icon: "success" });
        navigateAfterAuth(this.data.redirectUrl);
      })
      .catch((error) => {
        this.setData({ status: "error", message: error.message || "登录失败，请稍后重试。" });
      })
      .finally(() => {
        this.setData({ loading: false });
      });
  },

  goRegister() {
    const redirectQuery = this.data.redirectUrl ? `?redirect=${encodeURIComponent(this.data.redirectUrl)}` : "";
    wx.navigateTo({ url: `/pages/register/index${redirectQuery}` });
  },
});
