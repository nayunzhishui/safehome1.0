const { getCloudConfig, migrateLegacyCloudConfig } = require("./services/cloudConfig");

App({
  globalData: {
    token: "",
    user: null,
    cloudConfigError: null,
  },

  onLaunch() {
    migrateLegacyCloudConfig();
    if (wx.cloud && wx.cloud.init) {
      try {
        const cloudConfig = getCloudConfig();
        if (!cloudConfig.useLocalHttp) {
          wx.cloud.init({
            env: cloudConfig.cloudEnvId,
            traceUser: true,
          });
        }
      } catch (error) {
        this.globalData.cloudConfigError = {
          code: error.code || "cloud_config_invalid",
          message: error.userMessage || "连接配置不可用，请检查配置后重试。",
          recoverable: true,
        };
      }
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
    wx.removeStorageSync("safehome_dismissed_data_claim_id");
    wx.removeStorageSync("safehome:selectedTrainingCard");
    wx.removeStorageSync("safehome:latestTrainingRecommendation");
    wx.removeStorageSync("safehome:threeDayLightPlan");
  },
});
