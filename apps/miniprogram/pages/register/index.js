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
    nickname: "",
    redirectUrl: "",
    roleIndex: 0,
    roleOptions: [
      { value: "parent", label: "家长" },
      { value: "student", label: "学生" },
    ],
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

  onNicknameInput(event) {
    this.setData({ nickname: event.detail.value });
  },

  onRoleChange(event) {
    this.setData({ roleIndex: Number(event.detail.value || 0) });
  },

  submitRegister() {
    const username = this.data.username.trim();
    const password = this.data.password;
    const role = this.data.roleOptions[this.data.roleIndex].value;
    if (username.length < 3) {
      this.setData({ status: "error", message: "用户名至少需要 3 个字符" });
      return;
    }
    if (password.length < 8) {
      this.setData({ status: "error", message: "密码至少需要 8 个字符" });
      return;
    }
    this.setData({ loading: true, status: "loading", message: "正在注册..." });
    api.register({ username, password, role, nickname: this.data.nickname.trim() || undefined })
      .then((result) => {
        const app = getApp();
        if (app && app.setAuthSession) {
          app.setAuthSession(result.token, result.user);
        }
        wx.showToast({ title: "已注册", icon: "success" });
        navigateAfterAuth(this.data.redirectUrl);
      })
      .catch((error) => {
        this.setData({ status: "error", message: error.message || "注册失败，请稍后重试。" });
      })
      .finally(() => {
        this.setData({ loading: false });
      });
  },

  goLogin() {
    const redirectQuery = this.data.redirectUrl ? `?redirect=${encodeURIComponent(this.data.redirectUrl)}` : "";
    wx.navigateTo({ url: `/pages/login/index${redirectQuery}` });
  },
});
