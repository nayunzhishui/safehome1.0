const { createSafeHomeApi } = require("../../services/api");
const { getMinorSafeguardStatus } = require("../../services/minorSafeguardsApi");

const api = createSafeHomeApi();
const PROTECTION_URL = "/pages/settings-detail/index?type=protection";

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

function needsMinorSafeguardFlow(status) {
  if (!status) return true;
  if (status.age_verification_required) return true;
  if (!status.minor_safeguards_required) return false;
  return status.status !== "active";
}

function navigateAfterParticipantGate(user, redirectUrl) {
  if (!user || user.role !== "student") {
    navigateAfterAuth(redirectUrl);
    return;
  }
  getMinorSafeguardStatus()
    .then((status) => {
      if (needsMinorSafeguardFlow(status)) {
        wx.redirectTo({ url: PROTECTION_URL });
        return;
      }
      navigateAfterAuth(redirectUrl);
    })
    .catch(() => {
      // For a student account, fail toward the protection flow. The page can
      // show a retry state without exposing protected functions.
      wx.redirectTo({ url: PROTECTION_URL });
    });
}

Page({
  data: {
    username: "",
    password: "",
    redirectUrl: "",
    loading: false,
    wechatLoading: false,
    phoneLoading: false,
    wechatAvailable: true,
    phoneAvailable: true,
    status: "idle",
    message: "",
    capabilityMessage: "",
    mustChangePassword: false,
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  },

  onLoad(options = {}) {
    this.setData({ redirectUrl: normalizeRedirect(options.redirect) });
    this.loadAuthCapabilities();
  },

  loadAuthCapabilities() {
    api.getAuthCapabilities()
      .then((capabilities) => {
        const wechatAvailable = !!(capabilities.wechat_login && capabilities.wechat_login.available);
        const phoneAvailable = !!(capabilities.phone_login && capabilities.phone_login.available);
        let capabilityMessage = "";
        if (!wechatAvailable && !phoneAvailable) {
          capabilityMessage = "微信与手机号快捷登录尚未完成云端配置，请先使用账号密码登录。";
        } else if (!wechatAvailable) {
          capabilityMessage = "微信一键登录尚未完成云端配置，可使用手机号或账号密码登录。";
        } else if (!phoneAvailable) {
          capabilityMessage = "手机号快捷登录尚未完成云端配置，可使用微信或账号密码登录。";
        }
        this.setData({ capabilityMessage, wechatAvailable, phoneAvailable });
      })
      .catch(() => {
        // Older deployments may not expose capability probing yet; login buttons remain usable.
      });
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
        this.completeLogin(result, "已登录");
      })
      .catch((error) => {
        this.setData({ status: "error", message: error.message || "登录失败，请稍后重试。" });
      })
      .finally(() => {
        this.setData({ loading: false });
      });
  },

  completeLogin(result, toastTitle) {
    const app = getApp();
    if (app && app.setAuthSession) {
      app.setAuthSession(result.token, result.user);
    }
    if (result.user && result.user.must_change_password) {
      this.setData({
        mustChangePassword: true,
        currentPassword: this.data.password,
        password: "",
        status: "idle",
        message: "首次登录，请先设置新密码。完成后才可继续。",
      });
      return;
    }
    wx.showToast({ title: toastTitle, icon: "success" });
    navigateAfterParticipantGate(result.user, this.data.redirectUrl);
  },

  onCurrentPasswordInput(event) {
    this.setData({ currentPassword: event.detail.value });
  },

  onNewPasswordInput(event) {
    this.setData({ newPassword: event.detail.value });
  },

  onConfirmPasswordInput(event) {
    this.setData({ confirmPassword: event.detail.value });
  },

  submitPasswordChange() {
    const currentPassword = this.data.currentPassword;
    const newPassword = this.data.newPassword;
    if (!currentPassword || !newPassword) {
      this.setData({ status: "error", message: "请填写临时密码和新密码。" });
      return;
    }
    if (newPassword !== this.data.confirmPassword) {
      this.setData({ status: "error", message: "两次输入的新密码不一致。" });
      return;
    }
    this.setData({ loading: true, status: "loading", message: "正在更新密码..." });
    api.changePassword({ current_password: currentPassword, new_password: newPassword })
      .then((result) => {
        const app = getApp();
        if (app && app.setAuthSession) app.setAuthSession(result.token, result.user);
        wx.showToast({ title: "密码已更新", icon: "success" });
        navigateAfterParticipantGate(result.user, this.data.redirectUrl);
      })
      .catch((error) => {
        this.setData({ status: "error", message: error.message || "密码更新失败，请检查后重试。" });
      })
      .finally(() => this.setData({ loading: false }));
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
            this.completeLogin(result, "微信登录成功");
          })
          .catch((error) => {
            this.setData({
              status: "error",
              message: error.message || "微信登录暂不可用，请尝试其他登录方式。",
            });
          })
          .finally(() => {
            this.setData({ wechatLoading: false });
          });
      },
      fail: (error) => {
        const canceled = String((error && error.errMsg) || "").includes("cancel");
        this.setData({
          wechatLoading: false,
          status: canceled ? "idle" : "error",
          message: canceled
            ? "你已取消微信登录，可以继续选择其他登录方式。"
            : "微信登录凭证获取失败，请重新尝试或使用账号密码登录。",
        });
      },
    });
  },

  handlePhoneLogin(event) {
    const detail = event.detail || {};
    const code = detail.code || "";
    if (!code) {
      const detailMessage = String(detail.errMsg || "");
      const canceled = detailMessage.includes("deny") || detailMessage.includes("cancel");
      this.setData({
        status: canceled ? "idle" : "error",
        message: canceled
          ? "你已取消手机号授权，可以继续选择其他登录方式。"
          : "没有取得新的手机号授权凭证，请重新点击或使用账号密码登录。",
      });
      return;
    }
    this.setData({
      phoneLoading: true,
      status: "loading",
      message: "正在完成手机号登录...",
    });
    api.phoneLogin({ code })
      .then((result) => {
        this.completeLogin(result, "手机号登录成功");
      })
      .catch((error) => {
        this.setData({
          status: "error",
          message: error.message || "手机号登录暂不可用，请尝试其他登录方式。",
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
