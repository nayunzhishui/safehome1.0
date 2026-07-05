const { getCloudConfig } = require("./services/cloudConfig");

App({
  globalData: {
    token: "",
    user: null,
  },

  onLaunch() {
    if (wx.cloud && wx.cloud.init) {
      const cloudConfig = getCloudConfig();
      wx.cloud.init({
        env: cloudConfig.cloudEnvId,
        traceUser: true,
      });
    }
    this.globalData.token = wx.getStorageSync("auth_token") || "";
    this.globalData.user = wx.getStorageSync("auth_user") || null;
  },

  setAuthSession(token, user) {
    this.globalData.token = token || "";
    this.globalData.user = user || null;
    if (token) {
      wx.setStorageSync("auth_token", token);
      wx.setStorageSync("auth_user", user || null);
      wx.removeStorageSync("safehome_anonymous_user_id");
    }
  },

  logout() {
    this.globalData.token = "";
    this.globalData.user = null;
    wx.removeStorageSync("auth_token");
    wx.removeStorageSync("auth_user");
  },
});
