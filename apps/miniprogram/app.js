const { getCloudConfig, migrateLegacyCloudConfig } = require("./services/cloudConfig");
const { loadDisplayFonts } = require("./utils/display-font");
const { parseChannel, rememberChannel, flushChannelEvent } = require("./utils/channel");

// A3 渠道标记：记下第一次进来的渠道，登录后补报一次（docs/11_商业化开发/开发框架.md 第 2 节）。
function noteChannel(options) {
  try {
    rememberChannel(parseChannel(options || {}));
  } catch (error) {
    // 渠道统计出错不能影响启动。
  }
}

function reportChannel() {
  try {
    const { createSafeHomeApi } = require("./services/api");
    flushChannelEvent(createSafeHomeApi());
  } catch (error) {
    // 同上。
  }
}

App({
  globalData: {
    token: "",
    user: null,
    cloudConfigError: null,
  },

  onLaunch(options) {
    noteChannel(options);
    loadDisplayFonts();
    migrateLegacyCloudConfig();
    if (wx.cloud && wx.cloud.init) {
      try {
        const cloudConfig = getCloudConfig();
        if (!cloudConfig.useLocalHttp) {
          wx.cloud.init({
            env: cloudConfig.cloudEnvId,
            traceUser: false,
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
    if (this.globalData.token) reportChannel();
  },

  onShow(options) {
    noteChannel(options);
  },

  setAuthSession(token, user) {
    this.globalData.token = token || "";
    this.globalData.user = user || null;
    if (token) {
      wx.setStorageSync("auth_token", token);
      wx.setStorageSync("auth_user", user || null);
      wx.removeStorageSync("safehome_anonymous_user_id");
      reportChannel();
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
