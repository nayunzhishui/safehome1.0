const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

function normalizeRedirect(rawRedirect) {
  if (!rawRedirect) return "";
  const decoded = decodeURIComponent(rawRedirect);
  return decoded.startsWith("/pages/") ? decoded : "";
}

function navigateAfterAuth(redirectUrl) {
  if (redirectUrl) {
    const tabPages = ["/pages/home/index", "/pages/training/index", "/pages/course/index", "/pages/profile/index"];
    if (tabPages.includes(redirectUrl)) {
      wx.switchTab({ url: redirectUrl });
    } else {
      wx.redirectTo({ url: redirectUrl });
    }
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
    wechatLoading: false,
    phoneLoading: false,
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

  submitWechatLogin() {
    if (!wx.login) {
      this.setData({
        status: "error",
        message: "当前环境不支持微信登录，请使用账号密码登录。",
      });
      return;
    }
    this.setData({
      wechatLoading: true,
      status: "loading",
      message: "正在获取微信登录凭证...",
    });
    wx.login({
      success: (loginResult) => {
        if (!loginResult.code) {
          this.setData({
            wechatLoading: false,
            status: "error",
            message: "没有拿到微信登录凭证，请稍后重试或使用账号密码登录。",
          });
          return;
        }
        api.wechatLogin({ code: loginResult.code })
          .then((result) => {
            const app = getApp();
            if (app && app.setAuthSession) {
              app.setAuthSession(result.token, result.user);
            }
            wx.showToast({ title: "已登录", icon: "success" });
            navigateAfterAuth(this.data.redirectUrl);
          })
          .catch((error) => {
            this.setData({
              status: "error",
              message: error.debugMessage || error.message || "微信登录暂不可用，请使用账号密码登录。",
            });
          })
          .finally(() => {
            this.setData({ wechatLoading: false });
          });
      },
      fail: () => {
        this.setData({
          wechatLoading: false,
          status: "error",
          message: "微信登录凭证获取失败，请使用账号密码登录。",
        });
      },
    });
  },

  bindPhone(event) {
    const token = wx.getStorageSync("auth_token");
    if (!token) {
      this.setData({
        status: "error",
        message: "请先完成微信登录或账号登录，再绑定手机号。",
      });
      return;
    }
    const detail = event.detail || {};
    const code = detail.code || "";
    if (!code) {
      this.setData({
        status: "error",
        message: "没有拿到手机号授权 code。请确认小程序已配置手机号授权，或继续使用账号密码登录。",
      });
      return;
    }
    this.setData({
      phoneLoading: true,
      status: "loading",
      message: "正在检查手机号授权配置...",
    });
    api.bindWechatPhone({ code })
      .then(() => {
        this.setData({
          status: "success",
          message: "手机号已绑定。",
        });
      })
      .catch((error) => {
        this.setData({
          status: "error",
          message: error.debugMessage || error.message || "手机号授权暂不可用，请继续使用账号密码登录。",
        });
      })
      .finally(() => {
        this.setData({ phoneLoading: false });
      });
  },

  goRegister() {
    const redirectQuery = this.data.redirectUrl ? `?redirect=${encodeURIComponent(this.data.redirectUrl)}` : "";
    wx.navigateTo({ url: `/pages/register/index${redirectQuery}` });
  },
});
